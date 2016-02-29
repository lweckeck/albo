# ALBO - Automatic Lesion to Brain region Overlap

Albo is a tool for calculating the overlap between a lesion and various regions
in the brain, based on MRI sequences. Given a set of MRI images, the lesion is
automatically segmented and then registered to a standard brain. From there, the
overlap with various brain regions can be calculated.

## Prerequisites
Before the installation, make sure numpy>=1.6.1 and scipy>=0.17 are installed.
In Ubuntu, these programs can be installed from the package manager:
```
sudo apt-get install python-numpy python-scipy
```

To run the pipeline, the following additional programs must be available from the commandline.

Command | Ubuntu package | Remark
--------|----------------|-------
`cmtk`  | cmtk | -
`bet` | fsl | If it is only available as `fsl5.0-bet` or similar, add the line `source /etc/fsl/fsl.sh` to your `.bashrc` file
`elastix` | elastix | If not available in your package manager, download from https://launchpad.net/ubuntu/+source/elastix
NiftyReg tools | n/a | See http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftyReg_install


## Installation
Make sure
Download and unpack the program and run
```
python setup.py install
```

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
