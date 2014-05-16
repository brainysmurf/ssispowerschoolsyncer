from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.models.datastores.tree import AbstractTree
from psmdlsyncer.models.datastores.branch import DataStore
from psmdlsyncer.sql import MoodleDBSession
from psmdlsyncer.models.parent import MoodleParent

from psmdlsyncer.utils import NS2

class MoodleDataStore(DataStore):
    pass

class parents(MoodleDataStore):
    klass = MoodleParent

    @classmethod
    def make_parent(cls, student):
        idnumber = student.family_id
        return cls.make(idnumber)

class MoodleTree(AbstractTree):
    klass = MoodleImport
    pickup = [DataStore, MoodleDataStore]
    convert_course = False

    def process_students(self):
        """
        For Moodle since new students are added to the studentsALL cohort,
        we have to go over it twice in order for them to appear.
        """
        super().process_students()
        for student in self.student_info.content():
            self.students.make(*student)

    def process_teachers(self):
        """
        For Moodle since new students are added to the teachersALL or supportstaffALL cohort,
        we have to go over it twice in order for them to appear.
        """
        super().process_teachers()
        for teacher in self.teacher_info.content():
            self.teachers.make(*teacher)

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
                course_key, period_info, section_number, teacher_key, student_key = schedule

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

                    if section_number:
                        group = self.groups.make("{}{}-{}".format(teacher.username, course.ID, section_number))
                    else:
                        #self.logger.warning("No section number for group {}!".format(group))
                        #continue
                        group = self.groups.make("{}{}".format(teacher.username, course.ID))

                    # Now put in enrollments manually
                    enrollment = {course.ID: [group.ID]}
                    parent.add_enrollment(enrollment)

                else:
                    course = self.courses.get(course_key, self.convert_course)
                    teacher = self.teachers.get_key(teacher_key)
                    if not teacher:
                        self.logger.warning("Teacher not found! {}".format(teacher_key))
                        continue
                    if section_number:
                        group = self.groups.make("{}{}-{}".format(teacher.username, course.ID, section_number))
                    else:
                        self.logger.warning("No section number for group {}!".format(group))
                        continue
                        group = self.groups.make("{}{}".format(teacher.username, course.ID))

                    student = self.students.get_key(student_key)
                    if not student:
                        if self.teachers.get_key(student_key):
                            # case where teacher is enrolled into the group
                            # TODO: Figure out what to do about that
                            continue
                    parent = self.parents.make_parent(student)

                    parent.add_child(student)
                    student.add_parent(parent)

                    # Do some sanity checks
                    if not course:
                        self.logger.warning("Course not found! {}".format(course_key))
                        continue
                    if not student:
                        self.logger.warning("Student not found! {}".format(student_key))
                        continue
                    if not group:
                        self.logger.warning("Group not found! {}".format(section_number))
                        continue

                    self.associate(course, teacher, group, student)

                    timetable = self.timetables.make_timetable(
                        course, teacher, group, student, section_number, period_info
                        )
                    student.add_timetable(timetable)
                    teacher.add_timetable(timetable)

    def process_mrbs_editor(self):
        dnet = MoodleDBSession()
        for teacher_id in dnet.mrbs_editors():
            self.mrbs_editor.make(teacher_id)

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
            person.add_cohort(cohort_name)

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
