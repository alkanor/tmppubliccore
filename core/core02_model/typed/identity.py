from typing_extensions import TypeAliasType
from typing import Union
from pydantic import BaseModel


class SimpleLogin(BaseModel):
    username: str

class DoubleInfoLogin(BaseModel):
    system_id: str
    username: str

class TripleInfoLogin(BaseModel):
    service_id: str
    system_id: str
    username: str


Identity = Union[
                SimpleLogin,
                DoubleInfoLogin,
                TripleInfoLogin,
            ]


def identity_to_url(identity: Identity):
    match identity:
        case SimpleLogin():
            return identity.username
        case DoubleInfoLogin():
            return ':'.join([identity.system_id, identity.username])
        case TripleInfoLogin():
            return ':'.join([identity.service_id, identity.system_id, identity.username])
        case _:
            raise NotImplementedError
