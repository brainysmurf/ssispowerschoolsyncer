"""
Every student represents a student
"""
import re
from psmdlsyncer.utils.Dates import get_year_of_graduation, get_years_since_enrolled
from psmdlsyncer.utils.Utilities import no_whitespace_all_lower, determine_password
from psmdlsyncer.Entry import Entry
from psmdlsyncer.Errors import DocumentErrors
import os

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

    def __init__(self, num, stuid, grade, homeroom, homeroom_sortable, lastfirst, parent_emails, entry_date, nationality,
                 user_data = {},
                 path_to_errors='../errors',
                 path_to_output='../output'):
        self.path_to_errors = path_to_errors
        self.path_to_output = path_to_output
        self.num = num
        self.stuid = stuid
        self.entry_date = entry_date
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
        self.database_id = user_data.get(self.num)
        if self.database_id:
            self.database_id = self.database_id[1]

        self.determine_first_and_last()
        #self.determine_preferred_name()  # this is derived from preferred.txt

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
        self.homeroom = homeroom
        self.homeroom_sortable = homeroom_sortable
        self.profile_existing_institution = "Homeroom {}".format(self.homeroom)   # This is actually details that go on front page
        self.parent_emails = [p.lower() for p in parent_emails if p.strip()]
        self.determine_username()
        self.email = self.username + "@student.ssis-suzhou.net"
        self.email = self.email.lower()
        self.other_defaults()
        self._courses = []
        if self.is_secondary:
            self._cohorts = ['studentsSEC', 'students{}'.format(grade), 'students{}'.format(homeroom)]
            self.profile_extra_issecstudent = True
        if self.grade in range(6, 8):
            self.profile_extra_ismsstudent = True
            self._cohorts.append('studentsMS')
        if self.grade in range(9, 12):
            self.profile_extra_ishsstudent = True
            self._cohorts.append('studentsHS')
        elif self.is_elementary:
            self._cohorts = ['studentsELEM', 'students{}'.format(grade), 'students{}'.format(homeroom)]
            self.profile_extra_iselemstudent = True
        self._groups = []
        self._groups_courses = {}
        self._teachers = {}

    def get_existing_profile_fields(self):
        return [(key.split('profile_existing_')[1], self.__dict__[key]) for key in self.__dict__ if key.startswith('profile_existing_')]

    def get_extra_profile_fields(self):
        return [(key.split('profile_extra_')[1], self.__dict__[key]) for key in self.__dict__ if key.startswith('profile_extra_')]

    def other_defaults(self):
        #TODO: Delete this is_in_preferred later
        self.is_in_preferred_list = False

    def get_homeroom_teacher(self):
        grade_name = self.grade if self.grade <= 10 else 'SH1112'
        try:
            teacher_name = self._teachers['HROOM{}'.format(grade_name)]
        except:
            return None
        return teacher_name

    def determine_preferred_name(self):
        """
        """
        self.has_preferred_name = False
        if not hasattr(self, 'preferred_names_from_file'):
            # read in the information the first time
            self.preferred_names_from_file = {}
            with open('/home/lcssisadmin/ssispowerschoolsync/src/preferred_names.txt') as _f:
                for line in [l.strip('\n') for l in _f.readlines() if l.strip('\n')]:
                    split = line.split('\t')
                    if not len(split) == 5:
                        continue
                    stu_num = split[0]
                    preferred_first = split[3]
                    preferred_last = split[4]
                    if stu_num and preferred_first:
                        self.preferred_names_from_file[stu_num] = Object(firstname=preferred_first, lastname=preferred_last)
        just_alpha = lambda s: re.sub(r'[^a-z]', '', s.lower())
        is_different = lambda num: just_alpha(self.first) != just_alpha(self.preferred_names_from_file[num].firstname)
        register_preferred_name = lambda num: num in self.preferred_names_from_file and is_different(num)

        if register_preferred_name(self.num):
            this = self.preferred_names_from_file[self.num]
            self.preferred_first = this.firstname
            self.preferred_last = this.lastname
            self.has_preferred_name = True
        else:
            self.preferred_first = ""
            self.preferred_last = ""

        if self.has_preferred_name:
            format_string = "{preferred_first} {preferred_last}"
        else:
            format_string = "{first} {last}"
        self.preferred_name = format_string.format(**self.__dict__)

    def determine_username(self):
        """
        Determines usernames for already existing students
        and new ones alike
        """
        username_already_exists = self.user_data.get(self.num)
        if username_already_exists:
            username_already_exists = username_already_exists[0]
            self.username = username_already_exists
        else:
            taken_usernames = [item[1][0] for item in self.user_data.items()]
            first_half = no_whitespace_all_lower(self.first + self.last)[:20]
            second_half = str(get_year_of_graduation(self.grade))
            self.username = first_half + second_half
            times_through = 1
            while self.username in taken_usernames:
                print("Looking for a new name for student:\n{}".format(self.username))
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
            with open(self.path_to_errors + '/' + 'deletethesegroups.txt', 'a') as f:
                f.write("You need to delete group {}.\n".format(group))
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

    def database_new(self, student):
        #TODO: Depreciate
        pass
        new_students = self.path_to_uploads + '/' + 'added_students.txt'
        if not os.path.exists(new_students):
            pass
        with open(new_students, 'a') as f:
            print("NEW STUDENT {}".format(student))
            f.write("{} is a new student\n".format(student.lastfirst))
        
    def database_compare(self, prev):
        to_check = ['lastfirst', 'username', '_courses']
        for key in to_check:
            if not getattr(prev, key) == getattr(self, key):
                getattr(self, 'change_' + key.strip('_'))(prev)

    def change_homeroom(self, prev):
        """  Doesn't matter, really """
        pass
        
    def change_lastfirst(self, prev):
        #TODO: Depreciate
        pass
        last_first = self.path_to_uploads + '/' + 'changedlastfirst.txt'
        if not os.path.exists(last_first):
            pass
        with open(last_first, 'a') as f:
            f.write("Changed name from {} to {}\n".format(prev.lastfirst, self.lastfirst))

    def change_courses(self, prev):
        #TODO: Depreciate
        pass
        changed_courses = self.path_to_uploads + '/' + 'delete_user_from_course.txt'
        prev_courses = prev.courses()
        for course in self.courses():
            if not course in prev_courses:
                with open(changed_courses, 'a') as f:
                    f.write("{} added to course: {}\n".format(self.username, course))

        for course in prev.courses():
            if not course in self.courses():
                with open(changed_courses, 'a') as f:
                    f.write("{} removed from course: {}\n".format(self.username, course))
        

    def change_username(self, prev):
        #TODO: Depreciate
        pass
        changed_name = self.path_to_uploads + '/' + 'changed_names.txt'
        if not os.path.exists(changed_name):
            with open(changed_name, 'w') as f:
                f.write('username,firstname,lastname,oldusername\n')
        with open(changed_name, 'a') as f:
            f.write(",".join([self.username, self.first, self.last, prev.username]))

    def __repr__(self):
        return self.format_string("{firstrow}{num}: {email}, {homeroom}{midrow}{lastfirst}{lastrow}{_courses}\n",
                                  firstrow="+ ",
                                  midrow="\n| ",
                                  lastrow="\n| ")