# from ..core99_misc.fakejq.utils import check_dict_against_attributes_string
# from .context_dependency_graph import try_resolve
from .context_dependency_graph import invalidate_context_dependencies

from contextvars import ContextVar, Context as _Context
from typing import Dict, Any


# import threading


Context = Dict[str, Any]

_main_context = {}

_global_current_ctxt = ContextVar('context')
_global_current_ctxt.set(_main_context)
#_thread_local = threading.local()


def copy_context():  # custom copy_context to avoid writing in the _main_context from sub context
    current_value = _global_current_ctxt.get()
    ctxt = _Context()
    def _copy_context():
        from ..core31_policy.thread.copy import default_thread_context_copy
        # not quite the O(1) expected with copy_context but ok
        _global_current_ctxt.set(default_thread_context_copy(current_value))
    ctxt.run(_copy_context)
    # copy_dependencies_context(ctxt)  # already handled when copying context
    invalidate_context_dependencies('.localcontext')
    return ctxt

def current_ctxt():
    try:
        return _global_current_ctxt.get()
    except:
        from ..core31_policy.thread.copy import default_thread_context_copy
        _global_current_ctxt.set(default_thread_context_copy(_main_context))
        invalidate_context_dependencies('.localcontext')
    return _global_current_ctxt.get()

    # legacy with thread_local
    # # if main thread, keep the global variable
    # if threading.current_thread() is threading.main_thread():
    #     return _global_current_ctxt  # main context variable which will hold all the current context. Careful when modifying it
    # else:
    #     if not hasattr(_thread_local, 'current_ctxt'):
    #         _thread_local.current_ctxt = default_thread_context_copy(_global_current_ctxt)
    #         ###### below is a gas factory
    #         ## only time when the global current context is accessed from another thread
    #         # indict, callback = check_dict_against_attributes_string(_global_current_ctxt, '.policy.thread.copy_context')
    #         # if not indict:
    #         #     if not hasattr(_thread_local, 'getting_current_ctxt'):
    #         #         _thread_local.getting_current_ctxt = True
    #         #         try_resolve('.policy.thread.copy_context')['.policy.thread.copy_context']()
    #         #         return current_ctxt()
    #         #     else:  # avoid infinite loop
    #         #         return _global_current_ctxt
    #         # _thread_local.current_ctxt = callback(_global_current_ctxt)
    #     return _thread_local.current_ctxt
