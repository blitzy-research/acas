rem	DEC. 14, 1979
999    rem-----normal end of job---------------
print:print:print
print tab(10);program$+" COMPLETED"
print:print:print
common.return.code%=0
goto 999.3
999.1  rem-----abnormal end of job-------------
print:print:print
print tab(10);function$+" COMPLETED UNSUCCESSFULLY"
print tab(10);system$+" TERMINATING"
common.return.code%=1
print:print:print:print bell$
goto 999.3
999.2  rem-----premature end of job------------
print:print:print
print tab(10);function$+" TERMINATING AT OPERATOR'S REQUEST"
print:print:print
common.return.code%=2
999.3  rem-----return to menu or stop----------
if chained.from.root% \
	then	chain fn.file.name.out$(system$,null$,0,pw$,pms$) \
	else	stop
