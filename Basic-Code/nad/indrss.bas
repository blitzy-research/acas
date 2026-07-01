rem		   December 22, 1977
rem		UPDATED: DEC. 18, 1979 -- AMC
rem		UPDATED: JUNE. 9,1980 -- VBC, Applewood Computers
rem
rem	     N A M E   A N D   A D D R E S S   S Y S T E M
rem		    Record Selection System include
rem
2400	rem-----select routine---------------------------------------
	selected = true
	rem - it is assumed that test.name$ has been set to astericks
	if test.name$ = nad.name$				 \
		then	selected = false			:\
			number.deleted = number.deleted + 1	:\
			return
	if match.flag  then  gosub  2500	rem  check for match
	if range.flag  then  gosub  2600	rem  check for range
	return
2500	rem-----check for match--------------------------------------
	gosub  2700				rem set equates
	if utran  then	\
		tran.length = end.loc - start.loc + len(pattern$)	:\
		upper.tran$ = mid$(nad$(nad.num),start.loc,tran.length) :\
		gosub 3500						:\
		match.result = match(pattern$,upper.tran$,1)		:\
		gosub 3510						:\
	   else  \
		match.result = match(pattern$,nad$(nad.num),start.loc)
	if (match.result=0) or (match.result>end.loc) then selected=false :\
							  else selected=true
	if not.flag  then  selected = not selected
	return
2600	rem-----check for range--------------------------------------
	gosub 2700				rem  set equates
	range.result$ = mid$(nad$(nad.num),start.loc,sub.len)
	if utran  then	\
		upper.tran$ = range.result$	:\
		gosub 3500			:\   translate
		range.result$ = upper.tran$
	selected = false
	if (range.result$ >= low.valid$) and (range.result$ <= hi.valid$) \
			then	selected=true
	if not.flag  then  selected = not selected
	if (range.result$ > hi.valid$) and (not not.flag)  then  goto 5909
	return
2700	rem-----set up equates---------------------------------------
	nad$(1) = nad.name$
	nad$(2) = nad.addr1$
	nad$(3) = nad.addr2$
	nad$(4) = nad.city$
	nad$(5) = nad.state$
	nad$(6) = nad.zip$
	nad$(7) = nad.phone$
	nad$(8) = nad.ref$
	return
2800	rem-----get value of response--------------------------------
	print
	print tab(10);"Enter starting record number";
	input "";line ans$
	if ans$ = return$  then start.rec = 1 :\
		else  start.rec = val(ans$)
	if start.rec < 1  then \
		print tab(5); bell$; emsg$(11) :\
		goto 2800
	if end #1  then 2800.1	 rem reset eof jump
	read #1, start.rec; line anything$
	goto 2800.2
2800.1
		print tab(5); bell$; emsg$(11)
		goto 2800
2800.2
	if end #1  then 5909.1
	read #1, start.rec;
	record.number = start.rec - 1
2801
	print
	print tab(10);"Enter name of selection field";
	input ""; line ans$
	nad.num = 0
	if ans$ = return$  then done = true  :\
		return	 :\
	else done = false
	ans$=ucase$(ans$)
	if (ans$ = "NAME")      then  nad.num = 1
	if (ans$ = "ADDR1")     then  nad.num = 2
	if (ans$ = "ADDR2")     then  nad.num = 3
	if (ans$ = "ADDR3")     then  nad.num = 4 rem **** Uk version ****
	rem **** UK version change ****
	if (ans$ = "CODE")      then  nad.num = 6 rem **** UK version ****
	if (ans$ = "PHONE")     then  nad.num = 7
	if (ans$ = "REF")       then  nad.num = 8
	if nad.num <> 0  then  return		  rem  got a valid response
	print tab(10);"Valid responses are"
	print tab(10);"NAME       ADDR1      ADDR2      ADDR3"
	print tab(10);"CODE       PHONE      REF " rem **** UK version ****
	print
	goto 2801				  rem  loop
2900	rem-----set range or match------------------------------------
	while true
		print
		print tab(10);"Range or match (R or M)?";
		input ""; line ans$
		ans$=ucase$(ans$)
		if (ans$ = "R")  then \
				range.flag = true    :\
				return
		if (ans$ = "Not R")  then  \
				range.flag = true	      :\
				not.flag = true 	      :\
				return
		if (ans$ = "M")  then \
				match.flag = true    :\
				return
		if (ans$ = "Not M")  then  \
				match.flag = true	      :\
				not.flag = true 	      :\
				return
	wend
3000	rem-----range requests--------------------------------------
	print
	print tab(10);"Enter lowest valid value";
	input ""; line low.valid$
	print
	print tab(10);"Enter highest valid value";
	input ""; line hi.valid$
	if len(low.valid$) <> len(hi.valid$)  then  \
				print emsg$(3)	    :\
				print		   :\
				goto 3000
	if low.valid$ > hi.valid$  then       \
			print emsg$(8)	     :\
			print		     :\
			goto 3000
	need.tran = false
	utran = true
	test.lower$ = low.valid$
	gosub 3300			rem  test for lower case
	test.lower$ = hi.valid$
	gosub 3300
	if utran  then	gosub 3400	rem  ask if translation wanted
	if len(low.valid$) = field.len(nad.num)  then	       \
				start.loc = 1		      :\
				sub.len = field.len(nad.num)  :\
				return
3010
	print
	print tab(10);"Enter starting location";
	input ""; start.loc
	if start.loc < 1  then	   \
		print emsg$(7)	  :\
		goto 3010
	if (start.loc + len(low.valid$) - 1 ) > field.len(nad.num)  then  \
				print emsg$(4)		:\
				print			:\
				goto 3000
	sub.len = len(low.valid$)
	return
3100	rem-----match requests--------------------------------------
	print
	print tab(10);"Enter matching pattern";
	input ""; line pattern$
	need.tran = false		rem  these values must be set before
	utran = true			rem  the first time 3300 is called
	test.lower$ = pattern$
	gosub 3300
	if utran  then	gosub 3400
	if match("\\",pattern$,1) <> 0  then  goto 3105
	if len(pattern$) = field.len(nad.num)  then	\
				start.loc = 1		:\
				end.loc = 1		:\
				return
3105
	print
	print tab(10);"Enter first starting location";
	input "";start.loc
	print
	print tab(10);"Enter last starting location";
	input "";end.loc
	if start.loc > end.loc	then		\
			print emsg$(5)		:\
			print			:\
			goto 3105
	if end.loc > field.len(nad.num)  then	 \
			print emsg$(6)		:\
			print			:\
			goto 3105
	if match("\\",pattern$,1) > 0  then  return
	if (start.loc + len(pattern$) -1) > field.len(nad.num)	then  \
			print emsg$(4)		:\
			print			:\
			goto 3100
	return
3300
	rem -- look for lower case character and upper case character
	rem -- translation may be necessary if no lower case are found
	rem -- and at least one upper case are found
	x%= len(test.lower$)
	for i% = 1 to x%
		temp$ = mid$(test.lower$,x%,1)
		if temp$ >= "a"  then  utran = false
		if (temp$ <= "Z") and (temp$ >= "A")  then  need.tran = true
	next i%
	utran = utran and need.tran	rem  to ask for translation utran must
					rem  be true and need.tran must be true
	return
3400
	rem -- ask for translation
	while true
		print tab(10);"Do you want upper case translation (Y,N)?";
		input ""; line ans$
		if (ans$ = "Y") or (ans$ = "y")  then  return
		if (ans$ = "N") or (ans$ = "n")  then  \
				utran = false	      :\
				return
	wend
3500
	rem -- do translation of string
	upper.tran$=ucase$(upper.tran$)
	return
rem	x = len(upper.tran$)
rem	for i = 1 to x
rem		temp$ = mid$(upper.tran$,i,1)
rem		if temp$ >= "a"  then                   \
rem			temp$ = chr$(asc(temp$) and 95) :\
rem			upper.tran$ = left$(upper.tran$,i-1) + temp$ +	 \
rem				     right$(upper.tran$,x-i)
rem		next i
rem	return
3510
	rem -- reset the match value after match on shortened string
	if match.result <> 0  then  \
		match.result = match.result + start.loc - 1
	return
