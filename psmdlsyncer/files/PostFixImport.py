from psmdlsyncer.settings import config_get_section_attribute
import os

class PostFixImport:
    def __init__(self, school, unique):
        self.school = school
        self.unique = unique
        self.path_to_home = config_get_section_attribute('EMAIL', 'path_to_home')

    def content(self):
        if not (self.school == 'dist' and self.unique == 'studentinfo'):
            return ()

        for account in os.listdir(self.path_to_home):
            if account.startswith('.'):
                continue
            yield [account, '', '', "", "", "", "", "", ""]
