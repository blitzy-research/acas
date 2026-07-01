REM	DEC.  28, 1979	    --------------------------------------------
REM
REM    EQUATES NECESSARY FOR THE DMS SYSTEM (EXCLUDING CRT CHARACTERISTICS)
REM    STANDARD
REM-----------------------------------------------------------------------
%nolist
req.valid%=1: req.stopit%=2:	 req.cr%=3: req.back%=4: req.cancel%=5
req.next%= 6: req.save%=  7: req.adding%=8: req.delete%=9
asc.lspace%=8:	asc.refresh%= 18: asc.cr%=13: asc.del%= 127 :asc.quote%= 34

ctl.stopit$= chr$(27):	 ctl.cr$= chr$(13):    ctl.back$= chr$(2)
ctl.cancel$= chr$(24):	 ctl.next$= chr$(14):  ctl.save$= chr$(19)
ctl.adding$= chr$(1) :	 ctl.delete$=chr$(4)
crt.ctl.tbl$= ctl.stopit$+ctl.cr$+ctl.back$+ctl.cancel$+ctl.next$+ \
	      ctl.save$+ctl.adding$+ctl.delete$
dim crt.ctl.mask$(6)
crt.ctl.mask$(1)= ctl.stopit$
crt.ctl.mask$(2)= crt.ctl.mask$(1)+ctl.cr$+ctl.back$
crt.ctl.mask$(3)= crt.ctl.mask$(2)+ctl.cancel$
crt.ctl.mask$(4)= crt.ctl.mask$(2)+ctl.next$+ctl.save$+ctl.adding$
crt.ctl.mask$(5)= crt.ctl.mask$(4)+ctl.delete$
crt.ctl.mask$(6)= crt.ctl.mask$(2)+ctl.next$

crt.strnum%=1: crt.brktsgn%=2: crt.used%= 4:
crt.brt%=   8: crt.io%=     16

dim crt.sgn.fmt$(7)
crt.sgn.fmt$(1)= "#"
crt.sgn.fmt$(2)= "##"
crt.sgn.fmt$(3)= "###"
crt.sgn.fmt$(4)= "#,###"
crt.sgn.fmt$(5)= "##,###"
crt.sgn.fmt$(6)= "###,###"
crt.sgn.fmt$(7)= "#,###,###"

dim crt.brkt.fmt$(7)		    ,crt.pad.fmt$(7)
crt.brkt.fmt$(1)= "<#"              :crt.pad.fmt$(1)= " #"
crt.brkt.fmt$(2)= "<##"             :crt.pad.fmt$(2)= " ##"
crt.brkt.fmt$(3)= "<###"            :crt.pad.fmt$(3)= " ###"
crt.brkt.fmt$(4)= "<#,###"          :crt.pad.fmt$(4)= " #,###"
crt.brkt.fmt$(5)= "<##,###"         :crt.pad.fmt$(5)= " ##,###"
crt.brkt.fmt$(6)= "<###,###"        :crt.pad.fmt$(6)= " ###,###"
crt.brkt.fmt$(7)= "<#,###,###"      :crt.pad.fmt$(7)= " #,###,###"

dim crt.sgn.rd.fmt$(4)
crt.sgn.rd.fmt$(1)=".#"
crt.sgn.rd.fmt$(2)=".##"
crt.sgn.rd.fmt$(3)=".###"
crt.sgn.rd.fmt$(4)=".####"

dim crt.brkt.rd.fmt$(4),	crt.pad.rd.fmt$(4)
crt.brkt.rd.fmt$(1)=".#>"       :crt.pad.rd.fmt$(1)=".# "
crt.brkt.rd.fmt$(2)=".##>"      :crt.pad.rd.fmt$(2)=".## "
crt.brkt.rd.fmt$(3)=".###>"     :crt.pad.rd.fmt$(3)=".### "
crt.brkt.rd.fmt$(4)=".####>"    :crt.pad.rd.fmt$(4)=".#### "

crt.order.row.col% = -1
crt.order.col.row% = 0
crt.sca.decimal% = 1
crt.sca.hex% = 0
crt.file% = 20
rem-----------------------------
%list
