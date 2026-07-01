rem	  June 22, 1979
%nolist
sum.sum=0
sum.x%=1
while sum.x%<=len(cpyrght$)
	sum.sum=sum.sum+asc(mid$(cpyrght$,sum.x%,1))
	sum.x%=sum.x%+1
wend
if sum.sum<>pumpkin then \
	print bell$;tab(5);system$+"044 INVALID COMMAND SEQUENCE" :\
	stop
serial.number=(0fh and asc(mid$(dummy$,6,1)))
serial.number=serial.number+(0fh and asc(mid$(dummy$,5,1)))*16.0
serial.number=serial.number+(0fh and asc(mid$(dummy$,4,1)))*256.0
serial.number=serial.number+(0fh and asc(mid$(dummy$,3,1)))*4096.0
serial.number$=str$(serial.number)+chr$(asc(mid$(dummy$,7,1))+040h)+  \
				   chr$(asc(mid$(dummy$,8,1))+040h)+  \
				   chr$(asc(mid$(dummy$,9,1))+040h)
if chained% and common.serial.number$<>serial.number$ then \
	print bell$;tab(5);system$+"045 INVALID COMMAND SEQUENCE" :\
	stop
common.serial.number$=serial.number$
%list
