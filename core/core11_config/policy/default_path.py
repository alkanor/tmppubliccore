from ...core30_context.context_dependency_graph import context_dependencies, context_producer
from ...core22_action.policy.fs import check_dir_access
from ...core30_context.context import Context
from ..config import register_config_default

from typing import Callable
from pathlib import Path
from os import path
import os.path


# @register_policy('.config.default_config_paths')
@context_dependencies(('.executor.os', str), ('.executor.uid', int), ('.executor.gid', int))
def default_config_paths(ctxt: Context):
    if 'win' in ctxt['executor']['os'] and not 'darwin' in ctxt['executor']['os']:
        return [path.expandvars('%APPDATA%\\mgr\\config.yml'), path.expandvars('%APPDATA%\\mgr\\config.ini')]
    else:
        if ctxt['executor']['uid'] == 0 or ctxt['executor']['gid'] == 0:  # quick & dirty way to know we are root
            return ['/etc/mgr/config.yml', '/etc/mgr/config.ini',
                    path.expanduser('~/.mgr/config.yml'), path.expanduser('~/.mgr/config.ini')]
        else:  # if not root check if a config is available in current user home
            return [path.expanduser('~/.mgr/config.yml'), path.expanduser('~/.mgr/config.ini'),
                    '/etc/mgr/config.yml', '/etc/mgr/config.ini']


@context_dependencies(('.executor.os', str), ('.executor.uid', int), ('.executor.gid', int))
def default_database_paths(ctxt: Context):
    if 'win' in ctxt['executor']['os'] and not 'darwin' in ctxt['executor']['os']:
        return [path.expandvars('%APPDATA%\\mgr\\state.db')]
    else:
        if ctxt['executor']['uid'] == 0 or ctxt['executor']['gid'] == 0:
            return ['/var/mgr/state.db', path.expanduser('~/.mgr/state.db')]
        else:
            return [path.expanduser('~/.mgr/state.db')]

@context_dependencies(('.executor.os', str))
def default_database_url(ctxt: Context):
    if 'win' in ctxt['executor']['os'] and not 'darwin' in ctxt['executor']['os']:
        return [f"sqlite:////{path}" if path[1] == ':' and path[2] == '\\' else f"sqlite:///{path}"
                for path in default_database_paths()]
    else:
        return [f"sqlite:///{path}" for path in default_database_paths()]

register_config_default('.database', str, default_database_url()[0])


# @config_dependencies(('.config.repository_location', str | None))
@context_dependencies(('.interactor.ask', Callable[[...], str]))
@context_producer(('.fs.repository_location', Path))
def default_fs_repository(ctxt: Context):
    # little cheat there: the config is not required as a dependency (because it would be enforced otherwise)
    # so we test it there and act accordingly if it is there or not
    if 'config' in ctxt and 'config' in ctxt['config'] and 'repository_location' in ctxt['config']['config']:
        ctxt.setdefault('fs', {})['repository_location'] = ctxt['config']['config']['repository_location']
    else:
        possible_config_paths = default_config_paths()
        tested = set()
        for path in possible_config_paths:
            d = os.path.dirname(path)
            if d not in tested:
                tested.add(d)
                try:
                    check_dir_access(d)
                    ctxt.setdefault('config', {}).setdefault('config', {}).setdefault('repository_location', d)
                except:
                    pass
        ctxt.setdefault('config', {}).\
            setdefault('config', {}).\
            setdefault('repository_location', ctxt['interactor']['ask'](f"No writable repository location found among "
                                                                        f"{tested}, please give one"))
