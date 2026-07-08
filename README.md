# Skills

This repository contains local agent skills.

## Installation

Install all skills:

```sh
npx skills add doiyo/skills
```

Install one skill:

```sh
npx skills add doiyo/skills --skill x-feature-drafts
```

## Available Skills

### toggle-skills

Enables or disables skills by confirmed groups for the current agent only.

Use it when listing skill groups, disabling a whole installed bundle such as
marketing skills, or enabling/disabling a local skill family such as gstack. The
skill previews the exact current-agent config changes and requires confirmation
before editing any supported skill config.

Files:

- `skills/toggle-skills/SKILL.md`
- `skills/toggle-skills/scripts/toggle_skills.py`

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
