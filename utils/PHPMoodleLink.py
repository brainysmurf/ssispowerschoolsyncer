import subprocess
from utils.Formatter import Smartformatter

class CallPHP:
    """
    Implements common functions
    Serves as gateway to php functions available in moodle, makes available to Python
    """
    def __init__(self,
                 dry_run=True,
                 verbose = True,
                 path_to_cli="",
                 path_to_php="",
                 email_accounts=False,
                 moodle_accounts=False):
        self.sf = Smartformatter()
        self.verbose = verbose
        self.dry_run = dry_run
        self.path_to_cli = path_to_cli
        self.path_to_php = path_to_php
        self.email_accounts = email_accounts
        self.moodle_accounts = moodle_accounts

    def command(self, routine, cmd):
        self.sf(php_path=self.path_to_php, routine=routine, space=" ")
        cmd = self.sf('{php_path} phpclimoodle.php {routine}{space}' ) + cmd
        if not self.dry_run:
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

    def add_user_to_cohort(self, useridnumber, cohort_name):
        self.sf(useridnumber=useridnumber, cohort_name=cohort_name)
        to_pass = self.sf("{useridnumber} '{cohort_name}'")
        if self.moodle_accounts:
            return self.command('add_user_to_cohort', to_pass)
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
