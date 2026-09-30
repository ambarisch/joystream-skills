# linkedin-publish contract (version 1)

This skill implements the same contract as `x-publish` (version 1), so a caller can swap between them. This file restates it so the skill is self-contained. If the two ever differ, `x-publish/references/contract.md` is the reference for the shared parts, and any difference must be additive (see Versioning).

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
{"contract": 1, "ok": true, "url": "https://www.linkedin.com/feed/update/urn:li:share:1234567890/", "post_urn": "urn:li:share:1234567890", "weighted_length": 142}
```

Dry run success (nothing was posted):
```json
{"contract": 1, "ok": true, "dry_run": true, "weighted_length": 142, "tool": "<name of the tool that would be used>"}
```

Failure:
```json
{"contract": 1, "ok": false, "error_code": "TOO_LONG", "message": "Text is 3120 characters; limit is 3000.", "weighted_length": 3120}
```

Optional fields: `weighted_length` (whenever computed; for LinkedIn this is the conservative character count), `count_method` (`"manual"` if the script could not run), `post_urn` (LinkedIn's post identifier; `x-publish` returns `tweet_id` instead).

## Guarantees

- One call posts at most once. There is no automatic retry.
- The text is never modified.
- `ok: true` without `dry_run` means the posting tool returned a post identifier or URL. `url` and `post_urn` come from that response, never guessed.
- `dry_run: true` never posts, in any code path.
- `UNKNOWN_OUTCOME` means the post **may** have gone out. Do not re-post until a human checks LinkedIn.
- The skill never asks questions.

## Versioning

`contract` is a single integer, incremented when the contract grows. Changes must be additive only: new output fields, new error codes, new optional inputs. A breaking change (renamed or removed fields, changed meaning) must be released as a new skill, not as a higher number.

A caller declares the minimum version it needs (`requires-contract` in its frontmatter). It stops only if the callee's version is **lower** than that minimum. Equal or higher versions are compatible.

Version history:
- 1: `text`, `dry_run`; results as above; codes `EMPTY`, `TOO_LONG`, `NO_TOOL`, `AUTH`, `RATE_LIMIT`, `DUPLICATE`, `FORBIDDEN`, `UNKNOWN_OUTCOME`, `OTHER`.

## Error codes

See [error-codes.md](error-codes.md). Callers must treat any code they do not recognise as `OTHER`, and ignore fields they do not recognise.

## What `notion-post-queue` relies on

Reads `contract`, `ok`, `url`, `error_code`, `message`. Stops the whole run on `AUTH`, `RATE_LIMIT` and `NO_TOOL`. Holds the row on `UNKNOWN_OUTCOME`.
