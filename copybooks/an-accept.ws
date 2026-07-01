       *>1>>LISTING OFF
      *>
      *> copy book - an-accept.ws compatible for FREE and VARIABLE formats
      *>
       01  AN-ACCEPT-NUMERIC USAGE BINARY-SHORT.
           03  AN-LINE.
           03  AN-COLUMN.
           03  AN-MODE.
               88  AN-MODE-IS-NO-UPDATE          VALUE 0.
               88  AN-MODE-IS-UPDATE             VALUE 1.
           03  AN-FG.
               88  AN-FG-IS-BLACK                VALUE 0.
               88  AN-FG-IS-BLUE                 VALUE 1.
               88  AN-FG-IS-GREEN                VALUE 2.
               88  AN-FG-IS-CYAN                 VALUE 3.
               88  AN-FG-IS-RED                  VALUE 4.
               88  AN-FG-IS-MAGENTA              VALUE 5.
               88  AN-FG-IS-YELLOW               VALUE 6.
               88  AN-FG-IS-WHITE                VALUE 7.
           03  AN-BG.
               88  AN-BG-IS-BLACK                VALUE 0.
               88  AN-BG-IS-BLUE                 VALUE 1.
               88  AN-BG-IS-GREEN                VALUE 2.
               88  AN-BG-IS-CYAN                 VALUE 3.
               88  AN-BG-IS-RED                  VALUE 4.
               88  AN-BG-IS-MAGENTA              VALUE 5.
               88  AN-BG-IS-YELLOW               VALUE 6.
               88  AN-BG-IS-WHITE                VALUE 7.
           03  AN-FG2.
               88  AN-FG2-IS-BLACK               VALUE 0.
               88  AN-FG2-IS-BLUE                VALUE 1.
               88  AN-FG2-IS-GREEN               VALUE 2.
               88  AN-FG2-IS-CYAN                VALUE 3.
               88  AN-FG2-IS-RED                 VALUE 4.
               88  AN-FG2-IS-MAGENTA             VALUE 5.
               88  AN-FG2-IS-YELLOW              VALUE 6.
               88  AN-FG2-IS-WHITE               VALUE 7.
           03  AN-RETURN-CODE.
               88  AN-RETURN-CODE-VIA-ENTER      VALUE 0.
               88  AN-RETURN-CODE-VIA-PFKEY-01   VALUE 01. *> 1001
               88  AN-RETURN-CODE-VIA-PFKEY-02   VALUE 02.
               88  AN-RETURN-CODE-VIA-PFKEY-03   VALUE 03.
               88  AN-RETURN-CODE-VIA-PFKEY-04   VALUE 04.
               88  AN-RETURN-CODE-VIA-PFKEY-05   VALUE 05.
               88  AN-RETURN-CODE-VIA-PFKEY-06   VALUE 06.
               88  AN-RETURN-CODE-VIA-PFKEY-07   VALUE 07.
               88  AN-RETURN-CODE-VIA-PFKEY-08   VALUE 08.
               88  AN-RETURN-CODE-VIA-PFKEY-09   VALUE 09.
               88  AN-RETURN-CODE-VIA-PFKEY-10   VALUE 10.
               88  AN-RETURN-CODE-VIA-PFKEY-11   VALUE 11.
               88  AN-RETURN-CODE-VIA-PFKEY-12   VALUE 12.
               88  AN-RETURN-CODE-VIA-PFKEY-13   VALUE 13.
               88  AN-RETURN-CODE-VIA-PFKEY-14   VALUE 14.
               88  AN-RETURN-CODE-VIA-PFKEY-15   VALUE 15.
               88  AN-RETURN-CODE-VIA-PFKEY-16   VALUE 16.
               88  AN-RETURN-CODE-VIA-PFKEY-17   VALUE 17.
               88  AN-RETURN-CODE-VIA-PFKEY-18   VALUE 18.
               88  AN-RETURN-CODE-VIA-PFKEY-19   VALUE 19.
               88  AN-RETURN-CODE-VIA-PFKEY-20   VALUE 20.
               88  AN-RETURN-CODE-VIA-PFKEY-21   VALUE 21.
               88  AN-RETURN-CODE-VIA-PFKEY-22   VALUE 22.
               88  AN-RETURN-CODE-VIA-PFKEY-23   VALUE 23.
               88  AN-RETURN-CODE-VIA-PFKEY-24   VALUE 24.
               88  AN-RETURN-CODE-VIA-PFKEY-25   VALUE 25.
               88  AN-RETURN-CODE-VIA-PFKEY-26   VALUE 26.
               88  AN-RETURN-CODE-VIA-PFKEY-27   VALUE 27.
               88  AN-RETURN-CODE-VIA-PFKEY-28   VALUE 28.
               88  AN-RETURN-CODE-VIA-PFKEY-29   VALUE 29.
               88  AN-RETURN-CODE-VIA-PFKEY-30   VALUE 30.
               88  AN-RETURN-CODE-VIA-PFKEY-31   VALUE 31.
               88  AN-RETURN-CODE-VIA-PFKEY-32   VALUE 32.
               88  AN-RETURN-CODE-VIA-PFKEY-33   VALUE 33.
               88  AN-RETURN-CODE-VIA-PFKEY-34   VALUE 34.
               88  AN-RETURN-CODE-VIA-PFKEY-35   VALUE 35.
               88  AN-RETURN-CODE-VIA-PFKEY-36   VALUE 36.
               88  AN-RETURN-CODE-VIA-PFKEY-37   VALUE 37.
               88  AN-RETURN-CODE-VIA-PFKEY-38   VALUE 38.
               88  AN-RETURN-CODE-VIA-PFKEY-39   VALUE 39.
               88  AN-RETURN-CODE-VIA-PFKEY-40   VALUE 40.
               88  AN-RETURN-CODE-VIA-PFKEY-41   VALUE 41.
               88  AN-RETURN-CODE-VIA-PFKEY-42   VALUE 42.
               88  AN-RETURN-CODE-VIA-PFKEY-43   VALUE 43.
               88  AN-RETURN-CODE-VIA-PFKEY-44   VALUE 44.
               88  AN-RETURN-CODE-VIA-PFKEY-45   VALUE 45.
               88  AN-RETURN-CODE-VIA-PFKEY-46   VALUE 46.
               88  AN-RETURN-CODE-VIA-PFKEY-47   VALUE 47.
               88  AN-RETURN-CODE-VIA-PFKEY-48   VALUE 48. *> 1048
               88  AN-RETURN-CODE-VIA-PG-UP      VALUE 49. *> 2001
               88  AN-RETURN-CODE-VIA-PG-DOWN    VALUE 50. *> 2002
               88  AN-RETURN-CODE-VIA-TAB        VALUE 51. *> 2007
               88  AN-RETURN-CODE-VIA-BACK-TAB   VALUE 52. *> 2008
               88  AN-RETURN-CODE-VIA-ESCAPE     VALUE 99. *> 2005
           03  AN-ERROR-CODE.
               88  AN-ERROR-OK                   VALUE 0.
               88  AN-ERROR-NOT-EXTENDED-DISPLAY VALUE 4.
               88  AN-ERROR-S-ROW-OUT-OF-SCREEN  VALUE 8.
               88  AN-ERROR-S-COL-OUT-OF-SCREEN  VALUE 12.
               88  AN-ERROR-E-COL-OUT-OF-SCREEN  VALUE 16.
      *>
       *>>>LISTING ON
