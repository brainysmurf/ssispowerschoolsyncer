from psmdlsyncer.utils import NS, weak_reference
from psmdlsyncer.models.base import BaseModel
from collections import defaultdict
import re

map_days = {
'A': 'Monday',
'B': 'Tuesday',
'C': 'Wednesday',
'D': 'Thursday',
'E': 'Friday'
}

def make_list(str, delimiter='-'):
    if not delimiter in str:
        items = [str]
    else:
        items = str.split(delimiter)
    return items

class Timetable(BaseModel):
    def __init__(self, idnumber, course, teacher, group, student, period_info):
        self.idnumber = idnumber
        self.period_info = period_info
        self.course = course
        self.course_idnumber = course.idnumber
        self.teacher = teacher
        self.teacher_idnumber = teacher.idnumber
        self.student = student
        self.student_idnumber = student.idnumber
        self.group = group
        self.group_idnumber = group.idnumber

    def unpack_timetable(self):
        """
        return a dictionary that represents the timetable
        which can be json'd
        """
        result = defaultdict(lambda : defaultdict(dict))
        value = {
        'group': self.group_idnumber,
        'course': self.course_idnumber
        }
        for item in self.period_info.split(' '):
            # First seperate out the
            match = re.search(r'(.*)\((.*)\)', item)
            if not match:
                continue  # fatal error, really, because it means we don't know our own data
            periods, days = match.groups()
            for day in make_list(days):
                #key = map_days.get(day)
                key = day
                if not key:
                    # fatal error, really, because it means we don't know our own data
                    continue
                if '-' in periods:
                    result[key][periods] = value
                for period in make_list(periods):
                    result[key][period] = value
        return result

    def __sub__(self, other):
        return ()

    def __repr__(self):
        return '{}'.format(self.idnumber)

