#!/bin/bash
#
# Script to be used by user to unload  Cobol FILES .dat.
#     Will test if each file exists and if so run the
#     relevent UNL program.
#
#
# 06/06/2023 (c) Vincent B Coen from masterLD.sh
# 07/03/2025 revised to call seach prog that is present in ~/bin
#   with prog name ending in UNL as works a lot better.
#
#  NOTE  This script MUST be run FROM THE ACAS data directory containing
#                                ^^^^^^^^^^^^^
#        all of the Cobol Data files used within each sub-system, i.e., ACAS.
#
#  IT DOES NOT - NOT make use of the system param file or ACAS environment variables.
#   to work out the exact paths of the data files.
#
cd ~/ACAS
#
#
for i in `ls ~/bin/*UNL`; do $i; echo "Ran Unload program " $i; done
echo "All file Unloads processes completed"
echo "For all files ending with .dat* a .seq created"

if [ -e SYS-DISPLAY.log ]; then
   echo "Check SYS-DISPLAY.log for any errors etc"
fi

exit 0
