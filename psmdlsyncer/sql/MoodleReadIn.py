from psmdlsyncer.sql.MoodleDatabase import MoodleDBConnection
from collections import namedtuple
import re
import time

class MoodleImport(MoodleDBConnection):
    """
    Class used to import information about students
    """
    def __init__(self, school, unique):
        self.school = school
        self.unique = unique
        super().__init__()

    def content_dist_staffinfo(self):
        staff_ids = set([row.idnumber for row in
                         self.those_enrolled_in_one_of_these_cohorts(
                             'teachersALL', 'supportALL'
                             )
                         if row.idnumber])
        for staff_id in staff_ids:
            staff_info = self.get_unique_row('user', 'idnumber', 'firstname', 'lastname', 'email',
                                             idnumber=staff_id)
            if not staff_info:
                continue
            lastfirst = staff_info.lastname + ', ' + staff_info.firstname
            yield [staff_id, lastfirst, staff_info.email, '', '', '']

    def content_sec_courseinfo(self):
        """ RETURN ALL THE STUFF IN TEACHING & LEARNING TAB """
        for row in self.get_teaching_learning_courses(select_list=['shortname', 'fullname']):
            yield row.shortname, row.fullname

    def content_dist_studentinfo(self):
        """
        MOODLE DOESN'T HAVE CONCEPT OF SITE-WIDE ROLES,
        BUT IT DOES HAVE SITE-WIDE COHORTS, SO LET'S USE THAT
        """
        students = [ (row.idnumber, row.username, row.homeroom) for row in self.those_enrolled_in_cohort('studentsALL')]
        for student_id, student_username, student_homeroom in students:
            # pass grade as None tells the model to use the homeroom
            yield [student_id, '', None, student_homeroom, "", "", "", "", "",
                   student_username]

    def content_sec_studentschedule(self):
        enrollments = self.get_all_users_enrollments()
        for enrollment in enrollments:
            #do we really need the teacher id here?, yes that's how the group name is derived!!
            periods = ''
            section = ''
            teacher_name = ''
            teacher_id = ''
            student_name = ''
            yield [enrollment.crs_idnumber, periods, section, teacher_name, teacher_id, student_name, enrollment.usr_idnumber, enrollment.grp_name]

    def content(self):
        dispatch_to = getattr(self, 'content_{}_{}'.format(self.school, self.unique))
        if dispatch_to:
            yield from dispatch_to()
