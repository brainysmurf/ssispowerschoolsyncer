"""
Every Student data type represents a student.
Does context-specific processing
"""
import re
from psmdlsyncer.models.Entry import Entry
from psmdlsyncer.models.Course import Courses
from psmdlsyncer.utils.Utilities import convert_short_long

_courses = Courses()

class Scheduler:
    def __init__(self, convert=True):
        self.convert = convert

    def make(self, *schedule):
        """
        AT THE MOMENT THERE IS NO NEED FOR ANY CODE HERE
        """
        return Schedule(*schedule, convert=self.convert)

class Schedule(Entry):
    """
    REALLY JUST MOSTLY A NAMESPACE
    """
    kind = 'schedule'

    def __init__(self, course_number, course_name, periods, teacher_lastfirst, teacherID, student, studentID, group_name=None, convert=True):        
        """
        group_name param indicates that we don't have the teacher info but to derive that from the group name
        """
        self.original_course_number = course_number
        if convert:
            self.course = _courses.make_with_conversion(course_number, course_name)
        else:
            self.course = _courses.make_without_conversion(course_number, course_name)

        self.group = None
        self.teacher = None
        self.student = None
        self.course_number = self.course.ID
        self.student_family_id = studentID[:4] + 'P'
        self.periods = periods
        self.teacher_lastfirst = teacher_lastfirst
        self.teacher_id = teacherID
        self.student_id = studentID
        self.student = student
        self.group_name = group_name
        self.calculate_ID()
        self.ID = self.idnumber = self.student_id + self.teacher_id + self.course_number

    def setup_teacher(self, teacher):
        if teacher:
            self.teacher = teacher
            self.teacher_id = teacher.idnumber
            self.calculate_ID()

    def setup_student(self, student):
        if student:
            self.student = student
            self.student_id = student.idnumber
            self.calculate_ID()

    def setup_group(self, group):
        if group:
            self.group = group
            self.group_name = group.name

    def calculate_ID(self):
        self.ID = self.idnumber = self.student_id + self.teacher_id + self.course_number

    @property
    def course_id(self):
        return self.course.course_id

    def __repr__(self):
        return self.format_string("<Schedule: {course_number}, Student:{student_id}, Teacher:{teacher_id}>")

    def __hash__(self):
        return hash(self.ID)

    def __eq__(self, other):
        return self.ID == other.ID
    
