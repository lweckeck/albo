"""Provide global configuration to the albo module."""
import os

import albo.log as logging

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
    _classifier_dir = None

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
