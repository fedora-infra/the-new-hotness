# Setup fedmsg logging.
# See the following for constraints on this format http://bit.ly/Xn1WDn
bare_format = "[%(asctime)s][%(name)10s %(levelname)7s] %(message)s"

config = dict(
    logging=dict(
        version=1,
        disable_existing_loggers=False,
        # The root logger configuration; this is a catch-all configuration
        # that applies to all log messages not handled by a different logger
        root={"level": "INFO", "handlers": ["console"]},
        formatters=dict(bare={"datefmt": "%Y-%m-%d %H:%M:%S", "format": bare_format}),
        handlers=dict(
            console={
                "class": "logging.StreamHandler",
                "formatter": "bare",
                "level": "INFO",
                "stream": "ext://sys.stdout",
            }
        ),
        loggers=dict(
            fedmsg={"level": "INFO", "propagate": False, "handlers": ["console"]},
            moksha={"level": "INFO", "propagate": False, "handlers": ["console"]},
            root={"level": "INFO", "propagate": False, "handlers": ["console"]},
        ),
    )
)
