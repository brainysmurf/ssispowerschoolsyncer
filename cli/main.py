import click
from psmdlsyncer.settings import config

class Object:
    def __init__(self):
        pass
        
    # define common methods here

#
# Define global options here
#
@click.group()
@click.pass_context
def main(ctx):
    # Doesn't do much now, but leave it as boilerplate for when there are global flags n such
    ctx.obj = Object()

@main.group()
@click.argument('which', metavar="<student> or <teacher>")
@click.option('--date_offset', default='1', help="1 for tomorrow, -1 for yesterday; default=1", metavar='<INT>')
@click.option('--_date', help="Useful for debugging; today if not passed", metavar="<MM DD YYYY>")
@click.pass_obj
def notices(obj, which, _date=None, date_offset=None):
    """
    Manage and launch the Student and Teacher notices stuff
    """
    obj.student_notices = 'student' in which
    obj.teacher_notices = 'teacher' in which

    # first calc and setup _date stuff
    import time, datetime
    if _date:
        # If we are explicitely passed date, then use that
        time_object = time.strptime(_date, "%b %d %Y")
        date_object = datetime.date(
            month=time_object.tm_mon,
            day=time_object.tm_mday,
            year=time_object.tm_year
            )
    else:
        # Calculate the date we need by date_offset
        date_object = datetime.date.today() + datetime.timedelta(days=int(date_offset))

    if obj.student_notices:
        from psmdlsyncer.notices.StudentNotices import Student_Notices
        obj.notices = Student_Notices(date_object)
    elif obj.teacher_notices:
        from psmdlsyncer.notices.TeacherNotices import Teacher_Notices
        obj.notices = Teacher_Notices(date_object)
    else:
        click.echo('Bad Argument: Pass me either "teacher" or "student"')
        exit()

@notices.command()
def output():
    obj.notices.print_email([])

@notices.command()
@click.option('--email/--no_email', default=False, help="Email them or not (requires smtp server of course)")
@click.option('--edit_email/--no_edit_email', default=False, help="Email to some agent an email with edit links")
@click.option('--output/--no_output', default=False, help="Output to stdout?")
@click.option('--publish/--dont_publish', default=False, help="Goes to group-sec-all and elem-sec-all")
@click.option('--update_date_fields/--dont_update_date_fields', default=False, help="Output to stdout?")
@click.pass_obj
def launch(obj, email=False, edit_email=False, output=False, publish=False, update_date_fields=False):
    """
    Runs the student notices
    """
     
    if email:
        if publish:
            obj.notices.email_editing = False
            obj.notices.agent_map = {
                'group-sec-all@ssis-suzhou.net':['Whole School', 'Secondary', 'Elementary'],
                'group-es-all@ssis-suzhou.net':['Whole School', 'Elementary', 'Secondary']
                }

        obj.notices.email_to_agents()

    if edit_email:
        obj.notices.email_editing = True
        obj.notices.email_to_agents()

    if output:
        obj.notices.print_email([])

    if update_date_fields:
        obj.notices.update_date_fields()

@notices.command()
@click.option('--url', default=None, help="The URL for the WordPress site; default is to use settings.ini")
@click.option('--multisite/--not_multisite', default=True, help="Is the WP blog multisite or not?")
@click.option('--blog', default=None, help="If --multisite, then requires blog param")
@click.option('--author', default=None, help="Username of the author to use")
@click.option('--hour', default='immediately', help="Schedule the blog post this way", metavar='<H:M>')
@click.pass_obj
def post_to_wordpress(obj, url=None, multisite=True, blog=None, author=None, hour='immediately'):
    if multisite and not blog:
        click.secho('Multisite requires the blog parameter')
        exit()

    if hour == 'immediately':
        click.secho('Must have an hour argument', fg='red') #TODO
        exit()
    else:
        import time
        when = time.strptime(hour, '%H:%M')

    if not author:
        click.secho('Must send author argument', fg='red')
        exit()

    obj.notices.post_to_wordpress(url, blog, author, when)

@main.command()
@click.option('--inspect/--dont_inspect', default=False, help="Reads in and debug prompt")
@click.option('--output', type=click.File(mode='w'), default=None, help="Output differences to text file")
@click.pass_obj
def launch(obj, inspect=False, output=None):
    """
    Launch syncer stuff
    """
    import socket
    hostname = socket.gethostname()
    if 'dragonnet' in hostname:
        from psmdlsyncer.models.datastores.moodle import MoodleTree
        from psmdlsyncer.models.datastores.autosend import AutoSendTree
        from psmdlsyncer.syncing.templates import MoodleTemplate
        from psmdlsyncer.syncing.differences import DetermineChanges

        # To get the groups right we need to process AutosendTree first and send it over to Moodle
        # FIXME: groups should be the same!

        right = AutoSendTree()
        right.process()
        left = MoodleTree()
        left.groups.section_maps = {v:k for k, v in right.groups.section_maps.items()}  # items become the keys
        left.process()

        d = DetermineChanges(left, right, MoodleTemplate)

        if output:
            for item in d.subtract():
                output.write(str(item))
                output.write('\n')
            exit()
        if inspect:
            from IPython import embed
            embed()
            exit()
        d.go()

    elif 'student' in hostname:
        from psmdlsyncer.models.datastores.autosend import AutoSendTree
        autosend = AutoSendTree()
        autosend.process()
        autosend.build_automagic_emails(make_new_students=True)
        autosend.output_all_aliases()
        autosend.run_newaliases()

    else:
        print("Can't run, is the hostname wrong?")

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
@click.option('--subbranch', help="<students> or <teachers> or ...")
@click.option('--attribute', help="which attribute of the branch")
@click.option('--value', help="the value of the key in the branch")
@click.argument('which', default="both", metavar="<autosend> or <moodle> or <both>")
def dragonnet_user(which, subbranch=None, attribute=None, value=None, **kwargs):
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

    if not subbranch:
        subbranch = click.prompt("Enter subbranch are looking for: ", default='students')
    if not attribute:
        attribute = click.prompt("Enter the attribute you are looking for: ", default="idnumber")
    if not value:
        value = click.prompt("Enter the value you are looking for: ")

    autosend_item = getattr(autosend, subbranch).get_from_attribute(attribute, value) if autosend else None
    moodle_item = getattr(moodle, subbranch).get_from_attribute(attribute, value) if moodle else None
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
            if student.idnumber and student.username and student.email:
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
def output_bulk_email_json():
    from psmdlsyncer.models.datastores.autosend import AutoSendTree
    autosend = AutoSendTree()
    autosend.process()
    autosend.build_automagic_emails()
    autosend.output_json()

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

