from tests.core00_core_model.datastructure.base.common import init


if __name__ == "__main__":
    init()

    from core.core05_persistent_model.policy.session import get_session, commit_and_rollback_if_exception
    from core.core00_core_model.mixin.instance_mixin.collection_mixin import CollectionMixin
    from core.core00_core_model.mixin.instance_mixin.version_mixin import VersionMixin
    from core.core00_core_model.concept.timed import CreatedModifiedAt
    from core.core00_core_model.datastructure.base.alias import ALIAS
    from core.core20_messaging.log.common_loggers import debug_logger
    from core.core00_core_model.mixin.base_mixin import BaseMixins
    from core.core00_core_model.concept.merge import merge_concepts
    from core.core00_core_model.concept.named import Named
    #from sqlalchemy.orm import joinedload, aliased
    from sqlalchemy.orm import Mapped, mapped_column, relationship
    from sqlalchemy import or_, String, Integer, UniqueConstraint, ForeignKey

    logger = debug_logger()

    named_and_createdmodified_at = merge_concepts(Named, CreatedModifiedAt)


    class BaseObject(VersionMixin, *BaseMixins, named_and_createdmodified_at):
        __tablename__ = 'basicobject'
        notid: Mapped[int] = mapped_column(Integer, nullable=True)
        value: Mapped[str] = mapped_column(String, unique=True)

    class BaseUser(VersionMixin, *BaseMixins, named_and_createdmodified_at):
        __tablename__ = 'basicuser'

    class BaseMetadata(*BaseMixins, named_and_createdmodified_at):
        __tablename__ = 'named_dated'

    class BaseList(CollectionMixin('BASICLIST', BaseMetadata, BaseObject)):
        def add(self, entry, commit=False):
            coll_entry = self.__collection_entry__.create(metadata_obj=self.metadata, entry=entry, commit=False)
            self.session.add(coll_entry)
            if commit:
                commit_and_rollback_if_exception(self.session)
            self._entries.append(coll_entry)

    ALIAS_LIST = ALIAS(BaseList, 'basic_list_baseobjects')
    class ComplexList(CollectionMixin('LISTOFLIST', BaseMetadata, ALIAS_LIST)):
        def add(self, entry, commit=False):
            coll_entry = self.__collection_entry__.create(metadata_obj=self.metadata, entry=entry, commit=False)
            self.session.add(coll_entry)
            if commit:
                commit_and_rollback_if_exception(self.session)
            self._entries.append(coll_entry)
    COMPLEX_LIST = ALIAS(ComplexList, 'complext_list')

    class ACL(*BaseMixins):
        __tablename__ = 'basicacl'
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        object_id: Mapped[str] = mapped_column(ForeignKey(BaseObject.name), nullable=False)
        user_id: Mapped[str] = mapped_column(ForeignKey(BaseUser.name), nullable=False)
        value: Mapped[int] = mapped_column(Integer)

        user = relationship(BaseUser, foreign_keys=[user_id], backref='__basicusers_for_acl')
        object = relationship(BaseObject, foreign_keys=[object_id], backref='__basicobjects_for_acl')

        __table_args__ = (UniqueConstraint("object_id", "user_id", name="unique_acl"),)

    class OwnedBy(*BaseMixins):
        __tablename__ = 'basicownedby'
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        object_id: Mapped[str] = mapped_column(ForeignKey(BaseObject.name), unique=True)
        user_id: Mapped[str] = mapped_column(ForeignKey(BaseUser.name), nullable=False)

        user = relationship(BaseUser, foreign_keys=[user_id], backref='__basicusers_for_ownedby')
        object = relationship(BaseObject, foreign_keys=[object_id], backref='__basicobjects_for_ownedby')

    class ACLOwnedBy(*BaseMixins):
        __tablename__ = 'basicownedbyacl'
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        acl_id: Mapped[int] = mapped_column(ForeignKey(ACL.id), unique=True)
        user_id: Mapped[str] = mapped_column(ForeignKey(BaseUser.name), nullable=False)

        user = relationship(BaseUser, foreign_keys=[user_id], backref='__basicusers_for_aclownedby')
        acl = relationship(ACL, foreign_keys=[acl_id], backref='__basicacls_for_aclownedby')


    with get_session() as session:
        objs = [
            BaseObject.get_create(name='obj1', notid=1, value='thebasics'),
            BaseObject.get_create(name='obj2', notid=2, value='ownedbyme'),
            BaseObject.get_create(name='obj3', notid=3, value='ownedbymesharedto1'),
            BaseObject.get_create(name='obj4', notid=4, value='ownedbymesharedtoeveryone'),
            BaseObject.get_create(name='obj5', notid=5, value='ownedbyother'),
            BaseObject.get_create(name='obj6', notid=6, value='ownedbyothersharedtome'),
        ]

        users = [
            BaseUser.get_create(name='me'),
            BaseUser.get_create(name='otherpeople'),
            BaseUser.get_create(name='everybody')
        ]
        me = users[0]
        otherpeople = users[1]
        everyone = users[2]

        ownedby = [
            OwnedBy.get_create(user=me, object=objs[1]),
            OwnedBy.get_create(user=me, object=objs[2]),
            OwnedBy.get_create(user=me, object=objs[3]),
            OwnedBy.get_create(user=otherpeople, object=objs[4]),
            OwnedBy.get_create(user=otherpeople, object=objs[5]),
        ]

        acls = [
            ACL.get_create(user=me, object=objs[1], value=1),
            ACL.get_create(user=me, object=objs[2], value=1),
            ACL.get_create(user=me, object=objs[3], value=1),
            ACL.get_create(user=me, object=objs[5], value=1),
            ACL.get_create(user=otherpeople, object=objs[2], value=1),
            ACL.get_create(user=otherpeople, object=objs[3], value=1),
            ACL.get_create(user=otherpeople, object=objs[4], value=1),
            ACL.get_create(user=otherpeople, object=objs[5], value=1),
            ACL.get_create(user=everyone, object=objs[3], value=1),
            ACL.get_create(user=everyone, object=objs[5], value=1),
        ]

        acls_ownedby = [
            *[ACLOwnedBy.get_create(user=me, acl=acls[i]) for i in [0, 1, 2, 4, 5, 8]],
            *[ACLOwnedBy.get_create(user=otherpeople, acl=acls[i]) for i in [3, 6, 7, 9]],
        ]

        for acl_ownedby in acls_ownedby:
            logger.info(acl_ownedby)

        logger.info("All acl with me")
        for base_obj in BaseObject.get_join_with([(ACL, [ACL.value > 0, ACL.user == me]), (OwnedBy, [])]):
            logger.info(base_obj[0])
            logger.info(base_obj[1])

        logger.info("All acl with other and owned by me")
        for base_obj in BaseObject.get_join_with([(ACL, [ACL.value > 0, ACL.user != me]),
                                                  (OwnedBy, [OwnedBy.user == me])]):
            logger.info(base_obj[0])
            logger.info(base_obj[1])

        logger.info("All owned acl by me")
        for base_obj in BaseObject.get_join_with([((ACL, BaseObject.name == ACL.object_id), []),
                                                  ((ACLOwnedBy, ACL.id == ACLOwnedBy.acl_id), ACLOwnedBy.user == me)]):
            logger.info(base_obj[0])
            logger.info(base_obj[1])
