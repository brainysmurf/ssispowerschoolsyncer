from psmdlsyncer.models.datastores.tree import MoodleTree, AutoSendTree, PostfixTree
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.settings import logging
from psmdlsyncer.utils.modifications import ModificationStatement
from psmdlsyncer.utils import NS2
log = logging.getLogger(__name__)

# Used in Dispatched:
from psmdlsyncer.sql.MoodleDatabase import MoodleDBConnection

class expose:
    def __init__(self, debug=False):
        self.debug = debug
    def __call__(self, what):
        if not self.debug:
            return what
        else:
            return lambda *args, **kwargs: log.warning('{} called, but debugging on.'.format(what))

class MoodleAutosend:
    """
    Holds the methods that are called by the dispatcher
    Wrapper around modification methods
    Main task is to do prelim checks before actually making the mods
    """
    def __init__(self):
        self.moodle = MoodleDBConnection()
        self.moodle_mod = ModUserEnrollments()
        self.logging = logging.getLogger(self.__class__.__name__)
        self.log = self.logging.warn

    @expose()
    def add_to_moodle(self, *items):
        """
        """
        #First double-checks to see if we actually do have something in Moodle
        #for example, an account with item.email_address

        for item in items:
            self.log('+moodle  {}'.format(item))
            result = self.moodle.get_table('user', 'idnumber', email=item.email)

            # potentially the same email address could be registered in moodle, for staff who are also parents
            # annoying
            if result:
                if len(result) > 1:
                    self.log('got more than one account with this email: {}'.format(item.email))
                else:
                    idnumber_in_moodle = result[0][0]
                    if idnumber_in_moodle == "":
                        # we can be sure that this is an account that doesn't have an idnumber associated yet
                        # if the syncing code is working perfectly this shouldn't happen
                        # but sometimes people don't get powerschool numbers? or whatever
                        self.log('!moodle idnumber updated in moodle: {}'.format(item))
                        self.moodle.update_table('user',
                            where={'email': item.email_address},
                            idnumber=item.idnumber)
                    elif not idnumber_in_moodle == item.idnumber:
                        self.log('!moodle idnumber changed {}'.format(item))
                    elif idnumber_in_moodle == item.idnumber:
                        self.log('!moodle Account already exists, maybe not in cohort {}?'.format(item))
                    else:
                        self.log('?moodle No idea how I got here {}'.format(item))
            else:
                # really not in moodle
                which_handler = 'new_' + item.kind
                handler = getattr(self.moodle_mod, which_handler)
                # handler is either new student, new teacher, or ?
                # TODO: add 'new staff' eventually
                print(handler)
                handler(item)

    @expose(debug=True)
    def new_student(self, *items):
        self.add_to_moodle(*items)

    @expose(debug=True)
    def old_student(self, *items):
        self.remove_from_moodle(*items)

    @expose(debug=True)
    def new_teacher(self, *items):
        self.add_to_moodle(*items)

    @expose(debug=True)
    def old_teacher(self, *items):
        self.remove_from_moodle(*items)

    @expose(debug=True)
    def remove_from_moodle(self, *items):
        for item in items:
            self.log('-moodle   <not completed> {}'.format(item))

    @expose(debug=True)
    def enrol_student_into_course(self, *items):
        for item in items:
            self.log('+course    {} {}'.format(item._operation_target, item))
            self.moodle_mod.enrol_student_into_course(item) # just pass the whole schedule object itself

    @expose(debug=True)
    def deenrol_from_course(self, *items):
        for item in items:
            self.log('-course    <not implemented> {} {}'.format(item._operation_target, item))

    @expose(debug=True)
    def add_to_cohort(self, *items):
        for item in items:
            self.log('+cohort    {} {}'.format(item._operation_target, item))
            self.moodle_mod.add_user_to_cohort(item.idnumber, item._operation_target)

    @expose(debug=True)
    def remove_from_cohort(self, *items):
        for item in items:
            self.log('-cohort    {} {}'.format(item._operation_target, item))
            self.moodle_mod.remove_user_from_cohort(item.idnumber, item._operation_target)

    @expose(debug=True)
    def add_to_group(self, *items):
        for item in items:
            self.log('+group     {} {}'.format(item._operation_target, item))
            self.moodle_mod.remove_user_from_group(item.idnumber, item._operation_target)

    @expose(debug=True)
    def remove_from_group(self, *items):
        for item in items:
            self.log('-group     {} {}'.format(item._operation_target, item))
            self.moodle_mod.remove_user_from_group(item.idnumber, item._operation_target)

    @expose(debug=True)
    def add_to_schedule(self, *items):
        """ defunct """
        for item in items:
            self.log('+schedule  {}'.format(item))

    @expose(debug=True)
    def remove_from_schedule(self, *items):
        """ defunct """
        for item in items:
            self.log('-schedule {} {}'.format(item._operation_target, item))

    @expose(debug=True)
    def homeroom_changed(self, *items):
        for item in items:
            self.log('!homeroom {} {}'.format(item._operation_target, item))
            self.moodle.update_table('user',
                where={'idnumber': item.idnumber},
                department=item._operation_target)

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


class FindDifferences:
    """
    BOILERPLATE STUFF FOR MAKING THE WHEEL TURN
    LEFT IS "HAVE"
    RIGHT IS "NEED"
    """
    def __init__(self, left, right, template=None, **kwargs):
        self.left = left
        self.right = right
        self.template = template
        if not template:
            self.template = DefaultTemplate()
        self.logger = logging.getLogger("DefineDispatcher")
        self.default_logger = self.logger.info   # change this to info for verbosity
        self.default_logger("Inside DefineDispatcher")
        self.default_logger("Left: {}".format(self.left))
        self.default_logger("Right: {}".format(self.right))
        if template:
            self.template = template
            self.define_dispatcher = lambda item : getattr(self.template, item.status)
        if kwargs:
            self.define_dispatcher = lambda item : self.kwargs.get(item.status)
            self.defined(**kwargs)
        self.go()

    def go(self, **kwargs):
        for item in self.subtract():
            self.default_logger(item)
            dispatch = self.template.get(item.status) if self.template and hasattr(item, 'status') else None
            if dispatch:
                self.default_logger('Dispatching {} to {}'.format(str(item.param), dispatch.__name__))
                dispatch(item)
            else:
                #TODO: Handle unrecognized statuses here
                self.logger.warning("This item wasn't handled, because a handler ({}) wasn't defined!".format(item.status))
                pass

    def get_subbranch(self, tree, subbranch):
        """
        Returns the subbranch of tree
        TODO: Check and throw KeyError exception
        """
        return tree.__class__._store[tree.__class__.qual_name_format.format(
                branch=tree.__class__.__name__,
                delim=tree.__class__.qual_name_delimiter,
                subbranch=subbranch)]

    def subtract(self):
        subbranches = ['teachers', 'students', 'groups', 'schedules']
        for subbranch in subbranches:

            # First check for the differences between keys

            self.default_logger("Subbranch: {}".format(subbranch))
            left_branch = self.get_subbranch(self.left, subbranch)
            right_branch = self.get_subbranch(self.right, subbranch)
            self.default_logger("There are {} items in {}'s left branch".format(len(right_branch), subbranch))
            self.default_logger("There are {} items in {}'s right branch".format(len(right_branch), subbranch))

            self.default_logger("First difference:")
            self.default_logger(right_branch.keys() - left_branch.keys())
            # Loop through missing stuff and do with it what we must
            for key in right_branch.keys() - left_branch.keys():
                self.default_logger(key)
                yield ModificationStatement(
                    left = left_branch.get(key),
                    right = right_branch.get(key),
                    status = NS2.string("new_{term}", term=subbranch[:-1]),
                    param = [right_branch.get(key)]
                    )

            self.default_logger("Second difference:")
            self.default_logger(left_branch.keys() - right_branch.keys())

            for key in left_branch.keys() - right_branch.keys():
                yield ModificationStatement(
                    left = left_branch.get(key),
                    right = right_branch.get(key),
                    status = NS2.string("old_{term}", term=subbranch[:-1]),
                    param = [left_branch.get(key)]
                    )

            # Now check for the difference in values of each variable

            for item_key in left_branch:
                self.default_logger('item_key: {}'.format(item_key))
                item_left = left_branch.get(item_key)
                item_right = right_branch.get(item_key)
                if item_left and item_right:
                    self.default_logger("Finding the differences between\n\t{}\n\t{}".format(item_left, item_right))
                    for left_minus_right in item_left - item_right:
                        self.default_logger(left_minus_right)
                        yield ModificationStatement(
                            left = left_minus_right.left,
                            right = left_minus_right.right,
                            status = left_minus_right.status,
                            param = left_minus_right.param
                            )

class FindPostDifferences(FindDifferences):
    """
    This goes through the students and teachers subbranches, and calls the post_differences routines
    """
    def subtract(self):
        subbranches = ['teachers', 'students']
        for subbranch in subbranches:
            self.default_logger("Subbranch: {}".format(subbranch))
            left_branch = self.get_subbranch(self.left, subbranch)
            right_branch = self.get_subbranch(self.right, subbranch)
            self.default_logger("There are {} items in {}'s left branch".format(len(right_branch), subbranch))
            self.default_logger("There are {} items in {}'s right branch".format(len(right_branch), subbranch))

            for item_key in left_branch:
                self.default_logger('item_key: {}'.format(item_key))
                item_left = left_branch.get(item_key)
                item_right = right_branch.get(item_key)
                if item_left and item_right:
                    self.default_logger("Finding the post-differences between\n\t{}\n\t{}".format(item_left, item_right))

                    # magical trick that substitutes out the regular differences method
                    # have to set it at class level because the model uses class methods
                    item_left.__class__.__sub__ = item_left.post_differences

                    for left_minus_right in item_left - item_right:
                        self.default_logger(left_minus_right)
                        yield ModificationStatement(
                            left = left_minus_right.left,
                            right = left_minus_right.right,
                            status = left_minus_right.status,
                            param = left_minus_right.param
                            )

                    item_left.__class__.__sub__ = item_left.differences

class MainDispatcher:
    def __init__(self):
        self.logger = logging.getLogger('Differences')
        self.logger.info('Initiating Moodle')
        MoodleTree()
        self.logger.info('Initiating Autosend')
        AutoSendTree()

        moodle_autosend = MoodleAutosend()

        sync_moodle = config_get_section_attribute('MOODLE', 'sync')
        check_email = config_get_section_attribute('EMAIL', 'check_accounts')
        check_email = check_email == "True"
        if check_email:
            pass  # write this later

        if sync_moodle:
            self.logger.info('Defining dispatcher for moodle and autosend')
            DefineDispatcher(MoodleTree, AutoSendTree,
                template=moodle_autosend)

    def moodle_no_longer_needed(self, student):
        if student is None:
            self.logger.warning('How did I get a None student here in moodle_no_longer_needed?')
        self.logger.warning("Delete this moodle account {} ({})".format(student.ID, student.username))

    def email_no_longer_needed(self, student):
        if student:
            self.logger.warning("Delete this email account {}".format(student.username))


if __name__ == "__main__":

    first = MoodleTree.students.make('33', '333', '8', '8L', 'Moris, Adam', '', '', '', 'American')
    second = MoodleTree.students.make('12', '5555', '8', '8L', 'Moris, Adam', '', '', '', 'American')
    third = MoodleTree.students.make('33', '333', '8', '8L', 'Moris, Adam', '', '', '', 'American')
    fourth = AutoSendTree.students.make('33', '333', '8', '8L', 'Moris, Adam', '', '', '', 'American')

    assert(first == third)
    assert(first != second)
    assert(first != fourth)



    MainDispatcher()
