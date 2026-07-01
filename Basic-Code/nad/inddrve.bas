10	rem-----ask file name--02/12/80-----------------------------
	print
	print tab(10);"Enter";name.of.file$;" File name";
	input "";line in$
	in$=ucase$(in$)
	if in$=stop$ then stopit%=true%:return
	if match("*",in$,1)<>0 or       \
	   match(".",in$,1)<>0 or       \
	   match(":",in$,1)<>0 or       \
	   match(" ",in$,1)<>0 or       \
	   match("\?",in$,1)<>0         \
		then	print tab(05);bell$;		\
			"NAD009 TRY AGAIN, FILE NAMES CAN'T "+ \
			"CONTAIN :*.? OR SPACES."       :\
			goto 10
	file.name$=left$(in$+blank32$,8)
	return
11	rem-----ask for drive---------------------
	print
	print tab(10);"Enter drive (@,A-F;RET=CURLOG) ";
	input "";line in$
	in$=ucase$(in$)
	if in$=stop$ then stopit%=true%:return
	if in$=return$ then in$="@"
	if in$="A" or in$="B" or in$="C" or     \
	   in$="D" or in$="E" or in$="F" or in$="@" \
		then	drive$=in$+":"   :\
			return
	print tab(05);bell$;"NAD010 TRY AGAIN, "+       \
			"Drives must be an A, B, C, D, E, F, OR @."
	goto 11
