rem	Jan. 13, 1979
def fn.num%(no$)
	if match(left$(pound$,len(no$)),no$,1)<>1 and len(no$)>0 \
		then   fn.num%=false% \
		else   fn.num%=true%
	return
fend
