from tests.core00_core_model.datastructure.base.common import init


if __name__ == '__main__':
    init()

    from core.core05_persistent_model.policy.session import get_session, commit_and_rollback_if_exception
    from core.core00_core_model.datastructure.base.interval import Interval
    from core.core20_messaging.log.common_loggers import main_logger

    logger = main_logger()

    i = Interval(start=2, end=10)
    logger.info(i)
    logger.info(i.length)
    logger.info(i.contains(3))
    logger.info(i.contains(30))
    logger.info(i.contains(1))

    with get_session() as s:
        s.add(i)
        commit_and_rollback_if_exception(s)

    i2 = Interval(start=8, end=18)
    logger.info(i2)
    logger.info(i2.length)
    logger.info(i2.contains(3))
    logger.info(i2.intersects(i))

    logger.info(i.contains(3))
    logger.info(i.contains(30))
    logger.info(i.contains(1))
