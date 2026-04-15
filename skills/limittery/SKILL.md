---
name: limittery
description: Show current Claude Code token rate-limit usage as a detailed ASCII dashboard with 5-hour and 7-day windows. Use when the user runs /limittery, asks about remaining quota, token usage, rate limits, or how much Claude Code usage is left.
argument-hint: ""
allowed-tools: [Bash]
---

Run the limittery dashboard to display the current token rate-limit usage.

Use Bash to execute the dashboard script:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/dashboard.py"
```

Display the full output exactly as returned — do not summarise or reformat it.

If the Bash command fails because python is not found, try `python3` instead.
