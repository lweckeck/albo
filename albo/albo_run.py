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
import albo.atlases as atl

log = logging.get_logger(__name__)


def main(args):
    """Run pipeline."""
    logging.init(args.verbose, args.debug)
    logging.set_global_log_file(args.id + '_incomplete.log')
    if args.cache:
        config.get().cache_dir = os.path.abspath(args.cache)
    if args.output:
        config.get().output_dir = os.path.abspath(args.cache)

    # 1. determine best applicable classifier
    sequences = _parse_sequences(args.sequence)
    classifiers = clf.load_classifiers_from(config.get().classifier_dir)
    best_classifier = clf.best_classifier(classifiers, sequences.keys())
    if best_classifier is None:
        log.error('No applicable classifier has been found for the given '
                  'sequences. Run "albo list" for all available classifiers.')
        sys.exit(1)
    issues = clf.check_consistency(best_classifier)
    if len(issues) > 0:
        log.error('Classifier is inconsistent: {}'.format(', '.join(issues)))
        sys.exit(1)

    # 2. remove sequences unused by the classifier
    relevant_sequences = {key: sequence for key, sequence in sequences.items()
                          if key in best_classifier.sequences}
    if set(relevant_sequences.keys()) != set(sequences.keys()):
        log.warning('The best available classifier will only use the subset {}'
                    ' of available sequences!'
                    .format(relevant_sequences.keys()))

    # 3. select standardbrain
    stdbrain_sequence, stdbrain_path = \
        _select_standardbrain(relevant_sequences.viewkeys())

    # 4. execute pipeline
    _setup_output_dir(args.id, args.force)
    mask = ppl.segment_case(
        relevant_sequences, best_classifier, stdbrain_sequence, stdbrain_path,
        args.skullstripped)
    atl.calculate_atlas_overlaps(mask)

    # 5. move log file to output folder
    if os.path.isfile(logging.global_log_file):
        shutil.move(logging.global_log_file,
                    os.path.join(config.get().case_output_dir,
                                 args.id + '_sucessful.log'))
    log.info('Done.')
    sys.exit()


def _setup_output_dir(case_id, overwrite):
    output_path = os.path.join(config.get().output_dir, case_id)
    if not os.path.isdir(output_path):
        os.makedirs(output_path)
    elif os.path.isdir(output_path) and os.listdir(output_path) != []:
        if overwrite:
            shutil.rmtree(output_path)
            os.mkdir(output_path)
        else:
            log.error('There already is an output directory for the given ID.'
                      ' Use --force/-f to override.')
            sys.exit(1)
    config.get().case_output_dir = output_path


def _parse_sequences(id_sequence_mappings):
    sequences = dict()
    for s in id_sequence_mappings:
        try:
            identifier, path = s.split(':')
        except ValueError:
            log.error('Error parsing argument "{}". Input files must be passed'
                      ' as <sequence_id>:<path/to/file>.'.format(s))
            sys.exit(1)
        if not os.path.isfile(path):
            log.error('The path {} given for sequence {} is not a file.'
                      .format(path, identifier))
            sys.exit(1)
        sequences[identifier] = path
    return sequences


def _select_standardbrain(sequence_keys):
    sequence_keys = list(sequence_keys)
    ids = ['t1', 't2', 'flair']
    path = config.get().standardbrain_dir

    # list files in standardbrain directory and match to sequence ids
    files = [name for name in os.listdir(path)
             if os.path.isfile(os.path.join(path, name))
             if 'mask' not in name]

    standardbrains = dict()
    for id in ids:
        for f in files:
            if id in f.lower():
                standardbrains[id] = os.path.join(path, f)

    # return the first sequence and standardbrain matching one of the ids
    for id in ids:
        for index, key in enumerate(map(str.lower, sequence_keys)):
            if id in key:
                return sequence_keys[index], standardbrains[id]
    log.error('No standardbrain found for sequences {}. One of the sequences'
              ' {} must be present!'.format(sequence_keys, ", ".join(ids)))
    sys.exit(1)


def add_arguments_to(parser):
    """Add commandline arguments for this program to a given parser."""
    parser.add_argument('sequence', nargs='+', type=str, metavar="SEQID:PATH",
                        help='process sequences given as <sequence id>:<path '
                        'to file>, e.g. MR_Flair:path/to/file.nii.gz')
    parser.add_argument('--id', '-i', type=str, required=True,
                        help='use given string as case identifier, e.g. for'
                        ' naming the ouput folder')
    parser.add_argument('--skullstripped', action='store_true', help='if flag'
                        ' is set skullstripping will be skipped during'
                        ' preprocessing  and a brainmask will be used for'
                        ' standardbrain registration, if possible.')
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
