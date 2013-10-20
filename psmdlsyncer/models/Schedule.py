"""
Every Student data type represents a student.
Does context-specific processing
"""
from psmdlsyncer.models.Entry import Entry
from psmdlsyncer.models.Course import CourseFactory
from psmdlsyncer.utils.Utilities import convert_short_long
class ScheduleFactory:
    @classmethod
    def make(cls, *schedule):
        """
        AT THE MOMENT THERE IS NO NEED FOR ANY CODE HERE
        """
        return Schedule(*schedule)

class Schedule(Entry):
    """
    REALLY JUST MOSTLY A NAMESPACE
    """
    def __init__(self, course_number, course_name, periods, teacher, teacherID, student, studentID):
        self.original_course_number = course_number
        self.course = CourseFactory.make(course_number)
        self.kind = 'schedule'
        self.student_family_id = studentID[:4] + 'P'
        self.periods = periods
        self.teacher = teacher
        self.teacher_id = teacherID
        self.student_id = studentID
        self.student = student

    @property
    def course_id(self):
        return self.course.course_id

    def __repr__(self):
        return self.format_string("{course_number}:{student}")
