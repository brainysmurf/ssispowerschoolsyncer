from utils.DB import DragonNetDBConnection
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

    def __init__(self, verbose=True,
                 dry_run=True,
                 email_config=None,
                 moodle_config=None):
        """
        moodle_account should be config info
        """
        self.dry_run = dry_run
        self.email_config = email_config
        self.moodle_config = moodle_config
        if self.moodle_config:

            user = moodle_config.get('database_user')
            password = moodle_config.get('database_password')
            database = moodle_config.get('database_name')
            self.server = moodle_config.get('host')
            self.sync_moodle = moodle_config.getboolean('sync', False)
            self.sync_email  = email_config.getboolean('sync', False)

            super().__init__(user, password, self.server, database, verbose=verbose)
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
            if self.moodle_config and self.sync_moodle:
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
                    
            if self.email_config and self.sync_email:
                if self.email_config.get('accounts_path'):
                    if not os.path.exists(self.email_config.get('accounts_path') + '/' + student.username):
                        self.verbose and print("Raising NoEmailAddress")
                        raise NoEmailAddress

        if student.is_elementary:
            # Don't need to check for whether parent account exists or not, because that
            # will happen in family info below
            if student.grade == 5:
                if self.email_config and self.sync_email:
                    if not os.path.exists(self.email_config.get('accounts_path') + '/' + student.username):
                        self.verbose and print("Raising NoEmailAddress")
                        input(self)
                        raise NoEmailAddress

        familyid = student.family_id
        if self.sync_moodle:
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