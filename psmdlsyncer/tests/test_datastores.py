from psmdlsyncer.models.datastores.moodle import MoodleTree
from psmdlsyncer.models.datastores.autosend import AutoSendTree
from psmdlsyncer.syncing.templates import MoodleTemplate
from psmdlsyncer.syncing.differences import DetermineChanges

if __name__ == "__main__":

    inspect = False  # make this a command line argument

    left = MoodleTree()
    right = AutoSendTree()

    if inspect:
        from IPython import embed
        embed()

    DetermineChanges(left, right, MoodleTemplate)
