from psmdlsyncer.settings import logging
import re
import os
import csv
from psmdlsyncer.settings import config_get_section_attribute

# This is the version of the autosend files
# With each increase of number in the version, means that something about the fields have changed from within autosend
major_version = 3
prefix = config_get_section_attribute('AUTOSEND', 'prefix')
version_format = "{prefix}_{{school}}_{{unique}}_v{major_version}.{{minor_version}}".format(prefix=prefix, major_version=major_version)

class AutoSendImport:

    def __init__(self, school, unique):
        """
        Main task here is to set self.path
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        path_to_powerschool = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')
        if not path_to_powerschool:
            raise NotImplemented("Something wrong with the powerschool directory information")

        self.school = school
        self.unique = unique

        # Dynamically look at the directory and use the latest version
        path = path_to_powerschool + '/' + version_format.format(minor_version='', **locals())
        path = path.split(os.path.sep)[-1]
        candidates = [g for g in [f.split(os.path.sep)[-1] for f in os.listdir(path_to_powerschool)] if path in g]
        candidates = sorted(candidates)
        if not candidates:
            self.logger.critical("Autosend file not present for {} {}\ncontent method set to yield nothing".format(self.school, self.unique))
            self.content = lambda *args, **kwargs: []
            return
        final = candidates[-1]
        self.path = path_to_powerschool + '/' + final
        self.logger.info('Autosend: {}_{}\nParsing this file: {}'.format(school, unique, self.path))

    def content(self):
        with open(self.path) as f:
            # special handling for the staffinfo file, which has some status marks we have to filter out
            if self.school == 'dist' and self.unique == 'staffinfo':
                for row in csv.reader(f, delimiter='\t'):
                    if row[-1] == '1':
                        yield row
            else:
                yield from csv.reader(f, delimiter='\t')

if __name__ == "__main__":

    f = File('sec', 'studentschedule')
    for line in f.content():
        print(line)

