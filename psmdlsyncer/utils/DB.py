try:
    import postgresql
except:
    pass # Allow things to break later
import os

from psmdlsyncer.utils.Formatter import Smartformatter
from psmdlsyncer.settings import config, requires_setting

class DBConnection:
    """
    Glue code between me and the database
    """

    def __init__(self, user, password, server, database, verbose=False):
        sf = Smartformatter(user=user, password=password, server=server, database=database)
        self.last_call = None
        self._database = database
        self.db = postgresql.open(sf('pq://{user}:{password}@{server}/{database}'))

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
        where_phrase = " AND ".join(["{} = '{}'".format(w[0], w[1]) for w in where_items])
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

    def __init__(self):        
        settings = ['db_username', 'db_password', 'db_name', 'db_prefix', 'db_host']
        for setting in settings:
            requires_setting('MOODLE', setting)
        
        super().__init__(config['MOODLE'].get('db_username'),
                         config['MOODLE'].get('db_password'),
                         config['MOODLE'].get('db_host'),
                         config['MOODLE'].get('db_name'))

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

    def get_all_user_ids(self):
        return [i[0] for i in self.sql('select idnumber from ssismdl_user where deleted = 0')()]

    def get_all_parent_name_ids(self):
        return self.sql("select idnumber, username from ssismdl_user where deleted = 0 and idnumber like '%P'")()                

    def get_all_user_name_ids(self):
        return self.sql('select idnumber, username, firstname, lastname from ssismdl_user where deleted = 0')()

    def get_all_students_name_ids(self):
        return self.sql("select idnumber, username, firstname, lastname from ssismdl_user where deleted = 0 and not idnumber like '%P'")()

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
            return False
        lastlogin, lastaccess = result[0]
        return int(lastlogin) == 0 and int(lastaccess) == 0

    def get_userid_idnumber(self):
        return self.sql( "select id, idnumber, username from ssismdl_user")()
    
    def get_student_info(self):
        """
        RETURNS NEEDED INFORMATION ABOUT USER FOR students
        """
        get_users = self.sql("select idnumber, username, id, yahoo from ssismdl_user where char_length(idnumber) = 5 and not idnumber like '%P'")()
        user_data = {}
        for idnumber, username, _id, yahoo in get_users:
            ns = Smartformatter()
            ns.username = username
            ns.id = _id
            ns.slc_page = yahoo
            user_data[idnumber] = ns
        return user_data

    def get_all_users_enrollments(self):
        """ returns list of tuple (idnumber, groupname, courseidnumber) """
        return self.sql("select usr.idnumber, grp.name, crs.idnumber from ssismdl_user usr join ssismdl_groups_members gm on gm.userid = usr.id join ssismdl_groups grp on gm.groupid = grp.id join ssismdl_course crs on grp.courseid = crs.id where LENGTH(usr.idnumber)>0 and crs.id IN ({})".format(
            ",".join(self.get_teaching_learning_courses())
            ))()

    def get_all_users_activity_enrollments(self):
        return self.sql("select crs.fullname, usr.idnumber from ssismdl_enrol enrl join ssismdl_user_enrolments usrenrl on usrenrl.enrolid = enrl.id join ssismdl_course crs on enrl.courseid = crs.id join ssismdl_user usr on usrenrl.userid = usr.id where enrl.enrol = 'self'")()
        
        return self.sql("select usr.idnumber, crs.idnumber from ssismdl_user usr join ssismdl_course crs on grp.courseid = crs.id where LENGTH(usr.idnumber)>0 and crs.id IN (idnumber, grp.name, crs.idnumber from ssismdl_user usr join ssismdl_groups_members gm on gm.userid = usr.id join ssismdl_groups grp on gm.groupid = grp.id join ssismdl_course crs on grp.courseid = crs.id where LENGTH(usr.idnumber)>0 and crs.id I{})".format(
            ",".join(self.get_activities_courses())
            ))()
    
    def get_user_enrollments(self, idnumber):
        """ returns a list of tuples [(idnumber, groupname, courseidnumber)] """
        return self.sql("select usr.idnumber, grp.name, crs.idnumber from ssismdl_user usr join ssismdl_groups_members gm on gm.userid = usr.id join ssismdl_groups grp on gm.groupid = grp.id join ssismdl_course crs on grp.courseid = crs.id where usr.idnumber = '{}'".format(idnumber))()

    def get_user_cohort_enrollments(self):
        return self.sql("select usr.idnumber, cht.idnumber from ssismdl_cohort_members chtm join ssismdl_user usr on chtm.userid=usr.id join ssismdl_cohort cht on chtm.cohortid = cht.id where LENGTH(usr.idnumber)>0")()

    def get_user_profile_data(self):
        """
        RETURNS ANY PROFILE FIELD INFORMATION THAT BEGINS WITH 'is'
        """
        return self.sql("select usr.idnumber, usr.id, uif.shortname, uid.data from ssismdl_user_info_field uif join ssismdl_user_info_data uid on uid.fieldid = uif.id join ssismdl_user usr on uid.userid = usr.id where uif.shortname like 'is%'")()

    def get_parent_cohort_enrollments(self):
        return self.sql("select usr.idnumber, cht.idnumber from ssismdl_cohort_members chtm join ssismdl_user usr on chtm.userid=usr.id join ssismdl_cohort cht on chtm.cohortid = cht.id where POSITION('P' IN usr.idnumber)>0")()

    def get_parent_child_associations(self):
        """
        Returns which accounts are linked to which accounts
        """
        return self.sql("select usr.idnumber as parent, usr.id, child.idnumber as child from ssismdl_user usr join ssismdl_role_assignments ra on ra.userid = usr.id join ssismdl_role role on role.id = ra.roleid join ssismdl_context ctx on ctx.id = ra.contextid and ctx.contextlevel = 30 join ssismdl_user child on child.id = ctx.instanceid where role.shortname = 'parent' order by usr.idnumber")()

    def get_teaching_learning_categories(self):
        """
        Returns a tuple of every category within 'Teaching & Learning'
        Useful for subsequent call to get all courses within that category
        """
        result = self.sql("select id from ssismdl_course_categories where path like '/50/%'")()
        return { str(value[0]) for value in result }

    def get_teaching_learning_courses(self):
        """ Returns a set of id of courses that are in teaching/learning """
        result = self.sql("select id, idnumber, category from ssismdl_course where category in ({})".format(
            ",".join([str(c) for c in self.get_teaching_learning_categories()])
            ))
        return { str(item[0]) for item in result }

    def get_activities_courses(self):
        result = self.sql("select id, idnumber, category from ssismdl_course where category = '1'")()
        return { str(item[0]) for item in result }

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

    def __init__(self, database_name, field_name, samples=None):
        super().__init__()
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

    def __init__(self, database_name, field_name):
        super().__init__()
        self.field_name = field_name
        self.target = self.sql(
            "select ssismdl_data_fields.id from ssismdl_data join ssismdl_data_fields on (ssismdl_data.name = '{}' and ssismdl_data.id = ssismdl_data_fields.dataid and ssismdl_data_fields.name = '{}')"
            .format(database_name, field_name)
            )

        self.target_id = self.target()[0][0]

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

    db = DragonNetDBConnection()
    results = db.get_all_users_activity_enrollments()
    for result in results:
        if 'Minecraft' in result[0]:
            print(result)
