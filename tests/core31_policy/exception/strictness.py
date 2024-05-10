from core.core31_policy.exception.strictness import raise_exception_from_string, ExceptionLevel
from core.core31_policy.exception.format import ExceptionFormat
from core.core20_messaging.log.log_level import LogLevel
from core.core11_config.config import update_fixed


if __name__ == '__main__':
    ctxt = {
        'config': {
            'exception': {
                'level': ExceptionLevel.LAX,
                'format': ExceptionFormat.DEFAULT
            },
            'log': {
                'log_level': LogLevel.DEBUG
            }
        },
    }

    from core.core30_context.context import current_ctxt
    current_ctxt().update(ctxt)
    raise_exception_from_string('test')

    current_ctxt()['config'].update({'log': {'log_level': LogLevel.INFO}})
    update_fixed('.log.log_level')
    raise_exception_from_string('test2')

    ctxt['config']['exception']['level'] = ExceptionLevel.STRICT
    raise_exception_from_string('test3')
