#!/bin/bash
for i in `ls pl*.cbl`; do cobc -m $i -I ../copybooks -Wlinkage cobmysqlapi.o -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz -fdump=ws -fmissing-statement=ok; echo "Compiled " $i; done
cobc -x purchase.cbl -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz -fdump=ws -fmissing-statement=ok; echo "Compiled purchase"
# Now make purchase as a module incase user wishes to run via ACAS
cobc -m purchase.cbl -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz -fdump=ws -fmissing-statement=ok
exit 0
