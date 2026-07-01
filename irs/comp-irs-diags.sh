#!/bin/bash
for i in `ls irs0*.cbl`; do cobc -m $i  -I ../copybooks -Wlinkage cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -ftraceall -fdump=ALL; echo "Compiled " $i ; done
cobc -x irs.cbl -I ../copybooks -Wlinkage cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -ftraceall -fdump=ALL
cobc -m irsubp.cbl -I ../copybooks -Wlinkage cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -ftraceall -fdump=ALL
# Now make irs as a module incase user wishes to run via ACAS
cobc -m irs.cbl -I ../copybooks -Wlinkage cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -ftraceall -fdump=ALL; echo "Compiled IRS"
#
echo "Compiled for rdbms"
exit 0
