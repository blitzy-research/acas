#!/bin/bash
# 31/01/18 vbc - To include dummy-rdbms in place of *MT routines
#                      that call rdb client libraries.
# 04/02/18 vbc - Cleanup cobc steering so that -I removed and api lib included.
# 11/03/18 vbc - Added  -Wlinkage to all compiles.
# 06/05/18 vbc - Added compile for acasconvert1 IRS default layout change.
# 21/06/23 vbc - Added program acas-get-params
#
#  Exclude this group if NOT using rdbms and include one lower but inserting a #
# at the beginning of each line and remove it for dummy-rdbms.cbl
# for i in `ls comp-*MT.sh`; do $i; done
#

cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'
echo "Compiled accept_numeric.c"

cobc -m dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -fmissing-statement=ok
echo "Compiled dummy-rdbmsMT entry points"

cobc -m ACAS-Sysout.cbl -I ../copybooks -Wlinkage -fmissing-statement=ok; echo "Compiled ACAS-Sysout"

for i in `ls *MT.scb`; do presql2 $i; echo "Generated SQL source from" $i; done
for i in `ls *MT.cbl`; do cobc -m $i cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -fmissing-statement=ok; cobxref $i -FREE -VT; echo "Compiled " $i; done
echo "Compiled *MT"
#
for i in `ls maps0*.cbl`; do cobc -m -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -fmissing-statement=ok $i; cobxref $i -FREE -VT; echo "Compiled " $i; done
echo "compiled maps"

for i in `ls acas0*.cbl`; do cobc -m $i cobmysqlapi.o -I ../copybooks -Wlinkage -L /usr/local/mysql/lib -lmysqlclient -lz -fmissing-statement=ok; cobxref $i -FREE -VT; echo "Compiled " $i; done
for i in `ls acasirsub*.cbl`; do cobc -m $i cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -fmissing-statement=ok; cobxref $i -FREE -VT; echo "Compiled " $i; done
cobc -m acas-get-params.cbl -I ../copybooks -Wlinkage -lz; cobxref acas-get-params.cbl -FREE -VT;
echo "Compiled acas-get-params";
echo "Compiled acas*"

cobc -m fhlogger.cbl cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -fmissing-statement=ok; cobxref fhlogger.cbl -FREE -VT; echo "Compiled fhlogger"
cobc -m xl150.cbl cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -fmissing-statement=ok; cobxref xl150.cbl -FREE -VT
cobc -m sys002.cbl cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -fmissing-statement=ok; cobxref sys002.cbl -FREE -VT
echo "compiled xl150 & sys002"
#
cobc -x ACAS.cbl cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -fmissing-statement=ok; cobxref ACAS.cbl -FREE -VT
echo "Compiled ACAS.cbl"
#
#cobc -x acasconvert1.cbl -I ../copybooks -fmissing-statement=ok; cobxref acasconvert1.cbl -FREE -VT
#echo "Compiled acasconvert1.cbl - IRS Default file layout changes"
#
for i in `ls *LD.cbl`; do cobc -x $i cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -fmissing-statement=ok; cobxref $i -FREE -VT; done
echo "Compiled *LD.cbl"

for i in `ls *UNL.cbl`; do cobc -x $i -I ../copybooks; done
echo "Compiled *UNL.cbl"

for i in `ls *RES.cbl`; do cobc -x $i -I ../copybooks; done
echo "Compiled *RES.cbl"

exit 0

