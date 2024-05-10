# from ...core30_context.context_dependency_graph import context_producer
from typing import Dict, Any#, Callable
import copy


# this is very basic to copy the context between threads (it should remove all objects linked to the current thread)
def default_thread_context_copy(ctxt: Dict[str, Any]):
    return {
        k: copy.deepcopy(v) for k, v in ctxt.items() if k not in ['localcontext']
    }


## below is bad, please add config / context dependencies above
# @context_producer(('.policy.thread.copy_context', Callable[[Dict], Dict]))
# def default_thread_context_copy_policy(ctxt: Dict[str, Any]):
#     ctxt.setdefault('policy', {}).setdefault('thread', {}).setdefault('copy_context', default_thread_context_copy)
