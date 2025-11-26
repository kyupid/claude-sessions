# claude-sessions

Monitor and attach to Claude Code sessions in your terminal.

![demo](demo.gif)

## Installation

```bash
pip install claude-sessions
```

## Usage

Just run:

```bash
claude-sessions
```

This opens an **interactive TUI** where you can:
- Browse all saved sessions with **arrow keys**
- **Enter** to attach to the selected session
- **r** to refresh the list
- **q** or **Esc** to quit

The list auto-refreshes every 3 seconds.

### Commands

```bash
# Interactive session browser (default)
claude-sessions

# Monitor running processes
claude-sessions monitor

# Attach directly by number or ID
claude-sessions attach 1
claude-sessions attach 64b1fd94
```

| Command | Alias | Description |
|---------|-------|-------------|
| (default) | | Interactive session browser |
| `monitor` | | Monitor running Claude processes |
| `list` | `ls` | Same as default |
| `attach` | `a` | Attach to a session by number/ID |

## Features

- Interactive TUI with keyboard navigation
- Real-time session list refresh
- Resume sessions with `claude --resume`
- Shows session ID, directory, last activity, and first message
- Fallback to simple list if textual is not installed

## Requirements

- Python 3.10+
- macOS or Linux
- Claude Code CLI installed

## License

MIT
