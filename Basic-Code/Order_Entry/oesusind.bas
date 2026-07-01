REM %NOLIST
REM  ******************************************************************\
     *                                                                *\
     *    OESUSIND.BAS       SUSPENSE INDEX FILE CONTROL MODULE       *\
     *                                                                *\
     ******************************************************************

	REM ***  OPEN SUSPENSE FILE INDEX  ***

80500	FILE$=PR1.SUSP.DRV$+"OESUSIND.101" : M%=12 : N%=6 : GOSUB 85100
 RETURN

80510	ERROR$="UNABLE TO OPEN SUSPENSE FILE INDEX"
 GOTO 85000

 REM ***  READ SUSPENSE FILE INDEX  ***

80520	READ #6,N%; S2.KEY%, S2.RECNO%
	RETURN

80530	ERROR$="UNABLE TO READ SUSPENSE FILE INDEX"
	GOTO 85000

	REM ***  WRITE SUSPENSE INDEX RECORD  ***

80550	PRINT #6,N%; S2.KEY%, S2.RECNO%
	RETURN

80555	ERROR$="UNABLE TO WRITE SUSPENSE FILE INDEX"
	GOTO 85000

	REM ***  CREATE SUSPENSE FILE INDEX  ***

80560	FILE$=PR1.SUSP.DRV$+"OESUSIND.101" : M%=12 : N%=6 : GOSUB 85300
	RETURN

80565	ERROR$="UNABLE TO CREATE SUSPENSE FILE INDEX"
	GOTO 85000
REM %LIST
