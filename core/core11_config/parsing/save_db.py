from ..config import Config, config_dependencies


arguments_save_db = [
    (['--name', '-n'], {'help': 'Configuration name to save config as in database'}),
]

@config_dependencies(('.database', str))
def config_save_db(config: Config, db_name: str):
    raise NotImplementedError
