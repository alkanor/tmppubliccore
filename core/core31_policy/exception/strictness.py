from ...core11_config.config import register_config_default, Config, config_dependencies
from ...core30_context.context_dependency_graph import context_dependencies
from ...core30_context.context import Context
from .format import format_exception

from logging import Logger
from enum import Enum
import traceback


class ExceptionLevel(Enum):
    IGNORE = 1  # don't produce anything else than a debug message
    LAX = 2     # at least produce some warning but keep going
    STRICT = 3  # raise the exception no matter what

register_config_default('.exception.level', ExceptionLevel, ExceptionLevel.LAX)


#@register_policy('.exception.raise_exception')
@config_dependencies(('.exception.level', ExceptionLevel))
@context_dependencies(('.log.main_logger', Logger), ('.log.debug_logger', Logger | None))
def raise_exception_from_string(ctxt: Context, config: Config, msg: str):
    if config['exception']['level'] == ExceptionLevel.STRICT:
        raise Exception(msg)
    elif config['exception']['level'] == ExceptionLevel.LAX or config['exception']['level'] == ExceptionLevel.IGNORE:
        if config['exception']['level'] == ExceptionLevel.LAX:
            ctxt['log']['main_logger'].warning(msg)
        if ctxt['log']['debug_logger']:
            ctxt['log']['debug_logger'].debug(
                format_exception(traceback.extract_stack(), msg)
            )
    else:
        raise Exception(f"Exception level {config['exception']['level']} not known (should be valid {ExceptionLevel})")


@config_dependencies(('.exception.level', ExceptionLevel))
@context_dependencies(('.log.main_logger', Logger), ('.log.debug_logger', Logger | None))
def raise_exception(ctxt: Context, config: Config, exc: Exception):
    if config['exception']['level'] == ExceptionLevel.STRICT:
        raise exc
    elif config['exception']['level'] == ExceptionLevel.LAX or config['exception']['level'] == ExceptionLevel.IGNORE:
        if config['exception']['level'] == ExceptionLevel.LAX:
            formatted_exc = f"{exc}"
            if formatted_exc:
                ctxt['log']['main_logger'].warning(f"{formatted_exc}")
        if ctxt['log']['debug_logger']:
            ctxt['log']['debug_logger'].debug(
                ''.join(traceback.format_exception(exc, value=exc, tb=exc.__traceback__))
            )
    else:
        raise Exception(f"Exception level {config['exception']['level']} not known (should be valid {ExceptionLevel})")
