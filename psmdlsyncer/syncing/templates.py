import logging

class DefaultTemplate:
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
        self.default_logger("Add {0.left} to group {0.param}".format(item))

    def remove_from_group(self, item):
        self.default_logger("Remove {0.right} from group {0.param}".format(item))

    def enrol_in_course(self, item):
        self.default_logger("Enrol {0.left} into course {0.param}".format(item))

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

