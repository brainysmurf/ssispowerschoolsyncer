"""
Uses a list to make new accounts
"""

usernames = ['mypcoordinator']

courses_to_enrol = ['KORA10', 'HUMAN10', 'DESIG10', 'SCIEN10', 'HROOM10', 'CHIBF10', 'JAPA10', 'ENBAWA10', 'CHIBS10', 'CHIA10', 'ENGA10', 'PHYED10', 'ENGBA10', 'GERA10', 'ARTS10', 'MATSU10', 'CHIBA10', 'STDSWA10', 'STDSKL10', 'MATEX10', 'SPAB10', 'MATST10', 'ENGBS10']

from ssispowerschoolsyncer.utils.Bulk import MoodleCSVFile

output_file = MoodleCSVFile('/tmp/mypcoordinator.txt')
output_file.build_headers(['username', 'course_', 'type_'])

for username in usernames:
    row = output_file.factory()
    row.build_username(username)
    row.build_course_(courses_to_enrol)
    row.build_type_(['3' for course in courses_to_enrol])
    output_file.add_row(row)

print(output_file.output())
