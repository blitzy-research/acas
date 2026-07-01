#!/bin/bash
#
#
#   THIS SCRIPT HAS NOT YET BEEN TESTED
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# Script to be used by user to load Tables from Cobol Files.
#     Will test if each file exists and if so run the
#     relevent load program.
#
#  This is a script for lazy system administrators, (yes, me included !)
#     as the load modules should be run manually if a given data file exists
#      having configured the ACAS parameter file for use with RDBMS
#       see options Z in any of the sub systems and the Building the ACAS
#         system manual chapter 17 and onwards for parameter file set up
#          specifically paragraphs 1.13,
#
# 17/05/2019 (c) Vincent B Coen
# 17/05/2019 vbc - v1.00 Written for ACAS GC version.
# 13/06/2019 vbc - v1.01 Added O/P from SYS-DISPLAY.log via 'less'
# 18/07/2019 vbc - v1.02 Added direct tests for RC's (return codes) for system.dat
#                        processing- forgot to add them in 1.01.
# 26/04/2023 vbc - v1.03 After system data sort rest in order and make 1 liners
#                        removed unneeded error checks for value.dat.
# 31/05/2023 vbc - v1.04 Added slautogenLD and plautogenLD.
#
#  NOTE  This script MUST be run from the ACAS data directory containing
#        all of the Cobol Data files used within each sub-system, i.e., ACAS.
#
#  IT DOES NOT - NOT make use of the system param file or ACAS environment variables.
#    to work out the exact path of the data files.
#
# Each program checks for the existance of rdbms params within the
#  ACAS system parameter file including that the use RDB is set on
#  and not use files instead. If not programs will just quit.
#
# If params are not set up, they will exit with 128
# if  RDB not set up will exit with 64
#   if error writing data to rdb with 16
#
# MUST GET round to trapping these param errors (>63)
#  but it is a lot of typing :)
#

cd ~/ACAS
#
# First, process the five different records in the system file that are
#  used to create five RDBMS tables holding only one record each.
#
JOBSTATUS=0
if [ -e system.dat ]; then
    systemLD
# test for return-code? if exist -gt (greater than) 63 will quit script
   rc=$?
   JOBSTATUS=$rc
   if [ $rc -gt 63 ]     # != 0 ]
   then
      echo "Problem with data in system.dat - Aborting"
      exit $rc
   fi
    sys4LD
# test for return-code?
   rc=$?
   JOBSTATUS=$rc
   if [ $rc -gt 63 ]
   then
      echo "Problem with data in system.dat - Aborting"
      exit $rc
   fi
    finalLD
# test for return-code?
   rc=$?
   JOBSTATUS=$rc
   if [ $rc -gt 63 ]
   then
      echo "Problem with data in system.dat - Aborting"
      exit $rc
   fi
    dfltLD
# test for return-code?
   rc=$?
   JOBSTATUS=$rc
   if [ $rc != 0 ]
   then
      echo "Problem with data in system.dat - Aborting"
      exit $rc
   fi
fi
#
# Now for all the ACAS data files checking if each one exists before running
#  the load program (for each).
#
if [ -e analysis.dat ];  then analLD fi
if [ -e batch.dat ];     then glbatchLD fi
if [ -e delfolio.dat ];  then delfolioLD fi
if [ -e delinvno.dat ];  then sldelinvnosLD fi
if [ -e delivery.dat ];  then deliveryLD fi
if [ -e invoice.dat ];   then slinvoiceLD fi
if [ -e irsacnts.dat ];  then irsnominalLD fi
if [ -e irsdflt.dat ];   then irsdfltLD fi
if [ -e irsfinal.dat ];  then irsfinalLD fi
if [ -e irspost.dat ];   then irspostingLD fi
if [ -e ledger.dat ];    then nominalLD fi
if [ -e openitm3.dat ];  then otm3LD fi
if [ -e openitm5.dat ];  then otm5LD fi
if [ -e pay.dat ];       then paymentsLD fi
if [ -e pinvoice.dat ];  then plinvoiceLD fi
if [ -e plautogen.dat ]; then plautogenLD fi
if [ -e posting.dat ];   then glpostingLD fi
if [ -e postings2irs.dat ]; then  slpostingLD fi
if [ -e purchled.dat ];  then purchLD fi
if [ -e salesled.dat ];  then salesLD fi
if [ -e slautogen.dat ]; then slautogenLD fi
if [ -e staudit.dat ];   then auditLD fi
if [ -e stockctl.dat ];  then stockLD fi
if [ -e value.dat ];     then valueLD fi
#

if [ -e SYS-DISPLAY.log ]; then
   echo "All loads complete but check SYS-DISPLAY.log"
   less SYS-DISPLAY.log
   exit 0
fi
