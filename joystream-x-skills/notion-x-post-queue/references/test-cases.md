# Test rows to add before first real use

Use a test persona and a test X account:

1. A plain short post. Expect `Posted` + `Post URL`.
2. A post containing a long `https://` URL. It should count the URL as 23 characters and post.
3. 281 plain characters. Expect `[TOO_LONG]`, status unchanged.
4. Emojis and a line break. It should post with line breaks intact.
5. A row with a different persona, and a row with Status `Draft`. Neither should be touched.
6. A row already holding a `Post URL`. It should be skipped.
7. Post #1's exact text again. Expect `[DUPLICATE]`.
8. Disconnect X, then run. Expect `[AUTH]` on the first row and the run to stop.
