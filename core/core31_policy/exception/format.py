from ...core11_config.config import Config, register_config_default, config_dependencies

from traceback import FrameSummary, StackSummary
from enum import Enum


class ExceptionFormat(Enum):
    DEFAULT = 1
    MINIMAL = 2
    ONE_LINE = 3
    KEEP_ARRAY = 4

register_config_default('.exception.format', ExceptionFormat, ExceptionFormat.DEFAULT)


def default_trace_line_formatting(trace_line: FrameSummary):
    return f"\tFile \"{trace_line.filename}\", line {trace_line.lineno}, in {trace_line.name}\n\t\t{trace_line.line}"

# this is like StackSummary.format (but we do not have a full exception available, so we fake it)
def default_trace_formatting(trace_lines: StackSummary, message: str):
    return 'Traceback:\n' + '\n'.join(map(default_trace_line_formatting, trace_lines)) + f"\n\tException: {message}"


#@register_policy('.exception.format_exception')
@config_dependencies(('.exception.format', ExceptionFormat))
def format_exception(config: Config, trace_lines: StackSummary, message: str):
    if config['exception']['format'] == ExceptionFormat.DEFAULT:
        return default_trace_formatting(trace_lines, message)
    else:
        raise NotImplementedError
