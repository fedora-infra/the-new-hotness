# Setup fedmsg logging.
# See the following for constraints on this format http://bit.ly/Xn1WDn
config = {
    "logging": {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "bare": {
                # Timestamps are not included by default as journald provides
                # them. If you want a timestamp, add '[%(asctime)s]' to the
                # format string.
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                "format": "[%(name)s %(levelname)s] %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "bare",
                "level": "DEBUG",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "fedmsg": {"level": "DEBUG", "propagate": False, "handlers": ["console"]},
            "fmn": {"level": "DEBUG", "propagate": False, "handlers": ["console"]},
            "hotness": {"level": "DEBUG", "propagate": False, "handlers": ["console"]},
            "moksha": {"level": "DEBUG", "propagate": False, "handlers": ["console"]},
            "rebasehelper": {
                "level": "DEBUG",
                "propagate": False,
                "handlers": ["console"],
            },
        },
        # The root logger configuration; this is a catch-all configuration
        # that applies to all log messages not handled by a different logger
        "root": {"level": "INFO", "handlers": ["console"]},
    }
}
