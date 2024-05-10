from ....core24_datastream.policy.function_call import CallingContractArguments, consume_arguments_method
from ...policy.default_join import SQLJoinBehavior, default_check_joinable
from ...mixin.instance_mixin.repository_mixin import RepositoryMixin
from ...mixin.instance_mixin.eagerload_mixin import EagerloadMixin
from ....core05_persistent_model.policy.session import get_session
from ...mixin.meta_mixin.proxy_to import ProxyToMixin
from ...utils.column_type import column_to_type
from ...mixin.base_mixin import BaseMixinsNoJoin
from ...concept.named import Named

from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr, joinedload, aliased
from sqlalchemy import ForeignKey, orm
from typing import List


class Aliases(*BaseMixinsNoJoin, Named):
    __tablename__ = 'table_aliases'

    detail: Mapped[str]


alias_prefix = 'ALIAS'


def ALIAS(alias_target_class, alias_name: str, keep_full_name: bool = False):
    # this only case is when the class is simple (collections cannot inherit from the RepositoryMixin)
    is_simple = RepositoryMixin in alias_target_class.__mro__
    # either the class itself, or the metadata must be inspectable (for getting its primary key)
    alias_target = alias_target_class if is_simple else alias_target_class.__metadata__
    print("atbeg ", alias_target_class, is_simple, "=> ", alias_target)

    full_tablename = f"{alias_prefix}<{alias_target.__tablename__}({alias_name})>" \
        if not hasattr(alias_target_class, '__collection_entry__') \
        else f"{alias_prefix}<{alias_target_class.__collection_entry__.__tablename__}({alias_name})>"

    with get_session() as _:
        Aliases.get_create(name=alias_name, detail=full_tablename.replace(f"({alias_name})", ''))

    assert getattr(alias_target, '__tablename__', None), \
        f"Target class {alias_target} does not have mandatory tablename, it must by some SQL Alchemy object" \
        f" to create relation on"
    assert len(alias_target.primary_keys) == 1, f"Composite foreign key not supported by Alias class (yet)"

    alias_target_primary_key_name = alias_target.primary_keys_full[0].key
    print("the types?")
    print(alias_target_primary_key_name)
    mapped_alias_target_type, sqlalchemy_alias_target_type = column_to_type(alias_target.primary_keys_full[0])
    print(mapped_alias_target_type, sqlalchemy_alias_target_type)

    class Alias(ProxyToMixin(alias_target,
                             *([alias_target_class.__entry__] if hasattr(alias_target_class, '__collection_entry__')
                             else [])),
                EagerloadMixin, RepositoryMixin):

        __tablename__ = full_tablename if keep_full_name else alias_name
        __metadata_target__ = alias_target
        __target__ = alias_target_class

        __named_target__ = f"target<{alias_target.__tablename__}>"

        __joinable__ = {
            'behavior': SQLJoinBehavior.CUSTOM,
            'argument': 'custom_join',
        }

        @classmethod
        def custom_join(cls, parent, max_depth: int, current_depth: int,
                        join_path: List[type] | None = None):
            if current_depth < 0:  # no eager loading
                return lambda x: x, []
            if current_depth >= max_depth > 0:  # max depth reached
                return lambda x: x, []

            cls_or_parent = cls if not parent else parent
            metadata_alias = aliased(cls_or_parent.__metadata_target__)
            additional_to_query = []
            child_resolved = None
            if not default_check_joinable() or hasattr(cls_or_parent.__target__, 'join'):
                child_resolved, more_to_query = cls_or_parent.__target__.join(metadata_alias,
                                                                              max_depth, current_depth + 1,
                                                                              join_path)
                additional_to_query.extend(more_to_query)

            def resolve_query(initial_query):
                resolved = initial_query.outerjoin(metadata_alias)
                print(resolved)
                print(join_path[0].expression, cls_or_parent.aliased, parent)
                resolved = resolved.options(joinedload(*join_path, cls_or_parent.aliased))
                if child_resolved:
                    resolved = child_resolved(resolved)
                # resolved = resolved.group_by(getattr(metadata, metadata.primary_keys[0]))
                return resolved

            return resolve_query, additional_to_query

        aliased_id: Mapped[mapped_alias_target_type] = mapped_column(__named_target__, sqlalchemy_alias_target_type,
                                                                     ForeignKey(alias_target.primary_keys_full[0]),
                                                                     primary_key=True)

        @declared_attr
        def aliased(cls) -> Mapped[alias_target]:
            return relationship(alias_target, foreign_keys=[cls.aliased_id], backref='__'+full_tablename)

        @property
        def target(self):
            return self._base_object

        @target.setter
        def target(self):
            raise NotImplementedError

        @target.deleter
        def target(self):
            raise NotImplementedError

        @consume_arguments_method({
            'commit': (bool, CallingContractArguments.OneOrNone),
            'target': (alias_target, CallingContractArguments.OneOrNone),
            'target_class': (alias_target_class, CallingContractArguments.OneOrNone),  # in case of provided collection
        }, permit_multiple_types=True)
        def __init__(self, commit: bool = True,
                     target: alias_target | None = None,
                     target_class: alias_target_class | None = None,
                     **argv):
            print("CONSTRUCTING")
            print(target, target_class, argv)
            if is_simple and target_class:
                raise Exception(f"Not expecting {target_class} twice (already got target = {target})")
            if target_class:
                self.aliased = target_class.metadata
                self._base_object = target_class
            elif target:
                self.aliased = target
                self._base_object = target if is_simple else alias_target_class(self.aliased, commit=commit)
            else:
                if not argv:  # will not construct the object, waiting for a proper initialization afterwards
                    return
                print("HOLE ", alias_target_class, argv)
                self._base_object = alias_target.get_create(commit=commit, **argv) if is_simple \
                    else alias_target_class.get_create(commit=commit, **argv)
                print(self._base_object, is_simple, self._base_object.metadata, type(self._base_object.metadata),
                      type(self._base_object))
                self.aliased = self._base_object if is_simple else self._base_object.metadata
            if commit:
                self.ensure_target()

        @orm.reconstructor
        def init_on_load(self):
            self._base_object = self.aliased if is_simple else alias_target_class(self.aliased, commit=False)

        def ensure_target(self):
            # according to whether the provided object comes from DB (has his primary key set) or not, create the target
            if not hasattr(self.aliased, alias_target_primary_key_name) \
                    or not getattr(self.aliased, alias_target_primary_key_name):
                print("OLE2 ", self.aliased, type(self.aliased))
                attrs = {col: getattr(self.aliased, col) for col in self.aliased.columns}
                not_null_attrs = {k: v for k, v in attrs.items() if v}
                all_for = self.aliased.all_for(**not_null_attrs)
                if len(all_for) > 1:
                    raise Exception(f"Too much values for {alias_target} found with criteria: {not_null_attrs}, "
                                    f"either commit=False or add unicity constraint")
                if not all_for:
                    self.aliased.create(commit=True, **not_null_attrs)

        def __getattr__(self, item):
            if item == '_base_object':  # the object is not yet initialized, it causes infinite recursion
                return None
            return getattr(self._base_object, item)

        def __repr__(self):
            return '{' + f"alias #{self.aliased_id} -> {self._base_object}" + '}'

    return Alias
