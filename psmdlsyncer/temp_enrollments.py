from psmdlsyncer.utils.Bulk import MoodleCSVFile

class Enroll:

    def __init__(self, name, email, firstname, lastname):
        self.username = name
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.courses = []
        self.cohorts = []
        self.c = self.enroll_course

    def enroll_course(self, course):
        if isinstance(course, list):
            self.courses.extend( course )
        else:
            self.courses.append( course )

    def build(self, output_file):
        row = output_file.factory()
        row.build_username(self.username)
        row.build_password('changeme')
        row.build_email(self.email)
        row.build_firstname(self.firstname)
        row.build_lastname(self.lastname)
        row.build_course_(self.courses)
        row.build_type_( ['3' for c in self.courses] )
        output_file.add_row(row)


if __name__ == "__main__":

    output_file = MoodleCSVFile()
    output_file.build_headers(['username', 'password', 'email', 'firstname', 'lastname', 'course_', 'type_'])

    sub = Enroll('substituteteacher', 'noone@example.com', 'Substitute', 'Teacher')
    sub.c( ['STDSKL9', 'DRAMA9', 'SCIEN7', 'SCIEN6', 'ARMUSSH1112', 'CHIA10', 'ENGA2SH1112', 'STDSWA10', 'CAREERSH1112', 'CAREERSH1112', 'SCIEN9', 'SCIEN8', 'GERA10', 'HUMAN6', 'CHIA1SH1112', 'GERLLSH1112', 'CHILLSH1112', 'CHILLSH1112', 'ARTS9', 'LBCHISH1112', 'LBCHISH1112', 'ENVHONSH1112', 'SSHISSH1112', 'IBTOKSH1112', 'IBTOKSH1112', 'SSHISSH1112', 'SCIWA10', 'ENGI9', 'ENGI8', 'ENGI7', 'ENGI6', 'ARVISSH1112', 'ARMUSSH1112', 'SSENVSH1112', 'CHILLSH1112', 'GBSHSDSH1112', 'CHILLSH1112', 'TECOM10', 'LBSPASH1112', 'HROOM8', 'ENGA1SH1112', 'GERLISH1112', 'ARMUS10', 'GERLISH1112', 'LBCHIASH1112', 'ENGLLSH1112', 'ENGLLSH1112', 'LBCHIASH1112', 'GERA9', 'GERA8', 'DRAMA10', 'KORA1SH1112', 'SSENVSH1112', 'SSECOSH1112', 'SSECOSH1112', 'KORLISH1112', 'KORLISH1112', 'ARTS7', 'ARTS8', 'MATST6', 'SCBIOSH1112', 'ARTS6', 'KORA10', 'MATSU8', 'GRAHSDSH1112', 'MATST7', 'HUMAN10', 'MATST8', 'MATST9', 'MASTUS12', 'CHIA2SH1112', 'ENGBF8', 'LBENGSH1112', 'CHIA9', 'ENGBA10', 'CHIBA10', 'TECOM9', 'SSGEOSH1112', 'ARTHESH1112', 'CHIA8', 'GERLLSH1112', 'SSGEOSH1112', 'MAAPPHS1', 'LIBRASH1112', 'ARTSWA10', 'LIBRASH1112', 'ARMUS9', 'ENBAWA10', 'CHIA7', 'CHIA6', 'MASTUS11', 'MASTUS12', 'ARTS10', 'KORA9', 'LBSPASH1112', 'SSHISSH1112', 'SSHISSH1112', 'LBSPASH1112', 'ENGLISH1112', 'ENGLISH1112', 'JAPA1SH1112', 'KORA7', 'ENGA2SH1112', 'SSPSYSH1112', 'SCBIOSH1112', 'SCBIOSH1112', 'KORA8', 'LBENGSH1112', 'LBENGSH1112', 'SSBAMSH1112', 'TEMAT10', 'ENGA1SH1112', 'TECOMSH1112', 'PHYED10', 'SSENVSH1112', 'SSPHYHS1', 'ENGBS9', 'ENGLISH1112', 'ENGLISH1112', 'LBCHISH1112', 'LIBRA9', 'MASTUS12', 'JAPLISH1112', 'PEHEAH1112', 'MASTUS11', 'JAPLISH1112', 'LIBRA00', 'GERLLSH1112', 'SSGEOSH1112', 'SSGEOSH1112', 'LBSPASH1112', 'GERLISH1112', 'GERLISH1112', 'SSPSYSH1112', 'ARGRAHS1', 'SPAB6', 'ENGBS7', 'JAPA8', 'JAPA9', 'CHIBF10', 'TEDESSH1112', 'CHILLSH1112', 'JAPA6', 'JAPA7', 'SPAB8', 'SPAB9', 'PHYED9', 'PHYED8', 'ARVISSH1112', 'JAPLISH1112', 'PHYED7', 'PHYED6', 'DESIG10', 'GERLLSH1112', 'KORA1SH1112', 'ENGA10', 'TEDESSH1112', 'CHILISH1112', 'ARVISSH1112', 'ARVISSH1112', 'CHILISH1112', 'MATSU9', 'LBENGSH1112', 'CHIBF9', 'CHIBF8', 'ARCERHS1', 'KORLISH1112', 'KORLISH1112', 'ARVISSH1112', 'TECOMSH1112', 'TECOMSH1112', 'SCBIOSH1112', 'ENGBF7', 'ENGBF6', 'CHIBF7', 'CHIBF6', 'SSBAMSH1112', 'LBSPAASH1112', 'SSBAMSH1112', 'IBCAS1112', 'IBCAS1112', 'SPAB10', 'JAPLISH1112', 'MATEX9', 'SCBIOSH1112', 'MASTAS12', 'MASTAS11', 'JAPA10', 'CHILISH1112', 'PEHEAHS1', 'CHIBA8', 'CHILISH1112', 'CHIBS6', 'CHIBS7', 'SSASIHS1', 'TEDESSH1112', 'CHIBS8', 'CHIBS9', 'SCIEN10', 'ENGA6', 'LBENGSH1112', 'LBENGSH1112', 'ENGLLSH1112', 'ENGA2SH1112', 'TEFOO9', 'ENGA9', 'ARGRA9', 'SSPHYSH1112', 'SSPHYSH1112', 'XSTUDYSH1112', 'XSTUDYSH1112', 'SPAB7', 'SSPSYSH1112', 'TEDESSH1112', 'DANLISH1112', 'SSPSYSH1112', 'JAPLISH1112', 'ENGLLSH1112', 'ARVISSH1112', 'KORA6', 'MATEX10', 'SCBIOSH1112', 'ENGLLSH1112', 'MATSU10', 'TECOMSH1112', 'TECOMSH1112', 'HUMAN8', 'LBENGHS2', 'LBENGHS1', 'ENGBS8', 'CHIBS10', 'ARTHESH1112', 'ENGBS6', 'ARTHESH1112', 'MATSU7', 'ENGA7', 'MATSU6', 'TEFOO10', 'TEMAT9', 'ARMUSSH1112', 'HUMAN9', 'STDSKL10', 'SSECOSH1112', 'SSECOSH1112', 'DESIG7', 'DESIG6', 'SCCHESH1112', 'SSBAMSH1112', 'LBSPAASH1112', 'DESIG9', 'SSBAMSH1112', 'LASELSH1112', 'SCCHESH1112', 'SSBIOHS1', 'GERA1SH1112', 'DESIG8', 'TEFOOHS1', 'CHILLSH1112', 'SSPHYSH1112', 'LBCHISH1112', 'LBCHISH1112', 'SSPHYSH1112', 'ENBSWA10', 'ARTHESH1112', 'HROOM9', 'MAHIGH11', 'HROOM6', 'HROOM7', 'LBCHISH1112', 'LBCHISH1112', 'ENGBS10', 'ENGBA6', 'ENGBA7', 'MAAPPHS2', 'ENGLLSH1112', 'HUMAN7', 'SSPSYSH1112', 'CHIBA9', 'SSECOSH1112', 'TEDESSH1112', 'ENGBA8', 'ENGBA9', 'CHIBA6', 'KORLISH1112', 'KORLISH1112', 'ENGA8', 'GERA7', 'MASTAS11', 'MASTAS12', 'LBSPAASH1112', 'MAHIGH12', 'LIBHSDSH1112', 'SCCHESH1112', 'SCCHESH1112', 'ENGI10', 'ARMUSSH1112', 'SSAMEHS1', 'MATST10', 'CHIBA7', 'LBSPASH1112', 'GERA6', 'FREB6', 'HROOMSH1112', 'HROOMSH1112', 'HROOM10'] )

    sub.build(output_file)

    patrick = Enroll('tapritter@yahoo.com', 'tapritter@yahoo.com', 'Patrick', 'Ritter')
    patrick_s = Enroll('mypvisitor', 'noone@example.com', 'MYP', 'Visitor')
    stephen = Enroll('stephen.keegan@ibo.org', 'stephen.keegan@ibo.org', 'Stephen', 'Keegan')
    stephen_s = Enroll('dpvisitor', 'noone@example.com', 'DP', 'Visitor')

    c = ['PERSPROJ', 'MYPCURRIC', 'PUBCURRIC',
               'COREDOCS', 'TEACHLEARN', 'TEACHPROCED', 'STUDPROCED',
               'ARTDEPART', 'CASDEPT', 'CHINADEPART', 'CHINBDEPART',
               'COUNSDEPT', 'DEPTDESIGN', 'ENGADEPART', 'ENGBDEPART',
               'HUMANDEPART', 'MATHDEPART', 'PEDEPART', 'DEPTSCIENCE',
               'TOKDEPARTMENT', 'WLDEPARTMENT', 'PARPOLICY', 'LOSTFOUND',
               'KORPAR', 'PARENTCURRIC', 'Probe', 'PASTORAL', 'COLLCOUNS',
               'HUMAN8', 'SCIEN9', 'ENGBS7', 'ENGBA10', 'CHIA8', 'CHIBA6', 'KORA10',
               'MATST7', 'PHYED10','DESIG6', 'ARTS6', 'MYPARTSDOCS', 'MYPCHINA', 'MYPCHINB','MYPDESIGNDOCS',
               'MYPENGLISHDOCSA', 'MYPENGLISHDOCB', 'MYPFRENCHDOC', 'MYPGERMANDOCS', 'MYPHUMADOCS', 'MYPJAPDOC',
               'MYPKOREANDOC', 'MYPMATHCURDOCS','MYPPECURDOCS', 'MYPSCIENCECURDOCS','MYPSPANISH']

    patrick.c( c )
    patrick_s.c ( c )

    patrick.build(output_file)
    patrick_s.build(output_file)

    c = ['DPHSDWLCURRIC', 'DPHSDCHINCURRIC', 'DPHUMANDOCS', 'DPDESIGNCURDOCS',
               'DPARTSCURDOCS', 'DPSCIENCECURDOCS', 'DPENGCURDOCS', 'DPPECURDOCS', 'DPMATHCURDOCS','COUNSDEPT','TOKDEPARTMENT'
               'ARTDEPART', 'CASDEPT', 'CHINADEPART', 'CHINBDEPART',
               'COUNSDEPT', 'DEPTDESIGN', 'ENGADEPART', 'ENGBDEPART',
               'HUMANDEPART', 'MATHDEPART', 'PEDEPART', 'DEPTSCIENCE',
               'TOKDEPARTMENT', 'WLDEPARTMENT','EXTENDESSAYT', 'EXTENDESSAY', 
        ]
    
    stephen.c( c )
    stephen_s.c( c )
    stephen.build(output_file)
    stephen_s.build(output_file)

    print(output_file.output())

