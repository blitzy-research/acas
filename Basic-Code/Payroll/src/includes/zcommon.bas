rem-----SYSTEM COMMONS---11/06/79---------------------------------------
common chained.from.root%	 rem T/F true if called from menu
common chained% 		 rem T/F true if called from anybody
common chained.program.number%	 rem 0-99 number of this program
common common.return.code%	 rem 0 if ok, else 1,2,etc
common common.msg$		 rem error msg for menu to print
common common.chaining.status$	 rem genl info, codes are in include
common common.serial.number$	 rem serial number, stupid
common common.date$		 rem yymmdd   RUN date from menu
common common.drive%		 rem internal drive where PR1 and PR2 files are
common true%,false%		 rem -1, 0 for logical true, false
common sector.len%,pumpkin	 rem  disk sector size, zserial constant
common tof$,quote$,bell$,comma$  rem character strings
common pound$, blank$		 rem "#...#" and blanks
rem---------------------------------------------------------------------
