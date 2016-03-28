"""Nipype interfaces for various utility functions."""
from __future__ import absolute_import

import os
import numpy
import shutil

import nipype.interfaces.base as base
import medpy.io as mio

import albo.niftimodifymetadata as nmmd


class _NiftiModifyMetadataInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to modify', exists=True,
                        mandatory=True)
    out_file = base.File(desc='the output image location', genfile=True)
    tasks = base.traits.ListStr(desc='the changes to make in order of'
                                'appearance', mandatory=True)


class _NiftiModifyMetadataOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the modified image', exists=True)


class NiftiModifyMetadata(base.BaseInterface):
    """Correct nifti metadata."""

    input_spec = _NiftiModifyMetadataInputSpec
    output_spec = _NiftiModifyMetadataOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')

        shutil.copy(self.inputs.in_file, self.inputs.out_file)
        nmmd.nifti_modify_metadata(self.inputs.out_file, self.inputs.tasks)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            head, tail = os.path.split(self.inputs.in_file)
            return os.path.join(os.getcwd(), tail)


class _CondenseOutliersInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to threshold', exists=True,
                        mandatory=True)
    out_file = base.File(desc='the output image location', genfile=True)


class _CondenseOutliersOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the modified image', exists=True)


class CondenseOutliers(base.BaseInterface):
    """Condense outliers in an image."""

    input_spec = _CondenseOutliersInputSpec
    output_spec = _CondenseOutliersOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')

        in_file = self.inputs.in_file
        out_file = self.inputs.out_file

        image, header = mio.load(in_file)
        lower, upper = numpy.percentile(image, (1, 99.9))
        image[image < lower] = lower
        image[image > upper] = upper
        mio.save(image, out_file, header)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            head, tail = os.path.split(self.inputs.in_file)
            return os.path.join(os.getcwd(), tail)


class _ApplyMaskInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to apply the mask to',
                        exists=True, mandatory=True)
    mask_file = base.File(desc='the mask file')
    out_file = base.File(desc='the output image location')


class _ApplyMaskOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the masked image', exists=True)


class ApplyMask(base.BaseInterface):
    """Apply a mask to an image."""

    input_spec = _ApplyMaskInputSpec
    output_spec = _ApplyMaskOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')

        in_file = self.inputs.in_file
        mask_file = self.inputs.mask_file
        out_file = self.inputs.out_file

        image, header = mio.load(in_file)
        mask, _ = mio.load(mask_file)

        image[~(mask.astype(numpy.bool))] = 0
        mio.save(image, out_file, header)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            head, tail = os.path.split(self.inputs.in_file)
            return os.path.join(os.getcwd(), tail)


class _InvertMaskInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the mask to invert',
                        exists=True, mandatory=True)
    out_file = base.File(desc='the output mask location')


class _InvertMaskOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the inverted mask', exists=True)


class InvertMask(base.BaseInterface):
    """Invert a given binary mask."""

    input_spec = _InvertMaskInputSpec
    output_spec = _InvertMaskOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')

        mask, header = mio.load(self.inputs.in_file)
        inverted_mask = numpy.ones(mask.shape, numpy.uint8)
        inverted_mask[mask.astype(numpy.bool)] = 0

        mio.save(inverted_mask, self.inputs.out_file, header)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return os.path.abspath('inverted_' + os.path.basename(
                self.inputs.in_file))


class _InvertTransformationInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='file containing the matrix to invert',
                        exists=True, mandatory=True)
    out_file = base.File(desc='the output matrix file location')


class _InvertTransformationOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the inverted matrix file', exists=True)


class InvertTransformation(base.BaseInterface):
    """Invert a given flirt ,mat file and convert to decimal, if necessary."""

    input_spec = _InvertTransformationInputSpec
    output_spec = _InvertTransformationOutputSpec

    def _parse(self, token):
        try:
            result = float(token)
        except ValueError:
            result = float.fromhex(token)
        return result

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')
        s = open(self.inputs.in_file)
        matrix = numpy.array([[self._parse(token)
                              for token in line.split()]
                              for line in s.readlines()])
        inverted = numpy.linalg.inv(matrix)
        numpy.savetxt(self.inputs.out_file, inverted)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return os.path.abspath('inverted_' + os.path.basename(
                self.inputs.in_file))
