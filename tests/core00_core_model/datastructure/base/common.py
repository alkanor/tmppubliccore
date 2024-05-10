from core.core30_context.policy.common_contexts import load_local_context
from core.core31_policy.entrypoint.entrypoint import cli_entrypoint


def init():
    load_local_context()
    cli_entrypoint(True)
