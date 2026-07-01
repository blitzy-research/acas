REM----- DEC. 14, 1979 -----------------------------------
REM
def fn.abort%		REM STANDARD
REM
REM-------------------------------------------------------
%nolist
fn.abort%=false%
if constat% = 0  \
	then   return
trash%= conchar%
crt.col%= 30: crt.row%= 20
crt.stop$="(TYPE ""STOP"" TO STOP PROGRAM)"
crt.continue$="(PRESS RETURN TO CONTINUE)"
console
print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);crt.stop$
print using "&";fn.crt.sca$(crt.row%, crt.col%);crt.continue$;
if pr1.leading.crlf% then print
crt.count%= 0
while crt.count% < 5
	crt.print%= false%
	crt.data%= conchar%
	crt.count%= crt.count%+ 1
	if crt.data%= asc.cr% and crt.count%= 1 \
	    then print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);\
		 left$(blank$, len(crt.stop$)): \
		 print using "&";fn.crt.sca$(crt.row%, crt.col%); \
		 left$(blank$, len(crt.continue$)+5 ): \
		 lprinter: RETURN
	if ucase$(chr$(crt.data%))<> mid$("STOP"+chr$(asc.cr%),crt.count%,1)\
	    and crt.data%<> asc.lspace% and crt.data%<> asc.del% \
	    then trash%=fn.msg%(bell$+system$+ \
		"018 PRESS RETURN OR TYPE ""STOP"" "):\
		print using "&";fn.crt.sca$(crt.row%, \
		crt.col%+len(crt.continue$)+crt.count%);crt.backspace$;: \
		crt.count%= crt.count%-1: crt.print%= true%
	if crt.data%= asc.del% or crt.data%= asc.lspace% \
		then  crt.count%= crt.count%-1
	if (crt.data%= asc.lspace% or crt.data%= asc.del%) and crt.count% > 0 \
		then  print using "&";fn.crt.sca$ \
		(crt.row%, crt.col%+len(crt.continue$)+crt.count%); \
		crt.backspace$; :crt.count%=crt.count%-1: crt.print%=true%
	if pr1.leading.crlf% and crt.print%  then print
wend
print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);left$(blank$,len(crt.stop$))
print using "&";fn.crt.sca$(crt.row%,crt.col%);left$(blank$,len(crt.continue$)+5 )
fn.abort%=true%
return
fend
%list
