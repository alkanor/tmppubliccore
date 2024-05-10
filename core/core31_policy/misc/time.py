from ...core11_config.config import register_config_default, config_dependencies, Config

from datetime import datetime
import enum


class DateFormat(enum.Enum):
    FULL_WITH_TIME = enum.auto()
    ONLY_NUMBERS = enum.auto()
    SHORT_TEXT = enum.auto()
    FULL_TEXT_WITH_TIME = enum.auto()

register_config_default('.misc.date_format', DateFormat, DateFormat.FULL_WITH_TIME)


@config_dependencies(('.misc.date_format', DateFormat))
def current_date(config: Config):
    now = datetime.now()
    if config['misc']['date_format'] == DateFormat.FULL_WITH_TIME:
        return now.strftime("%d/%m/%Y %H:%M:%S")
    elif config['misc']['date_format'] == DateFormat.ONLY_NUMBERS:
        return now.strftime("%d/%m/%Y")
    elif config['misc']['date_format'] == DateFormat.SHORT_TEXT:
        return now.strftime("%b-%d-%Y")
    elif config['misc']['date_format'] == DateFormat.FULL_TEXT_WITH_TIME:
        return now.strftime("%B %d, %Y - %H:%M:%S")
    else:
        raise NotImplementedError