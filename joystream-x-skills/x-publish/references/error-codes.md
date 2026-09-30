# x-publish error codes

| Code | Meaning | Post went out? | What the caller should usually do |
|---|---|---|---|
| `EMPTY` | Text missing or only whitespace | No | Fix the copy |
| `TOO_LONG` | Over 280 by X counting (from the script or from X) | No | Shorten the copy |
| `NO_TOOL` | No tool in this session can create an X post | No | Stop; the environment needs an X connector |
| `AUTH` | Connector not connected, or token expired/revoked | No | Stop; the user must reconnect X |
| `RATE_LIMIT` | 429 / usage cap | No | Stop; try again on a later run |
| `DUPLICATE` | X rejected identical recent content | No | Human review |
| `FORBIDDEN` | Account suspended/locked or action not permitted | No | Human review |
| `UNKNOWN_OUTCOME` | Timeout, dropped connection, 5xx | **Maybe** | Do NOT re-post until a human checks X |
| `OTHER` | Anything else | No | Human review |

`NO_TOOL` is raised by the skill itself when tool discovery fails; it is never produced by classifying a tool error.

Classification order when done manually: `DUPLICATE`, `RATE_LIMIT`, `AUTH`, `FORBIDDEN`, `TOO_LONG`, `UNKNOWN_OUTCOME`, `OTHER`. `DUPLICATE` precedes `FORBIDDEN` because X reports duplicates as a 403.
