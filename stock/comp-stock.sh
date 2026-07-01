#!/bin/bash
for i in `ls st*.cbl`; do cobc -m -Wlinkage $i cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz ; echo "compiled " $i; done
cobc -x stock.cbl -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz; echo "Compiled Stock"
# Now make stock as a module incase user wishes to run via ACAS
cobc -m stock.cbl -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -D_FORTIFY_SOURCE=1 -lmysqlclient -lz
echo "Compiled for RDBMS"
exit 0
