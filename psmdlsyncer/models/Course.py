"""
Every Student data type represents a student.
Does context-specific processing
"""
import re
from psmdlsyncer.utils.Dates import get_year_of_graduation
from psmdlsyncer.utils.Utilities import derive_depart, department_heads
from psmdlsyncer.models.Entry import Entry
from psmdlsyncer.utils.Utilities import convert_short_long

class Course(Entry):

    def __init__(self, course_number, course_name, **kwargs):
        self.course_number = course_number
        self.moodle_short, self.moodle_long = convert_short_long(course_number, course_name)
        self.ID = self.moodle_short
        self.kind = 'course'
        self.department = derive_depart(self.moodle_short)
        self.heads = department_heads.get(self.department)
        if not self.heads:
            pass
        #print("No head of department???")
        #  print("{} {}".format(self.moodle_short, self.department))
        self._teachers = []

    def update_teachers(self, teach_obj):
        if teach_obj not in self._teachers:
            self._teachers.append(teach_obj.username)

    def teachers(self):
        return self._teachers

    def __repr__(self):
        teacher_txt = ", ".join(self._teachers)
        return self.format_string("{moodle_short} ({moodle_long}) : {teachers}", first="(", mid="| ", last=") ", teachers=teacher_txt)
