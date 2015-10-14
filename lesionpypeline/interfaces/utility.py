import os
import numpy
import shutil

import nipype.interfaces.base as base
import nipype.interfaces.io as nio

import lesionpypeline.utility.niftimodifymetadata as nmmd
import lesionpypeline.classify as cfy

# does not work for some reason ("Import error: No module named io"), replaced
# with cfy.mio since import works there
# import medpy.io as mio


class NiftiModifyMetadataInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to modify', exists=True,
                        mandatory=True)
    out_file = base.File(desc='the output image location', genfile=True)
    tasks = base.traits.ListStr(desc='the changes to make in order of'
                                'appearance', mandatory=True)


class NiftiModifyMetadataOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the modified image', exists=True)


class NiftiModifyMetadata(base.BaseInterface):
    input_spec = NiftiModifyMetadataInputSpec
    output_spec = NiftiModifyMetadataOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')

        shutil.copy(self.inputs.in_file, self.inputs.out_file)
        nmmd.nifti_modifiy_metadata(self.inputs.out_file, self.inputs.tasks)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            head, tail = os.path.split(self.inputs.in_file)
            return os.path.join(os.getcwd(), tail)


class CondenseOutliersInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to threshold', exists=True,
                        mandatory=True)
    out_file = base.File(desc='the output image location', genfile=True)


class CondenseOutliersOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the modified image', exists=True)


class CondenseOutliers(base.BaseInterface):
    input_spec = CondenseOutliersInputSpec
    output_spec = CondenseOutliersOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')

        in_file = self.inputs.in_file
        out_file = self.inputs.out_file

        image, header = cfy.mio.load(in_file)
        lower, upper = numpy.percentile(image, (1, 99.9))
        image[image < lower] = lower
        image[image > upper] = upper
        cfy.mio.save(image, out_file, header)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            head, tail = os.path.split(self.inputs.in_file)
            return os.path.join(os.getcwd(), tail)


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


class ApplyMaskInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to apply the mask to',
                        exists=True, mandatory=True)
    mask_file = base.File(desc='the mask file')
    out_file = base.File(desc='the output image location')


class ApplyMaskOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the masked image', exists=True)


class ApplyMask(base.BaseInterface):
    input_spec = ApplyMaskInputSpec
    output_spec = ApplyMaskOutputSpec

    def _run_interface(self, runtime):
        if not base.isdefined(self.inputs.out_file):
            self.inputs.out_file = self._gen_filename('out_file')

        in_file = self.inputs.in_file
        mask_file = self.inputs.mask_file
        out_file = self.inputs.out_file

        image, header = cfy.mio.load(in_file)
        mask, _ = cfy.mio.load(mask_file)

        image[~(mask.astype(numpy.bool))] = 0
        cfy.mio.save(image, out_file, header)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            head, tail = os.path.split(self.inputs.in_file)
            return os.path.join(os.getcwd(), tail)
