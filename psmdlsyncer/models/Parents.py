"""
Every Student data type represents a student.
Does context-specific processing
"""
from psmdlsyncer.models.Entry import Entry
_parent_dict = {}
class ParentFactory:
    """
    PARENTS AS A FIRST CLASS CITIZEN NEEDS TO HAVE DISTINCTIVE BEHAVIOR
    BECAUSE THEY COULD ALSO BE TEACHERS, AND MULTIPLE CHILDREN MEAN WE NEED
    SOME WAY OF PROCESSING THAT CASE
    """
    @classmethod
    def make_parent_from_parent(cls, student):
        if not student.ID in _parent_dict:
            _parent_dict[student.ID] = Parent(student)
            return _parent_dict[student.ID]
        else:
            parent = _parent_dict[student.ID]
            parent.add_child(student)
            return parent
class Parent(Entry):
    """
    DERIVED PRETTY MUCH FROM PROVIDED student OBJECT
    """
    def __init__(self, student):
        self.family_id = student.family_id
        self.kind = 'parent'
        self.add_child(student)
        self.grades = []
        self.homerooms = []
    def add_child(self, child):
        self.grades.append(child.grade)
        self.homerooms.append(child.homeroom)
