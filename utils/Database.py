import datetime
import postgresql
from utils.Dates import date_to_database_timestamp, today, tomorrow, yesterday
from utils.PythonMail import send_html_email
from utils.DB import DragonNetDBConnection
import shelve
import re

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
        self.db.close()

class ExtendMoodleDatabaseToAutoEmailer(DragonNetDBConnection):
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

        self.found = []
        d['date_to_check'] = date_to_database_timestamp(year=year, month=month, day=day)
        for tag in self.tags:
            d['tag'] = tag
            potential_rows = self.sql("select recordid from {table} where content = '{date_to_check}'".format(**d))()
            for row in potential_rows:
                d['recordid'] = row[0]
                match = self.sql("select * from {table} where recordid = {recordid} and content like '%{tag}%'".format(**d))()
                if match:
                    matched = self.sql("select * from {table} where recordid = {recordid}".format(**d))()
                    matched.sort(key=lambda x:x[0])
                    self.found.append( matched )
        self.verbose and input(self.found)
        self.reconstruct_found()

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
        self.fields = []
        # fields has to be typed in the order in which it appears
        # when sorted in ascending order by recordid on the backend

        # tags
        self.tags   = []
        # these are the tags that are manually put into fields on the front end
        # recommended that you use <span style="display:none"></span> to hide the actual tag from users
        # this class finds them using "content like '%tag%'" sql query

        # tag_map
        self.tag_map = {}
        # convert the tags to user-friendly version

        # search_date
        self.search_date = "next day"
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
        self.agents    = []
        # list of who to send all the data to

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
        self.final = {}    # list of dicts, each one an item
        for item in self.found:
            result = {}
            recordid = item[0][k_record_id]  # this is uniform throughout the item, just take the first one
            result['user'] = self.get_user_name_from_recordid(recordid)
            for field_id in range(0, len(item)):
                content = item[field_id][3]
                if content:
                    for tag in self.tags:
                        if tag in content:
                            result['tag'] = tag
                key = self.fields[field_id]
                result[key] = content
            key = result['tag']
            if not key in list(self.final.keys()):
                self.final[key] = []
            self.determine_priority(result)
            self.final[key].append( result )
 
        # record repeating events to database for future use
        for key in self.final.keys():
            items = self.final[key]
            for item in items:
                if item['timesrepeat']:
                    times = re.sub(r'[^0-9]', '', item['timesrepeat'])  # remove any non-numeric
                    if not times:
                        times = 0
                    else:
                        times = int(times)
                    priority_add = 2
                    for day in range(0, times):
                        day_to_repeat = self.date + datetime.timedelta(days=day+1)
                        if 'priority' not in list(item.keys()):
                            item['priority'] = 1000;
                            print("This item:\n{}\ndid not have a priority field, assigned 1000".format(item))
                        else:
                            item['priority'] += priority_add
                        priority_add += 2  # increase by 2 to allow for future expansion
                        self.repeatingevents.add(day_to_repeat, item)

        # incorporate repeated events already processed by previous run, if available
        for item in self.repeatingevents.get(self.date):
            if 'priority' not in list(item.keys()):
                item['priority'] = 1000
                print("Warning: This item:\n{}\ndid not have a priority field, assigned 1000".format(item))
                
            key = item['tag']
            if not key in list(self.final.keys()):
                self.final[key] = []

            existing_items = [self.unique(i) for i in self.final[key] if i]
            if not self.unique(item) in existing_items:
                self.final[key].append( item )

        # Sort items by priority
        for key in self.final.keys():
            items = self.final[key]
            items.sort(key=lambda x: x['priority'])

        
        if self.verbose:
            for key in self.final.keys():
                for item in self.final[key]:
                    for item_key in item.keys():
                        if not item_key == 'section':
                            print("{}: {}".format(item_key, item[item_key]))
                print()
            input()

    def get_user_name_from_recordid(self, recordid):
        userid = self.sql('select userid from ssismdl_data_records where id = {}'.format(recordid))()[0][0]
        self.verbose and print("User id: {}".format(userid))
        return self.get_user_name(userid)

    def get_user_name(self, userid):
        """
        Pulls in name info from user's profile
        """
        name_info = 'firstname, lastname'
        name = self.sql('select {} from ssismdl_user where id = {}'.format(name_info, userid))()[0]
        firstname, lastname = name
        name = "({} {})".format(firstname, lastname)
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
        if content.endswith('</p>'):
            return self.list(content[:-4] + " " + user + "</p>")
        else:
            return self.list(content + user + "</p>")

    def format_for_email(self, tags=[]):
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

        # Tags parameter is used by self.send_to_agents to format the email
        # If not passed, then we include all tags
        if not tags: tags = self.tags

        for tag in tags:
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
                
    def email_to_agents(self):
        """
        Follows the internal constructs and sends emails with associated tags to the agents
        """
        if self.agents:
            self.verbose and print("Sending {} to {}".format(self.name, self.agents))
            self.format_for_email()
            send_html_email(self.sender, self.agents, self.get_subject(), self.get_html())
        if self.agent_map:
            for agent in self.agent_map.keys():
                tags = self.agent_map[agent]
                self.format_for_email(tags)
                self.verbose and print("Sending {} to {}".format(self.name, agent))
                send_html_email(self.sender, agent, self.get_subject(), self.get_html())

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
        here = ExtendMoodleDatabaseToAutoEmailer('ssismdl_data_content')
        here.format_for_email()
    except Nothing:
        print("No matching entries found")
