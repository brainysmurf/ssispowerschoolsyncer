from psmdlsyncer.models.datastores.moodle import MoodleTree
from psmdlsyncer.models.datastores.autosend import AutoSendTree
from psmdlsyncer.syncing.templates import MoodleTemplate
from psmdlsyncer.syncing.differences import DetermineChanges

if __name__ == "__main__":


    left = MoodleTree()
    right = AutoSendTree()

    DetermineChanges(left, right, MoodleTemplate)
