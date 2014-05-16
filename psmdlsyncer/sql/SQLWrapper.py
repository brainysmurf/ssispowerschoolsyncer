"""
SQL WRAPPER
A SIMPLE WRAPPER FOR USE WITH A MOODLE DATABASE (postgres only at the moment)
"""

# ABSTRACT THIS ENOUGH SO THAT ANY ENGINE CAN BE USED
# RESEARCH INTO USING SQLALCHEMY FOR THIS
# SHOULD BE EASY ENOUGH AS THE SQL STATEMENTS ARE FAIRLY UNIVERSAL
import postgresql
import os
from psmdlsyncer.utils.Namespace import NS
from psmdlsyncer.settings import logging

class SQLWrapper:
    """
    Glue code between me and the database
    """

    def __init__(self, user, password, prefix, server, database, verbose=False):
        ns = NS(user=user, password=password,
                prefix=prefix,
                server=server, database=database)
        self.prefix = prefix
        self.last_call = None
        self._database = database
        self.db = postgresql.open(ns('pq://{user}:{password}@{server}/{database}'))
        self.logger = logging.getLogger(self.__class__.__name__)

    def make_ns(self, *args, **kwargs):
        ns = NS(*args, **kwargs)
        ns.PREFIX = self.prefix
        return ns

    def sql(self, *args, **kwargs):
        return self.db.prepare(*args, **kwargs)

    def call_sql(self, *args, **kwargs):
        return self.sql(*args, **kwargs)()

    def call_sql_only_one(self, *args, **kwargs):
        result = self.call_sql(*args, **kwargs)
        if result:
            return result[0][0]
        else:
            return None

    def call_sql_first_row(self, *args, **kwargs):
        result = self.call_sql(*args, **kwargs)
        if result:
            return result[0]
        else:
            return ()

    def table_exists(self, table_name):
        """
        RETURNS TRUE IF TABLE EXISTS, FALSE IF NOT
        TODO: MAKE THIS MUCH BETTER
        """
        ns = self.make_ns(table_name=table_name)
        return self.call_sql( ns("select exists(select 1 from information_schema.tables where table_name = '{PREFIX}{table_name}')") )[0][0]

    def escape(self, s):
        return s.replace("'", r"\\'")

    test_table = table_exists   # depreciated name

    def insert_table(self, table_name, **kwargs):
        #TODO: Handle case where there is an apostrophe
        columns = set([k for k in kwargs.keys()])
        columns_phrase = ", ".join(columns)
        values_list = []
        for c in columns:
            value = kwargs[c]
            if isinstance(value, bool):
                b = 1 if value else 0
                values_list.append( ' ' + str(b))
            elif isinstance(value, int):
                values_list.append( ' ' + self.escape(str(value)))
            else:
                values_list.append( " '" + self.escape(str(value)) + "'" )
        values_phrase = ", ".join(values_list)
        self.call_sql("insert into {}{} ({}) values ({})".format(self.prefix, table_name, columns_phrase, values_phrase))

    def update_table(self, table_name, where={}, **kwargs):
        set_phrase = ",".join(["{}='{}'".format(c[0], c[1]) for c in kwargs.items()])
        if where:
            wheres = []
            for key, value in where.items():
                if isinstance(value, int):
                    wheres.append( "{} = {}".format(key, value) )
                else:
                    wheres.append( "{} = '{}'".format(key, self.escape(value)))
            where_phrase = "where " + " AND ".join(wheres)
        else:
            where_phrase = ""
        self.call_sql('update {}{} set {} {}'.format(self.prefix, table_name, set_phrase, where_phrase))

    def update_or_insert(self, table_name, where={}, **kwargs):
        """
        If info already exists according to where_phrase, update it
        otherwise, insert it
        """
        if where=={}:
            return False
        if not self.table_exists(table_name):
            self.insert_table(table_name, where=where)
        else:
            self.update_table(table_name, where=where, **kwargs)
        return True

    def get_table(self, table_name, *select, **where):
        """
        RETURNS A TUPLE WITH DATA
        """
        if where:
            wheres = []
            for key, value in where.items():
                if isinstance(value, int):
                    wheres.append( "{} = {}".format(key, value) )
                else:
                    wheres.append( "{} = '{}'".format(key, value))
            where_phrase = "where " + " AND ".join(wheres)
        else:
            where_phrase = ""

        if select:
            select_phrase = ", ".join(select)
        else:
            select_phrase = '*'
        ns = self.make_ns(table_name=table_name,
                          select_phrase=select_phrase,
                          where_phrase=where_phrase)
        result = self.call_sql( ns("select {select_phrase} from {PREFIX}{table_name} {where_phrase}") )
        if result:
            return result
        else:
            return ()

    def get_unique_row(self, table_name, *select, **where):
        """
        RETURNS A NAMESPACE WITH DATA
        USE WHEN where_phrase IS A UNIQUE ROW
        IF ONLY ONE ITEM CALLED IN SELECT, RETURNS THE RAW DATA
        IF >1 RETURNS AN NS WITH ITEMS
        """
        if where:
            wheres = []
            for key, value in where.items():
                if isinstance(value, int):
                    wheres.append( "{} = {}".format(key, value) )
                else:
                    wheres.append( "{} = '{}'".format(key, value))
            where_phrase = "where " + " AND ".join(wheres)
        else:
            where_phrase = ""

        if select:
            select_phrase = ", ".join(select)
        else:
            select_phrase = '*'
        ns = self.make_ns(table_name=table_name,
                          select_phrase=select_phrase,
                          where_phrase=where_phrase)
        result = self.call_sql( ns("select {select_phrase} from {PREFIX}{table_name} {where_phrase}") )
        if result:
            if len(result) == 1:
                ns = self.make_ns()
                if len(select) == 1:
                    return result[0][0]
                for item in range(len(select)):
                    key = select[item]
                    value = result[0][item]
                    d = {key: value}
                    ns.define(**d)
                return ns
        else:
            return None

    def __del__(self):
        if self.db:
            self.db.close()


if __name__ == "__main__":


    db = MoodleDBConnection()

    db.insert_table('just_testing', idnumber="O'shea")





