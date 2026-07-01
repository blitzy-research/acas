	REM *****************************************************************\
	    *								                                *\
	    *	   OEDATES.BAS	   ORDER ENTRY DATE-TO-DAYS MODULE	        *\
	    *								                                *\
	    *****************************************************************

	M=D2 : D=D1 : Y=D3
	GOSUB 350

	REM ***  A CONTAINS THE NUMBER OF DAYS SINCE 0,0,0   ***

	A =A-29221
	A%=INT(A)
	GOTO 500

350	DATA 0,31,59,90,120,151,181,212,243,273,304,334
	FOR H=1 TO M : READ A : NEXT H
	A=A+Y*365+INT(Y/4)+D+1-INT(Y/100)+INT(Y/400)
	IF INT(Y/4)<>Y/4 THEN 450
	IF Y/400=INT(Y/400) THEN 430
	IF Y/100=INT(Y/100) THEN 450

430	IF M>2 THEN 450
	A=A-1

450	RETURN
