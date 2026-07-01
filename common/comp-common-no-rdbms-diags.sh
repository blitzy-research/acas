#!/bin/bash
# 31/01/18 vbc - To include dummy-rdbms in place of *MT routines
#                      that call rdb client libraries.
# 04/02/18 vbc - Cleanup cobc steering so that -I removed and api lib included.
#
# 04/02/18 vbc - This version of script for compiling for NON RDBMS system.
# 11/03/18 vbc - Added  -Wlinkage to all compiles.
# 06/05/18 vbc - Added compile for acasconvert1 IRS default layout change.
# 07/12/22 vbc - Extra text for echo msgs and use of -Wno-goto-section added
#                to remove the silly default warning in latest gnucobol v3.2.
# 21/06/23 vbc - Added program acas-get-params
# 24/01/24 vbc = Updated for runtine checks etc for none RDBMS builds
#
#cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'
#echo "Compiled accept_numeric.c"

cobc -m dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz
echo "Compiled dummy-rdbmsMT entry points"

cobc -m -lz ACAS-Sysout.cbl -I ../copybooks -Wlinkage -d -g -ftraceall -fdump=ALL; echo "Compiled ACAS-Sysout"
#
cp -vf dummy-rdbmsMT.* ../stock
cp -vf dummy-rdbmsMT.* ../sales
cp -vf dummy-rdbmsMT.* ../purchase
cp -vf dummy-rdbmsMT.* ../irs
cp -vf dummy-rdbmsMT.* ../general
echo "Copied dummy-rdbmsMT.so to irs, general, purchase, sales, stock dirs."
#
for i in `ls maps0*.cbl`; do cobc -m -lz $i -I ../copybooks -d -g -ftraceall -fdump=ALL -Wlinkage; echo "Compiled " $i; done
echo "compiled all maps"

for i in `ls acas0*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL; echo "Compiled " $i; done
for i in `ls acasirsub*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL; echo "Compiled " $i; done
cobc -m acas-get-params.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL;
echo "Compiled acas-get-params";
echo "Compiled all acas*"

cobc -m fhlogger.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL
echo "Compiled fhlogger"

cobc -m xl150.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL
cobc -m sys002.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL
echo "compiled xl150 & sys002"
#
cobc -x ACAS.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -d -g -ftraceall -fdump=ALL
echo "Compiled ACAS.cbl"
#
#cobc -x acasconvert1.cbl -I ../copybooks -d -g -fdump=ALL
#echo "Compiled acasconvert1.cbl - IRS Default file layout changes"
for i in `ls *UNL.cbl`; do cobc -x $i -Wlinkage -lz -I ../copybooks -d -g -ftraceall -fdump=ALL; done
echo "Compiled *UNL.cbl"

for i in `ls *RES.cbl`; do cobc -x $i -Wlinkage -lz -I ../copybooks -d -g -ftraceall -fdump=ALL; done
echo "Compiled *RES.cbl"
#
#for i in `ls *LD.cbl`; do cobc -x $i cobmysqlapi.o -I ../copybooks -Wlinkage -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -fdump=ALL; done
#echo "Compiled *LD.cbl"
echo "Compiled for No RDBMS"
exit 0
