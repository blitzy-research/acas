*>
*>  This data is present in ALL ACAS modules.
*>   When testing comlete you can set SW-Testing to zero
*>    to stop the logging file being produced.
*>
 01 ACAS-DAL-Common-data.     *> For DAL processing.
*>
*> log file reporting for testing otherwise zero
*>
     03  SW-Testing               pic 9   value 1.    *>   zero.
         88  Testing-1                    value 1.
*>
*>  Testing only for displays ws-where etc  otherwise zero
*>
     03  SW-Testing-2             pic 9   value zero.
         88  Testing-2                    value 1.
*>
     03  Log-File-Rec-Written     pic 9(6) value zero.    *> in both acas0nn and a DAL.
*>
