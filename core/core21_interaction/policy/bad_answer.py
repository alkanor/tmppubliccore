from ...core30_context.context_dependency_graph import context_producer, context_dependencies
from ...core11_config.config import register_config_default, config_dependencies, Config
from ...core30_context.context import Context

from typing import Callable, Any
from logging import Logger
from enum import Enum


class BadAnswerPolicy(Enum):
    REPEAT_UNTIL_GOOD = 1
    RAISE = 2
    RETRY_AND_EXIT = 3
    RETRY_AND_RAISE = 4
    ASK_RETRY_OR_STOP_OR_DEFAULT = 5
    RANDOM = 6
    DEFAULT_VALUE = 7


register_config_default('.interactor.bad_answer', BadAnswerPolicy, BadAnswerPolicy.REPEAT_UNTIL_GOOD)
register_config_default('.interactor.bad_answer_retry_count', int, 3)


@config_dependencies(('.interactor.bad_answer', BadAnswerPolicy), ('.interactor.bad_answer_retry_count', int))
@context_dependencies(('.log.main_logger', Logger))
def cli_bad_answer(ctxt: Context, config: Config, error_message,
                   call_question_again: Callable = None, transform_input_if_call_question_again: Callable = None,
                   accept_transform: Callable = None, output_from_transform: Callable = None,
                   unaccepted_answer_error: str = None,
                   *question_args, **question_argv):
    if error_message:
        ctxt['log']['main_logger'].warning(error_message)

    if config['interactor']['bad_answer'] == BadAnswerPolicy.REPEAT_UNTIL_GOOD:
        return call_question_again(transform_input_if_call_question_again, accept_transform,
                                   output_from_transform, unaccepted_answer_error,
                                   *question_args, **question_argv)
    elif config['interactor']['bad_answer'] == BadAnswerPolicy.RAISE:
        raise Exception(error_message)
    elif config['interactor']['bad_answer'] == BadAnswerPolicy.RETRY_AND_EXIT or \
            config['interactor']['bad_answer'] == BadAnswerPolicy.RETRY_AND_RAISE:
        if 'retry_count' in question_argv and \
                question_argv['retry_count'] >= config['interactor']['bad_answer_retry_count']:
            ctxt['log']['main_logger'].warning(
                f"Retry count {config['interactor']['bad_answer_retry_count']} exceeded, "
                f"{'raising' if config['interactor']['bad_answer'] != BadAnswerPolicy.RETRY_AND_EXIT else 'exiting'}")
            if config['interactor']['bad_answer'] == BadAnswerPolicy.RETRY_AND_EXIT:
                exit(1)
            else:
                raise Exception(f"Too much failures answering for {question_args}, {question_argv}")
        question_argv.setdefault('retry_count', 0)
        question_argv['retry_count'] += 1
        return call_question_again(transform_input_if_call_question_again, accept_transform,
                                   output_from_transform, unaccepted_answer_error,
                                   *question_args, **question_argv)
    else:
        raise NotImplementedError


@context_producer(('.interactor.bad_answer', Callable[[...], Any]))
@context_dependencies(('.interactor.local', bool, False), ('.interactor.cli', bool, False))  # dynamically generated
def policy_bad_answer(ctxt: Context):
    if ctxt['interactor']['local'] and ctxt['interactor']['type'] == 'cli':
        ctxt['interactor']['bad_answer'] = cli_bad_answer
    else:
        raise NotImplementedError
