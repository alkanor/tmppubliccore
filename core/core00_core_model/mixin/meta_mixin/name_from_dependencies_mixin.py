from .create_table_when_engine_mixin import AutoTableCreationMeta
from ....core05_persistent_model.sql_bases import add_sql_base
from ...utils.naming import classname_for

from sqlalchemy.ext.declarative import declarative_base


_cached_classes = {}

def ChangeClassNameMixinAndMeta(*SQLAlchemyObjects):
    classname = classname_for(*SQLAlchemyObjects)
    if _cached_classes.get(classname):
        return _cached_classes[classname]

    class ChangeClassNameMeta(AutoTableCreationMeta):
        def __new__(mcls, name, bases, dict):
            return AutoTableCreationMeta.__new__(mcls, f"{name}<{classname}>", bases, dict)

    _ChangeClassNameMixin = declarative_base(metaclass=ChangeClassNameMeta)
    _cached_classes[classname] = _ChangeClassNameMixin, ChangeClassNameMeta
    add_sql_base(_cached_classes[classname][0])
    return _cached_classes[classname]


def ChangeClassNameMixin(*SQLAlchemyObjects):
    return ChangeClassNameMixinAndMeta(*SQLAlchemyObjects)[0]

def ChangeClassNameMeta(*SQLAlchemyObjects):
    return ChangeClassNameMixinAndMeta(*SQLAlchemyObjects)[1]
