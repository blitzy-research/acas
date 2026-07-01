rem-----set up dms screen equates-10/18/79---------------
       crt.buffer.count%=8
       dim crt.screen.buffer$(crt.buffer.count%)
       crt.field.count% = 5
       dim crt.buffer$(crt.field.count%)
       dim crt.format.fields%(crt.field.count%,3)
       crt.format.fields%(0,0) = crt.field.count%
       crt.screen.buffer$(1) = crt.clear$+crt.background$

       crt.screen.buffer$(2)=fn.crt.sca$(1,1)+	   \
left$(blank$,fn.center%(pr1.co.name$,crt.columns%))+pr1.co.name$
       crt.screen.buffer$(3)=fn.crt.sca$(3,29)+     \
"INVENTORY SYSTEM"
       crt.screen.buffer$(4)=fn.crt.sca$(4,6)+	   \
"DATE ["+fn.date.out$(common.date$)+    \
"]      DEPLETIONS FROM STOCK      BATCH NUMBER [     ]"
       crt.screen.buffer$(5)=fn.crt.sca$(9,14)+     \
"ITEM NUMBER         [          ]"
       crt.screen.buffer$(6)=fn.crt.sca$(11,14)+     \
"QUANTITY DEPLETED   [         ]"
       crt.screen.buffer$(7)=fn.crt.sca$(13,14)+     \
"STOCKROOM QUANTITY  [       ]"
       crt.screen.buffer$(8)=fn.crt.sca$(15,14)+     \
"DESCRIPTION         [                              ]"
       crt.format.fields%(1,0)=4  :  crt.format.fields%(1,1)=68
       crt.format.fields%(1,2)=5  :  crt.format.fields%(1,3)=1
       crt.format.fields%(2,0)=9  :  crt.format.fields%(2,1)=35
       crt.format.fields%(2,2)=10  :  crt.format.fields%(2,3)=1
       crt.format.fields%(3,0)=11  :  crt.format.fields%(3,1)=35
       crt.format.fields%(3,2)=7  :  crt.format.fields%(3,3)=2
       crt.format.fields%(4,0)=13  :  crt.format.fields%(4,1)=35
       crt.format.fields%(4,2)=6  :  crt.format.fields%(4,3)=2
       crt.format.fields%(5,0)=15  :  crt.format.fields%(5,1)=35
       crt.format.fields%(5,2)=30  :  crt.format.fields%(5,3)=1

       trash%=fn.crt.display.background%


