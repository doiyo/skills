---
name: x-feature-drafts
description: Create X/Twitter draft posts for recent product or repository feature changes, optionally with existing screenshot attachments. Use when an agent needs to inspect recent commits or release notes, turn user-facing changes into concise X posts, crop existing screenshots into temporary upload assets, and save drafts through a logged-in Chrome/X browser session without publishing or scheduling.
---

# X Feature Drafts

## Overview

Use this skill to turn recent product changes into ready-to-review X drafts. Prefer grounded, repo-derived facts; keep the copy product-agnostic until the active repo or user context supplies product names, URLs, and voice.

## Workflow

1. Load local guidance before repository work. Read global agent guidance and the repo `AGENTS.md`/README or equivalent files with terminal tools, not a browser.
2. Establish the change window. Use the user-provided anchor, the latest X post, release notes, tags, or commit history to identify what changed after the last public update.
3. Inspect recent changes. Use `git log`, `git show --stat`, focused source reads, docs, screenshots, and product/site copy. Separate user-facing changes from internal-only maintenance.
4. Cluster 4-8 draft topics. Prefer concrete feature or behavior changes that can stand alone as posts. Merge tiny fixes into a broader polish/update post.
5. Draft copy. Use `references/post-style.md` for tone and structure. Infer product name, CTA URL, and voice from repo docs/site copy when available; otherwise ask only for high-impact missing information.
6. Prepare media. Use existing screenshots first. Crop or resize attachments into `/tmp`; do not overwrite repo assets. If repetitive cropping is needed, use `scripts/prepare_x_assets.py` with a manifest.
7. Save X drafts when browser access is available. Use the Chrome skill/plugin to claim the existing logged-in X tab or open X in the user profile. Create each draft, attach its media, confirm the preview/upload, close the composer, and save as draft.
8. Verify drafts. Open the X drafts list and confirm expected snippets and attached media are present.

## Safety Rules

- Never click Post, Publish, or Schedule unless the user explicitly asks in the same turn.
- Stop on login prompts, account prompts, rate limits, file-upload errors, missing save prompts, unclear draft state, or any publish/schedule ambiguity.
- Do not inspect cookies, passwords, profile storage, or browser session internals.
- Keep generated media in `/tmp` unless the user asks for saved artifacts elsewhere.
- If running outside an environment with browser-control and file-upload access, generate copy and temporary assets only; native X web drafts usually require an authenticated browser session and upload-capable browser tooling.

## Screenshot Asset Manifest

Use `scripts/prepare_x_assets.py` for repeatable image prep. The manifest is a JSON array:

```json
[
  {
    "source": "path/to/source.webp",
    "output": "/tmp/x-draft-feature.png",
    "crop": "720x720+0+80",
    "resize": "1200x1200",
    "extent": "1200x1200",
    "background": "white",
    "gravity": "center"
  }
]
```

Supported fields:

- `source` and `output` are required.
- `crop`, `resize`, and `extent` use ImageMagick geometry strings.
- `background` and `gravity` apply before `extent`.

## Browser Draft Procedure

- Open or claim the relevant X tab with the Chrome skill/plugin.
- Navigate to `https://x.com/compose/post`.
- Fill the post textbox, attach media through the file chooser, and wait for an image/media preview.
- Close the composer and choose the draft-saving option.
- After all drafts are created, open the drafts list and verify every expected post appears with media.
- Leave the drafts tab open for user review when useful.
