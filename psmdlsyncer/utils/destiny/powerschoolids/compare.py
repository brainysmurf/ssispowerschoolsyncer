import csv
from psmdlsyncer.Tree import Tree
everyone = Tree()
import re

student_keys = everyone.get_student_keys()
teacher_keys = everyone.get_teacher_keys()

def extract_powerschoolid(possible):
	regexp = '^(F|P|A) ?([0-9]{5})'
	result = re.match(regexp, possible)
	if result:
		return result.group(2)
	else:
		return False

def name_matches(person, firstname, lastname):
	a = person.first + person.last
	b = firstname + lastname
	a = re.sub('[^a-z]', '', a.lower())
	b = re.sub('[^a-z]', '', b.lower())
	return a == b

with open('patron_data_all.txt', 'rU', encoding='mac-roman') as _file:
	info = csv.reader(_file)
	first_row = None
	for row in info:
		powerschoolid, _, lastname, firstname, *_ = row
		powerschoolid = extract_powerschoolid(powerschoolid)
		if not powerschoolid:
			# check for name
			pass
		else:

			if powerschoolid in student_keys:
				student = everyone.get_student(powerschoolid)
				if not name_matches(student, firstname, lastname):
					print(lastname + ', ' + firstname + ' != ' + student.last + ', ' + student.first)
				else:
					pass
					#print(lastname + ', ' + firstname + ': {} -- found as student'.format(powerschoolid))

			elif lastname + ', ' + firstname in teacher_keys:
				teacher = everyone.get_teacher(lastname+ ', '+firstname)
				if teacher.num != powerschoolid:
					print(lastname + ', ' + firstname + ' powerschool should be {} NOT {}'.format(teacher.num, powerschoolid))
				else:
					pass
					#print(lastname + ', ' + firstname + ': {} -- found as teacher'.format(powerschoolid))
			else:
				found = everyone.find_student_by_name(firstname, lastname)
				if found:
					pass
					#print(found.num + ' ...' + lastname + ', ' + firstname + ': {} -- found by name as STUDENT '.format(powerschoolid))
				else:
					found = everyone.find_teacher_by_name(firstname, lastname)
					if found:
						pass
						#print(found.num + ' ...' + lastname + ', ' + firstname + ': {} -- found by name as TEACHER'.format(powerschoolid))
					else:
						print(lastname + ', ' + firstname + ': {} -- NOT FOUND'.format(powerschoolid))
