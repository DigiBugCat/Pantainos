"""
Generic logging configuration with color support and verbosity levels
"""

import logging
import sys

try:
    import colorlog

    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logging(*, debug: bool = False, verbose: bool = False, app_name: str | None = None) -> None:
    """
    Setup color-coded logging with appropriate verbosity levels.

    Args:
        debug: Enable DEBUG level for all loggers (most verbose)
        verbose: Enable DEBUG level for app only (medium verbosity)
        app_name: Application name for specific logger level setting
    """
    # Determine log level
    if debug:
        level = logging.DEBUG
        third_party_level = logging.DEBUG
    elif verbose:
        level = logging.DEBUG
        third_party_level = logging.INFO
    else:
        level = logging.INFO
        third_party_level = logging.WARNING

    # Create formatter
    if HAS_COLORLOG:
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Allow all levels, handlers will filter

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific app logger level if provided
    if app_name:
        logging.getLogger(app_name).setLevel(level)

    # Configure common third-party loggers to be less verbose
    third_party_loggers = [
        "httpx",
        "uvicorn",
        "fastapi",
        "websockets",
        "aiohttp",
        "twitchio",
    ]

    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(third_party_level)

    # Special handling for very noisy loggers
    if not debug:
        logging.getLogger("httpx._client").setLevel(logging.WARNING)
        logging.getLogger("websockets.protocol").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)
