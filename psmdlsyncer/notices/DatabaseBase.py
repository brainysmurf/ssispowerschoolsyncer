import postgresql
from psmdlsyncer.sql import MoodleDBConnection
from psmdlsyncer.mod.database import FieldObject
from psmdlsyncer.utils.Dates import today, tomorrow, yesterday
from psmdlsyncer.html_email import Email
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.notices.Model import DatabaseObjects, DatabaseObject, StartDateField, EndDateField
import re
import datetime
import smtplib

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
    #TODO: Make it simple to get the new kid on the block
    master_username = 'peterfowles'
    shared_command_line_args_switches = ['verbose', 'use_samples', 'no_emails', 'update_date_fields']
    shared_command_line_args_strings = {'passed_date':None}

    def __init__(self, database_name, server='dragonnet.ssis-suzhou.net'):
        """
        Populate self.found with legitimate entries
        Works by looking for target date on the backend, and then finding all entries with matching dates...
           ... and then adding any entries with any that share the same recordid
        """
        super().__init__()
        # Setup
        self.database_name = database_name
        dnet = MoodleDBConnection()
        self.database_id = dnet.get_unique_row("data", "id", name=self.database_name)

    def init(self):
        # Setup formatting templates for emails, can be overridden if different look required
        # The default below creates a simple list format
        # Need two {{ and }} because it goes through a parser later at another layer
        # Also, since it goes to an email, CSS is avoided
        self.verbose = self.settings.verbose
        self.start_html_tag    = '<html>'
        self.end_html_tag      = "</html>"
        self.header_pre_tag    = '<h3>'
        self.header_post_tag   = "</h3>"
        self.begin_section_tag = "<ul>"
        self.end_section_tag   = "</ul>"
        self.begin_list_tag    = '<li>'
        self.end_list_tag      = "</li>"
        self.colon             = ":"
        self.attachment_header = 'Attachments'
        self.email_editing     = False

        self.server = config_get_section_attribute('EMAIL', 'domain')
        if not self.server:
            print("Using localhost for mail server")
            self.server = 'localhost'
        
        self.name = self.__class__.__name__.replace("_", " ")
        # Class-specific settings, which are delegated to sub-classes
        self.define()
        self.setup_date()

        # Initial values
        month = self.date.month
        day   = self.date.day
        year  = self.date.year

        if self.section_field:
            if self.settings.use_samples:
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
        
        self.start_date_field = StartDateField(self.database_name, 'Start Date')
        self.end_date_field   = EndDateField(self.database_name, 'End Date')
        self.process()

        if self.settings.update_date_fields:
            self.start_date_field.update_menu_relative_dates( forward_days = (4 * 7) )
            self.end_date_field.update_menu_relative_dates(   forward_days = (4 * 7) )

        self.edit_word = "Edit"

    def process(self):
        """
        Finds the objects (using model_items method) and writes them to self.database_objects,
        and then processes them accordingly. Can be overridden if necessary, but must define self.database_objects
        """
        self.model = self.model_items()

        # DO NOT PASS IT A NAME, WE NEED A BLANK ONE
        self.database_objects = DatabaseObjects()

        self.verbose and print(self.database_objects)
        for item in self.model.items_within_date(self.date):
            self.verbose and print("Item within date found here:")
            item.determine_priority(self.date, self.priority_ids)
            if self.section_field:
                item.determine_section(self.section_field, self.section_field_default_value)
            self.database_objects.add(item)
        self.verbose and print("\n\nDatabase object")
        self.verbose and print(self.database_objects)
        
    def model_items(self):
        """
        Returns a generator object that represents the potential rows in the database
        If we are doing a dry-run then return a testing sample
        """
        if self.settings.use_samples:
            # Testing / Debugging use
            return DatabaseObjects(self.database_name, samples=self.samples(), verbose=self.verbose)
        else:
            # Production use
            return DatabaseObjects(self.database_name, verbose=self.verbose)

    def setup_date(self):
        """
        Responsible for setting up date variables, self.date and self.custom_date
        """
        if self.settings.passed_date:
            split = self.settings.passed_date.split('-')
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

        self.custom_date = custom_strftime('%A %B {S}, %Y', self.date)
        self.verbose and print(self.date)

    def email(self, email: "List or not", cc=None, bcc=None):
        """
        USE THE Email API TO SEND AN EMAIL
        HANDLES IT WHETHER OR NOT LISTS ARE PASSED
        """
        e = Email(self.server)
        e.define_sender(self.sender)
        if isinstance(email, list):
            for item in email:
                e.add_to(item)
        else:
            e.add_to(email)

        if cc:
           if isinstance(cc, list):
               for item in cc:
                   e.add_cc(item)
           else:
               e.add_cc(cc)

        if bcc:
            if isinstance(bcc, list):
                for item in bcc:
                    e.add_bcc(item)
            else:
                e.add_bcc(bcc)

        e.define_subject(self.get_subject())
        e.define_content(self.get_html())

        try:
            e.send()
        except smtplib.SMTPRecipientsRefused:
            self.print_email(email)
            

    def define(self):
        """
        OVERRIDE IN SUBCLASS
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

    def derive_content(self, item: "Model.DatabaseObject"):
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
        content = getattr(item, content_field)
        edit_phrase = ""

        # BLOCK FOR email_editing FEATURE
        # TODO GET A BETTER IMPLEMENTATION OF THIS!
        #      edit_phrase CAN BE BETTER BECAUSE THE MODEL HAS MOST OF THIS INFO
        #      ESPECIALLY THE dbid_id VARIABLE
        if self.email_editing and hasattr(item, 'dbid'):
            edit_phrase = '<br /><a href="http://dragonnet.ssis-suzhou.net/mod/data/view.php?d={}&mode=list&advanced=0&filter=1&advanced=1&f_{}={}">{}</a> '.format(
                self.database_id,
                self.model.dbid_id,
                item.dbid,
                self.edit_word)
            
        # NOW EDIT THE CONTENT SO THAT <p> TAGS ARE REMOVED, AND ANY SPACES ARE CONSOLIDATED
        content = re.sub(r'</*p>', '', content)
        content = re.sub(r'\n', ' ', content)
        content = re.sub(' {2,}', ' ', content).strip()

        # BLOCK FOR INCLUDING THE USER INFORMATION
        if hasattr(item, 'user'):
            # item.user is defined, so process accordingly
            if content.endswith('</p>'):
                return self.list(content[:-4] + " (" + item.user + ") " + edit_phrase + "</p>")
            else:
                return self.list(content + " (" + item.user + ") " + edit_phrase)
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
                self.verbose and print("Getting all items")
                items = self.database_objects.get_all_items()
            else:
                self.verbose and print("Getting section {} items".format(section))
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
            if self.settings.no_emails:
                self.print_email(self.agents)
            else:
                self.email(self.agents)

        if self.agent_map:
            for agent in self.agent_map.keys():
                sections = self.agent_map[agent]
                self.format_for_email(sections)
                self.verbose and print("Sending {} to {}".format(self.name, agent))
                if self.settings.no_emails:
                    self.print_email(agent)
                else:
                    self.email(agent)

    def post_to_wordpress(self, blog, hour, date=None):
        """
        SIMPLISTIC WAY TO GET WHAT COULD BE AN EMAIL ONTO A WORDPRESS BLOG
        REQUIRES wp-cli https://github.com/wp-cli/wp-cli
        ASSUMING WP INSTALLATION IS MULTISITE, BUT WORKS WITH STANDALONE (BLOG PARAMETER NOT NEEDED)
        If date IS none THEN USE self.date
        """
        self.format_for_email()
                    
        date_to_use = date if date else self.date            
        replace_apostrophes = "'\\''"
        d = {
            'title': self.get_subject(),   # remove the 'Student Notices for' part
            'author': 35,  # peter fowles
            'content': self.get_html().replace("'", replace_apostrophes).replace('\n', ''),   # escape apostrophes for bash
            'date': date_to_use.strftime('%Y-%m-%d {}'.format(hour.strftime('%H:%S:%M'))),
            'blog': "sites.ssis-suzhou.net/{}".format(blog)
            }
        command = """/usr/bin/wp post create --path=/var/www/wordpress --post_type=post --post_title='{title}' --post_content='{content}' --post_author={author} --post_status=future --post_date='{date}' --url={blog}""".format(**d)
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
        return "{}{}{}".format(self.begin_list_tag, s.strip('\n'), self.end_list_tag)
