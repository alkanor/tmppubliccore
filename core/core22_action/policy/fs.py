from ...core11_config.config import register_config_default, Config, config_dependencies
from ...core30_context.context_dependency_graph import context_dependencies
from ...core30_context.context import Context

from typing import Callable
from logging import Logger
from pathlib import Path
import enum
import os


class FolderAccessCheckPolicy(enum.Enum):
    CREATE_MISSING_FOLDERS = enum.auto()
    ASK_CREATE_MISSING_FOLDERS = enum.auto()
    DONOT_CREATE_MISSING_FOLDERS = enum.auto()
    RAISE_IF_NOT_EXISTING = enum.auto()


register_config_default('.fs.folder_access', FolderAccessCheckPolicy,
                        FolderAccessCheckPolicy.ASK_CREATE_MISSING_FOLDERS)


@config_dependencies(('.fs.folder_access', FolderAccessCheckPolicy))
@context_dependencies(('.interactor.ask_boolean', Callable[[...], bool]))
def check_dir_access(ctxt: Context, config: Config, d: str | Path):
    path = d if isinstance(d, Path) else Path(d)
    if not path.is_dir():
        if config['fs']['folder_access'] == FolderAccessCheckPolicy.CREATE_MISSING_FOLDERS:
            os.makedirs(d, exist_ok=True)
        elif config['fs']['folder_access'] == FolderAccessCheckPolicy.ASK_CREATE_MISSING_FOLDERS:
            if ctxt['interactor']['ask_boolean']({'c': True, 'a': False}) \
                        (f"Create missing directories for {d}? create (c) or abort (a)"):
                os.makedirs(d, exist_ok=True)
            else:
                return False
        elif config['fs']['folder_access'] == FolderAccessCheckPolicy.DONOT_CREATE_MISSING_FOLDERS:
            return False
        elif config['fs']['folder_access'] == FolderAccessCheckPolicy.RAISE_IF_NOT_EXISTING:
            raise Exception(f"Directory {d} not existing")
        else:
            raise NotImplementedError
    return True


def check_file_access(f: str | Path, mode='r'):
    d = os.path.dirname(f)
    check_dir_access(d)
    if mode == 'r':
        with open(f, 'r'):
            return True
    else:
        with open(f, 'ab'):
            return True


class BadFileAccessPolicy(enum.Enum):
    MOVE_BAD_FILE = enum.auto()
    ASK_MOVE_BAD_FILE = enum.auto()
    DONOT_MOVE_BAD_FILE = enum.auto()
    RAISE_IF_NOT_WRITEABLE = enum.auto()

register_config_default('.fs.bad_file_access', BadFileAccessPolicy,
                        BadFileAccessPolicy.ASK_MOVE_BAD_FILE)


@config_dependencies(('.fs.bad_file_access', FolderAccessCheckPolicy))
@context_dependencies(('.interactor.ask_boolean', Callable[[...], bool]), ('.log.debug_logger', Logger | None))
def bad_file_at(ctxt: Context, config: Config, fname: str | Path) -> Path:
    src = fname if isinstance(fname, Path) else Path(fname)
    if config['fs']['bad_file_access'] == BadFileAccessPolicy.MOVE_BAD_FILE:
        move = True
    elif config['fs']['bad_file_access'] == BadFileAccessPolicy.ASK_MOVE_BAD_FILE:
        move = ctxt['interactor']['ask_boolean']({'m': True, 'a': False}) \
                        (f"Move bad file {fname}? move (m) or abort (a)")
    elif config['fs']['bad_file_access'] == BadFileAccessPolicy.DONOT_MOVE_BAD_FILE:
        return src
    elif config['fs']['bad_file_access'] == BadFileAccessPolicy.RAISE_IF_NOT_WRITEABLE:
        raise Exception(f"Bad file at {fname}")
    else:
        raise NotImplementedError

    if move:
        prefix = f"{fname}" if isinstance(fname, Path) else fname
        dst = Path(prefix + ".bak")
        base_index = 1
        while dst.is_file() or dst.is_dir():
            dst = Path(prefix) + f".{base_index}.bak"
            base_index += 1
        src.rename(dst)
        return dst
    return src
