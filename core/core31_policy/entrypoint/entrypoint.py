from ...core10_parsing.parsing.string_transform import cli_string_transforms
from ...core10_parsing.policy.no_action import no_action_parsed
from ...core11_config.parsing.use import convert_conf_and_enrich
from ...core11_config.policy.default_env import default_config_env
from ...core11_config.policy.read_config import try_open_and_parse_config
from ...core30_context.context_dependency_graph import context_dependencies
from ...core10_parsing.cli.registry import command_registry
from ...core10_parsing.cli.simple_parse import simple_parse
from ...core30_context.context import Context, current_ctxt
from ..misc.dict_operations import update_dict_check_already_there
from ...core11_config.config import enrich_config

from typing import Callable, Dict
import regex
import sys
import os


def parse_environment(env_regex):
    result = {}
    for name, value in os.environ.items():
        if regex.match(env_regex, name):
            result[name] = value
    return result


def check_log_level_in_dict(config_dict, current_log_level):
    if '.log.log_level' in config_dict:
        if current_log_level != config_dict['.log.log_level']:
            enrich_config({'.log.log_level': config_dict['.log.log_level']})
        return config_dict['.log.log_level']
    return -1


def do_config_parsing(config_dict: Dict):
    log_value = current_ctxt().get('config', {}).get('log', {}).get('log_level', -1)

    # parse main environment arguments (only config and database, next C2 but if no database is provided atm it's over)
    key_envkeys, env_associations = default_config_env()
    parsed_env_main = {
        env_associations[k]: cli_string_transforms.get(env_associations[k], lambda x: x)(os.environ[k])
        for k in key_envkeys if k in os.environ
    }
    parsed_env_main.update({
        env_associations[k]: cli_string_transforms.get(env_associations[k], lambda x: x)(os.environ[k.upper()])
        for k in key_envkeys if k.upper() in os.environ
    })

    update_dict_check_already_there(config_dict, parsed_env_main)
    log_value = check_log_level_in_dict(config_dict, log_value)

    config_filename = config_dict.get('.config')
    if '.config' in config_dict:
        del config_dict['.config']

    location, parsed_config_file = try_open_and_parse_config(config_filename, sub_config=config_dict.get('.sub_config'))
    config_dict['.config_location'] = location
    convert_conf_and_enrich(parsed_config_file, config_dict)

    # parse BDD
    # from_bdd = parse_bdd_config()
    # parse C2, ...
    # from_c2 = parse_c2_config()


# pass at_least_one_action = True if you just want to parse cli inputs
@context_dependencies(('.interactor.parsing_no_action', Callable[[], None], False))
def cli_entrypoint(ctxt: Context, at_least_one_action = False):
    # this is going to determine the final log level (as it can change depending on each parsing step
    # and on dict merge policy)
    log_value = -1
    config_dict = {}

    # parse CLI args
    parsed_cli_dict = simple_parse(sys.argv[1:])
    if 'mgr' in parsed_cli_dict:  # global configuration in this case,
        # the manager callback is supposed to internally rebuild the config (do the do_config_parsing)
        config_dict.update(command_registry['mgr']['callback'](parsed_cli_dict['mgr']))
    else:
        do_config_parsing(config_dict)
    log_value = check_log_level_in_dict(config_dict, log_value)


    # now all is parsed, current_context['config'] is ready, give it to following layers
    # should process ARGV in the right order due to how is constructed the dict
    for key, value in parsed_cli_dict.items():
        if key != 'mgr':
            at_least_one_action = True
            result = command_registry[key]['callback'](value)

    if not at_least_one_action:
        no_action_parsed()
        return ctxt['interactor']['parsing_no_action']()
