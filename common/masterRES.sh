#!/bin/bash
#
# Script to be used by user to REload  Cobol Files .dat
#    from any existing .seq files.
#
# 06/06/2023 (c) Vincent B Coen from masterUNL.sh
# 07/03/2025 revised to call seach prog that is present in ~/bin
#
#   with prog name ending in RES as works a lot better.

#   THIS SCRIPT HAS NOT YET BEEN TESTED
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
#
#  WARNING YOU MUST HAVE MADE A BACK UP OF ALL DATA FILES BEFORE RUNNING.
#      IT will NOT check if you have !!
#
#  NOTE  This script MUST be run from the ACAS data directory containing
#        all of the Cobol Data files used within each sub-system, i.e., ACAS.
#
#  IT DOES NOT - NOT make use of the system param file or ACAS environment variables.
#   to work out the exact paths of the data files.

cd ~/ACAS

for i in `ls ~/bin/*RES`; do $i; echo "Ran restore program " $i; done
echo "All file restores processes completed"
echo "For all files ending with .seq* a .dat created"

if [ -e SYS-DISPLAY.log ]; then
   echo "Check SYS-DISPLAY.log for any errors etc"
fi

exit 0
