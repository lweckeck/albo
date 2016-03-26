"""High-level MRI sequence manipulation.

This module provides high-level functions for MRI sequence manipulation tasks.
"""
import sys

import albo.log as logging
import albo.config as config
import nipype.caching.memory as mem

import nipype.interfaces.fsl
import albo.interfaces.medpy
import albo.interfaces.cmtk
import albo.interfaces.utility


log = logging.get_logger(__name__)


def resample(in_file, pixel_spacing):
    """Resample given image.

    The spacing is defined in the context's configuration file.

    Parameters
    ----------
    in_file : string
        Path to the file to be resampled
    pixel_spacing : string
        Target pixel spacing as three comma-separated values.

    Returns
    -------
    string
        Path to the resampled file
    """
    log.debug('resample called with parameters:\n'
              '\tin_file = {}'.format(in_file))
    _resample = mem.PipeFunc(albo.interfaces.medpy.MedpyResample,
                             config.get().cache_dir)
    try:
        spacing = map(float, pixel_spacing)
    except ValueError:
        raise ValueError('The configured pixel spacing {} is invalid; must'
                         'be exactly 3 comma-separated numbers with a dot'
                         'as decimal mark!'.format(spacing))
    spacing_string = ','.join(map(str, spacing))

    result = _resample(in_file=in_file, spacing=spacing_string)
    return result.outputs.out_file


def register(moving_image, fixed_image):
    """Register moving image to fixed image.

    Registration is performed using the fsl flirt program.

    Parameters
    ----------
    moving_image : string
    Path to the image to warp.
    fixed_image : string
    Path to the image to register *moving_image* to.

    Returns
    -------
    string
        Path to the warped image
    string
        Path to the resulting transform file
    """
    log.debug('register called with parameters:\n'
              '\tmoving_image = {}\n'
              '\tfixed_image = {}'.format(moving_image, fixed_image))
    _register = mem.PipeFunc(nipype.interfaces.fsl.FLIRT,
                             config.get().cache_dir)
    result = _register(in_file=moving_image,
                       reference=fixed_image,
                       cost='mutualinfo',
                       cost_func='mutualinfo',
                       terminal_output='none')
    return result.outputs.out_file


def skullstrip(in_file):
    """Apply skullstripping to an image.

    Skullstripping is performed using the BET program.

    Parameters
    ----------
    in_file : string
        Path to the image to skullstrip

    Returns
    -------
    string
       Path to skullstripping mask.
    """
    log.debug('skullstrip called with parameters:\n'
              '\tin_file = {}'.format(in_file))
    _skullstrip = mem.PipeFunc(nipype.interfaces.fsl.BET,
                               config.get().cache_dir)
    result = _skullstrip(in_file=in_file, mask=True, robust=True,
                         output_type='NIFTI_GZ')
    return result.outputs.mask_file


def apply_mask(in_file, mask_file):
    """Apply binary mask to an image.

    Parameters
    ----------
    in_file : string
        Path to the image to mask
    mask_file : string
        Path to the mask file

    Returns
    -------
    string
        Path to the masked image
    """
    log.debug('apply_mask called with parameters:\n'
              '\tin_file = {}\n'
              '\tmask_file = {}'.format(in_file, mask_file))
    _apply_mask = mem.PipeFunc(albo.interfaces.utility.ApplyMask,
                               config.get().cache_dir)
    result = _apply_mask(in_file=in_file, mask_file=mask_file)
    return result.outputs.out_file


def correct_biasfield(in_file, mask_file, metadata_corrections=[]):
    """Perform biasfield correction and metadata correction on an image.

    Biasfield correction is performed using the CMTK mrbias program.

    Parameters
    ----------
    in_file : string
        Path to the image to perform biasfield and metadata correction on
    mask_file : string
        Path to mask file used to mask biasfield correction

    Returns
    -------
    string
        Path to the corrected image
    """
    log.debug('correct_biasfield called with parameters:\n'
              '\tin_file = {}\n'
              '\tmask_file = {}'.format(in_file, mask_file))
    _bfc = mem.PipeFunc(albo.interfaces.cmtk.MRBias,
                        config.get().cache_dir)
    _mod_metadata = mem.PipeFunc(
        albo.interfaces.utility.NiftiModifyMetadata,
        config.get().cache_dir)

    result_bfc = _bfc(in_file=in_file, mask_file=mask_file)
    result_mmd = _mod_metadata(in_file=result_bfc.outputs.out_file,
                               tasks=metadata_corrections)

    return result_mmd.outputs.out_file


def standardize_intensityrange(in_file, mask_file, model_file):
    """Perform intensity range standardization and outlier condensation.

    Intensityrange standardization is performed using the respective medpy
    program.

    Parameters
    ----------
    in_file : string
        Path to the image to perform intensityrange standardization on
    mask_file : string
        Path to mask file used to mask intensityrange standardization
    model_file : string
        Path to the intensity model file

    Returns
    -------
    string
        Path to the standardized file with condensed outliers
    """
    log.debug('standardize_intensityrange called with parameters:\n'
              '\tin_file = {}\n'
              '\tmask_file = {}\n'
              '\tmodel_file = {}'.format(in_file, mask_file, model_file))
    _irs = mem.PipeFunc(
        albo.interfaces.medpy.MedpyIntensityRangeStandardization,
        config.get().cache_dir)
    _condense_outliers = mem.PipeFunc(
        albo.interfaces.utility.CondenseOutliers,
        config.get().cache_dir)
    try:
        result_irs = _irs(in_file=in_file, out_dir='.',
                          mask_file=mask_file, lmodel=model_file)
    except RuntimeError as re:
        if "InformationLossException" in re.message:
            try:
                result_irs = _irs(in_file=in_file, out_dir='.', ignore=True,
                                  mask_file=mask_file, lmodel=model_file)
                log.warn("Loss of information may have occured when transforming"
                         " image {} to learned standard intensity space. Re-train"
                         " model to avoid this.".format(in_file))
            except RuntimeError as re2:
                if "unrecognized arguments: --ignore" in re2.message:
                    log.error(
                        "Image {} can not be transformed to the learned "
                        "standard intensity space without loss of information."
                        " Please re-train intensity models.".format(in_file))
                    sys.exit(1)
    result_co = _condense_outliers(
        in_file=result_irs.outputs.out_file)

    return result_co.outputs.out_file
