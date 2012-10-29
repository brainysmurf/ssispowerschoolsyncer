from utils.DB import DragonNetDBConnection
from utils.Formatter import Smartformatter

class Update(DragonNetDBConnection):
    pass

class Child:
    def __init__(self, student):
        self.username = student.username
        self.idnumber = student.num

    def output(self):
        print('\t' + self.username + '\t' + self.idnumber)

class Children:

    def __init__(self):
        self.children = []

    def add(self, student):
        self.children.append( Child(student) )

    def count(self):
        return len(self.children)

    def output(self):
        for child in self.children:
            child.output()

class Family:

    def __init__(self, family_id):
        self.family_id = family_id
        self.username = ""
        self.emails = []
        self.children = Children()

    def add(self, student):
        self.add_child(student)

    def add_child(self, student):
        for email in student.parent_emails:
            if not email in self.emails:
                self.emails.append(email)
        self.children.add(student)

    def children_count(self):
        return self.children.count()

    def output(self):
        print(self.family_id + " | " + str(len(self.username)) + " | " + ", ".join(self.username))
        newidnumber = "P:"
        newidnumber += ",".join([child.idnumber for child in self.children.children])
        print('\t-> ' + newidnumber)
        self.newidnumber = newidnumber
        self.children.output()

    def post_process(self):
        update = Update()
        
        self.idnumber = "P:"
        self.idnumber += ",".join([child.idnumber for child in self.children.children])
        if self.emails:
            self.email = self.emails[0]
        else:
            self.email = None
        print(self.idnumber)
        result = update.sql("select username from ssismdl_user where idnumber = '{}'".format(self.idnumber))()
        print(result)
        self.username = result[0]

class Families:

    def __init__(self):
        self.families = {}

    def add(self, student):
        family_id = student.num[0:4]
        if not self.contains(family_id):
            self.init(family_id)
        self.add_family(family_id, student)

    def init(self, family_id):
        self.families[family_id] = Family(family_id)

    def contains(self, key):
        return key in list(self.families.keys())

    def add_family(self, family_id, student):
        self.families[family_id].add_child(student)

    def output(self):
        for family in self.families.keys():
            self.families[family].output()

    def output_doubles(self):
        for family in self.families.keys():
            if len(self.families[family].username) > 1:
                self.families[family].output()
