from ...policy.default_join import default_check_joinable, SQLJoinBehavior, default_sql_join_policy
from .introspection_mixin import IntrospectionMixin
from .session_mixin import SessionMixin

from typing import Callable, List, Tuple, Any
from sqlalchemy.orm import Query, joinedload, aliased
from sqlalchemy.sql import expression


class EagerloadMixin(SessionMixin, IntrospectionMixin):

    __abstract__ = True

    @classmethod
    def _default_join_internal(cls, parent, max_depth: int, current_depth: int,
                               join_path: List[type] | None = None, join_on: List[str] | None = None) \
            -> Tuple[Callable[[Query], Query], List[type]]:
        if current_depth < 0:  # no eager loading
            return lambda x: x, []
        if current_depth >= max_depth > 0:  # max depth reached
            return lambda x: x, []

        current_alias = aliased(cls) if parent else cls  # create an alias if the current query has already a root
        join_path_copy = [] if not join_path else [cl for cl in join_path]
        relation_keys = cls.relations if not join_on else join_on
        additional_to_query = []
        joined_load_list = []
        children_resolved = []
        for key in relation_keys:
            if key[:2] != '__':  # otherwise these are indicative backref that would lead to infinite back & forth
                column_path = getattr(current_alias, key)
                next_join_path = join_path_copy + [column_path]
                joined_load_list.append(joinedload(*next_join_path))
                if not default_check_joinable() or hasattr(column_path.prop.argument, 'join'):
                    resolved, more_to_query = column_path.prop.argument.join(current_alias, max_depth, current_depth+1,
                                                                             next_join_path)
                    additional_to_query.extend(more_to_query)
                    children_resolved.append(resolved)

        def resolve_query(initial_query):
            resolved = initial_query
            if parent:  # otherwise the current class is in the bases for query object
                resolved = resolved.outerjoin(current_alias)
            for joined_load in joined_load_list:
                resolved = resolved.options(joined_load)
            for child in children_resolved:
                resolved = child(resolved)
            return resolved

        return resolve_query, additional_to_query

    @classmethod
    def join(cls, parent=None, max_depth: int = -1, current_depth: int = 0,
             join_path: List[type] | None = None):
        joinable_obj = getattr(cls, '__joinable__', {})
        if not joinable_obj:
            behavior, *args = default_sql_join_policy()
            if args:
                joinable_obj['argument'] = args[0]
            joinable_obj['behavior'] = behavior

        def join_dispatch(joinable_obj):
            match joinable_obj['behavior']:
                case SQLJoinBehavior.EAGER_ALL:
                    return cls._default_join_internal(parent, max_depth, current_depth, join_path,
                                                      joinable_obj.get('join_on', None))
                case SQLJoinBehavior.MAX_DEPTH:
                    if max_depth < 0 or joinable_obj['argument'] < max_depth:
                        new_max_depth = joinable_obj['argument']  # reduce max depth of subtree if inferior to current
                    return cls._default_join_internal(parent, new_max_depth, current_depth, join_path,
                                                      joinable_obj.get('join_on', None))
                case SQLJoinBehavior.IN_CONTEXT:
                    new_behavior, *new_args = default_sql_join_policy()
                    assert behavior != SQLJoinBehavior.IN_CONTEXT, \
                        'Should not happen in join_dispatch, assert to avoid infinite loop, check the ' \
                        'default_sql_join_policy function to ensure it does not return SQLJoinBehavior.IN_CONTEXT'
                    new_joinable_obj = {
                        'behavior': new_behavior,
                        'argument': new_args[0]
                    }
                    return join_dispatch(new_joinable_obj)
                case SQLJoinBehavior.CUSTOM:
                    return getattr(cls, joinable_obj['argument'])(parent, max_depth, current_depth, join_path)
                case SQLJoinBehavior.NO_LOAD:
                    return cls._default_join_internal(parent, max_depth, -1, join_path,
                                                      joinable_obj.get('join_on', None))
                case _:
                    raise NotImplementedError

        return join_dispatch(joinable_obj)

    @classmethod
    def get_join(cls, *args, **argv):
        query_func, all_objs = cls.join()
        all_objs = all_objs if not hasattr(cls, '__tablename__') else [cls] + all_objs
        initial_query = cls.session.query(*all_objs).filter_by(**argv).filter(*args)
        print(all_objs, initial_query)
        return query_func(initial_query).all()

    @classmethod
    def get_join_with(cls, joined_tables_and_filters: List[Tuple[Any, expression | List[expression]]], *args, **argv):
        query_func, all_objs = cls.join()
        all_objs = all_objs if not hasattr(cls, '__tablename__') else [cls] + all_objs
        all_objs = [all_objs[0]] + [table[0] if hasattr(table, '__iter__') else table
                                    for table, expr in joined_tables_and_filters] + all_objs[1:]
        initial_query = cls.session.query(*all_objs).filter_by(**argv).filter(*args)
        for obj, conditions in joined_tables_and_filters:
            if hasattr(obj, '__iter__'):
                args = obj
            else:
                args = [obj]
            print(obj, conditions, args)
            if hasattr(conditions, '__iter__'):
                initial_query = initial_query.join(*args).filter(*conditions)
            else:
                initial_query = initial_query.join(*args).filter(conditions)
            print(initial_query)
        return query_func(initial_query).all()
