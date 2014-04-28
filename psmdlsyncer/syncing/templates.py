import logging
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.sql.MoodleDatabase import MoodleDBConnection
log = logging.getLogger(__name__)

class dry_run:
    """
    Easy way to enable/disable debugging with a decorator
    """
    def __init__(self, debug=False):
        self.debug = debug
    def __call__(self, what):
        if not self.debug:
            return what
        else:
            return lambda *args, **kwargs: log.warning('{} called, but debugging on.'.format(what))

class DefaultTemplate:
    """
    Templates' job is to unpack the items that it is passed
    (probably ModificationStatements, but we don't really care what they are)
    and send it on to the low-level handlers
    This one just prints out what it sees
    """
    def __init__(self):
        self.logger = logging.getLogger("DefaultTemplate")
        self.default_logger = self.logger.info

    def get(self, item, default=None):
        return getattr(self, item, default) if hasattr(self, item) else default

    def old_student(self, item):
        self.default_logger("Found student who has now left: {}".format(item.left))

    def new_student(self, item):
        self.default_logger("Found new student: {}".format(item.right))

    def homeroom_changed(self, item):
        self.default_logger("Put {0.right} in homeroom: {0.right.homeroom}".format(item))

    def remove_from_cohort(self, item):
        self.default_logger("Take {0.right} out of this cohort: {0.param}".format(item))

    def add_to_cohort(self, item):
        self.default_logger("Put {0.left} into this cohort: {0.param}".format(item))

    def new_teacher(self, item):
        self.default_logger("We have a new teacher! {0.param}".format(item))

    def old_teacher(self, item):
        self.default_logger("Get out of here! {0.param}".format(item))

    def add_to_group(self, item):
        course = item.param.course
        group = item.param.group
        self.default_logger("Add {0.left} to group {2} in course {1}".format(item, course, group))

    def remove_from_group(self, item):
        course = item.param.course
        group = item.param.group
        self.default_logger("Remove {0.right} from group {2} in course {1}".format(item, course, group))

    def enrol_in_course(self, item):
        course = item.param.course
        group = item.param.group
        self.default_logger("Enrol {0.left} into course {1} in group {2}".format(item, course, group))

    def deenrol_from_course(self, item):
        self.default_logger("De-enrol {0.right} from course {0.param}".format(item))

    def new_schedule(self, item):
        pass

    def old_schedule(self, item):
        pass

    def new_course(self, item):
        self.default_logger("A NEW COURSE! {0.param} ".format(item))

    def old_course(self, item):
        self.default_logger("AN OLD COURSE! {0.param} ".format(item))

    def new_group(self, item):
        self.default_logger("A NEW GROUP! {0.param} ".format(item))

    def old_group(self, item):
        self.default_logger("AN OLD GROUP! {0.param} ".format(item))

    def username_changed(self, item):
        self.default_logger("Username changed! was {0.left.username} should be {0.param} ".format(item))


class MoodleTemplate(DefaultTemplate):
    """
    Unpacks the info that comes in and sends it on to the PHP routines that acutally
    does the work
    Note: If you want to have some sort of queuing feature that, say, makes sure that
    "new_group" gets called before "add_to_group" (to ensure it's already there when adding it)
    This is the place to do it.
    """
    def __init__(self):
        super().__init__()
        self.moodle = MoodleDBConnection()
        self.moodle_mod = ModUserEnrollments()

        # Set up some things
        courses = self.moodle.get_table('course', 'idnumber')
        self.courses = []
        for course in courses:
            course_idnumber = course[0]
            self.courses.append(course_idnumber)

        groups = self.moodle.get_table('groups', 'idnumber')
        self.groups = []
        for group in groups:
            group_name = group[0]
            self.groups.append(group_name)


    def course_exists(self, course_idnumber):
        return course_idnumber in self.courses

    def new_student(self, item):
        """
        """
        #First double-checks to see if we actually do have something in Moodle
        #for example, an account with item.email_address
        student = item.right.idnumber
        self.moodle_mod.new_student(student)

    # def old_student(self, item):
    #     """
    #     TODO: Determine how long it's been since the student has logged info
    #     and then go ahead and delete it
    #     (Deleting in Moodle is actually just setting deleted=1)
    #     """
    #     pass

    def new_teacher(self, item):
        """
        """
        super().new_teacher(item)
        teacher = item.right
        self.moodle_mod.new_teacher(teacher)

    def enrol_in_course(self, item):
        course_idnumber = item.param.course
        yes_no = course_idnumber in self.courses
        if yes_no:
            super().enrol_in_course(item)  # for output
        return yes_no

    def enrol_student_into_course(self, item):
        student = item.right.idnumber
        course = item.param.course
        group = item.param.group
        if self.enrol_in_course(item):   # for output and checking
            self.moodle_mod.enrol_student_into_course(student, course, group) # just pass the whole schedule object itself
        else:
            self.default_logger("Did NOT enrol {} into course {}, because it does not exist in Moodle".format(item.right, course))

    def enrol_teacher_into_course(self, item):
        teacher = item.right.idnumber
        course = item.param.course
        group = item.param.group
        if self.enrol_in_course(item):   # for output and checking
            self.moodle_mod.enrol_teacher_into_course(teacher, course, group) # just pass the whole schedule object itself
        else:
            self.default_logger("Did NOT enrol {} into course {}, because it does not exist in Moodle".format(item.right, course))

    def deenrol_student_from_course(self, item):
        super().deenrol_from_course(item)   # for output
        user = item.right.idnumber
        course = item.param.course
        group = item.param.group
        self.moodle_mod.deenrol_student_from_course(user, course)

    def deenrol_teacher_from_course(self, item):
        super().deenrol_from_course(item)   # for output
        user = item.right.idnumber
        course = item.param.course
        group = item.param.group
        self.moodle_mod.deenrol_teacher_from_course(user, course)

    def add_to_cohort(self, item):
        super().add_to_cohort(item)
        user = item.right.idnumber
        cohort = item.param
        self.moodle_mod.add_user_to_cohort(user, cohort)

    def remove_from_cohort(self, item):
        super().remove_from_cohort(item)
        user = item.left.idnumber
        cohort = item.param
        self.moodle_mod.remove_user_from_cohort(user, cohort)

    def new_group(self, item):
        super().new_group(item)
        course = item.right.course.ID
        group = item.param
        if group in self.groups:
            self.default_logger("Did NOT add group {} because it's already there....".format(group, course))
        elif course in self.courses:
            self.moodle_mod.add_group(group, course)
        else:
            self.default_logger("Did NOT add group {} because course {} does not exist.".format(group, course))

    def old_group(self, item):
        super().old_group(item)
        course = item.left.course
        group = item.param
        if not course or not course in self.courses:
            self.default_logger("Did NOT remove group {} because the correspoding course does not exist.".format(group, course))
        else:
            group = item.param
            self.moodle_mod.delete_group(group, course)

    def add_to_group(self, item):
        super().add_to_group(item)
        user = item.right.idnumber
        group = item.param.group
        course = item.param.course
        if course in self.courses:
            # We don't actually need the course...
            self.moodle_mod.add_user_to_group(user, group)
            #self.default_logger("Successfully put user {} into group {}".format(user, group))
        else:
            self.default_logger("Did NOT put in group {} because course {} does not exist.".format(group, course))

    def remove_from_group(self, item):
        super().remove_from_group(item)
        user = item.right.idnumber
        group = item.param.group
        course = item.param.course
        # We don't actually need the course...
        self.moodle_mod.remove_user_from_group(user, group)
        #self.default_logger("Successfully removed user {} from group {}".format(user, group))

    def username_changed(self, item):
        super().username_changed(item)
        user = item.left
        idnumber = user.idnumber
        from_what = item.left.username
        to_what = item.right.username
        if hasattr(user, 'login_method') and user.login_method == 'nologin':
            # Just go ahead and change it automatically, no need to inform anyone or anything
            self.moodle.update_where('user', where={
                'idnumber':idnumber
                },
                username=to_what)
            #self.default_logger("Successfully changed user {}'s username from {} to {}".format(
            #    idnumber, from_what, to_what
            #    ))

    def homeroom_changed(self, item):
        super().homeroom_changed(item)
        student = item.left
        from_what = item.left.homeroom
        to_what = item.param
        homeroom = item.param
        self.moodle.update_table('user', where={
            'idnumber':student.idnumber
            },
            department=homeroom)
        #self.default_logger("Successfully changed user {}'s homeroom from {} to {}".format(
        #    idnumber, from_what, to_what
        #    ))

