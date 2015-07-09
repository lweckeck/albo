#!/usr/bin/python

"""
Apply a percentile threshold to the image, condensing all outliers to the percentile values.
<program>.py <in-image> <out-image>
"""

import sys
import numpy
import medpy.io as mio

def condense_outliers(in_file, out_file):
        i, h = mio.load(in_file)
	li = numpy.percentile(i, (1, 99.9))
	i[i < li[0]] = li[0]
	i[i > li[1]] = li[1]
	mio.save(i, out_file, h)

if __name__ == "__main__":
	in_file = sys.argv[1]
        out_file = sys.argv[2]

        condense_outliers(in_file, out_file)
