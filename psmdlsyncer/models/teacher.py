from psmdlsyncer.models.base import BaseModel
from psmdlsyncer.utils import weak_reference
import re
from psmdlsyncer.utils.Utilities import no_whitespace_all_lower, derive_departments

PRIMARYSCHOOLID = 111
SECONDARYSCHOOLID = 112

class Teacher(BaseModel):
    kind = "teacher"

    def __init__(self, num, lastfirst, email, title, schoolid, status, **kwargs):
        self.num = num
        self.ID = num
        self.powerschool_id = num
        self.idnumber = self.num
        self.family_id = self.ID[:4] + 'P'
        self.lastfirst = lastfirst
        self.email = email if email.strip() else None
        self.email_address = self.email
        self.last, self.first = self.lastfirst.split(',')
        self.first = self.first.strip()
        self.last = self.last.strip()
        self.fullname = self.first + ' ' + self.last
        if not self.email:
            self.email = "{}@ssis-suzhou.net".format(re.sub(r'[^a-z]', '', "{}{}".format(self.first, self.last).lower()))
        self.preferred_name =self.first + " " + self.last
        self.profile_bool_deails = title
        if email:
            self.username = no_whitespace_all_lower(self.email.split('@')[0])
        else:
            self.username = no_whitespace_all_lower(self.preferred_name)
        self.title = title
        self._courses = []
        self._students = []
        self._teachers = []
        self._groups = []
        self._parents = []
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
        self.status = status
        self.profile_extra_isteacher = True

    def add_course(self, course):
        """ UPDATES INTERNAL AS WELL AS DETECTS HOMEROOM """
        reference = weak_reference(course)
        if not reference in self._courses:
            if course.ID.startswith('HROOM'):
                self.homeroom = int(re.sub('[A-Z_]', '', course.ID.upper()))
            self._courses.append(reference)

    def add_student(self, student):
        reference = weak_reference(student)
        if not student in self._students:
            self._students.append(reference)

    def add_group(self, group):
        reference = weak_reference(group)
        if not group in self._groups:
            self._groups.append(reference)

    def add_teacher(self, teacher):
        reference = weak_reference(teacher)
        if not teacher in self._teachers:
            self._teachers.append(reference)

    def add_parent(self, parent):
        reference = weak_reference(parent)
        if not parent in self._parents:
            self._parents.append(reference)

    @property
    def students(self):
        return [student() for student in self._students]

    @property
    def courses(self):
        return [course() for course in self._courses]

    @property
    def parents(self):
        return [parent() for parent in self._parents]

    @property
    def groups(self):
        return [group() for group in self._groups]

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
        self._departments = derive_departments([c.ID for c in self.courses])
        return self._departments

    def __repr__(self):
        return self.format_string("<Teacher: {lastfirst} ({ID}): {username}>") #{mid}{courses_str}", first="+ ", mid="\n| ", last="| ", courses_str=", ".join([course.ID for course in self.courses]))

    def differences(self, other):
        return ()

    __sub__ = differences

    def post_differences(self, other):
        return ()

