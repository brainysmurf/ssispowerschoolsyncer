"""
HIGHER LEVEL CLASS THAN CALLPHP
"""

from psmdlsyncer.php.PHPMoodleLink import CallPHP

from psmdlsyncer.utils import NS
from psmdlsyncer.settings import config_get_section_attribute

class ModUserEnrollments(CallPHP):
      """
      Takes raw information and sends it on to PHP
      At this point we should only be passing it
      """
      def __init__(self):
            super().__init__()
            self.default_logger = self.logger.debug
            self.new_email_cmd = config_get_section_attribute('EMAIL', 'new_student_cmd')
            path_to_home = config_get_section_attribute('EMAIL', 'path_to_home')

      def handle_error(self, error):
            print(error)
            if error and '-' in error:  # negative value indicates error
                  self.logger.warning(error)

      def enrol_student_into_course(self, student_idnumber, course_idnumber, group_name):
            error = self.enrol_user_into_course( student_idnumber, course_idnumber, group_name, "student" )
            self.handle_error(error)

      def enrol_teacher_into_course(self, teacher_idnumber, course_idnumber, group_name):
            error = self.enrol_user_into_course( teacher_idnumber, course_idnumber, group_name, "teacher" )
            self.handle_error(error)

      def deenrol_student_from_course(self, student_idnumber, course_idnumber):
            error = self.unenrol_user_from_course( student_idnumber, course_idnumber )
            self.handle_error(error)

      def deenrol_teacher_from_course(self, teacher_idnumber, course_idnumber):
            error = self.unenrol_user_from_course( teacher_idnumber, course_idnumber )
            self.handle_error(error)

      def enrol_parent_into_course(self, student_idnumber, course_idnumber, group_name):
            error = super().enrol_user_into_course( student_idnumber, course_idnumber, group_name, "parent" )
            self.handle_error(error)

      def enrol_teacher_into_course(self, student_idnumber, course_idnumber, group_name):
            error = super().enrol_user_into_course( student_idnumber, course_idnumber, group_name, "teacher" )
            self.handle_error(error)

      def enrol_student_into_courses(self, student):
            """
            Also sets up groups, and creates them if they don't exist
            """
            # TODO: This should really be done based on enrollment available in the model
            for key in student.enrollments:
                  course = key
                  group  = student.enrollments[key]
                  self.default_logger("Enrolling student {} into course {} in group {}".format(student.num, course, group))
                  error = self.enrol_user_in_course( student.num, course, group, 'Student' )
                  self.handle_error(error)

      def enrol_teacher_into_courses(self, teacher):
            # TODO: Make an abstract routine for use with teachers, parents, students
            pass

      def enrol_parent_into_courses(self, student):
            for index in range(0, len(student.courses())):
                  course = student.courses()[index]
                  group  = student.groups()[index]
                  error = self.enrol_user_in_course( student.family_id, course, group, 'Parent' )
                  self.handle_error(error)

      def new_student(self, student):
            try:
                  auth = student.login_method
            except AttributeError:
                  self.logger.warning("new_student called on {}, but no login_method provided, not adding".format(student))
                  return
            self.logger.warning('Creating {} account for {}'.format(auth, student))
            error = self.create_account( student.username, student.email, student.first, student.last, student.num, auth=auth )
            self.handle_error(error)

            for cohort in student.cohorts:
                  self.default_logger("Adding {} to cohort {}".format(student.num, cohort))
                  error = self.add_user_to_cohort( student.num, cohort )
                  self.handle_error(error)
            self.enrol_student_into_courses(student)
            self.logger.info("Successfully created new moodle account -- and enabled enrollments -- for student {}".format(student))

      def new_teacher(self, teacher):
            pass

      def no_email(self, student):
            sf = NS(student)
            sf.new_student_cmd = self.new_email_cmd

            error = self.shell( sf("/bin/bash {new_student_cmd} {num} {username} '{lastfirst}'") )
            self.handle_error(error)

      def enroll_in_groups(self, student):
            self.verbose and print("enroll_in_groups")
            get_groups = self.sql('select id, name from ssismdl_groups')()
            self._groups = {}
            self.verbose and print("Setting up _groups dict now")
            for item in get_groups:
                  groupid, groupname = item
            self._groups[groupid] = groupname

      def new_parent(self, student):
            emails = student.parent_emails
            if len(emails) == 1:
                  parent_email = emails[0]
            elif len(emails) > 1:
                  parent_email = emails[1]
            else:
                  #TODO: email this to admin
                  self.verbose and print("No parent email available, not creating parent account for {}\n{}".format(student.family_id, student))
                  return

            error = self.create_account( parent_email, parent_email, 'Parent ', parent_email, student.family_id )
            self.handle_error(error)

      def new_support_staff(self, staff):
            """
            Support staff have fairly simple accounts
            IStaff: username
                    first_name
                    last_name
                    email
                    num
            """
            error = self.create_account( staff.username, staff.email, staff.first_name, staff.last_name, staff.num )
            self.handle_error(error)

            error = self.add_user_to_cohort( staff.num, 'adminALL' )
            self.handle_error(error)

      def parent_account_not_associated(self, student):
            error = self.associate_child_to_parent( student.family_id, student.num )
            self.handle_error(error)

            cohorts = ['parentsALL']
            if student.is_secondary:
                  cohorts.append('parentsSEC')
            if student.is_elementary:
                  cohorts.append('parentsELEM')
            if student.is_korean:
                  cohorts.append('parentsKOREAN')
            if student.is_chinese:
                  cohorts.append('parentsCHINESE')

            for cohort in cohorts:
                  error = self.add_user_to_cohort( student.family_id, cohort )
                  self.handle_error(error)

            for index in range(0, len(student.courses())):
                  course = student.courses()[index]
                  group  = student.groups()[index]
                  error = self.enrol_user_in_course( student.family_id, course, group, 'Parent' )
                  self.handle_error(error)


class FakeStudent:

      def __init__(self):
            self.username = "success"
            self.fullname = "Mr Success"
            self.idnum = 555555555


if __name__ == "__main__":
      s = FakeStudent()
      m = DragonNetModifier()
      m.no_email(s)
