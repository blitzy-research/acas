#!/bin/bash
# 11.03.18 vbc - Added -Wlinkage to all compiles
# 20.03.21 vbc - Added echos for Compiled xxx
#

export COBCPY=../copybooks
export COB_COPY_DIR=../copybooks

for i in `ls irs0*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled " $i ; done
cobc -x irs.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -T $i.prn; echo "Compiled " $i;mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`
cobc -m irsubp.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -T $i.prn; echo "Compiled " $i;mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`
# Now make irs as a module incase user wishes to run via ACAS
cobc -m irs.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -T $i.prn; echo "Compiled " $i;mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'` ; echo "Compiled IRS"
#
echo "Compiled for No RDBMS"
exit 0
