	REM ******************************************************************\
	    *								                                 *\
	    *	   OE090A.BAS	    ORDER ENTRY CREDIT CARD PRINT PROGRAM    *\
	    *								                                 *\
	    ******************************************************************

%INCLUDE oecommon

	DIM PR1.PASSWORD$(3), PR1.CREDCARD.CODE%(4), PR1.CREDCARD.NAME$(4), \
		KEY$(5)

	PRINT CLRS$ : R%=ROW%(5)  : C%=COL%(21)
	Z$=BELL$+"PRESS RETURN WHEN PRINTER IS READY" : GOSUB 12100
	R%=ROW%(5)  : C%=COL%(56) : LENGTH=1	      : GOSUB 12200
	PRINT CLRS$ : R%=ROW%(5)  : C%=COL%(20)
	Z$="PRINTING CREDIT CARD VERIFICATION REPORT" : GOSUB 12100

	REM-----OPEN & READ PARAMETER FILE 1-----------------------------------

	GOSUB 80000 : GOSUB 80020

	REM-----CHECK QSORT IS ON DRIVE A--------------------------------------

	IF SIZE("A:QSORT.COM")=0 THEN 9000

	REM-----CHECK IF O/P FILE EXISTS AND DELETE----------------------------

	IF SIZE(PR1.CRED.DRV$+"oecred.prt")=0 THEN 100
	OPEN PR1.CRED.DRV$+"oecred.prt" AS 11
	DELETE 11

	REM-----DELETE OLD SORT PARAMETERS FILE--------------------------------

100	IF SIZE("a:oecred.srt")=0 THEN 200
	OPEN "a:oecred.srt" AS 11
	DELETE 11

	REM-----BUILD SORT PARAMETERS FILE-------------------------------------

200	PAD$		 =CHR$(0)		    REM PADDING CHARACTER
	EOF$		 =CHR$(26)		    REM END OF FILE MARKER
	FILL$		 ="        "                REM FILLER
	IF LEFT$(PR1.CRED.DRV$,1)="A" THEN \
		DRIVEIN$ =CHR$(1) :	   \	    REM I/P FILE DRIVE
		DRIVEOUT$=CHR$(1)		    REM O/P FILE DRIVE
	IF LEFT$(PR1.CRED.DRV$,1)="B" THEN \
		DRIVEIN$ =CHR$(2) :	   \	    REM I/P FILE DRIVE
		DRIVEOUT$=CHR$(2)		    REM O/P FILE DRIVE
	IF LEFT$(PR1.CRED.DRV$,1)="C" THEN \
		DRIVEIN$ =CHR$(3) :	   \	    REM I/P FILE DRIVE
		DRIVEOUT$=CHR$(3)		    REM O/P FILE DRIVE
	IF LEFT$(PR1.CRED.DRV$,1)="D" THEN \
		DRIVEIN$ =CHR$(4) :	   \	    REM I/P FILE DRIVE
		DRIVEOUT$=CHR$(4)		    REM O/P FILE DRIVE
	IN.NAME$	 =LEFT$("oecrefil"+FILL$,8) REM I/P FILE NAME
	IN.TYPE$	 =LEFT$("101"+FILL$,3)      REM I/P FILE TYPE
	OUT.NAME$	 =LEFT$("oecreprt"+FILL$,8) REM O/P FILE NAME
	OUT.TYPE$	 =LEFT$("101"+FILL$,3)      REM O/P FILE TYPE
	REC.LENGTH$	 =CHR$(220)		    REM I/P FILE REC LENGTH
	BACKUP.FLAG$	 =CHR$(0)		    REM OLD O/P FILE BACKUP
	DISK.CHANGE.FLAG$=CHR$(0)		    REM NEW O/P DISK FLAG
	CONSOLE.FLAG$	 =CHR$(1)		    REM STATISTICS PRINT
	WORK.DRIVE$	 =CHR$(1)		    REM WORK FILES DRIVE
	KEY$(1) 	 =CHR$(26)+CHR$(16)+"A"+"A" REM PRIMARY SORT KEY
	KEY$(2) 	 =CHR$(2)+CHR$(14)+"A"+"A"  REM SECONDARY SORT KEY
	KEY$(3) 	 =CHR$(0)+CHR$(0)+"A"+"N"   REM THIRD SORT KEY
	KEY$(4) 	 =CHR$(0)+CHR$(0)+"A"+"N"   REM FOURTH SORT KEY
	KEY$(5) 	 =CHR$(0)+CHR$(0)+"A"+"N"   REM FIFTH SORT KEY

	RECORD$=""
	RECORD$=RECORD$+DRIVEIN$+IN.NAME$+IN.TYPE$
	RECORD$=RECORD$+DRIVEOUT$+OUT.NAME$+OUT.TYPE$
	RECORD$=RECORD$+PAD$
	RECORD$=RECORD$+REC.LENGTH$
	RECORD$=RECORD$+PAD$+PAD$+PAD$+PAD$+PAD$
	RECORD$=RECORD$+BACKUP.FLAG$+DISK.CHANGE.FLAG$+CONSOLE.FLAG$
	RECORD$=RECORD$+WORK.DRIVE$
	FOR I%=1 TO 5 : RECORD$=RECORD$+KEY$(I%) : NEXT I%
	RECORD$=RECORD$+PAD$+PAD$+PAD$+PAD$+PAD$+PAD$+PAD$+PAD$
	RECORD$=RECORD$+EOF$

	REM-----OPEN SORT PARAMETER FILE---------------------------------------

	IF END #20 THEN 9010
	CREATE "a:oecred.srt" AS 20

	REM-----WRITE SORT PARAMETER FILE--------------------------------------

	PRINT #20; RECORD$

	REM-----CLOSE SORT PARAMETER FILE--------------------------------------

	CLOSE 20

	REM-----CREATE SUBMIT FILE---------------------------------------------

	END$ =CHR$(0)+CHR$(36)
	COM1$="CRUN2 oe qcred"
	COM2$="QSORT oecred.srt"

	REM-----OPEN SUBMIT FILE-----------------------------------------------

	IF END #20 THEN 9030
	CREATE "$$$.sub" RECL 128 AS 20

	REM-----WRITE SUBMIT FILE----------------------------------------------
	REM-----NOTE: COMMANDS ARE WRITTEN IN REVERSE ORDER OF EXECUTION-------

	IF END #20 THEN 9040
	PRINT USING "&"; #20; CHR$(LEN(COM1$))+COM1$+END$
	PRINT USING "&"; #20; CHR$(LEN(COM2$))+COM2$+END$

	REM-----CLOSE SUBMIT FILE----------------------------------------------

	CLOSE 20

	REM-----CLOSE PARAMETER FILE 1-----------------------------------------

	CLOSE 1

	REM-----EXECUTE SUBMIT FILE--------------------------------------------

	PRINT CLR$

500	STOP

9000	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(1)
	Z$=BELL$+"QSORT IS NOT PRESENT ON DRIVE A" : GOSUB 12100 : GOTO 500

9010	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(1)
	Z$=BELL$+"EOF ON SORT PARAMETERS FILE" : GOSUB 12100 : GOTO 500

9030	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(1)
	Z$=BELL$+"UNABLE TO OPEN SUBMIT FILE" : GOSUB 12100 : GOTO 500

9040	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(1)
	Z$=BELL$+"UNABLE TO WRITE TO SUBMIT FILE" : GOSUB 12100 : GOTO 500

%include oeinpout
%include oepr1fil
%include oefilsub
%include oegetpgm
