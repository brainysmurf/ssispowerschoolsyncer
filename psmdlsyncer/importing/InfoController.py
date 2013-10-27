from psmdlsyncer.importing.Information import AutoSend, Moodle   # adjust this to Tree later
class InfoController(Moodle):
    """
    PROVIDES HIGHER LEVEL ROUTINES THAN AVAILABLE IN TREE
    """
    @property
    def families(self):
        pass

    def get_family_emails(self, family_id):
        parent = self.tree.family

    @property
    def groups(self):
        """ TODO: LOOK INSIDE ENROLLMENTS """
        pass

    @property
    def grades(self):
        """ TODO: students? """
        pass

    @property
    def students(self):
        for student in self.tree.students:
            yield self.tree.students[student]

    @property
    def teachers(self):
        for teacher in self.tree.teachers:
            yield self.tree.teachers[teacher]

    @property
    def parents(self):
        for parent in self.tree.parents:
            yield self.tree.parents[parent]

    @property
    def secondary_students(self):
        for person in self.tree.students:
            student = self.tree.students[student]
            if student.is_secondary:
                yield student

    def get_any_startswith(self, id):
        return [person for person in self.tree.ALL \
                if hasattr(person, 'ID') and person.ID.startswith(id)]

    def get_one(self, id):
        """ RETURN THE ONE THAT HAS ID == ID """
        for person in self.tree.ALL:
            if person.ID == id:
                return person

    def student_from_ID(self, id):
        """ RETURN THE ONE THAT HAS ID == ID """
        return self.tree.students.get(id)
if __name__ == "__main__":
    klass = InfoController()
    for parent in klass.parents:
        if parent.number_courses != parent.number_groups:
            for person in klass.get_any_startswith(parent.ID[:4]):
                print(person)
            input()
