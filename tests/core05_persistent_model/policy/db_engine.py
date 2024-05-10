from core.core05_persistent_model.policy.session import create_sql_engine, get_session, current_session
from core.core00_core_model.mixin.instance_mixin.repository_mixin import RepositoryMixin
from core.core00_core_model.mixin.instance_mixin.session_mixin import SessionMixin
from core.core30_context.policy.common_contexts import load_local_context
from core.core31_policy.entrypoint.entrypoint import cli_entrypoint
from core.core20_messaging.log.common_loggers import debug_logger
from core.core30_context.context import copy_context


if __name__ == "__main__":
    load_local_context()
    cli_entrypoint(True)
    engine = create_sql_engine()

    logger = debug_logger()

    from sqlalchemy.orm import declarative_base, mapped_column, Mapped
    from sqlalchemy import String as _String

    Base = declarative_base()
    sql_bases = [Base]

    class String(RepositoryMixin, Base):
        __tablename__ = 'string'
        id: Mapped[str] = mapped_column(_String(), primary_key=True)

    Base.metadata.create_all(engine)

    from contextvars import Context


    def f():
        with get_session() as session:
            String.get_create(id='first')
            session.commit()

    with get_session() as s1:
        logger.info(f"a {list(s1.query(String).all())} {s1}")
        logger.info(SessionMixin.session)
        logger.info(current_session())
        with get_session() as s2:
            logger.info(f"b {list(s2.query(String).all())} {s2}")
            logger.info(SessionMixin.session)
            logger.info(current_session())
        logger.info(f"c {list(s1.query(String).all())} {s1}")
        logger.info(SessionMixin.session)
        logger.info(current_session())
        String.get_create(id='third')
        s1.commit()

    logger.info("in context 1")
    ctxt = Context()
    ctxt.run(f)
    logger.info("double in main")
    f()
    f()
    logger.info("in context 2")
    ctxt = Context()
    ctxt.run(f)
    logger.info("in context 3")
    ctxt = copy_context()
    ctxt.run(f)