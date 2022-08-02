#!/usr/bin/python

import os
import sys

# determine the absolute path to the disk
scriptDir = os.path.dirname(os.path.realpath(sys.argv[0]))
import os
args = ""
for i in range(1, len(sys.argv)):
	args = f"{args} {sys.argv[i]}" if (len(args)) else sys.argv[1]
sys.exit(os.system(f"python {scriptDir}/configure_lp.py -load {args}"))
