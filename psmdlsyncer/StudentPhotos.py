"""

Takes a folder that PowerSchool uses and makes a flat list.
Bascially, PowerSchool's internal student photo format exported out to format Moodle can use.

"""

import os, shutil

path_to_ps_photos = '../photos'
path_to_ps_data   = '../photos/db.txt'

from psmdlsyncer.utils.TextFileReader import TextFileReader

ps_data = TextFileReader(path_to_ps_data)

id_to_num = {}
for item in ps_data.generate():
    id_to_num[item.id] = item.student_number

new_folder = os.path.join(path_to_ps_photos, 'flat')
for folder in os.listdir(path_to_ps_photos):
    if folder.startswith('.'): continue
    inside_folder = os.path.join(path_to_ps_photos, folder)
    if inside_folder.endswith('.txt'): continue
    for this_folder in os.listdir(inside_folder):
        if this_folder.startswith('.'): continue
        target_file = os.path.join(os.path.join(inside_folder, this_folder), 'ph_normal.jpeg')
        try:
            new_name = id_to_num[this_folder] + '.jpg'
        except KeyError:
            print('No student by this ID: {}'.format(this_folder))
            continue
        shutil.copyfile(target_file, os.path.join(new_folder, new_name))
        

