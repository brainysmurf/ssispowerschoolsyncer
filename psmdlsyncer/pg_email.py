import postgresql
import datetime
from psmdlsyncer.utils.Dates import date_to_database_timestamp, today, tomorrow

verbose = True
catch_wrong = True

class Nothing(Exception): pass

html_output = open('pg_html_output', 'w')
h = html_output.write
plaintext_output = open('pg_text_output', 'w')
p = plaintext_output.write
subject_output = open('pg_subject_output', 'w')
s = subject_output.write

k_record_id = 2

# Following gives me 1st, 2nd, 3rd, 4th, etc
def suffix(d):
	return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
	return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

class Database_Emailer:
	"""
	Converts a database on moodle into a useable system that emails users
	"""
	fields = ['date', 'attachment', 'content', 'timesrepeat', 'section']   # in the order returned by sql query
	tags = ['##secstunot_all##', '##secstunot_hs##', '##secstunot_ms##']

	search_date = "same day"

	def __init__(self, user, password, database, table):
		"""
		Populate self.found with legitimate entries
		Works by looking for target date, and then finding all entries with matching dates...
		   ... and then adding any entries with any that share the same recordid
		"""
		d = {'user':user, 'password':password, 'database':database, 'table':table}
		self.db = postgresql.open('pq://{user}:{password}@localhost/{database}'.format(**d))

		if self.search_date == "same day":
			self.date = today()
		elif self.search_date == "next day":
			self.date = tomorrow()
		else:
			raise Nothing

		self.custom_date = custom_strftime('%A %B {S}, %Y', self.date)
		print(self.date)
		month = self.date.month
		day   = self.date.day
		year  = self.date.year

		self.sql = self.db.prepare
		self.found = []
		d['date_to_check'] = date_to_database_timestamp(year=year, month=month, day=day)
		for tag in self.tags:
			d['tag'] = tag
			potential_rows = self.sql("select recordid from {table} where content = '{date_to_check}'".format(**d))()
			for row in potential_rows:
				d['recordid'] = row[0]
				match = self.sql("select * from {table} where recordid = {recordid} and content like '%{tag}'".format(**d))()
				if match:
					matched = self.sql("select * from {table} where recordid = {recordid}".format(**d))()
					matched.sort(key=lambda x:x[0])
					self.found.append( matched )
		if not self.found:
			raise Nothing
		verbose and input(self.found)
		self.reconstruct_found()

	def __del__(self):
		self.db.close()

	def reconstruct_found(self):
		"""
		Takes sql information found and converts it into a usable dictionary full of information
	
		Object breaks down thus:
		self.final              = {}     # keys composed of self.tags
		self.final[key]         = []     # list of all objects that share the same tag
		self.final[key][0]      = {}     # each object is a dict
		self.final[key][0][key] = ""     # object keys composed of self.fields
		"""
		self.final = {}    # list of dicts, each one an item
		for item in self.found:
			result = {}
			recordid = item[0][k_record_id]  # this is uniform throughout the item, just take the first one
			result['user'] = self.get_user_info(recordid)
			for field_id in range(0, len(item)):
				content = item[field_id][3]
				if content:
					for tag in self.tags:
						if tag in content:
							result['tag'] = tag
				key = self.fields[field_id]
				result[key] = content
			key = result['tag']
			if not key in list(self.final.keys()):
				self.final[key] = []
			self.final[key].append( result )

		if verbose:
			for key in self.final.keys():
				for item in self.final[key]:
					for item_key in item.keys():
						if not item_key == 'section':
							print("{}: {}".format(item_key, item[item_key]))
				print()
			input()

	def get_user_info(self, index):
		userid = self.db.prepare('select userid from ssismdl_data_records where id = {}'.format(index))()[0][0]
		verbose and print("User id: {}".format(userid))
		name_info = 'institution, firstname, lastname'
		name = self.db.prepare('select {} from ssismdl_user where id = {}'.format(name_info, userid))()[0]
		user_defined, firstname, lastname = name
		if not user_defined:
			name = firstname + ' ' + lastname
		else:
			name = user_defined
		name = "({})".format(name)
		verbose and print("Name: {}".format(name))
		return name

	def reconstruct_data(self, index):
		"""
		Second in the classe's workflow:
		Go through all the items available that are equal to index
		And add it to reconstruction list.
		Then validate that list by number of fields.
		If it validates, add a dictionary of the fields to the self.final list
		"""
		verbose and print("Inside reconstructing!")
		reconstruction = []
		for item in self.tagged:
			if item[2] == index:
				reconstruction.append(item)
		reconstruction.sort(key=lambda x: x[1])
		verbose and print("Reconstructed results, rather ugly")
		verbose and print(reconstruction)
		final = {}
		
		if len(reconstruction) < len(self.fields):
			# this one cannot possibly be what we're looking for, so forget about it
			verbose and print("This item's number of fields does not match the expected number ({})".format(len(self.fields)))
			verbose and print(reconstruction)
			verbose and print(len(self.fields))
			print("-----")
			print("Dropped an entry:")
			print(reconstruction)
			print("-----")
			return
		for f in range(0, len(self.fields)):
			verbose and print(f)
			final[self.fields[f]] = reconstruction[f][3]

		# This adds the user information
		final['user'] = self.get_user_info(index)

		verbose and print("Here is the final result!  Appending!")
		verbose and print(final)
		self.final.append(final)

	def derive_content(self, item):
		"""
		Formats the content
		Removes the tailing </p>
		Adds user info, and recloses it
		"""
		if item['content'].endswith('</p>'):
			h(self.list(item['content'][:-4] + " " + item['user'] + "</p>"))
		else:
			h(self.list(item['content'] + item['user'] + "</p>"))

	def format_for_email(self):
		verbose and print("Inside formatting!")
		if not self.final: raise Nothing

		# Body of the notices
		s("Secondary Student Notices for {}\n".format(self.custom_date))
		h("<html>")
		h("<p><b>All Students:</b></p><ul>")
		something_in_this_section = False
		for item in self.final:
			if item['section'] == 'All Secondary' or not item['section']:
				# if item does not have section indicated, then assume that's for "All Secondary"
				self.derive_content(item)
				something_in_this_section = True
		if not something_in_this_section:
			h(self.list("No specific notices"))

		something_in_this_section = False
		h("</ul><br /><b>Secondary Grades 9-12:</b><ul>")
		for item in self.final:
			if item['section'] == "High School only":
				self.derive_content(item)
				something_in_this_section = True
		if not something_in_this_section:
			h(self.list("No specific notices"))

		something_in_this_section = False
		h("</ul><br /><b>Secondary Grades 6-8:</b><ul>")
		for item in self.final:
			if item['section'] == "Middle School only":
				self.derive_content(item)
				something_in_this_section = True
		if not something_in_this_section:
			h(self.list("No specific notices"))
		h("</ul>")

		# Attachments of the notices
		header = False
		for item in self.final:
			if item['attachment']:
				if not header: 
					h("<br /><b>Attachments:</b>")
					header = True
				h(item['attachment'])

		h("</html>")

	def list(self, s):
		return "<li>{}</li>".format(s)

if __name__ == "__main__":

	try:
		here = pg_email('moodle', 'ssissqlmoodle', 'moodle', 'ssismdl_data_content')
		here.format_for_email()
	except Nothing:
		print("No matching entries found")
