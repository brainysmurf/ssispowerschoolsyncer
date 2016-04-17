"""

Print out a list of courses and what they map to

"""
#from psmdlsyncer.utils.TextFileReader import AbstractInterfaceClass
from psmdlsyncer.utils.Utilities import convert_short_long
#from psmdlsyncer.db import DragonNetDBConnection

class Course():
    pass

class All:

    def __init__(self):
        self.db = {}

    def get(self, item, default=None):
        return self.db.get(item, default)

    def items(self):
        return list(self.db.keys())

    def add(self, course):
        id_str = course.course_number
        if not id_str in self.db.keys():
            self.db[id_str] = []
        self.db[id_str].append(course)

    def __iter__(self):
        return self.db

if __name__ == "__main__":

    # courses = TextFileReader('../powerschool/ssis_dist_courseinfo_v4.0',
    #                          interface_class=Course)
    all_courses = All()

    with open('../../powerschool/ssis_dist_courseinfo_v4.0') as _file: 
        for line in _file.readlines():
            course = Course()
            course.course_number, course.course_name = line.strip('\n').split('\t')
            course.short_after, course.long_after = convert_short_long(course.course_number, course.course_name)
            all_courses.add(course)

    # for course in all_courses:
    #     after_conversion = convert_short_long(course.course_number, course.course_name)
    #     course.short_after, course.long_after = after_conversion
    #     all_courses.add(course)

    with open('../output/course_output.txt', 'w') as f:
        f.write('ps\t' + 'dn_idnumber\t' + 'summary\n')
        for key in all_courses.items():
            course_list = all_courses.get(key)
            summary = ",".join([c.course_number for c in course_list])
            after = ([c.short_after for c in course_list])
            assert len(after) == 1
            after = after[0]
            f.write(key + '\t' + after + '\t' + summary + '\n')
