# JoyStream X Skills

Two standard Claude skills, portable across platforms (JoyStream, Claude Code, or anywhere with Notion and X tools).

| Skill | What it does | Depends on |
|---|---|---|
| `x-publish` | Publishes one text post to X, with exact X character counting and normalized error codes. Returns the post URL or `{error_code, message}`. | An X posting tool |
| `notion-x-post-queue` | Publishes every `Ready to Post` row for a persona and platform (default Twitter) from a Notion database, then writes back `Posted` + `Post URL`, or `Error`. | Notion tools, the platform's publish skill (`x-publish` for Twitter) |

Neither skill names a specific connector. Each states the capabilities it needs and picks whichever available tool provides them, acting as the running user. Known tool names per platform are in each skill's `references/tool-hints.md`. If no matching tool exists, the run stops with `NO_TOOL`. The scripts in `x-publish/scripts/` use only the Python 3 standard library: no packages are installed and no network calls are made.

## Import

Import this repo via git into JoyStream, then attach **both** skills to the agent that runs the queue. Use `notion-x-post-queue` as the entry skill; it calls `x-publish` for each post.

Agent inputs: `database_url`, `persona`, optional `platform` (default `Twitter`), optional `dry_run`. Triggers: manual or scheduled.

## Notion database requirements

- **Read:** `Platform` (the `platform` input, default `Twitter`), `Persona`, `Status` (`Ready to Post`), `Formatted Copy`.
- **Write:** `Status` (`Posted`), `Post URL` (URL type), `Error` (text type).

The skill checks all of these before posting anything, and stops with a clear error if any are missing.

## Contract between the skills

`notion-x-post-queue` calls `x-publish` needing contract version 1 or higher (stops only if the callee's version is lower): [x-publish/references/contract.md](x-publish/references/contract.md). Input `{text, dry_run}`; output a JSON object with `contract`, `ok`, and `url` or `error_code` + `message`.

## Dry run

Both skills accept `dry_run: true`. Nothing is posted and nothing is written to Notion; the result shows what would happen and which tools were found. Use it to check a new platform.

## Error codes (from x-publish)

- `EMPTY`
- `TOO_LONG`
- `NO_TOOL`
- `AUTH`
- `RATE_LIMIT`
- `DUPLICATE`
- `FORBIDDEN`
- `UNKNOWN_OUTCOME`
- `OTHER`

On failure, the row's `Error` column holds `[CODE] message (timestamp)`. `AUTH`, `RATE_LIMIT` and `NO_TOOL` stop the run.

Rows with `Error` starting with `[UNKNOWN_OUTCOME]` are held until a human checks X and clears the Error.

## Test rows

Queue behaviour: [notion-x-post-queue/references/test-cases.md](notion-x-post-queue/references/test-cases.md). Platform behaviour (X): [x-publish/references/test-cases.md](x-publish/references/test-cases.md).

## Tests

```bash
python3 -m unittest discover -s x-publish/scripts -p 'test_*.py'
```

## Script self-check

```bash
cd x-publish/scripts
python3 x_weighted_length.py --text "Hello 👋 https://example.com/some/long/path"   # weighted_length 32
python3 classify_x_error.py --error "429 Too Many Requests"                       # RATE_LIMIT
```
