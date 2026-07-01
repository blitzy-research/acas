rem-----set up dms screen equates-August 6,1979     ---------------
       crt.buffer.count%=7
       dim crt.screen.buffer$(crt.buffer.count%)
       crt.field.count% = 1
       dim crt.buffer$(crt.field.count%)
       dim crt.format.fields%(crt.field.count%,3)
       crt.format.fields%(0,0) = crt.field.count%
       crt.screen.buffer$(1) = crt.clear$+crt.background$

       crt.screen.buffer$(2)=fn.crt.sca$(1,2)+	   \
left$(blank$, (74-len(pr1.co.name$))/2)+pr1.co.name$
       crt.screen.buffer$(3)=fn.crt.sca$(3,20)+     \
display.date$+"     P A R A M E T E R   E N T R Y"
       crt.screen.buffer$(4)=fn.crt.sca$(4,36)+     \
"M E N U"
       crt.screen.buffer$(5)=fn.crt.sca$(6,30)+     \
"1 GENERAL PARAMETERS"
       crt.screen.buffer$(6)=fn.crt.sca$(8,30)+     \
"2 AUDIT PARAMETERS"
       crt.screen.buffer$(7)=fn.crt.sca$(10,30)+     \
"SELECT A SCREEN > [  ]"
       crt.format.fields%(1,0)=10  :  crt.format.fields%(1,1)=49
       crt.format.fields%(1,2)=2  :  crt.format.fields%(1,3)=1

       trash%=fn.crt.display.background%


