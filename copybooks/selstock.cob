*>
*>
*> 26/01/25 vbc - .01 Added new alt key Location for st030 report by location
*>
     select  Stock-File      assign               File-11
                             access               dynamic
                             organization         indexed
                             status               Fs-Reply
                             record key           Stock-Key
                             alternate record key Stock-Abrev-Key
                             alternate record key Stock-Desc      with duplicates
                             alternate record key Stock-Location  with duplicates. *> New 26/1/25.
