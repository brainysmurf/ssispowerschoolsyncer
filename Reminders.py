from utils.DB import DragonNetDBConnection
from Students import Students
from utils.Email import Email

class Connect(DragonNetDBConnection):

    def __init__(self):
        super().__init__()
        self.students = Students()

    def list_parents_not_activated(self):
        return self.sql("select username, idnumber from ssismdl_user where idnumber like '%P' and lastlogin = 0")()

    def get_students(self, idnumber):
        result = []
        for student_key in self.students.get_student_keys():
            student = self.students.get_student(student_key)
            if student.family_id == str(idnumber):
                result.append(student)
        return result

    def get_emails(self, students):
        result = []
        for student in students:
            for email in student.parent_emails:
                if not email in result:
                    result.append(email)
        if not result:
            print("Parent with these kids don't have email address\n{}?".format(students))
        return result

    def username_not_registered_email(self, parent_emails, username):
        return not username in parent_emails

    def notify(self, my_children, parent_emails):
        email = Email()
        "TODO"
        return

    def change_username(self, idnumber, new_username):
        self.sql("update ssismdl_user set username = '{}' where idnumber = '{}'".format(new_username, idnumber))
        self.sql("update ssismdl_user set email = '{}' where idnumber = '{}'".format(new_username, idnumber))
        self.sql("update ssismdl_user set lastname = '{}' where idnumber = '{}'".format(new_username, idnumber))

    def process(self):
        for parent in self.list_parents_not_activated():
            username, idnumber = parent
            my_children = self.get_students(idnumber)
            if not my_children:
                print("Student has left!")
                print(parent)
                print()
                continue
            parent_emails = self.get_emails(my_children)
            
            if self.username_not_registered_email(parent_emails, username):
                if not parent_emails:
                    print("Parent does not have emails!", username, idnumber)
                    print()
                else:
                    print("Parent has unregistered email!", username, idnumber)
                    if len(parent_emails) > 1:
                        new_username = parent_emails[1]
                    else:
                        new_username = parent_emails[0]
                    print("Using this one instead!: ", new_username)
                    self.change_username(idnumber, new_username)
                    print()

            self.notify(my_children, parent_emails)

if __name__ == "__main__":

    connect = Connect()

    connect.process()
