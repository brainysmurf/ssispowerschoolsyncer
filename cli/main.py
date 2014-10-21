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
def notices(date=None):
    """
    Manage and launch the Student and Teacher notices stuff
    """
    pass

@notices.group()
def student():
    """
    Commands for maipulating and launching student notices
    """
    pass

@student.command()
@click.option('--date', help="the date that we are pretending to be; default is today")
@click.option('--date_offset', default='0', help="Adjust accordingly to specific needs; default=0", metavar='<INT>')
def output(date=None, date_offset=None):
    import time, datetime
    if date:
        # If we are explicitely passed date, then use that
        time_object = time.strptime(date, "%b %d %Y")
        date_object = datetime.date(
            month=time_object.tm_mon,
            day=time_object.tm_mday,
            year=time_object.tm_year
            )
    else:
        # Calculate the date we need by date_offset
        date_object = datetime.date.today() + datetime.timedelta(days=int(date_offset))
    
    from psmdlsyncer.notices.StudentNotices import Student_Notices
    notices = Student_Notices(date_object)
    notices.format_for_email()
    notices.print_email([])

@student.command()
@click.option('--date', help="the date that we are pretending to be; default is today")
@click.option('--date_offset', default='0', help="Adjust accordingly to specific needs; default=0", metavar='<INT>')
@click.option('--email/--no_email', default=False, help="Email them or not (requires smtp server of course)")
@click.option('--edit_email/--no_edit_email', default=False, help="Email to some agent an email with edit links")
@click.option('--output/--no_output', default=False, help="Output to stdout?")
@click.option('--update_date_fields/--dont_update_date_fields', default=False, help="Output to stdout?")
def launch(date=None, date_offset=None, email=False, edit_email=False, output=False, update_date_fields=False):
    import time, datetime
    if date:
        # If we are explicitely passed date, then use that
        time_object = time.strptime(date, "%b %d %Y")
        date_object = datetime.date(
            month=time_object.tm_mon,
            day=time_object.tm_mday,
            year=time_object.tm_year
            )
    else:
        # Calculate the date we need by date_offset
        date_object = datetime.date.today() + datetime.timedelta(days=int(date_offset))
    
    from psmdlsyncer.notices.StudentNotices import Student_Notices
    notices = Student_Notices(date_object)

    if email:
        notices.email_to_agents()

    if edit_email:
        notices.email_editing = True
        notices.email_to_agents()

    if output:
        notices.print_email([])

    if update_date_fields:
        notices.update_date_fields()

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