"""Provide global configuration to the lesionpypeline module."""
import os
import ConfigParser

conf = dict()


def read_file(path):
    """Read configuration options from .conf file.

    Options are read with ConfigParser and stored in a dictonary, which
    contains another dictionary for each section, such that options can be read
    as follows:
    > value = config['section']['key']

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

        if section in conf.keys():
            conf[section].update(section_dict)
        else:
            conf[section] = section_dict

    # restore working directory
    os.chdir(cwd)
