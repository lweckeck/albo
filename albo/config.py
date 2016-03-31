"""Provide global configuration to the albo module."""
import os
import sys
import ConfigParser

import albo.log as logging

log = logging.get_logger(__name__)

DEFAULT_CONFIG_PATH = os.path.expanduser('~/.config/albo/albo.conf')
DEFAULT_CONFIG = """
[global]
# relative paths are interpreted as relative to the directory from which the
# program is started
cache_dir = ./cache
output_dir = ./out
classifier_dir =
standardbrain_dir =
atlas_dir =
"""


def expand_path(path):
    """Completely expand path (absolute, variables, user direcotry)."""
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))


def check_dir(dir, name):
    """Check if directory exists, if not, try to create it."""
    if dir == '':
        log.error('Path for {} not set. Please update configuration file'
                  ' ({})'.format(name, DEFAULT_CONFIG_PATH))
        sys.exit(1)
    dir = expand_path(dir)
    if not os.path.isdir(dir):
        log.warn("{} directory {} does not yet exist!"
                 .format(name.capitalize(), dir))
    return dir


class _Config(object):
    cache_dir = ''
    output_dir = ''
    case_output_dir = ''
    classifier_dir = ''
    standardbrain_dir = ''
    atlas_dir = ''

    options = dict()

    def __init__(self):
        """Initialize config object from default config file."""
        if not os.path.isfile(DEFAULT_CONFIG_PATH):
            os.makedirs(os.path.dirname(DEFAULT_CONFIG_PATH))
            with open(DEFAULT_CONFIG_PATH, 'w') as f:
                f.write(DEFAULT_CONFIG)
        parser = ConfigParser.ConfigParser()
        parser.read(DEFAULT_CONFIG_PATH)

        self.cache_dir = check_dir(parser.get('global', 'cache_dir'), 'cache')
        self.output_dir = check_dir(
            parser.get('global', 'output_dir'), 'output')
        self.case_output_dir = self.output_dir

        self.classifier_dir = check_dir(
            parser.get('global', 'classifier_dir'), 'classifier')
        self.standardbrain_dir = check_dir(
            parser.get('global', 'standardbrain_dir'), 'standardbrain')
        self.atlas_dir = check_dir(
            parser.get('global', 'atlas_dir'), 'atlas')


def get():
    """Return the global Config object."""
    global _config
    if _config is None:
        _config = _Config()
    return _config
