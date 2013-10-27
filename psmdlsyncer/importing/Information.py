"""
LOOKS AT THE SETTINGS AND DECIDES WHAT TO DO
IMPORTS THE CORRECT CLASSES AND PACKS THE INFO
"""
from psmdlsyncer.files import AutoSendFile
from psmdlsyncer.files import PostFixImport
from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.settings import logging
from psmdlsyncer.sql import ServerInfo
from psmdlsyncer.settings import define_command_line_arguments
from psmdlsyncer.models import Students, Teachers, Courses, Scheduler, Parents, Groups
from psmdlsyncer.utils import NS
from collections import defaultdict
import re

_parents = Parents()
_groups = Groups()
class Tree:
    """
    HOLDS THE MODEL OF THE INFORMATION THAT IS IMPORTED
    TODO: USE ServerInfo OBJECT TO CHECK RECORDS AGAINST DRAGONNET
    """
    exclusion_list = ['Sections, Dead', 'User, Drews Test']
    def __init__(self):
        #TODO: self.user_data = ServerInfo().get_student_info()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._tree = {'families': defaultdict(lambda : defaultdict(list)),
                      'schedule': defaultdict(lambda : defaultdict(list)),
                      'students':{}, 'teachers': {}, 'parents':{},'senior_teachers':{}, 'developers': {},
                      'support_staff':{}, 'courses':{}}
    @property
    def tree(self):
        return self._tree
    @property
    def students(self):
        return self.tree['students']
    @property
    def parents(self):
        return self.tree['parents']
    def families(self):
        return self.tree['families']
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
        RETURNS AN ITERABLE LIST OF ALL KEYS
        (AS LONG AS THE OBJECT HAS AN id FIELD)
        """
        result = {}
        for key in self.tree:
            for item in self.tree[key]:
                this = self.tree[key][item]
                if hasattr(this, 'ID'):
                    result[item] = this
        for key in result:
            yield result[key]
    def add_student(self, student):
        self.students[student.ID] = student
        self.parents[student.family_id] = _parents.make(student)
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
        if "Lab" in course.name:
            # TODO: Make this a setting somewhere
            # TODO: Also make it a regex, because there may be a course someday named "Labortory studies"
            # and that would break this
            return
        self.courses[course.ID] = course
    def add_support_staff(self, staff):
        self.support_staff[staff.ID] = staff
    def add_schedule(self, schedule):
        """
        TAKES THE RAW INFORMATION IN SCHEDULE AND UPDATES THE FIELDS FOR ALL
        THE INSTANCES
        """
        # setup, group is the only previously unknown in this instance
        teacher = self.get_teacher(schedule.teacher_id)
        student = self.get_student(schedule.student_id)
        if not student:
            self.logger.warning("This student is listed in bell schedule but not in the roster: {}"
                                .format(schedule))
            return
        parent = self.get_parent_of_student(student)
        course = self.get_course(schedule.course_id)
        if not course:
            # course must have been excluded from creation, probably not a problem
            self.logger.info("Course associated with student {} in schedule ".format(schedule.student_id) + \
                             "but excluded from creation internally: {}".format(schedule.course_id))
            return
        group = _groups.make(course, teacher)
        # parent is handled by adding the student, everything is derived from the student
        # teacher
        teacher.add_student(student)
        teacher.add_parent(parent)
        teacher.add_course(course)
        teacher.add_group(group)
        # student
        if student:
            student.add_teacher(teacher)
            student.add_course(course)
            student.add_group(group)
        # course
        course.add_student(student)
        course.add_parent(parent)
        course.add_teacher(teacher)
        course.add_group(group)
        
    def get(self, key):
        """
        LOOKS IN ALL OF THEM
        """
        return self.ALL[zkey]
    def get_student(self, key):
        return self.students.get(key)
    def get_parent_of_student(self, student):
        if not student:
            return None
        return self.parents.get(student.family_id)
    def get_teacher(self, key):
        return self.teachers.get(key)
    def get_support_staff(self, key):
        return self.support_staff.get(key)
    def get_course(self, key):
        return self.courses.get(key)
    def output(self):
        for kind in self.tree:
            for ID in self.tree[kind]:
                ns = NS(kind=kind,
                             id=ID, obj=self.tree[kind][ID])
                print(ns("{kind}{TAB}{id}{TAB}{obj}))"))

class AbstractClass:
    """
    DEFINES THE THINGS WE NEED COMMON TO ALL
    """
    def __init__(self):
        self._tree = Tree()
    def init(self):
        students = Students()
        teachers = Teachers()
        courses = Courses()
        scheduler = Scheduler()
        for student in self.student_info.content():
            self.add(students.make(*student))
        for teacher in self.teacher_info.content():
            self.add(teachers.make(*teacher))
        for course in self.course_info.content():
            self.add(courses.make(*course))
        for schedule in self.schedule_info.content():
            self.add(scheduler.make(*schedule))
    def make_ns(self, *args, **kwargs):
        return NS(*args, **kwargs)
    @property
    def tree(self):
        return self._tree
    def add(self, obj):
        if obj is None:
            return
        # determine the routine to dispatch to, get the attribute, and call it
        dispatch = 'add_' + obj.kind
        add_method = getattr(self.tree, dispatch)
        add_method(obj)
    def get(self, key):
        return self.tree.get(key)    
    def output(self):
        self.tree.output()

class NoClass:
    def __init__(self, *args, **kwargs):
        pass

class InfoController(AbstractClass):
    """
    PROVIDES HIGHER LEVEL ROUTINES THAN AVAILABLE IN TREE
    EX) DEFINES DIFFERENCES
    """
    klass = NoClass
    def __init__(self):
        super().__init__()
        self.student_info = self.klass('dist', 'studentinfo')
        self.teacher_info = self.klass('dist', 'staffinfo')
        self.course_info = self.klass('sec', 'courseinfo')
        self.allocations_info = self.klass('sec', 'teacherallocations')
        self.schedule_info = self.klass('sec', 'studentschedule')
        self.init()

    @property
    def families(self):
        pass
    def get_family_emails(self, family_id):
        parent = self.tree.family

    @property
    def groups(self):
        """ TODO: LOOK INSIDE ENROLLMENTS """
        pass

    @property
    def grades(self):
        """ TODO: students? """
        pass

    @property
    def students(self):
        for student in self.tree.students:
            yield self.tree.students[student]

    @property
    def teachers(self):
        for teacher in self.tree.teachers:
            yield self.tree.teachers[teacher]

    @property
    def parents(self):
        for parent in self.tree.parents:
            yield self.tree.parents[parent]

    @property
    def secondary_students(self):
        for person in self.tree.students:
            student = self.tree.students[student]
            if student.is_secondary:
                yield student

    @property
    def elementary_students(self):
        for person in self.tree.students:
            student = self.tree.students[student]
            if student.is_elementary:
                yield student

    def get_any_startswith(self, id):
        return [person for person in self.tree.ALL \
                if hasattr(person, 'ID') and person.ID.startswith(id)]

    def get_one(self, id):
        """ RETURN THE ONE THAT HAS ID == ID """
        for person in self.tree.ALL:
            if person.ID == id:
                return person

    def student_from_ID(self, id):
        """ RETURN THE ONE THAT HAS ID == ID """
        return self.tree.students.get(id)

    def differences(self, other):
        """
        FIRST CHECKS OUT DIFFERENCES IN KEYS
        """
        left = self.tree.students.keys()
        right = other.tree.students.keys()
        for student_id in left - right:
            ns = NS(status='new_student')
            ns.left = self.tree.students.get(student_id)
            ns.right = None
            ns.param = [self.tree.students.get(student_id)]
            yield ns
        for student_id in right - left:
            ns = NS(status='departed_student')
            ns.left = None
            ns.right = student_id
            ns.param = [self.tree.students.get(student_id)]
            yield ns

    __sub__ = differences

class AutoSend(InfoController):
    """    
    """
    klass = AutoSendFile
 
class Moodle(InfoController):
    """
    """
    klass = MoodleImport

class PostFix(InfoController):
    klass = PostFixImport

class PowerSchoolDatabase(AbstractClass):
    """
    CONNECT TO SOME DATABASE AND EXTRACT THE TEXT
    """
    pass
if __name__ == "__main__":
    moodle = Moodle()
    autosend = AutoSend()

    for item in autosend - moodle:
        if item.status == 'new_student':
            print(item)
