#!/bin/bash
# 31/01/18 vbc - To include dummy-rdbms in place of *MT routines
#                      that call rdb client libraries.
# 04/02/18 vbc - Cleanup cobc steering so that -I removed and api lib included.
# # 11/03/18 vbc - Added  -Wlinkage to all compiles.
# 06/05/18 vbc - Added compile for acasconvert1 IRS default layout change.
# 08/06/19 vbc - Added compile for ACAS-Sysout.
# 07/12/22 vbc - Extra text for echo msgs and use of -Wno-goto-section added
#                to remove the silly default warning in latest gnucobol v3.2.
# 21/06/23 vbc - Added program acas-get-params
# 09/07/23 vbc = Added to all comps  -fdump=all
#
#  Exclude this group if NOT using rdbms and include one lower but inserting a #
# at the beginning of each line and remove it for dummy-rdbms.cbl
# for i in `ls comp-*MT.sh`; do $i; done
#

cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'
echo "Compiled accept_numeric.c"

cobc -m dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -T dummy-rdbmsMT.prn; echo "Compiled dummy-rdbmsMT entry points"

cobc -m ACAS-Sysout.cbl -I ../copybooks -Wlinkage -T ACAS-Sysout.prn;  echo "Compiled ACAS-Sysout"

for i in `ls *MT.scb`; do presql2 $i; echo "Generated SQL source from" $i; done
for i in `ls *MT.cbl`; do cobc -m $i cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled " $i; done
echo "Compiled All *MT modules"
#
for i in `ls maps0*.cbl`; do cobc -m $i -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled " $i; done
echo "compiled all maps"
#
for i in `ls acas0*.cbl`; do cobc -m $i cobmysqlapi.o -I ../copybooks -Wlinkage -L /usr/local/mysql/lib -lmysqlclient -lz -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled " $i; done
#
for i in `ls acasirsub*.cbl`; do cobc -m $i cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled " $i; done
#
cobc -m acas-get-params.cbl cobmysqlapi.o -I ../copybooks -Wlinkage -L /usr/local/mysql/lib -lmysqlclient -lz -T acas-get-params.prn
echo "Compiled acas-get-params"
echo "Compiled all acas*"

cobc -m fhlogger.cbl cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -T fhlogger.prn; echo "Compiled fhlogger"
cobc -m xl150.cbl cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -T xl150.prn
cobc -m sys002.cbl cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -T sys002.prn
echo "compiled xl150 & sys002"
#
cobc -x ACAS.cbl cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -T ACAS.prn
echo "Compiled ACAS.cbl"
#
#cobc -x acasconvert1.cbl -I ../copybooks -fmissing-statement=ok
#echo "Compiled acasconvert1.cbl - IRS Default file layout changes"
#
for i in `ls *LD.cbl`; do cobc -x $i cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled " $i; done
echo "Compiled all *LD"

for i in `ls *UNL.cbl`; do cobc -x $i -I ../copybooks -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled " $i; done
echo "Compiled *UNL.cbl"

for i in `ls *RES.cbl`; do cobc -x $i -I ../copybooks -T $i.prn; mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "Compiled " $i; done
echo "Compiled *RES.cbl"
exit 0
