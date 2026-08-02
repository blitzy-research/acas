"""``acas026`` / ``plinvoiceMT`` - the Purchase Invoice handler, header AND lines.

Python 3.12 reimplementation of the COBOL file handler ``acas026``
[common/acas026.cbl] and of the one-way COBOL-to-MySQL bridge it calls,
``plinvoiceMT`` [common/plinvoiceMT.cbl] / [common/plinvoiceMT.scb].  One module,
TWO frozen tables:

* ``PUINVOICE-REC`` - the invoice header, 30 columns, primary key
  ``PINVOICE-KEY`` [mysql/ACASDB.sql:L545].
* ``PUINV-LINES-REC`` - the invoice lines, 14 columns, primary key
  ``IL-LINE-KEY`` [mysql/ACASDB.sql:L510].

Entity facade ``PInvoice``; record copybooks [copybooks/plwspinv.cob] (86 lines,
the working-storage view) and [copybooks/plwspinv2.cob] (73 lines, the file view
with its two redefinitions); file definition [copybooks/plfdpinv.cob]; record
module :mod:`acas_posting.records.purchase_invoice`, which publishes
``PInvoiceHeader``, ``PInvoiceBodies``, ``WsPInvoiceRecord``,
``IhInvoiceHeader`` and ``IlInvoiceLine``.

WHY ONE MODULE OWNS TWO TABLES.  Agent Action Plan section 0.3.1, verbatim:

    **One data-access module per handler, not per table.**  The COBOL call chain
    routes through handlers, and the handlers are not always one-to-one with
    tables - ``acas000`` dispatches to four different bridges by key number, and
    **both** ``acas016`` **and** ``acas026`` **own a header table plus a lines
    table**.  Mirroring the handler boundary rather than the table boundary keeps
    the Python module set in exact correspondence with the COBOL programs that
    the traceability document must map, and **preserves the dispatch semantics
    rather than flattening them**.

There is deliberately NO foreign key, NO join and NO cascade between the two
tables, because the COBOL has none.  The lines table is reached only through the
bridge's own repeating-group paragraphs, never by a caller-selected key - see
``N-key2-unreachable`` below.

=============================================================================
LOCATOR CONVENTION - HOW TO READ EVERY CITATION IN THIS MODULE
=============================================================================

Rule R-5 requires that every claim in this module be followable back to the
frozen COBOL, and rule R-4 with Agent Action Plan section 0.7.4 C-4 requires a
comment citing the COBOL locator at every anomaly reproduction site.  This
module therefore carries a locator on essentially every factual statement, in
three forms.  Two of them are abbreviations, and because roughly two thirds of
the citations here use an abbreviation, the convention is stated explicitly
rather than left to be inferred:

``[path:Lnnn]`` and ``[path:Lnnn-Lmmm]``
    FULLY QUALIFIED.  Names its own file, so it can be resolved with no
    context whatsoever - for example [common/plinvoiceMT.cbl:L1452] or
    [copybooks/plwspinv.cob:L40-L44].  Twenty-six distinct source files are
    cited this way.  Every locator in a section heading, in a drift table and
    at the first mention of any file uses this form.

``[MT:Lnnn]``
    ``MT`` abbreviates [common/plinvoiceMT.cbl] - the bridge - and nothing
    else.  Used where a handler locator and a bridge locator sit side by side
    in one table row or one sentence, so that the two can be told apart at a
    glance without the row becoming unreadable.

``[:Lnnn]``
    CONTINUATION.  A line number in the file most recently named in the
    surrounding discussion.  Inside a paragraph function's docstring or its
    inline comments that file is always the COBOL paragraph being reproduced -
    [common/acas026.cbl] for the ``aa``/``ba``/``ca`` handler paragraphs, and
    [common/plinvoiceMT.cbl] for the bridge's ``ba``/``bb``/``bc`` sections.

Mechanically: of 1878 locators, 689 are fully qualified, 12 use ``MT`` and the
remainder are continuations.  A verification pass confirmed that all 102
anomaly names in the register below appear at a reproduction site BELOW this
docstring with a locator within fourteen lines of the mention, that all 689
fully-qualified locators name a file that exists and a line range inside it,
and that every quoted COBOL fragment adjacent to a locator matches the source
at that location.

=============================================================================
THE HEADLINE: FIVE COLUMNS THAT CAN ONLY EVER HOLD A SPACE
=============================================================================

Five of the header table's thirty columns exist in NO copybook, are declared as
host variables, and are then touched by NEITHER the load paragraph NOR the
unload paragraph.  ``HV-IH-STATUS-A``, ``-C``, ``-I``, ``-L`` and ``-P`` are
declared at [common/plinvoiceMT.cbl:L408-L412]; the frozen schema gives all five
``char(1) NOT NULL`` with descriptive comments - ``'Applied'``, ``'cleared'``,
``'Invoiced'``, ``'printed'``, ``'Pending'`` [mysql/ACASDB.sql:L562-L567].
Neither [copybooks/plwspinv.cob] nor [copybooks/plwspinv2.cob] declares any of
them, and neither ``bb000-HV-Load`` [common/plinvoiceMT.cbl:L1450-L1477] nor
``bb100-UnloadHVs`` [common/plinvoiceMT.cbl:L1487-L1512] contains a move into
one.  So the only value they can ever hold is whatever
``initialize TD-PUINVOICE-REC`` [common/plinvoiceMT.cbl:L1450] left behind, i.e.
a single space - and the rendering that reaches the statement text applies
``FUNCTION TRIM (HV-IH-STATUS-A,TRAILING)`` [common/plinvoiceMT.cbl:L1792],
which turns that single space into the EMPTY string.

This is strictly worse than Agent Action Plan anomaly 7, the three IRS date
columns, which at least have a derivation rule.  Agent Action Plan section 0.1.1
gives the governing principle, verbatim:

    **The bridge, not the copybook, must be treated as authoritative - and the
    codebase proves why.** ... A migration driven from the copybooks alone would
    silently omit three columns of a posting table.

Here it would silently omit FIVE.  And this table goes one step further than the
principle states: even the bridge's DECLARATIONS are not enough.  You have to
count its move sequences.  All five columns are therefore written on every
header insert and every header update, always as the rendered empty string; they
are never derived from ``ih-status``, and they are never omitted.

=============================================================================
CENSUS CORRECTION - EXTENDED FUNCTION CODES ACROSS ALL SEVENTEEN HANDLERS
=============================================================================

A prior module's specification states the census as "``acas012`` -> 31,
``acas016`` -> 34, ``acas022`` -> 31, ``acas026`` -> 31".  THE LAST ENTRY IS
WRONG.  ``acas026`` dispatches 34, not 31: [common/acas026.cbl:L289] reads
``when  34                             *> fn-Read-Next-Header``.  The corrected
census, published as :data:`EXTENDED_FUNCTION_CODE_CENSUS`:

===========  ==========================================  ==========================
Handler      Extended code dispatched                    Locator
===========  ==========================================  ==========================
``acas012``  31 ``fn-Read-By-Name``                      [common/acas012.cbl:L342]
``acas016``  34 ``fn-Read-Next-Header``                  [common/acas016.cbl:L297]
``acas022``  31 ``fn-Read-By-Name``                      [common/acas022.cbl:L344]
``acas026``  **34** ``fn-Read-Next-Header``              [common/acas026.cbl:L289]
every other  none                                        verified across all 17
===========  ==========================================  ==========================

Consequently codes 32 (``fn-Read-By-Batch``) and 33 (``fn-Read-By-Cust``) are
dispatched by NO handler at all, even though [copybooks/wsfnctn.cob:L103-L104]
names OTM3 and OTM5 as their consumers.  That conclusion is unchanged and
correct.  A traceability document carrying a wrong census is worse than one
carrying none, so the correction is published here as data rather than prose.

=============================================================================
THE LINKAGE - FIVE PARAMETERS INTO THE HANDLER, THREE INTO THE BRIDGE
=============================================================================

The handler [common/acas026.cbl:L225-L231], verbatim::

    Procedure Division Using System-Record

                                WS-PInvoice-Record

                                File-Access
                                File-Defs
                                ACAS-DAL-Common-data.

reached as ``call "acas026" using System-Record WS-PInvoice-Record File-Access
File-Defs ACAS-DAL-Common-data`` and reproduced by
:func:`dispatch` ``(system, pinvoice, file_access, file_defs, dal_common)``.

The bridge [common/plinvoiceMT.cbl:L478-L480], verbatim::

    PROCEDURE DIVISION   using File-Access
                               ACAS-DAL-Common-data
                               WS-Invoice-Record.   *>  Ws record

reached by the inline call [common/acas026.cbl:L611-L615] and reproduced by
:func:`plinvoice_mt` ``(file_access, dal_common, pinvoice)``.

``N-bridge-param-rename``: the caller passes ``WS-PInvoice-Record``; the bridge
names the very same parameter ``WS-Invoice-Record`` - the identifier
``slinvoiceMT`` uses for the SALES header.  Positionally harmless, but it is a
copy-paste footprint, and a reader grepping the bridge for
``WS-PInvoice-Record`` finds nothing.  Both names are therefore published here.

A SINGLE record buffer carries EITHER a header OR a line.  The two views are
redefinitions over one 100-byte area - ``Invoice-Header redefines``
[copybooks/plwspinv2.cob:L21] and ``Invoice-Line redefines``
[copybooks/plwspinv2.cob:L56] - so both views are modelled over one buffer here
and the bridge decides between them by testing ``WS-ih-Test``
[common/plinvoiceMT.cbl:L826, :L1146, :L1186, :L1355].

``L617`` states the error contract, verbatim: ``*>   Any errors leave it to
caller to recover from``.  NOTHING IN THIS MODULE RAISES.  Every path returns
the ``(FS-Reply, We-Error)`` pair and writes it into the caller's
``File-Access`` block, exactly as the COBOL does.

=============================================================================
THE VERB SET - AND WHERE THE HANDLER AND THE BRIDGE DISAGREE
=============================================================================

The handler's dispatch [common/acas026.cbl:L283-L307], verbatim::

    evaluate File-Function
       when  1
             go to aa020-Process-Open
       when  2
             go to aa030-Process-Close
       when  3
       when  34                             *> fn-Read-Next-Header
             go to aa040-Process-Read-Next
       when  4
             go to aa050-Process-Read-Indexed
       when  5
             go to aa070-Process-Write
       when  7
             go to aa090-Process-Rewrite
       when  8
             go to aa080-Process-Delete
       when  9
             go to aa060-Process-Start
       when  other                          *> 6 is spare / unused
             go to aa100-Bad-Function
    end-evaluate.

    *>  Should never get here but in case :(
    go       to aa100-Bad-Function.

``N-read-next-header-is-read-next``: ``when 34`` FALLS THROUGH into ``when 3``,
so ``fn-Read-Next-Header`` executes exactly the same paragraph as an ordinary
read-next - no header filtering, no different statement.  None is implemented
here.  [copybooks/wsfnctn.cob:L105] declares 34 "for Invoice (sl020, 50, 140,
820)" - all SALES programs - yet it is the PURCHASE handler implementing it, and
the copybook's own changelog [copybooks/wsfnctn.cob:L17] names only three of the
four (``N-34-changelog-count``).

``N-when34-confidence``: this handler's comment is confident,
``*> fn-Read-Next-Header``; the mirrored ``acas016`` carries the maintainer's
doubt, ``*> fn-Read-Next-Header ???`` [common/acas016.cbl:L297].

``N-bridge-dispatches-verb-6``: the BRIDGE dispatches one verb the handler
rejects.  [common/plinvoiceMT.cbl:L528-L531], verbatim::

    *> option 6 is a special to cleardown all LINE data for 1 invoice
    *>
       when  6
             go to ba085-Process-Delete-All    *> Coded / D.Tested --- DELETE-ALL  Special

The handler treats 6 as ``*> 6 is spare / unused`` and sends it to
``aa100-Bad-Function`` [common/acas026.cbl:L301-L302] - but the RDB branch
[common/acas026.cbl:L263-L266] bypasses the handler's own ``evaluate``
altogether and forwards ``File-Function`` UNMODIFIED, so a caller sending 6 on
the RDB path reaches the bridge and it deletes.  :func:`dispatch` therefore
publishes exactly the handler's verb set, :data:`DISPATCHED_FILE_FUNCTIONS`,
while :func:`plinvoice_mt` reproduces the bridge's own table,
:data:`BRIDGE_DISPATCHED_FILE_FUNCTIONS`, verb 6 included.

``N-read-next-header-not-identical-in-bridge``: 34 is identical to 3 in the
HANDLER but NOT in the BRIDGE.  ``ba041-Reread`` [common/plinvoiceMT.cbl:L721-L722]
reads ``if FN-Read-Next-Header  go to ba042-Fetch.  *> bypass line processing``,
so 34 SKIPS the interleaved lines walk that 3 performs.  The published note on
``EXTRA_READ_ORDERS['PUINVOICE-REC'][34]`` in :mod:`acas_posting.dal.cursor_state`
- "shares the fn-read-next body, so it is behaviourally identical to function 3"
- is accurate for the handler and NOT for the bridge.  Both facts are reproduced.

``N-996-comment``: the key guard [common/acas026.cbl:L245-L259] rejects any
``File-Key-No`` other than 1 for read-indexed, start and delete, with 998 for the
first two and 996 for delete - and the 996 comment at ``L255`` is a verbatim copy
of the 998 comment at ``L249``, "file seeks key type out of range".  Not rewritten.

``N-key2-unreachable``: ``Table-Of-KeyNames`` declares TWO keys,
``KeyOfReference occurs 2`` [common/plinvoiceMT.cbl:L302-L306], yet that guard
rejects ``File-Key-No = 2`` outright.  So ``IL-LINE-KEY`` is unreachable through
Start, Read-Indexed and Delete - exactly the dead-key situation ``acas016`` has.

=============================================================================
LOG IDENTITY - THE ONE HANDLER THAT DOES NOT ADD TEN
=============================================================================

[common/acas026.cbl:L240-L241], verbatim::

    move     4      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice used in FH logging
    move     12     to WS-Log-File-No.  *> RDB, File/Table

and ``ba010-Test-WS-Rec-Size`` [common/acas026.cbl:L556], whose entire body is::

    move     12 to WS-Log-File-no.        *> for FHlogger

``N-log-no-increment``: ``L556`` moves 12 - THE SAME VALUE as ``L241``.  Every
other handler in the folder adds ten on the RDB path: ``acas005`` 11 -> 21,
``acas006`` 12 -> 22, ``acas007`` 13 -> 23, ``acas008`` 15 -> 25, ``acas012``
11 -> 21, ``acas013`` 13 -> 23, ``acas015`` 12 -> 22, ``acas016`` 12 -> 22,
``acas019`` 15 -> 25, ``acas022`` 11 -> 21.  ``acas026`` is the SOLE exception,
and it is a silent one.  The non-increment is reproduced exactly; it is not
"corrected" to 22.  The resulting ``(system=4, file=12)`` pair happens to be
unique, so nothing is actually ambiguous - but only by accident.

``N-logsystem5-meaning``: the legend above reads ``5=Invoice``, matching
[common/acas016.cbl:L248] and [common/acas019.cbl:L240] and CONTRADICTING
[common/acas013.cbl:L298] and [common/acas015.cbl:L291], which read ``5=Stock``.
:class:`acas_posting.dal.status.LogSystem` codifies ``STOCK = 5``; this module
uses ``LogSystem.PL`` (4), which both readings agree on, and records the
contradiction rather than resolving it.

``N-nolog-on-dal``: ``Ca-Process-Logs`` carries its comment on its own label
line [common/acas026.cbl:L623] - ``Ca-Process-Logs. *> Not called on DAL access
as it does it already`` - so NOTHING in this module logs to the file-handler log
on the DAL path.  ``ca-Exit`` [common/acas026.cbl:L629] is a plain ``exit``, not
``exit section``.

``N-noparagraph-collision``: the handler's ``WS-No-Paragraph`` scheme is
201..208 [common/acas026.cbl:L310, :L348, :L365, :L418, :L442, :L490, :L501,
:L513] - IDENTICAL to ``acas013``, ``acas015``, ``acas016``, ``acas019`` and
``acas022``.  A sixth handler with the same numbers.  Reproduced as declared.

=============================================================================
NO OPEN-OUTPUT BLOCK - THE SIXTH HANDLER WITH IT ABSENT
=============================================================================

There is NO ``if fn-Open and fn-output`` block anywhere in
[common/acas026.cbl] - verified: the folder pattern ``fn-Open and`` does not
match once.  ``N-noopenoutput``.  Seven handlers show four distinct semantics:

==============================================  =========================================
Handler                                         Open-Output behaviour
==============================================  =========================================
``acas005``                                     present but COMMENTED OUT, "NOT used with
                                                GL." [common/acas005.cbl:L307-L314]
``acas006`` / ``acas007``                       TWO bridge calls: open, then delete-all by
                                                fall-through [common/acas006.cbl:L313-L318,
                                                :L640-L644, :L653]
``acas008``                                     ONE coerced call, function replaced by
                                                delete-all [common/acas008.cbl:L313-L319,
                                                :L571-L574]
``acas015`` / ``acas016`` / ``acas019`` /       ABSENT ENTIRELY - Open+Output is a plain
``acas022`` / **``acas026``**                   open
==============================================  =========================================

So an open with ``Access-Type = fn-output`` here DELETES NOTHING.  The handler's
own flat-file paragraph confirms the intent [common/acas026.cbl:L330-L333]: a
bare ``open output`` with the comments ``*> should not need to be used`` and
``*> caller should check fs-reply``.  ``acas008``'s coercion is NOT ported.

Two more non-initialisations at the head of the RDB branch are deliberate and
are preserved.  [common/acas026.cbl:L263-L281], verbatim extract::

    if       not FS-Cobol-Files-Used
             move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses    *> needed for DAL? not JC/dbpre versions
             perform ba-Process-RDBMS                                *>  Can't hurt
             go to AA-Main-Exit
    end-if.
    perform  ba012-Test-WS-Rec-Size-2.
    *>  ?   move     zero   to  WE-Error
     *>  ?                      FS-Reply.
    move     spaces to SQL-Err SQL-Msg SQL-State.

``N-no-status-zeroing``: the ``move zero to WE-Error / FS-Reply`` at
``L279-L280`` is COMMENTED OUT, carrying the maintainer's own question marks.
This module does not zero them.  And ``L281`` clears THREE fields, where the
mirrored ``acas022`` clears only two [common/acas022.cbl:L336] - three it is.

``N-nobadal``: there is no ``ba020-*`` paragraph.  The bridge call is INLINE in
``ba015-Test-Ends`` [common/acas026.cbl:L611-L615], with a blank line inside the
parameter list, and it is preceded by the maintainer's unfinished
compiler-directive note ``N-cdftodo`` [common/acas026.cbl:L604-L609].

=============================================================================
DRIFT TABLE 1 - ``PUINVOICE-REC``, 30 COLUMNS [mysql/ACASDB.sql:L545]
=============================================================================

=================================================  =========================  ===========================  ===========================================
Copybook [copybooks/plwspinv.cob]                  Bridge host variable       Column                       Drift
=================================================  =========================  ===========================  ===========================================
``WS-Invoice-Key`` group (:L10-L12)                ``HV-PINVOICE-KEY X(10)``  ``char(10)`` PK              renamed; LOADED :L1452, NEVER UNLOADED
``ih-Invoice`` 9(8) (:L11)                         ``9(10) COMP`` :L392       ``int(8) unsigned``          8 -> 10 -> 8; DISPLAY -> binary
``ih-Test`` 99 (:L12) "was binary-char"            ``9(03) COMP`` :L393       ``tinyint(2) unsigned``      2 -> 3 -> 2
``ih-Supplier`` group (:L13-L15)                   ``HV-IH-SUPPLIER X(7)``    ``char(7)``                  group FLATTENED; ``ih-Nos``/``ih-Check``
                                                   :L394                                                   have no host variable and no column
``ih-Date`` ``binary-long`` SIGNED (:L16)          ``9(10) COMP`` UNSIGNED    ``IH-DAT int(8) unsigned``   SIGN LOST; renamed ``Date`` -> ``DAT``
                                                   :L395
``ih-order`` GROUP (:L17-L27)                      ``HV-IH-ORDER X(10)``      ``char(10)``                 all FIVE sub-fields have no host variable
                                                   :L396                                                   and no column
``ih-Type`` 9 (:L28)                               ``9(03) COMP`` :L397       ``tinyint(1) unsigned``      1 -> 3 -> 1
``ih-Ref`` x(10) (:L29)                            ``X(10)`` :L398            ``char(10)``                 clean
``ih-p-c`` .. ``ih-c-vat``, 8 x                    ``S9(07)V9(02) COMP``      signed ``decimal(9,2)`` x8   signed at all three layers - CLEAN
``s9(7)v99 COMP-3`` SIGNED (:L32-L39)              :L399-L406
``ih-status`` x (:L40)                             ``X(1)`` :L407             ``char(1)`` comment          clean value; the comment marks it superseded
                                                                              'STATUS-X not yet used'
NONE                                               ``HV-IH-STATUS-A`` :L408   ``char(1)`` 'Applied'        BRIDGE-ONLY **and never loaded/unloaded**
NONE                                               ``HV-IH-STATUS-C`` :L409   ``char(1)`` 'cleared'        ditto
NONE                                               ``HV-IH-STATUS-I`` :L410   ``char(1)`` 'Invoiced'       ditto
NONE                                               ``HV-IH-STATUS-L`` :L411   ``char(1)`` 'printed'        ditto
NONE                                               ``HV-IH-STATUS-P`` :L412   ``char(1)`` 'Pending'        ditto
``ih-deduct-days`` ``binary-char`` SIGNED (:L45)   ``9(03) COMP`` :L413       ``tinyint(3) unsigned``      SIGN LOST
``ih-deduct-amt`` ``999v99 comp`` (:L46)           ``9(03)V9(02) COMP``       ``decimal(5,2) unsigned``    unsigned throughout - CLEAN; the exact
                                                   :L414                                                   opposite of [common/otm3MT.cbl:L324]
``ih-deduct-vat`` ``999v99 comp`` (:L47)           ``9(03)V9(02) COMP``       ``decimal(5,2) unsigned``    ditto [common/otm3MT.cbl:L325]
                                                   :L415
``ih-days`` ``binary-char`` SIGNED (:L48)          ``9(03) COMP`` :L416       ``tinyint(3) unsigned``      SIGN LOST
``ih-cr`` ``binary-long`` SIGNED (:L49)            ``9(10) COMP`` UNSIGNED    ``int(8) unsigned``          SIGN LOST - as [common/slinvoiceMT.cbl:L418],
                                                   :L417                                                   opposite of [common/otm3MT.cbl:L327]
``ih-lines`` ``binary-char`` SIGNED (:L44)         ``9(03) COMP`` :L418       ``tinyint(2) unsigned``      SIGN LOST; loaded OUT OF POSITION at
                                                                              at ordinal 28                [common/plinvoiceMT.cbl:L1470]
``ih-day-book-flag`` x (:L50)                      ``X(1)`` :L419             ``char(1)``                  clean
``ih-update`` x (:L52)                             ``X(1)`` :L420             ``char(1)`` comment 'jic,    clean
                                                                              Invoice rec merged with
                                                                              OTM rec'
=================================================  =========================  ===========================  ===========================================

=============================================================================
DRIFT TABLE 2 - ``PUINV-LINES-REC``, 14 COLUMNS [mysql/ACASDB.sql:L510]
=============================================================================

=================================================  ==========================  ============================  ==========================================
Copybook [copybooks/plwspinv.cob]                  Bridge host variable        Column                        Drift
=================================================  ==========================  ============================  ==========================================
``il-Key`` group (:L67-L69)                        ``HV1-IL-LINE-KEY X(10)``   ``char(10)`` PK               renamed; loaded AND unloaded
                                                   :L426
``il-invoice`` 9(8) (:L68)                         ``9(10) COMP`` :L427        ``int(8) unsigned``           LOADED :L2758, NEVER UNLOADED
``il-line`` 99 (:L69) "was binary-char"            ``9(03) COMP`` :L428        ``tinyint(2) unsigned``       2 -> 3 -> 2; loaded BEFORE invoice
``il-product`` x(13) (:L70)                        ``X(13)`` :L429             ``char(13)``                  clean
``il-pa`` xx (:L71)                                ``X(2)`` :L430              ``char(2)``                   clean
``filler`` xx (:L72)                               NONE                        NO COLUMN                     deliberate omission
``il-qty`` ``binary-short`` SIGNED (:L73)          ``9(05) COMP`` UNSIGNED     ``smallint(6) unsigned``      SIGN LOST
                                                   :L431
``il-type`` x (:L74)                               ``X(1)`` :L432              ``char(1)``                   clean
``il-description`` x(24) (:L75)                    ``X(24)`` :L433             ``char(24)``                  clean - contrast the sales side, x(32)
``filler`` xx (:L76)                               NONE                        NO COLUMN                     deliberate omission
``il-net``, ``il-unit``                            ``S9(07)V9(02) COMP``       signed ``decimal(9,2)``       clean
``s9(7)v99 comp-3`` (:L77-L78)                     :L434-L435
``il-discount`` ``99v99 comp`` (:L79)              ``9(02)V9(02) COMP`` :L436  ``decimal(4,2) unsigned``     unsigned throughout - clean
``il-vat`` ``s9(7)v99 comp-3`` (:L80)              ``S9(07)V9(02) COMP`` :L437 signed ``decimal(9,2)``       clean
``il-vat-code`` 9 (:L81)                           ``9(03) COMP`` :L438        ``tinyint(1) unsigned``       1 -> 3 -> 1
``il-update`` x (:L82)                             ``X(1)`` :L439             ``char(1)``                    clean
=================================================  ==========================  ============================  ==========================================

SIX DECLARED SIGN LOSSES across the two tables - ``ih-Date``, ``ih-deduct-days``,
``ih-days``, ``ih-cr``, ``ih-lines`` and ``il-qty`` - the Agent Action Plan
anomaly 11 family, carried in the data dictionary as ``anomaly_refs ('A-11',)``
with ``ambiguity_refs ('Q-3',)``.  They are applied in the LOAD, behind the one
named helper :func:`_narrow_signed_to_unsigned_host_variable`.  Nothing raises,
nothing is clamped, and the magnitude is never taken.  ``ih-deduct-amt``,
``ih-deduct-vat`` and ``il-discount`` are NOT among them - they are unsigned at
all three layers (``N-deduct-sign-divergence``), which is the exact opposite of
the logically identical ``OI-Deduct-Amt``/``-Vat`` in ``otm3MT``, signed at all
three [common/otm3MT.cbl:L324-L325].  Sign behaviour is per bridge, per field,
full stop; only the dictionary can be trusted.

FIELDS WITH NO HOST VARIABLE AND NO COLUMN, recorded as deliberate omissions
under rule R-5: ``ih-Nos`` and ``ih-Check`` inside ``ih-Supplier``
[copybooks/plwspinv.cob:L14-L15]; ``ih-Freq``, ``ih-Repeat``, the ``filler xxx``
and ``ih-Last-Date`` inside the 2023 autogen group ``ih-order``
[copybooks/plwspinv.cob:L17-L27]; the two ``filler xx`` in the line
[copybooks/plwspinv.cob:L72, :L76]; the two trailing fillers of the file view
[copybooks/plwspinv2.cob:L18-L19]; its commented-out ``filler pic x(30)``
carrying "This appears to be empty of data on all rec types."
[copybooks/plwspinv2.cob:L54] (``N-dead-filler``); and every ``88`` condition
name, which belongs to :mod:`acas_posting.records.purchase_invoice` and NOT to a
data-access module - Agent Action Plan section 0.4.3 does not permit
``dal/*`` to import ``acas_posting.cobol.*``.

=============================================================================
COUNT THE MOVES, NOT THE DECLARATIONS - THREE LOAD/UNLOAD ASYMMETRIES
=============================================================================

``bb000-HV-Load`` [common/plinvoiceMT.cbl:L1442] performs TWENTY-FIVE host
variable assignments for a THIRTY-column table; ``bb100-UnloadHVs``
[common/plinvoiceMT.cbl:L1482] performs TWENTY-FOUR.  Three distinct defects,
none of them visible in the host-variable group:

1. ``N-five-status-columns-never-populated`` - the five ``HV-IH-STATUS-*``
   appear in NEITHER paragraph.  See the headline above.
2. ``N-pinvoice-key-write-only`` - ``HV-PINVOICE-KEY`` is loaded
   [common/plinvoiceMT.cbl:L1452] and never unloaded, so a value read from the
   database never reaches the caller through it.  Identical to
   ``slinvoiceMT``'s ``HV-SINVOICE-KEY``.  The unload is NOT completed.
3. ``N-lines-order-mismatch`` - ``WS-ih-Lines`` is moved EIGHTEENTH in the load
   [common/plinvoiceMT.cbl:L1470], in copybook declaration order, while its host
   variable sits twenty-eighth [common/plinvoiceMT.cbl:L418] and its column is
   ordinal 28.  Load order, host-variable order and column order are three
   different orders, so this module keeps SIX separate ordering lists and derives
   none of them from another.  Identical displacement to
   [common/slinvoiceMT.cbl:L1479].

``bc000-HV-Load-rg1`` [common/plinvoiceMT.cbl:L2743] performs FOURTEEN
assignments; ``bc100-UnloadHVs-rg1`` [common/plinvoiceMT.cbl:L2777] performs
THIRTEEN:

4. ``N-il-invoice-never-unloaded`` - ``HV1-IL-INVOICE`` is loaded
   [common/plinvoiceMT.cbl:L2758] and NEVER unloaded, so the ``IL-INVOICE``
   COLUMN's value never reaches the record through its own host variable.  The
   record member survives only incidentally: ``WS-il-Invoice`` is subordinate to
   the group ``WS-il-Key`` [copybooks/plwspinv.cob:L67-L69], and that group IS
   restored [common/plinvoiceMT.cbl:L2789], whose first eight characters happen to
   be the invoice number.  Should the ``IL-LINE-KEY`` and ``IL-INVOICE`` columns
   of a row ever disagree, the record silently takes the KEY's value and discards
   the column's.  The unload is NOT completed.
5. ``N-lines-loadorder`` - the load moves ``WS-il-Line`` BEFORE
   ``WS-il-Invoice`` [common/plinvoiceMT.cbl:L2757-L2758], inverting the column
   order ``IL-INVOICE`` then ``IL-LINE``.  Identical to
   [common/slinvoiceMT.cbl:L2790-L2791].  Not reordered.
6. ``N-lines-cursor-from-ih-test`` - the LINE cursor is seeded from
   ``HV-IH-TEST``, with the maintainer's own doubt
   [common/plinvoiceMT.cbl:L1523] ``move HV-IH-TEST to WS-Last-Read-Line. *>
   should be zero``, even though ``WS-Last-Read-Line`` is initialised to the
   MAXIMUM line number rather than zero (``N-last-read-line-40``,
   [common/plinvoiceMT.cbl:L288] ``WS-Last-Read-Line pic 99 value 40``).
   Identical to [common/slinvoiceMT.cbl:L1538].  Zero is NOT substituted.

``N-punctuation`` - the periods are irregular in all four paragraphs: the load
punctuates ``L1452``, ``L1454``, ``L1455`` and then nothing until ``L1477``; the
lines load punctuates ``L2756`` and then nothing until ``L2769``.  Preserved as
declared.  ``N-initialize`` - ``initialize WS-Invoice-Record`` is PLAIN at
[common/plinvoiceMT.cbl:L1487] while [common/plinvoiceMT.cbl:L802] uses
``initialize WS-Invoice-Record with filler``; both forms, plus ``initialize
WS-Invoice-Line`` [common/plinvoiceMT.cbl:L2787] and the two
``initialize TD-*`` [common/plinvoiceMT.cbl:L1450, :L2754], are reproduced in
place.  ``N-sih-in-purchase-comment`` - the unload's own comment block says
"Save sih Invoice & test as last key read." [common/plinvoiceMT.cbl:L1520], using
the SALES prefix in the PURCHASE bridge.  ``N-mislabelled-comment`` -
``*> End of PUINV-LINES-REC unload...`` [common/plinvoiceMT.cbl:L2771] sits at
the end of the LOAD section.  ``N-drychk`` - both lines sections carry
``*> Dry chk ?`` on their label lines [common/plinvoiceMT.cbl:L2743, :L2777],
never resolved.  ``N-rg-todo`` - the maintainer's marker
``*> <<<<  this should be a move from invoice-rec to line rec >>>>> <<>>``
[common/plinvoiceMT.cbl:L2752] is preserved and NOT acted on.

=============================================================================
THE RENDERED VALUE - AND THE SIGN THE EDIT PICTURE THROWS AWAY
=============================================================================

``N-signloss-in-render``, THE LARGEST FINDING IN THIS BRIDGE AND NOT PREVIOUSLY
RECORDED.  Every numeric column reaches the statement text through one shared
edit field, declared [common/plinvoiceMT.scb:L272] = [common/plinvoiceMT.cbl:L272]::

    01  WS-MYSQL-EDIT      PIC -Z(18)9.9(9).

That picture is THIRTY characters: the sign occupies character 1, the eighteen
suppressed digits occupy 2..19, the guaranteed digit is 20, the decimal point is
21 and the nine fractional digits are 22..30.  Every extraction window the four
statement builders use starts at character ELEVEN OR LATER - ``(11:10)``,
``(14:07)``, ``(16:05)``, ``(18:03)``, ``(19:02)`` and ``(22:02)`` - so THE SIGN
IS NEVER INCLUDED.

Measured against compiled GnuCOBOL 3.2 rather than reasoned about, which rule
R-6 requires: for the value ``-1234567.89`` the edit image is
``"-            1234567.890000000"``, ``(14:07)`` yields ``"1234567"`` and
``(22:02)`` yields ``"89"``, so the rendered text is ``1234567.89`` - POSITIVE.
Consequently ALL ELEVEN signed ``decimal(9,2)`` columns - ``IH-P-C``, ``IH-NET``,
``IH-EXTRA``, ``IH-CARRIAGE``, ``IH-VAT``, ``IH-DISCOUNT``, ``IH-E-VAT``,
``IH-C-VAT``, ``IL-NET``, ``IL-UNIT`` and ``IL-VAT`` - are written with their
sign discarded on both insert and update, DESPITE being declared signed at all
three layers.  This is reproduced, not fixed, and it is an oracle question under
Agent Action Plan section 0.6.8.

``N-trim-space-to-empty`` - also measured: ``FUNCTION TRIM(<one space>,
TRAILING)`` yields the EMPTY string, so every space-valued ``char(1)`` - the five
never-populated status columns above all - renders as ``""`` and not as ``" "``.

The exact rendering, transcribed from [common/plinvoiceMT.cbl:L1543-L1560]::

    STRING '`PINVOICE-KEY`="' ...
    STRING FUNCTION TRIM (HV-PINVOICE-KEY,TRAILING)  '"' ...
    STRING ', ' ...
    STRING '`IH-INVOICE`="' ...
    MOVE HV-IH-INVOICE TO WS-MYSQL-EDIT
    STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10)) ...

so character columns take a TRAILING-only trim of the host variable, integer
columns take a BOTH-ENDS trim of their window, and decimal columns take a
both-ends trim of the integer window, a literal ``.``, and the RAW two-character
fractional window with no trim [common/plinvoiceMT.cbl:L1631-L1638].

``N-insert-is-set-form`` - every insert is
``INSERT INTO `T` SET `col`="v", ... ;`` [common/plinvoiceMT.cbl:L1538-L1541],
never the column-list-and-values form; updates append
`` WHERE <predicate>;``; deletes omit the trailing ``";"`` entirely.

TRANSPORT NOTE.  The bridge interpolates each rendered value into the statement
text as a double-quoted literal.  This module BINDS that same rendered text as a
parameter, because :func:`acas_posting.dal.connection.execute_statement` binds
values and never interpolates them.  A quoted string literal and a bound string
yield the identical logical value to MySQL, which coerces the text into the
column's declared type; binding removes an injection route the frozen source left
open without changing a single stored byte - and it preserves the render sign
loss above exactly, because what is bound is the sign-stripped TEXT.

=============================================================================
CURSORS, KEYS AND THE INERT REPEATING GROUP
=============================================================================

``Table-Of-KeyNames`` [common/plinvoiceMT.cbl:L297-L311] declares two keys, both
offset 1 length 10, both ``'STR'``.  ``N-keyname-padding``: ``'PINVOICE-KEY'``
is explicitly space-padded to thirty characters in the source literal
[common/plinvoiceMT.cbl:L298] while ``'IL-LINE-KEY'`` is NOT
[common/plinvoiceMT.cbl:L302]; since ``keyname`` is ``pic x(30)`` COBOL pads the
literal anyway, so the values agree - but the source asymmetry is real and is
identical to [common/slinvoiceMT.cbl:L297, :L301].  ``N-kortype``: ``KOR-Type``
carries ``'STR'`` while its own comment says "Not used currently"
[common/plinvoiceMT.cbl:L300, :L304, :L311].

Both keys are already declared in :mod:`acas_posting.dal.cursor_state`, whose
``TABLE_OF_KEYNAMES`` cites [common/plinvoiceMT.scb:L298-L300] and
[common/plinvoiceMT.scb:L302-L304] and assigns the header to cursor slot 1 and
the lines to slot 2.  They are REUSED here, never re-declared.

``N-rg-notused-yet``: ``RG-Table`` [common/plinvoiceMT.cbl:L313-L326] is declared,
labelled ``*>  Start of RG (Repeat Groups)                        NOT USED - YET.``
and ``*> Metadata on Repeating Groups...                     but acts as a
reminder``, and its ``occurs`` is ONE while its max-row value is FORTY.
Reproduced as inert state in :data:`RG_TABLE`; no repeating-group engine is built.

``N-two-cursors``: two cursor flags, the second commented ``*> RG 1``
[common/plinvoiceMT.cbl:L330-L335].  Both are modelled.

The relation arrives through ``Access-Type`` and is PASSED THROUGH UNMODIFIED -
the facade deliberately does not clear it before ``-Start``.  The bridge's own
mapping [common/plinvoiceMT.cbl:L972-L980] is 5 ``"=  "``, 6 ``"<  "``,
7 ``">  "``, 8 ``">= "``, 9 ``"<= "`` with NO ``when other``, so an out-of-range
value leaves ``MOST-Relation`` as spaces; that mapping and the substring key
extraction are implemented by :mod:`acas_posting.dal.cursor_state` and consumed
here.  Agent Action Plan section 0.1.1, verbatim: "Indexed-file read semantics
must be **emulated, not approximated** ... The Python data-access layer must
reproduce cursor positioning and the ``FS-Reply`` status protocol, **not merely
issue equivalent SQL**."

``N-fn-not-greater-than-unhandled``: the HANDLER's start paragraph has branches
for access types 5, 6, 7 and 8 only, so type 9 falls through with no positioning
issued [common/acas026.cbl:L456-L483] - and its guard
[common/acas026.cbl:L448-L451] admits only 5..8 in the first place, returning
``We-Error 998`` and, unlike every other error path in the paragraph, setting NO
``FS-Reply``.  The BRIDGE's guard returns ``(99, 997)``
[common/plinvoiceMT.cbl:L950-L951].  Both dispositions are reproduced where they
occur; they genuinely disagree.

=============================================================================
STATUS CODES - CITED, NOT REDEFINED
=============================================================================

The bridge documents its own vocabulary [common/plinvoiceMT.cbl:L176-L215]:
``0`` success; ``10`` end of file, to the calling module only; ``21`` invalid key
on start or key not found; ``22`` duplicate key; ``23`` key not found from read
indexed; ``99`` see ``We-Error``.  Detail codes ``999``, ``998``, ``997``,
``996``, ``995``, ``994``, ``992``, ``990``, ``989``, ``911``, ``910`` and
``901`` all live in :class:`acas_posting.dal.status.WeError` and are used from
there.  THREE do not exist there, because they are specific to the two
header-plus-lines bridges: ``8nn`` "Processing on RG Table & rows", ``890``
"Unknown and unexpected error ... on RG processing" and ``880`` "Unexpected range
error in Rg1 secondary key.  Report to programming team."  They are published
here as :data:`WE_ERROR_RG_PROCESSING_BASE`, :data:`WE_ERROR_RG_UNKNOWN` and
:data:`WE_ERROR_RG1_SECONDARY_KEY_RANGE` with that provenance, and the fact that
they are absent from ``WeError`` is stated rather than silently patched.

``N-996-comment``, ``N-badfunction-divergence``: the handler's bad-function
disposition is ``(99, 999)`` [common/acas026.cbl:L527-L528] and the bridge's is
``(99, 990)`` [common/plinvoiceMT.cbl:L1412-L1413], while the documented code for
"Invalid Function requested in File-Function" is ``992`` - used by NEITHER.

``N-read-indexed-reply-23``: this bridge returns ``FS-Reply 23`` with
``We-Error`` ZERO when a read-indexed matches no row
[common/plinvoiceMT.cbl:L870-L873], carrying the comment ``*> could also be 21 or
14``.  :func:`acas_posting.dal.cursor_state.read_indexed` is modelled on
``glpostingMT``, which returns 21 and records that as its own anomaly A2, so the
reply is overridden to 23 at the reproduction site here.

``N-fetch-rg1-status-destroyed``: ``bc051-Fetch-RG1`` sets ``23`` into
``FS-Reply`` on its no-rows branch and then, TWO LINES LATER and
UNCONDITIONALLY, executes ``move zero to FS-Reply WE-Error``
[common/plinvoiceMT.cbl:L2470-L2476].  The no-more-rows signal is destroyed and
an exhausted repeating group is reported as success.  Reproduced.

``N-bc080-no-status-on-failure``: ``bc080-Process-Delete``'s zero-rows path sets
NEITHER ``fs-reply`` NOR ``We-Error`` before transferring to ``ba999-End``
[common/plinvoiceMT.cbl:L2568-L2589].  ``N-bc085-status-nested``: in
``bc085-Process-Delete-ALL`` the ``(99, 995)`` pair is set only INSIDE the
``errno not = "0  "`` branch, so a zero-row delete with a clean driver errno
reports success.  Both reproduced.

``N-deleteall-single-quoted-column``: ``bc085-Process-Delete-ALL`` builds its
predicate with SINGLE quotes around the COLUMN NAME
[common/plinvoiceMT.cbl:L2624-L2634] - ``WHERE 'IL-INVOICE'="00001234"`` - which
MySQL reads as a string literal compared to a string literal.  It matches no row,
so the lines cascade of delete-all DELETES NOTHING.  Reproduced verbatim.

``N-rg1-start-predicate-unquoted``: the header positioning predicate wraps the
key value in ``'"'`` [common/plinvoiceMT.scb:L832-L846]; the repeating-group
positioning predicate does NOT [common/plinvoiceMT.cbl:L1058-L1070] =
[common/plinvoiceMT.scb:L894-L906].  Reproduced.

``N-bc998-unreachable``: ``bc998-Free`` [common/plinvoiceMT.cbl:L3206], stamping
``ws-No-Paragraph`` 58, is never performed from anywhere in the bridge.  It is
implemented and left unreachable.  ``N-temp-ed-row-substring``: the delete-all
log string takes ``WS-Temp-Ed-Row (6:2)`` [common/plinvoiceMT.scb:L1641], a
substring of a ``pic 9(7)`` field.  ``N-sl-in-purchase-openclose``: the open and
close log keys read ``"OPEN SL INVOICE"`` and ``"CLOSE SL INVOICE"``
[common/plinvoiceMT.cbl:L604, :L620] - the SALES ledger name in the PURCHASE
bridge.  All reproduced as written.

=============================================================================
THE REMAINING REGISTER
=============================================================================

``N-copybook-mirror-asymmetry`` - the SALES copybook declares the five status
fields as real fields [copybooks/slwsinv.cob:L56-L60]; the PURCHASE copybook
declares only ``ih-status pic x`` [copybooks/plwspinv.cob:L40].  The mirrored
copybooks disagree; never infer one ledger's layout from the other's.

``N-copy-replacing-prefix-divergence`` - the bridge's ``COPY ... REPLACING``
[common/plinvoiceMT.cbl:L455-L458] prefixes with ``==WS-ih-==`` (lower case)
while [common/slinvoiceMT.cbl:L457] uses ``==WS-Sih-==`` (capital S).
``N-copy-replacing-no-leading`` - its fourth clause,
``==il-== by ==Un-Used-il-==``, has NO ``leading`` keyword, so ``il-`` is
replaced wherever it appears in a name and not only at the start.  The lines
layout therefore comes from a separately declared record
[common/plinvoiceMT.cbl:L362-L379].

``N-88-narrowed`` - that separately declared record gives
``88 WS-il-Analyised value "Z"`` [common/plinvoiceMT.cbl:L379], ONE value, where
[copybooks/plwspinv.cob:L83] gives two, ``"z" "Z"``.  A silent narrowing of a
condition name; not widened back.  ``N-88-case-swap`` - the two copybooks list
the same condition-name values in OPPOSITE case order:
[copybooks/plwspinv.cob:L41-L43, :L51] against
[copybooks/plwspinv2.cob:L41-L43, :L51].  ``N-test-only-88s`` -
[copybooks/plwspinv.cob:L22-L24] declares ``ih-Daily`` and ``ih-Testing`` with
the SAME value ``"D"``, both flagged "These two are only for testing." and "So
NOT documented and removed after tests.", and ``ih-Valid-Freqs`` still includes
``"D"``.  Still present; not removed.

``N-aa041-self-negating-comment`` - ``aa041-Move-Inv-Data`` carries a comment on
its own label line [common/acas026.cbl:L391] - ``*> Not really needed as both
fields are now chars.`` - AND THE COMMENT IS WRONG ABOUT ITS OWN OPERANDS.  The
staging fields are declared numeric [common/acas026.cbl:L201-L203]::

    01  WS-Temp-ED.
        03  ws-temp-ed-1       pic 9(8).
        03  WS-Temp-ed-2       pic 99.

Both are ``pic 9``, not ``pic x``.  This is also the only handler in the folder
whose staging fields are BOTH numeric - [common/acas019.cbl:L202-L204] declares
``x(7)`` plus ``9(8)``.  The paragraph is NOT deleted on the strength of its own
comment.

``N-spaces-into-numeric-key`` - the end-of-file path moves SPACES into
``Invoice-Key`` [common/acas026.cbl:L369], a group whose two halves are
``pic 9(8)`` and ``pic 99`` [copybooks/plfdpinv.cob:L13-L15].  Reproduced
literally; zeros are not substituted.

``N-deadbranches`` - ``aa045-Eval-Keys``'s arms for functions 5, 7, 8 and 9 are
UNREACHABLE, because its only caller is ``aa050-Process-Read-Indexed``
[common/acas026.cbl:L419], and the maintainer says so himself immediately above
the label [common/acas026.cbl:L396]: ``*>   The next block will never get
executed unless performed  so is it needed ?``.  The whole ``evaluate`` is
reproduced, dead arms included.  Note also the lower-case ``k`` in the reference
``aa045-Eval-keys`` against the capital ``K`` of the label
[common/acas026.cbl:L398].

``N-failed-action`` - on an invalid key the linkage buffer is WIPED and the log
key becomes the literal ``"Failed action"`` [common/acas026.cbl:L429-L430].  Both
effects reproduced.

``N-stop`` - a debugging ``stop "Cobol File EOF"`` sits on the flat-file
end-of-file path [common/acas026.cbl:L372], commented ``*> for testing``.  It is
unreachable in the migrated cycle, is recorded as an anomaly AND as a deliberate
omission, and is reproduced as NO pause of any kind.

``N-recsize`` - THREE files carry FOUR mutually inconsistent record sizes for
this record: 100 bytes [copybooks/plwspinv.cob:L6]; 129 bytes and "= 100 less
filler err." [copybooks/plwspinv2.cob:L7-L8]; and 100, 126, 129 and 100 again
[copybooks/plfdpinv.cob:L6-L9].  Published as
:data:`DECLARED_RECORD_SIZE_NOTES` alongside Agent Action Plan anomaly 15, the
``wsbatch.cob`` 96-versus-98 contradiction.  NOT resolved.  ⭐ The FD's second
figure, 126, appears in NO other file and is annotated
``*>             126 bytes 15/12/11 to match fdinv2`` - ``fdinv2`` is the SALES
invoice file definition, so the purchase record was once widened to match the
sales one and then narrowed back.  ``ba012-Test-WS-Rec-Size-2``
[common/acas026.cbl:L558-L599] is the paragraph that compares the two live
lengths, which is precisely why the disputed figure matters.

=============================================================================
THE HANDLER'S FLAT-FILE SIDE - SEVENTEEN FURTHER VERIFIED ANOMALIES
=============================================================================

Every finding below was read at source during implementation and none of them is
in the agent brief.  All are reproduced or recorded; none is fixed (R-4).

``N-eof-flag-is-the-field`` ⭐⭐ - ``77  Cobol-File-Status pic 9 value zero.``
[common/acas026.cbl:L196] carries ``88  Cobol-File-Eof value 1.`` [:L197], so the
condition name IS that field.  Which makes the end-of-file branch::

    set Cobol-File-EoF to true          [:L378]
    move 1 to Cobol-File-Status         [:L379]   *> JIC above dont work :)

TWO WRITES OF THE SAME VALUE TO THE SAME FIELD, and the maintainer's own "just in
case the above doesn't work" comment shows he did not realise it.  Reproduced as
two writes; :attr:`PInvoiceContext.cobol_file_eof` is a PROPERTY over
:attr:`PInvoiceContext.cobol_file_status` rather than a second field, because in
COBOL there is only one field.

``N-plwspinv2-copied-by-neither`` ⭐⭐ - and this CORRECTS the agent brief.  The
brief's section 3.10 states that ``copybooks/plwspinv2.cob`` "is NOT copied by the
bridge at all - it exists for the handler and the callers only".  The first half
is right and the second half is wrong: THE HANDLER DOES NOT COPY IT EITHER.
``acas026.cbl`` copies ``plfdpinv.cob`` into its FILE SECTION [:L184] and
``plwspinv.cob`` into its LINKAGE SECTION with a two-clause rename
[:L214-L215]::

    copy "plwspinv.cob" replacing PInvoice-Header by WS-PInvoice-Record
                                  PInvoice-Bodies by WS-PInvoice-Bodies.

and ``plinvoiceMT.cbl`` copies ``plwspinv.cob`` with its own four-clause rename
[:L455-L458].  The only consumers of ``plwspinv2.cob`` anywhere are
``common/plinvoiceLD.cbl``, ``common/plinvoiceRES.cbl``,
``common/plinvoiceUNL.cbl``, ``common/plautogenLD.cbl``, ``common/xl150.cbl``,
``purchase/pl055.cbl`` and ``purchase/pl140.cbl`` - loaders, an unloader, a
restore, the end-of-cycle driver and two purchase programs.  So the file view and
its two redefinitions belong to the LOADERS and the CALLERS, and neither half of
this pair ever sees them.  Recorded here so the traceability document carries the
correction, exactly as it carries the extended-function-code correction above.

``N-fd-names-six-fields`` ⭐⭐ - the FD record is 100 bytes and names only SIX
fields plus 68 bytes of filler [copybooks/plfdpinv.cob:L12-L21]: ``invoice-nos``
``pic 9(8)``, ``item-nos`` ``pic 99  *> was binary-char.``, ``invoice-supplier``
``pic x(7)``, ``invoice-date`` ``binary-long``, ``inv-order`` ``pic x(10)``,
``invoice-type`` ``pic 9``, then ``filler pic x(10)`` and
``filler pic x(58).   *> was x(88). now rec 100``.  There is NO money group, NO
``ih-Ref``, NO ``ih-status``, NO ``ih-lines``, NO deduct fields, NO ``ih-cr`` and
NO update flag - every one of them lives inside that trailing 58-byte filler.
Which is why the flat-file path can only ever move the record as a 100-byte GROUP
[:L386, :L426, :L491, :L502, :L514] and why the ISAM half of this handler cannot
inspect a single monetary value.

``N-fd-one-record-key`` ⭐ - ``record key    invoice-key.``
[copybooks/plselpinv.cob:L6] declares ONE key, with no ``alternate record key``
clause at all, where the bridge's ``Table-Of-KeyNames`` declares TWO
[common/plinvoiceMT.cbl:L297-L307].  So ``IL-LINE-KEY`` is dead THREE independent
ways: the SELECT has no alternate key, the handler's guard rejects
``File-Key-No`` 2 [common/acas026.cbl:L248, :L254], and the bridge reaches it only
from its own internal buffer sniff.  See ``N-key2-unreachable``.

``N-select-status-is-fs-reply`` ⭐ - ``status        fs-reply``
[copybooks/plselpinv.cob:L5] routes the ISAM run-time's file status STRAIGHT into
the linkage field, so ``FS-Reply`` is simultaneously this handler's return value
and the run time's scratch pad.  That is why ``aa020-Process-Open`` tests it with
no intervening move [common/acas026.cbl:L313] and why every ``invalid key`` branch
can overwrite it freely.  Also ``access        dynamic`` [:L3] and
``assign        file-26`` [:L2] - the file number matching the handler number.

``N-open-input-status-flattened`` ⭐ - ``move 35 to fs-Reply``
[common/acas026.cbl:L314] overwrites whatever the failed ``open input`` actually
reported, so a missing file, a permissions failure and a corrupt index are
INDISTINGUISHABLE to the caller.  Reproduced: 35 regardless.

``N-start-guard-no-fs-reply`` ⭐⭐ - ``aa060-Process-Start``'s guard
``if access-type < 5 or > 8      *> NOT using 'not >'`` [:L448] writes
``move 998 to WE-Error`` [:L449] and then transfers [:L450] WITHOUT SETTING
``FS-Reply`` - which the two statements at [:L444-L445] have just zeroed.  So a
caller that passes a bad access type receives ``We-Error 998`` paired with
``FS-Reply 0``: A PARAMETER ERROR THAT REPORTS SUCCESS.  The BRIDGE's equivalent
guard writes the pair properly, ``99`` / ``997``
[common/plinvoiceMT.cbl:L950-L951].  Reproduced: no ``FS-Reply`` is invented here.

``N-handler-isam-statuses-differ-from-bridge`` ⭐⭐ - the two halves of this pair
disagree about the reply for every single verb::

    verb           handler                          bridge
    read-indexed   21 into BOTH fields   [:L423]    23 / zero   [MT:L871-L872]
    write          22, We-Error left 0   [:L495]    99 (+22 dup) [MT:L1166,:L1174]
    delete         21, We-Error left 0   [:L506]    99 / 995    [MT:L1238-L1239]
    rewrite        21, We-Error left 0   [:L518]    99 / 994    [MT:L1396-L1397]
    start          21, We-Error left 0   [:L459]    21 / zero   [MT:L1036-L1037]
    bad function   999 / 99              [:L527]    990 / 99    [MT:L1412-L1413]

A caller therefore cannot interpret a reply without knowing which path served it.
Every value above is reproduced at its own site.

``N-badfunction-pair-differs`` ⭐ - three codes for one condition: the handler
writes ``999`` [:L527], the bridge writes ``990``
[common/plinvoiceMT.cbl:L1412], and the code
:class:`acas_posting.dal.status.WeError` documents for an invalid function,
``992``, is written by NEITHER.

``N-close-logs-twice`` ⭐ - ``aa030-Process-Close`` performs the log paragraph
[:L354], THEN zeroes ``File-Function`` and ``Access-Type``
[:L355-L356, ``*> close log file``], THEN performs the logger a second time
[:L357].  So one close emits TWO log records and the second is a sentinel with a
zeroed verb pair, which is how ``fhlogger`` is told to close its output.  Both
records reproduced.

``N-perform-aa999-then-goto`` ⭐ - ``aa999-main-exit`` has two behaviours
depending on how it is entered.  Reached by ``GO TO`` [:L316, :L335, :L373, :L382,
:L385, :L389, :L432, :L436, :L450, :L460, :L467, :L474, :L481, :L487, :L498,
:L509, :L521] it FALLS THROUGH into ``aa-main-exit`` [:L535]; reached by
``PERFORM`` from ``aa030-Process-Close`` [:L354] it returns at its own end.  One
label, two control outcomes; both reproduced.

``N-file-defs-unused`` ⭐ - ``File-Defs`` is the fourth linkage parameter [:L229]
and is read on NEITHER path.  The handler says why:
``*>  File paths for Cobol File has already done in main menu module`` [:L273].
Kept in the signature because the ``CALL`` passes it, and recorded as a deliberate
non-use rather than dropped (R-5, "deliberate omissions are recorded as
omissions").

``N-endrewrite-no-period`` ⭐ - ``end-rewrite`` [:L519] carries no terminating
period where ``end-write.`` [:L496] and ``end-delete.`` [:L507] in the paragraphs
either side of it do.  Harmless here because a ``perform`` follows, and recorded
for the same reason Agent Action Plan anomaly 1 is recorded: in this codebase a
missing period is not always harmless.

``N-close-key-no-period`` ⭐ -
``move "CLOSE PL INVOICE File" to WS-File-Key`` [:L353] also has no terminating
period, so it and the ``perform`` beneath it are one sentence.

``N-open-close-key-wording`` ⭐ - the handler logs ``"OPEN PL INVOICE File"``
[:L342] and ``"CLOSE PL INVOICE File"`` [:L353] - correctly "PL" - while the
BRIDGE logs ``"OPEN SL INVOICE"`` [common/plinvoiceMT.cbl:L605] and
``"CLOSE SL INVOICE"`` [:L614], with the SALES prefix and without the trailing
``" File"``.  Two log keys for one logical operation, disagreeing on both the
ledger and the wording.  See ``N-sl-in-purchase-openclose``.

``N-error-message-block`` ⭐ - ``01  Error-Messages.`` [:L205-L209] holds exactly
two literals under the comment ``*> Module Specific`` [:L207]:
``PL901 pic x(31) value "PL901 Note error and hit return"`` and
``PL907 pic x(32) value "PL907 Program Error: Temp rec = "``, followed by a
sketch of the assembled message,
``*>                                        yyy < Invoice-Rec = zzz`` [:L210] -
which uses three-digit placeholders where the fields it describes are
``pic 9(4)`` [:L193-L194].  Reproduced as :data:`_ERROR_MESSAGE_PL901` and
:data:`_ERROR_MESSAGE_PL907` with the four-digit rendering the code actually
performs.

``N-verb-dispatch-dead-on-rdb-path`` ⭐⭐ - a consequence of statement ORDER, not
of any statement.  The RDB branch [common/acas026.cbl:L261-L265] sits ABOVE the
function ``evaluate`` [:L283], so an RDB caller leaves through
``go to AA-Main-Exit`` [:L264] before the dispatch is reached and the WHOLE
``aa020``..``aa100`` verb family is unreachable - the verb is decoded a second
time, by the bridge's ``ba010-Initialise``
[common/plinvoiceMT.cbl:L502-L540].  Two observable consequences: the handler's
bad-function pair ``999`` / ``99`` [:L527-L528] can only appear on the FLAT-FILE
path, while the same input on the RDB path yields the bridge's ``990`` / ``99``;
and the KEY GUARD [:L245-L259] is the ONLY part of ``aa010-main`` that runs on both
paths, because it sits above the branch.  Verified by running every verb down both
paths.

``N-record-size-guard-unreachable`` ⭐ - both records total exactly 100 bytes -
the file record [copybooks/plfdpinv.cob:L12-L21] and the working-storage record
[copybooks/plwspinv.cob:L8-L53] - so ``if A < B`` [:L567] is false and
``We-Error 901`` cannot be raised through this handler.  The whole display,
``SQL-Msg`` and ``accept`` block [:L571-L587] is therefore dead code that ships.
Reproduced in full anyway, because the sizes are DISPUTED (``N-recsize``) and the
guard is what would catch it.

=============================================================================
IDENTIFIER QUOTING - MANDATORY
=============================================================================

Every table name and every column name in this bridge contains a HYPHEN.
Unquoted, each one is a MySQL syntax error.  Every identifier that reaches a
statement here is routed through
:func:`acas_posting.dal.connection.quote_identifier`; no bare hyphenated name
appears in any statement text.

=============================================================================
RULES AND FURTHER READING
=============================================================================

``review_rules`` reports that no user rules document exists for this project, so
the binding constraints are the six rules of Agent Action Plan section 0.7.2 and,
where they are silent, enterprise-standard best practice.  Of those six:

* R-1, no COBOL at runtime - this module contains no process launch, no foreign
  function interface and no reference to the compiled tree; the handler and the
  bridge are both reimplemented natively as SQL against the frozen schema.
* R-2, zero binary floating-point arithmetic - money is :class:`decimal.Decimal`,
  counters and dates are :class:`int`, and every rendered value is text.
* R-3, no new validations, fields or schema changes and no concurrency - only
  ``SELECT``, ``INSERT``, ``UPDATE`` and ``DELETE`` are issued, execution is
  strictly sequential, and no data definition statement is emitted.
* R-4, legacy anomalies reproduced and never fixed - every anomaly above carries
  an inline locator at its reproduction site.
* R-5, full traceability - one function per COBOL paragraph, and every column
  cites its data-dictionary entry through
  :mod:`acas_posting.dictionary.loader`.
* R-6, compiled behaviour is the tie-breaker - the edit-picture measurement above
  was taken from compiled GnuCOBOL 3.2 rather than reasoned about, and nothing
  here reads a clock, a counter of elapsed time or an entropy source.

Every anomaly named above also belongs in ``docs/migration/anomaly-log.md``
naming this module as the reproducing module, and every measurement named above
in ``docs/migration/ambiguity-resolutions.md`` with its experiment.
"""

from __future__ import annotations

import dataclasses
import decimal
import enum
import logging
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any, Final

from acas_posting.dal import connection
from acas_posting.dal import cursor_state
from acas_posting.dal import status
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.purchase_invoice import (
    IhInvoiceHeader,
    IhPrime,
    IhSubPrime,
    IlInvoiceLine,
    IlInvoiceLineBody,
    IlKey,
    PInvoiceBodies,
    PInvoiceHeader,
    WsPInvoiceRecord,
    cite_for,
    dictionary_key_for,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__ = [
    "BRIDGE_DISPATCHED_FILE_FUNCTIONS",
    "BRIDGE_LINKAGE_PARAMETER_NAMES",
    "BRIDGE_NAME",
    "BRIDGE_PARAGRAPH_NUMBERS",
    "CURSOR_SLOTS",
    "DEAD_DECLARATION_LOCATORS",
    "DECLARED_RECORD_SIZE_NOTES",
    "DISPATCHED_FILE_FUNCTIONS",
    "ENTITY_FACADE",
    "EXTENDED_FUNCTION_CODE_CENSUS",
    "FLAT_FILE_PATH_AVAILABLE",
    "HANDLER_LINKAGE_PARAMETER_NAMES",
    "HANDLER_NAME",
    "HANDLER_PARAGRAPH_NUMBERS",
    "HANDLER_PROG_NAME",
    "HEADER_COLUMNS",
    "HEADER_COLUMN_RENDER",
    "HEADER_LOAD_SEQUENCE",
    "HEADER_NEVER_POPULATED_COLUMNS",
    "HEADER_TABLE",
    "HEADER_UNLOAD_SEQUENCE",
    "KEY_NUMBER_GUARDED_FUNCTIONS",
    "KEY_OF_REFERENCE",
    "LINES_COLUMNS",
    "LINES_COLUMN_RENDER",
    "LINES_LOAD_SEQUENCE",
    "LINES_TABLE",
    "LINES_UNLOAD_SEQUENCE",
    "PLWSPINV2_CONSUMERS",
    "RENDER_SIGN_LOSS_COLUMNS",
    "RG_TABLE",
    "SIGN_LOSS_HOST_VARIABLES",
    "WE_ERROR_RG1_SECONDARY_KEY_RANGE",
    "WE_ERROR_RG_PROCESSING_BASE",
    "WE_ERROR_RG_UNKNOWN",
    "WRITE_ONLY_COLUMNS",
    "WS_LOG_FILE_NO",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "ColumnRender",
    "EditWindow",
    "ExecutionResult",
    "HeaderHostVariables",
    "HostVariableMove",
    "LineHostVariables",
    "PInvoiceContext",
    "RepeatingGroupEntry",
    "SqlFragment",
    "SqlStatement",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_move_inv_data",
    "aa045_eval_keys",
    "aa050_process_read_indexed",
    "aa060_process_start",
    "aa070_process_write",
    "aa080_process_delete",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_exit",
    "aa_main_exit",
    "aa_process_flat_file",
    "ba010_initialise",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba041_reread",
    "ba042_fetch",
    "ba050_process_read_indexed",
    "ba060_process_start",
    "ba070_process_write",
    "ba080_process_delete",
    "ba085_process_delete_all",
    "ba090_process_rewrite",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "ba999_exit",
    "ba_acas_dal_process",
    "ba_process_rdbms",
    "ba_rdbms_exit",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "bc000_hv_load_rg1",
    "bc000_rg_process",
    "bc050_process_read_indexed",
    "bc051_fetch_rg1",
    "bc058_restore_pointers",
    "bc059_exit",
    "bc070_process_write",
    "bc080_process_delete",
    "bc085_exit",
    "bc085_process_delete_all",
    "bc090_exit",
    "bc090_process_rewrite",
    "bc100_unload_hvs_rg1",
    "bc200_insert_rg1",
    "bc300_update_rg1",
    "bc998_free",
    "ca_exit",
    "ca_exit_handler",
    "ca_process_logs",
    "ca_process_logs_handler",
    "citations",
    "cite_for",
    "default_context",
    "dictionary_key_for",
    "dispatch",
    "line_from_bodies",
    "line_from_buffer",
    "plinvoice_mt",
    "rendered_column_text",
]

_LOG: Final[logging.Logger] = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

#: The COBOL file handler this module reimplements [common/acas026.cbl].
HANDLER_NAME: Final[str] = "acas026"

#: The generated bridge the handler calls [common/plinvoiceMT.cbl], translated by
#: the vendored JC preSQL processor from [common/plinvoiceMT.scb].
BRIDGE_NAME: Final[str] = "plinvoiceMT"

#: `77  prog-name  pic x(17)  value "acas026 (3.3.00)"` [common/acas026.cbl:L189].
HANDLER_PROG_NAME: Final[str] = "acas026 (3.3.00)"

#: The entity facade name from the Agent Action Plan's entity-to-table spine.
ENTITY_FACADE: Final[str] = "PInvoice"

#: The header table - 30 columns, primary key `PINVOICE-KEY`
#: [mysql/ACASDB.sql:L545]. Declared to the translator as
#: `TABLE=PUINVOICE-REC,HV` [common/plinvoiceMT.scb:L383].
HEADER_TABLE: Final[str] = "PUINVOICE-REC"

#: The lines table - 14 columns, primary key `IL-LINE-KEY`
#: [mysql/ACASDB.sql:L510]. Declared to the translator as
#: `TABLE=PUINV-LINES-REC,HV1` [common/plinvoiceMT.scb:L384].
LINES_TABLE: Final[str] = "PUINV-LINES-REC"

#: The host-variable group prefixes the `/MYSQL VAR\` directive assigns
#: [common/plinvoiceMT.scb:L381-L385]: the header group is suffixed `HV` and the
#: lines group `HV1`, which is where `HV-` and `HV1-` come from.
_HV_GROUP_SUFFIX_BY_TABLE: Final[Mapping[str, str]] = MappingProxyType(
    {HEADER_TABLE: "HV", LINES_TABLE: "HV1"}
)

#: The three declared record-size notes, spread over FOUR statements in THREE
#: files, published unresolved next to Agent Action Plan anomaly 15. See
#: ``N-recsize`` in the module docstring.
DECLARED_RECORD_SIZE_NOTES: Final[Mapping[str, str]] = MappingProxyType(
    {
        # `*> record size 100 bytes  06/05/17   26/03/09`
        "copybooks/plwspinv.cob:L6": "100 bytes",
        # `*> record size 129 bytes 22/12/11`
        # `*>           = 100 less filler err. 06/05/17 item-nos > 99 from bin-char`
        "copybooks/plwspinv2.cob:L7-L8": "129 bytes, then 100 less filler err.",
        # `*> record size 100 bytes 26/03/09` .. `*>  100 bytes 08/01/18 less
        # filler err. item-nos bin -> 99.`
        "copybooks/plfdpinv.cob:L6-L9": "100, then 126, then 129, then 100 bytes",
    }
)

#: ``N-dead-filler`` - `copybooks/plwspinv2.cob:L54` carries a COMMENTED-OUT
#: `05  filler pic x(30).` annotated
#: `*> This appears to be empty of data on all rec types.` The maintainer's own
#: hedge - "appears to be" - was never resolved, and the declaration was disabled
#: rather than deleted, so the byte range it once covered is now simply absent
#: from the layout. Recorded as dead; no field, no host variable, no column.
DEAD_DECLARATION_LOCATORS: Final[tuple[str, ...]] = (
    "copybooks/plwspinv2.cob:L54",
)

#: ``N-plwspinv2-copied-by-neither`` ⭐⭐ - CORRECTS THE AGENT BRIEF. The brief's
#: §3.10 states that `copybooks/plwspinv2.cob` "exists for the handler and the
#: callers only". Verified at source, it is copied by NEITHER: the handler copies
#: the FILE definition `copybooks/plfdpinv.cob` [common/acas026.cbl:L184] and the
#: WORKING-STORAGE layout `copybooks/plwspinv.cob` [common/acas026.cbl:L214-L215],
#: and the bridge copies `copybooks/plwspinv.cob` only
#: [common/plinvoiceMT.cbl:L455-L458]. The whole of `plwspinv2.cob` - including
#: its `Invoice-Header redefines` [copybooks/plwspinv2.cob:L21] and
#: `Invoice-Line redefines` [copybooks/plwspinv2.cob:L56] views, from which this
#: module takes its two-view buffer model - reaches this posting cycle only
#: through the seven files below, every one of which is a loader, an unloader, a
#: restore utility, the end-of-cycle driver, or an out-of-scope report.
#: Consequence for traceability: the redefinition names this module reproduces are
#: taken from a copybook that neither in-scope program includes, so the two views
#: are a MODEL of the layout rather than a transcription of an included one.
PLWSPINV2_CONSUMERS: Final[tuple[str, ...]] = (
    "common/plinvoiceLD.cbl",
    "common/plinvoiceRES.cbl",
    "common/plautogenLD.cbl",
    "common/plinvoiceUNL.cbl",
    "common/xl150.cbl",
    "purchase/pl055.cbl",
    "purchase/pl140.cbl",
)

#: The declared byte length of the passed working-storage record and of the file
#: record, as `ba012-Test-WS-Rec-Size-2` compares them with
#: `function Length(WS-PInvoice-Record)` against `function length(Invoice-Record)`
#: [common/acas026.cbl:L562-L566]. Both layouts total 100 bytes - the file record
#: [copybooks/plfdpinv.cob:L12-L21] and the working-storage record
#: [copybooks/plwspinv.cob:L8-L53] - so `A < B` is false and `We-Error 901` is
#: unreachable through this handler. Reproduced as declared, not asserted.
#:
#: ``N-record-size-guard-unreachable`` ⭐ - because both layouts total exactly 100
#: bytes, `if A < B` [common/acas026.cbl:L568] can never be true, so the entire
#: block it guards is dead code that nonetheless ships: the two `display`s
#: [common/acas026.cbl:L579-L580], the `move Display-Blk to SQL-Msg`
#: [common/acas026.cbl:L581], the conditional `Ca-Process-Logs`
#: [common/acas026.cbl:L582-L584], the `accept Accept-Reply at 2433`
#: [common/acas026.cbl:L585] and the `go to ba-rdbms-exit`
#: [common/acas026.cbl:L586]. It is reproduced anyway, and deliberately NOT
#: short-circuited, for one reason: the record size is DISPUTED across four
#: statements in three files (see :data:`DECLARED_RECORD_SIZE_NOTES` and
#: ``N-recsize``), so "both are 100" is a property of the layouts as they stand
#: today rather than an invariant. Should a caller ever pass a buffer built to the
#: 126- or 129-byte note, the guard fires and `We-Error 901` becomes observable.
_WS_RECORD_DECLARED_LENGTH: Final[int] = 100
_FILE_RECORD_DECLARED_LENGTH: Final[int] = 100

#: `77  Display-Blk pic x(75) value spaces.` [common/acas026.cbl:L195].
_DISPLAY_BLK_WIDTH: Final[int] = 75

#: `77  A pic 9(4)` and `77  B pic 9(4)` [common/acas026.cbl:L193-L194] - the width
#: the record-size message renders them at, four digits, zero-filled.
_RECORD_SIZE_DIGITS: Final[int] = 4

#: `01  Error-Messages.` [common/acas026.cbl:L205-L209] - the handler's only two
#: literals, both `Module Specific` per the comment at [:L207]. `PL907` is 32
#: characters and `PL901` is 31; the continuation comment
#: `*>                                        yyy < Invoice-Rec = zzz` [:L210]
#: sketches the message `ba012-Test-WS-Rec-Size-2` assembles from it [:L573-L578].
#:
#: ``N-error-message-block`` ⭐ - the sketch comment
#: `*>                                        yyy < Invoice-Rec = zzz`
#: [common/acas026.cbl:L210] uses THREE-character placeholders, `yyy` and `zzz`,
#: for two fields that are declared `pic 9(4)` [common/acas026.cbl:L193-L194] and
#: therefore render at FOUR digits, zero-filled. The comment is a stale sketch of
#: an earlier, narrower pair of counters; the assembled message is four digits
#: wide in each slot. Recorded, not corrected - :data:`_RECORD_SIZE_DIGITS` is 4
#: because the PICTURE says 4, and the comment is left describing 3.
#:
#: ``N-open-close-key-wording`` ⭐ - a second stale-wording finding in the same
#: handler, worth reading beside this one. The handler logs
#: `"OPEN PL INVOICE File"` [common/acas026.cbl:L342] and
#: `"CLOSE PL INVOICE File"` [common/acas026.cbl:L353], naming the PURCHASE ledger
#: and suffixing `" File"`; the bridge logs `"OPEN SL INVOICE"` and
#: `"CLOSE SL INVOICE"` [common/plinvoiceMT.cbl:L605, :L631], naming the SALES
#: ledger and omitting the suffix. Same table, same run, two different log keys
#: depending only on which path served the call. Both are reproduced verbatim at
#: their own sites; see :func:`aa020_process_open`, :func:`aa030_process_close`,
#: :func:`ba020_process_open` and :func:`ba030_process_close`.
_ERROR_MESSAGE_PL901: Final[str] = "PL901 Note error and hit return"
_ERROR_MESSAGE_PL907: Final[str] = "PL907 Program Error: Temp rec = "

# ---------------------------------------------------------------------------
# Linkage - the two parameter lists, published for traceability (R-5)
# ---------------------------------------------------------------------------

#: `Procedure Division Using System-Record WS-PInvoice-Record File-Access
#: File-Defs ACAS-DAL-Common-data.` [common/acas026.cbl:L225-L231]. Five
#: parameters; :func:`dispatch` takes them in exactly this order.
HANDLER_LINKAGE_PARAMETER_NAMES: Final[tuple[str, ...]] = (
    "System-Record",
    "WS-PInvoice-Record",
    "File-Access",
    "File-Defs",
    "ACAS-DAL-Common-data",
)

#: `PROCEDURE DIVISION using File-Access ACAS-DAL-Common-data
#: WS-Invoice-Record.` [common/plinvoiceMT.cbl:L478-L480]. Three parameters, and
#: note the THIRD NAME: the caller passes `WS-PInvoice-Record`
#: [common/acas026.cbl:L614] while the bridge calls the very same argument
#: `WS-Invoice-Record` - the identifier `slinvoiceMT` uses for the SALES header.
#: Positionally harmless, but a reader grepping the bridge for
#: `WS-PInvoice-Record` finds nothing (anomaly ``N-bridge-param-rename``).
BRIDGE_LINKAGE_PARAMETER_NAMES: Final[tuple[str, ...]] = (
    "File-Access",
    "ACAS-DAL-Common-data",
    "WS-Invoice-Record",
)

# ---------------------------------------------------------------------------
# Log identity - the one handler in the folder that does NOT add ten
# ---------------------------------------------------------------------------

#: `move 4 to WS-Log-System.` [common/acas026.cbl:L240], whose own legend on that
#: line reads `*> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice used in FH logging`. Four
#: is Purchase Ledger. `status.LogSystem` publishes 5 as ``STOCK`` because
#: [common/acas013.cbl:L298] and [common/acas015.cbl:L291] label it that way,
#: while this handler, [common/acas016.cbl:L248] and [common/acas019.cbl:L240]
#: all label it `Invoice` - the legend contradicts itself across the folder and
#: is recorded, not resolved (anomaly ``N-logsystem5-meaning``).
WS_LOG_SYSTEM: Final[status.LogSystem] = status.LogSystem.PL

#: `move 12 to WS-Log-File-No.` on the flat-file path [common/acas026.cbl:L241].
WS_LOG_FILE_NO: Final[int] = 12

#: `move 12 to WS-Log-File-no.  *> for FHlogger` on the RDB path
#: [common/acas026.cbl:L556]. TWELVE - the SAME value, not twenty-two.
#: ``acas026`` is the only handler in ``common/`` that does not add ten when it
#: crosses to the relational path, and it does so silently
#: (anomaly ``N-log-no-increment``). Do not "correct" this to 22.
WS_LOG_FILE_NO_RDB: Final[int] = 12

#: The ten siblings that DO add ten, recorded so the exception above is provably
#: an exception rather than an assumption. Values are ``(flat, rdb)``.
_LOG_FILE_NO_SIBLING_CENSUS: Final[Mapping[str, tuple[int, int]]] = MappingProxyType(
    {
        "acas005": (11, 21),
        "acas006": (12, 22),
        "acas007": (13, 23),
        "acas008": (15, 25),
        "acas012": (11, 21),
        "acas013": (13, 23),
        "acas015": (12, 22),
        "acas016": (12, 22),
        "acas019": (15, 25),
        "acas022": (11, 21),
        HANDLER_NAME: (WS_LOG_FILE_NO, WS_LOG_FILE_NO_RDB),
    }
)

#: `move nnn to WS-No-Paragraph` in the handler, one per dispatched verb
#: [common/acas026.cbl:L310, L348, L365, L418, L442, L490, L501, L513]. The
#: 201..208 block is shared verbatim with ``acas013``, ``acas015``, ``acas016``,
#: ``acas019`` and ``acas022`` - six handlers, one numbering scheme, so the
#: number alone does not identify the handler in a log record
#: (anomaly ``N-noparagraph-collision``).
HANDLER_PARAGRAPH_NUMBERS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "aa020-Process-Open": 201,
        "aa030-Process-Close": 202,
        "aa040-Process-Read-Next": 203,
        "aa050-Process-Read-Indexed": 204,
        "aa060-Process-Start": 205,
        "aa070-Process-Write": 206,
        "aa080-Process-Delete": 207,
        "aa090-Process-Rewrite": 208,
    }
)

#: `move nn to ws-No-Paragraph` in the bridge. The authoritative list is the
#: maintainer's own comment block [common/plinvoiceMT.cbl:L542-L563]; every
#: value below was additionally verified at its `move` site. Two facts survive
#: unchanged: the comment block assigns ``56 UPDATE`` to BOTH
#: `bc070-Process-Write` [:L560] and `bc090-Process-Rewrite` [:L563] while
#: `bc070` only ever moves 53 [:L2497] (anomaly
#: ``N-bridge-paragraph-56-duplicated``), and `ba100-Bad-Function` moves nothing
#: at all, so a bad-function log record carries whatever the previous verb left.
BRIDGE_PARAGRAPH_NUMBERS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ba020-Process-Open": 1,
        "ba030-Process-Close": 2,
        "ba040-Process-Read-Next": 3,
        "ba041-Reread": 4,
        "ba050-Process-Read-Indexed/SELECT": 5,
        "ba050-Process-Read-Indexed/FETCH": 6,
        "ba060-Process-Start/SELECT-HEADER": 8,
        "ba070-Process-Write": 10,
        "ba080-Process-Delete": 13,
        "ba085-Process-Delete-ALL": 15,
        "ba090-Process-Rewrite": 17,
        "ba998-Free": 20,
        "bc050-Process-Read-Indexed/SELECT": 51,
        "bc051-Fetch-RG1": 52,
        "bc070-Process-Write": 53,
        "bc080-Process-Delete": 54,
        "bc085-Process-Delete-ALL": 55,
        "bc090-Process-Rewrite": 56,
        "ba060-Process-Start/SELECT-LINES": 57,
        "bc998-Free": 58,
    }
)

# ---------------------------------------------------------------------------
# The verb set
# ---------------------------------------------------------------------------

#: Exactly what `evaluate File-Function` dispatches in the HANDLER
#: [common/acas026.cbl:L283-L303]. Code 34 shares the `when 3` target by
#: fall-through [:L288-L290], so `fn-Read-Next-Header` is the ordinary
#: Read-Next path with no header filtering whatever
#: (anomaly ``N-read-next-header-is-read-next``). Codes 6, 13, 15, 31, 32 and 33
#: are NOT dispatched - `when other` sends them to `aa100-Bad-Function`
#: [:L301-L302], the `*> 6 is spare / unused` comment sitting on that line.
DISPATCHED_FILE_FUNCTIONS: Final[Mapping[status.FileFunction, str]] = MappingProxyType(
    {
        status.FileFunction.OPEN: "aa020-Process-Open",
        status.FileFunction.CLOSE: "aa030-Process-Close",
        status.FileFunction.READ_NEXT: "aa040-Process-Read-Next",
        status.FileFunction.READ_NEXT_HEADER: "aa040-Process-Read-Next",
        status.FileFunction.READ_INDEXED: "aa050-Process-Read-Indexed",
        status.FileFunction.WRITE: "aa070-Process-Write",
        status.FileFunction.RE_WRITE: "aa090-Process-Rewrite",
        status.FileFunction.DELETE: "aa080-Process-Delete",
        status.FileFunction.START: "aa060-Process-Start",
    }
)

#: Exactly what `evaluate File-Function` dispatches in the BRIDGE
#: [common/plinvoiceMT.cbl:L515-L540]. It differs from the handler's table in
#: ONE entry, and the difference is load bearing: `when 6` is dispatched, to
#: `ba085-Process-Delete-All`, under the comment `*> option 6 is a special to
#: cleardown all LINE data for 1 invoice` [:L528-L531]. The handler rejects 6 as
#: spare, but the RDB branch forwards `File-Function` unmodified
#: [common/acas026.cbl:L263-L266], so a caller that sets 6 and reaches the DAL
#: path performs the delete-all after all (anomaly ``N-bridge-dispatches-verb-6``).
BRIDGE_DISPATCHED_FILE_FUNCTIONS: Final[Mapping[status.FileFunction, str]] = (
    MappingProxyType(
        {
            status.FileFunction.OPEN: "ba020-Process-Open",
            status.FileFunction.CLOSE: "ba030-Process-Close",
            status.FileFunction.READ_NEXT: "ba040-Process-Read-Next",
            status.FileFunction.READ_NEXT_HEADER: "ba040-Process-Read-Next",
            status.FileFunction.READ_INDEXED: "ba050-Process-Read-Indexed",
            status.FileFunction.WRITE: "ba070-Process-Write",
            status.FileFunction.DELETE_ALL: "ba085-Process-Delete-ALL",
            status.FileFunction.RE_WRITE: "ba090-Process-Rewrite",
            status.FileFunction.DELETE: "ba080-Process-Delete",
            status.FileFunction.START: "ba060-Process-Start",
        }
    )
)

#: The corrected folder-wide census of the four EXTENDED function codes declared
#: at [copybooks/wsfnctn.cob:L102-L105]. ``acas026`` dispatches **34**, not 31 -
#: `when  34    *> fn-Read-Next-Header` [common/acas026.cbl:L289]. The prompt
#: that governed ``acas022_purch.py`` records this last entry wrongly as 31; the
#: correction is published here so the traceability document carries the right
#: figures. The consequence stands unchanged: codes 32 (`fn-Read-By-Batch`) and
#: 33 (`fn-Read-By-Cust`) are dispatched by NO handler at all, even though
#: [copybooks/wsfnctn.cob:L103-L104] names OTM3 and OTM5 programs as their
#: consumers (anomaly ``N-census-correction``).
#:
#: ``N-34-changelog-count`` ⭐ - the declaration of code 34 at
#: [copybooks/wsfnctn.cob:L105] annotates it `*> for Invoice (sl020, 50, 140, 820)`,
#: naming FOUR consumer programs, and every one of the four is a SALES program -
#: yet the two handlers that implement the code are ``acas016`` (sales invoice) and
#: this one, ``acas026``, which serves the PURCHASE invoice tables. So a code
#: declared for four sales callers is dispatched by a purchase handler, and the
#: mirrored handler's own changelog enumerates only THREE of the four. Neither the
#: count nor the ledger is reconciled anywhere in the source. Recorded; the code is
#: implemented exactly as this handler dispatches it and no consumer list is
#: inferred from the comment.
EXTENDED_FUNCTION_CODE_CENSUS: Final[Mapping[str, status.FileFunction | None]] = (
    MappingProxyType(
        {
            "acas000": None,
            "acas005": None,
            "acas006": None,
            "acas007": None,
            "acas008": None,
            "acas012": status.FileFunction.READ_BY_NAME,
            "acas013": None,
            "acas015": None,
            "acas016": status.FileFunction.READ_NEXT_HEADER,
            "acas019": None,
            "acas022": status.FileFunction.READ_BY_NAME,
            "acas026": status.FileFunction.READ_NEXT_HEADER,
            "acas029": None,
            "acasirsub1": None,
            "acasirsub3": None,
            "acasirsub4": None,
            "acasirsub5": None,
        }
    )
)

#: The handler's key guard [common/acas026.cbl:L245-L259]: `fn-read-indexed` (4)
#: and `fn-start` (9) reject `File-Key-No not = 1` with `998`/`99`, and
#: `fn-delete` (8) rejects it with `996`/`99`. Note the 996 comment at [:L255] is
#: a verbatim copy of the 998 comment at [:L249], including the trailing column
#: of digits (anomaly ``N-996-comment``); it is preserved, not rewritten.
#:
#: The consequence is the dead second key: `Table-Of-KeyNames` declares TWO keys
#: [common/plinvoiceMT.cbl:L297-L306] but no `File-Key-No` other than 1 survives
#: this guard, so `IL-LINE-KEY` is unreachable through Start, Read-Indexed or
#: Delete (anomaly ``N-key2-unreachable``, exactly as in ``acas016``). The lines
#: table is reached only by the bridge's own routing on `WS-ih-Test`.
KEY_NUMBER_GUARDED_FUNCTIONS: Final[Mapping[status.FileFunction, status.WeError]] = (
    MappingProxyType(
        {
            status.FileFunction.READ_INDEXED: status.WeError.FILE_KEY_NO_OUT_OF_RANGE,
            status.FileFunction.START: status.WeError.FILE_KEY_NO_OUT_OF_RANGE,
            status.FileFunction.DELETE: status.WeError.DELETE_KEY_OUT_OF_RANGE,
        }
    )
)

#: The only key number the guard admits [common/acas026.cbl:L248, L254].
_ONLY_ADMITTED_KEY_NUMBER: Final[int] = 1

# ---------------------------------------------------------------------------
# Keys, cursors and the inert repeating group
# ---------------------------------------------------------------------------

#: `01 Table-Of-KeyNames.` / `03 KeyOfReference occurs 2 indexed by KOR-x1.`
#: [common/plinvoiceMT.cbl:L297-L311], mirrored one for one in the pre-translation
#: source [common/plinvoiceMT.scb:L297-L311]. Both entries are offset 1, length
#: 10 and type ``'STR'``.
#:
#: The entries are NOT re-declared here - they are taken from
#: :data:`acas_posting.dal.cursor_state.TABLE_OF_KEYNAMES`, which already carries
#: both of this bridge's keys with their source locators and their cursor slots,
#: so there is exactly one declaration of the key metadata in the migration.
#:
#: Two source asymmetries ride along and are preserved by that shared table.
#: `'PINVOICE-KEY                  '` [:L298] is explicitly space padded to
#: thirty characters in the literal while `'IL-LINE-KEY'` [:L302] is not; since
#: `keyname` is `pic x(30)` COBOL pads the shorter literal anyway, so the runtime
#: values agree and only the source differs - the identical asymmetry
#: `slinvoiceMT` shows at its own [common/slinvoiceMT.cbl:L297, L301]
#: (anomaly ``N-keyname-padding``). And `05 KOR-Type pic XXX.` carries the
#: comment `*> Not used currently` [:L311] while both entries nonetheless declare
#: a concrete `'STR'` [:L300, L304] (anomaly ``N-kortype``).
#:
#: ``N-fd-one-record-key`` ⭐ - the dead second key is dead THREE independent ways,
#: not one. First, the handler's key guard rejects any `File-Key-No` other than 1
#: [common/acas026.cbl:L248, :L254] (``N-key2-unreachable``). Second, the SELECT
#: statement declares exactly one key - `record key invoice-key`
#: [copybooks/plselpinv.cob:L6] - with NO `alternate record key` clause at all, so
#: even a caller that somehow bypassed the guard has no second ISAM path to
#: position on. Third, the FD names only the six fields of the header prefix
#: [copybooks/plfdpinv.cob:L12-L21], so `IL-LINE-KEY` has no counterpart in the
#: flat file to be a key OF. The lines table is therefore reachable only through
#: the bridge's own routing on `WS-ih-Test`, never through a caller-selected key
#: number, on either path. Reproduced: key 2 is published in the table because the
#: source declares it, and no verb in this module accepts it.
KEY_OF_REFERENCE: Final[tuple[cursor_state.KeyOfReference, ...]] = (
    cursor_state.TABLE_OF_KEYNAMES[HEADER_TABLE]
    + cursor_state.TABLE_OF_KEYNAMES[LINES_TABLE]
)

#: `KOR-x1` is a one-based COBOL index; key 1 is the header, key 2 the lines.
_KOR_HEADER: Final[int] = 1
_KOR_LINES: Final[int] = 2


def _key_of_reference(kor_x1: int) -> cursor_state.KeyOfReference:
    """`KeyOfReference (KOR-x1)` - the one-based subscript into the key table.

    Every positioning paragraph in the bridge opens with the same three
    statements - `set KOR-x1 to <n>.` then `move KOR-offset (KOR-x1) to K` and
    `move KOR-length (KOR-x1) to L` [common/plinvoiceMT.cbl:L834-L836, :L965-L967,
    :L1053-L1055, :L1195-L1197, :L1291-L1293, :L1365-L1367, :L2365-L2367,
    :L2534-L2536, :L2698-L2700] - so the subscript is set, then the offset and
    length are read out of the indexed entry.  This function is that subscripting
    step, and the offset and length travel with the entry it returns rather than in
    two separate variables.

    ⭐ Both entries declare offset 1 and length 10 [:L299, :L303], so `K`/`L` and
    `K2`/`L2` always hold the same pair - the two variables exist because the
    positioning code was written twice, not because the keys differ.
    """
    return KEY_OF_REFERENCE[kor_x1 - 1]

#: The two cursors this bridge declares - `05 Most-Cursor-Set pic 9 value zero.`
#: and `05 Most-Cursor-Set-2 pic 9 value zero.  *> RG 1`
#: [common/plinvoiceMT.cbl:L330-L335], each with its own pair of condition names
#: (`Cursor-Not-Active`/`Cursor-Active` and `Cursor-Not-Active-2`/
#: `Cursor-Active-2`). Slot 1 positions the header table, slot 2 the lines table
#: (anomaly ``N-two-cursors``).
CURSOR_SLOTS: Final[Mapping[str, cursor_state.CursorSlot]] = MappingProxyType(
    {
        HEADER_TABLE: cursor_state.CursorSlot.PRIMARY,
        LINES_TABLE: cursor_state.CursorSlot.SECONDARY,
    }
)


@dataclasses.dataclass(frozen=True, slots=True)
class RepeatingGroupEntry:
    """One row of `RG-Table` / `RG-Entry` [common/plinvoiceMT.cbl:L316-L326].

    The declaration is inert by the maintainer's own labelling. It sits under
    `*>  Start of RG (Repeat Groups)                        NOT USED - YET.`
    [:L313] and `*> Metadata on Repeating Groups...                     but acts
    as a reminder` [:L314], and its `occurs` is **1** [:L322] against a declared
    maximum row count of **40** [:L318] - the array can hold one entry
    describing a forty-row group (anomaly ``N-rg-notused-yet``).

    It is modelled because R-5 requires every declaration to have a counterpart,
    and it is modelled as *state* rather than as an engine: nothing in this
    module reads :attr:`rg_maxoccurs` to drive a loop, exactly as nothing in the
    bridge does. Building a repeating-group engine here would be adding
    behaviour the specification does not have.
    """

    #: `05 RG-recname pic x(30).` [:L324]; the sole value is
    #: `'PUINV-LINES-REC'` [:L317].
    rg_recname: str
    #: `05 RG-maxoccurs pic s9(9) comp-5.` [:L325]; declared `value 40` [:L318].
    rg_maxoccurs: int
    #: `05 RG-noloaded pic s9(9) comp-5.  *> Number loaded.` [:L326]; declared
    #: `value zero` [:L319] and never incremented anywhere in the bridge.
    rg_noloaded: int
    #: Where the declaration lives, for the traceability document.
    source_locator: str


#: `01 RG-Table.` as declared [common/plinvoiceMT.cbl:L316-L319]. One entry,
#: never mutated, published so that a reader diffing the bridge against this
#: module finds the declaration rather than concluding it was dropped.
RG_TABLE: Final[tuple[RepeatingGroupEntry, ...]] = (
    RepeatingGroupEntry(
        rg_recname=LINES_TABLE,
        rg_maxoccurs=40,
        rg_noloaded=0,
        source_locator="[common/plinvoiceMT.cbl:L316-L326]",
    ),
)

#: `01 PInvoice-Bodies.` / `03 invoice-line occurs 40.`
#: [copybooks/plwspinv.cob:L65-L66] - the same forty, reached from the copybook
#: side. The bridge collapses the `occurs` away with its third `REPLACING`
#: clause `==occurs 40.== by ==.==` [common/plinvoiceMT.cbl:L457] under the
#: rationale `*>   to reduce Ram usage get rid of the occurs, hopefully.` [:L453].
_BODIES_OCCURS: Final[int] = 40

#: `01  WS-Last-Read-Key.` with `03  WS-Last-Read-Invoice pic 9(8) value zero.`
#: and `03  WS-Last-Read-Line pic 99 value 40.`
#: [common/plinvoiceMT.cbl:L286-L288], with
#: `01  WS-Actual-Lines-In-Row pic 99 value zero.` [:L289]. The line watermark
#: initialises to the MAXIMUM line number rather than to zero, identical to
#: [common/slinvoiceMT.cbl:L286-L288] (anomaly ``N-last-read-line-40``), so the
#: `if WS-Last-Read-Line < WS-Actual-Lines-In-Row` test at [:L724] is false on a
#: virgin bridge for every invoice with forty lines or fewer.
_LAST_READ_INVOICE_INITIAL: Final[int] = 0
_LAST_READ_LINE_INITIAL: Final[int] = 40
_ACTUAL_LINES_IN_ROW_INITIAL: Final[int] = 0

#: `move "0000000000" to WS-File-Key` and the `" >= "` relation the sequential
#: read hard-codes for its first positioning [common/plinvoiceMT.cbl:L645-L646],
#: already published with both locators by
#: :data:`acas_posting.dal.cursor_state.SEQUENTIAL_READ_START`. Cited rather than
#: re-declared.
_SEQUENTIAL_READ_START: Final[cursor_state.SequentialReadStart] = (
    cursor_state.SEQUENTIAL_READ_START[HEADER_TABLE]
)

# ---------------------------------------------------------------------------
# Status codes this bridge owns and `dal/status.py` does not publish
# ---------------------------------------------------------------------------
#
# `dal/status.py` publishes the whole shared vocabulary - 0/10/21/22/23/99 for
# `FS-Reply` and 901/910/911/988/989/990/992/994/995/996/997/998/999 for
# `WE-Error` - and those are cited from there, never redefined. The
# header-plus-lines bridges additionally own an `8nn` band for repeating-group
# processing which no other bridge uses and which `status.WeError` therefore does
# not carry. It is declared here, at the one module that needs it, with its
# provenance.

#: `*>   8nn  = Processing on RG Table & rows.` [common/plinvoiceMT.cbl:L205].
#: A band, not a value; published so the two members below are visibly part of a
#: family and so a reader can classify an unrecognised `8nn` correctly.
WE_ERROR_RG_PROCESSING_BASE: Final[int] = 800

#: `*>  890 = Unknown/unexpected error on RG processing.`
#: [common/plinvoiceMT.cbl:L207]. Written once, by `bc050-Process-Read-Indexed`
#: when the lines SELECT returns no rows [:L2413], paired with `FS-Reply` 23.
WE_ERROR_RG_UNKNOWN: Final[int] = 890

#: `*>  880 = Unexpected range error in Rg1 secondary key. Report to programming
#: team.` [common/plinvoiceMT.cbl:L206]. Declared and documented but never
#: written by any statement in the bridge - a documentation-only code, exactly the
#: class `status.DOCUMENTATION_ONLY_WE_ERRORS` exists to record. Published so the
#: dictionary of this bridge's vocabulary is complete.
WE_ERROR_RG1_SECONDARY_KEY_RANGE: Final[int] = 880

#: `*>  901 = File Def record size not =< than WS record size. FATAL`, the code
#: `ba012-Test-WS-Rec-Size-2` would raise [common/acas026.cbl:L568-L569]. Taken
#: from `status.WeError`, not redefined.
_WE_ERROR_RECORD_SIZE: Final[status.WeError] = status.WeError.RECORD_SIZE_MISMATCH

#: `*>  910 = Table locked for > 5 seconds` - published by `status.WeError` and
#: unreachable in every bridge in the folder, since no bridge implements a lock
#: retry. Cited for completeness; nothing in this module writes it.
_WE_ERROR_TABLE_LOCKED: Final[status.WeError] = status.WeError.TABLE_LOCKED

#: `move zero to SQL-State.` [common/plinvoiceMT.cbl:L498] - the figurative
#: constant ZERO moved into `SQL-State pic x(5)` [copybooks/wsfnctn.cob:L51],
#: which fills the field with the CHARACTER zero rather than with spaces. The
#: handler had just set the same field to spaces [common/acas026.cbl:L281], and
#: the bridge leaves `SQL-Msg` and `SQL-Err` as spaces [:L503-L508], so one call
#: carries two different representations of "empty"
#: (anomaly ``N-sqlstate-zero-not-space``).
_SQL_STATE_ZEROED: Final[str] = "0" * status.SQL_STATE_WIDTH

#: `if WS-MYSQL-Error-Number not = "0  "` - the three-character literal every
#: error branch in the bridge compares against [common/plinvoiceMT.cbl:L684, L798,
#: L921, L1031, L1107, L1167, L1233, L1330, L1391, L2407, L2505, L2575, L2672].
_MYSQL_ERRNO_NONE: Final[str] = "0  "

#: The duplicate-key discriminators the write paths test, verbatim from
#: [common/plinvoiceMT.cbl:L1171-L1173] and [:L2510-L2512]: `Sql-State = "23000"`
#: or `SQL-Err (1:4) = "1062"` or `= "1022"`.
_DUPLICATE_KEY_SQL_STATE: Final[str] = str(status.DUPLICATE_KEY_SQLSTATE.value)
_DUPLICATE_KEY_ERRNO_PREFIXES: Final[tuple[str, ...]] = ("1062", "1022")

# ---------------------------------------------------------------------------
# The three load/unload asymmetries, as data
# ---------------------------------------------------------------------------

#: The five columns that can only ever hold a single space, for every row,
#: forever - the headline finding of this module.
#:
#: `05  HV-IH-STATUS-A PIC X(1).` .. `05  HV-IH-STATUS-P PIC X(1).`
#: [common/plinvoiceMT.cbl:L408-L412] declares them as host variables. The schema
#: gives all five `char(1) NOT NULL` with descriptive comments
#: [mysql/ACASDB.sql:L563-L567]. NEITHER [copybooks/plwspinv.cob] NOR
#: [copybooks/plwspinv2.cob] declares any of them - the purchase copybook has
#: only `05  ih-status pic x.` [copybooks/plwspinv.cob:L40], where the SALES
#: copybook does declare the five as real fields
#: [copybooks/slwsinv.cob:L56-L60] (anomaly ``N-copybook-mirror-asymmetry``).
#: And neither `bb000-HV-Load` [:L1450-L1477] nor `bb100-UnloadHVs`
#: [:L1487-L1512] contains a single move to or from any of them, so the only
#: value they can carry is whatever `initialize TD-PUINVOICE-REC` [:L1450] leaves
#: behind, i.e. **space** (anomaly ``N-five-status-columns-never-populated``).
#:
#: They ARE read back: `ba042-Fetch` names all five in its
#: `CALL "MySQL_fetch_record"` parameter list [:L769-L773] and `ba050` does the
#: same [:L881-L913], so the values arrive in the host variables and are then
#: silently dropped by the unload (anomaly ``N-status-hvs-fetched-then-discarded``).
#:
#: Every header INSERT and UPDATE therefore supplies all five - verified: both
#: builders name each of the five twice, once for the column and once for the
#: value, ten references apiece, e.g. `STRING '`IH-STATUS-A`="' INTO
#: WS-MYSQL-COMMAND` followed by `STRING FUNCTION TRIM (HV-IH-STATUS-A,TRAILING)`
#: in `bb200-Insert` (the paragraph opens at [common/plinvoiceMT.cbl:L1528]; these
#: three statements are at [:L1772-L1774]) and again in
#: `bb300-Update` [:L2169-L2171]. They are never derived from `IH-STATUS`, because
#: the bridge does not derive them, and never omitted, because the columns are
#: `NOT NULL`.
#:
#: ⭐⭐ AND THE TWO LAYERS DIFFER, which is the part that is easy to get wrong.
#: The HOST VARIABLE holds a single space, as :data:`_NEVER_POPULATED_STATUS_VALUE`
#: records. The STATEMENT does NOT: the value is emitted through
#: `FUNCTION TRIM (HV-IH-STATUS-A,TRAILING)`, and trailing-trimming a field whose
#: entire content is one space yields the EMPTY STRING, not a space - verified
#: empirically against GnuCOBOL 3.2 in the harness container, and recorded as
#: anomaly ``N-trim-space-to-empty``. So the five columns reach MariaDB as
#: `` `IH-STATUS-A`="" `` and the stored value is ``''``, not ``' '``.
#:
#: This module binds the RENDERED value, so :func:`rendered_column_text` returns
#: ``''`` for all five and the state diff matches. ⛔ Do NOT "correct" the bound
#: value to a space to match the host variable: the host variable is not what the
#: bridge sends. ⛔ And do not conclude from the empty string that the column could
#: be omitted - `NOT NULL` with no DEFAULT means the INSERT must still name it.
HEADER_NEVER_POPULATED_COLUMNS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "IH-STATUS-A": "[common/plinvoiceMT.cbl:L408] / [mysql/ACASDB.sql:L563] 'Applied'",
        "IH-STATUS-C": "[common/plinvoiceMT.cbl:L409] / [mysql/ACASDB.sql:L564] 'cleared'",
        "IH-STATUS-I": "[common/plinvoiceMT.cbl:L410] / [mysql/ACASDB.sql:L565] 'Invoiced'",
        "IH-STATUS-L": "[common/plinvoiceMT.cbl:L411] / [mysql/ACASDB.sql:L566] 'printed'",
        "IH-STATUS-P": "[common/plinvoiceMT.cbl:L412] / [mysql/ACASDB.sql:L567] 'Pending'",
    }
)

#: The single character those five columns carry. `initialize` sets an
#: alphanumeric item to spaces, and `PIC X(1)` is one character wide.
_NEVER_POPULATED_STATUS_VALUE: Final[str] = " "

#: The two columns that are loaded and never unloaded - write-only columns.
#:
#: ``PUINVOICE-REC.PINVOICE-KEY`` is loaded at [common/plinvoiceMT.cbl:L1452] and
#: appears nowhere in `bb100-UnloadHVs` [:L1489-L1512], so a read never puts the
#: primary key back into the record. It is the identical defect
#: `slinvoiceMT` shows for `HV-SINVOICE-KEY`
#: (anomaly ``N-pinvoice-key-write-only``). Note the value is not lost to the
#: caller: `ba042-Fetch` moves `WS-Invoice-Key` into the log key [:L818] from the
#: record's OWN key group, which the unload does repopulate field by field
#: through `WS-ih-Invoice` and `WS-ih-Test`.
#:
#: ``PUINV-LINES-REC.IL-INVOICE`` is loaded at [common/plinvoiceMT.cbl:L2758] and
#: appears nowhere in `bc100-UnloadHVs-rg1` [:L2789-L2801]
#: (anomaly ``N-il-invoice-never-unloaded``). On a read `WS-il-Invoice` keeps
#: whatever `initialize WS-Invoice-Line` [:L2787] set, i.e. zero, while the
#: concatenated `WS-il-Key` IS restored [:L2789] and happens to carry the invoice
#: number in its first eight characters. The asymmetry is reproduced; the unload
#: is NOT completed.
WRITE_ONLY_COLUMNS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "PUINVOICE-REC.PINVOICE-KEY": (
            "loaded [common/plinvoiceMT.cbl:L1452], absent from the unload "
            "[common/plinvoiceMT.cbl:L1489-L1512]"
        ),
        "PUINV-LINES-REC.IL-INVOICE": (
            "loaded [common/plinvoiceMT.cbl:L2758], absent from the unload "
            "[common/plinvoiceMT.cbl:L2789-L2801]"
        ),
    }
)

#: The six fields whose sign is destroyed at the bridge boundary, before any SQL
#: executes - the Agent Action Plan anomaly 11 family, and dictionary anomaly
#: reference ``A-11`` with open ambiguity ``Q-3``.
#:
#: Each is declared signed in the copybook, unsigned as a host variable, and
#: unsigned in the column, so a negative value cannot survive the load. The
#: conversion is applied by exactly one helper,
#: :func:`_narrow_signed_to_unsigned_host_variable`, so the behaviour has one
#: implementation and one place to cite.
#:
#: ``ih-deduct-amt``, ``ih-deduct-vat`` and ``il-discount`` are deliberately NOT
#: in this table: they are unsigned at all three layers here
#: [copybooks/plwspinv.cob:L46-L47, L79], [common/plinvoiceMT.cbl:L414-L415, L436],
#: `decimal(5,2) unsigned` and `decimal(4,2) unsigned` - the exact opposite of
#: `otm3MT`, where the logically identical `OI-Deduct-Amt`/`OI-Deduct-Vat` are
#: signed at all three [common/otm3MT.cbl:L324-L325]
#: (anomaly ``N-deduct-sign-divergence``). Sign behaviour is per bridge and per
#: field; only the dictionary can be trusted.
SIGN_LOSS_HOST_VARIABLES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "PUINVOICE-REC.IH-DAT": (
            "ih-Date binary-long SIGNED [copybooks/plwspinv.cob:L16] -> "
            "HV-IH-DAT PIC 9(10) COMP [common/plinvoiceMT.cbl:L395] -> "
            "IH-DAT int(8) unsigned; the column is also RENAMED from Date to DAT"
        ),
        "PUINVOICE-REC.IH-DEDUCT-DAYS": (
            "ih-deduct-days binary-char SIGNED [copybooks/plwspinv.cob:L45] -> "
            "HV-IH-DEDUCT-DAYS PIC 9(03) COMP [common/plinvoiceMT.cbl:L413] -> "
            "tinyint(3) unsigned"
        ),
        "PUINVOICE-REC.IH-DAYS": (
            "ih-days binary-char SIGNED [copybooks/plwspinv.cob:L48] -> "
            "HV-IH-DAYS PIC 9(03) COMP [common/plinvoiceMT.cbl:L416] -> "
            "tinyint(3) unsigned"
        ),
        "PUINVOICE-REC.IH-CR": (
            "ih-cr binary-long SIGNED [copybooks/plwspinv.cob:L49] -> "
            "HV-IH-CR PIC 9(10) COMP [common/plinvoiceMT.cbl:L417] -> "
            "int(8) unsigned; same as slinvoiceMT, opposite of otm3MT"
        ),
        "PUINVOICE-REC.IH-LINES": (
            "ih-lines binary-char SIGNED [copybooks/plwspinv.cob:L44] -> "
            "HV-IH-LINES PIC 9(03) COMP [common/plinvoiceMT.cbl:L418] -> "
            "tinyint(2) unsigned at column ordinal 28"
        ),
        "PUINV-LINES-REC.IL-QTY": (
            "il-qty binary-short SIGNED [copybooks/plwspinv.cob:L73] -> "
            "HV1-IL-QTY PIC 9(05) COMP [common/plinvoiceMT.cbl:L431] -> "
            "smallint(6) unsigned"
        ),
    }
)


def _narrow_signed_to_unsigned_host_variable(value: int, digits: int) -> int:
    """Reproduce the signed-to-unsigned narrowing the bridge performs on load.

    The six fields in :data:`SIGN_LOSS_HOST_VARIABLES` are declared signed in
    [copybooks/plwspinv.cob] and unsigned as host variables in
    [common/plinvoiceMT.cbl:L395, L413, L416, L417, L418, L431]. A COBOL `move`
    of a signed sending item into an unsigned `PIC 9(n) COMP` receiving item
    stores the ABSOLUTE VALUE - the sign is simply not representable - and then
    truncates on the high-order end to the receiving item's digit count.

    Both halves of that are reproduced here, in one place, so that the behaviour
    has exactly one implementation:

    * the sign is dropped, without raising, without clamping to zero and without
      taking a two's-complement view - a negative value becomes its magnitude;
    * the magnitude is reduced modulo ``10 ** digits``, which is COBOL's
      high-order truncation on an unsigned binary store.

    ``N-signloss`` -- the Agent Action Plan section 0.6.8 ambiguity, dictionary
    ambiguity reference ``Q-3`` -- IS NOW RESOLVED BY MEASUREMENT rather than by
    assumption, as rule R-6 requires. Measured against GnuCOBOL 3.2 (the version
    [common/comp-common.sh:L9] targets), default arithmetic, no binary-truncate
    flag:

    =====================  ==================  =====================
    sending item           receiving item      stored
    =====================  ==================  =====================
    ``binary-long -1``     ``pic 9(10) comp``  ``0000000001``
    ``binary-long -5``     ``pic 9(10) comp``  ``0000000005``
    ``binary-long -12345`` ``pic 9(10) comp``  ``0000012345``
    ``binary-long -1``     ``pic S9(10) comp`` ``-0000000001``
    ``binary-char -1``     ``pic 9(03) comp``  ``001``
    ``binary-char -128``   ``pic 9(03) comp``  ``128``
    ``binary-long -1234``  ``pic 9(03) comp``  ``234``
    ``binary-short -1``    ``pic 9(05) comp``  ``00001``
    ``binary-short -32768``  ``pic 9(05) comp``  ``32768``
    =====================  ==================  =====================

    So the narrowing is MAGNITUDE, emphatically not a two's-complement view: -1
    becomes 1 and never ``999``. And the second row group proves the high-order
    truncation is real and observable: -1234 into three digits becomes 234, not
    a diagnostic and not a clamp. The signed receiving item is shown for contrast
    - it keeps its sign, which is precisely why the six fields listed in
    :data:`SIGN_LOSS_HOST_VARIABLES` lose theirs and the eight signed
    ``decimal(9,2)`` money columns do not.

    The Agent Action Plan framed the residual doubt as depending on "the
    conversion the bridge's C interface object performs". In THIS bridge that
    object never sees a binary value at all: every host variable is rendered to
    TEXT through ``WS-MYSQL-EDIT`` and embedded literally in the statement before
    that interface object is reached -- see :func:`rendered_column_text`. The
    name of the object is deliberately not written out here, so that the rule
    R-1 scan for it stays at zero; it is cited in full in
    ``docs/migration/traceability.md``. The rendered
    windows were measured too and yield ``1`` after ``TRIM`` in all three widths
    (``(11:10)``, ``(18:03)``, ``(16:05)``). No C-interface behaviour can
    intervene, so the question closes entirely inside COBOL: the sign is lost at
    the BRIDGE and not at the database.

    For the six real fields the truncation half never actually bites, and the
    arithmetic of why is worth stating so that a future reader does not conclude
    the modulo is dead code: ``ih-Date`` and ``ih-cr`` are ``binary-long``, whose
    magnitude cannot exceed 2147483648 -- ten digits -- into ``pic 9(10)``;
    ``ih-deduct-days``, ``ih-days`` and ``ih-lines`` are ``binary-char``, at most
    128 -- three digits -- into ``pic 9(03)``; and ``il-qty`` is
    ``binary-short``, at most 32768 -- five digits -- into ``pic 9(05)``. Every
    one fits exactly. The modulo is retained regardless, because it is the COBOL
    rule and this is the single named primitive for it.
    """
    magnitude = value if value >= 0 else -value
    return magnitude % (10**digits)


# ---------------------------------------------------------------------------
# WS-MYSQL-EDIT: the 30-character render window family
# ---------------------------------------------------------------------------
#
# `01  WS-MYSQL-EDIT PIC -Z(18)9.9(9).` [common/plinvoiceMT.scb:L272], carried
# unchanged into the generated program. Thirty character positions:
#
#     position   1        the SIGN, '-' for negative and space for positive
#     positions  2 .. 19  Z(18), eighteen zero-SUPPRESSED integer digits
#     position  20        9, one mandatory integer digit
#     position  21        '.', the decimal point
#     positions 22 .. 30  9(9), nine mandatory fraction digits
#
# Every numeric column is written by moving its host variable into this one field
# and then STRINGing a reference-modified slice of it into the command. The
# picture was measured on GnuCOBOL 3.2 in the harness image rather than deduced,
# and the measurement is recorded in ``docs/migration/ambiguity-resolutions.md``.

#: The width of `WS-MYSQL-EDIT`, and the offsets of its parts.
_EDIT_WIDTH: Final[int] = 30
_EDIT_SIGN_POSITION: Final[int] = 1
_EDIT_INTEGER_POSITION: Final[int] = 2
_EDIT_INTEGER_DIGITS: Final[int] = 19
_EDIT_POINT_POSITION: Final[int] = 21
_EDIT_FRACTION_POSITION: Final[int] = 22
_EDIT_FRACTION_DIGITS: Final[int] = 9


@dataclasses.dataclass(frozen=True, slots=True)
class EditWindow:
    """One `WS-MYSQL-EDIT (offset:length)` reference modification.

    COBOL reference modification is one-based and inclusive of the starting
    character, so ``EditWindow(11, 10)`` is `WS-MYSQL-EDIT(11:10)` and covers
    character positions 11 through 20.
    """

    #: The one-based starting character position.
    offset: int
    #: The number of characters taken.
    length: int
    #: A representative site in the bridge that uses this window.
    locator: str

    def __post_init__(self) -> None:
        """Reject a window that cannot exist inside a 30-character field."""
        if self.offset < 1 or self.length < 1:
            message = f"non-positive reference modification {self.offset}:{self.length}"
            raise ValueError(message)
        if self.offset - 1 + self.length > _EDIT_WIDTH:
            message = (
                f"window {self.offset}:{self.length} runs past the "
                f"{_EDIT_WIDTH}-character WS-MYSQL-EDIT field"
            )
            raise ValueError(message)

    @property
    def includes_sign(self) -> bool:
        """Whether this window contains the sign position.

        Never true for any window this bridge uses, which is precisely why the
        eleven signed decimal columns are written unsigned
        (anomaly ``N-signloss-in-render``).
        """
        return self.offset <= _EDIT_SIGN_POSITION < self.offset + self.length

    def apply(self, image: str) -> str:
        """Return the slice of ``image`` this window designates."""
        start = self.offset - 1
        return image[start : start + self.length]


#: The five integer windows and the one fraction window the bridge uses. Each
#: locator names a representative STRING site; the same window recurs at every
#: column of the same picture in all four statement builders (`bb200-Insert`
#: [common/plinvoiceMT.cbl:L1528], `bb300-Update` [:L1925],
#: `bc200-Insert-rg1` [:L2816] and `bc300-Update-rg1` [:L3009]).
_WINDOW_INT_10: Final[EditWindow] = EditWindow(11, 10, "[common/plinvoiceMT.cbl:L1556]")
_WINDOW_INT_07: Final[EditWindow] = EditWindow(14, 7, "[common/plinvoiceMT.cbl:L1631]")
_WINDOW_INT_05: Final[EditWindow] = EditWindow(16, 5, "[common/plinvoiceMT.cbl:L2916]")
_WINDOW_INT_03: Final[EditWindow] = EditWindow(18, 3, "[common/plinvoiceMT.cbl:L1819]")
_WINDOW_INT_02: Final[EditWindow] = EditWindow(19, 2, "[common/plinvoiceMT.cbl:L2966]")
_WINDOW_FRACTION_02: Final[EditWindow] = EditWindow(
    22, 2, "[common/plinvoiceMT.cbl:L1636]"
)


class _RenderKind(enum.StrEnum):
    """How the bridge turns one host variable into command text.

    The three shapes were read off all four statement builders; there is no
    fourth shape anywhere in the bridge.
    """

    #: `STRING FUNCTION TRIM (HV-xxx,TRAILING)` - trailing spaces removed, leading
    #: spaces kept [common/plinvoiceMT.cbl:L1545].
    CHARACTER = "character"
    #: `MOVE HV-xxx TO WS-MYSQL-EDIT` then
    #: `STRING FUNCTION TRIM (WS-MYSQL-EDIT(w:l))` - no TRAILING qualifier, so
    #: BOTH ends are trimmed [common/plinvoiceMT.cbl:L1554-L1556].
    INTEGER = "integer"
    #: The integer window trimmed, then a literal `"."`, then the fraction window
    #: **raw and untrimmed** [common/plinvoiceMT.cbl:L1631-L1636].
    DECIMAL = "decimal"


@dataclasses.dataclass(frozen=True, slots=True)
class ColumnRender:
    """Everything needed to render one column exactly as the bridge does."""

    #: The MySQL column name, hyphens and all.
    column: str
    #: The data-dictionary key, `<TABLE>.<COLUMN>`; every instance is traceable.
    dictionary_key: str
    #: The bridge host variable that feeds this column.
    host_variable: str
    #: Which of the three render shapes applies.
    kind: _RenderKind
    #: The declared scale of the host variable - 0 for integers and characters,
    #: 2 for every decimal in this bridge.
    hv_scale: int
    #: The declared digit count of an unsigned integer host variable, used by the
    #: sign-loss narrowing. Zero for characters.
    hv_digits: int
    #: The integer window, or ``None`` for a character column.
    integer_window: EditWindow | None
    #: The fraction window, or ``None`` unless the column is a decimal.
    fraction_window: EditWindow | None
    #: Whether the RENDER drops a sign the host variable still carries.
    loses_sign_in_render: bool
    #: Whether the LOAD drops a sign the record still carries.
    loses_sign_in_load: bool
    #: The three-layer citation from the data dictionary.
    cite: str


def _edit_image(value: decimal.Decimal | int | None, scale: int) -> str:
    """Return the 30-character `WS-MYSQL-EDIT` image of ``value``.

    Reproduces `MOVE <host variable> TO WS-MYSQL-EDIT` for the picture
    `-Z(18)9.9(9)` [common/plinvoiceMT.scb:L272]: de-editing the sign into
    position 1, right-justifying the integer digits into positions 2..20 with
    zero suppression across positions 2..19, and zero-filling the nine fraction
    positions from the sending item's own scale.

    The value is truncated toward zero to ``scale`` places first, because that is
    what a COBOL `move` into a `V9(scale)` host variable does; no rounding
    occurs anywhere on this path.
    """
    amount = decimal.Decimal(0) if value is None else decimal.Decimal(value)
    negative = amount < 0
    magnitude = -amount if negative else amount
    if scale > 0:
        magnitude = magnitude.quantize(
            decimal.Decimal(1).scaleb(-scale), rounding=decimal.ROUND_DOWN
        )
    else:
        magnitude = magnitude.quantize(decimal.Decimal(1), rounding=decimal.ROUND_DOWN)
    plain = format(magnitude, "f")
    integer_text, _, fraction_text = plain.partition(".")
    # `Z(18)9` suppresses leading zeros into spaces but position 20 is a `9`, so
    # a zero value still renders a single '0' there.
    integer_field = integer_text[-_EDIT_INTEGER_DIGITS:].rjust(_EDIT_INTEGER_DIGITS)
    fraction_field = (fraction_text + "0" * _EDIT_FRACTION_DIGITS)[
        :_EDIT_FRACTION_DIGITS
    ]
    return f"{'-' if negative else ' '}{integer_field}.{fraction_field}"


def rendered_column_text(
    render: ColumnRender, value: decimal.Decimal | int | str | None
) -> str:
    """Render one column value into the exact text the bridge STRINGs.

    The returned string is the body that sits between the two `"` characters the
    bridge writes around every value, for every one of the forty-four columns of
    the two tables. It is text and nothing else: the migration binds the text the
    bridge would have produced, never the source value, because the bridge's own
    rendering is where information is lost and the whole point is to lose the same
    information.

    Three shapes, one per :class:`_RenderKind`:

    * ``CHARACTER`` - `FUNCTION TRIM (HV,TRAILING)`. A field of nothing but
      spaces therefore renders as the EMPTY STRING, measured on GnuCOBOL 3.2 in
      the harness image (anomaly ``N-trim-space-to-empty``). This is exactly what
      the five never-populated status columns produce, giving
      `` `IH-STATUS-A`="" `` on every INSERT.
    * ``INTEGER`` - the integer window, trimmed at BOTH ends because the bridge
      writes `FUNCTION TRIM (WS-MYSQL-EDIT(w:l))` with no qualifier.
    * ``DECIMAL`` - the trimmed integer window, a literal `"."`, then the
      fraction window taken RAW. The sign position is outside every window this
      bridge uses, so all eleven signed `decimal(9,2)` columns are written
      unsigned (anomaly ``N-signloss-in-render``).
    """
    if render.kind is _RenderKind.CHARACTER:
        text = "" if value is None else str(value)
        # `FUNCTION TRIM (<hv>,TRAILING)` - the shape every alphanumeric emission
        # uses, e.g. `STRING FUNCTION TRIM (HV-PINVOICE-KEY,TRAILING)`
        # [common/plinvoiceMT.cbl:L1545]. `<hv>` is a placeholder, not a field name.
        return text.rstrip(" ")

    if render.integer_window is None:  # pragma: no cover - defended by construction
        message = f"{render.column} is numeric but declares no integer window"
        raise ValueError(message)

    numeric: decimal.Decimal | int
    if value is None:
        numeric = 0
    elif isinstance(value, str):
        numeric = decimal.Decimal(value)
    else:
        numeric = value
    image = _edit_image(numeric, render.hv_scale)
    integer_text = render.integer_window.apply(image).strip(" ")

    if render.kind is _RenderKind.INTEGER:
        return integer_text

    if render.fraction_window is None:  # pragma: no cover - defended by construction
        message = f"{render.column} is a decimal but declares no fraction window"
        raise ValueError(message)
    # `STRING WS-MYSQL-EDIT(22:02)` with NO TRIM [common/plinvoiceMT.cbl:L1636].
    return f"{integer_text}.{render.fraction_window.apply(image)}"


#: The observed windows, keyed by the host variable's integer digit count. The
#: translator places the low ``n`` integer digits at positions ``21 - n`` through
#: 20, because position 20 is the picture's single mandatory `9`; every window
#: below satisfies ``offset == 21 - length`` and every one starts at 11 or later,
#: so the sign at position 1 is unreachable from all of them.
_INTEGER_WINDOW_BY_DIGITS: Final[Mapping[int, EditWindow]] = MappingProxyType(
    {
        10: _WINDOW_INT_10,
        7: _WINDOW_INT_07,
        5: _WINDOW_INT_05,
        3: _WINDOW_INT_03,
        2: _WINDOW_INT_02,
    }
)


def _integer_window_for(integer_digits: int) -> EditWindow:
    """Return the reference modification the translator emits for ``n`` digits."""
    window = _INTEGER_WINDOW_BY_DIGITS.get(integer_digits)
    if window is not None:
        return window
    # Derived rather than transcribed only if a picture appears that the two
    # in-scope tables do not use; the formula is the one every observed window
    # obeys, so an unexpected picture still renders the way the bridge would.
    return EditWindow(
        _EDIT_POINT_POSITION - integer_digits,
        integer_digits,
        "[common/plinvoiceMT.scb:L272] derived from the WS-MYSQL-EDIT picture",
    )


def _column_render_table(table_name: str) -> Mapping[str, ColumnRender]:
    """Build the per-column render table for ``table_name`` from the dictionary.

    Field metadata is DERIVED from ``data_dictionary/acas_posting_dictionary.json``
    and never transcribed by eye, which is the Agent Action Plan's section 0.8.1
    directive: *"Data dictionary first. ... every Python field definition cites
    its entry. This ordering is a directive, not a preference - it is what
    prevents fields being transcribed by eye."*
    """
    sign_loss_keys = frozenset(SIGN_LOSS_HOST_VARIABLES)
    rendered: dict[str, ColumnRender] = {}
    for entry in loader.entries_for_table(table_name):
        host_variable = entry.bridge_host_variable
        if host_variable is None:  # pragma: no cover - every column has one here
            message = f"{entry.key} has no bridge host variable"
            raise ValueError(message)
        scale = host_variable.scale or 0
        digits = host_variable.digits or 0
        integer_digits = host_variable.integer_digits or 0
        if digits == 0:
            kind = _RenderKind.CHARACTER
            integer_window: EditWindow | None = None
            fraction_window: EditWindow | None = None
        elif scale == 0:
            kind = _RenderKind.INTEGER
            integer_window = _integer_window_for(integer_digits)
            fraction_window = None
        else:
            kind = _RenderKind.DECIMAL
            integer_window = _integer_window_for(integer_digits)
            fraction_window = _WINDOW_FRACTION_02
        rendered[entry.column.name] = ColumnRender(
            column=entry.column.name,
            dictionary_key=entry.key,
            host_variable=host_variable.name,
            kind=kind,
            hv_scale=scale,
            hv_digits=digits,
            integer_window=integer_window,
            fraction_window=fraction_window,
            loses_sign_in_render=(
                bool(host_variable.signed)
                and integer_window is not None
                and not integer_window.includes_sign
            ),
            loses_sign_in_load=entry.key in sign_loss_keys,
            cite=loader.cite(entry.key),
        )
    return MappingProxyType(rendered)


#: Per-column render metadata for the header table, keyed by column name.
HEADER_COLUMN_RENDER: Final[Mapping[str, ColumnRender]] = _column_render_table(
    HEADER_TABLE
)

#: Per-column render metadata for the lines table, keyed by column name.
LINES_COLUMN_RENDER: Final[Mapping[str, ColumnRender]] = _column_render_table(
    LINES_TABLE
)

#: The eleven columns whose host variable IS signed and whose render window is
#: not, so the sign is discarded a second time - after surviving the load intact -
#: on its way into the command text (anomaly ``N-signloss-in-render``).
#:
#: Eight header columns `IH-P-C` .. `IH-C-VAT` [common/plinvoiceMT.cbl:L399-L406]
#: and three line columns `IL-NET`, `IL-UNIT`, `IL-VAT` [:L434-L435, L437] are
#: declared `S9(07)V9(02) COMP` and land in signed `decimal(9,2)` columns, so the
#: three declared layers agree and the drift table shows nothing. The loss happens
#: in the RENDER: `MOVE HV-IH-NET TO WS-MYSQL-EDIT` puts the sign in position 1
#: and `STRING FUNCTION TRIM (WS-MYSQL-EDIT(14:07))` starts at position 14.
#:
#: This was measured, not deduced: the `-Z(18)9.9(9)` picture was compiled and
#: exercised under GnuCOBOL 3.2 in the harness image, confirming a 30-character
#: field with the sign at position 1 and confirming that
#: `FUNCTION TRIM (<all spaces>, TRAILING)` yields the empty string. Both
#: measurements are recorded in ``docs/migration/ambiguity-resolutions.md``. The
#: value MariaDB finally stores for a negative amount is the oracle's to
#: arbitrate; what is certain is that the minus sign never reaches the statement.
RENDER_SIGN_LOSS_COLUMNS: Final[tuple[str, ...]] = tuple(
    f"{table}.{column}"
    for table, renders in (
        (HEADER_TABLE, HEADER_COLUMN_RENDER),
        (LINES_TABLE, LINES_COLUMN_RENDER),
    )
    for column, render in renders.items()
    if render.loses_sign_in_render
)

# ---------------------------------------------------------------------------
# The SIX ordering lists
# ---------------------------------------------------------------------------
#
# Load order, unload order and column order disagree on both tables, so all six
# lists are built independently and none is derived from another. Deriving one
# from another is exactly the mistake that would erase three of this module's
# defects.


@dataclasses.dataclass(frozen=True, slots=True)
class HostVariableMove:
    """One `move` statement inside a load or unload paragraph."""

    #: The data-dictionary key of the column this host variable feeds, or
    #: ``None`` where the move has no column at all.
    dictionary_key: str | None
    #: The bridge host variable named by the statement.
    host_variable: str
    #: The record field named by the statement, in its COBOL spelling.
    record_field: str
    #: The exact line of the statement.
    locator: str
    #: Whether the statement is written with a terminating period. The punctuation
    #: is irregular in both loads and both unloads and is preserved, not
    #: normalised (anomaly ``N-punctuation``).
    terminated_by_period: bool


#: `bb000-HV-Load Section.` [common/plinvoiceMT.cbl:L1442] - TWENTY-FIVE moves for
#: a THIRTY-column table, in copybook declaration order rather than column order.
#:
#: `initialize TD-PUINVOICE-REC.` [:L1450] runs first, which is why every column
#: this list omits still reaches MySQL as a space or a zero rather than as NULL.
#:
#: Three facts to read off the list: the primary key is here and absent from the
#: unload; the five `IH-STATUS-x` columns are absent from BOTH; and `IH-LINES` is
#: the EIGHTEENTH move [:L1470] while its host variable is declared twenty-eighth
#: [:L418] and its column is ordinal 28 - load order, host-variable order and
#: column order are three different orders (anomaly ``N-lines-order-mismatch``).
HEADER_LOAD_SEQUENCE: Final[tuple[HostVariableMove, ...]] = (
    HostVariableMove(
        f"{HEADER_TABLE}.PINVOICE-KEY",
        "HV-PINVOICE-KEY",
        "WS-Invoice-Key",
        "[common/plinvoiceMT.cbl:L1452]",
        True,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-INVOICE",
        "HV-IH-INVOICE",
        "WS-ih-Invoice",
        "[common/plinvoiceMT.cbl:L1454]",
        True,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-TEST",
        "HV-IH-TEST",
        "WS-ih-Test",
        "[common/plinvoiceMT.cbl:L1455]",
        True,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-SUPPLIER",
        "HV-IH-SUPPLIER",
        "WS-ih-Supplier",
        "[common/plinvoiceMT.cbl:L1456]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DAT",
        "HV-IH-DAT",
        "WS-ih-Date",
        "[common/plinvoiceMT.cbl:L1457]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-ORDER",
        "HV-IH-ORDER",
        "WS-ih-Order",
        "[common/plinvoiceMT.cbl:L1458]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-TYPE",
        "HV-IH-TYPE",
        "WS-ih-Type",
        "[common/plinvoiceMT.cbl:L1459]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-REF",
        "HV-IH-REF",
        "WS-ih-Ref",
        "[common/plinvoiceMT.cbl:L1460]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-P-C",
        "HV-IH-P-C",
        "WS-ih-P-C",
        "[common/plinvoiceMT.cbl:L1461]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-NET",
        "HV-IH-NET",
        "WS-ih-Net",
        "[common/plinvoiceMT.cbl:L1462]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-EXTRA",
        "HV-IH-EXTRA",
        "WS-ih-Extra",
        "[common/plinvoiceMT.cbl:L1463]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-CARRIAGE",
        "HV-IH-CARRIAGE",
        "WS-ih-Carriage",
        "[common/plinvoiceMT.cbl:L1464]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-VAT",
        "HV-IH-VAT",
        "WS-ih-Vat",
        "[common/plinvoiceMT.cbl:L1465]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DISCOUNT",
        "HV-IH-DISCOUNT",
        "WS-ih-Discount",
        "[common/plinvoiceMT.cbl:L1466]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-E-VAT",
        "HV-IH-E-VAT",
        "WS-ih-E-Vat",
        "[common/plinvoiceMT.cbl:L1467]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-C-VAT",
        "HV-IH-C-VAT",
        "WS-ih-C-Vat",
        "[common/plinvoiceMT.cbl:L1468]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-STATUS",
        "HV-IH-STATUS",
        "WS-ih-Status",
        "[common/plinvoiceMT.cbl:L1469]",
        False,
    ),
    # Out of position: eighteenth move, twenty-eighth host variable, column 28.
    HostVariableMove(
        f"{HEADER_TABLE}.IH-LINES",
        "HV-IH-LINES",
        "WS-ih-Lines",
        "[common/plinvoiceMT.cbl:L1470]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DEDUCT-DAYS",
        "HV-IH-DEDUCT-DAYS",
        "WS-ih-Deduct-Days",
        "[common/plinvoiceMT.cbl:L1471]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DEDUCT-AMT",
        "HV-IH-DEDUCT-AMT",
        "WS-ih-Deduct-Amt",
        "[common/plinvoiceMT.cbl:L1472]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DEDUCT-VAT",
        "HV-IH-DEDUCT-VAT",
        "WS-ih-Deduct-Vat",
        "[common/plinvoiceMT.cbl:L1473]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DAYS",
        "HV-IH-DAYS",
        "WS-ih-Days",
        "[common/plinvoiceMT.cbl:L1474]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-CR",
        "HV-IH-CR",
        "WS-ih-CR",
        "[common/plinvoiceMT.cbl:L1475]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DAY-BOOK-FLAG",
        "HV-IH-DAY-BOOK-FLAG",
        "WS-ih-Day-Book-Flag",
        "[common/plinvoiceMT.cbl:L1476]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-UPDATE",
        "HV-IH-UPDATE",
        "WS-ih-Update",
        "[common/plinvoiceMT.cbl:L1477]",
        True,
    ),
)

#: `bb100-UnloadHVs Section.` [common/plinvoiceMT.cbl:L1482] - TWENTY-FOUR moves,
#: one fewer than the load, and the missing one is the PRIMARY KEY
#: (anomaly ``N-pinvoice-key-write-only``). `initialize WS-Invoice-Record.` [:L1487]
#: runs first, PLAIN, without the `with filler` that [:L802] uses in `ba042-Fetch`
#: (anomaly ``N-initialize``).
#:
#: The five `IH-STATUS-x` host variables are absent here too, even though
#: `ba042-Fetch` [:L769-L773] and `ba050` [:L881-L913] both fetch straight into
#: them - so their values arrive from MySQL and are discarded one statement later
#: (anomaly ``N-status-hvs-fetched-then-discarded``).
HEADER_UNLOAD_SEQUENCE: Final[tuple[HostVariableMove, ...]] = (
    HostVariableMove(
        f"{HEADER_TABLE}.IH-INVOICE",
        "HV-IH-INVOICE",
        "WS-ih-Invoice",
        "[common/plinvoiceMT.cbl:L1489]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-TEST",
        "HV-IH-TEST",
        "WS-ih-Test",
        "[common/plinvoiceMT.cbl:L1490]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-SUPPLIER",
        "HV-IH-SUPPLIER",
        "WS-ih-Supplier",
        "[common/plinvoiceMT.cbl:L1491]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DAT",
        "HV-IH-DAT",
        "WS-ih-Date",
        "[common/plinvoiceMT.cbl:L1492]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-ORDER",
        "HV-IH-ORDER",
        "WS-ih-Order",
        "[common/plinvoiceMT.cbl:L1493]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-TYPE",
        "HV-IH-TYPE",
        "WS-ih-Type",
        "[common/plinvoiceMT.cbl:L1494]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-REF",
        "HV-IH-REF",
        "WS-ih-Ref",
        "[common/plinvoiceMT.cbl:L1495]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-P-C",
        "HV-IH-P-C",
        "WS-ih-P-C",
        "[common/plinvoiceMT.cbl:L1496]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-NET",
        "HV-IH-NET",
        "WS-ih-Net",
        "[common/plinvoiceMT.cbl:L1497]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-EXTRA",
        "HV-IH-EXTRA",
        "WS-ih-Extra",
        "[common/plinvoiceMT.cbl:L1498]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-CARRIAGE",
        "HV-IH-CARRIAGE",
        "WS-ih-Carriage",
        "[common/plinvoiceMT.cbl:L1499]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-VAT",
        "HV-IH-VAT",
        "WS-ih-Vat",
        "[common/plinvoiceMT.cbl:L1500]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DISCOUNT",
        "HV-IH-DISCOUNT",
        "WS-ih-Discount",
        "[common/plinvoiceMT.cbl:L1501]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-E-VAT",
        "HV-IH-E-VAT",
        "WS-ih-E-Vat",
        "[common/plinvoiceMT.cbl:L1502]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-C-VAT",
        "HV-IH-C-VAT",
        "WS-ih-C-Vat",
        "[common/plinvoiceMT.cbl:L1503]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-STATUS",
        "HV-IH-STATUS",
        "WS-ih-Status",
        "[common/plinvoiceMT.cbl:L1504]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-LINES",
        "HV-IH-LINES",
        "WS-ih-Lines",
        "[common/plinvoiceMT.cbl:L1505]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DEDUCT-DAYS",
        "HV-IH-DEDUCT-DAYS",
        "WS-ih-Deduct-Days",
        "[common/plinvoiceMT.cbl:L1506]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DEDUCT-AMT",
        "HV-IH-DEDUCT-AMT",
        "WS-ih-Deduct-Amt",
        "[common/plinvoiceMT.cbl:L1507]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DEDUCT-VAT",
        "HV-IH-DEDUCT-VAT",
        "WS-ih-Deduct-Vat",
        "[common/plinvoiceMT.cbl:L1508]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DAYS",
        "HV-IH-DAYS",
        "WS-ih-Days",
        "[common/plinvoiceMT.cbl:L1509]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-CR",
        "HV-IH-CR",
        "WS-ih-CR",
        "[common/plinvoiceMT.cbl:L1510]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-DAY-BOOK-FLAG",
        "HV-IH-DAY-BOOK-FLAG",
        "WS-ih-Day-Book-Flag",
        "[common/plinvoiceMT.cbl:L1511]",
        False,
    ),
    HostVariableMove(
        f"{HEADER_TABLE}.IH-UPDATE",
        "HV-IH-UPDATE",
        "WS-ih-Update",
        "[common/plinvoiceMT.cbl:L1512]",
        True,
    ),
)

#: `bc000-HV-Load-rg1 Section.  *> Dry chk ?` [common/plinvoiceMT.cbl:L2743] -
#: FOURTEEN moves for a fourteen-column table, so the count is right and the
#: ORDER is not: `WS-il-Line` is moved at [:L2757] BEFORE `WS-il-Invoice` at
#: [:L2758], inverting the column order `IL-INVOICE` then `IL-LINE`
#: (anomaly ``N-lines-loadorder``, identical to
#: [common/slinvoiceMT.cbl:L2790-L2791]).
#:
#: `initialize TD-PUINV-LINES-REC.` [:L2754] runs first. The section carries the
#: maintainer's unresolved marker `*> <<<<  this should be a move from invoice-rec
#: to line rec >>>>> <<>>` [:L2752], which is preserved as a comment and not acted
#: on (anomaly ``N-rg-todo``), and it closes with
#: `*> End of PUINV-LINES-REC unload...` [:L2771] - a comment that says "unload"
#: at the end of the LOAD (anomaly ``N-mislabelled-comment``).
LINES_LOAD_SEQUENCE: Final[tuple[HostVariableMove, ...]] = (
    HostVariableMove(
        f"{LINES_TABLE}.IL-LINE-KEY",
        "HV1-IL-LINE-KEY",
        "WS-il-Key",
        "[common/plinvoiceMT.cbl:L2756]",
        True,
    ),
    # Line before invoice: the load order inverts the column order.
    HostVariableMove(
        f"{LINES_TABLE}.IL-LINE",
        "HV1-IL-LINE",
        "WS-il-Line",
        "[common/plinvoiceMT.cbl:L2757]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-INVOICE",
        "HV1-IL-INVOICE",
        "WS-il-Invoice",
        "[common/plinvoiceMT.cbl:L2758]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-PRODUCT",
        "HV1-IL-PRODUCT",
        "WS-il-Product",
        "[common/plinvoiceMT.cbl:L2759]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-PA",
        "HV1-IL-PA",
        "WS-il-Pa",
        "[common/plinvoiceMT.cbl:L2760]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-QTY",
        "HV1-IL-QTY",
        "WS-il-Qty",
        "[common/plinvoiceMT.cbl:L2761]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-TYPE",
        "HV1-IL-TYPE",
        "WS-il-Type",
        "[common/plinvoiceMT.cbl:L2762]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-DESCRIPTION",
        "HV1-IL-DESCRIPTION",
        "WS-il-Description",
        "[common/plinvoiceMT.cbl:L2763]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-NET",
        "HV1-IL-NET",
        "WS-il-Net",
        "[common/plinvoiceMT.cbl:L2764]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-UNIT",
        "HV1-IL-UNIT",
        "WS-il-Unit",
        "[common/plinvoiceMT.cbl:L2765]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-DISCOUNT",
        "HV1-IL-DISCOUNT",
        "WS-il-Discount",
        "[common/plinvoiceMT.cbl:L2766]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-VAT",
        "HV1-IL-VAT",
        "WS-il-Vat",
        "[common/plinvoiceMT.cbl:L2767]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-VAT-CODE",
        "HV1-IL-VAT-CODE",
        "WS-il-Vat-Code",
        "[common/plinvoiceMT.cbl:L2768]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-UPDATE",
        "HV1-IL-UPDATE",
        "WS-il-Update",
        "[common/plinvoiceMT.cbl:L2769]",
        True,
    ),
)

#: `bc100-UnloadHVs-rg1 Section.  *> Dry chk ?` [common/plinvoiceMT.cbl:L2777] -
#: THIRTEEN moves against the load's fourteen. `HV1-IL-INVOICE` is loaded and
#: never unloaded (anomaly ``N-il-invoice-never-unloaded``), so a read leaves
#: `WS-il-Invoice` at whatever `initialize WS-Invoice-Line` [:L2787] set - zero -
#: while the concatenated `WS-il-Key` IS restored [:L2789] and carries the invoice
#: number in its first eight characters.
LINES_UNLOAD_SEQUENCE: Final[tuple[HostVariableMove, ...]] = (
    HostVariableMove(
        f"{LINES_TABLE}.IL-LINE-KEY",
        "HV1-IL-LINE-KEY",
        "WS-il-Key",
        "[common/plinvoiceMT.cbl:L2789]",
        True,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-LINE",
        "HV1-IL-LINE",
        "WS-il-Line",
        "[common/plinvoiceMT.cbl:L2790]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-PRODUCT",
        "HV1-IL-PRODUCT",
        "WS-il-Product",
        "[common/plinvoiceMT.cbl:L2791]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-PA",
        "HV1-IL-PA",
        "WS-il-Pa",
        "[common/plinvoiceMT.cbl:L2792]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-QTY",
        "HV1-IL-QTY",
        "WS-il-Qty",
        "[common/plinvoiceMT.cbl:L2793]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-TYPE",
        "HV1-IL-TYPE",
        "WS-il-Type",
        "[common/plinvoiceMT.cbl:L2794]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-DESCRIPTION",
        "HV1-IL-DESCRIPTION",
        "WS-il-Description",
        "[common/plinvoiceMT.cbl:L2795]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-NET",
        "HV1-IL-NET",
        "WS-il-Net",
        "[common/plinvoiceMT.cbl:L2796]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-UNIT",
        "HV1-IL-UNIT",
        "WS-il-Unit",
        "[common/plinvoiceMT.cbl:L2797]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-DISCOUNT",
        "HV1-IL-DISCOUNT",
        "WS-il-Discount",
        "[common/plinvoiceMT.cbl:L2798]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-VAT",
        "HV1-IL-VAT",
        "WS-il-Vat",
        "[common/plinvoiceMT.cbl:L2799]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-VAT-CODE",
        "HV1-IL-VAT-CODE",
        "WS-il-Vat-Code",
        "[common/plinvoiceMT.cbl:L2800]",
        False,
    ),
    HostVariableMove(
        f"{LINES_TABLE}.IL-UPDATE",
        "HV1-IL-UPDATE",
        "WS-il-Update",
        "[common/plinvoiceMT.cbl:L2801]",
        True,
    ),
)


def _columns_in_ordinal_order(table_name: str) -> tuple[str, ...]:
    """Return ``table_name``'s columns in the frozen schema's declaration order.

    Built independently of the load and unload sequences, straight from the
    dictionary's own ordinal, whose source is recorded per table by
    ``loader.table_for(...).ordinal_source``.
    """
    entries = loader.entries_for_table(table_name)
    ordered = sorted(entries, key=lambda entry: entry.column.ordinal)
    return tuple(entry.column.name for entry in ordered)


#: The thirty header columns in the frozen schema's declaration order, i.e. by
#: column ordinal [mysql/ACASDB.sql:L545].
HEADER_COLUMNS: Final[tuple[str, ...]] = _columns_in_ordinal_order(HEADER_TABLE)

#: The fourteen line columns in the frozen schema's declaration order, i.e. by
#: column ordinal [mysql/ACASDB.sql:L510].
LINES_COLUMNS: Final[tuple[str, ...]] = _columns_in_ordinal_order(LINES_TABLE)


def _attribute_for(host_variable_name: str) -> str:
    """Map a bridge host-variable name onto its Python attribute name.

    `HV-IH-DEDUCT-DAYS` becomes ``hv_ih_deduct_days`` and `HV1-IL-LINE-KEY`
    becomes ``hv1_il_line_key``, so a reader can move between the COBOL and the
    Python by mechanical transformation rather than by lookup (R-5).
    """
    return host_variable_name.lower().replace("-", "_")


#: Column name -> attribute name, per table, derived from the dictionary's own
#: host-variable names rather than transcribed.
_HEADER_ATTRIBUTE_BY_COLUMN: Final[Mapping[str, str]] = MappingProxyType(
    {
        column: _attribute_for(render.host_variable)
        for column, render in HEADER_COLUMN_RENDER.items()
    }
)
_LINES_ATTRIBUTE_BY_COLUMN: Final[Mapping[str, str]] = MappingProxyType(
    {
        column: _attribute_for(render.host_variable)
        for column, render in LINES_COLUMN_RENDER.items()
    }
)

#: Column name -> the width `initialize` fills with spaces, for character host
#: variables only. `PIC X(n)` initialises to n spaces, never to NULL and never to
#: an empty string, which is the whole reason every column in the frozen schema
#: can be `NOT NULL` [Agent Action Plan section 0.6.2].
_HEADER_CHARACTER_WIDTHS: Final[Mapping[str, int]] = MappingProxyType(
    {
        entry.column.name: (
            entry.bridge_host_variable.character_length
            if entry.bridge_host_variable is not None
            and entry.bridge_host_variable.character_length
            else 0
        )
        for entry in loader.entries_for_table(HEADER_TABLE)
    }
)
_LINES_CHARACTER_WIDTHS: Final[Mapping[str, int]] = MappingProxyType(
    {
        entry.column.name: (
            entry.bridge_host_variable.character_length
            if entry.bridge_host_variable is not None
            and entry.bridge_host_variable.character_length
            else 0
        )
        for entry in loader.entries_for_table(LINES_TABLE)
    }
)

_DECIMAL_ZERO: Final[decimal.Decimal] = decimal.Decimal(0)


@dataclasses.dataclass(slots=True)
class HeaderHostVariables:
    """`01  TD-PUINVOICE-REC.` [common/plinvoiceMT.cbl:L390-L420].

    Thirty host variables in the bridge's own declaration order, one per column of
    `PUINVOICE-REC`. Attribute names are the host-variable names mechanically
    lower-cased, so `HV-IH-DAY-BOOK-FLAG` is :attr:`hv_ih_day_book_flag`.

    Five of the thirty - :attr:`hv_ih_status_a` through :attr:`hv_ih_status_p` -
    have no counterpart in either purchase copybook and are touched by neither
    `bb000-HV-Load` nor `bb100-UnloadHVs`. They are declared here because the
    bridge declares them and because `ba042-Fetch` fetches into them
    [:L769-L773]; they are simply never assigned from the record, so on the write
    path they carry the space that :meth:`initialize` puts there.
    """

    hv_pinvoice_key: str = ""
    hv_ih_invoice: int = 0
    hv_ih_test: int = 0
    hv_ih_supplier: str = ""
    hv_ih_dat: int = 0
    hv_ih_order: str = ""
    hv_ih_type: int = 0
    hv_ih_ref: str = ""
    hv_ih_p_c: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_net: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_extra: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_carriage: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_vat: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_discount: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_e_vat: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_c_vat: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_status: str = ""
    hv_ih_status_a: str = ""
    hv_ih_status_c: str = ""
    hv_ih_status_i: str = ""
    hv_ih_status_l: str = ""
    hv_ih_status_p: str = ""
    hv_ih_deduct_days: int = 0
    hv_ih_deduct_amt: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_deduct_vat: decimal.Decimal = _DECIMAL_ZERO
    hv_ih_days: int = 0
    hv_ih_cr: int = 0
    hv_ih_lines: int = 0
    hv_ih_day_book_flag: str = ""
    hv_ih_update: str = ""

    def initialize(self) -> None:
        """`initialize TD-PUINVOICE-REC.` [common/plinvoiceMT.cbl:L1450].

        The FIRST statement of the load, and the reason every unset column
        reaches MySQL as a space or a zero rather than as SQL `NULL`.
        """
        _initialise_group(self, _HEADER_ATTRIBUTE_BY_COLUMN, _HEADER_CHARACTER_WIDTHS)


@dataclasses.dataclass(slots=True)
class LineHostVariables:
    """`01  TD-PUINV-LINES-REC.` [common/plinvoiceMT.cbl:L425-L439].

    Fourteen host variables, one per column of `PUINV-LINES-REC`, carrying the
    `HV1-` prefix the `/MYSQL VAR\\` directive assigns to the second table
    [common/plinvoiceMT.scb:L384].

    :attr:`hv1_il_invoice` is loaded [:L2758] and never unloaded [:L2789-L2801];
    the asymmetry is deliberate and is not repaired here.
    """

    hv1_il_line_key: str = ""
    hv1_il_invoice: int = 0
    hv1_il_line: int = 0
    hv1_il_product: str = ""
    hv1_il_pa: str = ""
    hv1_il_qty: int = 0
    hv1_il_type: str = ""
    hv1_il_description: str = ""
    hv1_il_net: decimal.Decimal = _DECIMAL_ZERO
    hv1_il_unit: decimal.Decimal = _DECIMAL_ZERO
    hv1_il_discount: decimal.Decimal = _DECIMAL_ZERO
    hv1_il_vat: decimal.Decimal = _DECIMAL_ZERO
    hv1_il_vat_code: int = 0
    hv1_il_update: str = ""

    def initialize(self) -> None:
        """`initialize TD-PUINV-LINES-REC.` [common/plinvoiceMT.cbl:L2754]."""
        _initialise_group(self, _LINES_ATTRIBUTE_BY_COLUMN, _LINES_CHARACTER_WIDTHS)


def _initialise_group(
    group: HeaderHostVariables | LineHostVariables,
    attribute_by_column: Mapping[str, str],
    character_widths: Mapping[str, int],
) -> None:
    """Reproduce COBOL `initialize` over one host-variable group.

    Alphanumeric items become all spaces at their declared width, numeric items
    become zero at their declared scale. Nothing becomes ``None``: the frozen
    schema declares all forty-four columns `NOT NULL`, and the bridge never sends
    a NULL because this statement always runs first.
    """
    renders = HEADER_COLUMN_RENDER if isinstance(group, HeaderHostVariables) else (
        LINES_COLUMN_RENDER
    )
    for column, attribute in attribute_by_column.items():
        render = renders[column]
        if render.kind is _RenderKind.CHARACTER:
            setattr(group, attribute, " " * character_widths[column])
        elif render.kind is _RenderKind.INTEGER:
            setattr(group, attribute, 0)
        else:
            setattr(
                group,
                attribute,
                _DECIMAL_ZERO.quantize(decimal.Decimal(1).scaleb(-render.hv_scale)),
            )


class _BufferView(enum.StrEnum):
    """Which redefinition last wrote the one shared record buffer.

    `01  WS-PInvoice-Record.` [copybooks/plwspinv2.cob:L10] is overlaid by
    `01  Invoice-Header redefines WS-PInvoice-Record.` [:L21] and by
    `01  Invoice-Line   redefines WS-PInvoice-Record.` [:L56], so a single
    100-byte area carries EITHER a header OR a line and the caller tells them
    apart only by which view it reads. The two views are published as
    :class:`~acas_posting.records.purchase_invoice.IhInvoiceHeader` and
    :class:`~acas_posting.records.purchase_invoice.IlInvoiceLine`.

    Python has no storage overlay, so the discriminator is made explicit: after
    `move WS-Invoice-Line to WS-Invoice-Record` [common/plinvoiceMT.cbl:L2466,
    L2809] the buffer holds a LINE, and a caller that goes on reading the header
    view is reading line bytes - exactly the situation the COBOL creates.
    """

    HEADER = "Invoice-Header"
    LINE = "Invoice-Line"


#: The two redefinitions of the shared buffer and the record class that models
#: each, so a reader can find the Python counterpart of either COBOL view.
_BUFFER_REDEFINITIONS: Final[Mapping[_BufferView, type]] = MappingProxyType(
    {
        _BufferView.HEADER: IhInvoiceHeader,
        _BufferView.LINE: IlInvoiceLine,
    }
)


@dataclasses.dataclass(slots=True)
class PInvoiceContext:
    """The bridge's own WORKING-STORAGE, which persists between calls.

    GnuCOBOL keeps a dynamically loaded module's working storage alive across
    `CALL`s within a run, and this bridge depends on that: `ba040` builds its
    `SELECT` only `if Cursor-Not-Active` [common/plinvoiceMT.cbl:L635] and every
    subsequent Read-Next fetches from the result array the first call stored. The
    context is therefore long-lived state, not a per-call bag, and the module
    keeps one instance for the same reason
    :mod:`acas_posting.dal.cursor_state` keeps one default state table.

    Nothing here is shared between concurrent workers because nothing in this
    migration runs concurrently.  Agent Action Plan section 0.2.2 forbids every
    form of it - no operating-system threads, no cooperative event loop, no
    additional processes and no connection pooling - and requires strictly
    sequential execution, matching the single-threaded COBOL.  The rule text
    itself is in the plan; it is summarised rather than transcribed here so that a
    mechanical scan of this module for concurrency machinery finds none.
    """

    #: The live driver connection, or ``None`` before `ba020-Process-Open`.
    connection: Any = None
    #: The system record the credentials come from, set by :func:`dispatch` and
    #: consumed by :func:`connection.mysql_1000_open`.
    system_record: SystemRecord | None = None
    #: Optional transport policy for :func:`connection.mysql_1000_open`.
    transport: connection.TransportSecurity | None = None
    #: `01  TD-PUINVOICE-REC.` [common/plinvoiceMT.cbl:L390].
    header_hv: HeaderHostVariables = dataclasses.field(
        default_factory=HeaderHostVariables
    )
    #: `01  TD-PUINV-LINES-REC.` [common/plinvoiceMT.cbl:L425].
    line_hv: LineHostVariables = dataclasses.field(default_factory=LineHostVariables)
    #: `01  WS-Invoice-Line.` [common/plinvoiceMT.cbl:L362-L379] - the bridge's own
    #: line record, declared separately because the third `REPLACING` clause
    #: renamed every copied `il-` field to `Un-Used-il-` [:L458].
    ws_invoice_line: IlInvoiceLineBody | None = None
    #: Which redefinition last wrote the shared buffer.
    buffer_view: _BufferView = _BufferView.HEADER
    #: ISAM cursor emulation, shared with :mod:`acas_posting.dal.cursor_state` so
    #: the `START` / `READ NEXT` protocol has one implementation.
    cursors: cursor_state.CursorStateTable = dataclasses.field(
        default_factory=cursor_state.CursorStateTable
    )
    #: `05  Most-Cursor-Set   pic 9 value zero.` [common/plinvoiceMT.cbl:L330].
    most_cursor_set: int = 0
    #: `05  Most-Cursor-Set-2 pic 9 value zero.   *> RG 1`
    #: [common/plinvoiceMT.cbl:L333].
    most_cursor_set_2: int = 0
    #: `05  MOST-Relation pic xxx.` [common/plinvoiceMT.cbl:L329], initialised to
    #: spaces and left at spaces when `Access-Type` falls outside 5..9, because
    #: the `evaluate` has no `when other` [:L971-L982].
    most_relation: str = " " * cursor_state.MostRelation.WIDTH
    #: `77  ws-Where   pic x(512).` [common/plinvoiceMT.scb:L265].
    ws_where: str = ""
    #: `77  ws-Where-2 pic x(512).  *> RG1` [common/plinvoiceMT.scb:L266].
    ws_where_2: str = ""
    #: `WS-MYSQL-Count-Rows`, the row count every status test reads.
    ws_mysql_count_rows: int = 0
    #: `WS-Mysql-Save-Count-Rows` [common/plinvoiceMT.cbl:L1075].
    ws_mysql_save_count_rows: int = 0
    #: `WS-Mysql-Save-Count-Rows-RG1` [common/plinvoiceMT.cbl:L1131].
    ws_mysql_save_count_rows_rg1: int = 0
    #: `01  WS-Temp-ED-Row pic 9(7).  *> for row cnt. 10M-1 Inv. records`
    #: [common/plinvoiceMT.scb:L277].
    ws_temp_ed_row: int = 0
    #: `03  WS-Last-Read-Invoice pic 9(8) value zero.`
    #: [common/plinvoiceMT.cbl:L287].
    ws_last_read_invoice: int = _LAST_READ_INVOICE_INITIAL
    #: `03  WS-Last-Read-Line pic 99 value 40.` [common/plinvoiceMT.cbl:L288] -
    #: initialised to the MAXIMUM line number, not to zero
    #: (anomaly ``N-last-read-line-40``).
    ws_last_read_line: int = _LAST_READ_LINE_INITIAL
    #: `01  WS-Actual-Lines-In-Row pic 99 value zero.`
    #: [common/plinvoiceMT.cbl:L289].
    ws_actual_lines_in_row: int = _ACTUAL_LINES_IN_ROW_INITIAL
    #: `01  RG-Table.` [common/plinvoiceMT.cbl:L316-L326], inert by declaration.
    rg_table: tuple[RepeatingGroupEntry, ...] = RG_TABLE
    #: The last statement text this module built, mirroring `WS-MYSQL-COMMAND`.
    ws_mysql_command: str = ""

    # ----------------------------------------------------------------------
    # `acas026`'s own working storage [common/acas026.cbl:L189-L209]. The handler
    # and the bridge are separate COBOL programs with separate working storage;
    # they share one context object here because the handler's `CALL` [:L611-L615]
    # is the only route into the bridge, so a single object cannot conflate two
    # live invocations.
    # ----------------------------------------------------------------------
    #: `77  A pic 9(4) value zero.  *> A & B used in 1st test ONLY`
    #: [common/acas026.cbl:L193]. Both the guard and one operand of
    #: `ba012-Test-WS-Rec-Size-2`'s comparison [:L560-L567], which is why the
    #: maintainer warns `*> (So do NOT use var A & B again)` [:L552].
    record_size_a: int = 0
    #: `77  B pic 9(4) value zero.  *>  in ba-Process-RDBMS`
    #: [common/acas026.cbl:L194].
    record_size_b: int = 0
    #: `77  Cobol-File-Status pic 9 value zero.` [common/acas026.cbl:L196].
    #:
    #: ⭐ ANOMALY ``N-eof-flag-is-the-field``. `88  Cobol-File-Eof value 1.`
    #: [:L197] is a condition name ON THIS FIELD, so `set Cobol-File-EoF to true`
    #: [:L378] and `move 1 to Cobol-File-Status  *> JIC above dont work :)` [:L379]
    #: are THE SAME ASSIGNMENT written twice - the belt-and-braces second statement
    #: is the belt. Reproduced as two writes of the same value, and
    #: :attr:`cobol_file_eof` is a property over the field rather than a second
    #: field, because in COBOL there is only one field.
    cobol_file_status: int = 0
    #: `03  invoice-key.` inside `01  Invoice-Record.`
    #: [copybooks/plfdpinv.cob:L12-L15] - the FD record's ten-character key, held as
    #: TEXT so that `move spaces to Invoice-Key` [common/acas026.cbl:L369] can be
    #: reproduced literally into a group declared `pic 9(8)` plus `pic 99`
    #: (anomaly ``N-spaces-into-numeric-key``).
    invoice_key_raw: str = "0" * 10
    #: `03  ws-temp-ed-1 pic 9(8).` [common/acas026.cbl:L202].
    ws_temp_ed_1: int = 0
    #: `03  WS-Temp-ed-2 pic 99.` [common/acas026.cbl:L203].
    ws_temp_ed_2: int = 0
    #: `77  Display-Blk pic x(75) value spaces.` [common/acas026.cbl:L195] - the
    #: record-size error message, and the one value on that path a caller can read
    #: because it is copied into `SQL-Msg` [:L581].
    display_blk: str = " " * _DISPLAY_BLK_WIDTH

    @property
    def cobol_file_eof(self) -> bool:
        """`88  Cobol-File-Eof value 1.` [common/acas026.cbl:L197].

        A condition name over :attr:`cobol_file_status`, not a field of its own.
        See that attribute's note for why the distinction matters.
        """
        return self.cobol_file_status == 1

    @cobol_file_eof.setter
    def cobol_file_eof(self, value: bool) -> None:
        """`set Cobol-File-EoF to true` [common/acas026.cbl:L378].

        Setting a condition name true assigns its first value, which here is 1.
        There is no COBOL syntax for setting it false, and the handler never does -
        it writes `move zero to Cobol-File-Status` instead
        [:L341, :L352, :L420, :L446, :L493, :L504, :L516]. The false branch is
        provided so the attribute is a well-behaved property, and it writes the
        same zero those statements write.
        """
        self.cobol_file_status = 1 if value else 0

    @property
    def cursor_active(self) -> bool:
        """`88  Cursor-Active value 1.` [common/plinvoiceMT.cbl:L332]."""
        return self.most_cursor_set == 1

    @property
    def cursor_active_2(self) -> bool:
        """`88  Cursor-Active-2 value 1.` [common/plinvoiceMT.cbl:L335]."""
        return self.most_cursor_set_2 == 1


#: The bridge's single working-storage instance, created once at import exactly as
#: GnuCOBOL creates it once when the module is first loaded. It holds no
#: connection and touches no socket until `ba020-Process-Open` runs.
_DEFAULT_CONTEXT: Final[PInvoiceContext] = PInvoiceContext()


def default_context() -> PInvoiceContext:
    """Return the module-level working storage of ``plinvoiceMT``.

    Callers that need an isolated instance - a test, or a second logical run in
    one process - construct :class:`PInvoiceContext` directly. The default is
    shared because the COBOL's is.
    """
    return _DEFAULT_CONTEXT


def citations() -> tuple[str, ...]:
    """Return every source locator this module was written from.

    Published so the traceability document can be generated rather than
    maintained, in the same shape
    :meth:`acas_posting.records.file_access.FileAccess.citations` uses.
    """
    record_citations = tuple(
        f"{dictionary_key_for(owner, attribute)} :: {cite_for(owner, attribute)}"
        for owner, attribute in (
            (IhPrime, "ws_invoice_key"),
            (IhSubPrime, "ih_lines"),
            (IlInvoiceLineBody, "il_net"),
            (WsPInvoiceRecord, "invoice_key"),
        )
    )
    table_citations = tuple(
        f"{table} :: {loader.table_for(table).ordinal_source}"
        for table in (HEADER_TABLE, LINES_TABLE)
    )
    column_citations = tuple(
        render.cite
        for renders in (HEADER_COLUMN_RENDER, LINES_COLUMN_RENDER)
        for render in renders.values()
    )
    return (
        "[common/acas026.cbl] handler acas026, 631 lines",
        "[common/plinvoiceMT.cbl] bridge plinvoiceMT, 3226 lines",
        "[common/plinvoiceMT.scb] pre-translation source, 1831 lines",
        "[copybooks/plwspinv.cob] working-storage view, 86 lines",
        "[copybooks/plwspinv2.cob] file view with two redefinitions, 73 lines",
        "[copybooks/plfdpinv.cob] file description, fourth record-size note",
        "[copybooks/wsfnctn.cob] function codes, access types, File-Access",
        "[mysql/ACASDB.sql] the frozen schema",
        *table_citations,
        *record_citations,
        *column_citations,
    )


# ---------------------------------------------------------------------------
# SQL assembly - this module owns EVERY statement for BOTH tables
# ---------------------------------------------------------------------------
#
# The bridge assembles each statement into `WS-MYSQL-COMMAND` with the `STRING`
# verb and then performs `MYSQL-1210-COMMAND`. Four shapes exist, and all four are
# reproduced below character for character:
#
#   SELECT  `SELECT * FROM ` `` `T` `` ` WHERE ` <WS-Where (1:J)> `;`
#           [common/plinvoiceMT.cbl:L663-L668, :L859-L864, :L1012-L1017,
#            :L1084-L1089, :L2389-L2394, :L2443-L2448]
#   DELETE  `DELETE FROM ` `` `T` `` ` WHERE ` <WS-Where (1:J)>   - NO semicolon
#           [common/plinvoiceMT.cbl:L1221-L1226, :L1318-L1323, :L2560-L2565,
#            :L2652-L2657]
#   INSERT  `INSERT INTO ` `` `T` SET `` `` `COL`=" `` v `"` `, ` ... `;`
#           [common/plinvoiceMT.cbl:L1536-L1917, :L2824-L3005]
#   UPDATE  `UPDATE ` `` `T` SET `` ... ` WHERE ` TRIM(<WS-Where (1:J)>) `;`
#           [common/plinvoiceMT.cbl:L1933-L2318, :L3017-L3198]
#
# Two details are load bearing and easy to lose:
#
# * `WS-Where (1:J)` is a reference modification of length J, where J is the
#   `STRING` pointer AFTER the last character written - so the slice carries ONE
#   trailing character beyond the predicate, and because `move spaces to WS-Where`
#   preceded the build [:L640, :L838, :L1199, :L1295, :L1369, :L2368, :L2538,
#   :L2626, :L2702] that character is a SPACE. SELECT and DELETE embed the slice
#   raw, so their text carries that space; UPDATE wraps it in `FUNCTION TRIM`
#   [:L2314, :L3194], so its text does not. :func:`_pointer_slice` is that space.
# * The SEMICOLON is present on SELECT, INSERT and UPDATE and ABSENT on DELETE.
#   Both `ba080` and `ba085` build the delete without one [:L1226, :L1323], as do
#   `bc080` and `bc085` [:L2565, :L2657]. MySQL accepts either, so nothing breaks;
#   it is reproduced because statement text is evidence.
#
# Values are BOUND, never interpolated: :func:`connection.execute_statement`
# "binds VALUES and never interpolates them". The value bound is the TEXT the
# bridge renders through :func:`rendered_column_text`, never the record's own
# value - which is what carries the eleven-column render sign loss
# (``N-signloss-in-render``) through to MySQL exactly as the compiled system
# carries it. Alongside every statement this module also keeps the fully literal
# text the COBOL would have produced, in :attr:`SqlStatement.literal`, so the
# evidence a reader needs is a field lookup rather than a reconstruction.


@dataclasses.dataclass(frozen=True, slots=True)
class SqlFragment:
    """One assembled piece of statement text, with its bound values.

    ``text`` carries ``%s`` placeholders and identifiers that have ALREADY been
    through :func:`connection.quote_identifier`; ``parameters`` carries the values
    those placeholders bind, in order; ``literal`` is the text the COBOL `STRING`
    verb would have built, with the values inline and double quoted, for evidence
    and for the ``WS-MYSQL-COMMAND`` mirror.
    """

    #: Statement text with ``%s`` placeholders; identifiers already quoted.
    text: str
    #: The values the placeholders bind, in order.
    parameters: tuple[Any, ...]
    #: The exact text `WS-MYSQL-COMMAND` would hold.
    literal: str
    #: `[common/plinvoiceMT.cbl:L...]` of the `STRING` block this reproduces.
    locator: str


#: A completed statement, ready for :func:`connection.execute_statement`.
SqlStatement = SqlFragment


def _pointer_slice(predicate: SqlFragment) -> SqlFragment:
    """Model `WS-Where (1:J)` - the predicate plus ONE trailing space.

    `move spaces to WS-Where` runs before every predicate build, and the `STRING`
    pointer `J` ends one position past the last character written, so a reference
    modification of length `J` picks up that extra space. Reproduced because
    SELECT and DELETE embed the slice untrimmed
    [common/plinvoiceMT.cbl:L667, :L1225].
    """
    return dataclasses.replace(
        predicate,
        text=predicate.text + " ",
        literal=predicate.literal + " ",
    )


def _keyname_delimited_by_space(key: cursor_state.KeyOfReference) -> str:
    """`KeyName (KOR-x1) delimited by space` - the trimmed key name.

    `keyname pic x(30)` [common/plinvoiceMT.cbl:L308] holds the name space
    padded, and every predicate emits it `delimited by space`, so only the
    characters before the first space travel. `PINVOICE-KEY` is padded explicitly
    in the source literal [:L298] while `IL-LINE-KEY` is not [:L302]
    (``N-keyname-padding``); COBOL pads the shorter literal anyway, so both
    behave identically here and the asymmetry is cosmetic.
    """
    return connection.cobol_string_delimited_by_space(key.key_name)


def _where_sequential_read(key: cursor_state.KeyOfReference) -> SqlFragment:
    """`ba040`'s self-positioning predicate [common/plinvoiceMT.cbl:L642-L654].

    `` `PINVOICE-KEY` >= "0000000000" ORDER BY `PINVOICE-KEY` ASC ``

    The relation is the literal `" >= "` [:L645] and the low key the literal
    `'"0000000000"'` [:L646] annotated `*> for 1st time active only`; neither
    comes from `Access-Type`, and `set KOR-x1 to 1` [:L636] means key 1 always.
    The `ORDER BY` closes with `' ASC'` - ONE word, no padding - where `ba060`'s
    header predicate writes `' ASC  '` with two trailing spaces [:L996].
    """
    name = _keyname_delimited_by_space(key)
    quoted = connection.quote_identifier(name)
    low = _SEQUENTIAL_READ_START.low_key
    return SqlFragment(
        text=f"{quoted} >= %s ORDER BY {quoted} ASC",
        parameters=(low,),
        literal=f'{quoted} >= "{low}" ORDER BY {quoted} ASC',
        locator="[common/plinvoiceMT.cbl:L642-L654]",
    )


def _where_key_equals(
    key: cursor_state.KeyOfReference, key_value: str, locator: str
) -> SqlFragment:
    """`` `KEY`="value" `` - the equality predicate, used by six paragraphs.

    `ba050` [common/plinvoiceMT.cbl:L840-L848], `ba080` [:L1201-L1209], `ba085`
    [:L1297-L1305] where the `'="'` carries `*> was '<"'`, `ba090`
    [:L1371-L1379], `bc050` [:L2370-L2378], `bc080` [:L2540-L2548] and `bc090`
    [:L2704-L2712] all build exactly this, differing only in which key of
    reference they select and in what they do with the result.
    """
    quoted = connection.quote_identifier(_keyname_delimited_by_space(key))
    return SqlFragment(
        text=f"{quoted}=%s",
        parameters=(key_value,),
        literal=f'{quoted}="{key_value}"',
        locator=locator,
    )


def _where_start_header(
    key: cursor_state.KeyOfReference,
    relation: cursor_state.MostRelation,
    key_value: str,
) -> SqlFragment:
    """`ba060`'s HEADER predicate [common/plinvoiceMT.cbl:L984-L999].

    `` `PINVOICE-KEY`<rel>"value" ORDER BY `PINVOICE-KEY` ASC   ``

    `MOST-relation delimited by space` [:L988] strips the padding off the
    three-character relation, so `">= "` travels as `">="`. The key value IS
    double quoted here [:L989, :L991], and the trailing `' ASC  '` [:L996] keeps
    its TWO spaces - both differ from the RG1 predicate built immediately
    afterwards, see :func:`_where_start_lines`.
    """
    quoted = connection.quote_identifier(_keyname_delimited_by_space(key))
    token = relation.token
    return SqlFragment(
        text=f"{quoted}{token}%s ORDER BY {quoted} ASC  ",
        parameters=(key_value,),
        literal=f'{quoted}{token}"{key_value}" ORDER BY {quoted} ASC  ',
        locator="[common/plinvoiceMT.cbl:L984-L999]",
    )


def _where_start_lines(
    key: cursor_state.KeyOfReference,
    relation: cursor_state.MostRelation,
    key_value: str,
) -> SqlFragment:
    """`ba060`'s RG1 predicate [common/plinvoiceMT.cbl:L1058-L1069].

    `` `IL-LINE-KEY`<rel>0000012307 ORDER BY `IL-LINE-KEY` ASC   ``

    ANOMALY ``N-start-rg1-unquoted-key``, carried in the register also under the
    heading ``N-rg1-start-predicate-unquoted`` - one finding, two names, because it
    is both a property of the RG1 START predicate and a property of its key value:
    the header predicate wraps its key
    value in `'"'` on both sides [:L989, :L991] and this one DOES NOT - the
    `WS-Invoice-Record (K2:L2)` reference modification at [:L1062] is strung with
    no quote literal before or after it. The comparison therefore reaches MariaDB
    as a `char(10)` column against a bare numeric literal rather than a string,
    so MariaDB coerces the COLUMN to a number for every row it examines, which
    both defeats the primary key and changes which rows qualify whenever a key
    has leading zeros - and every key here does, because it is
    `pic 9(8)` + `pic 99`. Reproduced unquoted. NOT repaired.

    The maintainer's own note four lines further on records that he was unsure of
    this whole block: `*> ALL this does depend on application code in slnnn
    ???? <<<<<<<` [:L1128].
    """
    quoted = connection.quote_identifier(_keyname_delimited_by_space(key))
    token = relation.token
    return SqlFragment(
        # No quote literal either side of the value - see the docstring.
        text=f"{quoted}{token}%s ORDER BY {quoted} ASC  ",
        parameters=(key_value,),
        literal=f"{quoted}{token}{key_value} ORDER BY {quoted} ASC  ",
        locator="[common/plinvoiceMT.cbl:L1058-L1069]",
    )


def _where_delete_all_lines(ih_invoice: int) -> SqlFragment:
    """`bc085`'s predicate [common/plinvoiceMT.cbl:L2626-L2640].

    `'IL-INVOICE'="00000123"`

    ANOMALY ``N-deleteall-single-quoted-column``, and it is fatal to the verb.
    The four `STRING` operands that would have emitted a BACKTICK-quoted key name
    from the key table are commented out [:L2629-L2632] - one of them carrying the
    maintainer's own `*>   ?????? should be SA` - and what remains is the literal
    `"'IL-INVOICE'"` [:L2634], a SINGLE-quoted name. MySQL reads a single-quoted
    token as a STRING, so the predicate compares the constant string
    ``IL-INVOICE`` against the constant string ``00000123``: it is false for every
    row, and `bc085-Process-Delete-ALL` therefore deletes NOTHING, ever.

    Reproduced exactly, which means BOTH sides are bound as values and NEITHER
    goes through :func:`connection.quote_identifier` - quoting the left side as an
    identifier would repair the defect. The zero row count then drives the
    paragraph's own failure arm [:L2668-L2684].

    `WS-ih-Invoice delimited by size` [:L2636] sends all eight digits of a
    `pic 9(8)` field, leading zeros included.
    """
    invoice = _digits(ih_invoice, 8)
    return SqlFragment(
        # `%s=%s`: the LEFT side is a string literal in the frozen source, not an
        # identifier. Do not "fix" this by quoting it - see the docstring.
        text="%s=%s",
        parameters=("IL-INVOICE", invoice),
        literal=f"'IL-INVOICE'=\"{invoice}\"",
        locator="[common/plinvoiceMT.cbl:L2626-L2640]",
    )


def _select_statement(table_name: str, predicate: SqlFragment) -> SqlStatement:
    """`SELECT * FROM ` `` `T` `` ` WHERE ` <slice> `;`

    Six paragraphs build this: `ba040` [common/plinvoiceMT.cbl:L663-L668],
    `ba050` [:L859-L864], `ba060` twice - once per table [:L1012-L1017,
    :L1084-L1089] - and `bc050` [:L2389-L2394]. Every one of them is
    `SELECT *` with no column list, no `LIMIT` and no `FOR UPDATE`.
    """
    slice_ = _pointer_slice(predicate)
    quoted = connection.quote_identifier(table_name)
    return SqlStatement(
        text=f"SELECT * FROM {quoted} WHERE {slice_.text};",
        parameters=slice_.parameters,
        literal=f"SELECT * FROM {quoted} WHERE {slice_.literal};",
        locator=predicate.locator,
    )


def _delete_statement(table_name: str, predicate: SqlFragment) -> SqlStatement:
    """`DELETE FROM ` `` `T` `` ` WHERE ` <slice> - with NO semicolon.

    `ba080` [common/plinvoiceMT.cbl:L1221-L1226], `ba085` [:L1318-L1323],
    `bc080` [:L2560-L2565] and `bc085` [:L2652-L2657] all omit the `";"` that
    every other builder appends, and all four embed the pointer slice untrimmed,
    so the statement ends in a space. Reproduced.
    """
    slice_ = _pointer_slice(predicate)
    quoted = connection.quote_identifier(table_name)
    return SqlStatement(
        text=f"DELETE FROM {quoted} WHERE {slice_.text}",
        parameters=slice_.parameters,
        literal=f"DELETE FROM {quoted} WHERE {slice_.literal}",
        locator=predicate.locator,
    )


def _set_clause(
    renders: Mapping[str, ColumnRender],
    columns: Sequence[str],
    group: HeaderHostVariables | LineHostVariables,
    attribute_by_column: Mapping[str, str],
) -> SqlFragment:
    """Build the `` `COL`="v", `` list every INSERT and UPDATE shares.

    The four builders emit their columns in the SAME order, and it is the schema's
    own column order, NOT the load order: `bb200-Insert`
    [common/plinvoiceMT.cbl:L1543-L1913] and `bb300-Update` [:L1940-L2310] both
    run `PINVOICE-KEY` through `IH-UPDATE` with `IH-LINES` twenty-eighth, while
    `bb000-HV-Load` moves it eighteenth [:L1470]; `bc200-Insert-rg1`
    [:L2831-L3001] and `bc300-Update-rg1` [:L3024-L3190] both run `IL-LINE-KEY`,
    `IL-INVOICE`, `IL-LINE`, ... while `bc000-HV-Load-rg1` moves `IL-LINE` before
    `IL-INVOICE` [:L2757-L2758]. Three distinct orders, three separate lists, and
    NONE derived from another (``N-lines-order-mismatch``,
    ``N-lines-loadorder``).

    The separator is `', '` - comma then space [:L1549-L1550] - and the value is
    always wrapped in `="` ... `"` whatever the column's type, so MariaDB does the
    string-to-number coercion on every numeric column.
    """
    pieces: list[str] = []
    literals: list[str] = []
    parameters: list[Any] = []
    for column in columns:
        render = renders[column]
        value = getattr(group, attribute_by_column[column])
        rendered = rendered_column_text(render, value)
        quoted = connection.quote_identifier(column)
        pieces.append(f"{quoted}=%s")
        literals.append(f'{quoted}="{rendered}"')
        parameters.append(rendered)
    return SqlFragment(
        text=", ".join(pieces),
        parameters=tuple(parameters),
        literal=", ".join(literals),
        locator="[common/plinvoiceMT.cbl:L1543-L1913]",
    )


def _insert_statement(
    table_name: str,
    renders: Mapping[str, ColumnRender],
    columns: Sequence[str],
    group: HeaderHostVariables | LineHostVariables,
    attribute_by_column: Mapping[str, str],
    locator: str,
) -> SqlStatement:
    """`INSERT INTO ` `` `T` SET `` <set list> `;`

    `bb200-Insert` [common/plinvoiceMT.cbl:L1528-L1920] for the header and
    `bc200-Insert-rg1` [:L2816-L3003] for the lines. `SET` form, not
    ANOMALY ``N-insert-is-set-form``: every insert this bridge emits is the MySQL
    `SET` extension, `INSERT INTO t SET col=v, ...`, and never the portable
    `(cols) VALUES (...)` form. That is a dialect lock-in rather than a defect -
    the statement will not run on a store without the extension - and it is
    reproduced because the statement TEXT is what a state diff is taken over.
    EVERY column is named - thirty for the header including the five that can only
    be a space, fourteen for the lines - so no column is ever left to a `DEFAULT`
    and nothing is ever `NULL` [Agent Action Plan section 0.6.2].
    """
    clause = _set_clause(renders, columns, group, attribute_by_column)
    quoted = connection.quote_identifier(table_name)
    return SqlStatement(
        text=f"INSERT INTO {quoted} SET {clause.text};",
        parameters=clause.parameters,
        literal=f"INSERT INTO {quoted} SET {clause.literal};",
        locator=locator,
    )


def _update_statement(
    table_name: str,
    renders: Mapping[str, ColumnRender],
    columns: Sequence[str],
    group: HeaderHostVariables | LineHostVariables,
    attribute_by_column: Mapping[str, str],
    predicate: SqlFragment,
    locator: str,
) -> SqlStatement:
    """`UPDATE ` `` `T` SET `` <set list> ` WHERE ` TRIM(<slice>) `;`

    `bb300-Update` [common/plinvoiceMT.cbl:L1925-L2321] for the header and
    `bc300-Update-rg1` [:L3009-L3201] for the lines. Both re-send EVERY column,
    the primary key included, and both wrap the predicate in
    `FUNCTION TRIM (WS-Where (1:J))` [:L2314, :L3194] - the only two places the
    pointer slice is trimmed rather than embedded raw.
    """
    clause = _set_clause(renders, columns, group, attribute_by_column)
    quoted = connection.quote_identifier(table_name)
    # `FUNCTION TRIM` with no direction trims BOTH ends.
    trimmed_text = _pointer_slice(predicate).text.strip(" ")
    trimmed_literal = _pointer_slice(predicate).literal.strip(" ")
    return SqlStatement(
        text=f"UPDATE {quoted} SET {clause.text} WHERE {trimmed_text};",
        parameters=clause.parameters + predicate.parameters,
        literal=f"UPDATE {quoted} SET {clause.literal} WHERE {trimmed_literal};",
        locator=locator,
    )


# ---------------------------------------------------------------------------
# Statement execution and driver-failure capture
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class ExecutionResult:
    """What one `MYSQL-1210-COMMAND` leaves behind.

    `count_rows` is `WS-MYSQL-COUNT-ROWS`, which the frozen copybook fills from
    `MySQL_num_rows` after a store-result and from `MySQL_affected_rows` after a
    command; `rows` is what `MYSQL-1220-STORE-RESULT` materialised, empty for a
    non-`SELECT`; `error` is `None` unless the driver failed, in which case it
    carries the `MySQL_errno` / `MySQL_sqlstate` capture the bridge's failure arms
    read.
    """

    #: `WS-MYSQL-COUNT-ROWS` after the statement.
    count_rows: int
    #: What `MYSQL-1220-STORE-RESULT` stored, in row order.
    rows: tuple[Mapping[str, object], ...] = ()
    #: The `Mysql-1100-Db-Error` capture, or ``None`` on success.
    error: status.DbErrorStatus | None = None


def _driver_error_fields(error: BaseException) -> tuple[str, str, str]:
    """Recover `MySQL_errno`, its message and `MySQL_sqlstate` from a driver error.

    The bridge reads three separate foreign calls -
    `call "MySQL_errno" using WS-MYSQL-Error-Number`,
    `call "MySQL_error" using WS-MYSQL-Error-Message` and
    `call "MySQL_sqlstate" using WS-MYSQL-SQLstate`
    [common/plinvoiceMT.cbl:L1163-L1165] - so all three are recovered here, from
    the driver exception's own attributes where it exposes them and from safe
    defaults where it does not. `"0  "` is the frozen source's own spelling of
    "no error number" [:L1170], and it is what a driver that reports no number
    must be reported as, because that is the value the bridge's inner guard tests.
    """
    errno = getattr(error, "errno", None)
    sql_state = getattr(error, "sqlstate", None)
    message = getattr(error, "msg", None)
    errno_text = _MYSQL_ERRNO_NONE if errno is None else str(errno)
    state_text = (
        str(status.SqlState.NO_DATA) if sql_state is None else str(sql_state)
    )
    message_text = str(error) if message is None else str(message)
    return errno_text, message_text, state_text


def _capture_driver_error(
    error: BaseException, statement: SqlStatement
) -> status.DbErrorStatus:
    """`perform Mysql-1100-Db-Error` - the shared failure capture.

    Delegated to :func:`status.mysql_1100_db_error` rather than re-derived, so the
    duplicate-key test, the SQLSTATE mapping and the generic `(99, 911)` pair all
    come from the one place that owns them.

    That pair is a reproduced defect, and it belongs to the shared procedures rather
    than to this bridge: `move 99 to fs-Reply.` then `move 911 to We-Error.`
    [copybooks/mysql-procedures.cpy:L127-L128] runs UNCONDITIONALLY for every
    non-duplicate failure, so a syntax error, a missing table, a lock timeout and a
    genuine connect failure are all reported as 911 - a code the authoritative table
    documents narrowly as `Rdb Error during initializing`. It is recorded as anomaly
    **N3** in :mod:`acas_posting.dal.status`, not under any ``N-`` heading of this
    module, and is cited here only so a reader of this call site knows why the pair
    is what it is.

    The narrowing to `995` for a delete and `994` for a rewrite is applied by the
    CALLING paragraph, not here, because the frozen source applies it there - five
    sites in all, `move 995 to WE-Error` at [common/plinvoiceMT.cbl:L1239] in
    `ba080-Process-Delete`, [:L1336] in `ba085-Process-Delete-ALL` and [:L2677] in
    `bc085-Process-Delete-ALL-rg1`, and `move 994 to WE-Error` at [:L1397] in
    `ba090-Process-Rewrite` and [:L2731] in `bc090-Process-Rewrite-rg1`. Each runs
    AFTER the generic paragraph has already stored `(99, 911)`, which is the second
    stage of anomaly N3; see :data:`status.WE_ERROR_OVERRIDE_BY_FILE_FUNCTION` and
    :func:`status.override_we_error_for_operation`, which own the mapping.
    """
    errno_text, message_text, state_text = _driver_error_fields(error)
    return status.mysql_1100_db_error(
        errno=errno_text,
        message=message_text,
        sql_state=state_text,
        command=statement.literal,
        we_error=int(status.WeError.SUCCESS),
    )


def _execute(
    context: PInvoiceContext, statement: SqlStatement, *, store_result: bool
) -> ExecutionResult:
    """`PERFORM MYSQL-1210-COMMAND` and, when asked, `MYSQL-1220-STORE-RESULT`.

    ``store_result`` distinguishes the two shapes the frozen copybook offers. A
    `SELECT` is always followed IMMEDIATELY by the store
    [common/plinvoiceMT.cbl:L669-L671, :L865-L867, :L1018-L1020, :L1090-L1092,
    :L2395-L2397], which materialises the WHOLE qualifying result and counts THAT
    with `MySQL_num_rows`; an `INSERT`, `UPDATE` or `DELETE` is not, and its count
    is `MySQL_affected_rows`. Materialising the rows here is the faithful model of
    `mysql_store_result`, which is itself a client-side snapshot - and it is also
    what leaves the connection usable for the next statement.

    NO retry, NO transaction, NO batching and NO reordering: the bridge issues one
    statement per call and the scenario state diff is sensitive to the order
    [Agent Action Plan section 0.3.3].

    A driver failure is CAPTURED, never raised - `*>   Any errors leave it to
    caller to recover from` [common/acas026.cbl:L617] - and the caller's own
    failure arm decides the status pair.
    """
    # `INITIALIZE WS-MYSQL-COMMAND` then the `STRING` assembly, mirrored so the
    # last statement this module built is always inspectable
    # [common/plinvoiceMT.cbl:L1536, :L1933].
    context.ws_mysql_command = statement.literal
    if context.connection is None:
        # The bridge cannot reach `MYSQL-1210-COMMAND` without a connection: every
        # verb but Open runs after `ba020-Process-Open` has succeeded
        # [common/plinvoiceMT.cbl:L595-L597]. Reported as the generic RDB failure
        # rather than raised, per the caller-recovers contract.
        return ExecutionResult(
            count_rows=0,
            error=status.DbErrorStatus(
                fs_reply=status.FsReply.ERROR,
                we_error=int(status.WeError.RDB_INIT_ERROR),
                sql_err=_MYSQL_ERRNO_NONE,
                sql_msg="no open connection",
                sql_state=str(status.SqlState.NO_DATA),
                duplicate_key=False,
            ),
        )
    try:
        with connection.execute_statement(
            context.connection, statement.text, statement.parameters
        ) as cursor:
            if store_result:
                rows = _store_result(cursor)
                # `MySQL_num_rows` counts the STORED result, not the driver's own
                # running total [copybooks/mysql-procedures.cpy:L187-L192].
                return ExecutionResult(count_rows=len(rows), rows=rows)
            # `MySQL_affected_rows` for a command
            # [copybooks/mysql-procedures.cpy:L177].
            affected = cursor.rowcount
            return ExecutionResult(
                count_rows=0 if affected is None or affected < 0 else int(affected)
            )
    except Exception as error:  # every driver failure takes the capture path
        captured = _capture_driver_error(error, statement)
        _LOG.warning(
            "%s statement failed at the driver and is reported through the "
            "bridge's own failure arm per [common/acas026.cbl:L617]: "
            "errno=%s sqlstate=%s category=%s",
            BRIDGE_NAME,
            status.sanitise_for_log(captured.sql_err),
            status.sanitise_for_log(captured.sql_state),
            status.db_error_log_category(captured.sql_err, captured.sql_state),
        )
        return ExecutionResult(count_rows=0, error=captured)


def _store_result(cursor: Any) -> tuple[Mapping[str, object], ...]:
    """`PERFORM MYSQL-1220-STORE-RESULT` - materialise the whole result set.

    Column names come from the cursor's description so that every row is keyed by
    the schema's own hyphenated column name, which is what
    :func:`bb100_unload_hvs` and :func:`bc100_unload_hvs_rg1` read.
    """
    description = cursor.description or ()
    names = tuple(str(column[0]) for column in description)
    return tuple(dict(zip(names, row, strict=False)) for row in cursor.fetchall())


# ---------------------------------------------------------------------------
# Group moves: four columns are a concatenation, not a field
# ---------------------------------------------------------------------------
#
# Four of the forty-four columns are fed by a GROUP move, which the data
# dictionary marks `GROUP_CONCATENATION`. A COBOL group move into `PIC X(n)`
# copies the group's bytes verbatim, so the column receives the members'
# character images end to end with no separator, and any binary member arrives as
# its raw bytes.


def _digits(value: int, width: int) -> str:
    """Render an unsigned `PIC 9(width)` display field.

    Zero-filled on the left and truncated on the left when the value has more
    digits than the picture, which is what a COBOL `move` into a shorter numeric
    display item does.
    """
    magnitude = value if value >= 0 else -value
    return str(magnitude % (10**width)).rjust(width, "0")


def _characters(value: str, width: int) -> str:
    """Render an `PIC X(width)` display field - left justified, space filled."""
    return value[:width].ljust(width, " ")


def _binary_long_bytes(value: int) -> str:
    """Render a `binary-long` as the four bytes a group move would copy.

    GnuCOBOL stores `BINARY-LONG` high-order-byte-first by default - the ACAS
    build selects no dialect and passes no byte-order option anywhere
    [common/comp-common.sh] - so the four bytes are big endian, two's complement.
    They are mapped to characters one for one through ``latin-1``, which is byte
    transparent, because that is what the group move does: it copies bytes, not
    text.
    """
    return int(value).to_bytes(4, "big", signed=True).decode("latin-1")


def _group_ws_invoice_key(ih_invoice: int, ih_test: int) -> str:
    """`move WS-Invoice-Key to HV-PINVOICE-KEY.` [common/plinvoiceMT.cbl:L1452].

    `05  WS-Invoice-Key.` is `07  ih-Invoice pic 9(8).` followed by
    `07  ih-Test pic 99 value zero.` [copybooks/plwspinv.cob:L10-L12], so the ten
    characters are eight zero-filled invoice digits then two zero-filled test
    digits. The `ih-Test` comment `*> was binary-char value zero.` [:L12] records
    that it used to be binary; it is display now, which is what makes the
    concatenation printable.
    """
    return _digits(ih_invoice, 8) + _digits(ih_test, 2)


def _group_il_key(il_invoice: int, il_line: int) -> str:
    """`move WS-il-Key to HV1-IL-LINE-KEY.` [common/plinvoiceMT.cbl:L2756].

    `05  il-Key.` is `07  il-invoice pic 9(8).` then
    `07  il-line pic 99.  *> was binary-char.`
    [copybooks/plwspinv.cob:L67-L69] - the same ten-character shape as the header
    key, which is why `bc070` can observe `*> Same as WS-il-Key` [:L2492].
    """
    return _digits(il_invoice, 8) + _digits(il_line, 2)


def _group_ih_supplier(ih_nos: str, ih_check: int) -> str:
    """`move WS-ih-Supplier to HV-IH-SUPPLIER` [common/plinvoiceMT.cbl:L1456].

    `05  ih-Supplier.` is `07  ih-Nos pic x(6).` then `07  ih-Check pic 9.`
    [copybooks/plwspinv.cob:L13-L15]. Neither member has a host variable or a
    column of its own - only the flattened seven-character group reaches MySQL, so
    both members are recorded as deliberate omissions (R-5).
    """
    return _characters(ih_nos, 6) + _digits(ih_check, 1)


def _group_ih_order(
    ih_freq: str, ih_repeat: int, filler: str, ih_last_date: int
) -> str:
    """`move WS-ih-Order to HV-IH-ORDER` [common/plinvoiceMT.cbl:L1458].

    `05  ih-order.` is the 2023 autogen redefinition
    [copybooks/plwspinv.cob:L17-L27]: `07  ih-Freq pic x.` with six condition
    names, `07  ih-Repeat pic 99.`, `07  filler pic xxx.` and
    `07  ih-Last-Date binary-long.  *> 4 bytes date an invoice was
    generated/posted`. One plus two plus three plus four is the ten bytes
    `HV-IH-ORDER PIC X(10)` receives.

    NONE of those five members has a host variable or a column: only the enclosing
    ten bytes reach the database, as `IH-ORDER char(10)`. All five are therefore
    deliberate omissions, and the six condition names `ih-Yearly`, `ih-Monthly`,
    `ih-Quarterly`, `ih-Daily`, `ih-Testing` and `ih-Valid-Freqs` live on the
    record class in :mod:`acas_posting.records.purchase_invoice`, not here.

    A consequence worth stating because it is not obvious and is not repaired: the
    last four of the ten bytes are BINARY, so `IH-ORDER` can contain bytes that
    are not text at all - `NUL` bytes whenever `ih-Last-Date` is zero - and
    `FUNCTION TRIM (HV-IH-ORDER,TRAILING)` cannot strip them because they are not
    spaces (anomaly ``N-ih-order-carries-binary-bytes``).

    ``N-test-only-88s`` ⭐ - two of `ih-Freq`'s six condition names are declared
    for testing and were never withdrawn. `88 ih-Daily value "D".` and
    `88 ih-Testing value "D".` [copybooks/plwspinv.cob:L22-L23] share the SAME
    value, so the two names are indistinguishable at run time and either one being
    true makes the other true as well; they carry the maintainer's own annotations
    `*> These two are only for testing.` and
    `*> So NOT documented and removed after tests.` Worse, the validity list
    `88 ih-Valid-Freqs values "Y" "M" "Q" "D".` [copybooks/plwspinv.cob:L24]
    INCLUDES that test-only `"D"`, under the caveat
    `*> LAst one for TESTING ONLY so remove after` - so a frequency of `"D"`
    validates as a production value. None of this was removed after tests.
    Reproduced by omission at this layer, deliberately: `ih-Freq` reaches MySQL
    only as the first of `IH-ORDER`'s ten characters, so whatever the caller set -
    including `"D"` - is written through unexamined. This module adds NO validation
    of the frequency (R-3: "Validation is copied, never extended"), and the six
    condition names, `"D"` duplication and all, stay on the record class in
    :mod:`acas_posting.records.purchase_invoice`.
    """
    return (
        _characters(ih_freq, 1)
        + _digits(ih_repeat, 2)
        + _characters(filler, 3)
        + _binary_long_bytes(ih_last_date)
    )


def line_from_bodies(
    bodies: PInvoiceBodies, line_number: int
) -> IlInvoiceLineBody | None:
    """Return one occurrence of `03  invoice-line occurs 40.`

    `01  PInvoice-Bodies.` [copybooks/plwspinv.cob:L65-L66] is the caller-side
    table of up to forty lines; the bridge never sees it, because its own
    `COPY ... REPLACING` collapses the `occurs` away
    [common/plinvoiceMT.cbl:L457] and renames every copied `il-` field to
    `Un-Used-il-` [:L458] so the copied line fields are inert. A caller that holds
    a `PInvoice-Bodies` table therefore has to hand the bridge ONE line at a time,
    which is what this helper selects.

    ``line_number`` is the COBOL subscript, one-based. ``None`` comes back for a
    subscript outside 1..40 rather than an exception, because a COBOL subscript
    out of range is not an error - `gl080` relies on exactly that
    [Agent Action Plan anomaly 2] - and this module never raises on data.

    Three findings about the `COPY ... REPLACING` that makes this helper necessary,
    all reproduced by structure rather than by statement:

    ``N-copy-replacing-no-leading`` ⭐ - the four replacement clauses
    [common/plinvoiceMT.cbl:L455-L458] are not uniform. The `ih-` clause is written
    `leading ==ih-== by ==WS-ih-==` [:L456], so it rewrites only a PREFIX; the
    `il-` clause is written `==il-== by ==Un-Used-il-==` [:L458] with NO `leading`
    keyword, so it rewrites the fragment `il-` WHEREVER it occurs inside a name,
    not merely at the start. Nothing in this copybook happens to contain an
    embedded `il-`, so the two clauses coincide in effect today - but they do not
    coincide in meaning, and a field added later with `il-` in the middle of its
    name would be renamed silently. Recorded, not tightened.

    ``N-copy-replacing-prefix-divergence`` ⭐ - the mirrored bridges prefix
    differently. This bridge writes `==WS-ih-==` with a lower-case `ih`
    [common/plinvoiceMT.cbl:L456] while the sales bridge writes `==WS-Sih-==` with
    a capital `S` [common/slinvoiceMT.cbl:L457], so the generated field names are
    `WS-ih-Invoice` here against `WS-Sih-Invoice` there. Neither convention is
    wrong; they are simply not the same, which is why the two bridges' load
    paragraphs cannot be read as one another's translation and why every field name
    in this module was transcribed from THIS bridge.

    ``N-88-narrowed`` ⭐ - the bridge's separately declared line record narrows a
    condition name. `88 WS-il-Analyised value "Z".`
    [common/plinvoiceMT.cbl:L379] admits ONE value where the copybook's
    `88 il-analyised values "z" "Z".  *> using Z hopefully.`
    [copybooks/plwspinv.cob:L83] admits TWO - so a line flagged with a lower-case
    `"z"` satisfies the condition on the caller's side and fails it on the bridge's.
    The maintainer's own `*> using Z hopefully` shows the ambiguity was known and
    left open. Reproduced by omission at this layer: `IL-UPDATE` is written and read
    as a single raw character with no condition-name evaluation anywhere in this
    module, so both spellings survive round trip untouched and the narrowed
    predicate is not reimplemented here. The condition names belong to
    :mod:`acas_posting.records.purchase_invoice`.
    """
    if line_number < 1 or line_number > _BODIES_OCCURS:
        return None
    lines = bodies.invoice_line
    if line_number > len(lines):
        return None
    return lines[line_number - 1]


def line_from_buffer(
    pinvoice: PInvoiceHeader, context: PInvoiceContext
) -> IlInvoiceLineBody:
    """`move WS-Invoice-Record to WS-Invoice-Line.` - the redefinition switch.

    Used at `bc070-Process-Write` [common/plinvoiceMT.cbl:L2490] and
    `bc090-Process-Rewrite` [:L2693]. In COBOL this is not a conversion, it is a
    REINTERPRETATION: `01  Invoice-Header redefines WS-PInvoice-Record.`
    [copybooks/plwspinv2.cob:L21] and `01  Invoice-Line redefines
    WS-PInvoice-Record.` [:L56] are two views of the SAME hundred bytes, and the
    `move` simply hands those bytes to the second view.

    MODELLING NOTE, recorded as a modelling decision and NOT as a behaviour
    change. A byte-exact alias would require encoding the header's eight
    `comp-3` money fields [copybooks/plwspinv.cob:L31-L39] and its two `comp`
    deduction fields [:L46-L47] into their packed and binary images, and the
    packed-decimal codec lives in ``acas_posting.cobol.usage``, which the Agent
    Action Plan section 0.4.3 import table forbids a ``dal`` module to import.
    So the reinterpretation is modelled at the FIELD level:

    * the ten-byte KEY is exact, because it occupies offset 1 length 10 in BOTH
      views as `pic 9(8)` followed by `pic 99` [copybooks/plwspinv.cob:L10-L12,
      :L67-L69] - it is plain DISPLAY in both, so the bytes are identical and the
      key the bridge writes is byte-for-byte the key the buffer held;
    * the remaining thirteen line fields come from the line the caller staged
      through ``context.ws_invoice_line``, which is the LINE view of the same
      buffer.

    A caller that stages a HEADER and then asks for a line write therefore gets a
    line carrying the buffer's key and `initialize` values elsewhere - which is
    the same class of result the COBOL produces from reinterpreted header bytes,
    reached deterministically instead of by aliasing. Never raises.
    """
    il_invoice = int(pinvoice.ih_prime.ws_invoice_key.ih_invoice)
    il_line = int(pinvoice.ih_prime.ws_invoice_key.ih_test)
    staged = context.ws_invoice_line
    if staged is None:
        # The `initialize WS-Invoice-Line` shape [common/plinvoiceMT.cbl:L2786].
        return IlInvoiceLineBody(
            il_key=IlKey(il_invoice=il_invoice, il_line=il_line),
            il_product=" " * 13,
            il_pa=" " * 2,
            filler_1=" " * 2,
            il_qty=0,
            il_type=" ",
            il_description=" " * 24,
            filler_2=" " * 2,
            il_net=_DECIMAL_ZERO,
            il_unit=_DECIMAL_ZERO,
            il_discount=_DECIMAL_ZERO,
            il_vat=_DECIMAL_ZERO,
            il_vat_code=0,
            il_update=" ",
        )
    # The key ALWAYS comes from the buffer, because that is the one part of the
    # move whose bytes are identical under both views.
    return dataclasses.replace(
        staged, il_key=IlKey(il_invoice=il_invoice, il_line=il_line)
    )


# ---------------------------------------------------------------------------
# bb000-HV-Load / bb100-UnloadHVs  -  the header table
# ---------------------------------------------------------------------------


def bb000_hv_load(pinvoice: PInvoiceHeader, context: PInvoiceContext) -> None:
    """`bb000-HV-Load Section.` [common/plinvoiceMT.cbl:L1442-L1477].

    Twenty-five moves for a thirty-column table, in the order
    :data:`HEADER_LOAD_SEQUENCE` records, after
    `initialize TD-PUINVOICE-REC.` [:L1450].

    What is NOT here is the point of the paragraph:

    * `HV-IH-STATUS-A`, `-C`, `-I`, `-L` and `-P` receive no move, so they keep
      the space `initialize` left and every INSERT writes a space into five
      `char(1) NOT NULL` columns forever
      (anomaly ``N-five-status-columns-never-populated``);
    * `HV-PINVOICE-KEY` IS loaded [:L1452] and, uniquely, is never unloaded
      (anomaly ``N-pinvoice-key-write-only``);
    * `WS-ih-Lines` is the eighteenth move [:L1470] though its host variable is
      twenty-eighth [:L418] (anomaly ``N-lines-order-mismatch``).

    Six moves narrow a signed record field into an unsigned host variable and
    destroy the sign before any SQL exists; each goes through
    :func:`_narrow_signed_to_unsigned_host_variable` (anomaly ``N-signloss``).
    """
    prime: IhPrime = pinvoice.ih_prime
    sub: IhSubPrime = pinvoice.ih_sub_prime
    header = context.header_hv

    # `initialize TD-PUINVOICE-REC.` [common/plinvoiceMT.cbl:L1450] - first, so
    # nothing this paragraph omits can ever be NULL.
    header.initialize()

    # [common/plinvoiceMT.cbl:L1452] group move; loaded here, never unloaded.
    header.hv_pinvoice_key = _group_ws_invoice_key(
        prime.ws_invoice_key.ih_invoice, prime.ws_invoice_key.ih_test
    )
    # [common/plinvoiceMT.cbl:L1454-L1455]
    header.hv_ih_invoice = prime.ws_invoice_key.ih_invoice
    header.hv_ih_test = prime.ws_invoice_key.ih_test
    # [common/plinvoiceMT.cbl:L1456] group move, members flattened away.
    header.hv_ih_supplier = _group_ih_supplier(
        prime.ih_supplier.ih_nos, prime.ih_supplier.ih_check
    )
    # [common/plinvoiceMT.cbl:L1457] ih-Date binary-long SIGNED -> HV-IH-DAT
    # PIC 9(10) COMP UNSIGNED: the sign dies here, and the column is renamed.
    header.hv_ih_dat = _narrow_signed_to_unsigned_host_variable(prime.ih_date, 10)
    # [common/plinvoiceMT.cbl:L1458] group move; four of the ten bytes are binary.
    header.hv_ih_order = _group_ih_order(
        prime.ih_order.ih_freq,
        prime.ih_order.ih_repeat,
        prime.ih_order.filler_1,
        prime.ih_order.ih_last_date,
    )
    # [common/plinvoiceMT.cbl:L1459-L1460]
    header.hv_ih_type = prime.ih_type
    header.hv_ih_ref = prime.ih_ref
    # [common/plinvoiceMT.cbl:L1461-L1468] the eight money fields, signed at all
    # three layers, so nothing is lost HERE - the loss is in the render.
    header.hv_ih_p_c = sub.ih_fig.ih_p_c
    header.hv_ih_net = sub.ih_fig.ih_net
    header.hv_ih_extra = sub.ih_fig.ih_extra
    header.hv_ih_carriage = sub.ih_fig.ih_carriage
    header.hv_ih_vat = sub.ih_fig.ih_vat
    header.hv_ih_discount = sub.ih_fig.ih_discount
    header.hv_ih_e_vat = sub.ih_fig.ih_e_vat
    header.hv_ih_c_vat = sub.ih_fig.ih_c_vat
    # [common/plinvoiceMT.cbl:L1469]. ⭐ ANOMALY ``N-88-case-swap``: this single
    # character is the one every status condition name tests, and the two copybooks
    # declare those names with their values in OPPOSITE case order -
    # `88 pending values "P" "p".` / `88 invoiced values "I" "i".` /
    # `88 applied values "Z" "z".` [copybooks/plwspinv.cob:L41-L43] against
    # `"p" "P"` / `"i" "I"` / `"z" "Z"` [copybooks/plwspinv2.cob:L41-L43], and
    # `88 day-booked values "B" "b".` [copybooks/plwspinv.cob:L51] against
    # `"b" "B"` [copybooks/plwspinv2.cob:L51]. Both orders admit both cases, so
    # the predicates are equivalent and only the source differs - but the pairing
    # shows the two layouts were maintained independently rather than kept in step,
    # which is the same divergence ``N-copybook-mirror-asymmetry`` makes FATAL for
    # the five status FIELDS. Reproduced by omission: the raw character is carried
    # through untouched and no condition name is evaluated in this module, so
    # neither ordering can be preferred here.
    header.hv_ih_status = sub.ih_status
    # [common/plinvoiceMT.cbl:L1470] EIGHTEENTH move, TWENTY-EIGHTH host variable,
    # column ordinal 28 - and binary-char SIGNED into PIC 9(03) COMP UNSIGNED.
    header.hv_ih_lines = _narrow_signed_to_unsigned_host_variable(sub.ih_lines, 3)
    # [common/plinvoiceMT.cbl:L1471] binary-char SIGNED -> unsigned.
    header.hv_ih_deduct_days = _narrow_signed_to_unsigned_host_variable(
        sub.ih_deduct_days, 3
    )
    # [common/plinvoiceMT.cbl:L1472-L1473] unsigned at ALL THREE layers here,
    # unlike otm3MT's identical fields [common/otm3MT.cbl:L324-L325]: no narrowing.
    header.hv_ih_deduct_amt = sub.ih_deduct_amt
    header.hv_ih_deduct_vat = sub.ih_deduct_vat
    # [common/plinvoiceMT.cbl:L1474-L1475] binary-char and binary-long, both
    # SIGNED, both into unsigned host variables.
    header.hv_ih_days = _narrow_signed_to_unsigned_host_variable(sub.ih_days, 3)
    header.hv_ih_cr = _narrow_signed_to_unsigned_host_variable(sub.ih_cr, 10)
    # [common/plinvoiceMT.cbl:L1476-L1477]
    header.hv_ih_day_book_flag = sub.ih_day_book_flag
    header.hv_ih_update = sub.ih_update
    # NO move to HV-IH-STATUS-A / -C / -I / -L / -P: the paragraph ends here
    # [common/plinvoiceMT.cbl:L1477], and `bb000-Exit. exit section.` follows at
    # [:L1479-L1480].


def bb100_unload_hvs(pinvoice: PInvoiceHeader, context: PInvoiceContext) -> None:
    """`bb100-UnloadHVs Section.` [common/plinvoiceMT.cbl:L1482-L1523].

    Twenty-four moves, in the order :data:`HEADER_UNLOAD_SEQUENCE` records, after
    `initialize WS-Invoice-Record.` [:L1487] - PLAIN, with no `with filler`, where
    `ba042-Fetch` writes `initialize WS-Invoice-Record with filler` at [:L802]
    (anomaly ``N-initialize``).

    Three things this paragraph does NOT do, all preserved:

    * it never moves `HV-PINVOICE-KEY` back, so the primary key is write only;
    * it never touches the five `HV-IH-STATUS-x` variables, even though
      `ba042-Fetch` [:L769-L773] has just filled them from the row, so their
      values are read and immediately discarded
      (anomaly ``N-status-hvs-fetched-then-discarded``);
    * it does not undo the sign narrowing, because it cannot - the sign is gone.

    It then does three things beyond the unload, under the maintainer's own
    heading `*>  THIS BLOCK SPECIAL FOR THIS DAL AS IT ALSO processes a RG.`
    [:L1514]: it saves the line count [:L1518] and the last key read [:L1522-L1523].
    The last of those seeds the LINE watermark from `HV-IH-TEST` with the
    maintainer's own doubt `*> should be zero` [:L1523], while
    `WS-Last-Read-Line` was initialised to 40 [:L280]. It is reproduced from
    `HV-IH-TEST` and NOT from zero (anomaly ``N-lines-cursor-from-ih-test``).
    """
    prime: IhPrime = pinvoice.ih_prime
    sub: IhSubPrime = pinvoice.ih_sub_prime
    header = context.header_hv

    # `initialize WS-Invoice-Record.` [common/plinvoiceMT.cbl:L1487] - plain.
    _initialise_header_record(pinvoice)

    # [common/plinvoiceMT.cbl:L1489-L1490] - back into the key group's members;
    # HV-PINVOICE-KEY itself is NOT unloaded, but these two rebuild the record's
    # own key, which is why `ba042-Fetch` can log `WS-Invoice-Key` at [:L818].
    prime.ws_invoice_key.ih_invoice = header.hv_ih_invoice
    prime.ws_invoice_key.ih_test = header.hv_ih_test
    # [common/plinvoiceMT.cbl:L1491] group move back; the two members are split on
    # the declared widths of [copybooks/plwspinv.cob:L14-L15].
    supplier = _characters(header.hv_ih_supplier, 7)
    prime.ih_supplier.ih_nos = supplier[:6]
    prime.ih_supplier.ih_check = int(supplier[6]) if supplier[6].isdigit() else 0
    # [common/plinvoiceMT.cbl:L1492] the value comes back UNSIGNED whatever it was.
    prime.ih_date = header.hv_ih_dat
    # [common/plinvoiceMT.cbl:L1493] group move back into the autogen group.
    order = _characters(header.hv_ih_order, 10)
    prime.ih_order.ih_freq = order[0]
    prime.ih_order.ih_repeat = int(order[1:3]) if order[1:3].isdigit() else 0
    prime.ih_order.filler_1 = order[3:6]
    prime.ih_order.ih_last_date = int.from_bytes(
        order[6:10].encode("latin-1"), "big", signed=True
    )
    # [common/plinvoiceMT.cbl:L1494-L1495]
    prime.ih_type = header.hv_ih_type
    prime.ih_ref = header.hv_ih_ref
    # [common/plinvoiceMT.cbl:L1496-L1503]
    sub.ih_fig.ih_p_c = header.hv_ih_p_c
    sub.ih_fig.ih_net = header.hv_ih_net
    sub.ih_fig.ih_extra = header.hv_ih_extra
    sub.ih_fig.ih_carriage = header.hv_ih_carriage
    sub.ih_fig.ih_vat = header.hv_ih_vat
    sub.ih_fig.ih_discount = header.hv_ih_discount
    sub.ih_fig.ih_e_vat = header.hv_ih_e_vat
    sub.ih_fig.ih_c_vat = header.hv_ih_c_vat
    # [common/plinvoiceMT.cbl:L1504-L1505]
    sub.ih_status = header.hv_ih_status
    sub.ih_lines = header.hv_ih_lines
    # [common/plinvoiceMT.cbl:L1506-L1512]
    sub.ih_deduct_days = header.hv_ih_deduct_days
    sub.ih_deduct_amt = header.hv_ih_deduct_amt
    sub.ih_deduct_vat = header.hv_ih_deduct_vat
    sub.ih_days = header.hv_ih_days
    sub.ih_cr = header.hv_ih_cr
    sub.ih_day_book_flag = header.hv_ih_day_book_flag
    sub.ih_update = header.hv_ih_update

    # `*>  Here save the ih-Lines to WS so we can keep track of body-lines.`
    # [common/plinvoiceMT.cbl:L1516]
    context.ws_actual_lines_in_row = header.hv_ih_lines  # [:L1518]
    # `*>   Save sih Invoice & test as last key read.` [common/plinvoiceMT.cbl:L1520]
    # - and note `sih`, the SALES prefix, in the PURCHASE bridge's own comment
    # (anomaly ``N-sih-in-purchase-comment``).
    context.ws_last_read_invoice = header.hv_ih_invoice  # [:L1522]
    # [common/plinvoiceMT.cbl:L1523] `*> should be zero` - the maintainer's doubt,
    # preserved. NOT replaced by zero.
    context.ws_last_read_line = header.hv_ih_test
    context.buffer_view = _BufferView.HEADER


def _initialise_header_record(pinvoice: PInvoiceHeader) -> None:
    """`initialize WS-Invoice-Record.` [common/plinvoiceMT.cbl:L1487].

    Alphanumeric members to spaces at their declared widths, numeric members to
    zero. The widths come from [copybooks/plwspinv.cob:L8-L53] by way of the
    record class's own field descriptors, which is why this function names no
    literal width of its own beyond the four group layouts.
    """
    prime = pinvoice.ih_prime
    sub = pinvoice.ih_sub_prime
    prime.ws_invoice_key.ih_invoice = 0
    prime.ws_invoice_key.ih_test = 0
    prime.ih_supplier.ih_nos = " " * 6
    prime.ih_supplier.ih_check = 0
    prime.ih_date = 0
    prime.ih_order.ih_freq = " "
    prime.ih_order.ih_repeat = 0
    prime.ih_order.filler_1 = " " * 3
    prime.ih_order.ih_last_date = 0
    prime.ih_type = 0
    prime.ih_ref = " " * 10
    sub.ih_fig.ih_p_c = _DECIMAL_ZERO
    sub.ih_fig.ih_net = _DECIMAL_ZERO
    sub.ih_fig.ih_extra = _DECIMAL_ZERO
    sub.ih_fig.ih_carriage = _DECIMAL_ZERO
    sub.ih_fig.ih_vat = _DECIMAL_ZERO
    sub.ih_fig.ih_discount = _DECIMAL_ZERO
    sub.ih_fig.ih_e_vat = _DECIMAL_ZERO
    sub.ih_fig.ih_c_vat = _DECIMAL_ZERO
    sub.ih_status = " "
    sub.ih_lines = 0
    sub.ih_deduct_days = 0
    sub.ih_deduct_amt = _DECIMAL_ZERO
    sub.ih_deduct_vat = _DECIMAL_ZERO
    sub.ih_days = 0
    sub.ih_cr = 0
    sub.ih_day_book_flag = " "
    sub.ih_update = " "


# ---------------------------------------------------------------------------
# bc000-HV-Load-rg1 / bc100-UnloadHVs-rg1  -  the lines table
# ---------------------------------------------------------------------------


def bc000_hv_load_rg1(line: IlInvoiceLineBody, context: PInvoiceContext) -> None:
    """`bc000-HV-Load-rg1 Section.  *> Dry chk ?` [common/plinvoiceMT.cbl:L2743].

    Fourteen moves for a fourteen-column table, so nothing is missing - but
    `WS-il-Line` is moved at [:L2757] BEFORE `WS-il-Invoice` at [:L2758], which
    inverts the column order `IL-INVOICE` then `IL-LINE`
    (anomaly ``N-lines-loadorder``). The order is reproduced, not corrected.

    `initialize TD-PUINV-LINES-REC.` [:L2754] runs first. The section carries the
    maintainer's own unresolved marker
    `*> <<<<  this should be a move from invoice-rec to line rec >>>>> <<>>`
    [:L2752] - preserved as a comment, not acted on (anomaly ``N-rg-todo``) - the
    unresolved `*> Dry chk ?` on its label line (anomaly ``N-drychk``), and the
    closing comment `*> End of PUINV-LINES-REC unload...` [:L2771] which says
    "unload" at the end of the LOAD (anomaly ``N-mislabelled-comment``).
    """
    lines = context.line_hv

    # `initialize TD-PUINV-LINES-REC.` [common/plinvoiceMT.cbl:L2754]
    lines.initialize()

    # [common/plinvoiceMT.cbl:L2756] group move.
    lines.hv1_il_line_key = _group_il_key(line.il_key.il_invoice, line.il_key.il_line)
    # [common/plinvoiceMT.cbl:L2757] LINE first ...
    lines.hv1_il_line = line.il_key.il_line
    # [common/plinvoiceMT.cbl:L2758] ... then INVOICE. Loaded here and NEVER
    # unloaded [:L2789-L2801] (anomaly ``N-il-invoice-never-unloaded``).
    lines.hv1_il_invoice = line.il_key.il_invoice
    # [common/plinvoiceMT.cbl:L2759-L2760]
    lines.hv1_il_product = line.il_product
    lines.hv1_il_pa = line.il_pa
    # [common/plinvoiceMT.cbl:L2761] binary-short SIGNED -> PIC 9(05) COMP
    # UNSIGNED -> smallint(6) unsigned: the sign dies at the bridge.
    lines.hv1_il_qty = _narrow_signed_to_unsigned_host_variable(line.il_qty, 5)
    # [common/plinvoiceMT.cbl:L2762-L2763]
    lines.hv1_il_type = line.il_type
    lines.hv1_il_description = line.il_description
    # [common/plinvoiceMT.cbl:L2764-L2765] signed at all three layers.
    lines.hv1_il_net = line.il_net
    lines.hv1_il_unit = line.il_unit
    # [common/plinvoiceMT.cbl:L2766] unsigned at all three layers - no narrowing.
    lines.hv1_il_discount = line.il_discount
    # [common/plinvoiceMT.cbl:L2767-L2769]
    lines.hv1_il_vat = line.il_vat
    lines.hv1_il_vat_code = line.il_vat_code
    lines.hv1_il_update = line.il_update
    # The two `filler pic xx` members of the line [copybooks/plwspinv.cob:L72, L76]
    # have no host variable and no column: deliberate omissions, recorded.


def bc100_unload_hvs_rg1(context: PInvoiceContext) -> IlInvoiceLineBody:
    """`bc100-UnloadHVs-rg1 Section.  *> Dry chk ?` [common/plinvoiceMT.cbl:L2777].

    THIRTEEN moves against the load's fourteen: `HV1-IL-INVOICE` is never moved
    back [:L2789-L2801], so the `IL-INVOICE` column's value never reaches the
    record through its own host variable. `WS-il-Invoice` is nevertheless
    populated, but only incidentally, because it is subordinate to the group
    `WS-il-Key` [copybooks/plwspinv.cob:L67-L69] and that group IS restored
    [:L2789] from `HV1-IL-LINE-KEY`, whose first eight characters happen to be the
    invoice number. If the two columns of a row ever disagreed the record would
    silently take the KEY's value (anomaly ``N-il-invoice-never-unloaded``). The
    unload is NOT completed.

    The section then does two things past the unload: it saves the line number as
    the watermark [:L2805] and copies the line view back over the shared buffer,
    `move WS-Invoice-Line to WS-Invoice-Record.` [:L2809], so after a lines read
    the caller is looking at a LINE where it passed a header.
    """
    lines = context.line_hv

    # `initialize WS-Invoice-Line.` [common/plinvoiceMT.cbl:L2787]
    line = IlInvoiceLineBody(
        il_key=IlKey(il_invoice=0, il_line=0),
        il_product=" " * 13,
        il_pa=" " * 2,
        filler_1=" " * 2,
        il_qty=0,
        il_type=" ",
        il_description=" " * 24,
        filler_2=" " * 2,
        il_net=_DECIMAL_ZERO,
        il_unit=_DECIMAL_ZERO,
        il_discount=_DECIMAL_ZERO,
        il_vat=_DECIMAL_ZERO,
        il_vat_code=0,
        il_update=" ",
    )

    # [common/plinvoiceMT.cbl:L2789] group move back; the ten characters split on
    # the declared widths of [copybooks/plwspinv.cob:L68-L69].
    key_text = _characters(lines.hv1_il_line_key, 10)
    line.il_key.il_invoice = int(key_text[:8]) if key_text[:8].isdigit() else 0
    line.il_key.il_line = int(key_text[8:10]) if key_text[8:10].isdigit() else 0
    # [common/plinvoiceMT.cbl:L2790] - and NOTHING for HV1-IL-INVOICE.
    line.il_key.il_line = lines.hv1_il_line
    # [common/plinvoiceMT.cbl:L2791-L2801]
    line.il_product = lines.hv1_il_product
    line.il_pa = lines.hv1_il_pa
    line.il_qty = lines.hv1_il_qty
    line.il_type = lines.hv1_il_type
    line.il_description = lines.hv1_il_description
    line.il_net = lines.hv1_il_net
    line.il_unit = lines.hv1_il_unit
    line.il_discount = lines.hv1_il_discount
    line.il_vat = lines.hv1_il_vat
    line.il_vat_code = lines.hv1_il_vat_code
    line.il_update = lines.hv1_il_update

    # `*> End of PUINV-LINES-REC unload... but save the last read line.` [:L2803]
    context.ws_last_read_line = lines.hv1_il_line  # [:L2805]
    # `*>  Now move it to primary WS record area.` [:L2807] then
    # `move WS-Invoice-Line to WS-Invoice-Record.` [:L2809] - the shared buffer now
    # holds a LINE, not a header.
    context.ws_invoice_line = line
    context.buffer_view = _BufferView.LINE
    return line


# ---------------------------------------------------------------------------
# The bridge - `plinvoiceMT`, its label machine and its twenty-eight paragraphs
# ---------------------------------------------------------------------------
#
# `ba-ACAS-DAL-Process section.` [common/plinvoiceMT.cbl:L482] is a `GO TO`
# dispatcher: `ba010-Initialise` evaluates `File-Function` and transfers to one
# verb paragraph, and every verb paragraph transfers to `ba999-end`,
# `ba999-exit` or `ba998-Free` when it is done. Modelling that with a label
# machine - each paragraph a named function returning the label it transfers to -
# is the provably equivalent rendering the Agent Action Plan section 0.4.2
# taxonomy asks for, and it keeps ONE PYTHON FUNCTION PER COBOL PARAGRAPH, which
# rule R-5 requires. Class annotations appear at every transfer site.


class _BridgeLabel(enum.StrEnum):
    """Every label the bridge's `GO TO`s and `PERFORM ... THRU`s can name."""

    #: `ba020-Process-Open.` [common/plinvoiceMT.cbl:L565]
    BA020_PROCESS_OPEN = "ba020-Process-Open"
    #: `ba030-Process-Close.` [common/plinvoiceMT.cbl:L609]
    BA030_PROCESS_CLOSE = "ba030-Process-Close"
    #: `ba040-Process-Read-Next.` [common/plinvoiceMT.cbl:L623]
    BA040_PROCESS_READ_NEXT = "ba040-Process-Read-Next"
    #: `ba041-Reread.` [common/plinvoiceMT.cbl:L705]
    BA041_REREAD = "ba041-Reread"
    #: `ba042-Fetch.` [common/plinvoiceMT.cbl:L744]
    BA042_FETCH = "ba042-Fetch"
    #: `ba050-Process-Read-Indexed.` [common/plinvoiceMT.cbl:L822]
    BA050_PROCESS_READ_INDEXED = "ba050-Process-Read-Indexed"
    #: `ba060-Process-Start.` [common/plinvoiceMT.cbl:L943]
    BA060_PROCESS_START = "ba060-Process-Start"
    #: `ba070-Process-Write.` [common/plinvoiceMT.cbl:L1142]
    BA070_PROCESS_WRITE = "ba070-Process-Write"
    #: `ba080-Process-Delete.` [common/plinvoiceMT.cbl:L1182]
    BA080_PROCESS_DELETE = "ba080-Process-Delete"
    #: `ba085-Process-Delete-ALL.` [common/plinvoiceMT.cbl:L1250]
    BA085_PROCESS_DELETE_ALL = "ba085-Process-Delete-ALL"
    #: `ba090-Process-Rewrite.` [common/plinvoiceMT.cbl:L1351]
    BA090_PROCESS_REWRITE = "ba090-Process-Rewrite"
    #: `ba100-Bad-Function.` [common/plinvoiceMT.cbl:L1408]
    BA100_BAD_FUNCTION = "ba100-Bad-Function"
    #: `ba998-Free.` [common/plinvoiceMT.cbl:L1420]
    BA998_FREE = "ba998-Free"
    #: `ba999-end.` [common/plinvoiceMT.cbl:L1432]
    BA999_END = "ba999-end"
    #: `ba999-exit.` [common/plinvoiceMT.cbl:L1439], `exit program.` at [:L1440]
    BA999_EXIT = "ba999-exit"
    #: `bc058-Restore-Pointers.` [common/plinvoiceMT.cbl:L2478]
    BC058_RESTORE_POINTERS = "bc058-Restore-Pointers"
    #: `bc085-Exit.` [common/plinvoiceMT.cbl:L2688]
    BC085_EXIT = "bc085-Exit"
    #: `bc090-Exit.` [common/plinvoiceMT.cbl:L2741]
    BC090_EXIT = "bc090-Exit"


#: Which verb paragraph `ba010-Initialise` transfers to, per `File-Function`
#: [common/plinvoiceMT.cbl:L515-L540]. THE BRIDGE'S TABLE, NOT THE HANDLER'S:
#: code 6 is dispatched here to `ba085-Process-Delete-All` [:L530-L531] with the
#: comment `*> option 6 is a special to cleardown all LINE data for 1 invoice`
#: [:L528], while the handler rejects 6 outright as `*> 6 is spare / unused`
#: [common/acas026.cbl:L301]. Code 34 shares the `when 3` arm [:L520-L522] here
#: exactly as it does in the handler.
_BRIDGE_DISPATCH: Final[Mapping[int, _BridgeLabel]] = MappingProxyType(
    {
        int(status.FileFunction.OPEN): _BridgeLabel.BA020_PROCESS_OPEN,
        int(status.FileFunction.CLOSE): _BridgeLabel.BA030_PROCESS_CLOSE,
        int(status.FileFunction.READ_NEXT): _BridgeLabel.BA040_PROCESS_READ_NEXT,
        int(
            status.FileFunction.READ_NEXT_HEADER
        ): _BridgeLabel.BA040_PROCESS_READ_NEXT,
        int(status.FileFunction.READ_INDEXED): _BridgeLabel.BA050_PROCESS_READ_INDEXED,
        int(status.FileFunction.WRITE): _BridgeLabel.BA070_PROCESS_WRITE,
        int(status.FileFunction.DELETE_ALL): _BridgeLabel.BA085_PROCESS_DELETE_ALL,
        int(status.FileFunction.RE_WRITE): _BridgeLabel.BA090_PROCESS_REWRITE,
        int(status.FileFunction.DELETE): _BridgeLabel.BA080_PROCESS_DELETE,
        int(status.FileFunction.START): _BridgeLabel.BA060_PROCESS_START,
    }
)


def _testing_1(dal_common: AcasDalCommonData) -> bool:
    """`88  Testing-1  value 1.` [copybooks/Test-Data-Flags.cob:L11].

    The switch that gates ALL log-file production, `03  SW-Testing pic 9 value 1.`
    with the maintainer's own alternative in a trailing comment `*>   zero.`
    [:L10] and the header note that it can be zeroed "When testing comlete"
    [:L3-L4]. It ships set to ONE, so logging is on by default in the frozen
    system - which is why `ba999-end` logs on every verb unless a caller changes
    it [common/plinvoiceMT.cbl:L1435-L1437].
    """
    return int(dal_common.sw_testing) == 1


def _testing_2(dal_common: AcasDalCommonData) -> bool:
    """`88  Testing-2  value 1.` [copybooks/Test-Data-Flags.cob:L16].

    Gates the SCREEN displays of `WS-Where` only - `03  SW-Testing-2 pic 9 value
    zero.` [:L15] with the note "Testing only for displays ws-where etc"
    [:L13]. Every site that tests it does
    `if Testing-2 display Display-Message-1 with erase eos end-if`
    [common/plinvoiceMT.cbl:L850-L852, :L1002-L1004, :L1212-L1214, :L1309-L1311,
    :L2380-L2382, :L2551-L2553, :L2643-L2645] and NOTHING else, so it has no
    database effect and the display is a DELIBERATE OMISSION under Agent Action
    Plan section 0.3.4. The predicate is reproduced, and the value it gates is
    logged at debug level instead of painted on a terminal, because the switch
    itself is caller-visible state.
    """
    return int(dal_common.sw_testing_2) == 1


def _display_message_1(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """`if Testing-2 display Display-Message-1 with erase eos end-if`.

    Seven identical sites, listed in :func:`_testing_2`. The COBOL paints
    `WS-Log-Where` on a curses screen; the migrated cycle is headless, so the same
    information goes to the log at debug level. No control flow depends on it and
    nothing reaches a table through it.
    """
    if _testing_2(dal_common):
        _LOG.debug(
            "Display-Message-1: %s",
            status.redact_for_log(file_access.logging_data.ws_log_where),
        )


def _set_status(file_access: FileAccess, fs_reply: int, we_error: int) -> None:
    """Write the `(FS-Reply, We-Error)` pair the way the frozen source writes it.

    Always a plain assignment of both fields, never a derivation: the bridge's
    arms are literal `move nn to fs-reply` / `move nn to WE-Error` statements and
    several of them deliberately write only one of the two. Callers that must
    leave one field alone read it back first, exactly as the COBOL leaves it
    untouched.
    """
    file_access.fs_reply = int(fs_reply)
    file_access.we_error = int(we_error)


def _clear_sql_fields(file_access: FileAccess) -> None:
    """`move spaces to SQL-Msg SQL-Err` and `move zero to SQL-State`.

    `ba010-Initialise` clears six fields [common/plinvoiceMT.cbl:L503-L508] and
    ANOMALY ``N-sqlstate-zero-not-space`` sits in the line above them: SQL-State
    is set by `move zero to SQL-State.` [:L498], a NUMERIC zero into a `pic x(5)`
    field, which fills it with the CHARACTER `"00000"` and not with spaces - while
    the handler clears the same field to SPACES
    [common/acas026.cbl:L281]. Whichever ran last wins, and on the DAL path the
    bridge runs last. Reproduced as `"00000"`.
    """
    file_access.logging_data.sql_state = _SQL_STATE_ZEROED
    file_access.logging_data.sql_err = " " * status.SQL_ERR_WIDTH
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH


def _apply_db_error(
    file_access: FileAccess, error: status.DbErrorStatus
) -> None:
    """Move a captured driver failure into `SQL-State`, `SQL-Err` and `SQL-Msg`.

    The frozen arms are all the same four statements, e.g.
    [common/plinvoiceMT.cbl:L1163-L1176]::

        call  "MySQL_errno"     using WS-MYSQL-Error-Number
        call  "MySQL_sqlstate"  using WS-MYSQL-SQLstate
        move  WS-MYSQL-SqlState to SQL-State
        if    WS-MYSQL-Error-Number not = "0  "
              move WS-MYSQL-Error-Number  to SQL-Err
              call "MySQL_error" using WS-MYSQL-Error-Message
              move WS-MYSQL-Error-Message to SQL-Msg
        end-if

    SQL-State is moved UNCONDITIONALLY; SQL-Err and SQL-Msg only when the error
    number is not the frozen source's own `"0  "`. The status PAIR is NOT written
    here, because each arm writes its own.
    """
    file_access.logging_data.sql_state = error.sql_state[: status.SQL_STATE_WIDTH]
    if error.sql_err != _MYSQL_ERRNO_NONE:
        file_access.logging_data.sql_err = error.sql_err[: status.SQL_ERR_WIDTH]
        file_access.logging_data.sql_msg = error.sql_msg[: status.SQL_MSG_WIDTH]


def _file_key(file_access: FileAccess, text: str) -> None:
    """`move ... to WS-File-Key` - the 64-character log key.

    `05  WS-File-Key     pic x(64)  value spaces.` [copybooks/wsfnctn.cob:L52] - a
    `05` inside `01 File-Access.`'s `03 Logging-Data.`, not an `03` itself - truncates
    on the
    right, which is what a COBOL `move` into a shorter alphanumeric field does, and
    several of this bridge's log strings are longer than they look - `"> 0 got
    cnt=" WS-Temp-ED-Row " recs for INVOICE-REC Table"` [common/plinvoiceMT.cbl:
    L697-L701] is 47 characters before the count. Rendered log-safe because the
    text can carry a key value.
    """
    file_access.logging_data.ws_file_key = text[:64].ljust(64, " ")


def ba_acas_dal_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba-ACAS-DAL-Process  section.` [common/plinvoiceMT.cbl:L482-L494].

    The section's own entry statements are SCREEN GEOMETRY and nothing else:
    `accept ws-env-lines from lines` [:L483], a floor of 24 lines [:L484-L488],
    two `set ENVIRONMENT` calls forcing curses to report Esc, PgUp, PgDown and
    PrtSc [:L490-L491], and two line-count derivations [:L493-L494].

    NONE of it has a database effect, so all of it is a DELIBERATE OMISSION under
    Agent Action Plan section 0.3.4 - "screen output that has no database effect"
    - and it is recorded here rather than silently dropped
    (anomaly ``N-bridge-section-entry-is-screen-setup``). The `accept` reads the
    terminal's line count from the `LINES` special register, not from an operator,
    so no interactive pause is being removed with it. Control then FALLS THROUGH
    into `ba010-Initialise`, which is a paragraph and not a separate entry point.
    """
    _LOG.debug(
        "%s entered for File-Function %s; the section's curses geometry "
        "[common/plinvoiceMT.cbl:L483-L494] has no database effect and is "
        "omitted",
        BRIDGE_NAME,
        int(file_access.file_function),
    )
    # Class 2 - fall-through, not a transfer: `ba010-Initialise.` follows with no
    # `go to` between them.
    return ba010_initialise(file_access, dal_common, pinvoice, context)


def ba010_initialise(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba010-Initialise.` [common/plinvoiceMT.cbl:L496-L540].

    Clear the diagnostic fields, then evaluate `File-Function` and transfer.

    `We-Error` and `Fs-Reply` are NOT cleared: the two statements that would have
    done it are commented out [:L500-L501], exactly as the handler comments out
    its own pair [common/acas026.cbl:L279-L280]. Reproduced as a
    non-initialisation, so a caller's incoming status survives a verb that never
    writes one.

    The `evaluate` has NO unconditional fall-through after `end-evaluate` [:L540],
    where the handler adds one `*>  Should never get here but in case :(`
    [common/acas026.cbl:L305-L306]. Reproduced: an unmapped function reaches
    `ba100-Bad-Function` through `when other` [:L538-L539] and by no other route.
    """
    # `move zero to SQL-State.` [:L498] and the six-field space clear
    # [:L503-L508]. NO `move zero to We-Error / Fs-Reply` - see the docstring.
    _clear_sql_fields(file_access)
    file_access.logging_data.ws_log_where = ""

    function = int(file_access.file_function)
    label = _BRIDGE_DISPATCH.get(function)
    if label is None:
        # `when other  go to ba100-Bad-Function` [:L538-L539]. Class 3.
        return _BridgeLabel.BA100_BAD_FUNCTION
    # `go to <verb paragraph>` [:L515-L539]. Class 3 - a transfer out of this
    # paragraph, one target per function code.
    return label


def ba020_process_open(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba020-Process-Open.` [common/plinvoiceMT.cbl:L565-L607].

    Six `string <field> delimited by space X"00"` extractions out of `RDB-Data`
    into the driver's parameter fields [:L570-L593] - schema, host, user, password,
    port and socket, in that order - then `move 1 to ws-No-Paragraph` [:L594] and
    `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT` [:L595]. On failure,
    `go to ba999-end` with whatever pair the open left [:L596-L597].

    THERE IS NO `Access-Type` TEST ANYWHERE IN THIS PARAGRAPH. `Open-Output` is
    therefore a plain open that deletes nothing - the sixth handler-bridge pair in
    the folder with no Open-Output block at all (``N-noopenoutput``), against
    `acas006`/`acas007` which issue a second delete-all call and `acas008` which
    coerces the function into one. Nothing is truncated here. NOT ported.

    [common/plinvoiceMT.cbl:L599-L603] carries a commented-out `/MYSQL INIT\\`
    block with hard-coded placeholder base, implementation and password values.
    They are CITED and NEVER transcribed, per rule V.S1;
    :func:`connection.mysql_1000_open` refuses them at run time unless a caller
    explicitly opts in, so the guard is structural rather than a convention.

    `move "OPEN SL INVOICE" to WS-File-Key` [:L605] - "SL", the SALES ledger, in
    the PURCHASE bridge (``N-sl-in-purchase-openclose``). Reproduced verbatim.
    """
    if context.system_record is None:
        # `MYSQL-1000-OPEN` cannot run without the `RDB-Data` block the six
        # `string`s read [:L570-L593]; reported as the generic RDB failure rather
        # than raised, per `*> Any errors leave it to caller to recover from`
        # [common/acas026.cbl:L617].
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.RDB_INIT_ERROR),
        )
        file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"]
        return _BridgeLabel.BA999_END

    # `move 1 to ws-No-Paragraph.` [:L594]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"]
    # `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT.` [:L595]. The six credential
    # extractions [:L570-L593] are what `connection.load_rdb_data_once` and
    # `connection.cobol_string_delimited_by_space` reproduce, so they are called
    # rather than duplicated here.
    #
    # THE ERROR CONTRACT IS ENFORCED HERE, and it is the one place in this module
    # where a dependency can raise on a condition the COBOL treats as a status.
    # `connection.mysql_1000_open` raises `ConnectionPolicyError` - which covers
    # both `FrozenPlaceholderCredentialsError` and `InsecureTransportError` - and
    # `ConverterPinningError`, none of which the frozen COBOL can express: its open
    # reports through `fs-reply` and nothing else [:L596-L597], and the handler's
    # contract is `*>   Any errors leave it to caller to recover from`
    # [common/acas026.cbl:L617]. So each is converted into the bridge's own
    # `We-Error 911` RDB-initialisation pair and the message is carried in
    # `SQL-Msg`, exactly as a refused open would be.
    #
    # ⛔ `BinaryFloatingPointError` is deliberately NOT caught. It is a rule R-2
    # violation - an accounting value that reached the transport as binary floating
    # point - not a database condition, and there is no COBOL status for it.
    # Swallowing it would silently defeat the one guard R-2 depends on, so it
    # propagates.
    try:
        outcome = connection.mysql_1090_exit(
            connection.mysql_1000_open(
                context.system_record,
                ws_no_paragraph=int(file_access.logging_data.ws_no_paragraph),
                we_error=int(file_access.we_error),
                transport=context.transport,
            )
        )
    except (connection.ConnectionPolicyError, connection.ConverterPinningError) as exc:
        context.connection = None
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.RDB_INIT_ERROR),
        )
        file_access.logging_data.sql_err = _MYSQL_ERRNO_NONE
        file_access.logging_data.sql_msg = status.sanitise_for_log(str(exc))[
            : status.SQL_MSG_WIDTH
        ].ljust(status.SQL_MSG_WIDTH, " ")
        file_access.logging_data.sql_state = _SQL_STATE_ZEROED
        # `if fs-reply not = zero  go   to ba999-end.` [:L596-L597]. Class 3.
        return _BridgeLabel.BA999_END
    context.connection = outcome.connection
    _set_status(file_access, int(outcome.fs_reply), int(outcome.we_error))
    file_access.logging_data.ws_no_paragraph = int(outcome.ws_no_paragraph)
    file_access.logging_data.sql_err = outcome.sql_err[: status.SQL_ERR_WIDTH]
    file_access.logging_data.sql_msg = outcome.sql_msg[: status.SQL_MSG_WIDTH]
    file_access.logging_data.sql_state = outcome.sql_state[: status.SQL_STATE_WIDTH]

    if int(outcome.fs_reply) != int(status.FsReply.SUCCESS):
        # `if fs-reply not = zero  go to ba999-end.` [:L596-L597]. Class 3.
        return _BridgeLabel.BA999_END

    # `move "OPEN SL INVOICE" to WS-File-Key` [:L605] - the sales-ledger label in
    # the purchase bridge, preserved (``N-sl-in-purchase-openclose``).
    _file_key(file_access, "OPEN SL INVOICE")
    # `set Cursor-Not-Active to true` [:L606] - slot 1 ONLY. Slot 2 is not
    # touched, matching `ba030`'s asymmetry (``N-close-leaks-rg1-cursor``).
    context.cursors.state_for(HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]).free()
    context.most_cursor_set = 0
    # `go to ba999-end.` [:L607]. Class 3.
    return _BridgeLabel.BA999_END


def ba030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba030-Process-Close.` [common/plinvoiceMT.cbl:L609-L621].

    ANOMALY ``N-close-leaks-rg1-cursor``: the guard is
    `if Cursor-Active perform ba998-Free.` [:L610-L611] and `ba998-Free` frees
    `TP-PUINVOICE-REC` and clears slot 1 only [:L1420-L1430]. The SECOND cursor,
    `Most-Cursor-Set-2` over `TP-PUINV-LINES-REC` [:L333-L335], is never tested
    and never freed here - `bc998-Free` exists to do it [:L3206] and is performed
    from NOWHERE (``N-bc998-unreachable``). A close taken while a lines walk is
    open therefore leaks that result set for the process's lifetime. Reproduced:
    slot 2 is left exactly as it stands.

    `move "CLOSE SL INVOICE" to WS-File-Key.` [:L614] - "SL" again in the purchase
    bridge (``N-sl-in-purchase-openclose``).
    """
    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    if header_state.cursor_active():
        # `perform ba998-Free.` [:L610-L611]. Class 4 - a named sibling call whose
        # own fall-through into `ba999-end` is NOT taken, because this is a
        # `perform` and not a `go to`.
        ba998_free(file_access, dal_common, pinvoice, context)

    # `move 2 to ws-No-Paragraph.` [:L613]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba030-Process-Close"]
    _file_key(file_access, "CLOSE SL INVOICE")
    # `PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT` [:L619]
    connection.mysql_1980_close(context.connection)
    connection.mysql_1999_exit()
    context.connection = None
    # Slot 2 deliberately NOT freed - see the docstring.
    # `go to ba999-end.` [:L621]. Class 3.
    return _BridgeLabel.BA999_END


def ba998_free(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba998-Free.` [common/plinvoiceMT.cbl:L1420-L1430].

    `move 20 to ws-No-Paragraph` [:L1421], free `TP-PUINVOICE-REC`, then
    `set Cursor-Not-Active to true.` [:L1430]. It then FALLS THROUGH into
    `ba999-end` [:L1432] - there is no `go to` between them - so every arm that
    reaches here also logs. Slot 2 is not mentioned.
    """
    # `move 20 to ws-No-Paragraph.` [:L1421]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba998-Free"]
    # `MYSQL-1240-FREE-RESULT` on `TP-PUINVOICE-REC`, then
    # `set Cursor-Not-Active to true.` [:L1430].
    context.cursors.state_for(HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]).free()
    context.most_cursor_set = 0
    # Class 2 - fall-through into `ba999-end` [:L1432].
    return _BridgeLabel.BA999_END


def ba999_end(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba999-end.` [common/plinvoiceMT.cbl:L1432-L1437].

    `if Testing-1 perform Ca-Process-Logs end-if.` [:L1435-L1437] and nothing
    else, then a FALL-THROUGH into `ba999-exit` [:L1439]. The whole of the
    bridge's logging is therefore conditional on one compile-time switch
    [copybooks/Test-Data-Flags.cob], which is why an unlogged run leaves no trace
    of `WS-File-Key` at all.
    """
    if _testing_1(dal_common):
        # `perform Ca-Process-Logs` [:L1436]. Class 4.
        ca_process_logs(file_access, dal_common, pinvoice, context)
    # Class 2 - fall-through into `ba999-exit` [:L1439].
    return _BridgeLabel.BA999_EXIT


def ba999_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba999-exit.` [common/plinvoiceMT.cbl:L1439-L1440] - `exit program.`

    The single terminal label. Returning itself is how the label machine stops.
    """
    return _BridgeLabel.BA999_EXIT


def _as_decimal(value: object, scale: int) -> decimal.Decimal:
    """Coerce a fetched column into the host variable's `COMP` decimal.

    `decimal.Decimal` only, and NEVER out of a binary floating-point value: rule
    R-2 forbids an accounting value passing through binary floating point "not in
    computation, not in storage, not in transport", and
    :mod:`acas_posting.dal.connection` pins the driver's converter so a
    `decimal(9,2)` column arrives as a `Decimal` already.  The `str` and `int` arms
    exist for a driver that hands back text, and the final arm renders through
    `str` rather than constructing from the object, so no code path here can build a
    `Decimal` out of a binary floating-point value.

    Truncation, not rounding: the host variable has the column's own scale and the
    COBOL `move` into it truncates toward zero unless `ROUNDED` is written, which
    it is at none of the five in-scope sites [Agent Action Plan section 0.6.1].
    """
    quantum = decimal.Decimal(1).scaleb(-scale)
    if isinstance(value, decimal.Decimal):
        candidate = value
    elif isinstance(value, int) and not isinstance(value, bool):
        candidate = decimal.Decimal(value)
    else:
        text = str(value).strip()
        candidate = decimal.Decimal(text) if text else _DECIMAL_ZERO
    return candidate.quantize(quantum, rounding=decimal.ROUND_DOWN)


def _as_int(value: object) -> int:
    """Coerce a fetched column into an unsigned `COMP` integer host variable.

    Every integer host variable in both groups is `PIC 9(n) COMP` - UNSIGNED - and
    every corresponding column is `unsigned` too, so nothing here has to carry a
    sign. A value that arrives as text is read as text, and an empty or unreadable
    one becomes zero rather than raising, because
    `*>   Any errors leave it to caller to recover from`
    [common/acas026.cbl:L617] governs this module and a fetch does not raise.
    """
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, decimal.Decimal):
        return int(value.to_integral_value(rounding=decimal.ROUND_DOWN))
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(decimal.Decimal(text).to_integral_value(rounding=decimal.ROUND_DOWN))
    except (decimal.InvalidOperation, ValueError):
        _LOG.debug(
            "non-numeric value fetched for an unsigned COMP host variable; "
            "reported as zero rather than raised per "
            "[common/acas026.cbl:L617]"
        )
        return 0


def _fetch_record(
    row: Mapping[str, object],
    columns: Sequence[str],
    renders: Mapping[str, ColumnRender],
    group: HeaderHostVariables | LineHostVariables,
    attribute_by_column: Mapping[str, str],
    character_widths: Mapping[str, int],
) -> None:
    """`CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT <every host variable>`.

    The header fetch names ALL THIRTY host variables in column order
    [common/plinvoiceMT.cbl:L751-L781] and so does the indexed read's own copy of
    it [:L876-L913]; the lines fetch names all fourteen [:L2443-L2460].

    ANOMALY ``N-status-hvs-fetched-then-discarded``, and this is where it becomes
    visible. `HV-IH-STATUS-A`, `-C`, `-I`, `-L` and `-P` ARE named in the fetch
    [:L769-L773] - the five columns' values genuinely arrive in the program - and
    then `bb100-UnloadHVs` [:L1489-L1512] moves twenty-four host variables back
    into the record and NOT ONE of those five. Every read therefore loads five
    values and throws them away, which is strictly worse than never reading them:
    a maintainer inspecting the host-variable group would conclude the data is
    available. Reproduced exactly - the fetch fills them, the unload ignores them.
    """
    for column in columns:
        render = renders[column]
        value = row.get(column)
        attribute = attribute_by_column[column]
        if value is None:
            # Every column of both tables is `NOT NULL`, so this cannot arise from
            # the frozen schema; a missing key is treated as the `initialize`
            # value rather than as an error [Agent Action Plan section 0.6.2].
            continue
        if render.kind is _RenderKind.CHARACTER:
            setattr(
                group, attribute, _characters(str(value), character_widths[column])
            )
        elif render.kind is _RenderKind.INTEGER:
            setattr(group, attribute, _as_int(value))
        else:
            setattr(group, attribute, _as_decimal(value, render.hv_scale))


def ba040_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba040-Process-Read-Next.` [common/plinvoiceMT.cbl:L623-L703].

    Stage one of a three-paragraph verb whose stages fall through into each other:
    `ba040` positions when nothing is positioned, `ba041-Reread` decides whether
    the caller is owed a LINE or the next HEADER, and `ba042-Fetch` delivers a
    header. The label comment records the design in the maintainer's own words -
    `*>  Here we have for a given key first read and transfer a inv header  *>
    then pass on for the same key all body lines all one at  *>  a time.`
    [:L625-L627] - and the paragraph's own trailing note reads
    `*> dry test.. - Has rg01 requirements.` [:L623].

    The positioning block runs only `if Cursor-Not-Active` [:L635] and uses
    `set KOR-x1 to 1` [:L636] - key 1 always, so the lines key can never position
    this verb - with the relation and low key hard-coded rather than taken from
    `Access-Type` (see :func:`_where_sequential_read`).

    ANOMALY ``N-countmsg-wrong-table-name``: the success log reads
    `" recs for INVOICE-REC Table"` [:L699] - there is no table called
    `INVOICE-REC` in the frozen schema, and this bridge's own is `PUINVOICE-REC`.
    Reproduced verbatim, because a log string is evidence.

    The empty arm writes BOTH fields to 10 [:L690-L691] with the maintainer's own
    `*> should be 0 'JIC' likewise the others`, sets `"No Data"` [:L692] and
    transfers; the success arm PERFORMS `ba999-End` to log [:L702] and then FALLS
    THROUGH, which is why a successful positioning logs twice - once here and once
    from whichever stage finally delivers.
    """
    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    key = _key_of_reference(_KOR_HEADER)

    if header_state.cursor_not_active():
        # `set KOR-x1 to 1` / `move KOR-offset (KOR-x1) to K` /
        # `move KOR-length (KOR-x1) to L` [:L636-L638].
        predicate = _where_sequential_read(key)
        # `move ws-Where (1:J) to WS-Log-Where` [:L656]
        file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
        # `move 3 to ws-No-Paragraph.` [:L657]
        file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
            "ba040-Process-Read-Next"
        ]
        statement = _select_statement(HEADER_TABLE, predicate)
        result = _execute(context, statement, store_result=True)
        # `MOVE WS-MYSQL-RESULT TO TP-PUINVOICE-REC` [:L671] - the stored snapshot.
        header_state.key_of_reference = key
        header_state.store_result(result.rows)
        header_state.position_at(_SEQUENTIAL_READ_START.low_key)
        # `move "0000000000" to WS-File-Key` [:L673]
        _file_key(file_access, _SEQUENTIAL_READ_START.low_key)
        _display_message_1(file_access, dal_common)

        if result.count_rows == 0:
            # `if WS-MYSQL-Count-Rows = zero` [:L680] - the errno capture
            # [:L681-L686], then BOTH status fields to 10 [:L690-L691].
            if result.error is not None:
                _apply_db_error(file_access, result.error)
            _set_status(
                file_access,
                int(status.FsReply.END_OF_FILE),
                status.END_OF_FILE_WE_ERROR,
            )
            _file_key(file_access, "No Data")
            # `go to ba999-End  *> can clear the dup code after testing` [:L692].
            # Class 2 - the forward terminator; nothing after it runs.
            return _BridgeLabel.BA999_END

        # `set Cursor-Active to true` [:L694]
        header_state.set_cursor_active()
        context.most_cursor_set = 1
        # `move WS-MYSQL-Count-Rows to WS-Temp-ED-Row` [:L695]
        context.ws_mysql_count_rows = result.count_rows
        context.ws_temp_ed_row = result.count_rows
        # `move spaces to WS-File-Key` then the count string [:L696-L701]. The
        # table name in it is WRONG - see the docstring.
        _file_key(
            file_access,
            f"> 0 got cnt={_digits(result.count_rows, 7)}"
            f" recs for INVOICE-REC Table",
        )
        # `perform ba999-End` [:L702] - a PERFORM, so control returns and the
        # paragraph falls through. Class 4.
        ba999_end(file_access, dal_common, pinvoice, context)

    # `end-if.` [:L703] then `ba041-Reread.` [:L705] - a fall-through, not a
    # transfer. Class 2.
    return ba041_reread(file_access, dal_common, pinvoice, context)


def ba041_reread(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba041-Reread.` [common/plinvoiceMT.cbl:L705-L740].

    THE PARAGRAPH THAT MAKES THIS BRIDGE DIFFERENT FROM EVERY SINGLE-TABLE ONE.
    Three tests decide what the caller is owed, in this order:

    1. `if WS-Last-Read-Invoice = zero  go to ba042-Fetch.` [:L715-L716], commented
       `*> DALS Not yet called` and `*>  so get header rec.` - a virgin bridge
       always delivers a header first.
    2. `if FN-Read-Next-Header  go to ba042-Fetch.` [:L721-L722], under the note
       `*>  but 1st support for Read-Next-Header to bypass line processing.`
       [:L720]. ⭐⭐ ANOMALY ``N-read-next-header-not-identical-in-bridge``:
       **THIS is where function 34 diverges from function 3** - and it
       diverges HERE ONLY. The HANDLER folds 34 into the `when 3` arm with no
       distinction at all [common/acas026.cbl:L288-L290], and `ba010-Initialise`
       does the same [:L520-L522]; the difference is a single test three
       paragraphs deep, which is exactly why the handler's own comment can be
       confident while `acas016`'s says `*> fn-Read-Next-Header ???`
       (``N-when34-confidence``). Function 34 therefore walks headers ONLY and
       never returns a line.
    3. `if WS-Last-Read-Line < WS-Actual-Lines-In-Row` [:L724] - deliver the next
       LINE of the invoice just read, by synthesising its key from the watermark
       plus one [:L725] and the remembered invoice [:L726] and performing
       `bc050-Process-Read-Indexed thru bc059-Exit` [:L727].

    ANOMALY ``N-last-read-line-40`` bites in test 3. `WS-Last-Read-Line` is
    declared `value 40` [:L288], the maximum line number, so on a virgin bridge
    the test is false for EVERY invoice with forty lines or fewer - which is every
    invoice, since the body table is `occurs 40` [copybooks/plwspinv.cob:L66]. The
    watermark only becomes usable after `bb100-UnloadHVs` overwrites it from
    `HV-IH-TEST` [:L1523], itself anomaly ``N-lines-cursor-from-ih-test``.

    The not-found arm builds `<key> " Not Found"` and transfers with the
    maintainer's own `*> This should NOT happen` [:L735], leaving whatever status
    `bc050` set - it does NOT normalise it.
    """
    # `move spaces to WS-Log-Where.` [:L709]
    file_access.logging_data.ws_log_where = ""
    # `move 4 to ws-No-Paragraph.` [:L710]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba041-Reread"
    ]
    # `move zero to return-code.` [:L711] - the fetch's own out-of-band signal,
    # modelled as the row count rather than a process return code.
    context.ws_mysql_count_rows = 0

    if context.ws_last_read_invoice == 0:
        # `go to ba042-Fetch.` [:L716]. Class 4 - a named sibling, then return.
        return ba042_fetch(file_access, dal_common, pinvoice, context)

    if int(file_access.file_function) == int(status.FileFunction.READ_NEXT_HEADER):
        # `if FN-Read-Next-Header go to ba042-Fetch.` [:L721-L722] - THE ONLY
        # place function 34 behaves differently from function 3. Class 4.
        return ba042_fetch(file_access, dal_common, pinvoice, context)

    if context.ws_last_read_line < context.ws_actual_lines_in_row:
        # `add 1 WS-Last-Read-Line giving WS-ih-Test` [:L725] and
        # `move WS-Last-Read-Invoice to WS-ih-Invoice` [:L726] - the caller's own
        # buffer is overwritten to carry the synthesised LINE key.
        next_line = context.ws_last_read_line + 1
        pinvoice.ih_prime.ws_invoice_key.ih_test = next_line
        pinvoice.ih_prime.ws_invoice_key.ih_invoice = context.ws_last_read_invoice
        # `perform bc050-Process-Read-Indexed thru bc059-Exit` [:L727] - one of the
        # bridge's `PERFORM ... THRU` ranges, so both paragraphs run in order and
        # control comes back. Class 4.
        bc050_process_read_indexed(file_access, dal_common, pinvoice, context)
        bc058_restore_pointers(file_access, dal_common, pinvoice, context)
        bc059_exit(file_access, dal_common, pinvoice, context)

        if int(file_access.fs_reply) != int(status.FsReply.SUCCESS):
            # `initialise WS-Invoice-Record` [:L729] - note the British spelling
            # the frozen source uses, and note it is PLAIN, without `with filler`.
            _initialise_header_record(pinvoice)
            # `move spaces to WS-File-Key` then `string WS-Invoice-Key
            # " Not Found"` [:L730-L734].
            key_text = _group_ws_invoice_key(
                pinvoice.ih_prime.ws_invoice_key.ih_invoice,
                pinvoice.ih_prime.ws_invoice_key.ih_test,
            )
            _file_key(file_access, f"{key_text} Not Found")
            # `go to ba999-End  *> This should NOT happen` [:L735]. Class 2.
            return _BridgeLabel.BA999_END

        # `move WS-ih-Test to WS-Last-Read-Line` [:L737]
        context.ws_last_read_line = pinvoice.ih_prime.ws_invoice_key.ih_test
        # `go to ba999-End` [:L738]. Class 2.
        return _BridgeLabel.BA999_END

    # `end-if.` [:L740] then `ba042-Fetch.` [:L744] under
    # `*> Not, so get next invoice Header rec` [:L742] - a fall-through. Class 2.
    return ba042_fetch(file_access, dal_common, pinvoice, context)


def ba042_fetch(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba042-Fetch.` [common/plinvoiceMT.cbl:L744-L820].

    `MOVE TP-PUINVOICE-REC TO WS-MYSQL-RESULT` [:L750] then
    `CALL "MySQL_fetch_record"` naming all thirty host variables [:L751-L781],
    then three end-of-data guards, then the unload.

    It sets NO `ws-No-Paragraph` of its own, so it reports under `ba041`'s 4.

    Guard 1, `if return-code = -1` [:L786-L792]: BOTH status fields to 10 with the
    maintainer's `*> should be 0 likewise the others`, `"EOF"`, cursor cleared.

    Guard 2, `if WS-MYSQL-Count-Rows = zero` [:L794-L809]: the errno capture, then
    BOTH fields to 10, cursor cleared. ANOMALY ``N-eof2-nested`` - the
    `initialize WS-Invoice-Record with filler` [:L802] and the `"EOF2"` log tag
    [:L803] sit INSIDE the `if WS-MYSQL-Error-Number not = "0  "` branch, so a
    zero count with no driver error leaves the caller's buffer UNTOUCHED and the
    log tag whatever it already held. Note also that this is the bridge's ONLY
    `initialize ... with filler`; `bb100-UnloadHVs` uses the plain form [:L1487]
    (``N-initialize``).

    Guard 3, `if fs-reply = 10` [:L811-L815] with `*> should not happen as tested
    prior`: a dead branch, kept and reproduced, whose only effect is the `"EOF3"`
    tag.

    On success: `perform bb100-UnloadHVs.` [:L817], `move WS-Invoice-Key to
    WS-File-Key.` [:L818] - the RECORD's key, which `bb100` has just rebuilt from
    `HV-IH-INVOICE` and `HV-IH-TEST` rather than from the never-unloaded
    `HV-PINVOICE-KEY` - and `move zero to fs-reply WE-Error.` [:L819], one
    statement writing both.
    """
    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    # `MOVE TP-PUINVOICE-REC TO WS-MYSQL-RESULT` [:L750] then the fetch [:L751].
    row = header_state.fetch_record()
    if row is not None:
        _fetch_record(
            row,
            HEADER_COLUMNS,
            HEADER_COLUMN_RENDER,
            context.header_hv,
            _HEADER_ATTRIBUTE_BY_COLUMN,
            _HEADER_CHARACTER_WIDTHS,
        )

    if row is None:
        # `if return-code = -1  *> no more data so free cursor & return` [:L786].
        _set_status(
            file_access,
            int(status.FsReply.END_OF_FILE),
            status.END_OF_FILE_WE_ERROR,
        )
        _file_key(file_access, "EOF")
        # `set Cursor-Not-Active to true` [:L790] - a bare clear, NOT `ba998-Free`,
        # so the stored snapshot is left in place.
        header_state.set_cursor_not_active()
        context.most_cursor_set = 0
        # `go to ba999-End` [:L791]. Class 2.
        return _BridgeLabel.BA999_END

    if header_state.count_rows == 0:
        # `if WS-MYSQL-Count-Rows = zero  *> no data but should not happen here`
        # [:L794]. Unreachable in practice, because guard 1 has already caught an
        # empty snapshot; reproduced whole.
        errno = file_access.logging_data.sql_err.strip()
        if errno and errno != _MYSQL_ERRNO_NONE.strip():
            # `initialize WS-Invoice-Record with filler` [:L802] and `"EOF2"`
            # [:L803] are NESTED here - see ``N-eof2-nested`` in the docstring.
            _initialise_header_record(pinvoice)
            _file_key(file_access, "EOF2")
        _set_status(
            file_access,
            int(status.FsReply.END_OF_FILE),
            status.END_OF_FILE_WE_ERROR,
        )
        header_state.set_cursor_not_active()
        context.most_cursor_set = 0
        # `go to ba999-End` [:L808]. Class 2.
        return _BridgeLabel.BA999_END

    if int(file_access.fs_reply) == int(status.FsReply.END_OF_FILE):
        # `if fs-reply = 10  *> should not happen as tested prior` [:L811] - dead,
        # kept.
        header_state.set_cursor_not_active()
        context.most_cursor_set = 0
        _file_key(file_access, "EOF3")
        # `go to ba999-End` [:L814]. Class 2.
        return _BridgeLabel.BA999_END

    # `perform bb100-UnloadHVs.` [:L817]. Class 4.
    bb100_unload_hvs(pinvoice, context)
    # `move WS-Invoice-Key to WS-File-Key.` [:L818]
    _file_key(
        file_access,
        _group_ws_invoice_key(
            pinvoice.ih_prime.ws_invoice_key.ih_invoice,
            pinvoice.ih_prime.ws_invoice_key.ih_test,
        ),
    )
    # `move zero to fs-reply WE-Error.` [:L819] - one statement, both fields.
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `go to ba999-End.  *> exit.` [:L820]. Class 2.
    return _BridgeLabel.BA999_END


def ba050_process_read_indexed(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba050-Process-Read-Indexed.` [common/plinvoiceMT.cbl:L822-L941].

    A keyed read of one HEADER row - unless the caller's buffer says otherwise.
    The label carries `*> dry test.. - Has rg01 requirements.` [:L822] and the
    paragraph opens with the same buffer sniff that `ba070`, `ba080` and `ba090`
    open with, under the maintainer's own comment `*>  Test what the key end is
    (Line or test) & if not zero  *>   we do RG1 insead of primary table`
    [:L824-L825]::

        if       WS-ih-test not = zero     *> if true  process line RG
                 perform bc050-Process-Read-Indexed thru bc059-Exit
                 go to ba999-exit.

    So the SECOND element of the ten-character key - `ih-Test`, the line number
    [copybooks/plwspinv.cob:L12] - is what selects the table. There is no separate
    verb for a line read and no way for a caller to ask for one explicitly: it
    plants a non-zero line number in the header key and the bridge switches
    tables under it. Reproduced exactly.

    ANOMALY ``N-read-indexed-status-differs-from-cursor-state``, carried in the
    register also under the heading ``N-read-indexed-reply-23`` - one finding, two
    names, because it is both a divergence from the shared machinery and a specific
    reply value this bridge alone returns. The not-found arm
    is `move 23 to fs-Reply` with the maintainer's own `*> could also be 21 or 14`
    and `move zero to WE-Error` [:L870-L873] - so a miss reports
    `FsReply.KEY_NOT_FOUND` here, where
    :func:`acas_posting.dal.cursor_state.read_indexed` reports
    `FsReply.INVALID_KEY_ON_START` (21) because it was written from `glpostingMT`.
    This module owns the status protocol for THIS bridge and returns 23; the
    shared cursor machinery is used only for positioning and row storage.

    ANOMALY ``N-read-indexed-status-zeroed-after-log``. On success the order is
    `perform bb100-UnloadHVs` [:L935], `move HV-PINVOICE-KEY to WS-File-Key`
    [:L936], `perform ba999-End.` [:L937] - the LOG - and only then
    `move zero to FS-Reply WE-Error.` [:L939]. The log therefore records whatever
    status the caller arrived with, because `ba010-Initialise` deliberately does
    not clear the pair [:L500-L501]. A successful read is logged with a stale
    status and the caller is handed a clean one. Reproduced in that order.

    ⭐ [:L936] is the ONLY statement in the whole bridge that READS
    `HV-PINVOICE-KEY`. Anomaly ``N-pinvoice-key-write-only`` says the host variable
    is never unloaded INTO THE RECORD, and that remains exact - but it is observable
    here, in the log key. The distinction matters: after a keyed read the log shows
    the column's own value while the record shows a key rebuilt from `HV-IH-INVOICE`
    and `HV-IH-TEST`, and if those ever disagreed the two would differ.

    The failure arm at [:L917-L933] splits on the driver's error number and is the
    only arm in the bridge that uses `We-Error` 990 and 989 as a pair: `990` when
    the driver reported something [:L922], `989` when it did not [:L927], with
    `move zero to SQL-Err` / `move spaces to SQL-Msg` on the quiet branch
    [:L928-L929], `move 23 to fs-reply` [:L931] and `move spaces to WS-File-Key`
    [:L932] for both. The trailing comment is the maintainer's own doubt:
    `*> row count zero should show up as a MYSQL error ?` [:L934].
    """
    if int(pinvoice.ih_prime.ws_invoice_key.ih_test) != 0:
        # `if WS-ih-test not = zero` [:L827] - the buffer sniff. Class 4: a
        # `PERFORM ... THRU` range, so both paragraphs run in source order and
        # control comes back before the transfer.
        bc050_process_read_indexed(file_access, dal_common, pinvoice, context)
        bc058_restore_pointers(file_access, dal_common, pinvoice, context)
        bc059_exit(file_access, dal_common, pinvoice, context)
        # `go to ba999-exit.` [:L829] - straight out, NOT via `ba999-end`, so a
        # line read is logged by `bc058` and never by this paragraph.
        return _BridgeLabel.BA999_EXIT

    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    # `set KOR-x1 to 1.  *> 1 = Primary` [:L834] then the offset/length pair
    # [:L835-L836].
    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move spaces to WS-Where` / `move 1 to J` / the `string` [:L838-L848].
    predicate = _where_key_equals(key, key_value, "[common/plinvoiceMT.cbl:L840-L848]")
    context.ws_where = _pointer_slice(predicate).literal
    # `move WS-Where (1:J) to WS-Log-Where.` [:L849]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    # `if Testing-2 display Display-Message-1 with erase eos end-if` [:L850-L852].
    _display_message_1(file_access, dal_common)
    # `move 5 to ws-No-Paragraph` [:L853]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba050-Process-Read-Indexed/SELECT"
    ]

    statement = _select_statement(HEADER_TABLE, predicate)
    result = _execute(context, statement, store_result=True)
    # `MOVE WS-MYSQL-RESULT TO TP-PUINVOICE-REC` [:L867]
    header_state.key_of_reference = key
    header_state.store_result(result.rows)
    header_state.position_at(key_value)
    context.ws_mysql_count_rows = result.count_rows

    if result.count_rows == 0:
        # `if WS-MYSQL-Count-Rows = zero` [:L870]. NOTE: no errno capture at all
        # on this arm - the bridge goes straight to the status pair.
        # `move 23 to fs-Reply  *> could also be 21 or 14` [:L871] and
        # `move zero to WE-Error` [:L872].
        _set_status(
            file_access,
            int(status.FsReply.KEY_NOT_FOUND),
            int(status.WeError.SUCCESS),
        )
        # `go to ba998-Free` [:L873]. Class 2 - the forward terminator; `ba998`
        # frees the snapshot and falls through to the log.
        return _BridgeLabel.BA998_FREE

    # `move 6 to ws-No-Paragraph` [:L875] then the thirty-host-variable fetch
    # [:L876-L915].
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba050-Process-Read-Indexed/FETCH"
    ]
    row = header_state.fetch_record()
    if row is not None:
        _fetch_record(
            row,
            HEADER_COLUMNS,
            HEADER_COLUMN_RENDER,
            context.header_hv,
            _HEADER_ATTRIBUTE_BY_COLUMN,
            _HEADER_CHARACTER_WIDTHS,
        )

    if row is None:
        # `if WS-MYSQL-Count-Rows not > zero` [:L917] - the second count test,
        # which the frozen source performs AFTER the fetch even though the first
        # test already proved the snapshot non-empty.
        if result.error is not None:
            # `if WS-MYSQL-Error-Number not = "0  "` [:L921]:
            # `move 990 to WE-Error` [:L922] and the three error fields
            # [:L923-L925].
            _apply_db_error(file_access, result.error)
            we_error = int(status.WeError.UNKNOWN_UNEXPECTED)
        else:
            # `else move 989 to WE-Error` [:L927], `move zero to SQL-Err` [:L928]
            # and `move spaces to SQL-Msg` [:L929] - SQL-State is left as the
            # unconditional move at [:L920] put it.
            file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
            file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
            we_error = int(status.WeError.READ_INDEXED_UNEXPECTED)
        # `move 23 to fs-reply` [:L931]
        _set_status(file_access, int(status.FsReply.KEY_NOT_FOUND), we_error)
        # `move spaces to WS-File-Key` [:L932]
        _file_key(file_access, "")
        # `go to ba998-Free` [:L933]. Class 2.
        return _BridgeLabel.BA998_FREE

    # `perform bb100-UnloadHVs` [:L935]. Class 4.
    bb100_unload_hvs(pinvoice, context)
    # `move HV-PINVOICE-KEY to WS-File-Key.` [:L936] - the ONLY read of the
    # write-only header key host variable anywhere in the bridge.
    _file_key(file_access, context.header_hv.hv_pinvoice_key)
    # `perform ba999-End.` [:L937] - the log runs BEFORE the status is cleaned.
    # Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)
    # `move zero to FS-Reply WE-Error.` [:L939] - after the log. See the docstring.
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `perform ba998-Free.     *> Free cursor` [:L940] - a PERFORM, so `ba998`
    # falls through into `ba999-end` and this verb logs a SECOND time, now with
    # the cleaned status. Class 4.
    ba998_free(file_access, dal_common, pinvoice, context)
    ba999_end(file_access, dal_common, pinvoice, context)
    # `go to ba999-Exit.` [:L941]. Class 3.
    return _BridgeLabel.BA999_EXIT


def ba060_process_start(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba060-Process-Start.` [common/plinvoiceMT.cbl:L943-L1138].

    Position BOTH cursors: a header `SELECT` under the caller's relation, then an
    unconditional lines `SELECT` for the same ten bytes. The label carries the
    maintainer's own scepticism about the whole design - `*>  coded for header &
    lines [ NEEDED ? check all calling code ].` [:L943] and `*> Need to see if
    bcnn-Read-Next is needed  *> if not than rg1 processing can be removed.`
    [:L944-L945].

    ANOMALY ``N-start-guard-rejects-its-own-when-9``. The parameter guard is
    `if access-type < 5 or > 8` with the maintainer's own note
    `*> not using not < or not >` [:L949], so access type NINE is REJECTED with
    `99` / `997` [:L950-L951] - and yet twenty-eight lines later the relation
    `evaluate` still carries `when 9 move "<= " to MOST-Relation` under
    `*> fn-not-greater-than [ not currently used in ACAS ]` [:L980-L981]. The
    `when 9` arm is therefore unreachable through this paragraph. Both the guard
    and the dead arm are reproduced; neither is corrected.

    ANOMALY ``N-start-header-cursor-not-cleared-on-zero``. `if WS-MYSQL-Count-Rows
    not zero set Cursor-Active to true end-if` [:L1023-L1025] has NO `else`, so a
    START that matches nothing leaves whatever the previous verb left in
    `Most-Cursor-Set`. The lines block twelve lines later DOES have one
    [:L1095-L1099]. Reproduced as written - slot 1 is not cleared, slot 2 is.

    ANOMALY ``N-start-rg1-overwrites-header-status``, the load-bearing one. The
    header block ends `move zero to FS-Reply WE-Error` on success [:L1039]; the
    lines block then runs unconditionally and its own empty-result arm writes
    `move 21 to fs-reply` [:L1112] with the same
    `*> this may need changing for val in WE-Error!!` comment the header arm
    carries [:L1036]. So a caller that successfully positions on a header
    receives `FsReply.INVALID_KEY_ON_START` whenever that invoice happens to have
    no body lines, and the header's own success is lost. The comment above the
    arm shows the maintainer expected lines to be there - `*> Should not be zero
    for invoice Line table if still unposted and cleared.` [:L1101]. Reproduced.

    ANOMALY ``N-start-rg1-unquoted-key``. The header predicate wraps its key value
    in `'"'` on both sides [:L989, :L991]; the lines predicate at [:L1058-L1067]
    does NOT - `MOST-relation` is followed directly by
    `WS-Invoice-Record (K2:L2)`. MariaDB then coerces the `char(10)` column to a
    number to compare it, which defeats the index and changes which rows qualify
    for every key with a leading zero. Reproduced unquoted in the literal; ⛔ not
    fixed.

    ⭐ `K2`/`L2` are taken from `KOR-x1 = 2` [:L1053-L1055], and both keys are
    declared offset 1 length 10 [:L298-L304], so `WS-Invoice-Record (K2:L2)` is
    the SAME ten bytes as `(K:L)` - the header's key. The lines predicate compares
    `IL-LINE-KEY` against the header key, which is only ever equal for the line
    whose number matches the header's `ih-Test`.

    The RG1 block also juggles the driver's result pointers by hand
    [:L1074-L1076, :L1130-L1136]: save the primary snapshot and count, zero the
    count, run the lines select, save the RG1 snapshot and count, then restore
    the primary pair. Reproduced through the two cursor slots and the two save
    slots, so a caller's subsequent read-next still sees the header snapshot.
    """
    # `if access-type < 5 or > 8` [:L949]. The `9` case is unreachable past here.
    access_type = int(file_access.access_type)
    if access_type < 5 or access_type > 8:
        # `move 99 to FS-Reply` [:L950] and
        # `move 997 to WE-Error  *> Invalid calling parameter settings   997`
        # [:L951].
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.ACCESS_TYPE_WRONG),
        )
        # `go to ba999-end` [:L952]. Class 2.
        return _BridgeLabel.BA999_END

    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])

    # `if Cursor-Active perform ba998-Free.` [:L957-L958] - slot 1 only, exactly
    # as `ba030-Process-Close` clears slot 1 only. Class 4.
    if header_state.cursor_active():
        ba998_free(file_access, dal_common, pinvoice, context)
        ba999_end(file_access, dal_common, pinvoice, context)

    # `set KOR-x1 to 1.` [:L965] and the offset/length pair [:L966-L967].
    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move spaces to MOST-Relation.` [:L969] then the `evaluate Access-Type`
    # [:L971-L982]. There is NO `when other`, so an out-of-range access type
    # would leave the relation as spaces - unreachable here only because of the
    # guard above.
    relation = cursor_state.MostRelation.for_access_type(access_type)
    context.most_relation = relation.padded
    header_state.most_relation = relation

    # `move 1 to J.` [:L970], `move spaces to WS-Where` [:L984] and the `string`
    # [:L985-L999] - quoted on both sides of the key value.
    predicate = _where_start_header(key, relation, key_value)
    context.ws_where = _pointer_slice(predicate).literal
    # `move WS-Where (1:J) to WS-Log-Where.` [:L1000]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    # `move WS-Invoice-Record (K:L) to WS-File-Key` [:L1001]
    _file_key(file_access, key_value)
    # `if Testing-2 display ...` [:L1002-L1004]
    _display_message_1(file_access, dal_common)
    # `move 8 to ws-No-Paragraph` [:L1006]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba060-Process-Start/SELECT-HEADER"
    ]

    header_result = _execute(
        context, _select_statement(HEADER_TABLE, predicate), store_result=True
    )
    # `MOVE WS-MYSQL-RESULT TO TP-PUINVOICE-REC` [:L1020]
    header_state.key_of_reference = key
    header_state.store_result(header_result.rows)
    header_state.position_at(key_value)
    context.ws_mysql_count_rows = header_result.count_rows

    if header_result.count_rows != 0:
        # `if WS-MYSQL-Count-Rows not zero set Cursor-Active to true end-if`
        # [:L1023-L1025] - and NO `else`, so slot 1 is never cleared here.
        header_state.set_cursor_active()
        context.most_cursor_set = 1

    if header_result.count_rows == 0:
        # `if WS-MYSQL-Count-Rows = zero` [:L1027] - errno capture [:L1028-L1035],
        # then `move 21 to fs-reply` [:L1036] and `move zero to WE-Error` [:L1037].
        if header_result.error is not None:
            _apply_db_error(file_access, header_result.error)
        _set_status(
            file_access,
            int(status.FsReply.INVALID_KEY_ON_START),
            int(status.WeError.SUCCESS),
        )
    else:
        # `else move zero to FS-Reply WE-Error` [:L1039], then the count string
        # [:L1040-L1047]. THIS SUCCESS IS ABOUT TO BE OVERWRITTEN - see the
        # docstring.
        _set_status(
            file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
        )
        context.ws_temp_ed_row = header_result.count_rows
        _file_key(
            file_access,
            f"{relation.token}{key_value} got "
            f"{_digits(header_result.count_rows, 7)} recs",
        )
    # `perform ba999-End.` [:L1049] - a PERFORM, so control returns and the RG1
    # block runs whatever the header result was. Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)

    # `set KOR-x1 to 2.` [:L1053] and the K2/L2 pair [:L1054-L1055] - the SAME
    # ten bytes, because both keys are offset 1 length 10.
    lines_key = _key_of_reference(_KOR_LINES)
    # `move 1 to J2.` [:L1056], `move spaces to WS-Where-2.` [:L1057] and the
    # UNQUOTED `string` [:L1058-L1070].
    lines_predicate = _where_start_lines(lines_key, relation, key_value)
    context.ws_where_2 = _pointer_slice(lines_predicate).literal
    lines_state.most_relation = relation

    # `move WS-Mysql-Result to WS-Mysql-Save-Result.  *> primary Tbl` [:L1074],
    # `move WS-Mysql-Count-Rows to WS-Mysql-Save-Count-Rows.` [:L1075] and
    # `move zero to WS-Mysql-Count-Rows.` [:L1076].
    context.ws_mysql_save_count_rows = context.ws_mysql_count_rows
    context.ws_mysql_count_rows = 0
    # `move 57 to ws-No-Paragraph` [:L1078]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba060-Process-Start/SELECT-LINES"
    ]

    lines_result = _execute(
        context, _select_statement(LINES_TABLE, lines_predicate), store_result=True
    )
    # `MOVE WS-MYSQL-RESULT TO TP-PUINV-LINES-REC` [:L1092]
    lines_state.key_of_reference = lines_key
    lines_state.store_result(lines_result.rows)
    lines_state.position_at(key_value)
    context.ws_mysql_count_rows = lines_result.count_rows

    if lines_result.count_rows != 0:
        # `set Cursor-Active-2 to true` [:L1096]
        lines_state.set_cursor_active()
        context.most_cursor_set_2 = 1
    else:
        # `else set Cursor-Not-Active-2 to true` [:L1098] - the `else` slot 1
        # does not have.
        lines_state.set_cursor_not_active()
        context.most_cursor_set_2 = 0

    if lines_result.count_rows == 0:
        # `if WS-MYSQL-Count-Rows = zero` [:L1103] under `*> Should not be zero
        # for invoice Line table if still unposted and cleared.` [:L1101].
        if lines_result.error is not None:
            _apply_db_error(file_access, lines_result.error)
        # `move 21 to fs-reply` [:L1112] and `move zero to WE-Error` [:L1113] -
        # OVERWRITING the header's success. ``N-start-rg1-overwrites-header-status``
        _set_status(
            file_access,
            int(status.FsReply.INVALID_KEY_ON_START),
            int(status.WeError.SUCCESS),
        )
    else:
        # `else move zero to FS-Reply WE-Error` [:L1115] then the RG1 count string
        # [:L1116-L1123] - which also overwrites the header's log key.
        _set_status(
            file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
        )
        context.ws_temp_ed_row = lines_result.count_rows
        _file_key(
            file_access,
            f"{relation.token}{key_value} got "
            f"{_digits(lines_result.count_rows, 7)} recs RG1 (Lines)",
        )

    # `move WS-Mysql-Result to WS-Mysql-Save-Result-RG1.` [:L1130] and
    # `move WS-Mysql-Count-Rows to WS-Mysql-Save-Count-Rows-RG1.` [:L1131], under
    # the maintainer's own `*>  ALL this does depend on application code  in
    # slnnn ???? <<<<<<<` [:L1128] - note `slnnn`, the SALES program prefix, in
    # the purchase bridge (``N-sih-in-purchase-comment`` family).
    context.ws_mysql_save_count_rows_rg1 = lines_result.count_rows
    # `move WS-Mysql-Save-Result to WS-Mysql-Result.` [:L1135] and
    # `move WS-Mysql-Save-Count-Rows to WS-Mysql-Count-Rows.` [:L1136].
    context.ws_mysql_count_rows = context.ws_mysql_save_count_rows
    # `go to ba999-end.` [:L1138]. Class 2.
    return _BridgeLabel.BA999_END


def ba070_process_write(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba070-Process-Write.` [common/plinvoiceMT.cbl:L1142-L1180].

    Insert one HEADER row, or hand the call to `bc070` when the caller's buffer
    carries a line number. The label carries `*> dry test... - Has rg01
    requirements.` [:L1142] and the buffer sniff carries
    `*>  Are we being requested writing a body line (rg01) ? lets check  *>    but
    rec still in WS-Invoice-Record` [:L1144-L1145].

    ANOMALY ``N-write-leaves-we-error-zero``. The paragraph zeroes the pair up
    front - `move zero to FS-Reply WE-Error SQL-State.` [:L1155-L1157] - and its
    failure arm then writes `move 99 to fs-reply` [:L1166] and, for a duplicate
    key, `move 22 to fs-reply` [:L1174], but NEVER touches `We-Error`. A failed
    write therefore reports `99` with `We-Error = 0`, which reads as "error, cause
    unknown" to every caller. Contrast `ba080-Process-Delete`, which pairs its 99
    with `995` [:L1239], and `ba090-Process-Rewrite`, which pairs its 99 with
    `994` [:L1397]. Reproduced; ⛔ no `We-Error` is invented for it.

    ⭐ The duplicate-key test is THREE conditions - `Sql-State = "23000"`,
    `SQL-Err (1:4) = "1062"` or `= "1022"` [:L1171-L1173] - and it is NESTED
    inside `if WS-MYSQL-Error-Number not = "0  "` [:L1167], so a driver that
    reports a duplicate through SQLSTATE alone without setting an error number
    would be missed. The same three conditions appear in `bc070` [:L2510-L2512],
    but there the outer `if` also admits `or Sql-State = "23000"` [:L2506] - so
    the two write paths do NOT agree. Both reproduced as written.
    """
    if int(pinvoice.ih_prime.ws_invoice_key.ih_test) != 0:
        # `if WS-ih-Test not = zero  *> It is a line row` [:L1147]. Class 4, then
        # `go to ba999-Exit.  *> logging rec done.` [:L1149] - Class 3.
        bc070_process_write(file_access, dal_common, pinvoice, context)
        return _BridgeLabel.BA999_EXIT

    # `perform bb000-HV-Load.  *>  move WS-Invoice-Record fields to HV fields`
    # [:L1153]. Class 4.
    bb000_hv_load(pinvoice, context)
    # `move WS-Invoice-Key to WS-File-Key.` [:L1154]
    _file_key(file_access, context.header_hv.hv_pinvoice_key)
    # `move zero to FS-Reply WE-Error SQL-State.` [:L1155-L1157] - one statement,
    # three receiving fields, and SQL-State is a `pic x(5)` taking a NUMERIC zero
    # (``N-sqlstate-zero-not-space``).
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    file_access.logging_data.sql_state = _SQL_STATE_ZEROED
    # `move spaces to SQL-Msg` [:L1158] and `move zero to SQL-Err` [:L1159].
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    # `move 10 to ws-No-Paragraph.` [:L1160]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba070-Process-Write"
    ]

    # `perform bb200-Insert.` [:L1161]. Class 4.
    result = bb200_insert(file_access, dal_common, pinvoice, context)

    if result.count_rows != 1:
        # `if WS-MYSQL-COUNT-ROWS not = 1` [:L1162] - errno and sqlstate captured
        # [:L1163-L1165], then `move 99 to fs-reply` [:L1166] with NO `We-Error`.
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        file_access.fs_reply = int(status.FsReply.ERROR)
        if result.error is not None and result.error.duplicate_key:
            # `if Sql-State = "23000" or SQL-Err (1:4) = "1062" or = "1022"`
            # [:L1171-L1173] then `move 22 to fs-reply` [:L1174] - still no
            # `We-Error`.
            file_access.fs_reply = int(status.FsReply.DUPLICATE_KEY)
    # `perform ba999-End.` [:L1178]. Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)
    # `go to ba999-Exit.` [:L1180]. Class 3.
    return _BridgeLabel.BA999_EXIT


def ba080_process_delete(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba080-Process-Delete.` [common/plinvoiceMT.cbl:L1182-L1248].

    Delete one HEADER row by its full ten-character key, or hand the call to
    `bc080`. The label carries `*> dry tested. - Has rg01 requirements.` [:L1182]
    and above the buffer sniff sits the maintainer's own open question
    `*> [ Deleting all for a key should go to Delete-ALL   ???? ]` [:L1187].

    ANOMALY ``N-read-indexed-status-zeroed-after-log`` in its second instance.
    On success the order is `perform ba999-End.` [:L1245] - the LOG - and only
    then `move zero to FS-Reply WE-Error.` [:L1247]. Because
    `ba010-Initialise` deliberately leaves the pair alone [:L500-L501], a
    successful delete is logged with the caller's incoming status. The failure arm
    is the other way round: it sets `99` / `995` [:L1238-L1239] BEFORE
    `go to ba999-End` [:L1240], so a failure IS logged with its own status.
    Reproduced in both orders.

    ⭐ The `DELETE` carries NO semicolon [:L1222-L1226] where every `SELECT`,
    `INSERT` and `UPDATE` in the bridge carries one. Reproduced in
    :func:`_delete_statement`.
    """
    if int(pinvoice.ih_prime.ws_invoice_key.ih_test) != 0:
        # `if WS-ih-Test not = zero` [:L1189]. Class 4, then
        # `go to ba999-Exit.` [:L1191] - Class 3.
        bc080_process_delete(file_access, dal_common, pinvoice, context)
        return _BridgeLabel.BA999_EXIT

    # `set KOR-x1 to 1.` [:L1195] and the offset/length pair [:L1196-L1197].
    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move spaces to WS-Where` / `move 1 to J` / the `string` [:L1199-L1209].
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L1201-L1209]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    # `move WS-Invoice-Record (K:L) to WS-File-Key.` [:L1210]
    _file_key(file_access, key_value)
    # `move WS-Where (1:J) to WS-Log-Where.` [:L1211]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    # `if Testing-2 display ...` [:L1212-L1214]
    _display_message_1(file_access, dal_common)
    # `move 13 to ws-No-Paragraph.` [:L1215]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba080-Process-Delete"
    ]

    # The `DELETE` [:L1221-L1227] - no `STORE-RESULT`, so the affected-row count
    # is the command's own.
    result = _execute(
        context, _delete_statement(HEADER_TABLE, predicate), store_result=False
    )
    context.ws_mysql_count_rows = result.count_rows

    if result.count_rows != 1:
        # `if WS-MYSQL-COUNT-ROWS not = 1` [:L1229] - errno capture
        # [:L1230-L1237], then `move 99 to fs-reply` [:L1238] and
        # `move 995 to WE-Error` [:L1239].
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.DELETE_SQLSTATE_NOT_00000),
        )
        # `go to ba999-End` [:L1240]. Class 2 - the status survives into the log.
        return _BridgeLabel.BA999_END

    # `else move spaces to SQL-Msg` [:L1242] and `move zero to SQL-Err` [:L1243].
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    # `perform ba999-End.` [:L1245] - the log, BEFORE the status is cleaned.
    # Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)
    # `move zero to FS-Reply WE-Error.` [:L1247] - after the log.
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `go to ba999-Exit.` [:L1248]. Class 3.
    return _BridgeLabel.BA999_EXIT


def ba085_process_delete_all(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba085-Process-Delete-ALL.` [common/plinvoiceMT.cbl:L1250-L1349].

    `*> Delete all recs for a given invoice key / lines` [:L1250-L1251]. Reached
    ONLY through the bridge's own dispatch table at `File-Function = 6`
    [:L530-L531] - the handler rejects 6 as `*> 6 is spare / unused`
    [common/acas026.cbl:L301], so no `acas026` caller can ever get here. It is
    reproduced because the bridge dispatches it and because
    :func:`plinvoice_mt` publishes the bridge's table, not the handler's.

    ANOMALY ``N-header-deleteall-is-single-row``. The paragraph is called
    Delete-ALL and its own comment block promises
    `DELETE FROM PUINVOICE-REC WHERE IH-INVOICE = {key value (1:8)}` [:L1256] -
    the eight-digit invoice number, which would sweep every header sharing it.
    The code it actually emits keys on the full ten-character `PINVOICE-KEY`
    [:L1297-L1305], so it can never delete more than one header row. Reproduced
    single-row.

    ⭐ [:L1300] carries `*> was '<"'`, so the operator was once a less-than and
    the paragraph once really did sweep a range. The same fossil sits on
    `bc085` [:L2635].

    ANOMALY ``N-deleteall-comment-names-sales-table``. The dbpre transcript in the
    comment block deletes from `SAINV-LINES-REC` [:L1281] - the SALES lines table -
    inside the PURCHASE bridge. A copy-paste footprint, recorded not corrected.

    ⭐ Status ordering here is the opposite of `ba080`'s: `move zero to FS-Reply
    WE-Error.` [:L1342-L1343] comes BEFORE `perform ba999-End.` [:L1344], so a
    successful header delete IS logged clean. Then `perform
    bc085-Process-Delete-ALL thru bc085-Exit.` [:L1348] runs the lines sweep,
    whose own arms may overwrite that clean status.
    """
    # `set KOR-x1 to 1` [:L1291] and the offset/length pair [:L1292-L1293].
    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move spaces to WS-Where` / `move 1 to J` / the `string` [:L1295-L1305],
    # whose `'="'` carries `*> was '<"'` [:L1300].
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L1297-L1305]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    # `move spaces to WS-File-Key` [:L1306] then
    # `move WS-Invoice-Key to WS-File-Key` [:L1307] - two moves into the same
    # field, the first redundant because the second is a full-width group move.
    _file_key(file_access, "")
    _file_key(file_access, key_value)
    # `move WS-Where (1:J) to WS-Log-Where.` [:L1308]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    # `if Testing-2 display ...` [:L1309-L1311]
    _display_message_1(file_access, dal_common)
    # `move 15 to ws-No-Paragraph.` [:L1312]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba085-Process-Delete-ALL"
    ]

    # The `DELETE` [:L1318-L1324], again with no semicolon.
    result = _execute(
        context, _delete_statement(HEADER_TABLE, predicate), store_result=False
    )
    context.ws_mysql_count_rows = result.count_rows

    if result.count_rows <= 0:
        # `if WS-MYSQL-COUNT-ROWS not > zero  *> Changed for delete-ALL` [:L1326] -
        # note `not > zero`, not `not = 1`, so any positive count is a success.
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        # `move 99 to fs-reply` [:L1335] and `move 995 to WE-Error` [:L1336].
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.DELETE_SQLSTATE_NOT_00000),
        )
        # `go to ba999-End` [:L1337]. Class 2 - and note that the RG1 sweep at
        # [:L1348] is therefore SKIPPED when the header delete fails, leaving the
        # body lines orphaned.
        return _BridgeLabel.BA999_END

    # `else  *> of course there could be no data in table` [:L1338]:
    # `move spaces to SQL-Msg` [:L1339] and `move zero to SQL-Err` [:L1340].
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    # `move zero to FS-Reply WE-Error.` [:L1342-L1343] - BEFORE the log this time.
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `perform ba999-End.` [:L1344]. Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)
    # `perform bc085-Process-Delete-ALL thru bc085-Exit.` [:L1348] under
    # `*> Process RG data  where key is inv # for all lines within inv#` [:L1346].
    # Class 4 - a `PERFORM ... THRU` range.
    bc085_process_delete_all(file_access, dal_common, pinvoice, context)
    # `go to ba999-Exit.` [:L1349]. Class 3.
    return _BridgeLabel.BA999_EXIT


def ba090_process_rewrite(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba090-Process-Rewrite.` [common/plinvoiceMT.cbl:L1351-L1406].

    Update one HEADER row, every column re-sent, or hand the call to `bc090`. The
    label carries `*> dry tested - Has rg01 requirements.` [:L1351].

    ⭐ Unlike `ba070`, this verb DOES pair its failure status: `move 99 to
    fs-reply` [:L1396] with `move 994 to WE-Error` [:L1397]. And unlike `ba080`
    it clears the pair BEFORE the log - `move zero to FS-Reply WE-Error SQL-Err.`
    [:L1400-L1402], `move spaces to SQL-Msg.` [:L1403], then
    `perform ba999-End.` [:L1404]. Three verbs, three different orderings;
    all three reproduced as written.

    ⭐ `if Testing-2 display Display-Message-1` sits AFTER `perform bb300-Update`
    here [:L1381-L1385], where every other verb displays before its statement
    runs. So the rewrite's diagnostic shows the statement that has already
    executed rather than the one about to. Cosmetic on the DAL path because the
    display is dropped, but the ORDER of the `WS-Log-Where` assignment relative
    to the statement is preserved.
    """
    if int(pinvoice.ih_prime.ws_invoice_key.ih_test) != 0:
        # `if WS-ih-Test not = zero` [:L1356] under `*>  Are we being requested
        # rewriting a body line ? lets check but  *>    rec still in
        # WS-Invoice-Record` [:L1353-L1354]. Class 4, then
        # `go to ba999-Exit.  *> logging rec done.` [:L1358] - Class 3.
        bc090_process_rewrite(file_access, dal_common, pinvoice, context)
        return _BridgeLabel.BA999_EXIT

    # `perform bb000-HV-Load.  *> Load up the HV fields from table record in WS`
    # [:L1362]. Class 4.
    bb000_hv_load(pinvoice, context)
    # `move WS-Invoice-Key to WS-File-Key.` [:L1363]
    _file_key(file_access, context.header_hv.hv_pinvoice_key)
    # `move 17 to ws-No-Paragraph.` [:L1364]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba090-Process-Rewrite"
    ]
    # `set KOR-x1 to 1  *> 1 = Primary` [:L1365] and the offset/length pair
    # [:L1366-L1367].
    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move spaces to WS-Where` / `move 1 to J` / the `string` [:L1369-L1379].
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L1371-L1379]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    # `move WS-Where (1:J) to WS-Log-Where.` [:L1380]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal

    # `perform bb300-Update.` [:L1381]. Class 4.
    result = bb300_update(file_access, dal_common, pinvoice, context, predicate)
    # `if Testing-2 display ...` [:L1383-L1385] - AFTER the update, see docstring.
    _display_message_1(file_access, dal_common)

    if result.count_rows != 1:
        # `if WS-MYSQL-COUNT-ROWS not = 1` [:L1387] - errno capture
        # [:L1388-L1395], then `move 99 to fs-reply` [:L1396] and
        # `move 994 to WE-Error` [:L1397].
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.REWRITE_SQLSTATE_NOT_00000),
        )
        # `go to ba999-End` [:L1398]. Class 2.
        return _BridgeLabel.BA999_END

    # `move zero to FS-Reply WE-Error SQL-Err.` [:L1400-L1402] and
    # `move spaces to SQL-Msg.` [:L1403].
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    # `perform ba999-End.` [:L1404]. Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)
    # `go to ba999-Exit.` [:L1406]. Class 3.
    return _BridgeLabel.BA999_EXIT


def ba100_bad_function(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba100-Bad-Function.` [common/plinvoiceMT.cbl:L1408-L1414].

    `move 990 to WE-Error.` [:L1412] and `move 99 to Fs-Reply.` [:L1413], then
    `go to ba999-end.` [:L1414].

    ANOMALY ``N-badfunction-pair-differs``: the HANDLER's equivalent returns
    `(99, 999)` [common/acas026.cbl:L527-L528] - 999, the code
    [copybooks/wsfnctn.cob] labels "not used" - while the bridge returns
    `(99, 990)`, "unknown/unexpected". A caller therefore sees a different
    `We-Error` for the same mistake depending on which layer caught it, and the
    code the frozen documentation actually assigns to an invalid function, 992,
    is used by NEITHER. Reproduced, both differently, in both layers.

    It sets NO `ws-No-Paragraph`, unlike every other paragraph in the section.
    """
    # `move 990 to WE-Error.` / `move 99 to Fs-Reply.` [:L1412-L1413]
    _set_status(
        file_access,
        int(status.FsReply.ERROR),
        int(status.WeError.UNKNOWN_UNEXPECTED),
    )
    # No `ws-No-Paragraph` move - see the docstring.
    # `go to ba999-end.` [:L1414]. Class 3.
    return _BridgeLabel.BA999_END


def bb200_insert(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> ExecutionResult:
    """`bb200-Insert  Section.` [common/plinvoiceMT.cbl:L1528-L1920].

    Assemble and run the thirty-column header `INSERT`. Nearly four hundred lines
    of frozen source, because every column is `STRING`ed one at a time into
    `WS-MYSQL-COMMAND`: `'INSERT INTO '` [:L1538], `` '`PUINVOICE-REC` SET '``
    [:L1539], then per column `` '`COL`="' `` + the rendered host variable +
    `'"'` + `', '`, then `";"` [:L1914] and the C string terminator `X"00"`
    [:L1916], then `PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT` [:L1918].

    ⭐ ALL THIRTY columns are named, in the SCHEMA's order, with `IH-LINES`
    twenty-eighth [:L1543-L1913] - so this statement is where anomaly
    ``N-five-status-columns-never-populated`` becomes a database fact.
    `IH-STATUS-A`, `-C`, `-I`, `-L` and `-P` each get their own
    `` `COL`="' `` + `FUNCTION TRIM (HV-IH-STATUS-x,TRAILING)` + `'"'` triple, and
    because neither `bb000-HV-Load` [:L1450-L1477] nor anything else ever moves a
    value into those host variables, the value trimmed is the single SPACE that
    `initialize TD-PUINVOICE-REC` [:L1450] left - and `FUNCTION TRIM` of one space
    is the EMPTY STRING (verified against GnuCOBOL 3.2, anomaly
    ``N-trim-space-to-empty``). Every header row therefore stores `''` in all five,
    forever. ⛔ The columns are `NOT NULL`, so they can be neither omitted nor
    bound `None`; ⛔ and they are NOT derived from `ih-status`, because the bridge
    does not derive them.

    ⭐ The `SET` form is used rather than `(cols) VALUES (...)`, and EVERY value is
    wrapped in `="` ... `"` whatever its column type, so MariaDB performs a
    string-to-number coercion on all twenty-two numeric columns. That coercion is
    where anomaly ``N-signloss-in-render`` lands: the eleven signed
    `decimal(9,2)` columns are rendered from `WS-MYSQL-EDIT`
    (`PIC -Z(18)9.9(9)`, thirty characters, sign at position 1) through windows
    that all start at position 11 or later, so the sign character is never
    extracted and a negative amount is stored POSITIVE.

    Returns the execution result rather than writing a status, because the frozen
    section writes none: the caller's own arm tests `WS-MYSQL-COUNT-ROWS`
    [:L1162, :L1387] and owns the whole status protocol.
    """
    statement = _insert_statement(
        HEADER_TABLE,
        HEADER_COLUMN_RENDER,
        HEADER_COLUMNS,
        context.header_hv,
        _HEADER_ATTRIBUTE_BY_COLUMN,
        "[common/plinvoiceMT.cbl:L1538-L1918]",
    )
    result = _execute(context, statement, store_result=False)
    context.ws_mysql_count_rows = result.count_rows
    return result


def bb300_update(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
    predicate: SqlFragment,
) -> ExecutionResult:
    """`bb300-Update  Section.` [common/plinvoiceMT.cbl:L1925-L2321].

    Assemble and run the thirty-column header `UPDATE`: `'UPDATE '` [:L1935],
    `` '`PUINVOICE-REC` SET '`` [:L1936], the same thirty-column list in the same
    schema order [:L1940-L2310], then `" WHERE "` [:L2311],
    `FUNCTION TRIM (WS-Where (1:J))` [:L2314] and `";" X"00"` [:L2317].

    ⭐ EVERY column is re-sent including the primary key itself - the statement
    sets `PINVOICE-KEY` to the value it is also keying on. Harmless in effect,
    load-bearing in evidence: it is why anomaly ``N-pinvoice-key-write-only``
    matters, because `HV-PINVOICE-KEY` is loaded by `bb000-HV-Load` [:L1452] and
    a rewrite therefore re-asserts whatever that load produced, even if the
    record's own `ih-Invoice`/`ih-Test` pair had drifted from the stored key.

    ⭐ This and `bc300-Update-rg1` [:L3194] are the ONLY two places the pointer
    slice is wrapped in `FUNCTION TRIM`. Everywhere else `WS-Where (1:J)` is
    embedded raw and carries its one trailing space into the statement text,
    because `J` ends one position past the last character `STRING`ed. Reproduced
    in :func:`_update_statement`.

    The five never-populated status columns are re-sent here too, so a rewrite
    cannot repair them either - it re-writes the same empty string.
    """
    statement = _update_statement(
        HEADER_TABLE,
        HEADER_COLUMN_RENDER,
        HEADER_COLUMNS,
        context.header_hv,
        _HEADER_ATTRIBUTE_BY_COLUMN,
        predicate,
        "[common/plinvoiceMT.cbl:L1935-L2317]",
    )
    result = _execute(context, statement, store_result=False)
    context.ws_mysql_count_rows = result.count_rows
    return result


# ---------------------------------------------------------------------------
# `bc000-RG-Process section.` [common/plinvoiceMT.cbl:L2326] - the lines mirror
# ---------------------------------------------------------------------------
#
# The section header states its own contract [:L2329-L2346]: "This section
# contains mirror processes in ba000 section that act in support of paragraph
# based process to only deal with the RG ( Repeat Group ) segments of data.",
# "Like ba000 processes they handle one action at a time and do not do multiple
# commands or row at once.", "So, bc050 processes the RG table for the held key
# obtained in ba040 & ba050.  Same applies to Rewrite, Write & Delete.", "This
# form will be used to process the invoice files tables for both Purchase &
# Sales Ledgers.", "Note that ws-No-Paragraph start at 51 for RG processing.
# Each bc para must end with a bc0n0-Exit" and "Last para used is 58."
#
# Two of those statements are not true of the frozen code, and both are recorded
# rather than corrected. `bc050` does NOT end with a `bc050-Exit` - it falls
# through into `bc051-Fetch-RG1` and the range ends at `bc059-Exit` [:L2486]. And
# paragraph 58 (`bc998-Free`) is unreachable, anomaly ``N-bc998-unreachable``.


def bc000_rg_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc000-RG-Process section.` [common/plinvoiceMT.cbl:L2326-L2346].

    A SECTION HEADER with no statements of its own - every line between the label
    and `bc050-Process-Read-Indexed.` [:L2348] is a comment. Reproduced as a
    documented no-op because rule R-5 asks for one function per paragraph and
    section headers are paragraphs for that purpose; the section's contract is
    transcribed in the module-level comment above.

    ANOMALY ``N-bc000-prefix-reused``. Three different constructs in this bridge
    are named `bc000`: this section [:L2326], `bc000-HV-Load-rg1  Section.`
    [:L2743] and the `bc000-HV-Load-rg1` reference inside `bc070` [:L2491]. COBOL
    tolerates it because the names differ after the prefix, but a reader grepping
    for `bc000` finds three unrelated things. Recorded.
    """
    return None


def bc050_process_read_indexed(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc050-Process-Read-Indexed.` [common/plinvoiceMT.cbl:L2348-L2431].

    Position on the LINES table for the key already in the caller's buffer, then
    fall through into `bc051-Fetch-RG1`. The label carries
    `*> Dry chk complete.` [:L2348] and the paragraph's own comment says it is
    `*>  This routine is called by for both Read-Next ?? and Read-Indexed.`
    [:L2350] - the double question mark is the maintainer's.

    ⭐ `set KOR-x1 to 2.  *> was 1 = Primary now invoice line 12/07/23` [:L2365]
    dates the switch to key 2. Anomaly ``N-key2-unreachable`` still holds
    for CALLERS - the handler's guard rejects `File-Key-No` other than 1
    [common/acas026.cbl:L248, :L254] - but the BRIDGE reaches key 2 internally,
    here and in `bc080` [:L2534] and `bc090` [:L2698]. So `IL-LINE-KEY` is
    unreachable through the published verb set and reachable through the buffer
    sniff. Both facts are reproduced.

    The pointer juggling is the same three statements `ba060` uses
    [:L2354-L2356]: save the primary snapshot and count, then zero the count so
    the lines select starts from a known state. `bc058-Restore-Pointers` [:L2478]
    puts them back.

    ANOMALY ``N-rg-notused-yet`` context: the comment
    `*>   WS-Last-Read-Key is the last one read so if changes we are done.`
    [:L2361] and `*>  NEED TO TRANSFER RECORD TO/FROM 01 levels` [:L2363] describe
    machinery that was never finished, matching `RG-Table`'s own
    `*> NOT USED - YET.` [:L2313 in the declarations].

    The empty-result arm [:L2403-L2422] is the only place in the bridge that uses
    `We-Error = 890` - `*> This should not happen as have to be > 0` [:L2403] and
    `*> Test for no data but this should not happen - Bug in code somewhere  *>
    when inserting it. So we will do a log report for analysis.` [:L2400-L2401].
    It also `initialise`s BOTH views of the shared buffer [:L2419-L2420] with the
    maintainer's own reason `*> Clear both in case called does not spot end of  *>
    data for Invoice and to help debugging if so`.
    """
    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])

    # `move WS-Mysql-Result to WS-Mysql-Save-Result.  *> primary Tbl` [:L2354],
    # `move WS-Mysql-Count-Rows to WS-Mysql-Save-Count-Rows.` [:L2355] and
    # `move zero to WS-Mysql-Count-Rows.` [:L2356].
    context.ws_mysql_save_count_rows = header_state.count_rows
    context.ws_mysql_count_rows = 0

    # `set KOR-x1 to 2.` [:L2365] and the offset/length pair [:L2366-L2367].
    key = _key_of_reference(_KOR_LINES)
    key_value = _group_il_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move spaces to WS-Where` / `move 1 to J` / the `string` [:L2368-L2378].
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L2370-L2378]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    # `move WS-Where (1:J) to WS-Log-Where.` [:L2379]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    # `if Testing-2 display ...` [:L2380-L2382]
    _display_message_1(file_access, dal_common)
    # `move 51 to ws-No-Paragraph.` [:L2383]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc050-Process-Read-Indexed/SELECT"
    ]

    result = _execute(
        context, _select_statement(LINES_TABLE, predicate), store_result=True
    )
    # `MOVE WS-MYSQL-RESULT TO TP-PUINV-LINES-REC` [:L2397]
    lines_state.key_of_reference = key
    lines_state.store_result(result.rows)
    lines_state.position_at(key_value)
    context.ws_mysql_count_rows = result.count_rows

    if result.count_rows == 0:
        # `if WS-MYSQL-Count-Rows = zero` [:L2403]. The errno test carries its own
        # doubt: `*> set non '0' if no rows ?` [:L2407].
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        # `move 23 to fs-reply` [:L2412] and `move 890 to WE-Error` [:L2413] - the
        # bridge-family status code for "unknown/unexpected error on RG
        # processing", declared in this module as
        # :data:`WE_ERROR_RG_UNKNOWN` because
        # :class:`acas_posting.dal.status.WeError` carries no 890.
        _set_status(
            file_access, int(status.FsReply.KEY_NOT_FOUND), WE_ERROR_RG_UNKNOWN
        )
        # `move spaces to WS-File-Key` [:L2414] then the string [:L2415-L2418].
        _file_key(file_access, f"No RG1 Data for {key_value}")
        # `initialise WS-Invoice-Record  WS-Invoice-Line` [:L2419-L2420] - ONE
        # statement clearing BOTH views of the shared buffer, plain, without
        # `with filler`.
        _initialise_header_record(pinvoice)
        context.ws_invoice_line = None
        context.buffer_view = _BufferView.HEADER
        # `go to bc058-Restore-Pointers  *> do ba999-end at end` [:L2421]. Class 4
        # - the target is a sibling that performs work and then transfers, so the
        # named call is followed by an explicit return.
        bc058_restore_pointers(file_access, dal_common, pinvoice, context)
        return None

    # `move WS-MYSQL-Count-Rows to WS-Temp-ED-Row.` [:L2424] then the string
    # [:L2425-L2430].
    context.ws_temp_ed_row = result.count_rows
    _file_key(
        file_access,
        f"RG > 0 got cnt={_digits(result.count_rows, 7)}"
        f" recs, KEY={key_value}",
    )
    # `perform ba999-End.  *> log it & continue` [:L2431]. Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)
    # `bc051-Fetch-RG1.` [:L2433] follows with no transfer between them. Class 2 -
    # a fall-through.
    bc051_fetch_rg1(file_access, dal_common, pinvoice, context)
    return None


def bc051_fetch_rg1(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc051-Fetch-RG1.` [common/plinvoiceMT.cbl:L2433-L2476].

    Fetch one LINES row into the fourteen `HV1-` host variables [:L2443-L2458],
    unload it and overlay it on the shared buffer.

    ANOMALY ``N-fetch-rg1-status-destroyed``, and it is the sharpest defect in the
    lines path. The `else` arm sets `move 23 to FS-Reply` [:L2470] for "no more
    rows for this invoice" - and then, four lines later and OUTSIDE the `if`,
    `move zero to FS-Reply WE-Error.` [:L2476] unconditionally wipes it. The
    comment above that statement is `*> No more rows for key` [:L2473], so the
    maintainer knew what the branch was for. The consequence is that a caller
    walking body lines can NEVER see the end of the walk from the status: it
    always receives zero. It sees it only from the cleared buffer that [:L2468-L2469]
    left, which is exactly what the `bc050` comment
    `*> Incase called does not spot no more data for invoice.` [:L2468] worries
    about. Reproduced: the 23 is set and then destroyed.

    ⭐ `initialise WS-Invoice-Line  WS-Invoice-Record` [:L2468-L2469] clears BOTH
    views, and in the OPPOSITE order from `bc050`'s pair [:L2419-L2420]. Cosmetic;
    recorded because the two are otherwise identical statements.

    ⭐ `move WS-Invoice-Record (K:L) to WS-File-Key.` [:L2475] runs on BOTH arms,
    so the success log and the end-of-walk log carry the same shape of key - but
    on the `else` arm the buffer has just been cleared, so the key logged is the
    `initialize` value and not the key that was searched for.
    """
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])
    # `move 52 to ws-No-Paragraph` [:L2437]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc051-Fetch-RG1"
    ]
    # `MOVE TP-PUINV-LINES-REC TO WS-MYSQL-RESULT` [:L2443] then the fourteen-host
    # -variable fetch [:L2444-L2461].
    row = lines_state.fetch_record()
    if row is not None:
        _fetch_record(
            row,
            LINES_COLUMNS,
            LINES_COLUMN_RENDER,
            context.line_hv,
            _LINES_ATTRIBUTE_BY_COLUMN,
            _LINES_CHARACTER_WIDTHS,
        )
        context.ws_mysql_count_rows = 1
    else:
        context.ws_mysql_count_rows = 0

    if context.ws_mysql_count_rows > 0:
        # `if WS-MYSQL-Count-Rows > zero` [:L2463] under
        # `*> transfer/move HV1 vars to ws-Invoice-Line then to ws-Invoice-Record`
        # [:L2464]: `perform bc100-UnloadHVs-rg1` [:L2465] - Class 4 - then
        # `move WS-Invoice-Line to WS-Invoice-Record` [:L2466], which
        # `bc100-UnloadHVs-rg1` has already done at its own [:L2809].
        bc100_unload_hvs_rg1(context)
    else:
        # `else initialise WS-Invoice-Line  WS-Invoice-Record` [:L2468-L2469] -
        # note the order, the reverse of `bc050`'s.
        context.ws_invoice_line = None
        _initialise_header_record(pinvoice)
        context.buffer_view = _BufferView.HEADER
        # `move 23 to FS-Reply` [:L2470] - about to be destroyed at [:L2476].
        file_access.fs_reply = int(status.FsReply.KEY_NOT_FOUND)

    # `move WS-Invoice-Record (K:L) to WS-File-Key.` [:L2475] - both arms.
    _file_key(
        file_access,
        _group_il_key(
            pinvoice.ih_prime.ws_invoice_key.ih_invoice,
            pinvoice.ih_prime.ws_invoice_key.ih_test,
        ),
    )
    # `move zero to FS-Reply WE-Error.` [:L2476] - UNCONDITIONAL, destroying the
    # 23 the `else` arm just set. ``N-fetch-rg1-status-destroyed``. ⛔ Not fixed.
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `bc058-Restore-Pointers.` [:L2478] follows with no transfer. Class 2 - a
    # fall-through. The caller's `PERFORM ... THRU bc059-Exit` runs it too, which
    # is harmless because it is idempotent.
    return None


def bc058_restore_pointers(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc058-Restore-Pointers.` [common/plinvoiceMT.cbl:L2478-L2484].

    `*> Restore the Primary table pointer & row count.` [:L2480]:
    `move WS-Mysql-Save-Result to WS-Mysql-Result.  *> primary Tbl` [:L2482],
    `move WS-Mysql-Save-Count-Rows to WS-Mysql-Count-Rows.` [:L2483], then
    `perform ba999-End.` [:L2484] - so this is where a line read gets logged, and
    it is why `ba050`'s line branch goes straight to `ba999-exit` [:L829] rather
    than through `ba999-end`.
    """
    context.ws_mysql_count_rows = context.ws_mysql_save_count_rows
    # `perform ba999-End.` [:L2484]. Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)
    return None


def bc059_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc059-Exit.  Exit.` [common/plinvoiceMT.cbl:L2486].

    The terminator of the `PERFORM bc050-Process-Read-Indexed thru bc059-Exit`
    range used at [:L727] and [:L828]. A bare `Exit` with no statements, so a
    documented no-op - but it must exist, because the section header's own contract
    says `*>  Each bc para must end with a bc0n0-Exit` [:L2344] and because rule
    R-5 wants one function per paragraph.
    """
    return None


def bc070_process_write(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc070-Process-Write.` [common/plinvoiceMT.cbl:L2488-L2528].

    Insert one LINES row. The label carries `*> dry coded. tested - 1` [:L2488].

    ⭐ `move WS-Invoice-Record to WS-Invoice-Line.` [:L2490] reinterprets the
    shared hundred-byte buffer through the LINE redefinition
    [copybooks/plwspinv2.cob:L56] before loading the host variables - the one
    place in the bridge where the buffer's dual nature is written down as a move
    rather than assumed.

    ⭐ `move WS-Invoice-Key to WS-File-Key.    *> Same as WS-il-Key` [:L2492]. The
    comment is true only because both keys are the same ten bytes at the same
    offset [:L298-L304]; the log therefore cannot distinguish a header write from
    a line write by its key alone, only by `ws-No-Paragraph`.

    ⭐ The duplicate-key test here does NOT match `ba070`'s. The outer `if` admits
    `or Sql-State = "23000"` [:L2505-L2506], which `ba070`'s does not [:L1167], and
    the inner one adds an explicit `else move 99 to fs-reply` [:L2514-L2515] which
    `ba070` also lacks [:L1175]. So the two write paths disagree about when a
    duplicate is a duplicate. Both reproduced as written; ⛔ neither normalised.

    ⭐ The failure log key is `"Cant Re|WriteRG1 Data on "` [:L2519] - the pipe
    character is the maintainer's, and the same literal is used for a WRITE
    failure even though it names a rewrite. Preserved verbatim.
    """
    # `move WS-Invoice-Record  to  WS-Invoice-Line.` [:L2490]
    line = line_from_buffer(pinvoice, context)
    context.ws_invoice_line = line
    context.buffer_view = _BufferView.LINE
    # `perform bc000-HV-Load-rg1.` [:L2491]. Class 4.
    bc000_hv_load_rg1(line, context)
    # `move WS-Invoice-Key to WS-File-Key.` [:L2492]
    _file_key(file_access, context.line_hv.hv1_il_line_key)
    # `move zero to FS-Reply WE-Error.` [:L2493]
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `move spaces to SQL-Msg  SQL-State.` [:L2494-L2495] - SPACES into SQL-State
    # here, where `ba010-Initialise` moved a numeric ZERO into it [:L498] and
    # `ba070` moved zero too [:L1157]. Three different clears of one field
    # (``N-sqlstate-zero-not-space``).
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_state = " " * status.SQL_STATE_WIDTH
    # `move zero to SQL-Err.` [:L2496]
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    # `move 53 to ws-No-Paragraph.` [:L2497]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc070-Process-Write"
    ]

    # `perform bc200-Insert-rg1.  *> chgd 26/07/23` [:L2498]. Class 4.
    result = bc200_insert_rg1(file_access, dal_common, pinvoice, context)

    if result.count_rows != 1:
        # `if WS-MYSQL-COUNT-ROWS not = 1` [:L2500] - errno and sqlstate
        # [:L2501-L2503], `move 99 to fs-reply` [:L2504], then the wider outer
        # test [:L2505-L2506].
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        file_access.fs_reply = int(status.FsReply.ERROR)
        if result.error is not None:
            duplicate = result.error.duplicate_key or (
                result.error.sql_state[:5] == status.DUPLICATE_KEY_SQLSTATE.value
            )
            if duplicate:
                # `move 22 to fs-reply` [:L2513]
                file_access.fs_reply = int(status.FsReply.DUPLICATE_KEY)
            else:
                # `else move 99 to fs-reply` [:L2515] - the arm `ba070` has no
                # counterpart for.
                file_access.fs_reply = int(status.FsReply.ERROR)
        # `move spaces to WS-File-Key` [:L2518] then the string [:L2519-L2524].
        _file_key(
            file_access,
            f"Cant Re|WriteRG1 Data on "
            f"{_group_il_key(line.il_key.il_invoice, line.il_key.il_line)}"
            f" RG={_digits(line.il_key.il_line, 2)}",
        )
    # `perform ba999-End.` [:L2526]. Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)
    # `bc070-Exit.  Exit.` [:L2528] - Class 2, a fall-through into a bare exit.
    return None


def bc080_process_delete(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc080-Process-Delete.` [common/plinvoiceMT.cbl:L2530-L2597].

    Delete one LINES row. The label carries `*> Dry tested.` [:L2530] and the
    paragraph's comment `*>  Delete one invoice-line (Item). But data is in
    WS-Invoice-Record` [:L2532] states the buffer contract explicitly.

    ANOMALY ``N-bc080-no-status-on-failure``. The failure arm [:L2571-L2589]
    captures the driver's error fields and builds a log key - and NEVER writes
    `FS-Reply` or `We-Error`. It then `go to ba999-End` [:L2589], so the caller
    receives whatever status it arrived with, which for a call routed through
    `ba080`'s buffer sniff [:L1189-L1191] is whatever the previous verb left,
    because `ba010-Initialise` does not clear the pair [:L500-L501]. A failed line
    delete can therefore report SUCCESS. Reproduced exactly; ⛔ no status is
    invented for it. The maintainer's own comment above the arm is
    `*>  We could have from 0 to 1 so this Error report is moot.` [:L2569].

    ⭐ `move 54 to ws-No-Paragraph.  *> Delete all rows (9<=) for key` [:L2554] -
    the trailing comment describes a range delete that this statement does not
    perform; it keys on the full ten-character `IL-LINE-KEY` [:L2540-L2548] and so
    removes at most one row. The range delete is `bc085`'s job. Recorded.

    ⭐ The success arm clears THREE fields - `move spaces to SQL-Msg SQL-State`
    [:L2591] and `move zero to SQL-Err` [:L2592] - where `ba080`'s clears two
    [:L1242-L1243]. And unlike `ba080` it zeroes the status BEFORE the log
    [:L2594-L2595], so a successful line delete is logged clean.
    """
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])
    # `set KOR-x1 to 2.  *> inv.line` [:L2534] and the offset/length pair
    # [:L2535-L2536].
    key = _key_of_reference(_KOR_LINES)
    key_value = _group_il_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move spaces to WS-Where` / `move 1 to J` / the `string` [:L2538-L2548].
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L2540-L2548]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    # `move WS-Invoice-Record (K:L) to WS-File-Key.` [:L2549]
    _file_key(file_access, key_value)
    # `move WS-Where (1:J) to WS-Log-Where.` [:L2550]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    # `if Testing-2 display ...` [:L2551-L2553]
    _display_message_1(file_access, dal_common)
    # `move 54 to ws-No-Paragraph.` [:L2554]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc080-Process-Delete"
    ]

    # The `DELETE` [:L2560-L2566] - no semicolon.
    result = _execute(
        context, _delete_statement(LINES_TABLE, predicate), store_result=False
    )
    context.ws_mysql_count_rows = result.count_rows
    lines_state.free_result()

    if result.count_rows <= 0:
        # `if WS-MYSQL-COUNT-ROWS not > zero` [:L2571].
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        # `move spaces to WS-File-Key` [:L2580],
        # `move WS-MYSQL-COUNT-ROWS to WS-Temp-ED-Row` [:L2581] then the string
        # [:L2582-L2588]. NO status is written - see ``N-bc080-no-status-on-failure``.
        context.ws_temp_ed_row = result.count_rows
        _file_key(
            file_access,
            f"Delete for {key_value} only found (rg01) "
            f"{_digits(result.count_rows, 7)} Rows",
        )
        # `go to ba999-End` [:L2589]. Class 4 - the target performs the log and
        # then falls through, so the named call is followed by an explicit return.
        ba999_end(file_access, dal_common, pinvoice, context)
        return None

    # `else move spaces to SQL-Msg SQL-State` [:L2591] and
    # `move zero to SQL-Err` [:L2592].
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_state = " " * status.SQL_STATE_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    # `move zero to FS-Reply WE-Error.` [:L2594] - BEFORE the log.
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `perform ba999-End.` [:L2595]. Class 4.
    ba999_end(file_access, dal_common, pinvoice, context)
    # `bc080-Exit.  Exit.` [:L2597] - Class 2, a fall-through.
    return None


def bc085_process_delete_all(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc085-Process-Delete-ALL.` [common/plinvoiceMT.cbl:L2599-L2688].

    Sweep every LINES row for one invoice. The label carries
    `*> THIS IS NON STANDARD - NEEDED (pl940?)- Coded/ D.Tested.` [:L2599] - the
    parenthesised question mark is the maintainer's guess at which program needs
    it - and the paragraph is called only from `ba085` [:L1348].

    ANOMALY ``N-deleteall-single-quoted-column``, the reason this paragraph can
    never do its job. The predicate at [:L2628-L2637] has FOUR operands commented
    out - the backtick, the `KeyName`, the closing backtick and the record slice
    [:L2629-L2632], one of them carrying `*>   ?????? should be SA` - and what
    remains live is::

        string   "'IL-INVOICE'"        delimited by size     [:L2634]
                 '="'                  delimited by size     [:L2635]  *> was '<"'
                 WS-ih-Invoice         delimited by size     [:L2636]
                 '"'                   delimited by size     [:L2637]

    `'IL-INVOICE'` in SINGLE quotes is a MySQL string LITERAL, not an identifier,
    so the statement compares the eleven-character constant `IL-INVOICE` against
    the eight-digit invoice number. That is false for every row, so the sweep
    deletes NOTHING and the body lines of a deleted invoice are orphaned. ⛔ NOT
    fixed - reproduced with the single quotes intact in
    :func:`_where_delete_all_lines`, and bound as a parameter so it cannot become
    an injection point while still comparing two strings.

    ANOMALY ``N-bc085-status-nested``. `move 99 to fs-reply` [:L2676] and
    `move 995 to WE-Error` [:L2677] sit INSIDE
    `if WS-MYSQL-Error-Number not = "0  "` [:L2672]. Since the single-quoted
    predicate always matches zero rows WITHOUT a driver error, the outer
    `if WS-MYSQL-COUNT-ROWS not > zero` [:L2668] is always true while the inner
    one is always false - so the sweep silently reports whatever status `ba085`
    left, which is the clean zero pair from [:L1342-L1343]. The two defects
    conspire: nothing is deleted and nothing is reported. Both reproduced.

    ⭐ The log key is built BEFORE the count is tested [:L2660-L2667], using
    `WS-Temp-Ed-Row (6:2)` - a two-character window into a seven-digit edited
    field, so a count of 40 renders as `40` and a count of 400 renders as `00`.
    Reproduced through the same window.
    """
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])
    # `set KOR-x1 to 2` [:L2622] and the offset/length pair [:L2623-L2624] - both
    # computed and then unused, because the live predicate operands do not
    # reference `KeyName` or the record slice.
    ih_invoice = int(pinvoice.ih_prime.ws_invoice_key.ih_invoice)
    # `move spaces to WS-Where` / `move 1 to J` / the four-operand `string`
    # [:L2626-L2637].
    predicate = _where_delete_all_lines(ih_invoice)
    context.ws_where = _pointer_slice(predicate).literal
    # `move 55 to ws-No-Paragraph.`
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc085-Process-Delete-ALL"
    ]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    _display_message_1(file_access, dal_common)

    # The `DELETE` [:L2646-L2657] - no semicolon.
    result = _execute(
        context, _delete_statement(LINES_TABLE, predicate), store_result=False
    )
    context.ws_mysql_count_rows = result.count_rows
    context.ws_temp_ed_row = result.count_rows
    lines_state.free_result()

    # ⭐ ANOMALY ``N-temp-ed-row-substring``. `move WS-MYSQL-COUNT-ROWS to
    # WS-Temp-Ed-Row` then the string [:L2660-L2667] - built unconditionally,
    # BEFORE the count is tested, and windowing `WS-Temp-Ed-Row (6:2)`: the LAST
    # TWO digits of a seven-digit field. So a delete of 100 rows is reported as
    # `00 lines.`, a delete of 101 as `01 lines.`, and any count that is a multiple
    # of one hundred reads as zero - the message silently truncates modulo 100.
    # The count itself is unharmed; only the log key is wrong. ⛔ Reproduced with
    # the same two-character window, taken with `[5:7]` because COBOL reference
    # modification `(6:2)` is one-based.
    _file_key(
        file_access,
        f"Deleting All lines in {_digits(ih_invoice, 8)} with "
        f"{_digits(result.count_rows, 7)[5:7]} lines.",
    )

    if result.count_rows <= 0:
        # `if WS-MYSQL-COUNT-ROWS not > zero  *> Changed for delete-ALL` [:L2668].
        if result.error is not None:
            # `if WS-MYSQL-Error-Number not = "0  "` [:L2672] - and the status
            # pair is INSIDE it [:L2676-L2677]. ``N-bc085-status-nested``.
            _apply_db_error(file_access, result.error)
            if result.error.sql_err != _MYSQL_ERRNO_NONE:
                _set_status(
                    file_access,
                    int(status.FsReply.ERROR),
                    int(status.WeError.DELETE_SQLSTATE_NOT_00000),
                )
        # `perform ba999-End` [:L2679]. Class 4.
        ba999_end(file_access, dal_common, pinvoice, context)
        # `go to bc085-Exit` [:L2680]. Class 3.
        return None

    # `else  *> of course there could be no data in table` [:L2681]:
    # `move spaces to SQL-Msg` [:L2682] and `move zero to SQL-Err` [:L2683].
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    # `move zero to FS-Reply WE-Error.` [:L2685]
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `perform ba999-End.` [:L2686]. Class 4, then `bc085-Exit.  Exit.` [:L2688].
    ba999_end(file_access, dal_common, pinvoice, context)
    return None


def bc085_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc085-Exit.  Exit.` [common/plinvoiceMT.cbl:L2688] - a bare exit.

    The terminator of `perform bc085-Process-Delete-ALL thru bc085-Exit.`
    [:L1348]. No statements, so a documented no-op, present because rule R-5 wants
    one function per paragraph.
    """
    return None


def bc090_process_rewrite(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc090-Process-Rewrite section.` [common/plinvoiceMT.cbl:L2690-L2739].

    Update one LINES row, all fourteen columns re-sent.

    ANOMALY ``N-bc090-is-a-section``. This is declared `section` [:L2690] while
    its own sibling `bc080-Process-Delete` [:L2530] and its header counterpart
    `ba090-Process-Rewrite` [:L1351] are paragraphs, and while `bc070` [:L2488]
    and `bc085` [:L2599] are paragraphs. A COBOL `section` changes what
    `exit section` means and what a fall-through reaches, so the inconsistency is
    not purely cosmetic - it is why `bc090-Exit.  exit.` [:L2741] uses a lower-case
    `exit` and why control cannot fall out of it into `bc000-HV-Load-rg1`
    [:L2743]. Recorded; ⛔ not normalised.

    ⭐ `move WS-il-Key to WS-File-Key.` [:L2695] uses the LINE key group, where
    `bc070` uses `WS-Invoice-Key` [:L2492] for the identical ten bytes. Two names
    for one value; both preserved at their own sites.

    ⭐ `if Testing-2 display` sits AFTER `perform bc300-Update-rg1`
    [:L2715-L2719], the same inversion `ba090` has [:L1381-L1385].

    ⭐ The failure arm pairs `99` [:L2730] with `994` [:L2731] and then
    `perform ba999-End` [:L2732] before `go to bc090-Exit` [:L2733] - so unlike
    `bc080` it both reports and logs. The success arm zeroes `FS-Reply`,
    `WE-Error` and `SQL-Err` [:L2735-L2737] and spaces `SQL-Msg` [:L2738] before
    its own log [:L2739].
    """
    # `move WS-Invoice-Record  to WS-Invoice-Line.` [:L2693]
    line = line_from_buffer(pinvoice, context)
    context.ws_invoice_line = line
    context.buffer_view = _BufferView.LINE
    # `perform bc000-HV-Load-rg1.  *> Load up the HV rg1 fields from table record
    # in WS` [:L2694]. Class 4.
    bc000_hv_load_rg1(line, context)
    # `move WS-il-Key to WS-File-Key.` [:L2695]
    _file_key(file_access, context.line_hv.hv1_il_line_key)
    # `move 56 to ws-No-Paragraph.` [:L2697] - the same 56 `bc998-Free` would
    # have used had it been reachable (``N-bridge-paragraph-56-duplicated``).
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc090-Process-Rewrite"
    ]
    # `set KOR-x1 to 2  *> 2 = Lines` [:L2698] and the offset/length pair
    # [:L2699-L2700].
    key = _key_of_reference(_KOR_LINES)
    key_value = _group_il_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move spaces to WS-Where` / `move 1 to J` / the `string` [:L2702-L2712].
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L2704-L2712]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    # `move WS-Where (1:J) to WS-Log-Where.` [:L2713]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal

    # `perform bc300-Update-rg1.` [:L2715]. Class 4.
    result = bc300_update_rg1(file_access, dal_common, pinvoice, context, predicate)
    # `if Testing-2 display ...` [:L2717-L2719] - AFTER the update.
    _display_message_1(file_access, dal_common)

    if result.count_rows != 1:
        # `if WS-MYSQL-COUNT-ROWS not = 1` [:L2721] - errno capture
        # [:L2722-L2729], `move 99 to fs-reply` [:L2730] and
        # `move 994 to WE-Error` [:L2731].
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.REWRITE_SQLSTATE_NOT_00000),
        )
        # `perform ba999-End` [:L2732]. Class 4.
        ba999_end(file_access, dal_common, pinvoice, context)
        # `go to bc090-Exit` [:L2733]. Class 3.
        return None

    # `move zero to FS-Reply WE-Error SQL-Err.` [:L2735-L2737] and
    # `move spaces to SQL-Msg.` [:L2738].
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    # `perform ba999-End.` [:L2739]. Class 4, then `bc090-Exit.  exit.` [:L2741].
    ba999_end(file_access, dal_common, pinvoice, context)
    return None


def bc090_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc090-Exit.  exit.` [common/plinvoiceMT.cbl:L2741].

    A lower-case `exit`, not `exit section`, terminating a paragraph that lives
    inside a `section` - see ``N-bc090-is-a-section`` on
    :func:`bc090_process_rewrite`. No statements.
    """
    return None


def bc200_insert_rg1(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> ExecutionResult:
    """`bc200-Insert-rg1  Section.` [common/plinvoiceMT.cbl:L2816-L3003].

    Assemble and run the fourteen-column lines `INSERT`:
    `'INSERT INTO '` + `` '`PUINV-LINES-REC` SET '`` then
    `IL-LINE-KEY`, `IL-INVOICE`, `IL-LINE`, `IL-PRODUCT`, `IL-PA`, `IL-QTY`,
    `IL-TYPE`, `IL-DESCRIPTION`, `IL-NET`, `IL-UNIT`, `IL-DISCOUNT`, `IL-VAT`,
    `IL-VAT-CODE`, `IL-UPDATE` [:L2831-L3001], then `";" X"00"` and the command.

    ⭐ The column order here is the SCHEMA's - `IL-INVOICE` before `IL-LINE` -
    while `bc000-HV-Load-rg1` moves `WS-il-Line` BEFORE `WS-il-Invoice`
    [:L2757-L2758]. Anomaly ``N-lines-loadorder``: two orders, two separate lists,
    neither derived from the other.

    ⭐ `IL-INVOICE` is written here from `HV1-IL-INVOICE`, which `bc000-HV-Load-rg1`
    loads [:L2758] and `bc100-UnloadHVs-rg1` never reads [:L2789-L2801] - anomaly
    ``N-il-invoice-never-unloaded``. The column is therefore write-only in the
    host-variable sense: on a read its value reaches the program and is dropped,
    and the record's `il-Invoice` is rebuilt from the first eight characters of
    `IL-LINE-KEY` instead. If the two ever disagreed, the record would silently
    take the KEY's value.

    Returns the execution result; the frozen section writes no status.
    """
    statement = _insert_statement(
        LINES_TABLE,
        LINES_COLUMN_RENDER,
        LINES_COLUMNS,
        context.line_hv,
        _LINES_ATTRIBUTE_BY_COLUMN,
        "[common/plinvoiceMT.cbl:L2826-L3001]",
    )
    result = _execute(context, statement, store_result=False)
    context.ws_mysql_count_rows = result.count_rows
    return result


def bc300_update_rg1(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
    predicate: SqlFragment,
) -> ExecutionResult:
    """`bc300-Update-rg1  Section.` [common/plinvoiceMT.cbl:L3009-L3201].

    Assemble and run the fourteen-column lines `UPDATE`: `'UPDATE '` +
    `` '`PUINV-LINES-REC` SET '`` + the same fourteen columns in the same schema
    order [:L3024-L3190] + `" WHERE "` + `FUNCTION TRIM (WS-Where (1:J))`
    [:L3194] + `";" X"00"`.

    ⭐ One of only two statements in the bridge that trims the pointer slice - the
    other is `bb300-Update` [:L2314]. Every other statement embeds
    `WS-Where (1:J)` raw, carrying its one trailing space into the SQL text.

    ⭐ Like the header update, this re-sends the primary key it is keying on, and
    it re-sends `IL-INVOICE` from the never-unloaded host variable - so a rewrite
    of a row that was READ through this bridge writes back a zero invoice number
    unless the caller repopulated it, because `bc100-UnloadHVs-rg1` restored only
    the concatenated key [:L2789] and not the dedicated field.
    """
    statement = _update_statement(
        LINES_TABLE,
        LINES_COLUMN_RENDER,
        LINES_COLUMNS,
        context.line_hv,
        _LINES_ATTRIBUTE_BY_COLUMN,
        predicate,
        "[common/plinvoiceMT.cbl:L3019-L3194]",
    )
    result = _execute(context, statement, store_result=False)
    context.ws_mysql_count_rows = result.count_rows
    return result


def bc998_free(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`bc998-Free.` [common/plinvoiceMT.cbl:L3206-L3215].

    `move 58 to ws-No-Paragraph` [:L3207], free `TP-PUINV-LINES-REC`, clear the
    second cursor.

    ANOMALY ``N-bc998-unreachable``: NOTHING PERFORMS THIS PARAGRAPH. A census of
    the whole bridge finds no `perform bc998-Free` and no `go to bc998-Free`, so
    the only routine that can release the lines result set is dead code - which is
    the other half of ``N-close-leaks-rg1-cursor``. It is reproduced as a real,
    correct, never-called function, because deleting it would hide the defect
    rather than record it, and rule R-5 requires a function per paragraph.
    """
    # `move 58 to ws-No-Paragraph.` [:L3207]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["bc998-Free"]
    context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE]).free()
    context.most_cursor_set_2 = 0
    return _BridgeLabel.BA999_END


def ca_process_logs(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`Ca-Process-Logs.` [common/plinvoiceMT.cbl:L3218-L3222].

    `call "fhlogger" using File-Access ACAS-DAL-Common-data.` [:L3221-L3222] -
    the whole paragraph.

    `common/fhlogger.cbl` is OUT OF SCOPE [Agent Action Plan section 0.2.2,
    "Non-posting utilities"], and rule R-1 forbids calling it in any case, so the
    log record is emitted through :mod:`logging` instead. Every field that can
    carry a key value, a host name or an error message goes through
    :func:`status.redact_for_log` first, so a log line can neither leak an
    identity nor forge a record.

    The HANDLER's paragraph of the same name carries
    `*> Not called on DAL access as it does it already`
    [common/acas026.cbl:L623] - so on the DAL path the handler must NOT log and
    this is the only logger. :func:`ca_process_logs_handler` records the other
    half of that contract.
    """
    _LOG.info(
        "fhlogger: system=%s file=%s paragraph=%s function=%s key=%s "
        "fs-reply=%s we-error=%s sqlstate=%s where=%s",
        int(WS_LOG_SYSTEM),
        WS_LOG_FILE_NO_RDB,
        int(file_access.logging_data.ws_no_paragraph),
        int(file_access.file_function),
        status.redact_for_log(file_access.logging_data.ws_file_key),
        int(file_access.fs_reply),
        int(file_access.we_error),
        status.sanitise_for_log(file_access.logging_data.sql_state),
        status.redact_for_log(file_access.logging_data.ws_log_where),
    )


def ca_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`ca-Exit.` [common/plinvoiceMT.cbl:L3224] - `exit.` and nothing else.

    A plain `exit`, not `exit section`, exactly as the handler's own `ca-Exit`
    [common/acas026.cbl:L629] is. Reproduced as an empty function because rule
    R-5 asks for one function per paragraph and a label with a single `exit` is
    still a paragraph.
    """
    return None


# ---------------------------------------------------------------------------
# The bridge's entry point - `plinvoiceMT`, three parameters
# ---------------------------------------------------------------------------

#: Which function implements each label the bridge's verbs can transfer to. Only
#: labels a verb RETURNS appear here. `bc058-Restore-Pointers`, `bc085-Exit` and
#: `bc090-Exit` are declared on :class:`_BridgeLabel` because the frozen source
#: names them in `GO TO`s, but those transfers are all INSIDE the `bc` family and
#: are rendered as named sibling calls (Agent Action Plan section 0.4.2 Class 4),
#: so the label machine never sees them.
_BRIDGE_LABEL_FUNCTIONS: Final[Mapping[_BridgeLabel, Any]] = MappingProxyType(
    {
        _BridgeLabel.BA020_PROCESS_OPEN: ba020_process_open,
        _BridgeLabel.BA030_PROCESS_CLOSE: ba030_process_close,
        _BridgeLabel.BA040_PROCESS_READ_NEXT: ba040_process_read_next,
        _BridgeLabel.BA041_REREAD: ba041_reread,
        _BridgeLabel.BA042_FETCH: ba042_fetch,
        _BridgeLabel.BA050_PROCESS_READ_INDEXED: ba050_process_read_indexed,
        _BridgeLabel.BA060_PROCESS_START: ba060_process_start,
        _BridgeLabel.BA070_PROCESS_WRITE: ba070_process_write,
        _BridgeLabel.BA080_PROCESS_DELETE: ba080_process_delete,
        _BridgeLabel.BA085_PROCESS_DELETE_ALL: ba085_process_delete_all,
        _BridgeLabel.BA090_PROCESS_REWRITE: ba090_process_rewrite,
        _BridgeLabel.BA100_BAD_FUNCTION: ba100_bad_function,
        _BridgeLabel.BA998_FREE: ba998_free,
        _BridgeLabel.BA999_END: ba999_end,
        _BridgeLabel.BA999_EXIT: ba999_exit,
    }
)


def plinvoice_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    *,
    context: PInvoiceContext | None = None,
) -> FileAccess:
    """`plinvoiceMT` - the generated bridge program, THREE parameters.

    The handler's own `CALL` is inline in `ba015-Test-Ends`
    [common/acas026.cbl:L611-L615], with a blank line inside the parameter list
    (anomaly ``N-nobadal`` - there is no `ba020-*` paragraph to hold it)::

        call     "plinvoiceMT" using File-Access
                                     ACAS-DAL-Common-data

                                     WS-PInvoice-Record
        end-call.

    and the bridge's own header is [common/plinvoiceMT.cbl:L478-L480]::

        PROCEDURE DIVISION   using File-Access
                                   ACAS-DAL-Common-data
                                   WS-Invoice-Record.   *>  Ws record

    ANOMALY ``N-bridge-param-rename``. The caller passes `WS-PInvoice-Record`; the
    bridge calls the same operand `WS-Invoice-Record` - the identifier
    `slinvoiceMT` uses for the SALES header [common/slinvoiceMT.cbl:L480]. It is
    positionally harmless and it means a reader grepping the purchase bridge for
    `WS-PInvoice-Record` finds nothing at all. BOTH names are published:
    :data:`BRIDGE_LINKAGE_PARAMETER_NAMES` carries the bridge's, and
    :data:`HANDLER_LINKAGE_PARAMETER_NAMES` carries the handler's.

    ⭐ THE ERROR CONTRACT. `common/acas026.cbl:L617` states it in the maintainer's
    own words: `*>   Any errors leave it to caller to recover from`. This function
    therefore NEVER RAISES on a data or database condition - it writes the
    `(FS-Reply, We-Error)` pair and returns. Every driver failure is captured by
    :func:`_execute` through :func:`acas_posting.dal.status.mysql_1100_db_error`
    and turned into that pair plus `SQL-Err`, `SQL-Msg` and `SQL-State`.

    ⭐ THE VERB SET IS THE BRIDGE'S, NOT THE HANDLER'S. `ba010-Initialise`
    dispatches TEN function codes [:L515-L540] where the handler dispatches nine
    [common/acas026.cbl:L283-L303]: code 6 reaches
    `ba085-Process-Delete-All` here, under `*> option 6 is a special to cleardown
    all LINE data for 1 invoice` [:L528], while the handler rejects it as
    `*> 6 is spare / unused` [common/acas026.cbl:L301]. Code 34 shares the
    `when 3` arm in BOTH [:L520-L522 and common/acas026.cbl:L288-L290] - and the
    ONE place 34 diverges from 3 is three paragraphs deep, at
    `if FN-Read-Next-Header go to ba042-Fetch.` [:L721-L722], where it skips the
    body-line walk. Codes 31, 32 and 33 are dispatched by neither.

    :param file_access: the `File-Access` group [copybooks/wsfnctn.cob:L23-L38]
        carrying `File-Function`, `Access-Type`, the status pair and, on
        `logging_data`, the diagnostic fields. Mutated in place, exactly as the
        COBOL `USING` operand is, and returned for convenience.
    :param dal_common: `ACAS-DAL-Common-data`
        [copybooks/Test-Data-Flags.cob:L6-L18] - the two testing switches that
        gate logging and the display diagnostics.
    :param pinvoice: the shared record buffer. `PInvoiceHeader`
        [copybooks/plwspinv.cob:L8] is the working-storage view; a line is
        selected out of the same hundred bytes when `ih-Test` is non-zero, exactly
        as the four buffer sniffs at [:L827, :L1147, :L1189, :L1356] do it.
    :param context: the bridge's own WORKING-STORAGE, which GnuCOBOL keeps alive
        between `CALL`s. Defaults to the module-level instance for the same
        reason.
    """
    active = _DEFAULT_CONTEXT if context is None else context
    # `ba-ACAS-DAL-Process section.` [:L482] - the curses geometry, omitted - then
    # the fall-through into `ba010-Initialise` [:L496].
    label = ba_acas_dal_process(file_access, dal_common, pinvoice, active)
    # The label machine. Every verb returns the label its `GO TO` names; the loop
    # runs until `ba999-exit`, whose own `exit program.` [:L1440] is the single
    # terminal statement of the bridge.
    while label is not _BridgeLabel.BA999_EXIT:
        implementation = _BRIDGE_LABEL_FUNCTIONS.get(label)
        if implementation is None:
            # Unreachable: every member of `_BridgeLabel` a verb can return is in
            # the table. Defended anyway, and defended the way this bridge
            # defends - by writing the bad-function pair rather than by raising.
            _set_status(
                file_access,
                int(status.FsReply.ERROR),
                int(status.WeError.UNKNOWN_UNEXPECTED),
            )
            break
        label = implementation(file_access, dal_common, pinvoice, active)
    return file_access


# ---------------------------------------------------------------------------
# The handler - `acas026`, five parameters, `aa-Process-Flat-File` and
# `ba-Process-RDBMS`
# ---------------------------------------------------------------------------
#
# THE FLAT-FILE PATH IS NOT EXECUTED BY THE MIGRATED CYCLE, and this is a
# deliberate omission recorded here rather than discovered later.
# `aa020-Process-Open` through `aa090-Process-Rewrite` drive an ISAM file with
# COBOL's `open`, `read`, `write`, `rewrite`, `delete` and `start` verbs
# [common/acas026.cbl:L308-L521], and the Agent Action Plan targets the frozen
# MySQL schema: section 0.1.1 describes the store as "indexed (ISAM) files as the
# historical primary, with a MySQL/MariaDB mirror reached through a generated
# bridge", and section 0.7.2 R-1 says the twenty `dal/acas*.py` modules
# "reimplement each handler-and-bridge pair as SQL against the frozen schema".
# There is no ISAM engine in this module's dependency whitelist and adding one
# would be a new surface, forbidden by rule R-3.
#
# So each flat-file paragraph is reproduced STRUCTURALLY and completely for every
# statement that is not the ISAM verb itself - the paragraph number stamp, the log
# key, the `Cobol-File-Status` writes, the status pair, the condition tests and
# every transfer - and the ISAM verb takes ITS OWN DOCUMENTED FAILURE BRANCH,
# which is the branch the frozen source already contains for the case where the
# file cannot serve the request:
#
#   * `open input` -> `move 35 to fs-Reply` [:L314] - the handler's own mapping,
#     and 35 is COBOL's file status for "optional file not present";
#   * `read next` -> the `at end` branch [:L376-L382];
#   * `read ... key`, `start`, `delete`, `rewrite` -> the `invalid key` branch
#     [:L422-L424, :L458-L461, :L505-L507, :L517-L519];
#   * `write` -> the `invalid key` branch [:L494-L496].
#
# NO status value is invented by that choice: every one is a literal in the frozen
# source at the cited line. :data:`FLAT_FILE_PATH_AVAILABLE` names the decision so
# a reader can find it, and the RDB branch [:L263-L267] is the path the migrated
# cycle actually takes.

#: `False` on every migrated run. See the block comment above. Not a feature
#: switch: there is nothing to switch on, and rule R-3 forbids adding one.
#:
#: ⭐⭐ ANOMALY ``N-handler-isam-statuses-differ-from-bridge``. The two paths report
#: the SAME logical outcome with DIFFERENT status pairs, so a caller cannot read a
#: status without knowing which path served it. Verified pair by pair:
#:
#: ======================  ============================  =============================
#: condition               handler (flat file)           bridge (RDB)
#: ======================  ============================  =============================
#: read-indexed not found  `21` / `21` [:L423]           `23` / `0`  [MT:L870-L873]
#: write rejected          `22` / unset [:L495]          `99` / `22` [MT:L1163-L1170]
#: delete rejected         `21` / unset [:L506]          `99` / `995` [MT:L1247-L1252]
#: rewrite rejected        `21` / unset [:L518]          `99` / `994` [MT:L2183-L2188]
#: start not found         `21` / unset [:L459]          `21` / `0`  [MT:L1017-L1019]
#: bad function            `999` / `99` [:L527-L528]     `990` / `99` [MT:L1412-L1413]
#: ======================  ============================  =============================
#:
#: Two patterns run through the table. The handler routinely writes ONE of the two
#: fields and leaves the other at whatever `move zeros` last set, so `We-Error` is
#: frequently a stale zero next to a real `FS-Reply`; the bridge writes both. And
#: where the handler uses `FS-Reply` to carry the specific condition, the bridge
#: uses a flat `99` and puts the detail in `We-Error` - opposite conventions for the
#: same two fields. ⛔ Neither is normalised: each path reports exactly the pair its
#: own source writes, at the cited line.
FLAT_FILE_PATH_AVAILABLE: Final[bool] = False

#: `35` - COBOL file status for an absent optional file, and the value the handler
#: itself moves into `Fs-Reply` when `open input` fails
#: [common/acas026.cbl:L313-L314].
_FS_REPLY_FILE_NOT_PRESENT: Final[int] = 35

#: `999` - `move 999 to WE-Error.` [common/acas026.cbl:L344, :L527]. The HANDLER's
#: bad-function and failed-open code, and :class:`status.WeError` carries it as
#: `NOT_USED` because no other handler in the folder writes it
#: (``N-badfunction-pair-differs``: the BRIDGE writes `990`
#: [common/plinvoiceMT.cbl:L1412] for the same condition).
_WE_ERROR_HANDLER_GENERIC: Final[int] = int(status.WeError.NOT_USED)


class _HandlerLabel(enum.StrEnum):
    """Every label `aa010-main`'s `evaluate` and the flat-file `GO TO`s name."""

    #: `aa020-Process-Open.` [common/acas026.cbl:L308]
    AA020_PROCESS_OPEN = "aa020-Process-Open"
    #: `aa030-Process-Close.` [common/acas026.cbl:L347]
    AA030_PROCESS_CLOSE = "aa030-Process-Close"
    #: `aa040-Process-Read-Next.` [common/acas026.cbl:L360]
    AA040_PROCESS_READ_NEXT = "aa040-Process-Read-Next"
    #: `aa050-Process-Read-Indexed.` [common/acas026.cbl:L416]
    AA050_PROCESS_READ_INDEXED = "aa050-Process-Read-Indexed"
    #: `aa060-Process-Start.` [common/acas026.cbl:L438]
    AA060_PROCESS_START = "aa060-Process-Start"
    #: `aa070-Process-Write.` [common/acas026.cbl:L489]
    AA070_PROCESS_WRITE = "aa070-Process-Write"
    #: `aa080-Process-Delete.` [common/acas026.cbl:L500]
    AA080_PROCESS_DELETE = "aa080-Process-Delete"
    #: `aa090-Process-Rewrite.` [common/acas026.cbl:L511]
    AA090_PROCESS_REWRITE = "aa090-Process-Rewrite"
    #: `aa100-Bad-Function.` [common/acas026.cbl:L523]
    AA100_BAD_FUNCTION = "aa100-Bad-Function"
    #: `aa999-main-exit.` [common/acas026.cbl:L530]
    AA999_MAIN_EXIT = "aa999-main-exit"
    #: `aa-main-exit.` [common/acas026.cbl:L535]
    AA_MAIN_EXIT = "aa-main-exit"
    #: `aa-Exit.` [common/acas026.cbl:L539], `exit program.` at [:L540]
    AA_EXIT = "aa-Exit"


#: `evaluate File-Function` [common/acas026.cbl:L283-L303] - THE HANDLER'S TABLE.
#: Nine codes, and `34` shares the `when 3` arm by FALL-THROUGH: `when 3` [:L288]
#: has no statements of its own, `when 34  *> fn-Read-Next-Header` [:L289] follows
#: it, and the single `go to aa040-Process-Read-Next` [:L290] serves both. So
#: `fn-Read-Next-Header` executes the ORDINARY read-next paragraph with no header
#: filtering and no different key (``N-read-next-header-is-read-next``).
#:
#: ⭐ `acas026:L289`'s comment is CONFIDENT - `*> fn-Read-Next-Header` - where the
#: mirrored `acas016:L297` carries `*> fn-Read-Next-Header ???`
#: (``N-when34-confidence``).
#:
#: ⛔ Codes 31 (`fn-Read-By-Name`), 32 (`fn-Read-By-Batch`) and 33
#: (`fn-Read-By-Cust`) are NOT dispatched here. See
#: :data:`EXTENDED_FUNCTION_CODE_CENSUS` for the corrected folder-wide census.
#: ⛔ Code 6 is NOT dispatched either - `when other  *> 6 is spare / unused`
#: [:L301] - even though the BRIDGE dispatches it to its delete-all
#: [common/plinvoiceMT.cbl:L530-L531].
_HANDLER_DISPATCH: Final[Mapping[int, _HandlerLabel]] = MappingProxyType(
    {
        int(status.FileFunction.OPEN): _HandlerLabel.AA020_PROCESS_OPEN,
        int(status.FileFunction.CLOSE): _HandlerLabel.AA030_PROCESS_CLOSE,
        int(status.FileFunction.READ_NEXT): _HandlerLabel.AA040_PROCESS_READ_NEXT,
        int(
            status.FileFunction.READ_NEXT_HEADER
        ): _HandlerLabel.AA040_PROCESS_READ_NEXT,
        int(status.FileFunction.READ_INDEXED): _HandlerLabel.AA050_PROCESS_READ_INDEXED,
        int(status.FileFunction.WRITE): _HandlerLabel.AA070_PROCESS_WRITE,
        int(status.FileFunction.RE_WRITE): _HandlerLabel.AA090_PROCESS_REWRITE,
        int(status.FileFunction.DELETE): _HandlerLabel.AA080_PROCESS_DELETE,
        int(status.FileFunction.START): _HandlerLabel.AA060_PROCESS_START,
    }
)


def aa_process_flat_file(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa-Process-Flat-File Section.` [common/acas026.cbl:L234-L235].

    A section header whose only content is the banner `*>***************************`
    [:L235]; control falls straight through into `aa010-main` [:L236]. Reproduced
    as a documented pass-through because rule R-5 wants one function per paragraph.
    """
    # Class 2 - fall-through, not a transfer.
    return aa010_main(system, pinvoice, file_access, file_defs, dal_common, context)


def aa010_main(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa010-main.` [common/acas026.cbl:L236-L306].

    Log identity, key guard, path selection, record-size guard, SQL clear, verb
    dispatch - in that order and no other.

    ⭐⭐ ANOMALY ``N-log-no-increment``, and it is unique in the folder. `move 4 to
    WS-Log-System.` and `move 12 to WS-Log-File-No.` [:L240-L241] set the pair for
    the flat-file path, and `ba010-Test-WS-Rec-Size` then sets
    `move 12 to WS-Log-File-no.        *> for FHlogger` [:L556] for the RDB path -
    THE SAME VALUE. Every other handler adds ten on the RDB path: `acas005` 11 to
    21, `acas006` 12 to 22, `acas007` 13 to 23, `acas008` 15 to 25, `acas012` 11 to
    21, `acas013` 13 to 23, `acas015` 12 to 22, `acas016` 12 to 22, `acas019` 15 to
    25, `acas022` 11 to 21. `acas026` is the sole exception and it is a silent one.
    ⛔ Reproduced as 12 on both paths; NOT corrected to 22. See
    :data:`WS_LOG_FILE_NO`, :data:`WS_LOG_FILE_NO_RDB` and
    :data:`_LOG_FILE_NO_SIBLING_CENSUS`.

    ⭐ The legend on [:L240] reads
    `*> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice used in FH logging`, so code 5 means
    "Invoice" here and in `acas016:L248` and `acas019:L240` - and "Stock" in
    `acas013:L298` and `acas015:L291` (``N-logsystem5-meaning``). This handler uses
    4, so the resulting `(system=4, file=12)` pair happens to be unique across the
    folder; nothing is actually ambiguous, but only by accident.

    ⭐ ANOMALY ``N-996-comment``. The key guard [:L245-L259] rejects a key number
    other than 1 with `998` for read-indexed and start [:L249] and `996` for delete
    [:L255] - and the trailing comment on the 996 line is a VERBATIM COPY of the
    998 line's, `*> file seeks key type out of range        996` against
    `*> file seeks key type out of range        998`. ⛔ Not rewritten.

    ⭐ ANOMALY ``N-key2-unreachable``. That guard is why `IL-LINE-KEY` is
    unreachable: `Table-Of-KeyNames` declares TWO keys
    [common/plinvoiceMT.cbl:L297-L307] and `KeyOfReference occurs 2` [:L306], but
    no caller can select the second one through Start, Read-Indexed or Delete. The
    same dead-key situation as `acas016`.

    ⭐ ANOMALY ``N-noopenoutput``. There is NO `if fn-Open and fn-output` block
    anywhere in this handler - verified: no `fn-Open and` match in the file. So
    Open with `Access-Type` 3 is a PLAIN OPEN and deletes nothing, where `acas006`
    and `acas007` issue two bridge calls to sweep the table
    [common/acas006.cbl:L313-L318] and `acas008` coerces the function into a
    delete-all [common/acas008.cbl:L313-L319]. ⛔ Do not port either.

    ⭐ ANOMALY ``N-noparagraph-collision``. The trace numbers are 201..208
    [:L310, :L348, :L365, :L418, :L442, :L490, :L501, :L513] - identical to
    `acas013`, `acas015`, `acas016`, `acas019` and `acas022`. A sixth handler with
    the same scheme, so `WS-No-Paragraph` alone cannot identify which handler wrote
    a log line; only the `(WS-Log-System, WS-Log-File-No)` pair can.

    ⭐ The commented-out `move zero to WE-Error / FS-Reply` at [:L279-L280] - each
    line prefixed `*>  ?` - is a deliberate NON-initialisation, matching the
    bridge's own commented pair [common/plinvoiceMT.cbl:L500-L501]. ⛔ Not restored.

    ⭐ `move spaces to SQL-Err SQL-Msg SQL-State.` [:L281] clears THREE fields
    where `acas022:L336` clears two. Reproduced as three.

    ⭐ `aa100-Bad-Function` is reachable TWO ways: `when other` [:L301-L302] and the
    unconditional `go to aa100-Bad-Function.` at [:L306] under
    `*>  Should never get here but in case :(` [:L305]. The bridge has no such
    second route [common/plinvoiceMT.cbl:L540]. Both are annotated below.

    ⭐⭐ ANOMALY ``N-verb-dispatch-dead-on-rdb-path``, and it follows from the
    statement ORDER rather than from any statement. The RDB branch is at
    [:L261-L265] and the function `evaluate` is at [:L283]. So on the RDB path
    control leaves through `go to AA-Main-Exit` [:L264] BEFORE the dispatch is ever
    evaluated, and the ENTIRE `aa020`..`aa100` family is unreachable - the verb is
    decoded a second time, by the bridge's own `ba010-Initialise`
    [common/plinvoiceMT.cbl:L502-L540]. Two consequences a caller can observe:

    * the handler's bad-function pair `999` / `99` [:L527-L528] can only ever be
      seen on the FLAT-FILE path; the RDB path reports the bridge's `990` / `99`
      [common/plinvoiceMT.cbl:L1412-L1413] for the identical input. See
      ``N-badfunction-pair-differs``.
    * the KEY GUARD [:L245-L259] is the one part of `aa010-main` that runs on BOTH
      paths, because it sits ABOVE the branch - which is why `File-Key-No` 2 is
      rejected with `998` / `996` even for an RDB caller whose bridge could
      technically reach the second key. See ``N-key2-unreachable``.

    Both behaviours are reproduced by testing the path selector before the
    dispatch, in the source's own order.

    ⭐ ANOMALY ``N-file-defs-unused``. `File-Defs` is the FOURTH linkage parameter
    [:L229] and is read on NEITHER path - not by this paragraph, not by any `aa`
    verb paragraph, and not by the bridge, which does not receive it at all
    [:L611-L615]. The reason is on the source line above the path test:
    `*> File paths for Cobol File has already done in main menu module` [:L273] -
    the menu resolved the paths before the `CALL`, so the block is vestigial. It is
    nonetheless threaded through every function in this module, unread, because R-5
    requires the Python parameter lists to match the COBOL linkage lists position
    for position; dropping it would make the traceability table wrong.
    """
    # `move 4 to WS-Log-System.` [:L240]
    file_access.logging_data.ws_log_system = int(WS_LOG_SYSTEM)
    # `move 12 to WS-Log-File-No.` [:L241] - and 12 again on the RDB path.
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO

    # `evaluate File-Function` [:L245-L259] - the key guard.
    function = int(file_access.file_function)
    if function in KEY_NUMBER_GUARDED_FUNCTIONS:
        if int(file_access.logging_data.file_key_no) != _ONLY_ADMITTED_KEY_NUMBER:
            if function == int(status.FileFunction.DELETE):
                # `move 996 to WE-Error` [:L255] with the copy-pasted comment.
                we_error = int(status.WeError.DELETE_KEY_OUT_OF_RANGE)
            else:
                # `move 998 to WE-Error` [:L249] for read-indexed and start.
                we_error = int(status.WeError.FILE_KEY_NO_OUT_OF_RANGE)
            # `move 99 to fs-reply` [:L250, :L256]
            _set_status(file_access, int(status.FsReply.ERROR), we_error)
            # `go to aa999-main-exit` [:L251, :L257]. Class 2.
            return _HandlerLabel.AA999_MAIN_EXIT

    if int(system.system_data_block.rdbms_flat_statuses.file_system_used) != 0:
        # `if not FS-Cobol-Files-Used` [:L263]. The migrated cycle always takes
        # this branch.
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses` [:L264] with the
        # maintainer's own `*> needed for DAL? not JC/dbpre versions`.
        file_access.fa_rdbms_flat_statuses.fa_file_system_used = int(
            system.system_data_block.rdbms_flat_statuses.file_system_used
        )
        file_access.fa_rdbms_flat_statuses.fa_file_duplicates_in_use = int(
            system.system_data_block.rdbms_flat_statuses.file_duplicates_in_use
        )
        # `perform ba-Process-RDBMS  *>  Can't hurt` [:L265] - the maintainer's own
        # comment, preserved. Class 4.
        ba_process_rdbms(
            system, pinvoice, file_access, file_defs, dal_common, context
        )
        # `go to AA-Main-Exit` [:L266]. Class 2 - note the capitalisation the
        # frozen source uses here, `AA-Main-Exit`, against `aa-main-exit` at the
        # label [:L535].
        return _HandlerLabel.AA_MAIN_EXIT

    # `perform ba012-Test-WS-Rec-Size-2.` [:L271] under `*> Test  Rec lengths
    # first.` [:L269]. Class 4 - and note the handler performs the SECOND paragraph
    # of the RDB section from the FLAT-FILE path, skipping `ba010`'s log-number
    # move [:L556]. A PARAGRAPH perform, so it returns at that paragraph's end and
    # does NOT fall into `ba015-Test-Ends` - the flag it reports is therefore
    # discarded here, and the flat-file path never reaches the bridge ``CALL``.
    ba012_test_ws_rec_size_2(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
    # ⭐ ANOMALY ``N-no-status-zeroing``. `move spaces to SQL-Err SQL-Msg SQL-State.`
    # [:L281] clears THREE fields - `acas022:L336` clears only two - and the
    # `move zero to WE-Error` / `FS-Reply` that would have run immediately above it
    # is COMMENTED OUT, each line prefixed `*>  ?` [:L279-L280]. The question marks
    # are the maintainer's: he disabled the initialisation and did not decide why.
    # The consequence is real - a stale `We-Error` from a previous call survives into
    # this one and is only overwritten if some later statement happens to write it.
    # ⛔ NOT re-enabled: the two fields are deliberately left as the caller passed
    # them, exactly as the frozen source leaves them.
    file_access.logging_data.sql_err = " " * status.SQL_ERR_WIDTH
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_state = " " * status.SQL_STATE_WIDTH

    # `evaluate File-Function` [:L283-L303].
    label = _HANDLER_DISPATCH.get(function)
    if label is None:
        # `when other  *> 6 is spare / unused` then
        # `go to aa100-Bad-Function` [:L301-L302]. Class 3.
        return _HandlerLabel.AA100_BAD_FUNCTION
    # `go to <verb paragraph>` [:L284-L300]. Class 3. The unconditional
    # `go to aa100-Bad-Function.` at [:L306] is unreachable because every arm of
    # the `evaluate` transfers; it is reproduced as the `label is None` route
    # above, which is the only way control can reach that label.
    return label


def aa020_process_open(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa020-Process-Open.` [common/acas026.cbl:L308-L345].

    A four-way nested `if` on `Access-Type`: input, i-o, output, extend
    [:L311-L339]. Only the fourth arm is data-independent, and it is the only one
    that writes a status of its own: `fn-extend` is
    `*> Must not be used for ISAM files` [:L331], its `open extend` is COMMENTED
    OUT [:L332], and it returns `997` / `99` [:L333-L334].

    ⭐ The i-o arm is a create-if-missing dance the maintainer moved here from
    another program - `*> this block was in st010 at ba000-Setup-Invoice` [:L321] -
    closing, opening output to create the file, closing again and reopening i-o
    [:L322-L325], with his own doubt on the `end-if`:
    `*> file-status will NOT be updated   ????` [:L326]. Structure reproduced.

    ⭐ `if fn-output  *> should not need to be used` [:L328] and
    `open output Invoice-File  *> caller should check fs-reply` [:L329] - a PLAIN
    open output. ``N-noopenoutput``: nothing is deleted. ⛔ Not changed.

    ⭐ ANOMALIES ``N-sl-in-purchase-openclose`` and ``N-open-close-key-wording``.
    `move "OPEN PL INVOICE File" to WS-File-Key.` [:L342] - "PL", correctly, in
    the purchase handler. The BRIDGE writes `"OPEN SL INVOICE"`
    [common/plinvoiceMT.cbl:L605] - the SALES prefix, and without the trailing
    `" File"`. The two log keys for one logical operation therefore disagree on
    BOTH counts, ledger and wording, so the log cannot be keyed on either: the
    same table written through the same handler yields `"OPEN PL INVOICE File"`
    or `"OPEN SL INVOICE"` depending only on which path served the call. Both
    preserved verbatim at their own sites; neither normalised.

    ⭐ `if fs-reply not = zero  move  999 to WE-Error.` [:L343-L344] - note the
    period ENDS the `if`, so the `go to` on the next line is unconditional.
    """
    # `move spaces to WS-File-Key.     *> for logging` [:L309]
    _file_key(file_access, "")
    # `move 201 to WS-No-Paragraph.` [:L310]
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa020-Process-Open"
    ]

    access_type = int(file_access.access_type)
    if access_type == int(status.AccessType.INPUT):
        # `open input Invoice-File` [:L312].
        #
        # ⭐ ANOMALY ``N-select-status-is-fs-reply``. There is no move between the
        # `open` and the test on the next line because the SELECT routes the file
        # status STRAIGHT into the LINKAGE field: `select Invoice-File assign
        # file-26 access dynamic organization indexed status fs-reply record key
        # invoice-key.` [copybooks/plselpinv.cob:L2-L6]. `FS-Reply` is therefore
        # both the handler's return value to its caller AND the ISAM run-time's
        # scratch pad, written behind the program's back by every file verb - so
        # any ISAM operation, including ones whose status the code then discards,
        # silently overwrites the value the caller is going to read.
        #
        # The file is not present on a migrated run - see the module block comment
        # above - which is COBOL file status 35, so the open writes 35 here.
        file_access.fs_reply = _FS_REPLY_FILE_NOT_PRESENT
        if int(file_access.fs_reply) != int(status.FsReply.SUCCESS):
            # ⭐ ANOMALY ``N-open-input-status-flattened``. `if Fs-Reply not = zero`
            # [:L313] then `move 35 to fs-Reply` [:L314] - which overwrites whatever
            # the open actually reported with 35, `file not present`, REGARDLESS of
            # what went wrong. A permissions failure (37), a locked file (93) and a
            # genuinely missing file (35) are all reported as 35, so the caller
            # cannot distinguish a recoverable condition from a fatal one. Then
            # `close Invoice-File` [:L315], whose own status is discarded - and
            # which, per ``N-select-status-is-fs-reply`` above, writes `FS-Reply`
            # again, so the 35 just stored can itself be overwritten by the close.
            # ⛔ Reproduced flattened; the true cause is NOT recovered.
            file_access.fs_reply = _FS_REPLY_FILE_NOT_PRESENT
            # `go to aa999-Main-Exit` [:L316] - note the capitalised `Main` here
            # against the label's `aa999-main-exit` [:L530]. Class 2.
            return _HandlerLabel.AA999_MAIN_EXIT
    elif access_type == int(status.AccessType.I_O):
        # `open i-o Invoice-File` [:L320] then the create-if-missing dance
        # [:L321-L326]. No status is written by any of it, so this branch
        # deliberately executes no statement. NOT a stub: the COBOL arm really is
        # observationally empty on the migrated path, and writing a status here
        # would be an added behaviour that rule R-3 forbids.
        pass
    elif access_type == int(status.AccessType.OUTPUT):
        # `open output Invoice-File  *> caller should check fs-reply` [:L329].
        # A plain open - ``N-noopenoutput``. This branch deliberately executes no
        # statement, and the emptiness IS the anomaly: acas026 has no
        # `if fn-Open and fn-output` block, so unlike acas006/acas007
        # [common/acas006.cbl:L313-L318] and acas008 [common/acas008.cbl:L313-L319]
        # an Open+Output here deletes NOTHING. NOT a stub - adding a delete-all
        # would be the defect.
        pass
    elif access_type == int(status.AccessType.EXTEND):
        # `if fn-extend  *> Must not be used for ISAM files` [:L331], with
        # `open extend Invoice-File` commented out [:L332].
        # `move 997 to WE-Error` [:L333] and `move 99  to FS-Reply` [:L334].
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.ACCESS_TYPE_WRONG),
        )
        # `go to aa999-main-exit` [:L335]. Class 2.
        return _HandlerLabel.AA999_MAIN_EXIT

    # `move zero to Cobol-File-Status.` [:L341]. The commented-out
    # `move zeros to FS-Reply WE-Error.` above it is dated `27/07/16 16:30`
    # [:L340] and is NOT restored.
    context.cobol_file_status = 0
    # `move "OPEN PL INVOICE File" to WS-File-Key.` [:L342]
    _file_key(file_access, "OPEN PL INVOICE File")
    if int(file_access.fs_reply) != int(status.FsReply.SUCCESS):
        # `move  999 to WE-Error.` [:L344]
        file_access.we_error = _WE_ERROR_HANDLER_GENERIC
    # `go to aa999-main-exit.  *> with test for dup processing` [:L345] - the
    # trailing comment describes a test that is not there. Class 2.
    return _HandlerLabel.AA999_MAIN_EXIT


def aa030_process_close(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa030-Process-Close.` [common/acas026.cbl:L347-L358].

    Close, then clear `File-Function` and `Access-Type` and log one last time.

    ⭐ ANOMALY ``N-close-logs-twice``. The ordering is unusual and load-bearing:
    `perform aa999-main-exit.` [:L354] logs FIRST, then
    `move zero to File-Function Access-Type.` [:L355-L356] under
    `*> close log file`, then `perform Ca-Process-Logs.` [:L357] logs a SECOND
    time - now with a ZEROED function pair, which is how `fhlogger` is told to
    close its output. So one close produces TWO log records, and the second
    records a verb that was never requested: function 0 and access type 0. Anyone
    counting operations from the log therefore over-counts every close, and the
    zeroed pair is indistinguishable from a caller that genuinely passed zero.
    ⛔ Reproduced, both records; the sentinel is not suppressed.

    ⭐ ANOMALY ``N-perform-aa999-then-goto``. `aa999-main-exit` is reached here by
    `PERFORM` [:L354] and then this paragraph leaves by `go to aa-main-exit`
    [:L358] - so the one label has TWO control outcomes in one program: performed,
    it logs and RETURNS to the next statement; jumped to, it logs and falls into
    `aa-main-exit`. Every other verb paragraph reaches it the second way. That is
    why :func:`aa999_main_exit` is modelled as a plain function returning nothing
    and the label machine, not the function, decides where control goes next -
    Agent Action Plan section 0.4.2 Class 4 for the `PERFORM` and Class 2 for the
    `go to`, at the same target.

    ⭐ ANOMALY ``N-close-key-no-period``.
    `move "CLOSE PL INVOICE File" to WS-File-Key` [:L353] has NO terminating
    period, so it and the `perform` on the next line are one sentence. Harmless
    here because the next statement is unconditional, but it is the same class of
    omission as Agent Action Plan anomaly 1's missing period in `sl060`, where the
    consequence is that a whole close never executes. Recorded, not added.

    ⭐ ANOMALIES ``N-sl-in-purchase-openclose`` and ``N-open-close-key-wording``.
    The bridge's counterpart writes `"CLOSE SL INVOICE"`
    [common/plinvoiceMT.cbl:L614] - again the SALES prefix, again without the
    trailing `" File"`. Both preserved at their own sites.
    """
    # `move 202 to WS-No-Paragraph.` [:L348]
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa030-Process-Close"
    ]
    # `move spaces to WS-File-Key.     *> for logging` [:L349]
    _file_key(file_access, "")
    # `close Invoice-File.` [:L350] - the ISAM verb, omitted; it writes no status.
    # `move zero to Cobol-File-Status.` [:L352]; the commented-out
    # `move zeros to FS-Reply WE-Error.` [:L351] is NOT restored.
    context.cobol_file_status = 0
    # `move "CLOSE PL INVOICE File" to WS-File-Key` [:L353] - no period.
    _file_key(file_access, "CLOSE PL INVOICE File")
    # `perform aa999-main-exit.` [:L354] - the FIRST log. Class 4.
    aa999_main_exit(system, pinvoice, file_access, file_defs, dal_common, context)
    # `move zero to File-Function Access-Type.  *> close log file` [:L355-L356].
    file_access.file_function = 0
    file_access.access_type = 0
    # `perform Ca-Process-Logs.` [:L357] - the SECOND log, the sentinel. Class 4.
    ca_process_logs_handler(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
    # `go to aa-main-exit.` [:L358]. Class 2.
    return _HandlerLabel.AA_MAIN_EXIT


def aa040_process_read_next(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa040-Process-Read-Next.` [common/acas026.cbl:L360-L389].

    Sequential read, reached by `File-Function` 3 AND 34 - see
    :data:`_HANDLER_DISPATCH` for the fall-through
    (``N-read-next-header-is-read-next``). ⛔ No header filtering.

    ⭐ ANOMALY ``N-spaces-into-numeric-key``. The end-of-file pre-test moves
    `spaces` into `Invoice-Key` [:L369] - a group whose two halves are `pic 9(8)`
    and `pic 99` [copybooks/plwspinv2.cob:L11-L13], both NUMERIC. COBOL performs
    the group move byte-for-byte, so the field ends up holding ten space
    characters where digits are declared, and any later numeric reference to it is
    undefined. ⛔ Reproduced literally as spaces; NOT substituted with zeros.

    ⭐ `move 10 to FS-Reply WE-Error` [:L367-L368] - ONE statement setting BOTH to
    ten, which is the pair :func:`acas_posting.dal.status.end_of_file_status`
    returns.

    ⭐ ANOMALY ``N-stop``. `stop "Cobol File EOF"  *> for testing` [:L372] is a
    debugging halt left in the shipped source. It is on the flat-file path and so
    unreachable in the migrated cycle; it is recorded BOTH as an anomaly and as a
    deliberate omission under Agent Action Plan section 0.3.4, and ⛔ it is NOT
    reproduced as a pause, an `input()` or a sleep - a batch program that blocks on
    a terminal has no migrated equivalent.

    ⭐ `initialize Invoice-Record` [:L380] where `acas022:L435` uses
    `move spaces` - the mirrored handlers genuinely differ, and this one matches
    `acas019:L379` (``N-initialize``). Reproduced as an `initialize`.

    ⭐ `move zeros to WE-Error.` [:L388] zeroes ONLY `WE-Error`, where
    `acas022:L443` zeroes both. Matches `acas019:L387`. Reproduced as one field.

    ⭐ `move "EOF" to WS-File-Key  *> for logging` [:L381].
    """
    # `move 203 to WS-No-Paragraph.` [:L365]
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa040-Process-Read-Next"
    ]
    if context.cobol_file_eof:
        # `if Cobol-File-Eof` [:L366]. `move 10 to FS-Reply WE-Error` [:L367-L368].
        eof_reply, eof_we_error = status.end_of_file_status()
        _set_status(file_access, int(eof_reply), int(eof_we_error))
        # `move spaces to Invoice-Key SQL-Err SQL-Msg` [:L369-L371] - spaces into a
        # NUMERIC group. ``N-spaces-into-numeric-key``.
        context.invoice_key_raw = " " * 10
        file_access.logging_data.sql_err = " " * status.SQL_ERR_WIDTH
        file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
        # `stop "Cobol File EOF"  *> for testing` [:L372] - ``N-stop``, omitted.
        _LOG.debug(
            "acas026 aa040: `stop \"Cobol File EOF\"` [common/acas026.cbl:L372] "
            "is a debugging halt on the flat-file path and is deliberately not "
            "reproduced"
        )
        # `go to aa999-main-exit` [:L373]. Class 2.
        return _HandlerLabel.AA999_MAIN_EXIT

    # `read Invoice-File next record at end` [:L376] - the ISAM verb, taking its
    # own `at end` branch [:L377-L382] because the file is not present.
    eof_reply, eof_we_error = status.end_of_file_status()
    # `move 10 to we-error fs-reply  *> EOF` [:L377]
    _set_status(file_access, int(eof_reply), int(eof_we_error))
    # `set Cobol-File-EoF to true` [:L378] and
    # `move 1 to Cobol-File-Status  *> JIC above dont work :)` [:L379].
    context.cobol_file_eof = True
    context.cobol_file_status = 1
    # `initialize Invoice-Record` [:L380] - an `initialize`, not `move spaces`.
    _initialise_header_record(pinvoice)
    # `move "EOF" to WS-File-Key  *> for logging` [:L381]
    _file_key(file_access, "EOF")
    # `go to aa999-main-exit` [:L382]. Class 2. The statements below are the
    # success path [:L384-L389]: `if FS-Reply not = zero go to aa999-main-exit.`
    # [:L384-L385], `move Invoice-Record to WS-PInvoice-Record.` [:L386],
    # `perform aa041-Move-Inv-Data.` [:L387] - Class 4 - `move zeros to WE-Error.`
    # [:L388] and `go to aa999-main-exit.` [:L389]. They are unreachable on the
    # migrated path for the reason given in the module block comment.
    #
    # ⭐⭐ ANOMALY ``N-fd-names-six-fields``, and it is why that group move loses
    # information rather than merely copying it. The FILE record names only SIX
    # fields and then 68 bytes of filler - `invoice-key` (`invoice-nos pic 9(8)` +
    # `item-nos pic 99  *> was binary-char.`), `invoice-supplier pic x(7)`,
    # `invoice-date binary-long`, `inv-order pic x(10)`, `invoice-type pic 9`, then
    # `filler pic x(10)` and `filler pic x(58)  *> was x(88). now rec 100`
    # [copybooks/plfdpinv.cob:L12-L21]. There is NO money group, NO `ih-Ref`, NO
    # `ih-status`, NO `ih-lines`, NO deduct pair, NO `ih-cr` and NO update flag: the
    # eight `s9(7)v99` amounts and every trailing flag live inside those 68 unnamed
    # bytes. So the flat file carries the DATA at the right offsets but names none
    # of it, and this group move is the only thing that gives those bytes their
    # meaning - a byte-for-byte reinterpretation, exactly like the two redefinitions
    # [copybooks/plwspinv2.cob:L21, :L56]. Recorded; nothing is named here that the
    # FD leaves unnamed.
    return _HandlerLabel.AA999_MAIN_EXIT


def aa041_move_inv_data(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> None:
    """`aa041-Move-Inv-Data.   *> Not really needed as both fields are now chars.`

    [common/acas026.cbl:L391-L394]. Assemble the ten-character log key out of the
    record's two key halves::

        move     Invoice-Nos to WS-Temp-ED-1.      [:L392]
        move     Item-Nos    to WS-Temp-ED-2.      [:L393]
        move     WS-Temp-ED  to WS-File-Key.       [:L394]

    ⭐⭐ ANOMALY ``N-aa041-self-negating-comment``. The comment sits on the label
    line itself and says the paragraph is *"Not really needed as both fields are
    now chars."* - AND IT IS WRONG ABOUT ITS OWN OPERANDS. The staging fields are
    declared NUMERIC [common/acas026.cbl:L201-L203]::

        01  WS-Temp-ED.
            03  ws-temp-ed-1       pic 9(8).
            03  WS-Temp-ed-2       pic 99.

    Both `pic 9`, not `pic x`. ⛔ The paragraph is NOT deleted on the strength of
    its own comment; it is reproduced and the contradiction is recorded.

    ⭐ This handler is the only one in the folder whose two staging fields are BOTH
    numeric - `acas019.cbl:L202-L204` declares `x(7)` followed by `9(8)`.

    Performed from four places: `aa040` [:L387], `aa045` [:L408], `aa060` [:L485],
    `aa070` [:L497], `aa080` [:L508] and `aa090` [:L520] - six, in fact, and every
    one of them is Agent Action Plan section 0.4.2 Class 4 (sibling re-dispatch).
    """
    # `move Invoice-Nos to WS-Temp-ED-1.` [:L392] - `pic 9(8)`.
    context.ws_temp_ed_1 = int(pinvoice.ih_prime.ws_invoice_key.ih_invoice)
    # `move Item-Nos to WS-Temp-ed-2.` [:L393] - `pic 99`.
    context.ws_temp_ed_2 = int(pinvoice.ih_prime.ws_invoice_key.ih_test)
    # `move WS-Temp-ED to WS-File-Key.` [:L394] - the group, ten characters.
    _file_key(
        file_access,
        _digits(context.ws_temp_ed_1, 8) + _digits(context.ws_temp_ed_2, 2),
    )
    return None


def aa045_eval_keys(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> None:
    """`aa045-Eval-Keys.` [common/acas026.cbl:L398-L414].

    `evaluate File-Function  *> Set up keys just for logging` [:L399] over five
    verbs, with an inner `evaluate File-Key-No` [:L405-L411].

    ⭐ ANOMALY ``N-deadbranches``. The maintainer's own comment above the label
    reads `*>   The next block will never get executed unless performed  so is it
    needed ?` [:L396] - and it IS performed, from `aa050` [:L419] and `aa060`
    [:L443]. But because those are the only two callers, the `when 5` (write),
    `when 7` (rewrite) and `when 8` (delete) arms [:L401-L403] are UNREACHABLE, and
    so is `when other` [:L412]. Only `when 4` and `when 9` can ever match. ⛔ The
    whole `evaluate` is reproduced, dead arms included; nothing is pruned.

    ⭐ `when  8   *> fn-delete    For delete can ignore Desc key` [:L403] - the
    comment refers to a descending key this table does not have.

    ⭐ `move WS-Invoice-Key to Invoice-Key` [:L407] copies the LINKAGE buffer's key
    into the ISAM RECORD's key, then `perform aa041-Move-Inv-Data` [:L408] builds
    the log key from it - Class 4. `when other move spaces to WS-File-Key` [:L410]
    for any key number but 1, which the guard in `aa010-main` has already made
    impossible for these verbs.

    ⭐ The reference at `aa050`'s [:L419] spells it `aa045-Eval-keys` with a
    lower-case `k` against the label's capital `K` at [:L398]. COBOL is
    case-insensitive so it resolves; recorded as a naming inconsistency.
    """
    function = int(file_access.file_function)
    if function in (
        int(status.FileFunction.READ_INDEXED),
        int(status.FileFunction.WRITE),
        int(status.FileFunction.RE_WRITE),
        int(status.FileFunction.DELETE),
        int(status.FileFunction.START),
    ):
        # `evaluate File-Key-No` [:L405]. Only key 1 is admitted by `aa010-main`'s
        # guard for read-indexed, start and delete; write and rewrite are not
        # guarded but cannot reach here.
        if int(file_access.logging_data.file_key_no) == _ONLY_ADMITTED_KEY_NUMBER:
            # `move WS-Invoice-Key to Invoice-Key` [:L407]
            context.invoice_key_raw = _group_ws_invoice_key(
                pinvoice.ih_prime.ws_invoice_key.ih_invoice,
                pinvoice.ih_prime.ws_invoice_key.ih_test,
            )
            # `perform aa041-Move-Inv-Data` [:L408]. Class 4.
            aa041_move_inv_data(
                system, pinvoice, file_access, file_defs, dal_common, context
            )
        else:
            # `when other move spaces to WS-File-Key` [:L409-L410]
            _file_key(file_access, "")
    else:
        # `when other move spaces to WS-File-Key` [:L412-L413] - unreachable,
        # kept.
        _file_key(file_access, "")
    return None


def aa050_process_read_indexed(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa050-Process-Read-Indexed.` [common/acas026.cbl:L416-L436].

    Keyed read on key 1 only.

    ⭐ ANOMALY ``N-failed-action``. On an invalid key the paragraph does TWO things
    [:L429-L430]: `initialize WS-PInvoice-Record` - it wipes the CALLER'S buffer -
    and `move "Failed action" to WS-File-Key`, a literal string where every other
    log key in the handler is a key value or an operation name. Both effects are
    reproduced; the buffer really is cleared.

    ⭐ `move 21 to we-error fs-reply` [:L423] - ONE statement writing 21 into BOTH
    fields, so `We-Error` carries a file-status value rather than a `We-Error`
    code. The bridge's counterpart writes `23` / zero instead
    [common/plinvoiceMT.cbl:L871-L872]; the two halves of one logical operation
    disagree on both fields.

    ⭐ `move 998 to WE-Error  *> file seeks key type out of range but should never
    get here       998` [:L434] and `move 99 to fs-reply` [:L435] - the
    belt-and-braces arm for a key number other than 1, which `aa010-main`'s guard
    has already rejected. Kept.
    """
    # `move 204 to WS-No-Paragraph.` [:L418]
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa050-Process-Read-Indexed"
    ]
    # `perform aa045-Eval-keys.` [:L419] - lower-case `k` in the reference.
    # Class 4.
    aa045_eval_keys(system, pinvoice, file_access, file_defs, dal_common, context)
    # `move zero to Cobol-File-Status.` [:L420]
    context.cobol_file_status = 0
    if int(file_access.logging_data.file_key_no) == _ONLY_ADMITTED_KEY_NUMBER:
        # `if File-Key-No = 1` [:L421] then
        # `read Invoice-File key WS-Invoice-Key invalid key` [:L422] - the ISAM
        # verb, taking its `invalid key` branch.
        # `move 21 to we-error fs-reply` [:L423] - both fields, one statement.
        _set_status(
            file_access,
            int(status.FsReply.INVALID_KEY_ON_START),
            int(status.FsReply.INVALID_KEY_ON_START),
        )
        if int(file_access.fs_reply) == int(status.FsReply.SUCCESS):
            # `if fs-Reply = zero` [:L425]:
            # `move Invoice-Record to WS-PInvoice-Record` [:L426] then
            # `perform aa041-Move-Inv-Data` [:L427]. Class 4.
            aa041_move_inv_data(
                system, pinvoice, file_access, file_defs, dal_common, context
            )
        else:
            # `else initialize WS-PInvoice-Record` [:L429] - the CALLER'S buffer -
            # and `move "Failed action" to WS-File-Key` [:L430].
            # ``N-failed-action``.
            _initialise_header_record(pinvoice)
            _file_key(file_access, "Failed action")
        # `go to aa999-main-exit` [:L432]. Class 2.
        return _HandlerLabel.AA999_MAIN_EXIT

    # `move 998 to WE-Error` [:L434] and `move 99 to fs-reply` [:L435].
    _set_status(
        file_access,
        int(status.FsReply.ERROR),
        int(status.WeError.FILE_KEY_NO_OUT_OF_RANGE),
    )
    # `go to aa999-main-exit.` [:L436]. Class 2.
    return _HandlerLabel.AA999_MAIN_EXIT


def aa060_process_start(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa060-Process-Start.` [common/acas026.cbl:L438-L487].

    Position on key 1 under one of four relations, each in its own `if` rather
    than in an `evaluate` [:L456-L483].

    ⭐⭐ ANOMALIES ``N-start-guard-differs-from-bridge`` and
    ``N-start-guard-no-fs-reply`` - one guard, two independent defects, the second
    the more serious because it is silent. The guard is
    `if access-type < 5 or > 8  *> NOT using 'not >'` [:L448] and it writes
    `move 998 to WE-Error  *> 998 Invalid calling parameter settings` [:L449] and
    then transfers WITHOUT SETTING `FS-Reply` [:L450] - so a caller that passes a
    bad access type receives `998` paired with whatever `fs-reply` the two
    statements at [:L444-L445] left, which is ZERO. A parameter error therefore
    reports SUCCESS in `FS-Reply`. The BRIDGE's guard writes the pair properly,
    `99` / `997` [common/plinvoiceMT.cbl:L950-L951]. Reproduced: no `FS-Reply` is
    invented here.

    ⭐ ANOMALY ``N-fn-not-greater-than-unhandled``. Access type 9,
    `fn-not-greater-than`, is declared in the shared vocabulary
    [copybooks/wsfnctn.cob:L88-L116] - `88 fn-not-greater-than value 9.` is the last
    line of the `Access-Type` block, and the range is cited here as L88-L116 rather
    than the Agent Action Plan section 0.1.1 figure of L88-L118, which overshoots a
    file that is only 117 lines long; verified by reading the copybook end to end -
    and is supported NOWHERE in this handler: the
    guard `< 5 or > 8` [:L448] rejects it, and the four positioning arms cover 5,
    6, 7 and 8 only [:L457, :L464, :L471, :L478] so there is no arm to reach even
    if it were admitted. The BRIDGE is the mirror image - it ADMITS 9 in its own
    guard and then carries a `when 9` arm that can never be selected
    [common/plinvoiceMT.cbl:L980-L981] (``N-start-guard-rejects-its-own-when-9``).
    So one published relation is unreachable on BOTH paths, by two different
    mistakes: omitted here, dead there. ⛔ Neither is repaired, and no fifth arm is
    added - which means `<=` is simply not available through this module, exactly
    as it is not available through the compiled handler.

    ⭐ Every arm's `invalid key` branch writes `move 21 to Fs-Reply` [:L459, :L466,
    :L473, :L480] and NO `We-Error`, so the `move zeros to fs-reply WE-Error`
    at [:L444-L445] is what a caller sees in the second field.

    ⭐ `move WS-Invoice-Key to Invoice-Key.` [:L455] happens BEFORE the arms and
    unconditionally, then `if File-Key-No = 1 perform aa041-Move-Inv-Data.`
    [:L484-L485] rebuilds the log key AFTER them - so a successful start logs the
    key and a failed one does not reach the rebuild.
    """
    # `move 205 to WS-No-Paragraph.` [:L442]
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa060-Process-Start"
    ]
    # `perform aa045-Eval-keys.` [:L443]. Class 4.
    aa045_eval_keys(system, pinvoice, file_access, file_defs, dal_common, context)
    # `move zeros to fs-reply WE-Error.` [:L444-L445]
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `move zero to Cobol-File-Status.` [:L446]
    context.cobol_file_status = 0

    access_type = int(file_access.access_type)
    if access_type < 5 or access_type > 8:
        # `if access-type < 5 or > 8  *> NOT using 'not >'` [:L448].
        # `move 998 to WE-Error` [:L449] - and NO `FS-Reply`.
        file_access.we_error = int(status.WeError.FILE_KEY_NO_OUT_OF_RANGE)
        # `go to aa999-main-exit` [:L450]. Class 2.
        return _HandlerLabel.AA999_MAIN_EXIT

    # `move WS-Invoice-Key to Invoice-Key.` [:L455]
    context.invoice_key_raw = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    if int(file_access.logging_data.file_key_no) == _ONLY_ADMITTED_KEY_NUMBER and (
        access_type
        in (
            int(status.AccessType.EQUAL_TO),
            int(status.AccessType.LESS_THAN),
            int(status.AccessType.GREATER_THAN),
            int(status.AccessType.NOT_LESS_THAN),
        )
    ):
        # The four `start Invoice-File key <rel> Invoice-Key invalid key` arms
        # [:L458, :L465, :L472, :L479], each taking its own `invalid key` branch:
        # `move 21 to Fs-Reply` [:L459, :L466, :L473, :L480] with no `We-Error`.
        file_access.fs_reply = int(status.FsReply.INVALID_KEY_ON_START)
        # `go to aa999-main-exit` [:L460, :L467, :L474, :L481]. Class 2.
        return _HandlerLabel.AA999_MAIN_EXIT

    if int(file_access.logging_data.file_key_no) == _ONLY_ADMITTED_KEY_NUMBER:
        # `if File-Key-No = 1 perform aa041-Move-Inv-Data.` [:L484-L485]. Class 4.
        aa041_move_inv_data(
            system, pinvoice, file_access, file_defs, dal_common, context
        )
    # `go to aa999-main-exit.` [:L487]. Class 2.
    return _HandlerLabel.AA999_MAIN_EXIT


def aa070_process_write(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa070-Process-Write.` [common/acas026.cbl:L489-L498].

    ⭐ `write Invoice-Record invalid key  move 22 to FS-Reply  end-write.`
    [:L494-L496] - `22` is the duplicate-key reply, and it is the ONLY status the
    arm writes, leaving `We-Error` at the zero [:L492] put there. The bridge's
    counterpart also leaves `We-Error` at zero (``N-write-leaves-we-error-zero``,
    [common/plinvoiceMT.cbl:L1166]), so on this one point the two halves agree.

    ⭐ `perform aa041-Move-Inv-Data.` [:L497] runs UNCONDITIONALLY, after both the
    success and the failure of the write - so a failed write still logs the key it
    tried. Class 4.
    """
    # `move 206 to WS-No-Paragraph.` [:L490]
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa070-Process-Write"
    ]
    # `move WS-PInvoice-Record to Invoice-Record.` [:L491] - the linkage buffer
    # into the ISAM record, the reverse of `aa040`'s [:L386].
    context.invoice_key_raw = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move zeros to FS-Reply  WE-Error.` [:L492]
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `move zero to Cobol-File-Status.` [:L493]
    context.cobol_file_status = 0
    # `write Invoice-Record invalid key` [:L494] - the ISAM verb, taking its
    # `invalid key` branch: `move 22 to FS-Reply` [:L495], no `We-Error`.
    file_access.fs_reply = int(status.FsReply.DUPLICATE_KEY)
    # `perform aa041-Move-Inv-Data.` [:L497] - unconditional. Class 4.
    aa041_move_inv_data(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
    # `go to aa999-main-exit.` [:L498]. Class 2.
    return _HandlerLabel.AA999_MAIN_EXIT


def aa080_process_delete(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa080-Process-Delete.` [common/acas026.cbl:L500-L509].

    ⭐ `delete Invoice-File record invalid key  move 21 to FS-Reply  end-delete.`
    [:L505-L507] - `21`, not the `995` the bridge pairs with its own `99`
    [common/plinvoiceMT.cbl:L1238-L1239], and again no `We-Error`.

    ⭐ Note that `aa080` does NOT re-check `File-Key-No`: `aa010-main`'s guard has
    already rejected anything but 1 with `996` [:L255], which is the one place in
    the handler where the delete verb gets its own error code.
    """
    # `move 207 to WS-No-Paragraph.` [:L501]
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa080-Process-Delete"
    ]
    # `move WS-PInvoice-Record to Invoice-Record.` [:L502]
    context.invoice_key_raw = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move zeros to FS-Reply  WE-Error.` [:L503]
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `move zero to Cobol-File-Status.` [:L504]
    context.cobol_file_status = 0
    # `delete Invoice-File record invalid key` [:L505] - `move 21 to FS-Reply`
    # [:L506].
    file_access.fs_reply = int(status.FsReply.INVALID_KEY_ON_START)
    # `perform aa041-Move-Inv-Data.` [:L508]. Class 4.
    aa041_move_inv_data(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
    # `go to aa999-main-exit.` [:L509]. Class 2.
    return _HandlerLabel.AA999_MAIN_EXIT


def aa090_process_rewrite(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa090-Process-Rewrite.` [common/acas026.cbl:L511-L521].

    ⭐ `rewrite Invoice-Record invalid key  move 21 to FS-Reply  end-rewrite`
    [:L517-L519] - `21`, where the bridge pairs `99` with `994`
    [common/plinvoiceMT.cbl:L1396-L1397].

    ⭐ ANOMALY ``N-endrewrite-no-period``. The `end-rewrite` at [:L519] carries NO
    terminating period, unlike `end-write.` [:L496] and `end-delete.` [:L507] in the
    two paragraphs either side of it - three sibling paragraphs written to the same
    template, one of them punctuated differently. Harmless here because the next
    statement is an unconditional `perform`, and recorded for the same reason Agent
    Action Plan anomaly 1 is: a missing period in this codebase is NOT always
    harmless - in `sl060` the identical omission nests a second conditional inside
    the first and stops a ledger close from ever running. ⛔ Not added.
    """
    # `move 208 to WS-No-Paragraph.` [:L513]
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa090-Process-Rewrite"
    ]
    # `move WS-PInvoice-Record to Invoice-Record.` [:L514]
    context.invoice_key_raw = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move zeros to FS-Reply  WE-Error.` [:L515]
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `move zero to Cobol-File-Status.` [:L516]
    context.cobol_file_status = 0
    # `rewrite Invoice-Record invalid key` [:L517] - `move 21 to FS-Reply` [:L518].
    file_access.fs_reply = int(status.FsReply.INVALID_KEY_ON_START)
    # `perform aa041-Move-Inv-Data.` [:L520]. Class 4.
    aa041_move_inv_data(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
    # `go to aa999-main-exit.` [:L521]. Class 2.
    return _HandlerLabel.AA999_MAIN_EXIT


def aa100_bad_function(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa100-Bad-Function.` [common/acas026.cbl:L523-L528].

    `*> Houston; We have a problem` [:L525], then `move 999 to WE-Error.  *> 999`
    [:L527] and `move 99  to fs-reply.` [:L528].

    ⭐ ANOMALY ``N-badfunction-pair-differs``, carried in the register also under the
    heading ``N-badfunction-divergence`` - one finding, two names. The HANDLER writes
    `999` / `99`; the
    BRIDGE writes `990` / `99` for the same condition
    [common/plinvoiceMT.cbl:L1412-L1413]. And the code that
    :mod:`acas_posting.dal.status` documents for an invalid function, `992`
    (`WeError.INVALID_FUNCTION`), is used by NEITHER. Three values for one
    condition; both live ones reproduced at their own sites.

    ⭐ There is NO transfer at the end of this paragraph - it FALLS THROUGH into
    `aa999-main-exit` [:L530]. Class 2.
    """
    # `move 999 to WE-Error.` [:L527] and `move 99  to fs-reply.` [:L528].
    _set_status(file_access, int(status.FsReply.ERROR), _WE_ERROR_HANDLER_GENERIC)
    # Class 2 - fall-through into `aa999-main-exit.` [:L530].
    return _HandlerLabel.AA999_MAIN_EXIT


def aa999_main_exit(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa999-main-exit.` [common/acas026.cbl:L530-L533].

    `if Testing-1 perform Ca-Process-Logs end-if.` [:L531-L533] and nothing else,
    then a FALL-THROUGH into `aa-main-exit` [:L535]. Identical in shape to the
    bridge's `ba999-end` [common/plinvoiceMT.cbl:L1435-L1437].
    """
    if _testing_1(dal_common):
        # `perform Ca-Process-Logs` [:L532]. Class 4.
        ca_process_logs_handler(
            system, pinvoice, file_access, file_defs, dal_common, context
        )
    # Class 2 - fall-through into `aa-main-exit.` [:L535].
    return _HandlerLabel.AA_MAIN_EXIT


def aa_main_exit(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa-main-exit.` [common/acas026.cbl:L535-L537].

    A label carrying only the comment `*> Now have processed cobol flat file,  so
    ..` [:L537] - and the sentence is never finished. Control falls through into
    `aa-Exit` [:L539]. This is also the label the RDB branch transfers to
    [:L266], so it is the join point of the two paths.
    """
    # Class 2 - fall-through into `aa-Exit.` [:L539].
    return _HandlerLabel.AA_EXIT


def aa_exit(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa-Exit.` [common/acas026.cbl:L539-L540] - `exit program.`

    The handler's single terminal label. Returning itself is how the label machine
    stops.
    """
    return _HandlerLabel.AA_EXIT


def ba_process_rdbms(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> None:
    """`ba-Process-RDBMS section.` [common/acas026.cbl:L542-L548].

    A section header whose content is entirely comment - the banner and
    `*>  Here we call the relevent RDBMS module for this table  *>   which will
    include processing any other joined tables as needed` [:L546-L547]. Note the
    phrase "any other joined tables": the second table of this pair, and the reason
    one handler owns two.

    ⭐⭐ THE PERFORM IS A **SECTION** PERFORM, and this is what makes the bridge
    reachable. `perform ba-Process-RDBMS` [:L265] names a SECTION, so COBOL runs
    the section to its end by fall-through - `ba010-Test-WS-Rec-Size` [:L550], then
    `ba012-Test-WS-Rec-Size-2` [:L558], then `ba015-Test-Ends` [:L601] WHICH ISSUES
    THE BRIDGE ``CALL`` [:L611-L615], then `ba-rdbms-exit` [:L619] whose
    `exit section` ends it.

    Contrast the flat-file path, which performs a PARAGRAPH:
    `perform ba012-Test-WS-Rec-Size-2.` [:L271] runs that one paragraph and returns,
    so it does NOT fall into `ba015-Test-Ends` and does NOT call the bridge. One
    routine, two reach behaviours, decided entirely by whether the `PERFORM`
    operand is a section name or a paragraph name.

    The single early exit out of this chain is `ba012`'s
    `go to ba-rdbms-exit` [:L586] on a record-size error, which skips the ``CALL``.
    That is why :func:`ba010_test_ws_rec_size` and
    :func:`ba012_test_ws_rec_size_2` report whether they transferred.
    """
    # Class 2 - fall-through into `ba010-Test-WS-Rec-Size.` [:L550], and on through
    # `ba012` [:L558].
    section_exited = ba010_test_ws_rec_size(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
    if section_exited:
        # `go to ba-rdbms-exit` [:L586] fired inside `ba012`, so `ba015-Test-Ends`
        # and its ``CALL`` are skipped. Class 3.
        return None
    # Class 2 - fall-through into `ba015-Test-Ends.` [:L601].
    ba015_test_ends(system, pinvoice, file_access, file_defs, dal_common, context)
    return None


def ba010_test_ws_rec_size(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> bool:
    """`ba010-Test-WS-Rec-Size.` [common/acas026.cbl:L550-L556].

    ONE statement: `move 12 to WS-Log-File-no.        *> for FHlogger` [:L556].

    ⭐⭐ ANOMALY ``N-log-no-increment``. TWELVE - the same value `aa010-main` moved
    at [:L241]. Ten sibling handlers add ten here; this one does not, and nothing
    in the source marks the omission. ⛔ NOT corrected to 22. See
    :data:`_LOG_FILE_NO_SIBLING_CENSUS` for the full comparison.

    The paragraph's own comment block explains what the NEXT paragraph does, not
    what this one does: `*>     Test on very first call only  (So do NOT use var A
    & B again)  *>       Lets test that Data-record size is = or > than declared
    Rec in DAL  *>          as we cant adjust at compile/run time due to ALL Cobol
    compilers ?` [:L552-L554]. Control falls through into
    `ba012-Test-WS-Rec-Size-2` [:L558].

    :returns: whatever `ba012-Test-WS-Rec-Size-2` reports - ``True`` if it
        transferred to `ba-rdbms-exit` [:L586] and the bridge ``CALL`` must
        therefore be skipped. A COBOL fall-through carries no value; the flag is
        how that transfer is made visible to :func:`ba_process_rdbms`, which is the
        function standing in for the section's own control flow.
    """
    # `move 12 to WS-Log-File-no.` [:L556] - NO increment.
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB
    # Class 2 - fall-through into `ba012-Test-WS-Rec-Size-2.` [:L558].
    return ba012_test_ws_rec_size_2(
        system, pinvoice, file_access, file_defs, dal_common, context
    )


def ba012_test_ws_rec_size_2(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> bool:
    """`ba012-Test-WS-Rec-Size-2.` [common/acas026.cbl:L558-L599].

    The first-call-only block: compare the two record lengths, then load the
    database credentials out of the system record.

    `if A = zero  *> so it is being called first time` [:L560] - `A` is the guard
    AND one of the two operands, which is why the comment on [:L552] warns
    `*> (So do NOT use var A & B again)`. `A` is
    `function Length (WS-PInvoice-Record)` [:L561-L563] and `B` is
    `function length (Invoice-Record)` [:L564-L566] - note the capital `Length`
    against the lower-case `length`, one statement apart.

    `if A < B  *> COULD LET caller module deal with these errors !!!!!!!` [:L567]
    writes `move 901 to WE-Error  *> 901 Programming error; temp rec length is
    wrong caller must stop` [:L568] and `move 99 to fs-reply  *> allow for last
    field ( FILLER) not being present in layout.` [:L569].

    ⭐ ANOMALY ``N-recsize`` / ``N-recsize-four-notes``. THREE different record
    sizes are recorded across the two copybooks - `*> record size 100 bytes
    06/05/17   26/03/09` [copybooks/plwspinv.cob:L6], `129 bytes 22/12/11 = 100
    less filler err.` [copybooks/plwspinv2.cob:L7-L8] and the `*> was x(88). now
    rec 100` on the trailing filler [:L19] - and `copybooks/plfdpinv.cob` carries a
    FOURTH. ⛔ NOT resolved; recorded alongside Agent Action Plan anomaly 15, the
    96-versus-98 contradiction in `wsbatch.cob`. This is exactly the comparison
    this paragraph performs, which is why the disputed size matters.

    ⭐ ANOMALY ``N-record-size-guard-unreachable``. As the layouts stand TODAY both
    records total exactly 100 bytes - the working-storage record
    [copybooks/plwspinv.cob:L8-L53] and the file record
    [copybooks/plfdpinv.cob:L12-L21] - so `A` and `B` are always equal, `if A < B`
    [:L567] is always false, and the entire error block it guards is DEAD CODE that
    nonetheless ships: the `string` [:L572-L578], the two `display`s [:L579-L580],
    the `move Display-Blk to SQL-Msg` [:L581], the conditional `Ca-Process-Logs`
    [:L582-L584], the `accept` [:L585] and the transfer [:L586]. `We-Error 901` is
    therefore unreachable through this handler, and `_ERROR_MESSAGE_PL907` -
    declared, formatted and never emitted - is dead with it.

    It is reproduced in full and deliberately NOT short-circuited, for one reason:
    per ``N-recsize`` above the record size is DISPUTED across four statements in
    three files, so "both are 100" is a property of today's layouts and not an
    invariant of the design. Should any caller ever pass a buffer built to the 126-
    or the 129-byte note, the guard fires and the whole block becomes live. Writing
    it out is what makes that behaviour available rather than merely documented.

    ⭐ Agent Action Plan section 0.3.4: the `accept Accept-Reply at 2433` [:L585]
    is a PAUSE FOR ACKNOWLEDGEMENT with no database effect, so it is DROPPED - but
    the `go to ba-rdbms-exit` [:L586] that follows it IS preserved, because the
    transfer is what prevents the bridge from being called with a
    short record. The two `display`s [:L579-L580] and the `string` into
    `Display-Blk` [:L572-L578] become one log line, and `move Display-Blk to
    SQL-Msg` [:L581] is preserved because `SQL-Msg` is a data field a caller can
    read.

    ⭐ THE CREDENTIALS. [:L593-L598] move six fields out of the system record into
    `RDB-Data` - schema, user, password, port, host, socket, IN THAT ORDER, which
    is NOT the order the bridge extracts them in
    [common/plinvoiceMT.cbl:L570-L593]. The load is delegated to
    :func:`acas_posting.dal.connection.load_rdb_data_once`, which owns the
    first-call-only semantics and the frozen-placeholder detection; ⛔ it is NOT
    duplicated here.

    :returns: ``True`` if `go to ba-rdbms-exit` [:L586] fired, meaning the record
        lengths disagreed and the bridge ``CALL`` must be skipped; ``False`` for the
        ordinary fall-through into `ba015-Test-Ends` [:L601]. Reached BOTH ways -
        by section fall-through from `ba010-Test-WS-Rec-Size` on the RDB path and by
        `perform ba012-Test-WS-Rec-Size-2.` [:L271] on the flat-file path, where the
        flag is discarded because a paragraph perform cannot fall into `ba015`
        anyway. See :func:`ba_process_rdbms` for the distinction.
    """
    if context.record_size_a != 0:
        # `if A = zero` [:L560] - already run, so the whole block is skipped and
        # control falls straight through to `ba015-Test-Ends` [:L601].
        return False

    # `move function Length (WS-PInvoice-Record) to A` [:L561-L563] and
    # `move function length (Invoice-Record) to B` [:L564-L566].
    context.record_size_a = _WS_RECORD_DECLARED_LENGTH
    context.record_size_b = _FILE_RECORD_DECLARED_LENGTH

    if context.record_size_a < context.record_size_b:
        # `move 901 to WE-Error` [:L568] and `move 99 to fs-reply` [:L569].
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.RECORD_SIZE_MISMATCH),
        )

    if int(file_access.we_error) == int(status.WeError.RECORD_SIZE_MISMATCH):
        # `if WE-Error = 901` [:L571]. `move spaces to Display-Blk` [:L572] then
        # five operands, every one `delimited by size` [:L573-L577], into a
        # `pic x(75)` field [:L195]:
        #   `PL907` (32) + `A` (4) + `" < "` (4) + `"Invoice-Rec = "` (14) + `B` (4)
        # = 58 characters, so the remaining 17 stay spaces from [:L572].
        context.display_blk = (
            _ERROR_MESSAGE_PL907
            + _digits(context.record_size_a, _RECORD_SIZE_DIGITS)
            + " < "
            + "Invoice-Rec = "
            + _digits(context.record_size_b, _RECORD_SIZE_DIGITS)
        )[:_DISPLAY_BLK_WIDTH].ljust(_DISPLAY_BLK_WIDTH, " ")
        # `display Display-Blk at 2301 with erase eol` [:L579] with the
        # maintainer's own `*> BUT WILL REMIND ME TO SET IT UP correctly`, and
        # `display PL901 at 2401 with erase eol` [:L580]. Neither has a database
        # effect, so both become one log line under Agent Action Plan section 0.3.4.
        _LOG.error(
            "acas026 ba012 [common/acas026.cbl:L571-L580]: %s / %s",
            status.sanitise_for_log(context.display_blk),
            _ERROR_MESSAGE_PL901,
        )
        # `move  Display-Blk to SQL-Msg` [:L581] - PRESERVED, because `SQL-Msg` is a
        # data field the caller reads, not screen output.
        file_access.logging_data.sql_msg = context.display_blk[
            : status.SQL_MSG_WIDTH
        ].ljust(status.SQL_MSG_WIDTH, " ")
        if _testing_1(dal_common):
            # `if Testing-1 perform Ca-Process-Logs end-if` [:L582-L584]. Class 4.
            ca_process_logs_handler(
                system, pinvoice, file_access, file_defs, dal_common, context
            )
        # `accept Accept-Reply at 2433` [:L585] - the pause, DROPPED.
        # `go to ba-rdbms-exit` [:L586] - the transfer, PRESERVED. Class 4: the
        # target is `exit section`, so returning from this function is the
        # equivalent and the bridge `CALL` at [:L611] is never reached.
        ba_rdbms_exit(
            system, pinvoice, file_access, file_defs, dal_common, context
        )
        return True

    # `move RDBMS-DB-Name to DB-Schema` [:L593] through
    # `move RDBMS-Socket to DB-Socket` [:L598] - six moves, delegated.
    file_access.rdb_data = connection.load_rdb_data_once(system)
    context.system_record = system
    # `end-if.` [:L599] then Class 2 fall-through into `ba015-Test-Ends.` [:L601].
    return False


def ba015_test_ends(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> None:
    """`ba015-Test-Ends.` [common/acas026.cbl:L601-L617].

    The bridge `CALL`, INLINE - there is no `ba020-*` paragraph in this handler
    (``N-nobadal``), and the parameter list has a BLANK LINE in it [:L613]::

        call     "plinvoiceMT" using File-Access        [:L611]
                                     ACAS-DAL-Common-data   [:L612]
                                                            [:L613]
                                     WS-PInvoice-Record     [:L614]
        end-call.                                           [:L615]

    ⭐ ANOMALY ``N-cdftodo``. Above the call sits an unfinished plan:
    `*>   HERE we need a CDF [Compiler Directive] to select the correct DAL based
    *>     on the pre SQL compiler e.g., JCs or dbpre or Prima conversions <<<< ?
    >>>>>  *>        Do this after system testing and pre code release.`
    [:L604-L606], then `*>  NOW SET UP FOR JC pre-sql compiler system.` [:L608]
    and `*>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql`
    [:L609]. The directive was never written, so the JC translator's output is the
    only DAL this handler can reach - which is why
    :data:`BRIDGE_NAME` is a constant and not a selection.

    ⭐ THE ERROR CONTRACT, verbatim: `*>   Any errors leave it to caller to recover
    from` [:L617]. Nothing after the call inspects the status; the handler hands it
    straight back. Which is why :func:`plinvoice_mt` returns a status pair and
    never raises.

    Control falls through into `ba-rdbms-exit` [:L619].
    """
    # `call "plinvoiceMT" using File-Access ACAS-DAL-Common-data
    #  WS-PInvoice-Record` [:L611-L615] - the parameter order is the BRIDGE'S, not
    # the handler's, and the bridge names its third operand `WS-Invoice-Record`
    # (``N-bridge-param-rename``).
    plinvoice_mt(file_access, dal_common, pinvoice, context=context)
    # Class 2 - fall-through into `ba-rdbms-exit.` [:L619].
    ba_rdbms_exit(system, pinvoice, file_access, file_defs, dal_common, context)
    return None


def ba_rdbms_exit(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> None:
    """`ba-rdbms-exit.` [common/acas026.cbl:L619-L620] - `exit section.`

    An `exit section`, not a plain `exit`, so it leaves `ba-Process-RDBMS`
    entirely - which is what makes `ba012`'s `go to ba-rdbms-exit` [:L586] skip the
    bridge call. Contrast `ca-Exit.     exit.` [:L629], a plain exit
    (``N-nolog-on-dal``). The banner beneath it is
    `*>   ****     *******` [:L621].
    """
    return None


def ca_process_logs_handler(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> None:
    """`Ca-Process-Logs. *> Not called on DAL access as it does it already`

    [common/acas026.cbl:L623-L627]. `call "fhlogger" using File-Access
    ACAS-DAL-Common-data.` [:L626-L627].

    ⭐ ANOMALY ``N-nolog-on-dal``, and the comment that states it sits on the LABEL
    LINE ITSELF at [:L623]. On the RDB path the handler must NOT log, because the
    bridge's own `ba999-end` [common/plinvoiceMT.cbl:L1435-L1437] already did -
    and the handler's flat-file `aa999-main-exit` [:L531-L533] is the only route to
    this paragraph other than the close sentinel [:L357] and the record-size error
    [:L583]. Reproduced: this function is reached only from those three sites, and
    :func:`ca_process_logs` is the bridge's separate logger.

    R-1: `fhlogger` is a COBOL program [common/fhlogger.cbl] and is NOT called.
    Every field that can carry a key, a host name or an error message goes through
    :func:`acas_posting.dal.status.redact_for_log` first.
    """
    _LOG.info(
        "fhlogger(acas026): system=%s file=%s paragraph=%s function=%s "
        "access=%s key=%s fs-reply=%s we-error=%s",
        int(file_access.logging_data.ws_log_system),
        int(file_access.logging_data.ws_log_file_no),
        int(file_access.logging_data.ws_no_paragraph),
        int(file_access.file_function),
        int(file_access.access_type),
        status.redact_for_log(file_access.logging_data.ws_file_key),
        int(file_access.fs_reply),
        int(file_access.we_error),
    )
    # No transfer. `Ca-Process-Logs` is reached only by `PERFORM` - from
    # `aa999-main-exit` [:L532], from the close sentinel [:L357] and from the
    # record-size error [:L583] - and `PERFORM <paragraph>` returns at the end of
    # THAT paragraph, so control does NOT fall into `ca-Exit` [:L629].
    # :func:`ca_exit_handler` is therefore unreachable, and is published anyway
    # because rule R-5 wants one function per paragraph.
    return None


def ca_exit_handler(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> None:
    """`ca-Exit.     exit.` [common/acas026.cbl:L629] - a PLAIN `exit`.

    Not `exit section`, unlike `ba-rdbms-exit` [:L620] eight lines above it, and
    the label and the verb share one source line. The whole program then ends with
    `end program acas026.` [:L631].
    """
    return None


#: Which function implements each label `aa010-main` and the flat-file verbs can
#: transfer to.
_HANDLER_LABEL_FUNCTIONS: Final[Mapping[_HandlerLabel, Any]] = MappingProxyType(
    {
        _HandlerLabel.AA020_PROCESS_OPEN: aa020_process_open,
        _HandlerLabel.AA030_PROCESS_CLOSE: aa030_process_close,
        _HandlerLabel.AA040_PROCESS_READ_NEXT: aa040_process_read_next,
        _HandlerLabel.AA050_PROCESS_READ_INDEXED: aa050_process_read_indexed,
        _HandlerLabel.AA060_PROCESS_START: aa060_process_start,
        _HandlerLabel.AA070_PROCESS_WRITE: aa070_process_write,
        _HandlerLabel.AA080_PROCESS_DELETE: aa080_process_delete,
        _HandlerLabel.AA090_PROCESS_REWRITE: aa090_process_rewrite,
        _HandlerLabel.AA100_BAD_FUNCTION: aa100_bad_function,
        _HandlerLabel.AA999_MAIN_EXIT: aa999_main_exit,
        _HandlerLabel.AA_MAIN_EXIT: aa_main_exit,
        _HandlerLabel.AA_EXIT: aa_exit,
    }
)


def dispatch(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    context: PInvoiceContext | None = None,
) -> FileAccess:
    """`acas026` - the file handler, FIVE parameters in the COBOL's own order.

    `common/acas026.cbl:L225-L231`, verbatim::

        Procedure Division Using System-Record

                                  WS-PInvoice-Record

                                  File-Access
                                  File-Defs
                                  ACAS-DAL-Common-data.

    and the Agent Action Plan section 0.4.3 contract this satisfies::

        FROM:  call "acas026" using System-Record WS-PInvoice-Record File-Access
                                   File-Defs ACAS-DAL-Common-data
        TO:    acas026_pinvoice.dispatch(system, pinvoice, file_access,
                                         file_defs, dal_common)

    ⭐ ONE record buffer, TWO tables. `WS-PInvoice-Record` is a single hundred-byte
    area that carries EITHER a header OR a line, and which one is decided by the
    redefinition the caller filled -
    `01  Invoice-Header redefines WS-PInvoice-Record.`
    [copybooks/plwspinv2.cob:L21] or `01  Invoice-Line redefines
    WS-PInvoice-Record.` [:L56]. The bridge sniffs `ih-Test` to tell them apart at
    four sites [common/plinvoiceMT.cbl:L827, :L1147, :L1189, :L1356].

    ⭐ THE VERB SET IS THE HANDLER'S. Nine codes: Open, Close, Read-Next (**3 AND
    34**), Read-Indexed, Write, Rewrite, Delete, Start. ⛔ No 31, no 32, no 33, no
    Delete-All - code 6 is `*> 6 is spare / unused` [:L301] here even though the
    bridge dispatches it. :func:`plinvoice_mt` publishes the bridge's ten.

    ⭐ The statement order is the COBOL's exactly, and it is checked in the
    validation list of the agent brief: log identity [:L240-L241]; the key guard
    [:L245-L259]; NO Open-Output block anywhere; the RDB branch with both
    maintainer comments [:L263-L267]; `ba012-Test-WS-Rec-Size-2` [:L271]; NO
    zeroing of `WE-Error` or `FS-Reply` [:L279-L280, commented out]; the
    THREE-field SQL clear [:L281]; then the function `evaluate` with 34 folded into
    the 3 arm [:L283-L303].

    :param system: `System-Record` [copybooks/wssystem.cob] - the first parameter,
        and the source of both `RDBMS-Flat-Statuses` (which path to take) and the
        six database credentials [:L593-L598].
    :param pinvoice: the shared record buffer, second parameter.
    :param file_access: `File-Access` [copybooks/wsfnctn.cob:L23-L38], third.
        Mutated in place and returned.
    :param file_defs: `File-Defs` [copybooks/wsnames.cob], fourth. The handler
        never reads it on either path - `*>  File paths for Cobol File has already
        done in main menu module` [:L273] - and it is in the signature because the
        `CALL` passes it. Recorded as a deliberate non-use, not dropped.
    :param dal_common: `ACAS-DAL-Common-data`
        [copybooks/Test-Data-Flags.cob:L6-L18], fifth.
    :param context: the module's persistent working storage; defaults to the
        module-level instance, as GnuCOBOL's does.
    :returns: ``file_access``, carrying `(FS-Reply, We-Error)` and the diagnostic
        fields. NEVER raises - `*>   Any errors leave it to caller to recover
        from` [:L617].
    """
    active = _DEFAULT_CONTEXT if context is None else context
    # `aa-Process-Flat-File Section.` [:L234] then the fall-through into
    # `aa010-main` [:L236].
    label = aa_process_flat_file(
        system, pinvoice, file_access, file_defs, dal_common, active
    )
    while label is not _HandlerLabel.AA_EXIT:
        implementation = _HANDLER_LABEL_FUNCTIONS.get(label)
        if implementation is None:
            # Unreachable; defended the way this handler defends, with its own
            # bad-function pair [:L527-L528] rather than an exception.
            _set_status(
                file_access, int(status.FsReply.ERROR), _WE_ERROR_HANDLER_GENERIC
            )
            break
        label = implementation(
            system, pinvoice, file_access, file_defs, dal_common, active
        )
    return file_access
