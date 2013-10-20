"""
MOODLEDATABASE

PROVIDES A HIGHER-LEVEL CLASS FOR USE WITH MOODLE INSTALLATIONS
"""
from psmdlsyncer.sql.SQLWrapper import SQLWrapper
from psmdlsyncer.settings import config, requires_setting
from psmdlsyncer.utils.Namespace import NS

class MoodleDBConnection(SQLWrapper):
    """
    PROVIDES ASSORTMENT OF USEFUL SQL QUERIES COMMON TO MOODLE INSTALLATIONS
    """

    def __init__(self):        
        settings = ['db_username', 'db_password', 'db_name', 'db_prefix', 'db_host']
        for setting in settings:
            requires_setting('MOODLE', setting)
        
        super().__init__(config['MOODLE'].get('db_username'),
                         config['MOODLE'].get('db_password'),
                         config['MOODLE'].get('db_prefix'),
                         config['MOODLE'].get('db_host'),
                         config['MOODLE'].get('db_name'))

    def create_temp_storage(self, table_name, *args):
        result = self.exists_temp_storage(table_name)
        if not result:
            column_phrase = ", ".join([a + ' varchar(255)' for a in args])
            self.call_sql('create table temp_{} ({})'.format(table_name, column_phrase))

    def add_temp_storage(self, table_name, **kwargs):
        #TODO: Handle case where there is an apostrophe
        columns_values = kwargs.items()
        columns_phrase = ", ".join([c[0] for c in columns_values])
        values_phrase = "'" + "', '".join([c[1] for c in columns_values]) + "'"
        self.call_sql("insert into temp_{} ({}) values ({})".format(table_name, columns_phrase, values_phrase))

    def clear_temp_storage(self, table_name, **where):
        where_items = where.items()
        if not where_items:
            return False
        where_phrase = " AND ".join(["where {} = '{}'".format(w[0], w[1]) for w in where_items])
        result = self.test_temp_storage(table_name, **where)
        if result:
            self.call_sql("delete from temp_{} {}".format(table_name, where_phrase))
        return result

    def test_temp_storage(self, table_name, **where):
        where_items = where.items()
        where_phrase = " AND ".join(["where {} = '{}'".format(w[0], w[1]) for w in where_items])
        result = self.call_sql("select * from temp_{} {}".format(table_name, where_phrase))
        if result:
            return True
        else:
            return False

    def dump_temp_storage(self, table_name, clear=False):
        """
        Return whatever is in the table, delete it if clear=True
        """
        result = self.call_sql("select * from temp_{}".format(table_name))
        if result and clear:
            self.sql("delete from temp_{}".format(table_name))
        return result

    def get_temp_storage(self, table_name, **where):
        where_items = where.items()
        where_phrase = " AND ".join(["where {} = '{}'".format(w[0], w[1]) for w in where_items])
        result = self.call_sql("select * from temp_{} {}".format(table_name, where_phrase))
        if result:
            return result
        else:
            return ()

    def empty_temp_storage(self, table_name):
        self.call_sql('truncate temp_{}'.format(table_name))

    def exists_temp_storage(self, table_name):
        return self.call_sql("select exists(select 1 from information_schema.tables where table_name = 'temp_{}')".format(table_name))[0][0]

    def delete_temp_storage(self, table_name):
        if self.exists_temp_storage('temp_' + table_name):
            self.call_sql('drop table temp_{}'.format(table_name))

    def list_existing_tables(self, prefix):
        results = self.call_sql("select table_name from information_schema.tables where table_name LIKE '{}%'".format(prefix))
        return [r[0] for r in results]

    def get_all_user_ids(self):
        return [i[0] for i in self.call_sql('select idnumber from ssismdl_user where deleted = 0')]

    def get_all_parent_name_ids(self):
        return self.call_sql("select idnumber, username from ssismdl_user where deleted = 0 and idnumber like '%P'")                

    def get_all_user_name_ids(self):
        return self.call_sql('select idnumber, username, firstname, lastname from ssismdl_user where deleted = 0')

    def get_all_students_name_ids(self):
        return self.call_sql("select idnumber, username, firstname, lastname from ssismdl_user where deleted = 0 and not idnumber like '%P'")

    def does_user_exist(self, idnumber):
        """
        We use the idnumber to ascertain if a student or parent account is there or not
        True if user exists, False if not
        """
        result = self.call_sql( "select username from ssismdl_user where idnumber = '{}'".format(idnumber) )
        return result

    def user_is_new(self, idnumber):
        result = self.call_sql( "select lastlogin, lastaccess from ssismdl_user where idnumber = '{}'".format(idnumber) )
        if not result:
            return False
        lastlogin, lastaccess = result[0]
        return int(lastlogin) == 0 and int(lastaccess) == 0

    def get_userid_idnumber(self):
        return self.call_sql( "select id, idnumber, username from ssismdl_user")
    
    def get_student_info(self):
        """
        RETURNS NEEDED INFORMATION ABOUT USER FOR students
        """
        get_users = self.call_sql("select idnumber, username, id, yahoo from ssismdl_user where char_length(idnumber) = 5 and not idnumber like '%P'")
        user_data = {}
        for idnumber, username, _id, yahoo in get_users:
            ns = NS()
            ns.username = username
            ns.id = _id
            ns.slc_page = yahoo
            user_data[idnumber] = ns
        return user_data

    def get_all_users_enrollments(self):
        """ returns list of tuple (idnumber, groupname, courseidnumber) """
        return self.call_sql("select usr.idnumber, grp.name, crs.idnumber from ssismdl_user usr join ssismdl_groups_members gm on gm.userid = usr.id join ssismdl_groups grp on gm.groupid = grp.id join ssismdl_course crs on grp.courseid = crs.id where LENGTH(usr.idnumber)>0 and crs.id IN ({})".format(
            ",".join(self.get_teaching_learning_courses())
            ))

    def get_all_users_activity_enrollments(self):
        return self.call_sql("select crs.fullname, usr.idnumber from ssismdl_enrol enrl join ssismdl_user_enrolments usrenrl on usrenrl.enrolid = enrl.id join ssismdl_course crs on enrl.courseid = crs.id join ssismdl_user usr on usrenrl.userid = usr.id where enrl.enrol = 'self' and not usr.idnumber = ''")
        
        return self.call_sql("select usr.idnumber, crs.idnumber from ssismdl_user usr join ssismdl_course crs on grp.courseid = crs.id where LENGTH(usr.idnumber)>0 and crs.id IN (idnumber, grp.name, crs.idnumber from ssismdl_user usr join ssismdl_groups_members gm on gm.userid = usr.id join ssismdl_groups grp on gm.groupid = grp.id join ssismdl_course crs on grp.courseid = crs.id where LENGTH(usr.idnumber)>0 and crs.id I{})".format(
            ",".join(self.get_activities_courses())
            ))
    
    def get_user_enrollments(self, idnumber):
        """ returns a list of tuples [(idnumber, groupname, courseidnumber)] """
        return self.call_sql("select usr.idnumber, grp.name, crs.idnumber from ssismdl_user usr join ssismdl_groups_members gm on gm.userid = usr.id join ssismdl_groups grp on gm.groupid = grp.id join ssismdl_course crs on grp.courseid = crs.id where usr.idnumber = '{}'".format(idnumber))

    def get_user_cohort_enrollments(self):
        return self.call_sql("select usr.idnumber, cht.idnumber from ssismdl_cohort_members chtm join ssismdl_user usr on chtm.userid=usr.id join ssismdl_cohort cht on chtm.cohortid = cht.id where LENGTH(usr.idnumber)>0")

    def get_user_profile_data(self):
        """
        RETURNS ANY PROFILE FIELD INFORMATION THAT BEGINS WITH 'is'
        """
        return self.call_sql("select usr.idnumber, usr.id, uif.shortname, uid.data from ssismdl_user_info_field uif join ssismdl_user_info_data uid on uid.fieldid = uif.id join ssismdl_user usr on uid.userid = usr.id where uif.shortname like 'is%'")

    def get_parent_cohort_enrollments(self):
        return self.call_sql("select usr.idnumber, cht.idnumber from ssismdl_cohort_members chtm join ssismdl_user usr on chtm.userid=usr.id join ssismdl_cohort cht on chtm.cohortid = cht.id where POSITION('P' IN usr.idnumber)>0")

    def get_parent_child_associations(self):
        """
        Returns which accounts are linked to which accounts
        """
        return self.call_sql("select usr.idnumber as parent, usr.id, child.idnumber as child from ssismdl_user usr join ssismdl_role_assignments ra on ra.userid = usr.id join ssismdl_role role on role.id = ra.roleid join ssismdl_context ctx on ctx.id = ra.contextid and ctx.contextlevel = 30 join ssismdl_user child on child.id = ctx.instanceid where role.shortname = 'parent' order by usr.idnumber")

    def get_teaching_learning_categories(self):
        """
        Returns a tuple of every category within 'Teaching & Learning'
        Useful for subsequent call to get all courses within that category
        """
        result = self.call_sql("select id from ssismdl_course_categories where path like '/50/%'")
        return { str(value[0]) for value in result }

    def get_teaching_learning_courses(self):
        """ Returns a set of id of courses that are in teaching/learning """
        result = self.sql("select id, idnumber, category from ssismdl_course where category in ({})".format(
            ",".join([str(c) for c in self.get_teaching_learning_categories()])
            ))
        return { str(item[0]) for item in result }

    def get_activities_courses(self):
        result = self.call_sql("select id, idnumber, category from ssismdl_course where category = '1'")
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
            response = self.call_sql('select idnumber, username, firstname, lastname from ssismdl_user;')
            for item in response:
                split = item.split("|")
                if not len(split) == 3:
                    continue
                idnumber, username, firstname, lastname = [s.strip() for s in strip]
                if not idnumber or not idnumber.isdigit():
                    continue
                self.id_username[username] = {'idnum':idnumber, 'name':lastname+", "+firstname}

        return self.id_username



if __name__ == "__main__":

    db = MoodleDBConnection()
    if db.table_exists("blahs"):
        print("EXISTS")
    else:
        print("DOESN'T EXIST")
    print(db.get_unique_row("user", "username", "email", email='happystudent@student.ssis-suzhou.net', idnumber='99999'))

    print(db.list_existing_tables('ssismdl_'))
