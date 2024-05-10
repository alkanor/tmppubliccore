from ...core30_context.context_dependency_graph import context_dependencies
from ...core10_parsing.cli.registry import register_simple_parsing
from ...core22_action.policy.write import write_data, OutputFormat
from ...core30_context.context import Context

from argparse import Namespace
from typing import Callable


arguments = [
    (['--dump', '-d'],
     {'help': 'Filename in which to dump the current full database model (SQL file)'}),
    # 'default': default_config_path(ctxt)}),
    (['--show', '-s'], {'help': 'Show the current database model',
                        'action': 'store_true'}),
]


def dump_model():
    raise NotImplementedError  # implements the real DB dump to SQL here

@context_dependencies(('.interactor.output.write_to', Callable[[str], None]))
def deal_with_parsed_data(ctxt: Context, parsed_data: Namespace):
    if parsed_data.show:
        dump_model()
        ctxt['interactor']['output']['write_to']('\n'.join(dump_model()))
        return
    elif not parsed_data.dump:
        raise Exception(f"Excepting a provided dump file if the --show option is not provided")
    write_data(dump_model(), OutputFormat.TEXT, parsed_data.dump)


register_simple_parsing('model', arguments=arguments, callback_after_parsing=deal_with_parsed_data)
