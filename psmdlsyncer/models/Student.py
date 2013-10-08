"""
Every student represents a student
"""
import re
from psmdlsyncer.utils.Dates import get_year_of_graduation, get_years_since_enrolled, get_academic_start_date
from psmdlsyncer.utils.Utilities import no_whitespace_all_lower
from psmdlsyncer.settings import logging
from psmdlsyncer.models.Entry import Entry
import os
import datetime

class Object:
    """
    Very general object, kwarg arguments are just set to itself, useful for simple data manipulation
    And makes code readable
    """
    def __init__(self, *args,**kwargs):
        if not kwargs:
            return
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

class Student(Entry):

    def __init__(self, num, stuid, grade, homeroom, homeroom_sortable, lastfirst, dob, parent_emails,
                 entry_date, nationality,
                 user_data = {}):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.num = num
        self.idnumber = self.num
        self.stuid = stuid
        self.entry_date = entry_date
        self.birthday = datetime.datetime.strptime(dob, '%m/%d/%Y')
        self.years_enrolled = get_years_since_enrolled(self.entry_date)
        self.family_id = num[:4] + 'P'
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
        self.is_new_student = self.entry_date >= get_academic_start_date()
        already_exists = user_data.get(self.num)
        self.database_id = already_exists.id if already_exists else None

        self.determine_first_and_last()
        #self.determine_preferred_name()  # this is derived from preferred.txt
        
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
        self.homeroom = homeroom.upper().strip()
        self.homeroom_sortable = homeroom_sortable
        
        self.profile_existing_department = self.homeroom   # This is actually details that go on front page
                                                           #self.profile_existing_address = self.bus_int
                                                           #self.profile_existing_phone1 = self.bus_morning
                                                           #self.profile_existing_phone2 = self.bus_afternoon

        self.parent_emails = [p.lower() for p in parent_emails if p.strip()]
        self.determine_username()
        self.email = self.username + "@student.ssis-suzhou.net"
        self.parent_link_email = self.username + 'PARENTS' + '@student.ssis-suzhou.net'
        self.email = self.email.lower()
        self.other_defaults()
        self._courses = []
        if self.is_secondary:
            self._cohorts = ['studentsALL', 'studentsSEC', 'students{}'.format(grade), 'students{}'.format(homeroom)]
            self.profile_extra_issecstudent = True
        if self.grade in range(6, 8):
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
        self._groups = []
        self._groups_courses = {}
        self._teachers = {}

    def get_existing_profile_fields(self):
        return [(key.split('profile_existing_')[1], self.__dict__[key]) for key in self.__dict__ if key.startswith('profile_existing_')]

    def other_defaults(self):
        #TODO: Delete this is_in_preferred later
        self.is_in_preferred_list = False

    def get_homeroom_teacher(self):
        grade_name = self.grade if self.grade <= 10 else 'SH1112'
        try:
            teacher_name = self._teachers['HROOM{}'.format(grade_name)]
        except KeyError:
            return None
        return teacher_name

    def determine_username(self):
        """
        DETERMINES THIS USERNAME TAKING INTO ACCOUNT EXISTING USERNAMES
        MAKES A NEW ONE IF CURRENT USERNAME IS TAKEN
        """
        username_already_exists = self.user_data.get(self.num)
        if username_already_exists:
            self.username = username_already_exists.username
        else:
            taken_usernames = [self.user_data[item].username for item in self.user_data]
            first_half = no_whitespace_all_lower(self.first + self.last)[:20]
            second_half = str(get_year_of_graduation(self.grade))
            self.username = first_half + second_half
            times_through = 1
            while self.username in taken_usernames:
                self.logger.warn("Looking for a new name for student:\n{}".format(self.username))
                self.username = first_half + ('_' * times_through) + second_half

    def update(self, key, value):
        self.key = value

    def update_preferred(self, value):
        self.preferred_first, self.preferred_last = value
        self.has_preferred_name = True
        self.determine_preferred_name()
        self.determine_username()

    def update_courses(self, course_obj, teacher_obj):
        # Sometimes PowerSchool's AutoSend has two course entries in order to take care of the scheduling (or something)
        self._courses.append(course_obj.moodle_short)
        d = {'username':teacher_obj.username,'name':course_obj.moodle_short}
        self.update_groups(course_obj.moodle_short, "{username}{name}".format(**d) )

    def courses(self):
        return self._courses

    def cohorts(self):
        return self._cohorts

    def groups(self):
        return self._groups

    def get_teachers_classes(self):
        return [ re.match('([a-z]+)([^a-z]+)', item).groups() for item in self.groups() ]

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
        teachers = self.teachers()
        return [teachers[k]+"@ssis-suzhou.net" for k in teachers.keys()]

    @property
    def homeroom_teacher_email(self):
        homeroom = self.get_homeroom_teacher()
        return homeroom and homeroom + '@ssis-suzhou.net'

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
    
    def __repr__(self):
        return self.format_string("{firstrow}{num}: {email}, {homeroom}{midrow}{lastfirst}{lastrow}{_courses}\n",
                                  firstrow="+ ",
                                  midrow="\n| ",
                                  lastrow="\n| ")

    
