def fn.name.flip$(name$)	REM 19-NOV-79
	temp% = match("*",name$,1)
	if temp% = 0 \
	   then \
		fn.name.flip$ = name$ :\
		return \
	   else \
		fn.name.flip$ = right$(name$,len(name$)-temp%) + \
		   " " + left$(name$,temp%-1)
	return
fend
