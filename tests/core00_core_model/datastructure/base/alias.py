from tests.core00_core_model.datastructure.base.common import init

if __name__ == '__main__':
    init()

    from core.core05_persistent_model.policy.session import get_session, commit_and_rollback_if_exception
    from core.core00_core_model.mixin.instance_mixin.collection_mixin import CollectionMixin
    from core.core00_core_model.datastructure.base.interval import Interval
    from tests.core00_core_model.mixin.collection_mixin import create_list
    from core.core00_core_model.datastructure.base.alias import ALIAS
    from core.core20_messaging.log.common_loggers import main_logger

    logger = main_logger()

    BaseMetadata, BasicListItem, BasicList = create_list()

    ALIAS_INTERVAL = ALIAS(Interval, 'interval_equiv')
    ALIAS_LIST = ALIAS(BasicList, 'basic_list')
    ALIAS_ITEM = ALIAS(BasicListItem, 'basic_item')

    class BasicListAlias(CollectionMixin('BASICLISTONALIAS', BaseMetadata, ALIAS_ITEM)):
        def add(self, entry, commit=False):
            coll_entry = self.__collection_entry__.create(metadata_obj=self.metadata, entry=entry, commit=False)
            self.session.add(coll_entry)
            if commit:
                commit_and_rollback_if_exception(self.session)
            self._entries.append(coll_entry)

    ALIAS_LIST_ALIAS = ALIAS(BasicListAlias, 'alias_of_list_of_alias')

    i = Interval(start=2, end=10)

    with get_session() as session:
        a1 = ALIAS_INTERVAL(i, commit=False)
        a2 = ALIAS_INTERVAL(start=3, end=12)

        logger.info(a1)
        logger.info(a2)

        logger.info(a1.length)
        logger.info(a2.contains(8))
        logger.info(a1.intersects(a2))

        session.add(i)
        logger.info(i)
        logger.info(a1)
        commit_and_rollback_if_exception(session)
        logger.info(i)
        logger.info(a1)

        session.add(a1)
        commit_and_rollback_if_exception(session)
        logger.info(a1)

        l1 = ALIAS_LIST(name='mylist')
        item1 = BasicListItem.get_create(value='itemX')
        l1.add(item1)
        l1.entries_updated()
        logger.info(l1)

        l2 = ALIAS_LIST_ALIAS.get_from_construct(name='listalias')
        aitem = ALIAS_ITEM.get_from_construct(item1)
        l2.add(aitem)
        l2.entries_updated()
        session.commit()
        logger.info(l2)
