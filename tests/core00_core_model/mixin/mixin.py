from core.core30_context.policy.common_contexts import load_local_context
from core.core31_policy.entrypoint.entrypoint import cli_entrypoint


if __name__ == "__main__":
    load_local_context()
    cli_entrypoint(True)

    from core.core00_core_model.mixin.meta_mixin.create_table_when_engine_mixin import AutoTableCreationMixin
    from core.core00_core_model.mixin.instance_mixin.representation_mixin import ReprMixin
    from core.core00_core_model.mixin.instance_mixin.repository_mixin import RepositoryMixin
    from core.core00_core_model.mixin.instance_mixin.session_mixin import SessionMixin
    from core.core05_persistent_model.policy.session import get_session
    from core.core00_core_model.concept.timed import CreatedModifiedAt
    from core.core20_messaging.log.common_loggers import debug_logger
    from core.core00_core_model.concept.merge import merge_concepts
    from core.core00_core_model.concept.named import Named

    logger = debug_logger()

    from sqlalchemy.orm import mapped_column, Mapped, relationship
    from sqlalchemy import String as _String, Integer, ForeignKey

    named_and_createdmodified_at = merge_concepts(Named, CreatedModifiedAt)

    class MyTable(AutoTableCreationMixin, ReprMixin, RepositoryMixin, named_and_createdmodified_at):
        __tablename__ = 'autocreate'
        notid: Mapped[int] = mapped_column(Integer, nullable=True)
        value: Mapped[str] = mapped_column(_String, unique=True)

    class MyRef(AutoTableCreationMixin, ReprMixin, RepositoryMixin, named_and_createdmodified_at):
        __tablename__ = 'autoref'
        fk: Mapped[int] = mapped_column(Integer, ForeignKey(MyTable.name), nullable=False)
        thetable: Mapped[MyTable] = relationship(MyTable, foreign_keys=[fk])

    import random
    import string

    with get_session() as session:
        logger.info(SessionMixin.session)
        obj = MyTable.get_create(value='bcd', name='??')
        obj2 = MyTable.force_create(value='bcde'+''.join([random.choice(string.ascii_letters) for _ in range(5)]),
                                    name='ab', force_index=True)
        logger.info(obj)
        logger.info(obj.self_to_json())
        logger.info(obj.class_to_json())
        logger.info(obj2)
        obj3 = MyRef.force_create(thetable=obj, name='X')
        logger.info(obj3)
        logger.info(obj3.self_to_json())
        logger.info(obj3.class_to_json())
