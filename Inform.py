from utils.Email import Email
from utils.Email import read_in_templates
from utils.Formatter import Smartformatter
from utils.PythonMail import send_html_email

def inform_admin(admin_email):
    pass

def reinform_new_parent(family):
    pass

def inform_new_student(family, student, server='localhost'):
    student_email_templates = read_in_templates('../templates/student_new_account')
    sender = '"DragonNet Admin" <lcssisadmin@student.ssis-suzhou.net>'
    sf = Smartformatter()
    sf.take_dict(student)
    email = Email(server)
    email.define_sender('lcssisadmin@student.ssis-suzhou.net', "DragonNet Admin")
    email.use_templates(student_email_templates)
    email.make_subject(sf("New Student in Homeroom {homeroom}, {lastfirst}"))
    homeroom_teacher = student.get_homeroom_teacher()
    if homeroom_teacher:
          email.add_to(homeroom_teacher)
    for family_email in family.emails:
          email.add_to(family_email)
    for class_teacher in student.get_teachers_as_list():
          email.add_to(class_teacher + '@ssis-suzhou.net')
    if student.grade in [11, 12]:
          email.add_cc('santinagambrill@ssis-suzhou.net')
          email.add_cc('matthewmarshall@ssis-suzhou.net')
    elif student.grade in [6, 7, 8, 9, 10]:
          email.add_cc('aubreycurran@ssis-suzhou.net')
    email.define_fields(sf)
    email.add_bcc('lcssisadmin@student.ssis-suzhou.net')
    email.add_bcc('brentclark@ssis-suzhou.net')
    email.add_bcc('geoffreyderry@ssis-suzhou.net')
    email.send()
    
def inform_new_parent(family, server='localhost'):
    """
    family is object
    """
    parent_email_templates = read_in_templates(
        '../templates/parent_new_account'
        )
    email = Email(server)
    email.define_sender('lcssisadmin@student.ssis-suzhou.net', "DragonNet Admin")
    email.use_templates(parent_email_templates)
    email.make_subject("Your SSIS DragonNet Parent Account")
    for family_email in family.emails:
        email.add_to(family_email)
    for student in family.children:
        if student.is_korean:
            email.add_language('kor')
        if student.is_chinese:
            email.add_language('chi')
    email.add_bcc('lcssisadmin@student.ssis-suzhou.net')
    email.define_field('username', family.email)
    email.define_field('salutation', 'Dear Parent')
    email.send()
        