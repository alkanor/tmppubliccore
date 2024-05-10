from ...core30_context.context_dependency_graph import context_dependencies
from ...core30_context.context import Context

from typing import Callable, Dict, Any, List, Tuple
import argparse
import io


command_registry = {}

def register_simple_parsing(command: str,
                            callback_after_parsing: Callable[[Dict[str, Any], argparse.Namespace, ...], Any],
                            arguments: List[Tuple[List[str], Dict[str, str]]] = None,
                            subparsers: Dict[str, str|List[Tuple[List[str], Dict[str, str]]]] = None,
                            description: str = None):
    assert command not in command_registry, f"Command {command} already in registry, please register another name"
    arg_parser = argparse.ArgumentParser(prog=command, description=description, exit_on_error=False)
    arg_parser.exit = lambda *args: None

    if arguments:
        for positional, optional in arguments:
            arg_parser.add_argument(*positional, **optional)

    subparsers_in_registry = {}
    if subparsers:
        subparsers_for_parser = arg_parser.add_subparsers(dest='command')
        for subparser_name in subparsers:
            subparser = subparsers_for_parser.add_parser(subparser_name,
                                                         description=subparsers[subparser_name]['description'],
                                                         exit_on_error=False)
            subparser.exit = lambda *args: None
            for positional, optional in subparsers[subparser_name]['arguments']:
                subparser.add_argument(*positional, **optional)
            subparsers_in_registry[subparser_name] = subparser

    command_registry[command] = {
        'parser': arg_parser,
        'subparsers': subparsers_in_registry,
        'built_from': {'arguments': arguments, 'subparsers': subparsers, 'description': description},
        'callback': callback_after_parsing,
    }


def help_for_parser_to_string(command_name: str, subparser: str = None):
    if subparser:
        help_for = command_registry[command_name]['subparsers'][subparser]
    else:
        help_for = command_registry[command_name]['parser']
    out = io.StringIO()
    help_for.print_help(out)
    out.seek(0)
    return out.read()


@context_dependencies(('.interactor.intent_back', Callable[[str], None]))
def help_back_to_user(ctxt: Context, command_name: str, subparser: str = None):
    to_print = help_for_parser_to_string(command_name, subparser)
    ctxt['interactor']['intent_back'](to_print)


# @context_dependancies('.database.sessionmaker')
# def save_parsing_registry_in_database(ctxt: Context):
#     with get_session() as session:
#     for command_name in command_registry:
#         built_from = command_registry[command_name]
        #PARSING_ARGUMENTS.GET_CREATE(...)
        #PARSING_SUBPARSERS.GET_CREATE(...)
    #...