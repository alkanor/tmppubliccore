from __future__ import annotations

from .identity_proof import IdentityProofForIdentity, PrivateKey, Credentials, AuthenticatedSomething, decode_part, \
    identity_proof_secret
from .identity import SimpleLogin, DoubleInfoLogin, TripleInfoLogin, identity_to_url
from .endpoint import Endpoint, endpoint_from_hostname_or_ip, endpoint_to_str
from .file import FilePhysical, EncryptedFile

from pydantic._internal._model_construction import ModelMetaclass
from typing import Literal, Union, Generic, TypeVar
from pydantic import BaseModel


default_ports = {
}

services_for_protos = {
}


class RegisterKnownService(ModelMetaclass):
    def __init__(cls, name, bases, dict):
        if dict.get('port', None):
            default_ports[dict['applicative_protocol']] = dict['port']
            services_for_protos[dict['applicative_protocol']] = cls
        super(RegisterKnownService, cls).__init__(name, bases, dict)


class DirectService(BaseModel, metaclass=RegisterKnownService):
    endpoint: Endpoint
    port: int
    layer4_protocol: str
    applicative_protocol: str


class TCPService(DirectService):
    layer4_protocol: Literal['TCP'] = 'TCP'


class UDPService(DirectService):
    layer4_protocol: Literal['UDP'] = 'UDP'


class TCPSSLService(DirectService):
    layer4_protocol: Literal['TCP+TLS'] = 'TCP+TLS'


class UDPSSLService(DirectService):
    layer4_protocol: Literal['UDP+TLS'] = 'UDP+TLS'


class SSHService(TCPService):
    applicative_protocol: Literal['SSH'] = 'SSH'
    port: int = 22


class SMBService(TCPService):
    applicative_protocol: Literal['SMB'] = 'SMB'
    port: int = 445


class RDPService(TCPService):
    applicative_protocol: Literal['RDP'] = 'RDP'
    port: int = 3389


class WINRMService(TCPService):
    applicative_protocol: Literal['WINRM'] = 'WINRM'
    port: int = 5985


class HTTPService(TCPService):
    applicative_protocol: Literal['HTTP'] = 'HTTP'
    port: int = 80


class HTTPSService(TCPSSLService):
    applicative_protocol: Literal['HTTPS'] = 'HTTPS'
    port: int = 443


class SOCKS4Service(TCPService):
    applicative_protocol: Literal['SOCKS4'] = 'SOCKS4'
    port: int = 1080


class SOCKS4AService(TCPService):
    applicative_protocol: Literal['SOCKS4A'] = 'SOCKS4A'
    port: int = 1080


class SOCKS5Service(TCPService):
    applicative_protocol: Literal['SOCKS5'] = 'SOCKS5'
    port: int = 1080


class AuthenticatedDirectService(AuthenticatedSomething[DirectService]):
    pass


SimpleService = Union[
    DirectService,
    AuthenticatedDirectService
]

GenericService = TypeVar('GenericService')
RestrictedSimpleService = Union[GenericService, AuthenticatedSomething[GenericService]]


class GenericServiceProxy(BaseModel, Generic[GenericService]):
    proxy: SimpleService | AuthenticatedSomething
    target: GenericService | AuthenticatedSomething[GenericService] | GenericServiceProxy[GenericService]


class ProxifiedService(BaseModel):
    proxy: SimpleService
    target: SimpleService | ProxifiedService


Service = Union[
    DirectService,
    AuthenticatedDirectService,
    ProxifiedService
]


# unfortunately variadic generics are not well handled by pydantic, will have to create subclasses for basic unions :/
class RestrictedService(BaseModel, Generic[GenericService]):
    service: Union[
        GenericService,
        AuthenticatedSomething[GenericService],
        GenericServiceProxy[GenericService]
    ]


def final_applicative_protocol_for_service(svc):
    match svc:
        case GenericServiceProxy() | ProxifiedService():
            return final_applicative_protocol_for_service(svc.target)
        case AuthenticatedSomething() | AuthenticatedDirectService():
            return final_applicative_protocol_for_service(svc.authenticated_object)
        case DirectService():
            return services_for_protos.get(svc.applicative_protocol, TCPService)
        case _:
            raise NotImplementedError




def deal_with_password_string(password_string):
    if password_string[0] == '<':
        fname_and_key = password_string[1:].split('|')
        fname = decode_part(fname_and_key[0])
        if len(fname_and_key) == 1:
            key = None
        else:
            key = decode_part('|'.join(fname_and_key[1:]))
        f = FilePhysical(filename=fname)
        if key:
            f = EncryptedFile(file=f, password=key)
        return PrivateKey(key=f)
    else:
        return Credentials(password=decode_part(password_string))


def parse_unitary_endpoint(url: str, final_target: Service=None):
    proto, target = url.split('://')
    additional_proto = proto.split('+')[-1].lower()
    if '+' in proto and additional_proto != 'tls' and additional_proto != 'ssl' and additional_proto[:5] != 'socks':
        proto = proto.split('+')[0]
    around_at = target.split('@')
    if len(around_at) == 1:
        login, identity_proof = None, None
        host_port = around_at[0].split(':')
    else:
        multi_login_and_password = around_at[0].split(':')
        if len(multi_login_and_password) <= 2:
            login = SimpleLogin(username=multi_login_and_password[0])
        elif len(multi_login_and_password) == 3:
            login = DoubleInfoLogin(system_id=multi_login_and_password[0], username=multi_login_and_password[1])
        elif len(multi_login_and_password) == 4:
            login = TripleInfoLogin(service_id=multi_login_and_password[0], system_id=multi_login_and_password[1],
                                    username=multi_login_and_password[2])
        else:
            raise NotImplementedError
        identity_proof = deal_with_password_string(multi_login_and_password[-1]) if len(multi_login_and_password) > 1 \
            else None
        host_port = around_at[1].split(':')

    if len(host_port) == 2:
        host, port = host_port
    else:
        host = host_port[0]
        port = None

    service_type = services_for_protos.get(proto.upper(), TCPService)
    service = service_type(endpoint=endpoint_from_hostname_or_ip(host),
                           port=port if port else default_ports[proto.upper()],
                           applicative_protocol=proto.upper())
    if login:
        if not identity_proof:
            identity_proof = Credentials(password=password_for_user(login, service, final_target))
        service = AuthenticatedDirectService(authenticated_object=service,
                                             identity_proof=IdentityProofForIdentity(identity=login,
                                                                                     proof=identity_proof)) \
            if service_type is TCPService else \
            AuthenticatedSomething[service_type](
                authenticated_object=service,
                identity_proof=IdentityProofForIdentity(identity=login,
                                                        proof=identity_proof))

    if final_target:
        target_type = final_applicative_protocol_for_service(final_target)
        if target_type is TCPService:
            service = ProxifiedService(proxy=service, target=final_target)
        else:
            service = GenericServiceProxy[target_type](proxy=service, target=final_target)
    return service


# socks4://a:b@10.2.3.10:3453>ssh://10.2.3.100
# https://a:<private_key@10.2.3.10:3453>socks5://10.2.3.100:1020>http://127.0.0.1:8000
def url_to_service(url):
    parts = url.split(">")
    service_after = None
    for part in parts[::-1]:
        service = parse_unitary_endpoint(part, service_after)
        service_after = service
    return service



def service_to_url(service: Service | RestrictedService):
    match service:
        case ProxifiedService() | GenericServiceProxy():
            return service_to_url(service.proxy) + '>' + service_to_url(service.target)
        case AuthenticatedDirectService() | AuthenticatedSomething():
            identity = identity_to_url(service.identity_proof.identity)
            identity_proof = identity_proof_secret(service.identity_proof.proof)
            without_auth = service_to_url(service.authenticated_object)
            split = without_auth.split('://')
            return f"{split[0]}://{identity}:{identity_proof}@" + '://'.join(split[1:])
        case RestrictedService():
            return service_to_url(service.service)
        case _:
            return f"{service.applicative_protocol.lower()}://{endpoint_to_str(service.endpoint)}" + \
                ('' if service.port == default_ports.get(service.applicative_protocol, -1) else f":{service.port}")


from ...core21_interaction.policy.password import password_for_user
