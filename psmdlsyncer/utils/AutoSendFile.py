import re
import os

# This is the version of the autosend files
# With each increase of number in the version, means that something about the fields have changed from within autosend
major_version = 3
version_format = "{prefix}_{{school}}_{{unique}}_v{major_version}.{{minor_version}}".format(prefix='ssis', major_version=major_version)

from psmdlsyncer.settings import config_get_section_attribute

class File:

    def __init__(self, school, unique):
        """
        Main task here is to set self.path
        """
        path_to_powerschool = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')
        if not path_to_powerschool:
            raise NotImplemented("Something wrong with the powerschool directory information")

        # Dynamically look at the directory and use the latest version
        path = path_to_powerschool + '/' + version_format.format(minor_version='', **locals())
        path = path.split(os.path.sep)[-1]
        candidates = [g for g in [f.split(os.path.sep)[-1] for f in os.listdir(path_to_powerschool)] if path in g]
        candidates = sorted(candidates)
        final = candidates[-1]
        self.path = path_to_powerschool + '/' + final
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

    f = File('sec', 'studentschedule')
    for line in f.content():
        print(line)
    
