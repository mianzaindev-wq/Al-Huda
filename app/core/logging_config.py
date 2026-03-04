"""
core/logging_config.py
----------------------
Configures the root logger with a rotating file handler and a
console handler. Call setup_logging() exactly once at startup.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> None:
    """Set up rotating file + console logging for the whole application."""

    # Log file sits in the project root (parent of app/)
    project_root = Path(__file__).parent.parent.parent.resolve()
    log_file = str(project_root / "app.log")

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    # Rotate at 10 MB, keep 5 backups
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
