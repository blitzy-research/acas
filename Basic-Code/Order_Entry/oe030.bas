	REM ******************************************************************\
     *                                                                *\
     *	 OE030.BAS    ORDER ENTRY SUSPENDED ORDER PROCEED PROGRAM      *\
     *                                                                *\
     ******************************************************************

	REM ***  The following variable names are used in this program	***\
	    ***       ORDNO%		 - Order number 		***\
	    ***       S1.CUST.ORDNO$	 - Customer order number	***\
	    ***       S1.CUSTNAME$	 - Customer name		***\
	    ***       S1.CUSTADD1$ }					***\
	    ***       S1.CUSTADD2$ }	 - Customer address		***\
	    ***       S1.CUSTADD3$ }					***\
	    ***       S1.POSTCODE$ }					***\
	    ***       S1.CUSTTEL$	 - Customer telephone number	***\
	    ***       S1.PAY%		 - Payment method		***\
	    ***       S1.INVOICE%	 - Invoice flag 		***\
	    ***       S1.INV.NAME$	 - Invoice name 		***\
	    ***       S1.INV.ADD1$     }				***\
	    ***       S1.INV.ADD2$     } - Invoice address		***\
	    ***       S1.INV.ADD2$     }				***\
	    ***       S1.INV.POSTCODE$ }				***\
	    ***       S1.INV.TEL$	 - Invoice telephone number	***\
	    ***       PARTNO$(n)	 - Part number			***\
	    ***       PARTDESC$(n)	 - Part description		***\
	    ***       QUANTITY%(n)	 - Quantity			***\
	    ***       PRICE(n)		 - Price			***\
	    ***       VAT(n)		 - VAT rate			***\
	    ***       INSTOCK%(n)	 - In stock indicator		***

%INCLUDE oecommon

	DIM PR1.PASSWORD$(3), PR1.CREDCARD.CODE%(4), PR1.CREDCARD.NAME$(4)

	REM-----OPEN & READ PARAMETER FILES------------------------------------

	GOSUB 80000 : GOSUB 80200 : GOSUB 80020 : GOSUB 80220

	DIM LINE$(11), PARTNO$(100), PARTDESC$(100), QUANTITY%(100),\
		PRICE(100), VAT(100), INSTOCK%(100), ERROR.MSG$(5)

	REM-----SET UP SCREEN LAYOUT-------------------------------------------

	DATA "FUNCTION 02 - PROCEED WITH SUSPENDED ORDER"
	DATA "ORDER NO  [     ]"
	DATA "CUSTOMER REF"
	DATA "CUSTOMER NAME"
	DATA "CUSTOMER ADDRESS"
	DATA "CUSTOMER TEL NO"
	DATA "PAYMENT METHOD"
	DATA "INVOICE NUMBER      [     ]"
	DATA "TOTAL AMOUNT"
	DATA "TOTAL VAT"
	DATA "CORRECT ORDER (Y/N) [ ]"

	FOR I%=1 TO 11 : READ LINE$(I%) : NEXT I%

	REM-----SET UP ERROR MESAGES-------------------------------------------

	DATA "Invalid order number"
	DATA "This order number is not suspended "
	DATA "This order has already been released "
	DATA "Invalid - must be Y or N"
	DATA "Invalid invoice number"

	FOR I%=1 TO 5 : READ ERROR.MSG$(I%) : NEXT I%

	REM-----OPEN OTHER FILES-----------------------------------------------

	IF END #4 THEN 80310
	GOSUB 80300
	IF END #5 THEN 80410
	GOSUB 80400
	IF END #6 THEN 80510
	GOSUB 80500
	IF END #7 THEN 80710
	GOSUB 80700

	REM ******************************************\
	    * INSERT CODING TO OPEN STOCK FILE       *\
	    ******************************************\
	    Use the ACAS Cobol FH (File handler) that \
	     creates a C module                      *


	REM-----POSITION AT END OF DISPATCH NOTE FILE--------------------------

	TRUE%=-1
	WHILE TRUE%
	IF END #4 THEN 100
		GOSUB 80320
		IF END #4 THEN 80330
		IF D1.RECTYPE%=1 THEN GOSUB 80322 \
		ELSE GOSUB 80324
	WEND

	REM-----POSITION AT END OF INVOICE FILE--------------------------------

100	TRUE%=-1
	WHILE TRUE%
		IF END #8 THEN 200
		GOSUB 80720
		IF END #8 THEN 80730
		IF I1.RECTYPE%=1 THEN GOSUB 80722 \
		ELSE GOSUB 80724
	WEND

	REM-----READ FIRST RECORD ON SUSPENSE INDEX----------------------------

200	IF END #6 THEN 80530
	N%=1 : GOSUB 80520 : INDEX.END%=S2.RECNO%

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
	N%=KEY.REC% : GOSUB 80420

	REM-----TEST IF LIVE ORDER---------------------------------------------

	IF S1.DEL%=1 THEN \
		R%=ROW%(23) : C%=COL%(1) :\
		Z$=BELL$+ERROR.MSG$(3)+EOL$ :\
		GOSUB 12100 : GOTO 305

	REM-----TEST IF INVOICE RECORD EXISTS----------------------------------

	IF S1.INVOICE%=0 THEN 320

	REM-----GET INVOICE RECORD---------------------------------------------

	IF END #5 THEN 80430
	N%=S1.NEXTREC% : GOSUB 80428

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
	GOSUB 11070 : GOSUB 11090 : GOSUB 11100 : GOSUB 11110
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
	IF F%=0   THEN GOSUB 11110 : GOTO 350
	IF F%=1   THEN 500
	IF F%=2   THEN 300
	Z$=UCASE$(Z$)
	IF Z$="Y" THEN 360
	IF Z$="N" THEN 300
	R%=ROW%(23) : C%=COL%(1)
	Z$=BELL$+ERROR.MSG$(4)+EOL$ : GOSUB 12100
	GOSUB 11110 : GOTO 350

	REM-----WRITE SUSPENDED ORDER TO DISPATCH NOTE AND INVOICE FILES-------

360	IF S1.INVOICE%=0 THEN 380
	GOSUB 11080
	IF PR1.INVNO.GEN%=1 THEN \
		INVNO%=PR3.INVOICE.NO% :\
		PR3.INVOICE.NO%=PR3.INVOICE.NO%+1 : ESC.FLAG1%=1 :\
		R%=ROW%(17) : C%=COL%(47) : Z$=STR$(INVNO%) : GOSUB 12100 :\
		GOTO 380

370	R%=ROW%(17) : C%=COL%(47) : LENGTH%=5 : GOSUB 12200
	IF F%=0  THEN GOSUB 11080 : GOTO 370
	IF F%=1  THEN 500
	IF F%=2  THEN GOSUB 11080 : GOSUB 11110 : GOTO 350
	IF Z$="" THEN R%=ROW%(23) : C%=COL%(1) :\
		Z$=BELL$+ERROR.MSG$(5)+EOL$ :\
		GOSUB 12100 : GOTO 370
	FOR I%=1 TO LEN(Z$)
		I=ASC(MID$(Z$,I%,1))
		IF I<48 OR I>57 THEN \
			R%=ROW%(23) : C%=COL%(1) :\
			Z$=BELL$+ERROR.MSG$(5)+EOL$ :\
			GOSUB 12100 : GOTO 370
	NEXT I%
	INVNO%=VAL(Z$)

380	FOR I%=1 TO J%
		INSTOCK%(I%)=0
	NEXT I%
	PART.DEL.FLAG%=0 : DISP.FIRSTREC%=0 : INV.FIRSTREC%=0

	REM ***************************************\
	    *	INSERT STOCK CHECK ROUTINE HERE   *\
	    ***************************************

	REM-----TEST THAT NO. OF PARTS IN ORDER > PARTS OUT OF STOCK-----------

	IF PART.DEL.FLAG%=J% THEN 420
	FOR I%=1 TO J%
		IF DISP.FIRSTREC%=1 THEN 390
		D1.ORDNO%   =ORDNO%	  : D1.RECTYPE%  =1
		D1.CUSTNAME$=S1.CUSTNAME$ : D1.CUSTADD1$ =S1.CUSTADD1$
		D1.CUSTADD2$=S1.CUSTADD2$ : D1.CUSTADD3$ =S1.CUSTADD3$
		D1.POSTCODE$=S1.POSTCODE$ : D1.CUSTORDNO$=S1.CUST.ORDNO$
		D1.DATE$    =S1.DATE$	  : D1.PAY%	 =S1.PAY%
		IF END#4 THEN 80345
		GOSUB 80340
		DISP.FIRSTREC%=1

390		D1.RECTYPE% =2		   : D1.PARTNO$  =PARTNO$(I%)
		D1.PARTDESC$=PARTDESC$(I%) : D1.QUANTITY%=QUANTITY%(I%)
		D1.INSTOCK% =INSTOCK%(I%)
		IF END #4 THEN 80355
		GOSUB 80350

	REM-----TEST IF INVOICE IS TO BE CREATED-------------------------------

		IF S1.INVOICE%=0 OR INSTOCK%(I%)=1 THEN 410
		IF INV.FIRSTREC%=1 THEN 400
		I1.ORDNO%     =ORDNO%		: I1.RECTYPE%  =1
		I1.CUSTNAME$  =S1.INV.NAME$	: I1.CUSTADD1$ =S1.INV.ADD1$
		I1.CUSTADD2$  =S1.INV.ADD2$	: I1.CUSTADD3$ =S1.INV.ADD3$
		I1.POSTCODE$  =S1.INV.POSTCODE$ : I1.CUSTORDNO$=S1.CUST.ORDNO$
		I1.DATE$      =S1.DATE$ 	: I1.PAY%      =S1.PAY%
		I1.INVOICE.NO%=INVNO%
		IF END #8 THEN 80745
		GOSUB 80740
		INV.FIRSTREC%=1

400		I1.RECTYPE% =2		   : I1.PARTNO$  =PARTNO$(I%)
		I1.PARTDESC$=PARTDESC$(I%) : I1.QUANTITY%=QUANTITY%(I%)
		I1.PRICE    =PRICE(I%)	   : I1.VAT	 =VAT(I%)
		IF END #8 THEN 80755
		GOSUB 80750

410	NEXT I%

	REM-----MAKE CHANGES TO SUSPENSE FILE----------------------------------

	REM-----READ SUSPENSE REC TYPE 1---------------------------------------

420	IF END #5 THEN 80422
	N%=KEY.REC% : GOSUB 80420
	IF PART.DEL.FLAG%=0 THEN S1.DEL%=1 \
	ELSE S1.REASON%=1
	IF END #5 THEN 80445
	GOSUB 80440
	IF S1.INVOICE%=0 THEN 430

	REM-----GET INVOICE RECORD---------------------------------------------

	IF END #5 THEN 80430
	N%=S1.NEXTREC% : GOSUB 80428
	IF PART.DEL.FLAG%>0 THEN 430
	S1.DEL%=1
	IF END #5 THEN 80465
	GOSUB 80460

	REM-----READ RECORD TYPE 3---------------------------------------------

430	FOR I%=1 TO J%

435		IF END #5 THEN 80426
		N%=S1.NEXTREC% : GOSUB 80424
		IF PARTNO$(I%)<>S1.PARTNO$ THEN 435
		IF INSTOCK%(I%)=0	   THEN S1.DEL%=1
		IF END #5 THEN 80455
		GOSUB 80450
	NEXT I%
	GOTO 300

500	IF ESC.FLAG%=1 THEN PR3.INVOICE.NO%=PR3.INVOICE.NO%-1
	IF END #3      THEN 80245
	GOSUB 80240
	CLOSE 1,3,4,5,6,8
	GOTO 90000

11010	R%=ROW%(1)  : C%=COL%(20) : Z$=LINE$(1)       : GOSUB 12100 : RETURN
11020	R%=ROW%(3)  : C%=COL%(1)  : Z$=LINE$(2)       : GOSUB 12100 : RETURN
11030	R%=ROW%(3)  : C%=COL%(26) : Z$=LINE$(3)+EOL$  : GOSUB 12100 : RETURN
11040	R%=ROW%(4)  : C%=COL%(26) : Z$=LINE$(4)+EOL$  : GOSUB 12100 : RETURN
11050	R%=ROW%(5)  : C%=COL%(26) : Z$=LINE$(5)+EOL$  : GOSUB 12100 : RETURN
11060	R%=ROW%(9)  : C%=COL%(26) : Z$=LINE$(6)+EOL$  : GOSUB 12100 : RETURN
11070	R%=ROW%(10) : C%=COL%(26) : Z$=LINE$(7)+EOL$  : GOSUB 12100 : RETURN
11080	R%=ROW%(17) : C%=COL%(26) : Z$=LINE$(8)+EOL$  : GOSUB 12100 : RETURN
11090	R%=ROW%(11) : C%=COL%(26) : Z$=LINE$(9)+EOL$  : GOSUB 12100 : RETURN
11100	R%=ROW%(12) : C%=COL%(26) : Z$=LINE$(10)+EOL$ : GOSUB 12100 : RETURN
11110	R%=ROW%(15) : C%=COL%(26) : Z$=LINE$(11)+EOL$ : GOSUB 12100 : RETURN

%include oeinpout
%include oepr1fil
%include oepr3fil
%include oedisfil
%include oesusfil
%include oesusind
%include oeinvfil
%include oefilsub
%include oegetpgm
