from psmdlsyncer.Tree import Tree
from psmdlsyncer.sql import MoodleDBConnection, ServerInfo
from psmdlsyncer.files import clear_folder, AutoSendFile, MoodleCSVFile
from psmdlsyncer.exceptions import NoStudentInMoodle, StudentChangedName, NoEmailAddress, NoParentAccount, \
    GroupDoesNotExist, StudentNotInGroup, ParentAccountNotAssociated, ParentNotInGroup, MustExit
from psmdlsyncer.inform import inform_new_parent, inform_new_student, reinform_new_parent
from psmdlsyncer.models import Families
from psmdlsyncer.php import ModUserEnrollments, CallPHP
from psmdlsyncer.utils import NS, convert_short_long, Categories, department_email_names, department_heads
from psmdlsyncer.html_email import Email, read_in_templates
from psmdlsyncer.settings import config, config_get_section_attribute, logging

import re
import datetime
import subprocess
from collections import defaultdict

def name_to_email(long_name):
    """
    USED FOR ACTIVITIES EMAIL GENERATION
    TODO: MOVE TO utils
    """
    try:
        where = long_name.index(')')
    except ValueError:
        where = -1
    where += 1
    long_name = long_name[where:].strip().lower()
    return re.sub('[^a-z0-9]', '', long_name)


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
        self.logger.warn('Started at {}'.format( datetime.datetime.now() ) )

        self.students = Tree()

        self.config = config

        self.dry_run = self.students.settings.dry_run

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

        from psmdlsyncer.settings import config_get_section_attribute
        self.path_to_powerschool = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')
        self.path_to_output = config_get_section_attribute('DIRECTORIES', 'path_to_output')
        self.path_to_errors = config_get_section_attribute('DIRECTORIES', 'path_to_errors')

        if self.students.settings.teachers:
            self.build_teachers()
        if self.students.settings.courses:
            self.build_courses()
        if self.students.settings.students:
            self.build_students()
        if self.students.settings.email_list:
            self.build_email_list()
        if self.students.settings.families:
            self.build_families()
        if self.students.settings.parents:
            self.build_parents()
        if self.students.settings.automagic_emails:
            self.build_automagic_emails()
        if self.students.settings.profiles:
            self.build_profiles()
        if self.students.settings.updaters:
            self.build_updates()
        if self.students.settings.remove_enrollments:
            self.remove_enrollments()
        if self.students.settings.enroll_cohorts:
            self.enroll_cohorts()

        self.logger.warn('Completed at {}'.format( datetime.datetime.now() ) )

    def build_courses(self):
        """
        ### TODO ###
        Implement this in totally different way, looking for course names
        of those that actually have enrollments rather than through powerschool file
        ############
        """
        self.logger.info("Building courses")
        courses = {}
        summaries = {}

        source = AutoSendFile('sec', 'courseinfo')
        with open(self.path_to_output + '/' + 'moodle_courses.txt', 'w') as f:
            f.write('fullname,shortname,category,summary,groupmode\n')
            self.logger.debug("Go through the file with course information, set up summaries and other info")
            for line in source.content():
                orig_short, orig_long = line
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
        """
        OUTPUTS A CSV FILE USEFUL FOR BULK UPLOAD TWT FEATURE IN MOODLE
        """
        self.logger.info("Building teachers and department heads")
        output_file = MoodleCSVFile(self.path_to_output + '/' + 'teachers_moodle_file.txt')
        output_file.build_headers(['username', 'firstname', 'lastname', 'password', 'email', 'idnumber', 'maildigest', 'course_', 'cohort_', 'type_'])

        # First do heads of department

        heads = defaultdict(list)
        for course_key in self.students.get_course_keys():
            course = self.students.get_course(course_key)
            these_heads = course.heads
            if not these_heads:
                continue
            for head in these_heads:
                if head:
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
            row.build_idnumber(teacher.idnumber)
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
        database = MoodleDBConnection()

        output_file = MoodleCSVFile(self.path_to_output + '/' + 'moodle_parents.txt')
        output_file.build_headers(['username', 'firstname', 'lastname', 'password', 'email', 'course_', 'group_', 'cohort_', 'type_'])

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)

            parent_account = database.get_unique_row("user",
                                                "username", "email",
                                                idnumber = student.family_id)
            if not parent_account:
                continue

            if student.courses():
                row = output_file.factory()
                row.build_username(parent_account.username)
                row.build_firstname('Parent of ')
                row.build_lastname(student.first + student.last)
                row.build_password('changeme')
                row.build_email(parent_account.email)
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

    def handle_new_student(self, results, family, student):
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
                    elif 'not_logged_in_yet' == comment:
                        self.logger.info("This family has had an account for a period of time and needs to be reminded of their account\n{}".format(family))
                        reinform_parent(family)
                self.server_information.clear_temp_storage('to_be_informed',
                                                           idnumber = family.idnumber)

            for child in family.children:
                results = self.server_information.get_temp_storage('to_be_informed',
                                                                   idnumber = child.num)
                if results:
                    self.handle_new_student(results, family, child)
                    self.server_information.clear_temp_storage('to_be_informed',
                                                           idnumber = child.num)

        # Ensure that informing has been done for students, which might otherwise be lost
        # in case something happened with the family account
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            results = self.server_information.get_temp_storage('to_be_informed',
                                                               idnumber = student.num)
            if results:
                self.handle_new_student(results, family, student, server=self.email_server)
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
    <td><a href="{url}">View (if available)</a></td>
    </tr>"""
        email_row = """
    <tr>
    <td>{course_short}</td>
    <td><a href="mailto:{teacher_email}">{teacher_email}</a></td>
    </tr>"""

        html_end = """</tbody>
    </table>"""

        if not self.config.has_section('MOODLE'):
            self.logger.warn("No moodle config available, cannot build profiles")
            return

        database = MoodleDBConnection()

        families = Families()

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            families.add(student)

        #TODO: Incorporate this into the whole thing later
        for family_key in families.families:
            family = families.families[family_key]
            ns = NS(family)
            try:
                ns.user_id = database.get_unique_row('user',
                                                     'id',
                                                     idnumber = family.num)
            except IndexError:
                # They don't have an account yet?
                continue

            for ns.extra_profile_field, ns.value in family.get_extra_profile_fields():
                ns.field_id = database.get_unique_row("user_info_field",
                                                      "id",
                                                      shortname=ns.extra_profile_field)
                if not ns.field_id:
                    self.logger.warn(ns("You need to manually add the {extra_profile_field} field!"))
                    continue
                if not ns.user_id:
                    continue
                there_already = database.get_unique_row("user_info_data", "data",
                                                        fieldid = ns.field_id,
                                                        userid = ns.user_id)
                if there_already:
                    if there_already == str(int(ns.value)):
                        # only call update if it's different
                        ns.value = int(ns.value)
                        self.logger.debug(ns('updating record {user_id} in ssis_user'))
                        database.call_sql(ns("update ssismdl_user_info_data set data = {value} where fieldid = {field_id} and userid = {user_id}"))
                    else:
                        self.logger.debug(ns("No change in {extra_profile_field}, so didn't call the database"))
                else:
                    self.logger.debug(ns('inserting {extra_profile_field}'))
                    database.sql(ns("insert into ssismdl_user_info_data (userid, fieldid, data, dataformat) values ({user_id}, {field_id}, {value}, 0)"))()
        for teacher_key in self.students.get_teacher_keys():
            teacher = self.students.get_teacher(teacher_key)
            formatter = NS(teacher)

            try:
                formatter.user_id = database.sql(formatter("select id from ssismdl_user where idnumber = '{num}'"))()[0][0]
            except IndexError:
                # They don't have an account yet?
                continue

            for formatter.extra_profile_field, formatter.value in teacher.get_extra_profile_fields():
                formatter.field_id = database.sql(formatter("select id from ssismdl_user_info_field where shortname = '{extra_profile_field}'"))()
                if not formatter.field_id:
                    self.logger.warn(formatter("You need to manually add the {extra_profile_field} field!"))
                    continue
                formatter.field_id = formatter.field_id[0][0]
                there_already = database.sql(formatter("select data from ssismdl_user_info_data where fieldid = {field_id} and userid = {user_id}"))()
                if there_already:
                    if not there_already[0][0] == str(int(formatter.value)):
                        # only call update if it's different
                        formatter.value = int(formatter.value)
                        self.logger.debug(formatter('updating record {user_id} in ssis_user'))
                        database.sql(formatter("update ssismdl_user_info_data set data = {value} where fieldid = {field_id} and userid = {user_id}"))()
                    else:
                        self.logger.debug(formatter("No change in {extra_profile_field}, so didn't call the database"))
                else:
                    self.logger.debug(formatter('inserting {extra_profile_field}'))
                    database.sql(formatter("insert into ssismdl_user_info_data (userid, fieldid, data, dataformat) values ({user_id}, {field_id}, {value}, 0)"))()

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)

            formatter = NS()
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

            homeroom_teacher = student.get_homeroom_teacher()
            if not homeroom_teacher:
                self.logger.warn("This student {} doesn't have a homeroom teacher? -- profile field not used, default to 'Not Available'".format(student.lastfirst))
                homeroom_teacher = '(Not available)'
            else:
                homeroom_teacher += '@ssis-suzhou.net'

            email_rows = [
                    email_row.format(**dict(teacher_name="Homeroom Teacher",
                                          teacher_email=homeroom_teacher,
                                          course_short = 'HROOM')),
                    email_row.format(**dict(teacher_name="All teachers",
                                          teacher_email=student.username + 'TEACHERS@student.ssis-suzhou.net', course_short='ALL TEACHERS'))
                                          ]

            if not formatter.user_id:
                self.logger.warn(formatter("User with idnumber {num} could not be found in the database, cannot put in profile: {username}"))
                continue

            # TODO: GET THE PROPER NAME OF THE TEACHER AND THE COURSE, YEAH?
            for teacherusername, course in student.get_teachers_classes():
                if course.startswith('HROOM'):
                    continue
                formatter.course_short = course
                query = database.sql(formatter("select id, fullname from ssismdl_course where shortname = '{course_short}'"))()
                if not query:
                     self.logger.info(formatter("Course with shortname {course_short} could not be found in the database"))
                     continue
                formatter.course_id, formatter.course_name = query[0]

                formatter.url = formatter("http://dragonnet.ssis-suzhou.net/course/user.php?mode=grade&id={course_id}&user={user_id}")
                grade_rows.append( formatter(grade_row) )

                formatter.teacher_email = teacherusername + '@ssis-suzhou.net'
                formatter.teacher_name = teacherusername
                formatter.student_name = student.lastfirst # for debugging
                email_rows.append( formatter(email_row) )
                self.logger.info(formatter('Added teacher {teacher_name} to {student_name}'))

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
                formatter.field_id = database.sql(formatter("select id from ssismdl_user_info_field where shortname = '{extra_profile_field}'"))()
                if not formatter.field_id:
                    self.logger.warn(formatter("You need to manually add the {extra_profile_field} field!"))
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

    def enroll_cohorts(self):
        dnet = ModUserEnrollments()
        for student in self.students:
            if student.is_secondary:
                for cohort in student._cohorts:
                    dnet.add_user_to_cohort(student.num, cohort)
        for parent in self.parents:
            if parent.is_secondary:
                for cohort in parent._cohorts:
                    dnet.add_user_to_cohort(parent.num, cohort)

    def remove_enrollments(self):
        """
        De-enrols all users from all courses, except for Grade 12s
        """
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            self.logger.info("Got to this one here: \n{}".format(student))
            dnet = MoodleDBConnection()
            modify = ModUserEnrollments()

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

            queried = dnet.get_user_enrollments(family.idnumber)

            for query in queried:
                _, group, course = query
                if course not in courses:
                    self.logger.warn('Unenrolling parent {} from course {}'.format(family.idnumber, course))
                    modify.unenrol_user_from_course(family.idnumber, course)


    def build_students(self):
        """
        Go through each student and do what is necessary to actually sync powerschool data
        """
        self.logger.debug("Building csv file for moodle")
        path_to_cli = self.config['MOODLE'].get('path_to_cli') if self.config.has_section('MOODLE') else None
        path_to_php = self.config['PHP']['php_path'] if self.config.has_section('PHP') else None
        modify = ModUserEnrollments()

        powerschool_autocom_file = MoodleCSVFile(self.path_to_output + '/' + 'student_emails_usernames.txt')
        powerschool_autocom_file.build_headers(['idnumber', 'email', 'username'])

        output_file = MoodleCSVFile(self.path_to_output + '/' + 'moodle_users.txt')
        output_file.build_headers(['username', 'idnumber', 'firstname', 'lastname', 'password', 'email', 'course_', 'group_', 'cohort_', 'type_'])

        secondary_homerooms = self.students.get_secondary_homerooms()
        elementary_homerooms = self.students.get_elementary_homerooms()

        self.logger.debug("Looping through students now")

        self.server_information.create_temp_storage('to_be_informed', 'idnumber', 'comment')

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)

            self.logger.warning("Got to this one here: \n{}".format(student))

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
                output_file.add_row(row)

                another_row = powerschool_autocom_file.factory()
                another_row.build_idnumber(student.num)
                another_row.build_email(student.email)
                another_row.build_username(student.username)
                powerschool_autocom_file.add_row(another_row)

            # Now process elementary
            # At the moment, elementary kids don't have dragonnet accounts nor do they have any email
            # Parents only need to have an account is all, and done.
            if student.is_elementary and int(student.num) > 30000:
                continue_until_no_errors = True
                times_through = 0
                while continue_until_no_errors:
                    try:
                        self.server_information.check_student(student, onlyraise=('NoParentAccount', 'NoEmailAddress',
                                                                                  'ParentAccountNotAssociated', 'NoStudentInMoodle'))

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

                another_row = powerschool_autocom_file.factory()
                another_row.build_idnumber(student.num)
                another_row.build_email(student.email)
                another_row.build_username(student.username)
                powerschool_autocom_file.add_row(another_row)

        output_file.output()
        powerschool_autocom_file.output()

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

        ns = NS(33)
        ns.PATH = path
        ns.EXT = '.txt'
        ns.INCLUDE = ' :include:'

        # The clear_folder routine erases all files in a certain folder
        # That has implications for postfix (when we're on the server), because
        # if you delete the .db files then postfix won't work. That is bad.
        # So, tell clear_folder to exclude them
        exclude_db_files = lambda x: x.endswith('.db')
        self.logger.debug("Clearing folders in postfix")
        clear_folder( ns.PATH, exclude=exclude_db_files)
        clear_folder(ns('{PATH}/grades'))
        clear_folder(ns('{PATH}/homerooms'))
        clear_folder(ns('{PATH}/classes'))
        clear_folder(ns('{PATH}/parentlink'))
        clear_folder(ns('{PATH}/teacherlink'))
        clear_folder(ns('{PATH}/special'))
        clear_folder(ns('{PATH}/departments'))
        clear_folder(ns('{PATH}/activities'))

        special_directory = []

        self.logger.debug("Setting up largest mailing lists first")

        for item in ['ALL', 'SEC', 'ELEM', 'KOREAN', 'CHINESE']:
            ns.this = item
            special_directory.append( ns('usebccparents{this}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparents{this}{EXT}') )

        with open( ns('{PATH}/special{EXT}'), 'w') as f:
            f.write( "\n".join(special_directory) )

        usebccparentsALL = []
        usebccstudentsALL = []
        usebccparentsELEM = []
        usebccparentsSEC = []
        usebccstudentsSEC = []
        usebccparentsCHINESE = []
        usebccparentsCHINESEELEM = []
        usebccparentsCHINESESEC = []
        usebccparentsCHINESEGRADE = defaultdict(list)
        usebccparentsKOREAN = []
        usebccparentsKOREANELEM = []
        usebccparentsKOREANSEC = []
        usebccparentsKOREANGRADE = defaultdict(list)
        usebccparentsJAPANESE = []
        usebccparentsJAPANESEELEM = []
        usebccparentsJAPANESESEC = []
        usebccparentsJAPANESEGRADE = defaultdict(list)
        # SWA DISTRIBUTION LISTS
        usebccparentsSWA = []
        usebccstudentsSWA = []
        usebccparentsSWAGRADE = defaultdict(list)
        usebccstudentsSWAGRADE = defaultdict(list)
        # HR AND GRADE
        usebccparentsHOMEROOM = defaultdict(list)
        usebccparentsGRADE = defaultdict(list)
        usebccparentsHOMEROOM = defaultdict(list)
        usebccstudentsELEM = defaultdict(list)
        usebccstudentsGRADE = defaultdict(list)
        usebccstudentsHOMEROOM = defaultdict(list)
        parentlink = defaultdict(list)
        teacherlink = defaultdict(list)
        teachersGRADE = defaultdict(list)
        hrlink = defaultdict(list)
        classes = defaultdict(list)
        classesPARENTS = defaultdict(list)
        special = defaultdict(list)

        self.logger.debug('Clearing the table on moodle')
        self.server_information.create_temp_storage('student_email_info',
          'list', 'email')
        self.server_information.empty_temp_storage('student_email_info')
        write_db = self.server_information.add_temp_storage
        self.logger.debug("Setting email lists")

        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            ns.homeroom = student.homeroom
            ns.grade = student.grade

            # TODO: Check for now grade or homeroom and warn
            if student.grade is "" or student.grade is None:
                self.logger.warn("This student does not have a grade:\n{}".format(student))
            if not student.homeroom:
                self.logger.warn("This student does not have a homeroom:\n{}".format(student))

            # USE ns.grade BECAUSE student.grade IS AN INTEGER
            # TODO: DO WE MAKE student.grade A STRING?
            # OR PUT THIS IN THE OBJECT SOMEWHOW?
            if ns.grade <= 0:
                ns.grade = {0: 'K', -1: 'R', -2: 'G', -3:'PK', -4:'N'}.get(ns.grade, None)

            usebccparentsALL.extend( student.guardian_emails )
            ns.grade and usebccparentsGRADE[ns.grade].extend(student.guardian_emails)
            ns.homeroom and usebccparentsHOMEROOM[ns.homeroom].extend(student.guardian_emails)

            if student.is_elementary:
                usebccparentsELEM.extend(student.guardian_emails)
                parentlink[student.username].extend( student.guardian_emails )
                teacherlink[student.username].extend(student.teacher_emails)
                hrlink[student.username].append(student.homeroom_teacher_email)

            if student.is_secondary:
                usebccparentsSEC.extend(student.guardian_emails)
                usebccstudentsSEC.append(student.email)
                if ns.grade:
                    usebccstudentsGRADE[ns.grade].append(student.email)
                    teachersGRADE[ns.grade].extend(student.teacher_emails)
                if student.homeroom:
                    usebccstudentsHOMEROOM[ns.homeroom].append(student.email)
                parentlink[student.username].extend( student.guardian_emails )
                teacherlink[student.username].extend(student.teacher_emails)
                hrlink[student.username].append(student.homeroom_teacher_email)
                for group in student.groups():
                    classes[group].append(student.email)
                    classesPARENTS[group].extend(student.guardian_emails)

            if student.is_chinese:
                usebccparentsCHINESE.extend( student.guardian_emails )
                student.is_secondary and usebccparentsCHINESESEC.extend( student.guardian_emails )
                student.is_elementary and usebccparentsCHINESEELEM.extend( student.guardian_emails )
                usebccparentsCHINESEGRADE[ns.grade].extend( student.guardian_emails )
            if student.is_korean:
                usebccparentsKOREAN.extend( student.guardian_emails )
                student.is_secondary and usebccparentsKOREANSEC.extend( student.guardian_emails )
                student.is_elementary and usebccparentsKOREANELEM.extend( student.guardian_emails )
                usebccparentsKOREANGRADE[ns.grade].extend( student.guardian_emails )
            if student.is_japanese:
                usebccparentsJAPANESE.extend( student.guardian_emails )
                student.is_secondary and usebccparentsJAPANESESEC.extend( student.guardian_emails )
                student.is_elementary and usebccparentsJAPANESEELEM.extend( student.guardian_emails )
                usebccparentsJAPANESEGRADE[ns.grade].extend( student.guardian_emails )
            if student.is_SWA:
                usebccparentsSWA.extend( student.guardian_emails )
                usebccstudentsSWA.append( student.email )
                usebccparentsSWAGRADE[ns.grade].extend( student.guardian_emails )
                usebccstudentsSWAGRADE[ns.grade].append( student.email )

        for ns.email in set(usebccparentsALL):
            write_db('student_email_info', list='usebccparentsALL', email=ns.email)

        for ns.email in set(usebccparentsSEC):
            write_db('student_email_info', list='usebccparentsSEC', email=ns.email)

        for ns.email in set(usebccparentsELEM):
            write_db('student_email_info', list='usebccparentsELEM', email=ns.email)

        for ns.grade in usebccparentsGRADE:
            for ns.email in set(usebccparentsGRADE[ns.grade]):
                write_db('student_email_info', list=ns('usebccparents{grade}'), email=ns('{email}'))

        for ns.grade in usebccstudentsGRADE:
            for ns.email in set(usebccstudentsGRADE[ns.grade]):
                write_db('student_email_info', list=ns('usebccstudents{grade}'), email=ns('{email}'))

        for ns.grade in teachersGRADE:
            for ns.email in set(teachersGRADE[ns.grade]):
                write_db('student_email_info', list=ns('teachers{grade}'), email=ns('{email}'))

        for ns.homeroom in usebccparentsHOMEROOM:
            for ns.email in set(usebccparentsHOMEROOM[ns.homeroom]):
                write_db('student_email_info', list=ns('usebccparents{homeroom}'), email=ns('{email}'))

        for ns.homeroom in usebccstudentsHOMEROOM:
            for ns.email in set(usebccstudentsHOMEROOM[ns.homeroom]):
                write_db('student_email_info', list=ns('usebccstudents{homeroom}'), email=ns('{email}'))

        for ns.student in teacherlink:
            for ns.email in set(teacherlink[ns.student]):
                write_db('student_email_info', list=ns('{student}TEACHERS'), email=ns('{email}'))

        for ns.student in parentlink:
            for ns.email in set(parentlink[ns.student]):
                write_db('student_email_info', list=ns('{student}PARENTS'), email=ns('{email}'))

        for ns.student in hrlink:
            for ns.email in set(hrlink[ns.student]):
                write_db('student_email_info', list=ns('{student}HR'), email=ns('{email}'))

        for ns.klass in classes:
            for ns.email in classes[ns.klass]:
                write_db('student_email_info', list=ns('{klass}'), email=ns('{email}'))

        for ns.klass in classesPARENTS:
            for ns.email in classes[ns.klass]:
                write_db('student_email_info', list=ns('{klass}PARENTS'), email=ns('{email}'))

        # GRADES
        directory_write = []
        for ns.grade in usebccparentsGRADE:
            directory_write.append( ns('usebccparents{grade}{COLON}{INCLUDE}{PATH}{SLASH}grades{SLASH}usebccparents{grade}{EXT}') )
            with open( ns('{PATH}{SLASH}grades{SLASH}usebccparents{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsGRADE[ns.grade])) )
        for ns.grade in usebccstudentsGRADE:
            directory_write.append( ns('usebccstudents{grade}{COLON}{INCLUDE}{PATH}{SLASH}grades{SLASH}usebccstudents{grade}{EXT}') )
            with open( ns('{PATH}{SLASH}grades{SLASH}usebccstudents{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccstudentsGRADE[ns.grade])) )
        for ns.grade in teachersGRADE:
            directory_write.append( ns('teachers{grade}{COLON}{INCLUDE}{PATH}{SLASH}grades{SLASH}teachers{grade}{EXT}') )
            with open( ns('{PATH}{SLASH}grades{SLASH}teachers{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(teachersGRADE[ns.grade])) )
        with open( ns('{PATH}{SLASH}grades{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

            #HS

        # HOMEROOMS
        directory_write = []
        for ns.homeroom in usebccparentsHOMEROOM:
            directory_write.append( ns('usebccparents{homeroom}{COLON}{INCLUDE}{PATH}{SLASH}homerooms{SLASH}usebccparents{homeroom}{EXT}') )
            with open( ns('{PATH}{SLASH}homerooms{SLASH}usebccparents{homeroom}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsHOMEROOM[ns.homeroom])) )
        for ns.homeroom in usebccstudentsHOMEROOM:
            directory_write.append( ns('usebccstudents{homeroom}{COLON}{INCLUDE}{PATH}{SLASH}homerooms{SLASH}usebccstudents{homeroom}{EXT}') )
            with open( ns('{PATH}{SLASH}homerooms{SLASH}usebccstudents{homeroom}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccstudentsHOMEROOM[ns.homeroom])) )
        with open( ns('{PATH}{SLASH}homerooms{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        # TEACHERLINK
        directory_write = []
        for ns.student in teacherlink:
            directory_write.append( ns('{student}TEACHERS{COLON}{INCLUDE}{PATH}{SLASH}teacherlink{SLASH}{student}TEACHERS{EXT}') )
            with open( ns('{PATH}{SLASH}teacherlink{SLASH}{student}TEACHERS{EXT}'), 'w') as f:
                f.write( '\n'.join(set(teacherlink[ns.student])) )
        with open( ns('{PATH}{SLASH}teacherlink{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        # PARENTLINK
        directory_write = []
        for ns.student in parentlink:
            directory_write.append( ns('{student}PARENTS{COLON}{INCLUDE}{PATH}{SLASH}parentlink{SLASH}{student}PARENTS{EXT}') )
            with open( ns('{PATH}{SLASH}parentlink{SLASH}{student}PARENTS{EXT}'), 'w') as f:
                f.write( '\n'.join(set(parentlink[ns.student])) )
        with open( ns('{PATH}{SLASH}parentlink{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        # HRLINK
        directory_write = []
        for ns.student in hrlink:
            if hrlink[ns.student]:  # not all kids have a homeroom teacher....
                directory_write.append( ns('{student}HR{COLON}{INCLUDE}{PATH}{SLASH}homeroomlink{SLASH}{student}HR{EXT}') )
                with open( ns('{PATH}{SLASH}homeroomlink{SLASH}{student}HR{EXT}'), 'w') as f:
                    try:
                        f.write( '\n'.join(set(hrlink[ns.student])) )
                    except TypeError:
                      pass
        with open( ns('{PATH}{SLASH}homeroomlink{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsALL{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsALL) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsSEC{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsSEC) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsELEM{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsELEM) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESE{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsCHINESE) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESESEC{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsCHINESESEC) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESEELEM{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsCHINESEELEM) )

        for ns.grade in usebccparentsCHINESEGRADE:
            with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESE{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsCHINESEGRADE[ns.grade])) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREAN{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsKOREAN) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREANELEM{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsKOREANSEC) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREANSEC{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsKOREANSEC) )

        for ns.grade in usebccparentsKOREANGRADE:
            with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREAN{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsKOREANGRADE[ns.grade])) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsJAPANESE{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsJAPANESE) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsJAPANESESEC{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsJAPANESESEC) )

        for ns.grade in usebccparentsJAPANESEGRADE:
            with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsJAPANESE{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsJAPANESEGRADE[ns.grade])) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsSWA{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsSWA) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccstudentsSWA{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccstudentsSWA) )

        with open( ns('{PATH}{SLASH}special{EXT}'), 'w') as f:
            for ns.this in ['usebccparentsALL', 'usebccparentsSEC', 'usebccparentsELEM',
                            'usebccparentsKOREAN', 'usebccparentsKOREANSEC', 'usebccparentsKOREANELEM',
                            'usebccparentsCHINESE', 'usebccparentsCHINESESEC', 'usebccparentsCHINESEELEM',
                            'usebccparentsJAPANESE', 'usebccparentsJAPANESESEC', 'usebccparentsJAPANESEELEM',
                            'usebccparentsSWA', 'usebccstudentsSWA']:
                f.write( ns('{this}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}{this}{EXT}{NEWLINE}') )
            for ns.grade in usebccparentsKOREANGRADE:
                f.write( ns('usebccparentsKOREAN{grade}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparentsKOREAN{grade}{EXT}{NEWLINE}') )
            for ns.grade in usebccparentsCHINESEGRADE:
                f.write( ns('usebccparentsCHINESE{grade}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparentsCHINESE{grade}{EXT}{NEWLINE}') )
            for ns.grade in usebccparentsJAPANESEGRADE:
                f.write( ns('usebccparentsJAPANESE{grade}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparentsJAPANESE{grade}{EXT}{NEWLINE}') )

        # CLASSES
        directory_write = []
        for ns.klass in classes:
            directory_write.append( ns('{klass}{COLON}{INCLUDE}{PATH}{SLASH}classes{SLASH}{klass}{EXT}') )
        for ns.klass in classesPARENTS:
            directory_write.append( ns('{klass}PARENTS{COLON}{INCLUDE}{PATH}{SLASH}classes{SLASH}{klass}PARENTS{EXT}') )
        with open( ns('{PATH}{SLASH}classes{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        for ns.klass in classes:
            with open( ns('{PATH}{SLASH}classes{SLASH}{klass}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(classes[ns.klass])) )

        for ns.klass in classesPARENTS:
            with open( ns('{PATH}{SLASH}classes{SLASH}{klass}PARENTS{EXT}'), 'w') as f:
                f.write( '\n'.join(set(classesPARENTS[ns.klass])) )

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
                ns.homeroom = teacher.homeroom
                if not teacher.homeroom in homeroom_teachers_dict.keys():
                    homeroom_teachers_dict[teacher.homeroom] = True
                    setup_postfix = ns('{PATH}/departments{EXT}')
                    with open(setup_postfix, 'a') as f:
                        f.write(ns("homeroomteachers{homeroom}: :include:{PATH}/departments/homeroomteachers{homeroom}{EXT}\n"))
                setup_postfix = ns('{PATH}/departments/homeroomteachers{homeroom}{EXT}')
                with open(setup_postfix, 'a') as f:
                    f.write(teacher.email + '\n')

        for ns.department in list(depart_dict.keys()):
            # department is now actually the email name we want to use
            setup_postfix = ns('{PATH}/departments{EXT}')
            with open(setup_postfix, 'a') as f:
                f.write( ns("{department}: :include:{PATH}/departments/{department}{EXT}\n") )

            setup_postfix = ns('{PATH}/departments/{department}{EXT}')
            with open(setup_postfix, 'w') as f:
                f.write( "\n".join(depart_dict[ns.department]) )

        # SETUP SECONDARY ACTIVITIES
        results = self.server_information.get_all_users_activity_enrollments()
        ns = NS()
        ns.domain = 'student.ssis-suzhou.net'
        activities_postfix = defaultdict(list)
        activities_postfix_parents = defaultdict(list)
        for result in results:
            activity_name, student_key = result
            student = self.students.get_student(student_key)
            if not student:
                self.logger.warning('This student is listed as having enrolled into an activity, ' + \
                                    'but no longer seems to be available at school. Ignored. {}'.format(student_key))
                continue
            activities_postfix[activity_name].append(student.email)
            activities_postfix_parents[activity_name].append(student.parent_link_email)

        # DO THE ACTIVITY EMAILS
        ns.path = config_get_section_attribute('DIRECTORIES', 'path_to_postfix')
        ns.base = 'activities'
        ns.SUFFIX = "ACT"
        ns.EXT = '.txt'
        ns.INCLUDE = ':include:'
        ns.activities_path = ns('{path}{SLASH}activities')
        with open(ns('{path}{SLASH}{base}{EXT}'), 'w'):
            pass

        for activity_name in activities_postfix:
            ns.handle = name_to_email(activity_name)
            ns.full_email = ns('{handle}{SUFFIX}')
            with open(ns('{path}{SLASH}{base}{EXT}'), 'a') as f:
                f.write(ns('{full_email}{COLON}{SPACE}{INCLUDE}' + \
                           '{activities_path}{SLASH}{full_email}{EXT}{NEWLINE}'))
            with open(ns('{activities_path}{SLASH}{full_email}{EXT}'), 'a') as f:
                f.write("\n".join(activities_postfix[activity_name]))

        ns.SUFFIX = "ACTPARENTS"
        for activity_name in activities_postfix_parents:
            ns.handle = name_to_email(activity_name)
            ns.full_email = ns('{handle}{SUFFIX}')
            with open(ns('{path}{SLASH}{base}{EXT}'), 'a') as f:
                f.write(ns('{full_email}{COLON}{SPACE}{INCLUDE}' + \
                           '{activities_path}{SLASH}{full_email}{EXT}{NEWLINE}'))
            with open(ns('{activities_path}{SLASH}{full_email}{EXT}'), 'a') as f:
                f.write("\n".join(activities_postfix_parents[activity_name]))

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

        from utils.DB import MoodleDBConnection as DNET
        dn = DNET()
        # id_map is needed because I need to know the id in the database
        id_map = dn.prepare_id_username_map()

        # result is the necessary format to update reset passwords in Moodle
        result = []
        result2 = []
        indexes = []
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            f = NS(student)
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
