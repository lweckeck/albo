#!/usr/bin/env python
"""Script to update atlas overlaps."""
import os
import sys
import argparse

import albo.config as config
import albo.log as logging
import albo.atlases as atl

log = logging.get_logger(__name__)


def main(args):
    """Update atlas overlaps."""
    output_dir = config.get().output_dir
    if not os.path.isdir(output_dir):
        log.error('Output directory {} does not exist!'.format(output_dir))
        sys.exit(1)
    log.info('Output directory: {}'.format(output_dir))
    case_dirs = [os.path.join(output_dir, d)
                 for d in os.listdir(output_dir)
                 if os.path.isdir(os.path.join(output_dir, d))]
    for d in case_dirs:
        log.info('Updating case {}'.format(d))
        config.get().case_output_dir = d
        segmentation_path = os.path.join(d, 'standard_segmentation.nii')
        if os.path.isfile(segmentation_path):
            atl.calculate_atlas_overlaps(segmentation_path)
    log.info('Done.')


def add_arguments_to(parser):
    """Add script-specific arguments to given parser."""
    parser.add_argument('--atlas_dir', '-d', type=str,
                        help='path to atlas directory (overrides path from'
                        ' config file)')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Update atlas overlaps.")
    add_arguments_to(parser)
    args = parser.parse_args()
    main(args)
