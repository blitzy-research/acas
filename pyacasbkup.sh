#!/bin/bash
# *** backup script for ACAS v3.3 GC versions ***
#  WARNING: this scripts filename 'pyacasbkup.sh' is fixed inside the ACAS menus
#     Don't change it unless you know what you are doing
#
# 09/04/2009 vbc - temp backup dir and filename prefix change
# 01/11/2025 vbc - Added support for Payroll - Does it need sep archive file name ?
#
if [ ! -d temp-backups ]; then
    mkdir `pwd`"/temp-backups"
#temp-backups
fi
#cd temp-backups
tar cvfz `pwd`"/temp-backups/acas-bkup-py-"`date +%Y%m%d%H%M%S`.tar.gz py*.dat**
#
# place here commands to copy file build above to
#       offline storage ie usb memory stick
# cp -vpf acas-bkup-py-"`date +%Y%m%d%H*`.tar.gz /mnt/sdd1/acas-backups
#
exit 0
