rem	NOV.  1, 1979	   -------------------------------------
rem
rem	fn.test%(t.f%, id%)
rem
rem-------------------------------------------------------------
%nolist
def fn.test%(bit%, id%)
	if crt.attrib%(id%) and bit% \
		then fn.test%= true% \
		else fn.test%= false%
	return
fend
%list
