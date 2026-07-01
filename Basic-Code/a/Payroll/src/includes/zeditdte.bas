rem	  May  10, 1979
rem requires: zparse, znum
def fn.leap.year%(year%)
	if (year%/4.0)-int%(year%/4.0)=0 \
		then   fn.leap.year%=true% \
		else   fn.leap.year%=false%
	return
fend

def fn.edit.date%(date$)			rem parameter file date
	fn.edit.date%=false%			rem information must be
	if fn.parse%(date$,"/")<>3 then return  rem initialized for this
	for xx2%=1 to 3 				rem function to
	  if not fn.num%(token$(xx2%)) then return	rem work
	next xx2%					rem correctly
	mo%=val(token$(pr1.date.mo%))
	dy%=val(token$(pr1.date.dy%))
	yr%=val(token$(pr1.date.yr%))
	if mo%<1 or mo%>12 or \
	   dy%<1 or dy%>31 or \
	   yr%<1 or yr%>99 then return
	if (mo%=4 or mo%=6 or mo%=9 or mo%=11) and dy%>30 then return
	if mo%=2 and not fn.leap.year%(yr%) and dy%>28 then return
	if mo%=2 and fn.leap.year%(yr%) and dy%>29 then return
	fn.edit.date%=true%
	return
fend


