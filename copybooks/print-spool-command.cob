*>
*> 2023/02/18 vbc - Added PP-Name and Print-File-Name - Landscape
*>
 01  Print-Report.
     03  filler          pic x(117)     value
     "lpr -r -o 'orientation-requested=4 page-left=21 page-top=24 " &   *> was 48 - 28/4/24 18mm from Top of page
     "page-right=10 sides=two-sided-long-edge cpi=12 lpi=8' -P ".
     03  PSN             pic x(48)      value "Smart_Tank_7300 ".  *> This is the Cups print spool, change it for yours
     03  PP-Name         pic x(24)      value "prt-1".      *> Don't change this line 18/02/23 was X(15)
*>
 01  PP-Print-File-Name  pic x(24)      value "prt-1".
