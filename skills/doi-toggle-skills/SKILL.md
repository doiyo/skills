---
name: doi-toggle-skills
description: Enable or disable skills for only the current agent runtime by confirmed groups. Use when the user asks to list, enable, disable, toggle, suppress, restore, or manage skills in the active agent, including requests like disable all marketing skills, enable Gmail skills, or disable all gstack skills at once.
---

# Doi Toggle Skills

## Overview

Use this skill to enable or disable skills for only the agent/runtime where the skill is invoked. Never toggle skills for other agents on the same machine as part of the ordinary workflow.

The helper script auto-detects the current agent. In Codex it can safely edit Codex `skills.config` entries. In Claude Code or Copilot, it must stay conservative: list diagnostics when possible and refuse `apply` unless that agent's local, documented enablement surface is known.

## Workflow

1. Discover current-agent groups with the helper script:

   ```bash
   python3 scripts/toggle_skills.py list
   ```

2. Match the user's request to groups for the current agent only.
   - Prefer groups derived from install source, such as `coreyhaines31/marketingskills`, when the request names a bundle or category.
   - Use location groups, such as `gstack`, when the request names a local skill directory or family.
   - If multiple plausible groups match, ask which group to change or whether to change all current-agent matches.
   - If the user says all skills, `--all` means all skills for the current agent only.

3. Preview the exact change before asking for confirmation:

   ```bash
   python3 scripts/toggle_skills.py plan --action disable --group GROUP_KEY
   python3 scripts/toggle_skills.py plan --action enable --group GROUP_KEY
   ```

4. Confirm with the user before mutation.
   - State the detected agent, action, group key, config path if writable, total skill count, and a short sample of affected skills.
   - Ask a direct confirmation question. Do not apply changes based only on inferred intent.

5. Apply only after confirmation and only if the detected agent supports safe writes:

   ```bash
   python3 scripts/toggle_skills.py apply --action disable --group GROUP_KEY
   python3 scripts/toggle_skills.py apply --action enable --group GROUP_KEY
   ```

6. Verify after applying.
   - Re-run the matching `plan` command and confirm the target count is already in the requested state.
   - Tell the user they may need to start a fresh session or reload skills before the active skill list updates.

## Safety Rules

- Current agent only. Do not toggle Codex, Claude Code, and Copilot together.
- Never delete skill folders or edit lockfiles for enable/disable requests.
- For Codex, edit only the configured Codex TOML file, defaulting to `~/.codex/config.toml`.
- Preserve existing config content and append missing `[[skills.config]]` blocks only when needed.
- For Claude Code and Copilot, refuse mutation unless the helper detects a safe local toggle surface.
- If writing outside the current workspace requires approval, request escalation for the apply command.
- Treat group names as selectors, not proof of intent: even when one group is obvious, confirm before applying.

## Helper Script

`toggle_skills.py` supports:

- `list`: print current-agent groups, counts, current enabled/disabled/default state, and sample skills.
- `plan --action enable|disable --group KEY`: dry-run the current-agent target set without changing files.
- `apply --action enable|disable --group KEY`: update current-agent config entries when supported.
- `--all`: target every discovered skill for the current agent only.
- `--json`: emit machine-readable output for precise summaries.
- `--config PATH`: use a non-default config path for Codex tests or unusual setups.

In Codex, the script groups skills by installed source from `~/.agents/.skill-lock.json` when available and by install location otherwise. This makes requests like disabling all marketing skills or all gstack skills work without hard-coded group names.
