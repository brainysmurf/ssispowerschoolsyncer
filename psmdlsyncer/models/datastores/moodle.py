from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.models.datastores.tree import AbstractTree
from psmdlsyncer.models.datastores.branch import DataStore
from psmdlsyncer.sql import MoodleDBSession
from psmdlsyncer.models.parent import MoodleParent

from psmdlsyncer.utils import NS2
from psmdlsyncer.settings import config_get_section_attribute

class MoodleDataStore(DataStore):
    pass

class parents(MoodleDataStore):
    """
    Use MoodleParent instead of Parent
    """
    klass = MoodleParent

    @classmethod
    def make_parent(cls, idnumber, *args, **kwargs):
        parent = cls.make(idnumber, *args, **kwargs)
        return parent

class MoodleTree(AbstractTree):
    klass = MoodleImport
    pickup = [DataStore, MoodleDataStore]
    convert_course = False

    def __init__(self):
        super().__init__()
        self.timetable_table = self.klass('dist', 'timetable_table')
        self.district_course_meta = self.klass('dist', 'course_metadata')
        self.district_online_portfolios = self.klass('dist', 'online_portfolios')

    def process_parents(self):
        """
        Go through the students and make parents based on that data
        """
        for idnumber, parent_id, _, _, _, _, _, _, _, _, username in self.parent_info.content():
            self.parents.make_parent(idnumber, parent_id, username=username)

    def process_online_portfolios(self):
        for key in self.district_online_portfolios.content():
            self.online_portfolios.make(key)

    def process_parent_links(self):
        """
        Here the main thing is creating the parent/child links and putting the child in the model
        """
        for parent_idnumber, child_idnumber in self.parent_student_links.content():
            parent = self.parents.get_key(parent_idnumber)
            child = self.students.get_key(child_idnumber)
            if parent and child:
                parent.add_child(child)
                self.parent_links.make_parent_link(parent_idnumber, child_idnumber)

    # def process_timetable_data(self):
    #     """
    #     This is different, we just go through each item and add it to the database
    #     """
    #     debug = config_get_section_attribute('DEBUGGING', 'inspect_timetable_data')
    #     for raw_data in self.timetable_table.get_timetable_data():
    #         _id, course_idnumber, teacher_idnumber, student_idnumber, group_idnumber, period_info, comment, active = raw_data
    #         course = self.courses.get_key(course_idnumber)
    #         teacher = self.teachers.get_key(teacher_idnumber)
    #         student = self.students.get_key(student_idnumber)
    #         # ensure that we have the group...
    #         group = NS2()
    #         group.idnumber = group_idnumber

    #         if course and teacher and student:
    #             result = self.timetable_datas.make_timetable_datas(course, teacher, group, student, period_info)
    #             debug and self.warning(result)
    #         else:
    #             debug and self.logger.warning("Not added")
    #             debug and self.logger.warning(course)
    #             debug and self.logger.warning(teacher)
    #             debug and self.logger.warning(student)
    #             debug and self.logger.warning(raw_data)
    #             debug and self.logger.warning('-----')
    #     if debug:
    #         from IPython import embed
    #         print(self)
    #         embed()

    def process_schedules(self):
        """
        Schedule should just have the keys for student and teachers
        """

        # We have to do the following ugliness in order to override the behavior of parents
        # Actually, it's not that ugly, but...

        for school in ['elementary', 'secondary']:
            self.default_logger('{} processing {} schedule'.format(self.__class__.__name__, school))
            # calls both secondary_schedule.content, elementary_schedule.content
            method = getattr(self, "{}_schedule".format(school))
            for schedule in method.content():
                self.default_logger('Processing {} schedule: {}'.format(school, schedule))
                course_key, period_info, section_number, teacher_key, student_key, groupId, groupName = schedule

                # We should check if we're dealing with a parent account or not
                # because we have to manually put in enrollments
                # TODO: Refactor to reduce repetitions
                if student_key.endswith('P'):
                    # okay, so here we are guaranteed
                    # that the parent should have already been created, because
                    # we sort the query DESC, so T then S then P

                    parent_key = student_key
                    parent = self.parents.get_key(parent_key)
                    if not parent:
                        self.logger.warning("Parent {} could not be found, probably because the student doesn't exist. What's with that?".format(student_key))
                        continue

                    course = self.courses.get(course_key, self.convert_course)
                    if not course:
                        # this may be an old-style group
                        if course_key.endswith('11'):
                            course_key = course_key + '12'
                        elif course_key.endswith('12'):
                            course_key = course_key[:-2] + '1112'
                        course = self.courses.get(course_key, self.convert_course)
                        if not course:
                            self.logger.warning("Course not found! {}".format(course_key))
                            continue

                    teacher = self.teachers.get_key(teacher_key)
                    if not teacher:
                        # see if the teacher_key is actually a username we can deal with
                        teacher = self.teachers.get_from_attribute('username', teacher_key)
                        if not teacher:
                            teacher = NS2()
                            teacher.username = teacher_key

                    group = self.groups.make_group_from_id(groupId, groupName)

                    # Now put in enrollments manually
                    enrollment = {course.ID: [group.ID]}
                    parent.add_enrollment(enrollment)

                else:
                    course = self.courses.get(course_key, self.convert_course)
                    teacher = self.teachers.get_key(teacher_key)
                    if not teacher:
                        self.logger.warning("Teacher not found! {}".format(teacher_key))
                        continue
                    if not course:
                        self.logger.warning("Course not found! {}".format(course_key))
                        continue

                    group = self.groups.make_group_from_id(groupId, groupName)

                    student = self.students.get_key(student_key)
                    if not student:
                        if self.teachers.get_key(student_key):
                            # case where teacher is enrolled into the group
                            # TODO: Figure out what to do about that
                            continue

                    # THIS IS DONE IN process_parents
                    # parent = self.parents.make_parent(student)

                    # parent.add_child(student)
                    # student.add_parent(parent)

                    # Do some sanity checks
                    if not course:
                        self.logger.warning("Course in schedule, but not found! {}".format(course_key))
                        continue
                    if not student:
                        #self.logger.warning("Student in schedule, but not found! {}".format(student_key))
                        continue
                    if not group:
                        self.logger.warning("Group not found! {}".format(section_number))
                        continue

                    self.associate(course, teacher, group, student)

                    # timetable = self.timetables.make_timetable(
                    #     course, teacher, group, student, section_number, period_info
                    #     )
                    # student.add_timetable(timetable)
                    # teacher.add_timetable(timetable)

                    #self.timetable_datas.make_timetable_datas(course, teacher, group, student, section_number, period_info)

    def process_mrbs_editors(self):
        for teacher in self.mrbs_editor_info.content():
            self.mrbs_editors.make(teacher.idnumber, teacher.id)

    def process_courses(self):
        debug = config_get_section_attribute('DEBUGGING', 'print_courses')
        for course in self.district_courses.content():
            new = self.courses.make_without_conversion(
                course.idnumber, course.fullname, course.grade, course.database_id
                )
            debug and self.logger.warning(new)
        for cmd in self.district_course_meta.content():
            new = self.course_metadatas.make_course_metadata(cmd.course_idnumber, cmd.course_grade)
            debug and self.logger.warning(new)
        if debug:
            from IPython import embed
            embed()

    def process_cohorts(self):
        cache = {}

        for cohort_info in self.cohort_info.content():
            idnumber, cohort_name = cohort_info
            if idnumber in cache:
                person = cache[idnumber]
            else:
                person = self.get_person(idnumber)
                if not person:
                    self.default_logger("invalid idnumber '{}' found when processing moodle cohorts".format(idnumber))
                    continue
                person._cohorts = []
                cache[idnumber] = person

            person.add_cohort(cohort_name)

        super().process_cohorts()

    def process_custom_profile_fields(self):
        # Indicate to the model we are are manually controlling the fields
        # By setting them all to None
        # Subsequent calls to .get_custom_field_keys won't return them again
        for person in self.get_everyone():
            for field in person.get_custom_field_keys():
                setattr(person, field, None)

        # Now look in Moodle's database for the values, and set them
        self.default_logger("Moodle processing profile fields")

        for profile_info in self.custom_profile_fields_info.content():
            self.default_logger("Processing custom profile: {}".format(profile_info))
            idnumber, username, shortname, data = profile_info
            if not idnumber and not data and shortname:
                # not user info, just the name itself, add it
                self.custom_profile_fields.make(shortname)
            person = self.get_person(idnumber)
            if not person:
                self.default_logger('Could not find person while processing {} moodle custom profile'.format(profile_info))
                continue
            person.set_custom_field(shortname, data)

        # Now go through and actually make the items in the branch
        super().process_custom_profile_fields()

if __name__ == "__main__":

    mstu33 = MoodleTree.students.make('33', '', '', '', '', '', '', '', '', '')
    mstu3333 = MoodleTree.students.make('3333', '', '', '', '', '', '', '', '', '')
    #au33 = AutoSendTree.students.make('33', '', '', '', '', '', '', '', '', '')
    mteach33 = MoodleTree.teachers.make('33', "Morris, Adam", '', '', '', '')
    mstu33_ = MoodleTree.students.make('33', '', '', '', '', '', '', '', '', '')
    mteach555 = MoodleTree.teachers.make('555', "Morris, Adam", '', '', '', '')
    mteach333 = MoodleTree.teachers.make('333', "Morris, Adam", '', '', '', '')
    assert(mstu33 != mstu3333)
    assert(mstu33 != mteach33)
    assert(mstu33_ == mstu33)
    #assert(mstu33 != au33)

    from IPython import embed
    embed()
