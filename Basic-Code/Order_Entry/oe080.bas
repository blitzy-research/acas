	REM ******************************************************************\
	    *								                                 *\
	    *	   OE080.BAS	    ORDER ENTRY INVOICE PRINT PROGRAM	     *\
	    *							                             	     *\
	    ******************************************************************

%include oecommon

	DIM PR1.PASSWORD$(3), PR1.CREDCARD.CODE%(4), PR1.CREDCARD.NAME$(4), \
		PARTNO$(100), PARTDESC$(100), QUANTITY%(100), PRICE(100), \
		VAT(20)

	REM-----OPEN & READ PARAMETER FILES------------------------------------

	GOSUB 80000 : GOSUB 80100 : GOSUB 80200
	GOSUB 80020 : GOSUB 80120 : GOSUB 80220

	REM-----SET UP FORMATS-------------------------------------------------

	F1$="OUR REF  #####         ORDER DATE     /...5../    "
	F2$="TEL: /...5...10../"
	FORMAT1$=F1$+F2$
	F1$="YOUR REF /...5..../    INVOICE DATE   /...5../    "
	F2$="VAT REG NO: /...5...10/"
	FORMAT2$=F1$+F2$
	F1$="/...5..../ /...5...10...15...20...25..../#####.## ##### "
	F2$="######.## ##.## #####.##"
	FORMAT3$=F1$+F2$
	F1$="" : FOR I=1 TO 40 : F1$=F1$+" " : NEXT I
	F2$="SUB TOTALS     #######.##      ######.##"
	FORMAT4$=F1$+F2$
	F2$="GRAND TOTAL   ########.##"
	FORMAT5$=F1$+F2$

	REM------DISPLAY INITIAL MESSAGES--------------------------------------

	CONSOLE
	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(21)
	Z$=BELL$+"Press return when printer is ready" : GOSUB 12100
	R%=ROW%(5) : C%=COL%(56) : LENGTH%=1 : GOSUB 12200
	PRINT CLRS$
	R%=ROW%(5) : C%=COL%(31) : Z$="Printing invoices" : GOSUB 12100

	REM-----OPEN INVOICE FILE----------------------------------------------

	IF END #8 THEN 80710
	GOSUB 80700

	FIRSTREC%=0

	REM-----READ INVOICE FILE----------------------------------------------

100	IF END #8 THEN 300
	GOSUB 80720
	IF I1.RECTYPE%=1 THEN 200

	REM-----BUILD DETAILS ARRAY--------------------------------------------

	IF END #8 THEN 80730
	GOSUB 80724
	J%=J%+1
	PARTNO$(J%)  =I1.PARTNO$   : PARTDESC$(J%)=I1.PARTDESC$
	QUANTITY%(J%)=I1.QUANTITY% : PRICE(J%)	  =I1.PRICE
	VAT(J%)      =I1.VAT
	GOTO 100

	REM-----PROCESS INVOICE RECORD-----------------------------------------

200	IF FIRSTREC%=1 THEN GOSUB 500 \
	ELSE FIRSTREC%=1
	IF END #8 THEN 80730
	GOSUB 80722
	ORDNO%	  =I1.ORDNO%	  : CUSTNAME$  =I1.CUSTNAME$
	CUSTADD1$ =I1.CUSTADD1$   : CUSTADD2$  =I1.CUSTADD2$
	CUSTADD3$ =I1.CUSTADD3$   : POSTCODE$  =I1.POSTCODE$
	CUSTORDNO$=I1.CUSTORDNO$  : DATE$      =I1.DATE$
	PAY%	  =I1.PAY%	  : INVOICE.NO%=I1.INVOICE.NO%
	J%	  =0
	GOTO 100

	REM-----END OF FILE PROCESSING-----------------------------------------

300	IF FIRSTREC%=1 THEN 305
	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(20)
	Z$=BELL$+"Invoice file empty - no records printed" : GOSUB 12100
	GOTO 307

305	GOSUB 500 : PRINT CLRS$
	R%=ROW%(5) : C%=COL%(34) : Z$=BELL$+"End of print" : GOSUB 12100

307	CLOSE 1,2,3,8
	NAME1$=PR1.DISP.DRV$+"oeinvfil.101"
	NAME2$=PR1.DISP.DRV$+"oeinvfil.201"
	NAME3$=PR1.DISP.DRV$+"oeinvfil.301"
	IF SIZE(NAME3$)=0 THEN 310
	FILE$=NAME3$ : N%=11
	GOSUB 85200 : DELETE 11

	REM-----BACKUP 201 TO 301----------------------------------------------

310	IF SIZE(NAME2$)=0 THEN 315
	Z%=RENAME(NAME3$,NAME2$)

	REM-----BACKUP 101  TO 201---------------------------------------------

315	Z%=RENAME(NAME2$,NAME1$)

	REM-----CREATE NEW 101-------------------------------------------------

	IF END #8 THEN 80765
	GOSUB 80760
	CLOSE 8
	GOTO 90000

	REM-----PRINT INVOICE--------------------------------------------------

500	LPRINTER
	GOSUB 550
	SUB.AMT=0 : SUB.VAT=0
	FOR I%=1 TO J%
		AMOUNT=PRICE(I%)*QUANTITY%(I%)
		SUB.AMT=SUB.AMT+AMOUNT
		VAT.AMT=AMOUNT*VAT(I%)/100
		SUB.VAT=SUB.VAT+VAT.AMT
		PRINT USING FORMAT3$; PARTNO$(I%), PARTDESC$(I%), PRICE(I%),\
			QUANTITY%(I%), AMOUNT, VAT(I%), VAT.AMT
		LINE%=LINE%+1
		IF LINE%=60 THEN GOSUB 550
	NEXT I%
	IF LINE%+7>60 THEN GOSUB 550
	PRINT TAB(56); "----------      ---------"
	PRINT USING FORMAT4$; SUB.AMT, SUB.VAT
	PRINT TAB(56); "----------      ---------"
	PRINT
	GRAND.TOT=SUB.AMT+SUB.VAT
	PRINT USING FORMAT5$; GRAND.TOT
	PRINT TAB(55); "==========="
	IF PAY%=1 THEN PAY$="CASH"
	IF PAY%=2 THEN PAY$="CHEQUE"
	IF PAY%=3 THEN PAY$="CREDIT CARD"
	IF PAY%=4 THEN 510
	PRINT "     PAID BY "; PAY$
	GOTO 520

510	PRINT "TERMS "; PR2.CREDIT.TERMS%; " DAYS"

520	CONSOLE
	RETURN

550	PRINT CHR$(12); TAB(33); "I N V O I C E"
	PRINT TAB(32); "============="
	PRINT
	PRINT "TO: "; CUSTNAME$; TAB(45); "FROM: "; PR2.NAME$
	PRINT "    "; CUSTADD1$; TAB(51); PR2.ADD1$
	PRINT "    "; CUSTADD2$; TAB(51); PR2.ADD2$
	PRINT "    "; CUSTADD3$; TAB(51); PR2.ADD3$
	PRINT "    "; POSTCODE$; TAB(51); PR2.POSTCODE$
	PRINT USING FORMAT1$; ORDNO%, DATE$, PR2.TELNO$
	PRINT USING FORMAT2$; CUSTORDNO$, PR3.DATE$, PR2.VATREGNO$
	PRINT
	PRINT " STOCK NO           DESCRIPTION             PRICE   ";\
		"QTY    AMOUNT  VAT   VAT AMT"
	PRINT " --------           -----------             -----   ";\
		"---    ------  ---   -------"
	PRINT
	LINE%=14
	RETURN

%include oeinpout
%include oepr1fil
%include oepr2fil
%include oepr3fil
%include oeinvfil
%include oefilsub
%include oegetpgm
