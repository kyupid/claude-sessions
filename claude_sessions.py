#!/usr/bin/env python3
"""Claude Code Session Detector - Monitor and attach to Claude Code sessions."""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt


def get_home_path():
    """Get home directory path for shortening display."""
    return str(Path.home())


def get_claude_dir():
    """Get Claude config directory path."""
    return Path.home() / ".claude"


def shorten_path(path: str, max_length: int = 50) -> str:
    """Shorten path by replacing home dir with ~ and truncating if needed."""
    if path is None:
        return "N/A"

    home = get_home_path()
    if path.startswith(home):
        path = "~" + path[len(home):]

    if len(path) > max_length:
        return "..." + path[-(max_length - 3):]
    return path


def format_uptime(create_time: float) -> str:
    """Format process uptime as human readable string."""
    elapsed = time.time() - create_time

    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    minutes = int((elapsed % 3600) // 60)

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def format_time_ago(timestamp: datetime) -> str:
    """Format timestamp as human readable time ago string."""
    now = datetime.now()
    elapsed = (now - timestamp).total_seconds()

    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    minutes = int((elapsed % 3600) // 60)

    if days > 0:
        return f"{days}d ago"
    elif hours > 0:
        return f"{hours}h ago"
    elif minutes > 0:
        return f"{minutes}m ago"
    else:
        return "just now"


def get_status_style(status: str) -> tuple[str, str]:
    """Return status text and style based on process status."""
    status_map = {
        "running": ("Running", "green"),
        "sleeping": ("Idle", "yellow"),
        "disk-sleep": ("I/O Wait", "yellow"),
        "stopped": ("Stopped", "red"),
        "zombie": ("Zombie", "red"),
    }
    return status_map.get(status, (status.capitalize(), "white"))


def get_claude_sessions() -> list[dict]:
    """Find all running Claude Code CLI sessions."""
    sessions = []

    for proc in psutil.process_iter(['pid', 'cwd', 'terminal', 'create_time', 'status']):
        try:
            cmdline = proc.cmdline()
            # Claude Code CLI runs as node but cmdline[0] is 'claude'
            if cmdline and cmdline[0] == 'claude':
                info = proc.info
                sessions.append({
                    'pid': info['pid'],
                    'cwd': info['cwd'],
                    'terminal': info['terminal'] or 'N/A',
                    'create_time': info['create_time'],
                    'status': info['status'],
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort by PID
    sessions.sort(key=lambda x: x['pid'])
    return sessions


def get_saved_sessions() -> list[dict]:
    """Find all saved Claude Code sessions from ~/.claude/projects/."""
    sessions = []
    projects_dir = get_claude_dir() / "projects"

    if not projects_dir.exists():
        return sessions

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        # Decode project path from directory name
        project_path = project_dir.name.replace("-", "/")
        if project_path.startswith("/"):
            project_path = project_path  # Already absolute
        else:
            project_path = "/" + project_path

        for session_file in project_dir.glob("*.jsonl"):
            session_id = session_file.stem

            try:
                # Read first and last line to get metadata
                with open(session_file, 'r') as f:
                    first_line = f.readline().strip()
                    if not first_line:
                        continue

                    first_entry = json.loads(first_line)

                    # Get last line for last activity
                    f.seek(0, 2)  # Go to end
                    file_size = f.tell()

                    # Read last few KB to find last line
                    read_size = min(4096, file_size)
                    f.seek(max(0, file_size - read_size))
                    last_lines = f.read().strip().split('\n')
                    last_line = last_lines[-1] if last_lines else first_line
                    last_entry = json.loads(last_line)

                # Extract first user message as summary
                summary = ""
                if first_entry.get('type') == 'user':
                    content = first_entry.get('message', {}).get('content', '')
                    if isinstance(content, str):
                        summary = content[:50] + "..." if len(content) > 50 else content

                # Parse timestamps
                first_ts = datetime.fromisoformat(first_entry['timestamp'].replace('Z', '+00:00'))
                last_ts = datetime.fromisoformat(last_entry['timestamp'].replace('Z', '+00:00'))

                sessions.append({
                    'session_id': session_id,
                    'cwd': first_entry.get('cwd', project_path),
                    'created': first_ts.replace(tzinfo=None),
                    'last_activity': last_ts.replace(tzinfo=None),
                    'summary': summary,
                    'file_path': str(session_file),
                })
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    # Sort by last activity (most recent first)
    sessions.sort(key=lambda x: x['last_activity'], reverse=True)
    return sessions


def is_session_running(session_id: str) -> bool:
    """Check if a session is currently running."""
    for proc in psutil.process_iter(['cmdline']):
        try:
            cmdline = proc.cmdline()
            if cmdline and 'claude' in cmdline[0]:
                # Check if --resume with this session ID
                if '--resume' in cmdline or '-r' in cmdline:
                    for i, arg in enumerate(cmdline):
                        if arg in ('--resume', '-r') and i + 1 < len(cmdline):
                            if cmdline[i + 1] == session_id:
                                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def create_table(sessions: list[dict]) -> Table:
    """Create a rich Table displaying session information."""
    table = Table(
        title="Claude Code Sessions",
        title_style="bold cyan",
        header_style="bold white",
        border_style="blue",
        show_lines=False,
    )

    table.add_column("PID", justify="right", style="cyan", width=8)
    table.add_column("Directory", style="white", min_width=30)
    table.add_column("Terminal", justify="center", style="magenta", width=12)
    table.add_column("Uptime", justify="right", style="green", width=10)
    table.add_column("Status", justify="center", width=10)

    for session in sessions:
        status_text, status_style = get_status_style(session['status'])

        table.add_row(
            str(session['pid']),
            shorten_path(session['cwd']),
            session['terminal'].replace('/dev/', ''),
            format_uptime(session['create_time']),
            Text(status_text, style=status_style),
        )

    return table


def create_saved_sessions_table(sessions: list[dict]) -> Table:
    """Create a rich Table displaying saved sessions."""
    table = Table(
        title="Saved Sessions",
        title_style="bold cyan",
        header_style="bold white",
        border_style="blue",
        show_lines=False,
    )

    table.add_column("#", justify="right", style="dim", width=3)
    table.add_column("Session ID", style="cyan", width=12)
    table.add_column("Directory", style="white", min_width=25)
    table.add_column("Last Active", justify="right", style="green", width=10)
    table.add_column("Summary", style="dim", max_width=30)

    for i, session in enumerate(sessions, 1):
        table.add_row(
            str(i),
            session['session_id'][:8] + "...",
            shorten_path(session['cwd'], 25),
            format_time_ago(session['last_activity']),
            session['summary'] or "-",
        )

    return table


def create_display(sessions: list[dict]) -> Panel:
    """Create the full display panel."""
    if not sessions:
        content = Text("No active Claude Code sessions", style="dim italic", justify="center")
    else:
        content = create_table(sessions)

    return Panel(
        content,
        title=f"[bold blue]Session Monitor[/bold blue] [dim]({len(sessions)} active)[/dim]",
        subtitle=f"[dim]Updated: {datetime.now().strftime('%H:%M:%S')} | Press Ctrl+C to exit[/dim]",
        border_style="blue",
    )


def cmd_monitor(args):
    """Monitor running Claude Code sessions."""
    console = Console()

    console.clear()
    console.print("[bold cyan]Claude Code Session Detector[/bold cyan]")
    console.print("[dim]Monitoring sessions every 3 seconds...[/dim]\n")

    try:
        with Live(create_display([]), console=console, refresh_per_second=0.5) as live:
            while True:
                sessions = get_claude_sessions()
                live.update(create_display(sessions))
                time.sleep(3)
    except KeyboardInterrupt:
        console.print("\n[dim]Monitoring stopped.[/dim]")


def cmd_list(args):
    """List all saved sessions."""
    console = Console()
    sessions = get_saved_sessions()

    if not sessions:
        console.print("[yellow]No saved sessions found.[/yellow]")
        return

    # Limit display
    limit = args.limit if hasattr(args, 'limit') and args.limit else 20
    display_sessions = sessions[:limit]

    table = create_saved_sessions_table(display_sessions)
    console.print(table)

    if len(sessions) > limit:
        console.print(f"[dim]... and {len(sessions) - limit} more sessions[/dim]")

    console.print(f"\n[dim]Use 'claude-sessions attach <number>' to resume a session[/dim]")


def cmd_attach(args):
    """Attach to a saved session."""
    console = Console()
    sessions = get_saved_sessions()

    if not sessions:
        console.print("[yellow]No saved sessions found.[/yellow]")
        return

    # If session ID/number provided
    if args.session:
        session_id = args.session

        # Check if it's a number (index)
        if session_id.isdigit():
            idx = int(session_id) - 1
            if 0 <= idx < len(sessions):
                session_id = sessions[idx]['session_id']
            else:
                console.print(f"[red]Invalid session number. Use 1-{len(sessions)}[/red]")
                return

        # Find session by ID (partial match)
        target_session = None
        for s in sessions:
            if s['session_id'].startswith(session_id):
                target_session = s
                break

        if not target_session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

    else:
        # Interactive selection
        table = create_saved_sessions_table(sessions[:20])
        console.print(table)
        console.print()

        try:
            choice = Prompt.ask(
                "[bold]Select session number[/bold]",
                default="1"
            )

            if not choice.isdigit():
                console.print("[red]Invalid selection[/red]")
                return

            idx = int(choice) - 1
            if not (0 <= idx < len(sessions)):
                console.print(f"[red]Invalid session number. Use 1-{min(20, len(sessions))}[/red]")
                return

            target_session = sessions[idx]

        except KeyboardInterrupt:
            console.print("\n[dim]Cancelled.[/dim]")
            return

    # Attach to session
    session_id = target_session['session_id']
    cwd = target_session['cwd']

    console.print(f"\n[green]Resuming session:[/green] {session_id[:8]}...")
    console.print(f"[dim]Directory: {cwd}[/dim]")
    console.print()

    # Change to session directory and run claude --resume
    try:
        os.chdir(cwd)
    except (FileNotFoundError, PermissionError):
        console.print(f"[yellow]Warning: Could not change to {cwd}, using current directory[/yellow]")

    # Execute claude --resume
    os.execlp("claude", "claude", "--resume", session_id)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="claude-sessions",
        description="Monitor and manage Claude Code sessions"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # monitor command (default)
    monitor_parser = subparsers.add_parser("monitor", help="Monitor running sessions (default)")
    monitor_parser.set_defaults(func=cmd_monitor)

    # list command
    list_parser = subparsers.add_parser("list", aliases=["ls"], help="List saved sessions")
    list_parser.add_argument("-n", "--limit", type=int, default=20, help="Max sessions to show")
    list_parser.set_defaults(func=cmd_list)

    # attach command
    attach_parser = subparsers.add_parser("attach", aliases=["a"], help="Attach to a saved session")
    attach_parser.add_argument("session", nargs="?", help="Session number or ID")
    attach_parser.set_defaults(func=cmd_attach)

    args = parser.parse_args()

    # Default to monitor if no command
    if args.command is None:
        args.func = cmd_monitor
        cmd_monitor(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
