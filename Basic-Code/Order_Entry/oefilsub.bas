rem %NOLIST
	REM ******************************************************************\
	    *								                                 *\
	    *	   OEFILSUB.BAS       FILE CONTROL SUBROUTINES MODULE	     *\
	    *								                                 *\
	    ******************************************************************

85000	PRINT CHR$(128+7); ERROR$
	STOP

85100	OPEN FILE$ RECL M% AS N%
	RETURN

85200	OPEN FILE$ AS N%
	RETURN

85300	CREATE FILE$ RECL M% AS N%
	RETURN

85400	CREATE FILE$ AS N%
	RETURN
rem %LIST
