"""
Every Student data type represents a student.
Does context-specific processing
"""
from psmdlsyncer.models.Entry import Entry
from psmdlsyncer.utils import NS
_parent_dict = {}
def object_already_exists(key):
    return key in _parent_dict
class ParentFactory:
    """
    PARENTS AS A FIRST CLASS CITIZEN NEEDS TO HAVE DISTINCTIVE BEHAVIOR
    BECAUSE THEY COULD ALSO BE TEACHERS, AND MULTIPLE CHILDREN MEAN WE NEED
    SOME WAY OF PROCESSING THAT CASE
    SO WE USE A FACTORY CLASS WITH A SINGLE CLASS METHOD
    """
    @classmethod
    def make(cls, student):
        """
        IF THE PARENT CLASS HAS ALREADY BEEN CREATED, PROCESSES AND RETURNS THAT
        OTHERWISE, MAKES A NEW ONE
        """
        if not object_already_exists(student.family_id):
            _parent_dict[student.family_id] = Parent(student)
            return _parent_dict[student.family_id]
        else:
            parent = _parent_dict[student.family_id]
            parent.add_child(student)
            return parent
class Parent(Entry):
    """
    DERIVED PRETTY MUCH FROM PROVIDED student OBJECT
    """
    def __init__(self, student):
        """ SETS COMMON ATTRIBUTES, CALLS add_child """
        self.family_id = student.family_id
        self.ID = student.family_id
        self.kind = 'parent'
        self.grades = []
        self._emails = []
        self.homerooms = []
        self.children = []
        self.courses = []
        self.groups = []
        self.teachers = []
        self.add_child(student)
    def add_child(self, child):
        """ SET ATTRIBUTES THAT DEPEND ON child HERE """
        self.children.append(child.ID)
        self.grades.append(child.grade)
        self._emails.extend(child.parent_emails)
        self.homerooms.append(child.homeroom)
    def add_course(self, course):
        if course.ID not in self.courses:
            self.courses.append(course.ID)
    def add_group(self, group):
        if group.ID not in self.groups:
            self.groups.append(group.ID)
    def add_teacher(self, teacher):
        if teacher.ID not in self.teachers:
            self.teachers.append(teacher.ID)
    @property
    def emails(self):
        return list(set(self._emails))
    @property
    def number_courses(self):
        return len(self.courses)
    @property
    def number_groups(self):
        return len(self.groups)
    def __repr__(self):
        ns = NS()
        ns.homerooms = " ".join(self.homerooms)
        ns.emails = ", ".join(self.emails)
        ns.parents_of = "Parents of " + ", ".join(self.children)
        ns.family_id = self.family_id
        ns.ID = self.ID
        ns.homerooms = "(" + ", ".join(self.homerooms) + ")"
        ns.courses = "{} courses".format(len(self.courses))
        ns.groups = "{} groups".format(len(self.groups))
        return ns("{firstrow}{ID}: {emails}, {parents_of} {homerooms}{midrow}" \
                  "{courses}{midrow}{groups}{lastrow}{NEWLINE}",
                                  firstrow="+ ",
                                  midrow="\n| ",
                                  lastrow="\n| ")
