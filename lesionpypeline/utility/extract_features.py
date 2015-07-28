#!/usr/bin/python

"""
Extract features from an supplied multi-spectral image according to a config file and saves them under the supplied target directory.
arg1: folder with image channels
arg2: mask image, features are only extracted for voxels where 1
arg3: the target folder to store the extracted features
arg4: the config file, containing a struct called features_to_extract that follows a special syntax

Note: Does not overwrite existing feature files.
"""

import os
import sys
import imp
import numpy
import itertools

from medpy.io import load, header

# configuration
trg_dtype = numpy.float32

def extract_features(in_dir, mask_file, out_dir, config_file):
	# loading the features to extract
	d, m = os.path.split(os.path.splitext(config_file)[0])
	f, filename, desc = imp.find_module(m, [d])
	features_to_extract = imp.load_module(m, f, filename, desc).features_to_extract

	# loading the image mask
	m = load(mask_file)[0].astype(numpy.bool)

	# extracting the required features and saving them
	for sequence, function_call, function_arguments, voxelspacing in features_to_extract:
		if not isfv(out_dir, sequence, function_call, function_arguments):
			#print sequence, function_call.__name__, function_arguments
			i, h = load('{}/{}.nii.gz'.format(in_dir, sequence))
			call_arguments = list(function_arguments)
			if voxelspacing: call_arguments.append(header.get_pixel_spacing(h))
			call_arguments.append(m)
			fv = function_call(i, *call_arguments)
			savefv(fv, out_dir, sequence, function_call, function_arguments)

def savefv(fv, trgdir, seq, fcall, fargs):
	"""Saves the supplied feature vector under a fixed naming rule."""
	name = 'feature.{}.{}.{}'.format(seq, fcall.func_name, '_'.join(['arg{}'.format(i) for i in fargs]))
	with open('{}/{}.npy'.format(trgdir, name), 'wb') as f:
		numpy.save(f, fv.astype(trg_dtype))

def isfv(trgdir, seq, fcall, fargs):
	name = 'feature.{}.{}.{}'.format(seq, fcall.func_name, '_'.join(['arg{}'.format(i) for i in fargs]))
	return os.path.exists('{}/{}.npy'.format(trgdir, name))

if __name__ == "__main__":
	in_dir = sys.argv[1]
        mask_file = sys.argv[2]
        out_dir = sys.argv[3]
        config_file = sys.argv[4]
        
        extract_features(in_dir, mask_file, out_dir, config_file)
