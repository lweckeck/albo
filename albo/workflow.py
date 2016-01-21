"""Lesion segmentation workflow."""
import albo.log as logging
import albo.sequences as seq
import albo.segmentation as seg

log = logging.get_logger(__name__)


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
