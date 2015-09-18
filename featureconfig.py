####
# Configuration file: Denotes the features to extract
# Formatted as a dictionary with sequences as keys and lists of tuples (function, args, voxelspacing) as values, where function is the
# feature extraction function, args a dictionary containing the function parameters, and voxelspacing a boolean indicating
# if the respective voxelspacing needs to be passed to the function.
####

from medpy.features.intensity import intensities, centerdistance, centerdistance_xdminus1, local_mean_gauss, local_histogram
from medpy.features.intensity import indices as indices_feature

features_to_extract = {
    'flair_tra': [
        (intensities, dict(), False),
        (local_mean_gauss, dict(sigma=3), True),
        (local_mean_gauss, dict(sigma=5), True),
        (local_mean_gauss, dict(sigma=7), True),
        (local_histogram, dict(bins=11, rang='image', cutoffp=(0, 100), size=5,  footprint=None, output=None, mode='ignore', origin=0), False), #11 bins, 5*2=10mm region
        (local_histogram, dict(bins=11, rang='image', cutoffp=(0, 100), size=10, footprint=None, output=None, mode='ignore', origin=0), False), #11 bins, 10*2=20mm region
        (local_histogram, dict(bins=11, rang='image', cutoffp=(0, 100), size=15, footprint=None, output=None, mode='ignore', origin=0), False), #11 bins, 15*2=30mm region
        (centerdistance_xdminus1, dict(dim=0), True),
        (centerdistance_xdminus1, dict(dim=1), True),
        (centerdistance_xdminus1, dict(dim=2), True)
    ],

    'dw_tra_b1000_dmean': [
        (intensities, dict(), False),
        (local_mean_gauss, dict(sigma=3), True),
        (local_mean_gauss, dict(sigma=5), True),
        (local_mean_gauss, dict(sigma=7), True),
        (local_histogram, dict(bins=11, rang='image', cutoffp=(0, 100), size=5,  footprint=None, output=None, mode='ignore', origin=0), False), #11 bins, 5*2=10mm region
        (local_histogram, dict(bins=11, rang='image', cutoffp=(0, 100), size=10, footprint=None, output=None, mode='ignore', origin=0), False), #11 bins, 10*2=20mm region
        (local_histogram, dict(bins=11, rang='image', cutoffp=(0, 100), size=15, footprint=None, output=None, mode='ignore', origin=0), False), #11 bins, 15*2=30mm region
    ],

    't1_sag_tfe': [
        (intensities, dict(), False),
        (local_mean_gauss, dict(sigma=3), True),
        (local_mean_gauss, dict(sigma=5), True),
        (local_mean_gauss, dict(sigma=7), True),
        (local_histogram, dict(bins=11, rang='image', cutoffp=(0, 100), size=5,  footprint=None, output=None, mode='ignore', origin=0), False), #11 bins, 5*2=10mm region
        (local_histogram, dict(bins=11, rang='image', cutoffp=(0, 100), size=10, footprint=None, output=None, mode='ignore', origin=0), False), #11 bins, 10*2=20mm region
        (local_histogram, dict(bins=11, rang='image', cutoffp=(0, 100), size=15, footprint=None, output=None, mode='ignore', origin=0), False), #11 bins, 15*2=30mm region
    ],
}
