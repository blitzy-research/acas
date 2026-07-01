rem----- DEC. 28, 1979 --------------------------------------------------------
rem
rem	fn.get%(mask%, id%)		REM STANDARD
rem
rem----------------------------------------------------------------------------
%nolist
   def fn.get%(mask%, id%)
	console
	if crt.rd%(id%)> 0 \
		then crt.limit%=crt.len%(id%)+crt.rd%(id%)+1 \
		else crt.limit%=crt.len%(id%)
	print using "&";        \
		fn.crt.sca$(crt.y%(id%),crt.x%(id%));crt.foreground$;
	if pr1.leading.crlf% then print
	in$=null$
	in.uc$=null$
	in.status%= 0
	in.len%= 0
	crt.done%=false%
	crt.valid.control%=0
	while not crt.done%
		crt.print%= false%
		crt.data% = conchar%
		crt.temp.back% = asc(mid$(crt.back.count$, crt.data%+1, 1))
		if crt.data% < 32  then \
			crt.data% = asc(mid$(crt.ctl.xlate$, crt.data%+1, 1))
		if crt.key%  then \
			crt.data% = asc(mid$(crt.key.xlate$, crt.data%+1, 1))
		if crt.data% = crt.key.prefix%	and not crt.key% \
			then  crt.key% = true% \
			else  crt.key% = false%
		if crt.temp.back% <> 0 and (crt.key% or crt.data% < 32) \
			then crt.print%= true%: \
				print using "&";fn.crt.sca$(crt.y%(id%), \
				crt.x%(id%)+crt.loop%+crt.temp.back%); \
				crt.mult.backspaces$(crt.temp.back%);
		if crt.data% = asc.del% \
			then crt.data% = asc.lspace%
		if crt.data%= asc.lspace% and in.len%> 0 \
			then crt.print%= true%: \
			  print using "&"; fn.crt.sca$(crt.y%(id%), \
			  crt.x%(id%)+in.len%);crt.backspace$; :\
			  in.len%= in.len% - 1: in$= left$(in$,in.len%)
		if crt.data%= asc.refresh% \
			then crt.print%= true%: trash%=fn.put.all%(true%): \
			  print using "&"; \
			  fn.crt.sca$(crt.y%(id%),crt.x%(id%)); \
			  crt.foreground$; : in.len%=0: in$=null$
		if crt.data%< 32 and crt.data%<> asc.lspace% and \
			crt.data%<> asc.refresh% and in.len%= 0 \
		  then crt.valid.control%= match(chr$(crt.data%), \
			crt.ctl.mask$(mask%), 1)
		if (crt.data%=asc.cr% and in.len%<>0) or crt.valid.control%<>0\
			then crt.done%=true%
		if not crt.done% and crt.data%< 32 and crt.data%<>asc.lspace% \
		  and crt.data%<> asc.refresh% and crt.valid.control%= 0\
			then crt.print%= true%: trash%= fn.msg% \
			(bell$+system$+"016 CONTROL CHARACTER NOT ACCEPTED"): \
			print using "&"; \
			fn.crt.sca$(crt.y%(id%), crt.x%(id%)+in.len%); \
			crt.foreground$;
		if crt.data% <> asc.cr% and crt.data% <> asc.lspace% and \
		  in.len% >= crt.limit% \
			then crt.print%= true%: trash%= fn.msg% \
			(bell$+system$+"017  LENGTH LIMIT EXCEEDED"): \
			print using "&"; \
			fn.crt.sca$(crt.y%(id%),crt.x%(id%)+in.len%+1); \
			crt.backspace$;crt.foreground$;
		if crt.data% = asc.quote% \
			then crt.print%= true%: trash%= fn.msg% \
			(bell$+system$+"018  QUOTES ARE INVALID CHARACTERS"): \
			print using "&"; \
			fn.crt.sca$(crt.y%(id%),crt.x%(id%)+in.len%+1); \
			crt.backspace$;crt.foreground$;
		if crt.data%>= 32 and crt.data%<> asc.quote% and \
		  not crt.key% and in.len%< crt.limit% \
			then in$= in$+ chr$(crt.data%): in.len%= in.len%+ 1
		if pr1.leading.crlf% and crt.print% then print
	wend
	in.status%= match(chr$(crt.data%), crt.ctl.tbl$, 1)+ 1
	if in.len% > 0 \
	  then	in.uc$= ucase$(in$): in.status%= req.valid%
	if crt.msg.issued% then trash%= fn.msg%(""): crt.msg.issued%= false%\
			   else print using"&";crt.background$;
	return
	fend
rem--------------------------------------------------------------
%list
