"""
"""
from psmdlsyncer.models.Entry import Entry
unknown_teacher = "<unknown teacher>"
unknown_course = "<unknown course>"
import re
from psmdlsyncer.utils import NS

class Groups:

    def __init__(self):
        self._groups = {}

    def make(self, course, teacher):
        teacher_username = teacher.username if teacher else unknown_teacher
        course_id = course.ID if course else unknown_course
        group_id = teacher_username + course_id
        if group_id in self._groups:
            return self._groups[group_id]
        else:
            group = Group(course, teacher)
            self._groups[group_id] = group
            return group

    @classmethod
    def make_from_idnumber(cls, idnumber):
        _, teacher_username, course_id, _ = re.split('([a-z]*)([^a-z]*)', idnumber)
        # make dummy 'objects'
        course = NS(course_id=course_id)
        teacher = NS(username=teacher_username)
        return Group(course, teacher)

class Group(Entry):
    """
    """
    kind = "group"

    def __init__(self, course, teacher):
        teacher_username = teacher.username if teacher else unknown_teacher
        course_id = course.course_id if course else unknown_course
        self.group_id = teacher_username + course_id
        self.course_number = course_id
        self.teacher_username = teacher_username
        self.ID = self.group_id

    def __repr__(self):
        return self.format_string("<Group>: {group_id}")
