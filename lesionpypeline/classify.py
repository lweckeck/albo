#!/usr/bin/python

import os
import sys
import imp
import numpy
import itertools
import pickle
import gzip

import medpy.io as mio
import medpy.features.utilities as mutil

from scipy.ndimage.morphology import binary_fill_holes, binary_dilation
from scipy.ndimage.measurements import label


TARGET_DTYPE = numpy.float32
"""type: Numpy-datatype to use for saving the extracted feature vector"""

PROBABILITY_THRESHOLD = 0.5
"""Threshold for binary segmentation, which is calculated from the probabilistic segmentation."""


def extract_features(features, image_paths, mask_file, out_dir):
    """Extract features from the given images, according to the given feature configuration.

    Args:
        features (list): list of pairs of sequence identifier and feature list. The feature list contains tuples
            (function, kwargs, voxelspacing?). function is a python function handle, kwargs a
            dictionary of named parameters, and voxelspacing? a boolean stating if the image's
            voxelspacing must be passed as an additional parameter.        
        image_paths (dict(str: str)): Dictionary that contains the paths to the images the
            features are to be extracted from as pairs "sequence_id: path".
            Sequence identifiers must be consistent with feature_config_file!
        mask_file (str): path to the mask file which restricts the area where features are extracted
        out_dir (str): path to save the resulting feature vectors to
    """

    mask = mio.load(mask_file)[0].astype(numpy.bool)

    images = {key: mio.load(image_paths[key]) for key in image_paths}
    for sequence, function_to_apply, kwargs, voxelspacing in features:
        image, header = images[sequence]
        kwargs['mask'] = mask
        if voxelspacing:
            kwargs['voxelspacing'] = mio.header.get_pixel_spacing(header)
                
        feature_vector = function_to_apply(image, **kwargs)
        filename = generate_feature_filename(sequence, function_to_apply, kwargs)
        save_feature_vector(feature_vector, out_dir, filename)

def load_feature_config(feature_config_file):
    """Loads the feature configuration dictionary from the given file.

    Args:
        feature_config_file (str): Path to a feature configuration file. The file must be a python
        module containing a dict called "features_to_extract".
    """
    directory, name = os.path.split(feature_config_file)
    module, _ = os.path.splitext(name)
    f, filename, desc = imp.find_module(module, [directory])
    features = imp.load_module(module, f, filename, desc).features_to_extract

    return features

def generate_feature_filename(sequence, function, kwargs):
    """Generates a file name for the given feature vector configuration.
    """
    argstrings = ('arg{}'.format(value) for key, value in kwargs.items()
                  if key not in {'mask', 'voxelspacing'})
    return 'feature.{}.{}.{}'.format(sequence, function.func_name, '_'.join(argstrings))

def save_feature_vector(feature_vector, target_dir, filename):
    """Saves the supplied feature vector as target_dir/filename.npy
    """
    path = '{}/{}.npy'.format(target_dir, filename)
    with open(path, 'wb') as f:
        numpy.save(f, feature_vector.astype(TARGET_DTYPE))

        
def apply_rdf(forest_file, feature_folder, mask_file, feature_config_file, segmentation_file, probability_file):
    """Apply an RDF to a case.
        
    Args:
        forest_file (str): the decision forest file
        feature_folder (str): the case folder holding the feature files
        mask_file (str): the cases mask file
        feature_config_file (str): file containing a struct identifying the features to use
        segmentation_file (str): the target segmentation file
        probability_file (str): the target probability file
    """

    features = load_feature_config(feature_config_file)
    feature_filenames = get_feature_filenames(features)
    
    # loading case features
    feature_vector = []
    for filename in feature_filenames:
        _file = os.path.join(feature_folder, '{}.npy'.format(filename))
        if not os.path.isfile(_file):
            raise Exception('The feature "{}" could not be found in folder "{}".'.format(filename, feature_folder))
        with open(_file, 'r') as feature_file:
            feature_vector.append(numpy.load(feature_file))
            
    feature_vector = mutil.join(*feature_vector)
    if feature_vector.ndim == 1:
        feature_vector = numpy.expand_dims(feature_vector, -1)

    # load and apply the decision forest
    with gzip.open(forest_file, 'r') as f:
        forest = pickle.load(f)
        probability_results = forest.predict_proba(feature_vector)[:,1]
        classification_results = probability_results > PROBABILITY_THRESHOLD # equivalent to forest.predict

    # prepare result images to save to disk
    mask, header = mio.load(mask_file)
    mask = mask.astype(numpy.bool)
    out_classification = numpy.zeros(mask.shape, numpy.uint8)
    out_probabilities = numpy.zeros(mask.shape, numpy.float32)
    out_classification[mask] = numpy.squeeze(classification_results).ravel()
    out_probabilities[mask] = numpy.squeeze(probability_results).ravel()

    # apply the post-processing morphology
    out_classification = binary_fill_holes(out_classification)

    mio.save(out_classification, segmentation_file, header, True)
    mio.save(out_probabilities, probability_file, header, True)

def get_feature_filenames(features):
    for sequence, function, kwargs, _ in features:
        yield generate_feature_filename(sequence, function, kwargs)
