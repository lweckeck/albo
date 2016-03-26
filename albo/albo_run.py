#!/usr/bin/env python
"""Script to run the albo pipeline."""

import os
import sys
import shutil
import argparse

import albo.classifiers as clf
import albo.log as logging
import albo.config as config
import albo.pipeline as ppl


log = logging.get_logger(__name__)

SEQUENCE_FILE_EXT = '.nii.gz'


def main(args):
    """Run pipeline."""
    logging.init(args.verbose, args.debug)
    logging.set_global_log_file(args.id + '_incomplete.log')
    _setup_output_dir(args.output, args.id, args.force)
    config.get().cache_dir = os.path.abspath(args.cache)

    # determine best applicable classifier
    sequences = _parse_sequences(args.sequence)
    stdbrain_sequence, stdbrain_path = _parse_standardbrain(args.standardbrain)
    classifiers = clf.load_classifiers_from(args.classifier_dir)
    best_classifier = clf.best_classifier(classifiers, sequences.keys())
    if best_classifier is None:
        log.error('No applicable classifier has been found for the given '
                  'sequences. Run "albo list" for all available classifiers.')
        sys.exit(1)

    # remove sequences unused by the classifier
    relevant_sequences = {key: sequence for key, sequence in sequences.items()
                          if key in best_classifier.sequences}
    if set(relevant_sequences.keys()) != set(sequences.keys()):
        log.warning('The best available classifier will only use the subset {}'
                    ' of available sequences!'
                    .format(relevant_sequences.keys()))

    # setup configuration and execute pipeline steps
    ppl.process_case(relevant_sequences, best_classifier,
                     stdbrain_sequence, stdbrain_path)

    # move log file to output folder
    if os.path.isfile(logging.global_log_file):
        shutil.move(logging.global_log_file,
                    os.path.join(config.get().output_dir,
                                 args.id + '_sucessful.log'))
    log.info('Done.')
    sys.exit()


def _setup_output_dir(dir, case_id, overwrite):
    output_path = os.path.join(os.path.abspath(dir), case_id)
    if os.path.isdir(output_path) and os.listdir(output_path) != []:
        if overwrite:
            shutil.rmtree(output_path)
            os.mkdir(output_path)
        else:
            log.error('There already is an output directory for the given ID.'
                      ' Use --force/-f to override.')
            sys.exit(1)
    config.get().output_dir = output_path


def _parse_sequences(id_sequence_mappings):
    sequences = dict()
    for s in id_sequence_mappings:
        identifier, path = s.split(':')
        if not os.path.isfile(path):
            log.error('The path {} given for sequence {} is not a file.'
                      .format(path, identifier))
            sys.exit(1)
        sequences[identifier] = path
    return sequences


def _parse_standardbrain(id_path_mapping):
    identifier, path = id_path_mapping.split(':')
    if not os.path.isfile(path):
        log.error('The path {} given for the standardbrain is not a file.'
                  .format(path))
    return identifier, path


def add_arguments_to(parser):
    """Add commandline arguments for this program to a given parser."""
    parser.add_argument('sequence', nargs='+', type=str, metavar="SEQID:PATH",
                        help='process sequences given as <sequence id>:<path '
                        'to file>, e.g. MR_Flair:path/to/file.nii.gz')
    parser.add_argument('--id', '-i', type=str, required=True,
                        help='use given string as case identifier, e.g. for'
                        ' naming the ouput folder')
    parser.add_argument('--config', '-c', type=str,
                        help='pipeline configuration file '
                        '(default: ~/.config/albo/albo.conf')
    parser.add_argument('--classifier_dir', '-d', type=str,
                        help='path to the directory to search for classifiers')
    parser.add_argument('--standardbrain', '-s', type=str, metavar='SEQID:PATH',
                        help='use given standardbrain, given as <sequence_id>:'
                        '<path>, as reference image for registration.')
    parser.add_argument('--cache', type=str,
                        help='path to caching directory')
    parser.add_argument('--output', '-o', type=str,
                        help='path to output directory')
    parser.add_argument('--force', '-f', action='store_true',
                        help='overwrite output directory if already present')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', action='store_true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run the lesion detection pipeline.')
    add_arguments_to(parser)
    args = parser.parse_args()
    main(args)
