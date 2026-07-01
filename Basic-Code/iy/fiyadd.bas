rem-----set up dms screen equates-18/Oct.,1979---------------
       crt.buffer.count%=9
       dim crt.screen.buffer$(crt.buffer.count%)
       crt.field.count% = 10
       dim crt.buffer$(crt.field.count%)
       dim crt.format.fields%(crt.field.count%,3)
       crt.format.fields%(0,0) = crt.field.count%
       crt.screen.buffer$(1) = crt.clear$+crt.background$
        no.blanks% = fn.center%(pr1.co.name$,crt.columns%)-2
        co.name$ = left$(blank$,no.blanks%)+pr1.co.name$

       crt.screen.buffer$(2)=fn.crt.sca$(4,31)+     \
"STOCK CONTROL SYSTEM"
       crt.screen.buffer$(3)=fn.crt.sca$(5,7)+	   \
"DATE ["+fn.date.out$(common.date$)+"]        ADDITIONS TO STOCK        BATCH NUMBER [      ]"
       crt.screen.buffer$(4)=fn.crt.sca$(8,6)+	   \
"ITEM NUMBER        [          ]        QUANTITY ORDERED     [       ]"
       crt.screen.buffer$(5)=fn.crt.sca$(10,6)+     \
"QUANTITY ADDED     [          ]        DATE ORDERED         [        ]"
       crt.screen.buffer$(6)=fn.crt.sca$(12,6)+     \
"UNIT COST          [           ]       DATE DUE             [        ]"
       crt.screen.buffer$(7)=fn.crt.sca$(14,6)+     \
"STOCKROOM QUANTITY [         ]         QUANTITY BACKORDERED [       ]"
       crt.screen.buffer$(8)=fn.crt.sca$(17,18)+     \
"DESCRIPTION [                              ]"
       crt.screen.buffer$(9)=fn.crt.sca$(3,2)+	   \
pad$+co.name$
       crt.format.fields%(1,0)=5  :  crt.format.fields%(1,1)=70
       crt.format.fields%(1,2)=5  :  crt.format.fields%(1,3)=2
       crt.format.fields%(2,0)=8  :  crt.format.fields%(2,1)=26
       crt.format.fields%(2,2)=10  :  crt.format.fields%(2,3)=1
       crt.format.fields%(3,0)=10  :  crt.format.fields%(3,1)=26
       crt.format.fields%(3,2)=7  :  crt.format.fields%(3,3)=2
       crt.format.fields%(4,0)=12  :  crt.format.fields%(4,1)=26
       crt.format.fields%(4,2)=8  :  crt.format.fields%(4,3)=3
       crt.format.fields%(5,0)=8  :  crt.format.fields%(5,1)=67
       crt.format.fields%(5,2)=6  :  crt.format.fields%(5,3)=2
       crt.format.fields%(6,0)=10  :  crt.format.fields%(6,1)=67
       crt.format.fields%(6,2)=8  :  crt.format.fields%(6,3)=1
       crt.format.fields%(7,0)=12  :  crt.format.fields%(7,1)=67
       crt.format.fields%(7,2)=8  :  crt.format.fields%(7,3)=1
       crt.format.fields%(8,0)=14  :  crt.format.fields%(8,1)=67
       crt.format.fields%(8,2)=6  :  crt.format.fields%(8,3)=2
       crt.format.fields%(9,0)=14  :  crt.format.fields%(9,1)=26
       crt.format.fields%(9,2)=6  :  crt.format.fields%(9,3)=2
       crt.format.fields%(10,0)=17  :  crt.format.fields%(10,1)=31
       crt.format.fields%(10,2)=30  :  crt.format.fields%(10,3)=1

       trash%=fn.crt.display.background%


