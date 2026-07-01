*> Copy Book = ACCEPTNM.CPY
*>  For
*> Routine = ACCEPT_NUMERIC.C
*> Version = 1.04
*> Dated  = 2024/03/13
*> Author = Chuck H.
*>
           MOVE :ROW:                  TO AN-LINE
           MOVE :COL:                  TO AN-COLUMN

           CALL     CBL-ACCEPT USING
               BY REFERENCE    :CBL-FLD:
               BY REFERENCE    AN-ACCEPT-NUMERIC.

           EVALUATE TRUE
               WHEN AN-ERROR-CODE NOT = ZERO
                    MOVE     9000   TO COB-CRT-STATUS
               WHEN AN-RETURN-CODE-VIA-ENTER
                    MOVE     ZERO   TO COB-CRT-STATUS
               WHEN AN-RETURN-CODE > 0
                AND AN-RETURN-CODE < 49
                    COMPUTE  COB-CRT-STATUS = AN-RETURN-CODE + 1000
               WHEN AN-RETURN-CODE = 49
                 OR AN-RETURN-CODE = 50
                    COMPUTE  COB-CRT-STATUS = AN-RETURN-CODE + 1952
               WHEN AN-RETURN-CODE = 51
                 OR AN-RETURN-CODE = 52
                    COMPUTE COB-CRT-STATUS = AN-RETURN-CODE + 1956
               WHEN AN-RETURN-CODE-VIA-ESCAPE
                    MOVE     2005   TO COB-CRT-STATUS
               WHEN OTHER
                    MOVE     9000   TO COB-CRT-STATUS
           END-EVALUATE
*>
