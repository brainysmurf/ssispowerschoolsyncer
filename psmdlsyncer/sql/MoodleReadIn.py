from psmdlsyncer.sql import MoodleDBSession
from collections import defaultdict
import re
import time

class MoodleImport(MoodleDBSession):
    """
    Class used to import information about students
    """
    def __init__(self, school, unique):
        self.school = school
        self.unique = unique
        super().__init__()

    def content_dist_staffinfo(self):
        for staff in self.users_enrolled_in_these_cohorts(['teachersALL', 'supportALL']):
            schoolid = self.wrap_no_result(self.get_user_schoolid, staff)
            if schoolid is None:
                schoolid = ''
            lastfirst = staff.lastname + ', ' + staff.firstname
            yield [staff.idnumber, staff.id, lastfirst, staff.email, '', schoolid, '', '']

    def content_sec_courseinfo(self):
        """ RETURN ALL THE STUFF IN TEACHING & LEARNING TAB """
        yield from self.get_teaching_learning_courses()

    def content_elem_courseinfo(self):
        """
        Not needed, because we have the above
        """
        return ()

    def content_dist_studentinfo(self):
        for student in self.users_enrolled_in_this_cohort('studentsALL'):
            # note, student.username on the end is an optional parameter
            # TODO: Add bus info here too!
            yield [student.idnumber, student.id, None, student.department, "", "", "", "", "", "", student.username]

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
        yield from self.get_custom_profile_records()

    def content_dist_cohorts(self):
        yield from self.get_cohorts()

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
        for row in self.bell_schedule():
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
                    section = ''
                    #self.logger.warning("Found when processing parent, moodle group {} does not have a section number attached, so much be illigitmate".format(groupname))
                    # TODO: we should indicate the enrollment by yielding what we can
                    #continue

                teachers = results[groupname]['teachers']
                course = results[groupname]['course']
                if not teachers:
                    if groupname[-2] == '-':
                        groupname = groupname[:-2]
                    # first do a heuristic to see if we can't get the teacher username from the group name
                    derived_teacher = re.sub('[^a-z]', '', groupname)
                    if derived_teacher:
                        teachers = [derived_teacher]
                    else:
                        self.logger.warning("Group with no teacher info: {}!".format(groupname))
                if not course:
                    if groupname[-2] == '-':
                        groupname = groupname[:-2]
                    derived_course = re.sub('[a-z]', '', groupname)
                    if derived_course:
                        course = derived_course
                    else:
                        self.logger.warning("No course for group {}".format(groupname))
                for teacher in teachers:
                    yield course, _period, section, teacher, userID

            else:
                # non-editing teachers...
                pass

        for group in results.keys():
            if '-' in group:
                section = group.split('-')[1]
            else:
                section = ''
                # self.logger.warning("Moodle group {} does not have a section number attached, so much be illigitmate".format(group))
                # continue
            teachers = results[group]['teachers']
            course = results[group]['course']
            if not course or not teachers:
                self.logger.warning("Group with no teacher info: {}!".format(group))
                continue

            for student in results[group]['students']:
                for teacher in teachers:
                    yield course, _period, section, teacher, student

if __name__ == "__main__":

    m = MoodleImport('', '')
    for student in m.users_enrolled_in_these_cohorts(['teachersALL', 'supportALL']):
        print(student)
