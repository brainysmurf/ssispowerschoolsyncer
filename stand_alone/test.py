from psmdlsyncer.settings import config, config_get_section_attribute
print('done')

import csv

path_to_students = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')
path_to_students += '/ssis_dist_studentinfo_v4.0'

with open(path_to_students) as _file:
    readin = csv.reader(_file, delimiter='\t')
    for line in readin:
        print(line)