from psmdlsyncer.sql.MoodleDatabase import MoodleDBConnection
from collections import namedtuple

class MoodleImport(MoodleDBConnection):
    def __init__(self, school, unique):
        self.school = school
        self.unique = unique
        super().__init__()

    def content_dist_staffinfo(self):
        staff_ids = set([row[0] for row in
                         self.those_enrolled_in_one_of_these_cohorts(
                             'teachersALL', 'supportALL'
                             )
                         if row[0]])
        for staff_id in staff_ids:
            staff_info = self.get_unique_row('user', 'idnumber', 'firstname', 'lastname', 'email',
                                             idnumber=staff_id)
            lastfirst = staff_info.lastname + ', ' + staff_info.firstname
            yield [staff_id, lastfirst, staff_info.email, '', '', '']

    def content_sec_courseinfo(self):
        """ RETURN ALL THE STUFF IN TEACHING & LEARNING TAB """
        yield from self.get_teaching_learning_courses(select_list=['shortname', 'fullname'])
    def content_sec_studentschedule(self):
        user_enrollments = self.get_all_users_enrollments()
        usernames = {}
        for row in self.get_table('user', 'idnumber', 'username'):
            usernames[username] = idnumber
        
        student_ids = [row[0] for row in self.those_enrolled_in_cohort('studentsSEC')]
        only_lowercase = re.compile(r'[^a-z]')

        results = set()
        for student_id in student_ids:
            for filtered in [row for row in user_enrollments if row[0] == student_id]:
                _, group, course = filtered
                teacherID = usernames.get(only_lowercase.sub('', group))
                if not teacherID:
                    print('uuuuh oh')
                    input(filtered)
                results.add(course_number, "", "", "", teacher_id, "", student_id)
        return results

    def content_dist_studentinfo(self):
        """
        MOODLE DOESN'T HAVE CONCEPT OF SITE-WIDE ROLES,
        BUT IT DOES HAVE SITE-WIDE COHORTS, SO LET'S USE THAT
        """
        student_ids = [row[0] for row in self.those_enrolled_in_cohort('studentsALL')]
        for student_id in student_ids:
            homeroom = self.get_table('user', 'department', idnumber=student_id)[0][0]
            yield [student_id, '', '', homeroom, "", "", "", "", ""]

    def content(self):
        dispatch_to = getattr(self, 'content_{}_{}'.format(self.school, self.unique))
        if dispatch_to:
            yield from dispatch_to()
