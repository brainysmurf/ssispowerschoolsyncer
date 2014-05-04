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
		"""
		Return all the custom_profile instance and class variables
		If a custom_profile is set to None, don't return it
		That way someone else can set it None for more manual control
		"""
		keys = [key for key in self.__dict__ if key.startswith('custom_profile_')]
		keys.extend([key for key in self.__class__.__dict__ if key.startswith('custom_profile_')])
		return [key for key in keys if getattr(self, key) is not None]

	def get_custom_field(self, name, default=None):
		return getattr(self, 'custom_profile_'+name, default)

	def set_custom_field(self, name, value):
		return setattr(self, 'custom_profile_'+name, value)

	def __sub__(self, right):
		for variable in self.__dict__:
			ns = NS2()
			ns.name = variable
			ns.left = getattr(self, variable)
			ns.right = getattr(right, variable)
			ns.status = ns.left == ns.right
			if not ns.status:
				yield ns
