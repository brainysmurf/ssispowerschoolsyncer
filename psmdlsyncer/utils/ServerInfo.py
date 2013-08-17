from psmdlsyncer.utils.DB import DragonNetDBConnection
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

class ParentNotInGroup(Exception):
    pass

class GroupDoesNotExist(Exception):
    pass

class StudentNotInGroup(Exception):
    pass

class MustExit(Exception):
    pass

class ServerInfo(DragonNetDBConnection):

    def __init__(self):
        """
        moodle_account should be config info
        """
        #TODO: Just use settings.config
        from psmdlsyncer.settings import config

        self.courses = {}
        self.email_config = config['EMAIL']
        self.moodle_config = config['MOODLE']
        if self.moodle_config:
            user = self.moodle_config.get('database_user')
            password = self.moodle_config.get('database_password')
            database = self.moodle_config.get('database_name')
            self.server = self.moodle_config.get('host')
            self.sync_moodle = self.moodle_config.getboolean('sync', False)
            self.sync_email  = self.email_config.getboolean('sync', False)

            super().__init__()
            self.verbose = True
            self.init_users_and_groups()

            # We'll need course information when enrolling into groups
            # this way we can avoid infinite loops
            self.verbose and print("Reading in course informaiton from database now")
            get_courses = self.sql('select id, idnumber from ssismdl_course')()
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

    def check_student(self, student, dontraise=(), onlyraise=()):
        """
        Raises errors describing what has happened, if anything
        Does not handle infinite loops though
        """
        # First, process the dontraise and onlyraise
        # onlyraise takes on priority over dontraise
        if onlyraise:
            all = ('StudentChangedName', 'NoStudentInMoodle',
                   'NoParentAccount', 'StudentNotInGroup',
                   'GroupDoesNotExist', 'NoEmailAddress',
                   'ParentAccountNotAssociated', 'ParentNotInGroup')
            dontraise = tuple( set(all) - set(onlyraise) )
        
        if not self.db:
            return
        idnumber = student.num
        username = student.username
        self.verbose and print("Checking current server information for student:\n{}".format(student))
        if student.is_secondary:
            # Account-based checks
            if self.moodle_config and self.sync_moodle:
                if self.students.get(idnumber):
                    if not username == self.students[idnumber]:
                        # Use the one that we know from DragonNet
                        # This error will not happen again
                        student.username = self.students[idnumber]
                        if not 'StudentChangedName' in dontraise:
                            self.verbose and print("Raising StudentChangedName")
                            raise StudentChangedName
                    else:
                        self.verbose and print("Account exists in moodle")
                else:
                    if not 'NoStudentInMoodle' in dontraise:
                        self.verbose and print("Raising NoStudentInMoodle")
                        raise NoStudentInMoodle

                self.verbose and print("Checking students' own enrollments")
                for i in range(len(student.courses())):
                    course = student.courses()[i]
                    self.verbose and print("Looking at enrollments for course {}".format(course))
                    group = student.groups()[i]

                    if members:
                        if not student.num in members:
                            if not course in self.courses.keys():
                                self.verbose and print("Not raising StudentNotInGroup because the course {} doesn't exist".format(course))
                                continue
                            if not 'StudentNotInGroup' in dontraise:
                                self.verbose and print("This student is not in group {}:\n{}".format(group, student))
                                raise StudentNotInGroup
                        else:
                            pass # ok
                    else:
                        self.verbose and print("This group doesn't exist at all: {}".format(group))
                        if not course in self.courses.keys():
                            self.verbose and print("Not raising GroupDoesNotExist because the course {} doesn't exist".format(course))
                            continue
                        if not 'GroupDoesNotExist' in dontraise:
                            raise GroupDoesNotExist

            if self.email_config and self.sync_email:
                if self.email_config.get('accounts_path'):
                    if not os.path.exists(self.email_config.get('accounts_path') + '/' + student.username):
                        if not 'NoEmailAddress' in dontraise:
                            self.verbose and print("Raising NoEmailAddress")
                            raise NoEmailAddress

        familyid = student.family_id
        if self.sync_moodle:
            if not familyid in list(self.families.keys()):
                if not 'NoParentAccount' in dontraise:
                    raise NoParentAccount
            else:
                if student.is_secondary:
                    if not student.num in self.families[familyid]:
                        if not 'ParentAccountNotAssociated' in dontraise:
                            self.verbose and print("Student account {} not associated with parent".format(student.num))
                            raise ParentAccountNotAssociated

            self.verbose and print("Now checking parent account enrollments")
            for i in range(len(student.courses())):
                course = student.courses()[i]
                group = student.groups()[i]

                if not group in self._groups.get(student.family_id):
                    if not course in self.courses.keys():
                        self.verbose and print("Not raising ParentNotInGroup because the course {} doesn't exist".format(course))
                        continue
                    self.verbose and print("This parent is not in group {}:\n{}".format(group, student.family_id))
                    if not 'ParentNotInGroup' in dontraise:
                        raise ParentNotInGroup
                else:
                    pass # ok
