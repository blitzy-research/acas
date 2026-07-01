	REM ******************************************************************\
	    *								                                 *\
	    *	   OE100.BAS	   ORDER ENTRY MENU PROGRAM		             *\
	    *								                                 *\
	    ******************************************************************
%INCLUDE oecommon

	CONSOLE

	DIM LINE$(16)

	DATA "01  INPUT NEW ORDER               [  ] "
	DATA "02  PROCEED WITH SUSPENDED ORDER  [  ]"
	DATA "03  CANCEL SUSPENDED ORDER        [  ] "
	DATA "04  NOT AVAILABLE                 [  ]"
	DATA "05  PRINT SUSPENDED ORDERS        [  ] "
	DATA "06  PRINT DISPATCH NOTES          [  ]"
	DATA "07  PRINT INVOICES                [  ] "
	DATA "08  PRINT VERIFICATION LIST       [  ]"
	DATA "09  DISPLAY MENU                  [  ] "
	DATA "10  UPDATE PARAMETER FILE         [  ]"
	DATA "11  USER PROGRAM 1                [  ] "
	DATA "12  USER PROGRAM 2                [  ]"
	DATA "13  USER PROGRAM 3                [  ] "
	DATA "14  USER PROGRAM 4                [  ]"
	DATA "15  END OF DAY                    [  ] "
	DATA "99  EXIT TO CP/M                  [  ]"

	FOR I%=1 TO 16 : READ LINE$(I%) : NEXT I%

	PRINT CLRS$
	R%=ROW%(1) : C%=COL%(32) : Z$="ORDER ENTRY SYSTEM" : GOSUB 12100
	R%=ROW%(3) : C%=COL%(39) : Z$="MENU"               : GOSUB 12100
	FOR I%=1 TO 15 STEP 2
		R%=ROW%(I%+4) : C%=COL%(2) : Z$=LINE$(I%)+LINE$(I%+1)
		GOSUB 12100
	NEXT I%

100	R%=ROW%(23) : C%=COL%(1)  : Z$="FUNCTION CODE [  ]" : GOSUB 12100
	R%=ROW%(23) : C%=COL%(16) : LENGTH%=2 : GOSUB 12200
	IF F%<>3 THEN 101
	FUNCTION$=Z$ : FUNCTION%=VAL(FUNCTION$)
	IF FUNCTION%=99 THEN 999
	IF FUNCTION%<1 OR FUNCTION%>15 THEN 101
	ON FUNCTION% GOTO 110,120,130,140,150,160,170,180,190,200,210,220,230,\
		240,250

101	R%=ROW%(23) : C%=COL%(40) : Z$=BELL$+"INVALID FUNCTION - REENTER"+EOL$
	GOSUB 12100 : GOTO 100

110	PGM$="oe020"
	GOTO 300
120	PGM$="oe030"
	GOTO 300
130	PGM$="oe040"
	GOTO 300
140	PGM$="oe050"
	GOTO 300
150	PGM$="oe060"
	GOTO 300
160	PGM$="oe070"
	GOTO 300
170	PGM$="oe080"
	GOTO 300
180	PGM$="oe090a"
	GOTO 300
190	PGM$="oe100"
	GOTO 300
200	PGM$="oe110"
	GOTO 300
210	PGM$="oeuser1"
	GOTO 300
220	PGM$="oeuser2"
	GOTO 300
230	PGM$="oeuser3"
	GOTO 300
240	PGM$="oeuser4"
	GOTO 300
250	PGM$="oe120"
	GOTO 300

300	Z$=PGM$+".INT" : Z%=SIZE(Z$)
	IF Z%=0 THEN \
		R%=ROW%(23) : C%=COL%(40) :\
		Z$=BELL$+"THIS FUNCTION IS NOT AVAILABLE"+EOL$ : GOSUB 12100 :\
		GOTO 100
	ON FUNCTION% GOSUB 400,410,420,430,440,450,460,470,480,490,500,510,\
		520,530,540
	CHAIN PGM$

400	R%=ROW%(5)  : C%=COL%(37) : Z$="01" : GOTO 600
410	R%=ROW%(5)  : C%=COL%(76) : Z$="02" : GOTO 600
420	R%=ROW%(7)  : C%=COL%(37) : Z$="03" : GOTO 600
430	R%=ROW%(7)  : C%=COL%(76) : Z$="04" : GOTO 600
440	R%=ROW%(9)  : C%=COL%(37) : Z$="05" : GOTO 600
450	R%=ROW%(9)  : C%=COL%(76) : Z$="06" : GOTO 600
460	R%=ROW%(11) : C%=COL%(37) : Z$="07" : GOTO 600
470	R%=ROW%(11) : C%=COL%(76) : Z$="08" : GOTO 600
480	R%=ROW%(13) : C%=COL%(37) : Z$="09" : GOTO 600
490	R%=ROW%(13) : C%=COL%(76) : Z$="10" : GOTO 600
500	R%=ROW%(15) : C%=COL%(37) : Z$="11" : GOTO 600
510	R%=ROW%(15) : C%=COL%(76) : Z$="12" : GOTO 600
520	R%=ROW%(17) : C%=COL%(37) : Z$="13" : GOTO 600
530	R%=ROW%(17) : C%=COL%(76) : Z$="14" : GOTO 600
540	R%=ROW%(19) : C%=COL%(37) : Z$="15" : GOTO 600

600	GOSUB 12100
	RETURN

999	R%=ROW%(19) : C%=COL%(76) : Z$="99" : GOSUB 12100
	GOTO 13000

%INCLUDE oeinpout

13000	END
