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
            with open(DEFAULT_CONFIG_PATH, 'w') as f:
                f.write(DEFAULT_CONFIG)
        parser = ConfigParser.ConfigParser()
        parser.read(DEFAULT_CONFIG_PATH)

        self.cache_dir = expand_path(parser.get('global', 'cache_dir'))
        if not os.path.isdir(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
            except OSError as e:
                log.error("Error creating cache directory {}: {}"
                          .format(self.cache_dir, e.message))
                sys.exit(1)

        self.output_dir = expand_path(parser.get('global', 'output_dir'))
        if not os.path.isdir(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except OSError as e:
                log.error("Error creating output directoy {}: {}"
                          .format(self.output_dir, e.message))
                sys.exit(1)

        self.case_output_dir = self.output_dir

        self.classifier_dir = expand_path(
            parser.get('global', 'classifier_dir'))
        if self.classifier_dir == '':
            log.error("Please set classifier directory in config file! "
                      "({})".format(DEFAULT_CONFIG_PATH))
            sys.exit(1)
        if not os.path.isdir(self.classifier_dir):
            log.error("Classifier directory {} does not exist!"
                      .format(self.classifier_dir))

        self.standardbrain_dir = expand_path(
            parser.get('global', 'standardbrain_dir'))
        if self.standardbrain_dir == '':
            log.error("Please set standardbrain directory in config file! "
                      "({})".format(DEFAULT_CONFIG_PATH))
            sys.exit(1)
        if not os.path.isdir(self.standardbrain_dir):
            log.error("Standardbrain directory {} does not exist!"
                      .format(self.standardbrain_dir))

        self.atlas_dir = expand_path(
            parser.get('global', 'atlas_dir'))
        if self.atlas_dir == '':
            log.error("Please set atlas directory in config file! "
                      "({})".format(DEFAULT_CONFIG_PATH))
            sys.exit(1)
        if not os.path.isdir(self.atlas_dir):
            log.error("Atlas directory {} does not exist!"
                      .format(self.atlas_dir))


_config = _Config()


def get():
    """Return the global Config object."""
    global _config
    if _config is None:
        _config = _Config()
    return _config
