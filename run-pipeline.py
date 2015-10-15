#!/usr/bin/env python
"""TODO."""

import os
import sys
import argparse

import lesionpypeline.pipeline as lp
import lesionpypeline.log as logging

log = logging.get_logger(__name__)


def main():
    """TODO."""
    parser = argparse.ArgumentParser(description='Run the lesion detection'
                                     ' pipeline.')
    parser.add_argument('directories', nargs='*', type=str, metavar='dir',
                        help='collect sequence files from given case folders')
    parser.add_argument('--case', dest='cases', action='append', default=[],
                        nargs='+', type=str, metavar='file',
                        help='list files of a case individually (useful only'
                        ' if files are spread over multiple directories - use'
                        ' positional dir argument otherwise)')
    parser.add_argument('--config', '-c', type=str, default='./pipeline.conf',
                        help='pipeline configuration file'
                        ' (default: ./pipeline.conf')
    parser.add_argument('--clear-cache', action='store_true',
                        help='delete old runs from disk')
    args = parser.parse_args()
    log.debug('args = {}'.format(repr(args)))

    pipeline = lp.Pipeline(args.config)

    if args.clear_cache:
        log.info('Clearing cache...')
        pipeline.clear_cache()

    case_list = list()
    # add files from given directories to case list
    for directory in args.directories:
        if os.path.isdir(directory):
            paths = [os.path.join(directory, f) for f in os.listdir(directory)]
            sequence_files = [os.path.abspath(f) for f in paths
                              if os.path.isfile(f)
                              if f.endswith(lp.SEQUENCE_FILE_EXT)]
            case_list.append(sequence_files)
        else:
            raise ValueError('{} is not an existing directory!'
                             .format(directory))

    # add files from manually given cases to case list
    for case in args.cases:
        # check if all files exist
        for f in case:
            if not os.path.isfile(f):
                raise ValueError('{} is not an existing file!'
                                 .format(f))
        case_list.append(case)

    log.debug('case_list = {}'.format(repr(case_list)))
    n = len(case_list)
    if n == 0:
        print 'No cases to process.'
        sys.exit()

    for i, case in enumerate(case_list):
        log.info('Processsing case {} of {}...'.format(i+1, n))
        pipeline.run_pipeline(case)

    log.info('All done.')
    sys.exit()


if __name__ == '__main__':
    main()
