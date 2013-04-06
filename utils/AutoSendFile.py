import re

class File:

    def __init__(self, path):
        self.path = path
        self.readin()

    def readin(self):
        with open(self.path) as _f:
            raw = "\n".join(_f.readlines())
        raw = re.sub('\n\n([\n\t])+', '\t', raw)
        raw = re.sub('\t{3,}', '\t', raw)
        self.raw = [line.strip('\t').strip('\r') for line in raw.split('\n') if line]

    def content(self):
        return self.raw


if __name__ == "__main__":

    f = File('../../powerschool/ssis_studentinfodumpall')
    for line in f.content():
        print(line)
    
