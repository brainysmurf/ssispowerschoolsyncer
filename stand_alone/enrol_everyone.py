from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.models.datastores.autosend import AutoSendTree

if __name__ == "__main__":

    autosend = AutoSendTree()
    autosend.process()
    moodlemod = ModUserEnrollments()

    for student_key in autosend.students.get_keys():

        student = autosend.students.get_key(student_key)
    
        for group in student.groups:
            moodlemod.add_user_to_group(student.idnumber, group.idnumber)

    for teacher_key in autosend.teachers.get_keys():

        teacher = autosend.teachers.get_key(teacher_key)
    
        for group in teacher.groups:
            moodlemod.add_user_to_group(teacher.idnumber, group.idnumber)

    for parent_key in autosend.parents.get_keys():

        parent = autosend.parents.get_key(parent_key)

        for group in parent.groups:
            moodlemod.add_user_to_group(parent.idnumber, group.idnumber)
