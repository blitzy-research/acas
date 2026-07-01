*>  TO BE TESTED ON HP Inktank 7305
*>
*> 2023/02/18 vbc - Added PP-Name and Print-File-Name - Portrait
*> 2024/01/11 vbc - SINGLED SIDED Fit to paper size;
*>                  otherwise use cpi-11.5 12.5 ish pitch
*> 2024/01/14 vbc - Chnaged cpi from 8 to 6 to give 6 lines per inch
*>                  to see if it looks any better.
*>
 01  Print-Report.
     03  filler          pic x(121)     value
     "lpr -r -o 'orientation-requested=3 page-left=21 page-top=24 " &  *> was 48 18mm from top
     "page-right=10 sides=one-sided fit-to-page cpi=12 lpi=6' -P ".
     03  PSN             pic x(48)      value "Smart_Tank_7300 ".
     03  PSN2 redefines PSN
                         pic x(40).
     *> This is the Cups print spool, change it for yours IT MUST HAVE A TRAILING SPACE
     03  PP-Name         pic x(24)      value "prt-1".      *> Don't change this line 18/02/23 was X(15)
*>
 01  PP-Print-File-Name  pic x(24)      value "prt-1".
*>
