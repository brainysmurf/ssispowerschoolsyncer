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
                        error = self.add_user_to_cohort( student.username, cohort )
                        print(error)
            for index in range(0, len(student.courses())):
                  course = student.courses()[index]
                  group  = student.groups()[index]
                  if test_run:
                        test('enrol_user_in_course', student, course + ' ' + group)
                  else:
                        error = self.enrol_user_in_course( student.username, course, group )
                        print(error)

            sender = '"DragonNet Admin" <lcssisadmin@student.ssis-suzhou.net>'
            sf = Smartformatter()
            sf.take_dict(student)
            recipient = student.get_homeroom_teacher()
            sf(homeroomteacher=recipient)
            html = sf(new_student_html)
            recipient += "@ssis-suzhou.net"
            if test_run:
                  test('send_html_email', student, recipient)
            else:
                  send_html_email(sender, recipient,
                            sf("New Student in Homeroom {homeroom}, {lastfirst}"),
                            html,
                            #ccwho = [t+"@ssis-suzhou.net" for t in student.teachers()],
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
                  test('no_email', student)
            else:
                  error = self.shell( sf('/bin/bash /home/lcssisadmin/ssispowerschoolsync/src/MakeNewStudentAccount.sh {num} {username} "{lastfirst}"') )
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
