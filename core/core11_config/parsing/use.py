from ...core31_policy.misc.dict_operations import update_dict_check_already_there
from ...core31_policy.exception.strictness import raise_exception
from ..config import enrich_config, nested_dict_to_dict
from ...core30_context.context import current_ctxt
from ..policy.read_config import parse_config

from argparse import Namespace


arguments_use = [
    (['subconfig'], {'help': 'Sub-configuration block to use (set as default)'}),
]


def convert_conf_and_enrich(parsed_config_file, config_dict=None):
    if config_dict is None:
        config_dict = {}
    parsed_config_file_flat = nested_dict_to_dict(parsed_config_file)
    common_keys = update_dict_check_already_there(config_dict, parsed_config_file_flat)
    try:  # not very clean, TODO: find a cleaner alternative to raise the appropriate exception in raise_exception
        try:  # we do this to have a cleaner error message when the parsing failed because of some enum
            enrich_config(config_dict)
        except Exception as e:
            raise Exception(f"Unable to enrich parsing ({e}), please check all enums within your config"
                            f" (config help if needed)") from e
    except Exception as e:
        raise_exception(e)
    return common_keys


def config_use(parsed: Namespace):
    config = current_ctxt()['config']
    location = config['config_location']
    config_dict_from_file = parse_config(location, parsed.subconfig)
    convert_conf_and_enrich(config_dict_from_file, None)
