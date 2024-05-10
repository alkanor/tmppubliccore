from ...core10_parsing.cli.registry import register_simple_parsing, help_back_to_user
from .save_db import config_save_db, arguments_save_db
from .show import config_show, arguments_show
from .help import config_help, arguments_help
from .list import config_list, arguments_list
from .use import config_use, arguments_use
from .set import config_set, arguments_set

from argparse import Namespace


subparsers = {
    'list': {
        'description': 'List all available subconfigs',
        'arguments': arguments_list,
    },
    'show': {
        'description': 'Show the target configuration (or all if none is provided)',
        'arguments': arguments_show,
    },
    'set': {
        'description': 'Set the target configuration',
        'arguments': arguments_set,
    },
    'help': {
        'description': 'Show the desired available options',
        'arguments': arguments_help,
    },
    'use': {
        'description': 'Use the target configuration as default',
        'arguments': arguments_use,
    },
    'savedb': {
        'description': 'Save the current configuration to provided database',
        'arguments': arguments_save_db,
    }
    # TODO: implement encrypted config, with encryption/decryption functions, policies to decrypt
}


def deal_with_parsed_data(parsed_data: Namespace):
    help_back = False
    if parsed_data.command == 'set':
        config_set(parsed_data)
    elif parsed_data.command == 'use':
        if not parsed_data.subconfig:
            help_back = True
        config_use(parsed_data)
    elif parsed_data.command == 'list':
        config_list(parsed_data)
    elif parsed_data.command == 'show':
        config_show(parsed_data)
    elif parsed_data.command == 'savedb':
        raise NotImplementedError
    elif parsed_data.command == 'help':
        if not parsed_data.modules and not parsed_data.subtrees and parsed_data.prefix is None:
            help_back = True
        else:
            config_help(parsed_data)
    if help_back:
        help_back_to_user('config', parsed_data.command)


register_simple_parsing('config', subparsers=subparsers, callback_after_parsing=deal_with_parsed_data)
