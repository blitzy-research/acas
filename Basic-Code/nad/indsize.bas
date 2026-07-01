	REM -- GET RECORD SIZE AND FIRST RECORD
	open file.name$ as 1
	read #1; line first.rec$
	nad.rec.len = len(first.rec$) + 2
	field.len(8) = nad.rec.len - 129   rem **** UK version change ****
	close 1
