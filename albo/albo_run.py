#!/usr/bin/env python
"""TODO."""

import os
import sys
import shutil
import argparse
import datetime
import pkg_resources

import classifiers
import albo.log as logging
import albo.config as config
import albo.workflow as wf


log = logging.get_logger(__name__)
now = datetime.datetime.now()

SEQUENCE_FILE_EXT = '.nii.gz'


def main(args):
    """Read parameters from console and run pipeline accordingly."""
    _setup_logging(args.verbose, args.debug, args.id)

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
    _setup_config(args.config, args.id, args.force, best_classifier)
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


def add_arguments(parser):
    """Add commandline arguments for this program to a given parser."""
    parser.add_argument('sequence', nargs='+', type=str, metavar="SEQID:PATH",
                        help='process sequences given as <sequence id>:<path '
                        'to file>, e.g. MR_Flair:path/to/file.nii.gz')
    parser.add_argument('--id', '-i', type=str, required=True,
                        help='use given string as case identifier, e.g. for'
                        ' naming the ouput folder')
    parser.add_argument('--config', '-c', type=str,
                        help='pipeline configuration file '
                        '(default: pipeline.conf')
    parser.add_argument('--force', '-f', action='store_true',
                        help='overwrite output directory if already present')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', action='store_true')


def _setup_config(config_file, case_id, overwrite, classifier):
    if config_file is None:
        config_file = pkg_resources.resource_filename(
            __name__, 'config/pipeline.conf')
    config.get().read_config_file(config_file)
    config.get().classifier = classifier

    output_path = os.path.join(config.get().output_dir, case_id)
    if os.path.isdir(output_path) and os.listdir(output_path) != []:
        if overwrite:
            shutil.rmtree(output_path)
        else:
            log.error('There already is an output directory for the given ID.'
                      ' Use --force/-f to override.')
            sys.exit(1)
    config.get().output_dir = output_path


def _setup_logging(verbose, debug, case_id):
    if debug:
        logging.set_global_level(logging.DEBUG)
        logging.set_nipype_level(logging.DEBUG)
    elif verbose:
        logging.set_global_level(logging.INFO)
        logging.set_nipype_level(logging.INFO)
    else:
        logging.set_global_level(logging.INFO)
        logging.set_nipype_level(logging.WARNING)

    logging.set_global_log_file(case_id + '_incomplete.log')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run the lesion detection pipeline.')
    add_arguments(parser)
    args = parser.parse_args()
    main(args)
