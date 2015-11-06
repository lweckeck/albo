
"""Contains functions for segmenting lesions using a classifier."""

import lesionpypeline.log as logging
import lesionpypeline.config as config
import nipype.caching.memory as mem

import lesionpypeline.interfaces.classifier

log = logging.get_logger(__name__)


def segment(sequences, mask):
    """Segment the lesions in the given images."""
    log.info('Extracting features...')
    features = extract_features(sequences, mask)

    log.info('Applying classifier...')
    segmentation_image, probability_image = apply_rdf(features, mask)

    return segmentation_image, probability_image


def extract_features(sequence_paths, mask_file):
    """Extract features from given images.

    Parameters
    ----------
    sequence_paths : dict[string, string]
        Dictionary mapping sequence identifier to sequence file path
    mask_file : string
        Path to mask file used to mask feature extraction

    Returns
    -------
    string
        Path to output directory containing the extracted features
    """
    log.debug('extract_features called with parameters:\n'
              '\tsequence_paths = {}\n'
              '\tmask_file = {}'.format(sequence_paths, mask_file))
    _extract_features = mem.PipeFunc(
        lesionpypeline.interfaces.classifier.ExtractFeatures,
        config.conf['pipeline']['cache_dir'])
    config_file = config.conf['segmentation']['feature_config_file']

    result = _extract_features(
        sequence_paths=sequence_paths, config_file=config_file,
        mask_file=mask_file, out_dir='.')
    return result.outputs.out_dir


def apply_rdf(feature_dir, mask_file):
    """Apply random decision forest algorithm to given feature set.

    Parameters
    ----------
    feature_dir : string
        Path to a directory containing the extracted features to use
        for classification
    mask_file : string
        Path to mask that was used for feature extraction

    Returns
    -------
    string
        Path to binary classification image
    string
        Path to probabilistic classification image
    """
    log.debug('apply_rdf called with parameters:\n'
              '\tfeature_dir = {}\n'
              '\tmask_file = {}'.format(feature_dir, mask_file))
    _apply_rdf = mem.PipeFunc(
        lesionpypeline.interfaces.classifier.ApplyRdf,
        config.conf['pipeline']['cache_dir'])
    config_file = config.conf['segmentation']['feature_config_file']
    classifier_file = config.conf['segmentation']['classifier_file']

    result = _apply_rdf(forest_file=classifier_file,
                        feature_config_file=config_file,
                        in_dir=feature_dir, mask_file=mask_file)
    return (result.outputs.out_file_segmentation,
            result.outputs.out_file_probabilities)
