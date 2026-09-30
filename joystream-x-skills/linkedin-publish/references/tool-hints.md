# Tool hints (non-binding)

`SKILL.md` selects the posting tool by capability. Names below are examples to make discovery quicker. Never require one, and prefer whatever the description says over a name match.

| Platform | Tool name seen | Notes |
|---|---|---|
| Generic MCP | names like `create_post`, `create_linkedin_post`, `linkedin_create_share`, `share_post` | Read the input schema first. Send only the field that holds the text. |

None have been tested yet. Add a row here after the first real run, including the tool's actual name and any required fields it had.

Response shapes to expect for the post id: a URN such as `urn:li:share:123` or `urn:li:ugcPost:123` in `id`, `data.id` or `post_urn`, an `x-restli-id` value, or a full post URL. The post URL is `https://www.linkedin.com/feed/update/{urn}/`.

Things to check on the first run (use `dry_run` first, then a test profile):
- **Required fields.** LinkedIn's API expects an author, a visibility and a lifecycle state. A good tool fills the author from the connected account. If the tool requires an author or organization id you cannot get from the session, the skill returns `OTHER`.
- **Escaping.** LinkedIn's post text field treats some characters (such as `( ) [ ] < > { } | @ # * _ ~ \`) as markup. Some tools escape them for you, some don't. Check that a post containing them appears as written, and add the result here.
- **Token expiry.** LinkedIn access tokens expire (about 60 days), which shows up as `AUTH`.
- **Scope.** A missing post-writing permission shows up as `FORBIDDEN`.

Add a row here when a new platform is used. Do not change `SKILL.md` for that.
