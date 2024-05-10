from ...core30_context.context_dependency_graph import context_producer, context_dependencies
from ...core30_context.context import Context
from .bad_answer import cli_bad_answer

from typing import Callable, Any, Dict
from functools import partial
from logging import Logger


@context_producer(('.interactor.cli_read', Callable[[], str]))
def read_cli(ctxt: Context):
    ctxt.setdefault('interactor', {})['cli_read'] = input


@context_dependencies(('.log.cli_interactor_logger', Logger), ('.interactor.cli_read', Callable[[], str]))
def ask_cli(ctxt: Context, to_ask: str):
    ctxt['log']['cli_interactor_logger'].info(f"[QUESTION] {to_ask}")
    return ctxt['interactor']['cli_read']()


def default_ask_cli(*args, **argv):
    question = ''
    if args:
        question += args[0]
        if len(args) > 1:
            question += ' ' + ' '.join(map(lambda x: f"({x})", args[1:]))
    if argv:
        question += ' (' + ', '.join([f"{k} = {v}" for k, v in argv.items()]) + ')'
    return ask_cli(question)


# this function gives both the accept_transform and the output_from_transform function
# and error_message for a given dict (for simple query/answer with string provided -> output object)
def accept_only_fixed_answers(answer_transform: Dict[str, Any]):
    def accept_transform(transformed_input):
        return transformed_input in answer_transform

    def output_from_transform(initial_input, transformed_input):
        return answer_transform[transformed_input]  # it will raise if not in answer_transform, this is expected

    error_message = f"expecting one answer of {list(answer_transform.keys())}"
    return accept_transform, output_from_transform, error_message


def default_ask_cli_transform_and_check(transform_input: Callable[[str], Any],
                                        accept_transform: Callable[[Any], bool],
                                        output_from_transform: Callable[[str, Any], bool],
                                        unaccepted_answer_error: str = None,
                                        *args, **argv):
    out = default_ask_cli(*args, **argv)
    transformed = transform_input(out)
    if accept_transform(transformed):
        return output_from_transform(out, transformed)
    else:
        error_message = f"Provided answer {out} transformed into {transformed} not accepted" \
                        f"{': ' + unaccepted_answer_error if unaccepted_answer_error else ''}"
        return cli_bad_answer(error_message, default_ask_cli_transform_and_check,
                              transform_input, accept_transform, output_from_transform, unaccepted_answer_error,
                              *args, **argv)


def default_ask_cli_boolean(boolean_accept_dict: Dict[str, bool] | None = None):
    if boolean_accept_dict:
        accept_transform, output_from_transform, error_message = accept_only_fixed_answers(boolean_accept_dict)
    else:
        basic_dict = {
            'y': True,
            'n': False,
        }
        accept_transform, output_from_transform, error_message = accept_only_fixed_answers(basic_dict)
    return partial(default_ask_cli_transform_and_check,
                   lambda answer: answer.lower(),
                   accept_transform,
                   output_from_transform,
                   error_message)


@context_producer(('.interactor.ask', Callable[[...], str]), ('.interactor.ask_boolean', Callable[[...], bool]))
@context_dependencies(('.interactor.local', bool, False), ('.interactor.cli', bool, False))  # dynamically generated
def ask_to_interactor(ctxt: Context):
    if ctxt['interactor']['local'] and ctxt['interactor']['type'] == 'cli':
        ctxt['interactor']['ask'] = default_ask_cli
        ctxt['interactor']['ask_boolean'] = default_ask_cli_boolean
    else:
        raise NotImplementedError
