#!/usr/bin/env python

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import lesionpypeline.workflow.preprocessing as pp

# list of case folder names
cases = ['10']

# dictionary of present sequences as 'sequence name': 'file prefix'
sequences = {
    'flair': 'flair_tra',
    't1': 't1_sag_tfe',
    'dw': 'dw_tra_b1000_dmean',
}
    

# datasink stores output files at given location
datasink = pe.Node(interface=nio.DataSink(), name='datasink')
datasink.inputs.container = 'out'
datasink.inputs.base_directory = '/home/lwe/Projects/LesionPypeline'

datagrabber = pp.assemble_datagrabber_subflow(cases, sequences)
resampling = pp.assemble_resampling_subflow(sequences.keys(), 'flair')
skullstripping = pp.assemble_skullstripping_subflow(sequences.keys(), 't1')

metaflow = pe.Workflow(name='metaflow')
pp.connect_subflows(metaflow, datagrabber, resampling)
pp.connect_subflows(metaflow, resampling, skullstripping)

for sequence in sequences.keys():
   metaflow.connect([
       (skullstripping, datasink, [(skullstripping.outputnode.name+'.'+sequence, sequence)])
   ])
