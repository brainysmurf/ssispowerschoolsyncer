"""

Print out a list of courses and what they map to

"""
from psmdlsyncer.utils.TextFileReader import TextFileReader, AbstractInterfaceClass
from psmdlsyncer.utils.Utilities import convert_short_long
from psmdlsyncer.utils.DB import DragonNetDBConnection

class Course(AbstractInterfaceClass):
    pass

class All:

    def __init__(self):
        self.db = {}

    def get(self, item, default=None):
        return self.db.get(item, default)

    def items(self):
        return list(self.db.keys())

    def add(self, course):
        id_str = course.short_after
        if not id_str in self.db.keys():
            self.db[id_str] = []
        self.db[id_str].append(course)

if __name__ == "__main__":

    courses = TextFileReader('../powerschool/ssis_courseinfoall',
                             interface_class=Course)
    all_courses = All()

    for course in courses.generate():
        after_conversion = convert_short_long(course.course_number, course.course_name)
        course.short_after, course.long_after = after_conversion
        all_courses.add(course)

    with open('../output/course_output.txt', 'w') as f:
        f.write('shortname\t' + 'idnumber\t' + 'summary\n')
        for short in all_courses.items():
            course_list = all_courses.get(short)
            id_string = ",".join([course.course_number for course in course_list])
            f.write(short + '\t' + short + '\t' + id_string + '\n')
