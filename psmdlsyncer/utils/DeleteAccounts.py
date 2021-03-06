from psmdlsyncer.Students import Students, put_in_order
from psmdlsyncer.settings import config
from psmdlsyncer.utils.DB import DragonNetDBConnection
from psmdlsyncer.utils.Formatter import Smartformatter
from collections import defaultdict

if __name__ == "__main__":

    students = Students()
    dnet = DragonNetDBConnection()
    all_ids = dnet.get_all_students_name_ids()
    to_delete = []

    for this_id, username, first, last in all_ids:
        if not this_id:
            continue
        student = students.get_student(this_id)
        if not student and not students.get_teacher(last + ', ' + first):
            to_delete.append( (this_id, username) )

    #for this_id, username in to_delete:
        #print(username + ',deleted')

    parents = dnet.get_all_parent_name_ids()
    for idnumber, username in parents:
        children = students.get_family(idnumber)
        if not children:
            print(username + ',deleted')
