rem	Nov.  8, 1979	   ------------------------------------------
rem
rem	  fn.lit%(id%)
rem
rem------------------------------------------------------------------
%nolist
def fn.lit%(id%)
	if crt.brt% and crt.attrib%(id%) \
		then print using "&";crt.foreground$;
	print using "&";fn.crt.sca$(crt.y%(id%), crt.x%(id%)); \
		crt.data$(id%); crt.background$
	crt.attrib%(id%)= crt.attrib%(id%) or crt.used%
	return
fend
%list
