#!/usr/bin/env python3
"""
Limittery dashboard — full ASCII display of Claude Code rate-limit usage.

Reads the cache written by statusline/statusline.py and renders a detailed
box-drawing dashboard. Run via the /limittery skill inside Claude Code.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

# ── Config ─────────────────────────────────────────────────────────────────────

CACHE_PATH = os.path.join(os.path.expanduser("~"), ".claude", "limittery-cache.json")
BOX_WIDTH  = 38   # inner width (between box walls)
BAR_WIDTH  = 20
STALE_SECS = 300  # warn if cache older than 5 minutes

# ── ANSI colours ───────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
DIM    = "\033[2m"

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

USE_COLOR = _supports_color()

def c(code: str, text: str) -> str:
    return f"{code}{text}{RESET}" if USE_COLOR else text

def color_for(pct: float) -> str:
    if pct > 80:
        return RED
    if pct > 50:
        return YELLOW
    return GREEN

# ── Bar ────────────────────────────────────────────────────────────────────────

FILLED = "\u2588"  # █
EMPTY  = "\u2591"  # ░

def make_bar(pct: float, width: int = BAR_WIDTH) -> str:
    pct    = max(0.0, min(100.0, pct))
    filled = round(pct / 100 * width)
    bar    = FILLED * filled + EMPTY * (width - filled)
    return c(color_for(pct), bar)

# ── Time helpers ───────────────────────────────────────────────────────────────

def format_countdown(resets_at) -> str:
    """resets_at is Unix epoch seconds (int or float)."""
    try:
        now   = datetime.now(timezone.utc)
        reset = datetime.fromtimestamp(float(resets_at), tz=timezone.utc)
        secs  = int((reset - now).total_seconds())
        if secs <= 0:
            return "resetting now"
        days,  rem  = divmod(secs, 86400)
        hours, rem  = divmod(rem,  3600)
        minutes     = rem // 60
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    except Exception:
        return "unknown"

def format_reset_clock(resets_at) -> str:
    try:
        reset    = datetime.fromtimestamp(float(resets_at), tz=timezone.utc)
        local_dt = reset.astimezone()
        return local_dt.strftime("%H:%M %Z, %d %b")
    except Exception:
        return "?"

# ── Box drawing ────────────────────────────────────────────────────────────────

W = BOX_WIDTH

def box_top()  -> str: return "\u2554" + "\u2550" * W + "\u2557"
def box_mid()  -> str: return "\u2560" + "\u2550" * W + "\u2563"
def box_bot()  -> str: return "\u255a" + "\u2550" * W + "\u255d"

def box_row(text: str) -> str:
    plain = re.sub(r"\033\[[0-9;]*m", "", text)
    pad   = W - len(plain)
    return "\u2551 " + text + " " * max(0, pad - 2) + " \u2551"

def box_title(text: str) -> str:
    pad   = W - len(text)
    left  = pad // 2
    right = pad - left
    return "\u2551" + " " * left + (c(BOLD, text) if USE_COLOR else text) + " " * right + "\u2551"

# ── Render a single window section ────────────────────────────────────────────

def render_window(label: str, info: dict) -> list:
    pct       = float(info.get("used_percentage", 0.0))
    resets_at = info.get("resets_at", 0)
    remaining = 100.0 - pct

    lines = [
        box_row(c(BOLD, label)),
        box_row(make_bar(pct)),
        box_row(c(color_for(pct), f"{pct:.1f}%") + " used  \u2022  " + c(color_for(pct), f"{remaining:.1f}%") + " remaining"),
        box_row(f"Resets in: {format_countdown(resets_at)}"),
        box_row(c(DIM, f"At: {format_reset_clock(resets_at)}")),
    ]
    return lines

# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    if not os.path.exists(CACHE_PATH):
        print("No data yet. Make sure the statusline is configured and Claude Code")
        print("has refreshed at least once (refreshInterval in settings.json).")
        print(f"\nCache path: {CACHE_PATH}")
        sys.exit(0)

    try:
        with open(CACHE_PATH, encoding="utf-8") as fh:
            cache = json.load(fh)
    except Exception as exc:
        print(f"Could not read cache: {exc}")
        sys.exit(1)

    # Staleness warning
    stale_warning = ""
    cached_at_str = cache.get("cached_at", "")
    if cached_at_str:
        try:
            cached_at = datetime.fromisoformat(cached_at_str)
            age       = (datetime.now(timezone.utc) - cached_at).total_seconds()
            if age > STALE_SECS:
                stale_warning = f"(data is {int(age // 60)}m old — waiting for next refresh)"
        except Exception:
            pass

    rate_limits = cache.get("rate_limits", {})

    rows = [box_top(), box_title("LIMITTERY \u2014 Rate Limit Monitor")]

    windows = [
        ("5-Hour Window", rate_limits.get("five_hour", {})),
        ("7-Day Window",  rate_limits.get("seven_day", {})),
    ]

    for label, info in windows:
        rows.append(box_mid())
        rows.extend(render_window(label, info))

    rows.append(box_bot())

    if stale_warning:
        rows.append(c(DIM, stale_warning))

    print("\n".join(rows))


if __name__ == "__main__":
    main()
