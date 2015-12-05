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

    relevant_sequences = {key: sequence for key, sequence in sequences.items()
                          if key in best_classifier.sequences}
    if set(relevant_sequences.keys()) != set(sequences.keys()):
        log.warning('The best available classifier will only use the subset {}'
                    ' of available sequences!'
                    .format(relevant_sequences.keys()))

    log.debug('sequences = {}'.format(repr(sequences)))
    log.debug('classifier = {}'.format(best_classifier))
    _setup(args, best_classifier)
    process_case(relevant_sequences)

    if os.path.isfile(logging.global_log_file):
        shutil.move(logging.global_log_file,
                    os.path.join(config.get().output_dir,
                                 args.id + '_sucessful.log'))
    log.info('Done.')
    sys.exit()


def process_case(sequences):
    """Run pipeline for given sequences."""
    # -- run pipeline
    resampled = wf.resample(sequences)
    skullstripped, brainmask = wf.skullstrip(resampled)
    bfced = wf.correct_biasfield(skullstripped, brainmask)
    preprocessed = wf.standardize_intensityrange(bfced, brainmask)
    segmentation, probability = wf.segment(preprocessed, brainmask)

    # -- preprocessed files
    for key in preprocessed:
        output(preprocessed[key])

    # -- brainmask
    output(brainmask, 'brainmask.nii.gz')

    # -- segmentation results
    output(segmentation, 'segmentation.nii.gz')
    output(segmentation, 'probability.nii.gz')


def output(filepath, save_as=None, prefix='', postfix=''):
    """Copy given file to output folder.

    If save_as is given, the file is saved with that name, otherwise the
    original filename is kept. Prefix and postfix are added in any case, where
    the postfix will be added between filename and file extension.
    """
    filename = save_as if save_as is not None else os.path.basename(filepath)

    components = filename.split('.')
    components[0] += postfix
    filename = prefix + '.'.join(components)

    out_path = os.path.join(config.get().output_dir, filename)
    if os.path.isfile(out_path):
        os.remove(out_path)
    shutil.copy2(filepath, out_path)


def _parse_args():
    parser = argparse.ArgumentParser(description='Run the lesion detection'
                                     ' pipeline.')
    parser.add_argument('sequence', nargs='+', type=str, metavar="SEQID:PATH",
                        help='process sequences given as <sequence id>:<path '
                        'to file>, e.g. MR_Flair:path/to/file.nii.gz')
    parser.add_argument('--id', '-i', type=str, required=True,
                        help='use given string as case identifier, e.g. for'
                        ' naming the ouput folder')
    parser.add_argument('--config', '-c', type=str,
                        default=os.path.join(os.path.dirname(__file__),
                                             'pipeline.conf'),
                        help='pipeline configuration file '
                        '(default: pipeline.conf')
    parser.add_argument('--force', '-f', action='store_true',
                        help='overwrite output directory if already present')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', action='store_true')
    return parser.parse_args()


def _setup(args, classifier):
    # setup logging
    if args.debug:
        logging.set_global_level(logging.DEBUG)
        logging.set_nipype_level(logging.DEBUG)
    elif args.verbose:
        logging.set_global_level(logging.INFO)
        logging.set_nipype_level(logging.INFO)
    else:
        logging.set_global_level(logging.INFO)
        logging.set_nipype_level(logging.WARNING)

    logging.set_global_log_file(args.id + '_incomplete.log')

    # init config
    config.get().read_config_file(args.config)
    config.get().classifier = classifier

    output_path = os.path.join(config.get().output_dir, args.id)
    if os.path.isdir(output_path) and os.listdir(output_path) != []:
        if args.force:
            shutil.rmtree(output_path)
        else:
            log.error('There already is an output directory for the given ID.'
                      ' Use --force/-f to override.')
            sys.exit(1)
    config.get().output_dir = output_path


if __name__ == '__main__':
    main()
