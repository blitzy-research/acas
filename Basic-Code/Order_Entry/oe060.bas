	REM ******************************************************************\
	    *							                            	     *\
	    *	   OE060.BAS	    ORDER ENTRY SUSPENSE FILE PRINT PROGRAM  *\
	    *								                                 *\
	    ******************************************************************

%include oecommon

	DIM PR1.PASSWORD$(3), PR1.CREDCARD.CODE%(4), PR1.CREDCARD.NAME$(4)

	REM ***  OPEN & READ PARAMETER FILES  ***

	GOSUB 80000 : GOSUB 80200 : GOSUB 80020 : GOSUB 80220

	DIM PARTNO$(100), PARTDESC$(100), QUANTITY%(100), PRICE(100),\
		VAT(100)

	LINE%=0 : PAGE%=0

	F1$="/...5...10...15...20...25..../   "
	F2$="   #####      /...5..../      /...5../      "
	F3$="####      /...5...10/      /...5...10...15...20..../"
	F4$="/...5...10...15...20.../         "
	F5$="/...5.../        /...5...10../   "
	F6$="/...5..../   /...5...10...15...20...25..../    #####    "
	F7$="#####.##    ##.##    ######.##    #####.##"
	F8$="                                 "
	FORMAT1$=F1$+F2$+F3$ : FORMAT2$=F4$+F6$+F7$
	FORMAT3$=F5$+F6$+F7$ : FORMAT4$=F8$+F6$+F7$

	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(21)
	Z$=BELL$+"Press return when printer is ready" : GOSUB 12100
	R%=ROW%(5) : C%=COL%(56) : LENGTH%=1 : GOSUB 12200
	PRINT CLRS$
	R%=ROW%(5) : C%=COL%(28) : Z$="Printing suspense file" : GOSUB 12100

	REM ***  OPEN SUSPENSE FILE INDEX  ***

	IF END #6 THEN 80510
	GOSUB 80500

	REM ***  OPEN MAIN SUSPENSE FILE  ***

	IF END #5 THEN 80410
	GOSUB 80400

	REC%=1

	REM ***  READ INDEX RECORD  ***

100	REC%=REC%+1 : N%=REC%
	IF END #6 THEN 300
	GOSUB 80520

	J%=0

	REM ***  READ RECORD TYPE 1 ON MAIN SUSPENSE FILE ***

	N%=S2.RECNO%
	IF END #5 THEN 80422
	GOSUB 80420

	REM ***  CHECK IF LIVE ORDER  ***

	IF S1.DEL%=1 THEN 100

	REM ***  BUILD MAIN DETAILS  ***

	ORDNO%	 =S1.ORDNO%    : CUSTNAME$ =S1.CUSTNAME$
	CUSTADD1$=S1.CUSTADD1$ : CUSTADD2$ =S1.CUSTADD2$
	CUSTADD3$=S1.CUSTADD3$ : POSTCODE$ =S1.POSTCODE$
	CUSTTEL$ =S1.CUSTTEL$  : CUSTORDNO$=S1.CUST.ORDNO$
	PAY%	 =S1.PAY%      : REASON%   =S1.REASON%
	DATE$	 =S1.DATE$     : DATE%	   =S1.DATE%
	IF S1.INVOICE%=0 THEN 200

	REM ***  READ RECORD TYPE 2  ***

	N%=S1.NEXTREC%
	IF END #5 THEN 80430
	GOSUB 80428

	REM ***  GET DETAIL RECORDS  ***

200	N%=S1.NEXTREC%
	IF END #5 THEN 80426
	GOSUB 80424

	REM ***  CHECK IF LIVE RECORD  ***

	IF S1.DEL%=1 THEN 210

	REM *** BUILD DETAIL ARRAY  ***

	J%=J%+1
	PARTNO$(J%)  =S1.PARTNO$   : PARTDESC$(J%)=S1.PARTDESC$
	QUANTITY%(J%)=S1.QUANTITY% : PRICE(J%)	  =S1.PRICE
	VAT(J%)      =S1.VAT

210	IF S1.NEXTREC%=0 THEN 220
	GOTO 200

	REM ***  WRITE REPORT  ***

220	LPRINTER
	IF LINE%=0 THEN GOSUB 250
	IF PAY%=1 THEN PAY$="CASH"
	IF PAY%=2 THEN PAY$="CHEQUE"
	IF PAY%=3 THEN PAY$="CREDIT CARD"
	IF PAY%=4 THEN PAY$="CREDIT"
	IF S1.REASON%=1 THEN REASON$="Out of stock"
	IF S1.REASON%=2 THEN REASON$="Awaiting cheque clearance"
	IF S1.REASON%=3 THEN REASON$="Credit card verification"
	IF S1.REASON%=4 THEN REASON$="Proforma invoice issued"
	DAYS%=PR3.DATE%-S1.DATE%
	FOR I%=1 TO J%
		IF I%<>1 THEN 230
		IF LINE%+6>60 THEN GOSUB 250
		PRINT
		PRINT USING FORMAT1$; CUSTNAME$, ORDNO%, CUSTORDNO$, DATE$,\
			DAYS%, PAY$, REASON$
		PRINT USING F1$; CUSTADD1$
		PRINT USING F1$; CUSTADD2$
		TOT.PRICE=PRICE(I%)*QUANTITY%(I%)
		TOT.VAT  =VAT(I%)*TOT.PRICE/100
		PRINT USING FORMAT2$; CUSTADD3$, PARTNO$(I%), PARTDESC$(I%),\
			QUANTITY%(I%), PRICE(I%), VAT(I%), TOT.PRICE, TOT.VAT
		GOTO 249

230		IF I%<>2 THEN 240
		TOT.PRICE=PRICE(I%)*QUANTITY%(I%)
		TOT.VAT  =VAT(I%)*TOT.PRICE/100
		PRINT USING FORMAT3$; POSTCODE$, CUSTTEL$, PARTNO$(I%),\
			PARTDESC$(I%), QUANTITY%(I%), PRICE(I%), VAT(I%),\
			TOT.PRICE, TOT.VAT
		LINE%=LINE%+5
		GOTO 249

240		TOT.PRICE=PRICE(I%)*QUANTITY%(I%)
		TOT.VAT  =VAT(I%)*TOT.PRICE/100
		PRINT USING FORMAT4$; PARTNO$(I%), PARTDESC$(I%),\
			QUANTITY%(I%), PRICE(I%), VAT(I%), TOT.PRICE, TOT.VAT
		LINE%=LINE%+1
		IF LINE%=60 THEN GOSUB 250

249	NEXT I%
	IF J%=1 THEN PRINT USING F5$; POSTCODE$, CUSTTEL$
	FOR I%=1 TO 131 : PRINT "-"; : NEXT I% : PRINT "-"
	CONSOLE : GOTO 100

250	PAGE%=PAGE%+1
	PRINT CHR$(12);
	PRINT "   DATE "; PR3.DATE$; TAB(48);\
		"S U S P E N S E  F I L E  R E P O R T"; TAB(122); "PAGE";\
		PAGE%
	PRINT "   ============="; TAB(47);\
		"====================================="; TAB(121);
	IF PAGE%<10 THEN PRINT "======" : GOTO 255
	IF PAGE%<100 THEN PRINT "========" : GOTO 255
	PRINT "========="

255	PRINT
	PRINT "CUSTOMER NAME/ADDRESS/TEL.NO.       OUR REF     THEIR REF";\
		"         DATE        DAYS      PAY METHOD       ";\
		"REASON FOR SUSPENSE"
	PRINT "-----------------------------       -------     ---------";\
		"         ----        ----      ----------       ";\
		"-------------------"
	PRINT TAB(34); "STOCK NO."; TAB(53); "STOCK DESCRIPTION"; TAB(83);\
		"QTY       PRICE     VAT     TOT PRICE     TOT VAT"
	PRINT TAB(34); "---------"; TAB(53); "-----------------"; TAB(83);\
		"---       -----     ---     ---------     -------"
	LINE%=7
	RETURN

300	PRINT CLRS$
	R%=ROW%(5) : C%=COL%(34) : Z$=BELL$+"end of print" : GOSUB 12100
	CLOSE 1,3,5,6
	GOTO 90000

%include oeinpout
%include oepr1fil
%include oepr3fil
%include oesusfil
%include oesusind
%include oefilsub
%include oegetpgm
