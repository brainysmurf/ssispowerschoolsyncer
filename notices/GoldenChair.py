#!/usr/local/bin/python3
    
if __name__ == "__main__":
    import sys
    import os
    path = os.path.realpath(__file__)
    src_path = None
    while not path == '/':
        path = os.path.split(path)[0]
        print(path)
        if not '__init__.py' in os.listdir(path):
            src_path = path
            break
    if src_path == None:
        raise ImportError("Could not set up!")
    else:
        sys.path.insert(0, src_path)
from utils import *

from DatabaseBase import ExtendMoodleDatabaseToAutoEmailer
from Model import DatabaseObject, DatabaseObjects
from utils.PythonMail import send_html_email
from utils.Dates import custom_strftime
from utils.DB import UpdateField
from notices.Samples import student_notices_samples, student_notices_tag_samples
import datetime
from utils.Formatter import Smartformatter
from Students import Students

verbose = False
catch_wrong = True

class Nothing(Exception): pass

k_record_id = 2

class Golden_Chair(ExtendMoodleDatabaseToAutoEmailer):
    """
    Converts a database on moodle into a useable system that emails users
    """
    def __init__(self):
        super().__init__('Golden Chair')

    def define(self):
        """
        Called by init
        """
        super().define()
        self.sender = 'DragonNet Admin <lcssisadmin@student.ssis-suzhou.net>'
        self.agents = ['rebeccalouiseclentwo@ssis-suzhou.net']
        self.agents = 'adammorris@ssis-suzhou.net'
        self.agent_map = {}

        self.search_date = "same day"

        #self.content_field = 'Full Content'
        #self.attachment_field = 'Attached Content'
        #self.section_field = 'School Section'

        #self.priority_ids = [32]

    def derive_content(self, item):
        sf = Smartformatter()
        sf.take_dict(item)
        return self.list(sf('{user_first_name} {user_last_name} nominated {student_name} for <strong>{reason_for_golden_chair}</strong>'))
        
    def process(self):
        """
        Overrides inherited method
        """
        items = self.raw_data()
        self.database_objects = DatabaseObjects(self.user, self.password, self.server, self.database)
        self.verbose and print(self.database_objects)
        for item in items.time_created_happened_between(self.date - datetime.timedelta(days=5), self.date):
            self.database_objects.add(item)
            self.verbose and print(item)
        self.verbose and print(self.database_objects)

    def samples(self):
        return student_notices_samples

    def section_samples(self):
        return student_notices_tag_samples

    def email_to_agents(self):
        if self.agents:
            verbose and print("Sending notices to {}".format(self.agents))
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
        notices = Golden_Chair()
        notices.email_to_agents()
    except Nothing:
        print("No matching entries found")
