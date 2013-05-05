class Columns(list):    
    def output(self):
        for item in self:
            print(item)

class AbstractInterfaceClass:
    """
    
    """
    def __init__(self, **kwargs):
        self.init(**kwargs)
    
    def init(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, self.get_hook(key)):
                hook = getattr(self, self.get_hook(key))
                setattr(self, key, hook(value))
            setattr(self, key, value)

    def get_hook(self, keyword):
        return 'hook_{}'.format(keyword)

    # Example hook
    def hook_id(self, value):
        """
        Gets called if there is a column 'id', value is from the text file in that column
        """
        # returns integer value of whatever is passed
        return int(value)

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
        Called after opening file, self.raw should be defined
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
        self.columns.output()

    def readin(self):
        with open(self.path) as the_file:
            the_file.readline() # skip
            for line in the_file:
                yield line.rstrip('\n')

    def assign(self):
        for line in self.readin():
            split = line.split(self.delimiter)
            content = {self.columns[i]: split[i] for i in range(len(self.columns))}
            if self.interface_class:
                yield self.interface_class(**content)
            else:
                yield content

if __name__ == "__main__":

    grades = TextFileReader('../powerschool/ssis_storedgrades', interface_class=AbstractInterfaceClass)
    for item in grades.assign():
        print(item)
