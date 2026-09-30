# Tool hints (non-binding)

`SKILL.md` selects the posting tool by capability. Names below are known examples to make discovery quicker. Never require one, and prefer whatever the description says over a name match.

| Platform | Tool name seen | Notes |
|---|---|---|
| JoyStream | `twitter.creation_of_a_post` | Send only the text field. |
| Local `xmcp` server (`xdevplatform/xmcp`) | `createPosts` | `text` is the body field; every other field is optional. A post has not yet succeeded here, so the success response shape is unseen (expect an id under `id` or `data.id`). Seen errors: `HTTP error 402: Payment Required ... credits depleted` (classified `RATE_LIMIT`) and `ECONNREFUSED: Unable to connect` when the local server is not running (classified `AUTH`). The server exposes many other tools (delete, follow, DMs); use only the create-post one. |
| Generic MCP | names like `create_tweet`, `create_post`, `post_tweet`, `x_create_post` | Read the input schema first. Send only the field that holds the text. |

Response shapes seen for the post id: `id`, `data.id`, `tweet_id`, or a post URL containing the id. If the response carries only a URL, take the numeric id from its last path segment.

Add a row here when a new platform is used. Do not change `SKILL.md` for that.
