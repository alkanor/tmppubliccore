from ...core30_context.context_dependency_graph import context_producer, context_dependencies
from ...core02_model.typed.service import DirectService, Service
from ...core02_model.typed.identity import Identity
from ...core30_context.context import Context

from typing import Callable
from logging import Logger
import getpass


def default_ask_password_cli(prompt=None):
    return getpass.getpass(prompt=prompt if not prompt else 'Password?')


@context_dependencies(('.interactor.local', bool, False), ('.interactor.cli', bool, False))
def ask_password(ctxt: Context, prompt=None):
    if ctxt['interactor']['local'] and ctxt['interactor']['type'] == 'cli':
        return default_ask_password_cli(prompt)
    else:
        raise NotImplementedError

@context_producer(('.interactor.ask_password', Callable[[...], str]))
@context_dependencies(('.interactor.local', bool, False), ('.interactor.cli', bool, False))  # dynamically generated
def ask_password_to_interactor(ctxt: Context):
    if ctxt['interactor']['local'] and ctxt['interactor']['type'] == 'cli':
        ctxt['interactor']['ask_password'] = ask_password
    else:
        raise NotImplementedError


@context_dependencies(('.vault.ask_password_for', Callable[[Identity, DirectService, Service|None], bytes|None], False),
                      ('.vault.keep_password', Callable[[Identity, DirectService, Service|None, bytes], None], False),
                      ('.log.main_logger', Logger))
def password_for_user(ctxt: Context, identity: Identity, target: DirectService, from_system: Service | None):
    prompt = f"Password for user {identity}, to authenticate on {target}" + \
             (f" (from {from_system})" if from_system else '') + '?'
    if 'vault' not in ctxt:
        ctxt['log']['main_logger'].info(f"No vault provided, asking password for {identity} directly")
        return ask_password(prompt=prompt)
    else:
        optional_from_vault = ctxt['vault']['ask_password_for'](identity, target, from_system)
        if optional_from_vault:
            return optional_from_vault
        else:
            password = ask_password(prompt=f"Password not found in vault. " + prompt)
            ctxt['vault']['keep_password'](identity, target, from_system, password)
            return password
