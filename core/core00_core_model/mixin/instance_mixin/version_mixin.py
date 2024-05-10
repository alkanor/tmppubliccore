from sqlalchemy.orm import mapped_column
from sqlalchemy import Integer, String
import uuid


class VersionMixin:
    __abstract__ = True

    version_id = mapped_column(Integer, nullable=False)
    __mapper_args__ = {"version_id_col": version_id}


class UUIDVersionMixin:
    version_uuid = mapped_column(String(32), nullable=False)

    __mapper_args__ = {
        "version_id_col": version_uuid,
        "version_id_generator": lambda version: uuid.uuid4().hex,
    }
