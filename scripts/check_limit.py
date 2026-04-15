#!/usr/bin/env python3
"""
Limittery hook script — warns when the 5-hour rate limit exceeds the threshold.

Runs on the Stop event (see hooks/hooks.json).
Outputs a Claude Code hook JSON response only when a warning is needed;
exits silently otherwise so normal sessions aren't cluttered.
"""

import json
import os
import sys

CACHE_PATH      = os.path.join(os.path.expanduser("~"), ".claude", "limittery-cache.json")
WARN_THRESHOLD  = 80.0  # percent


def main() -> None:
    if not os.path.exists(CACHE_PATH):
        sys.exit(0)

    try:
        with open(CACHE_PATH, encoding="utf-8") as fh:
            cache = json.load(fh)
    except Exception:
        sys.exit(0)

    rate_limits = cache.get("rate_limits", {})
    five_hour   = rate_limits.get("five_hour", {})
    pct         = float(five_hour.get("used_percentage", 0.0))

    if pct < WARN_THRESHOLD:
        sys.exit(0)

    msg = (
        f"\u26a0\ufe0f  Limittery: 5-hour limit is at {pct:.0f}% "
        f"(threshold: {WARN_THRESHOLD:.0f}%). "
        "Consider pausing until it resets."
    )
    print(json.dumps({"continue": True, "suppressOutput": False, "systemMessage": msg}))


if __name__ == "__main__":
    main()
