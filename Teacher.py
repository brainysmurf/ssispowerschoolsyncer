"""
Every Student data type represents a student.
Does context-specific processing
"""
from Entry import Entry
import re
from utils.Utilities import no_whitespace_all_lower, derive_departments

PRIMARYSCHOOLID = 111
SECONDARYSCHOOLID = 112

# self.is_secondary

class Teacher(Entry):

    def __init__(self, lastfirst, email, title, schoolid):
        self.lastfirst = lastfirst
        self.email = email if email.strip() else None
        self.last, self.first = self.lastfirst.split(',')
        self.first = self.first.strip()
        self.last = self.last.strip()
        if not self.email:
            self.email = "{}@ssis-suzhou.net".format(re.sub(r'[^a-z]', '', "{}{}".format(self.first, self.last).lower()))
        self.preferred_name = self.first + " " + self.last
        if email:
            self.username = no_whitespace_all_lower(self.email.split('@')[0])
        else:
            self.username = no_whitespace_all_lower(self.preferred_name)
        self.title = title
        self._courses = []
        self._students = []
        self._departments = []
        self.is_primary = False
        self.is_secondary = False
        if schoolid == str(PRIMARYSCHOOLID):
            self.is_primary = True
        if schoolid == str(SECONDARYSCHOOLID):
            self.is_secondary = True

    def update_courses(self, course_obj):
        if course_obj not in self._courses:
            self._courses.append(course_obj.moodle_short)

    def update_students(self, s):
        if s not in self._students:
            self._students.append(s.username)

    def courses(self):
        return self._courses

    def students(self):
        return self._students

    def derive_cohorts(self):
        """ Returns cohorts, dynamically created """
        l = self.get_departments()
        if self.is_secondary:
            l.append('teachersSEC')
        if self.is_primary:
            l.append('teachersELEM')
        if self.is_secondary or self.is_primary:
            l.append('teachersALL')
        return l

    def get_departments(self):
        if not self._departments:
            self._departments = derive_departments([c for c in self.courses()])
        return self._departments

    def __repr__(self):
        return self.format_string("{first}{preferred_name}:{username}{mid}{courses_str}", first="+ ", mid="\n| ", last="| ", courses_str=", ".join([a.course_number for a in self._courses]))


if __name__ == "__main__":

    pass
