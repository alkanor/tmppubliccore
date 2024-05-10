from core.core02_model.typed.identity_proof import IdentityProofForIdentity, Credentials, AuthenticatedSomething
from core.core02_model.typed.service import url_to_service, RestrictedService, AuthenticatedDirectService, \
    SOCKS5Service, service_to_url
from core.core05_persistent_model.typed.db_target import SQLiteDB, PostgreSQLService
from core.core02_model.typed.endpoint import IPEndpoint
from core.core02_model.typed.identity import SimpleLogin
from core.core02_model.typed.file import FilePhysical

from pydantic import BaseModel
from typing import Union


if __name__ == '__main__':
    s1 = "socks4://a:AAA=@10.2.3.10:3453>ssh://10.2.3.100"
    s2 = "https://a:<cHJpdmF0ZV9rZXk=|cGFzc3dk@10.2.3.10:3453>socks5://10.2.3.100:1020>http://127.0.0.1:8000"
    e1 = url_to_service(s1)
    e2 = url_to_service(s2)
    print(e1)
    print(e2)
    print(service_to_url(e2))

    A = AuthenticatedSomething[SQLiteDB]
    try:
        v = A(authenticated_object=PostgreSQLService(), identity_proof=IdentityProofForIdentity(
            identity=SimpleLogin(username='a'), proof=Credentials(password=b'p')))
    except Exception as e:
        print(f"Normal excpetion: {e}")
    v = A(authenticated_object=SQLiteDB(db_file=FilePhysical(filename='/tmp/db')),
          identity_proof=IdentityProofForIdentity(identity=SimpleLogin(username='a'),
                                                  proof=Credentials(password=b'p')))
    print(v)


    ads = AuthenticatedDirectService(authenticated_object=SOCKS5Service(endpoint=IPEndpoint(ip_address='10.0.1.0')),
          identity_proof=IdentityProofForIdentity(identity=SimpleLogin(username='a'),
                                                  proof=Credentials(password=b'p')))
    print(ads)
    print(service_to_url(ads))

    class UnionGachisBecauseNoVariadicInPydantic(BaseModel):
        svc: Union[RestrictedService[SQLiteDB], RestrictedService[PostgreSQLService]]

    v = UnionGachisBecauseNoVariadicInPydantic(svc=RestrictedService[SQLiteDB](
        service=SQLiteDB(db_file=FilePhysical(filename='/tmp/db'))))
    print(v)
    v = UnionGachisBecauseNoVariadicInPydantic(svc=RestrictedService[PostgreSQLService](
        service=url_to_service('pgsql://AAA=:AAA=@127.0.0.1')))
    print(v)
    print(service_to_url(v.svc))
