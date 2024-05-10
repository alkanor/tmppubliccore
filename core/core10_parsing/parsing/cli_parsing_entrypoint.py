from ...core31_policy.misc.dict_operations import update_dict_check_already_there
from .string_transform import cli_string_transforms
from ..cli.registry import register_simple_parsing
from ...core11_config.config import enrich_config
from ..policy.exit import exit_policy

from argparse import Namespace


arguments = [
    (['--config', '-c'],
     # the following statement must be backed by the right policy in case no config option is provided
     {'help': 'Yaml configuration file for global options, default to one of ~/.mgr/config.yml, '
              '/etc/mgr/config.yml, or %%APPDATA%%/mgr/config.yml (depending on OS and privileges)'}),
    # 'default': default_config_path(ctxt)}),
    (['--subconfig', '-sc'], {'help': 'Sub-configuration block to use from config file (default to default)',
                              'default': 'default'}),
    (['--loglevel', '-l'], {'help': 'Global logger value (default to info)',
                            'choices': ['error', 'warning', 'info', 'debug']}),
    (['--database', '-d'], {'help': 'Specify the database holding all the application state (including contexts)'}),
    (['--envregex', '-e'], {'help': 'Specify the environment regex to get environment variables into config (default is'
                                    ' ^\\.?config(\\..*)$ )',
                            'default': '^\\.?config(\\..*)$'}),
    (['--set'], {'help': 'Additional configuration options',
                 'metavar': 'KEY=VALUE',
                 'action': 'append'}),
]

different_matching = {
    'subconfig': '.sub_config',
    'loglevel': '.log.log_level',
    'envregex': '.env_regex',
    'set': '.additional_options'
}


def deal_with_parsed_data(parsed_data: Namespace):
    from ...core31_policy.entrypoint.entrypoint import do_config_parsing

    parsed_from_command_line = {
        f"{different_matching.get(k, '.'+k)}": cli_string_transforms.get(different_matching.get(k, k), lambda x: x)(v)
        for k, v in parsed_data.__dict__.items() if v
    }
    if '.additional_options' in parsed_from_command_line:
        config_tuples = {f".{k}": v for k, v in parsed_from_command_line['.additional_options']}
        _ = update_dict_check_already_there(parsed_from_command_line, config_tuples)
        del parsed_from_command_line['.additional_options']
    do_config_parsing(parsed_from_command_line)
    enrich_config(parsed_from_command_line)
    return parsed_from_command_line


# initial CLI entrypoint allowing to switch config
# (initial because if not starting with mgr, the default config is used)
register_simple_parsing('mgr', arguments=arguments, callback_after_parsing=deal_with_parsed_data)


def deal_with_exit(exit_data: Namespace):
    if exit_data.force:
        exit(0)
    else:
        exit_policy()

register_simple_parsing('exit', arguments=[(['--force', '-y'],
                                            {'help': 'force exit with no confirmation', 'action': 'store_true'}),],
                        callback_after_parsing=deal_with_exit)
