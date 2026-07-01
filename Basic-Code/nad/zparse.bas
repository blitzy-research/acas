rem	Feb. 28, 1979
def fn.parse%(data$,delim$)
	goto .0071
.700	rem-----dim.1------------------------------
	dim.1%=true%
	if token.limit%=0 then token.limit%=5
	dim token$(token.limit%)
	return
.0071	if not dim.1% then gosub .700
	tok%=1:eos%=false%:posit%=1
	while not eos% and tok%<=token.limit%
		delim%=match(delim$,data$,posit%)
		if delim%=0 \
			then eos%=true% :\
			     token$(tok%)=mid$(data$,posit%,255) \
			else token$(tok%)=mid$(data$,posit%,delim%-posit%) :\
			     tok%=tok%+1 :\
			     posit%=delim%+1
	wend
	fn.parse%=tok%
	return
fend
