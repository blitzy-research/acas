*>*************************************************************
*>   Working Storage for the system file versioning data used
*>   in all prime programs : general, sales, purchase, stock
*>    and sys002
*>*************************************************************
*> 18/09/16 vbc - Created to replace standalone versions of
*>                the same. Valid for RDB.
*> 15/01/18 vbc - Added extra field for Stats-Date-Period with a filler.
*>
 77  ws-Sys-Record-Ver-Prime          binary-char value 1.
 77  ws-Sys-Record-Ver-Secondary      binary-char value 4.   *> updated 15/01/18 see wssystem.cob
*>
