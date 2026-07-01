*>
*> 2023/02/18 vbc - Added PP-Name and Print-File-Name - Portrait
*>
 01  Print-Report.
     03  filler          pic x(117)     value
     "lpr -r -o 'orientation-requested=3 page-left=36 page-top=24 " &
     "page-right=24 sides=two-sided-long-edge cpi=12 lpi=8' -P ".
     03  PSN             pic x(48)      value "Smart_Tank_7300 ".  *> This is the Cups print spool, change it for yours
     03  PP-Name         pic x(24)      value "prt-1".      *> Don't change this line 2023-02-18 chngd from 15
*>
 01  PP-Print-File-Name  pic x(24)      value "prt-1".
