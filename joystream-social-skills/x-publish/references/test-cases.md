# x-publish test cases

Use a test X account. Run `x-publish` directly with `{text}` (or with `dry_run: true` where noted) and check the returned JSON. The scripts have automated tests too: `python3 -m unittest discover -s scripts -p 'test_*.py'`.

1. A plain short post. Expect `ok: true` and a `url`.
2. A post containing a long `https://` URL. It should count the URL as 23 characters and post.
3. 281 plain characters. Expect `TOO_LONG`, and no tool call.
4. Emojis and a line break. It should post with the line break intact, each emoji counted as 2.
5. Whitespace-only text. Expect `EMPTY`, and no tool call.
6. Post #1's exact text again. Expect `DUPLICATE`.
7. Disconnect X. Expect `AUTH`.
8. Account with no API credits (HTTP 402). Expect `RATE_LIMIT`.
9. Remove or disable the X tool. Expect `NO_TOOL`.
10. `dry_run: true` with valid text. Expect `ok: true`, `dry_run: true`, `weighted_length` and the tool name, and nothing posted.
11. `dry_run: true` with no X tool. Expect `NO_TOOL`.
12. A platform whose X tool has a different name. Use `dry_run` first and check the reported tool name.
