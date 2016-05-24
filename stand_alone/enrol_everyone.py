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