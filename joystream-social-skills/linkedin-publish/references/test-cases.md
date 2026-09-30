# linkedin-publish test cases

Use a test LinkedIn profile. Run `linkedin-publish` directly with `{text}` (or with `dry_run: true` where noted) and check the returned JSON. The scripts have automated tests too: `python3 -m unittest discover -s scripts -p 'test_*.py'`.

1. `dry_run: true` with valid text. Expect `ok: true`, `dry_run: true`, `weighted_length` and the tool name, and nothing posted. Do this first: it shows which tool was picked and what its schema requires.
2. `dry_run: true` with no LinkedIn tool. Expect `NO_TOOL`.
3. A plain short post. Expect `ok: true`, a `url` of the form `https://www.linkedin.com/feed/update/urn:li:.../`, and a `post_urn`.
4. A post with a URL, emoji and line breaks. It should post with line breaks intact.
5. A post with markup-like characters, such as `(test) [x] @name #tag *bold* _it_`. Check that it appears on LinkedIn exactly as written. If not, note the tool's escaping behaviour in `references/tool-hints.md`.
6. 3001 plain characters. Expect `TOO_LONG`, and no tool call.
7. Whitespace-only text. Expect `EMPTY`, and no tool call.
8. Post #3's exact text again. Expect `DUPLICATE` if LinkedIn rejects it; if LinkedIn accepts it, record that here.
9. Disconnect LinkedIn. Expect `AUTH`.
10. A tool that requires an author. Expect the skill to resolve it from the own-profile action (a `urn:li:person:` value), never an organization, and to post as you.
11. A tool that requires some other field the session cannot supply, or an own-profile lookup that fails. Expect `OTHER` naming what is missing, and no post.
12. A session that only has a tool gateway. Dry run: expect the create-post action to be found by search and its schema read, with the executor never called. Live: expect one execution of the create-post action only.
13. Gateway with no active LinkedIn connection. Expect `NO_TOOL`.
