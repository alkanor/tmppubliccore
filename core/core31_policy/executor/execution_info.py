from ...core30_context.context_dependency_graph import context_producer
from ...core30_context.context import Context

import platform
import os


@context_producer(('.executor.os', str), ('.executor.arch', str), ('.executor.platform', str), ('.executor.uid', int),
                  ('.executor.gid', int))
def init_executor_context(ctxt: Context):
    uid, gid = -1, -1
    if 'wind' not in platform.system().lower():
        uid, gid = os.getuid(), os.getgid()
    ctxt.setdefault('executor', {}) \
        .update({
            'os': platform.system().lower(),
            'arch': platform.machine().lower(),
            'platform': platform.platform().lower(),
            'uid': uid,
            'gid': gid
         })
