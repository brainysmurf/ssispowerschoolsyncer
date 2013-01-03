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

import datetime
try:
    import postgresql
    dry_run = False
except:
    dry_run = True
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

class DatabaseObject:
    """
    Represents an item in the database
    """
    months = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 'june':6, 'jul':7, 'july':7, 'aug':8, 'sep':9, 'sept':9, 'oct':10, 'nov':11, 'dec':12}
    
    def __init__(self, **kwargs):
        for field in kwargs.keys():
            self.define(field, kwargs[field])

    def define(self, field, value):
        setattr(self, field, value)

    def date_objects(self):
        """
        Returns the startdate and enddate as a datetime objects
        None means we don't have them
        Processing only happens once, results are stored as private internal objects
        You can reset it if you need to by setting _date_objects to None
        """
        if hasattr(self, '_date_objects') and not self._date_objects == None:
            return self._date_objects
        
        if not hasattr(self, 'startdate') or not hasattr(self, 'enddate'):
            return (None, None)

        date_objects = []   # Dates to compare to, needed because strings need to be converted into datetime objects
        
        for this_date in (re.search(r'\((.*)\)$', self.startdate).group(1), re.search(r'\((.*)\)$', self.enddate).group(1) if self.enddate else None):
            if not this_date:
                date_objects.append( None )
            else:
                split = this_date.split(' ')
                start_month = self.months.get(split[0].lower())
                start_day   = int(re.sub(r'[^0-9]', '', split[1]))
                start_year  = int(split[2])
                date_objects.append( datetime.date(start_year, start_month, start_day) )

        if not date_objects:
            date_objects = (None, None)
        self._date_objects = date_objects   # stores this for later so we don't have to process it all over again
        return self._date_objects


    def date_within(self, to_compare_date):
        """
        Given a datetime object date, determines if this object matches the date expected,
        that is, the date of this object falls within the passed date
        Comparison using datetime objects is done, conversion needed
        """
        start_compare, end_compare = self.date_objects()
        if not end_compare:
            # If not defined, then we assume it's for one day only, and therefore end_compare should equal start_compare
            end_compare = start_compare

        if not start_compare:
            return False
        
        # Now that we have the convertion from string to datetime object done,
        # We can do the actual comparison
        # First line manually coerces 'date' object to datetime
        result = to_compare_date >= start_compare and to_compare_date <= end_compare
        print(result)
        return result

    def __str__(self):
        return ", ".join( ["{}: {}".format(key, self.__dict__[key]) for key in self.__dict__ if self.__dict__[key] and not key.startswith('_') ] )

class DatabaseObjects(DragonNetDBConnection):
    """
    Defines the objects for use by the application
    """
    def __init__(self, database_name=None):
        """
        database_name is the database we are using
        If defined, it will use custom sql to get the information we need, and then put it into objects the application can use
        """
        super().__init__()
        self._db = []
        if database_name:
            # TODO: Verify database_name
            sql = """select dc.recordid, usr.firstname, usr.lastname, usr.institution, df.name, cd.content from ssismdl_data_content dc join ssismdl_data_records dr on dr.id = dc.recordid and dr.dataid = {} join ssismdl_user usr on dr.userid = usr.id join ssismdl_data_fields df on dc.fieldid = df.id""".format(database_name)
            # Unpack the sql results into useable objects.
            # NOTE: This essentially converts multiple rows into a pivot table
            # With a better sql query we could could simply this, but
            # making the pivot table in python isn't hard... plus easier to maintain
            sql_result = self.sql(sql)
            unique_records = []
            for row in sql_result:
                recordid = row[0]
                if not recordid in unique_records:
                    unique_records.append( recordid )
            # Now go through each unique record
            for unique_record in unique_records:
                records = [row for row in sql_result if row[0] == unique_record]
                if not records or len(records == 0):
                    print("Shouldn't get here!")    
                # Got the records with a single unique ID, now pack them in
                new_object = DatabaseObject()
                new_object.define(user_first_name = records[0][1])
                new_object.define(user_lastname = records[0][2])
                for row in records:
                    field = row[3]
                    value = row[4]
                    new_object.define(field=value)
                # Okay, we got everything, so now place it into our internal object
                self.add(new_object)
                

    def add(self, obj):
        self._db.append(obj)

    def items_within_date(self, date):
        return (item for item in self._db if item.date_within(date))

    def get_items_by_tag(self, tag):
        return (item for item in self if hasattr(item, 'tag') and item.tag == tag)

    def __iter__(self):
        self._iter_index = 0
        return self

    def __next__(self):
        which = self._iter_index
        self._iter_index += 1
        if which >= len(self._db):
            raise StopIteration
        return self._db[which]

    def __str__(self):
        return "\n/---- Database Objects ----\n" + "\n".join(["| {}".format(str(item)) for item in self]) + "\n\--------------------------\n"

class SampleDatabaseObjects(DatabaseObjects):
    pass

class ExtendMoodleDatabaseToAutoEmailer:
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

        import argparse
        parser = argparse.ArgumentParser(description="Integrates Moodle Database with emailing system")
        parser.add_argument('-t' '--test', action="store_true", dest="dry_run")    
        args = parser.parse_args()
        self.dry_run = args.dry_run
        
        d = {'table':table}

        self.name = self.__class__.__name__.replace("_", " ")
        self.define()
        self.setup_date()

        self.priority_one_users = []
        for user_id in self.priority_ids:
            self.priority_one_users.append( self.get_user_name(user_id) )
        self.verbose and print(self.priority_one_users)

        # Initial values
        month = self.date.month
        day   = self.date.day
        year  = self.date.year

        d['date_to_check'] = date_to_database_timestamp(year=year, month=month, day=day)
        self.process()

    def process(self):
        """
        Finds the objects (using raw_data method) and writes them to self.database_objects,
        and then processes them accordingly. Can be overridden if necessary, but must define self.database_objects
        """
        items = self.raw_data()
        self.database_objects = DatabaseObjects()
        for item in items.items_within_date(self.date):
            self.database_objects.add(item)
            self.determine_priority(item)
            self.determine_tag(item)
        print(self.database_objects)
        
        # code to be replaced
        #for tag in self.tags:
        #    d['tag'] = tag
        #    potential_rows = self.sql("select recordid from {table} where content = '{date_to_check}'".format(**d))()
        #    for row in potential_rows:
        #        d['recordid'] = row[0]
        #        match = self.sql("select * from {table} where recordid = {recordid} and content like '%{tag}%'".format(**d))()
        #        if match:
        #            matched = self.sql("select * from {table} where recordid = {recordid}".format(**d))()
        #            matched.sort(key=lambda x:x[0])
        #            self.found.append( matched )
        #self.verbose and input(self.found)
        #self.reconstruct_found()

        

    def raw_data(self):
        """
        Returns a generator object that represents the potential rows in the database
        If we are doing a dry-run then return a testing sample
        """
        if self.dry_run:
            if hasattr(self, 'samples'):
                return self.samples
            else:
                raise NotImplemented("Dry run detected, by samples not created!")
        else:
            return DatabaseObjects('select dc.recordid, usr.firstname, usr.lastname, usr.institution, df.name, cd.content from ssismdl_data_content dc join ssismdl_data_records dr on dr.id = dc.recordid and dr.dataid = {} join ssismdl_user usr on dr.userid = usr.id join ssismdl_data_fields df on dc.fieldid = df.id'.format())

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

        # tag_map
        self.tag_map = {}
        # convert the tags to user-friendly version

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

        # formatting options
        self.start_html_tag    = "<html>"
        self.end_html_tag      = "</html>"
        self.header_pre_tag    = "<p><b>"
        self.header_post_tag   = "</b></p>"
        self.begin_section_tag = "<ul>"
        self.end_section_tag   = "</ul><br />"
        self.colon             = ":"
        # These values work well for self.format_for_email's default behavior

    def determine_tag(self, the_item):
        """
        Processes a database item and assigns it a tag
        Useful in cases where things are organized by tags
        """
        the_item.tag = the_item.section

    def determine_priority(self, the_item):
        """
        Puts any user who prioritized number starts at 1
        If not any priority user, starts at value of 10
        Then, calculates priority based on how far away we are from having been published
        """
        self.verbose and print(the_item)
        user = the_item.user
        first_published, _ = the_item.date_objects()
        if user in self.priority_one_users:
            priority = 1    # one digit for highest priority
        else:
            priority = 10   # two digits for lower priority

        days_since = (datetime.date(self.date.year, self.date.month, self.date.day) - first_published).days   # substraction of two datetime object results in datetime object, which has 'days'
        if days_since < 0:
            raise NotImplmented('Huh? This was first published sometime in the future? Should not happen!')
        priority += days_since * 100
        self.verbose and print(priority)
        the_item.priority = priority

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
        if self.dry_run:
            return ""
        else:
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
        content = item.content
        user = item.user
        if content.endswith('</p>'):
            return self.list(content[:-4] + " (" + user + ")</p>")
        else:
            return self.list(content + " (" + user + ")</p>")

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
            items = self.database_objects.get_items_by_tag(tag)
            if not items:
                self.tag_not_found(tag)
            else:
                self.html("{header_pre_tag}{header}{colon}{header_post_tag}")
                self.html("{begin_section_tag}")
                
            for item in items:
                self.html(self.derive_content(item))   # puts in the content

            if items:
                self.html("{end_section_tag}")

        header = False
        for key in self.final.keys():
            for item in self.final[key]:
                if item['attachment']:
                    if not header:
                        self.header = "Attachments"
                        self.html("{header_pre_tag}{header}{colon}{header_post_tag}")
                        header = True
                    self.html(item['attachment'])

                
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
