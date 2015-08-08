#!/usr/bin/python

import os
import sys
import imp
import numpy
import itertools
import medpy.io as mio

target_dtype = numpy.float32
"""type: Numpy-datatype to use for saving the extracted feature vector"""

def extract_features(features, image_paths, mask_file, out_dir):
    """Extract features from the given images, according to the given feature configuration.

    Args:
        features (dict): Dictionary where keys are sequence identifiers and values are tuples
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

    for sequence, features in features.items():
        image, header = mio.load(image_paths[sequence])
        for function_to_apply, kwargs, voxelspacing in features:
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
        numpy.save(f, feature_vector.astype(target_dtype))
