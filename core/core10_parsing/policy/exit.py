from ...core30_context.context_dependency_graph import context_dependencies
from ...core11_config.config import config_dependencies, Config
from ...core31_policy.exception.format import format_exception
from ...core30_context.context import Context

from typing import Callable
from logging import Logger
import traceback
import enum


class ExitBehavior(enum.Enum):
    ASK = enum.auto()
    INFO_AND_EXIT = enum.auto()
    EXIT_SILENT = enum.auto()


@config_dependencies(('.misc.exit_behavior', ExitBehavior))
@context_dependencies(('.interactor.ask_boolean', Callable[[...], bool]),
                      ('.log.main_logger', Logger), ('.log.debug_logger', Logger | None))
def exit_policy(ctxt: Context, config: Config):
    if config['misc']['exit_behavior'] == ExitBehavior.ASK:
        exit_or_continue = ctxt['interactor']['ask_boolean']({'e': True, 'c': False}) \
            ('Exit asked, exit (e) or continue (c)?')
        if exit_or_continue:
            exit(0)
    elif config['misc']['exit_behavior'] == ExitBehavior.INFO_AND_EXIT:
        ctxt['log']['main_logger'].warning("Exit asked")
        if ctxt['log']['debug_logger']:
            ctxt['log']['debug_logger'].debug(
                format_exception(traceback.extract_stack(), "Asked exit at location")
            )
        exit(0)
    elif config['misc']['exit_behavior'] == ExitBehavior.EXIT_SILENT:
        exit(0)
    else:
        raise NotImplementedError
