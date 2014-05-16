import logging
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.sql.MDB import MoodleDBSession
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
    only = "course_grade_changed"    # for debugging

    def __init__(self):
        self.logger = logging.getLogger("DefaultTemplate")
        self.default_logger = self.logger.info

    def __getattribute__(self, name):
        if '_' in name:
            if object.__getattribute__(self, 'only'):
                if name == object.__getattribute__(self, 'only'):
                    return object.__getattribute__(self, name)
                else:
                    return object.__getattribute__(self, 'dummy')
            else:
                return super().__getattribute__(name)
        else:
            return super().__getattribute__(name)

    def dummy(self, *args, **kwargs):
        pass

    def get(self, item, default=None):
        return getattr(self, item, default) if hasattr(self, item) else default

    def old_student(self, item):
        pass # for now
        self.default_logger("Found student who has now left: {}".format(item.left))

    def old_parent(self, item):
        pass

    def new_student(self, item):
        self.default_logger("Found new student: {}".format(item.right))

    def homeroom_changed(self, item):
        self.default_logger("Put {0.right} in homeroom: {0.right.homeroom}".format(item))

    def remove_from_cohort(self, item):
        self.default_logger("Take {0.right} out of this cohort: {0.param}".format(item))

    def add_to_cohort(self, item):
        self.default_logger("Put {0.left} into this cohort: {0.param}".format(item))

    def new_teacher(self, item):
        self.logger.info("Found a new teacher! {0.param}".format(item))

    def new_student(self, item):
        self.logger.info("Found a new student! {0.param}".format(item))

    def new_parent(self, item):
        self.logger.info("Found a new parent! {0.param}".format(item))

    def old_teacher(self, item):
        self.logger.warning("Found teacher who has now left: {0.param}".format(item))

    def add_to_group(self, item):
        course = item.param.course
        group = item.param.group
        self.default_logger("Add {0.left} to group {2} in course {1}".format(item, course, group))

    def remove_from_group(self, item):
        course = item.param.course
        group = item.param.group
        self.default_logger("Remove {0.left} from group {2} in course {1}".format(item, course, group))

    def enrol_in_course(self, item):
        course = item.param.course
        group = item.param.group
        self.default_logger("Enrol {0.left} into course {1} in group {2}".format(item, course, group))

    def deenrol_from_course(self, item):
        self.default_logger("De-enrol {0.left} from course {0.param.course}".format(item))

    def new_schedule(self, item):
        pass

    def old_schedule(self, item):
        pass

    def new_cohort(self, item):
        self.default_logger("A NEW COHORT! {0.param} ".format(item))

    def old_cohort(self, item):
        self.default_logger("AN OLD COHORT! {0.param} ".format(item))

    def new_course(self, item):
        self.default_logger("A NEW COURSE! {0.param} ".format(item))

    def old_course(self, item):
        self.default_logger("AN OLD COURSE! {0.param} ".format(item))

    def new_group(self, item):
        self.default_logger("A NEW GROUP! {0.param} (should be created when someone enrolls...)".format(item))

    def old_group(self, item):
        self.default_logger("AN OLD GROUP! {0.param} ".format(item))

    def username_changed(self, item):
        self.default_logger("Username changed! was {0.left.username} should be {0.param} ".format(item))

    def add_custom_profile_field_to_user(self, item):
        self.default_logger("Adding custom profile field {0.param.field} to user {0.right.idnumber}".format(item))

    def remove_custom_profile_field_to_user(self, item):
        self.default_logger("Remove custom profile field? {0.param.field}".format(item))

    def course_grade_changed(self):
        self.default_logger("Course {0.left.idnumber} grade changed to {0.right.param} ".format(item))

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
        self.moodle = MoodleDBSession()
        self.moodle_mod = ModUserEnrollments()

        # Set up some things
        self.courses = self.moodle.get_list_of_attributes('course', 'idnumber')
        self.groups = self.moodle.get_list_of_attributes('group', 'name')

    def course_exists(self, course_idnumber):
        return course_idnumber in self.courses

    def new_cohort(self, item):
        super().new_cohort(item)
        cohort_name = ""  # unknown, only matters to front-end
        cohort_idnumber = item.param
        self.moodle.add_cohort(cohort_idnumber, cohort_name)

    def old_cohort(self, item):
        super().old_cohort()
        # Remove it?

    def new_student(self, item):
        """
        """
        if self.moodle.wrap_no_result(self.moodle.get_user_from_idnumber, item.right.username):
            self.logger.warning("Student already exists, maybe they are not in the studentsALL group?.")
        else:
            super().new_student(item)
            student = item.right
            self.moodle_mod.new_student(student)
            self.moodle_mod.add_user_to_cohort(student.idnumber, 'studentsALL')

    # def new_teacher(self, item):
    #     """
    #     """
    #     if self.moodle.wrap_no_result(self.moodle.get_user_from_idnumber, item.right.username):
    #         self.logger.warning("Staff member already exists, maybe they are not in the teachersALL or supportALL group?.")
    #     else:
    #         super().new_teacher(item)
    #         teacher = item.right
    #         self.moodle_mod.new_teacher(teacher)
    #         self.moodle_mod.add_user_to_cohort(teacher.idnumber, 'teachersALL')

    # def new_parent(self, item):
    #     """
    #     """
    #     super().new_parent(item)
    #     parent = item.right
    #     self.moodle_mod.new_parent(parent)
    #     self.moodle_mod.add_user_to_cohort(parent.idnumber, 'parentsALL')

    def new_group(self, item):
        """
        Although we detect new groups, the right thing to do is actually to create the group,
        as they are needed,
        when enrolling users.

        That's because groups and courses are inexplicably linked together
        and we have to do the checks for groups when enrolling anyway
        so best is to do the creation there
        """
        super().new_group(item)  # output

    def new_course(self, item):
        super().new_course(item)
        course = item.right
        self.moodle_mod.create_new_course(course.idnumber, course.name)

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

    def enrol_parent_into_course(self, item):
        parent = item.right.idnumber
        course = item.param.course
        group = item.param.group
        if self.enrol_in_course(item):   # for output and checking
            self.moodle_mod.enrol_parent_into_course(parent, course, group) # just pass the whole schedule object itself
        else:
            self.default_logger("Did NOT enrol {} into course {}, because it does not exist in Moodle".format(item.right, course))

    def deenrol_teacher_from_course(self, item):
        super().deenrol_from_course(item)   # for output
        user = item.right.idnumber
        course = item.param.course
        group = item.param.group
        self.moodle_mod.deenrol_teacher_from_course(user, course)

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

    def deenrol_parent_from_course(self, item):
        super().deenrol_from_course(item)   # for output
        user = item.right.idnumber
        course = item.param.course
        group = item.param.group
        self.moodle_mod.deenrol_parent_from_course(user, course)

    def add_to_cohort(self, item):
        super().add_to_cohort(item)
        user = item.right.idnumber
        cohort = item.param
        self.moodle_mod.add_user_to_cohort(user, cohort)

    # def remove_from_cohort(self, item):
    #     super().remove_from_cohort(item)
    #     user = item.left.idnumber
    #     cohort = item.param
    #     self.moodle_mod.remove_user_from_cohort(user, cohort)

    def new_group(self, item):
        course = item.right.course.ID
        group = item.param
        if group in self.groups:
            self.default_logger("Did NOT add group {} because it's already there....".format(group, course))
        elif course in self.courses:
            super().new_group(item)
            self.moodle_mod.add_group(group, course)
        else:
            self.default_logger("Did NOT add group {} because course {} does not exist.".format(group, course))

    def new_custom_profile(self, item):
        """
        This actually means that a particular user doesn't have a particular custom profile
        (It does NOT mean that this profile field doesn't exist...)
        """
        right = item.right
        name = right.idnumber
        self.default_logger("Found a new custom profile field {}".format(name))
        self.moodle.make_new_custom_profile_field(useridnumber, name, value)

    def old_custom_profile(self, item):
        """
        This actually means that a particular user has lost a particular profile field
        (It does NOT mean that this profile field should be deleted...)
        or does it?
        """
        # not sure what to do yet


    def old_group(self, item):
        course = item.left
        group = item.param
        if not course or not course in self.courses:
            self.default_logger("Did NOT remove group {} because the correspoding course does not exist.".format(group, course))
        else:
            super().old_group(item)
            group = item.param
            self.moodle_mod.delete_group(group, course)

    def add_to_group(self, item):
        user = item.right.idnumber
        group = item.param.group
        course = item.param.course
        if course in self.courses:
            super().add_to_group(item)
            # We don't actually need the course...

            self.moodle_mod.add_user_to_group(user, group)
            #self.default_logger("Successfully put user {} into group {}".format(user, group))
        else:
            self.default_logger("Did NOT put {} in group {} because course {} does not exist.".format(user, group, course))

    def remove_from_group(self, item):
        super().remove_from_group(item)
        user = item.right.idnumber
        group = item.param.group
        course = item.param.course
        # We don't actually need the course...
        self.moodle_mod.remove_user_from_group(user, group)

    def username_changed(self, item):
        user = item.left
        idnumber = user.idnumber
        from_what = item.left.username
        to_what = item.right.username
        if hasattr(user, 'login_method') and user.login_method == 'nologin':
            # Just go ahead and change it automatically, no need to inform anyone or anything
            # because the account isn't active anyway
            self.moodle.update_table('user', where={
                'idnumber':idnumber
                },
                username=to_what)
            super().username_changed(item)
        else:
            msg = "Student {} needs his/her username changed manually".format(from_what, to_what)
            if '_' in from_what:
                if from_what.replace('_', '') == to_what:
                    self.default_logger("Student {} with an underscore and whose username has NOT changed to {}.".format(from_what, to_what))
                else:
                    self.logger.warning(msg)
            else:
                self.logger.warning(msg)

    def custom_profile_value_changed(self, item):
        person = item.left.useridnumber
        field = item.param.field
        value = item.param.value
        self.moodle.set_user_custom_profile(person, field, value)

    def add_custom_profile_field_to_user(self, item):
        super().add_custom_profile_field_to_user(item)
        person = item.right.idnumber
        field = item.param.field
        value = item.param.value
        self.moodle.add_user_custom_profile(person, field, value)

    def homeroom_changed(self, item):
        super().homeroom_changed(item)
        student = item.left
        from_what = item.left.homeroom
        homeroom = item.param
        self.moodle.update_table('user', where={
            'idnumber':student.idnumber
            },
            department=homeroom)
        #self.default_logger("Successfully changed user {}'s homeroom from {} to {}".format(
        #    idnumber, from_what, to_what
        #    ))

    def course_grade_changed(self, item):
        if item.left.grade is None:
            # we need to add a new one
            self.moodle.insert_table('course_ssis_metadata',
                courseid = item.left.database_id,
                field='grade',
                value=item.param
                )
        else:
            # we just need to update the existing one
            self.moodle.update_table('course_ssis_metadata',
                where = dict(
                    courseid=item.left.database_id,
                    field='grade',
                    ),
                value=item.param
                )



