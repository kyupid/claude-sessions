#!/usr/bin/env python3
"""Claude Code Session Detector - Monitor all running Claude Code sessions."""

import time
from datetime import datetime
from pathlib import Path

import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


def get_home_path():
    """Get home directory path for shortening display."""
    return str(Path.home())


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


def main():
    """Main entry point."""
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


if __name__ == "__main__":
    main()
