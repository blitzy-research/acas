rem	Jan. 19, 1979
def fn.bracket$(number,l.digits%,cents%)
	temp$="###,###,###,###,###"
	temp%=len(str$(abs(int(number))))
	temp$=right$(temp$,temp%+int%(temp%/3.5))
	if cents% then temp$=temp$+".##"
	temp%=l.digits%+int%(l.digits%/3.5)+(cents%*(-3))+2
	if number<0 then temp$="<"+temp$+">" else temp$=" "+temp$+" "
	fn.bracket$=right$(blank$+temp$,temp%)
	return
fend
