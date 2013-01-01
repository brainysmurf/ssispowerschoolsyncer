import subprocess
from utils.Formatter import Smartformatter
from utils.Utilities import on_server
class CallPHP:
    """
    Implements common functions
    Serves as gateway to php functions available in moodle, makes available to Python
    """
    def __init__(self):
        self.sf = Smartformatter()
        self.on_server = on_server
        
    def command(self, routine, cmd):
        self.sf(routine=routine, space=" ")
        cmd = self.sf('/usr/bin/php phpclimoodle.php {routine}{space}' ) + cmd
        if self.on_server:
            p = subprocess.Popen( cmd,
                              shell=True, stdout=subprocess.PIPE, cwd="/var/www/moodle/admin/cli")
            result = p.communicate()
            print(result)
            return result
        else:
            print(cmd)

    def create_account(self, username, email, firstname, lastname, idnumber):
        self.sf(username=username, email=email, firstname=firstname, lastname=lastname, idnumber=idnumber)
        return self.command('create_account', self.sf("{username} {email} '{firstname}' '{lastname}' {idnumber}"))

    def enrol_user_in_course(self, idnumber, shortname, group, role="Student"):
        self.sf(idnumber=idnumber, shortname=shortname, group=group, role=role)
        return self.command('enrol_user_in_course', self.sf("{idnumber} {shortname} {group} {role}"))

    def add_user_to_cohort(self, useridnumber, cohort_name):
        self.sf(useridnumber=useridnumber, cohort_name=cohort_name)
        return self.command('add_user_to_cohort', self.sf("{useridnumber} '{cohort_name}'"))

    def add_user_to_group(self, userid, group_name):
        self.sf(userid=userid, group_name=group_name)
        return self.command('add_user_to_group', self.sf("{userid} '{group_name}'"))

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
