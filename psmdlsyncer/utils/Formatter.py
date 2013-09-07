class Smartformatter:
    """
    
    """
    def __init__(self, *args, _verbose=False, **kwargs):
        self.sep = ""
        self._args = None
        self._verbose = _verbose
        self.init()
        self.define(*args, **kwargs)

    def init(self):
        """
        DEFINE ANY STANDARD, READILY-AVAILABLE THINGS
        MUST ALWAYS BE IN ALL-CAPS
        """
        self.COLON = ':'
        self.NEWLINE = '\n'
        self.SPACE = ' '
        self.TAB = '\t'
        self.SLASH = '/'
        self.LPARENS = '('
        self.RPARENS = ')'
        # TODO: DEFINE OS PATH DISTICTION
        
    def define(self, *args, **kwargs):
        """
        SAME AS self.x = y
        """
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
        if args:
            self._args = [a for a in args if a]

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
        if self._args:
            return self.sep.join(self._args).format(**self.__dict__)
        else:
            return ""

    def __call__(self, *args, **kwargs):
        self.define(*args, **kwargs)
        result = str(self)
        if self._verbose:
            print(result)
        return result
