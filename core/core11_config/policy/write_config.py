from ..config import config_dependencies, Config, register_config_default, config_to_string, config_to_string_no_check
from ...core22_action.policy.write import OutputFormat, write_data

from typing import Dict
import configparser
import yaml
import io


non_writable_attributes = {
    'sub_config',
    'config_location',
}

def compute_string_dict_hash(string_dict: Dict[str, str]):
    return hash(frozenset(sorted(string_dict.items())))


def compute_hashes_for_sections(config_parser: configparser.ConfigParser):
    return {
        compute_string_dict_hash(
            {k: v for k, v in config_parser[section].items() if k not in config_parser['DEFAULT']}):
            section for section in config_parser.sections()
    }


def recursive_config_iterator(config: Config, config_parser: configparser.ConfigParser,
                              hashes_for_sections: Dict[str, str], first: bool = False):
    config_parser_dict = {}
    for section_or_attribute, value in config.items():
        if isinstance(value, str):
            config_parser_dict[section_or_attribute] = value
        elif isinstance(value, int):
            config_parser_dict[section_or_attribute] = str(value)
        elif isinstance(value, dict):
            sub_config = recursive_config_iterator(config[section_or_attribute], config_parser,
                                                   hashes_for_sections)
            config_parser_dict[f"{section_or_attribute}|dict"] = sub_config
        elif isinstance(value, list) or isinstance(value, set):
            if all([isinstance(v, str) for v in value]):
                config_parser_dict[f"{section_or_attribute}|list"] = ','.join(value)
            elif all([isinstance(v, dict) for v in value]):
                raise NotImplementedError
            else:
                raise Exception(f"Mixing types not supported (expecting all strings or all dicts)")
        else:
            raise NotImplementedError

    if not first:
        result_hash = compute_string_dict_hash(config_parser_dict)
        if result_hash not in hashes_for_sections:
            i = 0
            while f"{section_or_attribute}-{i}" in config_parser.sections():
                i += 1
            hashes_for_sections[result_hash] = f"{section_or_attribute}-{i}"
            config_parser[f"{section_or_attribute}-{i}"] = config_parser_dict
        return hashes_for_sections[result_hash]
    else:
        return config_parser_dict


def format_ini_dict(string_dict_or_cp: Dict[str, str | Dict] | configparser.ConfigParser):
    if not isinstance(string_dict_or_cp, configparser.ConfigParser):
        cp = configparser.ConfigParser()
        if 'DEFAULT' in string_dict_or_cp:
            cp['DEFAULT']['sub_config'] = string_dict_or_cp['DEFAULT']
        recursive_config_iterator({k: v for k, v in string_dict_or_cp.items() if k != 'DEFAULT'}, cp, {}, True)
    else:
        cp = string_dict_or_cp

    with io.StringIO() as ss:
        cp.write(ss)
        ss.seek(0)
        return ss.read()


def write_config_ini(string_config: Dict[str, str | Dict], location: str, sub_config: str | None = None):
    config_parser = configparser.ConfigParser()
    config_parser.read(location)  # read it so that it can be compared to current state

    sub_config = string_config.get('sub_config', 'default') if not sub_config else sub_config
    config_parser['DEFAULT']['sub_config'] = sub_config

    hashes_for_sections = compute_hashes_for_sections(config_parser)
    config_parser[sub_config] = recursive_config_iterator(
        {k: v for k, v in string_config.items() if k not in non_writable_attributes},
        config_parser,
        hashes_for_sections,
        True
    )

    write_data(config_parser, OutputFormat.INI, location)


def write_config_yaml(config: Config, location: str, sub_config: str | None = None):
    sub_config = config.get('sub_config', 'default') if not sub_config else sub_config

    try:
        with open(location, 'r') as previous_conf:
            to_write = yaml.safe_load(previous_conf)
    except IOError:
        to_write = {}

    to_write.update({'DEFAULT': sub_config})
    to_write.update({sub_config: {k: v for k, v in config.items() if k not in non_writable_attributes}})

    write_data(to_write, OutputFormat.YAML, location)


def write_restricted_config(location: str):
    if location[-4:] == '.ini':
        write_config_ini(config_to_string(True), location)
    elif location[-5:] == '.yaml' or location[-4:] == '.yml':
        write_config_yaml(config_to_string(True), location)
    else:
        raise Exception(f"Expecting some .ini, .yaml or .yml file as configuration input")


def write_config(config: Config, location: str):
    if location[-4:] == '.ini':
        write_config_ini(config_to_string_no_check(config), location)
    elif location[-5:] == '.yaml' or location[-4:] == '.yml':
        write_config_yaml(config_to_string_no_check(config), location)
    else:
        raise Exception(f"Expecting some .ini, .yaml or .yml file as configuration input")


register_config_default('.sub_config', str, 'default')

@config_dependencies(('.sub_config', str))
def write_current_config(config: Config, location: str):
    write_config(config, location)
