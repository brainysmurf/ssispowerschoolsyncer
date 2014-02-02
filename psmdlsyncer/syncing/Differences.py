from psmdlsyncer.importing import InfoController, Moodle, AutoSend, PostFix
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.settings import logging

# Used in Dispatched:
from psmdlsyncer.sql.MoodleDatabase import MoodleDBConnection

def log_item(kind):
    def _log(*items):
        for item in items:
            print('{}: {}'.format(kind, item))
    return _log

class Dispatched:
    """
    Holds the methods that are called by the dispatcher
    Wrapper around modification methods
    Main task is to do prelim checks before actually making the mods
    """
    def __init__(self):
        self.moodle = MoodleDBConnection()
        self.moodle_mod = ModUserEnrollments()

    def add_to_moodle(self, *items):
        """
        """
        #First double-checks to see if we actually do have something in Moodle
        #for example, an account with item.email_address

        for item in items:
            result = self.moodle.get_table('user', 'idnumber', email=item.email)            

            # potentially the same email address could be registered in moodle, for staff who are also parents
            # annoying
            if result:
                if len(result) > 1:
                    log_item('got more than one account with this email')(item)
                else:
                    idnumber_in_moodle = result[0][0]
                    if idnumber_in_moodle == "":
                        # we can be sure that this is an account that doesn't have an idnumber associated yet
                        # if the syncing code is working perfectly this shouldn't happen
                        # but sometimes people don't get powerschool numbers? or whatever
                        log_item('idnumber updated in moodle')(item)
                        self.moodle.update_table('user', 
                            where={'email': item.email_address},
                            idnumber=item.idnumber)
                    elif not idnumber_in_moodle == item.idnumber:
                        log_item('idnumber CHANGED?? {}'.format(idnumber_in_moodle))(item)
                    elif idnumber_in_moodle == item.idnumber:
                        log_item('Account already exists, maybe not in cohort {}?'.format(idnumber_in_moodle))(item)
                    else:
                        log_item('No idea how I got here')(item)
            else:
                # really not in moodle
                log_item('really needs to be added in moodle')(item)

    def enrol_in_course(self, *items):
        for item in items:
            log_item('enrol in course {}'.format(item._operation_target))(item)

    def deenrol_from_course(self, *items):
        for item in items:
            log_item('deenrol from course {}'.format(item._operation_target))(item)

    def add_to_cohort(self, *items):
        for item in items:
            log_item('add to cohort {}'.format(item._operation_target))(item)

    def remove_from_cohort(self, *items):
        for item in items:
            log_item('remove from cohort {}'.format(item._operation_target))(item)

    def homeroom_changed(self, *items):
        for item in items:
            log_item('homeroom_changed {}'.format(item._operation_target))(item)
            self.moodle.update_table('user',
                where={'idnumber': item.idnumber},
                department=item._operation_target)

class DefineDispatcher:
    """
    BOILERPLATE STUFF FOR MAKING THE WHEEL TURN
    LEFT IS "HAVE"
    RIGHT IS "NEED"
    """
    def __init__(self, left, right, **kwargs):
        self.left = left
        self.right = right
        self.define(**kwargs)
                
    def define(self, **kwargs):
        if kwargs:
            for item in self.subtract():
                dispatch = kwargs.get(item.status) if hasattr(item, 'status') else None
                if dispatch:
                    if hasattr(item, 'param') and item.param:
                        if not isinstance(item.param, list):
                            item.param = [item.param]
                        dispatch(*item.param)
                else:
                    #TODO: Handle unrecognized statuses here
                    print('unrecognized status')
                    input(item)
                    pass

    def subtract(self):
        # Invokes the __sub__ method
        return self.left - self.right

class MainDispatcher:
    def __init__(self):
        self.logger = logging.getLogger('Differences')
        self.logger.debug('Initiating Autosend')
        autosend = AutoSend()
        self.logger.debug('Initiating Moodle')
        moodle = Moodle()
        #moodle.tree.output_students()
        #self.logger.debug('Initiating Postfix')
        #postfix = PostFix()

        dispatch_target = Dispatched()

        sync_moodle = config_get_section_attribute('MOODLE', 'sync')
        check_email = config_get_section_attribute('EMAIL', 'check_accounts')

        if check_email:
            DefineDispatcher(postfix, autosend,
                new_student=log_item('no_email'),
                old_student=log_item('email_no_longer_needed')
                )
                #new_student=mod.no_email,
                #old_student=self.email_no_longer_needed)

        if sync_moodle:
            DefineDispatcher(moodle, autosend,
                new_student=dispatch_target.add_to_moodle,
                old_student=log_item('moodle_no_longer_needed'),
                new_teacher=dispatch_target.add_to_moodle,
                old_teacher=log_item('teacher_no_longer_needed'),

                enrol_in_course=dispatch_target.enrol_in_course,
                deenrol_from_course=dispatch_target.deenrol_from_course,
                add_to_cohort=dispatch_target.add_to_cohort,
                remove_from_cohort=dispatch_target.remove_from_cohort,

                homeroom_changed=dispatch_target.homeroom_changed,
                )
                #new_student=mod.new_student,
                #old_student=self.moodle_no_longer_needed,
                #new_teacher=mod.new_teacher,
                #old_teacher=None)

    def moodle_no_longer_needed(self, student):
        if student is None:
            self.logger.warning('How did I get a None student here in moodle_no_longer_needed?')
        self.logger.warning("Delete this moodle account {} ({})".format(student.ID, student.username))

    def email_no_longer_needed(self, student):
        self.logger.warning("Delete this email account {}".format(student.username))


if __name__ == "__main__":

    main = MainDispatcher()
