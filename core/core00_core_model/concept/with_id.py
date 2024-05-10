from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer


class WithID:
    __abstract__ = True

    __named_id__ = 'id'

    id: Mapped[int] = mapped_column(__named_id__, Integer, primary_key=True)
