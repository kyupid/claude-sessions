# claude-sessions

Monitor all running Claude Code sessions in your terminal.

```
┌─────────────────────── Session Monitor (9 active) ───────────────────────┐
│                          Claude Code Sessions                            │
│ ┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┓ │
│ ┃      PID ┃ Directory                    ┃  Terminal  ┃ Uptime ┃ Status┃ │
│ ┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━┩ │
│ │    31781 │ ~/git/my-project             │  ttys000   │  5d 3h │  Idle │ │
│ │    56351 │ ~                            │  ttys005   │ 1h 24m │  Idle │ │
│ │    61185 │ ~/git/another-project        │  ttys011   │    40m │  Idle │ │
│ └──────────┴──────────────────────────────┴────────────┴────────┴───────┘ │
│                    Updated: 18:45:32 | Press Ctrl+C to exit              │
└──────────────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install claude-sessions
```

## Usage

```bash
claude-sessions
```

That's it! The monitor updates every 3 seconds. Press `Ctrl+C` to exit.

## Features

- Real-time monitoring of all Claude Code CLI sessions
- Shows PID, working directory, terminal, uptime, and status
- Auto-refreshes every 3 seconds
- Clean TUI with [rich](https://github.com/Textualize/rich)

## Requirements

- Python 3.10+
- macOS or Linux
- Claude Code CLI installed

## License

MIT
