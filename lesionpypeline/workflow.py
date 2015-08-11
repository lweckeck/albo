#!/usr/bin/env python

import os
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as nutil
import nipype.interfaces.io as nio
import nipype.interfaces.elastix as elastix
import nipype.interfaces.fsl as fsl
import lesionpypeline.interfaces.medpy as medpy
import lesionpypeline.interfaces.utility as util
import lesionpypeline.interfaces.cmtk as cmtk

class Subflow(pe.Workflow):
    """Extends Nipypes workflow class by adding input and output nodes."""
    def __init__(self, name, in_fields, out_fields):
        super(Subflow, self).__init__(name=name)
        if in_fields:
            self._in_fields = list(in_fields)
            self._inputnode = pe.Node(interface=nutil.IdentityInterface(fields=self.in_fields), name=name+'_inputnode')
        else:
            self._in_fields = []

        if out_fields:
            self._out_fields = list(out_fields)
            self._outputnode = pe.Node(interface=nutil.IdentityInterface(fields=self.out_fields), name=name+'_outputnode')
        else:
            self._out_fields = []

    @property
    def inputnode(self):
        return self._inputnode

    @property
    def outputnode(self):
        return self._outputnode

    @property
    def in_fields(self):
        return self._in_fields

    @property
    def out_fields(self):
        return self._out_fields

def connect_subflows(workflow, first, second):
    """Connect common fields of outputnode of first subflow to inputnode of second subflow."""
    outputs = set(first.outputnode.outputs.get().keys())
    inputs = set(second.inputnode.inputs.get().keys())

    common_fields = outputs & inputs
    connection_list = [(first.outputnode.name+'.'+field, second.inputnode.name+'.'+field) for field in common_fields]
    workflow.connect([
        (first, second, connection_list)
    ])
    
    
def assemble_datagrabber_subflow(base_dir, cases, sequences):
    """Assemble datagrabbing subflow that reads files for given sequences from given case directories."""
    subflow = Subflow(name='datagrabber', in_fields=None, out_fields=sequences)
    
    # infosource node allows for execution of whole pipline on multiple cases
    infosource = pe.Node(interface=nutil.IdentityInterface(fields=['case']), name='infosource')
    infosource.iterables = ('case', cases)
    
    # datasource collects sequence files from case folders
    datasource = pe.Node(interface=nio.DataGrabber(infields=['case'], outfields=sequences.keys()), name='datasource')
    datasource.inputs.base_directory = base_dir
    datasource.inputs.template = '%s/%s.nii.gz'
    datasource.inputs.sort_filelist = True

    info = {sequence: [['case', filename]] for (sequence, filename) in sequences.items()}
    datasource.inputs.template_args = info

    subflow.connect(infosource, 'case', datasource, 'case')
    for sequence in sequences:
        subflow.connect(datasource, sequence, subflow.outputnode, sequence)

    return subflow

def assemble_resampling_subflow(sequences, base):
    """Assemble subflow that resamples given base sequence and registers the remaining sequences to base."""
    subflow = Subflow(name='resampling', in_fields=sequences, out_fields=sequences)
    DWI = 'dwi'
    ADC = 'adc'

    resample = pe.Node(interface=medpy.MedpyResample(), name='resample')
    resample.inputs.spacing = '3,3,3'
    subflow.connect([
        (subflow.inputnode, resample, [(base, 'in_file')]),
        (resample, subflow.outputnode, [('out_file', base)]),
    ])
    #remove sequence to avoid duplicate processing
    sequences.remove(base)

    if DWI in sequences and ADC in sequences:
        # DWI sequence is registered to resampling base as usual
        registration = pe.Node(interface=elastix.Registration(), name='dwi_registration')
        registration.inputs.parameters = [os.path.abspath('./configs/elastix_sequencespace_rigid_cfg.txt')]
        registration.inputs.terminal_output = 'none'

        subflow.connect([
            (subflow.inputnode, registration, [(DWI, 'moving_image')]),
            (resample, registration, [('out_file', 'fixed_image')]),
            (registration, subflow.outputnode, [('warped_file', DWI)]),
        ])

        # ADC sequence is instead warped using the transformation matrix from DWI registration
        transformation = pe.Node(interface=elastix.ApplyWarp(), name='adc_transformation')
        subflow.connect([
            (subflow.inputnode, transformation, [(ADC, 'moving_image')]),
            (registration, transform, [('transform', 'transform_file')]),
            (transformation, subflow.outputnode, [('warped_file', ADC)]),
        ])
        # remove sequences to avoid creating duplicate nodes later
        sequences.remove(ADC)
        sequences.remove(DWI)
            
    for sequence in sequences:
        registration = pe.Node(interface=elastix.Registration(), name=sequence+'_registration')
        registration.inputs.parameters = [os.path.abspath('./configs/elastix_sequencespace_rigid_cfg.txt')]
        registration.inputs.terminal_output = 'none'

        subflow.connect([
            (subflow.inputnode, registration, [(sequence, 'moving_image')]),
            (resample, registration, [('out_file', 'fixed_image')]),
            (registration, subflow.outputnode, [('warped_file', sequence)]),
        ])
        
    return subflow

def assemble_skullstripping_subflow(sequences, base):
    """Assemble subflow that uses FSL BET to skullstrip the base sequence and applies the resulting mask to the remaining sequences."""
    subflow = Subflow(name='skullstripping', in_fields=sequences, out_fields=sequences+['mask'])

    skullstrip = pe.Node(interface=fsl.BET(), name='skullstrip')
    skullstrip.inputs.terminal_output = 'none'
    skullstrip.inputs.mask = True
    skullstrip.inputs.robust = True
    skullstrip.inputs.output_type = 'NIFTI_GZ'

    subflow.connect([
        (subflow.inputnode, skullstrip, [(base, 'in_file')]),
        (skullstrip, subflow.outputnode, [('out_file', base), ('mask_file', 'mask')]),
    ])

    sequences.remove(base)
    for sequence in sequences:
        applymask = pe.Node(interface=fsl.ApplyMask(), name=sequence+'_applymask')
        applymask.inputs.terminal_output = 'none'

        subflow.connect([
            (subflow.inputnode, applymask, [(sequence, 'in_file')]),
            (skullstrip, applymask, [('mask_file', 'mask_file')]),
            (applymask, subflow.outputnode, [('out_file', sequence)]),
        ])
        
    return subflow

def assemble_biasfield_correction_subflow(sequences):
    """Assemble biasfield correction subflow that applies cmtk biasfield correction to each sequence."""
    subflow = Subflow(name='biasfieldcorrection', in_fields=sequences+['mask'], out_fields=sequences)

    corrections = {sequence: pe.Node(interface=cmtk.MRBias(), name=sequence+'_bfc') for sequence in sequences}
    metadatamods = {sequence: pe.Node(interface=util.NiftiModifyMetadata(tasks=['qf=aff', 'sf=aff', 'qfc=1', 'sfc=1']),
                         name=sequence+'_modmetadata') for sequence in sequences}

    for sequence in sequences:
        subflow.connect([
            (subflow.inputnode, corrections[sequence], [(sequence, 'in_file')]),
            (subflow.inputnode, corrections[sequence], [('mask', 'mask_file')]),
            (corrections[sequence], metadatamods[sequence], [('out_file', 'in_file')]),
            (metadatamods[sequence], subflow.outputnode, [('out_file', sequence)]),
        ])
    return subflow

def assemble_intensityrange_standardization_subflow(sequences, intensity_models):
    """Assemble subflow that applies medpy intensityrange standardization to each sequence."""
    subflow = Subflow(name='intensityrangestandardization', in_fields=sequences+['mask'], out_fields=sequences)

    standardizations = {sequence: pe.Node(interface=medpy.MedpyIntensityRangeStandardization(
        lmodel=intensity_models[sequence], out_dir='.'), name=sequence+'_intensityrangestd') for sequence in sequences}
    condenses = {sequence: pe.Node(interface=util.CondenseOutliers(), name=sequence+'_condenseoutliers')
                 for sequence in sequences}

    for sequence in sequences:
        subflow.connect([
            (subflow.inputnode, standardizations[sequence], [(sequence, 'in_file')]),
            (subflow.inputnode, standardizations[sequence], [('mask', 'mask_file')]),
            (standardizations[sequence], condenses[sequence], [('out_file', 'in_file')]),
            (condenses[sequence], subflow.outputnode, [('out_file', sequence)]),
        ])
    return subflow

def assemble_featureextraction_subflow(sequences, feature_config_file):
    """TODO"""
    subflow = Subflow(name='featureextraction', in_fields=sequences+['mask'], out_fields=['feature_dir'])

    extract_features = pe.Node(interface=util.ExtractFeatures(sequences=sequences, config_file=feature_config_file, out_dir='./'), name='extract_features')

    subflow.connect([
        (subflow.inputnode, extract_features, zip(sequences, sequences)),
        (subflow.inputnode, extract_features, [('mask', 'mask_file')]),
        (extract_features, subflow.outputnode, [('out_dir', 'feature_dir')]),
    ])
    return subflow

def assemble_classification_subflow(sequences, forest_file, feature_config_file):
    """TODO"""    
    subflow = Subflow(name='classification', in_fields=['feature_dir', 'mask'], out_fields=['segmentation_file', 'probabilities_file'])

    apply_rdf = pe.Node(interface=util.ApplyRdf(forest_file=forest_file, feature_config_file=feature_config_file),
                        name='apply_rdf')

    subflow.connect([
        (subflow.inputnode, apply_rdf, [('feature_dir', 'in_dir'),
                                        ('mask', 'mask_file')]),
        (apply_rdf, subflow.outputnode, [('out_file_segmentation', 'segmentation_file'),
                                         ('out_file_probabilities', 'probabilities_file')]),
    ])
    return subflow

