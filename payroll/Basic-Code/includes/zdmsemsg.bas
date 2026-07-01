rem	 NOV.  1,1979	       -----------------------------------------------
rem
rem	fn.emsg%(emsg%) 	REM STANDARD
rem
rem----------------------------------------------------------------------------
%nolist
   def fn.emsg%(emsg%)
	trash%= fn.msg%(bell$+emsg$(emsg%))
	common.msg$=emsg$(emsg%)
	return
fend
%list
