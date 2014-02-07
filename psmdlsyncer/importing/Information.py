"""
LOOKS AT THE SETTINGS AND DECIDES WHAT TO DO
IMPORTS THE CORRECT CLASSES AND PACKS THE INFO
"""

from psmdlsyncer.settings import logging
from psmdlsyncer.sql import ServerInfo
from psmdlsyncer.settings import define_command_line_arguments
from psmdlsyncer.models.datastores import MetaDataStore
from psmdlsyncer.utils import NS
from collections import defaultdict
import re

class TeacherWrapper:
    def __init__(self, username):
        self.username = username
        self.wrapped = Teacher('', ' , ', username + '@', '', '', '1')

    def __call__(self):
        return self.wrapped

    def __str__(self):
        return str(self.wrapped)

    def __repr__(self):
        return str(self.wrapped)

def add_link(left, right):
    """
    Wrapper function that calls the add_<x> method on left passing right as a parameter
    """
    if not left:
        # Can add some dugging tool here if necessary
        return
    if not right:
        # Can add some debugging tool here if necessary
        return
    right_kind = right.kind
    method = getattr(left, "add_{}".format(right_kind))
    method(right)



class BaseInformation(MetaDataStore):
    """
    DEFINES THE THINGS WE NEED COMMON TO ALL
    """
    convert_course = True   # by default, convert the course shortname

    def init(self):
        # Some of this stuff is pretty magical
        # The self.students, self.teachers, etc objects come from MetaDataStore
        # They actually return the new (or old) object, but we don't care about them here

        for student in self.student_info.content():
            self.students.make(*student)
        for teacher in self.teacher_info.content():
            self.teachers.make(*teacher)
        for group in self.group_info.content():
            self.groups.make(*group)
        for course in self.course_info.content():
            if self.convert_course:
                self.courses.make_with_conversion(*course)
            else:
                self.courses.make_without_conversion(*course)
        for schedule in self.schedule_info.content():
            schedules.make(*schedule)

    def make_ns(self, *args, **kwargs):
        return NS(*args, **kwargs)

    def process_student(self, student):
        self.students[student.ID] = student
        self.parents[student.family_id] = _parents.make(student)
        self.process_student_to_family(student)
        self.process_parent_to_family(student.family_id)

    def process_student_to_family(self, student):
        self.tree['families'][student.family_id]['children'].append(student)

    def process_teacher_to_family(self, teacher):
        self.tree['families'][teacher.family_id]['teacher'].append(teacher)

    def process_parent_to_family(self, family_id):
        self.tree['families'][family_id]['parent'].append(family_id)

    def process_teacher(self, teacher):
        self.teachers[teacher.ID] = teacher
        self.process_teacher_to_family(teacher)

    def process_group(self, group):
        input(group)

    def process_course(self, course):
        if "Lab" in course.name:
            # TODO: Make this a setting somewhere
            # TODO: Also make it a regex, because there may be a course someday named "Labortory studies"
            # and that would break this
            return
        self.courses[course.ID] = course

    def process_support_staff(self, staff):
        self.support_staff[staff.ID] = staff

    def process_schedule(self, schedule):
        """
        TAKES THE RAW INFORMATION IN SCHEDULE AND UPDATES THE FIELDS FOR ALL
        THE INSTANCES
        """
        # setup, group is the only previously unknown in this instance
        if schedule.group_name:
            teacher_username = re.sub(r'[^a-z]', '', schedule.group_name)
            teacher = self.get_teacher_from_username(teacher_username)
            if not teacher:
                # a teacher of status 1 with the username, enough to get us a decent group, eh?
                teacher = Teacher('', ' , ', teacher_username + '@', '', '', '1')
            schedule.setup_teacher(teacher)
        else:
            teacher = self.get_teacher(schedule.teacher_id)

        student = self.students.make(schedule.student_id)
        parent = self.parents.make(student.family_id)
        course = self.courses.make(schedule.course_id)
        group = self.groups.make(course, teacher)

        # Set up schedule, now that we know a bit more
        #schedule.setup_student(student)
        #schedule.setup_teacher(teacher)
        #schedule.setup_group(group)

        # parent is handled by adding the student, everything is derived from the student
        add_link(student, teacher)
        add_link(student, course)
        add_link(student, group)
        add_link(student, schedule)
    
        add_link(teacher, student)
        add_link(teacher, parent)
        add_link(teacher, course)
        add_link(teacher, group)
        
        add_link(course, student)
        add_link(course, parent)
        add_link(course, teacher)
        add_link(course, group)


class NoClass:
    def __init__(self, *args, **kwargs):
        pass

class InfoController(BaseInformation):
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
        self.group_info = self.klass('sec', 'groups')
        self.schedule_info = self.klass('sec', 'studentschedule')
        self.init()


    def differences(self, other):
        """
        FIRST CHECKS OUT DIFFERENCES IN KEYS
        """
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

    __sub__ = differences




if __name__ == "__main__":

    moodle = Moodle()

