"""
"""
from psmdlsyncer.models.base import BaseModel
unknown_teacher = "<unknown teacher>"
unknown_course = "<unknown course>"
import re
from psmdlsyncer.utils import NS
from psmdlsyncer.utils import weak_reference

class Class(BaseModel):
    """
    """
    kind = "group"

    def __init__(self, idnumber):
        self.change_name(idnumber)
        self._students = []
        self._teachers = []
        self._courses = []

    def change_name(self, new_name):
        self.group_id = self.ID = self.name = self.idnumber = new_name

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
    def courses(self):
        return [course() for course in self._courses]

    def add_course(self, course):
        reference = weak_reference(course)
        if not reference in self._courses:
            self._courses.append( reference )

    @property
    def students(self):
        return [student() for student in self._students]

    def add_student(self, student):
        reference = weak_reference(student)
        if not reference in self._students:
            self._students.append( reference )

    @property
    def courses(self):
        return [course() for course in self._courses]

    def add_course(self, course):
        reference = weak_reference(course)
        if not reference in self._courses:
            self._courses.append( reference )


    def differences(self, other):
        # groups possibly could have different students involved, but this is picked up in the schedule
        return ()

    __sub__ = differences


    def __repr__(self):
        return self.format_string("<Group>: {group_id}")
