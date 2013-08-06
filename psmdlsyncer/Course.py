"""
Every Student data type represents a student.
Does context-specific processing
"""
import re
from psmdlsyncer.utils.Dates import get_year_of_graduation
from psmdlsyncer.utils.Utilities import derive_depart, department_heads
from psmdlsyncer.Entry import Entry

class Course(Entry):

    def __init__(self, course_number, course_name, moodle_short, moodle_long, **kwargs):
        self.course_number = course_number
        self.course_name = course_name
        self.moodle_short = moodle_short
        self.department = derive_depart(moodle_short)
        self.heads = department_heads.get(self.department)
        if not self.heads:
            pass
        #print("No head of department???")
        #  print("{} {}".format(self.moodle_short, self.department))
        self.moodle_long = moodle_long
        self._teachers = []

    def update_teachers(self, teach_obj):
        if teach_obj not in self._teachers:
            self._teachers.append(teach_obj.username)

    def teachers(self):
        return self._teachers

    def __repr__(self):
        teacher_txt = ", ".join(self._teachers)
        return self.format_string("{moodle_short} | {teachers}", first="(", mid="| ", last=") ", teachers=teacher_txt)
