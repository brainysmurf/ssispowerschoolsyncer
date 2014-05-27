"""
Exposes native Moodle functions to python
Uses pexpect utility
"""

from psmdlsyncer.utils import NS
from psmdlsyncer.settings import config_get_section_attribute, logging
import pexpect, sys, os

class CallPHP:
    """
    Interfaces with php file phpclimoodle.php
    """
    def __init__(self):
        #TODO: Get this info from standard settings and config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.default_logger = self.logger.debug
        self.sf = NS()
        self.email_accounts = config_get_section_attribute('EMAIL', 'check_accounts')
        self.moodle_accounts = config_get_section_attribute('MOODLE', 'sync')
        # TODO: Depreciate this stupid dry run thingie, make it a logging feature instead
        self.dry_run = config_get_section_attribute('DEFAULTS', 'dry_run')
        self.path_to_cli = config_get_section_attribute('MOODLE', 'path_to_cli')
        self.path_to_php = config_get_section_attribute('MOODLE', 'path_to_php')
        if not self.path_to_php:
            self.path_to_php = '/usr/bin/php'

        # Moodle requires any php files to be run from the admin/cli directory
        os.chdir(self.path_to_cli)

        # And now, spawn it
        cmd = "{} {}/phpclimoodle.php".format(self.path_to_php, self.path_to_cli)
        self.process = pexpect.spawn(cmd)
        self.process.delaybeforesend = 0  # speed things up a bit, eh?
        self.process.timeout = 3600
        self.process.expect_exact('?: ') # not sure why this works the first time

    def command(self, routine, cmd):
        """
        Interfaces with pexpect
        """
        try:
            self.process.sendline(routine + ' ' + cmd)
        except OSError:
            if routine == "QUIT":
                return # this is expected, nevermind
            if self.process.isalive():
                self.logger.warning("Huh. Error but it's still alive!")
            else:
                self.logger.warning("The other side just up and died")

        # We know that the phpclimoodle file returns a plus if it's all good
        # and a negative if not, handle accordingly
        success_string = '\+.*'
        error_string = '-\d+ .*'
        which = self.process.expect([success_string, error_string])

        if which == 0:
            pass
        elif which == 1:
            str = self.process.after.decode('utf-8')
            where = str.find('\r\n?: ')
            if not where:
                self.logger.critical(str)
            self.logger.warning(str[:where])   # make sure this is a warning
        else:
            self.logger.critical(self.process.after.decode('utf-8'))   # This will probably be something essential

    def create_new_course(self, idnumber, fullname):
        self.command('create_new_course', "{} '{}'".format(idnumber, fullname))

    def create_account(self, username, email, firstname, lastname, idnumber, auth='manual'):
        self.sf.define(username=username, email=email, firstname=firstname, lastname=lastname, idnumber=idnumber, auth=auth)
        to_pass = self.sf("{username} '{email}' '{firstname}' '{lastname}' {idnumber} {auth}")
        self.command('create_account', to_pass)

    def create_group_for_course(self, course_id, group_name):
        self.command('create_group_for_course {} {}'.format(course_id, group_name))

    def create_inactive_account(self, username, email, firstname, lastname, idnumber):
        """
        CREATE A 'SUSPENDED' ACCOUNT (MAKES MORE SENSE TO CALL IT INACTIVE WHEN CREATING IT)
        SIMPLY BY PASSING nologin TO THE FUNCTION
        OTHERWISE, SAME AS create_account
        """
        self.sf.define(username=username, email=email, firstname=firstname, lastname=lastname, idnumber=idnumber)
        to_pass = self.sf("{username} {email} '{firstname}' '{lastname}' {idnumber} nologin")
        self.command('create_account', to_pass)

    def enrol_user_into_course(self, idnumber, shortname, group, role="Student"):
        self.sf.define(idnumber=idnumber, shortname=shortname, group=group, role=role)
        to_pass = self.sf("{idnumber} {shortname} {group} {role}")
        self.command('enrol_user_in_course', to_pass)

    def unenrol_user_from_course(self, idnumber, course):
        self.sf.define(idnumber=idnumber, course=course)
        self.command('deenrol_user_from_course', self.sf('{idnumber} {course}'))

    def add_user_to_cohort(self, useridnumber, cohortidnumber):
        self.sf.define(useridnumber=useridnumber, cohortidnumber=cohortidnumber)
        to_pass = self.sf("{useridnumber} '{cohortidnumber}'")
        self.command('add_user_to_cohort', to_pass)

    def remove_user_from_cohort(self, useridnumber, cohortidnumber):
        self.sf.define(useridnumber=useridnumber, cohortidnumber=cohortidnumber)
        to_pass = self.sf("{useridnumber} '{cohortidnumber}'")
        self.command('remove_user_from_cohort', to_pass)

    def new_cohort(self, cohortidnumber, cohortname):
        self.command("create_cohort {} '{}'".format(cohortidnumber, cohortname))

    def add_user_to_group(self, userid, group_name):
        self.sf.define(userid=userid, group_name=group_name)
        to_pass = self.sf("{userid} '{group_name}'")
        self.command('add_user_to_group', to_pass)

    def remove_user_from_group(self, userid, group_name):
        self.sf.define(userid=userid, group_name=group_name)
        to_pass = self.sf("{userid} '{group_name}'")
        self.command('remove_user_from_group', to_pass)

    def add_group(self, group, course):
        self.sf.define(group=group, course=course)
        to_pass = self.sf("{course} '{group}'")
        self.command('create_group_for_course', to_pass)

    def delete_group(self, group, course):
        self.sf.define(group=group, course=course)
        to_pass = self.sf("{course} '{group}'")
        self.command('delete_group_for_course', to_pass)

    def change_username(self, idnumber, new_name):
        self.command('change_username', "{} {}".format(idnumber, new_name))

    def associate_child_to_parent(self, idnumber, child_idnumber):
        self.command('associate_child_to_parent', "{} {}".format(idnumber, child_idnumber))

    def __del__(self):
        """
        Kill the spawned process
        """
        if self.process.isalive:
            try:
                self.command('QUIT', '')
            except:
                pass



