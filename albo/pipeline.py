"""Lesion segmentation workflow."""
import os
import shutil
import sys
import multiprocessing as mp

import albo.config as config
import albo.log as logging
import nipype.caching.memory as mem
import medpy.io as mio

import nipype.interfaces.fsl
import albo.interfaces.medpy
import albo.interfaces.cmtk
import albo.interfaces.utility
import albo.interfaces.classification
import albo.interfaces.niftyreg

log = logging.get_logger(__name__)


def segment_case(sequences, classifier, standardbrain_sequence,
                 standardbrain_path):
    """Run pipeline for given sequences."""
    # -- run preprocessing pipeline
    resampled, transforms = resample(
        sequences, classifier.pixel_spacing, classifier.registration_base)
    skullstripped, brainmask = skullstrip(
        resampled, classifier.skullstripping_base)
    bfced = correct_biasfield(skullstripped, brainmask)
    preprocessed = standardize_intensityrange(
            bfced, brainmask, classifier.intensity_models)
    for key in preprocessed:
        output(preprocessed[key])
    output(brainmask, 'brainmask.nii.gz')

    # -- perform image segmentation
    segmentation, probability = segment(
        preprocessed, brainmask, classifier.features,
        classifier.classifier_file)
    output(segmentation, 'segmentation.nii.gz')
    output(probability, 'probability.nii.gz')

    # -- register lesion mask to standardbrain
    if standardbrain_sequence == classifier.registration_base:
        _, header = mio.load(sequences[standardbrain_sequence])
        original_dims = mio.get_pixel_spacing(header)
        spacing = ','.join(map(str, original_dims))
        standard_mask = register_to_standardbrain(
            segmentation, standardbrain_path,
            sequences[standardbrain_sequence],
            auxilliary_original_spacing=spacing)
    else:
        standard_mask = register_to_standardbrain(
            segmentation, standardbrain_path,
            sequences[standardbrain_sequence],
            auxilliary_transform=transforms[standardbrain_sequence])
    output(standard_mask, 'standard_segmentation.nii')
    return standard_mask


def output(filepath, save_as=None, prefix='', postfix=''):
    """Copy given file to output folder.

    If save_as is given, the file is saved with that name, otherwise the
    original filename is kept. Prefix and postfix are added in any case, where
    the postfix will be added between filename and file extension.
    """
    filename = save_as if save_as is not None else os.path.basename(filepath)

    components = filename.split('.')
    components[0] += postfix
    filename = prefix + '.'.join(components)

    out_path = os.path.join(config.get().case_output_dir, filename)
    if os.path.isfile(out_path):
        os.remove(out_path)
    shutil.copy2(filepath, out_path)


def resample(sequences, pixel_spacing, fixed_image_key):
    """Resample and coregister the given set of sequences."""
    log.info('Resampling...')
    if fixed_image_key not in sequences:
        raise ValueError('The configured registration base sequence {} is not'
                         ' availabe in the current case: {}'
                         .format(fixed_image_key, sequences.keys()))
    # check pixelspacing format
    try:
        spacing = map(float, pixel_spacing)
        if len(spacing) != 3:
            raise ValueError
    except ValueError:
        raise ValueError('The configured pixel spacing {} is invalid; must'
                         'be exactly 3 comma-separated numbers with a dot'
                         'as decimal mark!'.format(spacing))
    spacing_string = ','.join(map(str, spacing))

    resampled = dict()
    transforms = dict()

    _resample = mem.PipeFunc(albo.interfaces.medpy.MedpyResample,
                             config.get().cache_dir)
    _register = mem.PipeFunc(nipype.interfaces.fsl.FLIRT,
                             config.get().cache_dir)

    result = _resample(in_file=sequences[fixed_image_key],
                       spacing=spacing_string)
    fixed_image = result.outputs.out_file
    resampled[fixed_image_key] = fixed_image

    for key in (sequences.viewkeys() - {fixed_image_key}):
        result = _register(in_file=sequences[key],
                           reference=fixed_image,
                           cost='mutualinfo',
                           cost_func='mutualinfo',
                           terminal_output='none')
        resampled[key] = result.outputs.out_file
        transforms[key] = result.outputs.out_matrix_file
    return resampled, transforms


def skullstrip(sequences, skullstrip_base_key):
    """Perform skullstripping and mask sequences accordingly."""
    log.info('Skullstripping...')
    if skullstrip_base_key not in sequences:
        raise ValueError('The configured skullstripping base sequence {} is'
                         ' not availabe in the current case: {}'
                         .format(skullstrip_base_key, sequences.keys()))
    _skullstrip = mem.PipeFunc(nipype.interfaces.fsl.BET,
                               config.get().cache_dir)
    _apply_mask = mem.PipeFunc(albo.interfaces.utility.ApplyMask,
                               config.get().cache_dir)

    skullstripped = dict()
    result = _skullstrip(in_file=sequences[skullstrip_base_key], mask=True,
                         robust=True,  output_type='NIFTI_GZ')
    mask = result.outputs.mask_file

    for key in sequences:
        result = _apply_mask(in_file=sequences[key], mask_file=mask)
        skullstripped[key] = result.outputs.out_file
    return skullstripped, mask


def correct_biasfield(sequences, mask, metadata_corrections=[]):
    """Correct biasfied in given sequences."""
    # -- Biasfield correction
    log.info('Biasfield correction...')
    _bfc = mem.PipeFunc(albo.interfaces.cmtk.MRBias,
                        config.get().cache_dir)
    _mod_metadata = mem.PipeFunc(
        albo.interfaces.utility.NiftiModifyMetadata,
        config.get().cache_dir)

    bfced = dict()
    for key in sequences:
        result_bfc = _bfc(in_file=sequences[key], mask_file=mask)
        result_mmd = _mod_metadata(in_file=result_bfc.outputs.out_file,
                                   tasks=metadata_corrections)
        bfced[key] = result_mmd.outputs.out_file
    return bfced


def standardize_intensityrange(sequences, mask, intensity_models):
    """Standardize intensityrange for given sequences."""
    log.info('Intensityrange standardization...')
    for key in sequences:
        if key not in intensity_models:
            raise KeyError(
                'No intensity model for sequence {} present!'.format(key))
    _irs = mem.PipeFunc(
        albo.interfaces.medpy.MedpyIntensityRangeStandardization,
        config.get().cache_dir)
    _condense_outliers = mem.PipeFunc(
        albo.interfaces.utility.CondenseOutliers,
        config.get().cache_dir)
    result = dict()
    for key in sequences:
        try:
            result_irs = _irs(in_file=sequences[key], out_dir='.',
                              mask_file=mask, lmodel=intensity_models[key])
        except RuntimeError as re:
            if "InformationLossException" in re.message:
                try:
                    result_irs = _irs(in_file=sequences[key], out_dir='.',
                                      ignore=True,
                                      mask_file=mask,
                                      lmodel=intensity_models[key])
                    log.warn("Loss of information may have occured when "
                             "transforming image {} to learned standard "
                             "intensity space. Re-train model to avoid this."
                             .format(sequences[key]))
                except RuntimeError as re2:
                    if "unrecognized arguments: --ignore" in re2.message:
                        log.error(
                            "Image {} can not be transformed to the learned "
                            "standard intensity space without loss of "
                            "information. Please re-train intensity models."
                            .format(sequences[key]))
                        sys.exit(1)
        result_co = _condense_outliers(
            in_file=result_irs.outputs.out_file)
        result[key] = result_co.outputs.out_file
    return result


def _extract_feature(kwargs):
    f = mem.PipeFunc(
        albo.interfaces.classification.ExtractFeature,
        config.get().cache_dir)
    result = f(**kwargs)
    return result.outputs.out_file


def segment(sequences, mask, features, classifier_file):
    """Segment the lesions in the given images."""
    log.info('Extracting features...')
    tasks = [dict(in_file=sequences[key], mask_file=mask,
                  function=function, kwargs=kwargs, pass_voxelspacing=vs)
             for key, function, kwargs, vs in features]
    pool = mp.Pool()
    features = pool.map(_extract_feature, tasks)

    log.info('Applying classifier...')
    _apply_rdf = mem.PipeFunc(
        albo.interfaces.classification.RDFClassifier,
        config.get().cache_dir)

    result = _apply_rdf(classifier_file=classifier_file,
                        feature_files=features, mask_file=mask)
    return result.outputs.segmentation_file, result.outputs.probability_file


def register_to_standardbrain(
        segmentation_mask, standardbrain, auxilliary_image,
        auxilliary_transform=None, auxilliary_original_spacing=None):
    """Register the given segmentation to a standard brain."""
    log.info('Standardbrain registration...')

    # 1. transform lesion mask to original t1/t2 space
    if auxilliary_transform is not None:
        _invert_transformation = mem.PipeFunc(
            albo.interfaces.utility.InvertTransformation,
            config.get().cache_dir)
        _apply_tranformation = mem.PipeFunc(
            nipype.interfaces.fsl.ApplyXfm,
            config.get().cache_dir)
        invert_result = _invert_transformation(in_file=auxilliary_transform)
        transformation_result = _apply_tranformation(
            in_file=segmentation_mask,
            in_matrix_file=invert_result.outputs.out_file,
            reference=auxilliary_image,
            interp="nearestneighbour"
        )
        segmentation_mask = transformation_result.outputs.out_file
    elif auxilliary_original_spacing is not None:
        _resample = mem.PipeFunc(albo.interfaces.medpy.MedpyResample,
                                 config.get().cache_dir)
        resample_result = _resample(
            in_file=segmentation_mask, spacing=auxilliary_original_spacing)
        segmentation_mask = resample_result.outputs.out_file

    _register_affine = mem.PipeFunc(albo.interfaces.niftyreg.Aladin,
                                    config.get().cache_dir)
    _register_freeform = mem.PipeFunc(albo.interfaces.niftyreg.F3D,
                                      config.get().cache_dir)
    _resample = mem.PipeFunc(albo.interfaces.niftyreg.Resample,
                             config.get().cache_dir)
    # 2. register t1/t2/flair to standardbrain
    affine_result = _register_affine(
        flo_image=auxilliary_image, ref_image=standardbrain
    )
    freeform_result = _register_freeform(
        flo_image=auxilliary_image, ref_image=standardbrain,
        in_affine=affine_result.outputs.affine
    )

    # 3. warp lesion mask to standardbrain
    resample_result = _resample(
        flo_image=segmentation_mask,
        ref_image=standardbrain, in_cpp=freeform_result.outputs.cpp_file,
        interpolation_order='0'
    )
    return resample_result.outputs.result_file
