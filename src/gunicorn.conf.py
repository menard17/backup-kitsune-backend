import structlog
import sys

# gunicorn Logging Configuration
# gunicorn have a different set of logs, so we need to separately configure
# gunicorn logging to use structlog processors.
pre_chain = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]

if sys.stderr.isatty():
    custom_formatter = {
        "()": structlog.stdlib.ProcessorFormatter,
        "processor": structlog.dev.ConsoleRenderer(),
        "foreign_pre_chain": pre_chain,
    }
else:
    custom_formatter = {
        "()": structlog.stdlib.ProcessorFormatter,
        "processor": structlog.processors.JSONRenderer(),
        "foreign_pre_chain": pre_chain,
    }

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "INFO", "handlers": []},
    "formatters": {"custom_formatter": custom_formatter},
    "handlers": {
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "custom_formatter",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "custom_formatter",
        },
    },
    "loggers": {
        "gunicorn": {"level": "INFO", "propagate": False, "handlers": ["console"]}
    },
}
