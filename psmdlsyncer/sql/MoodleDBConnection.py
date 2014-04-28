from psmdlsyncer.settings import config, requires_setting
from psmdlsyncer.utils import NS
from sqlalchemy import create_engine
from sqlalchemy.sql import select

class MoodleDBConnection2:
    """
    Let's use SQLAlchemy, okay?
    """

    def __init__(self):
        settings = ['db_username', 'db_password', 'db_name', 'db_prefix', 'db_host']
        for setting in settings:
            requires_setting('MOODLE', setting)

        ns = NS()
        ns.db_username = config['MOODLE'].get('db_username')
        ns.db_password = config['MOODLE'].get('db_password')
        ns.db_prefix = config['MOODLE'].get('db_prefix')
        ns.db_host = config['MOODLE'].get('db_host')
        ns.db_name = config['MOODLE'].get('db_name')

        self.dnet = create_engine(ns('postgres://{db_username}:{db_password}@{db_host}/{db_name}'))
        self.conn = self.dnet.connect()

    def select_where(fetch_statement, columns_or_table, where_statement):
        """
        Proof of concept really
        """
        sql_statement = \
            select(columns_or_table).where(where_statement)
        return getattr(self.conn.execute(sql_statement), fetch_statement)()

    def update_where(fetch_statement, columns_or_table, where_statement):
        """
        Proof of concept really
        """
        sql_statement = \
            select(columns_or_table).where(where_statement)
        return getattr(self.conn.execute(sql_statement), fetch_statement)()
