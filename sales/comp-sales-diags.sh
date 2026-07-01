#!/bin/bash
# 18/04/2024 vbc - 1.04? Updated for accept_numeric.c builds in sales.cbl
# 29/07/2025 vbc - Removed all references to accept_numeric -- too many problems.

#cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'

for i in `ls sl*.cbl`; do cobc -m $i -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -fdump=ALL -ftraceall -D_FORTIFY_SOURCE=1 ; echo "compiled " $i; done

#for i in `ls sl*.cbl`; do cobc -m $i -Wlinkage accept_numeric.c cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz -d -g -fdump=ALL -ftraceall -lncursesw -D_FORTIFY_SOURCE=1 -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'; echo "compiled " $i; done

#echo "Compiled sl120"

cobc -x sales.cbl -Wlinkage -d -g -ftraceall -fdump=ALL cobmysqlapi.o -D_FORTIFY_SOURCE=1 -I  ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz

#Now make sales as a module incase user wishes to run via ACAS

cobc -m sales.cbl -Wlinkage -d -g -ftraceall -fdump=ALL cobmysqlapi.o -D_FORTIFY_SOURCE=1 -I  ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz

#cobc -x sales.cbl -Wlinkage -d -g -ftraceall -fdump=ALL cobmysqlapi.o  accept_numeric.c -lncursesw -D_FORTIFY_SOURCE=1 -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT' -I  ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz

#Now make sales as a module incase user wishes to run via ACAS

#cobc -m sales.cbl -Wlinkage -d -g -ftraceall -fdump=ALL cobmysqlapi.o  accept_numeric.c -lncursesw -D_FORTIFY_SOURCE=1 -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT' -I  ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz

#cobc -m sl970.cbl accept_numeric.c cobmysqlapi.o -Wlinkage -d -g -ftraceall -fdump=ALL -lncursesw -D_FORTIFY_SOURCE=1 -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT' -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz


exit 0

