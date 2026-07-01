rem       May. 18, 1979
pr2.file% = 2
if end #pr2.file%  then 1.09	rem no parameter file
open  common.drive$ +":"+ system$ + "pr2.101"  as pr2.file%
read #pr2.file%; \
%include iiypr200

goto 1.2        rem close pr2 file

1.09 rem------ here if no parameter file -------------
common.msg$="IY006  No parameter Two file"
print tab(5);bell$;common.msg$
goto 999.1              rem exit paragraph

1.2 rem----- close pr2 file -----------
close pr2.file%

