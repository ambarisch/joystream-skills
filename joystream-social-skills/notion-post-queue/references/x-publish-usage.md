# How this skill calls the publish skill

The publish skill for a platform is chosen from the Publish skills table in `SKILL.md`; today that is `x-publish` for `Twitter`. The authoritative contract is `x-publish/references/contract.md`. This skill needs contract version **1 or higher** (`requires-contract` in its frontmatter). Summary of what it depends on:

- **Sends:** `{text, dry_run}`. `text` is exactly the `Formatted Copy` value; `dry_run` is passed through from this skill's input.
- **Reads:** `contract`, `ok`, `url`, `error_code`, `message`, `dry_run`. Ignores every other field.
- **Stopping for version:** stop only when the callee's version is lower than 1.
  - Preferred: before any post, read `metadata.contract` from `x-publish/SKILL.md`, if readable.
  - Otherwise: a result whose `contract` is present and lower than 1 stops the run, though the first row may already have been posted.
  - A result with no `contract` field is assumed compatible. Add a line to the summary's Warnings.
  - A higher version is always compatible.
- **Result shape check, per row** (in place of a strict version check):
  - `ok` must be a boolean.
  - When `ok` is true and this is not a dry run, `url` must be a non-empty string. Otherwise treat it as `[OTHER] x-publish returned success without a url`, and do not write `Posted`.
  - When `ok` is false, `error_code` and `message` must be present. Otherwise treat as `[OTHER]` with the raw result as the message.
  - An unrecognised `error_code` is treated as `OTHER`.
- **Dry run safety:** in a dry run, a result without `dry_run: true` means the callee may have posted for real (for example an older callee that ignores `dry_run`). Stop the run and say so in the summary.
- **Stops the run on:** `AUTH`, `RATE_LIMIT`, `NO_TOOL`.
- **Holds the row on:** `UNKNOWN_OUTCOME`, via the `[UNKNOWN_OUTCOME]` prefix in `Error`.
- **Invocation:** any mechanism that honours the contract (skill call, sub-agent, or following `x-publish/SKILL.md` inline).
