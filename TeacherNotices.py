from utils.Database import ExtendMoodleDatabaseToAutoEmailer
from utils.PythonMail import send_html_email
import re

catch_wrong = True

class Nothing(Exception): pass

k_record_id = 2

# Following gives me 1st, 2nd, 3rd, 4th, etc
def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

class Teacher_Notices(ExtendMoodleDatabaseToAutoEmailer):
    """
    Converts a database on moodle into a useable system that emails users
    """

    verbose = False

    def define(self):
        """
        Called by init
        """
        self.fields = ['date', 'content', 'attachment', 'timesrepeat', 'section']
        self.tags = ['##teachnotices_ws##', '##teachnotices_elem##', '##teachnotices_sec##']
        self.tag_map = {'##teachnotices_ws##':'Whole School',
                       '##teachnotices_elem##': 'Elementary Teacher Notice',
                       '##teachnotices_sec##': 'Secondary'}
        
        self.sender = 'DragonNet Admin <lcssisadmin@student.ssis-suzhou.net>'
        self.agents = ['adammorris@ssis-suzhou.net']
        self.agent_map = {
            'marktreichel@ssis-suzhou.net':['##teachnotices_ws##', '##teachnotices_elem##'],
            'richardbruford@ssis-suzhou.net':['##teachnotices_ws##', '##teachnotices_sec##']
            }

        self.search_date = "same day"

        self.start_html_tag    = "<html>"
        self.end_html_tag      = "</html>"
        self.header_pre_tag    = "<p><b>"
        self.header_post_tag   = "</b></p>"
        self.begin_section_tag = "<ul>"
        self.end_section_tag   = "</ul>" # extra br for formatting
        self.colon             = ":"
        self.priority_ids      = [32]
        self.unique            = lambda x: x['content']
        self.repeating_events_db_path = '/home/lcssisadmin/database_email/teachernotices'

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

    def tag_not_found(self, tag):
        """ What to do? """
        pass



if __name__ == "__main__":
    try:
        notices = Teacher_Notices('ssismdl_data_content')
        notices.email_to_agents()
    except Nothing:
        print("No matching entries found")
