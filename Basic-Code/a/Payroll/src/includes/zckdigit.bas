rem	  Nov. 21, 1978
def fn.ck.dig$(no$)
	sum%=0
	xx5%=1
	while xx5%<=len(no$)
		sum%=sum%+xx5%*val(mid$(no$,xx5%,1))
		xx5%=xx5%+1
	wend
	remainder%=sum%-(int(sum%/11)*11)
	if remainder%=10 then remainder%=0
	fn.ck.dig$=str$(remainder%)
	return
fend

