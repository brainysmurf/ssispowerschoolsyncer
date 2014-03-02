from psmdlsyncer.models.datastores.tree import AbstractTree

class test:
	def __init__(self, which):
		self.which = which

	def content(self):
		if self.which == 'left':
			return self.left_content()
		elif self.which == 'right':
			return self.right_content()


class test_student_info(test):
	def left_content(self):
		return (
			('33333', '1113', '6', '6L', 'Student, Happy', '05/02/1960', 'happyparent@gmail.com', '01/08/2013', 'America'),
			('44444', '1114', '3', '3BA', 'Student, Happier', '11/11/1954', 'happierparent@gmail.com', '01/08/2013', 'Italy'),
			('55555', '1115', '12', '12A', 'Student, Happiest', '11/11/1944', 'happiestparent@gmail.com', '01/08/2013', 'France'),

			('66666', '1116', '6', '10A', 'Student, Unhappy', '05/02/1960', 'unhappyparent@gmail.com', '01/08/2013', 'Somewhereland'),
			('77777', '1117', '3', '4BA', 'Student, Unhappier', '11/02/1950', 'unhappierparent@gmail.com', '01/08/2013', 'Nowhereland'),
			('88888', '1118', '12', '11L', 'Student, Unhappiest', '11/02/1955', 'unahappiestparent@gmail.com', '01/08/2013', 'Warland'),
			)

	def right_content(self):
		return (
			('33333', '1113', '6', '6L', 'Student, Happy', '05/02/1960', 'happyparent@gmail.com', '01/08/2013', 'America'),
			('44444', '1114', '3', '3BA', 'Student, Happier', '11/11/1954', 'happierparent@gmail.com', '01/08/2013', 'Italy'),
			('55555', '1115', '12', '12A', 'Student, Happiest', '11/11/1944', 'happiestparent@gmail.com', '01/08/2013', 'France'),

			('66666', '1116', '6', '10A', 'Student, Unhappy', '05/02/1960', 'unhappyparent@gmail.com', '01/08/2013', 'Somewhereland'),
			('77777', '1117', '3', '4BA', 'Student, Unhappier', '11/02/1950', 'unhappierparent@gmail.com', '01/08/2013', 'Nowhereland'),
			('88888', '1118', '12', '11L', 'Student, Unhappiest', '11/02/1955', 'unahappiestparent@gmail.com', '01/08/2013', 'Warland'),
			)


class test_schedule_info(test):
	def left_content(self):
		return (
			('AWESOMECLASS', '4-5(B) 6-7(A)', '5', 'Teacher, Happy', '81888', 'Student, Happy', '33333'),
			('AWESOMERCLASS', '2-3(A) 5-6(B)', '10', 'Teacher, Happier', '82888', 'Student, Happier', '44444'),
			('AWESOMESTCLASS', '4-5(C) 2-3(D)', '11', 'Teacher, Happiest', '83888', 'Student, Happiest', '55555')

			('BOOHISSCLASS', '1-2(A) 3-4(B)', '1', 'Teacher, Unhappy', '84888', 'Student, Unhappy', '66666')
			('BOOHISSERCLASS', '8-9(C) 4-5(A)', '2', 'Teacher, Unhappier', '85888', 'Student, Unhappier', '77777')
			('BOOHISSIESTCLASS', '3-4(A) 5-6(C)', '2', 'Teacher, Unhappiest', '86888', 'Student, Unhappieste', '88888')
		)

	def right_content(self):
		pass


class test_teacher_info(test):
	def left_content(self):
		return (
			('81888', 'Teacher, Happy', 'happyteacher@example.com', 'Mr', '1', '1'),
			('82888', 'Teacher, Happier', 'happierteacher@example.com', 'Mr', '1', '1'),
			('83888', 'Teacher, Happiest', 'happiestteacher@example.com', 'Mr', '1', '1'),

			('84888', 'Teacher, Unhappy', 'unhappyteacher@example.com', 'Mr', '1', '1'),
			('85888', 'Teacher, Unhappier', 'unhappierteacher@example.com', 'Mr', '1', '1'),
			('86888', 'Teacher, Unhappiest', 'unhappiestteacher@example.com', 'Mr', '1', '1'),
			)

	def right_content(self):
		pass


class test_schedule_info(test):
	def left_content(self):
		pass

	def right_content(self):
		pass


class test_course_info(test):
	def left_content(self):
		pass

	def right_content(self):
		pass


class test_allocations_info(test):
	def left_content(self):
		pass

	def right_content(self):
		pass


class test_group_info(test):
	def left_content(self):
		pass

	def right_content(self):
		pass


class test_schedule_info(test):
	def left_content(self):
		pass

	def right_content(self):
		pass


class TestLeftTree(AbstractTree):
	self.schedule_info = test_schedule_info()
	self.student_info = test_student_info()
	self.teacher_info = test_teacher_info()
	self.course_info = test_course_info()
	self.allocations_info = test_allocations_info()
	self.group_info = test_group_info()
	self.schedule_info = test_schedule_info()


class TestRightTree(AbstractTree):
	pass