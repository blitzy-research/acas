rem-----set up dms screen equates-   October 19,1979---------------
       crt.buffer.count%=9
       dim crt.screen.buffer$(crt.buffer.count%)
       crt.field.count% = 6
       dim crt.buffer$(crt.field.count%)
       dim crt.format.fields%(crt.field.count%,3)
       crt.format.fields%(0,0) = crt.field.count%
       crt.screen.buffer$(1) = crt.clear$+crt.background$

       crt.screen.buffer$(2)=fn.crt.sca$(1,2)+	   \
left$(blank$, (74-len(pr1.co.name$))/2)+pr1.co.name$
       crt.screen.buffer$(3)=fn.crt.sca$(3,12)+     \
fn.date.out$(common.date$)+"        I T E M   F I L E   P A R A M E T E R S"
       crt.screen.buffer$(4)=fn.crt.sca$(6,18)+     \
"NUMBER OF SYSTEM ITEM FILES            [ ]"
       crt.screen.buffer$(5)=fn.crt.sca$(8,18)+     \
"ITEM FILE ONE     DISK DRIVE           [ ]"
       crt.screen.buffer$(6)=fn.crt.sca$(10,18)+     \
"ITEM FILE TWO     DISK DRIVE           [ ]"
       crt.screen.buffer$(7)=fn.crt.sca$(11,18)+     \
"LOW ITEM NUMBER ON FILE TWO   [          ]"
       crt.screen.buffer$(8)=fn.crt.sca$(13,18)+     \
"ITEM FILE THREE   DISK DRIVE           [ ]"
       crt.screen.buffer$(9)=fn.crt.sca$(14,18)+     \
"LOW ITEM NUMBER ON FILE THREE [          ]"
       crt.format.fields%(1,0)=6  :  crt.format.fields%(1,1)=58
       crt.format.fields%(1,2)=1  :  crt.format.fields%(1,3)=2
       crt.format.fields%(2,0)=8  :  crt.format.fields%(2,1)=58
       crt.format.fields%(2,2)=1  :  crt.format.fields%(2,3)=1
       crt.format.fields%(3,0)=10  :  crt.format.fields%(3,1)=58
       crt.format.fields%(3,2)=1  :  crt.format.fields%(3,3)=1
       crt.format.fields%(4,0)=11  :  crt.format.fields%(4,1)=49
       crt.format.fields%(4,2)=10  :  crt.format.fields%(4,3)=1
       crt.format.fields%(5,0)=13  :  crt.format.fields%(5,1)=58
       crt.format.fields%(5,2)=1  :  crt.format.fields%(5,3)=1
       crt.format.fields%(6,0)=14  :  crt.format.fields%(6,1)=49
       crt.format.fields%(6,2)=10  :  crt.format.fields%(6,3)=1

       trash%=fn.crt.display.background%


