#!/bin/bash
# 11.03.18 vbc - Added -Wlinkage to all compiles
# 20.03.21 vbc - Added echos for Compiled xxx
# 24/01/24 vbc = Added diag for no rdbms
#
for i in `ls irs0*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL; echo "Compiled " $i ; done
cobc -x irs.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL
cobc -m irsubp.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL
# Now make irs as a module incase user wishes to run via ACAS
cobc -m irs.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL; echo "Compiled IRS"
#
echo "Compiled for No RDBMS"
exit 0
