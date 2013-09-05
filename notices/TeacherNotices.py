#!/usr/local/bin/python3

from DatabaseBase import ExtendMoodleDatabaseToAutoEmailer
import re
from Samples import teacher_notices_samples, teacher_notices_tag_samples
from psmdlsyncer.settings import settings

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
        self.start_html_tag = '<html><p><i>Teacher Notices are now published at 7:00 pm the day before. They are edited at 5:00 pm. <a href="http://sites.ssis-suzhou.net/secondarystudentannouncements/">Click here Secondary Student Notices</i></a></p>'

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
        self.agent_map = {}
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

    def samples(self):
        return teacher_notices_samples

    def section_samples(self):
        return teacher_notices_tag_samples


if __name__ == "__main__":
    try:
        notices = Teacher_Notices()
        notices.email_editing = True
        if settings.arguments.em_only:
            notices.email_editing = False
            notices.agent_map = {
                'group-sec-all@ssis-suzhou.net':['Whole School', 'Secondary']
            }
        notices.email_to_agents()
    except Nothing:
        print("No matching entries found")
