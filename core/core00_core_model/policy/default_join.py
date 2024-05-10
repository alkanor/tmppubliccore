from ...core11_config.config import register_config_default, config_dependencies, Config

import enum


class SQLJoinCheckPolicy(enum.Enum):
    FORCE_JOIN = enum.auto()
    CHECK_IF_JOINABLE = enum.auto()

register_config_default('.misc.sql_join_check', SQLJoinCheckPolicy, SQLJoinCheckPolicy.CHECK_IF_JOINABLE)


class SQLJoinBehavior(enum.Enum):
    EAGER_ALL = enum.auto()   # eagerly load all children
    MAX_DEPTH = enum.auto()   # defined according to the maximum recursion depth
    IN_CONTEXT = enum.auto()  # defined according to context, config, policy
    CUSTOM = enum.auto()      # defined within the class
    NO_LOAD = enum.auto()     # this should almost never be used, as it does not allow to load anything recursively

register_config_default('.misc.sql_join_behavior', SQLJoinBehavior, SQLJoinBehavior.EAGER_ALL)
register_config_default('.misc.sql_join_maxdepth', int, 4)


@config_dependencies(('.misc.sql_join_check', SQLJoinCheckPolicy))
def default_check_joinable(config: Config):
    return config['misc']['sql_join_check'] == SQLJoinCheckPolicy.CHECK_IF_JOINABLE

@config_dependencies(('.misc.sql_join_behavior', SQLJoinBehavior), ('.misc.sql_join_maxdepth', int))
def default_sql_join_policy(config: Config):  # this function is called when IN_CONTEXT is encountered is specified
    match config['misc']['sql_join_behavior']:
        case SQLJoinBehavior.EAGER_ALL | SQLJoinBehavior.CUSTOM | SQLJoinBehavior.NO_LOAD:
            return (config['misc']['sql_join_behavior'], )
        case SQLJoinBehavior.MAX_DEPTH:
            return (config['misc']['sql_join_behavior'], config['misc']['sql_join_maxdepth'])
        case SQLJoinBehavior.IN_CONTEXT:
            raise Exception("SQLJoinBehavior.IN_CONTEXT join policy should never be an option in "
                            "default_sql_join_policy (otherwise it would infinite loop)")
        case _:
            raise NotImplementedError
