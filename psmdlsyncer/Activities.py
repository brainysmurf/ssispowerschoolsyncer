from psmdlsyncer.Tree import Tree, put_in_order

from psmdlsyncer.utils import NS
from psmdlsyncer.sql import MoodleDBConnection
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.files import clear_folder

import re

def name_to_email(long_name):
	try:
		where = long_name.index(')')
	except ValueError:
		where = -1
	where += 1
	long_name = long_name[where:].strip().lower()
	return re.sub('[^a-z]', '', long_name)
	
def convert_activity_name(name):
	to_replace = r"""
		^   		# beginning of line
   		\s? 		# any whitespace
   		\(  		# left parens
   		.*? 		# anything inside, non-greedy
   		\)  		# right parents
		\s? 		# any whitespace
	"""
	to_replace = r"^\s?\(.*?\)\s?"
	return re.sub(to_replace, '', name)

if __name__ == "__main__":
	students = Tree()
   
	db = MoodleDBConnection()
	sf = NS(domain='student.ssis-suzhou.net')
	results = db.get_all_users_activity_enrollments()


	# PARSE RESULTS
	for result in results:
		activity_name, student_key = result
		student = students.get_student(student_key)
		if not student:
			continue

		sf.activity_name = convert_activity_name(activity_name)
		sf.take_dict(student)
		print(sf('{activity_name}{TAB}{idnumber}{TAB}{lastfirst}'))


	"""
	from collections import defaultdict
	postfix = defaultdict(list)
	activities = defaultdict(list)
	homerooms = defaultdict( lambda : defaultdict(list) )

	homerooms[student.homeroom][ (student.lastfirst, student)].append(activity_name)
	activities[activity_name].append(student)
	postfix[activity_name].append(student.email)

	homerooms_sorted = list(homerooms.keys())
	homerooms_sorted.sort(key=put_in_order)
	for homeroom in homerooms_sorted:
		print('\n' + homeroom)
		students_sorted = list(homerooms[homeroom].keys())
		students_sorted.sort(key=lambda x: x[0])
		for item in students_sorted:
			lastfirst, student = item
			s = NS()
			s.take_dict(student)
			s.activities = ", ".join( homerooms[homeroom][(lastfirst, student)] )
			print(s('{lastfirst}{COLON}{SPACE}{activities}'))

	activities_sorted = list(activities.keys())
	activities_sorted.sort()
	for activity in activities_sorted:
		print('\n' + activity)
		for student in activities[activity]:
			s = NS()
			s.take_dict(student)
			print(s('{lastfirst}{TAB}{homeroom}'))

	# DO THE ACTIVITY EMAILS
	sf.path = config_get_section_attribute('DIRECTORIES', 'path_to_postfix')
	sf.base = 'activities'
	sf.SUFFIX = "ACT"
	sf.EXT = '.txt'
	sf.INCLUDE = ':include:'
	sf.activities_path = sf('{path}{SLASH}{base}')
	sf.space = ' '
	clear_folder(sf.activities_path)
	with open(sf('{path}{SLASH}{base}{EXT}'), 'w'):
		pass

	for activity_name in postfix:
		sf.handle = name_to_email(activity_name)
		sf.full_email = sf('{handle}{SUFFIX}')
		with open(sf('{path}{SLASH}{base}{EXT}'), 'a') as f:
			f.write(sf('{full_email}{COLON}{SPACE}{INCLUDE}{activities_path}{SLASH}{full_email}{EXT}{NEWLINE}'))
		with open(sf('{activities_path}{SLASH}{full_email}{EXT}'), 'a') as f:
			f.write("\n".join(postfix[activity_name]))

	output = []
	for activity_name in postfix:
		output.append(name_to_email(activity_name))

	output.sort()
	for activity in output:
		sf.activity = activity
		sf.email = sf('{activity}{SUFFIX}{AT}{domain}')
		print(sf( '<a href="mailto:{email}">{email}</a><br />' ))
	"""