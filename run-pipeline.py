#!/usr/bin/env python
"""TODO."""

import os
import sys
import shutil
import argparse
import datetime

import lesionpypeline.log as logging
import lesionpypeline.config as config

import lesionpypeline.preprocessing as pp
import lesionpypeline.segmentation as seg

log = logging.get_logger(__name__)

SEQUENCE_FILE_EXT = '.nii.gz'


def main():
    """Read parameters from console and run pipeline accordingly."""
    parser = argparse.ArgumentParser(description='Run the lesion detection'
                                     ' pipeline.')
    parser.add_argument('directories', nargs='*', type=str, metavar='dir',
                        help='collect sequence files from given case folders')
    parser.add_argument('--config', '-c', type=str,
                        default=os.path.join(os.path.dirname(__file__),
                                             'pipeline.conf'),
                        help='pipeline configuration file '
                        '(default: pipeline.conf')
    parser.add_argument('--pack', '-p', type=str, required=True,
                        help='path to classifier pack folder')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    config.read_file(args.config)
    config.read_module(args.pack)

    if args.debug:
        logging.set_global_level(logging.DEBUG)
        logging.set_nipype_level(logging.DEBUG)
    elif args.verbose:
        logging.set_global_level(logging.INFO)
        logging.set_nipype_level(logging.INFO)
    else:
        logging.set_global_level(logging.INFO)
        logging.set_nipype_level(logging.WARNING)

    now = datetime.datetime.now()
    logging.set_global_log_file(now.strftime('%Y-%m-%d_%H%M%S.log'))

    case_list = list()
    for directory in args.directories:
        if os.path.isdir(directory):
            case_list.append(directory)
        else:
            log.error('{} is not an existing directory! Omitting.'
                      .format(directory))

    log.debug('case_list = {}'.format(repr(case_list)))
    n = len(case_list)
    if n == 0:
        log.warning('No cases to process. Exiting.')
        sys.exit()

    for i, case in enumerate(case_list):
        log.info('Processsing case {}, #{} of {}...'.format(case, i+1, n))
        process_case(case)

    log.info('All done.')
    sys.exit()


def process_case(case_dir):
    """Run pipeline for given case."""
    # -- gather sequence files
    dir_contents = [os.path.join(case_dir, f) for f in os.listdir(case_dir)]
    sequence_files = [os.path.abspath(f) for f in dir_contents
                      if os.path.isfile(f)
                      if f.endswith(SEQUENCE_FILE_EXT)]

    # -- construct mapping id -> file
    sequences = dict()
    for item in sequence_files:
        # remove file extension and use result as id
        path, filename = os.path.split(item)
        sequence_id = filename[:-len(SEQUENCE_FILE_EXT)]
        sequences[sequence_id] = os.path.join(
            os.path.abspath(path), filename)

    # -- run pipeline
    preprocessed_sequences, mask = pp.preprocess(sequences)
    segmentation, probability = seg.segment(preprocessed_sequences, mask)

    # -- store results
    output_dir = config.conf['pipeline']['output_dir']
    case_name = os.path.normpath(case_dir).split(os.path.sep)[-1]
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

    # -- segmentation results
    for path, filename in [(segmentation, 'segmentation.nii.gz'),
                           (probability, 'probability.nii.gz')]:
        out_path = os.path.join(case_output_dir, filename)
        if os.path.isfile(out_path):
            os.remove(out_path)
        shutil.copy2(path, out_path)

if __name__ == '__main__':
    main()
