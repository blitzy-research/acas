*>*******************************************
*>                                          *
*>  File Definition For PY State Tax File   *
*>                                          *
*>     Covers pyswt (ss), pylwt & pycal(s)  *
*>   ss=state code, s = m,s or H            *
*>  s = Single, M=Married, Head of house    *
*>                                          *
*>   file-54        file-49,50 or 51        *
*>                                          *
*>   Must decide how to deal with this, ie  *
*>   Only one state so ss not needed pycal  *
*>   cal (m,s,h  w neeed for weekly ?       *
*>  And pytax = for UK tax table maybe      *
*>                                          *
*>*******************************************
*>   Record Size 608 Bytes
*>   see wspystax.cob for later updates
*>
 fd  PY-State-Tax-File.   *> Covers for all state tables assuming only one
*>                           is ever in use at any one time for one business.
*>
 copy "wspystax.cob".
*>
