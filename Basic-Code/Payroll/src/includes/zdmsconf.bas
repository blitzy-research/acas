REM	 DEC. 14, 1979 ------------------------
REM
def fn.confirmed%		REM STANDARD
REM
REM--------------------------------------------
%nolist
fn.confirmed%=false%
crt.col%= 30: crt.row%= 20
crt.continue$="(TYPE ""RUN"" TO CONTINUE)"
crt.stop$="(TYPE ""STOP"" TO STOP PROGRAM)"
console
print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);crt.stop$
print using "&";fn.crt.sca$(crt.row%, crt.col%);crt.continue$;
if pr1.leading.crlf% then print
crt.done%= false%
crt.count%= 0
crt.current$= null$
while not crt.done%
	crt.print%= false%
	crt.data%= conchar%
	crt.count%= crt.count%+ 1
	crt.char$= ucase$(chr$(crt.data%))
	crt.data%= asc(crt.char$)
	if crt.count%= 1 and crt.char$="S" \
		then crt.current$="STOP"+chr$(asc.cr%)
	if crt.count%= 1 and crt.char$="R" \
		then crt.current$="RUN"+chr$(asc.cr%)
	if crt.current$<> null$ \
		then crt.cur.char%= asc(mid$(crt.current$,crt.count%,1)) \
		else crt.cur.char%= -1
	if crt.data%= asc.del% or crt.data%= asc.lspace% \
		then crt.count%= crt.count%- 1
	if (crt.data%= asc.lspace% or crt.data%= asc.del%) and crt.count% > 0 \
		then  print using "&";fn.crt.sca$ \
		(crt.row%, crt.col%+len(crt.continue$)+crt.count%); \
		crt.backspace$; :crt.count%=crt.count%-1: crt.print%=true%
	if crt.data%<> crt.cur.char% and  \
		crt.data% <> asc.lspace% and crt.data%<> asc.del% \
	    then trash%= fn.msg%(bell$+system$+"019 TYPE ""RUN"" OR TYPE ""STOP"""):\
		print using "&";fn.crt.sca$(crt.row%, \
		crt.col%+len(crt.continue$)+crt.count%);crt.backspace$;: \
		crt.count%= crt.count%-1: crt.print%= true%
	if pr1.leading.crlf% and crt.print%  then print
	if crt.count%= len(crt.current$) and crt.count%> 0 then crt.done%=true%
wend
if crt.count%= len("RUN")+1  then fn.confirmed%=true%
print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);left$(blank$,len(crt.stop$))
print using "&";fn.crt.sca$(crt.row%, crt.col%);left$(blank$,len(crt.continue$)+5)
return
fend
%list
