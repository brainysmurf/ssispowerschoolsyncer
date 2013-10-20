"""
"""
from psmdlsyncer.models.Entry import Entry
_groups = {}
class GroupFactory:
    @classmethod
    def make(cls, course, teacher):
        group_id = teacher.username + course.ID
        if group_id in _groups:
            return _groups[group_id]
        else:
            group = Group(course, teacher)
            _groups[group_id] = group
            return group
        
class Group(Entry):
    """
    """
    def __init__(self, course, teacher):
        self.group_id = teacher.username + course.course_id
        self.course_number = course.course_id
        self.ID = self.group_id
    def __repr__(self):
        return self.format_string("{course_number}")
