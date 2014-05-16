from psmdlsyncer.models.datastores.autosend import AutoSendTree
from psmdlsyncer.settings import define_command_line_arguments
from psmdlsyncer.settings import config

if __name__ == "__main__":


    inspect = False  # make this a command line argument

    right = AutoSendTree()

    for person in right.get_everyone():
        for custom_profile = person.get_custom_profile_recor
