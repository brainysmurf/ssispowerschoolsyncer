from psmdlsyncer.models.datastores import Students

class Nothing:
	pass

class AClass(Nothing, Students):

	def __init__(self):
		self.make("1", "34343", "9", "9L", "Park, Ji Yun", "07/23/97", "somewhere@over.com", "03/13/00", "Korean")

	def test(self):
		print(self._store)

test = AClass()
test.test()