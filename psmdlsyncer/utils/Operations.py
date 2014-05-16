from psmdlsyncer.models.datastores.autosend import AutoSendTree

if __name__ == "__main__":

    inspect = False  # make this a command line argument

    right = AutoSendTree()

    l = []
    for student in right.students.get_objects():
        if student.is_secondary:
            l.append("{last}, {first} ({idnumber})\n".format(**student.__dict__))

    l.sort()
    with open('results.txt', 'w') as f:
        for item in l:
            f.write(item)
