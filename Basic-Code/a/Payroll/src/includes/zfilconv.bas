rem 22-oct-79 CPM FILE NAME FUNCTIONS
	def fn.drive.in%(temp$)
		fn.drive.in% = -1
		if len(temp$) <> 1 then return
		temp$=ucase$(temp$)
		if temp$ <> "@" and     \
		   (temp$ > "D" or temp$ < "A")\
			then return
		if temp$ = "@"          \
			then fn.drive.in% = 0	\
			else fn.drive.in% = asc(temp$) - asc("A") + 1
		return
	fend
	def fn.drive.out$(temp%)
		if temp% = 0	\
			then fn.drive.out$ = "@"        \
			else fn.drive.out$ = chr$(asc("A") + temp% - 1)
		return
	fend
	def fn.file.name.out$(c.name$,c.type$,c.drive%,c.password$,c.params$)=\
		fn.drive.out$(c.drive%)+":"+c.name$+"."+c.type$
