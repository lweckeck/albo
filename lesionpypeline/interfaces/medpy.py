import nipype.interfaces.base as base
import os

class MedpyResampleInputSpec(base.CommandLineInputSpec):
    in_file = base.File(desc="the input image", position=0, exists=True, mandatory=True, argstr="%s")
    # file extension in name_template necessary because flag keep_extension does not seem to work
    out_file = base.File(desc="the output image", position=1, argstr="%s", hash_files=False,
                         name_source=["in_file"], name_template="%s_resampled.nii.gz")
    spacing = base.traits.String(desc="the desired voxel spacing in colon-separated values, e.g. 1.2,1.2,5.0",
                                 position=2, mandatory=True, argstr="%s")

class MedpyResampleOutputSpec(base.TraitedSpec):
    out_file = base.File(desc="the output image", exists=True)

class MedpyResampleTask(base.CommandLine):
    input_spec = MedpyResampleInputSpec
    output_spec = MedpyResampleOutputSpec
    cmd = "medpy_resample.py"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs
