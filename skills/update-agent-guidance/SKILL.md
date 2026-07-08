---
name: update-agent-guidance
description: Turn human feedback about agent mistakes, missed expectations, review comments, or behavior that should have been incorporated earlier into concise AGENTS.md guidance. Use when asked to update, improve, or decide where to put agent instructions in a project AGENTS.md, global ~/.agents/AGENTS.md, or another explicitly named AGENTS.md-style guidance file.
---

# Update Agent Guidance

## Overview

Use this skill to convert feedback from a specific agent failure into durable, non-redundant guidance for future agents. The goal is the smallest instruction change that would have prevented the problem.

## Workflow

1. Read existing guidance before proposing or editing anything.
   - Read the current repo `AGENTS.md` when working inside a repository.
   - Read `~/.agents/AGENTS.md` when global guidance may apply.
   - Read any explicitly named shared guidance file before considering it.
   - Use terminal/file tools for local markdown; do not open local docs in a browser.

2. Identify the reusable lesson.
   - Extract the behavior the human expected the agent to apply earlier.
   - Ignore one-off preferences, task-specific facts, or corrections that only apply to the current artifact.
   - Prefer clarifying an existing principle over adding a new rule when the existing text already nearly covers the issue.

3. Recommend the target guidance file.
   - Use project `AGENTS.md` for repo-specific workflow, architecture, verification, domain rules, or project conventions.
   - Use global `~/.agents/AGENTS.md` for cross-repo agent behavior, general coding judgment, review discipline, or communication expectations.
   - Use an explicitly named guidance file when the human points to one, unless its existing scope clearly does not match the lesson.

4. Confirm the target and edit with the human before editing.
   - State the recommended file and why.
   - State the section or location to change.
   - Show the proposed wording or patch-level edit.
   - Mention the other plausible target only if there is a real tradeoff.
   - Do not edit any guidance file until the human confirms both the target file and the proposed change.

5. Make the smallest non-redundant update.
   - Add one concise bullet near the most relevant existing section, or revise an existing bullet if that avoids duplication.
   - Avoid broad checklists when a narrow rule is enough.
   - Preserve the file's tone and structure.
   - Do not update `README.md` unless the missing guidance affects normal human contributor setup, verification, or usage outside agent context.

6. Verify the result.
   - Re-read the changed section and check it does not duplicate nearby guidance.
   - Summarize the exact file changed and the behavior the new guidance is meant to prevent.

## Guidance Quality Bar

Good guidance is:

- Actionable before the mistake happens.
- General enough to help future tasks.
- Narrow enough not to burden unrelated work.
- Written as a rule or heuristic, not a postmortem of the original incident.

Avoid guidance that:

- Restates generic coding principles already present.
- Encodes the exact example instead of the reusable lesson.
- Removes useful engineering judgment by banning a defensible option.
