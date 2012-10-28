class Smartformatter:
    """
    
    """
    def __init__(self, *args, **kwargs):
        self.sep = ""
        self._args = None
        self.define(*args, **kwargs)

    def define(self, *args, **kwargs):
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

    def __str__(self):
        if self._args:
            return self.sep.join(self._args).format(**self.__dict__)
        else:
            return ""

    def __call__(self, *args, **kwargs):
        self.define(*args, **kwargs)
        return str(self)
