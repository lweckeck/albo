
"""Contains functions for performing preprocessing steps."""
import os

import lesionpypeline.log as logging
import lesionpypeline.config as config
import nipype.caching.memory as mem

import nipype.interfaces.elastix
import nipype.interfaces.fsl
import lesionpypeline.interfaces.medpy
import lesionpypeline.interfaces.cmtk
import lesionpypeline.interfaces.utility

log = logging.get_logger(__name__)

# TODO insert correct names
ADC_ID = 'adc'
DWI_ID = 'dwi'


def preprocess(sequences):
    """Execute preprocessing pipeline.

    The steps include resampling and registration to a given pixel spacing,
    skullstripping, biasfield correction and intensityrange standardization.
    """
    # -- Preparation
    fixed_image_key = config.conf['registration_base']
    skullstrip_base_key = config.conf['skullstripping_base']

    if fixed_image_key not in sequences:
        raise ValueError('The configured registration base sequence {} is not'
                         ' availabe in the current case: {}'
                         .format(fixed_image_key, sequences.keys()))
    if skullstrip_base_key not in sequences:
        raise ValueError('The configured skullstripping base sequence {} is'
                         ' not availabe in the current case: {}'
                         .format(fixed_image_key, sequences.keys()))
    intensity_models = config.conf['intensity_models']
    for key in sequences:
        if key not in intensity_models:
            raise KeyError('No intensity model for sequence {} configured in'
                           ' classifier pack!'.format(key))

    result = dict(sequences)
    # -- Resampling
    log.info('Resampling...')
    fixed_image = resample(result[fixed_image_key])
    result[fixed_image_key] = fixed_image
    for key in (result.viewkeys()
                - {fixed_image_key, ADC_ID, DWI_ID}):
        result[key], _ = register(result[key], fixed_image)

    # special case: adc is not registered to the fixed image. Instead, the
    # transformation resulting from DWI_ID registration is applied.
    if DWI_ID in result:
        result[DWI_ID], transform = register(result[DWI_ID], fixed_image)
    if ADC_ID in result:
        if transform is not None:
            result[ADC_ID] = transform(result[ADC_ID], transform)
        else:
            result[ADC_ID] = register(result[ADC_ID], fixed_image)

    # -- Skullstripping
    log.info('Skullstripping...')
    mask = skullstrip(result[skullstrip_base_key])

    for key in result:
        result[key] = apply_mask(result[key], mask)

    # -- Biasfield correction, intensityrange standardization
    log.info('Biasfield correction...')
    for key in result:
        result[key] = correct_biasfield(result[key], mask)

    log.info('Intensityrange standardization...')
    for key in result:
        result[key] = standardize_intensityrange(
            result[key], mask, intensity_models[key])

    return result, mask


def resample(in_file):
    """Resample given image.

    The spacing is defined in the context's configuration file.

    Parameters
    ----------
    in_file : string
        Path to the file to be resampled

    Returns
    -------
    string
        Path to the resampled file
    """
    log.debug('resample called with parameters:\n'
              '\tin_file = {}'.format(in_file))
    _resample = mem.PipeFunc(lesionpypeline.interfaces.medpy.MedpyResample,
                             config.conf['pipeline']['cache_dir'])
    try:
        spacing = map(float, config.conf['pixel_spacing'])
    except ValueError:
        raise ValueError('The configured pixel spacing {} is invalid; must'
                         'be exactly 3 comma-separated numbers with a dot'
                         'as decimal mark!'.format(spacing))
    spacing_string = ','.join(map(str, spacing))

    result = _resample(in_file=in_file, spacing=spacing_string)
    return result.outputs.out_file


def register(moving_image, fixed_image):
    """Register moving image to fixed image.

    Registration is performed using the elastix program. The path to the
    elastix configuration file is configured in the pipeline config file.

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
    _register = mem.PipeFunc(nipype.interfaces.elastix.Registration,
                             config.conf['pipeline']['cache_dir'])
    parameters = config.conf['pipeline']['elastix_parameter_file']
    result = _register(moving_image=moving_image,
                       fixed_image=fixed_image,
                       parameters=parameters.split(','),
                       terminal_output='none')
    # elastix gives the same name to all warped files; restore original
    # name for clarity, changing the file extension if necessary
    oldpath, oldname = os.path.split(moving_image)
    if oldname.endswith('.nii'):
        oldname += '.gz'
    newpath, newname = os.path.split(result.outputs.warped_file)
    warped_file = os.path.join(newpath, oldname)

    # if the interface has run previously, the file is already renamed
    if os.path.isfile(result.outputs.warped_file):
        os.renames(result.outputs.warped_file, warped_file)

    return (warped_file,
            result.outputs.transform)


def transform(moving_image, transform_file):
    """Apply transfrom resulting from elastix registration to an image.

    Parameters
    ----------
    moving_image : string
        Path to the image to warp
    transform_file : string
        Path to the elastix transform to apply

    Returns
    -------
    string
        Path to the warped image
    """
    log.debug('tranform called with parameters:\n'
              '\tmoving_image = {}\n'
              '\ttransform = {}'.format(moving_image, transform_file))
    _transform = mem.PipeFunc(nipype.interfaces.elastix.ApplyWarp,
                              config.conf['pipeline']['cache_dir'])
    result = _transform(moving_image=moving_image,
                        transform_file=transform_file)
    return result.outputs.warped_file


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
                               config.conf['pipeline']['cache_dir'])
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
    _apply_mask = mem.PipeFunc(lesionpypeline.interfaces.utility.ApplyMask,
                               config.conf['pipeline']['cache_dir'])
    result = _apply_mask(in_file=in_file, mask_file=mask_file)
    return result.outputs.out_file


def correct_biasfield(in_file, mask_file):
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
    _bfc = mem.PipeFunc(lesionpypeline.interfaces.cmtk.MRBias,
                        config.conf['pipeline']['cache_dir'])
    _mod_metadata = mem.PipeFunc(
        lesionpypeline.interfaces.utility.NiftiModifyMetadata,
        config.conf['pipeline']['cache_dir'])

    result_bfc = _bfc(in_file=in_file, mask_file=mask_file)
    result_mmd = _mod_metadata(in_file=result_bfc.outputs.out_file,
                               tasks=config.conf['tasks'])

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
        lesionpypeline.interfaces.medpy.MedpyIntensityRangeStandardization,
        config.conf['pipeline']['cache_dir'])
    _condense_outliers = mem.PipeFunc(
        lesionpypeline.interfaces.utility.CondenseOutliers,
        config.conf['pipeline']['cache_dir'])

    result_irs = _irs(in_file=in_file, out_dir='.',
                      mask_file=mask_file, lmodel=model_file)
    result_co = _condense_outliers(
        in_file=result_irs.outputs.out_file)

    return result_co.outputs.out_file
