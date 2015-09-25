
"""Contains facilities for execution of the lesion detection pipeline.

The Pipeline class stores contextual information for
pipeline execution which is read from a config file.
"""

import os
import shutil
import logging
import ConfigParser

import nipype.caching

import nipype.interfaces.elastix
import nipype.interfaces.fsl
import lesionpypeline.interfaces.medpy
import lesionpypeline.interfaces.cmtk
import lesionpypeline.interfaces.utility

# TODO insert correct names
ADC_ID = 'adc'
DWI_ID = 'dwi'

SEQUENCE_FILE_EXT = '.nii.gz'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _check_configured_directory(path, name):
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        logger.warn('The configured {} {} does not exist'
                    ' - attempting to create directory...'
                    .format(name, path))
        os.makedirs(path)
    return path


def _check_configured_file(path, name):
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise ValueError('The configured {} {} does not exist!'
                         .format(name, path))
    return path


class Pipeline(object):

    """This class stores contextual information for pipeline execution.

    It stores a cache and information from a configuration file, to
    make the core pipeline functionality easily available.
    """

    _mem = None
    _output_dir = None

    _pixel_spacing = None
    _elastix_parameter_file = None
    _registration_base_list = None

    _skullstripping_base_list = None

    _intensity_model_dir = None

    _feature_config_file = None
    _forest_dir = None

    def __init__(self, config_file):
        """.

        Parameters
        ----------
        config : ConfigParser
            ConfigParser object from which the pipeline context is created
        """
        config = ConfigParser.SafeConfigParser()
        config.read(config_file)

        cache_dir = _check_configured_directory(
            config.get('common', 'cache_dir'), 'cache directory')
        self._mem = nipype.caching.Memory(cache_dir)
        logger.info('Using cache directory {}'.format(cache_dir))

        self._output_dir = _check_configured_directory(
            config.get('common', 'output_dir'),
            'output directory')
        logger.info('Using output directory {}'.format(self._output_dir))

        pixel_spacing = config.get('resampling', 'pixel_spacing')
        try:
            x, y, z = map(float, pixel_spacing.split(','))
        except ValueError:
            raise ValueError('The configured pixel spacing {} is invalid; must'
                             'be exactly 3 comma-separated numbers with a dot'
                             'as decimal mark!'.format(pixel_spacing))
        self._pixel_spacing = [x, y, z]

        self._elastix_parameter_file = _check_configured_file(
            config.get('resampling', 'elastix_parameter_file'),
            'elastix configuration file')

        rb = config.get('resampling', 'registration_base')
        self._registration_base_list = map(str.strip, rb.split(','))

        sb = config.get('skullstripping', 'base_image')
        self._skullstripping_base_list = map(str.strip, sb.split(','))

        self._intensity_model_dir = _check_configured_directory(
            config.get('intensityrangestandardization', 'model_dir'),
            'intensity model directory')
        logger.info('Using intensity model directory {}'
                    .format(self._intensity_model_dir))

        self._feature_config_file = _check_configured_file(
            config.get('classification', 'feature_config_file'),
            'feature configuration file')

        self._forest_dir = _check_configured_directory(
            config.get('classification', 'forest_dir'),
            'classification forest directory')

    @property
    def output_dir(self):
        """Return the output directory."""
        return self._output_dir

    def _get_registration_base(self, sequences):
        for s in self._registration_base_list:
            if s in sequences:
                return s
        raise RuntimeError('None of the configured registration base sequences'
                           '{} is present!'
                           .format(self._registration_base_list))

    def _get_skullstripping_base(self, sequences):
        for s in self._skullstripping_base_list:
            if s in sequences:
                return s
        raise RuntimeError('None of the configured skullstripping base'
                           'sequences {} is present!'
                           .format(self._registration_base_list))

    def _get_intensity_model(self, sequence):
        path = os.path.join(self._intensity_model_dir,
                            'intensity_model_{}.pkl'.format(sequence))
        if os.path.isfile(path):
            return path
        else:
            raise ValueError('No intensity model found for sequence {};'
                             'model file was expected at {}'
                             .format(sequence, path))

    def _get_forest(self, sequences):
        # TODO replace with selection mechanism
        forest_file = os.path.join(self._forest_dir, 'forest.pklz')
        if os.path.isfile(forest_file):
            return forest_file
        else:
            raise ValueError('No forest file found at {}!'
                             .format(forest_file))

    def run_pipeline(self, sequence_list):
        """Execute the lesion detection pipeline."""
        # -- Collect sequence files in dict
        sequence_paths = dict()
        for item in sequence_list:
            if item.endswith(SEQUENCE_FILE_EXT):
                # remove file extension
                path, filename = os.path.split(item)
                sequence_id = filename[:-len(SEQUENCE_FILE_EXT)]
                sequence_paths[sequence_id] = os.path.join(
                    os.path.abspath(path), filename)

        # -- Resampling
        fixed_image_key = self._get_registration_base(sequence_paths)
        fixed_image = self.resample(sequence_paths[fixed_image_key])

        sequence_paths[fixed_image_key] = fixed_image
        for key in (sequence_paths.viewkeys()
                    - {fixed_image_key, ADC_ID, DWI_ID}):
            sequence_paths[key], _ = self.register(
                sequence_paths[key], fixed_image)

        # special case: adc is not registered to the fixed image. Instead, the
        # transformation resulting from DWI_ID registration is applied.
        if DWI_ID in sequence_paths:
            sequence_paths[DWI_ID], transform = self.register(
                sequence_paths[DWI_ID], fixed_image)
            if ADC_ID in sequence_paths.keys():
                if transform is not None:
                    sequence_paths[ADC_ID] = self.transform(
                        sequence_paths[ADC_ID], transform)
                else:
                    sequence_paths[ADC_ID] = self.register(
                        sequence_paths[ADC_ID], fixed_image)

        # -- Skullstripping

        skullstrip_base_key = self._get_skullstripping_base(sequence_paths)
        mask = self.skullstrip(sequence_paths[skullstrip_base_key])

        for key in sequence_paths.viewkeys():
            sequence_paths[key] = self.apply_mask(sequence_paths[key], mask)

            # -- Biasfield correction, intensityrange standardization
        for key in sequence_paths.viewkeys():
            sequence_paths[key] = self.correct_biasfield(sequence_paths[key],
                                                         mask)
            sequence_paths[key] = self.standardize_intensityrange(
                sequence_paths[key],
                mask,
                self._get_intensity_model(key))

        # -- Feature extraction and RDF classification

        features = self.extract_features(sequence_paths, mask)
        classification_image, probability_image = self.apply_rdf(
            self._get_forest(sequence_paths), features, mask)

        for path, filename in [(classification_image, 'segmentation.nii.gz'),
                               (probability_image, 'probability.nii.gz')]:
            out_path = os.path.join(self.output_dir, filename)
            if os.path.isfile(out_path):
                os.remove(out_path)
            shutil.copy2(path, out_path)

    def clear_cache(self):
        """Clear all files from cache."""
        self._mem.clear_runs_since()

    def resample(self, in_file):
        """Resample given image.

        The spacing is defined in the context's configuration file.

        Parameters
        ----------
        in_file : string
            Path to the file to be resampled

        Returns
        -------
        string
            Path to the resampled file
        """
        cached_resample = self._mem.cache(
            lesionpypeline.interfaces.medpy.MedpyResample)
        result = cached_resample(
            in_file=in_file, spacing=','.join(map(str, self._pixel_spacing)))
        return result.outputs.out_file

    def register(self, moving_image, fixed_image):
        """Register moving image to fixed image.

        Registration is performed using the elastix program. The path to the
        elastix configuration file is configured in the pipeline config file.

        Parameters
        ----------
        moving_image : string
            Path to the image to warp.
        fixed_image : string
            Path to the image to register *moving_image* to.

        Returns
        -------
        string
            Path to the warped image
        string
            Path to the resulting transform file
        """
        cached_register = self._mem.cache(
            nipype.interfaces.elastix.Registration)
        result = cached_register(moving_image=moving_image,
                                 fixed_image=fixed_image,
                                 parameters=[self._elastix_parameter_file],
                                 terminal_output='none')
        return (result.outputs.warped_file,
                result.outputs.transform)

    def transform(self, moving_image, transform_file):
        """Apply transfrom resulting from elastix registration to an image.

        Parameters
        ----------
        moving_image : string
            Path to the image to warp
        transform_file : string
            Path to the elastix transform to apply

        Returns
        -------
        string
            Path to the warped image
        """
        cached_transform = self._mem.cache(nipype.interfaces.elastix.ApplyWarp)
        result = cached_transform(moving_image=moving_image,
                                  transform_file=transform_file)
        return result.outputs.warped_file

    def skullstrip(self, in_file):
        """Apply skullstripping to an image.

        Skullstripping is performed using the BET program.

        Parameters
        ----------
        in_file : string
            Path to the image to skullstrip

        Returns
        -------
        string
           Path to skullstripping mask.
        """
        cached_skullstrip = self._mem.cache(nipype.interfaces.fsl.BET)
        result = cached_skullstrip(in_file=in_file, mask=True, robust=True,
                                   output_type='NIFTI_GZ')
        return result.outputs.mask_file

    def apply_mask(self, in_file, mask_file):
        """Apply binary mask to an image.

        Parameters
        ----------
        in_file : string
            Path to the image to mask
        mask_file : string
            Path to the mask file

        Returns
        -------
        string
            Path to the masked image
        """
        cached_apply_mask = self._mem.cache(
            lesionpypeline.interfaces.utility.ApplyMask)
        result = cached_apply_mask(in_file=in_file, mask_file=mask_file)
        return result.outputs.out_file

    def correct_biasfield(self, in_file, mask_file):
        """Perform biasfield correction and metadata correction on an image.

        Biasfield correction is performed using the CMTK mrbias program.

        Parameters
        ----------
        in_file : string
            Path to the image to perform biasfield and metadata correction on
        mask_file : string
            Path to mask file used to mask biasfield correction

        Returns
        -------
        string
            Path to the corrected image
        """
        cached_bfc = self._mem.cache(lesionpypeline.interfaces.cmtk.MRBias)
        cached_mod_metadata = self._mem.cache(
            lesionpypeline.interfaces.utility.NiftiModifyMetadata)

        result_bfc = cached_bfc(in_file=in_file, mask_file=mask_file)
        result_mmd = cached_mod_metadata(
            in_file=result_bfc.outputs.out_file,
            tasks=['qf=aff', 'sf=aff', 'qfc=1', 'sfc=1'])

        return result_mmd.outputs.out_file

    def standardize_intensityrange(self, in_file, mask_file, model_file):
        """Perform intensity range standardization and outlier condensation.

        Intensityrange standardization is performed using the respective medpy
        program.

        Parameters
        ----------
        in_file : string
            Path to the image to perform intensityrange standardization on
        mask_file : string
            Path to mask file used to mask intensityrange standardization
        model_file : string
            Path to the intensity model file

        Returns
        -------
        string
            Path to the standardized file with condensed outliers
        """
        cached_irs = self._mem.cache(
            lesionpypeline.interfaces.medpy.MedpyIntensityRangeStandardization)
        cached_condense_outliers = self._mem.cache(
            lesionpypeline.interfaces.utility.CondenseOutliers)

        result_irs = cached_irs(in_file=in_file, out_dir='.',
                                mask_file=mask_file, lmodel=model_file)
        result_co = cached_condense_outliers(
            in_file=result_irs.outputs.out_file)

        return result_co.outputs.out_file

    def extract_features(self, sequence_paths, mask_file):
        """Extract features from given images.

        Parameters
        ----------
        sequence_paths : dict[string, string]
            Dictionary mapping sequence identifier to sequence file path
        mask_file : string
            Path to mask file used to mask feature extraction

        Returns
        -------
        string
            Path to output directory containing the extracted features
        """
        cached_extract_features = self._mem.cache(
            lesionpypeline.interfaces.utility.ExtractFeatures)
        result = cached_extract_features(sequence_paths=sequence_paths,
                                         config_file=self._feature_config_file,
                                         mask_file=mask_file,
                                         out_dir='.')
        return result.outputs.out_dir

    def apply_rdf(self, forest_file, feature_dir, mask_file):
        """Apply random decision forest algorithm to given feature set.

        Parameters
        ----------
        forest_file : string
            Path to a pickled class containing the classification forest
        feature_dir : string
            Path to a directory containing the extracted features to use
            for classification
        mask_file : string
            Path to mask that was used for feature extraction

        Returns
        -------
        string
            Path to binary classification image
        string
            Path to probabilistic classification image
        """
        cached_apply_rdf = self._mem.cache(
            lesionpypeline.interfaces.utility.ApplyRdf)
        result = cached_apply_rdf(
            forest_file=forest_file,
            feature_config_file=self._feature_config_file,
            in_dir=feature_dir,
            mask_file=mask_file)
        return (result.outputs.out_file_segmentation,
                result.outputs.out_file_probabilities)
