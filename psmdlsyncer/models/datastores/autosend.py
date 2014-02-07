from psmdlsyncer.models.datastores.abstract import AbstractTree
from psmdlsyncer.files import AutoSendImport

class AutoSendTree(AbstractTree):
    klass = AutoSendImport

    def process_groups(self):
        # For autosend, we have to derive the groups from the same place as the schedule
        for info in self.schedule_info.content():
            course_number, course_name, periods, teacher_lastfirst, teacherID, teacher_email, student, studentID = info
            teacher = self.teachers.get_key(teacherID)
            if self.convert_course:
                course = self.courses.get_with_conversion(course_number)
            else:
                course = self.courses.get_without_conversion(course_number)
            self.groups.make(teacher, course)

    def process_schedules(self):
        for info in self.schedule_info.content():
            # Schedule is a special case, where we want to bring in things from all over
            # TODO: Figure out a way to handle this in the model
            course_number, course_name, periods, teacher_lastfirst, teacherID, teacher_email, student, studentID = info
            teacher = self.teachers.get_key(teacherID)

            if self.convert_course:
                course = self.courses.get_with_conversion(course_number)
            else:
                course = self.courses.get_without_conversion(course_number)

            student = self.students.get_key(studentID)
            group = self.groups.get_key(teacher.username + course.idnumber)

            self.schedules.make(student, teacher, course)


