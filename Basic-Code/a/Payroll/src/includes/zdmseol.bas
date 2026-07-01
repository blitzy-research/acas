rem	Nov.  6, 1979	  -----------------------------------------------------
rem
rem	fn.crt.eol$		Erase to end of line
rem
rem----------------------------------------------------------------------------
%nolist
   def	fn.crt.eol% (row%, column%)
	if crt.eol$ <> ""       \
	  then	print fn.crt.sca$ (row%,column%) + crt.eol$ :	\
		return
	crt.temp% = crt.columns% - column% + 1
	if crt.temp% > 65	\
	  then	print fn.crt.sca$ (row%,column%)	\
				+ left$(blank$,65)	:	\
		print  fn.crt.sca$ (row%,column%+65)	\
				+ left$ (blank$,crt.temp%-65) \
	  else	print fn.crt.sca$ (row%,column%)	\
			+ left$ (blank$,crt.temp%)
	return
	fend
%list
