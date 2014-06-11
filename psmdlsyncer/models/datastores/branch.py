from psmdlsyncer.models.student import Student
from psmdlsyncer.models.teacher import Teacher
from psmdlsyncer.models.parent import Parent, MoodleParent
from psmdlsyncer.models.parent_link import ParentLink
from psmdlsyncer.models.custom_profile import CustomProfileField
from psmdlsyncer.models.course import Course
from psmdlsyncer.models.group import Group
from psmdlsyncer.models.schedule import Schedule
from psmdlsyncer.models.timetable import Timetable
from psmdlsyncer.models.timetable_datas import TimetableDatas
from psmdlsyncer.models.course_metadatas import CourseMetaData
from psmdlsyncer.models.mrbs import MRBSEditor
from psmdlsyncer.models.cohorts import Cohort
from psmdlsyncer.models.online_portfolios import OnlinePortfolio
from psmdlsyncer.utils.Utilities import convert_short_long
import logging
log = logging.getLogger(__name__)
from collections import defaultdict

class DataStore:
	"""
	"""
	__set_outerclass__ = True

	@classmethod
	def _resolve(cls):
		return cls.outer_store()[cls.fullname()]

	@classmethod
	def klass(cls):
		"""
		Override in subclass
		Should return the class object that we wish to use in the storestore
		"""
		#return Klass
		raise NotImplemented

	@classmethod
	def outer_store(cls):
		return cls.__outerclass__._store

	@classmethod
	def fullname(cls):
		return cls.__qualname__

	@classmethod
	def is_new(cls, idnumber):
		return not idnumber in cls.get_keys()

	@classmethod
	def get_keys(cls):
		return cls._resolve().keys()

	@classmethod
	def get_keys_startswith(cls, startswith):
		return [key for key in cls._resolve().keys() if key.startswith(startswith)]

	@classmethod
	def get_items(cls):
		for item in cls._resolve().items():
			yield item

	@classmethod
	def del_key(cls, key):
		del cls._resolve()[key]

	@classmethod
	def del_all_keys(cls, key):
		for key in cls.get_keys():
			cls.del_key(key)

	# TODO: Figure out why I can't do this
	# def __iter__(self):
	# 	input()
	# 	for item_key in self.get_keys():
	# 		yield self[item_key]

	@classmethod
	def get_objects(cls):
		return cls._resolve().values()

	@classmethod
	def get_object_n(cls, n):
		list(cls.get_objects())[n]

	@classmethod
	def get_key(cls, key):
		return cls._resolve().get(key)

	@classmethod
	def get_from_attribute(cls, attr, value):
		for item in cls.get_objects():
			if getattr(item, attr) == value:
				return item
		return None

	@classmethod
	def find_one_with_callback(cls, callback):
		for item in cls.get_objects():
			if callback(item):
				return item

	@classmethod
	def set_key(cls, key, value):
		cls.outer_store()[cls.fullname()][key] = value

	@classmethod
	def will_make_new(cls, new, *args, **kwargs):
		pass

	@classmethod
	def did_make_new(cls, new, *args, **kwargs):
		"""
		HOOK METHOD CALLED AFTER `make` MAKES A NEW ONE
		"""
		pass

	@classmethod
	def will_return_old(self, old, *args, **kwargs):
		pass

	@classmethod
	def make(cls, idnumber, *args, **kwargs):
		"""
		Returns the object if already created, otherwise makes a new one
		Can be overridden if desired
		idnumber should the identifying idnumber, otherwise a callable to derive it
		"""
		if callable(idnumber):
			# FIX: Can't remember why I made this!
			# Nothing seems to use it!
			idnumber = idnumber(*args, **kwargs)
		if cls.is_new(idnumber):
			# Instantiate the instance
			new = cls.klass(idnumber, *args, **kwargs)
			cls.will_make_new(new, *args, **kwargs)
			cls.set_key(idnumber, new)
			cls.did_make_new(new, *args, **kwargs)
			return new
		else:
			old = cls.get_key(idnumber)
			cls.will_return_old(old, *args, **kwargs)
			return old

class students(DataStore):
	klass = Student

class teachers(DataStore):
	klass = Teacher

class parents(DataStore):
	klass = Parent

	@classmethod
	def make_parent(cls, student):
		idnumber = student.family_id
		parent = cls.make(idnumber)
		parent.add_child(student)
		return parent

class parent_links(DataStore):
	klass = ParentLink

	@classmethod
	def did_make_new(cls, new, child):
		"""
		HOOK METHOD CALLED AFTER `make` MAKES A NEW ONE
		"""
		new.add_child(child)

	@classmethod
	def will_return_old(self, old, child):
		old.add_child(child)

	@classmethod
	def make_parent_link(cls, parent, child):
		return cls.make(parent, child)

class groups(DataStore):
	klass = Group
	sep = '-'
	section_maps = {}   # keep a record of section mappings, which lets us use abcs for the groups

	@classmethod
	def make_group(cls, course, teacher, section):
		"""
		Makes a group and parses the section as well
		The passed section should be the 'official' section number
		here we will change it to .a or .b accordingly
		"""
		idnumber = "{}{}".format(teacher.username.lower(), course.idnumber.upper())
		sectional_key = "{}{}{}".format(idnumber, cls.sep, section)
		if sectional_key in cls.section_maps.keys():
			# Already have it, so use that then
			return cls.make(cls.section_maps[sectional_key], course.idnumber)
		else:
			# first time running, make a new sectional
			how_many = len(cls.get_keys_startswith("{}{}".format(idnumber, cls.sep)))
			alpha = chr(ord('a') + how_many)
			new_sectional_value = "{}{}{}".format(idnumber, cls.sep, alpha)
			# keep for future reference, and return
			cls.section_maps[sectional_key] = new_sectional_value
			return cls.make(new_sectional_value, course.idnumber)

class course_metadatas(DataStore):
	klass = CourseMetaData

	@classmethod
	def make_course_metadata(cls, course_idnumber, course_grade):
		idnumber = course_idnumber
		cls.make(idnumber, course_idnumber, course_grade)

class timetable_datas(DataStore):
	klass = TimetableDatas

	@classmethod
	def make_timetable_datas(cls, course, teacher, group, student, period_info):
		idnumber = '{}/{}'.format(group.idnumber, student.idnumber)
		return cls.make(idnumber, course, teacher, group, student, period_info)

class timetables(DataStore):
	klass = Timetable

	@classmethod
	def make_timetable(cls, course, teacher, group, student, section, period_info):
		"""
		This one is a bit different from the others
		Making it just sets up an object that is then called to get the timetable data
		Return that, the calling function will pass it on to the student and teacher object
		"""
		idnumber = '{}/{}'.format(group.ID, student.idnumber)
		this = cls.make(idnumber, course, teacher, group, student, period_info)
		return this.unpack_timetable()

class courses(DataStore):
	klass = Course

	@classmethod
	def exclude(cls, idnumber, name):
		# TODO: Make this a setting
		return "Lab" in name

	@classmethod
	def make_with_conversion(cls, idnumber, name, *args, **kwargs):
		short, name = convert_short_long(idnumber, name)
		ret = cls.make(short, name, *args, **kwargs)
		if cls.exclude(idnumber, name) and not ret.exclude:
			ret.exclude = True
		return ret

	@classmethod
	def make_without_conversion(cls, idnumber, name, *args, **kwargs):
		ret = cls.make(idnumber, name, *args, **kwargs)
		if cls.exclude(idnumber, name) and not ret.exclude:
			ret.exclude = True
		return ret

	@classmethod
	def get(cls, idnumber, convert):
		if convert:
			return cls.get_with_conversion(idnumber)
		else:
			return cls.get_without_conversion(idnumber)

	@classmethod
	def get_with_conversion(cls, idnumber):
		short, _ = convert_short_long(idnumber, "")
		return cls.get_key(short)

	@classmethod
	def get_without_conversion(cls, idnumber):
		return cls.get_key(idnumber)

class schedules(DataStore):
	klass = Schedule

	@classmethod
	def make_schedule(cls, *args):
		"""
		no idnumber, we have to calculate that ourselves
		"""
		schedule_id = "".join([arg.ID for arg in args])
		return cls.make(schedule_id, *args)

class custom_profile_fields(DataStore):
	klass = CustomProfileField

	@classmethod
	def make_profile(cls, person):
		for custom_field in person.get_custom_field_keys():
			idnumber = person.plain_name_of_custom_field(custom_field)
			cls.make(idnumber)

class mrbs_editors(DataStore):
	klass = MRBSEditor

class cohorts(DataStore):
	klass = Cohort

	@classmethod
	def make_cohort(cls, person):
		for cohort in person.cohorts:
			cls.make(cohort)

class online_portfolios(DataStore):
	klass = OnlinePortfolio


