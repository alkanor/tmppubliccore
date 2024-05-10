from ....core05_persistent_model.policy.session import commit_and_rollback_if_exception
from .session_mixin import SessionMixin


# mostly inspired from https://github.com/absent1706/sqlalchemy-mixins/blob/master/sqlalchemy_mixins/activerecord.py

class RepositoryMixin(SessionMixin):
    __abstract__ = True

    def fill(self, **attrs):
        for key in attrs:
            setattr(self, key, attrs[key])
        # trigger an object reconstruction, since we are not in the case of the SQLAlchemy mapper that triggers it
        if hasattr(self, 'init_on_load'):
            self.init_on_load()
        return self

    @classmethod
    def create(cls, commit=True, **argv):
        return cls().fill(**argv).save(commit=commit)

    def update(self, commit=True, **argv):
        return self.fill(**argv).save(commit=commit)

    def delete(self, commit=True):
        self.session.delete(self)
        if commit:
            commit_and_rollback_if_exception(self.session)

    @classmethod
    def delete_many(cls, *ids, commit=True):
        for pk in ids:
            obj = cls.find(pk)
            if obj:
                obj.delete(commit=commit)
        if not commit:  # otherwise changes are committed
            cls.session.flush()

    @classmethod
    def all(cls):
        return cls.query.all()

    @classmethod
    def first(cls):
        return cls.query.first()

    @classmethod
    def find(cls, id_):
        return cls.query.get(id_)


    @classmethod
    def get_for(cls, **attrs):
        return cls.query.filter_by(**attrs).one_or_none()

    @classmethod
    def get_create(cls, commit=True, **attrs):
        existing = cls.get_for(**attrs)
        return existing if existing else cls.create(commit=commit, **attrs)

    @classmethod
    def get_from_instance(cls, instance, commit=True):  # instance must be of cls type (must be introspectable)
        attrs = {x: getattr(instance, x, None) for x in instance.columns + instance.relations}
        attrs = {x: attrs[x] for x in attrs if attrs[x]}
        existing = cls.get_for(**attrs)
        return existing if existing else cls.create(commit=commit, **attrs)

    @classmethod
    def get_from_construct(cls, *args, **argv):
        # construct the object attributes in case of complex object
        instance = cls(commit=argv.get('commit', True), *args, **argv)
        # then retrieve it /create it from database
        return cls.get_from_instance(instance, commit=argv.get('commit', True))

    @classmethod
    def filter_by(cls, **attrs):
        return cls.query.filter_by(**attrs)

    @classmethod
    def filter(cls, condition):
        return cls.query.filter(condition)

    @classmethod
    def all_for(cls, **attrs):
        return cls.filter_by(**attrs).all()

    @classmethod
    def all_for_condition(cls, condition):
        return cls.filter(condition).all()
