#!/bin/bash
# 29/07/2025 vbc - Removed all references to accept_numeric -- too many problems.

#cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'

for i in `ls sl*.cbl`; do cobc -m $i -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz -T $i.prn ; echo "compiled " $i; done
#echo "Compiled sl120"

cobc -x sales.cbl -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz -T $i.prn; echo "Compiled Sales"
#Now make sales as a module incase user wishes to run via ACAS

cobc -m sales.cbl -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz

exit 0
