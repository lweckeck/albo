
"""Contains functions for segmenting lesions using a classifier."""

import lesionpypeline.log as logging
import lesionpypeline.config as config
import nipype.caching.memory as mem

import lesionpypeline.interfaces.classification

log = logging.get_logger(__name__)


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
    list[string]
        List of paths to the extracted feature files
    """
    log.debug('extract_features called with parameters:\n'
              '\tsequence_paths = {}\n'
              '\tmask_file = {}'.format(sequence_paths, mask_file))
    _extract_feature = mem.PipeFunc(
        lesionpypeline.interfaces.classification.ExtractFeature,
        config.conf['pipeline']['cache_dir'])
    feature_list = config.conf['features']

    results = [_extract_feature(
        in_file=sequence_paths[key], mask_file=mask_file, function=function,
        kwargs=kwargs, pass_voxelspacing=voxelspacing)
        for key, function, kwargs, voxelspacing in feature_list]

    return [result.outputs.out_file for result in results]


def apply_rdf(feature_files, mask_file):
    """Apply random decision forest algorithm to given feature set.

    Parameters
    ----------
    feature_files : list[string]
        List of files containing the extracted features to use
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
              '\tfeature_files = {}\n'
              '\tmask_file = {}'.format(feature_files, mask_file))
    _apply_rdf = mem.PipeFunc(
        lesionpypeline.interfaces.classification.RDFClassifier,
        config.conf['pipeline']['cache_dir'])
    classifier_file = config.conf['classifier_file']

    result = _apply_rdf(classifier_file=classifier_file,
                        feature_files=feature_files, mask_file=mask_file)
    return (result.outputs.segmentation_file,
            result.outputs.probability_file)
