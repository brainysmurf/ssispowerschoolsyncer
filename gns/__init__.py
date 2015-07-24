"""
Global Name Space
Simple way to have global variables defined, used throughout the app
Reads in settings.ini and provides logging as well

"""

import contextlib, os, logging
import configparser
import datetime

class GNS(object):
    def __init__(self, *args, **kwargs):
        self.COLON = ':'
        self.CLN = ':'
        self.COMMA = ','
        self.CMMA = ','
        self.SEMICOLON = ';'
        self.NEWLINE = '\n'
        self.NWLNE = '\n'
        self.SPACE = ' '
        self.SPCE = ' '
        self.TAB = '\t'
        self.TB = '\t'
        self.SLASH = '/'
        self.LPARENS = '('
        self.RPARENS = ')'
        self.AT = '@'

        # Useful regexp phrases
        self.DOT = '.'
        self.ASTER = '*'

        # Now, create namespaces associated with setting.ini and config

        self.set_namespace('config')
        self.set_namespace('config.directories')

        self.config.directories.home = os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2]) + os.sep
        self.config.directories.settings_ini = self.config.directories.home + 'settings.ini'
        settings = configparser.ConfigParser()
        results = settings.read(self.config.directories.settings_ini)

        for SECTION in [s for s in settings.sections()]:
            section = SECTION.lower()
            self.set_namespace('config.{}'.format(section))
            for OPTION in settings.options(SECTION):
                option = OPTION.lower()
                value = settings.get(SECTION, OPTION)
                setattr(getattr(self.config, section), option, self.pythonize(value))

        path_to_logging = self('{config.directories.path_to_logging}/{date}', date=datetime.datetime.now().strftime('%x--%X').replace('/', '-'))
        #used to keep this in a file, let's just set it up right, shall we?
        log_level = self.config.logging.log_level
        numeric_level = getattr(logging, log_level.upper())
        if numeric_level is None:
            raise ValueError('Invalid log level: {}'.format(loglevel))

        logging.basicConfig(filename=path_to_logging, filemode='a+', level=numeric_level)

        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            # running with an attached terminal, automatically
            # set stdout debugging to full verbosity
            root = logging.getLogger()
            stdout_level = logging.DEBUG
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(logging.INFO)
            root.addHandler(stdout_handler)

    @staticmethod
    def pythonize(value):
        if isinstance(value, str) or isinstance(value, unicode):
            return {
                'true':True, 'false':False, 
                'on':True, 'off':False, 
                'yes':True, 'no':False
                }.get(value.lower().strip(), value)
        return value

    def setup_verbosity(self, obj):
        obj.verbose = self.config.defaults.verbose
        if obj.verbose:
            obj.default_logger = lambda *args, **kwargs: sys.stdout.write("".join(args) + '\n')
        else:
            obj.default_logger = lambda *args, **kwargs: ()

    @property
    def dict_not_underscore_not_upper(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_') and not key.isupper()}

    @staticmethod
    def make_object(name):
        return type(name, (), {})

    def set_namespace(self, ns):
        if not '.' in ns:
            setattr(self, ns, GNS.make_object(ns))
        else:
            class_name = []
            prev_class = self
            for inner in ns.split('.'):
                class_name.append(inner)
                if not hasattr(prev_class, inner):
                    setattr(prev_class, inner, GNS.make_object(".".join(class_name)))
                prev_class = getattr(prev_class, inner)

    def new(self):
        for key in self.dict_not_underscore_not_upper:
            del self.__dict__[key]

    def local(self):
        return self.__class__()        

    @contextlib.contextmanager
    def block(self):
        """TODO: Return __dict__ to original? """
        yield self.__class__()

    @property
    def dict_from_dict(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_')}

    def __call__(self, *args, **kwargs):
        d = self.dict_from_dict
        d.update(kwargs)
        try:
            return ''.join(args).format(**d)
        except AttributeError:
            return None

    @classmethod
    def string(cls, astring, *args, **kwargs):
        for arg in args:
            kwargs.update(arg.__dict__)
        return cls(*args, **kwargs)(astring)

    def get(self, path, default=None, required=True):
        me = self
        for inner in path.split('.'):
            if not hasattr(me, inner):
                if required:
                    raise TypeError(self('This app requires a setting for {path}', path=path))
                return default
            else:
                me = getattr(me, inner)
        return me

    @property
    def kwargs(self):
        return {key: value for key, value in self.__dict__.items() if key.islower() and not key.startswith('_')}

    @property
    def declared_kwargs(self):
        return {key: value for key, value in self.__dict__.items() if key.islower() and not key.startswith('_')}

    def __repr__(self):
        """
        VERY MEAGER WAY TO OUTPUT THIS DATA
        """
        return str(self.dict_not_underscore_not_upper)

import sys
sys.modules['gns'] = GNS()