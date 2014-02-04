import subprocess
from psmdlsyncer.utils import NS
from psmdlsyncer.settings import config_get_section_attribute, logging

class CallPHP:
    """
    Implements common functions
    Serves as gateway to php functions available in moodle, makes available to Python
    """
    def __init__(self):
        #TODO: Get this info from standard settings and config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sf = NS()
        self.dry_run = config_get_section_attribute('DEFAULTS', 'dry_run')
        self.path_to_cli = config_get_section_attribute('MOODLE', 'path_to_cli')
        self.path_to_php = config_get_section_attribute('MOODLE', 'path_to_php')
        if not self.path_to_php:
            self.path_to_php = '/usr/bin/php'
        self.email_accounts = config_get_section_attribute('EMAIL', 'check_accounts')
        self.moodle_accounts = config_get_section_attribute('MOODLE', 'sync')

    def command(self, routine, cmd):
        self.sf.define(php_path=self.path_to_php, routine=routine, space=" ")
        cmd = self.sf('{php_path} phpclimoodle.php {routine}{space}' ) + cmd
        if not self.dry_run:
            self.logger.debug('Calling using Popen: ' + cmd)
            p = subprocess.Popen( cmd,
                              shell=True, stdout=subprocess.PIPE, cwd=self.path_to_cli)
            result = p.communicate()
            # MAKE SURE TO LOG IT IF THERE IS SOME MESSAGE
            if len(result) > 1 and result[1]:
                self.logger.warn(result)
            return result
        else:
            return "Dry run enabled: {}".format(cmd)

    def create_account(self, username, email, firstname, lastname, idnumber, auth='manual'):
        self.sf.define(username=username, email=email, firstname=firstname, lastname=lastname, idnumber=idnumber, auth=auth)
        to_pass = self.sf("{username} {email} '{firstname}' '{lastname}' {idnumber} {auth}")
        if self.moodle_accounts:
            return self.command('create_account', to_pass)
        else:
            return "Dry run enabled: create_account {}".format(to_pass)

    def create_inactive_account(self, username, email, firstname, lastname, idnumber):
        """
        CREATE A 'SUSPENDED' ACCOUNT (MAKES MORE SENSE TO CALL IT INACTIVE WHEN CREATING IT)
        SIMPLY BY PASSING nologin TO THE FUNCTION
        OTHERWISE, SAME AS create_account
        """
        self.sf.define(username=username, email=email, firstname=firstname, lastname=lastname, idnumber=idnumber)
        to_pass = self.sf("{username} {email} '{firstname}' '{lastname}' {idnumber} nologin")
        if self.moodle_accounts:
            return self.command('create_account', to_pass)
        else:
            return "Moodle updating disabled: create_account {}".format(to_pass)

    def enrol_user_in_course(self, idnumber, shortname, group, role="Student"):
        self.sf.define(idnumber=idnumber, shortname=shortname, group=group, role=role)
        to_pass = self.sf("{idnumber} {shortname} {group} {role}")
        if self.moodle_accounts:
            return self.command('enrol_user_in_course', to_pass)
        else:
            return "Dry run enabled: enrol_user_in_course {}".format(to_pass)

    def unenrol_user_from_course(self, idnumber, course):
        self.sf(idnumber=idnumber, course=course)
        if self.moodle_accounts:
            return self.command('deenrol_user_in_course', self.sf('{idnumber} {course}'))
        else:
            return "Dry run enabled: deenrol_user_in_course".format(to_pass)

    def add_user_to_cohort(self, useridnumber, cohortidnumber):
        self.sf.define(useridnumber=useridnumber, cohortidnumber=cohortidnumber)
        to_pass = self.sf("{useridnumber} '{cohortidnumber}'")
        if self.moodle_accounts:
            return self.command('add_user_to_cohort', to_pass)
        else:
            return "Dry run enabled: add_user_to_cohort {}".format(to_pass)

    def remove_user_from_cohort(self, useridnumber, cohortidnumber):
        self.sf.define(useridnumber=useridnumber, cohortidnumber=cohortidnumber)
        to_pass = self.sf("{useridnumber} '{cohortidnumber}'")
        if self.moodle_accounts:
            return self.command('remove_user_from_cohort', to_pass)
        else:
            return "Dry run enabled: add_user_to_cohort {}".format(to_pass)

    def add_user_to_group(self, userid, group_name):
        self.sf.define(userid=userid, group_name=group_name)
        to_pass = self.sf("{userid} '{group_name}'")
        if self.moodle_accounts:
            return self.command('add_user_to_group', to_pass)
        else:
            return "Dry run enabled: add_user_to_group ".format(to_pass)

    def remove_user_from_group(self, userid, group_name):
        self.sf.define(userid=userid, group_name=group_name)
        to_pass = self.sf("{userid} '{group_name}'")
        if self.moodle_accounts:
            return self.command('remove_user_from_group', to_pass)
        else:
            return "Dry run enabled: add_user_to_group ".format(to_pass)

    def shell(self, command):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        return p.communicate()

    def change_username(self, idnumber, new_name):
        return self.command('change_username', "{} {}".format(idnumber, new_name))

    def associate_child_to_parent(self, idnumber, child_idnumber):
        return self.command('associate_child_to_parent', "{} {}".format(idnumber, child_idnumber))

class PowerSchoolIntegrator(CallPHP):
    pass

if __name__ == "__main__":

    p = PowerSchoolIntegrator()

    print(p.add_user_to_group('32352', 'darkosaboMATST10'))
