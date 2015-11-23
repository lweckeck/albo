"""Provide global configuration to the lesionpypeline module."""
import os
import ConfigParser
import importlib

conf = dict()

CLASSIFIER_SECTION = 'classifier'


def read_file(path):
    """Read configuration options from .conf file.

    Options are read with ConfigParser and stored in a dictonary, which
    contains another dictionary for each section, such that options can be read
    as follows:
    > value = conf['section']['key']

    When multiple files are read, the config is not overwritten but updated.
    """
    parser = ConfigParser.ConfigParser()
    parser.read(path)

    # change working directory to config file location
    cwd = os.getcwd()
    config_dir, _ = os.path.split(path)
    os.chdir(config_dir)

    for section in parser.sections():
        section_dict = dict()
        for key, value in parser.items(section):
            # if value is filename, convert to absolute path
            if os.path.isfile(value):
                value = os.path.abspath(value)
            section_dict[key] = value

        if section in conf.keys() and isinstance(conf[section], dict):
            conf[section].update(section_dict)
        else:
            conf[section] = section_dict

    # restore working directory
    os.chdir(cwd)


def read_module(path):
    """Read configuration options from python module.

    The given module is imported, and all contained variables are stored in the
    conf dictionary with the given section_name, such that options can be read
    as follows:
    > value = conf['section_name']['key']

    """
    normpath = os.path.normpath(path)
    module_path, module_name = os.path.split(normpath)
    module = importlib.import_module(module_name)

    # if module is given as folder with __init__.py
    if os.path.isdir(normpath):
        module_path = normpath

    for key in vars(module):
        if not key.startswith('__'):
            value = vars(module)[key]
            if isinstance(value, str):
                value_path = os.path.join(module_path, value)
                if os.path.isfile(value_path):
                    value = os.path.abspath(value_path)
            conf[key] = value

def read_imported_module(module):
    for key in vars(module):
        if not key.startswith('__'):
            conf[key] = vars(module)[key]
