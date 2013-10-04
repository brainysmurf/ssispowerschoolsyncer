"""
LOOKS AT THE SETTINGS AND DECIDES WHAT TO DO
IMPORTS THE CORRECT CLASSES AND PACKS THE INFO
"""
from psmdlsyncer.utils import NS
from copy import copy
from psmdlsyncer.files import AutoSendFile
from psmdlsyncer.models import Student, Teacher, Course, Schedule2, Enrollment
from collections import defaultdict
import re

class Tree:
    """
    HOLDS THE MODEL OF THE INFORMATION THAT IS IMPORTED
    """
    def __init__(self):
        self._tree = {'families': defaultdict(lambda : defaultdict(list)),  # nested defaultdict
                      'schedule': defaultdict(lambda : defaultdict(list)),
                      'students':{}, 'teachers': {}, 'senior_teachers':{}, 'developers': {},
                      'support_staff':{}, 'courses':{}}
    @property
    def tree(self):
        return self._tree
    @property
    def students(self):
        return self.tree['students']
    @property
    def teachers(self):
        return self.tree['teachers']
    @property
    def support_staff(self):
        return self.tree['support_staff']
    @property
    def courses(self):
        return self.tree['courses']
    @property
    def ALL(self):
        """
        RETURNS THE COMBINATION OF ALL OF THE KEYS
        """
        result = {}
        for key in self.tree:
            result.update(self.tree[key])
        return result

    def add_schedule(self, schedule):
        """
        SETS MOST OF THE INFORMATION
        """
        self.tree['schedule']['teacher_student'][schedule.teacher_id].append(schedule.student_id)
        self.tree['schedule']['student_teacher'][schedule.student_id].append(schedule.teacher_id)
        enrollment = Enrollment(schedule.course_number,
                                self.get_teacher(schedule.teacher_id).username)
        self.tree['schedule']['teacher_enrollment'][schedule.teacher_id] \
                                                             .append(enrollment)
        self.tree['schedule']['student_enrollment'][schedule.teacher_id] \
                                                             .append(enrollment)
        self.tree['schedule']['parent_enrollment'][schedule.student_family_id] \
                                                                   .append(enrollment)
    
    def add_student(self, student):
        self.students[student.ID] = student
        self.add_student_to_family(student)
        self.add_parent_to_family(student.family_id)

    def add_student_to_family(self, student):
        self.tree['families'][student.family_id]['children'].append(student)

    def add_teacher_to_family(self, teacher):
        self.tree['families'][teacher.family_id]['teacher'].append(teacher)

    def add_parent_to_family(self, family_id):
        self.tree['families'][family_id]['parent'].append(family_id)

    def add_teacher(self, teacher):
        self.teachers[teacher.ID] = teacher
        self.add_teacher_to_family(teacher)

    def add_course(self, course):
        self.courses[course.ID] = course

    def add_support_staff(self, staff):
        self.support_staff[staff.ID] = staff

    def get(self, key):
        """
        LOOKS IN ALL OF THEM
        """
        return self.ALL[key]

    def get_student(self, key):
        return self.students.get(key)

    def get_student_like(self, id):
        print(id)
        return [person for person in self.ALL \
                if hasattr(person, 'ID') and person.ID.startswith(id)]

    def get_teacher(self, key):
        return self.teachers.get(key)

    def get_support_staff(self, key):
        return self.support_staff.get(key)

    def output(self):
        for kind in self.tree:
            for ID in self.tree[kind]:
                ns = NS(kind=kind,
                             id=ID, obj=self.tree[kind][ID])
                if ns.kind == 'courses':
                    print(ns("{kind}{TAB}{id}{TAB}{obj}))"))

class AbstractClass:
    """
    DEFINES THE THINGS WE NEED COMMON TO ALL
    """
    def __init__(self):
        self._tree = Tree()
    
    def make_ns(self, *args, **kwargs):
        return NS(*args, **kwargs)

    @property
    def tree(self):
        return self._tree

    def add(self, obj):
        if obj is None:
            return
        if obj.kind == 'student':
            self.tree.add_student(obj)
        elif obj.kind == 'teacher':
            self.tree.add_teacher(obj)
        elif obj.kind == 'course':
            self.tree.add_course(obj)
        elif obj.kind == 'schedule':
            self.tree.add_schedule(obj)
            
    def get(self, key):
        return self.tree.get(key)
    
    def output(self):
        self.tree.output()

class AutoSend(AbstractClass):
    """
    
    """
    def __init__(self):
        super().__init__()
        self.students = AutoSendFile('dist', 'studentinfo')
        self.teachers = AutoSendFile('dist', 'staffinfo')
        self.courses = AutoSendFile('sec', 'courseinfo')
        self.allocations = AutoSendFile('sec', 'teacherallocations')
        self.schedule = AutoSendFile('sec', 'studentschedule')
        self.init()

    def init(self):
        for student in self.students.content():
            self.add(Student(*student))
        for teacher in self.teachers.content():
            self.add(Teacher(*teacher))
        for course in self.courses.content():
            self.add(Course(*course))
        for schedule in self.schedule.content():
            self.add(Schedule2(*schedule))

class PowerSchoolDatabase(AbstractClass):
    """
    CONNECT TO SOME DATABASE AND EXTRACT THE TEXT
    """
    pass


if __name__ == "__main__":

    autosend = True
    powerschool_database = False

    if autosend:
        klass = AutoSend()
    elif powerschool_database:
        klass = PowerSchoolDatabase()

    #klass.output()

    print(klass.tree.get_student_like('4221'))
