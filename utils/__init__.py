"""
Defines the absolutely basic utilties that this app uses
Mostly consists of stuff that I find really really useful

By convention, I always name these things in a way that pretty much guarantees a unique namespace:
  * All lowercase, no underscores
  * Vowels (includying y when it's a vowel) stripped out
  * EXCEPT for any vowels that begin or end a word
  
"""

class envrnmnt:
    """
    Look around and see where we are, set attributes accordingly
    """
    def __init__(self):
        self.on_server = False
        self.dry_run   = True

class strng:
    """
    String Template class
    Instead of typing "".format() all the time

    Hello Worlds:
    print(strng('Hello {name}', name='World'))                     # simplest meaningful case
    print(strng('Hello', '{name}', name='World', sep=', '))        # passed arguments are joined together
    d = {'greeting':'Hello', 'name':'World'}                       # define dictionary...
    print(strng('{greeting} {name}', d))                           # ...and pass it!
    print(strng('{greeting} {name}', o))                           # ...also works for passing objects!!
    print(strng('{greeting}', '{comma} {name}', d, o, comma=',')   # ...and in any combination thereof!!!

    Other methods are useful too (esp take_dict) but the above are the most common idioms

    """
    def __init__(self, *args, **kwargs):
        self.sep = ""
        self._args = []
        self.define(newline="\n", tab="\t", comma=",", period=".", colon=":", space=" ")
        self.define(*args, **kwargs)

    def define(self, *args, **kwargs):
        """
        Sets the internal 
        Args can be a dictionary, in which case it's recursively passed as a kwarg
        """
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
        if args:
            for a in args:
                if isinstance(a, dict):
                    self.define(**a)
                elif hasattr(a, '__dict__'):
                    self.define(**a.__dict__)
                else:
                    self._args.append(a)

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

    def out(self):
        return str(self)

    def __call__(self, *args, **kwargs):
        self.define(*args, **kwargs)
        return str(self)

class excptn(Exception):
    """
    Same as any other exception, except...
    ... it uses strng above

    """

    def __init__(self, error_string, **kwargs):
        if isinstance(error_string, strng):
            self.value = error_string
            if kwargs:
                self.value.define(**kwargs)
        else:
            self.value = strng(error_string, **kwargs)

    def __str__(self):
        return str(self.value)


# This makes sure it actually gets 'exported' when imported
__all__ = ['envrnmnt', 'strng', 'excptn']
