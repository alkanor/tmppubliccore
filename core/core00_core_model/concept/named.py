from ...core11_config.config import register_config_default, config_dependencies, Config
from ...core30_context.context_dependency_graph import context_dependencies
from ...core31_policy.misc.time import current_date
from ...core30_context.context import Context

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
import enum


class NameCreationPolicy(enum.Enum):
    DATE_PREFIX = enum.auto()
    INDEX_PREFIX = enum.auto()
    DATE_SUFFIX = enum.auto()
    INDEX_SUFFIX = enum.auto()
    COMPLEX_PREFIX = enum.auto()  # what, who, when (should be in current context)

register_config_default('.misc.name_creation_policy', NameCreationPolicy, NameCreationPolicy.INDEX_PREFIX)


@config_dependencies(('.misc.name_creation_policy', NameCreationPolicy))
@context_dependencies(('.interactor.who', str, False))
def prefix_policy(ctxt: Context, config: Config, classname, index, name, force_index: bool = False):
    if config['misc']['name_creation_policy'] is NameCreationPolicy.DATE_PREFIX:
        return current_date() + '-' + f"{str(index).zfill(3)}-" if force_index else ''
    elif config['misc']['name_creation_policy'] is NameCreationPolicy.INDEX_PREFIX:
        return str(index).zfill(3) + '-'
    elif config['misc']['name_creation_policy'] is NameCreationPolicy.COMPLEX_PREFIX:
        what = classname.name_prefix() + '.' if hasattr(classname, 'name_prefix') else ''
        return f"{what}{current_date()}" \
               f".{ctxt.get('interactor', {}).get('who', '?')}." + f"{str(index).zfill(3)}-" if force_index else ''
    else:
        return name

@config_dependencies(('.misc.name_creation_policy', NameCreationPolicy))
def suffix_policy(config: Config, classname, index, name, force_index: bool = False):
    if config['misc']['name_creation_policy'] is NameCreationPolicy.DATE_SUFFIX:
        return '-' + current_date() + f"-{str(index).zfill(3)}" if force_index else ''
    elif config['misc']['name_creation_policy'] is NameCreationPolicy.INDEX_SUFFIX:
        return '-' + str(index).zfill(3)
    else:
        return name


MAX_NAME_LENGTH = 255

class Named:  # All Named classes must have RepositoryMixin as a base
    __abstract__ = True

    __named_name__ = 'name'

    name: Mapped[str] = mapped_column(__named_name__, String(MAX_NAME_LENGTH), primary_key=True, nullable=False)

    @classmethod
    def force_create(cls, name: str, commit: bool = True, force_index: bool = False, **attrs):
        index = 1
        modified_name = f"{prefix_policy(cls, index, name, force_index)}{suffix_policy(cls, index, name, force_index)}"
        while cls.find(modified_name):
            index += 1
            modified_name = f"{prefix_policy(cls, index, name, True)}{suffix_policy(cls, index, name, True)}"
        return cls().fill(name=modified_name, **attrs).save(commit=commit)
