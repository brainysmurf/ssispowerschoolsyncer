"""
USES FANCY META-PROGRAMMING IN ORDER TO ACCOMPLISH A RATHER SIMPLE THING, SO BEWARE
"""
import inspect, sys, copy
from collections import defaultdict
import re, logging
log = logging.getLogger(__name__)
from psmdlsyncer.models.datastores.branch import DataStore, students, teachers, parents, \
	mrbs_editors, cohorts, parent_links, timetables, custom_profile_fields, groups, schedules, courses
from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.files import AutoSendImport
from psmdlsyncer.utils import NS2
from psmdlsyncer.settings import config_get_section_attribute

def is_immediate_subclass(klass, of_klass):
	"""
	This way datastores can use inheritance in fancier ways
	This also means that 'pickup' is more literal
	"""
	if klass is of_klass:
		return True
	if len(klass.__bases__) < 1:
		return False
	subclass = klass.__bases__[0]
	return subclass is of_klass

class DataStoreCollection(type):
	_store = defaultdict(dict)
	qual_name_delimiter = "."
	qual_name_format = "{branch}{delim}{subbranch}"

	def __init__(cls, name, bases, attrs):
		if attrs.get('pickup'):
			datastores = attrs.get('pickup')
			if not isinstance(datastores, list):
				datastores = [datastores]

			# Cycle through all the classes that have been declared in this module, so we can augment this class with those ones
			# Limitation: You have to declare your branches in the same place as this module
			# TODO: Get around above limitation by passing a string and importing that way

			for datastore in datastores:
				find_classes = []
				all_modules = sys.modules.keys()

				# For ease in use, we inspect all modules available at this place in the code
				# and look for the pickups classes
				for module_key in all_modules:
					module = sys.modules[module_key]
					get_all_module_classes = inspect.getmembers(module, inspect.isclass)

					# Now go through all classes in this particular module
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
							if 	is_immediate_subclass(class_reference, datastore): # now see if this object is subclass of class represented by `pickup`
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
		# Filter out any special __variables__ like that
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
		self._processed = False
		self.logger = logging.getLogger('AbstractTree')
		self.default_logger = self.logger.debug
		self.student_info = self.klass('dist', 'studentinfo')
		self.parent_info = self.klass('dist', 'parentinfo')
		self.parent_student_links = self.klass('dist', 'parentstudentlinks')
		self.teacher_info = self.klass('dist', 'staffinfo')
		self.district_courses = self.klass('dist', 'courseinfo')
		self.allocations_info = self.klass('sec', 'teacherallocations')
		self.secondary_schedule = self.klass('sec', 'studentschedule')
		self.elementary_schedule = self.klass('elem', 'studentschedule')
		self.custom_profile_fields_info = self.klass('dist', 'customprofiles')
		self.mrbs_editor_info = self.klass('dist', 'mrbs_editors')
		self.cohort_info = self.klass('dist', 'cohorts')

	def get_subbranches(self):
		return set([re.sub('^.*\.', '', key) for key in self.__class__._store.keys()])

	def get_store_keys(self):
		return [key for key in self.__class__._store.keys() if key.startswith(self.__class__.__name__)]

	def get_person(self, idnumber):
		student = self.students.get_key(idnumber)
		if student:
			return student
		teacher = self.teachers.get_key(idnumber)
		if teacher:
			return teacher
		parent = self.parents.get_key(idnumber)
		if parent:
			return parent
		return None

	def get_everyone(self):
		for student_key in self.students.get_keys():
			yield self.students.get_key(student_key)
		for teacher_key in self.teachers.get_keys():
			yield self.teachers.get_key(teacher_key)
		for parent_key in self.parents.get_keys():
			yield self.parents.get_key(parent_key)

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
			parent = self.parents.make_parent(student)
			student.add_parent(parent)

	def process_courses(self):
		for course_info in self.district_courses.content():
			self.default_logger('Processing course: {}'.format(course_info))
			if self.convert_course:
				course = self.courses.make_with_conversion(*course_info)
			else:
				course = self.courses.make_without_conversion(*course_info)

			self.course_metadatas.make_course_metadata(course.idnumber, course.grade)


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
				if not course:
					self.logger.warning("Course not found! {}".format(course_key))
					continue
				if course.exclude:
					self.default_logger("Course {} has been excluded!".format(course_key))
					# And so we should skip this schedule entirely!
					continue
				teacher = self.teachers.get_key(teacher_key)
				if not teacher:
					self.logger.warning("Teacher not found! {}".format(teacher_key))
					continue
				group = self.groups.make_group(course, teacher, section_number)
				if not group:
					self.logger.warning("Group not found! {}".format(section_number))
					continue
				student = self.students.get_key(student_key)

				# Do some sanity checks
				if not student:
					self.default_logger("Student not found, sometimes happens for some odd reason {}".format(student_key))
					continue

				self.associate(course, teacher, group, student)

				# timetable = self.timetables.make_timetable(
				# 	course, teacher, group, student, section_number, period_info
				# 	)
				# student.add_timetable(timetable)
				# teacher.add_timetable(timetable)

				# self.timetable_datas.make_timetable_datas(course, teacher, group, student, period_info)

				if student.login_method == 'manual':
					self.online_portfolios.make(student.idnumber)

				if str(config_get_section_attribute('DEBUGGING', 'inspect_teacher_schedule')) == teacher_key:
					self.logger.warning('{}\n{}\n{}\n'.format(teacher, group, student))
					from IPython import embed
					embed()

	# def process_timetable_data(self):
	# 	pass

	def process_parent_links(self):
		"""
		Go through the students and build a tree that maps students to parents
		"""
		for student in self.students.get_objects():
			for parent in student.parents:
				self.parent_links.make_parent_link(parent.idnumber, student.idnumber)

	def process_custom_profile_fields(self):
		"""
		The make_profile creates the keys, which are just the name of the fields
		"""
		for person in self.get_everyone():
			self.custom_profile_fields.make_profile(person)

	def process_cohorts(self):
		for person in self.get_everyone():
			self.cohorts.make_cohort(person)

	def process_mrbs_editors(self):
		for teacher in self.teachers.get_objects():
			self.mrbs_editors.make(teacher.idnumber)

	def process_online_portfolios(self):
		pass

	def associate(self, course, teacher, group, student):
		"""
		Updates everything in the model to point to each other
		"""
		course.associate(group, teacher, student)
		teacher.associate(course, group, student)
		student.associate(course, group, teacher)
		group.associate(course, teacher, student)

	def process(self):
		# Basically just calls every process_x method we have
		debug = config_get_section_attribute('DEBUGGING', 'print_process')
		order = ['students', 'teachers', 'parents', 'parent_links', 'cohorts', 'courses', 'schedules',  'mrbs_editors', 'online_portfolios']
		for o in order:
			method_name = 'process_{}'.format(o)
			method = getattr(self, method_name)
			debug and self.logger.warning(method)
			method()

	def blankify(self):
		for branch in self.get_store_keys():
			self.__class__._store[branch] = {}

	def re_process(self):
		"""
		Set everything to zero
		"""
		self.blankify()
		self.process()

class PostfixTree(AbstractTree):
	pass

class Item:
	def __init__(self, idnumber):
		self.idnumber = idnumber

if __name__ == "__main__":

	from psmdlsyncer.models.datastores.moodle import MoodleTree
	from psmdlsyncer.models.datastores.autosend import AutoSendTree

	moodle = MoodleTree()
	autosend = AutoSendTree()
	mstu33 = moodle.students.make('33', '', '', '', '', '', '', '', '', '')
	mstu3333 = moodle.students.make('3333', '', '', '', '', '', '', '', '', '')
	au33 = autosend.students.make('33', '', '', '', '', '', '', '', '', '')
	mteach33 = moodle.teachers.make('33', 3, "Morris, Adam", '', '', '', '', '')
	mstu33_ = moodle.students.make('33', '', '', '', '', '', '', '', '', '')
	mteach555 = moodle.teachers.make('555', 5, "Morris, Adam", '', '', '', '', '')
	mteach333 = moodle.teachers.make('333', 33, "Morris, Adam", '', '', '', '', '')
	assert(mstu33 != mstu3333)
	assert(mstu33 != mteach33)
	assert(mstu33_ == mstu33)
	assert(mstu33 != au33)

	from IPython import embed
	embed()

