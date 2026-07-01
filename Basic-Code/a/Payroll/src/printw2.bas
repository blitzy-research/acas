#include "ipycomm"
prgname$="PRINTW2 10 JANUARY, 1979 "
rem---------------------------------------------------------
rem
rem	  P A Y R O L L
rem
rem	  P  R	I  N  T  W  2
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------

program$="PRINTW2"
function.name$ = "FORM W2 PRINT"

#include "ipyconst"
#include "zdms"
#include "zdmsused"
#include "zdmsbrt"
#include "zdmsclr"
#include "znumeric"
#include "zckdigit"
#include "zdmsconf"
#include "zdmsabrt"
#include "zdspyorn"
#include "zstring"
def fn.leap.year%(year%)
	if (year%/4.0)-int(year%/4.0)=0 \
		then   fn.leap.year% = true% \
		else   fn.leap.year% = false%
	return
fend
#include "zdateio"
#include "zdateinc"
#include "zflip"
#include "ipydmemp"
#include "ipydmhis"
#include "zfilconv"
#include "fpyw2"

dim emsg$(20)
emsg$(01)="PY621 SYSTEM HAS NOT ACHIEVED YEAR-END STATE"
emsg$(02)="PY622 EMPLOYEE FILE NOT FOUND"
emsg$(03)="PY623 UNEXPECTED EOF ON EMPLOYEE FILE"
emsg$(04)="PY624 HISTORY FILE NOT FOUND"
emsg$(05)="PY625 UNEXPECTED EOF ON HISTORY FILE"
emsg$(06)="PY626 PR2 FILE NOT FOUND"
emsg$(07)="PY627 UNABLE TO WRITE TO PR2 FILE"
emsg$(08)="PY628 INVALID RESPONSE"
emsg$(09)="PY629 Y OR NO ONLY"
emsg$(10)="PY630 NUMERIC INTEGER ONLY"
emsg$(11)="PY631 INVALID CHECK DIGIT"
emsg$(12)="PY632 EMPLOYEE NUMBER TOO HIGH"
emsg$(13)="PY633 STARTING EMPLOYEE NUMBER CANNOT BE GREATER THAN ENDING NUMBER"
emsg$(14)="PY634 OUT OF RANGE"
emsg$(15)="PY635 THERE ARE NO TERMINATED EMPLOYEES IN THE FILE"
emsg$(16)="PY636"
emsg$(17)="PY637"
emsg$(18)="PY638"
emsg$(19)="PY639"
emsg$(20)="PY640"

REM--------CONSTANTS--------
a$ = "&"
disp% = 5	rem displacement for tabbing
col1% = disp% + 4
col2% = disp% + 21
col3% = disp% + 34
col4% = disp% + 49
col5% = disp% + 64
option% = 1
lines.to.next.form% = 4
forms.per.emp% = 1
print.local% = true%
dol$ = " ###,###.##"
line.9$ = a$+a$+a$+dol$
line.11$ = a$+dol$+dol$+dol$+dol$
line.13$ = a$+a$+dol$
line.15$ = dol$+dol$+a$
line.17$ = line.15$
pw$ = null$	rem may be used in future
pm$ = null$	rem  '   '  '   '    '
fld.all.emp%	= 1	:lit.all.emp%	  = 21
fld.range.emp%	= 2	:lit.range.emp%   = 23
fld.term.emp%	= 3	:lit.term.emp%	  = 25
fld.single.emp% = 4	:lit.single.emp%  = 27
fld.select%	= 5
fld.start.emp%	= 11	:lit.start.emp%   = 37
fld.end.emp%	= 12	:lit.end.emp%	  = 38
fld.emp.num%	= 13	:lit.emp.num%	  = 39
fld.print.local% = 6
fld.no.forms%	= 7
fld.no.lines%	= 8
fld.no.columns% = 9
fld.test.form%	= 10
fld.emp.no%	= 14	:lit.emp.no%	  = 40

REM-------setting up-------
print using a$; crt.clear$	rem clear screen
gosub 50	rem throw up screen
first% = true%
gosub 5 	rem set up file accessing
gosub 10	rem ok to run--stop if not ok
gosub 20	rem open EMP & read hdr--stop if not there
gosub 30	rem open HIS & read hdr---'   '   '    '
gosub 40	rem open PR2----- stop if not there

REM-------------------------------------------------------
REM----------MAIN DRIVER----------------------------------
WHILE true%
	gosub 190	rem clear optional fields
	gosub 100	rem do requests
	if start.emp.no% < 1  then start.emp.no% = 1
	if end.emp.no% > pr2.no.employees%  then \
		end.emp.no% = pr2.no.employees%
	gosub 180	rem set up emp no field
	if stopit% then \
		goto 901	rem  end
	lprinter
	emp.rec% = start.emp.no%

	while emp.rec% <= end.emp.no%	and not emp.eof%
		gosub 25	rem read emp.file
		if emp.eof%  then \
			goto 900	rem shouldn't happen unless term only
		gosub 35	rem read his file
		gosub 200	rem calculate & accumulate
		gosub 400	rem display emp no
		gosub 300	rem print form
		emp.rec% = emp.rec% + 1
	wend
900	console
WEND

901	if all.emp%  then \
		gosub 45	rem write new pr2


	gosub 500	rem close files
	if first%  then goto 999.2	rem prem.end
#include "zeoj"

REM-----------------------------------------------
REM----------subroutines--------------------------
5	rem-----set up file accessing-----
       emp.file.name$=fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pm$)
       his.file.name$=fn.file.name.out$(his.name$,"101",pr1.his.drive%,pw$,pm$)
	pr2.file.name$=fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pm$)
	return

10	rem-----ok to run?-----
	yearend% = true%
	trash% = fn.decompose.date%(pr2.check.date$)
	yr$ = right$(blank$+str$(yr%),2)
	if pr2.last.q.ended% = 4  then	\
		end.of.qtr$ = yr$+"1231" \
	   else \
		end.of.qtr$ = common.date$
	return
REM====REST OF YR END CHECKS NOT EXECUTED===============
	if pr1.m.used%	or  pr1.s.used%  then \
		gosub 16	rem check qtr end for mo & semimo
	if not yearend%  then goto 5.9
	if pr1.b.used%	then \
		incr% = 14  :\
		gosub 17	rem check qtr end for biwk
	if not yearend%  then goto 5.9
	if pr1.w.used%	then \
		incr% = 7   :\
		gosub 17	rem check qtr end for wk
5.9	if not yearend%  then \
		trash% = fn.emsg%(1) :\
		gosub 18	rem get confirmation to run
	return

16	rem-----check yr end for mo & semimo----=====NOT USED=====
	if pr2.last.sm.apply.no% <> 24	then \
		yearend% = false%
	return

17	rem-----check yr end for biwk & wk--=========NOT USED=======
	if fn.incr.date$(pr2.check.date$,incr%) <= end.of.qtr$ \
		then yearend% = false%
	return

18	rem-----still want to run?---=======NOT USED=======
	if not fn.confirmed%  then \
		goto 999.2	rem prem. end
	trash% = fn.put.all%(true%)
	return


REM---------------------------------------------------
REM----------file handling routines-----------------
20	rem----open emp.file & read-------
	if end #emp.file%  then 29.9
	open emp.file.name$  recl emp.len%  as emp.file%
	if end #emp.file%  then 29.99
	read #emp.file%,1;\
#include "ipyemphd"

	return

25	rem-----read employee record-----
	read #emp.file%,emp.rec%+1;\	rem account for hdr
#include "ipyemp"

	if emp.eof%  then return
	if emp.status$ = "D"  or \
	  (emp.status$ = "L" and term.only%)  or \
	  (emp.status$ = "A" and term.only%)  then \
		emp.rec% = emp.rec% + 1 :\
		goto 25
	emp.emp.name$ = fn.name.flip$(emp.emp.name$)
	return

29.9	rem-----emp file not found-----
	emsg% = 2
	gosub 99	rem display msg & delay
	goto 999.1	rem die, die, die
29.99	rem--------------- eof on emp-----
	emp.eof% = true%
	console
	if term.only% and no.forms% = 0  then \
		emsg% = 15  :\
		gosub 99    :\	rem display & delay
		return
	if term.only%  then return
	emsg% = 3
	gosub 99	rem display msg & stall
	close emp.file%, his.file%, pr2.file%
	goto 999.1	rem crash

30	rem-----open his file & read hdr-----
	if end #his.file%  then 39.9
	open his.file.name$  recl his.len%  as his.file%
	if end #his.file%  then 39.99
	read #his.file%,1;\
#include "ipyhishd"

	return

35	rem-----read his record-----
	read #his.file%,emp.rec%+1;\	rem account for hdr
#include "ipyhis"

	his.ytd.fica.gross = his.ytd.fica.taxable
	his.ytd.gross = his.ytd.income.taxable + his.ytd.other.taxable + \
			his.ytd.other.nontaxable + his.ytd.tips
	return

39.9	rem-----no his file------
	emsg% = 4
	gosub 99	rem display msg
	close emp.file%
	goto 999.1	rem crash
39.99	rem-----unexpected eof on his-------
	if term.only% and no.forms% = 0 \
		then return
	console
	emsg% = 5
	gosub 99	rem display msg
	close emp.file%, his.file%, pr2.file%
	goto 999.1	rem pfffffft

40	rem-----open pr2-----
	if end #pr2.file%  then 49.9
	open pr2.file.name$  as pr2.file%
	if end #pr2.file%  then 49.99
	return

45	rem-----write new pr2----
	if not yearend%  then return
	pr2.w2.printed% = true%
	print #pr2.file%;\
#include "ipypr2"
	return

49.9	rem-----no pr2 file-----
	emsg% = 6
	gosub 99	rem display emsg
	close emp.file%, his.file%
	goto 999.1	rem thud
49.99	rem-----unable to write pr2-----
	pr2.w2.printed% = false%
	emsg% = 7
	gosub 99	rem display msg
	close emp.file%, his.file%, pr2.file%
	goto 999.1	rem abend
REM------------end of file accessing-----------------
50	rem-----put up screen & get defaults-----
	start.lit% = 15
	end.lit% = 36
	for i% = start.lit% to end.lit%
		trash% = fn.lit%(i%)
	next i%
	trash% = fn.put%(fn.dsp.yorn$(print.local%),fld.print.local%)
	trash% = fn.put%(str$(forms.per.emp%),fld.no.forms%)
	trash% = fn.put%(str$(lines.to.next.form%),fld.no.lines%)
	trash% = fn.put%(str$(disp%),fld.no.columns%)
	trash% = fn.put%(fn.dsp.yorn$(true%),fld.test.form%)
	return

99	rem-----display emsg & stall-----
	trash% = fn.emsg%(emsg%)
	for i% = 1 to 300
	next i%
	return

REM-------------request subroutines-----------------
100	rem-----request print options-------
	field% = fld.select%
	while field% < fld.start.emp%
101		gosub 100.9	rem get input
		if stopit%  then return
		if cr% or back%  then \
			gosub 102	:\ rem change fld no
			goto 101	rem try again
		if not valid%  then \
			goto 101	\ rem do again
		else \
			on field% gosub \
				100.99,100.99,100.99,100.99, \	rem error
				105,	\  rem print option
				130,	\  rem print state & local info
				120,	\  rem number of forms
				160,	\  rem number of lines betw. forms
				170,	\  rem starting print column
				140,	\  rem test form
				100.99,100.99,100.99,100.99	rem error
		if valid%  then field% = field% + 1
		if stopit%  then return
	wend
	return

100.9	rem-----get data-----
	gosub 100.91	rem clear flags
	trash% = fn.get%(2,field%)
	if in.status% = req.valid%  then valid% = true%:return
	if in.status% = req.stopit%  then stopit% = true%:return
	if in.status% = req.cr%  then cr% = true%:return
	if in.status% = req.back%  then back% = true%
	return

100.91	rem-----clear flags------
	valid% = false%
	stopit% = false%
	cr% = false%
	back% = false%
	return

100.99	rem-----invalid field number-----
	field% = fld.select%
	valid% = false%
	return

102	rem----change field number-----
	if cr%	then field% = field% + 1
	if back%  then field% = field% - 1
	if field% > fld.test.form%  then \
		field% = fld.select%
	if field% < fld.select%  then \
		field% = fld.test.form%
	return

105	rem-----get selection--------
	gosub 106	rem check option
	trash% = fn.put%(str$(option%),fld.select%)
	if not valid%  then return
	on option% gosub	111, \	rem all emps
				112, \	rem range of emps
				113, \	rem all terminated
				114	rem one emp
	field% = fld.select%
	first% = false%
	if start.emp.no% <> 1  or \
	   end.emp.no% <> pr2.no.employees%  then \
		partial% = true%
	return

105.5	rem-----get lit #-----
	if option% = fld.all.emp%  then \
		lit% = lit.all.emp%
	if option% = fld.range.emp%  then \
		lit% = lit.range.emp%
	if option% = fld.term.emp%  then \
		lit% = lit.term.emp%
	if option% = fld.single.emp%  then \
		lit% = lit.single.emp%
	return

106	rem-----check option------
	if not first%  then \
		gosub 106.5	rem clear brt field & clear emp no flds
	valid% = true%
	digits% = 1
	gosub 126	rem verify numeric int
	if not num%  then \
		valid% = false% :\
		return
	if in.num% > 0	and in.num% <= 4  then \
		option% = in.num%  :\
		gosub 107	:\ rem set brtness & display arrow
		return
	emsg% = 14
	gosub 99	rem display emsg & delay
	valid% = false%
	return

106.5	rem-----clear brt fields & clear emp no flds------
	if option% = 0	then return
	gosub 105.5	rem get lit no
	trash% = fn.set.brt%(false%,lit%)
	trash% = fn.put%(null$,option%)
	trash% = fn.lit%(lit%)
	if option% = 1 or option% = 3  then return
	gosub 190	rem clear optional fields
	return

107	rem-----set brt & display arrow------
	gosub 105.5	rem gt lit #
	trash% = fn.set.brt%(true%,lit%)
	trash% = fn.lit%(lit%)
	trash% = fn.put%(">",option%)
	return

111	rem------all employees------
	all.emp% = true%
	term.only% = false%
	start.emp.no% = 1
	end.emp.no% = pr2.no.employees%
	return

112	rem-----range of emps------
	all.emp% = false%
	term.only% = false%
	trash% = fn.set.used%(true%,fld.start.emp%)
	trash% = fn.set.used%(true%,fld.end.emp%)
	trash% = fn.set.used%(true%,lit.start.emp%)
	trash% = fn.set.used%(true%,lit.end.emp%)
	trash% = fn.lit%(lit.start.emp%)
	trash% = fn.lit%(lit.end.emp%)
	trash% = fn.put%("00014",fld.start.emp%)
	emp$ = right$("000"+str$(pr2.no.employees%),4)
	ck.dig$ = fn.ck.dig$(emp$)
	trash% = fn.put%(emp$+ck.dig$,fld.end.emp%)

112.1	rem---starting emp no-----
	field%	= fld.start.emp%
	gosub 100.9	rem get data
	if stopit% or back%  then \
		stopit% = false% :\
		valid% = false%  :\
		return
	if cr%	then gosub 112.7	:\  rem plug in default
		goto 112.2	rem get ending number
	gosub 112.9	rem validate emp no
	if emp.invalid%  then goto 112.1	rem try again
	start.emp.no% = emp.rec%

112.2	rem----- ending emp no---------
	field% = fld.end.emp%
	gosub 100.9	rem get data
	if stopit%  then valid% = false%:return
	if cr%	then gosub 112.7	:\  rem plug in default
		return
	if back%  then goto 112.1	rem get starting no
	gosub 112.9	rem validate emp no
	if emp.invalid%  then goto 112.2	rem try again
	end.emp.no% = emp.rec%
	if start.emp.no% > end.emp.no%	then \
		emsg% = 13	:\
		gosub 99	:\  rem display
		goto 112.1	rem try again

112.7	rem------plug in def or max-----
	if field% = fld.start.emp%  then \
		emp.rec% = 1 \
	   else \
		emp.rec% = pr2.no.employees%
	return

112.9	rem-----validate emp no------
	emp.invalid% = false%
	digits% = 5
	gosub 126	rem validate num int
	if not num%  then \
		emp.invalid% = true%:return
	emp$ = left$(in$,4)
	if right$(in$,1) <> fn.ck.dig$(emp$)  then \
		emp.invalid% = true%  :\
		emsg% = 11  :\
		gosub 99    :\	rem display
		return
	emp.rec% = val(emp$)
	if emp.rec% > pr2.no.employees%  then \
		emp.invalid% = true%  :\
		emsg% = 12	:\
		gosub 99	rem display
	return

113	rem-----all terminated emps-----
	all.emp% = false%
	start.emp.no% = 1
	end.emp.no% = pr2.no.employees%
	term.only% = true%
	return

114	rem-----one employee------
	all.emp% = false%
	term.only% = false%
	trash% = fn.set.used%(true%,fld.emp.num%)
	trash% = fn.set.used%(true%,lit.emp.num%)
	trash% = fn.lit%(lit.emp.num%)
114.1	gosub 114.9	rem get emp.no
	if stopit%  then stopit% = false%:valid% = false%:return
	gosub 112.9	rem validate number
	if emp.invalid%  then goto 114.1	rem try again
	start.emp.no% = emp.rec%
	end.emp.no% = emp.rec%
	valid% = true%
	return

114.9	rem----get emp no, mask 1-----
	stopit% = false%
	valid% = false%
	trash% = fn.get%(1,fld.emp.num%)
	if in.status% = req.valid%  then valid% = true%:return
	if in.status% = req.stopit%  then stopit% = true%
	return

120	rem-----request # of copies-------
	digits% = 2
	gosub 126	rem check num integer
	if not num%  then valid% = false%
	if in.num% < 1 or in.num% > 10	then \
		valid% = false%  :\
		emsg% = 14	:\
		gosub 99	rem display msg
	if valid%  then forms.per.emp% = in.num%
	trash% = fn.put%(str$(forms.per.emp%),fld.no.forms%)
	return

126	rem-----check numeric integer------
	num% = fn.num%(in$)
	if len(in$)>digits% or not num%  then \
		num%=false%: \
		in.num% = 0 :\
		emsg% = 10  :\
		gosub 99	rem dislpay
	in.num% = val(in$)
	return

130	rem-----request print state & local amts------
	gosub 139	rem check response
	if t%  then print.local% = true%
	if f%  then print.local% = false%
	trash% = fn.put%(fn.dsp.yorn$(print.local%),fld.print.local%)
	return

139	rem-----check y/n-------
	t%=false%:f%=false%
	if in.uc$ = "Y"  or in.uc$ = "T" \
		then	t%=true%:return
	if in.uc$ = "N"  or in.uc$ = "F" \
		then	f%=true%:return
	valid% = false%
	emsg% = 9
	gosub 99	rem display emsg
	return

140	rem-----request test form-----
	test.form% = true%
	gosub 139	rem check response
	if t%  then test.form% = true%
	if f%  then test.form% = false%
	trash% = fn.put%(fn.dsp.yorn$(test.form%),fld.test.form%)
	if test.form%  then \
		valid% = false% :\
		gosub 145  :\	rem get test data
		lprinter  :\
		gosub 300 :\	rem print form
		console
	return

145	rem-----phony values for test form------
	emp.emp.name$	= "NOAH COUNT, ESQ."
	emp.addr1$	= "123456 789th AVE."
	emp.addr2$	= "APARTMENT 98765"
	emp.city$	= "CHICAGO"
	emp.state$	= "IL"
	emp.zip$	= "12345"
	subtotal$	= null$
	his.ytd.eic	= 111111.11
	emp.ssn$	= "000-00-0000"
	his.ytd.fwt	= 222222.22
	his.ytd.gross	= 333333.33
	his.ytd.fica	= 444444.44
	his.ytd.fica.gross = 555555.55
	emp.pension$	= "Y"
	his.ytd.tips	= 666666.66
	his.ytd.swt	= 777777.77
	his.ytd.gross	= 888888.88
	his.ytd.lwt	= 999999.99
	return


160	rem------how many lines betw forms------
	digits% = 2
	gosub 126	rem check num int
	if not num%  then valid% = false%
	if in.num% < 1	or in.num% > 99  then \
		valid% = false% :\
		emsg% = 14	:\
		gosub 99	rem display emsg & delay
	if valid%  then lines.to.next.form% = in.num%
	trash% = fn.put%(str$(lines.to.next.form%),fld.no.lines%)
	return

170	rem-----get displacement from left edge-------
	digits% = 2
	gosub 126	rem check num int
	if not num%  then valid% = false%
	if in.num% < 1	or in.num% > 50  then \
		valid% = false%  :\
		emsg% = 14	 :\
		gosub 99	rem display & delay
	if valid%  then \
		disp% = in.num% :\
		col1% = disp% + 4  :\
		col2% = disp% + 21 :\
		col3% = disp% + 34 :\
		col4% = disp% + 49 :\
		col5% = disp% + 64
	trash% = fn.put%(str$(disp%),fld.no.columns%)
	return

180	rem------set up emp no field--------
	trash% = fn.set.used%(true%,fld.emp.no%)
	trash% = fn.set.used%(true%,lit.emp.no%)
	trash% = fn.lit%(lit.emp.no%)
	return

190	rem-----clear optional fields-------
	trash% = fn.clr%(fld.start.emp%)
	trash% = fn.clr%(lit.start.emp%)
	trash% = fn.clr%(lit.end.emp%)
	trash% = fn.clr%(fld.end.emp%)
	trash% = fn.clr%(lit.emp.num%)
	trash% = fn.clr%(fld.emp.num%)
	trash% = fn.clr%(lit.emp.no%)
	trash% = fn.clr%(fld.emp.no%)
	return

199	rem-----premature burial-----
	gosub 500	rem close files
	trash% = fn.msg%("STOP REQUESTED")
	goto 999.2	rem prem end
	return

rem----------end of requests-------------------------

REM-------------processing routines------------------
200	rem-----calculations & accumulations-----
	sub.eic 	= sub.eic + his.ytd.eic
	sub.fwt 	= sub.fwt + his.ytd.fwt
	sub.fica	= sub.fica + his.ytd.fica
	sub.fica.gross	= sub.fica.gross + his.ytd.fica.gross
	sub.tips	= sub.tips + his.ytd.tips
	sub.swt 	= sub.swt + his.ytd.swt
	sub.lwt 	= sub.lwt + his.ytd.lwt
	sub.gross	= sub.gross + his.ytd.gross
	return

300	rem-----print form-----
	printed.per.emp% = 0
	while printed.per.emp% < forms.per.emp%
		gosub 305	rem check abort
		gosub 310	rem print co name & addr
		print using line.9$;tab(col1%);pr1.co.city$;tab(disp%+24);\
			pr1.co.state$;tab(disp%+27);pr1.co.zip$;tab(col3%); \
			his.ytd.eic
		print
		print using line.11$;tab(col1%);emp.ssn$;tab(col2%); \
			his.ytd.fwt;tab(col3%);his.ytd.gross;tab(col4%);\
			his.ytd.fica;tab(col5%);his.ytd.fica.gross
		print
		print using line.13$;tab(col1%);emp.emp.name$;tab(col3%); \
			emp.pension$;tab(col5%);his.ytd.tips
		print
		print using a$;tab(col1%);emp.addr1$;
		if print.local%  then \
			print using line.15$;tab(col3%);his.ytd.swt; \
				tab(col4%);his.ytd.gross;tab(col5%); \
				pr1.co.state$ \
		   else  print	rem suppress rest of line
		print using a$;tab(col1%);emp.addr2$
		print using a$;tab(col1%);emp.city$;
		if print.local%  then \
			print using line.17$;tab(col3%);his.ytd.lwt; \
				tab(col4%);his.ytd.gross;tab(col5%); \
				pr1.co.city$  \
		   else  print
		print using a$+a$;tab(col1%);emp.state$;tab(disp%+10);emp.zip$
		gosub 360	rem space to next form
		printed.per.emp% = printed.per.emp% + 1
		if test.form%  then return
	wend
	no.forms% = no.forms% + 1
	if no.forms% >= 41  then \
		gosub 350	rem do subtotal form
	return

305	rem-----abort print?-----_
	if fn.abort%  then \
		gosub 199	rem premature end
	if crt.data% = asc.cr% and crt.count% = 1 \
		then  trash% = fn.put.all%(true%) :\ rem only re-display
		      lprinter	rem  screen if abort msg appeared
	return

310	rem-----do emp addr lines------
	gosub 305	rem check abort
	print:print
	print using a$;tab(disp%+26);pr1.state.id$
	print
	print using a$+a$;tab(col1%);left$(pr1.co.name$+blank$,30); \
		tab(disp%+36);subtotal$
	print using a$;tab(col1%);pr1.co.addr1$
	print using a$+a$;tab(col1%);pr1.co.addr2$;tab(col3%);pr1.fed.id$
	print using a$;tab(col1%);pr1.co.addr3$
	return

350	rem-----do subtotal form-----
	gosub 305	rem check abort
	subtotal$ = "X"
	gosub 310	rem do co name & addr
	print using line.9$;tab(col1%);pr1.co.state$;tab(disp%+10); \
		pr1.co.zip$;tab(col3%);sub.eic
	print
	print using line.11$;null$;tab(col2%);sub.fwt;tab(col3%);sub.gross; \
		tab(col4%);sub.fica;tab(col5%);sub.fica.gross
	print
	print using line.13$;null$;null$;tab(col5%);sub.tips
	print
	if print.local%  then \
		print using line.15$;tab(col3%);sub.swt;tab(col4%);sub.gross;\
			tab(col5%);pr1.co.state$  \
	   else  print
	print
	if print.local%  then \
		print using line.17$;tab(col3%);sub.lwt;tab(col4%);sub.gross;\
			tab(col5%);pr1.co.city$  \
	   else  print
	print
	gosub 360	rem space to next form
	no.forms% = 0
	gosub 370	rem zero accum's
	subtotal$ = null$
	return

360	rem-----space to next form-----
	for i% = 1 to lines.to.next.form%
		print
	next i%
	return

370	rem-----zero accum's-----
	sub.eic 	= 0
	sub.fwt 	= 0
	sub.fica	= 0
	sub.fica.gross	= 0
	sub.tips	= 0
	sub.swt 	= 0
	sub.lwt 	= 0
	sub.gross	= 0
	return

400	rem-----print emp.no on screen-----
	console
	trash% = fn.put%(emp.no$,fld.emp.no%)
	lprinter
	return

rem-----------end of processing routines-----------------

500	rem-----close files-----
	close emp.file%
	close his.file%
	close pr2.file%
	return
