       IDENTIFICATION DIVISION.
       PROGRAM-ID. MAKESQLTABLE.
      *AUTHOR. J C CURREY.
      ************************************************************
      *                                                          *
      *      THIS PROGRAM GENERATES THE TSQL SCRIPT TO CREATE    *
      *        A TABLE                                           *
      *                                                          *
      *   VERSION 001--ORIGINAL VERSION                          *
      *                                                          *
      *                 NOVEMBER, 2020--J C CURREY               *
      *                                                          *
      ************************************************************
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.

           SELECT INPUT-FILE ASSIGN TO WS-NAME-INPUT-FILE
             ORGANIZATION IS LINE SEQUENTIAL
             FILE STATUS IS WS-INPUT-FILE-STATUS.

           SELECT OUTPUT-FILE ASSIGN TO WS-NAME-OUTPUT-FILE
             ORGANIZATION IS LINE SEQUENTIAL
             FILE STATUS IS WS-OUTPUT-FILE-STATUS.

       DATA DIVISION.
       FILE SECTION.
      *
       FD  INPUT-FILE.
       01  INPUT-RECORD.
           05  IR-BUFFER                       PIC X(80).

       FD  OUTPUT-FILE.
       01  OUTPUT-RECORD                       PIC X(128).

       WORKING-STORAGE SECTION.
      ****************************************************
      *   CONSTANTS, COUNTERS AND WORK AREAS             *
      ****************************************************
       01  WS-NAME-PROGRAM                     PIC X(18) VALUE
                                                  "makesqltable   001".
       01  WS-NO-PARAGRAPH                     PIC S9(4) COMP.
       01  WS-I                                PIC S9(4) COMP.
       01  WS-J                                PIC S9(4) COMP.
       01  WS-K                                PIC S9(4) COMP.
       01  WS-POSITION-IN-OUTPUT               PIC S9(4) COMP.
       01  WS-NAME-INPUT-FILE                  PIC X(128) VALUE SPACES.
       01  WS-NAME-OUTPUT-FILE                 PIC X(128) VALUE SPACES.
      *  1         2         3         4         5         6         7
      *890123456789012345678901234567890123456789012345678901234567890
       01  WS-INPUT-FILE-STATUS                PIC XX.
       01  WS-OUTPUT-FILE-STATUS               PIC XX.
       01  WS-READ-AREA                        PIC X(80).
       01  WS-NAME-DATA-BASE                   PIC X(30).
       01  WS-REMOVE-PREFIX                    PIC X(10).
       01  WS-TRIMMED-INPUT-RECORD             PIC X(80).
       01  WS-SECOND-TRIM                      PIC X(80).
       01  WS-THIRD-TRIM                       PIC X(80).
       01  WS-TABLE-NAME                       PIC X(64).
       01  WS-COLUMN-NAME                      PIC X(64).
       01  WS-CHARACTERS-WANTED                PIC S9(4) COMP.
       01  WS-ED5                              PIC ZZZZ9.
      ****************************************************************
      *                PROCEDURE DIVISION                            *
      ****************************************************************
       PROCEDURE DIVISION.
       0000-MAIN SECTION.
           PERFORM 1000-INITIALIZATION THRU 1990-EXIT.
           PERFORM 2000-PROCESS THRU 7990-EXIT.
           PERFORM 9000-END-OF-PROGRAM THRU 9990-EXIT.
           STOP RUN.
      ****************************************************************
      *               INITIALIZATION                                 *
      ****************************************************************
       1000-INITIALIZATION.
           MOVE 1000 TO WS-NO-PARAGRAPH.
           DISPLAY "I) ", WS-NAME-PROGRAM, " BEGINNING AT--"
             FUNCTION CURRENT-DATE.
           DISPLAY "A) ENTER INPUT FILE NAME " WITH NO ADVANCING.
           ACCEPT WS-NAME-INPUT-FILE.
           OPEN INPUT INPUT-FILE.
           IF WS-INPUT-FILE-STATUS IS NOT EQUAL TO "00"
             DISPLAY "T) CANNOT OPEN INPUT FILE "
               "STATUS=" WS-INPUT-FILE-STATUS
             STOP RUN.
           DISPLAY "A) ENTER THE FIELD NAME PREFIX TO REMOVE "
             WITH NO ADVANCING.
           ACCEPT WS-REMOVE-PREFIX.
           DISPLAY "A) ENTER OUTPUT FILE NAME " WITH NO ADVANCING.
           ACCEPT WS-NAME-OUTPUT-FILE.
           OPEN OUTPUT OUTPUT-FILE.
           IF WS-OUTPUT-FILE-STATUS IS NOT EQUAL TO "00"
             DISPLAY "T) CANNOT OPEN OUTPUT FILE "
               "STATUS=" WS-OUTPUT-FILE-STATUS
             STOP RUN.
           DISPLAY "A) ENTER DATABASE NAME " WITH NO ADVANCING.
           ACCEPT WS-READ-AREA.
           INSPECT WS-READ-AREA REPLACING ALL "-" BY "_".
           MOVE FUNCTION LOWER-CASE (WS-READ-AREA)
             TO WS-NAME-DATA-BASE.
       1990-EXIT.
           EXIT.
      *
      *    PROCESSING
      *
       2000-PROCESS.
           MOVE 2000 TO WS-NO-PARAGRAPH.
      *
      *    LOOK FOR 01 ENTRY (THERE MUST BE ONE AND ONLY ONE)
      *
       2010-READ.
           MOVE 2010 TO WS-NO-PARAGRAPH.
           READ INPUT-FILE NEXT RECORD
             AT END DISPLAY "T) NO 01 ENTRY FOUND"
                    GO TO 7990-EXIT.
           MOVE FUNCTION TRIM (INPUT-RECORD)
             TO WS-TRIMMED-INPUT-RECORD.
           IF WS-TRIMMED-INPUT-RECORD (1:2) IS EQUAL TO "01"
             THEN NEXT SENTENCE
             ELSE GO TO 2010-READ.
      *
           MOVE SPACES TO WS-TRIMMED-INPUT-RECORD (1:2).
           MOVE FUNCTION TRIM (WS-TRIMMED-INPUT-RECORD)
             TO WS-SECOND-TRIM.
           MOVE SPACES TO WS-TABLE-NAME.
           STRING
             WS-SECOND-TRIM
               DELIMITED BY "."
               INTO WS-TABLE-NAME.
           MOVE SPACES TO OUTPUT-RECORD.
           STRING
             "use "
             FUNCTION TRIM (WS-NAME-DATA-BASE)
             ";"
               INTO OUTPUT-RECORD.
           WRITE OUTPUT-RECORD.
           MOVE SPACES TO OUTPUT-RECORD.
           INSPECT WS-TABLE-NAME REPLACING ALL "-" BY "_".
           STRING
             "DROP TABLE IF EXISTS "
             FUNCTION LOWER-CASE (FUNCTION TRIM (WS-TABLE-NAME))
             ";"
               INTO OUTPUT-RECORD.
           WRITE OUTPUT-RECORD.
           MOVE SPACES TO OUTPUT-RECORD.
           STRING
             "CREATE TABLE `"
             FUNCTION LOWER-CASE (FUNCTION TRIM (WS-TABLE-NAME))
             "` ("
               INTO OUTPUT-RECORD.
           WRITE OUTPUT-RECORD.
           MOVE SPACES TO OUTPUT-RECORD.
           STRING
             "  `key` INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,"
               INTO OUTPUT-RECORD.
           WRITE OUTPUT-RECORD.
           MOVE SPACES TO OUTPUT-RECORD.
      *
      *    NOW LOOK FOR COLUMN DEFINITIONS
      *
       2100-READ-COLUMNS.
           READ INPUT-FILE NEXT RECORD
             AT END GO TO 2900-EOF.
           MOVE FUNCTION TRIM (INPUT-RECORD)
             TO WS-TRIMMED-INPUT-RECORD.
           IF WS-TRIMMED-INPUT-RECORD (1:1) EQUALS "*"
             GO TO 2100-READ-COLUMNS.
           IF WS-TRIMMED-INPUT-RECORD (1:2) EQUALS "01"
             THEN DISPLAY "T) CANNOT HAVE MORE THAN 01 DEFINITION"
                  GO TO 7980-CLOSE.
           IF WS-TRIMMED-INPUT-RECORD (1:2) IS NOT NUMERIC
             THEN DISPLAY "T) INVALID RECORD LISTED BELOW "
                  DISPLAY INPUT-RECORD
                  GO TO 7980-CLOSE.
           MOVE SPACES TO WS-TRIMMED-INPUT-RECORD (1:2).
           MOVE ZERO TO WS-I.
           INSPECT WS-REMOVE-PREFIX TALLYING WS-I
             FOR ALL CHARACTERS BEFORE INITIAL SPACE.
           MOVE 1 TO WS-J.
       2110-PREFIX-LOOP.
           IF WS-REMOVE-PREFIX (1:WS-I) EQUALS
             WS-TRIMMED-INPUT-RECORD (WS-J:WS-I)
               THEN MOVE SPACES TO
                      WS-TRIMMED-INPUT-RECORD (WS-J:WS-I)
                    NEXT SENTENCE
               ELSE ADD 1 TO WS-J
                    IF WS-J IS LESS THAN 80
                      THEN GO TO 2110-PREFIX-LOOP
                    END-IF
           END-IF.
           MOVE FUNCTION TRIM (WS-TRIMMED-INPUT-RECORD)
             TO WS-SECOND-TRIM.
           MOVE SPACES TO WS-COLUMN-NAME.
           MOVE ZERO TO WS-I.
           INSPECT WS-SECOND-TRIM
             TALLYING WS-I FOR ALL CHARACTERS BEFORE " ".
           MOVE WS-SECOND-TRIM (1:WS-I) TO WS-COLUMN-NAME.
           INSPECT WS-COLUMN-NAME REPLACING ALL "-" BY "_".
           MOVE 1 TO WS-POSITION-IN-OUTPUT.
           MOVE SPACES TO OUTPUT-RECORD.
           STRING
             "  `"
             FUNCTION LOWER-CASE (FUNCTION TRIM (WS-COLUMN-NAME))
             "` "
               INTO OUTPUT-RECORD
               WITH POINTER WS-POSITION-IN-OUTPUT.
      *NOW HANDLE THE PIC
           MOVE ZERO TO WS-I.
           INSPECT WS-SECOND-TRIM
             TALLYING WS-I FOR ALL CHARACTERS BEFORE "PIC".
           MOVE SPACES TO WS-THIRD-TRIM.
      *
      *    NOW GET THE REQUIRED DEFINITION
      *
           MOVE WS-SECOND-TRIM (WS-I + 5:) TO WS-THIRD-TRIM.
           IF "X" EQUALS WS-THIRD-TRIM (1:1) GO TO 2200-CHARACTERS.
           GO TO 2215-BAD-PIC.
      *
      *    CHARACTER (STRING) BASED DEFINITION
      *
       2200-CHARACTERS.
           MOVE 2200 TO WS-NO-PARAGRAPH.
           MOVE 1 TO WS-CHARACTERS-WANTED.
           MOVE 2 TO WS-I.
       2210-CHARACTER-LOOP.
           IF WS-THIRD-TRIM (WS-I:1) EQUALS "." GO TO 2240-GOT-COUNT.
           IF WS-THIRD-TRIM (WS-I:1) EQUALS "("
             GO TO 2220-GET-REPITITIONS.
           IF WS-THIRD-TRIM (WS-I:1) EQUALS "X"
             ADD 1 TO WS-CHARACTERS-WANTED
             ADD 1 TO WS-I
             IF WS-I IS LESS THAN 74
               THEN GO TO 2210-CHARACTER-LOOP
             END-IF
           END-IF.
       2215-BAD-PIC.
           DISPLAY "T) INVALID PIC CLAUSE BELOW ".
           DISPLAY INPUT-RECORD.
           GO TO 2900-EOF.
       2220-GET-REPITITIONS.
           MOVE ZERO TO WS-J.
           INSPECT WS-THIRD-TRIM TALLYING WS-J
             FOR ALL CHARACTERS BEFORE INITIAL ")".
           IF WS-J IS GREATER THAN 74 GO TO 2215-BAD-PIC.
           MOVE WS-THIRD-TRIM (WS-I + 1 : WS-J - WS-I)
             TO WS-CHARACTERS-WANTED.
      *
      *    NOW DETERMINE STRING TYPE
      *
       2240-GOT-COUNT.
           IF WS-CHARACTERS-WANTED IS GREATER THAN 255
             GO TO 2250-VARCHAR.
           MOVE WS-CHARACTERS-WANTED TO WS-ED5.
           STRING
             "CHAR("
             FUNCTION TRIM (WS-ED5)
             ") NOT NULL DEFAULT ' ',"
               INTO OUTPUT-RECORD
               WITH POINTER WS-POSITION-IN-OUTPUT.
           WRITE OUTPUT-RECORD.
           MOVE SPACES TO OUTPUT-RECORD.
           GO TO 2100-READ-COLUMNS.
      *
       2250-VARCHAR.
           MOVE WS-CHARACTERS-WANTED TO WS-ED5.
           STRING
             "VARCHAR("
             FUNCTION TRIM (WS-ED5)
             ") NOT NULL DEFAULT ' ',"
               INTO OUTPUT-RECORD
               WITH POINTER WS-POSITION-IN-OUTPUT.
           WRITE OUTPUT-RECORD.
           MOVE SPACES TO OUTPUT-RECORD.
           GO TO 2100-READ-COLUMNS.

       2900-EOF.
           STRING
             "  PRIMARY KEY(`key`)"
               INTO OUTPUT-RECORD.
           WRITE OUTPUT-RECORD.
           MOVE SPACES TO OUTPUT-RECORD.
           MOVE ")" TO OUTPUT-RECORD
           WRITE OUTPUT-RECORD.
           MOVE SPACES TO OUTPUT-RECORD.
           MOVE "ENGINE = MYISAM;" TO OUTPUT-RECORD.
           WRITE OUTPUT-RECORD.
           MOVE SPACES TO OUTPUT-RECORD.

      *
      *    END OF JOB
      *
       7980-CLOSE.
           CLOSE INPUT-FILE.
           CLOSE OUTPUT-FILE.
       7990-EXIT.
           EXIT.
      ****************************************************************
      *             TERMINATION                                      *
      ****************************************************************
       9000-END-OF-PROGRAM.
           MOVE 9000 TO WS-NO-PARAGRAPH.
           DISPLAY "I) " WS-NAME-PROGRAM " COMPLETED NORMALLY AT--"
               FUNCTION CURRENT-DATE.
           STOP RUN.
       9990-EXIT.
           EXIT.
