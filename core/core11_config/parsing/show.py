from ...core31_policy.misc.dict_operations import merge_recursive_only_not_in_first_dict
from ...core22_action.policy.write import write_data, OutputFormat
from ..policy.write_config import non_writable_attributes
from ...core30_context.context import current_ctxt
from ..policy.read_config import parse_config
from ..config import config_to_string

from argparse import Namespace


arguments_show = [
    # not very pleasant but to avoid the previous parsing option rewrite :/
    (['--sub-config', '-scf'], {'help': 'Sub-configuration block to show (default to None = current displayed)'}),
    (['--withdefault', '-wd'], {'help': 'Includes all configuration options default values if unset',
                                'action': 'store_true'}),
    (['--out', '-o'], {'help': 'Output the configuration options within the given file (instead of current one)'}),
    (['--outformat', '-of'], {'help': 'Set the (optional) output format in case an output file is given',
                              'choices': ['text', 'json', 'yaml', 'ini']}),
]


def dict_to_display(subconfig, outformat, config_dict):
    return {
        'DEFAULT': {
            'sub_config': subconfig,
        } if outformat and outformat.upper() == 'INI' else subconfig,
        subconfig: {
            k: v for k, v in config_dict.items() if k not in non_writable_attributes
        }
    }

def config_show(parsed: Namespace):
    config_dict = config_to_string(parsed.withdefault)

    if parsed.sub_config:
        config = current_ctxt()['config']
        location = config['config_location']
        config_dict_from_file = parse_config(location, parsed.sub_config)
        if parsed.withdefault:
            config_dict = merge_recursive_only_not_in_first_dict(config_dict_from_file, config_dict)
        else:
            config_dict = config_dict_from_file

    subconfig = parsed.sub_config if parsed.sub_config else config_dict['sub_config']
    dict_to_show = dict_to_display(subconfig, parsed.outformat, config_dict)

    write_data(dict_to_show, getattr(OutputFormat, parsed.outformat.upper()) if parsed.outformat else None, parsed.out)
