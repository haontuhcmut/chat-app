import logging
import logging.config


def setup_logging():
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": "INFO",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "loggers": {
                # Giữ log của uvicorn
                "uvicorn": {"level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"level": "INFO"},
                # App logger
                "app": {"level": "INFO"},
            },
        }
    )
