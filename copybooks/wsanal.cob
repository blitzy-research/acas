*>*******************************************
*>                                          *
*>  Record Definition For The Analysis File *
*>                                          *
*>*******************************************
*> 36 bytes 25/3/09
*> 24/07/16 vbc - Taken from fdanal.cob
*>
 01  WS-Analysis-Record.
     03  WS-Pa-Code.
         05  Pa-System     pic x.
         05  Pa-Group.
             07  Pa-First  pic x.
             07  Pa-Second pic x.
     03  Pa-Gl             pic 9(6).
     03  Pa-Desc           pic x(24).
     03  Pa-Print          pic xxx.
