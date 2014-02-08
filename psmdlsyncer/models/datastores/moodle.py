from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.models.datastores.abstract import AbstractTree
import re
import logging
log = logging.getLogger(__name__)

class MoodleAbstractTree(AbstractTree):
    klass = MoodleImport
    convert_course = False

    def process_schedules(self):
        for schedule in self.schedule_info.content():
            # Schedule is a special case, where we want to bring in things from all over
            # TODO: Figure out a way to handle this in the model
                # special case for Moodle
            student_idnumber, course_idnumber, group_name = schedule

            # With Moodle we only use the group name to derive everything
            teacher_username = re.sub('[^a-z]*', '', group_name)
            teacher = self.teachers.get_from_attribute('username', teacher_username)

            if self.convert_course:
                course = self.courses.get_with_conversion(course_idnumber)
            else:
                course = self.courses.get_without_conversion(course_idnumber)

            student = self.students.get_key(student_idnumber)
            if not teacher:
                log.warning("Teacher must have left, but his/her group remains: {}".format(group_name, teacher, course))
                continue
            if not course:
                log.warning("Course found in schedule but does not exist in Moodle {}.".format(course_idnumber))
                continue
            group = self.groups.get_key(teacher.username + course.idnumber)
            if not group:
                log.warning("Schedule has this group but doesn't exist in Moodle {}".format(group_name))
                continue

            # Okay, all clear, let's register it in the schedule
            self.schedules.make(student, teacher, course)

    def process_groups(self):
        for group_name in self.group_info.content():
            if not group_name:
                continue
            teacher_username = re.sub(r'[^a-z]', '', group_name)
            course_idnumber = re.sub(r'[a-z]', '', group_name)
            teacher = self.teachers.get_from_attribute('username', teacher_username)
            if self.convert_course:
                course = self.courses.get_with_conversion(course_idnumber)
            else:
                course = self.courses.get_without_conversion(course_idnumber)
            if not teacher or not course:
                continue

            self.groups.make(teacher, course)

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
