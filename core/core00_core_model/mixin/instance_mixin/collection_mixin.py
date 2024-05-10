from functools import reduce

from ....core20_messaging.log.common_loggers import main_logger
from ....core24_datastream.policy.function_call import CallingContractArguments, consume_arguments_method
from ....core05_persistent_model.policy.session import commit_and_rollback_if_exception
from ..meta_mixin.name_from_dependencies_mixin import ChangeClassNameMixin
from ...policy.default_join import SQLJoinBehavior, default_check_joinable
from ...utils.column_type import column_to_type
from .repository_mixin import RepositoryMixin
from .representation_mixin import ReprMixin
from .eagerload_mixin import EagerloadMixin
from .session_mixin import SessionMixin

from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr, joinedload, aliased
from sqlalchemy import Integer, ForeignKey, orm
from typing import List


# it the collection is a set (is_set = True), it implies some unicity constraints on rows
def CollectionMixin(collection_name, metadata_type, entry_type, is_set: bool = False):
    assert getattr(metadata_type, '__tablename__', None), \
        f"Metadata type {metadata_type} does not have mandatory tablename, it must by some SQL Alchemy object" \
        f" to create relation on"
    assert getattr(entry_type, '__tablename__', None), \
        f"Entry type {entry_type} does not have mandatory tablename, it must by some SQL Alchemy object" \
        f" to create relation on"
    assert len(metadata_type.primary_keys) == 1, f"Composite foreign key not supported by CollectionMixin (yet)"
    assert len(entry_type.primary_keys) == 1, f"Composite foreign key not supported by CollectionMixin (yet)"

    metadata_primary_key_name = metadata_type.primary_keys_full[0].key
    mapped_metadata_type, sqlalchemy_metdata_type = column_to_type(metadata_type.primary_keys_full[0])
    mapped_entry_type, sqlalchemy_entry_type = column_to_type(entry_type.primary_keys_full[0])

    print("iciii ", entry_type, entry_type.__tablename__, entry_type.primary_keys_full)

    # metadata_concept must inherit from the repository mixin
    class EntryMixin(ChangeClassNameMixin(metadata_type, entry_type), RepositoryMixin, EagerloadMixin, ReprMixin):

        __tablename__ = f"{collection_name}<{metadata_type.__tablename__}>[{entry_type.__tablename__}]"

        __named_metadata__ = f"metadata<{metadata_type.__tablename__}>"
        __named_entry__ = f"entry<{entry_type.__tablename__}>"

        if not is_set:
            id: Mapped[str] = mapped_column('id', Integer, primary_key=True)

        metadata_id: Mapped[mapped_metadata_type] = mapped_column(__named_metadata__, sqlalchemy_metdata_type,
                                                                  ForeignKey(metadata_type.primary_keys_full[0]),
                                                                  primary_key=is_set)
        entry_id: Mapped[mapped_entry_type] = mapped_column(__named_entry__, sqlalchemy_entry_type,
                                                            ForeignKey(entry_type.primary_keys_full[0]),
                                                            primary_key=is_set)

        @declared_attr
        def metadata_obj(cls) -> Mapped[metadata_type]:
            return relationship(metadata_type, foreign_keys=[cls.metadata_id], backref='__' + cls.__tablename__)

        @declared_attr
        def entry(cls) -> Mapped[entry_type]:
            return relationship(entry_type, foreign_keys=[cls.entry_id], backref='__' + cls.__tablename__)

    class CollectionMixin(EagerloadMixin):

        __metadata__ = metadata_type
        __entry__ = entry_type
        __collection_entry__ = EntryMixin

        __joinable__ = {
            'behavior': SQLJoinBehavior.CUSTOM,
            'argument': 'custom_join',
        }

        @classmethod
        def custom_join(cls, parent, max_depth: int, current_depth: int, join_path: List[type] | None = None):
            if current_depth < 0:  # no eager loading
                return lambda x: x, []
            if current_depth >= max_depth > 0:  # max depth reached
                return lambda x: x, []

            entrycoll_alias = aliased(cls.__collection_entry__)
            additional_to_query = [cls.__metadata__, entrycoll_alias] if not parent else [entrycoll_alias]
            entry_alias = aliased(cls.__entry__, name=f"{cls.__entry__.__tablename__}_{current_depth}")
            children_resolved = []

            for child in [entry_alias, cls.__metadata__ if not parent else parent]:
                if not default_check_joinable() or hasattr(child, 'join'):
                    child_resolved, more_to_query = child.join(child, max_depth, current_depth + 1,
                                                               [entrycoll_alias.entry.of_type(entry_alias)])
                    children_resolved.append(child_resolved)
                    additional_to_query.extend(more_to_query)

            def resolve_query(initial_query):
                resolved = initial_query.join(entrycoll_alias)
                resolved = resolved.outerjoin(aliased(cls.__entry__))
                resolved = resolved.options(joinedload(entrycoll_alias.entry))
                resolved = resolved.options(joinedload(entrycoll_alias.metadata_obj))
                for child_resolved in children_resolved:
                    resolved = child_resolved(resolved)
                return resolved

            return resolve_query, additional_to_query


        @consume_arguments_method({
            'commit': (bool, CallingContractArguments.OneOrNone),
            'metadata': (metadata_type, CallingContractArguments.OneOrNone),
        })
        def __init__(self, commit: bool = True, metadata: metadata_type | None = None, **argv):
            if not metadata:
                metadata = metadata_type.get_create(commit, **argv)
            self.entries_initialized = False
            self.metadata = metadata
            self._entries = []

        @classmethod
        def joined_collections(cls, *args, **argv):  # warning this method is dangerous and should be called during join
            all_entries = cls.get_join(*args, **argv)
            if not all_entries:
                return None

            def aggregate_for_metadata(cur_dict, value):
                per_root = cur_dict.setdefault(getattr(value[0], value[0].primary_keys[0]),
                                               {'metadata': value[0], 'data': {}})['data']
                # either the entry[1] (which is entry following custom_join) is an alias, or it's a normal object
                per_root.setdefault(value[1].entry.aliased_id
                                    if hasattr(value[1].entry, 'aliased_id') else value[1].entry.id,
                                    value[1])
                return cur_dict

            per_metadata = reduce(aggregate_for_metadata, all_entries, {})
            instances = []
            for k, v in per_metadata.items():
                instance = cls(v['metadata'])
                instance._entries = list(v['data'].values())
                instance.entries_initialized = True
                instances.append(instance)
            return instances


        @classmethod
        def create(cls, commit=True, **argv):
            return cls(commit=commit, **argv)

        def entries_updated(self, commit=True):
            self.__metadata__.query \
                .filter_by(**{metadata_primary_key_name: getattr(self.metadata, metadata_primary_key_name)}) \
                .update({})
            if commit:
                commit_and_rollback_if_exception(self.session)

        def update(self, commit=True, **argv):
            if argv:
                self.metadata.fill(**argv).save(commit=commit)
            else:
                self.entries_updated(commit)

        def delete(self, commit=True, with_entries=False):
            if with_entries:
                del self.entries
            self.metadata.delete(commit=commit)

        @property
        def entries(self) -> List[entry_type]:
            if not self.entries_initialized:
                self._entries = self.session \
                    .query(self.__collection_entry__) \
                    .options(joinedload(self.__collection_entry__.entry)) \
                    .filter(self.__collection_entry__.metadata_obj == self.metadata) \
                    .all()
                self.entries_initialized = True
            return [e.entry for e in self._entries]

        @entries.setter
        def entries(self, new_entries: List[entry_type]):
            del self.entries
            self._entries = []
            for entry in new_entries:
                col_entry = self.__collection_entry__.create(metadata_obj=self.metadata, entry=entry, commit=False)
                self.session.add(col_entry)
                self._entries.append(col_entry)
            self.update(commit=False)
            self.entries_initialized = True
            commit_and_rollback_if_exception(self.session)

        @entries.deleter
        def entries(self):
            self.session.query(self.__collection_entry__) \
                .filter(self.__collection_entry__.id.in_([entry.id for entry in self._entries])) \
                .delete(synchronize_session=False)
            self.update(commit=False)
            self.entries_initialized = False
            self._entries = []

        @property
        def join_entries(self):
            self.entries_query = self.session \
                .query(self.__collection_entry__) \
                .options(joinedload(self.__collection_entry__.entry))
            self.entries_query = self.__collection_entry__.join(self.entries_query) \
                .filter(self.__collection_entry__.metadata_obj == self.metadata)
            self._entries = self.entries_query.all()
            self.entries_initialized = True

        def __repr__(self):
            entries = '\n- '.join(map(repr, self.entries))
            return f"{self.metadata}" + f"\n- {entries}" if entries else ''

        @classmethod
        def get_for(cls, **attrs):
            metadata = cls.__metadata__.query.filter_by(**attrs).one_or_none()
            return cls(metadata) if metadata else None

        @classmethod
        def get_create(cls, commit=True, **attrs):
            existing = cls.get_for(**attrs)
            return existing if existing else cls(commit=commit, **attrs)

        @classmethod
        def all_for(cls, join=False, **attrs):
            result = [cls(m) for m in cls.__metadata__.query.filter_by(**attrs).all()]
            if join:
                for coll in result:
                    coll.join_entries()
            return result

        @classmethod
        def all_for_condition(cls, condition, join=False):
            result = [cls(m) for m in cls.__metadata__.query.filter(condition).all()]
            if join:
                for coll in result:
                    coll.join_entries()
            return result

    return CollectionMixin
