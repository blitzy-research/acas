#!/bin/bash
# 11/03/18 vbc - Added  -Wlinkage to all compiles.

export COBCPY=../copybooks
export COB_COPY_DIR=../copybooks


for i in `ls gl*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -Wlinkage -I ../copybooks -lz -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled " $i; done
cobc -x general.cbl dummy-rdbmsMT.cbl -Wlinkage -I ../copybooks -lz -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled general"
# Now make general as a module incase user wishes to run via ACAS
cobc -m general.cbl dummy-rdbmsMT.cbl -Wlinkage -I ../copybooks -lz
#
echo "Compiled for No RDBMS"
exit 0
