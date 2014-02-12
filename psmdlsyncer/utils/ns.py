class NS2:
	def __init__(self, *args, **kwargs):
		self.COLON = ':'
		self.COMMA = ','
		self.SEMICOLON = ';'
		self.NEWLINE = '\n'
		self.SPACE = ' '
		self.TAB = '\t'
		self.SLASH = '/'
		self.LPARENS = '('
		self.RPARENS = ')'
		self.AT = '@'

		# Useful regexp phrases
		self.DOT = '.'
		self.ASTER = '*'

		self._args = args
		for arg in self._args:
			kwargs.update(arg.__dict__)
		self.__dict__.update(kwargs)

	def dict_from_dict(self):
		return {key: value for key, value in self.__dict__.items() if not key.startswith('_')}

	def __call__(self, output):
		return output.format(*self._args, **self.dict_from_dict())

	@classmethod
	def string(cls, astring, *args, **kwargs):
		for arg in args:
			kwargs.update(arg.__dict__)
		return cls(*args, **kwargs)(astring)


