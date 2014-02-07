from psmdlsyncer.sql import MoodleImport
from psmdlsyncer.models.moodle_datastore import MoodleTree

class Moodle(MoodleTree):
    """
    """
    klass = MoodleImport
    convert_course = False   # do not convert course short, because Moodle's contents are already converted

    def __sub__(self, other):
        """
        Looks at the differences in groups
        """
        # This should happen first before things like students are added so in case there are groups to add
        # They do get deleted but then added again as per below

        super().__sub__(self, other)

