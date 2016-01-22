"""This module supplies methods for loading and selecting classifiers."""
import os
import imp


def load_classifiers_from(directory):
    """Load all classifiers from modules in the given directory."""
    if not os.path.isdir(directory):
        raise ValueError('{} is not a directory!'.format(directory))

    def _abspath(x):
        return os.path.join(directory, x)

    modules = [imp.load_source(name, path) for name, path in
               [(fname.replace('.py', ''), _abspath(fname))
                for fname in os.listdir(directory)
                if fname.endswith('.py')
                if fname != '__init__.py']]
    classifiers = [Classifier(m.__name__, m) for m in modules
                   if 'sequences' in vars(m)]

    subdirs = [d for d in map(_abspath, os.listdir(directory))
               if os.path.isdir(_abspath(d))]
    for subdir in subdirs:
        classifiers.extend(load_classifiers_from(subdir))
    return classifiers


def best_classifier(classifiers, sequences):
    """Return the best classifier for the given set of sequences."""
    applicable = [c for c in classifiers
                  if set(c.sequences).issubset(set(sequences))]
    if len(applicable) == 0:
        return None
    else:
        # return applicable classifier which uses the most sequences
        return max(applicable,
                   key=lambda x: len(set(x.sequences) & set(sequences)))


class Classifier(object):
    """Represents a classifier with associated preprocessing information."""

    def __init__(self, name, module):
        """Create classifier from module."""
        try:
            self.name = name
            self.sequences = module.sequences

            self.pixel_spacing = module.pixel_spacing
            self.registration_base = module.registration_base
            self.skullstripping_base = module.skullstripping_base

            # self.metadata_correction_tasks = module.tasks
            self.tasks = module.tasks
            self.intensity_models = module.intensity_models
            self.classifier_file = module.classifier_file

            self.features = module.features
        except AttributeError as e:
            raise ValueError('Given module is not a classifier module: ' +
                             e.message)

    def __str__(self):
        """Return the name of the classifier as string representation."""
        return self.name
