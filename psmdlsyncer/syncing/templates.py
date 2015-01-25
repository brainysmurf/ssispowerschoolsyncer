import logging
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.sql.MDB import MoodleDBSession
log = logging.getLogger(__name__)
import re, functools
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.exc import IntegrityError
from psmdlsyncer.settings import config_get_section_attribute

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
    #only = "new_cohort"    # for debugging

    def __init__(self):
        self.logger = logging.getLogger("DefaultTemplate")
        self.default_logger = self.logger.warning

    def __getattribute__(self, name):
        if '_' in name:
            if hasattr(self, 'only') and object.__getattribute__(self, 'only'):
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

    def old_teacher(self, item):
        pass # for now
        self.default_logger("Found teacher who has now left: {}".format(item.left))

    def old_parent(self, item):
        pass # for now
        self.default_logger("Found parent who has now left: {}".format(item.left))

    def old_parent_link(self, item):
        pass
 
    def homeroom_changed(self, item):
        self.default_logger("Put {0.right} in homeroom: {0.right.homeroom}".format(item))

    def remove_from_cohort(self, item):
        self.logger.debug("Take {0.right} out of this cohort: {0.param}".format(item))

    def add_to_cohort(self, item):
        self.default_logger("Put {0.left} into this cohort: {0.param}".format(item))

    def new_teacher(self, item):
        self.default_logger("Found a new teacher! {0.param}".format(item))

    def new_student(self, item):
        self.default_logger("Found a new student! {0.param}".format(item))

    def new_parent(self, item):
        self.default_logger("Found a new parent! {0.param}".format(item))

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
        self.logger.debug("A NEW COURSE! {0.param} ".format(item))

    def old_course(self, item):
        self.default_logger("AN OLD COURSE! {0.param} ".format(item))

    def old_course_metadata(self, item):
        self.default_logger("AN OLD COURSE METADATA! {0.param} ".format(item))

    def new_group(self, item):
        self.default_logger("A NEW GROUP! {0.param} (should be created when someone enrolls...)".format(item))

    def old_group(self, item):
        self.default_logger("AN OLD GROUP! {0.param} ".format(item))

    def username_changed(self, item):
        self.default_logger("Username changed! was {0.left.username} should be {0.param} ".format(item))

    def add_custom_profile_field_to_user(self, item):
        self.default_logger("Adding custom profile field {0.param.field} to user {0.right.idnumber}".format(item))

    def remove_custom_profile_field_to_user(self, item):
        # because of the way moodle works, we don't want it to remove, just leave it in there
        # no need to report it, either
        pass

    def course_grade_changed(self):
        self.default_logger("Course {0.left.idnumber} grade changed to {0.right.param} ".format(item))

    def new_parent_link(self, item):
        self.default_logger("New association: {0.param}".format(item))

    def new_mrbs_editor(self, item):
        self.default_logger("Add this person {0.param} as an mrbs editor".format(item))

    def associate_child_to_parent(self, item):
        self.default_logger("Associate child {0.param.child} to parent {0.param.parent} ".format(item))

    def deassociate_child_from_parent(self, item):
        self.default_logger("De-associate child {0.param.child} from parent {0.param.parent} ".format(item))

    def new_timetable(self, item):
        self.default_logger("New timetable {0.param} ".format(item))

    def new_timetable_data(self, item):
        self.logger.debug("New timetable data {0.param} ".format(item))

    def old_timetable_data(self, item):
        self.logger.debug("Old timetable data {0.param} ".format(item))

    def new_online_portfolio(self, item):
        self.default_logger("Creating new online portfolio for student {0.param}".format(item))

    def old_online_portfolio(self, item):
        self.default_logger("The student {0.param} still has an online portfolio".format(item))

    def new_course_metadata(self, item):
        self.logger.debug("New course metadata {0.right} ".format(item))

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
        self.moodlemod = ModUserEnrollments()

        # Set up some things
        self.courses = []
        for course in self.moodle.get_teaching_learning_courses():
            self.courses.append(course.idnumber)
        self.groups = self.moodle.get_list_of_attributes('group', 'name')

    def course_exists(self, course_idnumber):
        return course_idnumber in self.courses

    def new_cohort(self, item):
        super().new_cohort(item)
        cohort_idnumber = item.param
        cohort_name = cohort_idnumber
        self.moodle.add_cohort(cohort_idnumber, cohort_name)

    def old_cohort(self, item):
        super().old_cohort(item)
        # Remove it?

    def new_student(self, item):
        """
        """
        if self.moodle.wrap_no_result(self.moodle.get_user_from_idnumber, item.right.idnumber):
            self.logger.warning("Putting existing student {} into the studentsALL group?".format(item.right))
            self.moodlemod.add_user_to_cohort(item.right.idnumber, 'studentsALL')
        else:
            super().new_student(item)
            student = item.right
            self.moodlemod.new_student(student)

    def check_for_allow_deletions(self):
        """
        If there settings.ini file contains specific instructions to delete the accounts, then do so
        Otherwise assume False
        """
        return config_get_section_attribute('MOODLE', 'deletion_mode') == 'hard_delete'

    def check_for_keep_username_startswith(self, user):
        with_what = config_get_section_attribute('MOODLE', 'keep_username_startswith')
        if not with_what:
            return False
        with_what = with_what.split(',')
        for this in with_what:
            if user.username.startswith(this):
                return True
        return False

    def remove_user_from_all_groups(self, user):
        """
        Used in old_* accounts functions
        """
        debug = config_get_section_attribute('DEBUGGING', 'inspect_soft_deletion_groups')
        for group in user.groups:
            self.logger.warning("Removing old_student {} from group {} ".format(user, group))
            self.moodlemod.remove_user_from_group(user.idnumber, group.idnumber)

    def old_student(self, item):
        super().old_student(item)
        student = item.left

        if self.check_for_keep_username_startswith(student):
            self.default_logger('I {} am a sacred account, leave me alone!'.format(student))
            return

        if self.check_for_allow_deletions():
            # This is the hard delete mode here
            # This deletes the account, probably only need this once in a while
            # Main difference from soft delete is that it unenrols them from all courses, which can delete information
            self.moodlemod.delete_account(student.idnumber)

        else:
            # The following lot item is useful if you want to provide an admin with CSV file of students that
            # are going to be deleted, in transition from soft to hard delete
            #self.logger.warn(student.to_csv)

            # Now set the homeroom field to 'left' and remove them from any groups they are in
            # Doesn't delete the account, and doesn't unenrol them from courses, either
            # Which makes recovering them a simple matter.
            try:
                self.moodle.update_table('user', where={
                    'idnumber':student.idnumber
                    },
                    department='left')
            except (NoResultFound, MultipleResultsFound):
                self.logger.warn("Did not update homeroom field for student {}".format(student))

            try:
                self.moodle.update_table('user', where={
                    'idnumber':student.idnumber
                    },
                    deleted=1)
            except (NoResultFound, MultipleResultsFound):
                self.logger.warn("Could not set deleted of student {} to 1".format(student))

            # This might not be necessary now that we have deleted turn on,
            # So turn it off.
            #self.remove_user_from_all_groups(student)

    def old_teacher(self, item):
        super().old_teacher(item)
        teacher = item.left

        if self.check_for_keep_username_startswith(teacher):
            self.default_logger('I {} am a sacred account, leave me alone!'.format(teacher))
            return

        if self.check_for_allow_deletions():
            self.moodlemod.delete_account(teacher.idnumber)
        else:
            self.logger.warn('Deleting teacher: {}'.format(teacher))
            try:
                self.moodle.update_table('user', where={
                    'idnumber':teacher.idnumber
                    },
                    department='delete')
            except (NoResultFound, MultipleResultsFound):
                self.logger.warn("Did not update homeroom field for teacher {}".format(teacher))
            try:
                self.moodle.update_table('user', where={
                    'idnumber':teacher.idnumber
                    },
                    deleted=1)
            except (NoResultFound, MultipleResultsFound):
                self.logger.warn("Could not set deleted of teacher {} to 1".format(teacher))


            self.remove_user_from_all_groups(teacher)

    def old_parent(self, item):
        super().old_parent(item)
        parent = item.left

        if self.check_for_keep_username_startswith(parent):
            self.default_logger('I {} am a sacred account, leave me alone!'.format(parent))
            return

        if self.check_for_allow_deletions():
            self.moodlemod.delete_account(parent.idnumber)
        else:
            self.logger.warn('Deleting parent: {}'.format(parent))
            try:
                self.moodle.update_table('user', where={
                    'idnumber':parent.idnumber
                    },
                    department='delete')
            except (NoResultFound, MultipleResultsFound):
                self.logger.warn("Did not update homeroom field for parent {}".format(parent))
    
            self.remove_user_from_all_groups(parent)

    def new_teacher(self, item):
        """
        """
        if self.moodle.wrap_no_result(self.moodle.get_user_from_username, item.right.username):
            self.logger.warning("Staff member with username {} already exists, setting PS ID to {}.".format(item.right.username, item.right.idnumber))
            self.moodle.set_user_idnumber_from_username(item.right.username, item.right.idnumber)
        else:
            pass
            # super().new_teacher(item)
            # teacher = item.right
            # self.moodlemod.new_teacher(teacher)

    def new_parent(self, item):
        """
        """
        if self.moodle.wrap_no_result(self.moodle.get_user_from_idnumber, item.right.idnumber):
            self.logger.warning("Putting parent student {} into the parentsALL group".format(item.right))
            self.moodlemod.add_user_to_cohort(item.right.idnumber, 'parentsALL')
        if self.moodle.wrap_no_result(self.moodle.get_user_from_username, item.right.username):
            self.logger.warning("This parent with guardian email {0} is not linked. Search PS for 'GuardianEmail contains {0}' and email results to Admissions".format(item.right.email))
        else:
            super().new_parent(item)
            parent = item.right
            self.moodlemod.new_parent(parent)
            # Add to the appropriate cohort now to ensure it's working
            self.moodlemod.add_user_to_cohort(parent.idnumber, 'parentsALL')

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

    # def new_course(self, item):
    #     super().new_course(item)
    #     course = item.right
    #     self.moodlemod.create_new_course(course.idnumber, course.name)

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
            self.moodlemod.enrol_student_into_course(student, course, group) # just pass the whole schedule object itself
        else:
            self.logger.debug("Did NOT enrol {} into course {}, because it does not exist in Moodle".format(item.right, course))

    def enrol_teacher_into_course(self, item):
        teacher = item.right.idnumber
        course = item.param.course
        group = item.param.group
        if self.enrol_in_course(item):   # for output and checking
            self.moodlemod.enrol_teacher_into_course(teacher, course, group) # just pass the whole schedule object itself
        else:
            self.logger.debug("Did NOT enrol {} into course {}, because it does not exist in Moodle".format(item.right, course))

    def enrol_parent_into_course(self, item):
        parent = item.right.idnumber
        course = item.param.course
        group = item.param.group
        if self.enrol_in_course(item):   # for output and checking
            self.moodlemod.enrol_parent_into_course(parent, course, group) # just pass the whole schedule object itself
        else:
            self.logger.debug("Did NOT enrol {} into course {}, because it does not exist in Moodle".format(item.right, course))

    def deenrol_teacher_from_course(self, item):
        super().deenrol_from_course(item)   # for output
        #user = item.right.idnumber
        #course = item.param.course
        #group = item.param.group
        #self.moodlemod.deenrol_teacher_from_course(user, course)

    def deenrol_student_from_course(self, item):
        super().deenrol_from_course(item)   # for output
        #user = item.right.idnumber
        #course = item.param.course
        #group = item.param.group
        #self.moodlemod.deenrol_student_from_course(user, course)

    def deenrol_parent_from_course(self, item):
        super().deenrol_from_course(item)   # for output
        #user = item.right.idnumber
        #course = item.param.course
        #group = item.param.group
        #self.moodlemod.deenrol_parent_from_course(user, course)

    def add_to_cohort(self, item):
        super().add_to_cohort(item)
        user = item.right.idnumber
        cohort = item.param
        self.moodlemod.add_user_to_cohort(user, cohort)

    def remove_from_cohort(self, item):
        super().remove_from_cohort(item)
        #user = item.left.idnumber
        #cohort = item.param
        #self.moodlemod.remove_user_from_cohort(user, cohort)

    def new_group(self, item):
        if not item.right.course:
            self.default_logger("Did NOT add group {} because no course available".format(item.param))
            return
        course = item.right.course.ID
        group = item.param
        if group in self.groups:
            self.logger.debug("Did NOT add group {} because it's already there....".format(group, course))
        elif course in self.courses:
            super().new_group(item)
            self.moodlemod.add_group(group, course)
        else:
            self.logger.debug("Did NOT add group {} because course {} does not exist.".format(group, course))

    def new_custom_profile_field(self, item):
        """
        """
        right = item.right
        name = right.idnumber
        self.default_logger("Found a new custom profile field {}".format(name))
        self.moodle.make_new_custom_profile_field(name)

    def old_custom_profile_field(self, item):
        """
        This actually means that a particular user has lost a particular profile field
        (It does NOT mean that this profile field should be deleted...)
        or does it?
        """
        # not sure what to do yet

    def old_group(self, item):
        group = item.left
        course_idnumber = group.course_idnumber
        if course_idnumber not in self.courses:
            self.default_logger("Did NOT delete group {} because the correspoding course {} does not exist.".format(group, course_idnumber))
        else:
            super().old_group(item)
            self.moodlemod.delete_group(group.idnumber, course_idnumber)

    def add_to_group(self, item):
        user = item.right.idnumber
        group = item.param.group
        course = item.param.course
        if course in self.courses:
            super().add_to_group(item)
            # We don't actually need the course...

            self.moodlemod.add_user_to_group(user, group)
            #self.default_logger("Successfully put user {} into group {}".format(user, group))
        else:
            self.logger.debug("Did NOT put {} in group {} because course {} does not exist.".format(user, group, course))

    def remove_from_group(self, item):
        super().remove_from_group(item)
        #user = item.right.idnumber
        #group = item.param.group
        #course = item.param.course
        # We don't actually need the course...
        #self.moodlemod.remove_user_from_group(user, group)

    def username_changed(self, item):
        user = item.left
        idnumber = user.idnumber
        from_what = item.left.username
        to_what = item.right.username

        if hasattr(user, 'login_method') and user.login_method == 'nologin':
            # Just go ahead and change it automatically, no need to inform anyone or anything
            # because the account isn't active anyway
            # test for 'login_method' because teachers don't have that TODO: Add that to the model!
            try:
                self.moodle.update_table('user', where={
                    'idnumber':idnumber
                    },
                    username=to_what)
            except IntegrityError:
                self.logger.warning('Got integrity error trying to change user {}\'s username to {}'.format(idnumber, to_what))
            super().username_changed(item)
        else:
            justgrade = functools.partial(re.sub, '[a-z_]', '')
            if justgrade(item.left.username) != justgrade(item.right.username):
                self.logger.warning("Grade change: Username {} has changed grade, needs username changed to {}".format(from_what, to_what))
            else:
                msg = "Username {} needs his/her username changed manually to {} this happens when passport info gets changed".format(from_what, to_what)
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
        for i in range(len(item.param)):
            grade = item.param[i]
            field = 'grade{}'.format(i+1)

            exists = self.moodle.get_rows_in_table('course_ssis_metadata',
                courseid = item.left.database_id,
                field=field)

            if not exists:
                self.moodle.insert_table('course_ssis_metadata',
                    courseid = item.left.database_id,
                    field=field,
                    value=grade)
            else:
                # we just need to update the existing one
                self.moodle.update_table('course_ssis_metadata',
                    where = dict(
                        courseid=item.left.database_id,
                        field=field,
                        ),
                    value=grade
                )

    def new_parent_link(self, item):
        """
        Go through all the children and make the association
        """
        super().new_parent_link(item)
        for child_idnumber in item.right.children:
            self.moodlemod.associate_child_to_parent(item.right.parent_idnumber, child_idnumber)

    def associate_child_to_parent(self, item):
        """
        Go through all the children and make the association
        """
        super().new_parent_link(item)
        for child_idnumber in item.right.children:
            self.moodlemod.associate_child_to_parent(item.right.parent_idnumber, child_idnumber)

    def deassociate_child_from_parent(self, item):
        super().deassociate_child_from_parent(item)

    def new_mrbs_editor(self, item):
        super().new_mrbs_editor(item)
        self.moodle.add_mrbs_editor(item.param)

    def new_timetable(self, item):
        pass  # meaningless

    def old_timetable(self, item):
        pass # meaningless

    def new_timetable_data(self, item):
        super().new_timetable_data(item)
        self.moodle.add_timetable_data(item.right)

    def old_timetable_data(self, item):
        super().old_timetable_data(item)
        self.moodle.set_timetable_data_inactive(item.left)

    def new_course_metadata(self, item):
        super().new_course_metadata(item)
        self.moodle.add_course_metadata(item.right)

    def new_online_portfolio(self, item):
        super().new_online_portfolio(item)
        self.moodlemod.create_online_portfolio(item.param)
