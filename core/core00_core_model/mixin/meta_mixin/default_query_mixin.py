from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .name_from_dependencies_mixin import ChangeClassNameMeta
from ...utils.column_type import column_to_type
from ....core05_persistent_model.sql_bases import add_sql_base
from ...utils.naming import classname_for, tablename_for

from sqlalchemy.ext.declarative import declarative_base

from ....core24_datastream.policy.function_call import consume_arguments_method, CallingContractArguments


from ....core05_persistent_model.sql_bases import add_sql_base
from .name_from_dependencies_mixin import ChangeClassNameMeta
from ...utils.naming import classname_for

from sqlalchemy.ext.declarative import declarative_base


# any SQLAlchemyObject is either a SQLAlchemyObject or a tuple (SQLAlchemyObject, name, additional column attributes)
# the named_auto_methods argument is under the form {method_name: (query_type, *required_SQLAlchemyObjects)}
def DefautQueryMixinMeta(*SQLAlchemyObjectsOrTuples, **named_auto_methods):
    converted_attributes = [
        (x, x.__tablename__.lower(), {}) if not hasattr(x, '__iter__') else x
        for x in SQLAlchemyObjectsOrTuples
    ]
    SQLAlchemyObjects = [x[0] for x in converted_attributes]

    tablename_hint = tablename_for(*SQLAlchemyObjects)

    extended_attributes_fk = {
        f"{attr[1]}_id": mapped_column(ForeignKey(attr[0].primary_keys[0]), **attr[2]) for attr in converted_attributes
    }

    extended_attributes_relations = {
        attr[1]: relationship(attr[0], foreign_keys=[extended_attributes_fk[f"{attr[1]}_id"]])
        for attr in converted_attributes
    }

    main_decorator = consume_arguments_method({
        **{
            f"{attr[1]}_id": (column_to_type(extended_attributes_relations[attr[1]].primary_keys_full[0]),
                      CallingContractArguments.OneOrNone)
            for attr in converted_attributes
        },
        **{
            attr[1]: (attr[0], CallingContractArguments.OneOrNone)
            for attr in converted_attributes
        }
    })

    @classmethod
    @main_decorator
    def get_all():
        pass

    @classmethod
    @main_decorator
    def count():
        pass

    @classmethod
    @main_decorator
    def aggregate():
        pass

    default_methods = [
        get_all,
        count,
        aggregate,
    ]

    class DefautQueryMeta(ChangeClassNameMeta(*SQLAlchemyObjects)):
        def __new__(mcls, name, bases, dict):
            for arg in dict:
                assert (arg not in extended_attributes_fk.keys() + extended_attributes_relations.keys()),\
                    f"Attribute name {arg} cannot be set twice in DefaultQueryMixin"
            dict.update(extended_attributes_fk)
            dict.update(extended_attributes_relations)
            dict.update(default_methods)
            return ChangeClassNameMeta.__new__(mcls, f"{dict['__tablename__']}<{tablename_hint}>", bases, dict)

    _DefautQueryMixin = declarative_base(metaclass=DefautQueryMeta)
    return _DefautQueryMixin, DefautQueryMeta


def DefautQueryMixin(*SQLAlchemyObjectsOrTuples, **named_auto_methods):
    return DefautQueryMixinMeta(*SQLAlchemyObjectsOrTuples, **named_auto_methods)[0]
