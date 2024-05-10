from ...core31_policy.exception.strictness import raise_exception_from_string
from ...core30_context.context_dependency_graph import context_dependencies
from ...core99_misc.fakejq.utils import set_dict_against_attributes_string
from ..config import Config, register_config_default, config_dependencies
from .write_config import write_config
from ...core30_context.context import Context

from typing import List, Callable
from enum import Enum


class MissingConfigPolicy(Enum):
    RAISE = 1
    ASK = 2
    ASK_GROUP = 3
    ASK_AND_SAVE = 4

register_config_default('.config.missing_config', MissingConfigPolicy, MissingConfigPolicy.ASK_AND_SAVE)


#@register_policy('.config.missing_config')
@config_dependencies(('.config.missing_config', MissingConfigPolicy))  # ('.config_location', str) # not int config
@context_dependencies(('.interactor.ask', Callable[[...], str]))
def missing_config_policy(ctxt: Context, config: Config, missing_configs: List[str], func_name: str):
    missing_config = config['config']['missing_config'] if not isinstance(config['config']['missing_config'], str) \
        else getattr(MissingConfigPolicy, config['config']['missing_config'])
    if missing_config == MissingConfigPolicy.RAISE:
        raise Exception(f"Missing configuration for function {func_name}: {', '.join(missing_configs)}")
    elif missing_config == MissingConfigPolicy.ASK or missing_config == MissingConfigPolicy.ASK_AND_SAVE:
        filled = {}
        for missing_config_name in missing_configs:
            filled[missing_config_name] = \
                ctxt['interactor']['ask'](f"Configuration for item at {missing_config_name}? (for {func_name})", str)
        if missing_config == MissingConfigPolicy.ASK_AND_SAVE:
            for attr, value in filled.items():
                set_dict_against_attributes_string(config, attr, value)
            write_config(config, config['config_location'])
        return filled
    elif missing_config == MissingConfigPolicy.ASK_GROUP:
        filled = ctxt['interactor']['ask'](f"Configuration for missing items at {func_name}?", dict, missing_configs)
        return filled
    else:
        raise_exception_from_string(f"Non allowed value {config['config']['missing_config']} provided for {MissingConfigPolicy}")
        return {}
