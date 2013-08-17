#!/usr/local/bin/python3
    
from DatabaseBase import ExtendMoodleDatabaseToAutoEmailer
from Model import DatabaseObject
from psmdlsyncer.utils.PythonMail import send_html_email
from psmdlsyncer.utils.Dates import custom_strftime
from psmdlsyncer.utils.RelativeDateFieldUpdater import RelativeDateFieldUpdater
from Samples import student_notices_samples, student_notices_tag_samples
import datetime

class Nothing(Exception): pass

k_record_id = 2

class SNRDFU(RelativeDateFieldUpdater):
    pass

class Student_Notices(ExtendMoodleDatabaseToAutoEmailer):
    """
    Converts a database on moodle into a useable system that emails users
    """
    def __init__(self):
        self.verbose = False
        super().__init__('Secondary Notices Database')
        #self.start_html_tag = '<html><p><i>Translations available: <a href="http://sites.ssis-suzhou.net/ssakorean/">Korean</a></i></p>'

    def define(self):
        """
        Called by init
        """
        super().define()
        self.sender = 'Peter Fowles <peterfowles@ssis-suzhou.net>'
        self.agents = ['group-sec-all@ssis-suzhou.net',
                       'judychen15@student.ssis-suzhou.net',
                       'ruthellenlittle13@student.ssis-suzhou.net',
                       'soyeonpark13@student.ssis-suzhou.net',
                       'jihyungsuh13@student.ssis-suzhou.net',
                       'danbiku14@student.ssis-suzhou.net',
                       'myungjinlee14@student.ssis-suzhou.net']
        self.agents = 'adammorris@ssis-suzhou.net'
        self.agent_map = {}

        self.search_date = "next day"

        self.content_field = 'Full Content'
        self.attachment_field = 'Attached Content'
        self.section_field = 'School Section'

        self.priority_ids = [32]

    def samples(self):
        return student_notices_samples

    def section_samples(self):
        return student_notices_tag_samples

    def email_to_agents(self):
        if self.agents:
            self.verbose and print("Sending notices to {}".format(self.agents))
            message_to_staff = """<p><i>These are tomorrow's announcements, as of 7:00 pm today.</i></p>"""
            self.format_for_email()
            if self.no_emails:
                print("NOT sending email... but this is what would have been sent:")
                self.print_email(self.agents)
            else:
                send_html_email(self.sender, self.agents, self.get_subject(), self.get_html(first_p_block=message_to_staff),
                                domain='student.ssis-suzhou.net')
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
    try:
        notices = Student_Notices()
        notices.email_to_agents()
        notices.post_to_wordpress('secondarystudentannouncements', datetime.time(hour=7,minute=0,second=0))
    except Nothing:
        print("No matching entries found")
