#!/bin/bash
#
# Script to be used by user. If done by admin will need changing
#     Also file/executables permissions may need changing
#
# 02/10/2011 (c) Vincent B Coen
# 02/10/2011 vbc - v1.00 primary install script for ACAS GC (GnuCobol) version
# 17/11/2011 vbc - v1.01  copy error.txt to ~/bin
# 20/12/2011 vbc - v1.02  Added creation of dir's ~/ACAS archives
#                         and ~/ACAS/temp-backups
# 30/01/2012 vbc - v1.03 Copy ACAS binary
# 08/12/2016 vbc - v1.02 For v3.02 removed all programs run in ACAS
#                        support for new FH & DALs (replacing irsub1 - 5)
#                        Includes irs with v3.02 so removed Env set for IRS.
# 29/03/2017 vbc - v1.04 Repositioned the chmod - not in the right dir.
# 07/06/2017 vbc - v1.05 Added COB_EXIT_WAIT=on for environment.
# 02/02/2018 vbc - v1.06 Minor tidy up for ACAS v3.02
#                        Removed error.txt, IRS directories as redundant.
# 09/02/2018 vbc - v1.07 For scripts chged cp to include all as acasbkup*.sh
# 04/03/2018 vbc - v1.08 Adjusted setup for ~/common to test if analLD built if so
#                        mv / cp *LD, cobmysqlapi.so, *MT.so to ~/bin
#                        cp cobmysqlapi.so to ~/bin - JIC.
# 31/05/2020 vbc - v1.09 Added cp for masterLD.sh after cd common
# 26/06/2020 vbc - v1.10 Forgot to mv ACAS-Sysout.so ~/bin
# 25/06/2023 vbc - v1.11 Added *.RES, *UNL with *LD
#                        Match up this script and install-ACAS-preinstalled.sh
# 31/07/2023 vbc - v1.12 Test for acasconvert* before moving to ~/bin
# 17/04/2024 vbc - v1.13 Added accept-numeric.so for the copy from
#                        common and/or sales
# 15/09/2024 vbc - v1.14 Remarked out any acasconvert* processing as not used.
#
#  NOTE  this script MUST be run from the ACAS directory containing
#        the Cobol sources which are within each sub-system directory
#         eg., irs, general, sales, stock, purchase, OE, payroll,epos etc
#
#       In addition we will create the directories for the user in which
#       the data will reside other than in a common directory such as /opt
#         so you will need to change this script if needed.
#
#--------------------------------------------------------------
#  Does not matter if both scripts are run, other than duplicate
#   lines will be added to the .bashrc file so use
#   install-ACAS-preinstalled.sh for all subsequent installs.
#
#--------------------------------------------------------------
#
if [ ! -d ~/bin ]; then
    mkdir ~/bin
fi
#
#           Now change permissions and move the executables to users
#           bin directory
#

chmod u+x *.sh
cp -vf acasbkup*.sh ~/bin
cd common
cp -vf masterLD.sh ~/bin
chmod u+x ACAS acasconv*
cp -vf dummy-rdbmsMT.so ~/bin

#  CHECK IF RDBMS BUILT as AGAINST NO-RDBMS
if [ -e analLD ]; then
    chmod u+x *LD

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
#chmod u+x OE *.sh
#mv -vf OE ~/bin
#mv -vf *.so ~/bin
#
# Payroll is not available at this time for O/S versions
#
#cd ../payroll
#chmod u+x payroll *.sh
#mv -vf payroll ~/bin
#mv -vf *.so ~/bin
#
# EPOS is not available at this time for O/S versions
#
#cd ../EPOS
#chmod u+x EPOS/*.sh
#mv -vf EPOS ~/bin
#mv -vf *.so ~/bin
#
# add exports to users bash profile
#
cat << EOF >> ~/.bashrc
export COB_SCREEN_ESC=YES
export COB_SCREEN_EXCEPTIONS=YES
export COB_LIBRARY_PATH=~/bin
export COB_EXIT_WAIT=on
#
export PATH=~/bin:.:$PATH
export ACAS_LEDGERS=~/ACAS
export ACAS_BIN=~/bin
export TMPDIR=~/tmp
# the next one is an issue as ALL data files will go there regardless
#    so remarked out
#export DB_HOME=~/ACAS
#
#export #COB_PRE_LOAD=irs010:irs020:irs030:irs040:irs050:irs055:irs060:irs065:irs070:irs080:irs085:irs090:irsub1:irsub2:irsub3:irsub4:irsub5:irsubp
# above not needed but here as a reminder in case it or similar, needs to be installed
#

EOF
#
#  NOW create the directories for the ACAS data for this user
#   but we use the system defaults for directories, scripts so
#       mkdir kept seperate, in case if an error on one then rest can
#             still complete
#
if [ ! -d ~/ACAS ]; then
   mkdir ~/ACAS
   mkdir ~/ACAS/temp-backups
   mkdir ~/ACAS/archives
fi

if [ ! -d ~/ACAS/temp-backups ]; then
   mkdir ~/ACAS/temp-backups
   mkdir ~/ACAS/archives
fi

if [ ! -d ~/ACAS/archives ]; then
   mkdir ~/ACAS/archives
fi

if [ ! -d ~/ACAS-practice ]; then
   mkdir ~/ACAS-practice
   mkdir ~/ACAS-practice/temp-backups
   mkdir ~/ACAS-practice/archives
fi

if [ ! -d ~/tmp ]; then
   mkdir ~/tmp
fi
#cp -vf ~/bin/irsbakup.sh ~/IRS
# more needed if OE, EPOS or Payroll is supplied

echo "    *** ACAS installation complete & new paths etc created ***"
echo " "
echo "Now exit this terminal and load another so that new paths are found"
echo "and go to the new directory = ACAS and start running your chosen ACAS element's"
echo " Running this script more than once will put duplicate commands into"
echo "  your .bashrc file so you might want to remove them first"
echo "    but will not cause a problem other than being messy"
echo "  "
echo "  Instead use script install-ACAS-preinstalled.sh "
echo "    after using this one, ONCE - install-ACAS.sh "
exit 0

