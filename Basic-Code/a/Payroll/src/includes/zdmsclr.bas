rem	Nov. 18, 1979	   ---------------------------------------------------
rem
rem	fn.clr%(id%)
rem
rem---------------------------------------------------------------------------
%nolist
   def fn.clr%(id%)
	console
	if crt.attrib%(id%) and crt.io% \
		then crt.data$(id%)= null$
	crt.attrib%(id%)= crt.attrib%(id%) and not crt.used%
	print using "&"; \
	    fn.crt.sca$(crt.y%(id%), crt.x%(id%));
	if (crt.strnum% and crt.attrib%(id%)) or (crt.io% and crt.attrib%(id%))=0 \
		then print using "&";left$(blank$, crt.len%(id%)): RETURN
	if crt.brktsgn% and crt.attrib%(id%) \
	    then crt.temp%= len(crt.brkt.fmt$(crt.len%(id%)))+ \
		len(crt.brkt.rd.fmt$(crt.rd%(id%))) \
	    else crt.temp%= len(crt.sgn.fmt$(crt.len%(id%)))+ \
		len(crt.sgn.rd.fmt$(crt.rd%(id%)))
	print using "&";left$(blank$, crt.temp%)
	return
	fend
rem--------------------------------------------------------------------------
%list
