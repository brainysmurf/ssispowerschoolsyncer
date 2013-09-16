#!/usr/bin/env python3

from psmdlsyncer.Students import Students
from psmdlsyncer.Families import Families
from psmdlsyncer.utils.Bulk import MoodleCSVFile
from psmdlsyncer.utils.Utilities import no_whitespace_all_lower, convert_short_long, Categories, department_heads, department_email_names
from psmdlsyncer.utils.FilesFolders import clear_folder
from psmdlsyncer.utils.ServerInfo import ServerInfo, NoStudentInMoodle, StudentChangedName, NoEmailAddress, NoParentAccount, \
    GroupDoesNotExist, StudentNotInGroup, ParentAccountNotAssociated, ParentNotInGroup, MustExit
from psmdlsyncer.utils.AutoSendFile import File
from psmdlsyncer.Inform import inform_new_parent, inform_new_student, reinform_new_parent
import re
import datetime
import os
from psmdlsyncer.utils.Formatter import Smartformatter

from psmdlsyncer.ModifyDragonNet import DragonNetModifier

from psmdlsyncer.utils.DB import DragonNetDBConnection

import subprocess

from psmdlsyncer.utils.PHPMoodleLink import CallPHP
from psmdlsyncer.html_email.Email import Email, read_in_templates

from psmdlsyncer.settings import config, settings, config_get_section_attribute, logging

class DragonNet(DragonNetDBConnection):
    pass

class InfiniteLoop(Exception):
    pass

class PowerSchoolIntegrator():
    """
    Class that runs a script that automagically syncs PowerSchool data with the dnet server
    """
    temp_table = lambda: 'to_be_informed'
    temp_table_column_idnumber = lambda: 'idnumber'
    temp_table_column_comment = lambda: 'comment'
    
    def __init__(self):
        """
        
        """
        # if exists, move the php admin tool to to the right place

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Initiating PowerSchoolInteragrator instance")

        self.config = config
        self.settings = settings.arguments

        if self.settings.automagic_emails:
            # Set up dependencies
            self.settings.courses = True
            self.settings.teachers = True
            self.settings.students = True
        self.dry_run = self.settings.dry_run

        if 'DEFAULTS' in self.config.sections():
            for key in self.config['DEFAULTS']:
                setattr(self, key, self.config.getboolean('DEFAULTS', key))

        self.email_server = None
        if self.config.has_section("EMAIL"):
            self.email_server = self.config['EMAIL'].get('domain')
        if not self.email_server:
            self.email_server = 'localhost'

        have_email_section = self.config.has_section('EMAIL')
        have_moodle_section = self.config.has_section('MOODLE')
        self.server_information = ServerInfo()

        php_src = 'phpmoodle/phpclimoodle.php'   #TODO: Must figure out full path to myself, right?
        mv_to_path = self.config['MOODLE'].get('path_to_cli') if have_moodle_section else ""
        if os.path.exists(php_src) and mv_to_path and os.path.exists(mv_to_path):
            import shutil
            mv_to_full_path = mv_to_path + '/phpclimoodle.php'
            try:
                shutil.copy(php_src, mv_to_full_path)
                owner = self.config['MOODLE']['owner_id']
                group = self.config['MOODLE']['group_id']
                os.chown(mv_to_full_path, int(owner), int(group))
                self.logger.info("Copied php file that was at {} to the correct location in moodle's document root \
and set permissions accordingly.".format(php_src))
            except:  #TODO: Use the right exceptions
                self.logger.warn("Copying php file failed, do we have the right permissions?")
        else:
            self.logger.warn("php_src: {}, mv_to_path: {}".format(php_src, mv_to_path))
            self.logger.warn("Couldn't attempt the copy php file, settings printed above")
            self.logger.warn("END WARNING")

        from psmdlsyncer.settings import config_get_section_attribute
        self.path_to_powerschool = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')
        self.path_to_output = config_get_section_attribute('DIRECTORIES', 'path_to_output')
        self.path_to_errors = config_get_section_attribute('DIRECTORIES', 'path_to_errors')
        self.students = Students(user_data=self.server_information.get_student_info())

        if self.settings.teachers:
            self.build_teachers()
        if self.settings.courses:
            self.build_courses()
            self.build_student_courses()
        if self.settings.students:
            self.build_students()
        if self.settings.email_list:
            self.build_email_list()
        if self.settings.families:
            self.build_families()
        if self.settings.parents:
            self.build_parents()
        if self.settings.automagic_emails:
            self.build_automagic_emails()
        if self.settings.profiles:
            self.build_profiles()
        if self.settings.updaters:
            self.build_updates()
        if self.settings.remove_enrollments:
            self.remove_enrollments()
        #self.assign_groups()
        #self.build_student_list()
        #self.build_opening_table(students)
        #self.create_simple_accounts()
        #self.compile_student_parent_emails(students)


    def build_courses(self):
        """
        ### TODO ###
        Implement this in totally different way, looking for course names
        of those that actually have enrollments rather than through powerschool file
        ############
        """
        self.logger.info("Building courses")
        source = File('sec', 'courseinfo')
        raw = source.content()
        courses = {}
        summaries = {}
        with open(self.path_to_output + '/' + 'moodle_courses.txt', 'w') as f:
            f.write('fullname,shortname,category,summary,groupmode\n')
            self.logger.debug("Go through the file with course information, set up summaries and other info")
            for line in raw:
                orig_short, orig_long = line.strip('\n').split('\t')
                self.logger.debug("Building course: {}".format(orig_long))
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
        self.logger.info("Building teachers")
        output_file = MoodleCSVFile(self.path_to_output + '/' + 'teachers_moodle_file.txt')
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

        self.logger.debug("Head list has been built:\n{}".format(heads))
        
        for head in list(heads.keys()):
            self.logger.debug("Building head of dept as 'non-editing teacher' but can be made to manager later: {}".format(head))
            courses = heads[head]
            row = output_file.factory()
            row.build_username(head)
            row.build_firstname("headof")
            row.build_lastname("department")
            row.build_password('nopasswordneeded')
            row.build_email(head+'@ssis-suzhou.net')
            row.build_maildigest('1')
            row.build_course_(courses)
            row.build_cohort_(['departHEADS'])
            row.build_type_(['3' for c in courses])  # this is non-editing teacher....
            output_file.add_row(row)


        for teacher_key in self.students.teacher_info_controller.keys():
            teacher = self.students.teacher_info_controller.get(teacher_key)
            self.logger.debug("Building teacher: {}".format(teacher))
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

            # Update profile fields

        self.logger.info("Writing csv file suitable for 'Upload Users' feature into output folder")
        output_file.output()

    def build_parents(self):
        """
        Builds a manual file that can be imported in... horrible
        """
        self.logger.info("Building parents")
        database = DragonNetDBConnection()

        output_file = MoodleCSVFile(self.path_to_output + '/' + 'moodle_parents.txt')
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
        open(self.path_to_output + '/' + 'table.txt', 'w').close()
        for course_key in self.students.get_course_keys():
            course = self.students.get_course(course_key)
            teachers = course.teachers()
            table = """<table border="1" cellpadding="10" cellspacing="10" align="center" style="width: 300px;"><caption>Teacher Contact Information</caption>
    <tbody>{inside}</tbody></table>"""
            inside = """<tr><td>{username}@ssis-suzhou.net</td></tr>"""
            with open(self.path_to_output + "/" + "table.txt", 'a') as f:
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
        self.logger.info("Now build the student_courses file in the output folder")
        with open(self.path_to_output + '/' + 'student_courses', 'w') as f:
            for student_key in self.students.get_student_keys():
                student = self.students.get_student(student_key)
                self.logger.debug("Student course info for {}".format(student))
                d = student.__dict__.copy()
                d['courses'] = ",".join(student.courses())
                if student.homeroom in self.students.get_secondary_homerooms():
                    if student.courses():
                        f.write("{num}\t{username}\t{courses}\n".format(**d))

    def handle_new_student(results, family, student):
        for idnumber, comment in results:
            if 'newstudent' == comment:
                self.logger.info("This student is a new student and their homeroom teacher is getting emailed:\n{}".format(student))
                inform_new_student(family, student)

    def build_families(self):
        """server_information
        Loops through the students as a family, which is perfect spot to do informing
        This is because we have all the emails in one place
        And can tell them all sort of things
        """
        families = Families()

        self.logger.info("Building families")
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            families.add(student)

        for family_key in families.families:
            family = families.families[family_key]
            family.post_process()
            results = self.server_information.get_temp_storage('to_be_informed',
                                                        idnumber= family.idnumber)
            if results:
                results = set(results)   # remove duplicates, and since duplicates are removed from database with clear all we're good
                for idnumber, comment in results:
                    if 'newparent' == comment:
                        self.logger.info("This family is a new family and is being informed of their account:\n{}".format(family))
                        inform_new_parent(family)
                    else:
                        if 'not_logged_in_yet' == comment:
                            self.logger.info("This family has had an account for a period of time and needs to be reminded of their account\n{}".format(family))
                            reinform_parent(family)
                self.server_information.clear_temp_storage('to_be_informed',
                                                           idnumber = family.idnumber)

            for child in family.children:
                results = self.server_information.get_temp_storage('to_be_informed',
                                                                   idnumber = child.num)
                if results:
                    handle_new_student(results, family, child)
                    self.server_information.clear_temp_storage('to_be_informed',
                                                           idnumber = child.num)

        # Ensure that informing has been done for students, which might otherwise be lost
        # in case something happened with the family account
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            results = self.server_information.get_temp_storage('to_be_informed',
                                                               idnumber = student.num)
            if results:
                handle_new_student(results, family, student, server=self.email_server)
                self.server_information.clear_temp_storage('to_be_informed',
                                                           idnumber = student.num)

        # TODO: Email the admin any leftover items
        #leftover = self.server_information.dump_temp_storage('to_be_informed', clear=True)
        self.logger.info("to_be_informed should now be empty")

    def build_updates(self):
        self.logger.info("Building updates")
        section = self.config['MOODLE']
        user = section.get('database_user')
        password = section.get('password')
        host = section.get('host')
        database_name = section.get('database_name')
        
        from utils.DB import UpdateField
        homework_club_updater = UpdateField(user, password, host, database_name, 'Homework Detention Database', 'Student')
        homework_club_list = []
        #golden_chair_updater = UpdateField(self.database_user, self.database_password, self.host, self.database_name, 'Homework Club', 'Student')
        golden_chair_list = []
        
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            if student.grade >= 6 and student.grade <= 8:
                homework_club_list.append(student)
            if student.is_elementary:
                golden_chair_list.append(student)

        homework_club_list.sort(key=lambda s: s.last)
        golden_chair_list.sort(key=lambda s: s.homeroom)

        self.logger.info("Updating homework club")
        homework_club_updater.update_menu( ["{} ({} {})".format(student.full_name, student.homeroom, student.num) for student in homework_club_list] )
        #golden_chair_updater.update_menu(golden_chair_list)

    def build_profiles(self):
        """
        Updates user profile fields
        """
        self.logger.info("Building profiles")
        #TODO: Check for which day of the week it is ... only fun on Mondays.

        #if not datetime.datetime.today().strftime('%a').lower() == 'm':
        #    return

        html_start = """
    <table class="userinfotable">"""
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

        if not self.config.has_section('MOODLE'):
            self.logger.warn("No moodle config available, cannot build profiles")
            return

        moodle = self.config['MOODLE']
        host = moodle.get('host')
        user = moodle.get('database_user')
        password = moodle.get('password')
        database_name = moodle.get('database_name')
        database = DragonNetDBConnection()

        for student_key in self.students.get_student_keys(secondary=True):
            student = self.students.get_student(student_key)

            formatter = Smartformatter()
            formatter.take_dict(student)

            try:
                formatter.user_id = database.sql(formatter("select id from ssismdl_user where idnumber = '{num}'"))()[0][0]
            except IndexError:
                # They don't have an account yet?
                continue

            # TODO: Make preferred names and homeroom user_profile fields work

            grade_rows = [ grade_row.format(**dict(course_name="Forums",
                                                       course_short="All Classes",
                                                       url=format("http://dragonnet.ssis-suzhou.net/mod/forum/user.php?id={user_id}"))) ]

            email_rows = [
                    email_row.format(**dict(teacher_name="Homeroom Teacher",
                                          teacher_email=student.username + 'HR@student.ssis-suzhou.net',
                                          course_short = 'HROOM')),
                    email_row.format(**dict(teacher_name="All your teachers",
                                          teacher_email=student.username + 'TEACHERS@student.ssis-suzhou.net', course_short='N/A'))
                                          ]



            if not formatter.user_id:
                self.logger.warn(formatter("User with idnumber {num} could not be found in the database, cannot put in profile: {username}"))
                continue
            courses = []
            for course in student.courses():
                formatter.course_short = course
                if 'HROOM' in formatter.course_short:
                    continue
                query = database.sql(formatter("select id, fullname from ssismdl_course where shortname = '{course_short}'"))()
                if not query:
                     self.logger.info(formatter("Course with shortname {course_short} could not be found in the database"))
                     continue
                formatter.course_id, formatter.course_name = query[0]

                formatter.url = formatter("http://dragonnet.ssis-suzhou.net/course/user.php?mode=grade&id={course_id}&user={user_id}")
                grade_rows.append( formatter(grade_row) )

                for teacher_key in self.students.get_teacher_keys():
                    teacher = self.students.get_teacher(teacher_key)
                    if teacher.lastfirst in student.get_teacher_names():
                        for teacher_course in teacher.courses():
                            if 'HROOM' in teacher_course:
                                continue
                            if teacher_course in student.courses():
                                formatter.teacher_name = teacher.lastfirst.replace("'", '')
                                formatter.teacher_email = teacher.username + '@ssis-suzhou.net'
                                formatter.course_short = teacher_course
                                email_rows.append( formatter(email_row) )
                                break

                formatter.email_html = html_start
                for row in email_rows:
                    formatter.email_html += row
                formatter.email_html += html_end

                formatter.grade_html = html_start
                for row in grade_rows:
                    formatter.grade_html += row
                formatter.grade_html += html_end

                formatter.teacher_email_field_id = database.sql(formatter("select id from ssismdl_user_info_data where fieldid = 2 and userid = {user_id}"))()
                if not formatter.teacher_email_field_id:
                    database.sql(formatter("insert into ssismdl_user_info_data (userid, fieldid, data, dataformat) values ({user_id}, 2, '{email_html}', 0)"))()
                else:
                    formatter.teacher_email_field_id = formatter.teacher_email_field_id[0][0]
                    database.sql(formatter("update ssismdl_user_info_data set data = '{email_html}' where id = {teacher_email_field_id}"))()

                formatter.teacher_grade_field_id = database.sql(formatter("select id from ssismdl_user_info_data where fieldid = 3 and userid = {user_id}"))()
                if not formatter.teacher_grade_field_id:
                    database.sql(formatter("insert into ssismdl_user_info_data (userid, fieldid, data, dataformat) values ({user_id}, 3, '{grade_html}', 0)"))()
                else:
                    formatter.teacher_grade_field_id = formatter.teacher_grade_field_id[0][0]
                    database.sql(formatter("update ssismdl_user_info_data set data = '{grade_html}' where id = {teacher_grade_field_id}"))()

            for formatter.existing_profile_field, formatter.value in student.get_existing_profile_fields():
                self.logger.debug(formatter("Existing profile field: {existing_profile_field}"))
                # Just use database directly instead of checking to see if already there
                # (Below we have to check first)
                database.sql(formatter("update ssismdl_user set {existing_profile_field} = '{value}' where id = {user_id}"))()
                
            for formatter.extra_profile_field, formatter.value in student.get_extra_profile_fields():
                self.logger.debug(formatter("Manually created profile field: {extra_profile_field}"))
                formatter.field_id = database.sql(formatter("select id from ssismdl_user_info_field where shortname = '{extra_profile_field}'"))()
                if not formatter.field_id:
                    self.logger.debug(formatter("You need to manually add the {extra_profile_field} field!"))
                    continue
                formatter.field_id = formatter.field_id[0][0]
                there_already = database.sql(formatter("select data from ssismdl_user_info_data where fieldid = {field_id} and userid = {user_id}"))()
                if there_already:
                    if not there_already[0][0] == str(int(formatter.value)):
                        # only call update if it's different
                        formatter.value = int(formatter.value)
                        self.logger.debug(formatter('updating for {user_id}'))
                        database.sql(formatter("update ssismdl_user_info_data set data = {value} where fieldid = {field_id} and userid = {user_id}"))()
                    else:
                        self.logger.debug(formatter("No change in {extra_profile_field}, so didn't call the database"))
                else:
                    self.logger.debug(formatter('inserting {extra_profile_field}'))
                    database.sql(formatter("insert into ssismdl_user_info_data (userid, fieldid, data, dataformat) values ({user_id}, {field_id}, {value}, 0)"))()

    def build_email_list(self):
        with open(self.path_to_output + '/' + 'student_emails.txt', 'w') as f:
            for student_key in self.students.get_student_keys(secondary=True):
                student = self.students.get_student(student_key)
                if student.is_secondary:
                    f.write(student.email + '\n')

    def remove_enrollments(self):
        """
        De-enrols all users from all courses, except for Grade 12s
        """
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            self.logger.info("Got to this one here: \n{}".format(student))
            dnet = DragonNetDBConnection()
            modify = DragonNetModifier()

            # First handle secondary students
            if student.is_secondary and int(student.num) > 30000:
                if student.grade == 12:
                    continue
                queried = dnet.get_user_enrollments(student.num)
                courses = student.courses()
                for query in queried:
                    _, group, course = query
                    if course not in courses:
                        modify.unenrol_user_from_course(student.num, course)

        # NOW UNENROL PARENTS
        families = Families()

        self.logger.info("Building families")
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            families.add(student)

        for family_key in families.families:
            family = families.families[family_key]
            family.post_process()

            courses = []
            for child in family.children:
                courses.extend(child.courses())

            queried = dnet.get_user_enrollments(student.family_id)
            for query in queried:
                _, group, course = query
                if course not in courses:
                    self.logger.warn('Unenrolling parent {} from course {}'.format(student.family_id, course))
                    modify.unenrol_user_from_course(student.family_id, course)
            

    def build_students(self, verify=False):
        """
        Go through each student and do what is necessary to actually sync powerschool data
        """
        self.logger.debug("Building csv file for moodle")
        path_to_cli = self.config['MOODLE'].get('path_to_cli') if self.config.has_section('MOODLE') else None
        path_to_php = self.config['PHP']['php_path'] if self.config.has_section('PHP') else None
        modify = DragonNetModifier()

        output_file = MoodleCSVFile(self.path_to_output + '/' + 'moodle_users.txt')
        output_file.build_headers(['username', 'idnumber', 'firstname', 'lastname', 'password', 'email', 'course_', 'group_', 'cohort_', 'type_'])

        secondary_homerooms = self.students.get_secondary_homerooms()
        elementary_homerooms = self.students.get_elementary_homerooms()

        self.logger.debug("Looping through students now")

        self.server_information.create_temp_storage('to_be_informed', 'idnumber', 'comment')
        
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            self.logger.debug("Got to this one here: \n{}".format(student))

            # First handle secondary students
            if student.is_secondary and student.courses() and int(student.num) > 30000:                
                continue_until_no_errors = True
                times_through = 0
                while continue_until_no_errors:
                    try:
                        # Compares to the actual database, raises errors if there is anything different than what is expected
                        self.server_information.check_student(student)

                    except NoStudentInMoodle:
                        self.logger.debug("Student does not have a Moodle account:\n{}".format(student))
                        modify.new_student(student)
                        #TODO Do informing here
                        if self.dry_run:
                            times_through = 11
                            # or just manually update the database, right?
                        else:
                            self.server_information.init_users_and_groups()
                        self.server_information.add_temp_storage('to_be_informed',
                                                                 idnumber=student.num,
                                                                 comment='newstudent')

                    except NoEmailAddress:
                        self.logger.warn("Student does not have an email address:\n{}".format(student))
                        modify.no_email(student)
                        if self.dry_run:
                            times_through = 11
                            # or just manually update the database, right?

                    except GroupDoesNotExist:
                        self.logger.debug("At least one group does not exist, enrolling them, which will take care of this")
                        modify.enrol_student_into_courses(student)
                        if self.dry_run:
                            times_through = 11
                            # or just manually update the database, right?
                        else:
                            self.server_information.init_users_and_groups()                            
                        
                    except StudentNotInGroup:
                        self.logger.debug("Student not enrolled in at least one of the required groups")
                        modify.enrol_student_into_courses(student)
                        if self.dry_run:
                            times_through = 11
                            # or just manually update the database, right?
                        else:
                            self.server_information.init_users_and_groups()

                    except NoParentAccount:
                        self.logger.warn("No family account for student\n{}".format(student))
                        modify.new_parent(student)

                        # Informing the parent at this point is problematic:
                        #    * Not guaranteed that all children have already been associated with family account
                        #    * If above is not guaranteed then we can't also guarantee the inform email
                        #          will go to all the relevant emails
                        # Therefore, we inform the parent in build_families, after all students have been read in
                        # Because of that we store the parent account into a temp table in the database
                        # That way even if there is any subsequent error it'll still get processed
                        self.server_information.add_temp_storage('to_be_informed',
                                                                 idnumber = student.family_id,
                                                                 comment = 'newparent')
                        
                        if self.dry_run:
                            times_through = 11
                            # or just manually update the database, right?
                        else:
                            self.server_information.init_users_and_groups()
                    
                    except ParentAccountNotAssociated:
                        self.logger.warn("Parent account {} hasn't been assocated to student {}".format(student.family_id, student))
                        modify.parent_account_not_associated(student)
                        if self.dry_run:
                            times_through = 11
                            # or just manually update the database, right?
                        else:
                            self.server_information.init_users_and_groups()
                        
                    except ParentNotInGroup:
                        self.logger.debug("Parent is not enrolled in at least one group: {}".format(student.family_id))
                        modify.enrol_parent_into_courses(student)
                        if self.dry_run:
                            times_through = 11
                        else:
                            self.server_information.init_users_and_groups()
                        
                    except StudentChangedName:
                        #TODO: Implement an email feature or something to be handled manually by admin
                        self.logger.warn("Student has had his or her account name changed.\n" +
                              "We will continue using the available one as defined by DragonNet:\n{}, {}".format(
                                  student.num, student.username)
                            )

                    except MustExit:
                        continue_until_no_errors = False

                    else:
                        # executed when no errors are raised
                        continue_until_no_errors = False

                    times_through += 1
                    if times_through > 10:
                        self.logger.warn("Infinite Loop detected when processing student\n{}".format(student))
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
                        self.server_information.check_student(student, onlyraise=('NoParentAccount', 'NoEmailAddress', 'ParentAccountNotAssociated', 'NoStudentInMoodle'))

                    except NoStudentInMoodle:
                        self.logger.warn("Student does not have a Moodle account:\n{}".format(student))
                        modify.new_student(student)
                        #TODO Do informing here
                        if self.dry_run:
                            times_through = 11
                            # or just manually update the database, right?
                        else:
                            self.server_information.init_users_and_groups()

                    except NoParentAccount:
                        self.logger.warn("No parent account for elem student:\n{}".format(student))
                        modify.new_parent(student)
                        if self.dry_run:
                            times_through = 11
                        else:
                            self.server_information.init_users_and_groups()
                        self.server_information.add_temp_storage('to_be_informed',
                                                                 idnumber = student.family_id, comment = 'newparent')

                    except NoEmailAddress:
                        self.logger.warn("Student does not have an email address:\n{}".format(student))
                        modify.no_email(student)
                        if self.dry_run:
                            times_through = 11
                            # or just manually update the database, right?

                    except ParentAccountNotAssociated:
                        self.logger.warn("Parent account {} hasn't been assocated to student {}".format(student.family_id, student))
                        modify.parent_account_not_associated(student)
                        if self.dry_run:
                            times_through = 11
                            # or just manually update the database, right?
                        else:
                            self.server_information.init_users_and_groups()

                    except MustExit:
                        continue_until_no_errors = False
                    else:
                        # executed when no errors are raised
                        continue_until_no_errors = False
                    times_through += 1
                    if times_through > 10:
                        self.logger.warn("Infinite Loop detected when processing student\n{}".format(student))
                        continue_until_no_errors = False

        output_file.output()

    def build_emails_for_powerschool(self):

        with open(self.path_to_output + '/' + 'powerschool_email_output.txt', 'w') as output:
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
        with open(self.path_to_output + '/' + 'list_of_courses.txt', 'w') as f:
            [f.write("{}\n".format(c)) for c in the_courses]

    def create_simple_accounts(self):
        from utils.Utilities import no_whitespace_all_lower

        l = ["Bjoerkgaard, Maria", "Fowles, Rewa Margaret", "Liu, Wei-Chi", "Mo, Akane", "Paavola, Ira Aurora", "Roem, Yasmin Andinasari", "Yang, Szu-Kai", "Zheng, Ting-Yu"]
        courses = "TEDESSH1112"
        with open(self.path_to_output + '/' + 'simple_users.txt', 'w') as f:
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

       students_where = self.path_to_output + '/' + 'studentsbyclasses'
       clear_folder(students_where)
       parents_where = self.path_to_output + '/' + 'parentsbyclasses'
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
        with open(self.settings.output_path + '/output/idnumbers.txt', 'w') as f:
            f.write("username,idnumber,firstname,lastname,password,email\n")
            for student_key in self.students.get_student_keys():
                student = self.students.get_student(student_key)
                d = student.__dict__.copy()
                f.write('{username},{num},{first},{last},changeme,{email}\n'.format(**d))

    def build_automagic_emails(self):
        path = None
        if self.config.has_section("EMAIL"):
            path = config_get_section_attribute('DIRECTORIES', 'path_to_postfix')
        if not path:
            path = self.output_path + '/postfix'

        #TODO: Use smartformatter for this crap!
        d = {'path':path}
        d['ext'] = '.txt'

        # The clear_folder routine erases all files in a certain folder
        # That has implications for postfix (when we're on the server), because
        # if you delete the .db files then postfix won't work. That is bad.
        # So, tell clear_folder to exclude them
        exclude_db_files = lambda x: x.endswith('.db')

        self.logger.debug("Clearing folders in postfix")
        clear_folder('{path}'.format(**d), exclude=exclude_db_files) 
        #

        clear_folder('{path}/grades'.format(**d))
        clear_folder('{path}/homerooms'.format(**d))
        clear_folder('{path}/classes'.format(**d))
        clear_folder('{path}/parentlink'.format(**d))
        clear_folder('{path}/teacherlink'.format(**d))
        clear_folder('{path}/special'.format(**d))
        clear_folder('{path}/departments'.format(**d))

        self.logger.debug("Setting up largest mailing lists first")
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

        self.logger.debug("Setting up elementary email lists")
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

        self.logger.debug("Setting up secondary email lists")
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
                    if teacher and not teacher in added_teachers_grade[d['grade']]:
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
                teacher = student.get_homeroom_teacher()
                if teacher and not teacher in added_teachers_hr[d['homeroom']]:
                    f.write(teacher + '@ssis-suzhou.net\n')
                    added_teachers_hr[d['homeroom']].append(teacher)
                for teacher in student.get_teachers_as_list():
                    if teacher and not teacher in added_teachers_hr[d['homeroom']]:
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


        self.logger.debug("Set up department batch emails")
        ##  SETUP DEPARTMENTS, including by homeroom teachers
        depart_dict = {}
        homeroom_teachers_dict = {}
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
                        self.logger.debug("Adding {} (the head) into department {}".format(head, d_email_name))
                        depart_dict[d_email_name].append(head + "@ssis-suzhou.net")
                if teacher and not teacher.email in depart_dict[d_email_name]:
                    self.logger.debug("Adding {} into department {}".format(teacher, d_email_name))
                    depart_dict[d_email_name].append(teacher.email)

            if teacher.homeroom:
                d['homeroom'] = teacher.homeroom
                if not teacher.homeroom in homeroom_teachers_dict.keys():
                    homeroom_teachers_dict[teacher.homeroom] = True
                    setup_postfix = '{path}/departments{ext}'.format(**d)
                    with open(setup_postfix, 'a') as f:
                        f.write("homeroomteachers{homeroom}: :include:{path}/departments/homeroomteachers{homeroom}{ext}\n".format(**d))
                setup_postfix = '{path}/departments/homeroomteachers{homeroom}{ext}'.format(**d)
                with open(setup_postfix, 'a') as f:
                    f.write(teacher.email + '\n')

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
        newaliases_path = False
        if self.config.has_section('EMAIL'):
            newaliases_path = self.config['EMAIL'].get('newaliases_path')
        if newaliases_path:
            self.logger.info("Running newaliases")
            p = subprocess.Popen(newaliases_path, shell=True)
            self.logger.info(p.communicate())
        else:
            self.logger.warn("newaliases not run!")
        #TODO: If received error, should email admin


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
        with open(self.path_to_output + '/' + 'student_list_sorted_by_first.txt', 'w') as _file:
            _file.write("\n".join(result))

        with open(self.path_to_output + '/' + 'lookup/student_list_for_lookup.txt', 'w') as _file:
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
