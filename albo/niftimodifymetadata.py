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
import medpy.io as mio


def nifti_modify_metadata(image_file, tasks):
    """Modify metadata of image_file.

    See module docstring for list of possible tasks.
    """
    i, h = mio.load(image_file)

    for task in tasks:
        s, g = task.split('=')
        if g in GETTER:
            SETTER[s](h, GETTER[g](h))
        else:
            SETTER[s](h, int(g))

    mio.save(i.copy(), image_file, h)


def __set_qform_code(h, v):
    h.get_header()['qform_code'] = v


def __set_sform_code(h, v):
    h.get_header()['sform_code'] = v


def __set_qform(h, v):
    h.set_qform(v)


def __set_sform(h, v):
    h.set_sform(v)


def __get_qform_code(h):
    return h.get_header()['qform_code']


def __get_sform_code(h):
    return h.get_header()['sform_code']


def __get_affine(h):
    return h.get_affine()


def __get_qform(h):
    return h.get_qform()


def __get_sform(h):
    return h.get_sform()


def __get_diagonal(h):
    return numpy.diag(list(mio.header.get_pixel_spacing(h)) + [1])

SETTER = {
    'qfc': __set_qform_code,
    'sfc': __set_sform_code,
    'qf': __set_qform,
    'sf': __set_sform,
}
GETTER = {
    'qfc': __get_qform_code,
    'sfc': __get_sform_code,
    'aff': __get_affine,
    'qf': __get_qform,
    'sf': __get_sform,
    'dia': __get_diagonal,
}

if __name__ == "__main__":
    image_file = sys.argv[1]
    tasks = sys.argv[2:]

    nifti_modify_metadata(image_file, tasks)
