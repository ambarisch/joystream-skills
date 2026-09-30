---
name: notion-post-queue
description: Publish every "Ready to Post" row for a given persona and platform (default Twitter/X; LinkedIn supported) from a Notion content database, then write the result back to each row (Status "Posted" plus Post URL on success, or an Error description on failure). Use this skill whenever an agent needs to work through a Notion posting queue, publish scheduled or approved social posts for a persona, or sync post results back into Notion. Requires the platform's publish skill (x-publish for Twitter, linkedin-publish for LinkedIn) for the actual posting.
compatibility: Requires Notion tools in the session (MCP connector or equivalent) that can read a database schema, query rows and update pages, plus the publish skill for the platform (x-publish for Twitter, linkedin-publish for LinkedIn), each of which needs a posting tool for its platform.
metadata:
  version: "2.0.0"
  author: JoyStream
  depends-on: x-publish, linkedin-publish
  requires-contract: "1"   # minimum publish-skill contract version needed
---

# Notion → Post Queue

For one persona and one platform, find every row in a Notion database that is ready to publish, publish each one, and record the outcome on the row.

Notion is the shared state between agents and people: a person or an upstream agent marks rows "Ready to Post", and this skill turns them into live posts. This skill knows Notion; the platform's publish skill knows the platform. Each row's end state must truthfully reflect what happened on the platform, because other agents and people act on it.

## Inputs

- `database_url` (required): URL or ID of the Notion database.
- `persona` (required): the persona whose posts to publish. Must exactly match the row's `Persona` value (case-sensitive).
- `platform` (optional, default `Twitter`): the `Platform` value to publish. Must be listed under Publish skills below. One platform per run.
- `dry_run` (optional boolean, default false): do everything except posting and writing to Notion. See Dry run below.

If `database_url` or `persona` is missing or empty, stop immediately with an error. Don't guess a database or persona.

## Required capabilities

**Notion, three capabilities.** Choose tools by matching their descriptions and schemas to these, not by name (examples in [references/tool-hints.md](references/tool-hints.md), which are hints only):

1. Fetch a database's schema: property names, types and select/status options.
2. Query rows with filters and sort, following pagination.
3. Update a page's properties.

Prefer tools acting as the running user. Do not call Notion's HTTP API or any other route directly. If any of the three is missing, stop with `NO_TOOL: Notion tool for {capability} is not available` and post nothing.

**Publish skill for the platform.** Used for every post. Do not call a platform tool directly from this skill: the publish skill owns validation, tool discovery, the post call and error codes. It must implement contract version 1 or higher ([x-publish/references/contract.md](../x-publish/references/contract.md); what this skill uses is summarised in [references/x-publish-usage.md](references/x-publish-usage.md)). Any skill, sub-agent or inline procedure that honours that contract can stand in. If none is available, stop and report "{skill} is required".

## Publish skills

| `Platform` value | Publish skill |
|---|---|
| `Twitter` | `x-publish` |
| `LinkedIn` | `linkedin-publish` |

If `platform` is not in this table, stop with `NO_PUBLISHER: no publish skill for platform {platform}` and post nothing. Add a row here when a new publish skill exists.

## Database contract

| Property | Expected type | Read / write |
|---|---|---|
| `Platform` | Select | Read. Must equal `{platform}` |
| `Persona` | Select or text | Read. Must equal `{persona}` |
| `Status` | Select | Read `Ready to Post`; write `Posted` |
| `Formatted Copy` | Text or formula | Read. The post text |
| `Post URL` | URL | Write |
| `Error` | Text | Write |

### Property value shapes

Filters and updates must use the shape for the property's actual type, taken from the schema in Step 1. Read the update tool's schema for exact field names; the semantics are:

| Property (type) | Filter for equality | Value to write |
|---|---|---|
| `Status` (select or status) | option name equals the string | the option name `Posted` |
| `Post URL` (url) | n/a | the URL string |
| `Error` (rich text) | n/a | the text string; to clear, an empty string or empty rich text |
| `Persona` / `Platform` (select) | option name equals the string | not written |
| `Persona` / `Platform` (rich text) | text equals the string | not written |

If the update tool rejects a value shape, re-read the schema and retry the update once with the corrected shape before treating it as a failed update (Step 4d).

## Steps

### 1. Check the database before posting anything

Fetch the database schema with the Notion tool. Newer Notion workspaces place rows in a "data source" inside the database; if so, use that data source's id for the query, and the schema of that data source for the checks below.

Confirm the following, and write down the actual type of `Status`, `Platform` and `Persona`, since filters and updates are written differently for Status, Select and text properties:
- All six properties above exist.
- `Status` has both a `Ready to Post` and a `Posted` option.

If anything is missing, stop with an error naming exactly what is missing, and post nothing. Checking first matters because a post that can't be recorded as Posted would be published again on the next run.

### Check the publish skill version

Before posting anything, if the publish skill's `metadata.contract` is readable, compare it with this skill's `requires-contract`. If it is lower, stop with "{skill} contract {found} is older than required {required}" and post nothing. If it is equal or higher, continue. If it can't be read, continue and apply the result checks in Step 4c instead.

### 2. Find the rows

Query for rows matching all three conditions:
- `Platform` = `{platform}`
- `Persona` = `{persona}`
- `Status` = `Ready to Post`

Sort by created time, oldest first. Follow pagination until every matching row is collected.

If no rows match, finish with: `No posts ready for {persona}.`

### 3. Skip rows that must not be posted

Before posting, set aside rows that could produce a duplicate post. Report each one as skipped with its reason, and don't change it:
- `Post URL` is already filled. The row was probably posted before, but the status update failed.
- `Error` starts with `[UNKNOWN_OUTCOME]`. An earlier attempt may have gone out. A human must check the platform and clear the Error before the row is eligible again.

### 4. Post each remaining row, one at a time, in order

**a. Read the text.**
- Read the text only from property `Formatted Copy` and no other text property. If it is a formula type, use its string result.
- Keep line breaks. If the Notion tool encodes them as `<br>` tags, convert each `<br>` to a newline before posting; this is decoding the tool's output, not editing the copy.
- If a segment is a hyperlink whose URL doesn't appear in its visible text, post the visible text anyway, but add a warning for that row in the summary: the platform will not carry hidden links.

**b. Post it.** Call the publish skill with `{text}` (plus `dry_run: true` when this run is a dry run). Do not edit, shorten or clean up the copy; the publish skill will reject it if it's invalid.

**c. Write the result back to the row.** Check the result before using it (see [references/x-publish-usage.md](references/x-publish-usage.md)): if its shape is unusable, record `[OTHER]` on the row and continue; treat an unrecognised `error_code` as `OTHER`; never stop the run because of a version difference except as the version check before Step 2 describes. In a dry run, write nothing to Notion; record the result for the summary instead.
- **`ok: true`:** set `Status` = `Posted`, `Post URL` = the returned `url`, and clear `Error`.
- **`ok: false`:** leave `Status` unchanged. Set `Error` to `[{error_code}] {message} ({timestamp in UTC, ISO 8601})`, for example `[TOO_LONG] Text is 312 characters by X counting; limit is 280. (2026-09-24T10:15:00Z)`. The bracketed code at the start lets people filter on it, and step 3 relies on it.

**d. If the Notion update fails after a successful post,** try the update once more; writing to Notion is safe to repeat. If it still fails, list the row under "posted but not recorded" in the summary, with its post URL. That row will be posted again on the next run unless someone fixes it, so it must be impossible to miss.

**e. Decide whether to continue.**
- On `AUTH`, `RATE_LIMIT` or `NO_TOOL`, stop the run. Every later row would fail the same way. Report the remaining rows as not attempted and leave them untouched.
- On any other error, record it and continue with the next row.

### Dry run

With `dry_run: true`, run Steps 1 to 3 and Step 4a and 4b as normal, but the publish skill only validates and locates its tool. Write nothing to Notion. The summary replaces `Posted` with `Would post ({n})` and lists each row's `weighted_length` and the platform tool the publish skill reported. `Failed` lists rows the publish skill would reject. This checks the database, the row selection, the text handling and both tool lookups without side effects.

### 5. Report

End with this summary. It is the run's output, so keep it plain and complete:

```
Post queue — platform: {platform}, persona: {persona}
Posted ({n}):
- {row title} → {url}
Failed ({n}):
- {row title}: [{error_code}] {message}
Skipped ({n}):
- {row title}: {reason}
Not attempted ({n}): {reason the run stopped}
- {row title}
Posted but not recorded in Notion ({n}):   ← only if any; needs manual fix
- {row title} → {url}
Warnings:
- {row title}: {warning}
```

Omit sections that are empty, except `Posted`. Use the row's title property as `{row title}`, or the page ID if the title is empty.

## Rules

- Never mark a row `Posted` or write a `Post URL` unless the publish skill returned `ok: true` without `dry_run`.
- Never write to Notion in a dry run.
- Never touch rows for other platforms, personas or statuses.
- Never ask questions. This skill runs on a schedule, so every problem becomes an Error on the row or a line in the summary.
- The account used is whichever connection to the platform the running user has authenticated in the session. The `persona` input selects rows only; it does not choose the account.
