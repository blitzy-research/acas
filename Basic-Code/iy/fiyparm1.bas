rem-----set up dms screen equates-     August  9,1979	 ---------------
       crt.buffer.count%=13
       dim crt.screen.buffer$(crt.buffer.count%)
       crt.field.count% = 10
       dim crt.buffer$(crt.field.count%)
       dim crt.format.fields%(crt.field.count%,3)
       crt.format.fields%(0,0) = crt.field.count%
       crt.screen.buffer$(1) = crt.clear$+crt.background$

       crt.screen.buffer$(2)=fn.crt.sca$(1,2)+	   \
left$(blank$, (74-len(pr1.co.name$))/2)+pr1.co.name$
       crt.screen.buffer$(3)=fn.crt.sca$(3,32)+     \
"PARAMETER ENTRY"
       crt.screen.buffer$(4)=fn.crt.sca$(4,5)+	   \
display.date$+"        G E N E R A L   P A R A M E T E R S"
       crt.screen.buffer$(5)=fn.crt.sca$(6,2)+	   \
"COMPANY NAME [                                                            ]"
       crt.screen.buffer$(6)=fn.crt.sca$(8,2)+	   \
"CURRENT PERIOD    [       ]                    AVERAGE VALUATION   [ ]"
       crt.screen.buffer$(7)=fn.crt.sca$(9,7)+	   \
"(WEEK, MONTH, QUARTER)"
       crt.screen.buffer$(8)=fn.crt.sca$(11,2)+     \
"TO DATE PERIOD    [       ]                    ARRAY SIZE      [     ]"
       crt.screen.buffer$(9)=fn.crt.sca$(12,7)+     \
"(MONTH, QUARTER, YEAR)"
       crt.screen.buffer$(10)=fn.crt.sca$(14,2)+     \
"DATE FORM               [ ]                    CONSOLE BELL USED   [ ]"
       crt.screen.buffer$(11)=fn.crt.sca$(15,7)+     \
"(1 MM/DD/YY  2 DD/MM/YY)"
       crt.screen.buffer$(12)=fn.crt.sca$(17,2)+     \
"PAGE WIDTH            [   ]                    DEBUGGING           [ ]"
       crt.screen.buffer$(13)=fn.crt.sca$(19,2)+     \
"LINES PER PAGE        [   ]"
       crt.format.fields%(1,0)=6  :  crt.format.fields%(1,1)=16
       crt.format.fields%(1,2)=60  :  crt.format.fields%(1,3)=1
       crt.format.fields%(2,0)=8  :  crt.format.fields%(2,1)=21
       crt.format.fields%(2,2)=7  :  crt.format.fields%(2,3)=1
       crt.format.fields%(3,0)=11  :  crt.format.fields%(3,1)=21
       crt.format.fields%(3,2)=7  :  crt.format.fields%(3,3)=1
       crt.format.fields%(4,0)=14  :  crt.format.fields%(4,1)=27
       crt.format.fields%(4,2)=1  :  crt.format.fields%(4,3)=1
       crt.format.fields%(5,0)=17  :  crt.format.fields%(5,1)=25
       crt.format.fields%(5,2)=3  :  crt.format.fields%(5,3)=1
       crt.format.fields%(6,0)=19  :  crt.format.fields%(6,1)=25
       crt.format.fields%(6,2)=3  :  crt.format.fields%(6,3)=1
       crt.format.fields%(7,0)=8  :  crt.format.fields%(7,1)=70
       crt.format.fields%(7,2)=1  :  crt.format.fields%(7,3)=1
       crt.format.fields%(8,0)=11  :  crt.format.fields%(8,1)=66
       crt.format.fields%(8,2)=4  :  crt.format.fields%(8,3)=2
       crt.format.fields%(9,0)=14  :  crt.format.fields%(9,1)=70
       crt.format.fields%(9,2)=1  :  crt.format.fields%(9,3)=1
       crt.format.fields%(10,0)=17  :  crt.format.fields%(10,1)=70
       crt.format.fields%(10,2)=1  :  crt.format.fields%(10,3)=1

       trash%=fn.crt.display.background%


