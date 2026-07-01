rem----- NOV.  1,1979 --------------------------------------------------------
rem
rem	fn.crt.sca$		REM STANDARD
rem
rem-------------------------------------------------------------------------
%nolist
   def fn.crt.sca.row$(row%)
	if crt.sca.format% = crt.sca.hex%	\
	  then	fn.crt.sca.row$ \
			= crt.sca.row$	\
				+ chr$(crt.row.xlate%(row%)) \
	  else	fn.crt.sca.row$ \
			= crt.sca.row$	\
				+ str$(crt.row.xlate%(row%))
	return
	fend
   def fn.crt.sca.column$(column%)
	if crt.sca.format% = crt.sca.hex%	\
	  then	fn.crt.sca.column$ \
			= crt.sca.column$	\
			+ chr$(crt.column.xlate%(column%)) \
	  else	fn.crt.sca.column$ \
			= crt.sca.column$	\
				+ str$(crt.column.xlate%(column%))
	return
	fend
   def fn.crt.sca$(row%,column%)
	if crt.sca.order% = crt.order.row.col%	\
	  then	fn.crt.sca$ = crt.sca$		\
				+ fn.crt.sca.row$(row%) \
				+ fn.crt.sca.column$(column%)	\
	  else	fn.crt.sca$ = crt.sca$		\
				+ fn.crt.sca.column$(column%)	\
				+ fn.crt.sca.row$(row%)
	return
	fend
%list
rem--------------------------------------------------------------
