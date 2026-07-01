#!/bin/bash
# 31/01/18 vbc - To include dummy-rdbms in place of *MT routines
#                      that call rdb client libraries.
# 04/02/18 vbc - Cleanup cobc steering so that -I removed and api lib included.
#
# 04/02/18 vbc - This version of script for compiling for NON RDBMS system.
#
#
#  DO NOT USE THIS SCRIPT BUT comp-common-no-rdbms.sh
#    and no I do not remember why this was created
#
export COBCPY=../copybooks
export COB_COPY_DIR=../copybooks


cobc -m dummy-rdbms.cbl;echo "Compiled dummy-rdbms entry points"
cobc -m ACAS-Sysout.cbl; echo "Compiled ACAS-Sysout"
#
cp -vf dummy-rdbmsMT.* ../stock
cp -vf dummy-rdbmsMT.* ../sales
cp -vf dummy-rdbmsMT.* ../purchase
cp -vf dummy-rdbmsMT.* ../irs
cp -vf dummy-rdbmsMT.* ../general
echo "Copied dummy-rdbmsMT.so to irs, general, purchase, sales, stock dirs."

for i in `ls maps0*.cbl`; do cobc -m $i; echo "Compiled " $i; done
echo "compiled maps"

for i in `ls acas0*.cbl`; do cobc -m $i dummy-rdbms.so; echo "Compiled " $i; done
for i in `ls acasirsub*.cbl`; do cobc -m $i dummy-rdbms.so; echo "Compiled " $i; done
echo "Compiled acas*"

cobc -m fhlogger.cbl dummy-rdbms.so;echo "Compiled fhlogger"

cobc -m xl150.cbl dummy-rdbms.so
cobc -m sys002.cbl dummy-rdbms.so
echo "compiled xl150 & sys002"
#
cobc -x ACAS.cbl dummy-rdbms.so;echo "Compiled ACAS.cbl"
#
for i in `ls *UNL.cbl`; do cobc -x $i; done
echo "Compiled *UNL.cbl"

for i in `ls *RES.cbl`; do cobc -x $i; done
echo "Compiled *RES.cbl"
#
echo "Compiled for No RDBMS"

exit 0
