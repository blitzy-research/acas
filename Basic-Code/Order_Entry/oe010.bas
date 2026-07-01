	REM *****************************************************************\
	    *							                            	    *\
	    *	   OE010.BAS	   ORDER ENTRY START OF DAY PROGRAM	        *\
	    *								                                *\
	    *****************************************************************

%INCLUDE oecommon

	DIM PR1.PASSWORD$(3), PR1.CREDCARD.CODE%(4), PR1.CREDCARD.NAME$(4)

	REM ***  OPEN & READ PARAMETER FILES  ***

	GOSUB 80000 : GOSUB 80200 : GOSUB 80020 : GOSUB 80220

	REM ***  TEST IF STOCK FILE TO BE EXTRACTED  ***

	IF PR1.STOCKFIL.IND%=0 THEN 500

	REM *** 				     ***\
	    *****  INSERT STOCK FILE EXTRACT HERE  *****\
	    *** 				     ***

500	REM ***  TEST IF CUSTOMER FILE TO BE EXTRACTED	***

	IF PR1.CUSTFIL.IND%=0 THEN 1000

	REM *** 					***\
	    *****  INSERT CUSTOMER FILE EXTRACT HERE  *****\
	    *** 					***

1000	REM ***  TEST IF SALES FILE IS LINKED  ***

	IF PR1.SALESFIL.IND%=0 THEN 1500

	REM *** 				      ***\
	    *****  INSERT SALES LEDGER CODING HERE  *****\
	    *** 				      ***

1500	FILE$="DISPATCH NOTE"            : DRIVE$=PR1.DISP.DRV$ : GOSUB 4000
        FILE$="SUSPENSE"                 : DRIVE$=PR1.SUSP.DRV$ : GOSUB 4000
	    FILE$="INVOICE"                  : DRIVE$=PR1.INV.DRV$  : GOSUB 4000
	    FILE$="CREDIT CARD VERIFICATION" : DRIVE$=PR1.DISP.DRV$ : GOSUB 4000
	    PRINT BELL$; "Press return when ready";
	    INPUT ""; LINE Z$
	    IF END #4 THEN 1505
	    GOSUB 80300 : GOTO 1510

1505	IF END#4 THEN 80365
	GOSUB 80360

1510	IF END #7 THEN 1515
	GOSUB 80600 : GOTO 1520

1515	IF END #7 THEN 80655
	GOSUB 80650

1520	IF END #8 THEN 1525
	GOSUB 80700 : GOTO 1530

1525	IF END #8 THEN 80765
	GOSUB 80760

1530	IF END #6 THEN 1600
	GOSUB 80500
	IF END #5 THEN 80410
	GOSUB 80400 : GOTO 1700

1600	IF END #5 THEN 1610
	GOSUB 80400 : GOTO 80510

1610	IF END #5 THEN 80475
	GOSUB 80470
	IF END #6 THEN 80565
	GOSUB 80560
	S2.KEY%=0 : S2.RECNO%=1 : N%=1
	IF END #6 THEN 80555
	GOSUB 80550

1700	PR3.STARTOF.DAY%=0 : PR3.ENDOF.DAY%=1
	IF END #3 THEN 80245
	GOSUB 80240

	REM ***  CLOSE FILES  ***

	CLOSE 1,3,4,5,6,7,8

	REM ***  GET MENU   ***

	CHAIN "oe100"

4000	PRINT BELL$; "Place "; FILE$; " file on drive "; DRIVE$
	RETURN

%include oepr1fil
%include oepr3fil
%include oedisfil
%include oesusfil
%include oesusind
%include oecrefil
%include oeinvfil
%include oefilsub
