from psmdlsyncer.settings import config, config_get_section_attribute, \
     logging, define_command_line_arguments

class CommandLine:
    switches = []
    strings = {}
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.warn('Started at {}'.format( datetime.datetime.now() ) )
        define_command_line_arguments(*self.switches, **self.strings)
        self.config = config
        self.dry_run = self.students.settings.dry_run
        if 'DEFAULTS' in self.config.sections():
            for key in self.config['DEFAULTS']:
                setattr(self, key, self.config.getboolean('DEFAULTS', key))
        self.email_server = None
        # TODO: Figure out if this is really needed
        if self.config.has_section("EMAIL"):
            self.email_server = self.config['EMAIL'].get('domain')
        if not self.email_server:
            self.email_server = 'localhost'
        have_email_section = self.config.has_section('EMAIL')
        have_moodle_section = self.config.has_section('MOODLE')
        # moodle link
        self.server_information = ServerInfo()
        # required paths
        self.path_to_powerschool = config_get_section_attribute('DIRECTORIES', 'path_to_powerschool_dump')
        self.path_to_output = config_get_section_attribute('DIRECTORIES', 'path_to_output')
        self.path_to_errors = config_get_section_attribute('DIRECTORIES', 'path_to_errors')
        self.students = Tree()

