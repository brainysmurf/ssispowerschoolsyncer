import datetime
import postgresql
from utils.Dates import date_to_database_timestamp, today, tomorrow, yesterday
from utils.PythonMail import send_html_email
from utils.DB import DragonNetDBConnection
import shelve
import re

from utils.RelativeDateFieldUpdater import RelativeDateFieldUpdater

catch_wrong = True

class Nothing(Exception): pass

k_record_id = 2

# Following gives me 1st, 2nd, 3rd, 4th, etc
def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

class RepeatingEvents:
    """
    Feature that can be enabled or disabled, fails silently
    Provides a shelve
    Keys are dates
    Values consist of list items, which are repeating events
    """
    def __init__(self, path, unique):
        """
        unique: function that returns the part of the item that identifies the item as unique
        """
        self.unique = unique
        if not path:
            # if no path passed, don't enable
            self.db = {}
            self.inactive = True
            self.debug = True
        else:
            self.inactive = False
            self.debug = False
            self.path = path
            self.db = shelve.open(self.path, writeback=True)

    def convert_key(self, key):
        return key.strftime('%d-%m-%y')

    def get(self, key, default=[]):
        if self.inactive: return default
        return self.db.get(self.convert_key(key), default)

    def add(self, key, value):
        if self.debug:
            print("Attempting to add {} to key {} to\n{}".format(value, key, self._db))
            return
        if self.inactive: return  # fail silently
        key = self.convert_key(key)
        if not key in list(self.db.keys()):
            self.db[key] = []
        existing_values = [self.unique(item) for item in self.db[key] if item]
        if not self.unique(value) in existing_values:
            self.db[key].append(value)
        else:
            print("Notice: Did not add {} to repeating events.".format(self.unique(value)))

    def __del__(self):
        if self.db:
            self.db.close()

            

class Maths_Club(DragonNetDBConnection):
    """
    Converts a database on moodle into a useable system that emails users
    """

    verbose = False

    def __init__(self, table):
        """
        Populate self.found with legitimate entries
        Works by looking for target date on the backend, and then finding all entries with matching dates...
           ... and then adding any entries with any that share the same recordid
        """
        super().__init__()
        d = {'table':table}

        self.name = self.__class__.__name__.replace("_", " ")
        self.define()
        self.setup_date()

        self.repeatingevents = RepeatingEvents(self.repeating_events_db_path, self.unique)

        self.priority_one_users = []
        for user_id in self.priority_ids:
            self.priority_one_users.append( self.get_user_name(user_id) )
        self.verbose and print(self.priority_one_users)

        # Initial values
        month = self.date.month
        day   = self.date.day
        year  = self.date.year

        self.final = []
        self.field_updater = RelativeDateFieldUpdater('Maths Club Sign up', 'Date to Attend')
        
        d['date_to_check'] = self.field_updater.format_date(self.date)
        d['field_id'] = self.field_updater.target_id
        potential_rows = self.sql("select * from {table} where content like '%{date_to_check}%' and fieldid={field_id}".format(**d))()
        for row in potential_rows:
            recordid = row[2]
            user = self.get_user_name_from_recordid(recordid)
            self.final.append(
                {'user':user,
                 'content':row[3]
                }
                )
        self.verbose and input(self.found)
        self.reconstruct_found()

    def __del__(self):
        self.field_updater.update_menu_relative_dates(forward_days=14)
        super().__del__()
        

    def setup_date(self):
        """
        Responsible for setting up date variables, self.date and self.custom_date
        """
        if self.search_date == "same day":
            self.date = today()
        elif self.search_date == "next day":
            self.date = tomorrow()
        elif self.search_date == "day before":
            self.date = yesterday()
        else:
            raise Nothing

        self.custom_date = custom_strftime('%A %B {S}, %Y', self.date)
        print(self.date)

    def define(self):
        """
        Override in subclass in order to specify the fields
        """
        # priority_ids
        self.priority_ids = []
        # priority_ids have to be list of id numbers of users whose posts should be given priority 1

        # fields
        self.fields = ['date']
        # fields has to be typed in the order in which it appears
        # when sorted in ascending order by recordid on the backend

        # search_date
        self.search_date = "same day"
        # one of three values "next day", "same day", or "day before" which determines how self.date is set up
        # "day before" is useful mostly for testing

        # repeatingevents
        self.repeating_events_db_path = ''
        # to enable repeatingevents, just add the path here

        # Which field defines the unique one, used by repeatingevents
        self.unique = lambda x: x
        # often it'll be something like lambda x: x['content']

        # agentmap
        self.agent_map = {}
        # keys are the tags, and the list of the object is who to send that information to
        # TODO: Implement

        # agents
        self.agents    = ['adammorris@ssis-suzhou.net',
                          'iainfitzgerald@ssis-suzhou.net',
                          'paulskadsen@ssis-suzhou.net',
                          'ronniefrisinger@ssis-suzhou.net',
                          'garypost@ssis-suzhou.net']
        # list of who to send all the data to

        # sender
        self.sender   = 'DragonNet Admin <lcssisadmin@student.ssis-suzhou.net>'

        # formatting options
        self.start_html_tag    = "<html>"
        self.end_html_tag      = "</html>"
        self.header_pre_tag    = "<p><b>"
        self.header_post_tag   = "</b></p>"
        self.begin_section_tag = "<ul>"
        self.end_section_tag   = "</ul><br />"
        self.colon             = ":"
        # These values work well for self.format_for_email's default behavior


    def determine_priority(self, the_item):
        """
        Puts any user who prioritized number 1
        """
        self.verbose and print(the_item)
        user = the_item['user']
        if user in self.priority_one_users:
            the_item['priority'] = 1    # one digit for highest priority
        else:
            the_item['priority'] = 10   # two digits for lower priority

    def reconstruct_found(self):
        """
        Takes sql information found and converts it into a usable dictionary full of information
    
        Object breaks down thus:
        self.final              = {}     # keys composed of self.tags
        self.final[key]         = []     # list of all objects that share the same tag
        self.final[key][0]      = {}     # each object is a dict
        self.final[key][0][key] = ""     # object keys composed of self.fields
        """
        pass
    
    def get_user_name_from_recordid(self, recordid):
        userid = self.sql('select userid from ssismdl_data_records where id = {}'.format(recordid))()[0][0]
        self.verbose and print("User id: {}".format(userid))
        return self.get_user_name(userid)

    def get_user_name(self, userid):
        """
        Pulls in name info from user's profile
        """
        name_info = 'firstname, lastname, username'
        name = self.sql('select {} from ssismdl_user where id = {}'.format(name_info, userid))()[0]
        firstname, lastname, username = name
        email = '<a href="mailto:{username}@student.ssis-suzhou.net">email</a>'.format(**dict(username=username))
        name = "{} {} ({})".format(firstname, lastname, email)
        self.verbose and print("Name: {}".format(name))
        return name

    def tag_not_found(self, tag):
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
        Removes the tailing </p> (which the front end always puts)
        Adds user info, and recloses it
        """
        content = item['content']
        user = item['user']
        return self.list(user)

    def format_for_email(self):
        """
        Responsible for setting up html_output and subject_output
        Default behavior assumes:
        * Tags are headers
        * Each item in the tag is a listed item in that tag
        """
        self.html_output = ""
        self.subject_output = ""

        self.subject(self.name + "{colon} {custom_date}")

        self.html("{start_html_tag}")
        self.html("<p>The following students have signed up for today's Maths Club:</p>")

        for item in self.final:
            self.html(self.derive_content(item))   # puts in the content

        if not self.final:
            self.html( "<p>No one has signed up for today</p>" )

        if self.final:
            self.html("{end_section_tag}")
                
    def email_to_agents(self):
        """
        Follows the internal constructs and sends emails with associated tags to the agents
        """
        if self.agents:
            self.verbose and print("Sending {} to {}".format(self.name, self.agents))
            self.format_for_email()
            send_html_email(self.sender, self.agents, self.get_subject(), self.get_html(), domain='student.ssis-suzhou.net')
        if self.agent_map:
            for agent in self.agent_map.keys():
                tags = self.agent_map[agent]
                self.format_for_email(tags)
                self.verbose and print("Sending {} to {}".format(self.name, agent))
                send_html_email(self.sender, agent, self.get_subject(), self.get_html(), domain='student.ssis-suzhou.net')

    def post_to_wordpress(self, blog, hour):
        """
        Simplistic way to get what could be an email onto a wordpress blog
        Requires wp-cli https://github.com/wp-cli/wp-cli
        Assuming wp installation is multisite, but works with standalone (blog parameter not needed)
        """
        replace_apostrophes = "'\\''"    # workaround for bash
        d = {
            'path': "/var/www/wordpress",  # path to wordpress installation, needed for wp command
            'title': self.get_subject(),
            #'author': ??,  get ID in table by using wp user list | grep 'peterfowles'
            'content': self.get_html().replace("'", replace_apostrophes),   # escape apostrophes for bash
            'post_status': 'future',  # schedule it, don't do it immediately, 'publish' for now
            'date': self.date.strftime('%y-%m-%d {}:00:00'.format(hour)),    # post on hour on target date
            'blog': blog  # blog path for multisite
            }
        command = """/usr/bin/wp post create --path=/var/www/wordpress --post_type=post --post_title='{title}' --post_content='{content}' --post_author={author} --post_status=future --post_date='{date}' --blog={blog}""".format(**d)
        import subprocess
        print("Posting to wordpress")
        subprocess.call(command, shell=True)

    def get_subject(self, **kwargs):
        return self.subject_output.format(**kwargs)

    def get_html(self, **kwargs):
        return self.html_output.format(**kwargs)

    def list(self, s):
        """
        Can be used by formatting engine to make a list
        """
        return "<li>{}</li>".format(s)



if __name__ == "__main__":

    try:
        here = Maths_Club('ssismdl_data_content')
        here.format_for_email()
        here.email_to_agents()
    except Nothing:
        print("No matching entries found")
