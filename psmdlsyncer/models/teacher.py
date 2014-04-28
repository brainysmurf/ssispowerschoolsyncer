from psmdlsyncer.models.base import BaseModel
from psmdlsyncer.utils import weak_reference
import re
from psmdlsyncer.utils.Utilities import no_whitespace_all_lower, derive_departments
from collections import defaultdict
from psmdlsyncer.utils import NS

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
        self._timetable= defaultdict(lambda : defaultdict(dict))
        self._enrollments = defaultdict(list)
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
        self._cohorts = self.derive_cohorts()


    def add_course(self, course):
        """ UPDATES INTERNAL AS WELL AS DETECTS HOMEROOM """
        reference = weak_reference(course)
        if not reference in self._courses:
            if course.ID.startswith('HROOM'):
                self.homeroom = course.ID[5:]
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

    def associate(self, course, group, student):
        self.add_student(student)
        self.add_course(course)
        self.add_group(group)
        self.enrollments[course.ID].append( group.ID )

    @property
    def enrollments(self):
        return self._enrollments

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

    @property
    def enrollments(self):
        return self._enrollments

    @property
    def course_names(self):
        return sorted(["{} ('{}')".format(course.ID, course.name) for course in self.courses])

    @property
    def courses_sort(self):
        return sorted([course.ID for course in self.courses])

    @property
    def course_idnumbers(self):
        return set([course.ID for course in self.courses])

    @property
    def cohorts(self):
        return self._cohorts

    @property
    def cohort_idnumbers(self):
        return set(self.cohorts)

    @property
    def timetable(self):
        return self._timetable

    def add_timetable(self, timetable_dict):
        """
        timetable_dict is going to have days as the top-level key
        The next level keys are the periods
        """
        for day in timetable_dict:
            for period, value in timetable_dict[day].items():
                self.timetable[day][period].update(value)

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
        # Handle cohorts (site-wide groups)
        for to_add in set(other.cohort_idnumbers) - set(self.cohort_idnumbers):
            ns = NS()
            ns.status = 'add_to_cohort'
            ns.left = self
            ns.right = other
            ns.param = to_add
            yield ns

        for to_remove in set(self.cohort_idnumbers) - set(other.cohort_idnumbers):
            ns = NS()
            ns.status = 'remove_from_cohort'
            ns.left = self
            ns.right = other
            ns.param = to_remove
            yield ns

        # Other things
        attrs = ['username']
        for attr in attrs:
            if not getattr(self, attr) == getattr(other, attr):
                ns = NS()
                ns.status = attr+'_changed'
                ns.left = self
                ns.right = other
                ns.param = getattr(other, attr)
                yield ns

        for course in set(other.enrollments.keys()) - set(self.enrollments.keys()):
            for group in other.enrollments[course]:
                ns = NS()
                ns.status = 'enrol_teacher_into_course'
                ns.left = self
                ns.right = other
                to_add = NS()
                to_add.course = course
                to_add.group = group
                ns.param = to_add
                yield ns

        # Go through each course that they share, and check that
        # they have the same groups, if not, do what's right
        for course in set(self.enrollments.keys()) and set(other.enrollments.keys()):
            self_groups = self.enrollments[course]
            other_groups = other.enrollments[course]
            for group in other_groups:
                if not group in self_groups:
                    ns = NS()
                    ns.status = 'add_to_group'
                    ns.left = self
                    ns.right = other
                    to_add = NS()
                    to_add.course = course
                    to_add.group = group
                    ns.param = to_add
                    yield ns
            for group in self_groups:
                if not group in other_groups:
                    ns = NS()
                    ns.status = 'remove_from_group'
                    ns.left = self
                    ns.right = other
                    to_remove = NS()
                    to_remove.course = course
                    to_remove.group = group
                    ns.param = to_remove
                    yield ns

        for course in set(self.enrollments.keys()) - set(other.enrollments.keys()):
            for group in self.enrollments[course]:
                ns = NS()
                ns.status = 'deenrol_teacher_from_course'
                ns.left = self
                ns.right = other
                to_remove = NS()
                to_remove.course = course
                to_remove.group = group
                ns.param = to_remove
                yield ns

    __sub__ = differences

    # def post_differences(self, other):
    #     return ()

