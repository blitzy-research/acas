rem	DEC. 02, 1979
999    rem-----normal end of job---------------
trash%=fn.msg%(function.name$+" COMPLETED")
common.return.code%=0
goto 999.3
999.1  rem-----abnormal end of job-------------
print using "&";fn.crt.sca$(crt.rows%-2, 1);left$(blank$, crt.columns%)
print using "&";fn.crt.sca$(crt.rows%-1, 1);"     "+function.name$+\
	" COMPLETED UNSUCCESSFULLY     "+crt.msg.trailer$
common.return.code%=1
goto 999.3
999.2  rem-----premature end of job------------
trash%=fn.msg%(function.name$+" TERMINATING AT OPERATOR'S REQUEST")
common.return.code%=2
999.3  rem-----return to menu or stop----------
if chained.from.root% \
	then	chain system$ \
	else	stop
