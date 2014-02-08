import re
from psmdlsyncer.models.base import BaseModel

class Schedule(BaseModel):
    """
    REALLY JUST MOSTLY A NAMESPACE
    """
    kind = 'schedule'

    def __init__(self, schedule_id, student, teacher, course):        
        """
        group_name param indicates that we don't have the teacher info but to derive that from the group name
        """
        self.idnumber = self.ID = schedule_id
        self.student = student
        self.teacher = teacher
        self.course = course

    def __repr__(self):
        return self.format_string("<Schedule: {course_number}, Student:{student_id}, Teacher:{teacher_id}>")

    def __hash__(self):
        return hash(self.ID)

    def __eq__(self, other):
        return self.ID == other.ID
    
