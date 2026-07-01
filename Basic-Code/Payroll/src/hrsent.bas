#include "ipycomm"
prgname$="HRSENT    18 JANUARY, 1979 "
rem----------------------------------------------------------
rem
rem	H  R  S  E  N  T
rem
rem	REGULAR HOURS ENTRY PROGRAM
rem
rem	P A Y R O L L	   S Y S T E M
rem
rem	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="HRSENT"
function.name$ = "PAY TRANSACTION ENTRY"

#include "ipyconst"
#include "zserial"

#include "zdms"

#include "znumeric"
#include "zdateio"
#include "zparse"
#include "zeditdte"
#include "zstring"
#include "ipyedesc"
#include "ipyokcat"
#include "zckdigit"
#include "zfilconv"
#include "zdspyorn"
#include "zdmsclr"
#include "zflip"
#include "fpyhrsen"

dim emsg$(18)	rem can go to 25
emsg$(01) = "PY051 EMPLOYEE FILE NOT FOUND ON DRIVE "+str$(pr1.emp.drive%)
emsg$(02) = "PY052 EMPLOYEE FILE IS NULL"
emsg$(03) = "PY053 Y OR N ONLY"
emsg$(04) = "PY054 INVALID RESPONSE"
emsg$(05) = "PY055 HOURS FILE OF TYPE 000 FOUND"
emsg$(06) = "PY056 MUST BE NUMERIC INTEGER"
emsg$(07) = "PY057 NOT NUMERIC"
emsg$(08) = "PY058 EXCEEDS NUMBER OF RECORDS ON HOURS FILE: "
emsg$(09) = "PY059 INVALID CONTROL CHARACTER"
emsg$(10) = "PY060 INVALID CHECK DIGIT"
emsg$(11) = "PY061 INVALID EMPLOYEE NUMBER"
emsg$(12) = "PY062 TRANS. CODE CANNOT BE LESS THAN ZERO OR GREATER THAN "+STR$(PR1.MAX.ED.CATS%)
emsg$(13) = "PY063 INVALID DATE"
emsg$(14) = "PY064 PR2 FILE NOT FOUND ON SYSTEM DRIVE"
emsg$(15) = "PY065 INVALID TRANSACTION CODE"
emsg$(16) = "PY066 THERE ARE NO HOURS FILE RECORDS"
emsg$(17) = "PY067 TERMINATED, DELETED, OR INVALID EMPLOYEE"
emsg$(18) = "PY068 TYPE 101 HOURS FILE RENAMED TO TYPE 102"


rem----------------------------------------------------------
rem
rem	C O N S T A N T S
rem
rem----------------------------------------------------------

a$ = "&"
cat.0$ = "REG AND OT PAY"
names% = true%
null$ = ""
pw$ = null$	rem for future use
pm$ = null$
hrs.eff.date$ = common.date$

rem----------------------------------------------------------
rem
rem	S E T	    U P
rem
rem----------------------------------------------------------

gosub 30	rem throw up on screen
gosub 5 	rem set up file accessing
gosub 20	rem get.hrs.file
if not ok%  then goto 999.1	rem  prem. end
gosub 10	rem employee names desired?
if stopit%  then goto 999.2	rem stop requested
if not ok%  then goto 999.1
if write.pr2%  then \
	gosub 6 	rem try to open pr2--set ok% to false if ng
if not ok% then goto 999.1	rem abort
if stopit% then goto 999.2	rem premature.end
gosub 50	rem get rid of unwanted screen fields
if pr1.debugging%  then \
	trash% = fn.msg%("1  fre = "+str$(fre))

rem----------------------------------------------------------
rem
rem	M A I N      D R I V E R
rem
rem----------------------------------------------------------

gosub 100	rem process.input
gosub 600	rem rewrite hrs hdr, close & rename hrs
gosub 650	rem rewrite.pr2.file.if.needed

rem----------------------------------------------------------
rem
rem	E N D	  O F	  J O B
rem
rem----------------------------------------------------------

trash% = fn.msg%("STOP REQUESTED")

#include "zeoj"

rem----------------------------------------------------------
rem
rem	S U B R O U T I N E S
rem
rem----------------------------------------------------------
rem------set-up subroutines----------
5	rem------set up file accessing-------
      emp.file.name$=fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pm$)
      pr2.file.name$=fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pm$)
	return

6	rem------see if pr2 is present-----
	if end #pr2.file%  then 6.99
	open pr2.file.name$ as pr2.file%
	pr2.exists% = true%
	return

6.99	rem------no pr2 file------
	pr2.exists% = false%
	ok% = false%
	emsg% = 14
	gosub 99	rem display msg & display
	return

10	rem------get emp file if wanted------
	gosub 15	rem want names?
	if stopit%  then return 	rem premature burial
	if not names%  then  return	rem  don't open EMP
	gosub 11	rem open EMP
	if not emp.exists%  then \
		trash% = fn.emsg%(01) :\
		ok% = false%	:\
		return
	gosub 12	rem read emp hdr
	gosub 13	rem dimension tables for emp reads
	emp.emp.name$ = null$
	return

11	rem-----open employee file-----
	if end #emp.file% then 11.9
	open emp.file.name$ recl emp.len%  as emp.file%
	emp.exists% = true%
	return

11.9	rem-----can't open emp file------
	emp.exists% = false%
	emp.eof% = true%
	return

12	rem------read emp hdr-------
	if end #emp.file%  then 12.9	rem null emp file
	read #emp.file%,1; \
#include "ipyemphd"
	if end #emp.file% then 12.99	rem normal eof
	return

12.9	rem-----emp end of file on hdr read-----
	emp.eof% = true%
	trash% = fn.emsg%(02)
	stopit% = true%
	return

12.99	rem-----normal emp eof-----
	emp.eof% = true%
	return

13	rem------dimension tables for emp reads------
#include "ipydmemp"

	return

15	rem------want names?---------
	gosub 16	rem t/f
	if stopit%  then return 	rem prem end
	if t%  then names% = true%
	if f%  then names% = false%
	trash% = fn.put%(fn.dsp.yorn$(names%),fld.name.disp%)
	return

16	rem-----enter t/f/cr/back/stopit-----------------------
	t%=false%:f%=false%:cr%=false%:stopit%=false%
	while true%
		trash% = fn.get%(2,fld.name.disp%)
		if in.status% = req.stopit%  then stopit% = true%:return
		if in.status% = req.cr%  then cr% = true%
		if in.uc$="Y" or in.uc$="T" or cr% \
			then t% = true%:return
		if in.uc$ = "N"  or in.uc$ = "F" \
			then	f%=true%:return
		emsg% = 4
		gosub 99	rem display msg & delay
	wend


20	rem------get.hrs.file--------
	trash% = fn.msg%("PLEASE WAIT...GETTING FILES")
	hrs.in$=fn.file.name.out$(hrs.name$,"000",pr1.hrs.drive%,pw$,pm$)
	hrs.out$=fn.file.name.out$(hrs.name$,"001",pr1.hrs.drive%,pw$,pm$)
	gosub 21	rem get.status.of.101
	gosub 22	rem get.status.of.001
	gosub 23	rem get.status.of.000
	gosub 23.5	rem get status of 102
	if hrs.000.exists% \
		then	emsg% = 5     :\
			gosub 99      :\  rem display msg & delay
			ok%=false%    :\
			return
	if hrs.001.exists% \
		then trash% = rename(hrs.in$,hrs.out$)
	if not hrs.001.exists% \
		then	gosub 24     rem create.000
	if hrs.101.exists% \
		then	gosub 25	rem rename 101--delete 102 if there
	gosub 26	rem open hrs file for 345th time
	gosub 27	rem  read.hdr.rec
	gosub 28	rem reset.proof.flags & write hdr
	trash% = fn.put%(str$(hrs.hdr.batch.no%),fld.batch.no%)
	ok%=true%
	trash% = fn.msg%(null$)
	return

21	rem-----get status of 101-----
	type$ = "101"
	gosub 29	rem open hrs
	if hrs.exists%	then \
		hrs.101.exists% = true% :\
		close hrs.file%
	return

22	rem-----get status of 001------
	type$ = "001"
	gosub 29	rem open
	if hrs.exists%	then \
		hrs.001.exists% = true% :\
		close hrs.file%
	return

23	rem-----get status of 000-----
	type$ = "000"
	gosub 29	rem open
	if hrs.exists%	then \
		hrs.000.exists% = true% :\
		close hrs.file%
	return
23.5	rem------get status of 102---------
	type$ = "102"
	gosub 29	rem open it
	if hrs.exists%	then \
		hrs.102.exists% = true% :\
		close hrs.file%
	return

24	rem-----create 000 file------
	if end # hrs.file%  then 29.99	rem normal eof
	create hrs.in$	recl hrs.len%  as hrs.file%
	hrs.000.exists% = true%
	hrs.hdr.batch.no% = pr2.hrs.batch.no% + 1
	hrs.hdr.no.recs% = 0
	close hrs.file%
	write.pr2%  = true%
	return

25	rem -----delete 102 hrs file, rename 101 to 102-----
	if hrs.102.exists%  then \
		type$ = "102" :\
		gosub 29      :\	rem open hrs as type 102
		delete hrs.file%	rem delete 102
      trash%=rename(fn.file.name.out$(hrs.name$,"102",pr1.hrs.drive%,pw$,pm$),\
	     fn.file.name.out$(hrs.name$,"101",pr1.hrs.drive%,pw$,pm$))
	emsg% = 18
	gosub 99	rem display & delay
	return

26	rem-----open the hrs file for the last time------
	type$ = "000"
	gosub 29	rem open
	return

27	rem------read hdr rec-------
	read #hrs.file%,1; \
#include "ipyhrshd"

	return

28	rem------reset header flags & write hdr-------
	hrs.hdr.proof.no% = 0
	hrs.hdr.proofed% = false%
	print #hrs.file%,1; \
#include "ipyhrshd"

	return

29	rem-----try to open hrs-----
       hrs.file.name$=fn.file.name.out$(hrs.name$,type$,pr1.hrs.drive%,pw$,pm$)
	hrs.exists% = false%
	if end # hrs.file% then 29.9	rem no file
	open hrs.file.name$  recl hrs.len%  as hrs.file%
	if end #hrs.file%  then 29.99	rem normal eof
	hrs.exists% = true%
	return

29.9	rem-----open failed on hrs-----
	hrs.exists% = false%
	return

29.99	rem-----normal eof on hrs-------
	hrs.eof% = true%
	return

30	rem-----set up &  display screen-------
	fld.batch.no%  = 1
	fld.rec.no%    = 2
	fld.emp.no%    = 3
	fld.emp.name%  = 4
	fld.units%     = 7
	fld.rate%      = 5
	fld.desc%      = 6
	fld.date%      = 8
	fld.name.disp% = 9
	trash% = fn.put.all%(false%)	rem literals only
	trash% = fn.put%(fn.dsp.yorn$(names%),fld.name.disp%)
	return

40	rem----- fn.num --------------------------
	num% = fn.num%(in$)
	if len(in$)>digits% or not num%  then \
		num%=false%: \
		trash% = fn.emsg%(06) :RETURN
	in.num=val(in$)
	return

42	rem----- fn.numeric ----------------------
	numeric% = fn.numeric%(in$,left.digits%,right.digits%)
	if not numeric%  then trash% = fn.emsg%(07) :\
		return
	in.numeric=val(in$)
	return

50	rem-----set up dms screen fields-----
	trash% = fn.clr%(23)
	trash% = fn.clr%(fld.name.disp%)
	if not names%  then \
		trash% = fn.clr%(fld.emp.name%)
	return

99	rem-----display emsg & delay------
	trash% = fn.emsg%(emsg%)
	for i% = 1 to 250
	next i%
	return

rem------main driver subroutines--------
100	rem-----process.input------
	first.time%=true%
	write.needed%=true%
	if repeating% then goto 110
	gosub 300	rem get.record.number
	if stopit% then return
	if good.rec% and cr% then goto 120
	if not good.rec% and cr% \
		then  goto 100	rem goto process.input
	if back% then gosub 310 :\   rem get.prev.rec:
		goto 100      rem  process.input
	if next% then gosub 320 :\  rem   get.next.rec:
		goto 100      rem process.input
	if delete% and good.rec% then  gosub 330  :\	rem  delete.rec:
		good.rec% = false%	:\
		goto 100    rem process.input
	if save%   then goto 100
	if adding% then repeating%=true%

110	rem-----here if we are already repeating----------------
	if repeating% \
		then	gosub 400  :\	rem get next available
			gosub 410  :\	rem get defaults
			good.rec%=true%   :\
			gosub 450  :\	rem display record
			goto 120
	if not ok% \
		then	good.rec%=false%  :\
			goto 100	rem goto process.input
	gosub 325	rem read & display hrs
	goto 100	rem process.input

120	rem-----here if changing or adding----------------------
	gosub 200	rem get.data
	if hrs.emp.no$ = null$	then write.needed% = false%
	gosub 290	rem reset.flags
	if write.needed% \
		then	gosub 550  \	rem write.rec
		else	good.rec%=false%
	goto 100	rem process.input


rem------incoming data facilities---------
200	rem------get.data-------
	in$=hrs.emp.no$
	gosub 250	rem get.emp.no
	if stopit% and first.time%  \
		then	repeating%=false% :\
			write.needed% = false%
	first.time%=false%
	if stopit% then return
	if invalid.emp%  then \
		emsg% = 17	:\
		gosub 99		rem display & delay
	if cancel% or invalid.emp%  then write.needed%=false%:return
	if back%  then goto 230
	if cr%	then goto 210
	if not ok% \
		then	trash% = fn.put%(hrs.emp.no$,fld.emp.no%) :\
			invalid.emp% = false%	:\
			goto 200	rem get.data
	hrs.emp.no$=in$
	trash% = fn.put%(hrs.emp.no$,fld.emp.no%)
	if names%  then \
		gosub 560  :\	read emp file
		trash% = fn.put%(emp.emp.name$,fld.emp.name%)
	if invalid.emp%  then  \
		write.needed% = false% :\
		goto 200	rem if term. or deleted go no furthr


210	rem-----get rate--------------------------------------
	in$=str$(hrs.rate%)
	gosub 270	rem get.rate
	if stopit% then return
	if back% then goto 200
	if cr%	then goto 220
	if cancel% then write.needed%=false%:return
	if not ok% \
		then	trash% = fn.put%(str$(hrs.rate%),fld.rate%):\
			goto 210
	hrs.rate% = cat%
	trash% = fn.put%(str$(hrs.rate%),fld.rate%)
	trash% = fn.put%(desc$,fld.desc%)

220	rem-----get units-------------------------------------
	in$=str$(hrs.units)
	gosub 260	rem get.rate
	if stopit% then return
	if back% then goto 210
	if cr%	then goto 230
	if cancel% then write.needed%=false%:return
	if not ok% \
		then   trash% = fn.put%(str$(hrs.units),fld.units%):\
			goto 220	rem display old value & try again
	hrs.units = in.numeric
	trash% = fn.put%(str$(hrs.units),fld.units%)

230	rem-----get effective date----------------------------
	in$=fn.date.out$(hrs.eff.date$)
	gosub 280	rem fet.eff.date
	if stopit% then return
	if back% then goto 220
	if cr%	then goto 200
	if cancel% then write.needed%=false%:return
	if not ok% \
		then	trash%=fn.put%(fn.date.out$(hrs.eff.date$),fld.date%):\
			goto 230
	trash% = fn.put%(in$,fld.date%)
	hrs.eff.date$=fn.date.in$
	goto 200	rem get.data

250	rem-----get employee number-----
	field% = fld.emp.no%
	gosub 350	rem get data
	if valid%  then \
		gosub 255	rem check emp #
	return

255	rem-----edit employee number-----
	ok% = true%
	digits% = 5
	gosub 40	rem check num int.
	if not num%  then  ok%=false%:return
	if len(in$) <> 5  then \
		ok% = false% :\
		emsg% = 10   :\
		gosub 99     :\ rem display & delay
		return
	emp$ = left$(in$,4)
	if right$(in$,1) <> fn.ck.dig$(emp$)  then \
		ok% = false% :\
		emsg% = 10   :\
		gosub 99     :\ rem display & delay
		return
	emp.rec% = val(emp$)
	if emp.rec% > pr2.no.employees%  or   \
	   emp.rec% < 1      then \
		ok% = false% :\
		emsg% = 11   :\
		gosub 99     :\ rem display & delAy
		return
	write.needed% = true%
	invalid.emp% = false%
	return

260	rem-----get units------
	field% = fld.units%
	gosub 350	rem get data
	if valid% then \
		gosub 265	rem check units
	return

265	rem-----edit units-------
	ok% = true%
	left.digits% = 5
	right.digits% = 2
	gosub 42	rem check numeric
	if not numeric%  then ok% = false%
	return

270	rem-----get rate-------
	field% = fld.rate%
	gosub 350	rem get data
	if valid%  then \
		gosub 275	rem check rate
	return

275	rem-----edit rate-----
	ok% = true%
	digits% = 2
	gosub 40	rem check num int.
	if not num%  then ok% = false%:return
	cat% = val(in$)
	if cat% = 0  then \
		desc$ = cat.0$ :\
		return		rem jump around range check
	if cat% > 0  and cat% < 5  then \
		desc$ = pr1.rate.name$(cat%)  :\
		return
	if cat% > pr1.max.ed.cats%  or \
	   cat% < 0  then \
		ok% = false%  :\
		trash% = fn.emsg%(12) :\
		return
	if not cat.ok.to.enter%(cat%)  then \
		ok% = false%  :\
		trash% = fn.emsg%(15)
	desc$ = ed.desc.table$(cat%)
	return

280	rem-----get eff. date-----
	field% = fld.date%
	gosub 350	rem get data
	if valid%  then \
		gosub 285	rem check date
	return

285	rem-----edit eff. date------
	ok% = true%
	if not fn.edit.date%(in$)  then \
		ok% = false% :\
		trash% = fn.emsg%(13)
	return

290	rem-----reset flags-------
	valid%	 = false%
	stopit%  = false%
	cr%	 = false%
	back%	 = false%
	next%	 = false%
	cancel%  = false%
	save%	 = false%
	delete%  = false%
	return

rem-----record number facilities-------------
300	rem-----get record number-------
	field% = fld.rec.no%
	gosub 340	rem get data
	if valid%  then \
		adding% = false%  :\	rem turn off add if rec no used
		gosub 305 \	rem validate rec no
	   else \
		gosub 360	rem stopit or save msg
	return

305	rem-----edit record number------
	ok% = true%
	digits% = 4
	in$ = str$(val(in$))
	gosub 40	rem num int?
	if not num%  then good.rec% = false%:return
	if val(in$) > hrs.hdr.no.recs%	then \
		trash% = fn.msg%(bell$+emsg$(08)+ \
		   str$(hrs.hdr.no.recs%)+" IS MAX") :\
		ok% = false% :\
		trash% = fn.put%(null$,fld.rec.no%)  :\
		return
	hrs.rec% = val(in$)
	return

310	rem-----get previous record-----
	if hrs.hdr.no.recs% < 1  then \
		gosub 321  :\	rem no records
		return
	hrs.rec% = hrs.rec% - 1
	if hrs.rec% < 1  then \
		hrs.rec% = hrs.hdr.no.recs%
	gosub 325	rem read hrs file & display
	return

320	rem-----get next record-------
	if hrs.hdr.no.recs% < 1  then \
		gosub 321 :\	rem no records
		return
	hrs.rec% = hrs.rec% + 1
	if hrs.rec% > hrs.hdr.no.recs%	then \
		hrs.rec% = 1
	gosub 325	rem read hrs file & display
	return

321	rem-----no hrs recs-----
	emsg% = 16
	gosub 99	rem display msg & delay
	ok% = false%
	good.rec% = false%
	return

325	rem-----read & display hrs rec-----
	good.rec% = true%
	gosub 500	rem read hrs.file
	if hrs.deleted%  then \
		emp.emp.name$ = "DELETED RECORD" :\
		desc$ = "DELETED"  :\
		good.rec% = false%
	gosub 450	rem dispplay rec
	return

330	rem-----delete an hrs record------
	hrs.deleted% = true%
	adding% = false%
	gosub 550	rem write rec
	hrs.deleted% = false%
	trash% = fn.msg%("RECORD NUMBER "+str$(hrs.rec%)+" DELETED")
	return

340	rem-----get rec.no data-------
	gosub 290	rem reset flags
	trash% = fn.get%(5,field%)	rem accept any ctl-char but cancel
	gosub 341	rem check valid,stopit,cr,back
	if in.status% = req.next%  then next% = true%:return
	if in.status% = req.save%  then save% = true%:return
	if in.status% = req.adding%  then adding% = true%:return
	if in.status% = req.delete%  then delete% = true%:return
	return

341	rem-----check valid,stopit,back,cr-------
	if in.status% = req.valid%  then valid% = true%:return
	if in.status% = req.stopit%  then stopit% = true%:return
	if in.status% = req.cr%  then cr% = true%:return
	if in.status% = req.back%  then back% = true%
	return

350	rem-----get other data-----
	gosub 290	rem reset flags
	trash% = fn.get%(3,field%)	rem accepts valid,stopit,cr,back,cancel
	gosub 341	rem check valid,stopit,cr,back
	if in.status% = req.cancel%  then cancel% = true%
	return

360	rem-----check ctl chars (rec no)-----
	if stopit%  then \
		trash% = fn.msg%("STOP REQUESTED") :\
		return
	if save%  then \
		gosub 420  :\	rem save files
		return
	return

rem-----hrs file handling-------
400	rem-----get spot for new rec-----
	hrs.rec% = hrs.hdr.no.recs% + 1
	return

410	rem-----get default values------
	hrs.units   = 0.0
	hrs.rate%   = 0
	desc$	    = cat.0$
	return

420	rem-----save hrs file=====
	gosub 555	rem write hrs hdr
	close hrs.file%
	gosub 26	rem re-open hrs file
	trash% = fn.msg%(str$(hrs.hdr.no.recs%)+" RECORDS SAVED")
	return

450	rem-----display data------
	trash% = fn.put%(str$(hrs.rec%),fld.rec.no%)
	trash% = fn.put%(hrs.emp.no$,fld.emp.no%)
	if names%  then \
		trash% = fn.put%(emp.emp.name$,fld.emp.name%)
	trash% = fn.put%(str$(hrs.rate%),fld.rate%)
	trash% = fn.put%(desc$,fld.desc%)
	trash% = fn.put%(str$(hrs.units),fld.units%)
	trash% = fn.put%(fn.date.out$(hrs.eff.date$),fld.date%)
	return


rem------reads & writes---------
500	rem-----read an hrs rec------
	if pr1.debugging%  then \
		trash% = fn.msg%("500  fre = "+str$(fre))
	read #hrs.file%,hrs.rec%+1; \
#include "ipyhrs"
	if hrs.deleted%  then \
		trash%=fn.msg%("RECORD "+str$(hrs.rec%)+" HAS BEEN DELETED."):\
		good.rec% = false% :\
		return
	gosub 501	rem get name & desc
	return

501	rem-----get name & desc-------
	emp.emp.name$ = null$
	if hrs.rate% = 0  then \
		desc$ = cat.0$
	if hrs.rate% > 0  and hrs.rate% < 5  then \
		desc$ = pr1.rate.name$(hrs.rate%)
	if hrs.rate% >= 5  then \
		desc$ = ed.desc.table$(hrs.rate%)
	if names%  then gosub 560	rem  read emp file
	return

550	rem-----write an hrs rec------
	print #hrs.file%,hrs.rec%+1; \
#include "ipyhrs"

	if adding%  then\
		hrs.hdr.no.recs% = hrs.hdr.no.recs% + 1
	return

555	rem-----write hrs hdr-----
	print #hrs.file%,1; \
#include "ipyhrshd"
	return

560	rem-----read emp file-------
	if pr1.debugging%  then \
		trash% = fn.msg%("560  fre = "+str$(fre))
	emp.rec% = val(left$(hrs.emp.no$,4))
	invalid.emp% = false%
	read #emp.file%, emp.rec%+1; \
#include "ipyemp"

	if emp.status$ = "T"  then \
		emp.emp.name$ = "TERMINATED EMPLOYEE" :\
		invalid.emp% = true%
	if emp.status$ = "D"  then \
		emp.emp.name$ = "DELETED EMPLOYEE"  :\
		invalid.emp% = true%
	if emp.status$ = "L"  then \
		emp.emp.name$ = "EMPLOYEE ON LEAVE"
	emp.emp.name$ = fn.name.flip$(emp.emp.name$)
	return

rem------eoj routines-------
600	rem-----rename hrs file------
	gosub 555	rem write hrs hdr
	close hrs.file%
	trash% = rename(hrs.out$,hrs.in$)
	return

650	rem-----rewrite pr2-----
	if not write.pr2%  then return
	pr2.hrs.batch.no% = hrs.hdr.batch.no%
	print #pr2.file%; \
#include "ipypr2"

	close pr2.file%
	return
end
