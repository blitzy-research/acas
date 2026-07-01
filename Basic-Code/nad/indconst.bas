rem	  JUNE, 8, 1980
system$="NAD":version$=" VER:3.01 UK "  rem **** UK version change ****
system.name$="NAD"
cpyrght$="COPYRIGHT (C) 1980-2025 Applewood Computers " rem **** UK version change **
dummy$="NDppvvILP":true%=-1:false%=0:null$="":return$="":tof$=chr$(12) rem UK
back$="^":escape$=chr$(27):not.accepted%=9:comma$=",":sector.len%=128
asterisk$="*":bell$=chr$(7):pound$="##############":pumpkin=2314+77 rem UK ver
blank$="                                                                                                                                "
%include A:INDGETD
if not chained% then for x%=1 to 24:print:next x%	rem clear screen
if not chained% \
  then	print:print:print		:\
	print cpyrght$			:\
	print				:\
	print system.name$;version$	:\
	print program$			:\
	print:print:print		:\
	print				 \
  else	for x%=1 to 24:print:next x%			rem clear screen
if pr1.bell.suppressed% then bell$=null$
