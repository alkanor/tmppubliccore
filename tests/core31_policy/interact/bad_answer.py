from core.core30_context.context_dependency_graph import context_dependencies
from core.core21_interaction.policy.bad_answer import BadAnswerPolicy
from core.core20_messaging.log.common_loggers import main_logger
from core.core20_messaging.log.log_level import LogLevel
from core.core11_config.config import update_fixed

from typing import Callable


if __name__ == '__main__':

    ctxt = {
        'config': {
            'log': {
                'log_level': LogLevel.DEBUG
            },
            'interactor': {
            }
        },
        'interactor': {
            'local': True,
            'type': 'cli',
        }
    }

    from core.core30_context.context import current_ctxt

    current_ctxt().update(ctxt)
    main_logger()
    main_logger = current_ctxt()['log']['main_logger']


    @context_dependencies(('.interactor.ask_boolean', Callable[[...], bool]))
    def ask_question(ctxt):
        return ctxt['interactor']['ask_boolean']({'e': True, 'p': False}) \
            ('No possible configuration file remains, exit (e) or provide other one (p)?')

    ctxt['config']['interactor']['bad_answer'] = BadAnswerPolicy.REPEAT_UNTIL_GOOD
    update_fixed('.interactor.bad_answer')
    v = ask_question()
    main_logger.info(f"OK 1: {v}")

    ctxt['config']['interactor']['bad_answer'] = BadAnswerPolicy.RAISE
    update_fixed('.interactor.bad_answer')
    try:
        v = ask_question()
    except Exception as e:
        main_logger.info(f"Should throw exception immediately: {e}")
    main_logger.info(f"OK 2: {v}")

    ctxt['config']['interactor']['bad_answer'] = BadAnswerPolicy.RETRY_AND_RAISE
    update_fixed('.interactor.bad_answer')
    try:
        v = ask_question()
    except Exception as e:
        main_logger.info(f"Should throw exception after X tries depending on conf: {e}")
    main_logger.info(f"OK 3: {v}")

    # the 3 following are not yet implemented
    # ctxt['config']['interactor']['bad_answer'] = BadAnswerPolicy.ASK_RETRY_OR_STOP_OR_DEFAULT
    # update_fixed('.interactor.bad_answer')
    # ctxt['config']['interactor']['bad_answer'] = BadAnswerPolicy.RANDOM
    # update_fixed('.interactor.bad_answer')
    # ctxt['config']['interactor']['bad_answer'] = BadAnswerPolicy.DEFAULT_VALUE
    # update_fixed('.interactor.bad_answer')

    ctxt['config']['interactor']['bad_answer'] = BadAnswerPolicy.RETRY_AND_EXIT
    update_fixed('.interactor.bad_answer')
    v = ask_question()
    main_logger.info(f"OK 4: {v}")
