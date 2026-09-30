---
name: linkedin-publish
description: Publish one finished, text-only post to LinkedIn (the running user's own profile) through whichever LinkedIn tool is available in the session, with LinkedIn length validation and normalized error codes. Returns the post URL on success or a stable error code plus description on failure. Use this skill whenever an agent needs to post or publish copy to LinkedIn, including when posting is one step inside a larger workflow (e.g. publishing rows from a Notion content queue), so validation and error handling stay consistent across agents.
compatibility: Requires a tool in the session (MCP connector or equivalent) that can create a LinkedIn post as the running user. Python 3 (standard library only) is used for the bundled scripts, with a manual fallback.
metadata:
  version: "1.0.0"
  contract: "1"   # integer contract version implemented; see references/contract.md
  author: JoyStream
---

# LinkedIn Publish

Publish exactly one text post to LinkedIn as the profile the running user has connected, and return a predictable result.

This skill is a building block. It does not choose what to post, when to post, or whether copy is approved. The caller has already decided all of that. The job here is to post the text exactly as given, or explain precisely why it could not be posted.

It implements the same contract as `x-publish`, so a caller can use either one the same way.

## Required capability

**Create a text post on LinkedIn as the running user.** Nothing else is needed. Company pages and other organizations are out of scope: post to the user's own profile only.

Find the tool that provides it:
1. Look at the tools available in this session and choose the one whose description says it creates a post (share) on LinkedIn. Names vary by platform; go by the description and input schema. Known names are in [references/tool-hints.md](references/tool-hints.md) and are hints only.
2. Prefer a tool that acts as the running user's own connected account.
3. Do not call LinkedIn's HTTP API, scripts, browsers or any other route to post.
4. If no tool provides the capability, return `NO_TOOL` and stop. Do not try to work around it.

## Contract

Full schema, guarantees and versioning: [references/contract.md](references/contract.md). In brief:

- **Input:** `text` (required), `dry_run` (optional boolean, default false).
- **Output:** exactly one JSON object with `contract: 1`, and `ok: true` plus `url` and `post_urn`, or `ok: false` plus `error_code` and `message`. `weighted_length` is included whenever computed.
- **Dry run:** `{"contract": 1, "ok": true, "dry_run": true, "weighted_length": n, "tool": "<name>"}`. Nothing is posted.

Callers branch on `ok` and `error_code`, so never return free-form prose instead of the JSON.

### Error codes

See [references/error-codes.md](references/error-codes.md) for what each code means and what callers should do. Codes: `EMPTY`, `TOO_LONG`, `NO_TOOL`, `AUTH`, `RATE_LIMIT`, `DUPLICATE`, `FORBIDDEN`, `UNKNOWN_OUTCOME` (the post **may** have gone out; never re-post until a human checks LinkedIn), `OTHER`.

## Steps

### 1. Validate the text

If `text` is missing or only whitespace, return `EMPTY` without calling anything.

Otherwise, run the counter from this skill's folder:

```bash
python3 scripts/linkedin_length.py --text "<text>"
```

For text containing quotes, backticks or `$`, write the text to a temporary file and pass `--file <path>` instead, so the shell doesn't alter it.

The script prints JSON with `weighted_length`, `valid` and `empty`. It exits non-zero when the text is invalid, but the JSON is still printed; read the JSON rather than treating the exit code as a script failure. The limit is 3000 characters; the counting is deliberately conservative (see [references/counting-rules.md](references/counting-rules.md)).

- If `valid` is false and `empty` is true, return `EMPTY`.
- If `valid` is false otherwise, return `TOO_LONG` with a message like "Text is {weighted_length} characters; limit is 3000."

If scripts cannot run in this environment, count manually using the rules in [references/counting-rules.md](references/counting-rules.md), and add `"count_method": "manual"` to the result.

Never shorten, reword, trim or "fix" the text to make it fit. Changing approved copy is the caller's decision, not this skill's.

### 2. Publish

Find the posting tool as described under Required capability. Read its input schema before calling.

If `dry_run` is true, stop here: return the dry-run result with the chosen tool's name and the `weighted_length`. Do not call the tool.

Otherwise call the tool once, putting the text in the one field that carries the post body. Pass the text exactly as received, preserving line breaks. Do not escape or add markup unless the tool's own description says it requires it. Leave every optional field unset (media, articles, polls, reshares and so on).

Some tools require fields that only say the post is a normal public post. Those may be set to: visibility `PUBLIC`, lifecycle state `PUBLISHED`, and the feed distribution default. If the schema requires anything else that you cannot fill from `text` alone (an organization or author id, media, a title), return `OTHER` explaining what is required. Do not guess values.

Make one call only, with no automatic retry. A retry after an ambiguous failure is how duplicate posts happen.

### 3. Build the result

- **Success.** Take the post identifier from the tool's response: usually a URN such as `urn:li:share:123` or `urn:li:ugcPost:123` in `id` (sometimes `data.id`, `post_urn`, or an `x-restli-id` value). Return `ok: true` with `post_urn` = that URN and `url` = `https://www.linkedin.com/feed/update/{urn}/`.
  - If the tool returns a full post URL instead, use it as `url`, and use the URN from it if present.
  - If the action reports success but no identifier or URL can be found, return `UNKNOWN_OUTCOME` with message "Tool reported success but returned no post id". Never construct or guess a URL.
- **Failure.** Classify the raw error:
  ```bash
  python3 scripts/classify_linkedin_error.py --error "<raw error text or JSON>"
  ```
  Return `ok: false` with the `error_code` it gives. The `message` should be short and human-readable: include the HTTP status and LinkedIn's own wording when available, e.g. "429 Too Many Requests: daily limit reached". If scripts cannot run, apply the classification order in [references/error-codes.md](references/error-codes.md).

## Rules

- Never fabricate success, a post id or a URL.
- Never post more than once per invocation.
- Never ask the user questions. This skill runs inside unattended and scheduled agents, so missing or bad input becomes an error result.
- Use only tools the session provides for LinkedIn, chosen by capability. Do not call LinkedIn's API or any other external service directly.
- Post only to the running user's own profile, never to an organization page.
- `dry_run: true` never posts, on any path.
- Always include `contract: 1` in the result.
