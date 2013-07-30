
"""
LIMITATION:
IF there are any two variables, then you'll have to rewrite completely, because
it's not just a matter of 'how many', but of 'which ones'
"""

class moodle_csv_row:
	"""
	Represents a row in the file
	Keeps track of how many entries per each header
	So that when you output as CSV all the columns add up to the same number
	"""
	def __init__(self, header_list):
		self.header_list = header_list
		self.content = {}
		for key in header_list:
			self.content[key] = []

	def build(self, name, objects):
		if isinstance(objects, str):
			if name.endswith('_'):
				raise ValueError("Cannot use strings with variable headers, pass list instead")
			self.content[name] = [objects]
		elif isinstance(objects, list):
			if not name.endswith('_'):
				raise ValueError("Cannot use list with non-variable headers, pass str instead.")
			self.content[name].extend(objects)
		else:
			print(name)
			print(objects)
			raise ValueError("What on earth did you pass?")
		return self

	def build_(self, objects):
	        return self.build(self.name, objects)

	def __getattr__(self, name):
		if name.startswith('build_'):
			self.name = name[6:]
			return self.build_
		else:
			return self.__dict__[name]

	def __getitem__(self, name):
		return self.content[name]

	def output(self, max_dict):
		out = []
		for header in self.header_list:
			max = max_dict[header]
			l   = len(self.content[header])
			if l < max:
				for i in range(0, max-l):
					out.append("")
			out.extend(self.content[header])
		return ",".join(out)

class MoodleCSVFile:
	def __init__(self, path=''):
		self.rows = []
		self.header_info = {}   # keeps track of maximum entries per header
		self.header_list = []   # the header list
		self.path = path if path else None

	def add_row(self, r):
		"""
		Adds row, and updates header_info so we know how many of them we have to account for
		"""
		self.rows.append(r)
		for header in self.header_info.keys():
			this = r[header]
			if not isinstance(this, list):
				continue
			now_max = self.header_info[header]
			if now_max < len(this):
				self.header_info[header] = len(this)

	def factory(self):
		return moodle_csv_row(self.header_list)

	def build_headers(self, objects):
		for o in objects:
			self.header_info[o] = 0
		self.header_list.extend(objects)

	def output(self):
		"""
		Writes the data to the file if self.path is defined
		Also returns the data (so you can print to stdout)
		"""
		# out is just the header information
		out = []
		for header in self.header_list:
			max = self.header_info[header]
			if not max:
				out.append(header)
			else:
				if header.endswith('_'):
					for t in range(1, max+1):
						out.append( header[:-1] + str(t) )
				else:
					out.append( header )
		# s is the string to pass to the file
		s = ",".join(out) + '\n'
		s += "\n".join([r.output(self.header_info) for r in self.rows])
		if self.path:
			with open(self.path, 'w') as f:
				f.write(s)
		return s

if __name__ == "__main__":

	output_file = MoodleCSVFile()
	output_file.build_headers(['username', 'profile_field_blah', 'course_', 'cohort_'])

	row = output_file.factory()
	row.build_username('Adam Morris')
	row.build_profile_field_blah('boob')
	row.build_course_(['loves and misses', 'bun', 'ny'])
	row.build_cohort_(['howdy'])
	output_file.add_row(row)

	row = output_file.factory()
	row.build_username('Adam Morris')
	row.build_profile_field_blah('blah')
	row.build_course_(['Bunny', 'Ah'])
	row.build_cohort_(['no', 'yes', 'effing'])
	output_file.add_row(row)

	print(output_file.output())
