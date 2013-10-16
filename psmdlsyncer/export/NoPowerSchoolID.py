from psmdlsyncer.Tree import Tree
from psmdlsyncer.utils import NS
from psmdlsyncer.settings import define_command_line_arguments
args = define_command_line_arguments(format='{lastfirst}{SPACE}({num})')
tree = Tree()
# TODO: Need to output an example for ease of use

def notlegal(psID):
    if not psID.isdigit():
        return True
    if not len(psID) == 5:
        return True
    if int(psID) < 30000:
        return True
    return False

output = []
for teacher_key in tree.get_teacher_keys():
    teacher = tree.get_teacher(teacher_key)
    ns = NS(teacher)
    if teacher.status == 1 and notlegal(teacher.num):
        print(ns('{lastfirst}{TAB}{num}'))
