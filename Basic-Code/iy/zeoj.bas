rem     Apr. 24, 1979
999    rem-----normal end of job---------------
print:print:print
print tab(10);program$+" Completed"
print:print:print
common.return.code%=0
goto 999.3
999.1  rem-----abnormal end of job-------------
print:print:print
print tab(10);program$+" Completed Unsuccessfully"
print tab(10);system.name$ + " Terminating"
common.return.code%=1
print:print:print:print bell$
goto 999.3
999.2  rem-----premature end of job------------
print:print:print
print tab(10);program$+" Ending Prematurely"
print:print:print
common.return.code%=2
999.3  rem-----return to menu or stop----------

rem *** printer buffer fix (uk version 6/4/82 src)
        lprinter
        print : print : print
        console
rem *** end of fix ***

if chained.from.root% \
        then    chain system$ \
        else    stop

