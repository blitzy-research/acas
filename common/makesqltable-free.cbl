       >>SOURCE FREE
 identification division.
 program-id. MAKESQLTABLE.
*>author. j c currey.
*>***********************************************************
*>                                                          *
*>      this program generates the tsql script to create    *
*>        a table                                           *
*>                                                          *
*> 01/11/2020 1.00 J C Currey                               *
*> 27/05/2019 1.01 vbc - Updates for param reading if in    *
*>                       command line and free format.      *
*> 07/12/2022 1.02 vbc - mistyp WS-WS-NAME.. 1 too many -WS *
*>                                                          *
*>***********************************************************
 environment division.
 input-output section.
 file-control.
*>
    select input-file  assign WS-Name-Input-File
                       organization line sequential
                       file status  ws-input-file-status.

    select output-file assign WS-Name-Output-File
                       organization line sequential
                       file status ws-output-file-status.

 data division.
 file section.
*>
 fd  input-file.
 01  input-record.
     05  ir-buffer                       pic x(80).
*>
 fd  output-file.
 01  output-record                       pic x(128).
*>
 working-storage section.
*>***************************************************
*>   constants, counters and work areas             *
*>***************************************************
 01  Ws-Name-Program                     pic x(18) value "makesqltable v1.02".
 01  ws-no-paragraph                     pic s9(4) comp.
 01  ws-i                                pic s9(4) comp.
 01  ws-j                                pic s9(4) comp.
 01  ws-k                                pic s9(4) comp.
 01  ws-position-in-output               pic s9(4) comp.
 01  WS-Name-Input-File                  pic x(128) value spaces.
 01  WS-Name-Output-File                 pic x(128) value spaces.
 01  WS-Input-File-Status                pic xx.
 01  WS-Output-File-Status               pic xx.
 01  WS-Read-Area                        pic x(80)  value spaces.
 01  WS-Name-Data-Base                   pic x(30).
 01  WS-Remove-Prefix                    pic x(10)  value spaces.
 01  WS-Trimmed-Input-Record             pic x(80).
 01  WS-Second-Trim                      pic x(80).
 01  WS-Third-Trim                       pic x(80).
 01  WS-Table-Name                       pic x(64).
 01  WS-Column-Name                      pic x(64).
 01  WS-Characters-Wanted                pic s9(4) comp.
 01  ws-ed5                              pic zzzz9.
*>
*>***************************************************************
*>                procedure division                            *
*>***************************************************************
 procedure division       chaining WS-Name-Input-File
                                   WS-Remove-Prefix
                                   WS-Name-Output-File
                                   WS-Read-Area.
*>
 0000-main section.
     perform  1000-initialization thru 1990-exit.
     perform  2000-process thru 7990-exit.
     perform  9000-end-of-program thru 9990-exit.
     goback.
*>***************************************************************
*>               initialization                                 *
*>***************************************************************
 1000-initialization.
    move 1000 to ws-no-paragraph.
    display "I) ", ws-name-program, " BEGINNING AT--" function current-date.
     if       function upper-case (WS-Name-Input-File) = "-HELP" or "--HELP"
              display "Help on parameters:"
              display " All compulsory"
              display "1. Input File Name"
              display "2. Remove Prefix"
              display "3. Output File Name"
              display "4. Database Name"
              goback.
     if       WS-Name-Input-File (1:10) = spaces
              display "A) ENTER INPUT FILE NAME " with no advancing
              accept WS-Name-Input-File.
     open     input input-file.
     if       ws-input-file-status not = "00"
              display "T) CANNOT OPEN INPUT FILE " "STATUS=" ws-input-file-status
              goback.
     if       WS-Remove-Prefix = spaces
              display "A) ENTER THE FIELD NAME PREFIX TO REMOVE " with no advancing.
              accept WS-Remove-Prefix.
     if       WS-Name-Output-File (1:10) = spaces
              display "A) ENTER OUTPUT FILE NAME " with no advancing.
              accept WS-Name-Output-File.
     open     output output-file.
     if       ws-output-file-status not = "00"
              display "T) CANNOT OPEN OUTPUT FILE " "STATUS=" ws-output-file-status
              close input-file
                    output-file
              goback.
    if        WS-Read-Area (1:10) = spaces
              display "A) ENTER DATABASE NAME " with no advancing
              accept ws-read-area.
*>
*> All parameters accepted in if not included in command line
*>
    inspect ws-read-area replacing all "-" by "_".
    move function upper-case (ws-read-area) to ws-name-data-base.            *> changed from lower
*>
 1990-exit.
     exit.
*>
*>    Processing
*>
 2000-process.
    move 2000 to ws-no-paragraph.
*>
*>    look for 01 entry (there must be one and only one)
*>
 2010-read.
    move 2010 to ws-no-paragraph.
    read input-file next record
      at end display "T) NO 01 ENTRY FOUND"
             go to 7990-exit.
    move function trim (input-record)
      to ws-trimmed-input-record.
    if ws-trimmed-input-record (1:2) is equal to "01"
      then next sentence
      else go to 2010-read.
*>
    move spaces to ws-trimmed-input-record (1:2).
    move function trim (ws-trimmed-input-record)
      to ws-second-trim.
    move spaces to ws-table-name.
    string
      ws-second-trim
        delimited by "."
        into ws-table-name.
    move spaces to output-record.
    string
      "use "
      function trim (ws-name-data-base)
      ";"
        into output-record.
    write output-record.
    move spaces to output-record.
    inspect ws-table-name replacing all "-" by "_".
    string
      "DROP TABLE IF EXISTS "
      function lower-case (function trim (ws-table-name))
      ";"
        into output-record.
    write output-record.
    move spaces to output-record.
    string
      "CREATE TABLE `"
      function lower-case (function trim (ws-table-name))
      "` ("
        into output-record.
    write output-record.
    move spaces to output-record.
    string
      "  `key` INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,"
        into output-record.
    write output-record.
    move spaces to output-record.
*>
*>    now look for column definitions
*>
 2100-read-columns.
    read input-file next record
      at end go to 2900-eof.
    move function trim (input-record)
      to ws-trimmed-input-record.
    if ws-trimmed-input-record (1:1) equals "*"
      go to 2100-read-columns.
    if ws-trimmed-input-record (1:2) equals "01"
      then display "T) CANNOT HAVE MORE THAN 01 DEFINITION"
           go to 7980-close.
    if ws-trimmed-input-record (1:2) is not numeric
      then display "T) INVALID RECORD LISTED BELOW "
           display input-record
           go to 7980-close.
    move spaces to ws-trimmed-input-record (1:2).
    move zero to ws-i.
    inspect ws-remove-prefix tallying ws-i
      for all characters before initial space.
    move 1 to ws-j.
 2110-prefix-loop.
    if ws-remove-prefix (1:ws-i) equals
      ws-trimmed-input-record (ws-j:ws-i)
        then move spaces to
               ws-trimmed-input-record (ws-j:ws-i)
             next sentence
        else add 1 to ws-j
             if ws-j is less than 80
               then go to 2110-prefix-loop
             end-if
    end-if.
    move function trim (ws-trimmed-input-record)
      to ws-second-trim.
    move spaces to ws-column-name.
    move zero to ws-i.
    inspect ws-second-trim
      tallying ws-i for all characters before " ".
    move ws-second-trim (1:ws-i) to ws-column-name.
    inspect ws-column-name replacing all "-" by "_".
    move 1 to ws-position-in-output.
    move spaces to output-record.
    string
      "  `"
      function lower-case (function trim (ws-column-name))
      "` "
        into output-record
        with pointer ws-position-in-output.
*>
*> Now handle the pic
*>
    move zero to ws-i.
    inspect ws-second-trim
      tallying ws-i for all characters before "PIC".
    move spaces to ws-third-trim.
*>
*>   Now get the required definition
*>
    move ws-second-trim (ws-i + 5:) to ws-third-trim.
    if "X" equals ws-third-trim (1:1) go to 2200-characters.
    go to 2215-bad-pic.
*>
*>    Character (string) based definition
*>
 2200-characters.
    move 2200 to ws-no-paragraph.
    move 1 to ws-characters-wanted.
    move 2 to ws-i.
 2210-character-loop.
    if ws-third-trim (ws-i:1) equals "." go to 2240-got-count.
    if ws-third-trim (ws-i:1) equals "("
      go to 2220-get-repititions.
    if ws-third-trim (ws-i:1) equals "X"
      add 1 to ws-characters-wanted
      add 1 to ws-i
      if ws-i is less than 74
        then go to 2210-character-loop
      end-if
    end-if.
 2215-bad-pic.
    display "T) INVALID PIC CLAUSE BELOW ".
    display input-record.
    go to 2900-eof.
 2220-get-repititions.
    move zero to ws-j.
    inspect ws-third-trim tallying ws-j for all characters before initial ")".
    if ws-j is greater than 74 go to 2215-bad-pic.
    move ws-third-trim (ws-i + 1 : ws-j - ws-i) to ws-characters-wanted.
*>
*>    Determine string type
*>
 2240-got-count.
    if ws-characters-wanted is greater than 255
      go to 2250-varchar.
    move ws-characters-wanted to ws-ed5.
    string
      "CHAR("
      function trim (ws-ed5)
      ") NOT NULL DEFAULT ' ',"
        into output-record
        with pointer ws-position-in-output.
    write output-record.
    move spaces to output-record.
    go to 2100-read-columns.
*>
 2250-varchar.
    move ws-characters-wanted to ws-ed5.
    string
      "VARCHAR("
      function trim (ws-ed5)
      ") NOT NULL DEFAULT ' ',"
        into output-record
        with pointer ws-position-in-output.
    write output-record.
    move spaces to output-record.
    go to 2100-read-columns.

 2900-eof.
    string
      "  PRIMARY KEY(`key`)"
        into output-record.
    write output-record.
    move spaces to output-record.
    move ")" to output-record
    write output-record.
    move spaces to output-record.
    move "ENGINE = MYISAM;" to output-record.
    write output-record.
    move spaces to output-record.

*>
*>    End Of Job
*>
 7980-close.
    close input-file.
    close output-file.
 7990-exit.
    exit.
*>***************************************************************
*>             termination                                      *
*>***************************************************************
 9000-end-of-program.
    move 9000 to ws-no-paragraph.
    display "I) " ws-name-program " COMPLETED NORMALLY AT--"
        function current-date.
     goback.
 9990-exit.
    exit.
