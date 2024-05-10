from ...core02_model.typed.service import RestrictedService, url_to_service, Service, GenericServiceProxy, \
    ProxifiedService, service_to_url, SimpleService
from ...core20_messaging.log.logger import get_logger
from ...core30_context.context_dependency_graph import context_dependencies, context_producer
from ...core02_model.typed.file import FilePhysical, EncryptedFile
from ...core11_config.config import config_dependencies, Config
from ..typed.db_target import SQLiteDB, PostgreSQLService
from ...core22_action.policy.fs import check_file_access, bad_file_at
from ...core30_context.context import Context

from sqlalchemy import Engine, create_engine
from typing import Union, Callable, Iterator
from sqlalchemy.orm import sessionmaker, Session
from contextvars import ContextVar
from logging import Logger
import contextlib


SupportedDB = Union[RestrictedService[SQLiteDB], RestrictedService[PostgreSQLService]]

@context_producer(('.database.service', SupportedDB | Callable[[], SupportedDB]), ('.database.engine_url', str))
@context_dependencies(('.interactor.server.tunnel_to',
                       Callable[[Service | RestrictedService], SimpleService | Callable[[], SimpleService]]))
@config_dependencies(('.database', str))
def engine_from_config(config: Config, ctxt: Context):
    if config['database'][:6].lower() == 'sqlite':
        if config['database'][:19].lower() == 'sqlite+pysqlcipher:':
            fname = config['database'].split('@')[-1].split('://')[-1].split('?')[0]
            passwd = config['database'].split('://')[-1].split('@')[0].split(':')[-1]
            service = RestrictedService[SQLiteDB](service=SQLiteDB(db_file=EncryptedFile(
                file=FilePhysical(filename=fname), password=passwd)))
            engine_string = config['database'][:19].lower() + config['database'][19:]
        else:
            service = RestrictedService[SQLiteDB](service=SQLiteDB(db_file=FilePhysical(
                filename=config['database'][9:])))
            engine_string = config['database'][:7].lower() + config['database'][7:]
    else:  # expect pgsql
        complex_service = url_to_service(config['database'])
        match complex_service:
            case GenericServiceProxy() | ProxifiedService():  # this case requires an internal handle for proxying
                tunnel_to = ctxt['interactor']['server']['tunnel_to']
                # either a SimpleService or an iterable (context managed) SimpleService
                service = RestrictedService[PostgreSQLService](service=tunnel_to(complex_service))
                engine_string = service_to_url(service)
            case _:
                service = RestrictedService[PostgreSQLService](service=complex_service)
                engine_string = config['database']
    ctxt.setdefault('database', {})['service'] = service
    ctxt['database']['engine_url'] = engine_string


def merge_declarative_bases(sql_bases):
    from sqlalchemy import MetaData

    combined_meta_data = MetaData()

    for declarative_base in sql_bases:
        for (table_name, table) in declarative_base.metadata.tables.items():
            combined_meta_data._add_table(table_name, table.schema, table)

    return combined_meta_data


@context_dependencies(('.log.main_logger', Logger), ('.log.debug_logger', Logger | None))
def _construct_engine(ctxt: Context, engine_url, echo, sqlite, first_time=True, **argv):
    if echo:
        get_logger('sqlalchemy.engine')
        if ctxt['log']['debug_logger']:
            get_logger('sqlalchemy.pool')
            get_logger('sqlalchemy.dialects')
            get_logger('sqlalchemy.orm')
    try:
        # db_engine = create_engine(engine_url, echo=echo, **argv)
        db_engine = create_engine(engine_url, **argv)  # cleaner: no echo because on stdout, want in on loggging
    except Exception as e:
        if first_time:
            if sqlite:
                fname = engine_url.split(':///')[-1].split('?')[0]
                try:
                    check_file_access(fname)
                except Exception as e:
                    ctxt['log']['main_logger'].info(f"File access failed to file {fname}: {e}")
                    # trigger the bad file policy to either move or ask user what to do
                    ctxt['log']['main_logger'].info(f"Tried to operate on bad file with result {bad_file_at(fname)}")
            ctxt['log']['main_logger'].info(f"Unable to access {engine_url}, retrying one time")
            return _construct_engine(engine_url, echo, sqlite, False)
        else:
            raise Exception(f"Failed twice to load {engine_url}, please check your database uri")

    def _fk_pragma_on_connect(dbapi_con, con_record):
        if sqlite:
            dbapi_con.execute('pragma foreign_keys=ON')

    from sqlalchemy import event
    event.listen(db_engine, 'connect', _fk_pragma_on_connect)

    # from ..sql_bases import _sql_bases
    # # create all currently existing metadata for declared bases
    # try:
    #     (*map(lambda x: x.metadata.create_all(db_engine), _sql_bases[::-1]),)
    # except:  # if exception, may be that declarative bases contain unresolved references to other tables
    #     combined = merge_declarative_bases(_sql_bases)
    #     combined.create_all(db_engine)

    return db_engine


@context_producer(('.localcontext.database.engine', Engine | Callable[[], Engine]),
                  ('.localcontext.database.sessionmaker',
                   ContextVar[sessionmaker] | Callable[[...], ContextVar[sessionmaker]]))
@context_dependencies(('.database.service', SupportedDB | Callable[[], SupportedDB]), ('.database.engine_url', str),
                      ('.log.main_logger', Logger), ('.log.debug_logger', Logger | None))
def create_sql_engine(ctxt: Context, argv_engine={}, argv_sessionmaker={'expire_on_commit': False}):
    ctxt.setdefault('localcontext', {}).setdefault('database', {})
    match ctxt['database']['service']:
        case RestrictedService():
            db_engine = _construct_engine(ctxt['database']['engine_url'], ctxt['log']['debug_logger'] is not None,
                                          isinstance(ctxt['database']['service'].service, SQLiteDB), **argv_engine)
            ctxt['localcontext']['database']['sessionmaker'] = ContextVar('_sessionmaker', default=
                                                                          sessionmaker(db_engine, **argv_sessionmaker))
        case _:  # Callable case but cannot match against callable
            @contextlib.contextmanager
            def create_engine_in_context():
                with ctxt['database']['service']() as svc:  # in case the service requires resource management
                    yield _construct_engine(ctxt['database']['engine_url'],
                                            ctxt['log']['debug_logger'] is not None,
                                            isinstance(svc, SQLiteDB),
                                            **argv_engine)

            db_engine = create_engine_in_context

            @contextlib.contextmanager
            def create_session_maker() -> ContextVar[sessionmaker]:
                with create_engine_in_context() as db_engine:
                    yield ContextVar('_sessionmaker', default=sessionmaker(db_engine, **argv_sessionmaker))

            ctxt['localcontext']['database']['sessionmaker'] = create_session_maker
    ctxt['localcontext']['database']['engine'] = db_engine
    return db_engine


@contextlib.contextmanager
@context_dependencies(('.localcontext.database.engine', Engine | Callable[[], Engine]))
def get_engine(ctxt: Context) -> Iterator[Engine]:
    if isinstance(ctxt['localcontext']['database']['engine'], Engine):
        yield ctxt['localcontext']['database']['engine']
    else:  # assume the engine creator is context-managed
        with ctxt['localcontext']['database']['engine']() as engine_creator:
            yield engine_creator


# generators not yet handled by the core so cheating here
# @context_producer(('localcontext.database.current_session', ContextVar[Session]))
def _get_session(ctxt: Context, _sessionmaker: ContextVar, debug_logger: Logger = None):
    try:
        if 'localcontext' not in ctxt or 'database' not in ctxt['localcontext'] or\
                'current_session' not in ctxt['localcontext']['database'] \
                or not ctxt['localcontext']['database']['current_session'].get():
            session = _sessionmaker.get()()
            ctxt['localcontext']['database']['current_session'] = ContextVar('_session', default=session)
        else:
            session = ctxt['localcontext']['database']['current_session'].get()
        yield session
        session.commit()
        if debug_logger:
            debug_logger.debug("Session committed: {}".format(id(session)))
    except:
        session.rollback()
        if debug_logger:
            debug_logger.debug("Session rollback-ed: {}".format(id(session)))
        raise
    finally:
        # ctxt['database']['current_session'].set(None)  # session handles partial close with default close_resets_only
        if debug_logger:
            debug_logger.debug("Session closed: {}".format(id(session)))
        session.close()  # session handles partial close with default close_resets_only = True, so we can reuse it


@context_dependencies(('.localcontext.database.current_session', ContextVar[Session], False))
def current_session(ctxt: Context):
    if 'localcontext' not in ctxt or 'database' not in ctxt['localcontext'] or \
            'current_session' not in ctxt['localcontext']['database']:
        raise Exception('No current session in context, please execute current block in a "with get_session()" block')
    elif not ctxt['localcontext']['database']['current_session'].get():
        raise Exception('Session currently None, please execute in a context where it\'s not')
    return ctxt['localcontext']['database']['current_session'].get()


@contextlib.contextmanager
@context_dependencies(('.localcontext.database.sessionmaker',
                       ContextVar[sessionmaker] | Callable[[...], ContextVar[sessionmaker]]),
                      ('.log.debug_logger', Logger | None))
def get_session(ctxt: Context) -> Iterator[Session]:
    if isinstance(ctxt['localcontext']['database']['sessionmaker'], ContextVar):
        yield from _get_session(ctxt, ctxt['localcontext']['database']['sessionmaker'], ctxt['log']['debug_logger'])
    else:  # assume the sessionmaker is context-managed
        with ctxt['localcontext']['database']['sessionmaker']() as _sessionmaker:
            yield from _get_session(ctxt, _sessionmaker, ctxt['log']['debug_logger'])


def commit_and_rollback_if_exception(session):
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
