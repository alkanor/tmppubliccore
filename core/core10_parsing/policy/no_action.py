from ...core30_context.context_dependency_graph import context_producer, context_dependencies
from ...core31_policy.exception.strictness import raise_exception
from ...core30_context.context import Context
from ..cli.registry import command_registry
from ..cli.simple_parse import simple_parse

from typing import Callable
import shlex
import cmd


class BasicArgparseREPL(cmd.Cmd):
    prompt = '/> '

    def onecmd(self, command: str):
        try:
            ns_per_command = simple_parse(shlex.split(command))
            for key in ns_per_command:
                command_registry[key]['callback'](ns_per_command[key])
        except Exception as e:
            raise_exception(e)


def cli_repl_loop():
    try:
        BasicArgparseREPL().cmdloop()
    except KeyboardInterrupt:
        exit(0)


@context_producer(('.interactor.parsing_no_action', Callable[[], None]))
@context_dependencies(('.interactor.local', bool, False), ('.interactor.cli', bool, False))  # dynamically generated
def no_action_parsed(ctxt: Context):
    if ctxt['interactor']['local'] and ctxt['interactor']['type'] == 'cli':
        ctxt['interactor']['parsing_no_action'] = cli_repl_loop
        return cli_repl_loop
    else:
        raise NotImplementedError
