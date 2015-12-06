"""This module contains interface classes for the NiftyReg collection."""

import os
import nipype.interfaces.base as base


class _AladinInputSpec(base.CommandLineInputSpec):
    ref_image = base.File(desc='Filename of the reference (target) image',
                          mandatory=True, exists=True, argstr='-ref %s',
                          position=0)
    flo_image = base.File(desc='Filename of the floating (source) image',
                          mandatory=True, exists=True, argstr='-flo %s',
                          position=1)
    symmetric = base.traits.Bool(desc='Use symmetric version of the algorithm',
                                 argstr='-sym')
    affine = base.File(desc='Filename which contains the output affine '
                       'transformation [outputAffine.txt] ', argstr='-aff %s')
    rigid_only = base.traits.Bool(desc='Perform a rigid registration only (r'
                                  'igid+affine by default)', argstr='-rigOnly')
    affine_direct = base.traits.Bool(desc='Directly optimize 12 DoF affine '
                                     '[default: rigid initially then affine]',
                                     argstr='-affDirect')
    input_affine = base.File(desc='Filename which contains an input affine '
                             'transformation (Affine*Reference=Floating)',
                             exists=True, argstr='-inaff %s')
    input_affine_flirt = base.File(desc='Filename which contains an input '
                                   'affine transformation from Flirt',
                                   exists=True, argstr='-affFlirt %s')
    rmask_file = base.File(desc='Filename of a mask image in the reference '
                           'space', exists=True, argstr='-rmask %s')
    fmask_file = base.File(desc='Filename of a mask image in the floating '
                           'space. Only used when symmetric turned on',
                           exists=True, argstr='-fmask %s')
    result_file = base.File(desc='Filename of the resampled image '
                            '[outputResult.nii]', argstr='-res %s')
    max_iterations = base.traits.Int(desc='Number of iterations per level [5]',
                                     argstr='maxit %i')
    smooth_ref = base.traits.Float(desc='Smooth the reference image using the '
                                   'specified sigma (mm) [0]',
                                   argstr='-smooR %f')
    smooth_flo = base.traits.Float(desc='Smooth the floating image using the '
                                   'specified sigma (mm) [0]',
                                   argstr='-smooR %f')
    number_levels = base.traits.Int(desc='Number of levels to perform [3]',
                                    argstr='-ln %i')
    perform_levels = base.traits.Int(desc='Only perform the first levels [ln]',
                                     argstr='-lp %i')
    nac = base.traits.Bool(desc='Use the nifti header origins to initialise '
                           'the translation', argstr='-nac')
    block_percentage = base.traits.Int(desc='Percentage of block to use [50]',
                                       argstr='-%%v %i')
    inlier_percentage = base.traits.Int(desc='Percentage of inliers for the '
                                        'LTS [50]', argstr='-%%i %i')


class _AladinOutputSpec(base.TraitedSpec):
    affine = base.File(desc='Filename which contains the output affine '
                       'transformation [outputAffine.txt] ', argstr='-aff %s')
    result_file = base.File(desc='Filename of the resampled image '
                            '[outputResult.nii]', argstr='-res %s')


class Aladin(base.CommandLine):
    """Interface for the reg_aladin program."""

    input_spec = _AladinInputSpec
    output_spec = _AladinOutputSpec
    cmd = 'reg_aladin'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if base.isdefined(self.inputs.affine):
            outputs['affine'] = self.inputs.affine
        else:
            outputs['affine'] = os.path.abspath('outputAffine.txt')

        if base.isdefined(self.inputs.result_file):
            outputs['result_file'] = self.inputs.result_file
        else:
            outputs['result_file'] = os.path.abspath('outputResult.nii')

        return outputs


class _F3DInputSpec(base.CommandLineInputSpec):
    ref_image = base.File(
        desc='Filename of the reference image', exists=True, mandatory=True,
        argstr='-ref %s', position=0)
    flo_image = base.File(
        desc='Filename of the floating image', exists=True, mandatory=True,
        argstr='-flo %s', position=1)
    # initial transformation options (only one will be considered)
    in_affine = base.File(
        desc='Filename which contains an affine transformation '
        '(Affine*Reference=Floating)', exists=True, argstr='-aff %s',
        xor=['in_affFlirt', 'in_cpp'])
    in_affFlirt = base.File(
        desc='Filename which contains a flirt affine transformation (Flirt '
        'from the FSL package)', exists=True, argstr='-affFlirt %s',
        xor=['in_affine', 'in_cpp'])
    in_cpp = base.File(
        desc='Filename ofl control point grid input. The coarse spacing '
        'is defined by this file.', exists=True, argstr='-incpp %s',
        xor=['in_affine', 'in_affFlirt'])
    # output options
    cpp_file = base.File(desc='Filename of control point grid [outputCPP.nii]',
                         argstr='-cpp %s')
    result_file = base.File(desc='Filename of the resampled image '
                            '[outputResult.nii]', argstr='-res %s')
    # input image options (incomplete)
    rmask_file = base.File(
        desc='Filename of a mask image in the reference space', exists=True,
        argstr='-rmask %s')
    smooth_ref = base.traits.Float(
        desc='Smooth the reference image using the specified sigma (mm) [0]',
        argstr='-smooR %f')
    smooth_flo = base.traits.Float(
        desc='Smooth the floating image using the specified sigma (mm) [0]',
        argstr='-smooF %f')
    # spline options (not yet implemented)
    # objective function options (not yet implemented)
    # optimisation options (not yet implemented)
    # F3D_SYM options
    symmetric = base.traits.Bool(desc='Use symmetric approach', argstr='-sym')
    fmask_file = base.File(desc='Filename of a mask image in the floating '
                           'space. Only used when symmetric turned on',
                           exists=True, argstr='-fmask %s')
    inverse_consistency = base.traits.Float(
        desc='Weight of the inverse consistency penalty term [0.01]',
        argstr='-ic %f')
    # F3D2 options (not yet implemented)
    # other options (incomplete)
    verbose_off = base.traits.Bool(desc='Turn verbose off', argstr='-voff')


class _F3DOutputSpec(base.TraitedSpec):
    cpp_file = base.File(desc='Filename of control point grid [outputCPP.nii]')
    result_file = base.File(
        desc='Filename of the resampled image [outputResult.nii]')


class F3D(base.CommandLine):
    """Provides an (incomplete) interface for the reg_f3d program."""

    input_spec = _F3DInputSpec
    output_spec = _F3DOutputSpec
    cmd = 'reg_f3d'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if base.isdefined(self.inputs.cpp_file):
            outputs['cpp_file'] = self.inputs.cpp_file
        else:
            outputs['cpp_file'] = os.path.abspath('outputCPP.nii')

        if base.isdefined(self.inputs.result_file):
            outputs['result_file'] = self.inputs.result_file
        else:
            outputs['result_file'] = os.path.abspath('outputResult.nii')

        return outputs


class _ResampleInputSpec(base.CommandLineInputSpec):
    ref_image = base.File(
        desc='Filename of the reference image', exists=True, mandatory=True,
        argstr='-ref %s', position=0)
    flo_image = base.File(
        desc='Filename of the floating image', exists=True, mandatory=True,
        argstr='-flo %s', position=1)
    # only one option of the following will be taken into account
    in_affine = base.File(
        desc='Filename which contains an affine transformation '
        '(Affine*Reference=floating)', exists=True, mandatory=True,
        argstr='-aff %s', xor=['in_affFlirt', 'in_cpp', 'in_def'])
    in_affFlirt = base.File(
        desc='Filename which contains a radiological flirt affine '
        'transformation', exists=True, mandatory=True, argstr='-affFlirt %s',
        xor=['in_affine', 'in_cpp', 'in_def'])
    in_cpp = base.File(
        desc='Filename of the control point grid image (from reg_f3d)',
        exists=True, mandatory=True, argstr='-cpp %s',
        xor=['in_affine', 'in_affFlirt', 'in_def'])
    in_def = base.File(
        desc='Filename of the deformation field image (from reg_transform)',
        exists=True, mandatory=True, argstr='-def %s',
        xor=['in_affine', 'in_affFlirt', 'in_cpp'])
    # output options
    result_file = base.File(
        'outputResult.nii', desc='Filename of the resampled image '
        '[outputResult.nii]', argstr='-res %s', usedefault=True)
    # others
    interpolation_order = base.traits.Enum(
        '0', '1', '3', '4', desc='Interpolation order (0, 1, 3, 4)[3] (0=NN, '
        '1=LIN; 3=CUB, 4=SINC)', argstr='-inter %s')


class _ResampleOutputSpec(base.TraitedSpec):
    result_file = base.File(
        'outputResult.nii', desc='Filename of the resampled image '
        '[outputResult.nii]')


class Resample(base.CommandLine):
    """Interface for the reg_resample program."""

    input_spec = _ResampleInputSpec
    output_spec = _ResampleOutputSpec
    cmd = 'reg_resample'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['result_file'] = self.inputs.result_file
        return outputs
