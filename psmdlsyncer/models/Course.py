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
    def __init__(self, course_id, course_name):
        self.ID, self.name = convert_short_long(course_id, course_name)
        self.kind = 'course'
        self.course_id = course_id = self.ID
        self.department = derive_depart(self.name)
        self.heads = department_heads.get(self.department)
        if not self.heads:
            pass
        self._teachers = []
        self._students = []
        self._groups = []
        self._parents = []
    def add_teacher(self, teacher):
        if teacher.ID not in self._teachers:
            self._teachers.append(teacher.ID)
    def add_student(self, student):
        if not student:
            return
        if student.ID not in self._students:
            self._students.append(student.ID)
    def add_parent(self, parent):
        if not parent:
            return
        if parent.ID not in self._parents:
            self._parents.append(parent.ID)
    def add_group(self, group):
        if group.ID not in self._groups:
            self._groups.append(group.ID)
    @property
    def teachers(self):
        return self._teachers
    @property
    def students(self):
        return self._students
    @property
    def groups(self):
        return self._groups
    @property
    def parents(self):
        return self._parents
    def __repr__(self):
        teacher_txt = ", ".join(self._teachers)
        return self.format_string("{ID} ({name}) : {teachers}", first="(", mid="| ", last=") ", teachers=teacher_txt)
