rem	 Jan. 17, 1979
rem requires zstring,zdatei/o
def fn.hdr%(report$)
	print tof$
	page%=page%+1
	if page.width%=0 then page.width%=132
	if todays.date$=null$ then todays.date$=common.date$
	print tab(fn.center%(pr1.co.name$,page.width%));  \
		pr1.co.name$; \
		tab(page.width%-14); \
		"PAGE ";page%
	print tab(fn.center%(system.name$,page.width%));  \
		system.name$; \
		tab(page.width%-14); \
		"DATE ";fn.date.out$(todays.date$)
	print tab(fn.center%(report$,page.width%));report$
	fn.hdr%=3
	return
fend

