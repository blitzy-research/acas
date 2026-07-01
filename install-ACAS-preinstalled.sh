#!/bin/bash
#
# Script to be used by user. If done by admin will need changing
#     Also file/executables permissions may need changing
#
# 02/10/2011 (c) Vincent B Coen
# 02/10/2011 vbc - v1.00 primary install script for ACAS GC (GnuCobol) version
# 17/11/2011 vbc - v1.01 copy error.txt to ~/bin
# 20/12/2011 vbc - v1.02 Added creation of dir's ~/ACAS archives
#                        and ~/ACAS/temp-backups
# 30/01/2012 vbc - v1.03 Copy ACAS binary
# 09/04/2012 vbc - v1.0  from above to reinstall newly compiled programs
#                        where install has been run before
# 08/12/2016 vbc - v1.02 For v3.02 removed all programs run in ACAS
#                        support for new FH & DALs (replacing irsub1 - 5)
#                        Now does full systems including irs
# 29/03/2017 vbc - v1.04 Moving 1st chmod to correct dir - common.
# 02/02/2018 vbc - v1.05 Removed error.txt and IRS directory for v3.02.
# 09/02/2018 vbc - v1.06 For scripts chged cp to include all as acasbkup*.sh
# 04/03/2018 vbc - v1.07 Adjusted setup for ~/common to test if analLD built if so
#                        mv / cp *LD, cobmysqlapi.so, *MT.so to ~/bin
#                        cp cobmysqlapi.so to ~/bin - JIC.
#
# 13/06/2019 vbc - v1.08 Added cp for masterLD.sh
# 31/05/2020 vbc - v1.09 Moved above cp after cd common.
# 26/06/2020 vbc - v1.10 Forgot to mv ACAS-Sysout.so ~/bin
# 25/06/2023 vbc - v1.11 Added *.RES, *UNL with *LD
#                        Match up this script and install-ACAS.sh
# 31/07/2023 vbc - v1.12 Test for acasconvert* before moving to ~/bin
# 17/04/2024 vbc - v1.13 Added accept-numeric.so for the copy from
#                        common and/or sales
# 15/09/2024 vbc - v1.14 Remarked out any acasconvert* processing as not used.
#
#  NOTE  This script MUST be run from the ACAS directory containing
#        the Cobol sources which are within each sub-system directory
#         eg., irs, general, sales, stock, purchase, OE, payroll,epos etc
#        The last three are not supplied with the OS (Open Source) versions.
#
#--------------------------------------------------------------
#
if [ ! -d ~/bin ]; then
    mkdir ~/bin
fi
#
# Now change permissions and move the executables to users
#       bin directory
#

chmod u+x *.sh
cp -vf acasbkup*.sh ~/bin
cd common
cp -vf masterLD.sh ~/bin
chmod u+x ACAS acasconv*
cp -vf dummy-rdbmsMT.so ~/bin

#  CHECK IF RDBMS NOT BUILT AGAINST NO-RDBMS
if [ -e analLD ]; then
    chmod u+x *LD *RES *UNL
#
    cp -vf cobmysqlapi.so ~/bin
    mv -vf *LD ~/bin
    mv -vf *RES ~/bin
    mv -vf *UNL ~/bin
    mv -vf *MT.so ~/bin
fi

cp -vf dummy-rdbmsMT.so ~/bin
mv -vf sys002.so ~/bin
mv -vf xl150.so ~/bin
mv -vf acas*.so ~/bin
mv -vf maps*.so ~/bin
mv -vf ACAS ~/bin
mv -vf fhlogger.so ~/bin
mv -vf ACAS-Sysout.so ~/bin
#if [ -e acasconvert* ]; then
#   mv -vf acasconvert* ~/bin
#fi
if [ -e accept_numeric.so ]; then
mv -vf accept_numeric.so ~/bin
fi

cd ../irs
chmod u+x irs *.sh

mv -vf irs ~/bin
mv -vf irs*.so ~/bin

cd ../sales
chmod u+x *.sh sales

mv -vf sales ~/bin
mv -vf sales.so ~/bin
mv -vf sl*.so ~/bin
if [ -e accept_numeric.so ]; then
mv -vf accept_numeric.so ~/bin
fi
#cp -vf *.sh ~/bin

cd ../purchase
chmod u+x purchase *.sh

mv -vf purchase ~/bin
mv -vf purchase.so ~/bin
mv -vf pl*.so ~/bin
#cp -vf *.sh ~/bin

cd ../stock
chmod u+x stock *.sh

mv -vf stock ~/bin
mv -vf st*.so ~/bin
#cp -vf *.sh ~/bin

cd ../general
chmod u+x general *.sh

mv -vf general ~/bin
mv -vf general.so ~/bin
mv -vf gl*.so ~/bin
#cp -vf *.sh ~/bin
#
# OE is not available at this time for O/S versions
#
#cd ../OE
#chmod u+x OE/*.sh
#mv -vf OE ~/bin
#mv -vf *.so ~/bin
##cp -vf *.sh ~/bin
#
# Payroll is not available at this time for O/S versions
#
#cd ../payroll
#chmod u+x payroll/*.sh
#mv -vf payroll ~/bin
#mv -vf *.so ~/bin
##cp -vf *.sh ~/bin
#
# EPOS is not available at this time for O/S versions
#
#cd ../EPOS
#chmod u+x EPOS/*.sh
#mv -vf EPOS ~/bin
#mv -vf *.so ~/bin
##cp -vf *.sh ~/bin
#
# more needed if OE, EPOS or Payroll is supplied
echo "    *** ACAS re-installation complete  ***"
echo " "
exit 0

