"""
Every Student data type represents a student.
Does context-specific processing
"""
from psmdlsyncer.models.Entry import Entry
from psmdlsyncer.utils.Utilities import convert_short_long
class Schedule(Entry):
    """
    REALLY JUST MOSTLY A NAMESPACE
    """
    def __init__(self, course_number, course_name, periods, teacher, teacherID, student, studentID):
        self.course_number, self.course_name = convert_short_long(course_number, course_name)
        self.course_id = self.course_number
        self.kind = 'schedule'
        self.student_family_id = studentID[:4] + 'P'
        self.periods = periods
        self.teacher = teacher
        self.teacher_id = teacherID
        self.student_id = studentID
        self.student = student

    def __repr__(self):
        return self.format_string("{course_number}:{student}")
