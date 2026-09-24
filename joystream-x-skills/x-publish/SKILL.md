---
name: x-publish
description: Publish one finished, text-only post to X (Twitter) through the JoyStream X/Twitter connector, with exact X character-count validation and normalized error codes. Returns the post URL on success or a stable error code plus description on failure. Use this skill whenever an agent needs to post, tweet, or publish copy to X/Twitter, including when posting is one step inside a larger workflow (e.g. publishing rows from a Notion content queue), so validation and error handling stay consistent across agents.
---

# X Publish

Publish exactly one text post to X as the account connected to the running user's X/Twitter connector, and return a predictable result.

This skill is a building block. It does not choose what to post, when to post, or whether copy is approved. The caller has already decided all of that. The job here is to post the text exactly as given, or explain precisely why it could not be posted.

## Input

- `text` (required): the finished post copy. Any link is already part of the text.

## Output

Always return exactly one of these JSON shapes. Callers branch on `ok` and `error_code`, so never return free-form prose instead.

Success:
```json
{"ok": true, "url": "https://x.com/i/web/status/1234567890", "tweet_id": "1234567890", "weighted_length": 142}
```

Failure:
```json
{"ok": false, "error_code": "TOO_LONG", "message": "Text is 312 characters by X counting; limit is 280.", "weighted_length": 312}
```

`weighted_length` is included whenever it was computed.

### Error codes

| Code | Meaning | Post went out? | What the caller should usually do |
|---|---|---|---|
| `EMPTY` | Text missing or only whitespace | No | Fix the copy |
| `TOO_LONG` | Over 280 by X counting (from the script or from X) | No | Shorten the copy |
| `AUTH` | Connector not connected, or token expired/revoked | No | Stop; the user must reconnect X |
| `RATE_LIMIT` | 429 / usage cap | No | Stop; try again on a later run |
| `DUPLICATE` | X rejected identical recent content | No | Human review |
| `FORBIDDEN` | Account suspended/locked or action not permitted | No | Human review |
| `UNKNOWN_OUTCOME` | Timeout, dropped connection, 5xx | **Maybe** | Do NOT re-post until a human checks X |
| `OTHER` | Anything else | No | Human review |

## Steps

### 1. Validate the text

If `text` is missing or only whitespace, return `EMPTY` without calling anything.

Otherwise, run the counter from this skill's folder:

```bash
python3 scripts/x_weighted_length.py --text "<text>"
```

For text containing quotes, backticks or `$`, write the text to a temporary file and pass `--file <path>` instead, so the shell doesn't alter it.

The script prints JSON with `weighted_length`, `valid` and `empty`. X's counting is not a plain character count: URLs count as 23, emojis count as 2, and CJK characters count as 2. That is why the script is used instead of estimating by eye.

- If `valid` is false and `empty` is true, return `EMPTY`.
- If `valid` is false otherwise, return `TOO_LONG` with a message like "Text is {weighted_length} characters by X counting; limit is 280."

If scripts cannot run in this environment, count manually using the rules in the script's header comment, and add `"count_method": "manual"` to the result.

Never shorten, reword, trim or "fix" the text to make it fit. Changing approved copy is the caller's decision, not this skill's.

### 2. Publish

Call the X connector's create-post action (in JoyStream: `twitter.creation_of_a_post`) with only the `text` field. Pass the text exactly as received, preserving line breaks. Do not set polls, media, reply settings or any other field.

Make one call only, with no automatic retry. A retry after an ambiguous failure is how duplicate posts happen.

### 3. Build the result

- **Success.** Take the post id from the action's response (usually `id`, sometimes `data.id`). Return `ok: true` with `url` = `https://x.com/i/web/status/{id}`. This URL works without knowing the account's handle.
  - If the action reports success but no id can be found, return `UNKNOWN_OUTCOME` with message "X reported success but returned no post id". Never construct or guess a URL.
- **Failure.** Classify the raw error:
  ```bash
  python3 scripts/classify_x_error.py --error "<raw error text or JSON>"
  ```
  Return `ok: false` with the `error_code` it gives. The `message` should be short and human-readable: include the HTTP status and X's own wording when available, e.g. "429 Too Many Requests: rate limit reached". If scripts cannot run, apply the table above in the order listed; `DUPLICATE` is checked before `FORBIDDEN` because X reports duplicates as a 403.

## Rules

- Never fabricate success, a post id or a URL.
- Never post more than once per invocation.
- Never ask the user questions. This skill runs inside unattended and scheduled agents, so missing or bad input becomes an error result.
- Use only the JoyStream connector for X. Do not call X's API or any other external service directly.
