dim check.category%(pr1.max.ed.cats%)	rem   9/29/79
rem-----------------------------------------------------------
rem   check box 1 is gross pay.  It is the total of
rem   check boxes 2+3+4+5+6+7.
rem   check box 8 is net pay.  It is the difference
rem   between check box 1 and the sum of check
rem   boxes 9+10+11+12+13+14+15+16.
rem-----------------------------------------------------------
check.category%(01)=02	   rem REGULAR PAY
check.category%(02)=03	   rem OVERTIME PAY
check.category%(03)=04	   rem SPECIAL OT PAY
check.category%(04)=05	   rem COMMISSION
check.category%(05)=00	   rem VACATION TAKEN	  NOT ON CHECKS
check.category%(06)=00	   rem SICK LVE TAKEN	  NOT ON CHECKS
check.category%(07)=00	   rem COMP TIME TAKEN	  NOT ON CHECKS
check.category%(08)=00	   rem COMP TIME EARND	  NOT ON CHECKS
check.category%(09)=06	   rem BONUS
check.category%(10)=07	   rem TIPS COLLECTED
check.category%(11)=06	   rem ADVANCE
check.category%(12)=06	   rem SICK PAY
check.category%(13)=06	   rem VACATION PAY
check.category%(14)=06	   rem OTHER EXCLD PAY
check.category%(15)=06	   rem EXPENSE REIMB
check.category%(16)=06	   rem EIC
check.category%(17)=06	   rem OTHER PAY
check.category%(18)=14	   rem TIPS REPORTED
check.category%(19)=00	   rem UNUSED
check.category%(20)=09	   rem FWT
check.category%(21)=10	   rem SWT
check.category%(22)=11	   rem LWT
check.category%(23)=12	   rem FICA
check.category%(24)=13	   rem SDI
check.category%(25)=00	   rem UNUSED
check.category%(26)=00	   rem UNUSED
check.category%(27)=14	   rem ADVANCE REPAY
check.category%(28)=09	   rem FWT ADD-ON
check.category%(29)=10	   rem SWT ADD-ON
check.category%(30)=11	   rem LWT ADD-ON
check.category%(31)=12	   rem FICA ADD-ON
check.category%(32)=00	   rem UNUSED
check.category%(33)=00	   rem SYS1 FROM DED FILE
check.category%(34)=00	   rem SYS2 FROM DED FILE
check.category%(35)=00	   rem SYS3 FROM DED FILE
check.category%(36)=00	   rem SYS4 FROM DED FILE
check.category%(37)=00	   rem SYS5 FROM DED FILE
check.category%(38)=00	   rem EMP1 FROM EMP FILE
check.category%(39)=00	   rem EMP2 FROM EMP FILE
check.category%(40)=00	   rem EMP3 FROM EMP FILE
check.category%(41)=00	   rem UNUSED
check.category%(42)=00	   rem COMPANY FICA	  NOT ON CHECKS
check.category%(43)=00	   rem COMPANY FUTA	  NOT ON CHECKS
check.category%(44)=00	   rem COMPANY SUI	  NOT ON CHECKS
check.category%(45)=00	   rem UNUSED
check.category%(46)=00	   rem OTHER CO COST	  NOT ON CHECKS
check.category%(47)=00	   rem UNUSED
check.category%(48)=00	   rem UNUSED
check.category%(49)=00	   rem UNUSED
check.category%(50)=16	   rem OTHER DED
