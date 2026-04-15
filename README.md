# Limittery

Real-time rate-limit visualisation for [Claude Code](https://claude.ai/code).

Always-visible statusline showing your 5-hour and 7-day usage bars, current model, session cost, and elapsed time. Includes a `/limittery` command for a full ASCII dashboard.

```
5h ████████░░ 78% ↺42m  |  7d ███░░░░░░░ 28% ↺3d14h  |  Sonnet 4.6  |  $0.142  |  8m 03s
```

```
╔════════════════════════════════════════╗
║    LIMITTERY — Rate Limit Monitor      ║
╠════════════════════════════════════════╣
║ 5-Hour Window                          ║
║ ████████████████░░░░                   ║
║ 78.4% used  •  21.6% remaining         ║
║ Resets in: 42m                         ║
║ At: 18:00 UTC, 15 Apr                  ║
╠════════════════════════════════════════╣
║ 7-Day Window                           ║
║ ██████░░░░░░░░░░░░░░                   ║
║ 28.1% used  •  71.9% remaining         ║
║ Resets in: 3d 14h 6m                   ║
║ At: 00:00 UTC, 22 Apr                  ║
╚════════════════════════════════════════╝
```

**Requires Claude Code ≥ v2.1.109** and Python 3.7+.

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/leskoont/limittery ~/limittery

# 2. Run the installer — patches ~/.claude/settings.json automatically
python ~/limittery/scripts/install_statusline.py

# 3. Restart Claude Code
```

The statusline appears at the bottom of every session. Rate limit bars populate after the first API response.

### Options

```bash
# Change the refresh interval (default: 30 seconds)
python ~/limittery/scripts/install_statusline.py --refresh 60

# Remove limittery
python ~/limittery/scripts/install_statusline.py --uninstall
```

---

## Usage

| | |
|---|---|
| **Statusline** | Always visible at the bottom of Claude Code |
| **`/limittery`** | Full dashboard with exact percentages and reset times |
| **Warning** | Automatic message when the 5-hour window exceeds 80% |

### Colour coding

| Colour | Usage |
|--------|-------|
| Green  | ≤ 50% |
| Yellow | 51–80% |
| Red    | > 80% |

Set `NO_COLOR=1` to disable colours.

---

## License

MIT
