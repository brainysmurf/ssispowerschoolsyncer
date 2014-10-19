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
    autosend.process()
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

    left = MoodleTree()
    right = AutoSendTree()

    DetermineChanges(left, right, MoodleTemplate)

@main.group()
def output():
    """
    Writes various data that is useful for debugging purposes
    """
    pass

@output.command()
@click.argument('path_to_output', metavar='PATH_TO_OUTPUT <file>')
@click.argument('user_id', metavar='USER_ID <int>')
@click.argument('group_id', metavar='GROUP_ID <int>')
def student_emails(path_to_output, user_id, group_id):
    from psmdlsyncer.settings import config, config_get_section_attribute
    from psmdlsyncer.sql import MoodleDBSession

    path_to_powerschool = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')

    db = MoodleDBSession()

    with open(path_to_output, 'w') as _file:
        for student in db.users_enrolled_in_this_cohort('studentsALL'):
            _file.write('{},{},{}\n'.format(student.idnumber, student.username, student.email))

    import os
    os.chown(path_to_output, int(user_id), int(group_id))


@output.group()
def bulk_emails():
    pass

@bulk_emails.command()
def usebccparentsHOMEROOM():
    from psmdlsyncer.models.datastores.autosend import AutoSendTree
    autosend = AutoSendTree()
    autosend.process()
    autosend.output_parent_bulk_emails()