
from utils.DB import DragonNetDBConnection
from utils.Formatter import Smartformatter

class Update(DragonNetDBConnection):

    def __init__(self):
        self.sf = Smartformatter()
        self.sf.define(user_table='ssismdl_user',
                       _id='id')
        super().__init__()

    def change_idnumber(self, username, idnumber):
        """
        Change the user who lists themselves as having this email address to idnumber
        """
        self.sf.define(username=username, idnumber=idnumber)
        possibles = self.sql( self.sf("select {_id} from {user_table} where username = '{username}'") )()
        if len(possibles) > 1:
            print("Already have a username by that email address")
            return
        elif len(possibles) == 0:
            print("No user by that username!")
            print(username)
            return
        self.sf.define(idnum=possibles[0][0])
        print( self.sf("About to id #{idnum} in table {user_table}, setting its idnumber to {idnumber}") )
        self.sql( self.sf("update {user_table} set idnumber = '{idnumber}' where id = {idnum}") )()


class Child:
    def __init__(self, username, idnumber):
        self.username = username
        self.idnumber = idnumber

    def output(self):
        print('\t' + self.username + '\t' + self.idnumber)

class Children:

    def __init__(self):
        self.children = []

    def add(self, username, idnumber):
        self.children.append( Child(username, idnumber) )

    def count(self):
        return len(self.children)

    def output(self):
        for child in self.children:
            child.output()

class Family:

    def __init__(self, family_id):
        self.family_id = family_id
        self.username = []
        self.children = Children()

    def add(self, username, lastlogin, idnumber, child, childidnumber):
        if not username in self.username:
            self.username.append( username )
        self.lastlogin = lastlogin
        self.idnumber = idnumber
        self.add_child(child, childidnumber)

    def add_child(self, username, idnumber):
        self.children.add(username, idnumber)

    def children_count(self):
        return self.children.count()

    def output(self):
        print(self.family_id + " | " + str(len(self.username)) + " | " + ", ".join(self.username))
        newidnumber = "P:"
        newidnumber += ",".join([child.idnumber for child in self.children.children])
        print('\t-> ' + newidnumber)
        self.newidnumber = newidnumber
        self.children.output()
    

class Families:

    def __init__(self):
        self.families = {}

    def update_table(self):
        updater = Update()
        
        for family in self.families:
            family = self.families[family]
            if not len(family.username) == 1:
                print("More than one username under this dude")
                print(family)
                continue
            family.output()
            updater.change_idnumber(family.username[0], family.newidnumber)

    def add(self, username, lastlogin, idnumber, child, childidnumber):
        family_id = childidnumber[0:4]
        if not self.contains(family_id):
            self.init(family_id)
        self.add_family(family_id, username,
                        lastlogin, idnumber, child, childidnumber)

    def init(self, family_id):
        self.families[family_id] = Family(family_id)

    def contains(self, key):
        return key in list(self.families.keys())

    def add_family(self, family_id, username,
                   lastlogin, idnumber,
                   child, childidnumber):
        self.families[family_id].add(username, lastlogin,
                                     idnumber, child, childidnumber)

    def output(self):
        for family in self.families.keys():
            self.families[family].output()

    def output_doubles(self):
        for family in self.families.keys():
            if len(self.families[family].username) > 1:
                self.families[family].output()

def add(families, username, lastlogin, idnumber, child, childidnumber):
    families.add(username, lastlogin, idnumber, child, childidnumber)

def parse():

    import os
    if os.path.exists('/home/lcssisadmin'):
        path = '/home/lcssisadmin/student_parent_info.txt'
    else:
        path = '/Users/adammorris/student_parent_info.txt'

    raw = [r.strip('\n') for r in open(path).readlines() if r.strip('\n')]
    raw.pop(0)
    raw.pop(0)
    raw.pop(-1)

    families = Families()
    
    for line in raw:
        username, lastlogin, idnumber, child, childidnumber = [item.strip() for item in line.split('|')]
        add(families, username, lastlogin, idnumber, child, childidnumber)

    families.output()

    print()
    print()

    families.output_doubles()

    families.update_table()

if __name__ == "__main__":

    parse()
    
