# ALBO - Automatic Lesion to Brain region Overlap

Albo is a tool for calculating the overlap between a lesion and various regions
in the brain, based on MRI sequences. Given a set of MRI images, the lesion is
automatically segmented and then registered to a standard brain. From there, the
overlap with various brain regions can be calculated.

## Installation
Download and unpack the program and run
```
python setup.py install
```

If the installation fails due to scipy complaining about missing header files,
try running

```
sudo apt-get install python-dev gfortran cython liblapack-dev libatlas-dev
```

To be able to run the pipeline, also make sure the following commands are available
from your command-line.

Command | Debian package | Remark
--------|----------------|-------
`cmtk`  | cmtk | -
`bet` | fsl | If it is only available as `fsl5.0-bet` or similar, add the line `source /etc/fsl/fsl.sh` to your `.bashrc` file
`elastix` | elastix | -

## Basic usage

The basic information the program needs for running is a *case identifier*, as
well as the MRI sequence files to use. Additionally, the sequence files must be
annotated with their sequence types. The sequence types depend on the classifier
that is used.

```
albo run -id example-case MR_Flair:path/to/flair MR_T1:path/to/t1
```

To list all available classifiers with the sequence identifiers they use, use
`albo list`. 
