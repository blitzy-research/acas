rem-----set up dms screen equates-OCTOBER 18,1979---------------
       crt.buffer.count%=14
       dim crt.screen.buffer$(crt.buffer.count%)
       crt.field.count% = 14
       dim crt.buffer$(crt.field.count%)
       dim crt.format.fields%(crt.field.count%,3)
       crt.format.fields%(0,0) = crt.field.count%
       crt.screen.buffer$(1) = crt.clear$+crt.background$

       crt.screen.buffer$(2)=fn.crt.sca$(1,2)+	   \
left$(blank$, (70-len(pr1.co.name$))/2)+pr1.co.name$
       crt.screen.buffer$(3)=fn.crt.sca$(3,20)+     \
"S T O C K   C O N T R O L   S Y S T E M"
       crt.screen.buffer$(4)=fn.crt.sca$(5,5)+	   \
"["+fn.date.out$(common.date$)+"]            PROCESSING CYCLE"
       crt.screen.buffer$(5)=fn.crt.sca$(7,5)+	   \
"[ ]  1 ADD TO STOCK                    [ ]  4 REORDER REPORT"
       crt.screen.buffer$(6)=fn.crt.sca$(8,5)+	   \
"[ ]  2 DEPLETE STOCK                   [ ]  5 VALUATION REPORT"
       crt.screen.buffer$(7)=fn.crt.sca$(9,5)+	   \
"[ ]  3 TRANSACTION PROOF               [ ]  6 ACTIVITY REPORT"
       crt.screen.buffer$(8)=fn.crt.sca$(10,44)+     \
"[ ]  7 START AN ACTIVITY PERIOD"
       crt.screen.buffer$(9)=fn.crt.sca$(12,27)+     \
"SYSTEM START-UP"
       crt.screen.buffer$(10)=fn.crt.sca$(14,5)+     \
"[ ]  8 PARAMETER ENTRY                 [ ]  9 CREATE SORT PARAMETER FILES"
       crt.screen.buffer$(11)=fn.crt.sca$(16,25)+     \
"ITEM FILE MAINTENANCE"
       crt.screen.buffer$(12)=fn.crt.sca$(18,5)+     \
"[ ] 10 ITEM ENTRY                      [ ] 12 ITEM FILE PRINT"
       crt.screen.buffer$(13)=fn.crt.sca$(19,5)+     \
"[ ] 11 ITEM FILE SORT                  [ ] 13 ITEM FILE RECOPY"
       crt.screen.buffer$(14)=fn.crt.sca$(21,23)+     \
"SELECT A PROGRAM > [   ]"
       crt.format.fields%(1,0)=7  :  crt.format.fields%(1,1)=6
       crt.format.fields%(1,2)=1  :  crt.format.fields%(1,3)=1
       crt.format.fields%(2,0)=8  :  crt.format.fields%(2,1)=6
       crt.format.fields%(2,2)=1  :  crt.format.fields%(2,3)=1
       crt.format.fields%(3,0)=9  :  crt.format.fields%(3,1)=6
       crt.format.fields%(3,2)=1  :  crt.format.fields%(3,3)=1
       crt.format.fields%(4,0)=7  :  crt.format.fields%(4,1)=45
       crt.format.fields%(4,2)=1  :  crt.format.fields%(4,3)=1
       crt.format.fields%(5,0)=8  :  crt.format.fields%(5,1)=45
       crt.format.fields%(5,2)=1  :  crt.format.fields%(5,3)=1
       crt.format.fields%(6,0)=9  :  crt.format.fields%(6,1)=45
       crt.format.fields%(6,2)=1  :  crt.format.fields%(6,3)=1
       crt.format.fields%(7,0)=10  :  crt.format.fields%(7,1)=45
       crt.format.fields%(7,2)=1  :  crt.format.fields%(7,3)=1
       crt.format.fields%(8,0)=14  :  crt.format.fields%(8,1)=6
       crt.format.fields%(8,2)=1  :  crt.format.fields%(8,3)=1
       crt.format.fields%(9,0)=14  :  crt.format.fields%(9,1)=45
       crt.format.fields%(9,2)=1  :  crt.format.fields%(9,3)=1
       crt.format.fields%(10,0)=18  :  crt.format.fields%(10,1)=6
       crt.format.fields%(10,2)=1  :  crt.format.fields%(10,3)=1
       crt.format.fields%(11,0)=19  :  crt.format.fields%(11,1)=6
       crt.format.fields%(11,2)=1  :  crt.format.fields%(11,3)=1
       crt.format.fields%(12,0)=18  :  crt.format.fields%(12,1)=45
       crt.format.fields%(12,2)=1  :  crt.format.fields%(12,3)=1
       crt.format.fields%(13,0)=19  :  crt.format.fields%(13,1)=45
       crt.format.fields%(13,2)=1  :  crt.format.fields%(13,3)=1
       crt.format.fields%(14,0)=21  :  crt.format.fields%(14,1)=43
       crt.format.fields%(14,2)=3  :  crt.format.fields%(14,3)=1

       trash%=fn.crt.display.background%


