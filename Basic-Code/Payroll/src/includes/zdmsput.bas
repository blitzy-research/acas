rem    DEC. 02, 1979   --------------------------------------------------
rem
   def fn.put%(value$,id%)	REM STANDARD
rem
rem----------------------------------------------------------------------
%nolist
	crt.data$(id%)= value$
	print using "&";fn.crt.sca$(crt.y%(id%), crt.x%(id%));
	crt.attrib%(id%)= crt.attrib%(id%) or crt.used%
	if crt.brt% and crt.attrib%(id%) \
		then print using "&";crt.foreground$;
	if (crt.strnum% and crt.attrib%(id%)) or (crt.io% and crt.attrib%(id%))=0 \
		then print using "&";left$(value$+blank$, crt.len%(id%)); \
			crt.background$: RETURN
	if crt.brktsgn% and crt.attrib%(id%) \
		then gosub 50005.1 \
		else gosub 50005.2
	print using "&";crt.background$
	return
50005.1 \	monetary data
	crt.num = val(value$)
	crt.l.d%=len(str$(abs(int(crt.num))))
	crt.temp%= len(crt.brkt.fmt$(crt.len%(id%)))+ \
		len(crt.brkt.rd.fmt$(crt.rd%(id%)))
	if crt.num < 0	\
	    then print using right$(blank$+crt.brkt.fmt$(crt.l.d%)+ \
		crt.brkt.rd.fmt$(crt.rd%(id%)), crt.temp%);abs(crt.num) \
	    else print using right$(blank$+crt.pad.fmt$(crt.l.d%)+ \
		crt.pad.rd.fmt$(crt.rd%(id%)), crt.temp%); crt.num
	return

50005.2
	print using crt.sgn.fmt$(crt.len%(id%))+crt.sgn.rd.fmt$(crt.rd%(id%));\
		val(value$)
	return
fend
%list
