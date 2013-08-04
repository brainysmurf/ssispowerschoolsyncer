import subprocess
from psmdlsyncer.utils.Formatter import Smartformatter
from psmdlsyncer.settings import config_get_section_attribute, verbosity

class CallPHP:
    """
    Implements common functions
    Serves as gateway to php functions available in moodle, makes available to Python
    """
    def __init__(self):
        #TODO: Get this info from standard settings and config
        self.sf = Smartformatter()
        self.verbose = verbosity('CallPHP')
        self.dry_run = config_get_section_attribute('DEFAULTS', 'dry_run')
        self.path_to_cli = config_get_section_attribute('MOODLE', 'path_to_cli')
        self.path_to_php = config_get_section_attribute('MOODLE', 'path_to_php')
        self.email_accounts = config_get_section_attribute('EMAIL', 'check_accounts')
        self.moodle_accounts = config_get_section_attribute('MOODLE', 'sync')

    def command(self, routine, cmd):
        self.sf(php_path=self.path_to_php, routine=routine, space=" ")
        cmd = self.sf('{php_path} phpclimoodle.php {routine}{space}' ) + cmd
        if not self.dry_run:
            self.verbose and print('Calling using Popen: ' + cmd)
            p = subprocess.Popen( cmd,
                              shell=True, stdout=subprocess.PIPE, cwd=self.path_to_cli)
            result = p.communicate()
            self.verbose and print(result)
            return result
        else:
            print("Command sent in to CallPHP: {}".format(cmd))

    def create_account(self, username, email, firstname, lastname, idnumber):
        self.sf(username=username, email=email, firstname=firstname, lastname=lastname, idnumber=idnumber)
        to_pass = self.sf("{username} {email} '{firstname}' '{lastname}' {idnumber}")
        if self.moodle_accounts:
            return self.command('create_account', to_pass)
        else:
            return "Dry run enabled: create_account {}".format(to_pass)

    def enrol_user_in_course(self, idnumber, shortname, group, role="Student"):
        self.sf(idnumber=idnumber, shortname=shortname, group=group, role=role)
        to_pass = self.sf("{idnumber} {shortname} {group} {role}")
        if self.moodle_accounts:
            return self.command('enrol_user_in_course', to_pass)
        else:
            return "Dry run enabled: enrol_user_in_course {}".format(to_pass)

    def add_user_to_cohort(self, useridnumber, cohortidnumber):
        self.sf(useridnumber=useridnumber, cohortidnumber=cohortidnumber)
        to_pass = self.sf("{useridnumber} '{cohortidnumber}'")
        if self.moodle_accounts:
            self.verbose and print('Command: add_user_to_cohort {}'.format(to_pass))
            return self.command('add_user_to_cohort', to_pass)
        else:
            return "Dry run enabled: add_user_to_cohort {}".format(to_pass)

    def remove_user_from_cohort(self, useridnumber, cohortidnumber):
        self.sf(useridnumber=useridnumber, cohortidnumber=cohortidnumber)
        to_pass = self.sf("{useridnumber} '{cohortidnumber}'")
        if self.moodle_accounts:
            return self.command('remove_user_from_cohort', to_pass)
        else:
            return "Dry run enabled: add_user_to_cohort {}".format(to_pass)

    def add_user_to_group(self, userid, group_name):
        self.sf(userid=userid, group_name=group_name)
        to_pass = self.sf("{userid} '{group_name}'")
        if self.moodle_accounts:
            return self.command('add_user_to_group', to_pass)
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
