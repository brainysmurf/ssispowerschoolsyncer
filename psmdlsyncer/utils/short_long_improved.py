import re
exclude = ['PEHEAH', 'MAHIGH', 'IBCAS']
comma="&#44"
grade11n12 = re.compile(r'(11|12)$')
eleven_twelve = re.compile(r'(11|12)')	

def map_codes(short, grade, higher_lower):
	"""
	Meeting department needs requires an elaborate mapping system applied to some courses
	This routine meets those needs
	"""
	print('start {}'.format(short))
	grade = str(grade)
	higher_lower = str(higher_lower)
	if higher_lower == "H" and short.startswith('H'):
		input(higher_lower)
	result = {
		# MATHS DEPT needs certain things at the IB level
		# From head of department:
		#Hon Math SL/HL (11/12) can be removed. It is used to distinguish those students taking the IB exam. The course is exactly the same as Maths SL
		#Mathematics Applications (11) should be rewritten as HSD Mathematics Applications (11)
		#In Place of the 2 same named courses (IB Mathematics SL/HL (11/12)) We need; IB Mathematics SL (11), IB Mathematics SL (11), IB Mathematics HL (11) and IB Mathematics HL (12). Making this distinction is very important. The G11 and G 12 cohorts are large, the courses and IA's are different, and we submit course specific information to the IB on line
		#In place of IB Maths Studies SL/HL (11/12) there should be IB Maths Studies SL (11) and IB Maths Studies SL (12). For the same reason as above. There is no HL course for Studies Hon Math Studies (11/12) can be removed. It is used to distinguish those students taking the IB exam. The course is exactly the same as Maths Studies.

		# Convert hon maths studies to maths studies, respecting H/L, grade divisions
		'MADHONSH1112': 'MASTUS'+grade,
		'MASHONSH1112': 'MASTAS'+grade,
		# Divide IB maths by H/L, grade
		'MASTASH1112':  'MASTA'+higher_lower+grade,
		# Divide maths studies by H/L, grade
		'MASTUSH1112':  'MASTU'+higher_lower+grade,

		'MAHIGH1112': 'MAHIGH'+grade,

		# SWA Study Skills are really just learning support stuff
		'STUDYSWA10': 'STDSKL10',
		'STUDYSWA9': 'STDSKL9',
		'STUDYSWA9': 'STDSKL08',
        'STUDYSWA9': 'STDSKL07',
		'STUDYSWA9': 'STDSKL9',
        
		'ENBSWA9': 'ENGBA9',
		'ENBSWA8': 'ENGBA8',
		'ENBSWA7': 'ENGBA7',
		'ENBSWA6': 'ENGBA6',
		'ENBSWA10': 'ENGBA10',
		
		# Straight conversions
		'ENLHONSH1112': 'ENGLLSH1112',  # English A Lang & Lit
		'ENGHONSH1112': 'LBENGSH1112',  # English B
		'CNLHONSH1112': 'CHILLSH1112',  # Chinese
		'CNBHONSH1112': 'LBCHISH1112',  # Mandarin
		'KRLHONSH1112': 'KORLISH1112',  # Korean
		'KORLISH11': 'KORLISH1112', # Korean Hons
		'CNIHONSH1112': 'LBCHISH1112',  # Chinese ab initio
		'ARVHONSH1112': 'ARVISSH1112',  # Visual Arts
		'JPLHONSH1112': 'JAPLISH1112',   # Japanese
		'SPBHONSH1112': 'LBSPASH1112',  # Spanish
		'SPIHONSH1112': 'LBSPAASH1112', # spanish ab initio

		'PSYHONSH1112': 'SSPSYSH1112', # Psychology
		'ECOHONSH1112': 'SSECOSH1112', # Economics
		'BAMHONSH1112': 'SSBAMSH1112', # Business & Management

		'COMHONSH1112': 'TECOMSH1112', # Computer Science
		'ENVHONSH1112': 'SSENVSH1112', # Environmental Systems, one course
		
		'HONTEDSH1112': 'TEDESSH1112', # Design Technology
		'CNBHONSH1112': 'LBCHISH1112', # Chinese
		
		
		'BIOHONSH1112': 'SCBIOSH1112'   # Biology honors

						 #'DESIG9': 'GRAPHICDESIGN9',
						 #'DESIG10': 'GRAPHICDESIGN10'   TECOM10, TECOM9 deleted, TECOMSH1112 becomes TECOM1112CLARK, TEFOO9 TEFOO10 have been killed, TEMAT10 & 9 have been killed, TEFOOHS1 has been killed (and probably never ran)
		
		
		# 

	}.get(short)

	if not result:
		return short
	return result

def map_codes_names(short):

	return {
		'MASTAS11': "IB Mathematics SL (11)",
		'MASTAS12': "IB Mathematics SL (12)",
		
		'MASTUS11': "IB Math Studies SL (11)",
 		'MASTUH11': "IB Math Studies HL (11)", # doesn't exist though
		'MASTUS12': "IB Math Studies SL (12)",
		'MASTUH12': "IB Math Studies HL (12)",  # doesn't exist though

		'MAHIGH11': "IB Mathematics HL (11)",
		'MAHIGH12': "IB Mathematics HL (12)"

		}.get(short)

def convert_short_long(short, long):

	# First do blanket conversions
	short = re.sub(r'[^a-zA-Z0-9]', '', short)    # take out nonalpha
	short = re.sub(r'0([1-9]+)$', '\\1', short)   # take out leading zeroes
	grade = re.sub(r'[^0-9]+', '', short)         # get the grade
	print('grade is {}'.format(grade))
	short = short.replace('_', '')

        # Decision: We want our IB Diploma and HS Diploma courses to be collapsed
        # into the same shared course page.
        # The following logic ensures that by adjusting the short and long name.
        # This works because in powerschool the only difference in name and ID is
        # their ending.
	standard_higher = None   # we need to know which standard and higher later
	if grade11n12.search(short):
		print('grade11n12 yes')
		short = re.sub(grade11n12, '', short)
		if not short in exclude:
			# Determine standard or higher
			standard_higher = short[-1]
			if not (standard_higher == 'S' or standard_higher == "H"):
				# special case where a course code looks like it's an IB course
				# doesn't have a standard or higher level indicator
				# we can assume "standard"
				standard_higher = "S"
			# Now we can just tack on the standard to the end
			short += 'SH1112'
		else:
			print('specific course')
			# But don't take them out for specific courses
			standard_higher = short[-1]
			short += '1112'
		long  = eleven_twelve.sub('11/12', long)
		long  = long.replace(",", comma).replace('  ', ' ')

	print(standard_higher)
	print('before map code', short)
	short = map_codes(short, grade, standard_higher)
	print('after map code', short)
	change = map_codes_names(short)
	if change:
		long = change
	return short, long


if __name__ == "__main__":


	courses = [
	('MASHON11', 'Maths Honors something'),
	('SSBIOHS1', 'I dunno'),
	('MATAS12', "Mathematics Amazing (12)"),
	('ENGA__11', 'English for Adults (11)'),
	('PYISCI_08', 'Physical Science 8')
	]

	for short, long in courses:
		print('start {} {}'.format(short, long))
		short, long = convert_short_long(short, long)
		print('end {} {}'.format(short, long))		