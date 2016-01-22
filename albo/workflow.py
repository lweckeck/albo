"""Lesion segmentation workflow."""
import os
import shutil

import albo.config as config
import albo.log as logging
import albo.sequences as seq
import albo.segmentation as seg
import albo.standardbrainregistration as sbr

log = logging.get_logger(__name__)


def process_case(sequences, classifier):
    """Run pipeline for given sequences."""
    # -- run preprocessing pipeline
    resampled = resample(
        sequences, classifier.pixel_spacing, classifier.registration_base)
    skullstripped, brainmask = skullstrip(
        resampled, classifier.skullstripping_base)
    bfced = correct_biasfield(skullstripped, brainmask)
    preprocessed = standardize_intensityrange(
            bfced, brainmask, classifier.intensity_models)
    # -- perform image segmentation
    segmentation, probability = segment(
        preprocessed, brainmask, classifier.features,
        classifier.classifier_file)
    # -- register lesion mask to standardbrain
    if 'MR_T1' in sequences:
        t1 = sequences['MR_T1']
    elif 't1' in sequences:
        t1 = sequences['t1']
    else:
        raise Exception('No t1 sequence found!')
    standard_mask = register_to_standardbrain(segmentation, t1)

    # -- preprocessed files
    for key in preprocessed:
        output(preprocessed[key])

    # -- brainmask
    output(brainmask, 'brainmask.nii.gz')

    # -- segmentation results
    output(segmentation, 'segmentation.nii.gz')
    output(probability, 'probability.nii.gz')
    output(standard_mask, 'standard_segmentation.nii')


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

    out_path = os.path.join(config.get().output_dir, filename)
    if os.path.isfile(out_path):
        os.remove(out_path)
    shutil.copy2(filepath, out_path)


def resample(sequences, pixel_spacing, fixed_image_key):
    """Resample and coregister the given set of sequences."""
    if fixed_image_key not in sequences:
        raise ValueError('The configured registration base sequence {} is not'
                         ' availabe in the current case: {}'
                         .format(fixed_image_key, sequences.keys()))
    result = dict(sequences)
    # -- Resampling
    log.info('Resampling...')
    fixed_image = seq.resample(result[fixed_image_key], pixel_spacing)
    result[fixed_image_key] = fixed_image
    for key in (result.viewkeys() - {fixed_image_key}):
        result[key], _ = seq.register(result[key], fixed_image)
    return result


def skullstrip(sequences, skullstrip_base_key):
    """Perform skullstripping and mask sequences accordingly."""
    if skullstrip_base_key not in sequences:
        raise ValueError('The configured skullstripping base sequence {} is'
                         ' not availabe in the current case: {}'
                         .format(skullstrip_base_key, sequences.keys()))
    result = dict(sequences)
    log.info('Skullstripping...')
    mask = seq.skullstrip(result[skullstrip_base_key])

    for key in result:
        result[key] = seq.apply_mask(result[key], mask)
    return result, mask


def correct_biasfield(sequences, mask, metadata_corrections=[]):
    """Correct biasfied in given sequences."""
    # -- Biasfield correction
    log.info('Biasfield correction...')
    result = dict(sequences)
    for key in result:
        result[key] = seq.correct_biasfield(
            result[key], mask, metadata_corrections)
    return result


def standardize_intensityrange(sequences, mask, intensity_models):
    """Standardize intensityrange for given sequences."""
    for key in sequences:
        if key not in intensity_models:
            raise KeyError(
                'No intensity model for sequence {} present!'.format(key))

    result = dict(sequences)
    log.info('Intensityrange standardization...')
    for key in result:
        result[key] = seq.standardize_intensityrange(
            result[key], mask, intensity_models[key])
    return result


def segment(sequences, mask, features, classifier_file):
    """Segment the lesions in the given images."""
    log.info('Extracting features...')
    features = seg.extract_features(sequences, mask, features)

    log.info('Applying classifier...')
    segmentation_image, probability_image = seg.apply_rdf(
        features, mask, classifier_file)

    return segmentation_image, probability_image


def register_to_standardbrain(segmentation_mask, t1):
    """Register the given segmentation to a standard brain."""
    # TODO replace with proper selection
    standardbrain = '/home/lwe/Projects/lesion-pipeline/standardbrains/avg152T1.nii'

    log.info('Standardbrain registration...')
    _, affine = sbr.register_affine(t1, standardbrain)
    _, cpp = sbr.register_freeform(t1, standardbrain, in_affine=affine)
    segmentation_standardbrain = sbr.resample(
        segmentation_mask, standardbrain, cpp)

    return segmentation_standardbrain
