from ...core30_context.context_dependency_graph import context_dependencies
from .unreadable_config import unreadable_config_policy
from ...core30_context.context import Context
from .default_path import default_config_paths

from logging import Logger
import configparser
import yaml


def parse_yaml(location, sub_config):
    with open(location, 'r') as f:
        config = yaml.safe_load(f)

    if not sub_config or sub_config.lower() == 'default':
        if 'DEFAULT' in config:
            sub_config = config['DEFAULT']
            if not sub_config in config:
                raise Exception(f"Expecting provided sub_config {config['sub_config']} to be provided as dict")
        else:
            sub_config = 'default'
            if not config.get(sub_config):
                return {'sub_config': sub_config}

    if 'sub_config' in config[sub_config]:
        raise Exception(f"Not expecting sub_config an item of the {sub_config} dict")

    return {**config[sub_config], 'sub_config': sub_config}


def parse_section_recursive(config, sub_config, default_keys):
    result = {}
    for k, v in config[sub_config].items():
        if k not in default_keys:
            if '|' in k:
                name, t = k.split('|')
                if t == 'list':
                    result[name] = v.split(',')
                elif t == 'dict':
                    result[name] = parse_section_recursive(config, v, default_keys)
                elif t == 'list-dict':
                    result[name] = list(map(lambda s: parse_section_recursive(config, s, default_keys), v.split(',')))
                else:
                    raise Exception(f"Unexpected type {t}, expecting list, dict or list-dict")
            else:
                result[k] = v
    return result


def parse_ini(location, sub_config):
    with open(location, 'r') as _:  # raise exception is not existing, otherwise configparser does not
        pass

    config = configparser.ConfigParser()
    config.read(location)

    if not sub_config:
        if 'sub_config' not in config['DEFAULT']:
            sub_config = 'default'
        else:
            sub_config = config['DEFAULT']['sub_config']

    if sub_config not in config:
        raise Exception(f"Expecting provided sub_config {sub_config} to be provided as section")

    result_config = parse_section_recursive(config, sub_config, config['DEFAULT'].keys())
    result_config.update({'sub_config': sub_config})

    return result_config


def parse_config(location: str, sub_config: str = None):
    if location[-4:] == '.ini':
        loaded_config = parse_ini(location, sub_config)
    elif location[-5:] == '.yaml' or location[-4:] == '.yml':
        loaded_config = parse_yaml(location, sub_config)
    else:
        raise Exception(f"Expecting some .ini, .yaml or .yml file as configuration input")
    return loaded_config


@context_dependencies(('.log.main_logger', Logger))
def try_open_and_parse_config(ctxt: Context, possible_config_path: str | None = None, sub_config: str | None = None):
    possible_locations = [possible_config_path] if possible_config_path else []
    possible_locations.extend(default_config_paths())

    last_location = None
    while possible_locations:
        location = possible_locations.pop(0)
        try:
            loaded_config = parse_config(location, sub_config)
            ctxt['log']['main_logger'].info(f"Successfully parsed configuration {location}")
            return location, loaded_config
        except Exception as e:
            last_location = unreadable_config_policy(location, len(possible_locations) > 0, e)
    if last_location:  # gives it a last try
        loaded_config = parse_config(last_location, sub_config)
    return last_location, loaded_config


def list_subconfigs(location: str):
    if location[-4:] == '.ini':
        with open(location, 'r') as _:  # raise exception is not existing, otherwise configparser does not
            pass
        config = configparser.ConfigParser()
        config.read(location)
        return config.sections()
    elif location[-5:] == '.yaml' or location[-4:] == '.yml':
        with open(location, 'r') as f:
            config = yaml.safe_load(f)
            return list(config.keys())
    else:
        raise Exception(f"Expecting some .ini, .yaml or .yml file as configuration input")
