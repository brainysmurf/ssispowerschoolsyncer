"""
USES FANCY META-PROGRAMMING IN ORDER TO ACCOMPLISH A RATHER SIMPLE THING, SO BEWARE
"""
import inspect, sys, copy
from collections import defaultdict
import logging
log = logging.getLogger(__name__)
from psmdlsyncer.models.datastores.branch import DataStore, students, teachers, groups, schedules, courses
from psmdlsyncer.models.datastores.abstract import AbstractTree
from psmdlsyncer.models.datastores.moodle import MoodleAbstractTree
from psmdlsyncer.models.datastores.autosend import AutoSendAbstractTree
from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.files import AutoSendImport
from psmdlsyncer.utils import NS2

class DataStoreCollection(type):
	_store = defaultdict(dict)
	qual_name_format = "{branch}{delim}{subbranch}"
	qual_name_delimiter = "."

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
	def my_key_endwith(cls, endswith):
		return self._store[cls.qual_name_format.format(cls.__name__, key)]

	@classmethod
	def get_branch(cls, key):
		return key.split(cls.qual_name_delimiter)[-1]

	def __sub__(self, other):
		print("NOT HERE!")



		return []


class MoodleTree(MoodleAbstractTree, metaclass=DataStoreCollection):
	klass = MoodleImport
	pickup = DataStore

	def __sub__(self):
		input('not quite')

class AutoSendTree(AutoSendAbstractTree, metaclass=DataStoreCollection):
	klass = AutoSendImport
	pickup = DataStore

class PostfixTree(AbstractTree, metaclass=DataStoreCollection):
	pickup = DataStore

class Item:
	def __init__(self, idnumber):
		self.idnumber = idnumber


if __name__ == "__main__":

	mstu33 = Moodle.students.make('33', '', '', '', '', '', '', '', '')
	mstu3333 = Moodle.students.make('3333', '', '', '', '', '', '', '', '')
	au33 = AutoSend.students.make('33', '', '', '', '', '', '', '', '')
	mteach33 = Moodle.teachers.make('33', "Morris, Adam", '', '', '', '')
	mstu33_ = Moodle.students.make('33', '', '', '', '', '', '', '', '')
	mteach555 = Moodle.teachers.make('555', "Morris, Adam", '', '', '', '')
	mteach333 = Moodle.teachers.make('333', "Morris, Adam", '', '', '', '')
	assert(mstu33 != mstu3333)
	assert(mstu33 != mteach33)
	assert(mstu33_ == mstu33)
	assert(mstu33 != au33)

