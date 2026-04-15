#!/usr/bin/env python3
"""
Limittery — statusline auto-installer.

Patches ~/.claude/settings.json to wire up the limittery statusline script
so you don't have to edit the file manually.

Usage:
    python scripts/install_statusline.py
    python scripts/install_statusline.py --refresh 60   # custom interval in seconds
    python scripts/install_statusline.py --uninstall
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def resolve_statusline_script() -> str:
    """Return the absolute path to statusline/statusline.py next to this script."""
    here   = Path(__file__).resolve().parent          # scripts/
    plugin = here.parent                               # plugin root
    script = plugin / "statusline" / "statusline.py"
    if not script.exists():
        print(f"ERROR: Could not find statusline script at {script}", file=sys.stderr)
        sys.exit(1)
    return str(script)


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            print(f"ERROR: {SETTINGS_PATH} is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(1)
    return {}


def save_settings(data: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Backup first
    if SETTINGS_PATH.exists():
        backup = SETTINGS_PATH.with_suffix(".json.bak")
        shutil.copy2(SETTINGS_PATH, backup)
        print(f"Backed up existing settings to {backup}")
    with open(SETTINGS_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def install(refresh: int) -> None:
    script   = resolve_statusline_script()
    python   = sys.executable  # use the same python that's running this script
    command  = f'"{python}" "{script}"'

    settings = load_settings()
    existing = settings.get("statusLine", {})

    if existing.get("command") == command and existing.get("refreshInterval") == refresh:
        print("Limittery statusline is already configured — nothing to do.")
        return

    settings["statusLine"] = {
        "type":            "command",
        "command":         command,
        "refreshInterval": refresh,
    }

    save_settings(settings)
    print(f"Installed limittery statusline:")
    print(f"  command:         {command}")
    print(f"  refreshInterval: {refresh}s")
    print()
    print("Restart Claude Code to activate.")


def uninstall() -> None:
    settings = load_settings()
    if "statusLine" not in settings:
        print("No statusLine entry found in settings.json — nothing to remove.")
        return
    del settings["statusLine"]
    save_settings(settings)
    print("Removed limittery statusline from settings.json.")
    print("Restart Claude Code to apply.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install or uninstall the limittery statusline for Claude Code."
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=30,
        metavar="SECONDS",
        help="How often Claude Code refreshes the statusline (default: 30)",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the limittery statusline from settings.json",
    )
    args = parser.parse_args()

    if args.uninstall:
        uninstall()
    else:
        install(args.refresh)


if __name__ == "__main__":
    main()
