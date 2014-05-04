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
    def __init__(self, idnumber, course_idnumber, teacher_idnumber, group_idnumber, student_idnumber, period_info):
        self.value = period_info
        self.course_idnumber = course_idnumber
        self.teacher_idnumber = teacher_idnumber
        self.student_idnumber = student_idnumber
        self.group_idnumber = group_idnumber

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
        for item in self.value.split(' '):
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
