"""
Implements the command line for anywhere, just use:
from psmdlsyncer.settings import config
"""
import os
import argparse
import sys
import configparser    

class HoldPassedArguments:
    """
    Class that uses the argsparse module in the way I want it to
    Two hyphens means it's a switch with default of False
    One hyphen means it's a string parameter
    Switches are passed by arguments
    Strings are passed by keywords
    """

    def __init__(self, *switches, **strings):
        """
        switches are used for boolean values
        strings are usef for passed values
        """

        parser = argparse.ArgumentParser()
        for switch in switches:
            parser.add_argument('--' + switch, action='store_true')
        for string in strings.keys():
            parser.add_argument('-' + string, action='store', dest=string, default=strings[string])
        self.arguments = parser.parse_args(sys.argv[1:])
        #for key, value in vars(parser.parse_args(sys.argv[1:])).items():
        #    setattr(self.arguments, key, value)

current_working_list = os.path.abspath(os.getcwd()).split(os.sep)

# Look through every parent folder, looking for first settings.ini files
settings_list = []
while current_working_list:
    here = "/".join(current_working_list)
    if not here:
        break
    settings_list.append( here + '/settings.ini' )
    current_working_list.pop(-1)

settings = HoldPassedArguments('verbose', 'dry_run', 'teachers', 'courses',
                               'students', 'email_list', 'families', 'parents',
                               'automagic_emails', 'profiles', 'input_okay', 'updaters',
                               'enroll_cohorts', 'enroll_courses',
                                inspect_student=False)

config = configparser.ConfigParser(defaults={'dry_run':True, 'verbose':True})
results = config.read(settings_list)
if not results:
    print("Some error occurred when attempting to find settings.ini file...exiting")
    exit()

if config.has_section('ARGUMENTS'):
    config_arguments = config.items('ARGUMENTS')
    for key in config_arguments.keys():
        setattr(settings.arguments, key, config['ARGUMENTS'][key])

# SET UP ASSUMPTIONS GIVEN PASSED ARGUMENTS AT COMMAND LINE
if settings.arguments.automagic_emails:
    settings.arguments.courses = True
    settings.arguments.teachers = True
    settings.arguments.students = True
    
verbose = settings.arguments.verbose
dry_run = settings.arguments.dry_run

if 'DEFAULTS' in config.sections():
    for key in config['DEFAULTS']:
        setattr(settings, key, config.getboolean('DEFAULTS', key))

email_server = None
if config.has_section("EMAIL"):
    email_server = config['EMAIL'].get('domain')
if not email_server:
    email_server = 'localhost'

def config_get_section_attribute(section, attribute):
    """ returns None if not present, otherwise returns its value """
    if not config.has_section(section):
        return None
    if section == 'DEFAULTS':
        return config.getboolean(section, attribute)
    else:
        return config[section].get(attribute)

def requires_setting(section, attribute):
    """ Declare your settings needs this way, opt-in """
    if not config.has_section(section):
        raise Exception("I require {} attribute in {} section, no such section in settings.ini file".format(attribute, section))
    if not config[section].get(attribute):
        raise Exception("Requires {} attribute in {} section, no such attribute in settings.ini file".format(attribute, section))

def flag_passed(flag):
    return getattr(settings.arguments, flag)


__all__ = [verbose, dry_run, email_server, config, settings, requires_setting]
