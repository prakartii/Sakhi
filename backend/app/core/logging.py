"""Application-wide logging configuration.

Call setup_logging() once at process startup (see app.main). Everything else
in the codebase should call get_logger(__name__) rather than configuring its
own handlers.
"""

import logging
import sys

from app.core.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def setup_logging() -> None:
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )
    # SQLAlchemy's own engine logger is separate from DB_ECHO's per-query
    # output; keep it quiet unless we're actively debugging SQL.
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
