from psmdlsyncer.sql import MoodleDBSession
from psmdlsyncer.mod.database import FieldObject
from psmdlsyncer.utils.Dates import today, tomorrow, yesterday
from psmdlsyncer.html_email import Email
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.notices.Model import DatabaseObjects, DatabaseObject, StartDateField, EndDateField
import re
import datetime
import smtplib
import subprocess

from html.parser import HTMLParser

class TagKeeper(HTMLParser):
    def __init__(self, tags_to_keep, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self._text = []
        self._tags_to_keep = set(tags_to_keep)
        self.starttag = None
    def clear_text(self):
        self._text = []
    def handle_starttag(self, tag, attrs):
        self.starttag = tag
        if tag in self._tags_to_keep:
            self._text.append(self.get_starttag_text())
        else:
            self._text.append('')
    def handle_endtag(self, tag):
        if tag in self._tags_to_keep:
            self._text[-1] += "</{}>".format(tag)
        else:
            pass
    def handle_data(self, data):
        self._text[-1] += data
    def get_data(self):
        return ' '.join(self._text)

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

    def __init__(self, database_name, date):
        """
        Populate self.found with legitimate entries
        Works by looking for target date on the backend, and then finding all entries with matching dates...
           ... and then adding any entries with any that share the same recordid
        """
        super().__init__()
        # Setup
        self.database_name = database_name
        self.dnet = MoodleDBSession()
        self.database_id = self.dnet.get_column_from_row("data", 'id', name=self.database_name)
        self.setup_date(date)

    def init(self):
        # Setup formatting templates for emails, can be overridden if different look required
        # The default below creates a simple list format
        # Need two {{ and }} because it goes through a parser later at another layer
        # Also, since it goes to an email, CSS is avoided
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

        # Initial values
        month = self.date.month
        day   = self.date.day
        year  = self.date.year

        if self.section_field:
            self.section_field_object = FieldObject(self.database_name, self.section_field)
            self.section_field_default_value = self.section_field_object.default_value()
        else:
            self.section_field_object = None
            self.section_field_default_value = None
        
        self.start_date_field = StartDateField(self.database_name, 'Start Date')
        self.end_date_field   = EndDateField(self.database_name, 'End Date')
        self.process()

        self.edit_word = "Edit"

    def update_date_fields(self):
        self.start_date_field.update_menu_relative_dates( forward_days = (4 * 7) )
        self.end_date_field.update_menu_relative_dates(   forward_days = (4 * 7) )

    def process(self):
        """
        Finds the objects (using model_items method) and writes them to self.database_objects,
        and then processes them accordingly. Can be overridden if necessary, but must define self.database_objects
        """
        self.model = self.model_items()

        # DO NOT PASS IT A NAME, WE NEED A BLANK ONE
        self.database_objects = DatabaseObjects()
        stripper = TagKeeper(['a', 'b', 'i', 'ol', 'ul', 'li'])
        for item in self.model.items_within_date(self.date):
            stripper.clear_text()
            stripper.feed(item.full_content)
            item.full_content = stripper.get_data()
            item.determine_priority(self.date, self.priority_ids)
            if self.section_field:
                item.determine_section(self.section_field, self.section_field_default_value)
            self.database_objects.add(item)

    def model_items(self):
        """
        Returns a generator object that represents the potential rows in the database
        If we are doing a dry-run then return a testing sample
        """
        return DatabaseObjects(self.database_name)

    def setup_date(self, date):
        """
        """
        self.date = date
        self.custom_date = custom_strftime('%A %B {S}, %Y', self.date)

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
            
    def setup_priorities(self):
        self.priority_ids = []
        for username in self.priority_usernames:
            self.priority_ids.append(self.dnet.get_column_from_row('user', 'id', username=username))

    def define(self):
        """
        OVERRIDE IN SUBCLASS
        """
        # priority_ids
        self.priority_usernames = []
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

    def prepare_formatting(self, sections=[]):
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
            # Set my header so I can format with it
            self.header = section if section else self.__class__.__name__.replace("_", ' ')
            # Get the right items, depending on what the value of section is
            if section is None:
                items = self.database_objects.get_all_items()
            else:
                items = self.database_objects.get_items_by_section(section)
            # Check and make sure we actually have content in this section (cont ...)
            if not items:
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

    def print_email(self, recipient_list, format=True):
        if format:
            self.prepare_formatting()

        print("Email from {} to: {}".format(self.sender, recipient_list))
        print(self.get_subject())
        print(self.get_html())

    def email_to_agents(self, format=True):
        """
        Follows the internal constructs and sends emails with associated tags to the agents
        """
        if format:
            self.prepare_formatting()

        if self.agents:
            self.email(self.agents)

        if self.agent_map:
            for agent in self.agent_map.keys():
                sections = self.agent_map[agent]
                self.email(agent)

    def post_to_wordpress(self, url, blog, author, hour, format=True):
        """
        SIMPLISTIC WAY TO GET WHAT COULD BE AN EMAIL ONTO A WORDPRESS BLOG
        REQUIRES wp-cli https://github.com/wp-cli/wp-cli
        """
        if format:
            self.prepare_formatting()
        path_to_wordpress = config_get_section_attribute('SITES', 'path_to_docroot', required=True)
        path_to_wpcli = config_get_section_attribute('SITES', 'path_to_wpcli', required=True)
        if not url:
            wordpress_url = config_get_section_attribute('SITES', 'url', required=True)
        else:
            wordpress_url = url

        # Get the user information first
        command = "{} --path={} user get {} --format=json ".format(path_to_wpcli, path_to_wordpress, author)
        to_call = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        result, err = to_call.communicate()
        import json
        user = json.loads(result.decode())

        # Now clean up the html, add links if not there and remove errant tags, also clean up for passing on
        try:
            from lxml.html.clean import Cleaner
            from lxml.html.clean import autolink_html
        except ImportError:
            click.secho('We need lxml!', fg='red')

        content = self.get_html()
        cleaner = Cleaner(remove_tags=['p', 'div'])  # Moodle's editor has loads of lonely p and div tags
        content = cleaner.clean_html(content)
        content = autolink_html(content)
        replace_apostrophes = "'\\''"
        content = content.replace("'", replace_apostrophes).replace('\r', ' ')   # escape apostrophes for bash

        date_as_string = '{}-{}-{} {}:{}:00'.format(self.date.year, self.date.month, self.date.day, hour.tm_hour, hour.tm_min)

        d = {
            'title': self.get_subject(),   # remove the 'Student Notices for' part
            'author': user['ID'],
            'content': content,
            'date': date_as_string,
            'blog': blog,
            'url': wordpress_url,
            'path_to_wpcli': path_to_wpcli,
            'path_to_docroot': path_to_wordpress
            }

        command = """{path_to_wpcli} post create --path={path_to_docroot} --post_type=post --post_title='{title}' --post_content='{content}' --post_author={author} --post_status=future --post_date='{date}' --url={url}/{blog}""".format(**d)
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

if __name__ == "__main__":

    s = TagKeeper(['a'])
    s.feed('<p class="hi"><ol><li><a href="slkfjsdk">Thisfdsjkfd</a> </li><li>ddd</li></ol></p>')
    print(s.get_data())
