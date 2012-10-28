import postgresql

class access:
	prefix = 'ssismdl_'
	def __init__(self):
		self.db = postgresql.open('pq://moodle:ssissqlmoodle@localhost/moodle')
		self.sql = self.db.prepare

	def show_tables(self):
		return [t[0] for t in self.sql('select table_name from information_schema.tables')()]

	def show_tables_startswith(self, withwhat):
		return [t for t in self.show_tables() if t.startswith(self.prefix+withwhat)]

	def show_table_column_names(self, table):
		return [c[0] for c in self.sql("select column_name from information_schema.columns where table_name='{}'".format(self.prefix+table))()]

	def select_table(self, table):
		return self.sql('select * from {}{}'.format(self.prefix, table))()
	
	def __del__(self):
		self.db.close()


if __name__ == "__main__":

	a = access()
	print(a.show_table_column_names('data_fields'))
	input()
	print(a.select_table('data_fields'))
	print(a.sql("select param1 from ssismdl_data_fields where id = 7")())
