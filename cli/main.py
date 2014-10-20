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
def inspect():
    """
    Look at or confirm DragonNet or Email user information
    """
    pass

@inspect.command()
@click.option('--idnumber', metavar="<PowerSchoolID>", help="For debugging")
@click.option('--username', metavar="<DragonNet Username>", help="For checking on student email server")
@click.option('--path_to_users', default='path_to_users', help="Default is okay, but can be overridden should there be a reason to")
def email_user(path_to_users, username=None, idnumber=None):
    """
    Check to see if user has their account set up or not.
    """
    if path_to_users == 'path_to_users':
        from psmdlsyncer.settings import config_get_section_attribute
        path_to_users = config_get_section_attribute('DIRECTORIES', 'path_to_users')
    import os
    yes = "User has an account in this system"
    no = "User does NOT have an account system"
    _list = os.listdir(path_to_users)
    if idnumber and idnumber in _list:
        click.echo(yes)
        return
    if username and username in _list:
        click.echo(yes)
        return
    click.echo(no)


@inspect.command()
@click.option('--branch', help="<students> or <teachers> or ...")
@click.option('--attribute', help="which attribute of the branch")
@click.option('--value', help="the value of the key in the branch")
@click.argument('which', default="both", metavar="<autosend> or <moodle> or <both>")
def dragonnet_user(which, branch=None, attribute=None, value=None, **kwargs):
    """
    Check out the information that is provided by PowerSchool and compare that to Moodle
    """
    click.echo("Hi there, starting up our syncing software (patience is a virtue).")
    if which.lower() == 'autosend':
        from psmdlsyncer.models.datastores.autosend import AutoSendTree
        autosend = AutoSendTree()
        moodle = None
    elif which.lower() == 'moodle':
        from psmdlsyncer.models.datastores.moodle import MoodleTree
        moodle = MoodleTree()
        autosend = None
    elif which.lower() == 'both':
        from psmdlsyncer.models.datastores.autosend import AutoSendTree
        from psmdlsyncer.models.datastores.moodle import MoodleTree
        moodle = MoodleTree()
        autosend = AutoSendTree()

    click.echo('Begin processing...')
    autosend.process() if autosend else None
    moodle.process() if moodle else None
    click.echo('...done processing.')

    if not branch:
        branch = click.prompt("Enter branch are looking for: ", default='students')
    if not attribute:
        attribute = click.prompt("Enter the attribute you are looking for: ", default="idnumber")
    if not value:
        value = click.prompt("Enter the value you are looking for: ")

    autosend_item = getattr(autosend, branch).get_from_attribute(attribute, value) if autosend else None
    moodle_item = getattr(moodle, branch).get_from_attribute(attribute, value) if moodle else None
    click.echo(autosend_item.output(indent=4, add={'branch':'autosend'})) if autosend_item else None
    click.echo(moodle_item.output(indent=4, add={'branch':'moodle'})) if moodle_item else None

    #click.confirm("Continue?", abort=True)

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
    """
    Output into a file stuff needed for PowerSchool to read in via AutoCom
    """
    from psmdlsyncer.settings import config, config_get_section_attribute
    from psmdlsyncer.sql import MoodleDBSession

    path_to_powerschool = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')

    db = MoodleDBSession()

    with open(path_to_output, 'w') as _file:
        for student in db.users_enrolled_in_this_cohort('studentsALL'):
            _file.write('{},{},{}\n'.format(student.idnumber, student.username, student.email))

    import os
    os.chown(path_to_output, int(user_id), int(group_id))


@main.group()
def bulk_emails():
    """
    Figure out stuff with bulk email system
    """
    pass

@bulk_emails.command()
@click.argument('username', metavar="<DragonNet Username>")
def membership(username):
    from psmdlsyncer.settings import config_get_section_attribute
    from functools import partial
    import os
    # Set up directory and path checks with partials
    path_to_postfix = config_get_section_attribute('DIRECTORIES', 'path_to_postfix', required=True)
    os.chdir(path_to_postfix)
    resolve_this = partial(os.path.join, os.getcwd())

    for this_one in os.listdir('.'):
        full_path = resolve_this(this_one)
        if os.path.isdir(full_path):
            os.chdir(full_path)
            for file_name in os.listdir('.'):
                group, _ = os.path.splitext(file_name)
                with open(os.path.join(os.getcwd(), file_name)) as _file:
                    for line in _file:
                        if username in line:
                            click.echo(group)

@bulk_emails.command()
def usebccparentsHOMEROOM():
    from psmdlsyncer.models.datastores.autosend import AutoSendTree
    autosend = AutoSendTree()
    autosend.process()
    autosend.output_parent_bulk_emails()