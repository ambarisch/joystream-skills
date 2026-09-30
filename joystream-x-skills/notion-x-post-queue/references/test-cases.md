# Queue test rows to add before first real use

Use a test persona, a test Notion database and a test account on the platform. Platform-specific cases (length limits, counting, duplicates, credentials) live with the publish skill, for X in `x-publish/references/test-cases.md`. These cases cover the queue itself.

1. A valid `Ready to Post` row for the platform. Expect `Posted` + `Post URL`, and `Error` cleared.
2. A row whose `Formatted Copy` has line breaks. If the Notion tool returns `<br>`, the posted text should have real line breaks, not the tag.
3. A row with a different persona, a row for a different platform, and a row with Status `Draft`. None should be touched.
4. A row already holding a `Post URL`. It should be skipped and reported.
5. A row whose `Error` starts with `[UNKNOWN_OUTCOME]`. It should be skipped and reported.
6. A row the publish skill rejects (for example over the length limit). Expect `[CODE] message (timestamp)` in `Error`, status unchanged, and the run to continue with the next row.
7. Force `AUTH`, `RATE_LIMIT` or `NO_TOOL` on the first row (for example disconnect the platform). Expect the run to stop, later rows reported as not attempted and left untouched.
8. More matching rows than one page of results. Expect all of them to be processed.
9. `dry_run: true` over rows 1 to 5. Expect a `Would post` summary, and no change to any row.
10. Remove or disable the Notion update tool, then run. Expect `NO_TOOL` before anything is posted.
11. Remove a required property, or the `Posted` status option. Expect a stop naming exactly what is missing, before anything is posted.
12. Set `requires-contract` above the publish skill's `metadata.contract`. Expect the run to stop before posting anything.
13. `platform` set to a value not in the Publish skills table. Expect `NO_PUBLISHER` and nothing posted.
14. Run on a platform whose Notion tools are named differently. Use `dry_run` first and check the reported tool names.
