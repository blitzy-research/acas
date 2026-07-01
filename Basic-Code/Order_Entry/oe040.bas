	REM ******************************************************************\
	    *								                                 *\
	    *	 OE040.BAS    ORDER ENTRY SUSPENDED ORDER CANCEL PROGRAM     *\
	    *								                                 *\
	    ******************************************************************

	REM ***  The following variable names are used in this program	***\
	    ***       ORDNO%		 - Order number 		***\
	    ***       S1.INVOICE%	 - Invoice flag 		***\
	    ***       PARTNO$(n)	 - Part number			***\
	    ***       PARTDESC$(n)	 - Part description		***\
	    ***       QUANTITY%(n)	 - Quantity			***\
	    ***       PRICE(n)		 - Price			***\
	    ***       VAT(n)		 - VAT rate			***

%INCLUDE oecommon

	DIM PR1.PASSWORD$(3), PR1.CREDCARD.CODE%(4), PR1.CREDCARD.NAME$(4)

	REM-----OPEN & READ PARAMETER FILES------------------------------------

	GOSUB 80000 : GOSUB 80020

	DIM LINE$(11), PARTNO$(100), PARTDESC$(100), QUANTITY%(100),\
		PRICE(100), VAT(100), INSTOCK%(100), ERROR.MSG$(4)

	REM-----SET UP SCREEN LAYOUT-------------------------------------------

	DATA "FUNCTION 03 - CANCEL SUSPENDED ORDER"
	DATA "ORDER NO  [     ]"
	DATA "CUSTOMER REF"
	DATA "CUSTOMER NAME"
	DATA "CUSTOMER ADDRESS"
	DATA "CUSTOMER TEL NO"
	DATA "PAYMENT METHOD"
	DATA "TOTAL AMOUNT"
	DATA "TOTAL VAT"
	DATA "CORRECT ORDER (Y/N) [ ]"

	FOR I%=1 TO 10 : READ LINE$(I%) : NEXT I%

	REM-----SET UP ERROR MESSAGES------------------------------------------

	DATA "INVALID ORDER NUMBER"
	DATA "This order number not suspended"
	DATA "This order is no longer suspended"
	DATA "Invalid - must be Y or N"

	FOR I%=1 TO 4 : READ ERROR.MSG$(I%) : NEXT I%

	REM-----OPEN SUSPENSE FILES--------------------------------------------

	IF END #5 THEN 80410
	GOSUB 80400
	IF END #6 THEN 80510
	GOSUB 80500

	REM-----READ FIRST RECORD ON SUSPENSE INDEX----------------------------

200	IF END #6 THEN 80530
	N%=1 : GOSUB 80520
	INDEX.END%=S2.RECNO%

	REM-----DISPLAY SCREEN-------------------------------------------------

	PRINT CLRS$ : GOSUB 11010

300	R%=ROW%(2)  : C%=COL%(1) : Z$=EOP$     : GOSUB 12100 : ESC.FLAG%=0

305	GOSUB 11020 : R%=ROW%(3) : C%=COL%(12) : LENGTH%=5   : GOSUB 12200
	IF F%=0 THEN 305
	IF F%=1 THEN 500
	IF F%=2 THEN 305
	IF Z$="" THEN 305
	FOR I%=1 TO LEN(Z$)
		I=ASC(MID$(Z$,I%,1))
		IF I<48 OR I>57 THEN \
			R%=ROW%(23) : C%=COL%(1) :\
			Z$=BELL$+ERROR.MSG$(1)+EOL$ :\
			GOSUB 12100 : GOTO 305
	NEXT I%
	ORDNO%=VAL(Z$)

	REM-----GET ORDER NUMBER ON SUSPENSE INDEX-----------------------------

	IF END #6 THEN 80530
	FOR N%=2 TO INDEX.END%
		GOSUB 80520
		IF S2.KEY%=ORDNO% THEN 310
	NEXT N%
	R%=ROW%(23) : C%=COL%(1)
	Z$=BELL$+ERROR.MSG$(2)+EOL$
	GOSUB 12100 : GOTO 305

310	KEY.REC%=S2.RECNO%

	REM-----READ SUSPENSE REC TYPE 1---------------------------------------

	IF END #5 THEN 80422
	N%=KEY.REC%
	GOSUB 80420

	REM-----TEST IF LIVE ORDER---------------------------------------------

	IF S1.DEL%=1 THEN \
		R%=ROW%(23) : C%=COL%(1) :\
		Z$=BELL$+ERROR.MSG$(3)+EOL$ :\
		GOSUB 12100 : GOTO 305

	REM-----TEST IF INVOICE RECORD EXISTS----------------------------------

	IF S1.INVOICE%=0 THEN 320

	REM-----GET INVOICE RECORD---------------------------------------------

	IF END #5 THEN 80430
	N%=S1.NEXTREC%
	GOSUB 80428

	REM-----READ RECORD TYPE 3---------------------------------------------

320	IF END #5 THEN 80426
	J%=0

330	IF S1.NEXTREC%=0 THEN 340
	N%=S1.NEXTREC% : GOSUB 80424

	REM-----CHECK THAT IT IS A SUSPENDED PART------------------------------

	IF S1.DEL%=1 THEN 330
	J%=J%+1
	PARTNO$(J%)  =S1.PARTNO$   : PARTDESC$(J%)=S1.PARTDESC$
	QUANTITY%(J%)=S1.QUANTITY% : PRICE(J%)	  =S1.PRICE
	VAT(J%)      =S1.VAT
	GOTO 330

340	TOT.AMT=0 : TOT.VAT=0
	FOR I%=1 TO J%
		TOT.AMT=TOT.AMT+(PRICE(I%)*QUANTITY%(I%))
		TOT.VAT=TOT.VAT+(PRICE(I%)*QUANTITY%(I%)*VAT(I%)/100)
	NEXT I%
	IF S1.PAY%=1 THEN PAY$="CASH"
	IF S1.PAY%=2 THEN PAY$="CHEQUE"
	IF S1.PAY%=3 THEN PAY$="CREDIT CARD"
	IF S1.PAY%=4 THEN PAY$="CREDIT"

	REM-----DISPLAY ORDER DETAILS------------------------------------------

	GOSUB 11030 : GOSUB 11040 : GOSUB 11050 : GOSUB 11060
	GOSUB 11070 : GOSUB 11080 : GOSUB 11090 : GOSUB 11100
	C%=COL%(46)
	R%=ROW%(3)  : Z$=S1.CUST.ORDNO$ : GOSUB 12100
	R%=ROW%(4)  : Z$=S1.CUSTNAME$	: GOSUB 12100
	R%=ROW%(5)  : Z$=S1.CUSTADD1$	: GOSUB 12100
	R%=ROW%(6)  : Z$=S1.CUSTADD2$	: GOSUB 12100
	R%=ROW%(7)  : Z$=S1.CUSTADD3$	: GOSUB 12100
	R%=ROW%(8)  : Z$=S1.POSTCODE$	: GOSUB 12100
	R%=ROW%(9)  : Z$=S1.CUSTTEL$	: GOSUB 12100
	R%=ROW%(10) : Z$=PAY$		: GOSUB 12100
	R%=ROW%(11) : Z$=STR$(TOT.AMT)	: GOSUB 12100
	R%=ROW%(12) : Z$=STR$(TOT.VAT)	: GOSUB 12100

350	R%=ROW%(15) : C%=COL%(47) : LENGTH%=1 : GOSUB 12200
	IF F%=0 THEN \
		GOSUB 11100 : GOTO 350
	IF F%=1 THEN 500
	IF F%=2 THEN 300
	Z$=UCASE$(Z$)
	IF Z$="Y" THEN 420
	IF Z$="N" THEN 300
	R%=ROW%(23) : C%=COL%(1)
	Z$=BELL$+ERROR.MSG$(4)+EOL$
	GOSUB 12100 : GOSUB 11100 : GOTO 350

	REM-----MAKE CHANGES TO SUSPENSE FILE----------------------------------

	REM-----READ SUSPENSE REC TYPE 1---------------------------------------

420	IF END #5 THEN 80422
	N%=KEY.REC%
	GOSUB 80420
	S1.DEL%=1
	IF END #5 THEN 80445
	GOSUB 80440
	IF S1.INVOICE%=0 THEN 430

	REM-----GET INVOICE RECORD---------------------------------------------

	IF END #5 THEN 80430
	N%=S1.NEXTREC%
	GOSUB 80428
	S1.DEL%=1
	IF END #5 THEN 80465
	GOSUB 80460

	REM-----READ RECORD TYPE 3---------------------------------------------

430	IF S1.NEXTREC%=0 THEN 300
	IF END #5 THEN 80426
	N%=S1.NEXTREC%
	GOSUB 80424
	S1.DEL%=1
	IF END #5 THEN 80455
	GOSUB 80450
	GOTO 430

500	CLOSE 1,5,6
	GOTO 90000

11010	R%=ROW%(1)  : C%=COL%(23) : Z$=LINE$(1)       : GOSUB 12100 : RETURN
11020	R%=ROW%(3)  : C%=COL%(1)  : Z$=LINE$(2)       : GOSUB 12100 : RETURN
11030	R%=ROW%(3)  : C%=COL%(26) : Z$=LINE$(3)+EOL$  : GOSUB 12100 : RETURN
11040	R%=ROW%(4)  : C%=COL%(26) : Z$=LINE$(4)+EOL$  : GOSUB 12100 : RETURN
11050	R%=ROW%(5)  : C%=COL%(26) : Z$=LINE$(5)+EOL$  : GOSUB 12100 : RETURN
11060	R%=ROW%(9)  : C%=COL%(26) : Z$=LINE$(6)+EOL$  : GOSUB 12100 : RETURN
11070	R%=ROW%(10) : C%=COL%(26) : Z$=LINE$(7)+EOL$  : GOSUB 12100 : RETURN
11080	R%=ROW%(11) : C%=COL%(26) : Z$=LINE$(8)+EOL$  : GOSUB 12100 : RETURN
11090	R%=ROW%(12) : C%=COL%(26) : Z$=LINE$(9)+EOL$  : GOSUB 12100 : RETURN
11100	R%=ROW%(15) : C%=COL%(26) : Z$=LINE$(10)+EOL$ : GOSUB 12100 : RETURN

%include oeinpout
%include oepr1fil
%include oesusfil
%include oesusind
%include oefilsub
%include oegetpgm
