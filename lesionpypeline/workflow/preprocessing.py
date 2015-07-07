#!/usr/bin/env python

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as nutil
import nipype.interfaces.io as nio
import nipype.interfaces.elastix as elastix
import nipype.interfaces.fsl as fsl
import lesionpypeline.interfaces.medpy as medpy
import lesionpypeline.interfaces.utility as util

class Subflow(pe.Workflow):
    """Extends Nipypes workflow class by adding input and output nodes."""
    def __init__(self, name, sequences):
        super(Subflow, self).__init__(name=name)
        self._sequences = list(sequences)
        self._inputnode = pe.Node(interface=nutil.IdentityInterface(fields=self.sequences), name=name+'_inputnode')
        self._outputnode = pe.Node(interface=nutil.IdentityInterface(fields=self.sequences), name=name+'_outputnode')

    @property
    def inputnode(self):
        return self._inputnode

    @property
    def outputnode(self):
        return self._outputnode

    @property
    def sequences(self):
        return self._sequences

def connect_subflows(workflow, first, second):
    outputs = set(first.outputnode.outputs.get().keys())
    inputs = set(second.inputnode.inputs.get().keys())

    common_fields = outputs & inputs
    connection_list = [(first.outputnode.name+'.'+field, second.inputnode.name+'.'+field) for field in common_fields]
    workflow.connect([
        (first, second, connection_list)
    ])
    
    
def assemble_datagrabber_subflow(cases, sequences):
    subflow = Subflow(name='datagrabber', sequences=sequences)
    
    # infosource node allows for execution of whole pipline on multiple cases
    infosource = pe.Node(interface=nutil.IdentityInterface(fields=['case']), name='infosource')
    infosource.iterables = ('case', cases)
    
    # datasource collects sequence files from case folders
    datasource = pe.Node(interface=nio.DataGrabber(infields=['case'], outfields=sequences.keys()), name='datasource')
    datasource.inputs.base_directory = '/home/lwe/Projects/LesionPypeline/00original'
    datasource.inputs.template = '%s/%s.nii.gz'
    datasource.inputs.sort_filelist = True

    info = {sequence: [['case', filename]] for (sequence, filename) in sequences.items()}
    datasource.inputs.template_args = info

    subflow.connect(infosource, 'case', datasource, 'case')
    for sequence in sequences:
        subflow.connect(datasource, sequence, subflow.outputnode, sequence)

    return subflow

def assemble_resampling_subflow(sequences, base):
    subflow = Subflow(name='resampling', sequences=sequences)
    DWI = 'dwi'
    ADC = 'adc'

    resample = pe.Node(interface=medpy.MedpyResampleTask(), name='resample')
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
        registration.inputs.parameters = ['/home/lwe/Projects/LesionPypeline/configs/elastix_sequencespace_rigid_cfg.txt']
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
        registration.inputs.parameters = ['/home/lwe/Projects/LesionPypeline/configs/elastix_sequencespace_rigid_cfg.txt']
        registration.inputs.terminal_output = 'none'

        subflow.connect([
            (subflow.inputnode, registration, [(sequence, 'moving_image')]),
            (resample, registration, [('out_file', 'fixed_image')]),
            (registration, subflow.outputnode, [('warped_file', sequence)]),
        ])
        
    return subflow

def assemble_skullstripping_subflow(sequences, base):
    subflow = Subflow(name='skullstripping', sequences=sequences)

    skullstrip = pe.Node(interface=fsl.BET(), name='skullstrip')
    skullstrip.inputs.terminal_output = 'none'
    skullstrip.inputs.mask = True
    skullstrip.inputs.robust = True
    skullstrip.inputs.output_type = 'NIFTI_GZ'

    subflow.connect([
        (subflow.inputnode, skullstrip, [(base, 'in_file')]),
        (skullstrip, subflow.outputnode, [('out_file', base)]),
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
    pass

def assemble_intensityrange_standardization_subflow(sequences):
    pass

def assemble_featureextraction_subflow(sequences):
    pass

def assemble_classification_subflow(sequences):
    pass
