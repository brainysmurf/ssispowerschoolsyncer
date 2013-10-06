"""
ns = NS()
CREATES AN OBJECT THAT REPRESENTS A NAMESPACE

LOW-LEVEL CLASS USED THROUGHOUT PSMDLSYNCER TO PASS BACK AND FORTH INFO
AND MAKES IT EASY TO INCLUDE IN SQL STATEMENTS, AND SO FORTH

BEHAVOR:

1. ns = NS(object)  # ns NOW HAS EVERYTHING IN object.__dict__

2. DECLARATIVE METHOD
ns.object = 'hello'
ns.when = 'world'
ns('help {object}, {when}')  # 'hello, world'

3. INDIRECT DECLARATIVE
sub = 'i'
ver = 'love'
obj = 'you'
ns.NS(**locals())
ns('{sub} {verb} {obj}')  # 'i love you'

4. PREDEFINED NAMES IN ALL-CAPS
ns.define(salutation='hello', person='world')
ns('{salutation}{COMMA}{SPACE}{person}')  # 'hi, you'

"""

class NS:
    """
    
    """
    def __init__(self, *args, **kwargs):
        self.sep = ""
        self.init()
        self.define(*args, **kwargs)

    def init(self):
        """
        DEFINE ANY STANDARD, READILY-AVAILABLE THINGS
        MUST ALWAYS BE IN ALL-CAPS
        """
        self.COLON = ':'
        self.COMMA = ','
        self.SEMICOLON = ';'
        self.NEWLINE = '\n'
        self.SPACE = ' '
        self.TAB = '\t'
        self.SLASH = '/'
        self.LPARENS = '('
        self.RPARENS = ')'
        self.AT = '@'
        # TODO: DEFINE OS PATH DISTICTION
        
    def define(self, *args, **kwargs):
        """
        SAME AS self.x = y
        """
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
        if args:
            if isinstance(args, tuple):
                for a in args:
                    if hasattr(a, '__dict__'):
                        for key in a.__dict__:
                            setattr(self, key, a.__dict__[key])

    def take_dict(self, d):
        """
        Copy contents of d.__dict__ to mine.
        """
        for key in d.__dict__.keys():
            setattr(self, key, d.__dict__[key])

    def sep(self, sep):
        self.sep = sep

    def items(self):
        return [item for item in self.__dict__.items() if not item[0].startswith('_')]

    def __str__(self):
        return str([item for item in self.__dict__.items() if not item[0].isupper()])

    def __call__(self, s, **kwargs):
        self.define(**kwargs)
        result = s.format(**self.__dict__)
        return result

    def __repr__(self):
        """
        VERY MEAGER WAY TO OUTPUT THIS DATA
        """
        return str([item for item in self.__dict__.items() if not item[0].isupper()])

Smartformmater = NS  # depreciated name


if __name__ == "__main__":

    class Help:
        def __init__(self):
            self.hi = 'hi'
            self.there = 'there'

    help = Help()
    ns = NS(help)
    i = 'i'
    love='love'
    you='you'
    print(NS(**locals())('{i}{love}{you}'))
    print(ns('{hi} {there}'))
    print(ns('{hi}{COMMA}{SPACE}{there}'))
