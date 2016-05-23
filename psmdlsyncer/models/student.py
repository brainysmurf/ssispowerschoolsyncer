import logging

from psmdlsyncer.models.base import BaseModel
from psmdlsyncer.utils.Dates import get_year_of_graduation, get_years_since_enrolled, get_academic_start_date
from psmdlsyncer.utils.Utilities import no_whitespace_all_lower
from psmdlsyncer.utils import NS, weak_reference
from collections import defaultdict
import re
import datetime
import itertools
import json
_taken_usernames = []

class ProxyScheduleWrapper:
    def __init__(self, student_id, teacher_id, course_id):
        self.wrapped = ProxySchedule(student_id, teacher_id, course_id)

    def __call__(self):
        return self.wrapped

    def __str__(self):
        return str(self.wrapped)

    def __repr__(self):
        return str(self.wrapped)

class ProxySchedule:
    """
    Acts as a Course object that can go inside a student, without actually being a Course object
    This way we can define courses that students must be enrolled in
    And we know what we're getting
    """
    def __init__(self, student_id, teacher_id, course_id):
        self.student_id = student_id
        self.teacher_id = teacher_id
        self.course_id = course_id
        self.ID = self.student_id + self.teacher_id + self.course_number
        self.name = str(self)

    def __str__(self):
        return "<ProxySchedule {}>".format(self.idnumber)

    def __repr__(self):
        return str(self)

class ProxyCourseWrapper:
    def __init__(self, idnumber):
        self.idnumber = idnumber
        self.wrapped = ProxyCourse(self.idnumber)

    def __call__(self):
        return self.wrapped

    def __str__(self):
        return str(self.wrapped)

    def __repr__(self):
        return str(self.wrapped)

class ProxyCourse:
    """
    Acts as a Course object that can go inside a student, without actually being a Course object
    This way we can define courses that students must be enrolled in
    And we know what we're getting
    """
    def __init__(self, idnumber):
        self.idnumber = self.ID = idnumber
        self.name = str(self)

    def __str__(self):
        return "<ProxyCourse {}>".format(self.idnumber)

    def __repr__(self):
        return str(self)

class Student(BaseModel):
    """
    A student
    self.kind = student
    """
    kind = 'student'
    excluded_courses = ['XSTUDYSH1112']  #TODO: Make this a setting

    def __init__(self, num, stuid="", grade="", homeroom="", lastfirst=",", dob="", parent_emails="",
        entry_date="", department="", nationality="",
        username=None):
        """
        @param grade Pass None to derive from homeroom
        """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.num = num
        self.idnumber = self.num
        self.ID = self.num
        self.powerschoolID = self.ID
        self.database_id = stuid

        if self.idnumber == '48273':
            self.username = 'corbyn24'
        elif self.idnumber == '31543':
            self.username = 'gustavoramirez20'
        elif self.idnumber == '46572':
            self.username = 's.hatzopoulos18'
        else:
            self.username = username

        try:
            self.entry_date = datetime.datetime.strptime(entry_date, '%m/%d/%Y')
        except ValueError:
            self.entry_date = None
        try:
            self.birthday = datetime.datetime.strptime(dob, '%m/%d/%Y')
        except ValueError:
            self.birthday = None
        if not self.entry_date:
            self.years_enrolled = None
        else:
            self.years_enrolled = get_years_since_enrolled(self.entry_date)
        self.family_id = num[:4] + 'P'
        if grade is None:
            # If nothing was passed for grade, derive from homeroom
            # check first and handle case for no homeroom
            if not homeroom:
                self.logger.debug("This student {} ({}) has None for grade but no homeroom".format(username, self.ID))
                homeroom = "00"
                grade = 0
            else:
                grade = re.sub('[^0-9]+[0-9]{1}$', '', homeroom)
            self.hr_letter = re.sub('^[0-9]+', '', homeroom)
        else:
            self.hr_letter = ''
        try:
            grade = int(grade)
        except ValueError:
            self.logger.debug("This student {} ({}) has a non-integer grade: '{}'".format(username, self.ID, grade))
            grade = 0
        self.grade = grade
        if self.grade < 4:
            self.login_method = 'nologin'
        else:
            self.login_method = 'manual'
        self.custom_profile_isstudent = True
        self.is_secondary = grade >= 6
        self.custom_profile_issecstudent = self.is_secondary
        self.is_elementary = grade <= 5
        self.custom_profile_iselemstudent = self.is_elementary
        self.is_student = True
        self.custom_profile_isstudent = self.is_student
        self.lastfirst = lastfirst
        try:
            self.is_new_student = self.entry_date >= get_academic_start_date()
        except TypeError:
            self.is_new_student = False
        self.determine_first_and_last()
        #self.bus_int = bus_int
        #self.bus_morning = bus_morning
        #self.bus_afternoon = bus_afternoon
        self.department = department
        self.nationality = nationality
        self.is_korean = self.nationality == "Korea"
        self.is_japanese = self.nationality == "Japan"
        self.is_german = self.nationality == "Germany"
        self.is_chinese = self.nationality in ["China", "Hong Kong", "Taiwan", "Malaysia", "Singapore"]
        self.is_big5 = self.nationality in ["America", "Australia", "Canada", "New Zealand", "United Kingdom"]
        self.is_european = self.nationality in ["Austria", "Belgium", "Czech Republic", "Denmark", "Finland", "France", "Germany", "Hungary", "Italy", "Netherlands", "Norway", "Poland", "Portugal", "Spain", "Sweden", "Switzerland", "United Kingdom"]
        self.is_western = self.is_big5 or self.is_european
        self.custom_profile_iskorean = self.is_korean
        self.custom_profile_ischinese = self.is_chinese
        if homeroom:
            self.homeroom = homeroom.upper().strip()
        else:
            # FIXME: This should raise an error, because we don't have context here
            #                is this happening when reading in from Moodle, or from AutoSend?
            self.logger.debug("This student doesn't have a homeroom: {}".format(self.ID))
            self.homeroom = 'No HR'
        self.homeroom = homeroom.upper().strip()
        self.is_SWA = self.department == "SWA"
        self.homeroom_sortable = 0   # TODO: What's the put_in_order thing for then?

        self.profile_existing_department = self.homeroom
        #self.profile_existing_address = self.bus_int
        #self.profile_existing_phone1 = self.bus_morning
        #self.profile_existing_phone2 = self.bus_afternoon

        self.parent_emails = [p.lower() for p in re.split('[;,]', parent_emails) if p.strip()]
        if self.username is None:
            self.determine_username_email()
        else:
            self.email = self.username + '@student.ssis-suzhou.net'
        self.parent_link_email = self.username + 'PARENTS' + '@student.ssis-suzhou.net'
        self.email = self.email.lower()
        self.email_address = self.email
        self.other_defaults()
        self._courses = []
        self._schedule = []
        self._teachers = []
        self._groups = []
        self._parents = []
        self._timetable = defaultdict(lambda : defaultdict(dict))
        self._enrollments = defaultdict(list)
        self._homeroom_teacher = None
        if self.is_secondary:
            self._cohorts = ['studentsALL', 'studentsSEC', 'students{}'.format(grade), 'students{}'.format(homeroom)]
            self.custom_profile_issecstudent = True
        if self.grade in range(6, 9):
            self.custom_profile_ismsstudent = True
            self._cohorts.append('studentsMS')
        if self.grade in range(6, 11):
            self.custom_profile_ismypstudent = True
            self._cohorts.append('studentsMYP')
        if self.grade in range(9, 13):
            self.custom_profile_ishsstudent = True
            self._cohorts.append('studentsHS')
        if self.grade in range(11, 13):
            self._cohorts.append('studentsDP')
        if self.is_elementary:
            if self.grade >= 4:
                self._cohorts = ['studentsALL', 'studentsELEM', 'students{}'.format(grade), 'students{}'.format(homeroom)]
            else:
                self._cohorts = ['studentsALL']
            self.custom_profile_iselemstudent = True
            self.profile_existing_department = 'HOME4ES'
        self.is_middle_school = self.grade in range (6, 9)
        self.is_high_school = self.grade in range(10, 13)

    def get_existing_profile_fields(self):
        return [(key.split('profile_existing_')[1], self.__dict__[key]) for key in self.__dict__ if key.startswith('profile_existing_')]

    def other_defaults(self):
        #TODO: Delete this is_in_preferred later
        self.is_in_preferred_list = False

    @property
    def homeroom_teacher(self):
        if self._homeroom_teacher:
            return self._homeroom_teacher()
        else:
            return None

    @property
    def grade_string(self):
        if self.grade in range(1,13):
            return str(self.grade)
        return {0:'KINDERGARTEN', -1: 'NURSERY', -2:'PRENURSURY'}

    def determine_username_email(self):
        """
        DETERMINES THIS USERNAME TAKING INTO ACCOUNT EXISTING USERNAMES
        """
        first_half = no_whitespace_all_lower(self.first + self.last)[:20]
        second_half = str(get_year_of_graduation(self.grade))
        self.username = first_half + second_half
        times_through = 1
        report = False
        while self.username in _taken_usernames:
            self.logger.warning("Username {} already taken, looking for new name".format(self.username))
            report = True
            self.username = first_half + ('_' * times_through) + second_half

        if report:
            self.logger.warning("Using new username {}".format(self.username))
        self.email = self.username + '@student.ssis-suzhou.net'

    def update(self, key, value):
        self.key = value

    def associate(self, course, group, teacher):
        self.add_teacher(teacher)
        self.add_course(course)
        self.add_group(group)
        self.add_enrollment(course, group)
        if course.is_homeroom:
            self.add_homeroom_teacher(teacher)

    def add_homeroom_teacher(self, teacher):
        reference = weak_reference(teacher)
        self._homeroom_teacher = reference

    def add_schedule(self, schedule):
        # no weak reference, because they is nothing holding on to them
        self._schedule.append( schedule )

    def add_enrollment(self, course, group):
        if not group.ID in [g.idnumber for g in self.enrollments[course.ID]]:
            self.enrollments[course.ID].append( group )

    def add_course(self, course):
        if course.idnumber in self.excluded_courses:
            return
        if not course.ID in self.course_idnumbers:
            reference = weak_reference(course)
            self._courses.append( reference )

    def add_group(self, group):
        if not group.ID in self.group_idnumbers:
            reference = weak_reference(group)
            self._groups.append( reference )

    def add_cohort(self, cohort):
        if not cohort in self._cohorts:
            self._cohorts.append(cohort)

    def add_teacher(self, teacher):
        if not teacher.ID in self.teacher_idnumbers:
            reference = weak_reference(teacher)
            self._teachers.append( reference )

    def add_parent(self, parent):
        if not parent.ID in self.parents:
            reference = weak_reference(parent)
            self._parents.append( reference )

    @property
    def courses(self):
        if self.grade in [11, 12]:
            for force_enrol in ['IBTOKSH1112', 'IBCAS1112', 'LIBRASH1112']:
                if force_enrol not in [course().idnumber for course in self._courses]:
                    self._courses.append(ProxyCourseWrapper(force_enrol))
        return [course() for course in self._courses]

    @property
    def timetable(self):
        return self._timetable

    @property
    def custom_profile_timetable(self):
        if self.timetable == None:
            return None
        result = {}
        result['enrollments'] = self.enrollments
        result['timetable'] = self.timetable
        result['teacher_names'] = self.timetable_teacher_names
        return json.dumps(result)

    @custom_profile_timetable.setter
    def custom_profile_timetable(self, value):
        self._timetable = value

    def add_timetable(self, timetable_dict):
        """
        timetable_dict is going to have days as the top-level key
        The next level keys are the periods
        """
        for day in timetable_dict:
            for period, value in timetable_dict[day].items():
                self.timetable[day][period].update(value)

    @property
    def schedule(self):
        return self._schedule

    @property
    def schedule_idnumbers(self):
        # not really their idnumbers, but the naming is consistent
        # this really does work, since schedule implmenets a __hash__ and __eq__ operators
        return set(self._schedule)

    @property
    def enrollments(self):
        return self._enrollments

    def get_enrollments(self):
        for course in self.enrollments:
            for group in self.enrollments[course]:
                yield course, group

    @property
    def timetable_teacher_names(self):
        result = defaultdict( list )
        for group in self.groups:
            for teacher in group.teachers:
                this_teacher = {}
                this_teacher['lastfirst'] = teacher.lastfirst
                this_teacher['first'] = teacher.first
                this_teacher['last'] = teacher.last
                result[group.ID].append(this_teacher)
        return result

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
    def parent_idnumbers(self):
        return set([parents.ID for parents in self.parents])

    @property
    def teacher_idnumbers(self):
        return set([teacher.ID for teacher in self.teachers])

    @property
    def cohorts(self):
        return self._cohorts

    @property
    def cohort_idnumbers(self):
        return set(self.cohorts)

    @property
    def groups(self):
        """ undoes the weakreference """
        return [group() for group in self._groups]

    @property
    def group_idnumbers(self):
        return set([group.idnumber for group in self.groups])

    @property
    def group_names(self):
        return sorted([group.ID for group in self.groups])

    def get_english(self):
        # Returns the first English...
        englishes = [course for course in self._courses if 'ENG' in course]
        for english in englishes:
            if 'BS' in english:
                return "B Standard"
            elif 'BA' in english:
                return "B Advanced"
            elif 'BF' in english:
                return "B Foundation"
            elif 'I' in english:
                return "JumpStart"
            elif 'BENG' in english:
                return "English B"
            elif 'A' in english:
                return "English A"
            elif 'ENG' in english:
                return "English A"
            else:
                return "Unknown English! " + english
        return "No English Class?"

    def get_math(self):
        maths = [course for course in self._courses if 'MAT' in course]
        for math in maths:
            if 'ST' in math:
                return "Math Standard"
            elif 'SU' in math:
                return "Math Support"
            elif 'EX' in math:
                return "Math Extended"
            else:
                return "Unknown Maths!"

        return "No Maths?"

    @property
    def teachers(self):
        return self._teachers

    @property
    def parents(self):
        return [parent() for parent in self._parents]

    def get_teachers_as_list(self):
        """
        Called when I don't care about what courses they are in
        """
        return [item[1] for item in self.teachers]

    def get_teacher_names(self):
        """
        Return list of teachers
        """
        l = []
        for this in self._teachers.keys():
            l.append( self._teachers[this] )
        return l

    def determine_first_and_last(self):
        split = self.lastfirst.split(',')
        if not len(split) == 2:
            pass
        #print("Problem in Powerschool\n:{}:\nHe/she has a comma in his lastfirst field!".format(self.lastfirst))
        self.last = split[0]
        self.first = " ".join(split[1:])
        self.last = self.last.strip()
        self.first = self.first.replace(',', ' ').strip().replace('  ', ' ')
        self.full_name = "{} {}".format(self.first, self.last)

    @property
    def guardian_emails(self):
        return [e.strip() for e in self.parent_emails if e.strip()]

    @property
    def teacher_emails(self):
        return [teacher().email for teacher in self._teachers]

    @property
    def teachers(self):
        return [teacher() for teacher in self._teachers if teacher]

    @property
    def teacher_names(self):
        return sorted([teacher().fullname for teacher in self._teachers])

    @property
    def homeroom_teacher_email(self):
        hroom = self._homeroom_teacher
        if hroom:
            return hroom().email
        else:
            return None

    def compare_num(self, num):
        return self.num == str(num)

    def compare_kwargs(self, **kwargs):
        if set(list(kwargs.keys())).issubset(list(self.__dict__)):
            for key in kwargs:
                if not str(self.__dict__[key]) == str(kwargs[key]):
                    return False
        else:
            return False
        return True

    def __sub__(self, other):

        for item in super().__sub__(other):
            yield item

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
        attrs = ['homeroom', 'username']
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
                ns.status = 'enrol_student_into_course'
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
            #TODO: Check that parents are being put into courses as well as the groups
            self_groups = self.enrollments.get(course, [])
            other_groups = other.enrollments.get(course, [])
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
                ns.status = 'deenrol_student_from_course'
                ns.left = self
                ns.right = other
                to_remove = NS()
                to_remove.course = course
                to_remove.group = group
                ns.param = to_remove
                yield ns

    @property
    def to_csv(self):
        # FIXME: Calculate this right without relying on year
        justnumber = re.sub('[a-z_]', '', self.username)
        if not justnumber:
            grade = ""
        else:
            grade = str(13 - (int(justnumber) - 14))
        return self.format_string(",".join([grade, self.username, self.idnumber]))

    def __repr__(self):
        ns = NS()
        ns.ID = self.ID
        ns.username = self.username
        ns.homeroom = self.homeroom
        #ns.firstrow = "+ "
        #ns.midrow = "\n| "
        #ns.lastrow="\n| "
        #ns.lastfirst = self.lastfirst
        #ns.email = self.email
        #ns.homeroom = self.homeroom
        #ns.teachers = ", ".join(self.teacher_names)
        #ns.courses = ", ".join(self.course_names)
        #ns.groups = ", ".join(self.group_names)
        #ns.cohorts = ", ".join(self.cohorts)
        return ns("<Student {ID}/{homeroom}: {username}>") #, {homeroom}{midrow}{lastfirst}") # \
        #"{lastrow}{midrow}{teachers}{midrow}{courses}{midrow}{groups}{midrow}{cohorts}\n")
