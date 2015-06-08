from nipype.interfaces.base import TraitedSpec, CommandLineInputSpec, CommandLine, File, traits
import os

class MedpyResampleInputSpec(CommandLineInputSpec):
    input_file = File(desc="the input image", exists=True, mandatory=True, argstr="%s")
    output_file = File(desc="the output image", mandatory=True, argstr="%s", hash_files=False)
    spacing = traits.String(desc="the desired voxel spacing in colon-separated values, e.g. 1.2,1.2,5.0", mandatory=True, argstr="%s")

class MedpyResampleOutputSpec(TraitedSpec):
    output_file = File(desc="the output image", exists=True)

class MedpyResampleTask(CommandLine):
    input_spec = MedpyResampleInputSpec
    output_spec = MedpyResampleOutputSpec
    cmd = "medpy_resample.py"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['output_file'] = os.path.abspath(self.inputs.output_file)
        return outputs
