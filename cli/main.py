import click
#from psmdlsyncer.utils.ns import NS2

class Object(object):
    def __init__(self):
        # chance to get setings
        pass

    # define common methods here

#
# Define global options here
#
@click.group()
@click.pass_context
def main(ctx):
    ctx.obj = Object()

@main.group()
def launch():
    """
    Launch syncer stuff
    """
    pass

@launch.command()
@click.pass_obj
def email_server(obj):
    """
    Sets up postfix with bulk email system and student email accounts
    """
    from psmdlsyncer.models.datastores.autosend import AutoSendTree
    autosend = AutoSendTree()
    autosend.build_automagic_emails()

@launch.command()
@click.pass_obj
def dragonnet_server(obj):
    """
    Sets up postfix with bulk email system and student email accounts
    """
    from psmdlsyncer.models.datastores.moodle import MoodleTree
    from psmdlsyncer.models.datastores.autosend import AutoSendTree
    from psmdlsyncer.syncing.templates import MoodleTemplate
    from psmdlsyncer.syncing.differences import DetermineChanges

    DetermineChanges(left, right, MoodleTemplate)

@main.group()
def output():
    """
    Writes various data that is useful for debugging purposes
    """
    pass

@output.group()
def bulk_emails():
    pass

@bulk_emails.command()
def usebccparentsHOMEROOM():
    from psmdlsyncer.models.datastores.autosend import AutoSendTree
    autosend = AutoSendTree()
    autosend.process()
    autosend.output_parent_bulk_emails()