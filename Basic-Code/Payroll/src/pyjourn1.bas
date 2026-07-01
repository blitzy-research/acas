#include "ipycomm"
#include "ipyjrncm"
prgname$="PYJOURN1   JAN. 16, 1980 "
rem----------------------------------------------------------
rem
rem	P  Y  J  O  U  R  N  1
rem
rem	PRINT THE PAYROLL JOURNAL SUMMARIES
rem
rem	SECOND SECTION
rem
rem	P A Y R O L L	   S Y S T E M
rem
rem	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="PYJOURN1"
function.name$="PAYROLL JOURNAL PRINT"

#include "ipyconst"
#include "zfilconv"
#include "zdms"
#include "zdmsclr"

rem----------------------------------------------------------
rem
rem	C O N S T A N T S
rem
rem----------------------------------------------------------

dim emsg$(10)
emsg$(01)="PY771 ACT FILE NOT FOUND"
emsg$(02)="PY772 UNEXPECTED EOF ON PAY FILE"
emsg$(03)="PY773 BATCH TOTAL NOT ZERO"
emsg$(04)="PY774 "
emsg$(05)="PY775 "
emsg$(06)="PY776 "

#include "zdateio"
#include "zstring"
#include "ipydmemp"
#include "ipydmded"
#include "zbracket"
#include "zheading"
#include "fpyjrn"			rem define screen info

hdr2$="COMPANY PAYROLL SUMMARY"
hdr3$="LEDGER ACCOUNT SUMMARY"

def fn.round(rr)=(int((rr*100)+.5))/100

line.cnt%=1000			rem force a new page

rem----------------------------------------------------------
rem
rem	S E T	    U P
rem
rem----------------------------------------------------------

gosub 500			rem set up files

rem----------------------------------------------------------
rem
rem	M A I N       D R I V E R
rem
rem----------------------------------------------------------

if pr1.debugging% \
	then	trash%=fn.put%("fre: "+str$(fre),03)

gosub 12000				rem print amount summary
if stopit% \
	then	goto 999.2
if pr1.dist.used% \
	then	gosub 13000		rem print account summary
if stopit% \
	then	goto 999.2

rem----------------------------------------------------------
rem
rem	E N D	  O F	  J O B
rem
rem----------------------------------------------------------

lprinter:print:console		rem for centronics printer

gosub 600			rem update pay hdr

if batch.total<>0 \
	then	trash%=fn.emsg%(03)	:\
		goto 999.1

#include "zeoj"

rem----------------------------------------------------------
rem
rem	S U B R O U T I N E S
rem
rem----------------------------------------------------------

500	rem-----set up files---------------------------------
	gosub 720			rem get act file
	if not act.exists% \
		then	trash%=fn.emsg%(01)   :\
			goto 999.1
	gosub 730			rem read in act hdr

	gosub 610			rem get pay file
	if not pay.exists% \
		then	trash%=fn.emsg%(02)	:\
			goto 999.1
	gosub 620			rem get pay hdr
	return

600	rem-----update pay hdr-------------------------------
	pay.hdr.journal.printed%=true%
	gosub 630			rem write pay hdr
	close pay.file%
	return

610	rem-----get pay file---------------------------------
	pay.exists%=false%
	if end #pay.file% then 611
	open fn.file.name.out$(pay.name$,"101",pr1.pay.drive%,pw$,pms$) \
		recl pay.len%  as pay.file%
	pay.exists%=true%
611	rem-----here if pay file not present-----------------
	return

620	rem-----get pay hdr----------------------------------
	read #pay.file%,1;    \
#include "ipypayhd"
	return

630	rem-----update pay hdr-------------------------------
	print #pay.file%,1;	\
#include "ipypayhd"
	return

720	rem-----get act file---------------------------------
	if pr1.debugging% \
		then trash%=fn.put%("GETTING ACT FILE",03)
	act.exists%=false%
	if end #act.file% then 721
	open fn.file.name.out$(act.name$,"101",pr1.act.drive%,pw$,pms$) \
		recl act.len%  as act.file%
	act.exists%=true%
721	rem-----here if act file not present-----------------
	return

730	rem-----read in act hdr------------------------------
	read #act.file%,1;    \
#include "ipyacthd"
	return

6200	rem-----increment and test lines---------------------
	gosub 6205			rem test lines
	line.cnt%=line.cnt%+1
	return

6205	rem-----test lines-----------------------------------
	if line.cnt%>=pr1.lines.per.page%-2 \
		then	gosub 6210	rem do header
	return

6210	rem-----do header------------------------------------
	lprinter
	line.cnt%=fn.hdr%(fn.spread$(function.name$,1))+3
	console
	gosub 6300			rem check for interruption
	if stopit% then return
	if amount.summary% \
		then	gosub 6250	rem do amount summary header
	if account.summary% \
		then	gosub 6260	rem do account summary header
	return

6250	rem-----do amount  summary header--------------------
	trash%=fn.lit%(09)
	lprinter
	print "INTERVAL: ";
	print pay.hdr.interval$;
	print tab(fn.center%(hdr2$,pr1.page.width%));hdr2$;
	print tab(104);"FROM: ";
	print fn.date.out$(from.date$);
	print tab(120);"TO: ";
	print fn.date.out$(chk.hdr.to.date$)

	print tab(112);"CHECK DATE: ";
	print fn.date.out$(pr2.check.date$)
	line.cnt%=line.cnt%+1

	print
	console
	line.cnt%=line.cnt%+1
	return

6260	rem-----do account summary header--------------------
	trash%=fn.clr%(09)
	trash%=fn.lit%(10)
	lprinter
	print "INTERVAL: ";
	print pay.hdr.interval$;
	print tab(fn.center%(hdr3$,pr1.page.width%));hdr3$;
	print tab(104);"FROM: ";
	print fn.date.out$(from.date$);
	print tab(120);"TO: ";
	print fn.date.out$(chk.hdr.to.date$)

	print tab(112);"CHECK DATE: ";
	print fn.date.out$(pr2.check.date$)
	line.cnt%=line.cnt%+1

	print
	print tab(031);"ACCT";
	print tab(042);"GL";
	print tab(059);"A C C O U N T";
	print tab(092);"POSTED"

	print tab(032);"NO";
	print tab(041);"ACCT";
	print tab(062);"N A M E";
	print tab(092);"TOTAL"

	print
	console
	line.cnt%=line.cnt%+5
	return

6300	rem-----check for interruption-----------------------
	stopit%=false%
	if not constat% then return
	trash%=conchar%
	trash%=fn.lit%(11)
	trash%=fn.lit%(12)
	trash%=fn.get%(02,02)
	trash%=fn.clr%(11)
	trash%=fn.clr%(12)
	if in.status%=req.cr% \
		then	return
	if in.status%=req.stopit% \
		then	stopit%=true%
	if in.status%=req.back% \
		then	stopit%=true%
	return

9050	rem-----print a blank line---------------------------
	gosub 6200			rem increment and test lines
	lprinter
	print
	console
	return

11100	rem-----print units total----------------------------
	gosub 9050			rem a blank line
	units.total=0
	no.totals%=0
	for i%=1 to 4
		line.cnt%=line.cnt%+1
		gosub 6300		rem check for interruption
		if stopit% then return
		if total.units(i%)=0 \
			then	goto 11101	rem break
		no.totals%=no.totals%+1
		lprinter
		if no.totals%=1 \
			then	print tab(10);"TOTAL UNITS:";
		print using "/2345678901234/: ##,###.##";\
			tab(23),\
			pr1.rate.name$(i%),\
			total.units(i%)
		console
		grand.total.units=grand.total.units+total.units(i%)
11101
	next i%
	line.cnt%=line.cnt%+1
	gosub 6300			rem check for interruption
	if stopit% then return
	if no.totals%<=1 then return
	lprinter
	print using "    GRAND TOTAL UNITS: ##,###.##";\
		tab(23),\
		grand.total.units
	console
	return

11210	rem-----print hdr and amounts------------------------
	line.cnt%=line.cnt%+1
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print " ";                      rem extra leading blank
	print using " /2345678901/";\
		"   REG WAGES",\
		"  OTHER EARN",\
		"      TIPS  ",\
		"      FWT   ",\
		"      SWT   ",\
		"      LWT   ",\
		"      FICA  ",\
		"      SDI   ",\
		"  OTHER DEDS",\
		"      NET   "
	console

	line.cnt%=line.cnt%+1
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print " ";                      rem extra leading blank
	print using "  ###,###.## ";            \
			total.reg.wages;\
			total.other.earn;\
			total.tips;\
			total.fwt;\
			total.swt;\
			total.lwt;\
			total.fica;\
			total.sdi;\
			total.other.ded;
	print using " "+fn.bracket$(total.net,6,true%);abs(total.net);
	print				rem trailing crlf
	console
	return

12000	rem-----print amount summary-------------------------
	account.summary%=false%
	amount.summary%=true%
	line.cnt%=1000
	gosub 9050			rem print a blank line
	gosub 9050			rem print a blank line
	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print " ";                      rem extra leading blank
	tot$="     TOTAL  "
	print using " /2345678901/";\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$

	gosub 11210			rem print hdr and amounts
	if stopit% then return
	lprinter			rem console is set in 11210

	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	print				rem a blank line

	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	print " ";                      rem extra leading blank
	print using " /2345678901/";\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$,\
		tot$

	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	print " ";                      rem extra leading blank
	print using " /2345678901/";\
		"TIPS REPORTD",\
		"    CO FICA ",\
		"    CO FUTA ",\
		"     CO SUI ",\
		"  VAC TAKEN ",\
		"   SL TAKEN ",\
		"  COMP TAKEN",\
		" COMP EARNED",\
		"      EIC   "

	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	print " ";                      rem extra leading blank
	print using "  ###,###.## ";    \
			total.tips.reported;	\
			total.co.fica;		\
			total.co.futa;		\
			total.co.sui;		\
			total.vac.taken;	\
			total.sl.taken; 	\
			total.comp.taken;	\
			total.comp.earned;	\
			total.eic;
	print				rem trailing crlf
	console

	gosub 11100			rem print units total
	if stopit% then return
	return

13000	rem-----print account summary------------------------
	read #act.file%,1;		rem rewind act file
	gosub 730			rem read act hdr
	line.cnt%=1000
	account.summary%=true%
	amount.summary%=false%
	batch.total=0
	for act%=1 to pr2.no.acts%
		if acct.amt(act%)=0 \
			then	goto 13001	rem break
		gosub 13100			rem print account line
		if stopit% then return
		if dr.cr$="DR" \
			then	batch.total=batch.total+abs(acct.amt(act%)) \
			else	batch.total=batch.total-abs(acct.amt(act%))
13001
	next act%
	gosub 13200			rem print batch total line
	if stopit% then return
	return

13100	rem-----print account line---------------------------
	act.rec%=act%
	gosub 13110			rem read act record
	gosub 13120			rem determine DR or CR
	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print using "###";\
		tab(31),\
		act%;
	print using "/2345/";\
		tab(40),\
		act.no$;
	print using "/2345678901234567890123456789/";\
		tab(52),\
		act.desc$;
	print using "#,###,###.##";\
		tab(88),\
		abs(acct.amt(act%));
	print using "//";\
		tab(105),\
		dr.cr$
	console
	return

13110	rem-----read act rec---------------------------------
	read #act.file%,act.rec%+1;	\
#include "ipyact"
	return

13120	rem-----determine DR or CR---------------------------
	if left$(act.no$,1)="0" or  \
	   left$(act.no$,1)="4" or  \
	   left$(act.no$,1)="5"     \
		then	debits.normal%=true%   \
		else	debits.normal%=false%
	if debits.normal%		\
		then	dr.cr$="DR"  \
		else	dr.cr$="CR"
	if acct.amt(act.rec%)<0 \
		then	gosub 13125	rem swap dr/cr
	return

13125	rem-----swap dr/cr-----------------------------------
	if dr.cr$="DR" \
		then	dr.cr$="CR" \
		else	dr.cr$="DR"
	return

13200	rem-----print batch total line-----------------------
	gosub 9050			rem print a blank line
	if stopit% then return
	gosub 6200			rem increment and test lines
	if batch.total<0 \
		then	dr.cr$="CR" \
		else	dr.cr$="DR"
	if batch.total=0 \
		then	dr.cr$=null$
	lprinter
	print tab(70);	   \
		"BATCH TOTAL:";
	print using " #,###,###.##     //";             \
		tab(87),\
		abs(batch.total),\
		dr.cr$
	console
rem batch.total is tested in EOJ driver
	return
