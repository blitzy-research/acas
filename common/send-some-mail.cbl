       >>source free
*>
*>  Read purchase ledger manual for details regarding all three send-mail prcesses.
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>

identification division.
 program-id. sendsomemail.

 environment division.
 input-output section.
 data division.
 working-storage section.

 01  mail-to-address                     pic x(64).
 01  mail-subject                        pic x(64).
 01  mail-from-address                   pic x(64).
 01  mail-body                           pic x(256).
 01  mail-command                        pic x(512).
 01  mail-return                         usage binary-long.
 01  Mail-Attachment-Filename            Pic X(64).

 procedure division.
 beginning.


     move "vbcoen@gmail.com"         to mail-to-address.
     move "'Your current Statement from Applewood Computers'"  to mail-subject.
     move "vbcoen@gmail.com"     to mail-from-address.
     move "Your current statement from Applewood Computer is attached.Should you have any problems with this please email admin at: vbcoen@gmail.com. We thank you for your prompt attention."
                                     to mail-body.

*>     move "Your invoice from Applewood Computer is attached.Should you have any problems with this please email admin at: vbcoen@gmail.com. We thank you for your business and we hope to see you again soon."
*>                                     to mail-body.

     move "/home/vince/tmp/test.pdf" to mail-attachment-filename.

     string "echo '"
         function TRIM (mail-body TRAILING)
            "' | mailx -r "
         function TRIM (mail-from-address TRAILING)
            "-s "
         function TRIM (mail-subject TRAILING)
        " -a "
          function TRIM (mail-attachment-filename TRAILING)
         " "
          function TRIM (mail-to-address TRAILING)
              x"00" DELIMITED BY SIZE
            into mail-command.

     call "system" using mail-command
                   returning mail-return.
     if  mail-return not = zeros
          display mail-return
          stop "Read and hit return".
*>
     goback.
