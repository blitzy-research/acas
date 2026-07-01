#!/bin/bash
# 11/03/2018 vbc - Added -Wlinkage to all compiles.
# 29/07/2025 vbc - Removed all references to accept_numeric -- too many problems.

#cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'

export COBCPY=../copybooks
export COB_COPY_DIR=../copybooks


for i in `ls sl*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -D_FORTIFY_SOURCE=1 -T $i.prn; echo "Compiled " $i;mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "compiled " $i; done

#for i in `ls sl*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage accept_numeric.c -lz -lncursesw -D_FORTIFY_SOURCE=1 -A   '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'; echo "compiled " $i; done
#echo "Compiled sl120"
cobc -x sales.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -D_FORTIFY_SOURCE=1

#Now make sales as a module incase user wishes to run via ACAS
cobc -m sales.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -D_FORTIFY_SOURCE=1 -T $i.prn; echo "Compiled " $i;mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`
cobc -m sl970.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -D_FORTIFY_SOURCE=1

#cobc -m sales.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -D_FORTIFY_SOURCE=1 accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'
#cobc -m sl970.cbl dummy-rdbmsMT.cbl accept_numeric.c -Wlinkage -lncursesw -D_FORTIFY_SOURCE=1 -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT' -I ../copybooks -lz

echo "Compiled for No RDBMS"

exit 0
