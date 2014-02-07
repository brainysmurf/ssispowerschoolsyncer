from psmdlsyncer.models.student import Student
from psmdlsyncer.models.teacher import Teacher
from psmdlsyncer.models.course import Course
from psmdlsyncer.models.group import Group
from psmdlsyncer.models.schedule import Schedule

from psmdlsyncer.utils.Utilities import convert_short_long

class DataStore:
	"""
	"""
	__set_outerclass__ = True

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
		return cls.outer_store()[cls.fullname()].keys()

	@classmethod
	def get_items(cls):
		return cls.outer_store()[cls.fullname()].items()

	@classmethod
	def get_values(cls):
		return cls.outer_store()[cls.fullname()].values()

	@classmethod
	def get_key(cls, key):
		try:
			return cls.outer_store()[cls.fullname()][key]
		except KeyError:
			log.warning("No {} in {}{}".format(key, cls.__base__, cls.__qualname__))
			return None

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
	def did_make_new(self, new):
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
		"""
		if cls.is_new(idnumber):
			# Instantiate the klass
			new = cls.klass(idnumber, *args, **kwargs)
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

class courses(DataStore):
	klass = Course

	@classmethod
	def make_with_conversion(cls, idnumber, name=""):
		short, name = convert_short_long(idnumber, name)
		return cls.make(short, name)

	@classmethod
	def make_without_conversion(cls, idnumber, name=""):
		return cls.make(idnumber, name)

class schedules(DataStore):
	klass = Schedule

