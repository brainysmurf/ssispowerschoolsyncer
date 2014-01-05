from psmdlsyncer.importing import InfoController, Moodle, AutoSend, PostFix
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.settings import logging

class Differences:
    """
    PROCESSES DIFFERENCES BETWEEN TWO OBJECTS AND RELAYS TO THE RIGHT PLACE
    """

class DefineDispatcher:
    """
    BOILERPLATE STUFF FOR MAKING THE WHEEL TURN
    LEFT IS "HAVE"
    RIGHT IS "NEED"
    """
    def __init__(self, left, right, **kwargs):
        self.left = left
        self.right = right
        self.logger = logging.getLogger("Dispatcher")
        self.define(**kwargs)
                
    def define(self, **kwargs):
        if kwargs:
            for item in self.subtract():
                dispatch = kwargs.get(item.status)
                if dispatch:
                    if hasattr(item, 'param') and item.param:
                        if not isinstance(item.param, list):
                            item.param = [item.param]
                        self.logger.info('Dispatching to {} with param {}'.format(dispatch.__name__, str(item.param)))
                        dispatch(*item.param)

    def subtract(self):
        return self.left - self.right

class MainDispatcher:
    def __init__(self):
        self.logger = logging.getLogger('Differences')
        self.logger.info('Initiating Autosend')
        autosend = AutoSend()
        self.logger.info('Initiating Moodle')
        moodle = Moodle()
        self.logger.info('Initiating Postfix')
        postfix = PostFix()
        self.logger.info('Initiating ModUserEnrollments')
        mod = ModUserEnrollments()

        sync_moodle = config_get_section_attribute('MOODLE', 'sync')
        check_email = config_get_section_attribute('EMAIL', 'check_accounts')

        if check_email:
            self.logger.info('Defining dispatcher for postfix and autosend')
            DefineDispatcher(postfix, autosend,
                             old_student=mod.no_email)

        if sync_moodle:
            self.logger.info('Defining dispatcher for moodle and autosend')
            DefineDispatcher(moodle, autosend,
                             new_student=mod.new_student,
                             old_student=self.moodle_no_longer_needed,
                             new_teacher=mod.new_teacher,
                             old_teacher=None)

    def moodle_no_longer_needed(self, student):
        self.logger.warning("Delete this moodle account {} ({})".format(student.ID, student.username))

    def email_no_longer_needed(self, student):
        if student:
            self.logger.warning("Delete this email account {}".format(student.username))


if __name__ == "__main__":

    main = MainDispatcher()
