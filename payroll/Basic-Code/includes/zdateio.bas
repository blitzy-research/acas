rem	  May  10, 1979
def fn.date.in$=right$("00"+str$(yr%),2)+right$("00"+str$(mo%),2)+ \
	      right$("00"+str$(dy%),2)
dim out.date$(3)
def fn.date.out$(date$)
	out.date$(pr1.date.mo%)=mid$(date$,3,2)
	out.date$(pr1.date.dy%)=mid$(date$,5,2)
	out.date$(pr1.date.yr%)=mid$(date$,1,2)
	fn.date.out$=out.date$(1)+"/"+out.date$(2)+"/"+out.date$(3)
	return
fend

