"""Structured logging setup using structlog.

Local development gets human-friendly console output; other environments emit
JSON lines suitable for log aggregation. Helpers here are also where LLM usage
(tokens, cost, latency) is logged from the agent layer.
"""

import logging
import sys
from typing import cast

import structlog

_PROCESSORS_SHARED: list[structlog.types.Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
]


def configure_logging(log_level: str = "INFO", *, json_logs: bool = False) -> None:
    """Configure structlog + stdlib logging once at application startup."""
    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*_PROCESSORS_SHARED, structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping().get(log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
