
import os

import nipype.interfaces.base as base
import nipype.interfaces.io as nio
import lesionpypeline.classify as cfy

class ExtractFeaturesInputSpec(base.BaseInterfaceInputSpec):
    sequence_paths = base.traits.Dict(
        key_trait=base.traits.Str, value_trait=base.traits.File(exists=True),
        mandatory=True)
    mask_file = base.File(
        desc='Image mask, features are only extracted where mask has 1 values',
        mandatory=True, exists=True)
    out_dir = base.Directory(
        desc='Target folder to store the extracted features')
    config_file = base.File(
        desc='Configuration file, containing a struct called'
        'features_to_extract that follows a special syntax',
        mandatory=True, exists=True)


class ExtractFeaturesOutputSpec(base.TraitedSpec):
    out_dir = base.File(desc='Directory containing the extracted features')


class ExtractFeatures(nio.IOBase):
    input_spec = ExtractFeaturesInputSpec
    output_spec = ExtractFeaturesOutputSpec

    def _run_interface(self, runtime):
        features = cfy.load_feature_config(self.inputs.config_file)
        sequence_paths = self.inputs.sequence_paths
        mask_file = self.inputs.mask_file
        out_dir = os.path.abspath(self.inputs.out_dir)

        cfy.extract_features(features, sequence_paths, mask_file, out_dir)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_dir'] = os.path.abspath(self.inputs.out_dir)
        return outputs


class ApplyRdfInputSpec(base.BaseInterfaceInputSpec):
    forest_file = base.File(desc='the decision forest file', mandatory=True,
                            exists=True)
    in_dir = base.Directory(desc='the directory holding the feature files',
                            mandatory=True, exists=True)
    mask_file = base.File(
        desc='the mask file indicating on which voxels to operate',
        mandatory=True, exists=True)
    feature_config_file = base.File(
        desc='the file containing a struct indicating the features to use',
        mandatory=True, exists=True)
    out_file_segmentation = base.File(desc='the target segmentation file')
    out_file_probabilities = base.File(desc='the target probability file')


class ApplyRdfOutputSpec(base.TraitedSpec):
    out_file_segmentation = base.File(
        desc='the file containing the resulting segmentation', exists=True)
    out_file_probabilities = base.File(
        desc='the file containing the resulting probabilities', exists=True)


class ApplyRdf(base.BaseInterface):
    input_spec = ApplyRdfInputSpec
    output_spec = ApplyRdfOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file_segmentation):
            self.inputs.out_file_segmentation = self._gen_filename('out_file_segmentation')
        if not base.isdefined(self.inputs.out_file_probabilities):
            self.inputs.out_file_probabilities = self._gen_filename('out_file_probabilities')
        cfy.apply_rdf(
            self.inputs.forest_file,
            self.inputs.in_dir,
            self.inputs.mask_file,
            self.inputs.feature_config_file,
            self.inputs.out_file_segmentation,
            self.inputs.out_file_probabilities)

        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file_segmentation'] = self.inputs.out_file_segmentation
        outputs['out_file_probabilities'] = self.inputs.out_file_probabilities

        return outputs

    def _gen_filename(self, name):
        if name == 'out_file_segmentation':
            return os.path.abspath('./segmentation.nii.gz')
        elif name == 'out_file_probabilities':
            return os.path.abspath('./probabilities.nii.gz')
