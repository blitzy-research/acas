#!/bin/bash
# 11/03/18 vbc - Added  -Wlinkage to all compiles.
# 24/01/24 vbc - Added diags for NO RDBMS
#
for i in `ls gl*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -Wlinkage -I ../copybooks -lz -d -g -ftraceall -fdump=ALL; echo "Compiled " $i; done
cobc -x general.cbl dummy-rdbmsMT.cbl -Wlinkage -I ../copybooks -lz -d -g -ftraceall -fdump=ALL; echo "Compiled general"
# Now make general as a module incase user wishes to run via ACAS
cobc -m general.cbl dummy-rdbmsMT.cbl -Wlinkage -I ../copybooks -lz -d -g -ftraceall -fdump=ALL
#
echo "Compiled for No RDBMS"
exit 0
