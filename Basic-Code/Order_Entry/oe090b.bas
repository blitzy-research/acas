	REM ******************************************************************\
	    *								                                 *\
	    *	   OE090B.BAS	    ORDER ENTRY CREDIT CARD PRINT PROGRAM    *\
	    *								                                 *\
	    ******************************************************************

%include oecommon

	DIM PR1.PASSWORD$(3), PR1.CREDCARD.CODE%(4), PR1.CREDCARD.NAME$(4)

	REM-----OPEN & READ PARAMETER FILES 1 & 3------------------------------

	GOSUB 80000 : GOSUB 80200 : GOSUB 80020 : GOSUB 80220

	REM-----SET UP FORMATS-------------------------------------------------

	F1$="     /...5...10...15/    /...5...10.../    /.../    "
	F3$="/...5...10...15...20...25..../"
	F4$="    /.../    #######.##"
	F5$="/...5.../       /...5...10../"
	F6$="" : FOR I=1 TO 52 : F6$=F6$+" " : NEXT I
	FORMAT1$=F1$+F3$+F4$			REM PRINT LINE 1
	FORMAT2$=F6$+F3$			REM PRINT LINE 2
	FORMAT3$=F6$+F5$			REM PRINT LINE 3

	REM-----SET UP REPORT HEADING FORMATS----------------------------------

	F1$="DATE /...5../"+LEFT$(F6$,24)
	F2$="C R E D I T  C A R D  V E R I F I C A T I O N  R E P O R T"
	F3$=LEFT$(F6$,28)+"PAGE ###"
	HEADING1$=F1$+F2$+F3$			REM HEADING LINE 1
	F1$="============="+LEFT$(F6$,24)
	F2$="=========================================================="
	F3$=LEFT$(F6$,29)+"========"
	HEADING2$=F1$+F2$+F3$			REM HEADING LINE 2
	F1$="     CREDIT CARD NAME     CARD NUMBER     EXPIRY"
	F2$="    CUSTOMER NAME/ADDRESS/TEL.NO.    OUR REF       AMOUNT"
	F3$="    AUTHORISATION CODE"
	HEADING3$=F1$+F2$+F3$			REM HEADING LINE 3
	F1$="     ----------------     -----------     ------"
	F2$="    -----------------------------    -------      ------"
	F3$="    ------------------"
	HEADING4$=F1$+F2$+F3$			REM HEADING LINE 4

	REM-----OPEN SORTED CREDIT CARD FILE-----------------------------------

	IF END #20 THEN 80810
	GOSUB 80800

	CARDCHANGE$="" : FIRSTREC%=0 : LINE%=0 : PAGE%=0
	LPRINTER

	REM-----READ CREDIT CARD FILE------------------------------------------

100	IF END #20 THEN 300
	GOSUB 80820 : FIRSTREC%=1
	IF C1.CREDNAME$<>CARDCHANGE$ OR LINE%+6>60 THEN GOSUB 200
	C1.ORDER.TOTAL=VAL(C1.ORDER.TOTAL$)
	PRINT
	PRINT USING FORMAT1$; C1.CREDNAME$, C1.CREDNO$, C1.EXPIRY$,\
		C1.CUSTNAME$, C1.ORDNO$, C1.ORDER.TOTAL
	PRINT USING FORMAT2$; C1.CUSTADD1$
	PRINT USING FORMAT2$; C1.CUSTADD2$
	PRINT USING FORMAT2$; C1.CUSTADD3$
	PRINT USING FORMAT3$; C1.POSTCODE$, C1.CUSTTEL$
	LINE%=LINE%+6
	GOTO 100

200	PAGE%=PAGE%+1
	PRINT CHR$(12);
	PRINT USING HEADING1$; PR3.DATE$, PAGE%
	PRINT HEADING2$
	PRINT
	PRINT HEADING3$
	PRINT HEADING4$
	LINE%=5
	CARDCHANGE$=C1.CREDNAME$
	RETURN

300	CONSOLE
	IF FIRSTREC%=1 THEN 305
	PRINT CLRS$ : R%=ROW%(5) : C%=COL%(17)
	Z$=BELL$+"CREDIT CARD FILE EMPTY - NO RECORDS PRINTED"
	GOSUB 12100 : GOTO 307

305	PRINT CLRS$
	R%=ROW%(5) : C%=COL%(34) : Z$=BELL$+"END OF PRINT" : GOSUB 12100

	REM-----DELETE PRINT FILE----------------------------------------------

307	DELETE 20
	CLOSE 1,3
	NAME1$=PR1.CRED.DRV$+"oecrefil.101"
	NAME2$=PR1.CRED.DRV$+"oecrefil.201"
	NAME3$=PR1.CRED.DRV$+"oecrefil.301"
	IF SIZE(NAME3$)=0 THEN 310
	FILE$=NAME3$ : N%=11
	GOSUB 85200
	DELETE N%

	REM-----BACKUP 201 TO 301----------------------------------------------

310	IF SIZE(NAME2$)=0 THEN 315
	Z%=RENAME(NAME3$,NAME2$)

	REM-----BACKUP 101 TO 201----------------------------------------------

315	Z%=RENAME(NAME2$,NAME1$)

	REM-----CREATE NEW 101-------------------------------------------------

	IF END #7 THEN 80655
	GOSUB 80650
	CLOSE 7
	GOTO 90000


%include oeinpout
%include oepr1fil
%include oepr3fil
%include oecrefil
%include oecreprt
%include oefilsub
%include oegetpgm
