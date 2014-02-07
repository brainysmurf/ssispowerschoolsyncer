from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.models.datastores.abstract import AbstractTree

class MoodleTree(AbstractTree):
    klass = MoodleImport

    def process_schedules(self):
        for schedule in self.schedule_info.content():
            # Schedule is a special case, where we want to bring in things from all over
            # TODO: Figure out a way to handle this in the model
                # special case for Moodle
            student_idnumber, course_idnumber, group_name = schedule
            teacher_username = re.sub('[^a-z]*', '', group_name)
            teacher = self.teachers.get_from_attribute('username', teacher_username)

            if self.convert_course:
                course = self.courses.get_with_conversion(course_idnumber)
            else:
                course = self.courses.get_without_conversion(course_idnumber)

            student = self.students.get_key(student_idnumber)
            if not teacher or not course:
                log.warning("Could not get group: {} {}".format(teacher, course))
            else:
                group = self.groups.get_key(teacher.username + course.idnumber)

            self.schedules.make(student, teacher, course)

    def process_groups(self):
        for info in self.group_info.content():
            group_name = info
            if not group_name:
                continue
            teacher_username = re.sub(r'[^a-z]', '', group_name)
            course_idnumber = re.sub(r'[a-z]', '', group_name)
            teacher = self.teachers.get_from_attribute('username', teacher_username)
            course = self.courses.get_key(course_idnumber)
            if not teacher or not course:
                continue

            idnumber = teacher.username + course.idnumber
            self.groups.make(idnumber, teacher, course)

    def __sub__(self, other):
        """

        """
        left = self.tree.students.keys()
        right = other.tree.students.keys()

        for student_id in right - left:
            ns = NS(status='new_student')
            ns.left = self.tree.students.get(student_id)
            ns.right = other.tree.students.get(student_id)
            ns.param = [ns.right]
            yield ns

        for student_id in left - right:
            ns = NS(status='old_student')
            ns.left = self.tree.students.get(student_id)
            ns.right = other.tree.students.get(student_id)
            ns.param = [ns.left]
            yield ns

        left = self.tree.teachers.keys()
        right = other.tree.teachers.keys()

        for teacher_id in right - left:
            ns = NS(status='new_teacher')
            ns.left = self.tree.teachers.get(teacher_id)
            ns.right = other.tree.teachers.get(teacher_id)
            ns.param = [ns.right]
            yield ns

        for teacher_id in left - right:
            ns = NS(status='old_teacher')
            ns.left = self.tree.teachers.get(teacher_id)
            ns.right = other.tree.teachers.get(teacher_id)
            ns.param = [ns.left]
            yield ns

        # Now look at the individual information.
        for student_id in self.tree.students.keys():
            left = self.tree.students.get(student_id)
            right = other.tree.students.get(student_id)
            if left and right:
                yield from left - right
