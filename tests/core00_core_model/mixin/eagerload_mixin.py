from tests.core00_core_model.datastructure.base.common import init


if __name__ == "__main__":
    init()

    from core.core05_persistent_model.policy.session import get_session, commit_and_rollback_if_exception
    from core.core00_core_model.mixin.instance_mixin.collection_mixin import CollectionMixin
    from tests.core00_core_model.mixin.collection_mixin import create_list
    from core.core00_core_model.datastructure.base.alias import ALIAS
    from core.core20_messaging.log.common_loggers import debug_logger
    #from sqlalchemy.orm import joinedload, aliased
    from sqlalchemy import or_

    logger = debug_logger()


    BaseMetadata, BasicListItem, BasicList = create_list()

    ALIAS_LIST = ALIAS(BasicList, 'basic_list')
    class ComplexList(CollectionMixin('COMPLEXLIST', BaseMetadata, ALIAS_LIST)):
        def add(self, entry, commit=False):
            coll_entry = self.__collection_entry__.create(metadata_obj=self.metadata, entry=entry, commit=False)
            self.session.add(coll_entry)
            if commit:
                commit_and_rollback_if_exception(self.session)
            self._entries.append(coll_entry)

    with get_session() as session:
        items = [BasicListItem.get_create(value='item'+str(i)) for i in range(10)]

        metadata1 = BaseMetadata.get_for(name='listeA')
        init = metadata1 is None
        metadatas = []
        for i in range(4):
            metadatas.append(BaseMetadata.get_create(name='liste'+chr(ord('A')+i)))

        lists = [BasicList(metadatas[i]) for i in range(4)]
        if init:
            import random
            for i in range(4):
                n = random.choice([2, 5, 10])
                for j in range(n):
                    lists[i].add(items[random.randint(0, 9)])
        [session.add(l.metadata) for l in lists]

        logger.info("PRINTING LISTS")
        for l in lists:
            logger.info(l)
        logger.info("END PRINTING LISTS")

    with get_session() as session:
        logger.info(f"ALIAS_LIST from construct")
        list_alias = [ALIAS_LIST.get_from_construct(l) for l in lists]
        logger.info(f"ALIAS_LIST from construct END")

        metadata_c1 = BaseMetadata.get_for(name='complexlisteA')
        init = metadata_c1 is None
        metadatas_c = []
        for i in range(3):
            logger.info(f"ADDING COMPLEX LIST {i}")
            metadatas_c.append(BaseMetadata.get_create(name='complexliste' + chr(ord('A') + i)))

        complexlists = [ComplexList(metadatas_c[i]) for i in range(3)]
        if init:
            for i in range(4):
                complexlists[0].add(list_alias[i])
            for i in range(1):
                complexlists[1].add(list_alias[i])
            for i in range(1,3):
                complexlists[2].add(list_alias[i])

        logger.info("PRINT COMPLEX LISTS")
        logger.info(complexlists)

    logger.info("====== Now le grand jour ======")
    with get_session() as session:
        logger.info("BASIC")
        basic = BasicList.joined_collections(name='listeB')
        logger.info(basic)

        logger.info("AND FINALLY")
        final = ComplexList.joined_collections(name='complexlisteC')
        logger.info(final)

        logger.info("MOST COMPLEX")
        final_all = ComplexList.joined_collections(or_(BaseMetadata.name == 'complexlisteA',
                                                       BaseMetadata.name == 'complexlisteB'))
        for L in final_all:
            logger.info("ANOTHER ONE")
            logger.info(L)


# OK below
# A = ComplexList.__collection_entry__
# B = ComplexList.__entry__  # alias
# C = ComplexList.__entry__.__metadata_target__  # metadata (de collection de l'alias)
# D = ComplexList.__entry__.__target__.__collection_entry__  # collection entries de la coll de l'alias
# E = ComplexList.__entry__.__target__.__entry__  # entry finale finale de la collection
# logger.info((ComplexList.__entry__.__target__.__metadata__, ComplexList.__entry__.__metadata_target__))
# res = session.query(A, D) \
#     .filter_by(metadata_id='complexlisteA') \
#     .outerjoin(B,
#                onclause=A.entry_id == B.aliased_id) \
#     .outerjoin(C,
#                onclause=B.aliased_id == C.name) \
#     .outerjoin(D,
#                onclause=C.name == D.metadata_id) \
#     .outerjoin(E,
#                onclause=D.entry_id == E.id) \
#     .options(joinedload(A.entry)) \
#     .options(joinedload(A.metadata_obj)) \
#     .options(joinedload(A.entry, B.aliased)) \
#     .options(joinedload(D.entry)) \
#     .options(joinedload(D.metadata_obj))

# Same: OK
# A = ComplexList.__collection_entry__
# B = ComplexList.__entry__  # alias
# C = ComplexList.__entry__.__metadata_target__  # metadata (de collection de l'alias)
# D = ComplexList.__entry__.__target__.__collection_entry__  # collection entries de la coll de l'alias
# E = ComplexList.__entry__.__target__.__entry__  # entry finale finale de la collection
# logger.info((ComplexList.__entry__.__target__.__metadata__, ComplexList.__entry__.__metadata_target__))
# res = session.query(A, D) \
#     .filter_by(metadata_id='complexlisteA') \
#     .outerjoin(B) \
#     .options(joinedload(A.entry)) \
#     .options(joinedload(A.metadata_obj)) \
#     .outerjoin(C) \
#     .options(joinedload(A.entry, B.aliased)) \
#     .outerjoin(D) \
#     .options(joinedload(D.entry)) \
#     .options(joinedload(D.metadata_obj)) \
#     .outerjoin(E)


# # Same: OK
# A = ComplexList.__collection_entry__
# B = ComplexList.__entry__  # alias
# C = ComplexList.__entry__.__metadata_target__  # metadata (de collection de l'alias)
# D = ComplexList.__entry__.__target__.__collection_entry__  # collection entries de la coll de l'alias
# E = ComplexList.__entry__.__target__.__entry__  # entry finale finale de la collection
# logger.info((ComplexList.__entry__.__target__.__metadata__, ComplexList.__entry__.__metadata_target__))
# CAlias = aliased(C)
# res = session.query(C, A, D) \
#     .filter(C.name == 'complexlisteA') \
#     .outerjoin(A) \
#     .outerjoin(B) \
#     .options(joinedload(A.entry)) \
#     .options(joinedload(A.metadata_obj)) \
#     .outerjoin(CAlias) \
#     .group_by(CAlias.name) \
#     .options(joinedload(A.entry, B.aliased)) \
#     .outerjoin(D) \
#     .options(joinedload(D.entry)) \
#     .options(joinedload(D.metadata_obj)) \
#     .outerjoin(E)
# print(f"BEFORE: {res}")
# print(f"After: {res.all()}")