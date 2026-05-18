# Skills

This repository contains local agent skills.

## Available Skills

### update-agent-guidance

Turns feedback about agent mistakes or missed expectations into concise, durable
`AGENTS.md` guidance.

Use it when deciding whether feedback belongs in a project `AGENTS.md`, global
`~/.agents/AGENTS.md`, or another explicitly named guidance file. The skill
focuses on making the smallest non-redundant instruction change that would have
prevented the issue.

Files:

- `skills/update-agent-guidance/SKILL.md`

### x-feature-drafts

Creates ready-to-review X/Twitter draft posts from recent product or repository
changes.

Use it when turning recent commits, release notes, or product updates into
concise draft posts. The skill can inspect recent changes, draft post copy,
prepare screenshot attachments, and save drafts through an authenticated
Chrome/X session without publishing.

Files:

- `skills/x-feature-drafts/SKILL.md`
- `skills/x-feature-drafts/references/post-style.md`
- `skills/x-feature-drafts/scripts/prepare_x_assets.py`
