from .introspection_mixin import IntrospectionMixin

from sqlalchemy import inspect


# mostly inspired from https://github.com/absent1706/sqlalchemy-mixins/blob/master/sqlalchemy_mixins/repr.py

class ReprMixin(IntrospectionMixin):
    __abstract__ = True

    __repr_attrs__ = []

    @classmethod
    def class_to_json(cls, max_nesting=-1, cur_nesting=0):
        return {
            'classname': cls.__name__,
            'tablename': cls.__tablename__,
            'attrs': {
                **{
                    k: getattr(cls, k).type for k in cls.columns
                },
                **{
                    k: '[...]' if cur_nesting >= max_nesting >= 0 else
                    (getattr(cls.__mapper__.attrs, k).argument.class_to_json(max_nesting, cur_nesting + 1)
                     if hasattr(getattr(cls.__mapper__.attrs, k).argument, 'class_to_json')
                     else getattr(cls.__mapper__.attrs, k).argument) for k in cls.relations
                }
            }
        }

    def self_to_json(self, max_nesting=-1, cur_nesting=0):
        return {
            'id': self._id_str,
            'classname': self.__class__.__name__,
            'tablename': self.__class__.__tablename__,
            'attrs': {
                **{
                    k: getattr(self, k) for k in self.columns
                },
                **{
                    k: '[...]' if cur_nesting >= max_nesting >= 0 else
                    (getattr(self, k).self_to_json(max_nesting, cur_nesting + 1)
                     if hasattr(getattr(self, k), 'self_to_json')
                     else getattr(self, k)) for k in self.relations if k[:2] != '__'
                }
            }
        }

    @property
    def _id_str(self):
        ids = inspect(self).identity
        if ids:
            return '-'.join([str(x) for x in ids]) if len(ids) > 1 \
                else str(ids[0])
        else:
            return 'None'

    @property
    def _repr_attrs_str(self):
        attrs = self.__repr_attrs__ if self.__repr_attrs__ else self.columns + \
                                                                [k for k in self.relations if k[:2] != '__']
        values = []
        for key in attrs:
            if key in self.primary_keys:
                continue
            value = getattr(self, key)
            wrap_in_quote = isinstance(value, str)
            if wrap_in_quote:
                value = f"'{value}'"
            values.append(f"{key}={value}")
        return ', '.join(values)

    def __repr__(self):
        repr_attrs = self._repr_attrs_str
        return '{'+f"{self.__class__.__tablename__} #{self._id_str}{' '+repr_attrs if repr_attrs else ''}"+'}'
