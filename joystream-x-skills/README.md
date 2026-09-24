# JoyStream X Skills

Two standard Claude skills for the JoyStream agent library.

| Skill | What it does | Depends on |
|---|---|---|
| `x-publish` | Publishes one text post to X, with exact X character counting and normalized error codes. Returns the post URL or `{error_code, message}`. | X/Twitter connector |
| `notion-x-post-queue` | Publishes every `Ready to Post` Twitter row for a persona from a Notion database, then writes back `Done` + `Post URL`, or `Error`. | Notion connector, `x-publish` |

Both skills use only JoyStream connectors, authenticated with each user's own credentials. The scripts in `x-publish/scripts/` use only the Python 3 standard library: no packages are installed and no network calls are made.

## Import

Import this repo via git into JoyStream, then attach **both** skills to the agent that runs the queue. Use `notion-x-post-queue` as the entry skill; it calls `x-publish` for each post.

Agent inputs: `database_url`, `persona`. Triggers: manual or scheduled.

## Notion database requirements

- **Read:** `Platform` (`Twitter`), `Persona`, `Status` (`Ready to Post`), `Formatted Copy`.
- **Write:** `Status` (`Done`), `Post URL` (URL type), `Error` (text type).

The skill checks all of these before posting anything, and stops with a clear error if any are missing.

## Error codes (from x-publish)

- `EMPTY`
- `TOO_LONG`
- `AUTH`
- `RATE_LIMIT`
- `DUPLICATE`
- `FORBIDDEN`
- `UNKNOWN_OUTCOME`
- `OTHER`

On failure, the row's `Error` column holds `[CODE] message (timestamp)`. `AUTH` and `RATE_LIMIT` stop the run.

Rows with `Error` starting with `[UNKNOWN_OUTCOME]` are held until a human checks X and clears the Error.

## Test rows to add before first real use

Use a test persona and a test X account:

1. A plain short post. Expect `Done` + `Post URL`.
2. A post containing a long `https://` URL. It should count the URL as 23 characters and post.
3. 281 plain characters. Expect `[TOO_LONG]`, status unchanged.
4. Emojis and a line break. It should post with line breaks intact.
5. A row with a different persona, and a row with Status `Draft`. Neither should be touched.
6. A row already holding a `Post URL`. It should be skipped.
7. Post #1's exact text again. Expect `[DUPLICATE]`.
8. Disconnect X, then run. Expect `[AUTH]` on the first row and the run to stop.

## Script self-check

```bash
cd x-publish/scripts
python3 x_weighted_length.py --text "Hello 👋 https://example.com/some/long/path"   # weighted_length 32
python3 classify_x_error.py --error "429 Too Many Requests"                       # RATE_LIMIT
```
