from psmdlsyncer.sql.MoodleDatabase import MoodleDBConnection
from collections import defaultdict
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
        yield from self.get_dragonnet_enrollments()

    def content(self):
        dispatch_to = getattr(self, 'content_{}_{}'.format(self.school, self.unique))
        if dispatch_to:
            yield from dispatch_to()

    def get_dragonnet_enrollments(self):
        results = defaultdict(lambda : defaultdict(list))

        for row in self.call_sql("""
select
    crs.idnumber courseID, usr.idnumber as userID, usr.username as username, r.name as rolename, grps.name as groupName
FROM ssismdl_course crs
JOIN ssismdl_course_categories cat ON cat.id = crs.category
JOIN ssismdl_context ct ON crs.id = ct.instanceid
JOIN ssismdl_role_assignments ra ON ra.contextid = ct.id
JOIN ssismdl_user usr ON usr.id = ra.userid
JOIN ssismdl_role r ON r.id = ra.roleid
JOIN ssismdl_groups_members mmbrs ON mmbrs.userid = usr.id
JOIN ssismdl_groups grps ON grps.id = mmbrs.groupid
where
    not crs.idnumber like '' and
    not usr.idnumber like '' and
    cat.path like '/{}/%'
order by
    r.name DESC
""".format(50)):
            courseID, userID, username, roleName, groupname = row
            # Do different things based on the role
            # For teachers, we have to see if they are the owner of the group
            if roleName == "Teacher":
                # we have to derive the group name
                groupname = username + courseID
                results[groupname]['course'] = courseID
                results[groupname]['teachers'].append(userID)

            elif roleName == "Student":
                if userID.endswith('P'):
                    # Ensure there are no parents mistakenly being put
                    # TODO: Unenrol them?
                    continue

                if not groupname:
                    #TODO: Turn this into a warning
                    print("No groupname, what to do?")
                    continue

                results[groupname]['students'].append(userID)

            elif roleName == "Parent":
                pass

        # TODO: Section
        _period = ''
        _section = ''
        for group in results.keys():
            for student in results[group]['students']:
                for teacher in results[group]['teachers']:
                    yield results[group]['course'], _period, _section, teacher, student

