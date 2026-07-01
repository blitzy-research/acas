rem	5-oct-79
rem
rem	function that converts a boolean value to a string
rem	'Y' or 'N'
rem
	def fn.dsp.yorn$(boolean.value%)
	if boolean.value%	\
	   then fn.dsp.yorn$ = "Y"\
	   else fn.dsp.yorn$ = "N"
	return
	fend
