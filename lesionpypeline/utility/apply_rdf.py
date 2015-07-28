#!/usr/bin/python

"""
Apply an RDF to a case.
arg1: the decision forest file
arg2: the case folder holding the feature files
arg3: the cases mask file
arg4: file containing a struct identifying the features to use
arg5: the target segmentation file
arg6: the target probability file
"""

import os
import sys
import imp
import pickle
import numpy

from scipy.ndimage.morphology import binary_fill_holes, binary_dilation
from scipy.ndimage.measurements import label

from medpy.io import load, save
from medpy.features.utilities import join

# constants
n_jobs = 6
probability_threshold = 0.5

def apply_rdf(forest_file, case_folder, mask_file, feature_cnf_file, segmentation_file, probability_file):
	# load features to use and create proper names from them
	features_to_use = load_feature_names(feature_cnf_file)

        # loading case features
	feature_vector = []

	for feature_name in features_to_use:
		_file = os.path.join(case_folder, '{}.npy'.format(feature_name))
		if not os.path.isfile(_file):
			raise Exception('The feature "{}" could not be found in folder "{}". Breaking.'.format(feature_name, case_folder))
		with open(_file, 'r') as f:
			feature_vector.append(numpy.load(f))
	feature_vector = join(*feature_vector)
	if 1 == feature_vector.ndim:
		feature_vector = numpy.expand_dims(feature_vector, -1)

	# load and apply the decision forest
	with open(forest_file, 'r') as f:
		forest = pickle.load(f)
	probability_results = forest.predict_proba(feature_vector)[:,1]
	classification_results = probability_results > probability_threshold # equivalent to forest.predict

	# preparing  image
	m, h = load(mask_file)
    	m = m.astype(numpy.bool)
    	oc = numpy.zeros(m.shape, numpy.uint8)
	op = numpy.zeros(m.shape, numpy.float32)
    	oc[m] = numpy.squeeze(classification_results).ravel()
	op[m] = numpy.squeeze(probability_results).ravel()

	# applying the post-processing morphology
	oc = binary_fill_holes(oc)

	# saving the results
    	save(oc, segmentation_file, h, True)
    	save(op, probability_file, h, True)

def feature_struct_entry_to_name(fstruct):
	seq, fcall, fargs, _ = fstruct
	return 'feature.{}.{}.{}'.format(seq, fcall.func_name, '_'.join(['arg{}'.format(i) for i in fargs]))
	
def load_feature_struct(f):
	"Load the feature struct from a feature config file."
	d, m = os.path.split(os.path.splitext(f)[0])
	f, filename, desc = imp.find_module(m, [d])
	return imp.load_module(m, f, filename, desc).features_to_extract

def load_feature_names(f):
	"Load the feature names from a feature config file."
	fs = load_feature_struct(f)
	return [feature_struct_entry_to_name(e) for e in fs]

if __name__ == "__main__":
	forest_file = sys.argv[1]
	case_folder = sys.argv[2]
	mask_file = sys.argv[3]
	feature_cnf_file = sys.argv[4]
	segmentation_file = sys.argv[5]
	probability_file = sys.argv[6]

	apply_rdf(forest_file, case_folder, mask_file, feature_cnf_file, segmentation_file, probability_file)
