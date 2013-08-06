from ssispowerschoolsyncer.utils.TextFileReader import AbstractInterfaceClass

class PowerSchoolRow(AbstractInterfaceClass):
    """
    Practice for PowerSchoolIntegrator
    """

    def hook_grade_level(self, value):
        return int(value)

    def hook_termid(self, value):
        return int(value)

    def hook_behavior(self, value):
        return Behavior(value)

    def hook_grade(self, value):
        return Grade(value)

    def is_getting_key(self, key):
        """
        PowerSchool autosend data often has [1] or [2] in the column name
        """
        return re.sub('\[.*\]', '', key)

    def generate():
        for line in self.readin():
            split = line.split(self.delimiter)
            content = {self.columns[i]: split[i] for i in range(len(self.columns))}
            if self.interface_class:
                yield self.interface_class(**content)
            else:
                yield content

    def __str__(self):
        return "ID: {student_number} Behavior {behavior} Grade: {grade}".format(**self.__dict__)



class PowerSchoolReader(TextFileReader):
    """
    Extends TextFileReader to have multiple objects depending on name in brackets
    """

    def __init__(self, path, interface_classes={},
                 delimiter='\t'):
        """
        Pass me a klass, and there are more hooks, otherwise we'll use dictionaries as an interface
        """
        self.path = path
        self.delimiter = delimiter
        self.columns = Columns()
        self.interface_classes = interface_classes
        self.init()

    def init(self):
        """
        Called after constructor
        """
        with open(self.path) as the_file:
            firstline = the_file.readline()
            firstline = firstline.rstrip()
        icolumn = 1
        split = firstline.split(self.delimiter)
        for icolumn in range(0, len(split)):
            column = split[icolumn].replace(' ', '_').lower()
            if re.match('^\[(.*)\]', column):
                pass
            else:
                self.columns.append(column)
            icolumn += 1
            
        
    def generate(self):
        """
        Returns objects
        """
        for line in self.readin():
            split = line.split(self.delimiter)
            content = {self.columns[i]: split[i] for i in range(len(self.columns))}
            if self.interface_class:
                yield self.interface_class(**content)
            else:
                yield content
