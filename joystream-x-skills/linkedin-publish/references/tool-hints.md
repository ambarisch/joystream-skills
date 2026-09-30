# Tool hints (non-binding)

`SKILL.md` selects the posting tool by capability. Names below are examples to make discovery quicker. Never require one, and prefer whatever the description says over a name match.

| Platform | Tool name seen | Notes |
|---|---|---|
| Composio gateway (tested end to end) | Gateway tools `COMPOSIO_SEARCH_TOOLS`, `COMPOSIO_GET_TOOL_SCHEMAS`, `COMPOSIO_MULTI_EXECUTE_TOOL`; LinkedIn actions `LINKEDIN_CREATE_LINKED_IN_POST` (required: `author`, `commentary`) and `LINKEDIN_GET_MY_INFO` (no input) | Found by search, not direct tools. Run an action with `COMPOSIO_MULTI_EXECUTE_TOOL` using `tools: [{tool_slug, arguments}]` and the `session_id` the search returned. `LINKEDIN_GET_MY_INFO` returns the member id in `data.id` (a bare id), so build `urn:li:person:{id}`. `commentary` is the text field; visibility, lifecycle and distribution default to `PUBLIC`, `PUBLISHED`, main feed. The create-post response is `data.x_restli_id`, already a full URN such as `urn:li:share:7511...`, and `https://www.linkedin.com/feed/update/{urn}/` opened the real post. The search suggests `LINKEDIN_CREATE_ARTICLE_OR_URL_SHARE` as a fallback on HTTP 426; this skill does not use it. In a dry run, report the action slug as the `tool`. |
| Generic MCP | names like `create_post`, `create_linkedin_post`, `linkedin_create_share`, `share_post` | Read the input schema first. Send only the field that holds the text. |

Only the Composio row comes from a real session. Add or correct rows here after each first real run.

Response shapes to expect for the post id: a URN such as `urn:li:share:123` or `urn:li:ugcPost:123` in `id`, `data.id`, `post_urn`, `x_restli_id` or `data.x_restli_id`, or a full post URL. The post URL is `https://www.linkedin.com/feed/update/{urn}/`.

Things to check on the first run (use `dry_run` first, then a test profile):
- **Required fields.** LinkedIn's API expects an author, a visibility and a lifecycle state. If the tool wants an author, the skill builds it from the read-only own-profile action. If it needs an author or organization id that cannot be resolved that way, the skill returns `OTHER`.
- **Escaping.** LinkedIn's post text field treats some characters (such as `( ) [ ] < > { } | @ # * _ ~ \`) as markup. Some tools escape them for you, some don't. Check that a post containing them appears as written, and add the result here.
- **Token expiry.** LinkedIn access tokens expire (about 60 days), which shows up as `AUTH`.
- **Scope.** A missing post-writing permission shows up as `FORBIDDEN`.

Add a row here when a new platform is used. Do not change `SKILL.md` for that.
