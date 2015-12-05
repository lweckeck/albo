"""Provide global configuration to the lesionpypeline module."""
import os
import types
import ConfigParser

import lesionpypeline.log as logging

log = logging.get_logger(__name__)
config = None


def get():
    """Return the global Config object."""
    global config
    if config is None:
        config = _Config()
    return config


class _Config(object):
    _cache_dir = ''
    _output_dir = ''
    _classifier = None

    options = dict()

    @property
    def cache_dir(self):
        if self._cache_dir is '':
            log.warn('Cache directory uninitialized. Using default value: '
                     './cache')
            self._cache_dir = './cache'
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self, value):
        # remove old value if emtpy directory
        old = self._cache_dir
        if os.path.isdir(old) and os.listdir(old) == []:
            os.rmdir(old)
        if not os.path.isdir(value):
            log.warn('Cache directory {} does not yet exist. Creating...'
                     .format(value))
            os.makedirs(value)
        self._cache_dir = value

    @property
    def output_dir(self):
        if self._output_dir is '':
            log.warn('Output directory uninitialized. Using default value: '
                     './out')
            self._output_dir = './out'
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value):
        # remove old value if emtpy directory
        old = self._output_dir
        if os.path.isdir(old) and os.listdir(old) == []:
            os.rmdir(old)
        if not os.path.isdir(value):
            log.warn('Output directory {} does not yet exist. Creating...'
                     .format(value))
            os.makedirs(value)
        self._output_dir = value

    @property
    def classifier(self):
        if self._classifier is None:
            raise ValueError('Classifier uninitialized!')
        return self._classifier

    @classifier.setter
    def classifier(self, value):
        if not isinstance(value, types.ModuleType):
            raise TypeError('"{}" is an invalid type for property classifier, '
                            'must be of type "module"!'.format(type(value)))
        elif 'sequences' not in vars(value):
            raise ValueError('{} has no attribute sequences, which is required'
                             ' for classifier modules!')
        else:
            self._classifier = value

    def read_config_file(self, path):
        """Read configuration options from .conf file.

        Options are read with ConfigParser and stored in the global
        Config object. Values for cache_dir and output_dir are handled
        specially, additional options are stored in the options
        dict. Note that sections are not respected, i.e. if there are
        two keys in different sections with the same name, one will be
        overwritten.

        Example:
        [section]
        key=value

        > value = Config().options['key']
        """
        parser = ConfigParser.ConfigParser()
        parser.read(path)

        # change working directory to config file location
        cwd = os.getcwd()
        config_dir, _ = os.path.split(path)
        os.chdir(config_dir)

        for section in parser.sections():
            for key, value in parser.items(section):
                # if value is filename, convert to absolute path
                if os.path.isfile(value):
                    value = os.path.abspath(value)

                if key == 'cache_dir':
                    self.cache_dir = value
                elif key == 'output_dir':
                    self.output_dir = value
                else:
                    self.options[key] = value
        # restore working directory
        os.chdir(cwd)
