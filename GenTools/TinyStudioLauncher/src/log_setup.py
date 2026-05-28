"""Console logger with optional colorlog (stdlib fallback if missing)."""

import logging
import sys
from typing import Optional


def get_module_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(stream=sys.stdout)
    try:
        import colorlog

        handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
        )
    except ImportError:
        handler.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))

    stream: Optional[object] = handler.stream
    if stream is not None and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8")
        except (OSError, ValueError, AttributeError):
            pass

    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
