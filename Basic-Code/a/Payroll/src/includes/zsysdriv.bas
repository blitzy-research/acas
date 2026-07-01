rem	  Nov. 06, 1979
def fn.get.sys.drive%
    if size(fn.file.name.out$(system$+"PR1","101", 1,password$,params$))<> 0\
	then fn.get.sys.drive%=1: RETURN
    if size(fn.file.name.out$(system$+"PR1","101", 2,password$,params$))<> 0\
	then fn.get.sys.drive%=2: RETURN
    fn.get.sys.drive%= -1: RETURN
fend

