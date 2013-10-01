"""
Every Student data type represents a student.
Does context-specific processing
"""
import re
from psmdlsyncer.utils.Dates import get_year_of_graduation
from psmdlsyncer.models.Entry import Entry

class Allocation(Entry):

    def __init__(self, course_number, teacher):
        self.course_number = course_number
        self.course_teacher = teacher

    def __repr__(self):
        return self.format_string("{first}{course_number}:{studentID}{last}", first="(", last=") ")
