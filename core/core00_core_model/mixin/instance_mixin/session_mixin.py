from ....core05_persistent_model.policy.session import current_session, commit_and_rollback_if_exception
from ...utils.class_property import classproperty


class SessionMixin:
    __abstract__ = True

    _session = None

    @classproperty
    def session(cls):
        if cls._session is None:
            cls._session = current_session()
        return cls._session

    @classproperty
    def query(cls):
        return cls.session.query(cls)

    def save(self, commit=True):
        self.session.add(self)
        if commit:
            commit_and_rollback_if_exception(self.session)
        return self
