#!/bin/bash

export COBCPY=../copybooks
export COB_COPY_DIR=../copybooks

for i in `ls st*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "compiled " $i; done
cobc -x stock.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -T $i.prn; echo "Compiled " $i;mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "compiled Stock"
# Now make stock as a module incase user wishes to run via ACAS
cobc -m stock.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz
echo "Compiled for No RDBMS"
exit 0
