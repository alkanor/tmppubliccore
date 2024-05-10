from ...core02_model.typed.service import TCPService
from ...core02_model.typed.file import File

from pydantic import BaseModel
from typing import Literal


class SQLiteDB(BaseModel):
    db_file: File

class PostgreSQLService(TCPService):
    applicative_protocol: Literal['PGSQL'] = 'PGSQL'
    port: int = 5432

class MYSQLService(TCPService):
    applicative_protocol: Literal['MYSQL'] = 'MYSQL'
    port: int = 3306

class ORACLEService(TCPService):
    applicative_protocol: Literal['ORACLESQL'] = 'ORACLESQL'
    port: int = 1521

class MSSQLService(TCPService):
    applicative_protocol: Literal['MSSQL'] = 'MSSQL'
    port: int = 3306
