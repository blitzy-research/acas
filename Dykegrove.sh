#!/bin/bash
# 28-04.18 vbc - New script to run ACAS etc for Dykegrove
#                Change name of program running from ACAS to irs
#                If only running that one.
cd ~/ACAS/Dykegrove
export ACAS_LEDGERS=/home/vince/ACAS/Dykegrove
# Leaving the above line in (without the leading '#' is just belt and braces.
#
ACAS ACAS_LEDGERS=/home/vince/ACAS/Dykegrove
exit 0
#

