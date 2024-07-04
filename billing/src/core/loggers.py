import sys

LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line}" " - {message}"
)

STDOUT_LOGGER = {
    "sink": sys.stdout,
    "level": "TRACE",
    "colorize": True,
    "format": (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level: <8}"
        " | <level>{name}:{function}:{line} - {message}</level>"
    ),
}

TRACE_FILE_LOGGER = {
    "sink": "logs/trace/trace.log",
    "level": "TRACE",
    "format": LOG_FORMAT,
    "serialize": True,
    "backtrace": False,
    "diagnose": False,
    "enqueue": True,
    "rotation": "21:00",
    "retention": "10 days",
    "compression": "zip",
}

ERROR_FILE_LOGGER = {
    "sink": "logs/error/error.log",
    "level": "ERROR",
    "format": LOG_FORMAT,
    "serialize": True,
    "backtrace": True,
    "diagnose": False,
    "enqueue": True,
    "rotation": "21:00",
    "retention": "10 days",
    "compression": "zip",
}
