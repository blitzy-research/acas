#!/bin/bash
# 24/01/24 vbc - Added diags for no RDBMS builds
#
for i in `ls st*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL; echo "compiled " $i; done
cobc -x stock.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL; echo "compiled Stock"
# Now make stock as a module incase user wishes to run via ACAS
cobc -m stock.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL
echo "Compiled for No RDBMS"
exit 0
