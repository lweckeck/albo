# ALBO - Automatic Lesion to Brain region Overlap

Albo is a tool for calculating the overlap between a lesion and brain regions,
based on MRI sequences. Given a set of MRI images, the lesion is automatically
segmented and then registered to a standard brain. Now, the lesion overlap with
brain regions is calculated based on brain atlases.

## Prerequisites

The following programs are needed for installing and running albo:

-   NumPy
-   SciPy
-   Computational Morphometry Toolkit (CMTK)
-   FSL
-   NiftyReg

Apart from NiftyReg, in Ubuntu these programs can be installed with the command

```shell
sudo apt-get install python-numpy python-scipy cmtk fsl
```

NiftyReg needs to be built from source, see
[here](http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftyReg_install) for
instructions.

After installation, you may need to add something like `source
/etc/fsl/5.0/fsl.sh` to your .bashrc file, depending on your FSL version. This
makes, e.g., the command `bet` available, instead of `fsl5.0-bet`, which is
required by albo. See `man fsl` for details.

## Installation

Download and unpack the program (or clone the repository) and run `python
setup.py install`. This may download further Python dependencies.

Open the file `./config/albo/albo.conf` and set the paths needed by the program.
Then, place the classifiers, standardbrains and

## Usage

This section provides just a rough overview. See the
[wiki](https://github.com/lweckeck/albo/wiki) for more
information, or run `albo -h` in your terminal.

Configure the necessary paths in `~/.config/albo/albo.conf`.

To list all available classifiers and the sequence identifiers they emply, use

```shell
albo list
```

Assuming there is a classifier identifying the FLAIR sequence as MR_Flair and
the T1 sequence as MR_T1, to run the program, use

```shell
albo run --id case-id MR_Flair:path/to/flair MR_T1:path/to/t1
```

In case new atlases were added to the atlas directory, re-calculate the overlap
for all previously segmented cases with

```shell
albo update
```
