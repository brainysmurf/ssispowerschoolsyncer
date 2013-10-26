"""
"""
from psmdlsyncer.models.Entry import Entry

class Groups:
    def __init__(self):
        self._groups = {}
    def make(self, course, teacher):
        group_id = teacher.username + course.ID
        if group_id in self._groups:
            return self._groups[group_id]
        else:
            group = Group(course, teacher)
            self._groups[group_id] = group
            return group

class Group(Entry):
    """
    """
    def __init__(self, course, teacher):
        self.group_id = teacher.username + course.course_id
        self.course_number = course.course_id
        self.teacher_username = teacher.username
        self.ID = self.group_id
    def __repr__(self):
        return self.format_string("{group_id}")
