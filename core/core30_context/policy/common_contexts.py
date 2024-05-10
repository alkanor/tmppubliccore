from ..context_dependency_graph import context_dynamic_producer
from ..context import Context


@context_dynamic_producer(('.interactor.local', bool), ('.interactor.type', str))
def load_local_context(ctxt: Context):
    ctxt.setdefault('interactor', {}).update({
        'local': True,
        'type': 'cli'
    })

# @context_dynamic_producer(('.executor.network.ip_interfaces', List[IPNetworkInterface]))
# def load_network_context(ctxt: Context):
#     raise NotImplementedError
