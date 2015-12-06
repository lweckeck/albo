"""Nipype interface for CMTK MRBias program."""
import os

import nipype.interfaces.base as base


class _MRBiasInputSpec(base.CommandLineInputSpec):
    in_file = base.File(desc='the input image', exists=True, mandatory=True,
                        argstr='%s', position=-2)
    out_file = base.File(desc='the output image', argstr='%s', position=-1,
                         genfile=True)
    mask_file = base.File(desc='binary foreground mask', exists=True,
                          argstr='--mask %s')


class _MRBiasOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the output image')


class MRBias(base.CommandLine):
    """Minimal interface for the cmtk mrbias program."""

    input_spec = _MRBiasInputSpec
    output_spec = _MRBiasOutputSpec
    cmd = 'cmtk mrbias'

    def _gen_filename(self, name):
        if name == 'out_file':
            filename = os.path.basename(self.inputs.in_file)
            if filename.endswith('.nii'):
                filename += '.gz'
            return os.path.join(os.getcwd(), filename)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_filename('out_file')

        return outputs
