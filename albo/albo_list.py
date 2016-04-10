#!/usr/bin/env python
"""Script to list all available classifiers."""

import sys
import argparse

import albo.config as config
import albo.classifiers as clf


def main(args):
    """List classifiers."""
    classifier_dir = config.get().classifier_dir
    print "Directory: {}".format(classifier_dir)
    classifiers = clf.load_classifiers_from(classifier_dir)
    if len(classifiers) == 0:
        print "No classifiers found."
        sys.exit(0)
    names = [c.name for c in classifiers]
    seqs = [", ".join(c.sequences) for c in classifiers]
    issues = [', '.join(clf.check_consistency(c)) for c in classifiers]
    longest_name = max(names, key=len)
    for name, seq, issue in \
            [("Classifier:", "Sequences:", "")] + zip(names, seqs, issues):
        print "{} {}".format(name.ljust(len(longest_name)), seq)
        if len(issue) > 0:
            print "\tDetected issues: " + issue


def add_arguments_to(parser):
    """Add script-specific arguments to given parser."""
    parser.add_argument('--classifier_dir', '-d', type=str,
                        help='path to the directory to search for classifiers')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='List all available classifiers.')
    add_arguments_to(parser)
    args = parser.parse_args()
    main(args)
