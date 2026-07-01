#!/bin/bash
for i in `ls irs0*.cbl`; do cobc -m $i  -I ../copybooks -Wlinkage cobmysqlapi.o -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz -fdump=ws -fmissing-statement=ok; echo "Compiled " $i ; done
cobc -x irs.cbl -I ../copybooks -Wlinkage cobmysqlapi.o -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz -fdump=ws -fmissing-statement=ok
cobc -m irsubp.cbl -I ../copybooks -Wlinkage cobmysqlapi.o -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz -fdump=ws -fmissing-statement=ok
# Now make irs as a module incase user wishes to run via ACAS
cobc -m irs.cbl -I ../copybooks -Wlinkage cobmysqlapi.o -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz -fdump=ws -fmissing-statement=ok; echo "Compiled IRS"
#
echo "Compiled for rdbms"
exit 0
