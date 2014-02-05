from psmdlsyncer.models.Entry import Entry
from psmdlsyncer.utils import NS
from psmdlsyncer.utils import weak_reference
from psmdlsyncer.models.meta import AbstractFactoryDataStore

class Parents(AbstractFactoryDataStore):
    """
    PARENTS AS A FIRST CLASS CITIZEN NEEDS TO HAVE DISTINCTIVE BEHAVIOR
    BECAUSE THEY COULD ALSO BE TEACHERS, AND MULTIPLE CHILDREN MEAN WE NEED
    SOME WAY OF PROCESSING THAT CASE
    SO WE USE A FACTORY CLASS WITH A SINGLE CLASS METHOD
    """
    @classmethod
    def klass(cls):
        return Parent

class Parent(Entry):
    """
    DERIVED PRETTY MUCH FROM PROVIDED student OBJECT
    """
    kind = 'parent'

    def __init__(self, student):
        """ SETS COMMON ATTRIBUTES, CALLS add_child """
        self.family_id = student.family_id
        self.ID = student.family_id
        self.children = []
        self.add_child(student)

    @property
    def grades(self):
        return [child.grade for child in self.children]

    @property
    def homerooms(self):
        result = []
        for child in self.children:
            this_child = child()
            result.append(this_child.homeroom)
        return set( result )

    @property
    def emails(self):
        result = []
        for child in self.children:
            this_child = child()
            result.extend(this_child.guardian_emails)
        return set(result)

    @property
    def courses(self):
        result = []
        for child in self.children:
            this_child = child()
            result.extend(this_child.courses)
        return set(result)

    @property
    def groups(self):
        result = []
        for child in self.children:
            this_child = child()
            result.extend(this_child.groups)
        return set( result )

    def teachers(self):
        result = []
        for child in self.children:
            this_child = child()
            result.extend(this_child.teachers)
        return result
    def add_child(self, child):
        """ SET ATTRIBUTES THAT DEPEND ON child HERE """
        self.children.append( weak_reference(child) )
    @property
    def children_ids(self):
        result = []
        for child in self.children:
            this_child = child()
            result.append( this_child.ID )
        return result

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
        ns.parents_of = "Parents of " + ", ".join(self.children_ids)
        ns.family_id = self.family_id
        ns.ID = self.ID
        ns.homerooms = "(" + ", ".join(self.homerooms) + ")"
        ns.courses = "{} courses".format(len(self.courses))
        ns.groups = "{} groups".format(len(self.groups))
        return ns("<Parent {ID}: {emails}, {parents_of} {homerooms}>") #{midrow}" \
                  #"{courses}{midrow}{groups}{lastrow}{NEWLINE}",
                  #                firstrow="+ ",
                  #                midrow="\n| ",
                  #                lastrow="\n| ")
