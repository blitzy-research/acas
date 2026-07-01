rem	NOV.  1, 1979	   -------------------------------------
rem
rem	fn.set.used%(t.f%, id%) 	REM STANDARD
rem
rem-------------------------------------------------------------
%nolist
def fn.set.used%(t.f%, id%)
	crt.attrib%(id%)= crt.attrib%(id%) and not crt.used%
	crt.attrib%(id%)= crt.attrib%(id%) or  (crt.used% and t.f%)
	return
fend
%list
