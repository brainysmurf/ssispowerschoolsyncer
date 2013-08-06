class BasicException(Exception):
    def __init__(self, it):
        self.it = it

    def __str__(self):
        return repr(self.it)

