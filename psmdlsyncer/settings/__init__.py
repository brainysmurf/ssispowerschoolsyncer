
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

current_working_list = os.path.abspath(os.path.join(__file__, os.pardir)).split(os.sep)

# Look through every parent folder, looking for first settings.ini files
settings_list = []
while current_working_list:
    here = "/".join(current_working_list)
    if not here:
        break
    settings_list.append( here + '/settings.ini' )
    current_working_list.pop(-1)

def define_command_line_arguments(*switches, **strings):
    if switches or strings:
        return HoldPassedArguments(*switches, **strings).arguments
    else:
        return None

config = configparser.ConfigParser(defaults={'dry_run':True, 'verbose':True})
results = config.read(settings_list)
if not results:
    print("Some error occurred when attempting to find settings.ini file...exiting")
    exit()

verbose = config.getboolean('DEFAULTS', 'verbose')
dry_run = config.getboolean('DEFAULTS', 'dry_run')

email_server = None
if config.has_section("EMAIL"):
    email_server = config['EMAIL'].get('domain')
if not email_server:
    email_server = 'localhost'

def config_get_logging_level():
    return config_get_section_attribute('LOGGING', 'log_level')

def config_get_section_attribute(section, attribute, required=False):
    """ returns None if not present, otherwise returns its value """
    if required:
        requires_setting(section, attribute)
    try:
        if not config.has_section(section):
            return None
        if section in ['DEFAULTS', 'DEBUGGING']:
            return config.getboolean(section, attribute)
        else:
            return config[section].get(attribute)
    except configparser.NoOptionError:
        return None

def requires_setting(section, attribute):
    """ Declare your settings needs this way, opt-in """
    if not config.has_section(section):
        raise Exception("I require {} attribute in {} section, no such section in settings.ini file".format(attribute, section))
    if not config[section].get(attribute):
        raise Exception("Requires {} attribute in {} section, no such attribute in settings.ini file".format(attribute, section))

def flag_passed(flag):
    return hasattr(settings.arguments, flag)

def verbosity(passed):
    if config.has_section('DEFAULTS') and config['DEFAULTS'].get(passed):
        return config.getboolean('DEFAULTS', passed)
    else:
        return False

# setup a few loggers
import logging
path_to_logging = config_get_section_attribute('DIRECTORIES', 'path_to_logging')
if not path_to_logging:
    print("You have to add a path_to_logging settings in DIRECTORIES section, which should be a directory")
    exit()
#used to keep this in a file, let's just set it up right, shall we?
log_level = config_get_section_attribute('LOGGING', 'log_level')
numeric_level = getattr(logging, log_level.upper())
if numeric_level is None:
    raise ValueError('Invalid log level: {}'.format(loglevel))

import datetime
path_to_logging += str(datetime.datetime.now().isoformat())
logging.basicConfig(filename=path_to_logging, filemode='a+', level=numeric_level)

if sys.stdout.isatty():
    # running with an attached terminal, automatically
    # set stdout debugging to full verbosity
    root = logging.getLogger()
    stdout_level = logging.DEBUG
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    root.addHandler(stdout_handler)

__all__ = [verbose, verbosity, dry_run, email_server, config, requires_setting, define_command_line_arguments, logging]
