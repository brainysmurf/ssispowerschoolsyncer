from psmdlsyncer.settings import config_get_section_attribute
import os

class PostFixImport:
    def __init__(self, school, unique):
        self.school = school
        self.unique = unique
        self.path_to_passwd = config_get_section_attribute('EMAIL', 'path_to_passwd')

    def content(self):
        if self.school != 'dist' or self.unique != 'studentinfo':
            return ()
        
        with open(self.path_to_passwd) as f:
            for account in f:
                username, _, _, _, idnumber, _, _ = account.split(':')
                yield [idnumber, '', None, "", "", "", "", "", "", username]

