try:
    import postgresql
except:
    pass # Allow things to break later
import os

from utils.Formatter import Smartformatter

class NotActuallyPG:
    def __init__(self):
        pass

    def __call__(self):
        return []


class DBConnection:
    """
    Glue code between me and the database
    """

    def __init__(self, user, password, server, database, verbose=False):
        sf = Smartformatter(user=user, password=password, server=server, database=database)
        self.last_call = None
        self._database = database
        self.verbose = verbose
        self.verbose and print(sf("About to connect to {server}"))
        self.db = postgresql.open(sf('pq://{user}:{password}@{server}/{database}'))

    def sql(self, *args, **kwargs):
        if not self.db:
            return NotActuallyPG()
        if self.verbose:
            print_db = self._database
            if not self.last_call:
                self.last_call = 'prepared'
            print('Database ' + print_db + ' ' +  self.last_call)
            print('\t', *args)
            if kwargs:
                print('\t', kwargs.items())
        self.last_call = None
        return self.db.prepare(*args, **kwargs)

    def call_sql(self, *args, **kwargs):
        self.last_call = 'calling' if self.verbose else None
        return self.sql(*args, **kwargs)()

    def call_sql_only_one(self, *args, **kwargs):
        self.last_call = 'calling only one' if self.verbose else None
        result = self.call_sql(*args, **kwargs)
        if result:
            return result[0][0]
        else:
            return None

    def call_sql_first_row(self, *args, **kwargs):
        self.last_call = 'calling first row' if self.verbose else None
        result = self.call_sql(*args, **kwargs)
        if result:
            return result[0]
        else:
            return ()

    def test_table(self, table_name, **where):
        where_items = where.items()
        where_phrase = " AND ".join(["where {} = '{}'".format(w[0], w[1]) for w in where_items])
        result = self.sql("select * from {} {}".format(table_name, where_phrase))()
        if result:
            return True
        else:
            return False

    def insert_table(self, table_name, **kwargs):
        #TODO: Handle case where there is an apostrophe
        columns_values = kwargs.items()
        columns_phrase = ", ".join([c[0] for c in columns_values])
        values_phrase = "'" + "', '".join([c[1] for c in columns_values]) + "'"
        self.sql("insert into temp_{} ({}) values ({})".format(table_name, columns_phrase, values_phrase))()

    def update_table(self, table_name, where={}, **kwargs):
        set_phrase = ",".join(["{}='{}'".format(c[0], c[1]) for c in kwargs.items()])
        where_items = where.items()
        where_phrase = " AND ".join(["where {} = '{}'".format(w[0], w[1]) for w in where_items])
        self.sql('update {} set {} where {}'.format(table_name, set_phrase, where_phrase))()

    def update_or_insert(self, table_name, where={}, **kwargs):
        """
        If info already exists according to where_phrase, update it
        otherwise, insert it
        """
        if where=={}:
            return False
        if not self.test_table(table_name, **where):
            self.insert_table(table_name, where=where)
        else:
            self.update_table(table_name, where=where, **kwargs)

    def get_table(self, table_name, **where):
        where_items = where.items()
        where_phrase = " AND ".join(["where {} = '{}'".format(w[0], w[1]) for w in where_items])
        result = self.sql("select * from {} {}".format(table_name, where_phrase))()
        if result:
            return result
        else:
            return ()

    def __del__(self):
        if self.db:
            self.db.close()

class DragonNetDBConnection(DBConnection):

    def __init__(self, user, password, server, database, verbose=False):
        super().__init__(user, password, server, database, verbose=verbose)

    def create_temp_storage(self, table_name, *args):
        if not self.exists_temp_storage(table_name):
            column_phrase = ", ".join([a + ' varchar(255)' for a in args])
            self.sql('create table temp_{} ({})'.format(table_name, column_phrase))()

    def add_temp_storage(self, table_name, **kwargs):
        #TODO: Handle case where there is an apostrophe
        columns_values = kwargs.items()
        columns_phrase = ", ".join([c[0] for c in columns_values])
        values_phrase = "'" + "', '".join([c[1] for c in columns_values]) + "'"
        self.sql("insert into temp_{} ({}) values ({})".format(table_name, columns_phrase, values_phrase))()

    def clear_temp_storage(self, table_name, **where):
        where_items = where.items()
        if not where_items:
            return False
        where_phrase = " AND ".join(["where {} = '{}'".format(w[0], w[1]) for w in where_items])
        result = self.test_temp_storage(table_name, **where)
        if result:
            self.sql("delete from temp_{} {}".format(table_name, where_phrase))()
        return result

    def test_temp_storage(self, table_name, **where):
        where_items = where.items()
        where_phrase = " AND ".join(["where {} = '{}'".format(w[0], w[1]) for w in where_items])
        result = self.sql("select * from temp_{} {}".format(table_name, where_phrase))()
        if result:
            return True
        else:
            return False

    def dump_temp_storage(self, table_name, clear=False):
        """
        Return whatever is in the table, delete it if clear=True
        """
        result = self.sql("select * from temp_{}".format(table_name))()
        if result and clear:
            self.sql("delete from temp_{}".format(table_name))
        return result

    def get_temp_storage(self, table_name, **where):
        where_items = where.items()
        where_phrase = " AND ".join(["where {} = '{}'".format(w[0], w[1]) for w in where_items])
        result = self.sql("select * from temp_{} {}".format(table_name, where_phrase))()
        if result:
            return result
        else:
            return ()

    def empty_temp_storage(self, table_name):
        self.sql('truncate temp_{}'.format(table_name))()

    def exists_temp_storage(self, table_name):
        return self.list_existing_tables('temp_' + table_name)

    def delete_temp_storage(self, table_name):
        if self.exists_temp_storage('temp_' + table_name):
            self.sql('drop table temp_{}'.format(table_name))()

    def list_existing_tables(self, prefix):
        result = self.sql("select tablename from pg_tables where tablename = '{}'".format(prefix))()
        if result:
            return True
        else:
            return False

    def does_user_exist(self, idnumber):
        """
        We use the idnumber to ascertain if a student or parent account is there or not
        True if user exists, False if not
        """
        result = self.sql( "select username from ssismdl_user where idnumber = '{}'".format(idnumber) )()
        return result

    def user_is_new(self, idnumber):
        result = self.sql( "select lastlogin, lastaccess from ssismdl_user where idnumber = '{}'".format(idnumber) )()
        if not result:
            self.verbose and print("Didn't find anything in the database: {}".format(idnumber))
            return False
        lastlogin, lastaccess = result[0]
        return int(lastlogin) == 0 and int(lastaccess) == 0

    def get_student_info(self):
        self.verbose and print("Reading in usernames that are already taken")
        get_users = self.sql('select idnumber, username, id from ssismdl_user')()
        user_data = {}
        for idnumber, username, _id in get_users:
            user_data[idnumber] = (username, _id)
        return user_data

    def get_parent_child_associations(self):
        """
        Returns which accounts are linked to which accounts
        """
        return self.sql("select usr.idnumber as parent, usr.id, child.idnumber as child from ssismdl_user usr join ssismdl_role_assignments ra on ra.userid = usr.id join ssismdl_role role on role.id = ra.roleid join ssismdl_context ctx on ctx.id = ra.contextid and ctx.contextlevel = 30 join ssismdl_user child on child.id = ctx.instanceid where role.shortname = 'parent' order by usr.idnumber")()

    def prepare_id_username_map(self):
        self.id_username = {}
        if not self.on_server:
            raw = [l.strip('\n') for l in open('../id_username.txt').readlines() if l.strip('\n')]
            for line in raw:
                try:
                    idnum, username, firstname, lastname = line.split('|')
                except ValueError:
                    continue
                idnum = idnum.strip()
                username = username.strip() + "@student.ssis-suzhou.net"
                firstname = firstname.strip()
                lastname = lastname.strip()
                self.id_username[username] = {'idnum':idnum, 'name': lastname+", "+firstname}
        else:
            response = self.sql('select idnumber, username, firstname, lastname from ssismdl_user;')()
            for item in response:
                split = item.split("|")
                if not len(split) == 3:
                    continue
                idnumber, username, firstname, lastname = [s.strip() for s in strip]
                if not idnumber or not idnumber.isdigit():
                    continue
                self.id_username[username] = {'idnum':idnumber, 'name':lastname+", "+firstname}

        return self.id_username


class FieldObject(DragonNetDBConnection):
    """

    """

    def __init__(self, user, password, server, database, database_name, field_name, samples=None):
        super().__init__(user, password, server, database)
        self.use_samples = samples
        if not self.use_samples:
            self.database_name = database_name
            self.database_id = self.sql("select id from ssismdl_data where name = '{}'".format(self.database_name))()[0][0]
            self.field_name = field_name

    def all_values(self):
        if self.use_samples:
            return self.use_samples
        values = self.sql("select param1 from ssismdl_data_fields where name = '{}' and dataid = {}".format(self.field_name, self.database_id))()[0][0]
        values = values.split('\r\n')
        return values

    def default_value(self):
        return self.all_values()[0]

class UpdateField(DragonNetDBConnection):
    """
    Class that is used to update a field in a database module
    """

    def __init__(self, user, password, server, database, database_name, field_name):
        super().__init__(user, password, server, database)
        self.field_name = field_name
        try:
            self.target = self.sql(
            "select ssismdl_data_fields.id from ssismdl_data join ssismdl_data_fields on (ssismdl_data.name = '{}' and ssismdl_data.id = ssismdl_data_fields.dataid and ssismdl_data_fields.name = '{}')"
            .format(database_name, field_name)
            )
        except:
            self.target_id = None
            return

        try:
            self.target_id = self.target()[0][0]
        except:
            self.target_id = None

    def update_menu(self, value):
        """
        
        """
        if self.target_id is None:
            return
        if isinstance(value, list):
            value = "\r\n".join(value)
        command = "update ssismdl_data_fields set param1 = '{}' where id = {}".format(value, self.target_id)
        try:
            self.sql(command)()
        except:
            print("I was unable to issue the following sql command: {}".format(command))


class ProfileUpdater(DragonNetDBConnection):

    def update_profile_fields_for_user(user):
        """
        Takes any variables in user that begins with "profile_extra"
        and adds them to the right database area so that it registers in DragonNet
        Boolean only, if you need text areas use one of the randome ID things
        """
        
        for key, value in [item for itme in luser.__dict__.items() if item[0].startswith('profile_extra_')]:
             results = self.get_table('ssismdl_user_profile_field',
                               shortname = key)
             if not results:
                #TODO: Inform admin that you need to create it
                #TODO? Create it for them???
                continue

             fieldid = results[0][0]

             if hasattr(user, 'database_id') and user.database_id:
                 where = {'userid':user.database_id, 'fieldid':fieldid}
                 self.update_or_insert('ssismdl_user_profile_data',
                                      where=where,
                                      userid=user.database_id,
                                      fieldid=fieldid,
                                      data='1',
                                      dataformat='0')
                

if __name__ == "__main__":

    pass
