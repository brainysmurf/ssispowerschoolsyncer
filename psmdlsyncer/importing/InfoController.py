from psmdlsyncer.importing.Information import AutoSend   # adjust this to Tree later
class InfoController(AutoSend):
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
        for item in self.tree.students:
            yield self.tree.students[item]
    @property
    def parents(self):
        for item in self.tree.parents:
            yield self.tree.parents[item]
    @property
    def secondary_students(self):
        for person in self.tree.students:
            student = self.tree.students[student]
            if student.is_secondary:
                yield student
    def get_any_startswith(self, id):
        return [person for person in self.tree.ALL \
                if hasattr(person, 'ID') and person.ID.startswith(id)]
if __name__ == "__main__":
    klass = InfoController()
    for parent in klass.parents:
        if parent.number_courses != parent.number_groups:
            for person in klass.get_any_startswith(parent.ID[:4]):
                print(person)
            input()
