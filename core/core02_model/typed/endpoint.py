from pydantic.networks import IPvAnyAddress
from pydantic import BaseModel
from typing import Union


class Host(BaseModel):
    name: str

class L2Endpoint(BaseModel):
    mac_address: str

class IPEndpoint(BaseModel):
    ip_address: IPvAnyAddress


def endpoint_from_hostname_or_ip(hostname_or_ip):
    try:
        return IPEndpoint(ip_address=hostname_or_ip)
    except:
        return Host(name=hostname_or_ip)

Endpoint = Union[Host, L2Endpoint, IPEndpoint]


def endpoint_to_str(endpoint: Endpoint):
    match endpoint:
        case Host():
            return endpoint.name
        case L2Endpoint():
            return endpoint.mac_address
        case IPEndpoint():
            return str(endpoint.ip_address)
        case _:
            raise NotImplementedError
