"""
Holds all information about a particular student
Reads in from Powerschool file
"""

from psmdlsyncer.files import AutoSendFile, SimpleReader
from psmdlsyncer.exceptions import BasicException, NoSuchStudent
from psmdlsyncer.models import Student, Course, Teacher, Schedule, Allocation, Controller
from psmdlsyncer.sql import ServerInfo
from psmdlsyncer.utils import NS

import datetime
from psmdlsyncer.files import clear_folder

from psmdlsyncer.settings import define_command_line_arguments, config_get_section_attribute, logging

import re
from collections import defaultdict

def put_in_order(what, reverse=False):
    what = what.upper()
    result = 1 # elementary don't have LEARN
    if reverse:
        trans = {'L':8,'E':7,'A':6,'R':5,'N':4,'S':3,'SWA':2,'JS':1}
    else:
        trans = {'L':1,'E':2,'A':3,'R':4,'N':5,'S':6,'SWA':7, 'JS':8}
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
    elif re.sub('[1..9]', '', what):
        result = ord(re.sub('[1..9]', '', what)[0])
    return result

class Tree:

    exclude_these_teachers_manually = ['Sections, Dead', 'User, Drews Test']

    def __init__(self):
        """
        Does the work of reading in basic information from file, creates native Python structures
        StudentNumber\tHomeroom\tLastFirst\tguardianemails
        """
        self.settings = define_command_line_arguments(
                               'verbose', 'log_level', 'dry_run', 'teachers', 'courses',
                               'students', 'email_list', 'families', 'parents',
                               'automagic_emails', 'profiles', 'input_okay', 'updaters',
                               'enroll_cohorts', 'enroll_courses', 'remove_enrollments', inspect_student=False)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.path_to_powerschool = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')
        self.path_to_output = config_get_section_attribute('DIRECTORIES', 'path_to_output')
        self.student_info_file = AutoSendFile('dist', 'studentinfo')
        self.student_info_controller = Controller(Student)
        self.course_info_controller = Controller(Course)
        self.teacher_info_controller = Controller(Teacher)
        self.schedule_info_controller = Controller(Schedule)
        self.allocation_info_controller = Controller(Allocation)
        self.user_data = ServerInfo().get_student_info()
        self.read_in()
        homerooms = None
        self._secondary_homerooms = None
        self._elementary_homerooms = None
        self.get_homerooms()
        self.get_secondary_homerooms()
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
        for line in self.student_info_file.content():
            # This MUST sync with AutoSend
            try:
                stunum, stuid, grade, homeroom, firstlast, DOB, parent_emails, entry_date, nationality = line
            except ValueError:
                self.logger.warn(line)
                self.logger.warn("Skipping above line... did one of the fields have a newline character in there?")
                continue

            if not homeroom:
                self.logger.warn('This student does not have a homeroom {}: {}'.format(stunum, firstlast))
            
            try:
                grade = int(grade)
            except ValueError:
                self.logger.warn('This student has a non-integer grade {}: {}'.format(stunum, firstlast))
                grade = 0
            new_student = self.add(stunum,
                stuid, grade,
                homeroom,
                self.convert_hr_to_sortable(homeroom),
                firstlast,DOB,                                   
                re.split('[;,]', parent_emails),
                datetime.datetime.strptime(entry_date, '%m/%d/%Y'),
                nationality,
                user_data=self.user_data)

        self.read_in_others()
        self.sync_others()

    def read_in_others(self):
        if self.settings.courses:
            self.read_in_courses()
            self.read_in_schedule()
        if self.settings.teachers:
            self.read_in_teachers()
            self.read_in_allocations()

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
        if self.settings.courses:
            self.sync_courses()     # this one for reference
            self.sync_schedule()    # this one to export student data
        if self.settings.teachers:
            self.sync_teachers()    # this one to export teacher data
            self.sync_allocations() # copy to teachers

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
        for line in AutoSendFile('sec', 'courseinfo').content():
            course_number, full_name = line
            moodle_short, moodle_long = convert_short_long(course_number, full_name)
            self.add_course(course_number, full_name, moodle_short, moodle_long)
            
    def sync_courses(self):
        """
        No syncing necessary, this one is for reference
        """
        pass

    def read_in_allocations(self):
        allocations = AutoSendFile('sec', 'teacherallocations')
        raw = allocations.content()
        self.allocation_table = defaultdict(list)
        for line in raw:
            course_number, course_name, teacher_name, status, termID = line
            teacher = self.teacher_info_controller.get(teacher_name)
            if not teacher:
                self.logger.info("No teacher by this name?: {}".format(teacher_name))
                continue
            self.allocation_table[course_number].append(self.teacher_info_controller.get(teacher_name))

    def sync_allocations(self):
        self.logger.info("Syncing teachers")
        for allocation in self.allocation_table.keys():
            for teacher in self.allocation_table[allocation]:
                if not teacher: 
                    self.logger.warn("no teacher?")
                    self.logger.warn(allocation)
                    self.logger.warn(self.allocation_table[allocation])
                    continue
                teacher = self.teacher_info_controller.get(teacher.lastfirst)
                course = self.course_info_controller.get(allocation)
                if course and teacher:
                    self.logger.debug("Syncing teacher {} with course {}".format(teacher, course))
                    course.update_teachers(teacher)
                    teacher.update_courses(course)

    def read_in_teachers(self):
        teachers = AutoSendFile('dist', 'staffinfo')
        raw = teachers.content()
        for line in raw:
            try:
                num, lastfirst, email, title, schoolid, staff_status = line
            except ValueError:
                self.logger.info("This teacher wasn't added to database: {}".format(line))
                continue
            if 1 == int(staff_status):
                self.add_teacher(lastfirst, num, email, title, staff_status, schoolid)

    def sync_teachers(self):
        """
        Create associations required: Students they have, courses they have
        """
        pass

    def read_in_schedule(self):
        schedule = AutoSendFile('sec', 'studentschedule')
        raw = schedule.content()
        self.schedule = defaultdict(list)
        for line in schedule.content():
            course_number, periods, session_number, teacher, teacherID, student, studentID = line
            self.schedule[course_number].append((teacher, studentID))

    def sync_schedule(self):
        """
        Put courses and teachers into student data, so they can be exported
        """
        self.logger.info("Syncing schedule information")
        for key in self.schedule.keys():
            for row in self.schedule[key]:
                teacher_lastfirst, studentID = row
                course = self.course_info_controller.get(key)
                teacher = self.teacher_info_controller.get(teacher_lastfirst)
                student = self.student_info_controller.get(studentID)
                if not student:
                    self.logger.warn("sync_schedule problem: {}".format(row))
                    continue
                if teacher and student:
                    self.logger.debug("Syncing teacher {} with student {}".format(teacher, student))
                    teacher.update_students(student)
                if student and course and teacher:
                    self.logger.debug("Syncing student {} with teacher {} with course {}".format(student, teacher, course))
                    student.update_teachers(course, teacher)
                    student.update_courses(course, teacher)

    def convert_hr_to_integer(self, hr):
        return {'K':-1, 'R':-2, 'G':-3, 'P':-4, 'N':-5}.get(hr[0], put_in_order(hr, reverse=True))
 
    def convert_hr_to_grade(self, hr):
        if not hr: raise NoHomeroom(hr)
        if not re.match(r'^[a-zA-Z]', hr):
            return int(re.sub(r'[a-zA-Z]', '', hr))
        else:
            hr = hr.upper()
            result = {'K':-1, 'R':-2, 'G':-3, 'P':-4, 'N':-5}.get(hr[0], None)
            if result == None: raise UnknownGrade(hr)
            return result

    def convert_hr_to_sortable(self, hr):
        return 0 #TODO: Use put_in_order, right?
        return self.convert_hr_to_grade(hr) + (1 / self.convert_hr_to_integer(hr))

    def add(self, *args, **kwargs):
        """
        Takes data and sends it on to controller
        """
        return self.student_info_controller.add(*args, **kwargs)

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

    def get_family(self, idnumber):
        if len(idnumber) == 5:
            idnumber = idnumber[:4]
        students = []
        for num in range(0, 9):
            student = self.get_student(idnumber + str(num))
            if student:
                students.append(student)
        return students

    def get_all_student_keys(self):
        return list(self.student_info_controller._db.keys())

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
    print('Full Name,User Name,Email\n')
    for student_key in students.get_student_keys():
        student = students.get_student(student_key)
        sf = NS()
        sf.take_dict(student)
        if student.grade == 5:
            print(sf('{first} {last},{username},{email}'))
    #students.courses_output()
    #print("Here are the ones with ???:")
    #students.output_filter(check_is_in_preferred_list)
    #students.teachers_output()
    #students.courses_output()
    #students.students_output()


