"""
Centralized logging configuration for MedIntel AI.

Usage:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Processing started")
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "medintel", level: int | None = None) -> logging.Logger:
    """
    Configure and return a named logger with console and rotating file handlers.

    Args:
        name:  Logger namespace (e.g. 'medintel.pdf_service').
        level: Override log level; defaults to LOG_LEVEL env var or DEBUG.

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers on re-import
    if logger.handlers:
        return logger

    # Resolve level
    if level is None:
        env_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
        level = getattr(logging, env_level, logging.DEBUG)

    logger.setLevel(level)

    # ── Formatter ─────────────────────────────────────────────
    fmt = "%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    # ── Console handler (INFO+) ────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # ── File handler (DEBUG+) ──────────────────────────────────
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"medintel_{datetime.now().strftime('%Y%m%d')}.log"
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        # Non-fatal: log to console only if file creation fails (e.g. read-only FS)
        logger.warning(f"Could not create log file {log_file}: {e}")

    return logger


# Convenience alias so callers can do:
#   from src.utils.logger import get_logger
get_logger = setup_logger
