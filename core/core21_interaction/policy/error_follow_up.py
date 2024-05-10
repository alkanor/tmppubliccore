from ...core30_context.context_dependency_graph import context_dependencies
from ...core31_policy.exception.strictness import raise_exception_from_string
from ...core30_context.context import Context

from typing import Callable, Any
from enum import Enum


class EncounteredErrorArrayProcessing(Enum):
    GO_NEXT_RAISE_AT_END = 1
    VERBOSE_GO_NEXT_RAISE_AT_END = 2
    VERBOSE_GO_NEXT_ASK_AT_END = 3
    STOP_FIRST_FAILURE = 4  # this is just exception raising
    ASK = 5
    VERBOSE_ASK = 6


# @register_policy('.misc.array_processing_error')
@context_dependencies(('.interactor.ask_boolean', Callable[[...], bool]), ('.interactor.ask', Callable[[...], str]))
def error_when_processing_array(ctxt: Context, encountered_error_policy: EncounteredErrorArrayProcessing,
                                remaining_items_to_test: bool, raised_exception: Exception,
                                failed_attempt_message: str, no_more_items_message: str, continue_message: str,
                                exit_or_specify_manually: Callable[[Context], Any]):
    if encountered_error_policy == EncounteredErrorArrayProcessing.STOP_FIRST_FAILURE:
        raise Exception(raised_exception)
    elif encountered_error_policy == EncounteredErrorArrayProcessing.GO_NEXT_RAISE_AT_END or \
            encountered_error_policy == EncounteredErrorArrayProcessing.VERBOSE_GO_NEXT_RAISE_AT_END or \
            encountered_error_policy == EncounteredErrorArrayProcessing.VERBOSE_GO_NEXT_ASK_AT_END:
        if not encountered_error_policy == EncounteredErrorArrayProcessing.GO_NEXT_RAISE_AT_END:
            raise_exception_from_string(f"Error attempting to {failed_attempt_message}: {raised_exception}")
        if not remaining_items_to_test:
            if encountered_error_policy == EncounteredErrorArrayProcessing.VERBOSE_GO_NEXT_ASK_AT_END:
                return exit_or_specify_manually(ctxt)
            else:
                raised_exception.strerror = f"{no_more_items_message}, " \
                                            f"latest encountered error: {raised_exception.strerror}"
                raise Exception(raised_exception)
    elif encountered_error_policy == EncounteredErrorArrayProcessing.ASK or \
            encountered_error_policy == EncounteredErrorArrayProcessing.VERBOSE_ASK:
        if encountered_error_policy == EncounteredErrorArrayProcessing.VERBOSE_ASK:
            raise_exception_from_string(f"Error attempting to {failed_attempt_message}: {raised_exception}")
        if remaining_items_to_test:
            exit_or_ask = ctxt['interactor']['ask_boolean']({'c': True, 'e': False}) \
                (f"{continue_message} Continue (c) Exit (e)")
            if not exit_or_ask:
                exit(0)
        else:
            return exit_or_specify_manually(ctxt)
    else:
        raise NotImplementedError
