# Create a globally-available session_maker for the Moodle database
# TODO: Make this more portable
from psmdlsyncer.utils import NS2
from psmdlsyncer.settings import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

ns = NS2()
ns.db_username = config['MOODLE'].get('db_username')
ns.db_prefix = config['MOODLE'].get('db_prefix')
ns.db_password = config['MOODLE'].get('db_password')
ns.db_host = config['MOODLE'].get('db_host')
ns.db_name = config['MOODLE'].get('db_name')
engine =  create_engine(
    'postgresql://{db_username}:{db_password}@{db_host}/{db_name}'.\
        format(**ns.declared_kwargs))
session_maker = sessionmaker(bind=engine, expire_on_commit=False)

@contextmanager
def DBSession():
    session = session_maker()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
#DBSession = DBSessionContext

__all__ = [DBSession]
