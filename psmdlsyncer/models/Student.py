"""
Every student represents a student
"""
from psmdlsyncer.sql import MoodleDBConnection
from psmdlsyncer.utils.Dates import get_year_of_graduation, get_years_since_enrolled, get_academic_start_date
from psmdlsyncer.utils.Utilities import no_whitespace_all_lower
from psmdlsyncer.settings import logging
from psmdlsyncer.models.Entry import Entry
from psmdlsyncer.utils import NS, weak_reference
import re
import os
import datetime
_taken_usernames = []

class Students:
    """
    MAKES A NEW STUDENT, RESPONSIBLE FOR FILLING IN THE INFORMATION THAT ALREADY
    EXISTS WITHIN MOODLE.    
    """
    def __init__(self):
        self._user_data = {}
        dnet = MoodleDBConnection()
        # any fields selected in next call means that moodle has the cononical version of that data
        # changing the email address on Moodle will automatically update psmdlsyncer, too
        # TODO: Make this more portable
        for row in dnet.get_table('user', 'id', 'idnumber', 'username', 'email'):
            ns = NS()
            ns.id, ns.idnumber, ns.username, ns.email = row
            self._user_data[ns.idnumber] = ns
        # list of usernames
        _taken_usernames = [self._user_data[student].username for student in self._user_data]

    def make(self, *args, **kwargs):
        """
        IF THE PARENT CLASS HAS ALREADY BEEN CREATED, PROCESSES AND RETURNS THAT
        OTHERWISE, MAKES A NEW ONE
        """
        student_id = args[0]  # first argument passed is assumed to be the id
        student_obj = Student(*args, **kwargs)
        user_data = self._user_data.get(student_id)
        if user_data:
            student_obj.database_id = user_data.id
            student_obj.username = user_data.username
        return student_obj

class Student(Entry):
    """
    A student
    self.kind = student
    """ 

    kind = 'student'

    def __init__(self, num, stuid, grade, homeroom, lastfirst, dob, parent_emails, 
        entry_date, nationality,
        username=None,
        passed_cohorts=None, passed_groups=None,
        user_data={}):
        """
        @param grade Pass None to derive from homeroom
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.num = num
        self.idnumber = self.num
        self.ID = self.num
        self.powerschoolID = self.ID
        self.stuid = stuid
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
                grade = re.sub('[^0-9]', '', homeroom)
        try:
            grade = int(grade)
        except ValueError:
            self.logger.info("This student {} ({}) has a non-integer grade: '{}'".format(username, self.ID, grade))
            grade = 0
        self.grade = grade
        self.profile_extra_isstudent = True
        self.is_secondary = grade >= 6
        self.profile_extra_issecstudent = self.is_secondary
        self.is_elementary = grade <= 5
        self.profile_extra_iselemstudent = self.is_elementary
        self.is_student = True
        self.profile_extra_isstudent = self.is_student
        self.lastfirst = lastfirst
        self.user_data = user_data
        try:
            self.is_new_student = self.entry_date >= get_academic_start_date()
        except TypeError:
            self.is_new_student = False
        self.determine_first_and_last()        
        #self.bus_int = bus_int
        #self.bus_morning = bus_morning
        #self.bus_afternoon = bus_afternoon
        self.nationality = nationality
        self.is_korean = self.nationality == "Korea"
        self.is_japanese = self.nationality == "Japan"
        self.is_german = self.nationality == "Germany"
        self.is_chinese = self.nationality in ["China", "Hong Kong", "Taiwan", "Malaysia", "Singapore"]
        self.is_big5 = self.nationality in ["America", "Australia", "Canada", "New Zealand", "United Kingdom"]
        self.is_european = self.nationality in ["Austria", "Belgium", "Czech Republic", "Denmark", "Finland", "France", "Germany", "Hungary", "Italy", "Netherlands", "Norway", "Poland", "Portugal", "Spain", "Sweden", "Switzerland", "United Kingdom"]
        self.is_western = self.is_big5 or self.is_european
        self.profile_extra_iskorean = self.is_korean
        self.profile_extra_ischinese = self.is_chinese
        if homeroom:
            self.homeroom = homeroom.upper().strip()
        else:
            # FIXME: This should raise an error, because we don't have context here
            #                is this happening when reading in from Moodle, or from AutoSend?
            self.logger.debug("This student doesn't have a homeroom: {}".format(self.ID))
            self.homeroom = 'No HR'
        self.homeroom = homeroom.upper().strip()
        self.is_SWA = 'SWA' in self.homeroom
        self.homeroom_sortable = 0   # TODO: What's the put_in_order thing for then?
        
        self.profile_existing_department = self.homeroom
        #self.profile_existing_address = self.bus_int
        #self.profile_existing_phone1 = self.bus_morning
        #self.profile_existing_phone2 = self.bus_afternoon

        self.parent_emails = [p.lower() for p in re.split('[;,]', parent_emails) if p.strip()]
        if username is None:
            self.determine_username_email()
        else:
            self.username = username
            self.email = username + '@student.ssis-suzhou.net'
        self.parent_link_email = self.username + 'PARENTS' + '@student.ssis-suzhou.net'
        self.email = self.email.lower()
        self.other_defaults()
        self._courses = []
        self._teachers = []
        self._groups = []
        self._homeroom_teacher = None
        if self.is_secondary:
            self._cohorts = ['studentsALL', 'studentsSEC', 'students{}'.format(grade), 'students{}'.format(homeroom)]
            self.profile_extra_issecstudent = True
        if self.grade in range(6, 9):
            self.profile_extra_ismsstudent = True
            self._cohorts.append('studentsMS')
        if self.grade in range(9, 13):
            self.profile_extra_ishsstudent = True
            self._cohorts.append('studentsHS')
        if self.grade in range(11, 13):
            self._cohorts.append('students1112')
        if self.is_elementary:
            self._cohorts = ['studentsALL', 'studentsELEM', 'students{}'.format(grade), 'students{}'.format(homeroom)]
            self.profile_extra_iselemstudent = True
            self.profile_existing_department = 'HOME4ES'
        self.is_middle_school = self.grade in range (6, 9)
        self.is_high_school = self.grade in range(10, 13)
        self._groups = []
        self._teachers = []

        # Now look at anything that has been passed and set accordingly
        if not passed_cohorts is None:
            self._cohorts = passed_cohorts
        if not passed_groups is None:
            self._groups = passed_groups

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

    def determine_username_email(self):
        """
        DETERMINES THIS USERNAME TAKING INTO ACCOUNT EXISTING USERNAMES
        """
        first_half = no_whitespace_all_lower(self.first + self.last)[:20]
        second_half = str(get_year_of_graduation(self.grade))
        self.username = first_half + second_half
        times_through = 1
        while self.username in _taken_usernames:
            self.logger.warning("Username {} already taken".format(self.username))
            self.logger.warning("Looking for a new name for student:\n{}".format(self.username))
            self.username = first_half + ('_' * times_through) + second_half
        self.email = self.username + '@student.ssis-suzhou.net'

    def update(self, key, value):
        self.key = value
    def associate(self, teacher, course, group):
        self.add_teacher(teacher)
        self.add_course(course)
        self.add_group(group)
        if 'HROOM' in course.ID:
            self.add_homeroom_teacher(teacher)
    def add_homeroom_teacher(self, teacher):
        reference = weak_reference(teacher)
        if self._homeroom_teacher:
            input("Two homeroom teachers?")
        self._homeroom_teacher = reference
    def add_course(self, course):
        reference = weak_reference(course)
        if not reference in self._courses:
            self._courses.append( reference )
    def add_group(self, group):
        reference = weak_reference(group)
        if not reference in self._groups:
            self._groups.append( reference )
    def add_teacher(self, teacher):
        reference = weak_reference(teacher)
        if not reference in self._teachers:
            self._teachers.append( reference )
    @property
    def courses(self):
        return [course() for course in self._courses]
    @property
    def course_names(self):
        return sorted(["{} ('{}')".format(course().ID, course().name) for course in self._courses])
    @property
    def cohorts(self):
        return self._cohorts
    @property
    def groups(self):
        return [group for group in self._groups]
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

    def update_groups(self, shortcode, group):
        """
        Processes the group information, as necessary
        """
        # Need to process it because the group code = moodlecode
        # But in cases where it ends with '1112' I need to actually tell it '11' or '12'
        # Because if a teacher has a grade 11 and grade 12, there'll be in the same group

        if group.endswith('1112'):
            newgroup = group[:-4]
            newgroup += str(self.grade)
            group = newgroup
        
        if group:
            self._groups.append(group)
            self._groups_courses[shortcode] = group

    def update_teachers(self, course, teacher):
        if teacher and course not in self._teachers:
            self._teachers[course.moodle_short] = teacher.username
        else:
            pass

    def teachers(self):
        return self._teachers

    def get_teachers_as_list(self):
        """
        Called when I don't care about what courses they are in
        """
        return [item[1] for item in self.teachers().items()]

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
        teachers = self.teachers
        return [teacher().email for teacher in self._teachers]

    @property
    def teachers(self):
        return [teacher() for teacher in self._teachers]

    @property
    def teacher_names(self):
        return sorted([teacher().fullname for teacher in self._teachers])

    @property
    def homeroom_teacher_email(self):
        hroom = self._homeroom_teacher
        if hroom:
            return hroom.email
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

    def differences(self, other):
        if not self.cohorts is other.cohorts:
            for to_add in self.cohorts - other.cohorts:
                ns = NS()
                ns.status = 'add_to_cohort'
                ns.left = self.cohorts
                ns.right = other.cohorts
                ns.param = to_add
                yield ns
            for to_remove in self.cohorts - other.cohorts:
                ns = NS()
                ns.status = 'remove_from_cohort'
                ns.left = self.cohorts
                ns.right = other.cohorts
                ns.param = to_add
                yield ns
                
    
    __sub__ = differences

    def __repr__(self):
        ns = NS()
        ns.ID = self.ID
        ns.firstrow = "+ "
        ns.midrow = "\n| "
        ns.lastrow="\n| "
        ns.lastfirst = self.lastfirst
        ns.email = self.email
        ns.username = self.username
        ns.homeroom = self.homeroom
        ns.teachers = ", ".join(self.teacher_names)
        ns.courses = ", ".join(self.course_names)
        ns.groups = ", ".join(self.group_names)
        ns.cohorts = ", ".join(self.cohorts)
        #return ns("{firstrow}{ID}: {email}, {homeroom}{midrow}{lastfirst}" \
        #"{lastrow}{midrow}{teachers}{midrow}{courses}{midrow}{groups}{midrow}{cohorts}\n")
        return ns("Student {username} ({ID} {homeroom})")
