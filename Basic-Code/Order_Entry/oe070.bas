
	REM ******************************************************************\
	    *								                                 *\
	    *	   OE070.BAS	    ORDER ENTRY DISPATCH NOTE PRINT PROGRAM  *\
	    *							                             	     *\
	    ******************************************************************

%include oecommon

	DIM PR1.PASSWORD$(3), PR1.CREDCARD.CODE%(4), PR1.CREDCARD.NAME$(4)

	REM ***  OPEN & READ PARAMETER FILES  ***

	GOSUB 80000 : GOSUB 80100 : GOSUB 80200 : GOSUB 80020
	GOSUB 80120 : GOSUB 80220

	DIM PARTNO$(100), PARTDESC$(100), QUANTITY%(100), INSTOCK%(100)

	F1$="OUR REF  /.../"
	F2$="                                    "
	F3$="TEL : /...5...10../"
	FORMAT1$=F1$+F2$+F3$
	F1$="YOUR REF /...5..../    ORDER DATE    /...5../     "
	F2$="DISPATCH NOTE DATE    /...5../"
	FORMAT2$=F1$+F2$
	F1$="         /...5..../        "
	F2$="/...5...10...15...20...25..../"
	F3$="        ###### //"
	FORMAT3$=F1$+F2$+F3$

	CONSOLE
	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(21)
	Z$=BELL$+"Press return when printer is ready" : GOSUB 12100
	R%=ROW%(5) : C%=COL%(56) : LENGTH%=1 : GOSUB 12200
	PRINT CLRS$
	R%=ROW%(5) : C%=COL%(27) : Z$="Printing dispatch notes" : GOSUB 12100

	REM ***  OPEN DISPATCH NOTE FILE  ***

	IF END #4 THEN 80310
	GOSUB 80300

	FIRSTREC%=0

	REM ***  READ DISPATCH NOTE FILE  ***

100	IF END #4 THEN 300
	GOSUB 80320
	IF D1.RECTYPE%=1 THEN 200

	REM ***  BUILD DETAILS ARRAY  ***

	IF END #4 THEN 80330
	GOSUB 80324
	J%=J%+1
	PARTNO$(J%)  =D1.PARTNO$   : PARTDESC$(J%)=D1.PARTDESC$
	QUANTITY%(J%)=D1.QUANTITY% : INSTOCK%(J%) =D1.INSTOCK%
	GOTO 100

	REM ***  RECORD TYPE 1 PROCESSING  ***

200	IF FIRSTREC%=1 THEN \
		GOSUB 500 \
	ELSE \
		FIRSTREC%=1
	IF END #4 THEN 80330
	GOSUB 80322
	ORDNO$	 =RIGHT$("     "+STR$(D1.ORDNO%),5)
	CUSTNAME$=D1.CUSTNAME$
	CUSTADD1$=D1.CUSTADD1$ : CUSTADD2$ =D1.CUSTADD2$
	CUSTADD3$=D1.CUSTADD3$ : CUSTORDNO$=D1.CUSTORDNO$
	POSTCODE$=D1.POSTCODE$ : DATE$	   =D1.DATE$
	PAY%	 =D1.PAY%      : J%	   =0
	GOTO 100

	REM ***  END OF FILE PROCESSING  ***

300	IF FIRSTREC%=1 THEN 305
	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(17)
	Z$=BELL$+"Dispatch note file empty - no records printed"
	GOSUB 12100 : GOTO 307

305	GOSUB 500  : PRINT CLRS$
	R%=ROW%(5) : C%=COL%(34) : Z$=BELL$+"End of print" : GOSUB 12100

307	CLOSE 1,2,3,4
	NAME1$=PR1.DISP.DRV$+"boedisfil.101"
	NAME2$=PR1.DISP.DRV$+"oedisfil.201"
	NAME3$=PR1.DISP.DRV$+"oedisfil.301"
	IF END #11 THEN 310
	FILE$=NAME3$ : N%=11
	GOSUB 85200
	DELETE 11

	REM-----BACKUP 201 TO 301----------------------------------------------

310	IF SIZE(NAME2$)=0 THEN 315
	Z%=RENAME(NAME3$,NAME2$)

	REM-----BACKUP 101 TO 201----------------------------------------------

315	Z%=RENAME(NAME2$,NAME1$)

	REM-----CREATE NEW 101 FILE--------------------------------------------

	IF END #4 THEN 80365
	GOSUB 80360
	CLOSE 4
	GOTO 90000

	REM ***  PRINT DISPATCH NOTE  ***

500	LPRINTER
	GOSUB 520
	FOR I%=1 TO J%
		IF INSTOCK%(I%)=1 THEN INSTOCK$="* " \
		ELSE INSTOCK$="  "
		PRINT USING FORMAT3$; PARTNO$(I%), PARTDESC$(I%), \
			QUANTITY%(I%), INSTOCK$
		LINE%=LINE%+1
		IF LINE%=60 THEN GOSUB 520
	NEXT I%

510	PRINT : PRINT
	IF PAY%=1 THEN PAY$="CASH"
	IF PAY%=2 THEN PAY$="CHEQUE"
	IF PAY%=3 THEN PAY$="CREDIT CARD"
	IF PAY%=4 THEN 512
	PRINT "PAID BY "; PAY$
	GOTO 515

512	PRINT "TERMS "; PR2.CREDIT.TERMS%; " DAYS"

515	PRINT "Items marked '*' are currently out of stock ";\
		"and will be delivered at a later date"
	CONSOLE : RETURN

520	PRINT CHR$(12); TAB(25); "D I S P A T C H  N O T E"
	PRINT TAB(24); "========================"
	PRINT
	PRINT "TO: "; CUSTNAME$; TAB(45); "FROM: "; PR2.NAME$
	PRINT "    "; CUSTADD1$; TAB(51); PR2.ADD1$
	PRINT "    "; CUSTADD2$; TAB(51); PR2.ADD2$
	PRINT "    "; CUSTADD3$; TAB(51); PR2.ADD3$
	PRINT "    "; POSTCODE$; TAB(51); PR2.POSTCODE$
	PRINT
	PRINT USING FORMAT1$; ORDNO$, PR2.TELNO$
	PRINT USING FORMAT2$; CUSTORDNO$, DATE$, PR3.DATE$
	PRINT
	PRINT TAB(10); "STOCK NO."; TAB(37); "DESCRIPTION"; TAB(66);\
		"QUANTITY"
	PRINT TAB(10); "---------"; TAB(37); "-----------"; TAB(66);\
		"--------"
	LINE%=14
	RETURN

%include oeinpout
%include oepr1fil
%include oepr2fil
%include oepr3fil
%include oedisfil
%include oefilsub
%include oegetpgm
