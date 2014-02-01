"""
Every Student data type represents a student.
Does context-specific processing
"""
import re
from psmdlsyncer.utils.Dates import get_year_of_graduation
from psmdlsyncer.utils.Utilities import derive_depart, department_heads
from psmdlsyncer.utils import weak_reference
from psmdlsyncer.models.Entry import Entry
from psmdlsyncer.utils.Utilities import convert_short_long

class Courses:
    def __init__(self, convert_course=True):
        """
        convert_course IS USED IN ORDER TO TELL THE CLASS WHETHER OR NOT
        CONVERSION USING convert_short_long IN UTILS/UTILTIIES.PHP
        THIS IS NECESSARY BECAUSE THERE IS NOT A 1:1 COORESPONDANCE
        BETWEEN COURSES IN POWERSCHOOL AND IN MOODLE
        """
        self._courses = {}
        self.convert_course = convert_course

    def make(self, *course):
        course_id = course[0]
        if course_id in self._courses:
            return self._courses[course_id]
        else:
            course = Course(*course, convert_course=self.convert_course)
            self._courses[course_id] = course
            return course

class Course(Entry):
    kind = "course"

    def __init__(self, course_id, course_name="", convert_course=True):
        if convert_course:
            self.ID, self.name = convert_short_long(course_id, course_name)
        else:
            self.ID, self.name = course_id, course_name
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
        if not teacher:
            return
        reference = weak_reference(teacher)
        if not reference in self._teachers:
            self._teachers.append( reference )

    def add_student(self, student):
        reference = weak_reference(student)
        if not reference in self._students:
            self._students.append( reference )

    def add_parent(self, parent):
        reference = weak_reference(parent)
        if not reference not in self._parents:
            self._parents.append( reference )

    def add_group(self, group):
        reference = weak_reference(group)
        if not reference in self._groups:
            self._groups.append( reference )

    @property
    def teachers(self):
        return [teacher() for teacher in self._teachers]

    @property
    def students(self):
        return [student() for student in self._students]

    @property
    def groups(self):
        return [group() for group in self._groups]

    @property
    def parents(self):
        return self._parents

    def __repr__(self):
        teacher_txt = ", ".join([teacher.username for teacher in self.teachers])
        return self.format_string("{ID} ({name}) : {teachers}", first="(", mid="| ", last=") ", teachers=teacher_txt)
