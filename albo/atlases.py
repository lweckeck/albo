"""Calculate overlap of mask with atlas regions."""
import os
import numpy
import csv

import medpy.io as mio
import albo.config as config


def _get_atlas_files(atlas_dir):
    return [os.path.join(atlas_dir, name)
            for name in os.listdir(atlas_dir)
            if os.path.isfile(os.path.join(atlas_dir, name))
            if '.nii' in name]


def calculate_atlas_overlaps(mask):
    """Given an image mask, calculate overlap with all available atlases."""
    atlas_files = _get_atlas_files(config.get().atlas_dir)
    mask, mask_header = mio.load(mask)

    xdim, ydim, zdim = mio.get_pixel_spacing(mask_header)
    pixel_volume = xdim * ydim * zdim

    for atlas_file in atlas_files:
        atlas, atlas_header = mio.load(atlas_file)
        atlas_masked = atlas.copy()
        atlas_masked[~(mask.astype(numpy.bool))] = 0

        region_sizes = numpy.bincount(atlas.ravel())
        overlaps = numpy.bincount(atlas_masked.ravel())

        atlas_name = os.path.basename(atlas_file).split('.')[0]
        csv_path = os.path.join(config.get().case_output_dir,
                                atlas_name + '.csv')
        w = csv.writer(open(csv_path, 'w'))
        w.writerow(
            ['value', 'id', 'voxel overlap', 'mL overlap', 'percent overlap'])
        for index, number in enumerate(overlaps):
            if number != 0:
                w.writerow([index, '', number, number * pixel_volume,
                            float(number) / region_sizes[index]])
