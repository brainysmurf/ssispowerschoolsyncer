from utils.Database import ExtendMoodleDatabaseToAutoEmailer
from utils.PythonMail import send_html_email
from utils.Dates import custom_strftime

verbose = False
catch_wrong = True

class Nothing(Exception): pass

k_record_id = 2

class Student_Notices(ExtendMoodleDatabaseToAutoEmailer):
    """
    Converts a database on moodle into a useable system that emails users
    """

    def define(self):
        """
        Called by init
        """
        self.fields = ['date', 'attachment', 'content', 'timesrepeat', 'section']
        self.unique = lambda x: x['content']

        self.tags = ['##secstunot_all##', '##secstunot_hs##', '##secstunot_ms##']
        self.tag_map = {'##secstunot_all##':'All Secondary',
                       '##secstunot_hs##': 'High School',
                       '##secstunot_ms##': 'Middle School'}

        self.sender = 'Peter Fowles <peterfowles@ssis-suzhou.net>'
        self.agents = ['group-sec-all@ssis-suzhou.net',
                       'judychen15@student.ssis-suzhou.net',
                       'ruthellenlittle13@student.ssis-suzhou.net',
                       'soyeonpark13@student.ssis-suzhou.net',
                       'jihyungsuh13@student.ssis-suzhou.net']

        self.agent_map = {}

        self.search_date = "next day"

        self.start_html_tag    = "<html>"
        self.end_html_tag      = "</html>"
        self.header_pre_tag    = "<p><b>"
        self.header_post_tag   = "</b></p>"
        self.begin_section_tag = "<ul>"
        self.end_section_tag   = "</ul><br />" # extra br for formatting
        self.priority_ids      = [32]

        self.repeating_events_db_path = '/home/lcssisadmin/database_email/studentnotices'

    def format_for_email(self):
        verbose and print("Inside formatting!")
        if not self.final: raise Nothing
        verbose and print(self.final)
        self.colon = ':'

        # Body of the notices
        self.subject("Student Notices for {custom_date}")
        self.html_output = ""

        self.html("{start_html_tag}")
        self.html("{first_p_block}", format=False)
        for tag in self.tags:
            self.header = self.tag_map.get(tag, "NO HEADER")
            items = self.final.get(tag, [])
            if not items:
                self.tag_not_found(tag)
            else:
                self.html("{header_pre_tag}{header}{colon}{header_post_tag}")
                self.html("{begin_section_tag}")
                
            for item in items:
                self.html(self.derive_content(item))   # puts in the content

            if items:
                self.html("{end_section_tag}")

        # Attachments of the notices
        header = False
        for key in self.final.keys():
            for item in self.final[key]:
                if item['attachment']:
                    if not header:
                        self.header = "Attachments"
                        self.html("{header_pre_tag}{header}{colon}{header_post_tag}")
                        header = True
                    self.html(item['attachment'])

        self.html("{end_html_tag}")

    def email_to_agents(self):
        if self.agents:
            verbose and print("Sending notices to {}".format(self.agents))
            message_to_staff = """<p><i>These are tomorrow's announcements, as of 7:00 today.</i></p>"""
            self.format_for_email()
            send_html_email(self.sender, self.agents, self.get_subject(), self.get_html(first_p_block=message_to_staff))
        if self.agent_map:
            raise NotImplemented

    def post_to_wordpress(self):
        replace_apostrophes = "'\\''"
        d = {
            'title': self.get_subject(just_date=True),   # remove the 'Student Notices for' part
            'author': 35,  # peter fowles
            'content': self.get_html().replace("'", replace_apostrophes).replace('\n', ''),   # escape apostrophes for bash
            'date': self.date.strftime('%y-%m-%d 7:00:00'),
            'blog': "sites.ssis-suzhou.net/secondarystudentannouncements"
            }
        command = """/usr/bin/wp post create --path=/var/www/wordpress --post_type=post --post_title='{title}' --post_content='{content}' --post_author={author} --post_status=future --post_date='{date}' --blog={blog}""".format(**d)
        import subprocess
        subprocess.call(command, shell=True)

    def get_user_name(self, userid):
        """
        Uses 'institution' field, if available, otherwise uses the default name defined in user's profile
        """
        name_info = 'institution, firstname, lastname'
        name = self.sql('select {} from ssismdl_user where id = {}'.format(name_info, userid))()[0]
        user_defined, firstname, lastname = name
        if not user_defined:
            name = firstname + ' ' + lastname
        else:
            name = user_defined
        name = "({})".format(name)
        self.verbose and print("Name: {}".format(name))
        return name

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
        notices = Student_Notices('ssismdl_data_content')
        notices.email_to_agents()
        notices.post_to_wordpress()
    except Nothing:
        print("No matching entries found")
