""""""

import os
import importlib

_modulenames = [m.replace('.py', '')
                for m in os.listdir(os.path.dirname(__file__))
                if m.endswith('.py')]

classifiers = [importlib.import_module('.'+m, __package__)
               for m in _modulenames
               if '__init__' not in m]


def best_classifier(present_sequences):
    """Return the best classifier for the given set of sequences."""
    # classifier is applicable if all its sequences are present
    valid_classifiers = [c for c in classifiers
                         if set(c.sequences).issubset(set(present_sequences))]
    if len(valid_classifiers) == 0:
        raise ValueError('No classifier applicable to the given sequence '
                         'combination!')

    # the best applicable classifier is the one with the most present sequences
    best_classifier = max(valid_classifiers,
                          key=(lambda x:
                               len(set(x.sequences) & set(present_sequences))))
    return best_classifier
