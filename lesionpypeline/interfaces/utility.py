import numpy as np
import nipype.interfaces.base as base
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
import lesionpypeline.utility.fileutil as futil
import lesionpypeline.utility.niftimodifymetadata as nmmd
import lesionpypeline.utility.condenseoutliers as cdo
import lesionpypeline.utility.extract_features as exf
import lesionpypeline.utility.apply_rdf as rdf

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

class ExtractFeaturesInputSpec(base.BaseInterfaceInputSpec):
    in_dir = base.Directory(desc='Folder with input images', mandatory=True, exists=True)
    mask_file = base.File(desc='Image mask, features are only extracted where mask has 1 values', mandatory=True, exists=True)
    out_dir = base.Directory(desc='Target folder to store the extracted features', value='.')
    config_file = base.File(desc='Configuration file, containing a struct called features_to_extract that follows a special syntax', mandatory=True, exists=True)
    
class ExtractFeaturesOutputSpec(base.TraitedSpec):
    out_dir = base.File(desc='Directory containing the extracted features', exists=True)
    
class ExtractFeatures(base.BaseInterface):
    input_spec = ExtractFeaturesInputSpec
    output_spec = ExtractFEaturesOutputSpec

    def _run_interface(self, runtime):
        in_dir = self.inputs.in_dir
        mask_file = self.inputs.mask_file
        out_dir = self.inputs.out_dir
        config_file = self.inputs.config_file

        exf.extract_features(in_dir, mask_file, out_dir, config_file)
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
    out_file_probability = base.File(desc='the target probability file', value=os.path.abspath('./PROBABILITIES.out'))

class ApplyRdfOutputSpec(base.TraitedSpec):
        out_file_segmentation = base.File(desc='the file containing the resulting segmentation', exists=True)
    out_file_probability = base.File(desc='the file containing the resulting probabilities', exists=True)

class ApplyRdf(base.BaseInterface):
    input_spec = ApplyRdfInputSpec
    output_spec = ApplyRdfOuputSpec

    def _run_interface(self, runtime):
        rdf.apply_rdf(
            self.inputs.forest_file,
            self.inputs.in_dir,
            self.inputs.mask_file,
            self.inputs.feature_config_file,
            self.inputs.out_file_segmentation,
            self.inputs.out_file_propabilities)

        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file_segmentation'] = self.inputs.out_file_segmentation
        outputs['out_file_probabilities'] = self.inputs.out_file_probabilities

        return outputs
        
class InsertInputSpec(base.BaseInterfaceInputSpec):
    """Input specification for Insert class"""
    value = base.traits.Any(desc='Value to insert into list')
    index = base.traits.Int(desc='Index to insert value before')
    inlist = base.traits.List(desc='List to insert value into')

class InsertOutputSpec(base.TraitedSpec):
    """Output specification for Insert class"""
    out = base.traits.List(desc='List with inserted value')

class Insert(nio.IOBase):
    """Basic interface class to insert a value into a list before a given index, based on python's List.insert semantics
    Examples
    --------
    >>> from lesionpypeline.interfaces.utility import Insert
    >>> ins = Insert()
    >>> ins.inputs.value = 10
    >>> ins.inputs.index = 2
    >>> ins.inputs.inlist = [0,1,2,3,4,5]
    >>> out = ins.run()
    >>> out.outputs.out
    [0, 1, 10, 2, 3, 4, 5]
    """
    input_spec = InsertInputSpec
    output_spec = InsertOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        l = self.inputs.inlist
        l.insert(self.inputs.index, self.inputs.value)
        outputs['out'] = l

        return outputs
            

class TeeInputSpec(base.BaseInterfaceInputSpec):
    """Input specification for Tee class"""
    inlist = base.InputMultiPath(base.traits.Any, mandatory=True,
                  desc='list of values to choose from')
    index = base.InputMultiPath(base.traits.Int, mandatory=True,
                           desc='0-based indices of values to send to selected, the rest goes to rejected')

class TeeOutputSpec(base.TraitedSpec):
    """Output specification for Tee class"""
    selected = base.OutputMultiPath(base.traits.Any, desc='list of values designated for selected')
    rejected = base.OutputMultiPath(base.traits.Any, desc='list of remaining values')

class Tee(nio.IOBase):
    """Basic interface class to select values from a list based on indices, and output the selected values as well as the not selected values
    Examples
    --------
    >>> from lesionpypeline.interfaces.utility import Tee
    >>> t = Tee()
    >>> t.inputs.inlist = [10,20,30,40,50]
    >>> t.inputs.index = [2,3]
    >>> out = t.run()
    >>> out.outputs.selected
    [30, 40]
    >>> out.outputs.rejected
    [10, 20, 50]
    """
    input_spec = TeeInputSpec
    output_spec = TeeOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        selected_indices = self.inputs.index
        filtered_indices = [i for i in range(len(self.inputs.inlist)) if i not in selected_indices]
        
        outputs['selected'] = [self.inputs.inlist[i] for i in selected_indices]
        outputs['rejected'] = [self.inputs.inlist[i] for i in filtered_indices]
        return outputs
        
    
