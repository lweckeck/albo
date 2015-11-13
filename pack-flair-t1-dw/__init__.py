
sequences = ['flair_tra', 'dw_tra_b1000_dmean', 't1_sag_tfe']
presumed_performance = 9000.1

# target pixel spacing
pixel_spacing = [3, 3, 3]

# sequence to be resampled to target pixel spacing; other sequences are then
# registered to this sequence
registration_base = 'flair_tra'

# sequence to perform skullstripping on; resulting mask is applied to remaining
# sequences
skullstripping_base = 't1_sag_tfe'

# tasks for metadata correction
# tasks = ['qf=aff', 'sf=aff', 'qfc=1', 'sfc=1']
tasks = []

intensity_model_flair_tra = 'intensity_model_flair_tra.pkl'
intensity_model_dw_tra_b1000_dmean = 'intensity_model_dw_tra_b1000_dmean.pkl'
intensity_model_t1_sag_tfe = 'intensity_model_t1_sag_tfe.pkl'

feature_config_file = 'featureconfig.py'
# pickled, gzipped RDF sklearn RDF expected
classifier_file = 'forest.pklz'

from medpy.features.intensity import (intensities, centerdistance_xdminus1,
                                      local_mean_gauss, local_histogram)

features = [
    ('flair_tra', intensities, dict(), False),
    ('flair_tra', local_mean_gauss, dict(sigma=3), True),
    ('flair_tra', local_mean_gauss, dict(sigma=5), True),
    ('flair_tra', local_mean_gauss, dict(sigma=7), True),
    # 11 bins, 5*2=10mm region
    ('flair_tra', local_histogram, dict(
        bins=11, rang='image', cutoffp=(0, 100), size=5,  footprint=None,
        output=None, mode='ignore', origin=0), False),
    # 11 bins, 10*2=20mm region
    ('flair_tra', local_histogram, dict(
        bins=11, rang='image', cutoffp=(0, 100), size=10, footprint=None,
        output=None, mode='ignore', origin=0), False),
    # 11 bins, 15*2=30mm region
    ('flair_tra', local_histogram, dict(
        bins=11, rang='image', cutoffp=(0, 100), size=15, footprint=None,
        output=None, mode='ignore', origin=0), False),
    ('flair_tra', centerdistance_xdminus1, dict(dim=0), True),
    ('flair_tra', centerdistance_xdminus1, dict(dim=1), True),
    ('flair_tra', centerdistance_xdminus1, dict(dim=2), True),
    ('t1_sag_tfe', intensities, dict(), False),
    ('t1_sag_tfe', local_mean_gauss, dict(sigma=3), True),
    ('t1_sag_tfe', local_mean_gauss, dict(sigma=5), True),
    ('t1_sag_tfe', local_mean_gauss, dict(sigma=7), True),
    # 11 bins, 5*2=10mm region
    ('t1_sag_tfe', local_histogram, dict(
        bins=11, rang='image', cutoffp=(0, 100), size=5,  footprint=None,
        output=None, mode='ignore', origin=0), False),
    # 11 bins, 10*2=20mm region
    ('t1_sag_tfe', local_histogram, dict(
        bins=11, rang='image', cutoffp=(0, 100), size=10, footprint=None,
        output=None, mode='ignore', origin=0), False),
    # 11 bins, 15*2=30mm region
    ('t1_sag_tfe', local_histogram, dict(
        bins=11, rang='image', cutoffp=(0, 100), size=15, footprint=None,
        output=None, mode='ignore', origin=0), False),
    ('dw_tra_b1000_dmean', intensities, dict(), False),
    ('dw_tra_b1000_dmean', local_mean_gauss, dict(sigma=3), True),
    ('dw_tra_b1000_dmean', local_mean_gauss, dict(sigma=5), True),
    ('dw_tra_b1000_dmean', local_mean_gauss, dict(sigma=7), True),
    # 11 bins, 5*2=10mm region
    ('dw_tra_b1000_dmean', local_histogram, dict(
        bins=11, rang='image', cutoffp=(0, 100), size=5,  footprint=None,
        output=None, mode='ignore', origin=0), False),
    # 11 bins, 10*2=20mm region
    ('dw_tra_b1000_dmean', local_histogram, dict(
        bins=11, rang='image', cutoffp=(0, 100), size=10, footprint=None,
        output=None, mode='ignore', origin=0), False),
    # 11 bins, 15*2=30mm region
    ('dw_tra_b1000_dmean', local_histogram, dict(
        bins=11, rang='image', cutoffp=(0, 100), size=15, footprint=None,
        output=None, mode='ignore', origin=0), False),
]
