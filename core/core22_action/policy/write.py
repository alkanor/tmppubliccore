from ...core11_config.config import register_config_default, config_dependencies, Config
from ...core30_context.context_dependency_graph import context_producer, context_dependencies
from ...core30_context.context import Context
from .send import default_send_cli

from typing import Callable, Any
from logging import Logger
from enum import Enum, auto
import os.path
import json
import yaml


class WriteOnExistingFile(Enum):
    RAISE = auto()
    WARNING_DONT_DO = auto()
    WARNING_DO = auto()
    APPEND = auto()
    SILENT_DONT_DO = auto()
    SILENT_DO = auto()
    ASK = auto()


class EnforceFormatFromExt(Enum):
    EXT_TO_FORMAT = auto()
    DONT_CARE = auto()


class OutputFormat(Enum):
    TEXT = auto()
    JSON = auto()
    YAML = auto()
    INI = auto()


class OutputFormatPolicy(Enum):
    FORCE_TO_FILE_EXTENSION = auto()
    FORCE_TO_GIVEN_FORMAT = auto()
    FORCE_TO_FILE_EXTENSION_WITH_WARNING = auto()
    FORCE_TO_GIVEN_FORMAT_WITH_WARNING = auto()
    ASK_IF_EXTENSION_DOES_NOT_MATCH = auto()


register_config_default('.interactor.output.file.rewrite_behavior', WriteOnExistingFile,
                        WriteOnExistingFile.ASK)
register_config_default('.interactor.output.file.rewrite_behavior_if_forced', WriteOnExistingFile,
                        WriteOnExistingFile.WARNING_DO)
register_config_default('.interactor.output.ext_behavior', EnforceFormatFromExt, EnforceFormatFromExt.EXT_TO_FORMAT)
register_config_default('.interactor.output.format', OutputFormat, OutputFormat.TEXT)
register_config_default('.interactor.output.output_format_policy', OutputFormatPolicy,
                        OutputFormatPolicy.ASK_IF_EXTENSION_DOES_NOT_MATCH)


@config_dependencies(('.interactor.output.output_format_policy', OutputFormatPolicy),
                     ('.interactor.output.ext_behavior', EnforceFormatFromExt),
                     ('.interactor.output.format', OutputFormat))
@context_dependencies(('.log.debug_logger', Logger | None), ('.log.main_logger', Logger),
                      ('.interactor.ask', Callable[[...], str]))
def format_data(ctxt: Context, config: Config, data: Any, output_format: OutputFormat | None, destination: Any):
    if not destination:  # this case is the default with the interactor write to, so get the config option
        fmt = config['interactor']['output']['format'] if not output_format else output_format
    elif isinstance(destination, str):  # this case we should have an output file (in the future it may change)
        if config['interactor']['output']['ext_behavior'] == EnforceFormatFromExt.DONT_CARE:
            fmt = config['interactor']['output']['format'] if not output_format else output_format
        else:
            lower_dst = destination[-5:].lower()
            if lower_dst == '.json':
                fmt = OutputFormat.JSON
            elif lower_dst == '.yaml' or lower_dst[-4:] == '.yml':
                fmt = OutputFormat.YAML
            elif lower_dst[-4:] == '.ini':
                fmt = OutputFormat.INI
            else:
                fmt = OutputFormat.TEXT
            if output_format and fmt != output_format:
                of_policy = config['interactor']['output']['output_format_policy']
                if of_policy == OutputFormatPolicy.FORCE_TO_FILE_EXTENSION:
                    ctxt['log']['debug_logger'].debug(f"Specified output format {output_format}"
                                                      f" not considered regarding extension {fmt}")
                elif of_policy == OutputFormatPolicy.FORCE_TO_FILE_EXTENSION_WITH_WARNING:
                    ctxt['log']['main_logger'].warning(f"Specified output format {output_format}"
                                                       f" not considered regarding extension {fmt}")
                elif of_policy == OutputFormatPolicy.FORCE_TO_GIVEN_FORMAT:
                    fmt = output_format
                    ctxt['log']['debug_logger'].debug(f"Specified output format {output_format} forced,"
                                                      f" not matching the file extension")
                elif of_policy == OutputFormatPolicy.FORCE_TO_GIVEN_FORMAT_WITH_WARNING:
                    fmt = output_format
                    ctxt['log']['main_logger'].warning(f"Specified output format {output_format} forced,"
                                                       f" not matching the file extension")
                else:
                    keep_format_content = ctxt['interactor']['ask_boolean']({'k': True, 'c': False}) \
                        (f"Extension not matching output format {output_format}, do you want to keep provided format"
                         f" (k) or change to match the file extension to {fmt} (c)?")
                    if keep_format_content:
                        fmt = output_format
    else:
        raise NotImplementedError

    if fmt == OutputFormat.TEXT:
        return f"{data}"
    elif fmt == OutputFormat.JSON:
        return json.dumps(data)
    elif fmt == OutputFormat.YAML:
        return yaml.dump(data)
    elif fmt == OutputFormat.INI:
        from ...core11_config.policy.write_config import format_ini_dict
        return format_ini_dict(data)
    else:
        raise NotImplementedError


@config_dependencies(('.interactor.output.file.rewrite_behavior', WriteOnExistingFile),
                     ('.interactor.output.file.rewrite_behavior_if_forced', WriteOnExistingFile))
@context_dependencies(('.interactor.output.write_to', Callable[[str], None]), ('.log.main_logger', Logger),
                      ('.interactor.local', bool, False), ('.interactor.cli', bool, False),
                      ('.interactor.ask', Callable[[...], str]))
def write_data(ctxt: Context, config: Config, input_data: Any, output_format: OutputFormat,
               destination: Any | None = None, **additional_arguments):
    formatted_data = format_data(input_data, output_format, destination)
    if not destination:
        return ctxt['interactor']['output']['write_to'](formatted_data)
    elif isinstance(destination, str):  # this case we should have an output file (in the future it may change)
        already_existing = os.path.isfile(destination)
        mode = 'w'
        do_ok = True
        if already_existing:
            if 'force' in additional_arguments and additional_arguments['force']:
                policy = config['interactor']['output']['file']['rewrite_behavior_if_forced']
            else:
                policy = config['interactor']['output']['file']['rewrite_behavior']
            if policy == WriteOnExistingFile.RAISE:
                raise Exception(f"Forbidden attempt to rewrite file {destination}")
            elif policy == WriteOnExistingFile.WARNING_DO:
                ctxt['log']['main_logger'].warning(f"File {destination} will be rewritten with new data "
                                                   f"due to current policy")
            elif policy == WriteOnExistingFile.WARNING_DONT_DO:
                ctxt['log']['main_logger'].warning(f"File {destination} won't be rewritten with new data "
                                                   f"due to current policy")
                do_ok = False
            elif policy == WriteOnExistingFile.APPEND:
                mode = 'a'
            elif policy == WriteOnExistingFile.SILENT_DONT_DO:
                do_ok = False
            elif policy == WriteOnExistingFile.ASK:
                do_ok = ctxt['interactor']['ask_boolean']({'r': True, 'a': False}) \
                    (f"File {destination} already existing, rewrite (r) or abort (a)?")
            else:
                raise NotImplementedError

        if do_ok:
            with open(destination, mode) as f:
                f.write(formatted_data)
    else:
        raise NotImplementedError  # future cases: network send, database send, C2 send, etc ...


@context_producer(('.interactor.output.write_to', Callable[[str], None]))
@context_dependencies(('.interactor.local', bool, False), ('.interactor.cli', bool, False))  # dynamically generated
def output_write_to(ctxt: Context):
    if ctxt['interactor']['local'] and ctxt['interactor']['type'] == 'cli':
        ctxt['interactor'].setdefault('output', {})['write_to'] = default_send_cli
    else:
        raise NotImplementedError
