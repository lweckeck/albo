#!/usr/bin/env python

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import medpy_resample_interface

#infosource node allows for execution of whole pipeline on multiple cases
infosource = pe.Node(interface=util.IdentityInterface(fields=['case']), name='infosource')
infosource.iterables = ('case', ['10'])

#datasource collects sequences according to specified case folder
datasource = pe.Node(interface=nio.DataGrabber(infields=['case'], outfields=['flair', 't1', 'dw']), name='datasource')
datasource.inputs.base_directory = '/home/lwe/Projects/LesionPipeline/00original'
datasource.inputs.template = '%s/%s.nii.gz'
datasource.inputs.sort_filelist = True

info = dict(
    flair=[['case', 'flair_tra']],
    t1=[['case', 't1_sag_tfe']],
    dw=[['case', 'dw_tra_b1000_dmean']]
    )
datasource.inputs.template_args = info

resample = pe.Node(interface=medpy_resample_interface.MedpyResampleTask(), name='resample')
resample.inputs.output_file = './out.nii.gz'
resample.inputs.spacing = '3,3,3'

datasink = pe.Node(interface=nio.DataSink(), name='datasink')
datasink.inputs.container = 'out'
datasink.inputs.base_directory = '/home/lwe/Projects/LesionPipeline'

workflow = pe.Workflow(name='workflow')
workflow.connect(
    [(infosource, datasource, [('case', 'case')]),
     (datasource, resample, [('flair', 'input_file')]),
     (resample, datasink, [('output_file', 'resampled')]),
     ])

