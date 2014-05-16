"""

Takes a folder that PowerSchool uses and makes a flat list.
Bascially, PowerSchool's internal student photo format exported out to format Moodle can use.

"""

import os, shutil
from psmdlsyncer.models.datastores.autosend import AutoSendTree

# who knows where this might be, so let's not use settings.ini for this
# TODO: make this a command line argument

teacher_data = AutoSendTree()
id_cache = {}

for teacher in teacher_data.teachers.get_objects():
    id_cache[teacher.database_id] = teacher.idnumber

path_to_ps_photos = '../../powerschool/photos/faculty'

new_folder = os.path.join(path_to_ps_photos, 'flat')
for folder in os.listdir(path_to_ps_photos):
    if folder.startswith('.'): continue
    inside_folder = os.path.join(path_to_ps_photos, folder)
    if inside_folder.endswith('.txt'): continue
    for this_folder in os.listdir(inside_folder):
        if this_folder.startswith('.'): continue
        target_file = os.path.join(os.path.join(inside_folder, this_folder), 'ph_normal.jpeg')
        try:
            new_name = id_cache[this_folder] + '.jpg'
        except KeyError:
            print('No teacher by this ID: {}'.format(this_folder))
            continue
        shutil.copyfile(target_file, os.path.join(new_folder, new_name))


