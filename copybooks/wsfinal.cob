*>**************************************************
*>                                                 *
*>   Working Storage For The Final Account Record  *
*>                                                 *
*>**************************************************
*> 416 bytes 02/03/09 but written as 1024 (system-record size) 07/11/10
*>    Can we link this one for GL up with IRS??
*> included filler 15/10/25 now = 1024 as created by sys002
*>
 01  Final-Record.
     03  ar1             pic x(16)      occurs  26.
     03  filler          pic x(608).  *> size now 1024 as used in sys002
