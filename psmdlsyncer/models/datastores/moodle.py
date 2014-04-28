from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.models.datastores.tree import AbstractTree
from psmdlsyncer.models.datastores.branch import DataStore

class MoodleTree(AbstractTree):
    klass = MoodleImport
    pickup = DataStore
    convert_course = False

    def process_schedules(self):
        """
        Schedule should just have the keys for student and teachers
        """
        for school in ['elementary', 'secondary']:
            self.default_logger('{} processing {} schedule'.format(self.__class__.__name__, school))
            # calls both secondary_schedule.content, elementary_schedule.content
            method = getattr(self, "{}_schedule".format(school))
            for schedule in method.content():
                self.default_logger('Processing {} schedule: {}'.format(school, schedule))
                course_key, period_info, section_number, teacher_key, student_key = schedule
                course = self.courses.get(course_key, self.convert_course)
                teacher = self.teachers.get_key(teacher_key)
                if not teacher:
                    self.logger.warning("Teacher not found! {}".format(teacher_key))
                    continue
                if section_number:
                    group = self.groups.make("{}{}-{}".format(teacher.username, course.ID, section_number))
                else:
                    group = self.groups.make("{}{}".format(teacher.username, course.ID))
                student = self.students.get_key(student_key)

                # Do some sanity checks
                if not course:
                    self.logger.warning("Course not found! {}".format(course_key))
                    continue
                if not student:
                    self.logger.warning("Student not found! {}".format(student_key))
                    continue
                if not group:
                    self.logger.warning("Group not found! {}".format(section_number))

                self.associate(course, teacher, group, student)

                timetable = self.timetables.make_timetable(
                    course, teacher, group, student, section_number, period_info
                    )
                student.add_timetable(timetable)
                teacher.add_timetable(timetable)

    def process_profile_fields(self):
        self.default_logger("Moodle processing profile fields")
        for profile_info in self.custom_profile_fields.content():
            idnumber, username, shortname, data = profile_info


