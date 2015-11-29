#!/usr/bin/env python
"""TODO."""

import os
import sys
import shutil
import argparse
import datetime

import classifiers
import lesionpypeline.log as logging
import lesionpypeline.config as config

import lesionpypeline.workflow as wf


log = logging.get_logger(__name__)
now = datetime.datetime.now()

SEQUENCE_FILE_EXT = '.nii.gz'


def main():
    """Read parameters from console and run pipeline accordingly."""
    args = _parse_args()

    sequences = dict()
    for s in args.sequence:
        identifier, path = s.split(':')
        if not os.path.isfile(path):
            log.error('The path {} given for sequence {} is not a file.'
                      .format(path, identifier))
            sys.exit(1)
        sequences[identifier] = path

    try:
        best_classifier = classifiers.best_classifier(sequences.keys())
    except ValueError as e:
        log.error(e.message)
        classifiers.print_available_classifiers()
        sys.exit(1)

    if set(best_classifier.sequences) != set(sequences.keys()):
        log.warning('The best available classifier will only use the subset {}'
                    ' of available sequences!'
                    .format(best_classifier.sequences))

    log.debug('sequences = {}'.format(repr(sequences)))
    log.debug('classifier = {}'.format(best_classifier))
    _setup_config(args, best_classifier)
    process_case(sequences)

    log.info('All done.')
    sys.exit()


def process_case(sequences):
    """Run pipeline for given sequences."""
    # -- run pipeline
    preprocessed_sequences, brainmask = wf.preprocess(sequences)
    segmentation, probability = wf.segment(preprocessed_sequences, brainmask)

    # -- store results
    output_dir = config.conf['pipeline']['output_dir']
    #    case_name = os.path.normpath(case_dir).split(os.path.sep)[-1]
    case_name = now.strftime('%Y-%m-%d_%H%M%S')
    case_output_dir = os.path.join(output_dir, case_name)

    if not os.path.isdir(case_output_dir):
        os.makedirs(case_output_dir)

    # -- preprocessed files
    for key in preprocessed_sequences:
        path = preprocessed_sequences[key]
        _, tail = os.path.split(path)
        out_path = os.path.join(case_output_dir, "preprocessed_"+tail)
        if os.path.isfile(out_path):
            os.remove(out_path)
        shutil.copy2(path, out_path)

    # -- brainmask
    out_path = os.path.join(case_output_dir, 'brainmask.nii.gz')
    if os.path.isfile(out_path):
        os.remove(out_path)
    shutil.copy2(brainmask, out_path)

    # -- segmentation results
    for path, filename in [(segmentation, 'segmentation.nii.gz'),
                           (probability, 'probability.nii.gz')]:
        out_path = os.path.join(case_output_dir, filename)
        if os.path.isfile(out_path):
            os.remove(out_path)
        shutil.copy2(path, out_path)


def _parse_args():
    parser = argparse.ArgumentParser(description='Run the lesion detection'
                                     ' pipeline.')
    parser.add_argument('sequence', nargs='+', type=str,
                        help='process sequences given as id:path, e.g. '
                        'MR_Flair:path/to/file.nii.gz')
    parser.add_argument('--config', '-c', type=str,
                        default=os.path.join(os.path.dirname(__file__),
                                             'pipeline.conf'),
                        help='pipeline configuration file '
                        '(default: pipeline.conf')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', action='store_true')

    return parser.parse_args()


def _setup_config(args, classifier):
    config.read_file(args.config)
    config.read_imported_module(classifier)

    if args.debug:
        logging.set_global_level(logging.DEBUG)
        logging.set_nipype_level(logging.DEBUG)
    elif args.verbose:
        logging.set_global_level(logging.INFO)
        logging.set_nipype_level(logging.INFO)
    else:
        logging.set_global_level(logging.INFO)
        logging.set_nipype_level(logging.WARNING)

    logging.set_global_log_file(now.strftime('%Y-%m-%d_%H%M%S.log'))
    logging.set_global_log_file('current.log')


if __name__ == '__main__':
    main()
