import re
from psmdlsyncer.models.base import BaseModel

class Schedule(BaseModel):
    """
    REALLY JUST MOSTLY A NAMESPACE
    """
    kind = 'schedule'

    def __init__(self, schedule_ID, course, teacher, student):
        """
        Schedules don't come built-in with schedule ids, so we have to derive it ourselves,
        which is done in the datastores
        """
        self.idnumber = self.ID = schedule_ID
        self.student = student
        self.teacher = teacher
        self.course = course

    def __repr__(self):
        return self.format_string("<Schedule: {idnumber}, Student:{student}, Teacher:{teacher}>")

    def __hash__(self):
        return hash(self.ID)

    def __eq__(self, other):
        return self.ID == other.ID

    def __sub__(self, other):
        """
        Schedules are special cases, since we define the ID number by its items,
        we can be assured that there are no differences between any of them
        So how do we know a change occured? For that, we look at the students
        """
        return []
