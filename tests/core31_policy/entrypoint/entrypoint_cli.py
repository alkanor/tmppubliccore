from core.core30_context.policy.common_contexts import load_local_context
from core.core31_policy.entrypoint.entrypoint import cli_entrypoint


if __name__ == '__main__':
    load_local_context()
    cli_entrypoint()
