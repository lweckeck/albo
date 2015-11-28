"""Load classifiers files and choose best classifier for given sequences."""

import importlib

_classifier_modules = [
    'ISLES_SISS_flair',
    'ISLES_SISS_flair_dwi',
    'ISLES_SISS_flair_t1',
    'ISLES_SISS_flair_t1_dwi',
    'ISLES_SISS_flair_t1_t2',
    'ISLES_SISS_flair_t1_t2_dwi',
    'ISLES_SISS_flair_t2',
    'ISLES_SISS_flair_t2_dwi',
    'forest'
]

classifiers = [importlib.import_module('.'+m, __package__)
               for m in _classifier_modules]


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


def print_available_classifiers():
    """Print the module names and sequences of all available classifiers."""
    for c in classifiers:
        name_str = c.__name__
        sequences_str = ', '.join(c.sequences)
        print name_str + ':'
        print '\t' + sequences_str
