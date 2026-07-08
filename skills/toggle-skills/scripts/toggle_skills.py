#!/usr/bin/env python3
"""Discover, preview, and toggle skills for the current agent runtime only."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Protocol

EXCLUDED_PATH_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
}
UNSUPPORTED_EXIT = 3


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path
    groups: frozenset[str] = field(default_factory=frozenset)


class AgentAdapter(Protocol):
    key: str
    display_name: str
    supports_apply: bool

    def default_config_path(self) -> Path | None: ...

    def discover_skills(self) -> list[Skill]: ...

    def group_summary(self, skills: Iterable[Skill], config_path: Path | None) -> list[dict[str, object]]: ...

    def plan(self, action: str, targets: list[Skill], config_path: Path | None) -> dict[str, object]: ...

    def apply(self, payload: dict[str, object], config_path: Path | None) -> None: ...


def skill_name(skill_md: Path) -> str:
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return skill_md.parent.name
    match = re.match(r"---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return skill_md.parent.name
    name_match = re.search(r"^name:\s*([^\n#]+)", match.group(1), re.MULTILINE)
    return name_match.group(1).strip().strip('"\'') if name_match else skill_md.parent.name


def is_discoverable_skill_path(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    for part in parts:
        if part in EXCLUDED_PATH_PARTS:
            return False
        if part.startswith(".") and part != ".system":
            return False
    return True


def resolve_targets(skills: list[Skill], group: str | None, all_skills: bool) -> list[Skill]:
    if all_skills:
        return skills
    if not group:
        raise SystemExit("Provide --group GROUP or --all.")
    keys = sorted({candidate for skill in skills for candidate in skill.groups})
    exact = [key for key in keys if key.lower() == group.lower()]
    if exact:
        key = exact[0]
        return [skill for skill in skills if key in skill.groups]
    partial = [key for key in keys if group.lower() in key.lower()]
    if len(partial) == 1:
        key = partial[0]
        return [skill for skill in skills if key in skill.groups]
    if partial:
        print("Multiple groups match. Choose one of:", file=sys.stderr)
        for key in partial:
            print(f"  {key}", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(f"No group matches: {group}")


def unsupported_payload(adapter: AgentAdapter, command: str) -> dict[str, object]:
    return {
        "agent": adapter.key,
        "agent_display_name": adapter.display_name,
        "supported": False,
        "command": command,
        "message": (
            f"{adapter.display_name} skill toggling is not supported because no safe "
            "local per-skill enablement config surface was detected."
        ),
    }


def load_source_groups(home: Path) -> dict[Path, set[str]]:
    groups: dict[Path, set[str]] = {}
    lockfiles = [home / ".agents/.skill-lock.json", home / ".agents/skills/skills-lock.json"]
    for lockfile in lockfiles:
        if not lockfile.exists():
            continue
        try:
            data = json.loads(lockfile.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for name, meta in data.get("skills", {}).items():
            if not isinstance(meta, dict):
                continue
            path = home / ".agents/skills" / name / "SKILL.md"
            source = meta.get("source")
            if source:
                groups.setdefault(path.resolve(), set()).add(str(source))
    return groups


def plugin_group(path: Path, home: Path) -> str | None:
    cache = home / ".codex/plugins/cache"
    try:
        rel = path.resolve().relative_to(cache.resolve())
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0] if parts else None


def codex_location_groups(path: Path, home: Path) -> set[str]:
    out: set[str] = set()
    roots = [home / ".agents/skills", home / ".codex/skills"]
    for root in roots:
        try:
            rel = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        if rel.parts:
            out.add(rel.parts[0])
        return out
    group = plugin_group(path, home)
    if group:
        out.add(group)
        out.add(group.split("/")[-1].split("@")[0])
    return out


def parse_codex_config(config_path: Path) -> dict[str, str]:
    if not config_path.exists():
        return {}
    lines = config_path.read_text(encoding="utf-8").splitlines()
    states: dict[str, str] = {}
    index = 0
    while index < len(lines):
        if lines[index].strip() != "[[skills.config]]":
            index += 1
            continue
        start = index
        index += 1
        while index < len(lines) and not lines[index].startswith("["):
            index += 1
        block = "\n".join(lines[start:index])
        path_match = re.search(r'^path\s*=\s*"([^"]+)"', block, re.MULTILINE)
        enabled_match = re.search(r"^enabled\s*=\s*(true|false)", block, re.MULTILINE)
        if path_match and enabled_match:
            states[path_match.group(1)] = enabled_match.group(1)
    return states


class CodexAdapter:
    key = "codex"
    display_name = "Codex"
    supports_apply = True

    def __init__(self, home: Path):
        self.home = home

    def default_config_path(self) -> Path:
        return self.home / ".codex/config.toml"

    def discover_skill_paths(self) -> set[Path]:
        paths: set[Path] = set()
        for root in [self.home / ".agents/skills", self.home / ".codex/skills"]:
            if root.exists():
                paths.update(
                    path.resolve()
                    for path in root.rglob("SKILL.md")
                    if is_discoverable_skill_path(path, root)
                )
        plugin_cache = self.home / ".codex/plugins/cache"
        if plugin_cache.exists():
            for skills_dir in plugin_cache.glob("*/*/skills"):
                if skills_dir.exists():
                    paths.update(
                        path.resolve()
                        for path in skills_dir.rglob("SKILL.md")
                        if is_discoverable_skill_path(path, skills_dir)
                    )
        return paths

    def discover_skills(self) -> list[Skill]:
        source_groups = load_source_groups(self.home)
        skills: list[Skill] = []
        for path in sorted(self.discover_skill_paths(), key=lambda item: str(item)):
            groups = set(source_groups.get(path.resolve(), set()))
            groups.update(codex_location_groups(path, self.home))
            if not groups:
                groups.add(str(path.parent))
            skills.append(Skill(name=skill_name(path), path=path, groups=frozenset(groups)))
        return skills

    def group_summary(self, skills: Iterable[Skill], config_path: Path | None) -> list[dict[str, object]]:
        if config_path is None:
            config_path = self.default_config_path()
        states = parse_codex_config(config_path)
        groups: dict[str, list[Skill]] = {}
        for skill in skills:
            for group in skill.groups:
                groups.setdefault(group, []).append(skill)
        rows = []
        for key, group_skills in sorted(groups.items(), key=lambda item: item[0].lower()):
            status = {"enabled": 0, "disabled": 0, "default": 0}
            for skill in group_skills:
                state = states.get(str(skill.path), "default")
                if state == "false":
                    status["disabled"] += 1
                elif state == "true":
                    status["enabled"] += 1
                else:
                    status["default"] += 1
            rows.append({
                "agent": self.key,
                "group": key,
                "count": len(group_skills),
                "enabled": status["enabled"],
                "disabled": status["disabled"],
                "default": status["default"],
                "sample": [skill.name for skill in group_skills[:5]],
            })
        return rows

    def plan(self, action: str, targets: list[Skill], config_path: Path | None) -> dict[str, object]:
        if config_path is None:
            config_path = self.default_config_path()
        states = parse_codex_config(config_path)
        desired = "false" if action == "disable" else "true"
        changes = []
        already = []
        for skill in targets:
            state = states.get(str(skill.path), "default")
            item = {"name": skill.name, "path": str(skill.path), "current": state, "desired": desired}
            if state == desired:
                already.append(item)
            else:
                changes.append(item)
        return {
            "agent": self.key,
            "agent_display_name": self.display_name,
            "supported": True,
            "action": action,
            "config": str(config_path),
            "total": len(targets),
            "change_count": len(changes),
            "already_count": len(already),
            "changes": changes,
            "already": already,
        }

    def apply(self, payload: dict[str, object], config_path: Path | None) -> None:
        if config_path is None:
            config_path = self.default_config_path()
        changes = payload["changes"]
        if config_path.exists():
            lines = config_path.read_text(encoding="utf-8").splitlines()
        else:
            lines = []
        desired_by_path = {item["path"]: item["desired"] for item in changes}
        seen: set[str] = set()
        index = 0
        while index < len(lines):
            if lines[index].strip() != "[[skills.config]]":
                index += 1
                continue
            start = index
            index += 1
            while index < len(lines) and not lines[index].startswith("["):
                index += 1
            end = index
            block = lines[start:end]
            path_line = next((line for line in block if line.strip().startswith("path")), None)
            if not path_line:
                continue
            path_match = re.search(r'"([^"]+)"', path_line)
            if not path_match:
                continue
            path = path_match.group(1)
            if path not in desired_by_path:
                continue
            desired = desired_by_path[path]
            seen.add(path)
            for offset, line in enumerate(block):
                if line.strip().startswith("enabled"):
                    lines[start + offset] = f"enabled = {desired}"
                    break
            else:
                lines.insert(end, f"enabled = {desired}")
                index += 1
        missing = [item for item in changes if item["path"] not in seen]
        if missing and lines and lines[-1] != "":
            lines.append("")
        for item in missing:
            lines.extend([
                "[[skills.config]]",
                f"path = \"{item['path']}\"",
                f"enabled = {item['desired']}",
                "",
            ])
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


class UnsupportedAgentAdapter:
    supports_apply = False

    def __init__(self, key: str, display_name: str, home: Path, roots: list[Path]):
        self.key = key
        self.display_name = display_name
        self.home = home
        self.roots = roots

    def default_config_path(self) -> Path | None:
        return None

    def discover_skills(self) -> list[Skill]:
        skills: list[Skill] = []
        for root in self.roots:
            if not root.exists():
                continue
            for path in sorted(root.rglob("SKILL.md"), key=lambda item: str(item)):
                if not is_discoverable_skill_path(path, root):
                    continue
                try:
                    rel = path.resolve().relative_to(root.resolve())
                    group = rel.parts[0] if rel.parts else str(path.parent)
                except ValueError:
                    group = str(path.parent)
                skills.append(Skill(name=skill_name(path), path=path.resolve(), groups=frozenset({group})))
        return skills

    def group_summary(self, skills: Iterable[Skill], config_path: Path | None) -> list[dict[str, object]]:
        rows = []
        groups: dict[str, list[Skill]] = {}
        for skill in skills:
            for group in skill.groups:
                groups.setdefault(group, []).append(skill)
        for key, group_skills in sorted(groups.items(), key=lambda item: item[0].lower()):
            rows.append({
                "agent": self.key,
                "group": key,
                "count": len(group_skills),
                "enabled": 0,
                "disabled": 0,
                "default": len(group_skills),
                "sample": [skill.name for skill in group_skills[:5]],
                "note": "apply unsupported; no safe enablement config detected",
            })
        if not rows:
            rows.append({
                "agent": self.key,
                "group": "diagnostics",
                "count": 0,
                "enabled": 0,
                "disabled": 0,
                "default": 0,
                "sample": [],
                "note": "no skill files or safe enablement config detected",
            })
        return rows

    def plan(self, action: str, targets: list[Skill], config_path: Path | None) -> dict[str, object]:
        payload = unsupported_payload(self, "plan")
        payload.update({"action": action, "total": len(targets), "change_count": 0, "changes": []})
        return payload

    def apply(self, payload: dict[str, object], config_path: Path | None) -> None:
        raise RuntimeError(payload["message"])


def detect_adapter(home: Path) -> AgentAdapter:
    override = os.environ.get("TOGGLE_SKILLS_AGENT", "").strip().lower()
    if override:
        return adapter_for_key(override, home)
    env = os.environ
    if any(key.startswith("CODEX_") for key in env) or env.get("CODEX_HOME"):
        return CodexAdapter(home)
    if any(key.startswith("CLAUDE") for key in env):
        return adapter_for_key("claude-code", home)
    if any(key.startswith("COPILOT") or key.startswith("GITHUB_COPILOT") for key in env):
        return adapter_for_key("copilot", home)
    if (home / ".codex/config.toml").exists():
        return CodexAdapter(home)
    return adapter_for_key("unknown", home)


def adapter_for_key(key: str, home: Path) -> AgentAdapter:
    if key in {"codex", "openai-codex"}:
        return CodexAdapter(home)
    if key in {"claude", "claude-code"}:
        return UnsupportedAgentAdapter("claude-code", "Claude Code", home, [home / ".claude/skills"])
    if key in {"copilot", "github-copilot"}:
        return UnsupportedAgentAdapter("copilot", "Copilot", home, [home / ".copilot/skills", home / ".config/github-copilot/skills"])
    return UnsupportedAgentAdapter("unknown", "Unknown agent", home, [])


def print_human_list(adapter: AgentAdapter, rows: list[dict[str, object]]) -> None:
    print(f"Agent: {adapter.display_name} ({adapter.key})")
    for row in rows:
        sample = ", ".join(row["sample"])
        note = f"\tnote={row['note']}" if row.get("note") else ""
        print(
            f"{row['group']}\tcount={row['count']}\t"
            f"enabled={row['enabled']} disabled={row['disabled']} default={row['default']}\t"
            f"sample={sample}{note}"
        )


def print_human_plan(payload: dict[str, object]) -> None:
    print(f"Agent: {payload['agent_display_name']} ({payload['agent']})")
    if not payload.get("supported", True):
        print(payload["message"])
        return
    print(f"Action: {payload['action']}")
    print(f"Config: {payload['config']}")
    print(f"Targets: {payload['total']} skills")
    print(f"Would change: {payload['change_count']}")
    print(f"Already desired state: {payload['already_count']}")
    for item in payload["changes"][:20]:
        print(f"  {item['name']}: {item['current']} -> {item['desired']}")
    if payload["change_count"] > 20:
        print(f"  ... {payload['change_count'] - 20} more")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None)
    parser.add_argument("--json", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--config", default=None)
    list_parser.add_argument("--json", action="store_true")

    for name in ["plan", "apply"]:
        sub = subparsers.add_parser(name)
        sub.add_argument("--config", default=None)
        sub.add_argument("--json", action="store_true")
        sub.add_argument("--action", choices=["enable", "disable"], required=True)
        target = sub.add_mutually_exclusive_group(required=True)
        target.add_argument("--group")
        target.add_argument("--all", action="store_true")

    args = parser.parse_args()
    home = Path.home()
    adapter = detect_adapter(home)
    config_arg = args.config or getattr(args, "config", None)
    config_path = Path(config_arg).expanduser() if config_arg else adapter.default_config_path()
    skills = adapter.discover_skills()

    if args.command == "list":
        rows = adapter.group_summary(skills, config_path)
        if args.json:
            print(json.dumps({"agent": adapter.key, "groups": rows}, indent=2))
        else:
            print_human_list(adapter, rows)
        return 0

    targets = resolve_targets(skills, args.group, args.all)
    payload = adapter.plan(args.action, targets, config_path)
    if args.command == "apply":
        if not adapter.supports_apply or not payload.get("supported", True):
            payload["command"] = "apply"
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print_human_plan(payload)
            return UNSUPPORTED_EXIT
        adapter.apply(payload, config_path)
        payload["applied"] = payload["change_count"]
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_human_plan(payload)
        if args.command == "apply":
            print(f"Applied: {payload['applied']}")
    if not payload.get("supported", True):
        return UNSUPPORTED_EXIT
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
