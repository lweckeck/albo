
"""TODO."""

import nipype.interfaces as interfaces
import lesionpypeline.interfaces.medpy as medpy

# TODO insert correct names
ADC = 'adc'
DWI = 'dwi'


def execute_pipeline(sequences, config):
    """Execute the lesion detection pipeline."""
    context = PipelineContext(config)

    # -- Resampling

    # TODO get base key from config file
    fixed_image_key = 'a'
    fixed_image = context.resample(sequences[fixed_image_key])

    sequences[fixed_image_key] = fixed_image
    for key in sequences.viewkeys() - {fixed_image_key, ADC, DWI}:
        sequences[key], _ = context.register(sequences[key], fixed_image)

    # special case: adc is not registered to the fixed image. Instead, the
    # transformation resulting from DWI registration is applied.
    if DWI in sequences:
        sequences[DWI], transform = context.register(sequences[DWI],
                                                     fixed_image)
    if ADC in sequences.keys():
        if transform is not None:
            sequences[ADC] = context.transform(sequences[ADC], transform)
        else:
            sequences[ADC] = context.register(sequences[ADC], fixed_image)

    # -- Skullstripping
    # TODO
    skullstrip_base_key = 'a'
    mask = context.skullstrip(sequences[skullstrip_base_key])

    for key in sequences.viewkeys():
        sequences[key] = context.apply_mask(sequences[key], mask)

    # -- Biasfield correction, intensityrange standardization
    for key in sequences.viewkeys():
        sequences[key] = context.correct_biasfield(sequences[key])
        sequences[key] = context.standardize_intensityrange(sequences[key])

    # -- Feature extraction and RDF classification
    features = context.extract_features(sequences)
    classification_image, probability_image = context.apply_rdf(features)


class PipelineContext(object):

    """This class stores contextual information for pipeline execution.

    It stores a cache and information from a configuration file, to
    make the core pipeline functionality easily available.
    """

    _mem = None

    _pixel_spacing = None
    _elastix_parameter_file = None
    _intensity_model_dir = None
    _feature_config_file = None
    _forest_file = None

    def __init__(self, sequences, config):
        """TODO."""
        pass

    def get_registration_base(sequences):
        """Return the sequence to register other sequences to.

        TODO
        """
        pass

    def get_skullstripping_base(sequences):
        """Return the sequence to use for skullstripping.

        TODO
        """
        pass

    def resample(self, in_file):
        """Resample given image.

        The spacing is defined in the context's configuration file.
        """
        print 'resample {}'.format(in_file)
        return in_file

    def register(self, moving_image, fixed_image):
        """Register moving image to fixed image.

        Parameters
        ----------
        moving_image : string
            Path to the image to warp.
        fixed_image : string
            Path to the image to register to.

        Returns
        -------
        string
            Path to the warped image
        string
            Path to the resulting transform file
        """
        print 'register {} to {}'.format(moving_image, fixed_image)
        return moving_image, 'transform'

    def transform(self, moving_image, transform_file):
        """Apply transfrom resulting from registration to an image.

        TODO
        """
        print 'transform {} using {}'.format(moving_image, transform_file)
        return moving_image

    def skullstrip(self, in_file):
        """Apply skullstripping to an image.

        Returns
        -------
        string
           Path to skullstripping mask.
        """
        print 'skullstrip {}'.format(in_file)
        return in_file

    def apply_mask(self, in_file, mask):
        """Apply binary mask to an image.

        TODO
        """
        print 'mask {} with {}'.format(in_file, mask)
        return in_file

    def correct_biasfield(self, in_file):
        """Perform biasfield correction and metadata correction on an image.

        TODO
        """
        print 'correct biasfield {}'.format(in_file)
        return in_file

    def standardize_intensityrange(self, in_file):
        """Perform intensity range standardization and outlier condensation.

        TODO
        """
        print 'standardize intensity {}'.format(in_file)
        return in_file

    def extract_features(self, in_files):
        """Extract features from given images.

        TODO
        """
        print 'extract features from {}'.format(repr(in_files))
        return []

    def apply_rdf(self, features):
        """Apply random decision forest algorithm to given feature set.

        TODO
        """
        print 'apply rdf to {}'.format(repr(features))
        return None, None
