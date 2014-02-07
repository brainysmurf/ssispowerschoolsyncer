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

    def __sub__(self, other):
        """
        Should override to describe the behavor of what happens when the instance is on the left side
        of the subtraction (differences)
        Should use the classes' methods for example self.students and self.teachers to access the information
        """
        raise NotImplemented

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

    def init(self):
        # Some of this stuff is pretty magical
        # The self.students, self.teachers, etc objects come from MetaDataStore
        # They actually return the new (or old) object, but we don't care about them here

        self.process_students()
        self.process_teachers()
        self.process_courses()

        self.process_groups()
        self.process_schedules()



if __name__ == "__main__":

    class Test(AbstractTree):
        pass
    class Test2(AbstractTree):
        pass

    assert(Test.students.make('33')  != Test2.students.make('33') )

