
import os
import numpy
import shutil

import nipype.interfaces.base as base

import lesionpypeline.niftimodifymetadata as nmmd

# does not work for some reason ("Import error: No module named io"), replaced
# with nmmd.mio since import works there
# import medpy.io as mio


class NiftiModifyMetadataInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to modify', exists=True,
                        mandatory=True)
    out_file = base.File(desc='the output image location', genfile=True)
    tasks = base.traits.ListStr(desc='the changes to make in order of'
                                'appearance', mandatory=True)


class NiftiModifyMetadataOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the modified image', exists=True)


class NiftiModifyMetadata(base.BaseInterface):
    input_spec = NiftiModifyMetadataInputSpec
    output_spec = NiftiModifyMetadataOutputSpec

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


class CondenseOutliersInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to threshold', exists=True,
                        mandatory=True)
    out_file = base.File(desc='the output image location', genfile=True)


class CondenseOutliersOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the modified image', exists=True)


class CondenseOutliers(base.BaseInterface):
    input_spec = CondenseOutliersInputSpec
    output_spec = CondenseOutliersOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')

        in_file = self.inputs.in_file
        out_file = self.inputs.out_file

        image, header = nmmd.mio.load(in_file)
        lower, upper = numpy.percentile(image, (1, 99.9))
        image[image < lower] = lower
        image[image > upper] = upper
        nmmd.mio.save(image, out_file, header)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            head, tail = os.path.split(self.inputs.in_file)
            return os.path.join(os.getcwd(), tail)


class ApplyMaskInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to apply the mask to',
                        exists=True, mandatory=True)
    mask_file = base.File(desc='the mask file')
    out_file = base.File(desc='the output image location')


class ApplyMaskOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the masked image', exists=True)


class ApplyMask(base.BaseInterface):
    input_spec = ApplyMaskInputSpec
    output_spec = ApplyMaskOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')

        in_file = self.inputs.in_file
        mask_file = self.inputs.mask_file
        out_file = self.inputs.out_file

        image, header = nmmd.mio.load(in_file)
        mask, _ = nmmd.mio.load(mask_file)

        image[~(mask.astype(numpy.bool))] = 0
        nmmd.mio.save(image, out_file, header)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            head, tail = os.path.split(self.inputs.in_file)
            return os.path.join(os.getcwd(), tail)
