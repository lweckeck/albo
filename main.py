#!/usr/bin/env python

import os
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import lesionpypeline.workflow as lwf

# list of case folder names
cases = ['10']

# dictionary of present sequences as 'sequence name': 'file prefix'
sequences = {
   'flair': 'flair_tra',
   't1': 't1_sag_tfe',
   'dw': 'dw_tra_b1000_dmean',
}
model_folder='102intensitymodels'
intensity_models = {sequence: os.path.abspath(model_folder+'/intensity_model_'+filename+'.pkl')
                    for sequence, filename in sequences.items()}

# datasink stores output files at given location
datasink = pe.Node(interface=nio.DataSink(), name='datasink')
datasink.inputs.container = 'out'
datasink.inputs.base_directory = '/home/lwe/Projects/LesionPypeline'

datagrabber = lwf.assemble_datagrabber_subflow(cases, sequences)
resampling = lwf.assemble_resampling_subflow(sequences.keys(), 'flair')
skullstripping = lwf.assemble_skullstripping_subflow(sequences.keys(), 't1')
biasfield = lwf.assemble_biasfield_correction_subflow(sequences.keys())
intensityrange = lwf.assemble_intensityrange_standardization_subflow(sequences.keys(), intensity_models)

metaflow = pe.Workflow(name='metaflow', base_dir='.')
lwf.connect_subflows(metaflow, datagrabber, resampling)
lwf.connect_subflows(metaflow, resampling, skullstripping)
lwf.connect_subflows(metaflow, skullstripping, biasfield)
lwf.connect_subflows(metaflow, biasfield, intensityrange)

metaflow.connect([
    (skullstripping, intensityrange, [(skullstripping.outputnode.name+'.mask', intensityrange.inputnode.name+'.mask')]),
])

for sequence in sequences.keys():
   metaflow.connect([
       (intensityrange, datasink, [(intensityrange.outputnode.name+'.'+sequence, sequence)])
   ])
