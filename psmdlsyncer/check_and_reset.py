import postgresql
import re
import subprocess
import os

from psmdlsyncer.html_email.Email import Email, read_in_templates
from psmdlsyncer.utils.Formatter import Smartformatter
from psmdlsyncer.settings import config_get_section_attribute

reset_password_templates = "/home/lcssisadmin/ssispowerschoolsync/templates/password_reset"

def system_call(str):
    subprocess.call(str, shell=True)

class Access:
    sf = Smartformatter()
    prefix = 'ssismdl_'
    def __init__(self):
        
        sf.db_name = config_get_section_attribute('MOODLE', 'db_name')
        sf.db_username = config_get_section_attribute('MOODLE', 'db_username')
        sf.db_password = config_get_section_attribute('MOODLE', 'db_password')
        sf.db_host = config_get_section_attribute('MOODLE', 'db_host')
        self.db = postgresql.open(sf('pq://{db_username}:{db_password}@/{db_name}'))
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

            # [(5123, 49, 1082, 'Happy Student (Test, 99999)', None, None, None, None), (5124, 50, 1082, '##lcssisadmin##: All', None, None, None, None)

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

            dont_again()
        return reset_list

    def reset_email_only(self, who):
        return # this is now broken
        careful = open('/etc/passwd').readlines()
        path = '/home/lcssisadmin/database_password_reset/reset_password.txt'
        for line in careful:
            if ":"+who+":" in line:
                with open(path, 'a') as f:
                    f.write( re.sub(':x:', ':changeme:', line) )
                system_call("/usr/sbin/newusers {}".format(path))
                os.remove(path)
        # Don't email the user their password!

    def reset_dragonnet_only(self, who):
        careful = open('/etc/passwd').readlines()
        for line in careful:
            if ":"+who+":" in line:
                split = line.split(':')
                idnumber = split[4]   # by convention the idnumber is stored as the fifth item
                username = split[0]
                system_call('/usr/bin/php /var/www/moodle/admin/cli/reset_password_changeme_file.php {}'.format(idnumber))

                email = Email()
                read_in_templates(reset_password_templates, email)
                if username.endswith('P'):
                    # We have a parent account, and the email should be different
                    email.add_language('parent')
                    email.define_field('salutation', "Dear SSIS Parent,")
                else:
                    email.add_language('student')
                    email.define_field('salutation', "Dear SSIS Student,")
                email.define_sender('lcssisadmin@student.ssis-suzhou.net', "DragonNet Admin")
                email.define_field('password', 'changeme')
                email.define_field('url', 'http://dragontv.ssis-suzhou.net/podcasts/dragonnet-instruction-how-tos/i-forgot-my-dragonnet-password')
                email.make_subject('Your DragonNet Password has been reset')
                email.add_bcc('lcssisadmin@student.ssis-suzhou.net')
                email.add_to(username + '@student.ssis-suzhou.net')
                email.send()

    def reset_all_passwords(self, who):
        print("Resetting {} dragonnet2 and email".format(who))
        self.reset_email_only(who)
        self.reset_dragonnet_only(who)

    def scan_and_reset(self):
        scanned = self.get_list_of_resets()
        for item in scanned:
            print("About to reset {target}'s {which}.".format(**item))
            try:
                getattr(self, item['which'].strip())(item['target'])
            except AttributeError:
                print("I do not have a method that goes by the name of {}".format(item['which']))

if __name__ == "__main__":

    a = Access()
    a.scan_and_reset()
