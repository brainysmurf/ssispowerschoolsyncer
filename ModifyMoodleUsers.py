from utils.PHPMoodleLink import CallPHP
from utils.Formatter import Smartformatter
from utils.PythonMail import send_html_email

new_student_html = """
<html>
<p>Dear {homeroom} Homeroom Teacher:</p>
<p>You have a new student in your homeroom, {lastfirst}. Here is their DragonNet account information.</p>
<blockquote><ul>
<li><strong>Username: {username}</strong></li>
<li><strong>Password: changeme</strong></li>
</ul></blockquote>
<p>Here is their email address:</p><blockquote><ul>
<li><strong>Email: {username}@student.ssis-suzhou.net</strong></li>
</ul></blockquote>
<p>Perhaps one of the first things the buddy can do is take him or her through logging into DragonNet and Student Email and changing the passwords.</p>
<p><em>Reminder: They should be encouraged to use the same password for both accounts. Although the same username is the same, changing the password on DragonNet does not change the Student Email password, and vice versa.</em></p>
<p>Dear Subject Teachers:</p>
<p>Please note that this student has been enrolled in the appropriate classes on DragonNet.</p>
<p>Regards,</p>
<p>DragonNet Admin</p>
</html>
"""
changed_name_html = """
<html>
<p>Dear {homeroom} Homeroom Teacher:</p>
<p>A student in your homeroom, {lastfirst}, passport information has changed, and therefore so has his DragonNet account login information. Please inform him or her of this.</p>
<blockquote><ul>
<li><strong>Username: {username}</strong></li>
</ul></blockquote>
<p><em>Their password has not changed, and are still enrolled in their courses.</em></p>
<p>Regards,</p>
<p>DragonNet Admin</p>
</html>
"""

test_run = False

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

class StudentModifier(CallPHP):

      def new_student(self, student):
            if test_run:
                  test('create_account', student, '')
            else:
                  error = self.create_account( student.username, student.email, student.first, student.last, student.num )
                  print(error)

            for cohort in student.cohorts():
                  if test_run:
                        test('add_user_to_cohort', student, cohort)
                  else:
                        error = self.add_user_to_cohort( student.num, cohort )
                        print(error)
            for index in range(0, len(student.courses())):
                  course = student.courses()[index]
                  group  = student.groups()[index]
                  if test_run:
                        test('enrol_user_in_course', student, course + ' ' + group)
                  else:
                        error = self.enrol_user_in_course( student.num, course, group )
                        print(error)

            sender = '"DragonNet Admin" <lcssisadmin@student.ssis-suzhou.net>'
            sf = Smartformatter()
            sf.take_dict(student)
            recipient = student.get_homeroom_teacher()
            if recipient:
                  recipient += "@ssis-suzhou.net"
            else:
                  recipient = 'adammorris@ssis-suzhou.net'
            cc_who = []
            if student.grade in [11, 12]:
                  cc_who.append('santinagambrill@ssis-suzhou.net')
                  cc_who.append('matthewmarshall@ssis-suzhou.net')
            elif student.grade in [6, 7, 8, 9, 10]:
                  cc_who.append('aubreycurran@ssis-suzhou.net')
            sf(homeroomteacher=recipient)
            html = sf(new_student_html)
            if test_run:
                  test('send_html_email', student, recipient)
            else:
                  send_html_email(sender, recipient,
                            sf("New Student in Homeroom {homeroom}, {lastfirst}"),
                            html,
                            cc_who,
                            bccwho="lcssisadmin@student.ssis-suzhou.net")

      def change_name(self, student):
            if test_run:
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
            if test_run:
                  test('no_email', student, '')
            else:
                  error = self.shell( sf("/bin/bash /home/lcssisadmin/ssispowerschoolsync/src/MakeNewStudentAccount.sh {num} {username} '{lastfirst}'") )
                  print(error)

      def new_parent(self, student):
            test_run = True
            emails = student.parent_emails
            if len(emails) == 1:
                  parent_email = emails[0]
            elif len(emails) > 1:
                  parent_email = emails[1]
            else:
                  print("No parent email available, not creating parent account for {}\n{}".format(student.family_id, student))
                  return

            if test_run:
                  test('new_parent', student, student.family_id)
            else:
                  error = self.create_account( parent_email, parent_email, 'Parent ', parent_email, student.family_id )
                  print(error)


      def parent_account_not_associated(self, student):
            test_run = True
            if test_run:
                  test('parent_account_not_associated', student, student.family_id)
                  return
            else:
                  error = self.associate_child_to_parent( student.family_id, student.username )
                  print(error)

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
                  if test_run:
                        test('add_user_to_cohort', student.family_id, cohort)
                  else:
                        error = self.add_user_to_cohort( student.family_id, cohort )
                        print(error)
                        
            for index in range(0, len(student.courses())):
                  course = student.courses()[index]
                  group  = student.groups()[index]
                  if test_run:
                        test('enrol_user_in_course', student, course + ' ' + group + ' NOT the student, but the parent {}'.format(student.family_id))
                  else:
                        error = self.enrol_user_in_course( student.family_id, course, group, 'Parent' )
                        print(error)
            


class FakeStudent:

      def __init__(self):
            self.username = "success"
            self.fullname = "Mr Success"
            self.idnum = 555555555
      

if __name__ == "__main__":
      s = FakeStudent()
      m = StudentModifier()
      m.no_email(s)
