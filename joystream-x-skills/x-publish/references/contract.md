# x-publish contract (version 1)

This is the single source of truth for how callers invoke `x-publish` and what they get back. Any skill, sub-agent or inline procedure that honours this contract can stand in for `x-publish`.

## Invocation

Any mechanism is fine (skill invocation, sub-agent, or reading `SKILL.md` and following it inline) as long as the input and output below are respected.

## Input

| Field | Type | Required | Meaning |
|---|---|---|---|
| `text` | string | yes | Finished post copy, line breaks preserved. Any link is already inside the text. |
| `dry_run` | boolean | no, default `false` | Validate the text and locate the posting tool, but do not post. |

## Output

Exactly one JSON object, never prose. `contract` (an integer) is always present and is the contract version this skill implements.

Success:
```json
{"contract": 1, "ok": true, "url": "https://x.com/i/web/status/1234567890", "tweet_id": "1234567890", "weighted_length": 142}
```

Dry run success (nothing was posted):
```json
{"contract": 1, "ok": true, "dry_run": true, "weighted_length": 142, "tool": "<name of the tool that would be used>"}
```

Failure:
```json
{"contract": 1, "ok": false, "error_code": "TOO_LONG", "message": "Text is 312 characters by X counting; limit is 280.", "weighted_length": 312}
```

Optional fields: `weighted_length` (whenever computed), `count_method` (`"manual"` if the script could not run).

## Guarantees

- One call posts at most once. There is no automatic retry.
- The text is never modified.
- `ok: true` without `dry_run` means the posting tool returned a post id. `url` and `tweet_id` come from that response, never guessed.
- `dry_run: true` never posts, in any code path.
- `UNKNOWN_OUTCOME` means the post **may** have gone out. Do not re-post until a human checks X.
- The skill never asks questions.

## Versioning

`contract` is a single integer, incremented when the contract grows. Changes must be additive only: new output fields, new error codes, new optional inputs. A breaking change (renamed or removed fields, changed meaning) must be released as a new skill, not as a higher number, so that a caller written for an older version keeps working.

A caller declares the minimum version it needs (`requires-contract` in its frontmatter). It stops only if the callee's version is **lower** than that minimum. Equal or higher versions are compatible.

Version history:
- 1: `text`, `dry_run`; results as above; codes `EMPTY`, `TOO_LONG`, `NO_TOOL`, `AUTH`, `RATE_LIMIT`, `DUPLICATE`, `FORBIDDEN`, `UNKNOWN_OUTCOME`, `OTHER`.

## Error codes

See [error-codes.md](error-codes.md). Callers must treat any code they do not recognise as `OTHER`, and ignore fields they do not recognise.

## What `notion-x-post-queue` relies on

Reads `contract`, `ok`, `url`, `error_code`, `message`. Stops the whole run on `AUTH`, `RATE_LIMIT` and `NO_TOOL`. Holds the row on `UNKNOWN_OUTCOME`.
