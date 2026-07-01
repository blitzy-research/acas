rem	DEC. 02, 1979		    ---------------------------------------
rem
rem	fn.msg%(text$)		REM STANDARD
rem
rem----------------------------------------------------------------------------
%nolist
rem
   def fn.msg%(text$)
	crt.msg.issued%= true%
	print using "&"; crt.msg.header$                \
			+ left$ (text$+blank$, crt.columns%-15) \
			+ crt.msg.trailer$
	return
fend
%list
