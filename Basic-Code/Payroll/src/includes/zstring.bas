rem	 Nov. 13, 1978
def fn.center%(a$,w%)=int%((w%-len(a$))/2)
def fn.pad$(a$,q%)=left$(a$+blank$,q%)
def fn.spread$(a$,q%)
	temp$=null$
	pad$=left$(blank$,q%)
	i%=1
	while i%<=len(a$)
		if mid$(a$,i%,1)=" " then temp$=temp$+pad$
		temp$=temp$+mid$(a$,i%,1)+pad$
		i%=i%+1
	wend
	fn.spread$=temp$
	return
fend

