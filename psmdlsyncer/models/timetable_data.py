from psmdlsyncer.models.base import BaseModel

class TimetableDatas(BaseModel):
    def __init__(self, idnumber, course, teacher, group, student, section_number, period_info, active=True):
        self.idnumber = idnumber
        self.course = course
        self.grade = course.grade
        self.group = group
        self.section = section_number
        self.teacher = teacher
        self.student = student
        self.period_info = period_info
        self.active = active

    def __repr__(self):
        return "<TimetableDatas {}>".format(idnumber)

    def __str__(self):
        return "<TimetableDatas {}>".format(idnumber)
