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
    """
    def __init__(self, left, right, **kwargs):
        self.left = left
        self.right = right
        self.define(**kwargs)
                
    def define(self, **kwargs):
        if kwargs:
            for item in self.subtract():
                dispatch = kwargs.get(item.status)
                if dispatch:
                    if hasattr(item, 'param') and item.param:
                        if not isinstance(item.param, list):
                            item.param = [item.param]
                        dispatch(*item.param)

    def subtract(self):
        return self.left - self.right

class DefineAttrDispatcher(DefineDispatcher):
    def __init__(self, attr, *args, **kwargs):
        self.attr = attr

    def subtract(self):
        

class MainDispatcher:
    def __init__(self):
        moodle = Moodle()
        autosend = AutoSend()
        postfix = PostFix()
        mod = ModUserEnrollments()
        self.logger = logging.getLogger('Differences')

        sync_moodle = config_get_section_attribute('MOODLE', 'sync')
        check_email = config_get_section_attribute('EMAIL', 'check_accounts')

        if check_email:
            # Generate new email accounts
            DefineDispatcher(autosend, postfix,
                             'new_student'=mod.no_email,
                             'old_student'=self.email_no_longer_needed)
            
        if sync_moodle:
            # Generate unneeded moodle accounts
            DefineDispatcher(moodle, autosend,
                             'new_student'=mod.new_student,
                             'old_student'=self.moodle_no_longer_needed,
                             'new_teacher'=mod.new_teacher,
                             'old_teacher'=None)
            
    def moodle_no_longer_needed(self, student):
        self.logger.warning("Delete this moodle account {} ({})".format(student.ID, student.username))

    def email_no_longer_needed(self, student):
        self.logger.warning("Delete this email account {}".format(student.username))


if __name__ == "__main__":

    main = MainDispatcher()
