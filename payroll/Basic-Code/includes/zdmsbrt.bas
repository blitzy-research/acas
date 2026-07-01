rem	NOV.  1, 1979	   -------------------------------------
rem
rem	fn.set.brt%(t.f%, id%)		REM STANDARD
rem
rem-------------------------------------------------------------
%nolist
def fn.set.brt%(t.f%, id%)
	crt.attrib%(id%)= crt.attrib%(id%) and not crt.brt%
	crt.attrib%(id%)= crt.attrib%(id%) or  (crt.brt% and t.f%)
	return
fend
%list
