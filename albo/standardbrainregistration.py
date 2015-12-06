"""Functions for registering the lesion segmentation to a standard brain."""

import albo.log as logging
import albo.config as config
import nipype.caching.memory as mem

import albo.interfaces.utility
import albo.interfaces.niftyreg

log = logging.get_logger(__name__)


def register_to_standardbrain(segmentation_mask, t1):
    """Register the given segmentation to a standard brain."""
    # TODO replace with proper selection
    standardbrain = '/home/lwe/Projects/lesion-segmentation-pipeline/LesionPypeline/standardbrain/avg152T1_masked.nii'

    registration_mask = invert_mask(segmentation_mask)

    _, affine = register_affine(t1, standardbrain, registration_mask)
    _, cpp = register_freeform(t1, standardbrain, registration_mask, affine)
    segmentation_standardbrain = resample(segmentation_mask, standardbrain,
                                          cpp)

    return segmentation_standardbrain


def register_affine(floating_image, reference_image, floating_mask=None):
    """Register floating image to reference image.

    Registration is performed using the reg_aladin program of the niftyreg
    package.

    Parameters
    ----------
    floating_image : string
        Path to the image to warp.
    reference_image : string
        Path to the image to register *floating_image* to.
    floating_mask : string
        Path to mask file to mask floating image during registration.

    Returns
    -------
    string
        Path to the warped image
    string
        Path to the resulting affine transform
    """
    _register = mem.PipeFunc(albo.interfaces.niftyreg.Aladin,
                             config.get().cache_dir)
    kwargs = dict(flo_image=floating_image, ref_image=reference_image)
    if floating_mask is not None:
        kwargs['fmask_file'] = floating_mask
        kwargs['symmetric'] = True
    result = _register(**kwargs)

    return (result.outputs.result_file,
            result.outputs.affine)


def register_freeform(floating_image, reference_image, floating_mask=None,
                      in_affine=None):
    """Register floating image to reference image.

    Registration is performed using the reg_f3d program of the niftyreg
    package.

    Parameters
    ----------
    floating_image : string
        Path to the image to warp.
    reference_image : string
        Path to the image to register *floating_image* to.
    floating_mask : string
        Path to mask file to mask floating image during registration.
    in_affine : string
        Path to affine transformation file to use for initialization.

    Returns
    -------
    string
        Path to the warped image
    string
        Path to the resulting control point grid transform
    """
    _register = mem.PipeFunc(albo.interfaces.niftyreg.F3D,
                             config.get().cache_dir)
    kwargs = {'flo_image': floating_image, 'ref_image': reference_image}
    if floating_mask is not None:
        kwargs['fmask_file'] = floating_mask
        kwargs['symmetric'] = True
    if in_affine is not None:
        kwargs['in_affine'] = in_affine

    result = _register(**kwargs)

    return (result.outputs.result_file,
            result.outputs.cpp_file)


def resample(floating_image, reference_image, transform_file):
    """Register floating image to reference image using given transform.

    Resampling is performed using the reg_resample program of the niftyreg
    package.

    Parameters
    ----------
    floating_image: string
        Path to the image to warp
    reference_image: string
        Path to the reference image
    transform_file: string
        Path to the transform to use for warping

    Returns
    -------
    string
        Path to the resampled image
    """
    _resample = mem.PipeFunc(albo.interfaces.niftyreg.Resample,
                             config.get().cache_dir)
    result = _resample(
        flo_image=floating_image,
        ref_image=reference_image,
        in_cpp=transform_file,
        interpolation_order='0')
    return result.outputs.result_file


def invert_mask(mask):
    """Invert given binary mask.

    Parameters
    ----------
    mask : string
        Path to the mask to invert.

    Returns
    -------
    string
        Path to the inverted mask file.
    """
    log.debug('invert_mask called with parameters:\n'
              'mask = {}'.format(mask))

    _invert = mem.PipeFunc(albo.interfaces.utility.InvertMask,
                           config.get().cache_dir)
    result = _invert(in_file=mask)

    return result.outputs.out_file
