rem	 Apr. 24, 1978
%include znumber

def fn.numeric%(no$,left.digits%,right.digits%)
	fn.numeric%=false%
	radix%=match(".",no$,1)
	if radix%=0 then \
		radix%=len(no$)+1
	hi$=left$(no$,radix%-1)
	lo$=right$(no$,len(no$)-radix%)
	if len(hi$)>left.digits% or \
	   len(lo$)>right.digits% then \
		return
	if not fn.num%(hi$) or \
	   not fn.num%(lo$) then \
		return
	fn.numeric%=true%
	return
fend

