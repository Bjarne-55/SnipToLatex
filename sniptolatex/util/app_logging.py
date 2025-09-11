"""Lightweight application logging helpers.

Captures errors that occur off the main thread (e.g., during model requests)
without introducing heavy dependencies. Logs are written to a predictable
per-user location depending on the OS.

Locations
- Windows: %LOCALAPPDATA%\SnipToLatex\Logs\app.log
- macOS:   ~/Library/Logs/SnipToLatex/app.log
- Linux:   $XDG_STATE_HOME/SnipToLatex/Logs/app.log (defaults to
           ~/.local/state/SnipToLatex/Logs/app.log)
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import sys
import traceback
from typing import Optional


def default_log_dir() -> Path:
    """Return the default directory for app logs based on the platform.

    Returns:
        Path: Directory path that should contain the log file.
    """
    if sys.platform.startswith("win"):
        # Prefer %LOCALAPPDATA% (e.g., C:\Users\<user>\AppData\Local)
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            base = str(Path.home() / "AppData" / "Local")
        return Path(base) / "SnipToLatex" / "Logs"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "SnipToLatex"
    # Linux and others — use XDG state directory
    base = os.environ.get("XDG_STATE_HOME")
    if not base:
        base = str(Path.home() / ".local" / "state")
    return Path(base) / "SnipToLatex" / "Logs"


def append_log(message: str, exc: Optional[BaseException] = None) -> None:
    """Append a log entry to the default log file.

    The function never raises; any failures are silently ignored to avoid
    breaking the user experience.

    Args:
        message: Summary line for the log entry.
        exc: Optional exception to include with traceback.
    """
    try:
        log_dir = default_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "app.log"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {message}\n")
            if exc is not None:
                fh.write("Exception: " + repr(exc) + "\n")
                tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                fh.write(tb + "\n")
    except Exception:
        # Never propagate logging failures
        pass
