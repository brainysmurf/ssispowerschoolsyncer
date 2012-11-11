"""
Every student represents a student
"""
import re
from utils.Dates import get_year_of_graduation
from utils.Utilities import no_whitespace_all_lower, determine_password
from Entry import Entry
from Errors import DocumentErrors
from Constants import k_path_to_uploads, k_path_to_errors
import os

class Student(Entry):

    def __init__(self, num, grade, homeroom, lastfirst, parent_emails, nationality):
        self.num = num
        self.family_id = num[:4] + 'P'
        self.grade = grade
        self.is_secondary = grade >= 6
        self.is_elementary = grade <= 5
        self.is_student = True
        self.lastfirst = lastfirst
        self.determine_first_and_last()
        self.nationality = nationality
        self.is_korean = self.nationality == "Korea"
        self.is_chinese = self.nationality in ["China", "Hong Kong", "Taiwan", "Malaysia", "Singapore"]
        self.homeroom = homeroom
        self.parent_emails = [p.lower() for p in parent_emails if p.strip()]
        self.has_preferred_name = False
        self.determine_preferred_name()
        self.determine_username()
        self.email = self.username + "@student.ssis-suzhou.net"
        self.email = self.email.lower()
        self.other_defaults()
        self._courses = []
        if self.is_secondary:
            self._cohorts = ['studentsSEC', 'students{}'.format(grade), 'students{}'.format(homeroom)]
        elif self.is_elementary:
            self._cohorts = ['studentsELEM', 'students{}'.format(grade), 'students{}'.format(homeroom)]
        self._groups = []
        self._teachers = {}

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
        if self.has_preferred_name:
            format_string = "{preferred_first} {preferred_last}"
        else:
            format_string = "{first} {last}"
        self.preferred_name = format_string.format(**self.__dict__)

    def determine_username(self):
        self.username = no_whitespace_all_lower(self.first + self.last)[:20]
        self.username += str(get_year_of_graduation(self.grade))
        
    def update(self, key, value):
        self.key = value

    def update_preferred(self, value):
        self.preferred_first, self.preferred_last = value
        self.has_preferred_name = True
        self.determine_preferred_name()
        self.determine_username()

    def update_courses(self, course_obj, teacher_obj):
        self._courses.append(course_obj.moodle_short)
        d = {'username':teacher_obj.username,'name':course_obj.moodle_short}
        self.update_groups("{username}{name}".format(**d) )

    def courses(self):
        return self._courses

    def cohorts(self):
        return self._cohorts

    def groups(self):
        return self._groups

    def update_groups(self, group):
        """
        Processes the group information, as necessary
        """
        # Need to process it because the group code = moodlecode
        # But in cases where it ends with '1112' I need to actually tell it '11' or '12'
        # Because if a teacher has a grade 11 and grade 12, there'll be in the same group

        if group.endswith('1112'):
            newgroup = group[:-4]
            newgroup += str(self.grade)
            with open(k_path_to_errors + '/' + 'deletethesegroups.txt', 'a') as f:
                f.write("You need to delete group {}.\n".format(group))
            group = newgroup
        
        if group and not group in self._groups:
            self._groups.append(group)

    def update_teachers(self, course, teacher):
        if teacher and course not in self._teachers:
            self._teachers[course.moodle_short] = teacher.username
        else:
            pass

    def teachers(self):
        return self._teachers

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
        new_students = k_path_to_uploads + '/' + 'added_students.txt'
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
        last_first = k_path_to_uploads + '/' + 'changedlastfirst.txt'
        if not os.path.exists(last_first):
            pass
        with open(last_first, 'a') as f:
            f.write("Changed name from {} to {}\n".format(prev.lastfirst, self.lastfirst))

    def change_courses(self, prev):
        changed_courses = k_path_to_uploads + '/' + 'delete_user_from_course.txt'
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
        changed_name = k_path_to_uploads + '/' + 'changed_names.txt'
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
