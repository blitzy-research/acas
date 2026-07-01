rem-----set up dms screen equates-oct. 18,1979---------------
       crt.buffer.count%=13
       dim crt.screen.buffer$(crt.buffer.count%)
       crt.field.count% = 14
       dim crt.buffer$(crt.field.count%)
       dim crt.format.fields%(crt.field.count%,3)
       crt.format.fields%(0,0) = crt.field.count%
       crt.screen.buffer$(1) = crt.clear$+crt.background$

       crt.screen.buffer$(2)=fn.crt.sca$(1,2)+     \
left$(blank$, (70-len(pr1.co.name$))/2)+pr1.co.name$
       crt.screen.buffer$(3)=fn.crt.sca$(3,1)+     \
"DATE ["+fn.date.out$(common.date$)+"]       STOCK CONTROL SYSTEM"
       crt.screen.buffer$(4)=fn.crt.sca$(4,26)+     \
"P A R T   E N T R Y"
       crt.screen.buffer$(5)=fn.crt.sca$(5,2)+	   \
"ACCESS KEY                                                 ITEM  NUMBER"
       crt.screen.buffer$(6)=fn.crt.sca$(6,1)+	   \
"[          ]                                                [          ]"
       crt.screen.buffer$(7)=fn.crt.sca$(8,1)+	   \
"DESCRIPTION        [                              ]"
       crt.screen.buffer$(8)=fn.crt.sca$(10,1)+     \
"STOCKROOM QUANTITY [       ]            SUPPLIER NUMBER     [     ]"
       crt.screen.buffer$(9)=fn.crt.sca$(12,1)+     \
"REORDER POINT      [       ]              COST / UNIT       [           ]"
       crt.screen.buffer$(10)=fn.crt.sca$(14,1)+     \
"STD REORDER QTY    [       ]              QUANTITY ON ORDER [       ]"
       crt.screen.buffer$(11)=fn.crt.sca$(16,1)+     \
"RETAIL PRICE       [           ]          DATE ORDERED      [        ]"
       crt.screen.buffer$(12)=fn.crt.sca$(18,1)+     \
"STOCK VALUE        [              ]       DATE DUE          [        ]"
       crt.screen.buffer$(13)=fn.crt.sca$(20,43)+     \
"BACK ORDERED      [       ]"
       crt.format.fields%(1,0)=6  :  crt.format.fields%(1,1)=2
       crt.format.fields%(1,2)=10  :  crt.format.fields%(1,3)=1
       crt.format.fields%(2,0)=6  :  crt.format.fields%(2,1)=62
       crt.format.fields%(2,2)=10  :  crt.format.fields%(2,3)=1
       crt.format.fields%(3,0)=8  :  crt.format.fields%(3,1)=21
       crt.format.fields%(3,2)=30  :  crt.format.fields%(3,3)=1
       crt.format.fields%(4,0)=10  :  crt.format.fields%(4,1)=21
       crt.format.fields%(4,2)=6  :  crt.format.fields%(4,3)=2
       crt.format.fields%(5,0)=12  :  crt.format.fields%(5,1)=21
       crt.format.fields%(5,2)=6  :  crt.format.fields%(5,3)=2
       crt.format.fields%(6,0)=14  :  crt.format.fields%(6,1)=21
       crt.format.fields%(6,2)=6  :  crt.format.fields%(6,3)=2
       crt.format.fields%(7,0)=16  :  crt.format.fields%(7,1)=21
       crt.format.fields%(7,2)=8  :  crt.format.fields%(7,3)=3
       crt.format.fields%(8,0)=18  :  crt.format.fields%(8,1)=21
       crt.format.fields%(8,2)=10  :  crt.format.fields%(8,3)=3
       crt.format.fields%(9,0)=10  :  crt.format.fields%(9,1)=62
       crt.format.fields%(9,2)=5  :  crt.format.fields%(9,3)=1
       crt.format.fields%(10,0)=12  :  crt.format.fields%(10,1)=62
       crt.format.fields%(10,2)=8  :  crt.format.fields%(10,3)=3
       crt.format.fields%(11,0)=14  :  crt.format.fields%(11,1)=62
       crt.format.fields%(11,2)=6  :  crt.format.fields%(11,3)=2
       crt.format.fields%(12,0)=16  :  crt.format.fields%(12,1)=62
       crt.format.fields%(12,2)=8  :  crt.format.fields%(12,3)=1
       crt.format.fields%(13,0)=18  :  crt.format.fields%(13,1)=62
       crt.format.fields%(13,2)=8  :  crt.format.fields%(13,3)=1
       crt.format.fields%(14,0)=20  :  crt.format.fields%(14,1)=62
       crt.format.fields%(14,2)=6  :  crt.format.fields%(14,3)=2

       trash%=fn.crt.display.background%


