# joystream

Skill repository for the JoyStream agent library. Each collection is a folder of skills; each skill is a folder with a `SKILL.md` (YAML frontmatter with `name` and `description`, then instructions) and optional `scripts/`, `references/` and `assets/`.

| Collection | Skills |
|---|---|
| [joystream-social-skills](joystream-social-skills/) | `x-publish`, `linkedin-publish`, `notion-post-queue` |

## Import

Import this repo via git into JoyStream and attach the skills an agent needs. See each collection's README for dependencies and inputs.

## Adding a skill

- Directory name must equal the `name` in frontmatter (lowercase, hyphens, max 64 chars).
- `description` states what the skill does and when to use it (max 1024 chars).
- Keep `SKILL.md` under 500 lines; move detail to `references/`.
