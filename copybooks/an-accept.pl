      *>
      *> performed after calling "accept_numeric" routine
      *>
       AN-Test-Status.
           move     zeros to COB-CRT-STATUS.
           evaluate AN-Return-Code
                    when = zero
                             move     zero to COB-CRT-STATUS
                    when > zero and < 49 *> F1 thru F48
                             compute COB-CRT-STATUS = AN-Return-Code + 1000
                    when = 49            *> PAGE-UP - 2001
                             move     2001 to COB-CRT-STATUS
                    when = 50            *> PAGE-DOWN - 2002
                             move     2002 to COB-CRT-STATUS
                    when = 51            *> TAB    - 2007
                             move     2007 to COB-CRT-STATUS
                    when = 52            *> BACK-TAB - 2008
                             move     2008 to COB-CRT-STATUS
                    when = 99            *> ESCAPE - 2005
                             move     2005 to COB-CRT-STATUS
                    when other           *> No Others Coded For
                             move     9000 to COB-CRT-STATUS
           end-evaluate.
      *>
