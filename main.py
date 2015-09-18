#!/usr/bin/env python

import os
import sys
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import lesionpypeline.workflow as lwf

base_dir = os.path.abspath('./00original/')

# list of case folder names
if len(sys.argv) > 1:
   cases = sys.argv[1:]
else:
   cases = ['10']

# dictionary of present sequences as 'sequence name': 'file prefix'
sequence_dict = {
   'flair': 'flair_tra',
   't1': 't1_sag_tfe',
   'dw': 'dw_tra_b1000_dmean',
}
sequences = ['flair_tra', 't1_sag_tfe', 'dw_tra_b1000_dmean']
model_folder='102intensitymodels'
intensity_models = {sequence: os.path.abspath(model_folder+'/intensity_model_'+sequence+'.pkl')
                    for sequence in sequences}

feature_config_file = os.path.abspath('./featureconfig.py')
forest_file = os.path.abspath('./101forests/forest.pklz')

# datasink stores output files at given location
datasink = pe.Node(interface=nio.DataSink(), name='datasink')
datasink.inputs.container = 'out'
datasink.inputs.base_directory = os.path.abspath('.')

datagrabber = lwf.assemble_datagrabber_subflow(base_dir, cases, sequences[:])
resampling = lwf.assemble_resampling_subflow(sequences[:], 'flair_tra')
skullstripping = lwf.assemble_skullstripping_subflow(sequences[:], 't1_sag_tfe')
biasfield = lwf.assemble_biasfield_correction_subflow(sequences[:])
intensityrange = lwf.assemble_intensityrange_standardization_subflow(sequences[:], intensity_models)
featureextraction = lwf.assemble_featureextraction_subflow(sequences[:], feature_config_file)
applyrdf = lwf.assemble_classification_subflow(sequences[:], forest_file, feature_config_file)

metaflow = pe.Workflow(name='metaflow', base_dir='.')
lwf.connect_subflows(metaflow, datagrabber, resampling)
lwf.connect_subflows(metaflow, resampling, skullstripping)
lwf.connect_subflows(metaflow, skullstripping, biasfield)
lwf.connect_subflows(metaflow, biasfield, intensityrange)
lwf.connect_subflows(metaflow, intensityrange, featureextraction)
lwf.connect_subflows(metaflow, featureextraction, applyrdf)

for subflow in [intensityrange, featureextraction, applyrdf]:
   metaflow.connect([
      (skullstripping, subflow, [(skullstripping.outputnode.name+'.mask', subflow.inputnode.name+'.mask')]),
   ])

for sequence in sequences:
   metaflow.connect([
      (intensityrange, datasink, [(intensityrange.outputnode.name+'.'+sequence, sequence)]),
   ])

metaflow.connect([
   (applyrdf, datasink, [(applyrdf.outputnode.name+'.segmentation_file', 'segmentation_file')]),
   (applyrdf, datasink, [(applyrdf.outputnode.name+'.probabilities_file', 'probabilities_file')])
])

#metaflow.run()
