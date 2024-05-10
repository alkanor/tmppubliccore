from ...core31_policy.misc.dict_operations import merge_recursive_only_not_in_first_dict
from ..policy.write_config import write_config_ini, write_config_yaml
from ...core20_messaging.log.log_level import LogLevel
from ...core30_context.context import current_ctxt
from ..config import config_to_string, enrich_config, nested_dict_to_dict
from ..policy.read_config import parse_config

from argparse import Namespace
from typing import List


def check_and_parse_set_options(values: List[str]):
    return list(map(check_and_parse_set_option, values))


def check_and_parse_set_option(value: str):
    if '=' not in value:
        raise Exception(f"Expecting = to get key, value for config option, but found {value}")
    s = value.split('=')
    return s[0], '='.join(s[1:])


arguments_set = [
    (['--sub-config', '-scf'], {'help': 'Sub-configuration block to set (default to default)'}),
    (['--loglevel', '-l'], {'help': 'Global logger value',
                            'choices': ['critical', 'error', 'warning', 'info', 'debug']}),
    (['--database', '-d'], {'help': 'Global database holding all the application state (including further contexts)'}),
    (['--set'], {'help': 'Additional configuration options',
                 'action': 'append'}),
    (['--out', '-o'], {'help': 'Output the configuration options within the given file (instead of current one)'}),
    (['--outformat', '-of'], {'help': 'Set the (optional) output format in case an output file is given (default yaml)',
                              'choices': ['yaml', 'ini']}),
]


def config_set(parsed: Namespace):
    config_dict = {k: v for k, v in check_and_parse_set_options(parsed.set)} if parsed.set else {}
    if parsed.loglevel:
        config_dict.setdefault('log', {})['log_level'] = getattr(LogLevel, parsed.loglevel.upper())
    if parsed.database:
        config_dict['database'] = parsed.database
    config_dict = merge_recursive_only_not_in_first_dict(config_dict, config_to_string(True))

    config = current_ctxt()['config']
    location = config['config_location']
    if parsed.sub_config:
        config_dict_from_file = parse_config(location, parsed.sub_config)
        config_dict = merge_recursive_only_not_in_first_dict(config_dict_from_file, config_dict)
    else:
        enrich_config(nested_dict_to_dict(config_dict))

    subconfig = parsed.sub_config if parsed.sub_config else config_dict['sub_config']
    if parsed.out:
        location = parsed.out

    if parsed.outformat == 'ini' or (not parsed.outformat and location[-4:].upper() == '.INI'):
        write_config_ini(config_dict, location, subconfig)
    else:
        write_config_yaml(config_dict, location, subconfig)
