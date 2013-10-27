from psmdlsyncer.sql.MoodleDatabase import MoodleDBConnection
from collections import namedtuple
import re

class MoodleImport(MoodleDBConnection):
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
            lastfirst = staff_info.lastname + ', ' + staff_info.firstname
            yield [staff_id, lastfirst, staff_info.email, '', '', '']

    def content_sec_courseinfo(self):
        """ RETURN ALL THE STUFF IN TEACHING & LEARNING TAB """
        for row in self.get_teaching_learning_courses(select_list=['shortname', 'fullname']):
            yield row.shortname, row.fullname
            
    def content_sec_studentschedule(self):
        users_enrollments = list(self.get_all_users_enrollments())
        usernames = {}
        for row in self.get_table('user', 'idnumber', 'username', deleted=0):
            idnumber = row[0]
            username = row[1]
            usernames[username] = idnumber
        
        student_ids = [row.idnumber for row in self.those_enrolled_in_cohort('studentsSEC')]
        only_lowercase = re.compile(r'[^a-z]')

        results = set()
        for student_id in student_ids:
            for filtered in [row for row in users_enrollments if row.usr_idnumber == student_id]:
                username = only_lowercase.sub('', filtered.grp_name)
                teacher_id = usernames.get(username)
                if not teacher_id:
                    self.logger.info("no idnumber for {}, how am I supposed to know what's what?".format(username))
                    continue
                results.add( (filtered.crs_idnumber, "", "", "", teacher_id, "", student_id) )
        return results

    def content_dist_studentinfo(self):
        """
        MOODLE DOESN'T HAVE CONCEPT OF SITE-WIDE ROLES,
        BUT IT DOES HAVE SITE-WIDE COHORTS, SO LET'S USE THAT
        """
        student_ids = [row.idnumber for row in self.those_enrolled_in_cohort('studentsALL')]
        for student_id in student_ids:
            homeroom = self.get_table('user', 'department', idnumber=student_id)[0][0]
            yield [student_id, '', '', homeroom, "", "", "", "", ""]

    def content(self):
        dispatch_to = getattr(self, 'content_{}_{}'.format(self.school, self.unique))
        if dispatch_to:
            yield from dispatch_to()
