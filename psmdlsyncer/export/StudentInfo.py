from psmdlsyncer.Tree import Tree
from psmdlsyncer.utils import NS
from psmdlsyncer.settings import define_command_line_arguments
args = define_command_line_arguments(format='{lastfirst}{SPACE}({num})')
tree = Tree()
# TODO: Need to output an example for ease of use

output = []
for student_key in tree.get_student_keys():
    student = tree.get_student(student_key)
    if student.is_secondary:
        ns = NS(student)
        print(ns(args.format))
