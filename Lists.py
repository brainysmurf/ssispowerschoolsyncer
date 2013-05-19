from Students import Students
from utils.Formatter import Smartformatter

class Config:
    def __init__(self):
        self.students = True
        self.verbose = False
        self.courses = False
        self.teachers = False
        self.output_path = '../output'

config = Config()
students = Students(config)

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
    results.append(sf("{last}{comma}{space}{first}{space}{left}{homeroom}{space}{num}{right}{newline}"))

results.sort()

with open(config.output_path + '/' + 'all_students', 'w') as f:
    for item in results:
        f.write(item)
        
