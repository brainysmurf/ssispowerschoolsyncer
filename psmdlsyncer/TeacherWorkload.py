from psmdlsyncer.Students import Students
from psmdlsyncer.utils.Formatter import Smartformatter

class Teachers:

    def __init__(self):
        self._db = {}

    def add(self, teacher):
        if not teacher in self._db.keys():
            self._db[teacher] = 0
        self._db[teacher] += 1

    def total(self):
        return len(list(self._db.keys()))

if __name__ == '__main__':

    class Config:
        verbose = False
        courses = True
        teachers = True
        students = True

    students = Students(Config())
    teachers = Teachers()
    ns = Smartformatter()
    
    for student_key in students.get_student_keys():
        student = students.get_student(student_key)
        for teacher in student.get_teachers_as_list():
            teachers.add(teacher)

    ns.total_load = 0
    teacher_tuples = []
    
    for ns.teacher in teachers._db.keys():
        ns.total_load += teachers._db[ns.teacher]
        teacher_tuples.append( (ns.teacher, teachers._db[ns.teacher]) )


    ns.total_teachers = teachers.total()

    print(ns("Total teachers: {total_teachers}"))

    ns.average_load = ns.total_load / ns.total_teachers
    
    print(ns("Average Load: {average_load}"))

    teacher_tuples.sort(key=lambda x: x[1], reverse=True)

    for ns.teacher, ns.load in teacher_tuples:
        print(ns("{teacher}: {load}"))
