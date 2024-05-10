from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import ColumnProperty
from datetime import datetime


def column_to_type(column: ColumnProperty):
    if isinstance(column.class_attribute.type, String):
        return str, String
    elif isinstance(column.class_attribute.type, Integer):
        return int, Integer
    elif isinstance(column.class_attribute.type, DateTime):
        return datetime, DateTime
    raise NotImplementedError
