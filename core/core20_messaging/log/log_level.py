from ...core11_config.config import register_config_default

from enum import Enum
import logging


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


register_config_default('.log.log_level', LogLevel, LogLevel.INFO)
