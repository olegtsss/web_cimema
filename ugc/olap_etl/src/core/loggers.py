import logging

LOGGER_FORMAT = (
    "{time:DD-MM-YYYY at HH:mm:ss} | {level} | file: {file} |"
    " func: {function} | line: {line} | message: {message}"
)

LOGGER_COMMON_ARGS = {
    "diagnose": True,
    "rotation": "30 Mb",
    "retention": 3,
    "compression": "zip",
}

LOGGER_DEBUG = {
    "backtrace": False,
    "sink": "logs/debug/debug.log",
    "level": logging.DEBUG,
    "format": LOGGER_FORMAT,
} | LOGGER_COMMON_ARGS

LOGGER_ERROR = {
    "backtrace": True,
    "sink": "logs/error/error.log",
    "level": logging.ERROR,
    "format": LOGGER_FORMAT,
} | LOGGER_COMMON_ARGS
