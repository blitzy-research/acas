#!/bin/bash
# 11/03/2018 vbc - Added -Wlinkage to all compiles.
# 24/01/2024 vbc - Added diags to no RDBMS
# 29/07/2025 vbc - Removed all references to accept_numeric -- too many problems.
#
#cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'

for i in `ls sl*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -d -g -ftraceall -fdump=ALL -I ../copybooks -Wlinkage -lz; echo "compiled " $i; done

#for i in `ls sl*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl accept_numeric.c -d -g -ftraceall -fdump=ALL -I ../copybooks -Wlinkage -lz -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'; echo "compiled " $i; done
#echo "Compiled sl120"

cobc -x sales.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL

#cobc -x sales.cbl dummy-rdbmsMT.cbl accept_numeric.c -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'
#Now make sales as a module incase user wishes to run via ACAS

cobc -m sales.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL

#cobc -m sales.cbl dummy-rdbmsMT.cbl accept_numeric.c -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'
echo "Compiled for No RDBMS"
exit 0
