from ...core11_config.parsing.set import check_and_parse_set_options
from ...core20_messaging.log.log_level import LogLevel


cli_string_transforms = {
    '.log_level': lambda v: getattr(LogLevel, v.upper()),
    '.log.log_level': lambda v: getattr(LogLevel, v.upper()),
    '.additional_options': lambda v: check_and_parse_set_options(v),
}
