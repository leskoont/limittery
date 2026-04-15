#!/usr/bin/env python3
"""
Limittery statusline script for Claude Code.

Claude Code pipes a JSON object to stdin; this script outputs a compact
rate-limit bar string to stdout and caches the data for the dashboard.

Actual JSON input format (Claude Code v2.1.109+):
{
  "rate_limits": {
    "five_hour": { "used_percentage": 78.4, "resets_at": 1776268297 },
    "seven_day":  { "used_percentage": 28.1, "resets_at": 1776787200 }
  }
}
Note: resets_at is Unix epoch seconds (not ISO string).
      Keys are five_hour / seven_day (not 5_hour / 7_day).

Example output:
  5h ████████░░ 78% ↺42m  |  7d ███░░░░░░░ 28% ↺3d14h
"""

import json
import sys
import os
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows (cp1251/cp1252 terminals can't encode block chars)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

# ── ANSI colour helpers ────────────────────────────────────────────────────────

RESET  = "\033[0m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

USE_COLOR = _supports_color()

def colorize(text: str, percentage: float) -> str:
    if not USE_COLOR:
        return text
    if percentage > 80:
        return f"{RED}{text}{RESET}"
    if percentage > 50:
        return f"{YELLOW}{text}{RESET}"
    return f"{GREEN}{text}{RESET}"

# ── Bar rendering ──────────────────────────────────────────────────────────────

BAR_WIDTH = 10
FILLED    = "\u2588"  # █
EMPTY     = "\u2591"  # ░

def make_bar(percentage: float, width: int = BAR_WIDTH) -> str:
    pct = max(0.0, min(100.0, percentage))
    filled = round(pct / 100 * width)
    return FILLED * filled + EMPTY * (width - filled)

# ── Reset countdown ────────────────────────────────────────────────────────────

def format_countdown(resets_at) -> str:
    """Return a compact human-readable time until reset, e.g. '42m' or '3d14h'.
    resets_at is Unix epoch seconds (integer or float).
    """
    try:
        now   = datetime.now(timezone.utc)
        reset = datetime.fromtimestamp(float(resets_at), tz=timezone.utc)
        secs  = int((reset - now).total_seconds())
        if secs <= 0:
            return "now"
        days,  rem  = divmod(secs, 86400)
        hours, rem  = divmod(rem,  3600)
        minutes     = rem // 60
        if days > 0:
            return f"{days}d{hours}h"
        if hours > 0:
            return f"{hours}h{minutes}m"
        return f"{minutes}m"
    except Exception:
        return "?"

# ── Cache ──────────────────────────────────────────────────────────────────────

CACHE_PATH = os.path.join(os.path.expanduser("~"), ".claude", "limittery-cache.json")

def write_cache(data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        payload = {
            "cached_at":   datetime.now(timezone.utc).isoformat(),
            "rate_limits": data,
        }
        with open(CACHE_PATH, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
    except Exception:
        pass

# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    rate_limits = payload.get("rate_limits", {})
    write_cache(rate_limits)

    windows = [
        ("five_hour", "5h"),
        ("seven_day",  "7d"),
    ]

    parts = []
    for key, label in windows:
        info = rate_limits.get(key)
        if info is None:
            continue
        pct  = float(info.get("used_percentage", 0.0))
        bar  = make_bar(pct)
        cd   = format_countdown(info.get("resets_at", 0))
        segment = f"{label} {bar} {pct:.0f}% \u21ba{cd}"
        parts.append(colorize(segment, pct))

    # Session info: model, cost, duration
    cost = payload.get("cost", {})
    cost_usd = cost.get("total_cost_usd")
    duration_ms = cost.get("total_duration_ms")
    model = payload.get("model", {}).get("display_name", "")

    if model:
        parts.append(model)
    if cost_usd is not None:
        parts.append(f"${cost_usd:.3f}")
    if duration_ms:
        secs = int(duration_ms / 1000)
        if secs < 60:
            parts.append(f"{secs}s")
        else:
            parts.append(f"{secs // 60}m {secs % 60:02d}s")

    if parts:
        print("  |  ".join(parts))
    else:
        print("limittery: waiting for data...")


if __name__ == "__main__":
    main()
