#!/usr/bin/env python

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.elastix as elastix
import nipype.interfaces.fsl as fsl
import medpy_resample_interface

class PreprocessingWorkflow(pe.Workflow):
    """TODO"""
    def __init__(self, name, sequences, registrationbase, skullstrippingbase):
        """"""
        super(PreprocessingWorkflow, self).__init__(name=name)

        self.inputnode = pe.Node(interface=util.IdentityInterface(fields=sequences), name='inputnode')
        self.outputnode = pe.Node(interface=util.IdentityInterface(fields=sequences), name='outputnode')
        #TODO resolve name conflict parameters - variables
        self.registrationbase = pe.Node(interface=util.IdentityInterface(fields=['base']), name='registrationbase')
        self.skullstrippingbase = pe.Node(interface=util.IdentityInterface(fields=['base']), name='skullstrippingbase')

        for sequence in sequences:
            # Step 1: Resampling / Registraition / (Transformation)
            if sequence == registrationbase:
                resample = pe.Node(interface=medpy_resample_interface.MedpyResampleTask(), name=sequence+'_resample')
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
