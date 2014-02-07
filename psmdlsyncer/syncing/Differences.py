from psmdlsyncer.models.datastores import MoodleTree
from psmdlsyncer.models.datastores import AutoSendTree
from psmdlsyncer.models.datastores import PostfixTree
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.settings import logging
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

class DefineDispatcher:
    """
    BOILERPLATE STUFF FOR MAKING THE WHEEL TURN
    LEFT IS "HAVE"
    RIGHT IS "NEED"
    """
    def __init__(self, left, right, template=None, **kwargs):
        self.left = left
        self.right = right
        self.logger = logging.getLogger("Dispatcher")
        if template:
            self.template = template
            self.define_dispatcher = lambda item : getattr(self.template, item.status)
        if kwargs:
            self.define_dispatcher = lambda item : self.kwargs.get(item.status)
            self.defined(**kwargs)
        self.go()

    def go(self, **kwargs):
        for item in self.subtract():
            dispatch = self.define_dispatcher(item) if hasattr(item, 'status') else None
            if dispatch:
                if hasattr(item, 'param') and item.param:
                    if not isinstance(item.param, list):
                        item.param = [item.param]
                    self.logger.debug('Dispatching to {} with param {}'.format(dispatch.__name__, str(item.param)))
                    dispatch(*item.param)
            else:
                #TODO: Handle unrecognized statuses here
                print('unrecognized status')
                pass

    def subtract(self):
        # Invokes the __sub__ method
        return self.left - self.right

class MainDispatcher:
    def __init__(self):
        self.logger = logging.getLogger('Differences')
        self.logger.info('Initiating Autosend')
        autosend = AutoSend()
        self.logger.info('Initiating Moodle')
        moodle = Moodle()
        moodle.tree.output_students()
        #self.logger.debug('Initiating Postfix')
        #postfix = PostFix()

        moodle_autosend = MoodleAutosend()

        sync_moodle = config_get_section_attribute('MOODLE', 'sync')
        check_email = config_get_section_attribute('EMAIL', 'check_accounts')

        if check_email:
            self.logger.info('Defining dispatcher for postfix and autosend')
            DefineDispatcher(postfix, autosend,
                new_student=log_item('no_email'),
                old_student=log_item('email_no_longer_needed')
                )
                #new_student=mod.no_email,
                #old_student=self.email_no_longer_needed)

        if sync_moodle:
            self.logger.info('Defining dispatcher for moodle and autosend')
            DefineDispatcher(moodle, autosend, template=moodle_autosend)

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

    from IPython import embed
    embed()

    assert(first == third)
    assert(first != second)
    assert(first != fourth)



    MainDispatcher()    
