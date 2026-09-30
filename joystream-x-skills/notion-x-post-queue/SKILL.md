---
name: notion-x-post-queue
description: Publish every "Ready to Post" Twitter row for a given persona from a Notion content database to X, then write the result back to each row (Status "Posted" plus Post URL on success, or an Error description on failure). Use this skill whenever an agent needs to work through a Notion posting queue, publish scheduled or approved social posts for a persona to X/Twitter, or sync X post results back into Notion. Requires the x-publish skill for the actual posting.
compatibility: Requires Notion tools in the session (MCP connector or equivalent) that can read a database schema, query rows and update pages, plus the x-publish skill (which needs an X posting tool).
metadata:
  version: "1.1.0"
  author: JoyStream
  depends-on: x-publish
  requires-contract: "1"   # minimum x-publish contract version needed
---

# Notion → X Post Queue

For one persona, find every row in a Notion database that is ready to go to X, publish each one, and record the outcome on the row.

Notion is the shared state between agents and people: a person or an upstream agent marks rows "Ready to Post", and this skill turns them into live posts. Each row's end state must truthfully reflect what happened on X, because other agents and people act on it.

## Inputs

- `database_url` (required): URL or ID of the Notion database.
- `persona` (required): the persona whose posts to publish. Must exactly match the row's `Persona` value (case-sensitive).
- `dry_run` (optional boolean, default false): do everything except posting and writing to Notion. See Dry run below.

If `database_url` or `persona` is missing or empty, stop immediately with an error. Don't guess a database or persona.

## Required capabilities

**Notion, three capabilities.** Choose tools by matching their descriptions and schemas to these, not by name (examples in [references/tool-hints.md](references/tool-hints.md), which are hints only):

1. Fetch a database's schema: property names, types and select/status options.
2. Query rows with filters and sort, following pagination.
3. Update a page's properties.

Prefer tools acting as the running user. Do not call Notion's HTTP API or any other route directly. If any of the three is missing, stop with `NO_TOOL: Notion tool for {capability} is not available` and post nothing.

**x-publish skill.** Used for every post. Do not call an X tool directly from this skill: x-publish owns validation, tool discovery, the post call and error codes. It must implement contract version 1 or higher ([x-publish/references/contract.md](../x-publish/references/contract.md); what this skill uses is summarised in [references/x-publish-usage.md](references/x-publish-usage.md)). Any skill, sub-agent or inline procedure that honours that contract can stand in. If none is available, stop and report "x-publish skill is required".

## Database contract

| Property | Expected type | Read / write |
|---|---|---|
| `Platform` | Select | Read. Must equal `Twitter` |
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

### Check the x-publish version

Before posting anything, if the `x-publish` skill's `metadata.contract` is readable, compare it with this skill's `requires-contract`. If it is lower, stop with "x-publish contract {found} is older than required {required}" and post nothing. If it is equal or higher, continue. If it can't be read, continue and apply the result checks in Step 4c instead.

### 2. Find the rows

Query for rows matching all three conditions:
- `Platform` = `Twitter`
- `Persona` = `{persona}`
- `Status` = `Ready to Post`

Sort by created time, oldest first. Follow pagination until every matching row is collected.

If no rows match, finish with: `No posts ready for {persona}.`

### 3. Skip rows that must not be posted

Before posting, set aside rows that could produce a duplicate post. Report each one as skipped with its reason, and don't change it:
- `Post URL` is already filled. The row was probably posted before, but the status update failed.
- `Error` starts with `[UNKNOWN_OUTCOME]`. An earlier attempt may have gone out. A human must check X and clear the Error before the row is eligible again.

### 4. Post each remaining row, one at a time, in order

**a. Read the text.**
- Read the text only from property `Formatted Copy` and no other text property. If it is a formula type, use its string result.
- Keep line breaks.
- If a segment is a hyperlink whose URL doesn't appear in its visible text, post the visible text anyway, but add a warning for that row in the summary: X will not carry hidden links.

**b. Post it.** Call x-publish with `{text}` (plus `dry_run: true` when this run is a dry run). Do not edit, shorten or clean up the copy; x-publish will reject it if it's invalid.

**c. Write the result back to the row.** Check the result before using it (see [references/x-publish-usage.md](references/x-publish-usage.md)): if its shape is unusable, record `[OTHER]` on the row and continue; treat an unrecognised `error_code` as `OTHER`; never stop the run because of a version difference except as the version check before Step 2 describes. In a dry run, write nothing to Notion; record the result for the summary instead.
- **`ok: true`:** set `Status` = `Posted`, `Post URL` = the returned `url`, and clear `Error`.
- **`ok: false`:** leave `Status` unchanged. Set `Error` to `[{error_code}] {message} ({timestamp in UTC, ISO 8601})`, for example `[TOO_LONG] Text is 312 characters by X counting; limit is 280. (2026-09-24T10:15:00Z)`. The bracketed code at the start lets people filter on it, and step 3 relies on it.

**d. If the Notion update fails after a successful post,** try the update once more; writing to Notion is safe to repeat. If it still fails, list the row under "posted but not recorded" in the summary, with its X URL. That row will be posted again on the next run unless someone fixes it, so it must be impossible to miss.

**e. Decide whether to continue.**
- On `AUTH`, `RATE_LIMIT` or `NO_TOOL`, stop the run. Every later row would fail the same way. Report the remaining rows as not attempted and leave them untouched.
- On any other error, record it and continue with the next row.

### Dry run

With `dry_run: true`, run Steps 1 to 3 and Step 4a and 4b as normal, but x-publish only validates and locates its tool. Write nothing to Notion. The summary replaces `Posted` with `Would post ({n})` and lists each row's `weighted_length` and the X tool x-publish reported. `Failed` lists rows x-publish would reject. This checks the database, the row selection, the text handling and both tool lookups without side effects.

### 5. Report

End with this summary. It is the run's output, so keep it plain and complete:

```
X post queue — persona: {persona}
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

- Never mark a row `Posted` or write a `Post URL` unless x-publish returned `ok: true` without `dry_run`.
- Never write to Notion in a dry run.
- Never touch rows for other platforms, personas or statuses.
- Never ask questions. This skill runs on a schedule, so every problem becomes an Error on the row or a line in the summary.
- The X account used is whichever X connection the running user has authenticated in the session. The `persona` input selects rows only; it does not choose the X account.
