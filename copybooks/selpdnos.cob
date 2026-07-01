*>
*>   Updated 30/04/15 to provide ISAM so that DELETE will work under
*> GC v2.1
*>
     select  del-inv-nos-file  assign        File-23
                               access        dynamic
                               organization  indexed
                               record key    Del-Inv-Nos
                               status        fs-reply.
