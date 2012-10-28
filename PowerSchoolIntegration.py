from Students import Students
from utils.Bulk import MoodleCSVFile
from utils.Utilities import no_whitespace_all_lower, convert_short_long, Categories, department_heads, department_email_names
from utils.FilesFolders import clear_folder
from utils.DB import ServerInfo
from utils.DB import NoStudentInMoodle, StudentChangedName, NoEmailAddress
from ReadFiles import SimpleReader
import re
import datetime
import os
from utils.Formatter import Smartformatter

from ModifyMoodleUsers import StudentModifier

from Constants import k_path_to_output, k_path_to_powerschool

import subprocess

class InfiniteLoop(Exception):
    pass

class PowerSchoolIntegrator:
    """
    Class that runs a script that automagically syncs PowerSchool data with the dnet server
    """

    def __init__(self):
        self.run_newaliases = False
        print('------------------------------------------------------')
        print(datetime.datetime.today())
        self.students = Students()
        self.build_student_courses()
        self.build_teachers()
        self.build_courses()
        self.build_students()
        #self.build_parents(students)
        self.build_automagic_emails()

        #self.build_student_list(students)
        #self.build_opening_table(students)
        #self.create_simple_accounts()
        #self.compile_student_parent_emails(students)

        #self.setup_idnumbers(students)
        print('------------------------------------------------------')

    def build_courses(self):
        """
        ### TODO ###
        Implement this in totally different way, looking for course names
        of those that actually have enrollments rather than through powerschool file
        ############
        """
        source = SimpleReader(k_path_to_powerschool + '/' + 'ssis_courseinfosec')
        raw = source.raw()
        courses = {}
        summaries = {}
        with open(k_path_to_output + '/' + 'moodle_courses.txt', 'w') as f:
            f.write('fullname,shortname,category,summary,groupmode\n')
            for line in raw:
                orig_short, orig_long, _ = line.strip('\n').split('\t')
                short, long = convert_short_long(orig_short, orig_long)
                courses[short] = long
                if short not in summaries.keys():
                    summaries[short] = ""
                summaries[short] += short + " "

            for course in courses.keys():
                output = {}
                output['long'] = courses[course]
                output['course'] = course.strip()
                output['category'] = Categories(course)
                output['summary'] = summaries[course]
                output['groupmode'] = 2  #groupsvisible
                                         #output['maxupload'] = '209715200'
                f.write("{long},{course},{category},{summary},{groupmode}\n".format(**output))


    def build_teachers(self):
        output_file = MoodleCSVFile(k_path_to_output + '/' + 'teachers_moodle_file.txt')
        output_file.build_headers(['username', 'firstname', 'lastname', 'password', 'email', 'maildigest', 'course_', 'cohort_', 'type_'])

        # First do heads of department

        heads = {}
        for course_key in self.students.get_course_keys():
            course = self.students.get_course(course_key)
            these_heads = course.heads
            if not these_heads:
                continue
            for head in these_heads:
                if head:
                    if not head in list(heads.keys()):
                        heads[head] = []
                    heads[head].append(course.moodle_short)

        for head in list(heads.keys()):
            courses = heads[head]
            row = output_file.factory()
            row.build_username(head)
            row.build_firstname("firstname")
            row.build_lastname("lastname")
            row.build_password('changeme')
            row.build_email(head+'@ssis-suzhou.net')
            row.build_maildigest('1')
            row.build_course_(courses)
            row.build_cohort_(['departHEADS'])
            row.build_type_(['3' for c in courses])  # non-editing teacher
            output_file.add_row(row)


        for teacher_key in self.students.teacher_info_controller.keys():
            teacher = self.students.teacher_info_controller.get(teacher_key)
            row = output_file.factory()
            row.build_username(teacher.username)
            row.build_firstname(teacher.first)
            row.build_lastname(teacher.last)
            row.build_password('changeme')
            row.build_email(teacher.email)
            row.build_maildigest('1')
            if teacher.courses:
                row.build_course_([c for c in teacher.courses()])
            else:
                row.build_course_([])
                self.students.document_error('teacher_no_courses', teacher)
            row.build_cohort_(teacher.derive_cohorts())
            row.build_type_(['2' for c in teacher.courses()])
            output_file.add_row(row)

        output_file.output()

        output_file = MoodleCSVFile(k_path_to_output + '/' + 'teachers_moodle_classic.txt')
        output_file.build_headers(['username', 'firstname', 'lastname', 'password', 'email', 'course_', 'type_'])

        for teacher_key in self.students.teacher_info_controller.keys():
            teacher = self.students.teacher_info_controller.get(teacher_key)
            if teacher.courses():
                row = output_file.factory()
                row.build_username(teacher.username)
                row.build_firstname(teacher.first)
                row.build_lastname(teacher.last)
                row.build_password('changeme')
                row.build_email(teacher.email)
                row.build_maildigest('1')
                row.build_course_([c for c in teacher.courses()])
                row.build_type_(['2' for c in teacher.courses()])
                output_file.add_row(row)
            else:
                self.students.document_error('teacher_no_courses', teacher)
        output_file.output()


    def build_parents(self):
        """
        MUST IMPLEMENT AS CREATING A DATABASE
        """

        output_file = MoodleCSVFile(k_path_to_output + '/' + 'moodle_parents.txt')
        output_file.build_headers(['username', 'firstname', 'lastname', 'password', 'email', 'course_', 'group_', 'cohort_', 'type_'])

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)

            parent_emails = student.parent_emails
            if not parent_emails:
                self.students.document_error('student_no_parent_email', student)
                continue
            parent_email = parent_emails[0]
            if not parent_email:
                self.students.document_error('student_no_parent_email', student)
                continue

            if student.courses():
                row = output_file.factory()
                row.build_username(parent_email)
                row.build_firstname('Parent of ')
                row.build_lastname(student.first + student.last)
                row.build_password('changeme')
                row.build_email(parent_email)
                row.build_course_(student.courses())
                row.build_group_(student.groups())
                cohorts = ['parentsALL']
                if student.is_secondary:
                    cohorts.append('parentsSEC')
                elif student.is_primary:
                    cohorts.append('parentsELEM')
                if student.is_korean:
                    cohorts.append('parentsKOREAN')
                row.build_cohort_(cohorts)
                row.build_type_(["1" for c in student.courses()])
                output_file.add_row(row)

        output_file.output()



    def build_opening_table(self):
        open(k_path_to_output + '/' + 'table.txt', 'w').close()
        for course_key in self.students.get_course_keys():
            course = self.students.get_course(course_key)
            teachers = course.teachers()
            table = """<table border="1" cellpadding="10" cellspacing="10" align="center" style="width: 300px;"><caption>Teacher Contact Information</caption>
    <tbody>{inside}</tbody></table>"""
            inside = """<tr><td>{username}@ssis-suzhou.net</td></tr>"""
            with open(k_path_to_output + "/" + "table.txt", 'a') as f:
                f.write(course.moodle_short + '\n')
                body = ""
                for teacher in teachers:
                    if teacher == "deadsections":
                        continue
                    d = {'username':teacher}
                    body += inside.format(**d)
                d['inside'] = body
                f.write(table.format(**d) + '\n\n')

    def build_student_courses(self):
        with open(k_path_to_output + '/' + 'student_courses', 'w') as f:
            for student_key in self.students.get_student_keys():
                student = self.students.get_student(student_key)
                d = student.__dict__.copy()
                d['courses'] = ",".join(student.courses())
                if student.homeroom in self.students.get_secondary_homerooms():
                    if student.courses():
                        f.write("{num}\t{courses}\n".format(**d))


    def build_students(self, verify=False):
        """
        Go through each student and do what is necessary to actually sync powerschool data
        """
        ## CLASSIC

        output_file = MoodleCSVFile(k_path_to_output + '/' + 'classic_users.txt')
        output_file.build_headers(['username', 'idnumber', 'firstname', 'lastname', 'password', 'email', 'course_'])
        verify and print("Verifying...")
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            if student.homeroom in self.students.get_secondary_homerooms():
                if student.courses():
                    row = output_file.factory()
                    row.build_username(student.username)
                    row.build_idnumber(student.num)
                    row.build_firstname(student.first)
                    row.build_lastname(student.last)
                    row.build_password('changeme')
                    row.build_email(student.email)
                    row.build_course_(student.courses())
                    if verify:
                        if len(student.groups()) != len(student.courses()):
                            input("There shouldn't be any students who have an unequal amount of groups and courses! But there is!")
                    output_file.add_row(row)
                else:
                    self.students.document_error('students_no_courses', student)
        output_file.output()

        ## DRAGONNET 2

        server_information = ServerInfo()
        modify = StudentModifier()

        output_file = MoodleCSVFile(k_path_to_output + '/' + 'moodle_users.txt')
        output_file.build_headers(['username', 'idnumber', 'firstname', 'lastname', 'password', 'email',
                                   'profile_field_contacts', 'course_', 'group_', 'cohort_', 'type_'])
        verify and print("Verifying...")

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            if student.homeroom in self.students.get_secondary_homerooms() and student.courses():
                # Compare to the original database
                continue_until_no_errors = True
                times_through = 0
                while continue_until_no_errors:
                    error = False
                    try:
                        server_information.check_student(student)

                    except NoStudentInMoodle:
                        #error = True
                        print("Student does not have an account:\n{}".format(student))
                        modify.new_student(student)

                    except StudentChangedName:
                        #error = True
                        print("Student has had his or her account name changed: {}, {}".format(student.num, student.username))
                        modify.change_name(student)

                    except NoEmailAddress:
                        error = True
                        modify.no_email(student)

                    continue_until_no_errors = error
                    times_through += 1
                    if times_through > 100:
                        raise InfiniteLoop


                # Make the output file
                row = output_file.factory()
                row.build_username(student.username)
                row.build_idnumber(student.num)
                row.build_firstname(student.first)
                row.build_lastname(student.last)
                row.build_password('changeme')
                row.build_email(student.email)

                row.build_profile_field_contacts(student.profile_field_contacts)
                row.build_course_(student.courses())
                row.build_group_(student.groups())
                row.build_cohort_(student.cohorts())
                row.build_type_(["1" for c in student.courses()])
                if verify:
                    if len(student.groups()) != len(student.courses()):
                        self.students.document_error('verification_failed', student)
                output_file.add_row(row)
        output_file.output()

        with open(k_path_to_output + '/' + 'email_users.txt', 'w') as f:
            for student_key in self.students.get_student_keys():
                student = self.students.get_student(student_key)
                if student.homeroom in self.students.get_secondary_homerooms():
                    d = student.__dict__.copy()
                    d['sep'] = ':'
                    d['newline'] = '\n'
                    d['tab'] = '\t'
                    d['password'] = 'changeme'
                    f.write("{preferred_name}{newline}".format(**d))
                    f.write("{username}{sep}{password}{sep}{sep}{sep}{num}{sep}/home/{username}{sep}/bin/bash{newline}".format(**d))

        clear_folder(k_path_to_output + '/' + 'homerooms')
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            if student.homeroom in self.students.get_secondary_homerooms():
                    with open(k_path_to_output + '/' + 'homerooms/homeroom{}.txt'.format(student.homeroom), 'a') as f:
                        d = student.__dict__.copy()
                        d['sep'] = ':'
                        d['newline'] = '\n'
                        d['tab'] = '\t'
                        d['message'] = "These are your credentials for ALL your DragonNet accounts and email. You are expected to use these accounts responsibly. DO NOT SHARE."
                        f.write("{username}{newline}".format(**d))

        clear_folder(k_path_to_output + '/' + 'parents')
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            if student.homeroom in self.students.get_secondary_homerooms():
                    with open(k_path_to_output + '/' + 'parents/homeroom{}.txt'.format(student.homeroom), 'a') as f:
                        d = student.__dict__.copy()
                        d['sep'] = ':'
                        d['newline'] = '\n'
                        d['tab'] = '\t'
                        d['parent_emails'] = '\n'.join([s for s in student.parent_emails if s])
                        d['message'] = "These are your credentials for ALL your DragonNet accounts and email. You are expected to use these accounts responsibly. DO NOT SHARE."
                        f.write("{parent_emails}{newline}".format(**d))


    def build_emails_for_powerschool(self):

        with open(k_path_to_output + '/' + 'powerschool_email_output.txt', 'w') as output:
            output.write('Student_Number\tLastFirst\tLTIS_AS_email\n')
            for student_key in self.students.student_info_controller.keys():
                student = self.students.student_info_controller.get(student_key)
                d = student.__dict__.copy()
                d['tab'] = "\t"
                d['newline'] = "\n"
                output.write("{num}{tab}{lastfirst}{tab}{email}{newline}".format(**d))


    def build_emails(self):

        with open(k_path_to_output + '/' + 'email_output.txt', 'w') as output:
            for student_key in self.students.student_info_controller.keys():
                student = self.students.student_info_controller.get(student_key)
                d = student.__dict__.copy()
                d['tab'] = "\t"
                d['newline'] = "\n"
                output.write("{num}{tab}{grade}{tab}{lastfirst}{tab}{homeroom}{tab}{email}{newline}".format(**d))

    def list_courses(self):
        the_courses = []
        for course_key in self.students.course_info_controller.keys():
            course = self.students.get_course(course_key)
            the_courses.append(course.moodle_short)
        the_courses.sort()
        with open(k_path_to_output + '/' + 'list_of_courses.txt', 'w') as f:
            [f.write("{}\n".format(c)) for c in the_courses]

    def create_simple_accounts(self):
        from utils.Utilities import no_whitespace_all_lower

        l = ["Bjoerkgaard, Maria", "Fowles, Rewa Margaret", "Liu, Wei-Chi", "Mo, Akane", "Paavola, Ira Aurora", "Roem, Yasmin Andinasari", "Yang, Szu-Kai", "Zheng, Ting-Yu"]
        courses = "TEDESSH1112"
        with open(k_path_to_output + '/' + 'simple_users.txt', 'w') as f:
            f.write("username,firstname,lastname,password,email,course1\n")
            for student in l:
                last, first = student.split(', ')
                username = no_whitespace_all_lower(first + last)
                username = username[:20]
                f.write(username+","+first.strip()+","+last.strip()+",changeme,"+ username + "@student.ssis-suzhou.net," + courses+"\n")

    def compile_student_parent_emails(self):
       list_of_groups = []
       for key in self.students.get_student_keys():
           student = self.students.get_student(key)
           groups = student.groups()
           for group in groups:
               if not group in list_of_groups:
                   list_of_groups.append(group)

       students_where = k_path_to_output + '/' + 'studentsbyclasses'
       clear_folder(students_where)
       parents_where = k_path_to_output + '/' + 'parentsbyclasses'
       clear_folder(parents_where)
       for group in list_of_groups:
           teacher = re.sub(r'[^a-z]', '', group)
           d = {'studentswhere':students_where, 'parentswhere':parents_where}
           d['teacher'] = teacher
           today = datetime.date.today()
           d['date'] = today.strftime("%b%d").upper()
           d['ext'] = ".txt"
           d['group'] = group
           d['newline'] = '\n'
           with open('{studentswhere}/{teacher}{ext}'.format(**d), 'a') as f:
              f.write('{group}{newline}'.format(**d))
              count = 0
              for key in self.students.get_student_keys():
                  student = self.students.get_student(key)
                  groups = student.groups()
                  if group in groups:
                      d['studentemail'] = student.email
                      f.write("{studentemail}{newline}".format(**d))
                      count += 1
              f.write("Total of {} students.\n\n".format(count))

           with open('{parentswhere}/{teacher}PARENTS{ext}'.format(**d), 'a') as f:
              f.write('{group}PARENTS{newline}'.format(**d))
              for key in self.students.get_student_keys():
                 student = self.students.get_student(key)
                 groups = student.groups()
                 if group in groups:
                    d['parentemails'] = "\n".join(student.parent_emails)
                    f.write("{parentemails}{newline}".format(**d))
              f.write('\n')

    def setup_idnumbers(self):
        with open('../output/idnumbers.txt', 'w') as f:
            f.write("username,idnumber,firstname,lastname,password,email\n")
            for student_key in self.students.get_student_keys():
                student = self.students.get_student(student_key)
                d = student.__dict__.copy()
                f.write('{username},{num},{first},{last},changeme,{email}\n'.format(**d))


    def build_automagic_emails(self):
        try:
            path = '/home/lcssisadmin'
            self.on_server = os.path.exists(path)
            path = '/etc/postfix/aliases'
        except OSError:
            self.on_server = False
            
        if not self.on_server:
            path = '../postfix'
        d = {'path':path}
        d['ext'] = '.txt'

        # The clear_folder routine erases all files in a certain folder
        # That has implications for postfix (when we're on the server), because
        # if you delete the .db files then postfix won't work. That is bad.
        # So, tell clear_folder to exclude them
        exclude_db_files = lambda x: x.endswith('.db')
        clear_folder('{path}'.format(**d), exclude=exclude_db_files) 
        # 

        clear_folder('{path}/grades'.format(**d))
        clear_folder('{path}/homerooms'.format(**d))
        clear_folder('{path}/classes'.format(**d))
        clear_folder('{path}/parentlink'.format(**d))
        clear_folder('{path}/teacherlink'.format(**d))
        clear_folder('{path}/special'.format(**d))
        clear_folder('{path}/departments'.format(**d))

        setup_postfix = '{path}/parentsKOREAN{ext}'.format(**d)
        with open(setup_postfix, 'w') as f:
            f.write("usebccparentsKOREAN: :include:{path}/special/usebccparentsKOREAN{ext}\n".format(**d))
        setup_postfix = '{path}/special/usebccparentsKOREAN{ext}'.format(**d)
        with open(setup_postfix, 'w') as f:
            f.write('usebccparentsKOREANmanual')
        setup_postfix = '{path}/parentsCHINESE{ext}'.format(**d)
        with open(setup_postfix, 'w') as f:
            f.write("usebccparentsCHINESE: :include:{path}/special/usebccparentsCHINESE{ext}\n".format(**d))
        setup_postfix = '{path}/special/usebccparentsCHINESE{ext}'.format(**d)
        with open(setup_postfix, 'w') as f:
            f.write('usebccparentsCHINESEmanual')

        done_homerooms = []
        done_grades = []

        for student_key in self.students.get_elementary_student_keys():
            student = self.students.get_student(student_key)
            d['grade'] = student.grade
            if d['grade'] <= 0:
                d['grade'] = {0: 'K', -1: 'R', -2: 'G', -3:'PK', -4:'N'}.get(d['grade'])
            d['homeroom'] = student.homeroom.upper().strip()

            ## SET UP GRADES
            setup_postfix = '{path}/grades{ext}'.format(**d)
            if not d['grade'] in done_grades:
                with open(setup_postfix, 'a') as f:
                    f.write("usebccparents{grade}: :include:{path}/grades/usebccparents{grade}{ext}\n".format(**d))
                done_grades.append(d['grade'])

            setup_postfix = '{path}/grades/usebccparents{grade}{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')

            ## SETUP HOMEROOMS
            setup_postfix = '{path}/homerooms{ext}'.format(**d)
            if not d['homeroom'] in done_homerooms:
                with open(setup_postfix, 'a') as f:
                    f.write("usebccparents{homeroom}: :include:{path}/homerooms/usebccparents{homeroom}{ext}\n".format(**d))
                done_homerooms.append(d['homeroom'])

            setup_postfix = '{path}/homerooms/usebccparents{homeroom}{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')

            # SETUP SPECIAL
            if student.is_korean:
                if 'mommachen' in " ".join(student.parent_emails):
                    print(student)
                    input()
                setup_postfix = "{path}/special/usebccparentsKOREAN{ext}".format(**d)
                with open(setup_postfix, 'a') as f:
                    f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')
            if student.is_chinese:
                setup_postfix = "{path}/special/usebccparentsCHINESE{ext}".format(**d)
                with open(setup_postfix, 'a') as f:
                    f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')


        done_homerooms = []
        done_grades = []
        done_groups = []
        added_teachers_grade = {}
        added_teachers_hr = {}

        # SECONDARY
        for student_key in self.students.get_secondary_student_keys():
            student = self.students.get_student(student_key)
            d['grade'] = student.grade
            d['homeroom'] = student.homeroom
            d['username'] = student.username
            d['homeroom_teacher'] = student.get_homeroom_teacher()

            ## SET UP PARENTLINK
            setup_postfix = '{path}/parentlink{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("{username}PARENTS: :include:{path}/parentlink/{username}PARENTS{ext}\n".format(**d))

            setup_postfix = '{path}/parentlink/{username}PARENTS{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')

            ## SET UP TEACHERLINK
            setup_postfix = '{path}/teacherlink{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("{username}TEACHERS: :include:{path}/teacherlink/{username}TEACHERS{ext}\n".format(**d))

            setup_postfix = '{path}/teacherlink/{username}TEACHERS{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                teachers = student.teachers()
                f.write("\n".join([teachers[k]+"@ssis-suzhou.net" for k in teachers.keys()]) + '\n')

            # SET UP HOMEROOMLINK
            setup_postfix = '{path}/homeroomlink{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("{username}HR: {homeroom_teacher}@ssis-suzhou.net\n".format(**d))

            ## SET UP GRADES
            setup_postfix = '{path}/grades{ext}'.format(**d)
            if not d['grade'] in done_grades:
                added_teachers_grade[d['grade']] = []
                with open(setup_postfix, 'a') as f:
                    f.write("usebccstudents{grade}: :include:{path}/grades/usebccstudents{grade}{ext}\n".format(**d))
                    f.write("usebccparents{grade}: :include:{path}/grades/usebccparents{grade}{ext}\n".format(**d))
                    f.write("teachers{grade}: :include:{path}/grades/teachers{grade}{ext}\n".format(**d))
                done_grades.append(d['grade'])

            setup_postfix = '{path}/grades/usebccstudents{grade}{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                if student.email.strip():
                    f.write(student.email.strip()+'\n')

            setup_postfix = '{path}/grades/usebccparents{grade}{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')

            setup_postfix = '{path}/grades/teachers{grade}{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                for teacher in student.get_teacher_names():
                    if not teacher in added_teachers_grade[d['grade']]:
                        f.write(teacher + '@ssis-suzhou.net\n')
                        added_teachers_grade[d['grade']].append(teacher)

            ## SETUP HOMEROOMS
            setup_postfix = '{path}/homerooms{ext}'.format(**d)
            if not d['homeroom'] in done_homerooms:
                added_teachers_hr[d['homeroom']] = []
                with open(setup_postfix, 'a') as f:
                    f.write("usebccstudents{homeroom}: :include:{path}/homerooms/usebccstudents{homeroom}{ext}\n".format(**d))
                    f.write("usebccparents{homeroom}: :include:{path}/homerooms/usebccparents{homeroom}{ext}\n".format(**d))
                    f.write("teachers{homeroom}: :include:{path}/homerooms/teachers{homeroom}{ext}\n".format(**d))
                homeroom_teacher = student.get_homeroom_teacher()
                if homeroom_teacher:
                    with open('{path}/homerooms/usebccparents{homeroom}{ext}'.format(**d), 'a') as f:
                        f.write(student.get_homeroom_teacher() + '@ssis-suzhou.net\n')
                done_homerooms.append(d['homeroom'])

            setup_postfix = '{path}/homerooms/usebccstudents{homeroom}{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                if student.email.strip():
                    f.write(student.email.strip() + '\n')

            setup_postfix = '{path}/homerooms/usebccparents{homeroom}{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')

            setup_postfix = '{path}/homerooms/teachers{homeroom}{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                if not teacher in added_teachers_hr[d['homeroom']]:
                    f.write(teacher + '@ssis-suzhou.net\n')
                    added_teachers_hr[d['homeroom']].append(teacher)

            # SETUP SPECIAL
            if student.is_korean:
                setup_postfix = "{path}/special/usebccparentsKOREAN{ext}".format(**d)
                with open(setup_postfix, 'a') as f:
                    f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')
            if student.is_chinese:
                setup_postfix = "{path}/special/usebccparentsCHINESE{ext}".format(**d)
                with open(setup_postfix, 'a') as f:
                    f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')

            ##  SETUP CLASSES
            for group in student.groups():
                d['group'] = group
                if not group in done_groups:
                    done_groups.append(group)
                    setup_postfix = '{path}/classes{ext}'.format(**d)
                    with open(setup_postfix, 'a') as f:
                        f.write("{group}: :include:{path}/classes/{group}{ext}\n".format(**d))

                setup_postfix = '{path}/classes/{group}{ext}'.format(**d)
                with open(setup_postfix, 'a') as f:
                    if student.email.strip():
                        f.write(student.email.strip() + '\n')

                setup_postfix = '{path}/classes/{group}PARENTS{ext}'.format(**d)
                with open(setup_postfix, 'a') as f:
                    f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')


        ##  SETUP DEPARTMENTS
        depart_dict = {}
        for teacher_key in self.students.get_teacher_keys():
            teacher = self.students.get_teacher(teacher_key)
            departments = teacher.get_departments()
            for department in departments:
                d_email_name = department_email_names.get(department)
                if not d_email_name:
                    continue
                if not d_email_name in list(depart_dict.keys()):
                    heads = department_heads.get(department, [])  # returns a list
                    depart_dict[d_email_name] = []
                    for head in heads:
                        depart_dict[d_email_name].append(head + "@ssis-suzhou.net")
                if not teacher.email in depart_dict[d_email_name]:
                    depart_dict[d_email_name].append(teacher.email)

        for department in list(depart_dict.keys()):
            # department is now actually the email name we want to use 
            d['department'] = department
            setup_postfix = '{path}/departments{ext}'.format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("{department}: :include:{path}/departments/{department}{ext}\n".format(**d))

            setup_postfix = '{path}/departments/{department}{ext}'.format(**d)
            with open(setup_postfix, 'w') as f:
                f.write( "\n".join(depart_dict[department]) )

        # run newaliases command on exit if we're on the server
        if self.on_server:
            p = subprocess.Popen('/usr/bin/newaliases', shell=True)
            print(p.communicate())



    def build_student_list(self):

        from utils.DB import DragonNetDBConnection as DNET
        dn = DNET()
        id_map = dn.prepare_id_username_map()

        result = []
        result2 = []
        indexes = []
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            f = Smartformatter()
            f.take_dict(student)
            f(newline='\n')
            result.append( f("{first} {last} ({homeroom} {num})") )

            f( idnum=id_map.get(student.email, {}).get('idnum',"NOTFOUND") )

            index = f('{first} {last}')[:2]
            if not index in indexes:
                indexes.append(index)
            result2.append( (index, f('<a href="http://dragonnet.ssis-suzhou.net/user/profile.php?id=2{idnum}">{first} {last}</a> ({username} {homeroom} {num})<br />')) )

        result.sort()
        result2.sort(key=lambda x:x[0])
        indexes.sort()

        with open(k_path_to_output + '/' + 'student_list_sorted_by_first.txt', 'w') as _file:
            _file.write("\n".join(result))

        with open(k_path_to_output + '/' + 'lookup/student_list_for_lookup.txt', 'w') as _file:
            _file.write('Here are some shortcuts to the areas:<br/>')
            for index in indexes:
                _file.write('<a href="#{}">{}</a>, '.format(index, index))
            _file.write('<br /><br />')

            for item in result2:
                index = item[0]
                if index in indexes:
                    _file.write('<a name="{}"></a>'.format(index))
                    indexes.pop(indexes.index(index))
                _file.write(item[1]+'\n')


if __name__ == "__main__":

    p = PowerSchoolIntegrator()
