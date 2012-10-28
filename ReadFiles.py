"""
Send it the path, it gives back the raw information line by line
"""

class SimpleReader:
    def __init__(self, path):
        self.path = path

    def raw(self):
        with open(self.path) as f:
            return f.readlines()
