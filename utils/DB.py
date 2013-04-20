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

class StudentChangedName(Exception):
    pass

class NoStudentInMoodle(Exception):
    pass

class NoEmailAddress(Exception):
    pass

class NoParentAccount(Exception):
    pass

class ParentAccountNotAssociated(Exception):
    pass

class ParentNotInGroup(Exception):
    pass

class GroupDoesNotExist(Exception):
    pass

class StudentNotInGroup(Exception):
    pass

class MustExit(Exception):
    pass

class DBConnection:
    """
    Glue code between me and the database
    """

    def __init__(self, user, password, server, database, verbose=False):
        sf = Smartformatter(user=user, password=password, server=server, database=database)
        self.last_call = None
        self._database = database
        self.verbose = verbose
        self.verbose and input(sf("About to connect to {server}"))
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

    def __init__(self, server, verbose=False):
        super().__init__('moodle', 'ssissqlmoodle', server, 'moodle', verbose=verbose)

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
        try:
            self.target = self.sql(
            "select ssismdl_data_fields.id from ssismdl_data join ssismdl_data_fields on (ssismdl_data.name = '{}' and ssismdl_data.id = ssismdl_data_fields.dataid and ssismdl_data_fields.name = '{}')"
            .format(database_name, field_name)
            )
        except:
            self.target_id = 0
            return
        self.target_id = self.target()[0][0]

    def update_menu(self, value):
        """
        
        """
        if isinstance(value, list):
            value = "\r\n".join(value)
        command = "update ssismdl_data_fields set param1 = '{}' where id = {}".format(value, self.target_id)
        try:
            self.sql(command)()
        except:
            print("I was unable to issue the following sql command: {}".format(command))

class ServerInfo(DragonNetDBConnection):

    def __init__(self, verbose=True,
                 dry_run=True,
                 email_accounts=False,
                 moodle_accounts={}):
        """
        moodle_account should be config info
        """
        self.dry_run = dry_run
        self.email_accounts = email_accounts
        self.moodle_accounts = moodle_accounts
        if self.moodle_accounts:
            self.server = moodle_accounts.get('host')
            super().__init__(self.server, verbose=verbose)
            self.init_users_and_groups()

            # We'll need course information when enrolling into groups
            # this way we can avoid infinite loops
            self.verbose and print("Reading in course informaiton from database now")
            get_courses = self.sql('select id, shortname from ssismdl_course')()
            for item in get_courses:
                courseid, shortname = item
                self.courses[shortname] = courseid
        else:
            self.db = None

    def init_users_and_groups(self):
        """
        Sets up internal databases for use with syncs
        """
        self.students = {}
        self.courses = {}
        self.users_db_map = {}
        self.families = {}

        self.verbose and print("Reading in student accounts from database now")
        get_students = self.sql('select id, idnumber, username from ssismdl_user where deleted = 0')()
        self.verbose and print("Looping through results and setting up students and family dict information")
        for item in get_students:
            id, idnumber, username = item
            if idnumber.isdigit():
                self.students[idnumber] = username
            elif idnumber.endswith('P'):
                self.families[idnumber] = []
            self.users_db_map[id] = idnumber

        self.verbose and print("Reading in parent and student associations from database now")
        get_families = self.get_parent_child_associations()
        self.verbose and print("Looping through and putting children information into family dict")
        for family in get_families:
            idnumber, _id, child = family
            if not idnumber:
                # Many accounts don't have idnumber... exclude teachers
                continue
            f = self.families.get(idnumber)
            if f == None:
                #TODO: Implement as some email feature
                self.verbose and print("Something wrong with parent account:\n{}".format(family))
                continue
            f.append(child)

        self.verbose and print("Reading in group information from database")
        get_groups = self.sql('select id, name from ssismdl_groups')()
        self._group_names = {}  # dict of just their names
        self._groups = {}        # dict of groups user is in
        self.verbose and print("Setting up _groups dict now")
        for item in get_groups:
            groupid, groupname = item
            self._group_names[groupid] = groupname

        self.verbose and print("Reading in group member information from database")
        self._group_members = {}
        group_members = self.sql('select groupid, userid from ssismdl_groups_members')()
        self.verbose and print("Looping through members and setting up _group_members dict")
        for item in group_members:
            groupid, userid = item

            groupname = self._group_names[groupid]

            # Some users will be in the database but aren't necessarily students, or are old students
            # So we'll be very careful how we figure the following out:
            if not groupname in list(self._group_members.keys()):
                self._group_members[groupname] = []
            if not userid in self.users_db_map.keys():
                continue
            usernum = self.users_db_map[userid]
            if not usernum in self._groups:
                self._groups[usernum] = []
            # Store the actual information
            self._groups[usernum].append(groupname)
            self._group_members[groupname].append(usernum)

    def check_student(self, student):
        """
        Raises errors describing what has happened, if anything
        Does not handle infinite loops though
        """
        if not self.db:
            return
        idnumber = student.num
        username = student.username
        self.verbose and print("Checking current server information for student:\n{}".format(student))
        if student.is_secondary:
            # Account-based checks
            if self.moodle_accounts:
                if self.students.get(idnumber):
                    if not username == self.students[idnumber]:
                        # Use the one that we know from DragonNet
                        # This error will not happen again
                        student.username = self.students[idnumber]
                        self.verbose and print("Raising StudentChangedName")
                        raise StudentChangedName
                    else:
                        self.verbose and print("Account exists in moodle")
                else:
                    self.verbose and print("Raising NoStudentInMoodle")
                    raise NoStudentInMoodle

                self.verbose and print("Checking enrollments")
                for i in range(len(student.courses())):
                    course = student.courses()[i]
                    self.verbose and print("Looking at enrollments for course {}".format(course))
                    group = student.groups()[i]
                    members = self._group_members.get(group)

                    self.verbose and print("Checking out students' own enrollments")
                    if members:
                        if not student.num in members:
                            if not course in self.courses.keys():
                                self.verbose and print("Not raising StudentNotInGroup because the course {} doesn't exist".format(course))
                                continue
                            self.verbose and print("This student is not in group {}:\n{}".format(group, student))
                            raise StudentNotInGroup
                        else:
                            pass # ok
                    else:
                        self.verbose and print("This group doesn't exist at all: {}".format(group))
                        if not course in self.courses.keys():
                            self.verbose and print("Not raising GroupDoesNotExist because the course {} doesn't exist".format(course))
                            continue
                        raise GroupDoesNotExist
                # TODO: Implement this in preparation for 2012/13 school year
                # Now see about deleting groups they shouldn't be a part of
                # Not yet implemented because I don't have the balls to actually do this,
                # lest something happen and I am unawares
                #if not student.groups() == self._groups[student.num]:
                #    database_groups = set(self._groups[student.num])
                #    schedule_groups = set(student.groups())
                #    self.verbose and print("Going through each group that is in the database but not in the schedule")
                #    for group in schedule_groups:
                #        print(group)
                #    print('------')
                #    for group in database_groups.difference(schedule_groups):
                #        if group.endswith('12') or group.endswith('11'):
                #            continue
                #        print(group)
                #    input()

                # Now see if I should de-enrol anyone from a course
                # Don't do this yet, because we have to filter out things by the teaching & learning category
                # Yuck
                # TODO: Unenroll students from courses in teaching & learning they don't need to be in anymore
                    
            if self.email_accounts and not os.path.exists('/home/{}'.format(username)):  #TODO: use path provided in settings
                input(self.email_accounts)
                if self.email_accounts: 
                    self.verbose and print("Raising NoEmailAddress")
                    raise NoEmailAddress

        familyid = student.family_id
        if not familyid in list(self.families.keys()):
            raise NoParentAccount
        else:
            if student.is_secondary:
                if not student.num in self.families[familyid]:
                    self.verbose and print("Student account {} not in here: {}".format(student.num, self.families[familyid]))
                    raise ParentAccountNotAssociated

        self.verbose and print("Now checking parent account enrollments")
        for i in range(len(student.courses())):
            course = student.courses()[i]
            group = student.groups()[i]
            members = self._group_members.get(group)

            if members:
                if not student.family_id in members:
                    if not course in self.courses.keys():
                        self.verbose and print("Not raising ParentNotInGroup because the course {} doesn't exist".format(course))
                        continue
                    self.verbose and print("This parent is not in group {}:\n{}".format(group, student.family_id))
                    raise ParentNotInGroup
                else:
                    pass # ok

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
