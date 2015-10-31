"""Provide global configuration to the lesionpypeline module."""
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

    for section in parser.sections():
        section_dict = dict()
        for key, value in parser.items(section):
            section_dict[key] = value

        if section in conf.keys():
            conf[section].update(section_dict)
        else:
            conf[section] = section_dict
