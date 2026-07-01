#!/bin/bash
#
# This will compile ALL subsystems using the scripts within each directory
####
#  THE lines with copybooks need to be uncommented when building the SF archives
#   and source tree.
#
# and this to set up cobcpy
export COBCPY=../copybooks
export COB_COPY_DIR=../copybooks
# comp top level as might be wanted
#cobc -x -I copybooks ACAS.cbl
# now compile all sub-systems ...
# - - Changed i_r_sys..   to irs  for v3.02
cd common
./comp-common.sh
echo "Common modules done"
cd ../general
./comp-gl.sh
echo "General Ledger done"
cd ../irs
./comp-irs.sh
echo "IRS done"
cd ../purchase
./comp-purchase.sh
echo "Purchase Ledger done"
cd ../sales
./comp-sales.sh
echo "Sales Ledger done"
cd ../stock
./comp-stock.sh
echo "Stock Control done"
#   Not yet released under Open Source
#cd ../OE
#./comp-OE.sh
#echo "OE done"
#cd ../payroll
#./comp-payroll.sh
#echo "payroll done"
#cd ../epos
#./comp-epos.sh
#echo "Epos done"
#
echo "We Are all done but check for any error or warning messages"
exit 0
