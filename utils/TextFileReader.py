import re

class Columns(list):    
    def output(self):
        for item in self:
            print(item)

class AbstractInterfaceClass:
    """
    
    """
    def __init__(self, **kwargs):
        self.init(**kwargs)

    def __str__(self):
        return self.__class__.__name__ + ': ' + "\n\t".join([key + ' -> ' + str(getattr(self, key)) for key in self.__dict__])
    
    def init(self, **kwargs):
        for key, value in kwargs.items():

            new_key = self.is_getting_key(key)
            
            if hasattr(self, self.will_get_hook(new_key)):
                hook = getattr(self, self.will_get_hook(new_key))
                setattr(self, new_key, hook(value))
            setattr(self, new_key, value)

    def is_getting_key(self, key):
        """
        Override if needed to standardize key names
        In order to ensure we can get attributes without using getattr,
        we need to make key a legal attribute name that can be typed with . syntax
        """
        return re.sub('[\[\]()]', '', key)

    def will_get_hook(self, keyword):
        return 'hook_{}'.format(keyword)

    # Example hook
    def hook_id(self, value):
        """
        Gets called if there is a column 'id', value is from the text file in that column
        """
        # returns integer value of whatever is passed
        return int(value)

class Grade:    
    def __init__(self, value):
        self.value = value

class Behavior:
    def __init__(self, value):
        self.value = value
        
class TextFileReader:
    """
    Provides mechanism for creation of classes (or of dictionary instances)
    by reading in a TSV or CSV file and assigning those default values

    CSV file must contain a first row whereby columns are defined

    By default the values are all strings but can be converted by defining hook_ methods
    """

    def __init__(self, path, interface_class=None,
                 delimiter='\t'):
        """
        Pass me a klass, and there are more hooks, otherwise we'll use dictionaries as an interface
        """
        self.path = path
        self.delimiter = delimiter
        self.columns = Columns()
        self.interface_class = interface_class
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
            self.columns.append(column)
            icolumn += 1

    def readin(self):
        with open(self.path) as the_file:
            the_file.readline() # skip first row
            for line in the_file:
                yield line.rstrip('\n')

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

    def __iter__(self):
        return self.assign

if __name__ == "__main__":

    grades = TextFileReader('../powerschool/ssis_storedgrades')
    for item in grades.generate():
        print(item)
