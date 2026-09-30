# Tool hints (non-binding)

`SKILL.md` selects Notion tools by capability. Names below are examples only; go by the tool descriptions and schemas.

| Capability | Typical MCP tool names | Watch for |
|---|---|---|
| Fetch database schema | `fetch`, `retrieve_database`, `get_database` | Newer workspaces expose rows through a data source; the query tool may want the data source id, not the database id. |
| Query rows | `query_database`, `query_data_source`, `search` | Filter syntax differs for `select`, `status` and `rich_text` properties. Results are paginated (`next_cursor`, `has_more`). |
| Update page properties | `update_page`, `update_properties`, `patch_page` | Property values must be in the shape for their type; see the table in `SKILL.md`. |

Add a row when a new platform is used. Do not change `SKILL.md` for that.
