from ...core11_config.config import config_dependencies, Config
from .log_level import LogLevel

import logging


@config_dependencies(('.log.log_level', LogLevel))
def get_logger(config: Config, name: str):
    logger = logging.getLogger(name)
    logger.setLevel(config['log']['log_level'].value)

    handler = logging.StreamHandler()
    handler.setLevel(config['log']['log_level'].value)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S')
    handler.setFormatter(formatter)

    for hdlr in logger.handlers[:]:
        logger.removeHandler(hdlr)
        logger.handlers.clear()
        logger.propagate = False

    logger.addHandler(handler)

    return logger
