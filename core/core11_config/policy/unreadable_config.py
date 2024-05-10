from ...core21_interaction.policy.error_follow_up import error_when_processing_array, EncounteredErrorArrayProcessing
from ...core11_config.config import Config, register_config_default, config_dependencies
from ...core30_context.context import Context

from enum import Enum


class UnreadableConfigPolicy(Enum):
    GO_NEXT_RAISE_AT_END = 1
    VERBOSE_GO_NEXT_RAISE_AT_END = 2
    VERBOSE_GO_NEXT_ASK_AT_END = 3
    STOP_FIRST_FAILURE = 4  # this is just exception raising
    ASK = 5
    VERBOSE_ASK = 6


register_config_default('.config.unreadable_config', EncounteredErrorArrayProcessing,
                        EncounteredErrorArrayProcessing.VERBOSE_GO_NEXT_ASK_AT_END)


def exit_or_specify_conf(ctxt: Context):
    exit_or_ask = ctxt['interactor']['ask_boolean']({'e': True, 'p': False}) \
        ('No possible configuration file remains, exit (e) or provide other one (p)?')
    if exit_or_ask:
        exit(0)
    return ctxt['interactor']['ask']('Please specify a valid location for an existing config file')


@config_dependencies(('.config.unreadable_config', EncounteredErrorArrayProcessing))
def unreadable_config_policy(config: Config,
                             failed_config: str, remaining_files_to_test: bool, raised_exception: Exception):
    encountered_error_policy = config['config']['unreadable_config']
    failed_attempt_message = f"read config {failed_config}"
    no_more_items_message = 'No more configuration file available'
    continue_message = f"Unable to read {failed_config}, check next configuration?"
    exit_or_specify_manually = exit_or_specify_conf
    return error_when_processing_array(encountered_error_policy, remaining_files_to_test, raised_exception,
                                       failed_attempt_message, no_more_items_message, continue_message,
                                       exit_or_specify_manually)
