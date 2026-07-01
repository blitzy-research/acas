REM	Nov.  6, 1979	   -----------------------------------------
REM
REM	COMMON AREA FOR DMS VARIABLES (INCLUDING CRT CHARACTERISTICS)
REM	STANDARD
REM-----------------------------------------------------------------
%nolist
common	crt.sca$, crt.sca.row$, crt.sca.column$
common	crt.clear$
common	crt.foreground$, crt.background$, crt.clear.foreground$
common	crt.home.cursor$
common	crt.up.cursor$, crt.down.cursor$, crt.right.cursor$, crt.left.cursor$
common	crt.backspace$
common	crt.alarm$
common	crt.eol$, crt.eos$
common	crt.insert.line$, crt.delete.line$
common	crt.order.row.col%, crt.order.col.row%, crt.sca.order%
common	crt.sca.hex%, crt.sca.decimal%, crt.sca.format%
common	crt.rows%,crt.columns%
common	crt.row.xlate%(1), crt.column.xlate%(1)
common	crt.file%
common	crt.msg.header$, crt.msg.trailer$
common	crt.mult.backspaces$(1), crt.back.count$
common	crt.ctl.xlate$
common	crt.key.prefix%, crt.key.xlate$
common	crt.strnum%, crt.brktsgn%, crt.used%, crt.brt%, crt.io%
common	crt.sgn.fmt$(1),  crt.sgn.rd.fmt$(1)
common	crt.brkt.fmt$(1), crt.brkt.rd.fmt$(1)
common	crt.pad.fmt$(1),  crt.pad.rd.fmt$(1)
common	req.valid%, req.stopit%, req.cr%, req.back%, req.cancel%
common	req.next%, req.save%, req.adding%, req.delete%
common	asc.lspace%, asc.refresh%, asc.cr%, asc.del%
common	ctl.stopit$, ctl.cr$, ctl.back$, ctl.cancel$, ctl.next$
common	ctl.save$, ctl.adding$, ctl.delete$
common	crt.ctl.tbl$
common	crt.ctl.mask$(1)
%list
REM  END OF DMS COMMON	----------------------------------------
REM
