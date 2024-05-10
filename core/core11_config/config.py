from typing import Dict, Callable, Any, Tuple, Type
from functools import wraps
from enum import Enum
import json
import copy


Config = Dict[str, Any]

_dependencies_per_function: Dict[str, Tuple[str, Type]] = {}
_functions_dependant_of = {}
_default_value_for = {}
_type_of_attribute = {}
_config_value_or_default: Dict[str, Tuple[bool, Type, Any]] = {}
_not_yet_encountered: Dict[str, str] = {}


def config_dependencies(*deps: Tuple[str, Type]):
    def sub(f: Callable[[...], Any]):
        key = f"{f.__module__}.{f.__name__}"
        assert key not in _dependencies_per_function, f"Config dependencies for {key} already registered"
        _dependencies_per_function[key] = deps

        for attributes_string, _type in deps:
            _functions_dependant_of.setdefault(attributes_string, set()).add(key)
            _type_of_attribute[attributes_string] = _type

        @wraps(f)
        def f_with_deps_resolved(*args, **argv):
            context = current_ctxt()
            config = context.setdefault('config', {})
            unknown_configs = []
            default_to_fixed = []
            has_been_deep_copied = False

            for attributes_string, expected_type_from_dep in deps:
                if attributes_string in _config_value_or_default:
                    is_default_value, expected_type, value = _config_value_or_default[attributes_string]
                    assert expected_type == expected_type_from_dep, \
                        f"Expecting type {expected_type_from_dep} from dependency, found {expected_type}"
                    # the other case is when the config already contains the right value, so do nothing
                    if is_default_value:
                        # check if the config contains the desired value, in this case not a default value anymore
                        success, value_from_context = check_dict_against_attributes_string(config, attributes_string)
                        if success:
                            _config_value_or_default[attributes_string] = (False, expected_type, value_from_context)
                            default_to_fixed.append(attributes_string)
                        else:
                            if not has_been_deep_copied:
                                config = copy.deepcopy(config)  # this is in order not to pollute the context
                                # with a default value
                            set_dict_against_attributes_string(config, attributes_string, value)
                else:
                    if attributes_string in _not_yet_encountered:
                        typed = right_type_for(_not_yet_encountered[attributes_string], expected_type_from_dep)
                        set_dict_against_attributes_string(config, attributes_string, typed)
                    else:
                        unknown_configs.append(attributes_string)

            if unknown_configs:
                from .policy.missing_config import missing_config_policy

                filled_values = missing_config_policy(unknown_configs, key)

                for attributes_string, value in filled_values.items():
                    expected_type = _type_of_attribute[attributes_string]
                    value = right_type_for(value, expected_type)
                    _config_value_or_default[attributes_string] = (False, expected_type, value)
                    set_dict_against_attributes_string(config, attributes_string, value)
                    if has_been_deep_copied:  # in this case the changes should be reported within the context
                        set_dict_against_attributes_string(context['config'], attributes_string, value)
                    default_to_fixed.append(attributes_string)

            if default_to_fixed:
                update_fixed(*default_to_fixed)

            return f(config, *args, **argv)

        return f_with_deps_resolved

    return sub


def register_config_default(attribute_string, default_value_type, default_value):
    if attribute_string in _config_value_or_default:  # should not happen, but tolerate the case where not a default val
        assert _config_value_or_default[attribute_string][0] is False, \
            f"Not allowing to register twice for the same default value location {attribute_string}"
    _config_value_or_default[attribute_string] = (True, default_value_type, default_value)
    _type_of_attribute[attribute_string] = default_value_type
    _default_value_for[attribute_string] = default_value


# some tweaks there to convert from string to any correct type
def right_type_for(value, str_or_default_type):
    if str_or_default_type == bool:
        return False if isinstance(value, str) and (value.lower() == 'false' or value == '0')\
                        or isinstance(value, int) and value == 0 else True
    if str_or_default_type == list or str_or_default_type == dict:
        return json.loads(value)
    if issubclass(str_or_default_type, Enum):
        if isinstance(value, str_or_default_type):
            return value
        return getattr(str_or_default_type, value)
    return str_or_default_type(value)


def inverse_type_to_string(value):
    match value:
        case bool():
            return 'true' if value else 'false'
        case int():
            return str(value)
        case str():
            return value
        case Enum():
            return value.name
        case dict() | list() | set():
            return json.dumps(value)
        case _:
            raise NotImplementedError


def _recursive_nested_dict_to_dict(nested_dict: Dict[str, Any], cur_prefix: str = ''):
    for k, v in nested_dict.items():
        if isinstance(v, dict):
            yield from _recursive_nested_dict_to_dict(v, f"{cur_prefix}.{k}")
        else:
            yield f"{cur_prefix}.{k}", v

def nested_dict_to_dict(nested_dict: Dict[str, Any]):
    return {k: v for k, v in _recursive_nested_dict_to_dict(nested_dict)}


def enrich_config(config_to_merge: Dict[str, Any]):
    rightly_typed = {
        k: right_type_for(v, _config_value_or_default.get(k, (str, str))[1]) for k, v in config_to_merge.items()
    }
    updated_attributes = []
    context = current_ctxt()
    context.setdefault('config', {})
    for key in rightly_typed:
        set_dict_against_attributes_string(context['config'], key, rightly_typed[key])
        if key in _config_value_or_default:
            if _config_value_or_default[key][0]:
                updated_attributes.append(key)
            _config_value_or_default[key] = (False, _config_value_or_default[key][1], rightly_typed[key])
        else:  # maybe the module using the config is not yet load to declare default value, keep it
            _not_yet_encountered[key] = rightly_typed[key]
    update_fixed(*updated_attributes)


def config_to_string(with_default: bool = False):
    output = {}
    for key in _config_value_or_default:
        # only writing it if a specific value has been set or if explicitly asked to dump default
        if with_default or not _config_value_or_default[key][0]:
            set_dict_against_attributes_string(output, key,
                                               inverse_type_to_string(_config_value_or_default[key][2]))
    return output


def config_to_string_no_check(config: Dict[str, Any]):
    output = nested_dict_to_dict(config)
    transformed = {}
    for key in output:
        if key in _config_value_or_default:
            set_dict_against_attributes_string(transformed, key, inverse_type_to_string(_config_value_or_default[key][2]))
        else:
            set_dict_against_attributes_string(transformed, key, inverse_type_to_string(output[key]))
    return transformed


def update_fixed(*attributes_strings: str):
    functions_to_update = set()
    for attributes_string in attributes_strings:
        functions_to_update = functions_to_update.union(
            _functions_dependant_of.get(attributes_string, set())
        )
    for function in functions_to_update:
        # in this case it is known that the function as no argument in order to be called during dependency resolve
        func = is_context_producer(function)
        if func:
            func()


def modules():
    all_keys = sorted(list({k.split('.')[1] for k in _config_value_or_default.keys() if k != '.sub_config'}))
    return all_keys

def subtrees_for_module(module: str):
    all_keys = sorted(list({k.split('.')[2] for k in _config_value_or_default.keys() if k[1:len(module)+1] == module}))
    return all_keys

def subtree_at(prefix: str):
    temp = {k for k in _config_value_or_default.keys()
            if k[1:len(prefix)+1] == prefix or not prefix}
    return {
        k: {
            'current_value': inverse_type_to_string(_config_value_or_default[k][2]),
            'type': f"{_config_value_or_default[k][1]}",
            **({'possible_values': [e.name for e in _config_value_or_default[k][1]]}
               if issubclass(_config_value_or_default[k][1], Enum) else {})
        }
        for k in temp
    }


from ..core99_misc.fakejq.utils import check_dict_against_attributes_string, set_dict_against_attributes_string
from ..core30_context.context_dependency_graph import is_context_producer
from ..core30_context.context import current_ctxt
