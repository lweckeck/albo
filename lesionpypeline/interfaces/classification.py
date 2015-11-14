""""""
# necessary for correct import of medpy.io; otherwise python mistakes medpy.py
# in this folder for the module
from __future__ import absolute_import

import os
import numpy
import pickle
import gzip

import nipype.interfaces.base as base
import nipype.interfaces.io as nio
# import lesionpypeline.classify as cfy

import medpy.io as mio
import medpy.features.utilities as mutil
import scipy.ndimage


PROBABILITY_THRESHOLD = 0.5
"""Threshold for binary segmentation, which is calculated from the
probabilistic segmentation.
"""


class ExtractFeatureInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(
        desc='The image to extract the feature from', mandatory=True,
        exists=True)
    mask_file = base.File(
        desc='Image mask, features are only extracted where mask has 1 values',
        mandatory=True, exists=True)
    function = base.traits.Function(
        desc='The function to use for feature extraction', mandatory=True,
        nohash=True)
    kwargs = base.traits.DictStrAny(
        desc='A dictionary of keyword arguments that is passed to the feature'
        ' extraction function')
    pass_voxelspacing = base.traits.Bool(
        desc='Whether to pass the in_file`s voxel spacing to the feature '
        'extraction function or not.')
    out_file = base.File(desc='Target file name of the extracted features.',
                         hash_files=False)


class ExtractFeatureOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='The extracted feature as a numpy file.')


class ExtractFeature(base.BaseInterface):
    input_spec = ExtractFeatureInputSpec
    output_spec = ExtractFeatureOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')
        if not base.isdefined(self.inputs.pass_voxelspacing):
            self.inputs.pass_voxelspacing = False
        if not base.isdefined(self.inputs.kwargs):
            self.inputs.kwargs = dict()

        image, header = mio.load(self.inputs.in_file)
        kwargs = self.inputs.kwargs
        kwargs['mask'] = mio.load(self.inputs.mask_file)[0].astype(numpy.bool)
        if self.inputs.pass_voxelspacing:
            kwargs['voxelspacing'] = mio.header.get_pixel_spacing(header)

        feature_vector = self.inputs.function(image, **kwargs)
        with open(self.inputs.out_file, 'wb') as f:
            numpy.save(f, feature_vector.astype(numpy.float32))
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file

        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            args = self.inputs.kwargs.items()
            argstrings = ('{}{}'.format(key, value) for key, value in args
                          if key not in {'mask', 'voxelspacing'})
            _, tail = os.path.split(self.inputs.in_file)
            in_filename = tail.split('.')[0]
            filename = 'feature_{}_{}_{}.npy'.format(
                in_filename, self.inputs.function.func_name,
                '_'.join(argstrings))
            return os.path.abspath(filename)


class RDFClassifierInputSpec(base.BaseInterfaceInputSpec):
    feature_files = base.traits.List(
        desc='List of feature files. Must be in the correct order!',
        trait=base.File(exists=True), mandatory=True)
    classifier_file = base.File(
        desc='Pickled python object containing the RDF classifier to use.',
        mandatory=True, exists=True)
    mask_file = base.File(
        desc='Mask file indicating on which voxels to operate',
        mandatory=True, exists=True)
    segmentation_file = base.File(desc='the target segmentation file')
    probability_file = base.File(desc='the target probability file')


class RDFClassifierOutputSpec(base.TraitedSpec):
    segmentation_file = base.File(
        desc='the file containing the resulting segmentation', exists=True)
    probability_file = base.File(
        desc='the file containing the resulting probabilities', exists=True)


class RDFClassifier(base.BaseInterface):
    input_spec = RDFClassifierInputSpec
    output_spec = RDFClassifierOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.segmentation_file):
            self.inputs.segmentation_file = self._gen_filename(
                'segmentation_file')
        if not base.isdefined(self.inputs.probability_file):
            self.inputs.probability_file = self._gen_filename(
                'probability_file')

        features = []
        for path in self.inputs.feature_files:
            with open(path, 'r') as f:
                features.append(numpy.load(f))

        feature_vector = mutil.join(*features)
        if feature_vector.ndim == 1:
            feature_vector = numpy.expand_dims(feature_vector, -1)

        # load and apply the decision forest
        with gzip.open(self.inputs.classifier_file, 'r') as f:
            classifier = pickle.load(f)
            prob_classification = classifier.predict_proba(feature_vector)[:, 1]
            # equivalent to forest.predict
            bin_classification = prob_classification > PROBABILITY_THRESHOLD

        # prepare result images to save to disk
        mask, header = mio.load(self.inputs.mask_file)
        mask = mask.astype(numpy.bool)
        segmentation_image = numpy.zeros(mask.shape, numpy.uint8)
        segmentation_image[mask] = numpy.squeeze(bin_classification).ravel()
        probability_image = numpy.zeros(mask.shape, numpy.float32)
        probability_image[mask] = numpy.squeeze(prob_classification).ravel()

        # apply the post-processing morphology
        segmentation_image = scipy.ndimage.morphology.binary_fill_holes(
            segmentation_image)

        mio.save(segmentation_image, self.inputs.segmentation_file, header,
                 force=True)
        mio.save(probability_image, self.inputs.probability_file, header,
                 force=True)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['segmentation_file'] = self.inputs.segmentation_file
        outputs['probability_file'] = self.inputs.probability_file

        return outputs

    def _gen_filename(self, name):
        if name == 'segmentation_file':
            return os.path.abspath('segmentation.nii.gz')
        elif name == 'probability_file':
            return os.path.abspath('probabilities.nii.gz')
