from ...core30_context.context_dependency_graph import context_dependencies
from ...core22_action.policy.write import OutputFormat, write_data
from ...core30_context.context import Context
from ..policy.read_config import list_subconfigs

from argparse import Namespace


arguments_list = [
    (['--outformat', '-of'], {'help': 'Set the (optional) output format to display subconfig names as',
                              'choices': ['text', 'json', 'yaml']}),
]

@context_dependencies(('.config.config_location', str, False))
def config_list(ctxt: Context, parsed: Namespace):
    location = ctxt['config']['config_location']
    sections = [s for s in list_subconfigs(location) if s != 'DEFAULT']
    write_data(sections, getattr(OutputFormat, parsed.outformat.upper()) if parsed.outformat else None)
