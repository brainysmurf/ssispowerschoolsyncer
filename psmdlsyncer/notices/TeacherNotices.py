from psmdlsyncer.notices.DatabaseBase import ExtendMoodleDatabaseToAutoEmailer
import re
from psmdlsyncer.settings import define_command_line_arguments

class Nothing(Exception): pass

# Following gives me 1st, 2nd, 3rd, 4th, etc
def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

class Teacher_Notices(ExtendMoodleDatabaseToAutoEmailer):
    """
    Converts a database on moodle into a useable system that emails users
    """

    def __init__(self):
        super().__init__('Teacher Notices Database')
        self.settings = define_command_line_arguments('group_sec_all',
                                                      *self.shared_command_line_args_switches,
                                                      **self.shared_command_line_args_strings)
        self.init()

    def define(self):
        """
        Called by init
        """
        super().define()
        self.sender = 'DragonNet Admin <lcssisadmin@student.ssis-suzhou.net>'
        self.agents = ['adammorris@ssis-suzhou.net']
        self.agent_map = {
            'rebeccalouiseclentwo@ssis-suzhou.net':['Whole School', 'Elementary'],
            'nicholaslittle@ssis-suzhou.net':['Whole School', 'Secondary']
            }
        self.search_date = "next day"
        self.content_field = 'Full Content'
        self.attachment_field = 'Attached Content'
        self.section_field = 'School Section'
        self.priority_ids      = [32, 14, 48]

    def post_to_wordpress(self):
        """ Teacher notices doesn't have a wordpress site ...  yet? """
        pass

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

    def section_not_found(self, tag):
        """ What to do? """
        pass

if __name__ == "__main__":
    try:
        notices = Teacher_Notices()
        notices.email_editing = True
        if notices.settings.group_sec_all:  #TODO: CHANGE em_only TO SOMETHING MORE SENSIBLE
            notices.email_editing = False
            notices.agent_map = {
                'group-sec-all@ssis-suzhou.net':['Whole School', 'Secondary']
            }
        notices.email_to_agents()
    except Nothing:
        print("No matching entries found")
