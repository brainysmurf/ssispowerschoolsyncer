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

    def content_dist_online_portfolios(self):
        for item in self.get_online_portfolios():
            yield item

    def content_dist_staffinfo(self):
        for staff in self.users_enrolled_in_these_cohorts(['teachersALL', 'supportstaffALL']):
            schoolid = self.wrap_no_result(self.get_user_schoolid, staff)
            if schoolid is None:
                schoolid = ''
            lastfirst = staff.lastname + ', ' + staff.firstname
            yield [staff.idnumber, staff.id, lastfirst, staff.email, '', schoolid, '', '']

    def content_dist_course_metadata(self):
        for item in self.get_course_metadata():
            yield item

    def content_dist_courseinfo(self):
        """ RETURN ALL THE STUFF IN TEACHING & LEARNING TAB """
        for item in self.get_teaching_learning_courses():
            yield item

    def content_elem_courseinfo(self):
        """
        Not needed, because we have the above
        """
        return ()

    def content_dist_parentstudentlinks(self):
        """

        """
        for item in self.get_parent_student_links():
            yield item

    def content_dist_studentinfo(self):
        for student in self.users_enrolled_in_this_cohort('studentsALL'):
            # note, student.username on the end is an optional parameter
            # TODO: Add bus info here too!
            lastfirst = "{}, {}".format(student.lastname, student.firstname)
            yield [student.idnumber, student.id, None, student.department, lastfirst, "", "", "", "", "", student.username]

    def content_dist_parentinfo(self):
        for parent in self.users_enrolled_in_this_cohort('parentsALL'):
            yield [parent.idnumber, parent.id, None, "", "", "", "", "", "", "", parent.username]

    def content_sec_studentschedule(self):
        for item in self.get_bell_schedule():
            yield item

    def content_dist_timetable_table(self):
        for item in self.get_timetable_table():
            yield item

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
        for field in self.get_custom_profile_fields():
            yield None, None, field.shortname, None
        for item in self.get_custom_profile_records():
            yield item

    def content_dist_cohorts(self):
        for item in self.get_cohorts():
            yield item

    def content_dist_mrbs_editors(self):
        for item in self.get_mrbs_editors():
            yield item

    def content(self):
        dispatch_to = getattr(self, 'content_{}_{}'.format(self.school, self.unique))
        if dispatch_to:
            for item in dispatch_to():
                yield item

    def get_bell_schedule(self):
        """
        Makes a generator that outputs basically outputs SSIS' bell schedule
        First does an SQL statement to get the raw data, and then processes it in python
        to get the expected output.
        (Getting it done in pure sql with nested selects was just a bit too tedius)
        """
        results = defaultdict(lambda : defaultdict(list))
        for row in self.bell_schedule():
            _period = ''
            courseID, userID, username, roleName, groupId, groupName = row

            if not groupId:
                continue

            # Do different things based on the role
            # For teachers, we have to see if they are the owner of the group

            if roleName == "editingteacher":
                # TODO: Can be deleted, right?
                # if not groupId:
                #     groupId = username + courseID
                results[groupId]['course'] = courseID

                # Most probably, there will only be one teacher in this group
                # But hard-coding it as one object seems wrong, so use a list
                # FIXME: If teachers were to be manaully put into a group
                #        that isn't their own group, we have some trouble
                #        There isn't any reason for them to do that
                #        But we should probably close that off
                #        (Maybe look at the username before adding here?)
                results[groupId]['teachers'].append(userID)

            elif roleName == "manager":
                # what do we do in this case?
                continue

            elif roleName == "student":
                if userID.endswith('P'):
                    # Ensure there are no parents mistakenly being put
                    # TODO: Unenrol them?
                    continue

                if not groupId:
                    #TODO: Figure out why the SQL query returns so many blank groups
                    continue

                if not userID in results[groupId]['students']:
                    results[groupId]['students'].append(userID)

            elif roleName == "parent":
                # The below will work okay because we sorted the query by name
                # and Teacher comes before Parent
                # a bit of a workaround, but it should work okay
                if not groupId:
                    #TODO: Figure out why the SQL query returns so many blank groups
                    continue

                if '-' in groupId:
                    section = groupId.split('-')[1]
                else:
                    section = ''
                    #self.logger.warning("Found when processing parent, moodle group {} does not have a section number attached, so much be illigitmate".format(groupId))
                    # TODO: we should indicate the enrollment by yielding what we can
                    #continue

                teachers = results[groupId]['teachers']
                course = results[groupId]['course']
                if not teachers:
                    if groupId[-2] == '-':
                        groupId = groupId[:-2]
                    # first do a heuristic to see if we can't get the teacher username from the group name
                    derived_teacher = re.sub('[^a-z]', '', groupId)
                    if derived_teacher:
                        teachers = [derived_teacher]
                    else:
                        self.logger.warning("Group with no teacher info: {}!".format(groupId))
                if not course:
                    if groupId[-2] == '-':
                        groupId = groupId[:-2]
                    derived_course = re.sub('[a-z]', '', groupId)
                    if derived_course:
                        course = derived_course
                    else:
                        self.logger.warning("No course for group {}".format(groupId))
                for teacher in teachers:
                    yield course, _period, section, teacher, userID, groupId, groupName

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
            if course and not teachers:
                self.logger.warning("Group with no teacher info: {}!".format(group))
                continue
            elif not course:
                self.logger.warning("Empty course {} that has a group?: {}!".format(str(course), group))
                continue

            for student in results[group]['students']:
                for teacher in teachers:  # note: there will only be one teacher...
                    yield course, _period, section, teacher, student, group, ''

if __name__ == "__main__":

    m = MoodleImport('', '')
    for info in m.get_bell_schedule():
        pass
