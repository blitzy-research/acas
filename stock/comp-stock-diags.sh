#!/bin/bash
# 28/02/24 1.01 added prn generation.

for i in `ls st*.cbl`; do cobc -m -Wlinkage $i cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -ftraceall -fdump=ALL -T $i.prn; echo "Compiled " $i;mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; done
cobc -x stock.cbl -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -ftraceall -fdump=ALL; echo "Compiled Stock"
#-fmissing-statement=ok; echo "Compiled Stock"
# Now make stock as a module incase user wishes to run via ACAS
cobc -m stock.cbl -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -ftraceall -fdump=ALL
echo "Compiled for RDBMS"
exit 0
