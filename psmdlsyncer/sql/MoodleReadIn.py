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
            yield [staff_id, lastfirst, staff_info.email, '', '', '', '']

    def content_sec_courseinfo(self):
        """ RETURN ALL THE STUFF IN TEACHING & LEARNING TAB """
        for row in self.get_teaching_learning_courses(select_list=['shortname', 'fullname']):
            yield row.shortname, row.fullname

    def content_elem_courseinfo(self):
        """
        Not needed, because we have the above
        """
        return ()

    def content_dist_studentinfo(self):
        """
        MOODLE DOESN'T HAVE CONCEPT OF SITE-WIDE ROLES,
        BUT IT DOES HAVE SITE-WIDE COHORTS, SO LET'S USE THAT
        """
        students = [ (row.idnumber, row.username, row.homeroom) for row in self.those_enrolled_in_cohort('studentsALL')]
        for student_id, student_username, student_homeroom in students:
            # pass grade as None tells the model to use the homeroom
            yield [student_id, '', None, student_homeroom, "", "", "", "", "", "",
                   student_username]

    def content_sec_studentschedule(self):
        yield from self.get_bell_schedule()

    def content_elem_studentschedule(self):
        """
        Not needed, because content_sec_studentschedule does the job
        """
        return ()

    def content_dist_customprofiles(self):
        """
        The model by default takes care of the custom_profile fields,
        but with Moodle we have to download from the database
        """
        yield from self.call_sql("""
SELECT
    u.idnumber, u.username, f.shortname, d.data from ssismdl_user_info_data d
JOIN
    ssismdl_user_info_field f ON f.id = d.fieldid
JOIN
    ssismdl_user u ON u.id = d.userid
""")

    def content(self):
        dispatch_to = getattr(self, 'content_{}_{}'.format(self.school, self.unique))
        if dispatch_to:
            yield from dispatch_to()

    def get_bell_schedule(self):
        """
        Makes a generator that outputs basically outputs SSIS' bell schedule
        First does an SQL statement to get the raw data, and then processes it in python
        to get the expected output.
        (Getting it done in pure sql with nested seelcts was just a bit too tedius)
        """
        results = defaultdict(lambda : defaultdict(list))
        for row in self.call_sql("""
select distinct
    crs.idnumber courseID, usr.idnumber as userID, usr.username as username, r.name as rolename, grps.name as groupName
FROM ssismdl_course crs
JOIN ssismdl_course_categories cat ON cat.id = crs.category
JOIN ssismdl_context ct ON crs.id = ct.instanceid
JOIN ssismdl_role_assignments ra ON ra.contextid = ct.id
JOIN ssismdl_user usr ON usr.id = ra.userid
LEFT JOIN ssismdl_role r ON r.id = ra.roleid
LEFT JOIN ssismdl_groups_members mmbrs ON mmbrs.userid = usr.id
LEFT JOIN ssismdl_groups grps ON grps.id = mmbrs.groupid and grps.courseid = crs.id
where
    not crs.idnumber like '' and
    not usr.idnumber like '' and
    cat.path like '/{}/%'
order by
    r.name DESC,
    usr.idnumber,
    grps.name
""".format(50)):
            _period = ''
            courseID, userID, username, roleName, groupname = row
            if not groupname:
                continue

            # Do different things based on the role
            # For teachers, we have to see if they are the owner of the group

            if roleName == "Teacher":
                # TODO: Can be deleted, right?
                # if not groupname:
                #     groupname = username + courseID
                results[groupname]['course'] = courseID

                # Most probably, there will only be one teacher in this group
                # But hard-coding it as one object seems wrong, so use a list
                # FIXME: If teachers were to be manaully put into a group
                #        that isn't their own group, we have some trouble
                #        There isn't any reason for them to do that
                #        But we should probably close that off
                #        (Maybe look at the username before adding here?)
                results[groupname]['teachers'].append(userID)

            elif roleName == "Manager":
                # what do we do in this case?
                continue

            elif roleName == "Student":
                if userID.endswith('P'):
                    # Ensure there are no parents mistakenly being put
                    # TODO: Unenrol them?
                    continue

                if not groupname:
                    #TODO: Figure out why the SQL query returns so many blank groups
                    continue

                if not userID in results[groupname]['students']:
                    results[groupname]['students'].append(userID)

            elif roleName == "Parent":
                # The below will work okay because we sorted the query by name
                # and Teacher comes before Parent
                # a bit of a workaround, but it should work okay
                if not groupname:
                    #TODO: Figure out why the SQL query returns so many blank groups
                    continue

                if '-' in groupname:
                    section = groupname.split('-')[1]
                else:
                    self.logger.warning("Found when processing parent, moodle group {} does not have a section number attached, so much be illigitmate".format(groupname))
                    # we should indicate the enrollment by yielding what we can
                    continue

                teachers = results[groupname]['teachers']
                course = results[groupname]['course']
                if not course or not teachers:
                    self.logger.warning("Group with no teacher info: {}!".format(groupname))
                    continue
                for teacher in teachers:
                    yield course, _period, section, teacher, userID

            else:
                # non-editing teachers...
                pass

        for group in results.keys():
            if '-' in group:
                section = group.split('-')[1]
            else:
                self.logger.warning("Moodle group {} does not have a section number attached, so much be illigitmate".format(group))
                continue
            teachers = results[group]['teachers']
            course = results[group]['course']
            if not course or not teachers:
                self.logger.warning("Group with no teacher info: {}!".format(group))
                continue

            for student in results[group]['students']:
                for teacher in teachers:
                    yield course, _period, section, teacher, student



