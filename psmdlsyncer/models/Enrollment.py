"""

"""
from psmdlsyncer.models.Course import Course
from psmdlsyncer.models.Entry import Entry
class Enrollment(Entry):
    def __init__(self, course_number, group_name):
        self.course = course
        self.group = group
    def __repr__(self):
        return self.format_string("{course}:{group}")
