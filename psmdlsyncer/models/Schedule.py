"""
Every Student data type represents a student.
Does context-specific processing
"""
from psmdlsyncer.models.Entry import Entry

class Schedule(Entry):

    def __init__(self, course_number, teacher, studentID):
        self.course_number = course_number
        self.course_teacher = teacher
        self.studentID = studentID
        self._students = []

    def __repr__(self):
        return self.format_string("{first}{course_number}:{studentID}{last}", first="(", last=") ")
