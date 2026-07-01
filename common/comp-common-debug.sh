#!/bin/bash
# 31/01/18 vbc - To include dummy-rdbms in place of *MT routines
#                      that call rdb client libraries.
# 04/02/18 vbc - Cleanup cobc steering so that -I removed and api lib included.
# 21/06/23 vbc - Added program acas-get-params
#
#  Exclude this group if NOT using rdbms and include one lower but inserting a #
# at the beginning of each line and remove it for dummy-rdbms.cbl
# for i in `ls comp-*MT.sh`; do $i; done

cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'
echo "Compiled accept_numeric.c"

for i in `ls *MT.scb`; do presql2 $i; echo "Generated SQL source from" $i; done
for i in `ls *MT.cbl`; do cobc -m -ftraceall -d -g -fdump=ALL $i cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz; echo "Compiled " $i; done
echo "Compiled *MT"
# The one above or the one below NOT BOTH
# include if NOT using RDBMS BUT-- dummy-rdbms.so inlcuded instead of cobmysqlapi.o everywhere.
#cobc -m dummy-rdbms.cbl -fmissing-statement=ok
#

for i in `ls maps0*.cbl`; do cobc -m -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -fdump=ALL $i; echo "Compiled " $i; done
echo "compiled maps"

for i in `ls acas0*.cbl`; do cobc -m -d -g -fdump=ALL $i cobmysqlapi.o -L /usr/local/mysql/lib -lmysqlclient -lz; echo "Compiled " $i; done
for i in `ls acasirsub*.cbl`; do cobc -m -d -g -fdump=ALL $i cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz; echo "Compiled " $i; done

cobc -m -ftraceall -d -g -fdump=ALL acas-get-params.cbl -I ../copybooks -Wlinkage -lz;
echo "Compiled acas-get-params";
echo "Compiled acas*"

cobc -m -d -g -fdump=ALL fhlogger.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
echo "Compiled fhlogger"

cobc -m xl150.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -fdump=ALL
cobc -m -d -g -fdump=ALL sys002.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
echo "compiled xl150 & sys002"
#
cobc -x ACAS.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -fdump=ALL
echo "Compiled ACAS.cbl"
#
for i in `ls *LD.cbl`; do cobc -x $i cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -fdump=ALL; done
echo "Compiled *LD.cbl"

for i in `ls *UNL.cbl`; do cobc -x -d -g -fdump=ALL $i -I ../copybooks; done
echo "Compiled *UNL.cbl"

for i in `ls *RES.cbl`; do cobc -x -d -g -fdump=ALL $i -I ../copybooks; done
echo "Compiled *RES.cbl"
exit 0
