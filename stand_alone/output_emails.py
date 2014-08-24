from psmdlsyncer.settings import config, config_get_section_attribute
print('done')
from psmdlsyncer.sql import MoodleDBSession

#import csv

path_to_powerschool = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')
path_to_file = '/home/lcssisadmin/students_email_autocom.csv'

db = MoodleDBSession()

with open(path_to_file, 'w') as _file:
	for student in db.users_enrolled_in_this_cohort('studentsALL'):
		_file.write('{},{},{}\n'.format(student.idnumber, student.username, student.email))

import os
os.chown(path_to_file, 1000, 1000)
