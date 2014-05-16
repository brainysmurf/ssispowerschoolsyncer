from psmdlsyncer.models.datastores.tree import AbstractTree
from psmdlsyncer.files import AutoSendImport
from psmdlsyncer.models.datastores.branch import DataStore



class AutoSendTree(AbstractTree):
    pickup = DataStore
    klass = AutoSendImport
    convert_course = True

    def process_mrbs_editor(self):
        for teacher in self.teachers.get_objects():
            self.mrbs_editor.make(teacher.ID)
