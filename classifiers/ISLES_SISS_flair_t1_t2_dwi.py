"""Classifier configuration for MR_Flair sequence.

Training set sampling
#####################
N_s=2500000

Forest
######
type=RandomForestClassifier
T=100
D=200
criterion=gini
max_features=auto
bootstrap=true

Post-processing
###############
min-lesion size: 1000
"""
import os

sequences = ['MR_Flair', 'MR_T1', 'MR_T2', 'MR_DWI']

# target pixel spacing
pixel_spacing = [3, 3, 3]

# sequence to be resampled to target pixel spacing; other sequences are then
# registered to this sequence
registration_base = 'MR_Flair'

# sequence to perform skullstripping on; resulting mask is applied to remaining
# sequences
skullstripping_base = 'MR_T1'

# tasks for metadata correction
# tasks = ['qf=aff', 'sf=aff', 'qfc=1', 'sfc=1']
tasks = []

intensity_models = {s: os.path.join(os.path.dirname(__file__),
                                    'intensity_model_'+s+'.pkl')
                    for s in sequences}


# pickled, gzipped RDF sklearn RDF expected
classifier_file = os.path.join(
    os.path.dirname(__file__), 'ISLES_SISS_flair_t1_t2_dwi.pklz')

from medpy.features import (
    intensities, local_mean_gauss, hemispheric_difference, local_histogram,
    centerdistance_xdminus1)

features = [
    ('MR_Flair', intensities, dict(), False),
    ('MR_Flair', local_mean_gauss, dict(sigma=3), True),
    ('MR_Flair', local_mean_gauss, dict(sigma=5), True),
    ('MR_Flair', local_mean_gauss, dict(sigma=7), True),
    ('MR_Flair', hemispheric_difference,
     dict(sigma_active=1, sigma_reference=1, cut_plane=0), True),
    ('MR_Flair', hemispheric_difference,
     dict(sigma_active=3, sigma_reference=3, cut_plane=0), True),
    ('MR_Flair', hemispheric_difference,
     dict(sigma_active=5, sigma_reference=5, cut_plane=0), True),
    # 11 bins, 5*2=10mm region
    ('MR_Flair', local_histogram, dict(bins=11, size=5), False),
    # 11 bins, 10*2=20mm region
    ('MR_Flair', local_histogram, dict(bins=11, size=10), False),
    # 11 bins, 15*2=30mm region
    ('MR_Flair', local_histogram, dict(bins=11, size=15), False),
    ('MR_Flair', centerdistance_xdminus1, dict(dim=0), True),
    ('MR_Flair', centerdistance_xdminus1, dict(dim=1), True),
    ('MR_Flair', centerdistance_xdminus1, dict(dim=2), True),
    ('MR_T1', intensities, dict(), False),
    ('MR_T1', local_mean_gauss, dict(sigma=3), True),
    ('MR_T1', local_mean_gauss, dict(sigma=5), True),
    ('MR_T1', local_mean_gauss, dict(sigma=7), True),
    ('MR_T1', hemispheric_difference,
     dict(sigma_active=1, sigma_reference=1, cut_plane=0), True),
    ('MR_T1', hemispheric_difference,
     dict(sigma_active=3, sigma_reference=3, cut_plane=0), True),
    ('MR_T1', hemispheric_difference,
     dict(sigma_active=5, sigma_reference=5, cut_plane=0), True),
    # 11 bins, 5*2=10mm region
    ('MR_T1', local_histogram, dict(bins=11, size=5), False),
    # 11 bins, 10*2=20mm region
    ('MR_T1', local_histogram, dict(bins=11, size=10), False),
    # 11 bins, 15*2=30mm region
    ('MR_T1', local_histogram, dict(bins=11, size=15), False),
    ('MR_T2', intensities, dict(), False),
    ('MR_T2', local_mean_gauss, dict(sigma=3), True),
    ('MR_T2', local_mean_gauss, dict(sigma=5), True),
    ('MR_T2', local_mean_gauss, dict(sigma=7), True),
    ('MR_T2', hemispheric_difference,
     dict(sigma_active=1, sigma_reference=1, cut_plane=0), True),
    ('MR_T2', hemispheric_difference,
     dict(sigma_active=3, sigma_reference=3, cut_plane=0), True),
    ('MR_T2', hemispheric_difference,
     dict(sigma_active=5, sigma_reference=5, cut_plane=0), True),
    # 11 bins, 5*2=10mm region
    ('MR_T2', local_histogram, dict(bins=11, size=5), False),
    # 11 bins, 10*2=20mm region
    ('MR_T2', local_histogram, dict(bins=11, size=10), False),
    # 11 bins, 15*2=30mm region
    ('MR_T2', local_histogram, dict(bins=11, size=15), False),
    ('MR_DWI', intensities, dict(), False),
    ('MR_DWI', local_mean_gauss, dict(sigma=3), True),
    ('MR_DWI', local_mean_gauss, dict(sigma=5), True),
    ('MR_DWI', local_mean_gauss, dict(sigma=7), True),
    ('MR_DWI', hemispheric_difference,
     dict(sigma_active=1, sigma_reference=1, cut_plane=0), True),
    ('MR_DWI', hemispheric_difference,
     dict(sigma_active=3, sigma_reference=3, cut_plane=0), True),
    ('MR_DWI', hemispheric_difference,
     dict(sigma_active=5, sigma_reference=5, cut_plane=0), True),
    # 11 bins, 5*2=10mm region
    ('MR_DWI', local_histogram, dict(bins=11, size=5), False),
    # 11 bins, 10*2=20mm region
    ('MR_DWI', local_histogram, dict(bins=11, size=10), False),
    # 11 bins, 15*2=30mm region
    ('MR_DWI', local_histogram, dict(bins=11, size=15), False),
]
