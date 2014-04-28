"""
USES FANCY META-PROGRAMMING IN ORDER TO ACCOMPLISH A RATHER SIMPLE THING, SO BEWARE
"""
import inspect, sys, copy
from collections import defaultdict
import re, logging
log = logging.getLogger(__name__)
from psmdlsyncer.models.datastores.branch import DataStore, students, teachers, parents, parent_links, timetables, custom_profile, groups, schedules, courses
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
	convert_course = False   # by default, don't run any conversion on the course shortname

	def __init__(self):
		self.logger = logging.getLogger('AbstractTree')
		self.default_logger = self.logger.debug
		self.student_info = self.klass('dist', 'studentinfo')
		self.teacher_info = self.klass('dist', 'staffinfo')
		self.secondary_courses = self.klass('sec', 'courseinfo')
		self.elementary_courses = self.klass('elem', 'courseinfo')
		self.allocations_info = self.klass('sec', 'teacherallocations')
		self.secondary_schedule = self.klass('sec', 'studentschedule')
		self.elementary_schedule = self.klass('elem', 'studentschedule')
		self.init()

	def process_students(self):
		self.default_logger('{} inside processing students'.format(self.__class__.__name__))
		for student in self.student_info.content():
			self.default_logger('Processing student: {}'.format(student))
			self.students.make(*student)

	def process_teachers(self):
		self.default_logger('{} inside processing teachers'.format(self.__class__.__name__))
		for teacher in self.teacher_info.content():
			self.default_logger('Processing teacher: {}'.format(teacher))
			self.teachers.make(*teacher)

	def process_parents(self):
		"""
		Go through the students and make parents based on that data
		"""
		for student in self.students.get_objects():
			self.parents.make_parent(student)

	def process_courses(self):
		self.default_logger('{} processing secondary courses'.format(self.__class__.__name__))
		for course in self.secondary_courses.content():
			self.default_logger('Processing course: {}'.format(course))
			if self.convert_course:
				self.courses.make_with_conversion(*course)
			else:
				self.courses.make_without_conversion(*course)

		self.default_logger('{} processing elementary courses'.format(self.__class__.__name__))
		for course in self.elementary_courses.content():
			self.default_logger('Processing course: {}'.format(course))
			if self.convert_course:
				self.courses.make_with_conversion(*course)
			else:
				self.courses.make_without_conversion(*course)

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
				group = self.groups.make_group(course, teacher, section_number)
				student = self.students.get_key(student_key)

				# Do some sanity checks
				if not course:
					self.logger.warning("Course not found! {}".format(course_key))
					continue
				if not teacher:
					self.logger.warning("Teacher not found! {}".format(teacher_key))
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



	def process_parent_links(self):
		"""
		Go through the students and build a tree that maps students to parents
		"""
		for student in self.students.get_objects():
			for parent in student.parents:
				self.parent_links.make_parent_link(parent, student)

	def process_custom_profile(self):
		"""
		By default, does nothing, because the model takes care of it
		"""
		for student in self.students.get_objects():
			self.custom_profile.make_profile(student)
		for parent in self.parents.get_objects():
			self.custom_profile.make_profile(parent)
		for teacher in self.teachers.get_objects():
			self.custom_profile.make_profile(teacher)

	def process_timetables(self):
		pass

	def associate(self, course, teacher, group, student):
		"""
		Updates everything in the model to point to each other
		"""
		course.associate(group, teacher, student)
		teacher.associate(course, group, student)
		student.associate(course, group, teacher)
		group.associate(course, teacher, student)
		# do not need to do group.add_teacher or .add_course because that is done at init

	def init(self):
		# Some of this stuff is pretty magical
		# The self.students, self.teachers, etc objects come from MetaDataStore
		# They actually return the new (or old) object, but we don't care about them here
		self.process_students()
		self.process_teachers()
		self.process_parents()
		self.process_parent_links()
		self.process_courses()
		self.process_schedules()
		self.process_custom_profile()
		self.process_timetables()


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

