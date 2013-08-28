from psmdlsyncer.Students import Students
from psmdlsyncer.utils.Formatter import Smartformatter

from settings import config_get_section_attribute

students = Students()

results = []

for student_key in students.get_student_keys():
    student = students.get_student(student_key)
    if not student.is_secondary:
        continue
    if student.grade == 12:
        continue
    sf = Smartformatter(newline='\n', comma=',', space=" ",
                        left='(', right=')')
    sf.take_dict(student)
    results.append(sf("{homeroom}:{space}{first}{space}{last}{space}{left}{num}{right}{newline}"))

results.sort()

with open(config_get_section_attribute('DIRECTORIES', 'path_to_output') + '/' + 'all_students', 'w') as f:
    for item in results:
        f.write(item)
        
