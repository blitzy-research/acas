8510	return		rem this is a dummy rtn
8520	rem-----basic console interruption feature-----------------
	end.wanted=false
	if not constat% then return
	trash%=conchar% 			rem remove garbage
	while true
		print tab(15);"Type stop to abort printout"
		print tab(15);"Hit return key to continue";
		input ""; line ans$
		if ans$ = return$  then  return
		if ucase$(ans$)="STOP" or ans$=chr$(27) \
			then	end.wanted = true   :\
				return
	wend
