import os
import numpy
import nipype.interfaces.base as base
import nipype.interfaces.io as nio
import lesionpypeline.utility.fileutil as futil
import lesionpypeline.utility.niftimodifymetadata as nmmd
import lesionpypeline.utility.condenseoutliers as cdo
import lesionpypeline.utility.extract_features as exf
import lesionpypeline.utility.apply_rdf as rdf

import medpy.io as mio


class NiftiModifyMetadataInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to modify', exists=True, mandatory=True)
    tasks = base.traits.ListStr(desc='the changes to make in order of appearance', mandatory=True)

class NiftiModifyMetadataOutputSpec(base.TraitedSpec):
    out_file = base.File(desc='the modified image', exists=True)

class NiftiModifyMetadata(base.BaseInterface):
    input_spec = NiftiModifyMetadataInputSpec
    output_spec = NiftiModifyMetadataOutputSpec

    def _run_interface(self, runtime):
        image = self.inputs.in_file
        tasks = self.inputs.tasks

        nmmd.nifti_modifiy_metadata(image, tasks)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.in_file
        return outputs

class CondenseOutliersInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to threshold', exists=True, mandatory=True)
    out_file = base.File(desc='the output image location')

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

        cdo.condense_outliers(in_file, out_file)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            in_file = self.inputs.in_file
            return futil.append_file_postfix(in_file, '_condensedoutliers')

class ExtractFeaturesInputSpec(base.DynamicTraitedSpec):
    mask_file = base.File(desc='Image mask, features are only extracted where mask has 1 values', mandatory=True, exists=True)
    out_dir = base.Directory(desc='Target folder to store the extracted features')
    config_file = base.File(desc='Configuration file, containing a struct called features_to_extract that follows a special syntax', mandatory=True, exists=True)
    
class ExtractFeaturesOutputSpec(base.TraitedSpec):
    out_dir = base.File(desc='Directory containing the extracted features')
    
class ExtractFeatures(nio.IOBase):
    input_spec = ExtractFeaturesInputSpec
    output_spec = ExtractFeaturesOutputSpec

    _sequences = []

    def __init__(self, sequences, **inputs):
        super(ExtractFeatures, self).__init__(**inputs)
        
        self._sequences = sequences
        # use add_class_trait
        nio.add_traits(self.inputs, sequences, base.File)
        self.inputs.set(**inputs)
            
    def _run_interface(self, runtime):
        features = exf.load_feature_config(self.inputs.config_file)
        image_paths = {sequence: self.inputs.get()[sequence] for sequence in self._sequences}
        mask_file = self.inputs.mask_file
        out_dir = os.path.abspath(self.inputs.out_dir)

        exf.extract_features(features, image_paths, mask_file, out_dir)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_dir'] = os.path.abspath(self.inputs.out_dir)
        return outputs

class ApplyRdfInputSpec(base.BaseInterfaceInputSpec):
    forest_file = base.File(desc='the decision forest file', mandatory=True, exists=True)
    in_dir = base.Directory(desc='the directory holding the feature files', mandatory=True, exists=True)
    mask_file = base.File(desc='the mask file indicating on which voxels to operate', mandatory=True, exists=True)
    feature_config_file = base.File(desc='the file containing a struct indicating the features to use', mandatory=True, exists=True)
    out_file_segmentation = base.File(desc='the target segmentation file', value=os.path.abspath('./SEGMENTATION.out'))
    out_file_probabilities = base.File(desc='the target probability file', value=os.path.abspath('./PROBABILITIES.out'))

class ApplyRdfOutputSpec(base.TraitedSpec):
    out_file_segmentation = base.File(desc='the file containing the resulting segmentation', exists=True)
    out_file_probabilities = base.File(desc='the file containing the resulting probabilities', exists=True)

class ApplyRdf(base.BaseInterface):
    input_spec = ApplyRdfInputSpec
    output_spec = ApplyRdfOutputSpec

    def _run_interface(self, runtime):
        rdf.apply_rdf(
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

class ApplyMaskInputSpec(base.BaseInterfaceInputSpec):
    in_file = base.File(desc='the image file to apply the mask to', exists=True, mandatory=True)
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

        image, header = mio.load(in_file)
        mask, _ = mio.load(mask_file)

        image[~(mask.astype(numpy.bool))] = 0
        mio.save(image, out_file, header)
        
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            in_file = self.inputs.in_file
            return futil.append_file_postfix(in_file, '_masked')
