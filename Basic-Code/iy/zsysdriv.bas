rem       Nov. 15, 1978
rem       22 April 2009 - remove drive letters
def fn.get.sys.drive$
        if size(system$+"pr1.101") then \
                fn.get.sys.drive$="":return
        fn.get.sys.drive$=null$:return
fend

