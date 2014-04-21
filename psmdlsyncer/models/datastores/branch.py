from psmdlsyncer.models.student import Student
from psmdlsyncer.models.teacher import Teacher
from psmdlsyncer.models.course import Course
from psmdlsyncer.models.group import Group
from psmdlsyncer.models.schedule import Schedule
from psmdlsyncer.utils.Utilities import convert_short_long
import logging
log = logging.getLogger(__name__)

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
	def get_items(cls):
		return cls._resolve().items()

	@classmethod
	def get_values(cls):
		return cls._resolve().values()

	@classmethod
	def get_key(cls, key):
		return cls._resolve().get(key)

	@classmethod
	def get_from_attribute(cls, attr, value):
		for item in cls.get_values():
			if getattr(item, attr) == value:
				return item
		return None

	@classmethod
	def set_key(cls, key, value):
		cls.outer_store()[cls.fullname()][key] = value

	@classmethod
	def will_make_new(cls, new):
		pass

	@classmethod
	def did_make_new(cls, new):
		"""
		HOOK METHOD CALLED AFTER `make` MAKES A NEW ONE
		"""
		pass

	@classmethod
	def will_return_old(self, old):
		pass

	@classmethod
	def make(cls, idnumber, *args, **kwargs):
		"""
		Returns the object if already created, otherwise makes a new one
		Can be overridden if desired
		idnumber should the identifying idnumber, otherwise a callable to derive it
		"""
		if callable(idnumber):
			# TODO handle passing errors
			# Can't remember why I made this!
			idnumber = idnumber(*args, **kwargs)
		if cls.is_new(idnumber):
			# Instantiate the instance
			new = cls.klass(idnumber, *args, **kwargs)
			cls.will_make_new(new)
			cls.set_key(idnumber, new)
			cls.did_make_new(new)
			return new
		else:
			old = cls.get_key(idnumber)
			cls.will_return_old(old)
			return old

class students(DataStore):
	klass = Student

class teachers(DataStore):
	klass = Teacher

class groups(DataStore):
	klass = Group

	def make_group(self, teacher, course):
		group_id = teacher.username + course.ID
		return cls.make()

class courses(DataStore):
	klass = Course

	@classmethod
	def make_with_conversion(cls, idnumber, name=""):
		short, name = convert_short_long(idnumber, name)
		return cls.make(short, name)

	@classmethod
	def make_without_conversion(cls, idnumber, name=""):
		return cls.make(idnumber, name)

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
