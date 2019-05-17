#!/usr/bin/env python

import sys
from kmzfile import readkmz
# import vrccolors
import sectorfile
from pathlib import Path

# Sectorfiles to be updated
# Input file to be sectorile_airac.sct2
# Output file to be sectorfile_airacrX.sct2
sectorfiles = [
    "BLI_TWR_V1",
    "EUG_APP_PRO_V1",
    "GEG_APP_PRO_V1",
    "LMT_APP_PRO_V1",
    "MFR_APP_PRO_V1_1",
    "MWH_APP_PRO_V1",
    "NUW_APP_PRO_V1",
    "OTH_TWR_V1",
    "P80_TRACON_PRO_V1_2",
    "PSC_APP_PRO_V1",
    "S46-PRO-v2_2",
    "YKM_APP_PRO_V1_1",
    "ZSE-v3_05"
]

# Location of the diagram kmz
kmlfile = sys.argv[2]
print("Will open: "+str(kmlfile))

# Current airac cycle, part of filenames
airac = "1903"

# Modification version of current airac
modver = sys.argv[3]

# Where to look for the master file set
masterdir = Path(sys.argv[1])
newdiags = readkmz(masterdir / kmlfile)
# print(newdiags["KSEA"].reflines)
# Iterate over each sectorfile
# Basic workflow is:
#  Read current sector file and split into sections
#  Prune out labels that will be replaced
#  Write new file, inserting new content as required
for sfile in sectorfiles:
    print("Processing "+sfile)
    sectorobj = sectorfile.sectorfileobj(sfile, masterdir, airac, modver)
    sectorobj.addnewdiagrams(newdiags)
    sectorobj.write()
