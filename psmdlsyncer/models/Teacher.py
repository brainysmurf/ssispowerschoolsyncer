"""
Every Student data type represents a student.
Does context-specific processing
"""
from psmdlsyncer.models.Entry import Entry
import re
from psmdlsyncer.utils.Utilities import no_whitespace_all_lower, derive_departments

PRIMARYSCHOOLID = 111
SECONDARYSCHOOLID = 112

# self.is_secondary

class Teacher(Entry):

    def __init__(self, num, lastfirst, email, title, schoolid, status, **kwargs):
        self.num = num
        self.idnumber = self.num
        self.ID = num
        self.family_id = self.num[:4] + 'P'
        self.kind = 'teacher'
        self.lastfirst = lastfirst
        self.email = email if email.strip() else None
        self.last, self.first = self.lastfirst.split(',')
        self.first = self.first.strip()
        self.last = self.last.strip()
        if not self.email:
            self.email = "{}@ssis-suzhou.net".format(re.sub(r'[^a-z]', '', "{}{}".format(self.first, self.last).lower()))
        self.preferred_name = self.first + " " + self.last
        self.profile_bool_details = title
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
        self.homeroom = None
        if schoolid == str(PRIMARYSCHOOLID):
            self.is_primary = True
            self.profile_bool_iselemteacher = True
        if schoolid == str(SECONDARYSCHOOLID):
            self.is_secondary = True
            self.profile_bool_issecteacher = True
        self.status = self.determine_status(status)
        self.profile_extra_isteacher = True

    def determine_status(self, status):
        return {2:'left', 1:'here'}.get(int(status))

    def update_courses(self, course_obj):
        course_name = course_obj.moodle_short
        if course_name not in self._courses:
            if course_name.startswith('HROOM'):
                self.homeroom = int(re.sub('[A-Z]', '', course_name.upper()))
            self._courses.append(course_name)

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
        self._departments = derive_departments([c for c in self.courses()])
        return self._departments

    def __repr__(self):
        return self.format_string("{first}{preferred_name}:{username}{mid}{courses_str}", first="+ ", mid="\n| ", last="| ", courses_str=", ".join([a for a in self._courses if a]))


if __name__ == "__main__":

    pass
