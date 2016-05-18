"""
HIGHER LEVEL CLASS THAN CALLPHP
"""
from psmdlsyncer.php.PHPMoodleLink import CallPHP

from psmdlsyncer.utils import NS
from psmdlsyncer.settings import config_get_section_attribute
import functools
import psmdlsyncer.inform as inform

class ModUserEnrollments(CallPHP):
    """
    Takes raw information and sends it on to PHP
    At this point we should only be passing it
    """
    def __init__(self):
        super().__init__()
        self.default_logger = self.logger.debug
        self.new_email_cmd = config_get_section_attribute('DIRECTORIES', 'path_to_newstudent_script')

    def enrol_student_into_course(self, student_idnumber, course_idnumber, group_name):
        self.enrol_user_into_course( student_idnumber, course_idnumber, group_name, "student" )

    def enrol_teacher_into_course(self, teacher_idnumber, course_idnumber, group_name):
        self.enrol_user_into_course( teacher_idnumber, course_idnumber, group_name, "teacher" )

    def deenrol_student_from_course(self, student_idnumber, course_idnumber):
        self.unenrol_user_from_course( student_idnumber, course_idnumber )

    def deenrol_teacher_from_course(self, teacher_idnumber, course_idnumber):
        self.unenrol_user_from_course( teacher_idnumber, course_idnumber )

    def deenrol_parent_from_course(self, parent_idnumber, course_idnumber):
        self.unenrol_user_from_course( parent_idnumber, course_idnumber )

    def enrol_parent_into_course(self, parent_idnumber, course_idnumber, group):
        self.enrol_user_into_course( parent_idnumber, course_idnumber, group.name, group.idnumber, "parent" )

    def enrol_teacher_into_course(self, teacher_idnumber, course_idnumber, group):
        self.enrol_user_into_course( teacher_idnumber, course_idnumber, group.name, group.idnumber, "teacher" )

    def new_student(self, student):
        try:
            auth = student.login_method
        except AttributeError:
            self.logger.warning("new_student called on {}, but no login_method provided, not adding".format(student))
            return
        self.logger.info('Creating {} account for {}'.format(auth, student))
        self.create_account( student.username, student.email, student.first, student.last, student.num, auth=auth )

        # TODO: If above didn't work, this won't do anything useful
        for cohort in student.cohorts:
            self.default_logger("Adding {} to cohort {}".format(student.num, cohort))
            self.add_user_to_cohort( student.num, cohort )
        for cohort in student.cohorts:
            self.add_user_to_cohort(student.ID, cohort)
        for course, group in student.get_enrollments():
            self.enrol_student_into_course(student.ID, course, group)
        inform.inform_new_student(student)

    def delete_user(self, user):
        self.delete_account(user.idnumber)

    def new_teacher(self, teacher):
        self.logger.info('Creating account for {}'.format(teacher))
        self.create_account( teacher.username, teacher.email, teacher.first, teacher.last, teacher.num, auth='manual' )
        for cohort in teacher.cohorts:
            self.add_user_to_cohort(teacher.ID, cohort)
        for course, group in teacher.get_enrollments():
            self.enrol_teacher_into_course(teacher.ID, course, group)

    def new_parent(self, parent):
        self.logger.info('Creating account for {}'.format(parent))
        # parents' email is their username
        self.create_account( parent.username, parent.email, "Parent", parent.email, parent.idnumber, auth='manual' )
        for cohort in parent.cohorts:
            self.add_user_to_cohort(parent.ID, cohort)
        for course, group in parent.get_enrollments():
            self.enrol_parent_into_course(parent.ID, course, group)
        inform.inform_new_parent(parent)

    def add_cohort(self, name):
        pass

    # def new_group(self, group):
    #     self.logger.info('Creating account for {}'.format(parent))

    def no_email(self, student):
        sf = NS(student)
        sf.new_student_cmd = self.new_email_cmd

        self.shell( sf("/bin/bash {new_student_cmd} {num} {username} '{lastfirst}'") )

    def enroll_in_groups(self, student):
        get_groups = self.sql('select id, name from ssismdl_groups')()
        self._groups = {}
        for item in get_groups:
            groupid, groupname = item
        self._groups[groupid] = groupname

    def new_support_staff(self, staff):
        """
        Support staff have fairly simple accounts
        IStaff: username
              first_name
              last_name
              email
              num
        """
        self.create_account( staff.username, staff.email, staff.first_name, staff.last_name, staff.num )

        self.add_user_to_cohort( staff.num, 'adminALL' )






class FakeStudent:

    def __init__(self):
        self.username = "success"
        self.fullname = "Mr Success"
        self.idnum = 555555555


if __name__ == "__main__":
    s = FakeStudent()
    m = DragonNetModifier()
    m.no_email(s)
