from psmdlsyncer.utils import NS2

class BaseModel:
	def update(self, key, value):
		self.key = value

	def compare_kwargs(self, **kwargs):
		if set(list(kwargs.keys())).issubset(list(self.__dict__)):
			for key in kwargs:
				if not str(self.__dict__[key]) == str(kwargs[key]):
					return False
		else:
			return False
		return True

	def format_string(self, s, **kwargs):
		d = self.__dict__.copy()
		for key in kwargs.keys():
			# replace anything sent in, this is on purpose
			# because as it turns out you might have a method with the same name
			d[key] = kwargs[key]
		return s.format(**d)

	def plain_name_of_custom_field(self, custom_field):
		return custom_field.split('custom_profile_')[1]

	def get_custom_field_keys(self):
		return [key for key in self.__dict__ if key.startswith('custom_profile_')]

	def __sub__(self, right):
		for variable in self.__dict__:
			ns = NS2()
			ns.name = variable
			ns.left = getattr(self, variable)
			ns.right = getattr(right, variable)
			ns.status = ns.left == ns.right
			if not ns.status:
				yield ns
