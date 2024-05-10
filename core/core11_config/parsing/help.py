from ...core22_action.policy.write import write_data, OutputFormat
from ..config import modules, subtrees_for_module, subtree_at

from argparse import Namespace



# this one holds some mutually exclusive argument groups but this is not handled yet
arguments_help = [
    (['--modules', '-ms'], {'help': 'List all available modules in which some config options can be set',
                            'action': 'store_true'}),
    (['--module', '-m'], {'help': 'Set the module to perform list operations on'}),
    (['--subtrees', '-sts'], {'help': 'List all available subtrees for module in which some config options can be set',
                             'action': 'store_true'}),
    (['--prefix', '-p'], {'help': 'Set the subtree to perform list operations on (this requires a module provided)'}),
    (['--out', '-o'], {'help': 'Output the configuration options within the given file'}),
    (['--outformat', '-of'], {'help': 'Set the (optional) output format in case an output file is given',
                              'choices': ['text', 'json', 'yaml', 'ini']}),
]

def config_help(parsed: Namespace):
    data = {}
    if parsed.modules:
        data.update({
            'modules': modules()
        })
    if parsed.subtrees:
        if not parsed.module:
            raise Exception(f"Subtrees option requires to specify a module")
        data.update({
            parsed.module: subtrees_for_module(parsed.module)
        })
    if parsed.prefix is not None:
        data.update({
            f"prefix:{parsed.prefix}": subtree_at(parsed.prefix)
        })

    write_data(data, getattr(OutputFormat, parsed.outformat.upper()) if parsed.outformat else None, parsed.out)
