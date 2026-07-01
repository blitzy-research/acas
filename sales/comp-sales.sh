#!/bin/bash
# 29/07/2025 vbc - Removed all references to accept_numeric -- too many problems.


#cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'

for i in `ls sl*.cbl`; do cobc -m $i -Wlinkage cobmysqlapi.o -D_FORTIFY_SOURCE=1 -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz; echo "compiled " $i; done

cobc -x sales.cbl -Wlinkage cobmysqlapi.o -D_FORTIFY_SOURCE=1 -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz; echo "Compiled Sales"

#for i in `ls sl*.cbl`; do cobc -m $i -Wlinkage accept_numeric.c cobmysqlapi.o -lncursesw -D_FORTIFY_SOURCE=1 -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT' -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz; echo "compiled " $i; done

#cobc -x sales.cbl -Wlinkage accept_numeric.c cobmysqlapi.o -lncursesw -D_FORTIFY_SOURCE=1 -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT' -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz; echo "Compiled Sales"

#Now make sales as a module incase user wishes to run via ACAS
#cobc -m sales.cbl -Wlinkage cobmysqlapi.o -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz

cobc -m sales.cbl -Wlinkage cobmysqlapi.o -D_FORTIFY_SOURCE=1 -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz

#cobc -m sales.cbl -Wlinkage accept_numeric.c cobmysqlapi.o -lncursesw -D_FORTIFY_SOURCE=1 -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT' -I ../copybooks -L/usr/local/mysql/lib -lmysqlclient -lz

exit 0
