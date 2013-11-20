from psmdlsyncer.Tree import Tree
from psmdlsyncer.utils import NS
from psmdlsyncer.settings import define_command_line_arguments
args = define_command_line_arguments(format='{lastfirst}{SPACE}({num})')
tree = Tree()
# TODO: Need to output an example for ease of use

output = []
print('idnumber,username,fullname,shortname,category,backup')
for student in tree.students():
    print(student)
    if student.is_secondary:
        ns = NS(student)
        print(ns('{ID}{COMMA}{username}{lastfirst}{COMMA}OLP{ID}{COMMA}"Invisible / Online Portfolios"{COMMA}backup-moodle2-course-1489-olptemplate-20131101-1225.mbz'))
