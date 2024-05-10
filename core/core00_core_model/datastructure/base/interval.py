from __future__ import annotations

from ...mixin.base_mixin import BaseMixinsNoJoin

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped


# mostly extracted from https://docs.sqlalchemy.org/en/20/orm/extensions/hybrid.html

class Interval(*BaseMixinsNoJoin):
    __tablename__ = 'interval'

    id: Mapped[int] = mapped_column(primary_key=True)
    start: Mapped[int]
    end: Mapped[int]

    @hybrid_property
    def length(self) -> int:
        return self.end - self.start

    @hybrid_method
    def contains(self, point: int) -> bool:
        return (self.start <= point) & (point <= self.end)

    @hybrid_method
    def intersects(self, other: Interval) -> bool:
        return self.contains(other.start) | self.contains(other.end)
