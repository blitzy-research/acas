rem %NOLIST
	REM ******************************************************************\
	    *								                                 *\
	    *	   OEINPOUT.BAS      ORDER ENTRY SCREEN INPUT/OUTPUT MODULE  *\
	    *								                                 *\
	    ******************************************************************

12100	PRINT AF$; CHR$(128+R%); CHR$(128+C%); Z$
	RETURN

12200	Z$="" : F%=0
	FOR F1%=1 TO LENGTH%+1
12205		PRINT AF$; CHR$(128+R%); CHR$(128+C%+F1%-1)
		CHAR%=CONCHAR%
		IF CHAR%=27 THEN \
			F%=1 :\
			GOTO 12210
		IF CHAR%=2 THEN \
			F%=2 :\
			GOTO 12210
		IF CHAR%=13 THEN \
			F%=3 :\
			GOTO 12210
		IF LEN(Z$)=0 AND CHAR%=8 THEN 12205
		IF LEN(Z$)=1 AND CHAR%=8 THEN \
			Z$=" " :\
			GOSUB 12100 :\
			GOTO 12200
		IF CHAR%=8 THEN \
			F1%=F1%-1 :\
			PRINT AF$; CHR$(128+R%); CHR$(128+C%+F1%-1); " " :\
			Z$=LEFT$(Z$,LEN(Z$)-1) :\
			GOTO 12205
		Z$=Z$+CHR$(CHAR%)
	NEXT F1%

12210	IF F%=3 THEN \
		TEMP.Z$=Z$  :\
		R%=ROW%(23) :\
		C%=COL%(1)  :\
		Z$=EOL$     :\
		GOSUB 12100 :\
		Z$=TEMP.Z$  :\
		GOTO 12215
	IF F%=0 THEN \
		Z$=BELL$+"ENTRY TOO LONG"+EOL$ :\
		R%=ROW%(23) :\
		C%=COL%(1)  :\
		GOSUB 12100
12215	RETURN
rem %LIST
