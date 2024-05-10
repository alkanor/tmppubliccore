from ...core30_context.context_dependency_graph import context_producer, context_dependencies
from ...core30_context.context import Context

from typing import Callable
from logging import Logger


@context_dependencies(('.log.main_logger', Logger))
def default_send_cli(ctxt: Context, data: str):
    return ctxt['log']['main_logger'].info(data)


@context_producer(('.interactor.intent_back', Callable[[str], None]))
@context_dependencies(('.interactor.local', bool, False), ('.interactor.cli', bool, False))  # dynamically generated
def send_back_to_interactor(ctxt: Context):
    if ctxt['interactor']['local'] and ctxt['interactor']['type'] == 'cli':
        ctxt['interactor']['intent_back'] = default_send_cli
    else:
        raise NotImplementedError
