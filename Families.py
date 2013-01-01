from utils.DB import DragonNetDBConnection
from utils.Formatter import Smartformatter

class Update(DragonNetDBConnection):
    pass

class Children:

    def __init__(self):
        self.children = []

    def add(self, student):
        self.children.append( student )

    def count(self):
        return len(self.children)

    def output(self):
        for child in self.children:
            child.output()

    def __str__(self):
        return ", ".join([child for child in self.children])

    def __iter__(self):
        self.iter_item = 0
        return self

    def __next__(self):
        if self.iter_item < len(self.children):
            item = self.iter_item
            self.iter_item += 1
            return self.children[item]
        else:
            raise StopIteration

class Family:

    def __init__(self, family_id):
        self.family_id = family_id
        self.username = ""
        self.emails = []
        self.parent_account_id = family_id + 'P'
        self.children = Children()

    def __str__(self):
        return "Family\n:Family ID: {}, Username: {}\nChildren:\n{}".format(self.family_id,
                                                                  self.username, ", ".join([str(student) for student in self.children]))

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
        """
        Returns True if post_process was successful
        """
        update = Update()
        
        if self.emails:
            # Use the second email, dammit, because that's usually the mother
            if len(self.emails) > 1:
                self.email = self.emails[1]
            else:
                self.email = self.emails[0]
        else:
            self.email = None
        id_number = self.family_id + 'P'
        result = update.sql("select username from ssismdl_user where idnumber = '{}'".format(id_number))()
        if result:
            self.username = result[0]
        else:
            self.username = self.email
            
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

    def __str__(self):
        return "\n".join(str([family for family in self.families]))
