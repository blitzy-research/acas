#!/bin/bash
# 11/03/2018 vbc - Added -Wlinkage to all compiles.
# 25/10/2025 vbc - Chg for ACCEPT_NUMERIC static linkage
# 02/02/2026 vbc   Chg for all *.cbl files but there are 2 / 3 acting as templates
#                  for new programs with errors.

cobc -m ACCEPT_NUMERIC.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'

export COBCPY=../copybooks
export COB_COPY_DIR=../copybooks

for i in `ls *.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -D_FORTIFY_SOURCE=1 ACCEPT_NUMERIC.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT' -T $i.prn;  mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`; echo "compiled " $i; done

#for i in `ls py*.cbl`; do cobc -m $i dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage ACCEPT_NUMERIC.c -lz -lncursesw -D_FORTIFY_SOURCE=1 -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'; echo "compiled " $i; done

cobc -x payroll.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -D_FORTIFY_SOURCE=1 ACCEPT_NUMERIC.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'

#Now make payroll as a module incase user wishes to run via ACAS
cobc -m payroll.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -D_FORTIFY_SOURCE=1 ACCEPT_NUMERIC.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT' -T payroll.prn; echo "Compiled payroll"

#;mv $i.prn `echo $i.prn | sed 's/cbl.prn/prn/'`

#cobc -m payroll.cbl dummy-rdbmsMT.cbl -I ../copybooks -Wlinkage -lz -D_FORTIFY_SOURCE=1 accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H -DDECIMAL_RIGHT'

echo "Compiled for No RDBMS"

exit 0
