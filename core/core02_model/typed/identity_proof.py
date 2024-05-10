from ...core11_config.config import config_dependencies, Config, register_config_default
from .file import File, EncryptedFile, FileContent, FilePhysical, absolute_inode_name
from .identity import Identity

from pydantic import BaseModel, SecretBytes
from typing import Union, TypeVar, Generic
from enum import Enum
import base64


class Credentials(BaseModel):
    password: SecretBytes


class PrivateKey(BaseModel):
    key: SecretBytes | File | EncryptedFile


class BiometryFingerprint(BaseModel):
    somehash: bytes


IdentityProof = Union[
    Credentials,
    PrivateKey,
    BiometryFingerprint,
]


class IdentityProofForIdentity(BaseModel):
    identity: Identity
    proof: IdentityProof


GenericService = TypeVar('GenericService')

class AuthenticatedSomething(BaseModel, Generic[GenericService]):
    authenticated_object: GenericService
    identity_proof: IdentityProofForIdentity



class PasswordInURLFormat(Enum):
    HEX = 1
    BASE64 = 2  # enables to differentiate passwords from file like <fname|file_key from raw passwords
    ENCRYPTED_BASE64 = 3
    PLAINTEXT = 4  # this is not advised as it does not allow to differentiate fname and passwords
    VAULT_REFERENCE = 5
    GUESS = 6


register_config_default('.misc.password_in_url_format', PasswordInURLFormat, PasswordInURLFormat.BASE64)


@config_dependencies(('.misc.password_in_url_format', PasswordInURLFormat))
def decode_part(config: Config, password_string):
    format = config['misc']['password_in_url_format']
    match format:
        case PasswordInURLFormat.HEX:
            return bytes.fromhex(password_string.encode())
        case PasswordInURLFormat.BASE64:
            return base64.b64decode(password_string.encode())
        case PasswordInURLFormat.PLAINTEXT:
            return password_string.encode()
        case PasswordInURLFormat.ENCRYPTED_BASE64:
            raise NotImplementedError
        case PasswordInURLFormat.VAULT_REFERENCE:
            raise NotImplementedError
        case PasswordInURLFormat.GUESS:
            raise NotImplementedError
        case _:
            raise Exception(f"Bad config value provided in .misc.password_in_url_format")

@config_dependencies(('.misc.password_in_url_format', PasswordInURLFormat))
def encode_part(config: Config, password_bytes: bytes):
    format = config['misc']['password_in_url_format']
    match format:
        case PasswordInURLFormat.HEX:
            return password_bytes.hex()
        case PasswordInURLFormat.BASE64:
            return base64.b64encode(password_bytes).decode()
        case PasswordInURLFormat.PLAINTEXT:
            return password_bytes.decode()
        case PasswordInURLFormat.ENCRYPTED_BASE64:
            raise NotImplementedError
        case PasswordInURLFormat.VAULT_REFERENCE:
            raise NotImplementedError
        case PasswordInURLFormat.GUESS:
            raise NotImplementedError
        case _:
            raise Exception(f"Bad config value provided in .misc.password_in_url_format")

def identity_proof_secret(identity_proof):
    match identity_proof:
        case Credentials():
            return encode_part(identity_proof.password.get_secret_value())
        case PrivateKey():
            match identity_proof.key:
                case SecretBytes():
                    return encode_part(identity_proof.key.get_secret_value())
                case FileContent():
                    return encode_part(identity_proof.key.content)
                case FilePhysical():
                    return '<' + encode_part(absolute_inode_name(identity_proof.key.get_secret_value()))
                case EncryptedFile():
                    match identity_proof.key.file:
                        case FileContent():
                            return '<' + encode_part(identity_proof.key.file.content)
                        case FilePhysical():
                            return '<' + encode_part(absolute_inode_name(identity_proof.key.file).encode()) + \
                                '|' + encode_part(identity_proof.key.password.get_secret_value())
                        case _:
                            raise NotImplementedError
                case _:
                    raise NotImplementedError
        case _:
            raise NotImplementedError
