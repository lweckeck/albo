#!/usr/bin/env python

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as nutil
import nipype.interfaces.io as nio
import nipype.interfaces.elastix as elastix
import nipype.interfaces.fsl as fsl
import lesionpypeline.interfaces.medpy as medpy
import lesionpypeline.interfaces.utility as util

class WorkflowStep(pe.Workflow):
    """TODO"""
    def __init__(self, name):
        super(WorkflowStep, self).__init__(name=name)
        self._inputnode = pe.Node(interface=nutil.IdentityInterface(fields=['sequences']), name=name+'_inputnode')
        self._outputnode = pe.Node(interface=nutil.IdentityInterface(fields=['sequences']), name=name+'_outputnode')

    @property
    def inputnode(self):
        return self._inputnode

    @property
    def outputnode(self):
        return self._outputnode

class ResamplingStep(WorkflowStep):
    """TODO"""
    def __init__(self, name, base_index=0):
        super(ResamplingStep, self).__init__(name=name)
        
        baseselector = pe.Node(interface=util.Tee(index=base_index), name=name+'_baseselector')

        resample = pe.Node(interface=medpy.MedpyResampleTask(), name=name+'_resample')
        resample.inputs.spacing = '3,3,3'
        
        registration = pe.MapNode(interface=elastix.Registration(), iterfield='moving_image', name=name+'_registration')
        registration.inputs.parameters = ['/home/lwe/Projects/LesionPypeline/configs/elastix_sequencespace_rigid_cfg.txt']
        registration.inputs.terminal_output = 'none'

        reinsert = pe.Node(interface=util.Insert(index=base_index), name=name+'_reinsert')
        
        self.connect([
            (self.inputnode, baseselector, [('sequences', 'inlist')]),
            (baseselector, resample, [('selected', 'in_file')]),
            (baseselector, registration, [('rejected', 'moving_image')]),
            (resample, registration, [('out_file', 'fixed_image')]),
            (resample, reinsert, [('out_file', 'value')]),
            (registration, reinsert, [('warped_file', 'inlist')]),
            (reinsert, self.outputnode, [('out', 'sequences')]) ])

class ResamplingStep2(WorkflowStep):
    """TODO"""
    def __init__(self, name, sequences, base_index=0):
        super(ResamplingStep, self).__init__(name=name)

        baseselector = pe.Node(interface=nutil.Select(index=base_index), name=name+'_baseselector')
        basefilter = pe.Node(interface.nutil.Select(), name=name+'_basefilter')

        resample = pe.Node(interface=medpy.MedpyResampleTask(), name=name+'_resample')
        resample.inputs.output_file = sequences[base_index]+'_resampled.nii.gz'
        resample.inputs.spacing = '3,3,3'
        
        registration = pe.MapNode(interface=elastix.Registration(), iterfield='moving_image', name=name+'_registration')
        registration.inputs.parameters = ['/home/lwe/Projects/LesionPypeline/configs/elastix_sequencespace_rigid_cfg.txt']
        registration.inputs.terminal_output = 'none'

#        self.connect([
#            (self.inputnode, baseselector, [('sequences', 'inlist')]),
#            (self.inputnode, basefilter, [('sequences', 'inlist')]),
#            (baseselector, resample, [('out', 'input_file')]),
#            (basefilter, registration, [('out', 'moving_image')]),
#            (resample, registration, [('output_file', 'fixed_image')]),
#            (resample, self.outputnode, [('output_file',

class PreprocessingWorkflow(pe.Workflow):
    """TODO"""
    def __init__(self, name, sequences, registrationbase, skullstrippingbase):
        """"""
        super(PreprocessingWorkflow, self).__init__(name=name)

        self.inputnode = pe.Node(interface=nutil.IdentityInterface(fields=sequences), name='inputnode')
        self.outputnode = pe.Node(interface=nutil.IdentityInterface(fields=sequences), name='outputnode')
        #TODO resolve name conflict parameters - variables
        self.registrationbase = pe.Node(interface=nutil.IdentityInterface(fields=['base']), name='registrationbase')
        self.skullstrippingbase = pe.Node(interface=nutil.IdentityInterface(fields=['base']), name='skullstrippingbase')

        for sequence in sequences:
            # Step 1: Resampling / Registraition / (Transformation)
            if sequence == registrationbase:
                resample = pe.Node(interface=medpy.MedpyResampleTask(), name=sequence+'_resample')
                resample.inputs.output_file = 'out.nii.gz'
                resample.inputs.spacing = '3,3,3'
                self.connect([(self.inputnode, resample, [(sequence, 'input_file')]),
                              (resample, self.registrationbase, [('output_file', 'base')]),
                              ])
                prevnode, prevport = resample, 'output_file'
            else:
                registration = pe.Node(interface=elastix.Registration(), name=sequence+'_registration')
                registration.inputs.parameters = ['/home/lwe/Projects/LesionPypeline/configs/elastix_sequencespace_rigid_cfg.txt']
                registration.inputs.terminal_output = 'none'
                self.connect([
                    (self.inputnode, registration, [(sequence, 'moving_image')]),
                    (self.registrationbase, registration, [('base', 'fixed_image')]),
                    ])
                prevnode, prevport = registration, 'warped_file'

            # Step 2: Skullstripping
            if sequence == skullstrippingbase:
                skullstrip = pe.Node(interface=fsl.BET(), name=sequence+'_skullstrip')
                skullstrip.inputs.terminal_output = 'none'
                skullstrip.inputs.mask = True
                skullstrip.inputs.robust = True
                skullstrip.inputs.output_type = 'NIFTI_GZ'
                # HACK
                skullstrip.interface._cmd = 'fsl5.0-bet'
                self.connect([
                    (prevnode, skullstrip, [(prevport, 'in_file')]),
                    (skullstrip, self.skullstrippingbase, [('mask_file', 'base')]),
                    ])
                prevnode, prevport = skullstrip, 'out_file'
            else:
                applymask = pe.Node(interface=fsl.ApplyMask(), name=sequence+'_applymask')
                applymask.inputs.terminal_output = 'none'
                # HACK
                applymask.interface._cmd = 'fsl5.0-fslmaths'
                self.connect([
                    (prevnode, applymask, [(prevport, 'in_file')]),
                    (self.skullstrippingbase, applymask, [('base', 'mask_file')]),
                    ])
                prevnode, prevport = applymask, 'out_file'
            # Final Step: Map to Output
            self.connect([
                (prevnode, self.outputnode, [(prevport, sequence)])
                ])
