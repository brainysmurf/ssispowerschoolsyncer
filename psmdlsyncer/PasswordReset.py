#/usr/bin/python3

"""
Simply checks to see if there is anything in the queque that is set up, and act on it

Will be run by root so need full paths to everything
"""

import datetime
import subprocess
import os
from psmdlsyncer.utils.Email import Email
from psmdlsyncer.utils.Email import read_in_templates

def system_call(str):
    subprocess.call(str, shell=True)

reset_password_templates = "/home/lcssisadmin/ssispowerschoolsync/templates/password_reset"
path = "/home/lcssisadmin/database_password_reset/reset_password.txt"

if os.path.exists(path):
    email = Email()
    read_in_templates(reset_password_templates, email)
    email.add_language('en')
    email.define_sender('lcssisadmin@student.ssis-suzhou.net')
    email.make_subject('Local Password Reset')
    email.add_to('lcssisadmin@student.ssis-suzhou.net')
    with open(path) as _f:
        print("Resetting the following local password(s):\n{}".format("\n".join(_f.readlines())))
    system_call("/usr/sbin/newusers {}".format(path))
    os.remove(path)
    email.send()

path = "path=/home/lcssisadmin/database_password_reset/dragonnet_reset_password.txt"
if os.path.exists(path):
    email = Email()
    read_in_templates(reset_password_templates, email)
    email.add_language('en')
    email.define_sender('lcssisadmin@student.ssis-suzhou.net')
    email.make_subject('DragonNet Password Reset')
    email.add_to('lcssisadmin@student.ssis-suzhou.net')
    with open(path) as _f:
        print("Resetting the following dragonnet password(s):\n".format("\n".join(_f.readlines())))
    system_call('/usr/bin/php /var/www/moodle/admin/cli/reset_password_changeme_file.php')
    os.remove(path)
    email.send()
