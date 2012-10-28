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
        self.children.output()
    

class Families:

    def __init__(self):
        self.families = {}

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

def parse(path):

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

if __name__ == "__main__":

    parse('/Users/adammorris/student_parent_info.txt')
    
