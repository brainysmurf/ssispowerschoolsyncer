from psmdlsyncer.utils import NS
from psmdlsyncer.models.parent import Parent
from psmdlsyncer.models.teacher import Teacher
from psmdlsyncer.models.student import Student
from psmdlsyncer.models.group import Group
from psmdlsyncer.models.course import Course
from psmdlsyncer.models.schedule import Schedule
from psmdlsyncer.utils.Utilities import convert_short_long

import logging
log = logging.getLogger(__name__)
import re

class AbstractTree():
    convert_course = True   # by default, convert the course shortname

    def __init__(self):
        super().__init__()
        self.student_info = self.klass('dist', 'studentinfo')
        self.teacher_info = self.klass('dist', 'staffinfo')
        self.course_info = self.klass('sec', 'courseinfo')
        self.allocations_info = self.klass('sec', 'teacherallocations')
        self.group_info = self.klass('sec', 'groups')
        self.schedule_info = self.klass('sec', 'studentschedule')
        self.init()

    @classmethod
    def get_students(cls):
        return cls._store[cls.__name__]

    @staticmethod
    def derive_group_idnumber(teacher, course):
        return "{}{}".format(teacher.username, course.idnumber)

    @staticmethod
    def derive_schedule_idnumber(student, teacher, course):
        return "{}.{}.{}".format(student and student.idnumber or "", teacher and teacher.idnumber or "", course and course.idnumber or "")

    def init(self):
        self.process_students()
        self.process_teachers()
        self.process_courses()

        self.process_groups()
        self.process_schedules()

    def process_students(self):
        for student in self.student_info.content():
            self.students.make(*student)

    def process_teachers(self):
        for teacher in self.teacher_info.content():
            self.teachers.make(*teacher)     

    def process_courses(self):
        for course in self.course_info.content():
            if self.convert_course:
                self.courses.make_with_conversion(*course)
            else:
                self.courses.make_without_conversion(*course)

    def process_groups(self):
        for group in self.group_info.content():
            self.groups.make(*group)

    def process_secheule(self):
        # no good standard way to do this, quite yet
        pass


    def __sub__(self, other):
        """

        """
        input('yay')
        left = self.tree.students.keys()
        right = other.tree.students.keys()

        for student_id in right - left:
            ns = NS(status='new_student')
            ns.left = self.tree.students.get(student_id)
            ns.right = other.tree.students.get(student_id)
            ns.param = [ns.right]
            yield ns

        for student_id in left - right:
            ns = NS(status='old_student')
            ns.left = self.tree.students.get(student_id)
            ns.right = other.tree.students.get(student_id)
            ns.param = [ns.left]
            yield ns

        left = self.tree.teachers.keys()
        right = other.tree.teachers.keys()

        for teacher_id in right - left:
            ns = NS(status='new_teacher')
            ns.left = self.tree.teachers.get(teacher_id)
            ns.right = other.tree.teachers.get(teacher_id)
            ns.param = [ns.right]
            yield ns

        for teacher_id in left - right:
            ns = NS(status='old_teacher')
            ns.left = self.tree.teachers.get(teacher_id)
            ns.right = other.tree.teachers.get(teacher_id)
            ns.param = [ns.left]
            yield ns

        # Now look at the individual information.
        for student_id in self.tree.students.keys():
            left = self.tree.students.get(student_id)
            right = other.tree.students.get(student_id)
            if left and right:
                yield from left - right


    

if __name__ == "__main__":

    class Test(AbstractTree):
        pass
    class Test2(AbstractTree):
        pass

    assert(Test.students.make('33')  != Test2.students.make('33') )

