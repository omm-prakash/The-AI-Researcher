"""
Centralized logging configuration for the agent project.

Usage in any module:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)

Logs are written to:
  - Console (stdout) with color-coded levels
  - storage/logs/agent.log  (rotating, 5 MB per file, 5 backups kept)
  - storage/logs/errors.log (ERROR+ only, same rotation policy)
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
# Resolve storage/logs relative to the project root (two levels up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOG_DIR = _PROJECT_ROOT / "storage" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_AGENT_LOG   = _LOG_DIR / "agent.log"
_ERROR_LOG   = _LOG_DIR / "errors.log"

# ── Formatters ───────────────────────────────────────────────────────────────
_FILE_FMT = logging.Formatter(
    fmt="%(asctime)s  %(levelname)-8s  %(name)-35s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_CONSOLE_FMT = logging.Formatter(
    fmt="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
    datefmt="%H:%M:%S",
)

# ── Handlers ─────────────────────────────────────────────────────────────────
def _make_rotating(path: Path, level: int) -> logging.handlers.RotatingFileHandler:
    handler = logging.handlers.RotatingFileHandler(
        filename=path,
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(_FILE_FMT)
    return handler


_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.DEBUG)
_console_handler.setFormatter(_CONSOLE_FMT)

_file_handler  = _make_rotating(_AGENT_LOG,  logging.DEBUG)
_error_handler = _make_rotating(_ERROR_LOG,  logging.ERROR)


# ── Root logger setup (called once at app startup) ───────────────────────────
def setup_logging(level: int = logging.DEBUG) -> None:
    """
    Call this once — ideally at the top of main.py — to configure the root
    logger for the entire application.
    """
    root = logging.getLogger()
    if root.handlers:
        return  # already configured (e.g. during testing)

    root.setLevel(level)
    root.addHandler(_console_handler)
    root.addHandler(_file_handler)
    root.addHandler(_error_handler)

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "groq", "google", "werkzeug", "watchfiles"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialised — agent.log + errors.log → %s", _LOG_DIR
    )


def get_logger(name: str) -> logging.Logger:
    """
    Convenience wrapper — identical to logging.getLogger() but documents
    the expected usage pattern.
    """
    return logging.getLogger(name)
