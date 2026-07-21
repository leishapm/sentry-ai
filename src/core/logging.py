import logging
from logging.config import dictConfig

from src.core.config import settings


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {
                "handlers": ["console"],
                "level": settings.log_level.upper(),
            },
            "loggers": {
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": settings.log_level.upper(),
                    "propagate": False,
                }
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

