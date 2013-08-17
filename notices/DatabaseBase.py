#!/usr/local/bin/python3
import postgresql
from psmdlsyncer.utils.Dates import today, tomorrow, yesterday
from psmdlsyncer.utils.PythonMail import send_html_email
from psmdlsyncer.html_email import Email
from psmdlsyncer.utils.DB import FieldObject
from Model import DatabaseObjects, DatabaseObject, StartDateField, EndDateField
import re
import datetime

class Nothing(Exception): pass

# Following gives me 1st, 2nd, 3rd, 4th, etc
def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


class ExtendMoodleDatabaseToAutoEmailer:
    """
    Converts a database on moodle into a useable system that emails users
    """

    def __init__(self, database_name, server='dragonnet.ssis-suzhou.net'):
        """
        Populate self.found with legitimate entries
        Works by looking for target date on the backend, and then finding all entries with matching dates...
           ... and then adding any entries with any that share the same recordid
        """
        super().__init__()
        # Setup
        self.database_name = database_name
        import argparse
        parser = argparse.ArgumentParser(description="Integrates Moodle Database with emailing system")
        parser.add_argument('-e', '--no_emails', action="store_true", help="Do NOT send emails")
        parser.add_argument('-w', '--no_wordpress', action="store_true", help="Do NOT post to wordpress")
        parser.add_argument('-x', '--use_samples', action="store_true", help="Use included samples")
        parser.add_argument('-v', '--verbose', action="store_true", help="Tell you what I'm doing")
        parser.add_argument('-d', '--passed_date', help="DD-MM-YYYY format")
        parser.add_argument('-s', '--smtp', action="store", help="Which smtp server to use")
        parser.add_argument('-u', '--user', action="store", help="username for database")
        parser.add_argument('-b', '--database', action="store", help="database name")
        parser.add_argument('-p', '--password', action="store", help="password, insecure if sent in the command line")
        parser.add_argument('-m', '--domain', action="store", help="the domain of the server that hosts our moodle database")
        
        args = parser.parse_args()
        self.use_samples = args.use_samples
        self.no_emails = args.no_emails
        self.verbose = args.verbose
        self.passed_date = args.passed_date
        self.no_wordpress = args.no_wordpress
        self.smtp = args.smtp
        self.user = args.user
        self.database = args.database
        self.password = args.password
        self.server = args.domain if args.domain else 'localhost'
        # Setup formatting templates for emails, can be overridden if different look required
        # The default below creates a simple list format
        # Need two {{ and }} because it goes through a parser later at another layer
        self.start_html_tag    = '<html>'
        self.end_html_tag      = "</body></html>"
        self.end_html_tag      = "</html>"
        self.header_pre_tag    = '<div style="font-family:Tahoma,sans-serif;font-weight:bold;font-size:18px;margin-top:20px;margin-bottom:20px;">'
        self.header_post_tag   = "</div>"
        self.begin_section_tag = ""
        self.end_section_tag   = "<br />"
        self.begin_list_tag    = '<div style="font-family:Tahoma,sans-serif;font-size:12px;margin-left:50px;margin-right:50px;margin-bottom:10px;padding: 15px 20px 15px 45px; background-color: #fff; border: 2px solid #4D63A3;">'
        self.end_list_tag      = "</div>"
        self.colon             = ":"
        self.attachment_header = 'Attachments'
        self.name = self.__class__.__name__.replace("_", " ")
        # Class-specific settings, which are delegated to sub-classes
        self.define()
        self.setup_date()

        # Initial values
        month = self.date.month
        day   = self.date.day
        year  = self.date.year

        if self.section_field:
            if self.use_samples:
                # Testing/Debugging use
                self.section_field_object = FieldObject(self.database_name, self.section_field,
                                        samples=self.section_samples())
            else:
                # Production use
                self.section_field_object = FieldObject(
                    self.database_name, self.section_field)
            self.section_field_default_value = self.section_field_object.default_value()
        else:
            self.section_field_object = None
            self.section_field_default_value = None
        
        self.start_date_field = StartDateField(self.user,
                                               self.password,
            self.server,
            self.database,
            self.database_name, 'Start Date')
        self.end_date_field   = EndDateField(self.user,
                                             self.password,
            self.server,
            self.database,
            self.database_name, 'End Date')
        self.process()
        self.start_date_field.update_menu_relative_dates( forward_days = (4 * 7) )
        self.end_date_field.update_menu_relative_dates(   forward_days = (4 * 7) )

    def process(self):
        """
        Finds the objects (using raw_data method) and writes them to self.database_objects,
        and then processes them accordingly. Can be overridden if necessary, but must define self.database_objects
        """
        items = self.raw_data()
        self.database_objects = DatabaseObjects(self.user, self.password, self.server, self.database)
        self.verbose and print(self.database_objects)
        for item in items.items_within_date(self.date):
            self.verbose and print("Item here:")
            item.determine_priority(self.date, self.priority_ids)
            if self.section_field:
                item.determine_section(self.section_field, self.section_field_default_value)
            self.database_objects.add(item)
            self.verbose and print(item)
        self.verbose and print(self.database_objects)
        
    def raw_data(self):
        """
        Returns a generator object that represents the potential rows in the database
        If we are doing a dry-run then return a testing sample
        """
        if self.use_samples:
            # Testing / Debugging use
            return DatabaseObjects(self.database_name, samples=self.samples(), verbose=self.verbose)
        else:
            # Production use
            return DatabaseObjects(self.user, self.password, self.server, self.database, self.database_name, verbose=self.verbose)

    def setup_date(self):
        """
        Responsible for setting up date variables, self.date and self.custom_date
        """
        if self.passed_date:
            split = self.passed_date.split('-')
            if not len(split) == 3:
                raise Exception("Date needs to be in the right format")
            day = int(split[0])
            month = int(split[1])
            year = int(split[2])
            self.date = datetime.date(year, month, day)
        elif self.search_date == "same day":
            self.date = today()
        elif self.search_date == "next day":
            self.date = tomorrow()
        elif self.search_date == "day before":
            self.date = yesterday()
        else:
            raise Nothing
        self.date = datetime.date(2013, 8, 19)

        self.custom_date = custom_strftime('%A %B {S}, %Y', self.date)
        self.verbose and print(self.date)

    def define(self):
        """
        Override in subclass
        """
        # priority_ids
        self.priority_ids = []
        # priority_ids have to be list of id numbers of users whose posts should not "sink" as much as the others

        # section_field
        self.section_field = ''
        # If the form has a field that creates sections, give its name here, its contents will form section
        # in the output.

        # attachment_field
        self.attachment_field = ''
        # Attachments is any content that goes to the very bottom.
        # This was originally intended to be in lieu of files, but could have other applications as well

        # section_field
        self.section_field = ''
        # If there are multiple sections, then define the name in Moodle's field here

        # search_date
        self.search_date = "next day"
        # one of three values "next day", "same day", or "day before" which determines how self.date is set up
        # "day before" is useful mostly for testing

        # agentmap
        self.agent_map = {}
        # keys are the tags, and the list of the object is who to send that information to
        # TODO: Implement

        # agents
        self.agents    = []
        # list of who to send all the data to

    def samples(self):
        """
        Only called when use_samples is true.
        Intended to be overridden
        """
        return []

    def section_samples(self):
        """
        Only called when use_samples is true.
        Intended to be overridden
        """
        return []

    def section_not_found(self, tag):
        """
        Special processing for when tag not found?
        """
        pass

    def html(self, the_html, format=True):
        if format:
            self.html_output += the_html.format(**self.__dict__)
        else:
            self.html_output += the_html

    def subject(self, the_subject):
        self.subject_output = the_subject.format(**self.__dict__)

    def derive_content(self, item):
        """
        Formats the content of the item
        if item.user is defined, adds user info at the end
        Removes the tailing </p> (which the model puts in by default)
        And calls self.list which just adds accordingly html
        Adds user info, and recloses it
        """
        content_field = self.content_field.replace(' ', '_').lower()
        if not hasattr(item, content_field):
            return "This item does not have any content!"
        content = getattr(item, content_field).strip()
        if hasattr(item, 'user'):
            # item.user is defined, so process accordingly
            if content.endswith('</p>'):
                return self.list(content[:-4] + " (" + item.user + ")</p>")
            else:
                return self.list(content + " (" + item.user + ")")
        else:
            # no item.user, so just send the content back
            return self.list(content)

    def format_for_email(self, sections=[]):
        """
        Responsible for setting up html_output and subject_output
        Default behavior assumes:
        * Tags are headers
        * Each item in the tag is a listed item in that tag
        """
        self.colon = ':'
        self.html_output = ""
        self.subject_output = ""

        self.subject(self.name + "{colon} {custom_date}")

        self.html("{start_html_tag}")
        # Set tags: What is passed trumps all, otherwise use the sections provided in define()
        sections_to_use = 'all'
        if sections:
            sections_to_use = sections
        else:
            if self.section_field:
                # Note, we can safely assume we have section_field_object defined
                # Use its method all_values(), which uses sql to get the values
                sections_to_use = self.section_field_object.all_values()
        if sections_to_use == 'all':
            sections_to_use = [None]
        # Iterate over the sections, if None then it'll get all of them, as indicated above
        for section in sections_to_use:
            self.verbose and print("In section {}".format(section))
            # Set my header so I can format with it
            self.header = section if section else self.__class__.__name__.replace("_", ' ')
            # Get the right items, depending on what the value of section is
            if section is None:
                items = self.database_objects.get_all_items()
            else:
                items = self.database_objects.get_items_by_section(section)
            # Check and make sure we actually have content in this section (cont ...)
            if not items:
                self.verbose and print("Nothing found!")
                self.section_not_found(section)
            else:
                self.html("{header_pre_tag}{header}{colon}{header_post_tag}")
                self.html("{begin_section_tag}")
            # Now actually output the content of each item   
            for item in items:
                self.html(self.derive_content(item))   # puts in the content
            # ... this last if statement is continuation from check above
            if items:
                self.html("{end_section_tag}")

        header = False
        for item in self.database_objects:
            vrble_frm_strng                  = lambda strng: strng.replace(' ', '_').lower()
            get_attachment_content           = lambda objct, strng: getattr(objct, vrble_frm_strng(strng))
            item_has_attachment_available    = lambda objct, strng: hasattr(objct, vrble_frm_strng(strng))

            if item_has_attachment_available(item, self.attachment_field):
                attachment = get_attachment_content(item, self.attachment_field)
                if attachment:
                    if not header:
                        self.header = self.attachment_header
                        self.html("{header_pre_tag}{header}{colon}{header_post_tag}")
                        header = True
                    self.html(attachment)

        self.html("{end_html_tag}")

    def print_email(self, recipient_list):
        print("Email from {} to: {}".format(self.sender, recipient_list))
        print(self.get_subject())
        print(self.get_html())
                
    def email_to_agents(self):
        """
        Follows the internal constructs and sends emails with associated tags to the agents
        """
        if self.agents:
            self.verbose and print("Sending {} to {}".format(self.name, self.agents))
            self.format_for_email()
            if self.no_emails:
                self.print_email(self.agents)
            else:
                send_html_email(self.sender, self.agents, self.get_subject(), self.get_html(),
                                domain='student.ssis-suzhou.net')
        if self.agent_map:
            for agent in self.agent_map.keys():
                sections = self.agent_map[agent]
                self.format_for_email(sections)
                self.verbose and print("Sending {} to {}".format(self.name, agent))
                if self.no_emails:
                    self.print_email(agent)
                else:
                    send_html_email(self.sender, agent, self.get_subject(), self.get_html(),
                                domain='student.ssis-suzhou.net')
                    #email = Email(self.server)
                    #email.define_sender(self.sender)
                    #email.add_to(agent)
                    #email.define_subject(self.get_subject())
                    #email.define_content(self.get_html())
                    #email.send()
                    #send_html_email(self.sender, agent, self.get_subject(), self.get_html())

    def post_to_wordpress(self, blog, hour):
        """
        Simplistic way to get what could be an email onto a wordpress blog
        Requires wp-cli https://github.com/wp-cli/wp-cli
        Assuming wp installation is multisite, but works with standalone (blog parameter not needed)
        """
        if self.no_wordpress:
            print("NOT posting to wordpress")
            print(self.get_subject())
            return
        replace_apostrophes = "'\\''"
        d = {
            'title': self.get_subject(),   # remove the 'Student Notices for' part
            'author': 35,  # peter fowles
            'content': self.get_html().replace("'", replace_apostrophes).replace('\n', ''),   # escape apostrophes for bash
            'date': self.date.strftime('%Y-%m-%d {}'.format(hour.strftime('%H:%S:%M'))),
            'blog': "sites.ssis-suzhou.net/{}".format(blog)
            }
        command = """/usr/bin/wp post create --path=/var/www/wordpress --post_type=post --post_title='{title}' --post_content='{content}' --post_author={author} --post_status=future --post_date='{date}' --url={blog}""".format(**d)
        print(command)
        import subprocess
        subprocess.call(command, shell=True)

    def get_subject(self, **kwargs):
        return self.subject_output.format(**kwargs)

    def get_html(self, **kwargs):
        return self.html_output.format(**kwargs)

    def list(self, s):
        """
        Can be used by formatting engine to make a list
        """
        return "{}{}{}".format(self.begin_list_tag, s, self.end_list_tag)

