import nipype.interfaces.base as base
import os

class MedpyResampleInputSpec(base.CommandLineInputSpec):
    in_file = base.File(desc='the input image', position=0, exists=True, mandatory=True, argstr='%s')
    # file extension in name_template necessary because flag keep_extension does not seem to work
    out_file = base.File(desc='the output image', position=1, argstr='%s',
                         name_source=['in_file'], name_template='%s_resampled.nii.gz')
    spacing = base.traits.String(desc='the desired voxel spacing in colon-separated values, e.g. 1.2,1.2,5.0',
                                 position=2, mandatory=True, argstr='%s')

class MedpyResampleOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the output image', exists=True)

class MedpyResample(base.CommandLine):
    """Provides an interface for the medpy_resample.py script"""
    input_spec = MedpyResampleInputSpec
    output_spec = MedpyResampleOutputSpec
    cmd = 'medpy_resample.py'

class MedpyIntensityRangeStandardizationInputSpec(base.CommandLineInputSpec):
    in_file = base.File(desc='The image to transform', position=-1, exists=True, mandatory=True, argstr='%s')
    out_file = base.File(desc='Save the transformed images under this location.', argstr='--save-images %s',
                         name_source=['in_file'], name_template='%s_irs.nii.gz')
    mask_file = base.File(desc='A number binary foreground mask. Alternative to supplying a threshold.', exists=True,
                          mandatory=True, xor=['threshold'], argstr='--masks %s')
    threshold = base.traits.Int(desc='All voxel with an intensity > threshold are considered as foreground. Supply either this or a mask for each image.',
                                mandatory=True, xor=['mask_file'], argstr='--threshold %d')
    lmodel = base.traits.File(desc='Location of the pickled intensity range model to load. Activated application mode.',
                              exists=True, mandatory=True, argstr='--load-model %s')
    verbose = base.traits.Bool(desc='Verbose output', argstr='-v')
    debug = base.traits.Bool(desc='Display debug information', argst='-d')
    force = base.traits.Bool(desc='Overwrite existing files', argstr='-f')

class MedpyIntensityRangeStandardizationOutputSpec(base.TraitedSpec):
      out_file = base.File(desc='The output image', exists=True)

class MedpyIntensityRangeStandardization(base.CommandLine):
    """Provides an interface for the medpy_intensity_range_standardization.py script, as of now restricted to the transformation case"""
    input_spec = MedpyIntensityRangeStandardizationInputSpec
    output_spec = MedpyIntensityRangeStandardizationOutputSpec
    cmd = 'medpy_intensity_range_standardization.py'
