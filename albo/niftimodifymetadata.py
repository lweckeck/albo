#!/usr/bin/python

"""
Modifies a NifTi file's metadata in place.

arg1: the image to modify
arg2+: the changes to make in order of appearance
    qfc=x : set qform_code = x
    sfc=x : set sform_code = x
    qfc=sfc : set sform_code = qform_code
    sfc=qfc : set sform_code = qform_code
    qf=dia : set qform = diag(spacing)
    sf=dia : set sform = diag(spacing)
    qf=sf : set qform = sform
    sf=qf : set sform = qform
    qf=aff : set qform = affine
    sf=aff : set sform = affine
"""

import sys
import numpy
import operator
import medpy.io as mio

SETTER = {
    'qfc': lambda h, v: operator.setitem(h.get_header(), 'qform_code', v),
    'sfc': lambda h, v: operator.setitem(h.get_header(), 'sform_code', v),
    'qf': lambda h, v: h.set_qform(v),
    'sf': lambda h, v: h.set_sform(v),
}
GETTER = {
    'qfc': lambda h: h.get_header()['qform_code'],
    'sfc': lambda h: h.get_header()['sform_code'],
    'qf': lambda h: h.get_qform(),
    'sf': lambda h: h.get_sform(),
    'aff': lambda h: h.get_affine(),
    'dia': lambda h: numpy.diag(list(mio.header.get_pixel_spacing(h)+[1])),
}


def nifti_modify_metadata(image_file, tasks):
    """Modify metadata of image_file.

    See module docstring for list of possible tasks.
    """
    image, header = mio.load(image_file)

    for task in tasks:
        field, value = task.split('=')
        if value in GETTER:
            SETTER[field](header, GETTER[value](header))
        else:
            SETTER[field](header, int(value))

    mio.save(image.copy(), image_file, header)


if __name__ == "__main__":
    image_file = sys.argv[1]
    tasks = sys.argv[2:]

    nifti_modify_metadata(image_file, tasks)
