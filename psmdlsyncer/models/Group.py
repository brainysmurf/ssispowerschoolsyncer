"""
"""
from psmdlsyncer.models.meta import BaseModel
unknown_teacher = "<unknown teacher>"
unknown_course = "<unknown course>"
import re
from psmdlsyncer.utils import NS

class Group(BaseModel):
    """
    """
    kind = "group"

    def __init__(self, idnumber, teacher, course):
        teacher_username = teacher.username if teacher else unknown_teacher
        course_id = course.course_id if course else unknown_course
        self.group_id = self.name = self.idnumber = teacher_username + course_id
        self.course_number = course_id
        self.teacher_username = teacher_username
        self.ID = self.group_id

    def __repr__(self):
        return self.format_string("<Group>: {group_id}")
