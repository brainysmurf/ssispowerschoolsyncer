from psmdlsyncer.models.datastores.autosend import AutoSendTree
from psmdlsyncer.db import DBSession
from psmdlsyncer.db.MoodleDB import User

# moodle = MoodleTree()
powerschool = AutoSendTree()

# moodle.process()
powerschool.process()

with DBSession() as session:
    for teacher in session.query(User).filter(User.idnumber.like('%x%')):
        correct_teacher = powerschool.teachers.get_from_attribute('username', teacher.username)
        if correct_teacher:
            teacher.idnumber = correct_teacher.idnumber
            input(teacher.username)

    for teacher in session.query(User).filter(User.idnumber == ''):
        correct_teacher = powerschool.teachers.get_from_attribute('username', teacher.username)
        if correct_teacher:
            teacher.idnumber = correct_teacher.idnumber
            input(teacher.username)
