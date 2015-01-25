"""
"""
from psmdlsyncer.models.base import BaseModel
unknown_teacher = "<unknown teacher>"
unknown_course = "<unknown course>"
import re
from psmdlsyncer.utils import NS
from psmdlsyncer.utils import weak_reference

class Group(BaseModel):
    """
    """
    kind = "group"

    def __init__(self, idnumber, course_idnumber, section):
        self.group_id = self.ID = self.name = self.idnumber = idnumber
        self._students = []
        self._teachers = []
        self._course = None
        self.course_idnumber = course_idnumber
        self.section = section

    @property
    def teachers(self):
        return [teacher() for teacher in self._teachers]

    def add_teacher(self, teacher):
        reference = weak_reference(teacher)
        if not reference in self._teachers:
            self._teachers.append( reference )

    def associate(self, course, teacher, student):
        self.add_course(course)
        self.add_teacher(teacher)
        self.add_student(student)

    @property
    def course(self):
        return self._course() if self._course else None

    @property
    def students(self):
        return [student() for student in self._students]

    def add_student(self, student):
        reference = weak_reference(student)
        if not reference in self._students:
            self._students.append( reference )

    def add_course(self, course):
        reference = weak_reference(course)
        self._course = reference

    def __sub__(self, other):
        # groups possibly could have different students involved, but this is picked up in the schedule
        return ()

    def __repr__(self):
        return self.format_string("<Group>: {group_id}")
