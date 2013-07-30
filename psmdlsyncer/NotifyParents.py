from psmdlsyncer.utils.Email import Email

body_html = """
<p>Dear Parent,</p>

<p><a href="http://sites.ssis-suzhou.net/helpdesk/parent-accounts/content-of-email-notification-korean/">Chinese</a>, <a href="http://sites.ssis-suzhou.net/helpdesk/parent-accounts/content-of-email-notification-korean/">Korean</a>.</p>

<p><i>This is an automated message. No reply necessary.</i></p>

<p>As a parent of a child at SSIS, you have been given a login for <b>DragonNet 2</b>. Using this account, you can access information that is made availble to parents and your child's courses. You can also view teacher feedback on specific assignments.</p>

<p>Please <a href="http://dragonnet.ssis-suzhou.net/my">login</a>:</p>

<blockquote><b><pre>Your username is:
{email}

Your password is:
{password}</pre></b></blockquote>

<p>You will need to change your password after logging in. Please note that the password requires at least one non-alphanumeric character.</p>

<p>Here are the features that your parent account provides:</p>

<ul>
<li>You can find the classes in the "Teaching & Learning" tab.</li>
<li>You can find curriculum and other information in the "Parents" tab.</li>
<li>You can find additional information by clicking on your child's name under "My Children".</li>
</ul>

<p>Thank you and kind regards,</p>

<p>SSIS DragonNet Admin Team</p>
"""

if __name__ == "__main__":

    parents = open('/var/www/moodle/admin/cli/new_parents.txt').readlines()

    for parent in [p.strip("\n") for p in parents if p]:

        d = {'email':parent, 'password':'changeme'}
        body_content = body_html.format(**d)

        send_html_email('dragonnethelp@student.ssis-suzhou.net', parent,
                        "Your SSIS Parent Account on DragonNet 2",
                        body_content,
                        ccwho='adammorris@ssis-suzhou.net')
        
