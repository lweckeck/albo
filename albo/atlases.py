"""Calculate overlap of mask with atlas regions."""
import os
import numpy
import csv
import collections

import medpy.io as mio
import albo.config as config


def _get_atlas_files():
    atlas_dir = config.get().atlas_dir
    return [os.path.join(atlas_dir, name)
            for name in os.listdir(atlas_dir)
            if os.path.isfile(os.path.join(atlas_dir, name))
            if '.nii' in name]


def _get_region_name_map(atlas_name):
    mapping = collections.defaultdict(str)
    atlas_dir = config.get().atlas_dir
    csv_path = os.path.join(atlas_dir, atlas_name + '.csv')
    if not os.path.isfile(csv_path):
        return mapping
    with open(csv_path, 'r') as f:
        for row in csv.reader(f):
            try:
                mapping[int(row[0])] = row[1]
            except ValueError:
                pass
    return mapping


def calculate_atlas_overlaps(mask):
    """Given an image mask, calculate overlap with all available atlases."""
    atlas_files = _get_atlas_files()
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
        region_names = _get_region_name_map(atlas_name)
        out_csv_path = os.path.join(config.get().case_output_dir,
                                    atlas_name + '.csv')
        w = csv.writer(open(out_csv_path, 'w'))
        w.writerow(
            ['value', 'id', 'voxel overlap', 'mL overlap', 'percent overlap'])
        for index, number in enumerate(overlaps):
            if number != 0:
                w.writerow([index,
                            region_names[index],
                            number,
                            number * pixel_volume,
                            float(number) / region_sizes[index]])
