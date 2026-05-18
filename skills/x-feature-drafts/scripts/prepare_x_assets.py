#!/usr/bin/env python3
"""Prepare temporary image attachments for X draft posts from a JSON manifest."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON manifest: {error}") from error
    if not isinstance(data, list):
        raise SystemExit("Manifest must be a JSON array")
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise SystemExit(f"Manifest item {index} must be an object")
        if not item.get("source") or not item.get("output"):
            raise SystemExit(f"Manifest item {index} requires source and output")
    return data


def build_command(item: dict[str, Any]) -> list[str]:
    command = ["magick", str(Path(item["source"]).expanduser())]
    if item.get("crop"):
        command.extend(["-crop", str(item["crop"])])
    if item.get("resize"):
        command.extend(["-resize", str(item["resize"])])
    if item.get("background"):
        command.extend(["-background", str(item["background"])])
    if item.get("gravity"):
        command.extend(["-gravity", str(item["gravity"])])
    if item.get("extent"):
        command.extend(["-extent", str(item["extent"])])
    command.append(str(Path(item["output"]).expanduser()))
    return command


def prepare_item(item: dict[str, Any], dry_run: bool) -> None:
    source = Path(item["source"]).expanduser()
    output = Path(item["output"]).expanduser()
    if not source.exists():
        raise SystemExit(f"Source does not exist: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = build_command(item)
    print(" ".join(command))
    if dry_run:
        return
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON manifest describing image crops")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without writing outputs")
    args = parser.parse_args()

    if shutil.which("magick") is None:
        raise SystemExit("ImageMagick 'magick' command was not found")

    for item in load_manifest(args.manifest):
        prepare_item(item, args.dry_run)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
