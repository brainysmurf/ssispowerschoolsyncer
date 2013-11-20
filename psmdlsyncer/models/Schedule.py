"""
Every Student data type represents a student.
Does context-specific processing
"""
from psmdlsyncer.models.Entry import Entry
from psmdlsyncer.models.Course import Courses
from psmdlsyncer.utils.Utilities import convert_short_long

# Do I really need this 
_courses = Courses()

class Scheduler:
    def make(self, *schedule):
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
        self.course = _courses.make(course_number)
        self.course_number = self.course.ID
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
        return self.format_string("Course: {course_number}, Student:{student_id}, Teacher:{teacher_id}")

    
