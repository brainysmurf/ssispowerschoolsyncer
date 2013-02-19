from utils.PythonMail import send_html_email
from Students import Students
from utils.DB import DragonNetDBConnection


def send_reminders(students):
    database = DragonNetDBConnection()

    check_kind = {'never attempted':
    {sql:"select id, idnumber, username from ssismdl_user where deleted = 0 and lastlogin = 0 and lastaccess = 0",
     message:"you have never attempted to login"},
    'tried but failed':
    {sql:"select id, idnumber, username from ssismdl_user where deleted = 0 and lastlogin = 0 and lastaccess <> 0",
     message:"you have tried to login but were unsucessful"}
     }

    for kind in check_kind.keys():
        
        accounts = self.sql(
            check_kind[kind]['sql']
            )()

        for account in accounts:
            id, idnumber, username = account
            if idnumber.endswith('P'):
                # Parent Account, derive all the emails to send them
                to_who = students.get_family_emails(idnumber)
                body = parentremind_html.format(
                    records=check_kind[kind]['message'],
                    username=username
                    )

                print(check[kind])
                print('\t' + to_who)
            
            elif idnumber.isdigit():
                # Holy shit a student hasn't used it yet???

                to_who = 'lcssisadmin@student.ssis-suzhou.net'
                body = "This student {}, {} ".format(student.username, student.idnumber) + check_kind[kind]

                print(body)

if __name__ == "__main__":

    students = Students()

    send_reminders(students)
