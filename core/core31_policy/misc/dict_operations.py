from ...core11_config.config import register_config_default, config_dependencies, Config
from ...core30_context.context_dependency_graph import context_dependencies
from ..exception.strictness import ExceptionLevel
from ...core30_context.context import Context

from typing import Dict, Any, Callable, List
from logging import Logger
from enum import Enum


class UpdateDictConflict(Enum):
    KEEP = 1
    MERGE = 2
    CHOOSE = 3  # this one indicates interaction will be used (more complicated)

register_config_default('.misc.update_dict_conflict', UpdateDictConflict, UpdateDictConflict.KEEP)


@config_dependencies(('.exception.level', ExceptionLevel))
@context_dependencies(('.log.debug_logger', Logger | None), ('.log.main_logger', Logger))
def already_in_dict(ctxt: Context, config: Config,
                    initial_dict: Dict[Any, Any], dict_to_merge_into: Dict[Any, Any],
                    raise_if_strict: bool = False, no_print: bool = False):
    common_keys = set(initial_dict.keys()).intersection(set(dict_to_merge_into.keys()))
    optional_debug_logger = ctxt['log']['debug_logger']
    if optional_debug_logger and common_keys and not no_print:
        optional_debug_logger.debug(f"Common keys {common_keys} between the two provided dicts")
    if common_keys:
        if config['exception']['level'] == ExceptionLevel.LAX or not raise_if_strict:
            if config['exception']['level'] == ExceptionLevel.LAX and optional_debug_logger and not no_print:
                optional_debug_logger.debug('Policy LAX so only warning printed as there are common keys')
            if not no_print:
                ctxt['log']['main_logger'].warning(f"Common keys {common_keys} between provided dicts")
        elif config['exception']['level'] == ExceptionLevel.STRICT and raise_if_strict:
            if optional_debug_logger and not no_print:
                optional_debug_logger.debug('Policy STRICT so raising exception as there are common keys between'
                                            f" provided dicts (also depending on raise_if_strict={raise_if_strict})")
            if raise_if_strict:
                raise Exception(f"Dict to merge into keys are already in source dict: {common_keys}")
            else:
                ctxt['log']['main_logger'].error(f"Dict to merge into keys are already in source dict: {common_keys}")
        else:
            raise Exception(f"config value for exception_level must be either {ExceptionLevel.LAX} or "
                            f"{ExceptionLevel.STRICT}, not {config['exception']['level']}")
    return common_keys


#@register_policy('.misc.update_dict_conflict')
@config_dependencies(('.misc.update_dict_conflict', UpdateDictConflict))
@context_dependencies(('.log.debug_logger', Logger | None), ('.log.main_logger', Logger),
                      ('.interactor.ask', Callable[[...], str]))
def update_dict_check_already_there(ctxt: Context, config: Config,
                                    initial_dict: Dict[Any, Any], dict_to_merge_into: Dict[Any, Any],
                                    raise_if_strict: bool = False):
    common_keys = already_in_dict(initial_dict, dict_to_merge_into, raise_if_strict, no_print=True)

    if common_keys:
        ctxt['log']['main_logger'].info(f"Common keys {common_keys}, dict will be modified or"
                                        f" not according to config['misc']['update_dict_conflict'] = "
                                        f"{config['misc']['update_dict_conflict']}")
        if config['misc']['update_dict_conflict'] == UpdateDictConflict.KEEP:
            initial_dict.update(**{k: v for k, v in dict_to_merge_into.items() if k not in common_keys})
        elif config['misc']['update_dict_conflict'] == UpdateDictConflict.MERGE:
            initial_dict.update(dict_to_merge_into)
        elif ctxt['misc']['update_dict_conflict'] == UpdateDictConflict.CHOOSE:
            chosen_items_to_merge = {}
            for key in common_keys:
                chosen_items_to_merge[key] = ctxt['interactor']['ask'] \
                    (f"Choose between {initial_dict[key]} and {dict_to_merge_into[key]}", type(initial_dict[key]),
                     initial_dict[key], dict_to_merge_into[key])
            initial_dict.update(**{k: v for k, v in dict_to_merge_into.items() if k not in common_keys})
            initial_dict.update(chosen_items_to_merge)
        else:
            raise Exception(f"config value for update_dict_conflict must be either {UpdateDictConflict.KEEP}, "
                            f"{UpdateDictConflict.MERGE} or {UpdateDictConflict.CHOOSE}, not "
                            f"{ctxt['misc']['update_dict_conflict']}")
    else:
        initial_dict.update(dict_to_merge_into)

    return common_keys


def merge_recursive_only_not_in_first_dict(d1: Dict, d2: Dict):
    out = {}
    for k in d2:
        if k not in d1:
            out[k] = d2[k]
        else:
            if isinstance(d1[k], dict):
                out[k] = merge_recursive_only_not_in_first_dict(d1[k], d2[k])
            else:
                out[k] = d1[k]
    for k in d1:
        if k not in d2:
            out[k] = d1[k]
    return out
