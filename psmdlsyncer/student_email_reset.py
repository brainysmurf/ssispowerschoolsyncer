"""

PROVIDES AN API TO POLL MOODLE'S DATABASE FOR STUDENT EMAIL PASSWORD RESETS

REQUIRES THE FOLLOWING:
    user_email_password_reset TABLE
    finger INSTALLED ON THE EMAIL SERVER

Access IS A WRAPPER TO THE DATABASE CALLS

"""

import postgresql
import re
import subprocess
import os
import sys

from psmdlsyncer.html_email.Email import Email, read_in_templates
from psmdlsyncer.utils.Formatter import Smartformatter, NS
from psmdlsyncer.settings import config_get_section_attribute

class NoSuchUser(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def system_call(command):
    """
    WRAPPER FOR THE Popen CALL
    TURN RESULT INTO AN OBJECT AND RETURN
    DOES NOT CHECK FOR ERRORS
    DO NOT USE WITH USER INPUT

    CONVERTS TO APPROPRIATE ENCODING, RETURNS 'REGULAR' STRINGS
    """
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # SKIP CHECK FOR not p
    # SIMPLY RETURN THE STANDARD OUT

    sf = Smartformatter()
    encoding = sys.getdefaultencoding()
    sf.stdout, sf.stderr = p.communicate()
    sf.stdout = sf.stdout.decode(encoding).strip('\n')
    sf.stderr = sf.stderr.decode(encoding).strip('\n')
    return sf

def check_user(powerschoolID):
    """
    WRAPPER FOR SYSTEM CALL finger powerschooLID
    LOOKS AT RESULT AND PUTS username INSIDE RESULT
    """
    result = system_call('finger {} | tail -n 1'.format(powerschoolID))
    finger_returns_when_no_such_user = 'no such user.'
    if result.stdout.endswith(finger_returns_when_no_such_user):
        raise NoSuchUser
    match = re.match(r'([a-z]*[0-9]{2}) (.*)', result.stdout)
    if not match:
        raise Exception(result("Whoa, something happened when parsing result from finger command!{NEWLINE}{stdout}"))
    result.username = match.group(1)
    if not result.username:
        raise Exception(result("Did not find a username??!!{NEWLINE}{stdout}"))
    return result

class Access:

    prefix = 'ssismdl_'
    def __init__(self):
        sf = Smartformatter()
        sf.db_name = config_get_section_attribute('MOODLE', 'db_name')
        sf.db_username = config_get_section_attribute('MOODLE', 'db_username')
        sf.db_password = config_get_section_attribute('MOODLE', 'db_password')
        sf.db_host = config_get_section_attribute('MOODLE', 'db_host')
        self.db = postgresql.open(sf('pq://{db_username}:{db_password}@{db_host}/{db_name}'))
        self.sql = self.db.prepare

    def __del__(self):
        self.db.close()

    def convert_to_table(self, table):
        if table.startswith(self.prefix):
            return table
        else:
            return self.prefix + table

    def show_tables(self):
        return [t[0] for t in self.sql('select table_name from information_schema.tables')()]

    def show_tables_startswith(self, withwhat):
        return [t for t in self.show_tables() if t.startswith(self.prefix+withwhat)]

    def show_table_column_names(self, table):
        return [c[0] for c in self.sql("select column_name from information_schema.columns where table_name='{}'".format(self.prefix+table))()]

    def select_table(self, table):
        return self.sql('select * from {}{}'.format(self.prefix, table))()

    def select_table_by_kwarg(self, table, **kwargs):
        """
        Takes only the first kwargs arg as the format
        where {what} = {value}
        Sweeet.
        """
        d = {'table':self.convert_to_table(table), 'id':id}
        wheres = []
        for i in range(len(list(kwargs.keys()))):
            passed = list(kwargs.keys())[i]
            value = kwargs[passed]
            if str(value).isdigit:
                wheres.append( "{} = {}".format(passed, value) )
            else:
                wheres.append( "{} = '{}'".format(passed, value) )
        d['wherestring'] = " AND ".join(wheres)
        return self.sql('select * from {table} where {wherestring}'.format(**d))()

    def update_table(self, table, column, row, value):
        d = {'column':column, 'table':self.convert_to_table(table), 'row':row, 'value':value}
        if not str(row).isdigit():
            raise NotImplemented("row must be an integer")
        return self.sql("update {table} set {column} = '{value}' where id = {row};".format(**d))()

    def delete_table_by_kwarg(self, table, **kwargs):
        """
        SELECT table WHERE kwargs
        """
        sf = Smartformatter()
        sf.table = self.convert_to_table(table)
        wheres = []
        for i in range(len(list(kwargs.keys()))):
            passed = list(kwargs.keys())[i]
            value = kwargs[passed]
            if str(value).isdigit:
                wheres.append( "{} = {}".format(passed, value) )
            else:
                wheres.append( "{} = '{}'".format(passed, value) )
        sf.wherestring = " AND ".join(wheres)
        return self.sql(sf('delete from {table} where {wherestring}'))()

    def update_kwarg(self, table, column, value, **kwargs):
        d = {'column':column, 'table':self.convert_to_table(table), 'value':value}

        # set up the wherestring by going through each kwargs key
        wheres = []
        for i in range(len(list(kwargs.keys()))):
            passed = list(kwargs.keys())[i]
            value = kwargs[passed]
            if str(value).isdigit:
                wheres.append( "{} = {}".format(passed, value) )
            else:
                wheres.append( "{} = '{}'".format(passed, value) )
        d['wherestring'] = " AND ".join(wheres)

        return self.sql("update {table} set {column} = '{value}' where {wherestring};".format(**d))

    def get_list_of_resets(self):

        d = {'table':self.convert_to_table('data_content')}
        #command = self.sql('select id,recordid,content from {table}'.format(**d))

        # command will return the recordid of any itmes that have't yet been labeled "Success"
        command = self.sql("""select distinct dc.id,dc.recordid from ssismdl_data_content dc join ssismdl_data_records dr on dc.recordid = dr.id join ssismdl_data d on dr.dataid = 11 join ssismdl_data_fields on dc.fieldid = 50 where dc.content not like 'Success%'""")        
        command_result = command()
        if not command_result:
            return []  # shortcut

        # we have something, so go through it all
        reset_list = []
        
        for record_item in command_result:
            id, recordid = record_item
            d['recordid'] = recordid
            select = self.select_table_by_kwarg(**d)
            
            # Sort by fieldid, so I can extract it the right way
            select.sort( key=lambda x: x[1] )

            # This is bad, need to port this code to a way that doesn't change
            # Or at least do some trick to check
            if select[0][3]:
                target = select[0][3]
                #if select[2][3]:
                #target = select[2][3]
            reset_list.append(  {'target':select[0][3][-6:-1], 'which':select[1][3].lower().replace(' ', '_')}  )
            # TODO

            success = "Success: Reset {} password".format(select[0][3][17:])
            dont_again = self.update_kwarg(d['table'], 'content', success, recordid=recordid, id=id)
            print('Entry on the database has been changed to read successful')

            dont_again()
        return reset_list

    def reset_email(self, who):
        careful = open('/etc/passwd').readlines()
        path = '/home/lcssisadmin/database_password_reset/reset_password.txt'
        try:
            result = check_user(who)
        except NoSuchUser:
            print(result("No such user returned in call with {}".format(who)))
            return

        # RESULT NOW HAS username
        result.default_password = 'changeme'
        result = system_call(result('echo {username}:{default_password} | chpasswd'))
        print(result)

        """
        for line in careful:
            if ":"+who+":" in line:
                with open(path, 'a') as f:
                    f.write( re.sub(':x:', ':changeme:', line) )
                system_call("/usr/sbin/newusers {}".format(path))
                os.remove(path)
        """
                
if __name__ == "__main__":

    dnet = Access()
    results = dnet.select_table('user_email_password_reset')
    # COLLAPSE SO WE ARE GUARENTEED TO BE WORKING WITH JUST ONE AT A TIME
    results = set(results)
    for row in results:
        sf = Smartformatter()
        sf.userid, sf.num, sf.fullname, sf.email = row
        print(sf('About to reset {fullname} ({num}) email password to changeme'))
        dnet.reset_email(str(sf.num))
        print(sf('Done'))
        sf.table = dnet.convert_to_table('user_email_password_reset')
        command = dnet.sql(sf("delete from {table} where powerschoolid = '{num}'"))
        command()
