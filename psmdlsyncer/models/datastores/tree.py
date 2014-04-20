"""
USES FANCY META-PROGRAMMING IN ORDER TO ACCOMPLISH A RATHER SIMPLE THING, SO BEWARE
"""
import inspect, sys, copy
from collections import defaultdict
import re, logging
log = logging.getLogger(__name__)
from psmdlsyncer.models.datastores.branch import DataStore, students, teachers, groups, schedules, courses
from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.files import AutoSendImport
from psmdlsyncer.utils import NS2

class DataStoreCollection(type):
	_store = defaultdict(dict)
	qual_name_delimiter = "."
	qual_name_format = "{branch}{delim}{subbranch}"

	def __init__(cls, name, bases, attrs):
		if attrs.get('pickup'):
			datastore = attrs.get('pickup')
			# Cycle through all the classes that have been declared in this module, so we can augment this class with those ones
			# Limitation: You have to declare your branches in the same place as this module
			# TODO: Get around above limitation by passing a string and importing that way
			get_all_module_classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
			for class_name, class_reference in get_all_module_classes:
				nested_class_name = NS2.string(
					cls.qual_name_format,
					branch=cls.__name__,
					delim=cls.qual_name_delimiter,
					subbranch=class_reference.__name__
					)
				if class_name in attrs.keys():   # first check to see if the programmer declared something else by the same name
					declared_class = attrs[class_name]  # this is now whatever the programmer declared
					if inspect.isclass(declared_class) and issubclass(declared_class, datastore):
						# If we're here, we need to adjust some augment, to match what we would do automatically (like below)
						setattr(declared_class, '__qualname__', nested_class_name)
						setattr(declared_class, '__outerclass__', cls)
				elif class_reference is not datastore:  # check to ensure our heuristic doesn't detect itself
					if issubclass(class_reference, datastore): # now see if this object is subclass of class represented by `pickup`
						# okay, we need to manually pickup the class and bring it into ours
						# copy the class entirely (won't work otherwise)
						copied_class = type(name, class_reference.__bases__, dict(class_reference.__dict__))
						# set up magic
						copied_class.__qualname__ = nested_class_name
						copied_class.__outerclass__ = cls
						# and assign this brand new class to ours
						setattr(cls, class_reference.__name__, copied_class)
				else:
					pass # nothing to do here, programmer defined a method or object with the same name but not a subclass of class referenced by `pickup`

	@classmethod
	def keys(cls):
		return cls._store.keys()

	@classmethod
	def get_branch(cls, key):
		return key.split(cls.qual_name_delimiter)[-1]

	@classmethod
	def my_subbranch(cls, subbranch):
		return cls._store[cls.qual_name_format.format(
			branch=cls.__name__,
			delim=cls.qual_name_delimiter,
			subbranch=subbranch
			)]


class AbstractTree(metaclass=DataStoreCollection):
	convert_course = True   # by default, convert the course shortname

	def __init__(self):
		super().__init__()
		self.student_info = self.klass('dist', 'studentinfo')
		self.teacher_info = self.klass('dist', 'staffinfo')
		self.course_info = self.klass('sec', 'courseinfo')
		self.allocations_info = self.klass('sec', 'teacherallocations')
		self.group_info = self.klass('sec', 'groups')
		self.schedule_info = self.klass('sec', 'studentschedule')
		self.init()


	def process_students(self):
		for student in self.student_info.content():
			self.students.make(*student)

	def process_teachers(self):
		for teacher in self.teacher_info.content():
			self.teachers.make(*teacher)

	def process_courses(self):
		for course in self.course_info.content():
			if self.convert_course:
				self.courses.make_with_conversion(*course)
			else:
				self.courses.make_without_conversion(*course)

	def process_groups(self):
		for group in self.group_info.content():
			self.groups.make(*group)

	def process_schedules(self):
		# no good standard way to do this, quite yet
		for schedule in self.schedule_info.content():
			course_key, period_info, section, teacher_key, student_key = schedule
			course = self.courses.get(course_key, False)  # send in False rather than class default
			self.schedules.make(*schedule)

	def init(self):
		# Some of this stuff is pretty magical
		# The self.students, self.teachers, etc objects come from MetaDataStore
		# They actually return the new (or old) object, but we don't care about them here

		self.process_students()
		self.process_teachers()
		self.process_courses()

		self.process_groups()
		self.process_schedules()




class MoodleTree(AbstractTree):
	klass = MoodleImport
	pickup = DataStore
	convert_course = False

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
				log.warning("Could not get group: {} {}".format(teacher_username, course_idnumber))
			else:
				group = self.groups.get_key(teacher.username + course.idnumber)

			self.schedules.make(student, teacher, course)

	def process_groups(self):
		for group_name in self.group_info.content():
			if not group_name:
				continue
			teacher_username = re.sub(r'[^a-z]', '', group_name)
			course_idnumber = re.sub(r'[a-z]', '', group_name)
			teacher = self.teachers.get_from_attribute('username', teacher_username)
			course = self.courses.get_key(course_idnumber)
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


class AutoSendTree(AbstractTree):
	pickup = DataStore
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

			# wait a minute, why am I getting group here anyway?
			if not teacher or not course:
				group = None
			else:
				group = self.groups.get_key(teacher.username + course.idnumber)

			self.schedules.make(student, teacher, course)


class PostfixTree(AbstractTree):
	pass

class Item:
	def __init__(self, idnumber):
		self.idnumber = idnumber


if __name__ == "__main__":

	mstu33 = MoodleTree.students.make('33', '', '', '', '', '', '', '', '')
	mstu3333 = MoodleTree.students.make('3333', '', '', '', '', '', '', '', '')
	au33 = AutoSendTree.students.make('33', '', '', '', '', '', '', '', '')
	mteach33 = MoodleTree.teachers.make('33', "Morris, Adam", '', '', '', '')
	mstu33_ = MoodleTree.students.make('33', '', '', '', '', '', '', '', '')
	mteach555 = MoodleTree.teachers.make('555', "Morris, Adam", '', '', '', '')
	mteach333 = MoodleTree.teachers.make('333', "Morris, Adam", '', '', '', '')
	assert(mstu33 != mstu3333)
	assert(mstu33 != mteach33)
	assert(mstu33_ == mstu33)
	assert(mstu33 != au33)

