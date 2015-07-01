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
    
registration_base = 'flair'
skullstripping_base = 't1'
    
# infosource node allows for execution of whole pipline on multiple cases
infosource = pe.Node(interface=util.IdentityInterface(fields=['case']), name='infosource')
infosource.iterables = ('case', cases)

# datasource collects sequence files from case folders
datasource = pe.Node(interface=nio.DataGrabber(infields=['case'], outfields=['sequences']), name='datasource')
datasource.inputs.base_directory = '/home/lwe/Projects/LesionPypeline/00original'
datasource.inputs.template = '%s/%s.nii.gz'
datasource.inputs.sort_filelist = True

#info = {sequence: [['case', filename]] for (sequence, filename) in sequences.items()}
#datasource.inputs.template_args = info
datasource.inputs.template_args['sequences'] = [['case', sequences.values()]]

# datasink stores output files at given location
datasink = pe.Node(interface=nio.DataSink(), name='datasink')
datasink.inputs.container = 'out'
datasink.inputs.base_directory = '/home/lwe/Projects/LesionPypeline'

#workflow = pp.PreprocessingWorkflow(name='workflow', sequences=sequences.keys(), registrationbase='flair', skullstrippingbase='t1')

workflow = pp.ResamplingStep(name='resamplingstep', base_index=sequences.values().index('flair_tra'))

metaflow = pe.Workflow(name='metaflow')

metaflow.connect([
    (infosource, datasource, [('case', 'case')]),
    (datasource, workflow, [('sequences', 'resamplingstep_inputnode.sequences')]),
    (workflow, datasink, [('resamplingstep_outputnode.sequences', 'sequences')]),
])
#for sequence in sequences.keys():
#    metaflow.connect([
#        (datasource, workflow, [(sequence, 'inputnode.'+sequence)]),
#        (workflow, datasink, [('outputnode.'+sequence, sequence)])
#    ])
