from psmdlsyncer.models.base import BaseModel

class CourseMetaData(BaseModel):
    grade_sep = ','

    def __init__(self, idnumber, course_idnumber, course_grade):
        self.idnumber = idnumber
        self.course_idnumber = course_idnumber
        self.course_grade = course_grade

    def __repr__(self):
        return "<CourseMetaData {}>".format(self.idnumber)

    def __str__(self):
        return "<CourseMetaData {}>".format(self.idnumber)
