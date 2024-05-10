from ...core02_model.typed.service import Service, RestrictedService, SimpleService
from ...core30_context.context_dependency_graph import context_producer
from ...core30_context.context import Context

from typing import Callable


def tcp_tunnel_to(service: Service | RestrictedService) -> SimpleService | Callable[[], SimpleService]:
    raise NotImplementedError

@context_producer(('.interactor.server.tunnel_to',
                   Callable[[Service | RestrictedService], SimpleService | Callable[[], SimpleService]]))
def tcp_tunnel_to(ctxt: Context):
    ctxt.setdefault('interactor', {}).setdefault('server', {}).setdefault('tunnel_to', tcp_tunnel_to)
