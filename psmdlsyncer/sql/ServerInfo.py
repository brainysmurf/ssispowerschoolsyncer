from psmdlsyncer.sql import MoodleDBConnection
from psmdlsyncer.settings import logging, config
import os

from psmdlsyncer.exceptions import StudentChangedName, NoStudentInMoodle, NoEmailAddress, NoParentAccount, ParentAccountNotAssociated, ParentNotInGroup, GroupDoesNotExist, StudentNotInGroup

class ServerInfo(MoodleDBConnection):

    def __init__(self):
        """
        moodle_account should be config info
        """
        self.logger = logging.getLogger(self.__class__.__name__)

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
            self.init_users_and_groups()

            # We'll need course information when enrolling into groups
            # this way we can avoid infinite loops
            self.logger.debug("Reading in course informaiton from database now")
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

        self.logger.debug("Reading in student accounts from database now")
        get_students = self.sql('select id, idnumber, username from ssismdl_user where deleted = 0')()
        self.logger.debug("Looping through results and setting up students and family dict information")
        for item in get_students:
            id, idnumber, username = item
            if idnumber.isdigit():
                self.students[idnumber] = username
            elif idnumber.endswith('P'):
                self.families[idnumber] = []
            self.users_db_map[id] = idnumber

        self.logger.debug("Reading in parent and student associations from database now")
        get_families = self.get_parent_child_associations()
        self.logger.debug("Looping through and putting children information into family dict")
        for family in get_families:
            idnumber, _id, child = family
            if not idnumber:
                # Many accounts don't have idnumber... exclude teachers
                continue
            f = self.families.get(idnumber)
            if f == None:
                #TODO: Implement as some email feature
                self.logger.debug("Something wrong with parent account:\n{}".format(family))
                continue
            f.append(child)

        self.logger.debug("Reading in group information from database")
        get_groups = self.sql('select id, name from ssismdl_groups')()
        self._group_names = {}  # dict of just their names
        self._groups = {}        # dict of groups user is in
        self.logger.debug("Setting up _groups dict now")
        for item in get_groups:
            groupid, groupname = item
            self._group_names[groupid] = groupname

        self.logger.debug("Reading in group member information from database")
        self._group_members = {}
        group_members = self.sql('select groupid, userid from ssismdl_groups_members')()
        self.logger.debug("Looping through members and setting up _group_members dict")
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
        self.logger.debug("Checking current server information for student:\n{}".format(student))
        if student.is_secondary:
            # Account-based checks
            if self.moodle_config and self.sync_moodle:
                if self.students.get(idnumber):
                    if not username == self.students[idnumber]:
                        # Use the one that we know from DragonNet
                        # This error will not happen again
                        student.username = self.students[idnumber]
                        if not 'StudentChangedName' in dontraise:
                            self.logger.debug("Raising StudentChangedName")
                            raise StudentChangedName
                else:
                    if not 'NoStudentInMoodle' in dontraise:
                        self.logger.debug("Raising NoStudentInMoodle")
                        raise NoStudentInMoodle

                self.logger.debug("Checking students' own enrollments")
                for i in range(len(student.courses())):
                    course = student.courses()[i]
                    self.logger.debug("Looking at enrollments for course {}".format(course))
                    group = student.groups()[i]
                    members = self._group_members.get(group)

                    if members:
                        if not student.num in members:
                            if not course in self.courses.keys():
                                self.logger.warn("Not raising StudentNotInGroup because the course {} doesn't exist".format(course))
                                continue
                            if not 'StudentNotInGroup' in dontraise:
                                self.logger.debug("This student is not in group {}:\n{}".format(group, student))
                                raise StudentNotInGroup
                        else:
                            pass # ok
                    else:
                        self.logger.warn("This group doesn't exist at all: {}".format(group))
                        if not course in self.courses.keys():
                            self.logger.warn("Not raising 'GroupDoesNotExist' because the course {} doesn't exist".format(course))
                            continue
                        if not 'GroupDoesNotExist' in dontraise:
                            raise GroupDoesNotExist

            if self.email_config and self.sync_email:
                if self.email_config.get('accounts_path'):
                    if not os.path.exists(self.email_config.get('accounts_path') + '/' + student.username):
                        if not 'NoEmailAddress' in dontraise:
                            self.logger.debug("Raising NoEmailAddress")
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
                            self.logger.debug("Student account {} not associated with parent".format(student.num))
                            raise ParentAccountNotAssociated

            self.logger.debug("Now checking parent account enrollments")
            for i in range(len(student.courses())):
                course = student.courses()[i]
                group = student.groups()[i]

                groups = self._groups.get(student.family_id)
                if not groups and not 'ParentNotInGroup' in dontraise:
                    raise ParentNotInGroup
                if not group in groups:
                    if not course in self.courses.keys():
                        self.logger.debug("Not raising ParentNotInGroup because the course {} doesn't exist".format(course))
                        continue
                    self.logger.debug("This parent is not in group {}:\n{}".format(group, student.family_id))
                    if not 'ParentNotInGroup' in dontraise:
                        raise ParentNotInGroup
                else:
                    pass # ok