rem-----ZDATEINC--10/25/79------------------------------------

def fn.decompose.date%(date$)
	dy%=val(mid$(date$,5,2))
	mo%=val(mid$(date$,3,2))
	yr%=val(mid$(date$,1,2))
	return
fend

def fn.last.day%(mo%,yr%)
	if mo%=1 or mo%=3 or mo%=5 or mo%=7 or mo%=8 or mo%=10 or mo%=12 \
		then	fn.last.day%=31:return
	if mo%=4 or mo%=6 or mo%=9 or mo%=11 \
		then	fn.last.day%=30:return
	if fn.leap.year%(yr%)  \
		then	fn.last.day%=29  \
		else	fn.last.day%=28
	return
fend

def fn.incr.year%(xx8%)
	xx8%=xx8%+1
	if xx8%>99 then xx8%=0
	fn.incr.year%=xx8%
	return
fend
def fn.incr.month%(xx9%)
	xx9%=xx9%+1
	if xx9%>12 \
		then	xx9%=1	:\
			yr%=fn.incr.year%(yr%)
	fn.incr.month%=xx9%
	return
fend
def fn.incr.date$(date$,bump%)
	trash%=fn.decompose.date%(date$)
	while bump%>0
		bump%=bump%-1
		dy%=dy%+1
		if dy%>fn.last.day%(mo%,yr%) \
			then	dy%=1  :\
				mo%=fn.incr.month%(mo%)
	wend
	fn.incr.date$=fn.date.in$
	return
fend
