"""
Holds all information about a particular student
Reads in from Powerschool file
"""

from ReadFiles import SimpleReader
from Exceptions import BasicException
from Controller import Controller, NoSuchStudent
from Password import Password
from Student import Student
from Course import Course
from Teacher import Teacher
from Schedule import Schedule
from Allocation import Allocation

from utils.Utilities import convert_short_long, determine_password
from utils.FilesFolders import clear_folder
from utils.Utilities import course_reference
from Constants import k_homerooms, k_path_to_databases, k_path_to_output, k_path_to_errors, k_path_to_powerschool, k_path_to_uploads
from Errors import DocumentErrors

import re
import os

class UnknownGrade(BasicException): pass
class NoHomeroom(BasicException): pass

def put_in_order(what):
    result = 0 # elementary don't have LEARN
    trans = {'L':1,'E':2,'A':3,'R':4,'N':5,'S':6,'SWA':7}
    if '6' in what:
        result = 100 + trans[re.sub('[0-9]', '', what)]
    elif '7' in what:
        result =  200 + trans[re.sub('[0-9]', '', what)]
    elif '8' in what:
        result =  300 + trans[re.sub('[0-9]', '', what)]
    elif '9' in what:
        result =  400 + trans[re.sub('[0-9]', '', what)]
    elif '10' in what:
        result = 500 + trans[re.sub('[0-9]', '', what)]
    elif '11' in what:
        result = 600 + trans[re.sub('[0-9]', '', what)]
    elif '12' in what:
        result = 700 + trans[re.sub('[0-9]', '', what)]
    return result

class Students:

    exclude_these_teachers_manually = ['Sections, Dead', 'User, Drews Test']

    def __init__(self):
        """
        Does the work of reading in basic information from file, creates native Python structures
        StudentNumber\tHomeroom\tLastFirst\tguardianemails
        """
        self.errors = DocumentErrors(k_path_to_errors)
        self.student_info_file = SimpleReader(k_path_to_powerschool + '/' + 'ssis_studentinfodumpall')
        self.raw = self.student_info_file.raw()
        self.student_info_controller = Controller(Student)
        self.course_info_controller = Controller(Course)
        self.teacher_info_controller = Controller(Teacher)
        self.schedule_info_controller = Controller(Schedule)
        self.allocation_info_controller = Controller(Allocation)
        self.read_in()
        self._homerooms = None
        self._secondary_homerooms = None
        self._elementary_homerooms = None
        self.get_homerooms()
        self.get_secondary_homerooms()

    def document_error(self, kind, content):
        self.errors.document_errors(kind, content)

    def get_homerooms(self):
        if not self._homerooms:
            self._homerooms = []
            for student_key in self.get_student_keys():
                student = self.get_student(student_key)
                if not student.homeroom in self._homerooms:
                    self._homerooms.append(student.homeroom)
        self._homerooms.sort(key=put_in_order)
        return self._homerooms

    def student_keys_by_secondary_homerooms(self):
        for hr in self.get_secondary_homerooms():
            for student_key in self.get_secondary_student_keys():
                student = self.get_student(student_key)
                if student.homeroom == hr:
                    yield student

    def get_secondary_homerooms(self):
        if not self._secondary_homerooms:
            self._secondary_homerooms = []
            for student_key in self.get_student_keys():
                student = self.get_student(student_key)
                if student.is_secondary:
                    if not student.homeroom in self._secondary_homerooms:
                        self._secondary_homerooms.append(student.homeroom)
        self._secondary_homerooms.sort(key=put_in_order)
        return self._secondary_homerooms

    def get_elementary_homerooms(self):
        if not self._elementary_homerooms:
            self._elementary_homerooms = []
            for student_key in self.get_elementary_student_keys():
                student = self.get_student(student_key)
                if student.is_elementary:
                    if not student.homeroom in self._elementary_homerooms:
                        self._elementary_homerooms.append(student.homeroom)
        return self._elementary_homerooms
    
    def get_all_groups(self):
        list_of_groups = []
        for key in self.get_student_keys():
            student = self.get_student(key)
            groups = student.groups()
            for group in groups:
                if not group in list_of_groups:
                    list_of_groups.append(group)
        return list_of_groups

    def get_all_grades(self):
        list_of_grades = []
        for key in self.get_student_keys():
            student = self.get_student(key)
            grade = student.grade
            if not grade in list_of_grades:
                list_of_grades.append(grade)
        return list_of_grades

    def read_in(self):
        """
        Parses file into pythonic data types, called at construction
        Reads in other information as well
        """
        for line in self.raw:

            # This MUST sync with AutoSend
            stunum, homeroom, firstlast, parent_emails, nationality, _ = line.strip('\n').split('\t')
       
            try:
                grade = self.convert_hr_to_grade(homeroom)
            except NoHomeroom:
                # Do not enroll because a student's info is not live until they've been enrolled in a homeroom
                self.document_error('student_no_homeroom', "{}: {}\n".format(stunum, firstlast))
                continue

            # This SHOULD PROBABLY sync with AutoSend, with above
            self.add(stunum,
                grade,
                homeroom,
                firstlast,
                re.split('[;,]', parent_emails),
                nationality)

        self.read_in_others()
        self.sync_others()

    def read_in_others(self):
        #self.read_in_preferred()
        self.read_in_courses()
        self.read_in_teachers()
        self.read_in_allocations()
        self.read_in_schedule()

    def read_in_preferred(self):
        self.preferred_temp = {}
        with open('preferred_names.txt') as pn:
            raw = pn.readlines()
            for line in raw:
                line = line.strip('\n')
                if not line.strip(): continue
                num, lastfirst, homeroom, first, last = line.strip('\n').split('\t')
                num = num.strip()
                try:
                    self.preferred_temp[num] = (first, last)
                except KeyError:
                    input(num)

    def sync_others(self):
        """ Round robin """
        #self.sync_preferred()   # this one to get the names right
        self.sync_courses()     # this one for reference
        self.sync_teachers()    # this one to export teacher data
        self.sync_allocations() # copy to teachers
        self.sync_schedule()    # this one to export student data
        self.sync_profile_fields()

    def sync_preferred(self):
        """
        Get the names right, modify the student data to compensate for PowerSchool's lack
        """
        for student in self.preferred_temp.keys():
            target = student
            source = self.preferred_temp[student]
            try:
                self.update(target, 'preferred', source)
            except NoSuchStudent:
                pass

    def read_in_courses(self):
        courses = SimpleReader(k_path_to_powerschool + '/' + 'ssis_courseinfosec')
        raw = courses.raw()
        for line in raw:
            course_number, full_name, _ = line.split('\t')
            moodle_short, moodle_long = convert_short_long(course_number, full_name)
            self.add_course(course_number, full_name, moodle_short, moodle_long)
            
    def sync_courses(self):
        """
        No syncing necessary, this one is for reference
        """
        pass

    def read_in_allocations(self):
        allocations = SimpleReader(k_path_to_powerschool + '/' + 'ssis_teacherallocationsec')
        raw = allocations.raw()
        self.allocation_table = {}
        for line in raw:
            line = line.strip().strip('\n')
            try:
                course_number, course_name, teacher_name, termID = line.strip('\n').split('\t')
            except ValueError:
                print("What is this?")
                input(line.split('\t'))
                continue
            if course_number not in self.allocation_table:
                self.allocation_table[course_number] = []
            self.allocation_table[course_number].append(self.teacher_info_controller.get(teacher_name))
            
    def sync_allocations(self):
        for allocation in self.allocation_table.keys():
            for teacher in self.allocation_table[allocation]:
                if not teacher: continue
                teacher = self.teacher_info_controller.get(teacher.lastfirst)
                course = self.course_info_controller.get(allocation)
                if course and teacher:
                    course.update_teachers(teacher)
                    teacher.update_courses(course)

    def read_in_teachers(self):
        teachers = SimpleReader(k_path_to_powerschool + '/' + 'ssis_teacherinfodumpall')
        raw = teachers.raw()
        for line in raw:
            try:
                lastfirst, email, title, schoolid, status, _ = line.strip('\n').split('\t')
            except ValueError:
                print("This teacher wasn't added to database: {}".format(line))
            if lastfirst in self.exclude_these_teachers_manually:
                continue
            if 1 == int(status):
                self.add_teacher(lastfirst, email, title, schoolid)
            else:
                pass # teachers with status of not 1 are no longer here

    def sync_teachers(self):
        """
        Create associations required: Students they have, courses they have
        """
        pass

    def read_in_schedule(self):
        schedule = SimpleReader(k_path_to_powerschool + '/' + 'ssis_studentscheduledumpsec')
        raw = schedule.raw()
        self.schedule = {}
        for line in raw:
            line = line.strip('\n').split('\t')
            course_number, section_details, termID, teacher, student, studentID, _ = line
            if not course_number in self.schedule:
                self.schedule[course_number] = []
            self.schedule[course_number].append((teacher, studentID))

    def sync_schedule(self):
        """
        Put courses and teachers into student data, so they can be exported
        """
        for key in self.schedule.keys():
            for row in self.schedule[key]:
                teacher_lastfirst, studentID = row
                course = self.course_info_controller.get(key)
                teacher = self.teacher_info_controller.get(teacher_lastfirst)
                student = self.student_info_controller.get(studentID)
                if not student:
                    self.document_error("sync_schedule", row)
                    continue
                if teacher and student:
                    teacher.update_students(student)
                if student and course and teacher:
                    student.update_teachers(course, teacher)
                    student.update_courses(course, teacher)

    def sync_profile_fields(self):
        """
        Input profile fields that students need as it goes around.
        """

        for student_key in self.get_student_keys():
            student = self.get_student(student_key)
            courses = student.courses()
            contacts = ""
            for course_num in courses:
                for course_key in self.course_info_controller.keys():
                    course  = self.course_info_controller.get(course_key)
                    if course.moodle_short == course_num:
                        break
                teacher_username = student.teachers().get(course_num)
                for teacher_key in self.teacher_info_controller.keys():
                    teacher = self.teacher_info_controller.get(teacher_key)
                    if teacher.username == teacher_username:
                        break
                if not teacher:
                    print(teacher_username)
                d = {}
                d['student'] = student.lastfirst
                d['teacher'] = teacher.first + " " + teacher.last
                d['teacher_email'] = teacher.email
                d['course_name'] = course.course_name
                d['course_url'] = course_reference.get(course.moodle_short)
                if d['course_url']:
                    d['course_url'] = "http://dragonnet.ssis-suzhou.net/course/view.php?id={}".format( d['course_url'].strip() )
                    contacts += "{teacher} teaches <a href=\"{course_url}\">{course_name}</a>: <a href=\"mailto:{teacher_email}\">{teacher_email}</a><br />".format(**d)
                else:
                    contacts += "{teacher} teaches {course_name}: <a href=\"mailto:{teacher_email}\">{teacher_email}</a><br />".format(**d)
            student.profile_field_contacts = contacts.replace(',', '')  # comma in here would cause a problem
 
    def convert_hr_to_grade(self, hr):
        if not hr: raise NoHomeroom(hr)
        if not re.match(r'^[a-zA-Z]', hr):
            return int(re.sub(r'[a-zA-Z]', '', hr))
        else:
            hr = hr.upper()
            result = {'K':0, 'R':-1, 'G':-2, 'P':-3, 'N':-4}.get(hr[0], None)
            if result == None: raise UnknownGrade(hr)
            return result

    def add(self, *args, **kwargs):
        """
        Takes data and sends it on to controller
        """
        self.student_info_controller.add(*args, **kwargs)

    def add_course(self, *args, **kwargs):
        self.course_info_controller.add(*args, **kwargs)

    def add_teacher(self, *args, **kwargs):
        self.teacher_info_controller.add(*args, **kwargs)

    def add_allocation(self, *args, **kwargs):
        self.allocation_info_controller.add(*args, **kwargs)

    def add_schedule(self, *args, **kwargs):
        self.schedule_info_controller.add(*args, **kwargs)

    def update(self, item, key, value):
        self.student_info_controller.update(item, key, value)

    # The following messages are meant to be for convenience and testing

    def output(self, *args, **kwargs):
        self.student_info_controller.output()

    def output_filter(self, *args, **kwargs):
        self.student_info_controller.output_filter(*args, **kwargs)

    def courses_output(self):
        self.course_info_controller.output()

    def students_output(self):
        self.student_info_controller.output()

    def teachers_output(self):
        self.teacher_info_controller.output()

    def get_course_keys(self):
        return list(self.course_info_controller.keys())

    def get_course(self, course_id):
        return self.course_info_controller.get(course_id)

    def get_student(self, student_id):
        return self.student_info_controller.get(student_id)

    def get_students_by_family_id(self, family_id):
        info = self.student_info_controller
        return [info.get_student(student_key) for student_key in info.get_student_keys()
                if info.get_student(student_key).family_id == family_id]

    def get_family_emails(self, family_id):
        emails = []
        for student in self.get_students_by_family_id(family_id):
            emails.extend( student.parent_emails )
        return set(emails)

    def get_student_keys(self, secondary=False):
        """
        Returns all of them.
        """
        if secondary:
            return [s for s in list(self.student_info_controller.keys()) if self.student_info_controller.get(s).is_secondary]
        else:
            return list(self.student_info_controller.keys())

    def get_secondary_student_keys(self):
        return self.get_student_keys(secondary=True)

    def get_elementary_student_keys(self):
        return [s for s in list(self.student_info_controller.keys()) if self.student_info_controller.get(s).is_elementary]

    def get_teacher_keys(self):
        return list(self.teacher_info_controller.keys())

    def get_teacher(self, teacher_id):
        return self.teacher_info_controller.get(teacher_id)

    def get_students_filter(self, **kwargs):
        l = list(self.student_info_controller.keys())
        for key in self.student_info_controller.keys():
            this = self.get_student(key)
            if not this:
                continue
            if this.compare_kwargs(**kwargs):
                yield this

def check_is_in_preferred_list(this):
    return this.compare_kwargs(num=35263)

if __name__ == "__main__":

    students = Students()
    for student_key in students.get_student_keys():
        student = students.get_student(student_key)
        if student.has_preferred_name:
            print(student.first, student.last)
            print(student.preferred_first)
    #students.courses_output()
    #print("Here are the ones with ???:")
    #students.output_filter(check_is_in_preferred_list)
    #students.teachers_output()
    #students.courses_output()
    #students.students_output()


