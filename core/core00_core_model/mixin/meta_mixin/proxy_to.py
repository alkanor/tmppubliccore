from ....core05_persistent_model.sql_bases import add_sql_base
from .name_from_dependencies_mixin import ChangeClassNameMeta
from ...utils.naming import classname_for

from sqlalchemy.ext.declarative import declarative_base


_cached_classes = {}

def ProxyToMeta(SQLAlchemyTarget, *additional_types):
    classname = classname_for(SQLAlchemyTarget, *additional_types)
    if _cached_classes.get(classname):
        return _cached_classes[classname]

    class ProxyToMeta(ChangeClassNameMeta(SQLAlchemyTarget, *additional_types)):
        def __getattr__(*args, **argv):
            return getattr(SQLAlchemyTarget, args[1]) if len(args) >= 2 else \
                getattr(SQLAlchemyTarget, args[0])

    _ProxyToMixin = declarative_base(metaclass=ProxyToMeta)
    _cached_classes[classname] = _ProxyToMixin, ProxyToMeta
    add_sql_base(_cached_classes[classname][0])
    return _cached_classes[classname]


def ProxyToMixin(SQLAlchemyTarget, *additional_types):
    return ProxyToMeta(SQLAlchemyTarget, *additional_types)[0]
