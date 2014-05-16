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
    id_cache[teacher.fullname] = teacher.idnumber

path_to_ps_photos = '/Users/adammorris/Desktop/staffphotos'

new_folder = os.path.join(path_to_ps_photos, 'flat')
for this_file in os.listdir(path_to_ps_photos):
    if this_file.startswith('.') or this_file == 'flat' or this_file == 'for powerschool': continue
    this_name, ext = this_file.split('.')
    try:
        new_name = id_cache[this_name] + '.jpg'
    except KeyError:
        print('No teacher by this fullname: {}'.format(this_file))
        continue
    shutil.copyfile(os.path.join(path_to_ps_photos, this_file), os.path.join(new_folder, new_name))


