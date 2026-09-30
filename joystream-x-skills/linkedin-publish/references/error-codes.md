# linkedin-publish error codes

| Code | Meaning | Post went out? | What the caller should usually do |
|---|---|---|---|
| `EMPTY` | Text missing or only whitespace | No | Fix the copy |
| `TOO_LONG` | Over 3000 characters (from the script or from LinkedIn) | No | Shorten the copy |
| `NO_TOOL` | No tool in this session can create a LinkedIn post | No | Stop; the environment needs a LinkedIn connector |
| `AUTH` | Connector not connected, or token expired/revoked (LinkedIn tokens expire) | No | Stop; the user must reconnect LinkedIn |
| `RATE_LIMIT` | 429 / throttled / daily or application limit reached | No | Stop; try again on a later run |
| `DUPLICATE` | LinkedIn rejected identical recent content | No | Human review |
| `FORBIDDEN` | 403: missing permission (for example the post-writing scope), or account restricted | No | Human review |
| `UNKNOWN_OUTCOME` | Timeout, dropped connection, 5xx | **Maybe** | Do NOT re-post until a human checks LinkedIn |
| `OTHER` | Anything else | No | Human review |

`NO_TOOL` is raised by the skill itself when tool discovery fails; it is never produced by classifying a tool error.

Classification order when done manually: `DUPLICATE`, `RATE_LIMIT`, `AUTH`, `FORBIDDEN`, `TOO_LONG`, `UNKNOWN_OUTCOME`, `OTHER`. `DUPLICATE` precedes `FORBIDDEN` because duplicates can arrive as a 4xx that also mentions permissions.
