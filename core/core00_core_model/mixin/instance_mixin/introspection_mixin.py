from ...utils.class_property import classproperty

from sqlalchemy.ext.hybrid import HybridExtensionType
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy import inspect


# mostly inspired from https://github.com/absent1706/sqlalchemy-mixins/blob/master/sqlalchemy_mixins/inspection.py

class IntrospectionMixin:

    @classproperty
    def columns(cls):
        return inspect(cls).columns.keys()

    @classproperty
    def primary_keys_full(cls):
        mapper = cls.__mapper__
        return [
            mapper.get_property_by_column(column)
            for column in mapper.primary_key
        ]

    @classproperty
    def primary_keys(cls):
        return [pk.key for pk in cls.primary_keys_full]

    @classproperty
    def relations(cls):
        return [c.key for c in cls.__mapper__.attrs
                if isinstance(c, RelationshipProperty)]

    # TODO: test it
    @classproperty
    def hybrid_properties(cls):
        items = inspect(cls).all_orm_descriptors
        return [item.__name__ for item in items
                if item.extension_type == HybridExtensionType]
