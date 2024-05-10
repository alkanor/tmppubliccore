from .meta_mixin.create_table_when_engine_mixin import AutoTableCreationMixin
from .instance_mixin.repository_mixin import RepositoryMixin
from .instance_mixin.representation_mixin import ReprMixin
from .instance_mixin.eagerload_mixin import EagerloadMixin


# cannot merge classes as it will lead to the exception to the class not having a __tablename__ attribute
BaseMixins = (AutoTableCreationMixin, ReprMixin, RepositoryMixin, EagerloadMixin)

BaseMixinsNoJoin = (AutoTableCreationMixin, ReprMixin, RepositoryMixin)
