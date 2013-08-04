from psmdlsyncer.utils.PHPMoodleLink import CallPHP
from psmdlsyncer.utils.Formatter import Smartformatter
from psmdlsyncer.utils.PythonMail import send_html_email

def test(id, student, extra):
      sf = Smartformatter()
      if isinstance(student, str):
            print(student, extra)
            return
      sf.take_dict(student)
      sf.define(extra=extra)
      print (
            {
            'create_account': sf('Create user account'),
            'add_user_to_cohort': sf('Add user {lastfirst} to cohort {extra}'),
            'enrol_user_in_course': sf('Add user {lastfirst} to course and group {extra}'),
            'send_html_email': sf('Sending homeroom teacher {extra} email information about {lastfirst}'),
            'change_name': sf("Changing name of {lastfirst}"),
            'no_email': sf("This student {lastfirst} does not have an email account"),
            }.get(id, None)
            )

class DragonNetModifier(CallPHP):

      def enrol_student_into_courses(self, student):
            """
            Also sets up groups, and creates them if they don't exist
            """
            for index in range(0, len(student.courses())):
                  course = student.courses()[index]
                  group  = student.groups()[index]
                  if self.dry_run:
                        test('enrol_user_in_course', student, course + ' ' + group)
                  else:
                        error = self.enrol_user_in_course( student.num, course, group, 'Student' )
                        if error and error[nnao0] == '-':
                              # got an error code, print it
                              output = input if self.verbose else print
                              output(error)

      def enrol_parent_into_courses(self, student):
            for index in range(0, len(student.courses())):
                  course = student.courses()[index]
                  group  = student.groups()[index]
                  if self.dry_run:
                        test('enrol_user_in_course', student, course + ' ' + group)
                  else:
                        error = self.enrol_user_in_course( student.family_id, course, group, 'Parent' )
                        if error and error[0] == '-':
                              # got an error code, print it
                              if self.verbose:
                                    output = input
                              else:
                                    output = print
                              output(error)

      def new_student(self, student):
            if self.dry_run:
                  test('create_account', student, '')
            else:
                  error = self.create_account( student.username, student.email, student.first, student.last, student.num )
                  print(error)

            #TODO: Test for cohorts, raise error, and move this to seperate function
            for cohort in student.cohorts():
                  if self.dry_run:
                        test('add_user_to_cohort', student, cohort)
                  else:
                        error = self.add_user_to_cohort( student.num, cohort )
                        print(error)
            self.enrol_student_into_courses(student)

            #TODO: Modify profile fields as appropriate

      def change_name(self, student):
            if self.dry_run:
                  test('change_name', student, '')
            else:
                  error = self.change_username(student.num, student.username)
                  print(error)
                  sender = '"DragonNet Admin" <lcssisadmin@student.ssis-suzhou.net>'
                  sf = Smartformatter()
                  sf.take_dict(student)
                  recipient = student.get_homeroom_teacher()+"@ssis-suzhou.net"
                  html = sf(changed_name_html)
                  send_html_email(sender, recipient,
                                  sf("{lastfirst}'s DragonNet Username has changed"),
                                  html,
                                  bccwho="lcssisadmin@student.ssis-suzhou.net")

      def no_email(self, student):
            sf = Smartformatter()
            sf.take_dict(student)
            if self.dry_run:
                  test('no_email', student, '')
            else:
                  error = self.shell( sf("/bin/bash /home/lcssisadmin/ssispowerschoolsync/src/MakeNewStudentAccount.sh {num} {username} '{lastfirst}'") )
                  if error and error[0] == '-':
                        output = input if self.verbose else print
                        output(error)

      def create_groups_for_student(self, student):
            self.verbose and print("create_groups_for_students")
            get_groups = self.sql('select id, name from ssismdl_groups')()
            _groups = {}
            self.verbose and print("Setting up _groups dict now")
            for item in get_groups:
                  groupid, groupname = item
            _groups[groupname] = groupid

            for group in student.groups():
                  if not group in _groups.keys():
                        self.create_groups_for_course(group, )

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

            if self.dry_run:
                  test('new_parent', student, student.family_id)
            else:
                  error = self.create_account( parent_email, parent_email, 'Parent ', parent_email, student.family_id )
                  if error and error[0] == '-':
                        output = input if self.verbose else print
                        output(error)

      def new_support_staff(self, staff):
            """
            Support staff have fairly simple accounts
            IStaff: username
                    first_name
                    last_name
                    email
                    num
            """
            if self.dry_run:
                  test('new_staff', staff, '')
            else:
                  error = self.create_account( staff.username, staff.email, staff.first_name, staff.last_name, staff.num )
                  if error and error[0] == '-':
                        output = input if self.verbose else print
                        output(error)

            if self.dry_run:
                  test('add_user_to_cohort', staff.num, 'adminALL')
            else:
                  error = self.add_user_to_cohort( staff.num, 'adminALL' )
                  print(error)

      def parent_account_not_associated(self, student):
            if self.dry_run:
                  test('parent_account_not_associated', student, student.family_id)
                  return
            else:
                  error = self.associate_child_to_parent( student.family_id, student.num )
                  if error and error[0] == '-':
                        output = input if self.verbose else print
                        output(error)

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
                  if self.dry_run:
                        test('add_user_to_cohort', student.family_id, cohort)
                  else:
                        error = self.add_user_to_cohort( student.family_id, cohort )
                        print(error)
                        
            for index in range(0, len(student.courses())):
                  course = student.courses()[index]
                  group  = student.groups()[index]
                  if self.dry_run:
                        test('enrol_user_in_course', student, course + ' ' + group + ' NOT the student, but the parent {}, '.format(student.family_id), 'Parent')
                  else:
                        error = self.enrol_user_in_course( student.family_id, course, group, 'Parent' )
                        if error and error[0] == '-':
                              output = input if self.verbose else print
                              output(error)

class FakeStudent:

      def __init__(self):
            self.username = "success"
            self.fullname = "Mr Success"
            self.idnum = 555555555
      

if __name__ == "__main__":
      s = FakeStudent()
      m = DragonNetModifier()
      m.no_email(s)