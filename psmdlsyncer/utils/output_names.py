from psmdlsyncer.Tree import Tree
students = Tree()

results = []

for student_key in students.get_student_keys():
    student = students.get_student(student_key)

    if student.grade in range(8, 11) and student.is_SWA:
        pe_teacher = [item[1] for item in student.teachers().items() if item[0].startswith('PHYED')]
        try:
            pe_teacher = pe_teacher[0]
        except IndexError:
            print("This student doesn't have a PE teacher? {0}".format(student))
            print(student.teachers())
            pe_teacher = "None"
        results.append("{0.first} {0.last}\t{0.homeroom}\t{pe_teacher}\n".format(student, pe_teacher=pe_teacher))

print(sorted(results))

with open('output.txt', 'w') as f:
    for student in sorted(results):
        f.write(student)
