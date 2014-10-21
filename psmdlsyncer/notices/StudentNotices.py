from psmdlsyncer.settings import define_command_line_arguments
from psmdlsyncer.html_email.Email import Email
from psmdlsyncer.utils.Dates import custom_strftime, today
from psmdlsyncer.notices.DatabaseBase import ExtendMoodleDatabaseToAutoEmailer
from psmdlsyncer.notices.Model import DatabaseObject
import datetime

class Nothing(Exception): pass

k_record_id = 2

class Student_Notices(ExtendMoodleDatabaseToAutoEmailer):
    """
    Converts a database on moodle into a useable system that emails users
    """
    def __init__(self, *args, **kwargs):
        self.verbose = False
        self.end_of_item = ""
        super().__init__('Secondary Notices Database', *args, **kwargs)
        self.init()
        #self.start_html_tag = '<html><p><i>Translations available: <a href="http://sites.ssis-suzhou.net/ssakorean/">Korean</a></i></p>'

    def define(self):
        """
        Called by init
        """
        super().define()
        self.sender = 'DragonNet Admin <lcssisadmin@student.ssis-suzhou.net>'
        self.agents = ['Lucy Burden <lucyburden@ssis-suzhou.net>']
        self.agent_map = {}

        self.search_date = "next day"

        self.content_field = 'Full Content'
        self.attachment_field = 'Attached Content'
        self.section_field = 'School Section'

        self.priority_usernames = ['lucyburden']
        self.setup_priorities()

    def email_to_agents(self):
        if self.agents:
            self.verbose and print("Sending notices to {}".format(self.agents))
            message_to_staff = """<p>Edit these notices by <a href="http://dragonnet.ssis-suzhou.net/mod/data/view.php?d=5">going here</a>.</p>"""
            self.format_for_email()
            self.email(self.agents)

        if self.agent_map:
            raise NotImplemented

    def get_subject(self, just_date=False):
        if just_date:
            return self.subject_output[20:]
        else:
            return self.subject_output

    def get_html(self, first_p_block=""):
        d = {
            'first_p_block':first_p_block
            }
        return self.html_output.format(**d)

    def tag_not_found(self, tag):
        """ What to do? """
        pass


if __name__ == "__main__":
    notices = Student_Notices()
    # TURN ON THE ABILITY TO CLICK "EDIT" NEXT TO EACH ONE.
    # THIS REQUIRES THAN A dbid FIELD BE CREATED ON THE SERVER SIDE
    # TODO: STREAMLINE THIS BETTER
    if notices.settings.email:
        notices.email_editing = True
        notices.email_to_agents()
    if notices.settings.wordpress:
        notices.email_editing = False
        notices.post_to_wordpress('secondarystudentannouncements', datetime.time(hour=19,minute=5,second=0), date=today())
