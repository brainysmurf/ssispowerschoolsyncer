from Students import Students
from Families import Families
from utils.Bulk import MoodleCSVFile
from utils.Utilities import no_whitespace_all_lower, convert_short_long, Categories, department_heads, department_email_names
from utils.FilesFolders import clear_folder
from utils.DB import ServerInfo
from utils.DB import NoStudentInMoodle, StudentChangedName, NoEmailAddress, NoParentAccount, ParentAccountNotAssociated, MustExit
from ReadFiles import SimpleReader
import re
import datetime
import os
from utils.Formatter import Smartformatter

from ModifyMoodleUsers import StudentModifier

from utils.DB import DragonNetDBConnection

from Constants import k_path_to_output, k_path_to_powerschool

import subprocess

from utils.PHPMoodleLink import CallPHP
from utils.Email import Email
from utils.Email import read_in_templates


class DragonNet(DragonNetDBConnection):
    pass

class InfiniteLoop(Exception):
    pass

class PowerSchoolIntegrator:
    """
    Class that runs a script that automagically syncs PowerSchool data with the dnet server
    """

    def __init__(self):
        """
        
        """
        # if exists, move the php admin tool to to the right place
        
        self.run_newaliases = False
        print('------------------------------------------------------')
        print(datetime.datetime.today())

        import os
        php_src = 'phpmoodle/phpclimoodle.php'
        if os.path.exists(php_src):
            os.rename(php_src, '/var/www/moodle/admin/cli/phpclimoodle.php')
            print("Moved php file that was at {} to the correct location in moodle's document root.".format(php_src))

        self.students = Students()
        self.build_student_courses()
        #self.build_teachers()
        self.build_courses()
        self.build_students()
        self.build_email_list()
        self.build_families()
        self.build_parents()
        self.build_automagic_emails()
        self.build_profiles()
        #self.assign_groups()
        #self.build_student_list()
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
                print(line)
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
        database = DragonNetDBConnection()

        output_file = MoodleCSVFile(k_path_to_output + '/' + 'moodle_parents.txt')
        output_file.build_headers(['username', 'firstname', 'lastname', 'password', 'email', 'course_', 'group_', 'cohort_', 'type_'])

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)

            parent_account = database.sql("select username, email from ssismdl_user where idnumber = '{}'".format(student.family_id))()
            if not parent_account:
                continue
            parent_username, parent_email = parent_account[0]

            if student.courses():
                row = output_file.factory()
                row.build_username(parent_username)
                row.build_firstname('Parent of ')
                row.build_lastname(student.first + student.last)
                row.build_password('changeme')
                row.build_email(parent_email)
                row.build_course_(student.courses())
                row.build_group_(student.groups())
                cohorts = []
                if student.is_secondary:
                    cohorts.append('studentsSEC')
                elif student.is_primary:
                    cohorts.append('studentsELEM')
                    #TODO: Make the below retroactive
                    #if student.is_korean:
                    #cohorts.append('studentsKOREAN')
                    #if student.is_chinese:
                    #cohorts.append('studentsCHINESE')
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

    def new_parent(self, family):
        """
        Associate student with parent
        Enrol parent as parent into child's courses
        Enrol parent into parent cohorts
        Email the parent
        """
        print("Create family account for \n{}".format(family))
        php = CallPHP()

        parent_email_templates = read_in_templates('/home/lcssisadmin/ssispowerschoolsync/templates/parent_new_account')
        
        php.create_account(family.email,
                                family.email,
                                 'Parent ',
                                 family.email,
                                 family.parent_account_id)

        print("Adding parent {} to parent cohort.".format(family.parent_account_id))
        php.add_user_to_cohort(family.parent_account_id, 'parentsALL')

        for child in family.children.children:
            print("Associating child:", child.username)
            php.associate_child_to_parent(family.parent_account_id,
                                                  child.num)
            if child.is_elementary:
                print("Adding parent {} to cohort 'parentsELEM'".format(family.parent_account_id))
                php.add_user_to_cohort(family.parent_account_id, 'parentsELEM')
            if child.is_secondary:
                print("Adding parent {} to cohort 'parentsSEC'".format(family.parent_account_id))
                php.add_user_to_cohort(family.parent_account_id, 'parentsSEC')

            for course in child.courses():
                group = child._groups_courses[course]
                php.enrol_user_in_course(family.parent_account_id, course, group, 'Parent')

        email = Email()
        email.define_sender('lcssisadmin@student.ssis-suzhou.net', "DragonNet Admin")
        email.use_templates(parent_email_templates)
        email.make_subject("Your SSIS DragonNet Parent Account")
        for family_email in family.emails:
            email.add_to(family_email)
        for student in family.children:
            if student.is_korean:
                email.add_language('kor')
            if student.is_chinese:
                email.add_language('chi')
        email.add_bcc('lcssisadmin@student.ssis-suzhou.net')
        email.define_field('username', family.email)
        email.define_field('salutation', 'Dear Parent')
        email.send()
        

    def build_families(self):

        families = Families()
        dragonnet = DragonNet()

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            families.add(student)

        for family_key in families.families:
            family = families.families[family_key]
            family.post_process()
            if not dragonnet.does_user_exist(family.parent_account_id):
                # Enrol, associate, send email
                self.new_parent(family)

    def assign_groups(self):
        from utils.PHPMoodleLink import CallPHP
        php = CallPHP()
        
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            for group in student.groups():
                print(php.add_user_to_group(student.num, group))


    def build_profiles(self):
        """
        Updates user profile fields
        """

        #TODO: Check for which day of the week it is ... only fun on Mondays.
        
        #if not datetime.datetime.today().strftime('%a').lower() == 'm':
        #    return

        html_start = """
<table style="width: 400px;" border="0" cellpadding="5" cellspacing="5" border="1">
<tbody>"""
        grade_row = """
<tr>
<td>{course_name} ({course_short})</td>
<td><a href="{url}">View Feedback</a></td>
</tr>"""
        email_row = """
<tr>
<td>{teacher_name} ({course_short})</td>
<td><a href="mailto:{teacher_email}">Email</a></td>
</tr>"""

        html_end = """</tbody>
</table>"""
        
        database = DragonNetDBConnection()
        
        for student_key in self.students.get_student_keys(secondary=True):
            student = self.students.get_student(student_key)
            
            d = {}

            try:
                _id = database.sql("select id from ssismdl_user where idnumber = '{}'".format(student.num))()[0][0]
            except IndexError:
                # They don't have an account yet?
                continue
            
            # TODO: Make preferred names and homeroom user_profile fields work
            #database.sql("update xxxx set homeroom = '{}' where id = {}".format(student.homeroom, _id))()
            #database.sql("update xxxx set preferred_name = '{}' where id = {}".format(student.preferred_name, _id))()

            grade_rows = [ grade_row.format(**dict(course_name="Forums",
                                                   course_short="All Classes",
                                                   url="http://dragonnet.ssis-suzhou.net/mod/forum/user.php?id={}".format(_id))) ]

            email_rows = [
                email_row.format(**dict(teacher_name="Homeroom Teacher",
                                      teacher_email=student.username + 'HR@student.ssis-suzhou.net',
                                      course_short = 'HROOM')),
                email_row.format(**dict(teacher_name="All your teachers",
                                      teacher_email=student.username + 'TEACHERS@student.ssis-suzhou.net', course_short='N/A'))
                                      ]

            

            if not _id:
                print("User with idnumber {} could not be found in the database: {}".format(student.idnum, student.username))
                continue
            courses = []
            for course in student.courses():
                if 'HROOM' in course:
                    continue
                query = database.sql("select id, fullname from ssismdl_course where shortname = '{}'".format(course))()
                if not query:
                    print("Course with shortname {} could not be found in the database".format(course))
                    continue
                course_id, course_fullname = query[0]

                grade_url = "http://dragonnet.ssis-suzhou.net/course/user.php?mode=grade&id={}&user={}".format(course_id, _id)
                d['course_name'] = course_fullname
                d['course_short'] = course
                d['url'] = grade_url
                grade_rows.append( grade_row.format(**d) )

            for teacher_key in self.students.get_teacher_keys():
                teacher = self.students.get_teacher(teacher_key)
                if teacher.username in student.get_teacher_names():
                    for teacher_course in teacher.courses():
                        if 'HROOM' in teacher_course:
                            continue
                        if teacher_course in student.courses():
                            d['teacher_name'] = teacher.lastfirst.replace("'", '')
                            d['teacher_email'] = teacher.username + '@ssis-suzhou.net'
                            d['course_short'] = teacher_course
                            email_rows.append( email_row.format(**d) )
                            break

            email_html = html_start
            for row in email_rows:
                email_html += row
            email_html += html_end

            grade_html = html_start
            for row in grade_rows:
                grade_html += row
            grade_html += html_end

            teacher_email_field_id = database.sql("select id from ssismdl_user_info_data where fieldid = 2 and userid = {}".format(_id))()
            if not teacher_email_field_id:
                database.sql("insert into ssismdl_user_info_data (userid, fieldid, data, dataformat) values ({}, 2, '{}', 0)".format(_id, email_html))()
            else:
                teacher_email_field_id = teacher_email_field_id[0][0]
                database.sql("update ssismdl_user_info_data set data = '{}' where id = {}".format(email_html, teacher_email_field_id))()

            teacher_grade_field_id = database.sql("select id from ssismdl_user_info_data where fieldid = 3 and userid = {}".format(_id))()
            if not teacher_grade_field_id:
                database.sql("insert into ssismdl_user_info_data (userid, fieldid, data, dataformat) values ({}, 3, '{}', 0)".format(_id, grade_html))()
            else:
                teacher_grade_field_id = teacher_grade_field_id[0][0]
                database.sql("update ssismdl_user_info_data set data = '{}' where id = {}".format(grade_html, teacher_grade_field_id))()

            #print(grade_html)
            #print()
            #print(email_html)

    def build_email_list(self):
        with open(k_path_to_output + '/' + 'student_emails.txt', 'w') as f:
            for student_key in self.students.get_student_keys(secondary=True):
                student = self.students.get_student(student_key)
                if student.homeroom in self.students.get_secondary_homerooms() and student.courses() and int(student.num) > 30000:
                    f.write(student.email + '\n')

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
        output_file.build_headers(['username', 'idnumber', 'firstname', 'lastname', 'password', 'email', 'course_', 'group_', 'cohort_', 'type_'])
        verify and print("Verifying...")

        secondary_homerooms = self.students.get_secondary_homerooms()
        elementary_homerooms = self.students.get_elementary_homerooms()

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)

            # First handle secondary students
            if student.homeroom in secondary_homerooms and student.courses() and int(student.num) > 30000:                
                continue_until_no_errors = True
                times_through = 0
                while continue_until_no_errors:
                    try:
                        # Compares to the actual database, raises errors if there is anything different than what is expected
                        server_information.check_student(student)

                    except NoStudentInMoodle:
                        print("Student does not have a Moodle account:\n{}".format(student))
                        modify.new_student(student)

                    except NoEmailAddress:
                        modify.no_email(student)

                    except StudentChangedName:
                        print("Student has had his or her account name changed: {}, {}".format(student.num, student.username))
                        #modify.change_name(student)

                    # THESE ARE CURRENTLY DONE IN BUILD FAMILIES
                    except NoParentAccount:
                        #modify.new_parent(student)
                        continue_until_no_errors = False
                    
                    except ParentAccountNotAssociated:
                        #modify.parent_account_not_associated(student)
                        continue_until_no_errors = False

                    except MustExit:
                        continue_until_no_errors = False

                    else:
                        # executed when no errors are raised
                        continue_until_no_errors = False

                    times_through += 1
                    if times_through > 10:
                        print("Infinite Loop detected when processing student\n{}".format(student))
                        continue_until_no_errors = False


                # Make the output file
                row = output_file.factory()
                row.build_username(student.username)
                row.build_idnumber(student.num)
                row.build_firstname(student.first)
                row.build_lastname(student.last)
                row.build_password('changeme')
                row.build_email(student.email)

                row.build_course_(student.courses())
                row.build_group_(student.groups())
                row.build_cohort_(student.cohorts())
                row.build_type_(["1" for c in student.courses()])
                if verify:
                    if len(student.groups()) != len(student.courses()):
                        self.students.document_error('verification_failed', student)
                output_file.add_row(row)

            # Now process elementary
            # At the moment, elementary kids don't have dragonnet accounts nor do they have any email
            # Parents only need to have an account is all, and done.
            if student.homeroom in elementary_homerooms and int(student.num) > 30000:
                continue_until_no_errors = True
                times_through = 0
                while continue_until_no_errors:
                    try:
                        server_information.check_student(student)
                    except NoParentAccount:
                        modify.new_parent(student)
                        continue_until_no_errors = False
                    except MustExit:
                        continue_until_no_errors = False
                    else:
                        # executed when no errors are raised
                        continue_until_no_errors = False
                    times_through += 1
                    if times_through > 10:
                        print("Infinite Loop detected when processing student\n{}".format(student))
                        continue_until_no_errors = False
            
            
        output_file.output()

        # THIS WHOLE BLOCK ISN'T REALLY NEEDED ANYMORE
        #with open(k_path_to_output + '/' + 'email_users.txt', 'w') as f:
        #    for student_key in self.students.get_student_keys():
        #        student = self.students.get_student(student_key)
        #        if student.homeroom in self.students.get_secondary_homerooms():
        #            d = student.__dict__.copy()
        #            d['sep'] = ':'
        #            d['newline'] = '\n'
        #            d['tab'] = '\t'
        #            d['password'] = 'changeme'
        #            f.write("{preferred_name}{newline}".format(**d))
        #            f.write("{username}{sep}{password}{sep}{sep}{sep}{num}{sep}/home/{username}{sep}/bin/bash{newline}".format(**d))

        #clear_folder(k_path_to_output + '/' + 'homerooms')
        #for student_key in self.students.get_student_keys():
        #    student = self.students.get_student(student_key)
        #    if student.homeroom in self.students.get_secondary_homerooms():
        #            with open(k_path_to_output + '/' + 'homerooms/homeroom{}.txt'.format(student.homeroom), 'a') as f:
        #                d = student.__dict__.copy()
        #                d['sep'] = ':'
        #                d['newline'] = '\n'
        #                d['tab'] = '\t'
        #                d['message'] = "These are your credentials for ALL your DragonNet accounts and email. You are expected to use these accounts responsibly. DO NOT SHARE."
        #                f.write("{username}{newline}".format(**d))

        #clear_folder(k_path_to_output + '/' + 'parents')
        #for student_key in self.students.get_student_keys():
        #    student = self.students.get_student(student_key)
        #    if student.homeroom in self.students.get_secondary_homerooms():
        #            with open(k_path_to_output + '/' + 'parents/homeroom{}.txt'.format(student.homeroom), 'a') as f:
        #                d = student.__dict__.copy()
        #                d['sep'] = ':'
        #                d['newline'] = '\n'
        #                d['tab'] = '\t'
        #                d['parent_emails'] = '\n'.join([s for s in student.parent_emails if s])
        #                d['message'] = "These are your credentials for ALL your DragonNet accounts and email. You are expected to use these accounts responsibly. DO NOT SHARE."
        #                f.write("{parent_emails}{newline}".format(**d))


    def build_emails_for_powerschool(self):

        with open(k_path_to_output + '/' + 'powerschool_email_output.txt', 'w') as output:
            output.write('Student_Number\tLastFirst\tLTIS_AS_email\n')
            for student_key in self.students.student_info_controller.keys():
                student = self.students.student_info_controller.get(student_key)
                d = student.__dict__.copy()
                d['tab'] = "\t"
                d['newline'] = "\n"
                output.write("{num}{tab}{lastfirst}{tab}{email}{newline}".format(**d))

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

        setup_postfix = '{path}/special{ext}'.format(**d)
        with open(setup_postfix, 'w') as f:
            f.write("usebccparentsALL: :include:{path}/special/usebccparentsALL{ext}\n".format(**d))
        setup_postfix = '{path}/special{ext}'.format(**d)
        with open(setup_postfix, 'a') as f:
            f.write("usebccparentsSEC: :include:{path}/special/usebccparentsSEC{ext}\n".format(**d))
        setup_postfix = '{path}/special{ext}'.format(**d)
        with open(setup_postfix, 'a') as f:
            f.write("usebccparentsELEM: :include:{path}/special/usebccparentsELEM{ext}\n".format(**d))

        setup_postfix = '{path}/special{ext}'.format(**d)
        with open(setup_postfix, 'a') as f:
            f.write("usebccparentsKOREAN: :include:{path}/special/usebccparentsKOREAN{ext}\n".format(**d))
        setup_postfix = '{path}/special{ext}'.format(**d)
        with open(setup_postfix, 'a') as f:
            f.write("usebccparentsCHINESE: :include:{path}/special/usebccparentsCHINESE{ext}\n".format(**d))

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
            setup_postfix = "{path}/special/usebccparentsALL{ext}".format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')

            setup_postfix = "{path}/special/usebccparentsELEM{ext}".format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')
                
            if student.is_korean:
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
            setup_postfix = "{path}/special/usebccparentsALL{ext}".format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')

            setup_postfix = "{path}/special/usebccparentsSEC{ext}".format(**d)
            with open(setup_postfix, 'a') as f:
                f.write("\n".join([e.strip() for e in student.parent_emails if e.strip()]) + '\n')

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
                    with open(setup_postfix, 'a') as f:
                        f.write("{group}PARENTS: :include:{path}/classes/{group}PARENTS{ext}\n".format(**d))

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
        # id_map is needed because I need to know the id in the database
        id_map = dn.prepare_id_username_map()

        # result is the necessary format to update reset passwords in Moodle
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

            result2.append(
                (index,
                 f('<a href="http://dragonnet.ssis-suzhou.net/user/profile.php?id={idnum}">{first} {last}</a> ({username} {homeroom} {num})<br />')) )

        # Here is where I want to 

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
