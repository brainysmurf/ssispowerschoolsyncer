import Students

if __name__ == "__main__":

    students = Students()

    list_of_groups = []
    for key in students.get_student_keys():
        student = students.get_student(key)
        groups = student.groups()
        for group in groups:
            if not group in list_of_groups:
                list_of_groups.append(group)
