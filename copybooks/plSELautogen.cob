*>
*>    For PL & taken from file-026
*>
     select  Agen-Invoice-File    assign        file-30
                                  access        dynamic
                                  organization  indexed
                                  status        fs-reply
                                  record key    Agen-Invoice-Key.
