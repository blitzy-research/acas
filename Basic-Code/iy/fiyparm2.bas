rem-----set up dms screen equates-August 6,1979       ---------------
       crt.buffer.count%=7
       dim crt.screen.buffer$(crt.buffer.count%)
       crt.field.count% = 3
       dim crt.buffer$(crt.field.count%)
       dim crt.format.fields%(crt.field.count%,3)
       crt.format.fields%(0,0) = crt.field.count%
       crt.screen.buffer$(1) = crt.clear$+crt.background$

       crt.screen.buffer$(2)=fn.crt.sca$(1,2)+	   \
left$(blank$, (74-len(pr1.co.name$))/2)+pr1.co.name$
       crt.screen.buffer$(3)=fn.crt.sca$(3,30)+     \
"PARAMETER  ENTRY"
       crt.screen.buffer$(4)=fn.crt.sca$(4,18)+     \
display.date$+"    A U D I T   P A R A M E T E R S"
       crt.screen.buffer$(5)=fn.crt.sca$(6,30)+     \
"AUDIT DRIVE [ ]"
       crt.screen.buffer$(6)=fn.crt.sca$(8,25)+     \
"ADDITIONS AUDIT USED [ ]"
       crt.screen.buffer$(7)=fn.crt.sca$(9,24)+     \
"DEPLETIONS AUDIT USED [ ]"
       crt.format.fields%(1,0)=6  :  crt.format.fields%(1,1)=43
       crt.format.fields%(1,2)=1  :  crt.format.fields%(1,3)=1
       crt.format.fields%(2,0)=8  :  crt.format.fields%(2,1)=47
       crt.format.fields%(2,2)=1  :  crt.format.fields%(2,3)=1
       crt.format.fields%(3,0)=9  :  crt.format.fields%(3,1)=47
       crt.format.fields%(3,2)=1  :  crt.format.fields%(3,3)=1

       trash%=fn.crt.display.background%


