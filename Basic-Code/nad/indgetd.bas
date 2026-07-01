rem	  FEB. 12, 1979
def fn.get.drive$
.004	print tab(10);"Enter nad file drive (@,A-F;RET=CURLOG) ";
	input "";line in$
	if in$=return$ then in$="@"
	if in$<>null$ then in$=ucase$(in$)
	if in$<>"A" and in$<>"B" and in$<>"C" and          \
	   in$<>"D" and in$<>"E" and in$<>"F" and in$<>"@" \
		then	print bell$;tab(5);"NAD010 INVALID DRIVE LETTER" :\
			goto .004
	fn.get.drive$=in$
	return
fend
