#!/usr/bin/python

import os
import sys
import imp
import pickle
import numpy

from scipy.ndimage.morphology import binary_fill_holes, binary_dilation
from scipy.ndimage.measurements import label

from medpy.io import load, save
from medpy.features.utilities import join

import lesionpypeline.utility.extract_features as exf

PROBABILITY_THRESHOLD = 0.5

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

    features = exf.load_feature_config(feature_config_file)
    feature_filenames = get_feature_filenames(features)
    
    # loading case features
    feature_vector = []
    for filename in feature_filenames:
        _file = os.path.join(feature_folder, '{}.npy'.format(filename))
        if not os.path.isfile(_file):
            raise Exception('The feature "{}" could not be found in folder "{}".'.format(filename, feature_folder))
        with open(_file, 'r') as feature_file:
            feature_vector.append(numpy.load(feature_file))
            
    feature_vector = join(*feature_vector)
    if feature_vector.ndim == 1:
        feature_vector = numpy.expand_dims(feature_vector, -1)

    # load and apply the decision forest
    with open(forest_file, 'r') as f:
        forest = pickle.load(f)
        probability_results = forest.predict_proba(feature_vector)[:,1]
        classification_results = probability_results > PROBABILITY_THRESHOLD # equivalent to forest.predict

    # prepare result images to save to disk
    mask, header = load(mask_file)
    mask = mask.astype(numpy.bool)
    out_classification = numpy.zeros(mask.shape, numpy.uint8)
    out_probabilities = numpy.zeros(mask.shape, numpy.float32)
    out_classification[mask] = numpy.squeeze(classification_results).ravel()
    out_probabilities[mask] = numpy.squeeze(probability_results).ravel()

    # apply the post-processing morphology
    out_classification = binary_fill_holes(out_classification)

    save(out_classification, segmentation_file, header, True)
    save(out_probabilities, probability_file, header, True)

def get_feature_filenames(features):
    for sequence, feature_list in features:
        for function, kwargs, _ in feature_list:
            yield exf.generate_feature_filename(sequence, function, kwargs)
