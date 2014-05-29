from psmdlsyncer.models.datastores.postfix import PostfixTree
from psmdlsyncer.models.datastores.autosend import AutoSendTree
from psmdlsyncer.syncing.differences import DetermineChanges

if __name__ == "__main__":

    left = PostfixTree()

    left.process()
