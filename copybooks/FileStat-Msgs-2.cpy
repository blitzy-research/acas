*> ***************************************************************
*> ** Author: Gary L. Cutler                                    **
*> **         CutlerGL@gmail.com                                **
*> ** Amendments Vincent B. Coen                                **
*> **         vbcoen@gmail.com                                  **
*> **                                                           **
*> ** This copybook defines an EVALUATE statement capable of    **
*> ** translating two-digit FILE-STATUS codes to a message.     **
*> **                                                           **
*> ** Use the REPLACING option to COPY to change the names of   **
*> ** the MSG and STATUS identifiers to                         **
*> ** the names your program needs.                             **
*> Such as replacing STATUS by fs-reply msg by exception-msg.   **
*>                                                              **
*> ** chg 09/08/23 vbc for missing statuses                     **
*> ** Chg 11/12/23 vbc for missing statuses                     **
*> ** Chg 10/04/25 vbc match all quotes & spacing/layout        **
*> ** chg to FREE format                                        **
*> ** Chg 24/08/25 vbc #91 description.                         **
*> ** Chg 15.11.25 vbc Replace all ' for "                      **
*> ***************************************************************
*>
     EVALUATE STATUS
          WHEN "00" MOVE "Success                  " TO MSG
          WHEN "02" MOVE "Success Duplicate        " TO MSG
          WHEN "04" MOVE "Success Incomplete       " TO MSG
          WHEN "05" MOVE "Success Optional, Missing" TO MSG
          when "06" move "Multiple Records LS      " TO MSG
          WHEN "07" MOVE "Success No Unit          " TO MSG
          when "09" move "Success LS Bad Data      " TO MSG
          WHEN "10" MOVE "End Of File              " TO MSG
          WHEN "14" MOVE "Out Of Key Range         " TO MSG
          WHEN "21" MOVE "Key Invalid              " TO MSG
          WHEN "22" MOVE "Key Exists               " TO MSG
          WHEN "23" MOVE "Key Not Exists           " TO MSG
          WHEN "24" MOVE "Key Boundary violation   " TO MSG
          WHEN "30" MOVE "Permanent Error          " TO MSG
          WHEN "31" MOVE "Inconsistent Filename    " TO MSG
          WHEN "34" MOVE "Boundary Violation       " TO MSG
          WHEN "35" MOVE "File Not Found           " TO MSG
          WHEN "37" MOVE "Permission Denied        " TO MSG
          WHEN "38" MOVE "Closed With Lock         " TO MSG
          WHEN "39" MOVE "Conflict Attribute       " TO MSG
          WHEN "41" MOVE "Already Open             " TO MSG
          WHEN "42" MOVE "Not Open                 " TO MSG
          WHEN "43" MOVE "Read Not Done            " TO MSG
          WHEN "44" MOVE "Record Overflow          " TO MSG
          WHEN "46" MOVE "Read Error               " TO MSG
          WHEN "47" MOVE "Input Denied             " TO MSG
          WHEN "48" MOVE "Output Denied            " TO MSG
          WHEN "49" MOVE "I/O Denied               " TO MSG
          WHEN "51" MOVE "Record Locked            " TO MSG
          WHEN "52" MOVE "End-Of-Page              " TO MSG
          WHEN "57" MOVE "I/O Linage               " TO MSG
          WHEN "61" MOVE "File Sharing Failure     " TO MSG
          WHEN "71" MOVE "Bad Character LS         " TO MSG
          WHEN "91" MOVE "Feature Not Available    " TO MSG
          WHEN OTHER
                  MOVE "Unknown File Status      " TO MSG
*>
     END-EVALUATE.

