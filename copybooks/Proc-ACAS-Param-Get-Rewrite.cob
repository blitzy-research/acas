*>
 zz900-Read-System-Param  section.
*>
*> First get system param cobol file
*>
 zz900-Open.
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open-Input.
     if       fs-reply not = zero
              move     "sys002" to ws-called    *> create param file by requested info from user
              call     ws-called using ws-calling-data file-defs
              perform  System-Open
     end-if.
*>
 zz900-Get-System-Recs.
     move     zeros to File-System-Used         *> again in case RDB setup
                       File-Duplicates-In-Use.  *> if sys002 just been run.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Read-Indexed.              *> Read Cobol file params
     if       fs-reply not = zero               *> should NOT happen as done in
              perform System-Close              *> open-system
              move    "sys002" to ws-called     *> create param file by requested info from user
              call     ws-called using ws-calling-data file-defs
              perform  System-Open
              go to zz900-Get-System-Recs
     end-if.
*>
     perform  System-Close.
*>
 zz900-Exit.
     exit     section.
*>
 zz910-Rewrite-System-Param  section.
*>
*> Save to RDB or file.
*>
 zz910-Open.
*> Force RDB processing
     if       File-System-Used NOT = zero
              move     "66" to FA-RDBMS-Flat-Statuses
              move     1 to File-Key-No
              perform  System-Open
              move     1 to File-Key-No
              perform  System-Rewrite
              perform  System-Close
     end-if.
*>
*> Now do the same for the Cobol file.
*>
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.   *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open.                       *> Open cobol file params as I/O
     move     1 to File-Key-No.
     perform  System-Rewrite.                    *> Update Cobol file params
     perform  System-Close.                      *> Close the Cobol param file.
*>
 zz910-Exit.
     exit     section.
