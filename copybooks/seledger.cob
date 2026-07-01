*> 29/01/18 added alt key but rem'd out as only found in use in gl030
*>   so will create a table by name and sort it.
*> IF FOUND IN USE IN OTHER PROGRAMS WILL RECONSIDER.
*>
     select  Ledger-File     assign               File-5
                             access               dynamic
                             organization         indexed
                             status               fs-reply
                             record key           Ledger-Key .
 *>                            alternate record key Ledger-Name with
 *>                                                  duplicates.
*>

