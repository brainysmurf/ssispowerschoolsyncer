from psmdlsyncer.php import ModUserEnrollments

class Moodle(CommandLine):
    # for ease in testing
    switches = ['profiles','enrollments','cohorts','all']
    def __init__(self):
        super().__init__()
        self.mod_moodle = ModUserEnrollments()

    def go(self):
        self.logger.debug("Building csv file for moodle")
        path_to_cli = self.config['MOODLE'].get('path_to_cli') if self.config.has_section('MOODLE') else None
        

        for account in self.tree.ALL:
            this_id = account.ID
            
            



if __name__=="__main__":
    moodle = Moodle()
    moodle.go()
