from __future__ import annotations

from pydantic import BaseModel, SecretBytes
from typing import Union
import os


class FileContent(BaseModel):
    content: bytes

class PhysicalDirectory(BaseModel):
    dirname: str
    parent: PhysicalDirectory | None = None

class FilePhysical(BaseModel):
    filename: str
    parent: PhysicalDirectory | None = None

class EncryptedFile(BaseModel):
    file: Union[FileContent, FilePhysical]
    password: SecretBytes | None


File = Union[FileContent, FilePhysical, EncryptedFile]


def recursive_join(obj: FilePhysical | PhysicalDirectory, attribute_func, join_func):
    attribute = attribute_func(obj)
    if attribute:
        return join_func(recursive_join(attribute, attribute_func, join_func), obj)
    return join_func(None, obj)


def inode_name(f: FilePhysical | EncryptedFile | PhysicalDirectory):
    match f:
        case FileContent() | FilePhysical():
            return f.filename
        case PhysicalDirectory():
            return f.dirname
        case EncryptedFile():
            match f.file:
                case FilePhysical():
                    return f.file.filename
                case FileContent():
                    raise NotImplementedError
        case _:
            raise NotImplementedError


def absolute_inode_name(f: FilePhysical | EncryptedFile | PhysicalDirectory):
    def join_func(x, y):
        tmp = inode_name(y)
        while tmp and tmp[0] == os.path.sep:
            tmp = tmp[1:]
        return os.path.join(x, tmp) if x else tmp
    return recursive_join(f, lambda x: x.parent, join_func)


def file_content(f: File):
    match f:
        case FileContent():
            return f.content
        case FilePhysical():
            return open(absolute_inode_name(f), 'rb').read()
        case EncryptedFile():
            raise NotImplementedError
