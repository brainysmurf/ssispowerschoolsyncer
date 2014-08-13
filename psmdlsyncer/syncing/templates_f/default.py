import logging

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
        self.default_logger = self.logger.info

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
        self.default_logger("New timetable data {0.param} ".format(item))

    def old_timetable_data(self, item):
        self.default_logger("Old timetable data {0.param} ".format(item))

    def new_online_portfolio(self, item):
        self.default_logger("Creating new online portfolio for student {0.param}".format(item))

    def new_course_metadata(self, item):
        self.default_logger("New course metadata {0.right} ".format(item))



