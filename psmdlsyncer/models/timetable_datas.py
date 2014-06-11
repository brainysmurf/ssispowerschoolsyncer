from psmdlsyncer.models.base import BaseModel

class TimetableDatas(BaseModel):
    def __init__(self, idnumber, course, teacher, group, student, period_info, active=True):
        self.idnumber = idnumber
        self.course = course
        self.grade = course.grade
        self.group = group
        self.teacher = teacher
        self.student = student
        self.active = active
        self.period_info = period_info

    def __repr__(self):
        return "<TimetableDatas {}>".format(self.idnumber)

    def __str__(self):
        return "<TimetableDatas {}>".format(self.idnumber)
