from ....core05_persistent_model.sql_bases import add_sql_base

from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from functools import reduce


class MergeMapperArgsMeta(DeclarativeMeta):

    def __new__(mcls, name, bases, dict):
        def merge(cur_dict, value):
            cur_dict.update(getattr(value, '__mapper_args__', {}))
            return cur_dict
        mapper_args = reduce(merge, bases, {})
        mapper_args.update(dict.get('__mapper_args__', {}))
        return DeclarativeMeta.__new__(mcls, name, bases,
                                       {**dict, '__mapper_args__': mapper_args} if mapper_args else dict)


MergeMapperArgsMixin = declarative_base(metaclass=MergeMapperArgsMeta)

add_sql_base(MergeMapperArgsMixin)
