comma="&#44"  # moodle knows this is a comma
exclude = ['PEHEAH', 'MAHIGH', 'IBCAS']

import re, os
import random
random.seed()

on_server = os.path.exists('/home/lcssisadmin')

course_reference = {'LBENGHS2': ' 1052', 'ARVHONSH1112': ' 1235', 'MATSU10': ' 1097', 'testingtesting': '  209', 'GERA7': ' 1151', 'GERA8': ' 1152', 'GERA9': ' 1150', 'PEDEPART': ' 1306', 'HROOM9': ' 1074', 'MYPPECURDOCS': ' 1225', 'HUMAN10': ' 1162', 'CAREERSH1112': ' 1157', 'PARENTS': ' 1206', 'GERLISH1112': ' 1030', 'ENGLISH7ALL': ' 1261', 'GERA1SH1112': ' 1067', 'DPDESIGNCURDOCS': ' 1234', 'CHINADEPART': ' 1316', 'LIBRASH1112': ' 1093', 'ARTHESH1112': ' 1024', 'TEACHGUID': ' 1272', 'COUNSCORN': ' 1269', 'HROOM8': ' 1073', 'TECOM10': ' 1080', 'TECOMSH1112': ' 1079', 'COUNSELORS': ' 1205', 'DESIG10': ' 1120', 'KORA10': ' 1114', 'TEMAT10': ' 1173', 'SCIEN10': ' 1164', 'MYPSPANISH': ' 1293', 'HROOM10': ' 1060', 'XSTUDYSH1112': ' 1188', 'LBSPASH1112': ' 1096', 'ACTIVITIES': ' 1221', 'ROBOTICS': ' 1270', 'LBSPAASH1112': ' 1166', 'PHYED6': ' 1109', 'ENGBA6': ' 1039', 'MYPCURRIC': ' 1274', 'ENGA6': ' 1198', 'ENGA7': ' 1196', 'ARMUSSH1112': ' 1023', 'SSASIHS1': ' 1147', 'ENGA8': ' 1197', 'ENGA9': ' 1195', 'ENGI8': ' 1028', 'MYPARTSDOCS': ' 1219', 'Student Issues': ' 1224', 'STAFFINFO': ' 1212', 'SCIEN8': ' 1168', 'SCIEN9': ' 1165', 'SCIEN6': ' 1170', 'SSHISSH1112': ' 1037', 'SCBIOSH1112': ' 1056', 'DEPTSCIENCE': ' 1213', 'ENGI9': ' 1034', 'GBSHSDSH1112': ' 1277', 'MATST10': ' 1135', 'ENGBS9': ' 1094', 'ENBSWA10': ' 1191', 'ENGI6': ' 1026', 'ENGI7': ' 1029', 'SSPHYSH1112': ' 1101', 'JAPA10': ' 1057', 'JAPA7': ' 1068', 'JAPA6': ' 1069', 'DANLISH1112': ' 1243', 'SCIEN7': ' 1167', 'ARCERHS1': ' 1058', 'DPHUMANDOCS': ' 1258', 'IBCAS1112': ' 1022', 'ENGHONSH1112': ' 1245', 'CHIBF8': ' 1046', 'CHIBF9': ' 1076', 'GERLLSH1112': ' 1020', 'ENBAWA10': ' 1280', 'JAPA9': ' 1070', 'KORPAR': ' 1264', 'MASTUS11': ' 1281', 'MASTUS12': ' 1282', 'CHILLSH1112': ' 1019', 'PARENTCURRIC': ' 1223', 'LIBHSDSH1112': ' 1244', 'CHIBS10': ' 1043', 'DRAMA10': ' 1283', 'MYPDESIGNDOCS': ' 1226', 'ARTS10': ' 1180', 'GRADE5': ' 1210', 'HROOMSH1112': ' 1059', 'ENVHONSH1112': ' 1236', 'PEHEAH1112': ' 1148', 'CHIA9': ' 1129', 'DPMATHCURDOCS': ' 1232', 'CHIA10': ' 1134', 'GRAHSDSH1112': ' 1246', 'ENGA10': ' 1193', 'MYPMATHCURDOCS': ' 1227', 'KORLISH1112': ' 1090', 'MYPCHINB': ' 1298', 'SSPHYHS1': ' 1087', 'HUMANDEPART': ' 1310', 'MYPCHINA': ' 1297', 'ARTS7': ' 1172', 'ARTS6': ' 1174', 'LASELSH1112': ' 1199', 'PERSPROJ': ' 1260', 'ENGBA8': ' 1042', 'Staff Association': '  417', 'ENGI10': ' 1040', 'Cover': ' 1201', 'ARTS9': ' 1169', 'ARTS8': ' 1171', 'SSGEOSH1112': ' 1061', 'SANDBOX': ' 1215', 'MYPENGLISHDOCB': ' 1299', 'MATEX9': ' 1161', 'TEMAT9': ' 1181', 'DPARTSCURDOCS': ' 1233', 'PHYED10': ' 1116', 'ARGRAHS1': ' 1066', 'DESIG8': ' 1144', 'DESIG9': ' 1142', 'DEPTDESIGN': ' 1275', 'HEADSOFGRADES': ' 1222', 'DESIG6': ' 1146', 'DESIG7': ' 1145', 'LBENGSH1112': ' 1063', 'CHIA7': ' 1125', 'MYPJAPDOC': ' 1302', 'ARTDEPART': ' 1317', 'MATST7': ' 1121', 'MAHIGH1112': ' 1115', 'MATST6': ' 1122', 'DRAMA9': ' 1286', 'SSPSYSH1112': ' 1158', 'ENGBS8': ' 1092', 'DPSCIENCECURDOCS': ' 1231', 'SSBAMSH1112': ' 1128', 'PUBCURRIC': ' 1294', 'ENGBDEPART': ' 1313', 'ENGLISH8ALL': ' 1265', 'KORDEPART': ' 1308', 'FREB6': ' 1279', 'CHIA6': ' 1140', 'MYPHUMADOCS': ' 1257', 'MATSU6': ' 1102', 'ARVISSH1112': ' 1032', 'ENGBS7': ' 1088', 'ENGBS6': ' 1086', 'HROOM7': ' 1077', 'CHILISH1112': ' 1072', 'CHIA8': ' 1127', 'ENGLLSH1112': ' 1025', 'MATST8': ' 1119', 'CHIBF6': ' 1050', 'ENGBA10': ' 1027', 'SPANDEPART': ' 1305', 'CHIBF7': ' 1044', 'CHIA2SH1112': ' 1078', 'PEHEAHS1': ' 1159', 'GRADE1': ' 1207', 'GRADE3': ' 1209', 'GRADE2': ' 1211', 'PARPOLICY': ' 1271', 'MASTUSH1112': ' 1113', 'ARTSWA10': ' 1055', 'MASTASH1112': ' 1021', 'GERA10': ' 1085', 'LBCHISH1112': ' 1153', 'ARGRA9': ' 1064', 'GRADE4': ' 1208', 'CHIBA9': ' 1187', 'CHIBA8': ' 1186', 'TEACHERNOTICES': ' 1259', 'TECOM9': ' 1083', 'GERMANDEPART': ' 1311', 'STDSKL9': ' 1123', 'DPPECURDOCS': ' 1229', 'CHIBA7': ' 1185', 'CHIBA6': ' 1184', 'JAPA8': ' 1071', 'HOMEROOM6T': ' 1319', 'CHIBA10': ' 1179', 'ARMUS9': ' 1285', 'COLLCOUNS': ' 1268', 'CHIBF10': ' 1062', 'DPENGCURDOCS': ' 1230', 'HUMAN9': ' 1176', 'HUMAN8': ' 1175', 'HUMAN7': ' 1178', 'HUMAN6': ' 1177', 'GERA6': ' 1155', 'TEFOO10': ' 1160', 'PHYED8': ' 1111', 'PHYED9': ' 1112', 'LBENGHS1': ' 1053', 'MYPENGLISHDOCSA': ' 1220', 'IBTOKSH1112': ' 1194', 'KORA6': ' 1126', 'LOOKUP': ' 1304', 'STDSWA10': ' 1141', 'SPAB7': ' 1136', 'SPAB6': ' 1137', 'SPAB9': ' 1098', 'SPAB8': ' 1099', 'TEFOO9': ' 1084', 'SCIWA10': ' 1189', 'CHIBS9': ' 1051', 'CHIA1SH1112': ' 1190', 'MATHDEPART': ' 1307', 'CHIBS8': ' 1049', 'SANDBOX3': ' 1217', 'SANDBOX2': ' 1216', 'TEACHSUPGUID': ' 1218', 'MYPGERMANDOCS': ' 1301', 'STDSKL10': ' 1139', 'JAPA1SH1112': ' 1138', 'MATSU7': ' 1107', 'COUNSDEPT': ' 1296', 'NurseStation': ' 1200', 'TEDESSH1112': ' 1095', 'TEACHTS': ' 1262', 'MATSU8': ' 1108', 'MATSU9': ' 1105', 'ENGA1SH1112': ' 1192', 'SSBIOHS1': ' 1104', 'SSAMEHS1': ' 1149', 'MATEX10': ' 1154', 'FRENCHDEPART': ' 1312', 'ENGHUM6ALL': ' 1263', 'SPAB10': ' 1106', 'MYPKOREANDOC': ' 1303', 'ADMINISTRATION': ' 1266', 'SCCHESH1112': ' 1183', 'ENGBA7': ' 1038', 'ENGADEPART': ' 1314', 'SPIHONSH1112': ' 1292', 'ARMUS10': ' 1288', 'SSENVSH1112': ' 1131', 'LOSTFOUND': ' 1267', 'ENGBA9': ' 1041', 'SECSTUNOTICES': ' 1203', 'LIBRA00': ' 1081', 'MAAPPHS1': ' 1089', 'MAAPPHS2': ' 1091', 'LBCHIASH1112': ' 1048', 'CHINBDEPART': ' 1315', 'ENGLISH1112': ' 1054', 'MYPSCIENCECURDOCS': ' 1228', 'JAPLISH1112': ' 1156', 'PHYED7': ' 1110', 'KORA1SH1112': ' 1065', 'MYPFRENCHDOC': ' 1300', 'TEACHLEARN': ' 1273', 'MATHCLUB': ' 1318', 'MATST9': ' 1117', 'HROOM6': ' 1075', 'MASTAS11': ' 1289', 'MASTAS12': ' 1290', 'TEFOOHS1': ' 1143', 'CHIBS7': ' 1047', 'CHIBS6': ' 1045', 'KORA8': ' 1130', 'KORA9': ' 1118', 'ENGA2SH1112': ' 1082', 'KORA7': ' 1132', 'DNETFAQTEACH': ' 1204', 'Probe': ' 1202', 'LIBRA9': ' 1276', 'SPORTS': ' 1214', 'JAPDEPART': ' 1309', 'DragonNet': '    1', 'ENGBF6': ' 1031', 'ENGBF7': ' 1033', 'TEST': '  841', 'ENGBS10': ' 1100', 'ENGBF8': ' 1035', 'SSECOSH1112': ' 1036', 'MASHONSH1112': ' 1256'}

depart_dict = {
	'hro': 'departHROOM',
	'maa': 'departMATH',
	'mas': 'departMATH',
	'mat': 'departMATH',
	'mah': 'departMATH',
	'kor': 'departWL',
	'chi':'departCHI',
	'cnb':'departCHI',
	'ger': 'departWL',
	'lbc': 'departWL',
	'lbs': 'departWL',
	'jap': 'departWL',
	'spi':'departWL',
	'dan':'departWL',
	'spa': 'departWL',
	'spb':'departWL',
	'fre':'departWL',
	'lib':'departLIB',
	'arm': 'departARTS',
	'art': 'departARTS',
	'arv': 'departARTS',
	'arc': 'departARTS',
	'dra': 'departARTS',
	'arg': 'departARTS',
	'hum': 'departHUM',
	'eco':'departHUM',
	'psy':'departHUM',
	'sse': 'departHUM',
	'env':'departHUM',
	'ssh': 'departHUM',
	'ssg': 'departHUM',
	'ssb': 'departHUM',
	'ssa': 'departHUM',
	'com':'departDESIGN',
	'gra':'departDESIGN',
	'tec': 'departDESIGN',
	'hon':'departDESIGN',
	'las': 'departENGLISH',
	'lbe': 'departENGLISH',
	'eng': 'departENGLISH',
	'enb': 'departENGLISH',
	'sci': 'departSCIENCE',
	'bio':'departSCIENCE',
	'scb': 'departSCIENCE',
	'ssp': 'departSCIENCE',
	'ssc': 'departSCIENCE',
	'scc': 'departSCIENCE',
	'phy': 'departPE',
	'phe': 'departPE',
	'peh': 'departPE',
	'tef': 'departDESIGN',
	'des': 'departDESIGN',
	'tem': 'departDESIGN',
	'ted': 'departDESIGN',
	'gra': 'departDESIGN',
	'tok':'departTOK',
	'ibt':'departTOK',
	'std':'departTOK',
	'xst':'departOTHERS',
	'car':'departCAR',
	'ibc':'departCAS'}

department_email_names = {
	'departHUM':'humanitiesdepartment',
	'departARTS':'artsdepartment',
	'departTOK':'tokdepartment',
	'departHROOM':'homeroomteachers',
	'departSCIENCE':'sciencedepartment',
	'departENGLISH':'englishdepartment',
	'departLIB':'librarydepartment',
	'departPE':'pedepartment',
	'departWL':'worldlanguagesdepartment',
	'departTOK':'tokdepartment',
	'departDESIGN':'designdepartment',
	'departCHI':'chinesedepartment',
	'departMATH':'mathsdepartment',
 	}

department_heads = {
	# Make lists in case there are multiple needs
	'departMATH': ['garypost'],
	'departWL':   ['reneerehfeldt'],
	'departARTS': ['brettnugent', 'heidimesser'],
	'departHUM': ['jarrettbrown', 'donpreston'],
	'departENGLISH': ['lauralynnstefureak', 'ingridmorton'],
	'departPE': ['mitchhyde'],
	'departSCIENCE': ['bryandennie'],
	'departDESIGN': ['patricelder'],
	'departCHI': ['rebeccaruan'],
	'departCAS': ['santinagambrill'],
	'departHROOM': ['peterfowles']
	}

def determine_password():
	s = 'abcdefghjklmnopqrtuvwxyz'  # no s or i
	p = "".join([random.choice(s) for i in range(0,4)])  # four random letters
	return "ssiS1!" + p

def derive_depart(course):
	course = course[:3]
	depart = depart_dict.get(course.lower())
	if depart:
		return depart
	else:
		pass
	#print("unknown department")
	#print("\t{}".format(course))
	return None

def derive_departments(courses):
	results = []
	for course in courses:
		depart = derive_depart(course)
		if depart:
			results.append(depart)
	d = {}
	for x in results:
		d[x] = 1
	return list(d.keys())














def map_codes(short, grade, higher_lower):
	"""
	Meeting department needs requires an elaborate mapping system applied to some courses
	This routine meets those needs
	"""
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
		
		# Straight conversions
		'ENLHONSH1112': 'ENGLLSH1112',  # English A Lang & Lit
		'ENGHONSH1112': 'LBENGSH1112',  # English B
		'CNLHONSH1112': 'CHILLSH1112',  # Chinese
		'CNBHONSH1112': 'LBCHISH1112',  # Mandarin
		'KRLHONSH1112': 'KORLISH1112',  # Korean
		'CNIHONSH1112': 'LBCHISH1112',  # Chinese ab initio
		'ARVHONSH1112': 'ARVISSH1112',  # Visual Arts
		'JPLHONSH1112': 'JAPLISH1112',   # Japanese
		'SPBHONSH1112': 'LBSPASH1112',  # Spanish
		'SPIHONSH1112': 'LBSPAASH1112', # spanish ab initio

		'PSYHONSH1112': 'SSPSYSH1112', # Psychology
		'ECOHONSH1112': 'SSECOSH1112', # Economics
		'BAMHONSH1112': 'SSBAMSH1112', # Business & Management

		'COMHONSH1112': 'TECOMSH1112', # Computer Science
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
		'MAHIGH12': "IB Mathematics HL (12"

		}.get(short)

def convert_short_long(short, long):
	# First do blanket conversions
	short = re.sub(r'[^a-zA-Z0-9]', '', short)    # take out nonalpha
	short = re.sub(r'0([1-9]+)$', '\\1', short)   # take out leading zeroes
	grade = re.sub(r'[^0-9]+', '', short)         # get the grade
	short = short.replace('_', '')

        # Decision: We want our IB Diploma and HS Diploma courses to be collapsed
        # into the same shared course page.
        # The following logic ensures that by adjusting the short and long name.
        # This works because in powerschool the only difference in name and ID is
        # their ending.
	grade11n12 = r'(.*)(11|12)$'
	standard_higher = None   # we need to know which standard and higher later
	if re.match(grade11n12, short):
		short = re.sub(grade11n12, '\\1',   short)
		if not short in exclude:
			# Take out the last S (standard) or H (high)
			standard_higher = re.sub(r'.*([SH])$', '\\1', short)
			if standard_higher == short:
				# special case where a course code looks like it's an IB course
				# doesn't have a standard or higher level indicator
				# checking with head of maths, he says you can assume standard level
				standard_higher = "S"
			short = re.sub(r'(.*)[SH]$', '\\1', short)
			short += 'SH1112'
		else:
			# But don't take them out for specific courses
			standard_higher = re.sub(r'.*([SH])$', '\\1', short)
			short += '1112'
		long  = re.sub(r'(.*)\(1[12]\)', '\\1 (11/12)', long).strip()
		long  = long.replace(" SL ", " SL/HL").replace(" HL ", " SL/HL").replace('  ', ' ').replace(',', comma)


	short = map_codes(short, grade, standard_higher)
	change = map_codes_names(short)
	if change:
		long = change
	return short, long


def no_whitespace_all_lower(base):
	return re.sub(r'[^a-z]', '', base.replace(' ', '').lower())


class Categories:
	def __init__(self, shortname):
		self.declare()
		shortname = shortname.lower()[:3]
		self._s = self.__dict__[shortname] if shortname in self.__dict__.keys() else ""

	def __str__(self):
		return self._s

	def declare(self):
		wl = "World Languages"
		ch = "Chinese"
		at = "Arts"
		hm = "Humanities"
		en = "English"
		sc = "Science"
		lb = "Others"
		ma = "Math"
		pe = "Physical Education"
		ds = "Design"
		ss = "Others"
		tk = "Others"
		self.maa = self.academics(ma)
		self.mas = self.academics(ma)
		self.mat = self.academics(ma)
		self.mah = self.academics(ma)
		self.hmr = self.homeroom()
		self.chi = self.academics(ch)
		self.kor = self.academics(wl)
		self.ger = self.academics(wl)
		self.lbc = self.academics(wl)
		self.lbs = self.academics(wl)
		self.jap = self.academics(wl)
		self.spa = self.academics(wl)
		self.fre = self.academics(wl)
		self.dan = self.academics(wl)
		self.ibc = self.academics("Others")
		self.arm = self.academics(at)
		self.art = self.academics(at)
		self.arv = self.academics(at)
		self.arc = self.academics(at)
		self.dra = self.academics(at)
		self.arg = self.academics(at)
		self.hum = self.academics(hm)
		self.sse = self.academics(hm)
		self.ssh = self.academics(hm)
		self.ssg = self.academics(hm)
		self.ssb = self.academics(hm)
		self.ssa = self.academics(hm)
		self.tec = self.academics(ds)
		self.las = self.academics(en)
		self.lbe = self.academics(en)
		self.eng = self.academics(en)
		self.enb = self.academics(en)
		self.sci = self.academics(sc)
		self.scb = self.academics(sc)
		self.ssp = self.academics(sc)
		self.ssp = self.academics(sc)
		self.ssc = self.academics(sc)
		self.scc = self.academics(sc)
		self.env = self.academics(sc)
		self.lib = self.academics(lb)
		self.phy = self.academics(pe)
		self.phe = self.academics(pe)
		self.peh = self.academics(pe)
		self.tef = self.academics(ds)
		self.des = self.academics(ds)
		self.tem = self.academics(ds)
		self.ted = self.academics(ds)
		self.gra = self.academics(ds)
		self.std = self.academics(ss)
		self.ibt = self.academics(tk)
		self.car = self.academics("Others")
		self.xst = self.academics(ss)
		self.hro = self.academics("Others")
		self.lib = self.academics("Others")

	def homeroom(self):
		return "Homeroom"

	def academics(self, code):
		return "Teaching & Learning / {0}".format(code)


def put_in_order(what):
    trans = {'L':1,'E':2,'A':3,'R':4,'N':5,'S':6,'SWA':7}
    if '6' in what:
        result = 100 + trans[re.sub('[0-9]', '', what)]
    elif '7' in what:
        result =  200 + trans[re.sub('[0-9]', '', what)]
    elif '8' in what:
        result =  300 + trans[re.sub('[0-9]', '', what)]
    elif '9' in what:
        result =  400 + trans[re.sub('[0-9]', '', what)]
    elif '10' in what:
        result = 500 + trans[re.sub('[0-9]', '', what)]
    elif '11' in what:
        result = 600 + trans[re.sub('[0-9]', '', what)]
    elif '12' in what:
        result = 700 + trans[re.sub('[0-9]', '', what)]
    return result


if __name__ == "__main__":

	print('new one')
	courses = os.listdir('/home/helpdesk/groups/classes')
	catch = []
	for course in courses:
		short, long = convert_short_long(course, "")
		catch.append(short)

	print
	print(catch)
	print

	raw = open('/home/powerschool/courseinfosec').readlines()
	catch = []
	courses = []
	for r in raw:
		courses.append(r.strip('\n').split('\t')[0])	
	catch = []
	for course in courses:
		short, long = convert_short_long(course, "")
		print(short)
		catch.append(course)

	print()
	print(catch)
	print()
	print(derive_departments(catch))
	
