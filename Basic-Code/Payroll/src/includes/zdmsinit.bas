rem	DEC. 02, 1979	  -----------------------------------------------------
rem
rem	fn.crt.cmdstr$
rem	fn.crt.initialize%(file$, disk$)
rem
rem----------------------------------------------------------------------------
%nolist
   def	fn.crt.cmdstr$
	if crt.temp$ = ""       \
	  then	fn.crt.cmdstr$ = "" :   \
		return
	crt.str$ = ""
	for crt.loop% = 1 to len (crt.temp$)
		crt.str$ = crt.str$	\
				+ chr$( asc(mid$(crt.temp$,crt.loop%,1)) \
					and 7fh)
		next
	fn.crt.cmdstr$ = crt.str$
	return
	fend

rem
rem----------------------------------------------------------------------------
rem
rem	fn.crt.initialize%	Initialize CRT display management interface
rem
rem----------------------------------------------------------------------------
rem
   def fn.crt.initialize% (crt.def.file$,crt.disk$)
	fn.crt.initialize% = 0
rem
rem---------------------------------------------------------------------------
rem
rem	CRT characteristics definition of a Hazeltine 1500 CRT terminal
rem
rem---------------------------------------------------------------------------
rem
	crt.leadin$ = chr$(126)
	crt.sca$ = crt.leadin$+chr$(17) 	rem set cursor address
	crt.sca.row$ = ""
	crt.sca.column$ = ""
	crt.sca.format% = crt.sca.hex%
	crt.sca.order% = crt.order.col.row%
	crt.clear$ = crt.leadin$ + chr$(28)	rem	clear screen
	crt.clear.foreground$ = crt.leadin$+chr$(29)	rem clear foreground
	crt.foreground$ = crt.leadin$+chr$(31)		rem begin foreground data
	crt.background$ = crt.leadin$+chr$(25)		rem begin background data
	crt.home$ = crt.leadin$+chr$(18)			rem home cursor
	crt.up.cursor$ = crt.leadin$+chr$(12)		rem up one row
	crt.down.cursor$ = crt.leadin$+chr$(11) 	rem down one row
	crt.right.cursor$ = chr$(16)			rem right one column
	crt.left.cursor$ = chr$(8)			rem left one column
	crt.backspace$ = chr$(8)+" "+chr$(8)            rem destructive backspace
	crt.alarm$ = chr$(7)				rem console alarm
	crt.eol$ = crt.leadin$+chr$(15)
	crt.eos$ = crt.leadin$+chr$(24)
	crt.delete.line$ = crt.leadin$+chr$(19)
	crt.insert.line$ = crt.leadin$+chr$(26)
rem
	crt.columns% = 80
	dim crt.column.xlate%(crt.columns%)
	for crt.loop% = 1 to 31
		crt.column.xlate%(crt.loop%) = 95 + crt.loop%
		next
	for crt.loop% = 32 to 80
		crt.column.xlate%(crt.loop%) = crt.loop% - 1
		next
rem
	crt.rows% = 24
	dim crt.row.xlate%(crt.rows%)
	for crt.loop% = 1 to crt.rows%
		crt.row.xlate% (crt.loop%) = 95 + crt.loop%
		next
	crt.msg.header$ = fn.crt.sca$(crt.rows%,10) + crt.background$
	crt.msg.trailer$ = fn.crt.sca$(crt.rows%-1,1)
	dim crt.mult.backspaces$(2)
	crt.mult.backspaces$(0)=""
	crt.mult.backspaces$(1)=crt.backspace$
	crt.mult.backspaces$(2)=crt.backspace$+crt.backspace$
		for crt.loop%=0 to 31
			crt.ctl.xlate$=crt.ctl.xlate$+chr$(crt.loop%)
			next
		for crt.loop%=0 to 31
			crt.back.count$=crt.back.count$+chr$(0)
			next
		for crt.loop%=32 to 127
			crt.back.count$=crt.back.count$+chr$(1)
			next
		crt.key.prefix%=-1
	if crt.def.file$ = ""   \
	  then	fn.crt.initialize% = 0 :	\
		return	\
	  else	crt.file$ = crt.def.file$ + ".def"
	if crt.disk$ <> ""      \
	  then	crt.file$ = crt.disk$ + ":" + crt.file$
	if end #crt.file%	\
	  then	50000.1
	open crt.file$ as crt.file%
	if end #crt.file%	\
	  then	50000.2
read #crt.file%;line crt.temp$
crt.sca$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.sca.row$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.sca.column$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.clear$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.foreground$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.background$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.clear.foreground$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.home.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.up.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.down.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.right.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.left.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.backspace$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.alarm$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.eol$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.eos$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.insert.line$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.delete.line$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.init.io.port.data$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.init.console.data$=fn.crt.cmdstr$
	read #crt.file%;crt.sca.order%
	read #crt.file%;crt.sca.format%
	read #crt.file%;			\
		crt.rows%,		\
		crt.columns%
	dim crt.row.xlate%(crt.rows%)
	dim crt.column.xlate%(crt.columns%)
	for crt.loop% = 1 to crt.rows%
		read #crt.file%;crt.row.xlate%(crt.loop%)
		next
	for crt.loop% = 1 to crt.columns%
		read #crt.file%;crt.column.xlate%(crt.loop%)
		next
	read #crt.file%;		\
		crt.init.storage.count%,	\
		crt.init.subroutine.addr,	\
		crt.init.io.port%
	if crt.init.storage.count% > 0	\
	  then	for crt.loop% = 1 to crt.init.storage.count% :	\
		   read #crt.file%;	\
				crt.init.storage.addr,	\
				crt.init.storage.value% :	\
		   poke crt.init.storage.addr,crt.init.storage.value%
		   next
	crt.len% = len(crt.init.io.port.data$)
	if crt.len% > 0 \
	  then	for crt.loop% = 1 to crt.len%	:	\
		   out crt.init.io.port%,		\
			asc(mid$(crt.init.io.port.data$,crt.loop%,1)) : \
		   next
	if crt.init.console.data$ <> "" \
	  then	console :	\
		print using "&";crt.init.console.data$
read #crt.file%;line crt.trash$
	if end #crt.file%  then  50000.0
read #crt.file%;line crt.temp$
	crt.ctl.xlate$=fn.crt.cmdstr$
	if end #crt.file%  then  50000.2
read #crt.file%;line crt.temp$
	crt.back.count$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
	crt.key.xlate$=fn.crt.cmdstr$
	read #crt.file%; crt.key.prefix%
50000.0 \
	close crt.file%
	crt.msg.header$ = fn.crt.sca$(crt.rows%,10) + crt.background$
	crt.msg.trailer$ = fn.crt.sca$(crt.rows%-1,1)
	crt.mult.backspaces$(0)=""
	crt.mult.backspaces$(1)=crt.backspace$
	crt.mult.backspaces$(2)=crt.backspace$+crt.backspace$
	return
50000.1 \
	fn.crt.initialize% = 1
	return
50000.2 \
	fn.crt.initialize% = 2
	close crt.file%
	return
	fend
%list
