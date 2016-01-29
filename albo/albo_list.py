#!/usr/bin/env python
"""Script to list all available classifiers."""

import os
import sys
import argparse

import albo.classifiers as clf


def main(args):
    """List classifiers."""
    print "Directory: {}".format(os.path.abspath(args.classifier_dir))
    classifiers = clf.load_classifiers_from(args.classifier_dir)
    if len(classifiers) == 0:
        print "No classifiers found."
        sys.exit(0)
    names = [c.name for c in classifiers]
    seqs = [", ".join(c.sequences) for c in classifiers]
    longest_name = max(names, key=len)
    for name, seq in [("Classifier:", "Sequences:")] + zip(names, seqs):
        print "{} {}".format(name.ljust(len(longest_name)), seq)


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
