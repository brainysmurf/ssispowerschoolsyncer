try:
    import postgresql
except ImportError:
    pass
import os

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

class MustExit(Exception):
    pass

class DBConnection:

    def __init__(self, user, password, database):
        d = {'user':user, 'password':password, 'database':database}
        self.db = postgresql.open('pq://{user}:{password}@localhost/{database}'.format(**d))
        self.sql = self.db.prepare

    def __del__(self):
        if self.db:
            self.db.close()

class DragonNetDBConnection(DBConnection):

    def __init__(self):
        self.on_server = os.path.exists('/home/lcssisadmin')
        if self.on_server:
            super().__init__('moodle', 'ssissqlmoodle', 'moodle')
        else:
            print("Reminder, we are not on the server so no sql will work!")
            self.db = None

    def does_user_exist(self, idnumber):
        """
        We use the idnumber to ascertain if a student or parent account is there or not
        True if user exists, False if not
        """
        result = self.sql( "select username from ssismdl_user where idnumber = '{}'".format(idnumber) )()
        return result

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

    def __init__(self):
        super().__init__()
        self.students = {}
        self.families = {}
        self._checked = []
        if self.on_server:
            get_students = self.sql('select id, idnumber, username from ssismdl_user where deleted = 0')()
            for item in get_students:
                id, idnumber, username = item
                if idnumber.isdigit():
                    self.students[int(idnumber)] = username
                elif idnumber.endswith('P'):
                    self.families[idnumber] = []

            get_families = self.sql("select usr.idnumber as parent, usr.id, child.username as child from ssismdl_user usr join ssismdl_role_assignments ra on ra.userid = usr.id join ssismdl_role role on role.id = ra.roleid join ssismdl_context ctx on ctx.id = ra.contextid and ctx.contextlevel = 30 join ssismdl_user child on child.id = ctx.instanceid where role.shortname = 'parent' order by usr.idnumber")()
            for family in get_families:
                idnumber, _id, child = family
                if not idnumber:
                    # Many accounts don't have idnumber... exclude teachers
                    continue
                f = self.families.get(idnumber)
                if f == None:
                    print(idnumber)
                    print(f)
                    print(family)
                    input("Something wrong with parent account")
                    continue
                f.append(child)

            get_groups = self.sql('select id, name from ssismdl_groups')()
            self._groups = {}
            for item in get_groups:
                groupid, groupname = item
                self._groups[groupid] = groupname
                
            self._group_members = {}
            group_members = self.sql('select groupid, userid from ssismdl_groups_members')()
            for item in group_members:
                groupid, userid = item

                groupid = int(groupid)
                userid = int(userid)
                username = self.sql('select username from ssismdl_user where id = {}'.format(userid))()[0][0]
                groupname = self._groups[groupid]

                if not groupname in list(self._group_members.keys()):
                    self._group_members[groupname] = []
                self._group_members[groupname].append(username)

        print("hello")
        import pdb; pdb.set_trace()

    def check_student(self, student):
        """
        Raises errors describing what has happened, if anything
        Does not handle infinite loops though
        """
        idnumber = student.num
        username = student.username

        if student.idnumber in ['43462', '43463', '43922', '43933', '43932', '43782']:
            import pdb; pdb.set_trace()
        if student.is_secondary:
            # Account-based checks
            if self.students.get(int(idnumber)):
                if not username == self.students[int(idnumber)]:
                    # Use the one that we know from DragonNet
                    # This error will not happen again
                    student.username = self.students[int(idnumber)]
                    raise StudentChangedName
                else:
                    pass # we're good
            else:
                # don't let it repeat, if error occurs, not my problem
                self.students[int(idnumber)] = username
                # raise error, again, if this interrupts the flow, not this class' problem
                raise NoStudentInMoodle

            # Account-information checks
            for group in student.groups():
                members = self._group_members.get(group)
                if members:
                    if not student.username in members:
                        print("This student {} is not in group {}".format(student.lastfirst, group))
                else:
                    print("This group doesn't exist at all: {}".format(group))

            if self.on_server and not os.path.exists('/home/{}'.format(username)):
                raise NoEmailAddress

        familyid = student.family_id
        if not familyid in list(self.families.keys()):
            raise NoParentAccount
        else:
            if student.is_secondary:
                if not student.username in self.families[familyid]:
                    raise ParentAccountNotAssociated
