r"""COBOL file handler ``acas016`` and its bridge ``slinvoiceMT`` - the Invoice entity.

WHAT THIS MODULE OWNS
=====================
This is the ONLY module that issues SQL against the two Sales Invoice tables.
It reimplements a handler-and-bridge PAIR, which is why it carries two layers:

* the handler ``[common/acas016.cbl]`` - 641 lines - which validates the key
  number, decides flat-file versus RDB, and dispatches by function code; and
* the bridge ``[common/slinvoiceMT.cbl]`` - 3259 lines - which owns the host
  variables, the cursors and every SQL statement.

Entity ``Invoice`` -> handler ``acas016`` -> bridge ``slinvoiceMT`` -> **TWO**
tables:

======================= ======= ============================ ==================
Table                   Columns Primary key                  DDL
======================= ======= ============================ ==================
``SAINVOICE-REC``       31      ``SINVOICE-KEY`` ``char(10)`` [mysql/ACASDB.sql:L844-L877]
``SAINV-LINES-REC``     14      ``IL-LINE-KEY`` ``char(10)``  [mysql/ACASDB.sql:L809-L826]
======================= ======= ============================ ==================

Record layouts come from ``copybooks/slwsinv.cob`` (100 lines) and
``copybooks/slwsinv2.cob`` (109 lines) through
:mod:`acas_posting.records.sales_invoice`, which publishes ``SInvoiceHeader``,
``SInvoiceBodies``, ``SilInvoiceLine``, ``InvoiceRecord``, ``IhInvoiceHeader``
and ``IlInvoiceLine``.

WHY ONE MODULE OWNS TWO TABLES
==============================
Agent Action Plan section 0.3.1, verbatim:

    "**One data-access module per handler, not per table.** The COBOL call chain
    routes through handlers, and the handlers are not always one-to-one with
    tables - `acas000` dispatches to four different bridges by key number, and
    **both `acas016` and `acas026` own a header table plus a lines table**.
    Mirroring the handler boundary rather than the table boundary keeps the
    Python module set in exact correspondence with the COBOL programs that the
    traceability document must map, and **preserves the dispatch semantics
    rather than flattening them**."

CORRECTION TO THE AGENT ACTION PLAN - THE EXTRA READ FUNCTIONS
==============================================================
AAP section 0.4.1.5 says this module needs "the extra by-name/by-batch/by-customer
read functions". **That is factually wrong and is NOT implemented here.** The
authoritative function-code vocabulary is ``[copybooks/wsfnctn.cob:L102-L105]``:

* ``fn-Read-By-Name value 31``  [:L102] - "for Salesled (SL160)" -> ``acas012``
* ``fn-Read-By-Batch value 32`` [:L103] - "for OTM3/5 (sl095/pl095)" -> ``acas019``/``acas029``
* ``fn-Read-By-Cust value 33``  [:L104] - "for OTM3 (sl110, 120, 190)" -> ``acas019``
* ``fn-Read-Next-Header value 34`` [:L105] - "for Invoice (sl020, 50, 140, 820)"

``acas016``'s dispatch names exactly ONE of those four, code **34**, at
``[common/acas016.cbl:L297]``. Codes 31, 32 and 33 appear nowhere in this
module. The facade confirms it independently: the twelve published ``Invoice-*``
verbs at ``[copybooks/Proc-ACAS-FH-Calls.cob:L885-L946]`` include
``Invoice-Read-Next-Header`` [:L927] and contain **no** ``Read-By-*`` verb and
no ``Open-Extend``. Implementing 31/32/33 would add three behaviours the COBOL
does not have, which is precisely what rule R-3 forbids.

THE LINKAGE - FIVE PARAMETERS, ONE RECORD BUFFER
================================================
``[common/acas016.cbl:L233-L239]``, verbatim::

    Procedure Division Using System-Record

                              WS-Invoice-Record

                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.

There is ONE record parameter for TWO tables. ``WS-Invoice-Record`` is a UNION
buffer: ``copybooks/slwsinv2.cob`` declares ``Invoice-Record`` at [:L27], then
``Invoice-Header redefines Invoice-Record`` at [:L38] and ``Invoice-Line
redefines Invoice-Record`` at [:L91] - three views of the same 137 bytes. The
caller sets the buffer to whichever view the operation needs and the function
code plus ``WS-Sih-Test`` decide which table is touched. :class:`InvoiceBuffer`
reproduces that as ONE parameter with the shared ten-byte key region promoted,
never as two typed parameters.

The bridge takes three parameters in a DIFFERENT order,
``[common/acas016.cbl:L621-L625]``, verbatim::

    call     "slinvoiceMT" using File-Access
                                 ACAS-DAL-Common-data
                                 WS-Invoice-Record
    end-call.

Both signatures are published here for traceability (rule R-5):
:func:`dispatch` and :func:`slinvoice_mt`.

``[common/acas016.cbl:L627]`` states the error contract, verbatim:
``*>   Any errors leave it to caller to recover from``. Therefore **nothing in
this module raises on a database or status error** - every path returns the
``(FS-Reply, We-Error)`` pair in the caller's ``File-Access`` block.
:func:`acas_posting.dal.status.raise_for_status` is opt-in and is never called.

THE VERB SET AND THE TWO DIFFERENT DISPATCHES
=============================================
The handler and the bridge each have their own ``evaluate File-Function``, and
they **disagree about function code 6**. Both are reproduced, each in its own
layer, because they are reached on different paths.

Handler dispatch ``[common/acas016.cbl:L291-L311]`` - the FLAT-FILE path only::

    when 1  -> aa020-Process-Open
    when 2  -> aa030-Process-Close
    when 3       *>  (fall through)                       [:L296]
    when 34 -> aa040-Process-Read-Next   *> fn-Read-Next-Header ???   [:L297]
    when 4  -> aa050-Process-Read-Indexed
    when 5  -> aa070-Process-Write
    when 7  -> aa090-Process-Rewrite
    when 8  -> aa080-Process-Delete
    when 9  -> aa060-Process-Start
    when other -> aa100-Bad-Function     *> 6 is spare / unused        [:L309]

Bridge dispatch ``[common/slinvoiceMT.cbl:L516-L541]`` - the RDB path::

    when 1 -> ba020   when 2 -> ba030   when 3 / when 34 -> ba040
    when 4 -> ba050   when 5 -> ba070
    when 6 -> ba085-Process-Delete-All   *> option 6 is a special to
                                         *> cleardown all LINE data for 1 invoice
    when 7 -> ba090   when 8 -> ba080    when 9 -> ba060
    when other -> ba100-Bad-Function

Two consequences, both preserved:

1. ``when 3`` and ``when 34`` share a branch in BOTH layers, so whatever
   distinguishes them is re-derived INSIDE the shared body, never from the
   branch. The distinguishing test is ``ba041-Reread``:
   ``if FN-Read-Next-Header go to ba042-Fetch.``
   ``[common/slinvoiceMT.cbl:L722]`` - function 34 skips the line-walking block
   and always fetches the next HEADER.
2. Function 6 reaches ``aa100-Bad-Function`` in the handler but
   ``ba085-Process-Delete-All`` in the bridge. This is not a contradiction: the
   RDB branch at ``[common/acas016.cbl:L271-L275]`` performs
   ``ba-Process-RDBMS`` and then ``go to AA-Main-Exit``, so the handler's
   ``evaluate`` is never reached on the RDB path. See anomaly
   N-delete-all-bad-function below.

The two bad-function paragraphs also return DIFFERENT codes: the handler sets
``999``/``99`` ``[common/acas016.cbl:L535-L536]`` and the bridge sets
``990``/``99`` ``[common/slinvoiceMT.cbl:L1414-L1415]``.

THE KEY GUARD
=============
``[common/acas016.cbl:L253-L267]``, verbatim::

    evaluate File-Function
             when  4   *> fn-read-indexed
             when  9   *> fn-start
               if     File-Key-No not = 1
                      move 998 to WE-Error       *> file seeks key type out of range        998
                      move 99 to fs-reply
                      go   to aa999-main-exit
               end-if
             when     8  *> fn-delete
               if     File-Key-No not = 1
                      move 996 to WE-Error       *> file seeks key type out of range        996
                      move 99 to fs-reply
                      go   to aa999-main-exit
               end-if
    end-evaluate.

The guard admits key 1 only, yet the bridge declares TWO keys of reference
(below). Key 2 is therefore unreachable through the guarded verbs - see anomaly
N-key2-unreachable. The guard is NOT relaxed.

THE TWO HOST-VARIABLE GROUPS
============================
``[common/slinvoiceMT.cbl:L381-L385]`` declares both tables in one directive
block, verbatim::

    *> /MYSQL VAR\
    *>       ACASDB
    *>       TABLE=SAINVOICE-REC,HV
    *>       TABLE=SAINV-LINES-REC,HV1

The ``HV`` / ``HV1`` prefix is how the translator keeps them apart. The groups
are ``01 TD-SAINVOICE-REC`` at [:L389-L421] (31 host variables) and
``01 TD-SAINV-LINES-REC`` at [:L425-L440] (14 host variables). The other
``/MYSQL-END\`` markers at [:L604], [:L621], [:L673], [:L785] and [:L870] are
per-statement translator blocks, not further groups.

THREE ORDERINGS THAT DO NOT AGREE
=================================
For the header the copybook order, the host-variable order and the column order
are all different, and ``IH-LINES`` is where they diverge:

* copybook position 24 - ``sih-lines`` at ``[copybooks/slwsinv.cob:L61]``,
  immediately after the five status bytes;
* load-paragraph position 24 - ``move WS-Sih-Lines to HV-IH-LINES`` at
  ``[common/slinvoiceMT.cbl:L1479]``, before deduct-days, i.e. copybook order;
* host-variable position 29 - ``HV-IH-LINES`` at [:L419], after ``HV-IH-CR``;
* column ordinal 29 - ``IH-LINES`` in ``[mysql/ACASDB.sql:L873]``.

Therefore :data:`HEADER_COLUMNS` (column-ordinal order, taken from
``loader.entries_for_table``) and :data:`HEADER_LOAD_SEQUENCE` (move order,
taken from each host variable's ``load_source``) are built INDEPENDENTLY and one
is never derived from the other. Same for the lines. See
N-triple-order-mismatch.

THE ``COPY ... REPLACING`` THAT DELETES THE OCCURS
==================================================
``[common/slinvoiceMT.cbl:L453-L459]``, verbatim::

    *>  Using the first record but not the 2nd as it uses occurs 40 but
    *>   to reduce Ram usage get rid of the occurs.

    copy "slwsinv.cob"   replacing SInvoice-Header   by WS-Invoice-Record
                                   leading ==sih-==  by ==WS-Sih-==
                                   ==occurs 40.==    by ==.==
                                   ==sil-==          by ==Un-Used-Sil-==.

Four replacements, all load-bearing: the header record gains a fourth name; the
header fields gain the ``WS-Sih-`` prefix; the ``occurs 40`` on
``SInvoice-Bodies`` is DELETED, collapsing 40 elements to one; and every
``sil-`` field is renamed ``Un-Used-Sil-`` to announce it is dead. The bridge
declares its OWN line record in Working-Storage instead, ``01 WS-Invoice-Line``
at [:L361-L377]. So the header layout here follows the copybook and **the line
layout follows the bridge's working-storage declaration**, not the copybook.

THE DRIFT TABLE - ``SAINVOICE-REC``, 31 COLUMNS
===============================================
Every conversion is taken from ``loader.drift_for(<key>)``; the table is
reproduced for the reader.

**Read the Drift column narrowly.** It compares the three DECLARATIONS -
copybook, bridge host variable, MySQL column - and "clean" means only that those
three agree. It does NOT mean a value passes through unchanged, because a second
conversion happens afterwards at the ``WS-MYSQL-EDIT`` render step that no
declaration records; see "ELEVEN MORE SIGN LOSSES AT THE RENDER STEP" below and
:data:`MYSQL_EDIT_WINDOWS`. Eleven columns marked "clean" here lose their sign
there.

=== ============================ ============================ ======================= =========================
Ord Copybook (slwsinv.cob)       Bridge host variable         Column                  Drift
=== ============================ ============================ ======================= =========================
1   ``WS-Invoice-Key`` group L20 ``HV-SINVOICE-KEY X(10)``    ``char(10)`` **PK**     bridge-only concatenation
2   ``sih-invoice 9(8)`` L21     ``9(10) COMP`` L392          ``int(8) unsigned``     8 -> 10 -> 8
3   ``sih-test 99`` L22          ``9(03) COMP`` L393          ``tinyint(2) unsigned`` 2 -> 3 -> 2
4   ``sih-customer`` group L23   ``X(7)`` L394                ``char(7)``             group flattened
5   ``sih-date`` BINARY-LONG L26 ``9(10) COMP`` L395          ``IH-DAT int(8) uns.``  **SIGN LOST** + renamed
6   ``sih-order x(10)`` L27      ``X(10)`` L396               ``char(10)``            clean
7   ``sih-type 9`` L39           ``9(03) COMP`` L397          ``tinyint(1) unsigned`` 1 -> 3 -> 1
8   ``sih-ref x(10)`` L40        ``X(10)`` L398               ``char(10)``            clean
9   ``sih-description`` L42      ``X(32)`` L399               ``char(32)``            clean
10  ``sih-p-c``   COMP-3 L44     ``S9(07)V9(02)`` L400        signed ``decimal(9,2)`` clean, widen only
11  ``sih-net``   COMP-3 L45     ``S9(07)V9(02)`` L401        signed ``decimal(9,2)`` clean
12  ``sih-extra`` COMP-3 L46     ``S9(07)V9(02)`` L402        signed ``decimal(9,2)`` clean
13  ``sih-carriage`` COMP-3 L47  ``S9(07)V9(02)`` L403        signed ``decimal(9,2)`` clean
14  ``sih-vat``   COMP-3 L48     ``S9(07)V9(02)`` L404        signed ``decimal(9,2)`` clean
15  ``sih-discount`` COMP-3 L49  ``S9(07)V9(02)`` L405        signed ``decimal(9,2)`` clean
16  ``sih-e-vat`` COMP-3 L50     ``S9(07)V9(02)`` L406        signed ``decimal(9,2)`` clean
17  ``sih-c-vat`` COMP-3 L51     ``S9(07)V9(02)`` L407        signed ``decimal(9,2)`` clean
18  ``sih-status x`` L52         ``X(1)`` L408                ``char(1)``             clean
19  ``sih-status-P`` L56         ``X(1)`` L409                ``char(1)``             clean
20  ``sih-status-L`` L57         ``X(1)`` L410                ``char(1)``             clean
21  ``sih-status-C`` L58         ``X(1)`` L411                ``char(1)``             clean
22  ``sih-status-A`` L59         ``X(1)`` L412                ``char(1)``             clean
23  ``sih-status-I`` L60         ``X(1)`` L413                ``char(1)``             clean
24  ``sih-deduct-days`` BIN-CHAR ``9(03) COMP`` L414          ``tinyint(3) unsigned`` **SIGN LOST**
25  ``sih-deduct-amt 999v99``    ``9(03)V9(02)`` L415         ``decimal(5,2) uns.``   clean
26  ``sih-deduct-vat 999v99``    ``9(03)V9(02)`` L416         ``decimal(5,2) uns.``   clean
27  ``sih-days`` BINARY-CHAR L65 ``9(03) COMP`` L417          ``tinyint(3) unsigned`` **SIGN LOST**
28  ``sih-cr`` BINARY-LONG L66   ``9(10) COMP`` L418          ``int(8) unsigned``     **SIGN LOST**
29  ``sih-lines`` BIN-CHAR L61   ``9(03) COMP`` L419          ``tinyint(2) unsigned`` **SIGN LOST** + moved
30  ``sih-day-book-flag`` L67    ``X(1)`` L420                ``char(1)``             clean
31  ``sih-update x`` L69         ``X(1)`` L421                ``char(1)``             clean
=== ============================ ============================ ======================= =========================

THE DRIFT TABLE - ``SAINV-LINES-REC``, 14 COLUMNS
=================================================
The left-hand column is the bridge's own working-storage line record
``[common/slinvoiceMT.cbl:L361-L377]``, not the copybook, for the reason given
above.

=== ============================ ============================ ======================== =========================
Ord Bridge WS line record        Bridge host variable         Column                   Drift
=== ============================ ============================ ======================== =========================
1   ``WS-Sil-Key`` group L362    ``HV1-IL-LINE-KEY X(10)``    ``char(10)`` **PK**      bridge-only concatenation
2   ``WS-Sil-Invoice 9(8)`` L363 ``9(10) COMP`` L428          ``int(8) unsigned``      **LOADED, NEVER UNLOADED**
3   ``WS-Sil-Line 99`` L364      ``9(03) COMP`` L429          ``tinyint(2) unsigned``  2 -> 3 -> 2, load inverted
4   ``WS-Sil-Product x(13)``     ``X(13)`` L430               ``char(13)``             clean
5   ``WS-Sil-Pa xx`` L366        ``X(2)`` L431                ``char(2)``              clean
6   ``WS-Sil-Qty`` BIN-SHORT     ``9(05) COMP`` L432          ``smallint(6) unsigned`` **SIGN LOST**
7   ``WS-Sil-Type x`` L368       ``X(1)`` L433                ``char(1)``              clean
8   ``WS-Sil-Description`` L369  ``X(32)`` L434               ``char(32)``             clean
9   ``WS-Sil-Net`` COMP-3 L370   ``S9(07)V9(02)`` L435        signed ``decimal(9,2)``  clean
10  ``WS-Sil-Unit`` COMP-3 L371  ``S9(07)V9(02)`` L436        signed ``decimal(9,2)``  clean
11  ``WS-Sil-Discount 99v99``    ``9(02)V9(02)`` L437         ``decimal(4,2) uns.``    clean
12  ``WS-Sil-Vat`` COMP-3 L373   ``S9(07)V9(02)`` L438        signed ``decimal(9,2)``  clean
13  ``WS-Sil-Vat-Code 9`` L374   ``9(03) COMP`` L439          ``tinyint(1) unsigned``  1 -> 3 -> 1
14  ``WS-Sil-Update x`` L375     ``X(1)`` L440                ``char(1)``              clean
--  ``sil-Back-Ordered``         **NONE** - ``filler pic x``  **NO COLUMN**            2024 field stops here
=== ============================ ============================ ======================== =========================

SIX SIGN LOSSES - AND A CORRECTION TO THE AGENT PROMPT'S SEVEN
==============================================================
The generated data dictionary reports ``drift.signedness = True`` on exactly SIX
entries of the 45, each carrying ``anomaly_refs = ('A-11',)`` and
``ambiguity_refs = ('Q-3',)``: ``IH-DAT``, ``IH-DEDUCT-DAYS``, ``IH-DAYS``,
``IH-CR``, ``IH-LINES`` and ``IL-QTY``. They are :data:`SIGN_LOSS_KEYS`.

The agent prompt counts seven by including ``sih-test``. That is corrected here
rather than silently followed: ``[copybooks/slwsinv.cob:L22]`` reads
``05  sih-test      pic 99  value zero.  *> WAS binary-char`` - the field is
``PIC 99`` DISPLAY and **unsigned today**; the ``WAS binary-char`` note is
historical, and ``drift.signedness`` is ``False`` for it. Rule R-5 makes the
dictionary authoritative ("Data dictionary first ... it is what prevents fields
being transcribed by eye"), so six it is. The seventh is recorded as a
historical, not a live, narrowing.

The money's DECLARATIONS are clean: all ELEVEN ``decimal(9,2)`` columns - eight
on the header, three on the lines - are signed at copybook, host variable and
column alike, and the two ``decimal(5,2) unsigned`` deduction columns plus
``IL-DISCOUNT decimal(4,2) unsigned`` are unsigned at all three layers.

ELEVEN MORE SIGN LOSSES AT THE RENDER STEP - N-edit-mask-sign
=============================================================
**A clean declaration does NOT mean a negative value survives, and the agent
prompt's "the signed money is genuinely clean here" is right about the
declarations and wrong about the behaviour.** The bridge never binds a numeric
host variable: it ``MOVE``s it into ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)``
``[common/slinvoiceMT.cbl:L271]`` and ``STRING``s a fixed substring, and because
the mask's single ``-`` is FIXED insertion at position 1 while no window starts
before position 11, the sign is STRUCTURALLY UNREACHABLE. So the eleven signed
money columns lose their sign too - at the RENDER step rather than at the
``MOVE`` - which brings the real total to SEVENTEEN columns in which a negative
source lands positive: the six narrowings above plus these eleven.

This was ARBITRATED, not reasoned about. ``slinvoiceMT`` does not reference the
missing ``copybooks/ACAS-SQLstate-error-list.cob``, so it compiles; the compiled
bridge was built and driven against the frozen schema and stored ``+1234.56``
for a ``sih-net`` of ``-1234.56``, and ``5``/``9`` for ``sih-date``/``sih-cr`` of
``-5``/``-9``. A field-by-field diff of all 31 header and all 14 line columns
against this module's rows is EMPTY. See :data:`MYSQL_EDIT_WINDOWS` for the
mask layout, the 26 per-column windows with their render-site locators, and the
companion N-edit-mask-truncation anomaly, and
``docs/migration/ambiguity-resolutions.md`` for the resolution of Q-3,
Q-edit-mask-sign and Q-edit-mask-truncation.

The contrast worth keeping is therefore narrower than the prompt suggests: what
makes ``valueMT``'s money sign loss legible is that it loses the sign at the
DECLARATION, visibly, whereas this bridge loses it invisibly at the render.

FIELDS WITH NO HOST VARIABLE AND NO COLUMN - DELIBERATE OMISSIONS (R-5)
=======================================================================
Recorded as omissions, never added:

* ``sih-nos`` and ``sih-check`` - the two components of ``sih-customer``
  ``[copybooks/slwsinv.cob:L24-L25]``; only the flattened 7-byte group reaches
  ``IH-CUSTOMER``.
* ``sih-Freq``, ``sih-Repeat``, the ``filler xxx`` and ``sih-Last-Date`` - the
  whole ``filler redefines sih-order`` autogen view
  ``[copybooks/slwsinv.cob:L28-L38]``; only the raw 10 bytes reach ``IH-ORDER``.
  No COLUMN is added for any of the four - but note that they ARE those ten
  bytes, so what a caller writes through them still has to reach ``IH-ORDER``.
  See correction C1 below.
* ``sil-Back-Ordered`` ``[copybooks/slwsinv.cob:L97-L98]`` and its twin
  ``il-Back-Ordered`` ``[copybooks/slwsinv2.cob:L106]`` - added 03/03/24, with
  **no host variable and no column**. See N-back-ordered-dropped.
* ``slwsinv2.cob``'s trailing ``filler pic x(10)`` [:L35] and
  ``filler pic x(95)`` [:L36], and its ``Invoice-Customer`` / ``Invoice-Date`` /
  ``Invoice-Type`` generic view - representation only.
* ``WS-Body-Key pic x(9). *> Not used`` ``[common/slinvoiceMT.cbl:L348]`` and
  the ``RG-Table`` reminder block [:L316-L326] - declared, never used.

THE ``NOT NULL`` INVARIANT - DEFAULT, NEVER OMIT
================================================
``initialize TD-SAINVOICE-REC.`` is the first statement of the header load
``[common/slinvoiceMT.cbl:L1453]`` and ``initialize TD-SAINV-LINES-REC.`` the
first of the line load [:L2787], so an unset host variable becomes zero or
space, never SQL ``NULL``. AAP section 0.6.2, verbatim: *"This is why every
column in the schema can be declared `NOT NULL` and why the Python layer must
default rather than omit."* All 31 header columns and all 14 line columns are
``NOT NULL`` with no ``DEFAULT`` in the frozen DDL. Every ``INSERT`` here names
every column and **no parameter is ever bound as ``None``**.

STATUS CODES - INCLUDING A FAMILY UNIQUE TO THE TWO-TABLE BRIDGES
=================================================================
The authoritative comment block is ``[common/slinvoiceMT.cbl:L183-L209]``. Note
the agent prompt cites ``L473-L481`` for it; that span is the ``screen section``
(``Display-Message-1`` / ``Display-Message-2``). The correction is recorded
rather than silently applied. Verbatim extract [:L199-L207]::

    *>                                     910* = Table locked > 5 seconds
    *>                                     901  = File Def Record size not =< than ws record size
    *>                                     8nn  = Processing on RG Table & rows.
    *>                                     890  = Unknown and unexpected error, again ^^ see above on RG processing
    *>                                     880  = Unexpected range error in Rg1 secondary key.
    *>                                            Report to programming team.

The ``8nn`` family exists in NO single-table bridge - it belongs to this module
and to ``acas026_pinvoice.py`` alone. Of the two named members only **890 is
ever assigned**, once, at ``[common/slinvoiceMT.cbl:L2446]``. **880 is
documented and never assigned anywhere in this bridge** (its only non-comment
use in the whole frozen tree is ``[common/paymentsMT.cbl:L1741]``), so it is
declared here as documented-only and never emitted - emitting it would add a
code path the COBOL does not have. See N-rg-status-codes.

``910`` is not implemented as a retry: AAP anomaly N1 establishes that the
lock-retry ladder at ``copybooks/mysql-procedures.cpy:L209-L256`` is dead code
whose only ``perform`` is commented out, so a lock surfaces as ``(99, 911)``.
``901`` belongs to :mod:`acas_posting.dal.connection` and is called, not
duplicated.

ANOMALIES REPRODUCED OR RECORDED (rule R-4)
===========================================
Each is reproduced at a site carrying its own inline ``[path:Lnnn]`` locator, per
AAP section 0.7.4 C-4. Every one also belongs in
``docs/migration/anomaly-log.md`` naming this module; the oracle questions
belong in ``docs/migration/ambiguity-resolutions.md``.

* **N-il-invoice-never-unloaded** - ``HV1-IL-INVOICE`` is loaded [:L2791] and
  never unloaded [:L2822-L2834]; 14 moves out, 13 back. The dictionary agrees:
  ``unloaded_to_record`` is ``False`` and ``unload_source`` is ``None``.
* **N-lines-loadorder** - the line load moves LINE [:L2790] before INVOICE
  [:L2791] while the host-variable group [:L428-L429] and the column list both
  put INVOICE first. Third load-order inversion in the tree.
* **N-lines-cursor-from-ih-test** - the LINES cursor position is seeded from the
  HEADER's ``IH-TEST`` [:L1538] with the author's hedge ``*> should be zero``.
* **N-back-ordered-dropped** - the 03/03/24 field has no host variable and no
  column; the bridge has a bare ``filler pic x`` where it would sit [:L377].
* **N-rg-notused-yet** - the RG metadata says ``NOT USED - YET`` [:L313-L314]
  while ``bc000``/``bc100``/``bc200`` [:L2849]/``bc300`` [:L3042] are the only
  path to the lines table.
* **N-two-cursors** - ``Most-Cursor-Set`` and ``Most-Cursor-Set-2``
  [:L331-L336], never collapsed.
* **N-key2-unreachable** - two keys of reference [:L296-L310] against a guard
  admitting only key 1 ``[common/acas016.cbl:L256]``, [:L262].
* **N-delete-all-bad-function** - ``Invoice-Delete-All``
  ``[copybooks/Proc-ACAS-FH-Calls.cob:L911]`` and ``fn-Delete-All value 6``
  ``[copybooks/wsfnctn.cob:L94]`` exist, yet ``[common/acas016.cbl:L309]`` calls
  6 "spare / unused" and routes it to bad-function, while the BRIDGE calls it
  "a special to cleardown all LINE data for 1 invoice" and marks it
  "Coded / D.Tested" ``[common/slinvoiceMT.cbl:L529-L532]``. Since the RDB branch
  leaves before the handler's evaluate, WHICH ANSWER A CALLER GETS DEPENDS ON
  ``File-System-Used``: the verb works on the RDB path and dies with 999/99 on the
  ISAM path. AAP anomaly #6 family, made conditional. And on the working path it
  still clears no line data, because ba085 matches one header row by exact key
  (N-ba085-not-actually-all) and bc085's predicate is a string literal
  (N-bc085-string-constant-predicate).
* **N-perform-range-violation** - ``ba012-Test-WS-Rec-Size-2`` is reached BOTH by a
  SECTION perform ``[common/acas016.cbl:L273]`` and by a PARAGRAPH perform
  ``[:L279]``, and its ``go to ba-rdbms-exit`` ``[:L596]`` leaves the PERFORM range
  in the second case - an undefined return. The two PERFORM forms are honoured
  separately (the fall-through lives in ``ba_process_rdbms_handler``, not in the
  paragraph functions, so the ISAM path never calls the bridge) and the undefined
  return is recorded as an oracle question rather than invented.
* **N-copy-replacing** - the ``occurs 40`` deletion and the ``Un-Used-Sil-``
  renaming [:L456-L459].
* **N-triple-key-materialisation** - the key is stored three times per row on
  both tables [:L391-L393], [:L427-L429].
* **N-header-key-not-unloaded** - ``HV-SINVOICE-KEY`` loaded [:L1455], not
  unloaded [:L1496-L1527].
* **N-triple-order-mismatch** - copybook, host-variable and column orderings all
  differ; ``IH-LINES`` at 24 / 24 / 29 / 29.
* **N-rg-status-codes** - ``8nn``, ``890``, ``880``; only 890 is assigned.
* **N-signloss** - six live narrowings, applied in the loads before SQL is
  built, behind one named helper, with no raise, no ``abs``, no clamp.
* **N-edit-mask-sign** - every numeric column is rendered through
  ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` ``[common/slinvoiceMT.cbl:L271]`` and a
  fixed substring of it; the mask's ``-`` is FIXED insertion at position 1 and
  none of the 26 windows starts before position 11, so a negative value is
  stored POSITIVE. Adds ELEVEN more sign losses on top of N-signloss's six - the
  signed ``decimal(9,2)`` money columns whose declarations are clean - for a
  real total of seventeen. ARBITRATED against the compiled bridge, which stored
  ``+1234.56`` for a ``sih-net`` of ``-1234.56``. Reproduced by
  :func:`render_through_mysql_edit`; see :data:`MYSQL_EDIT_WINDOWS`.
* **N-edit-mask-truncation** - the same windows are narrower than the mask's 19
  integer positions - ``(14:07)``, ``(11:10)``, ``(18:03)``, ``(16:05)``,
  ``(19:02)`` - so a value with more integer digits than its window loses the
  HIGH-ORDER excess silently. Reproduced by :func:`ws_mysql_edit`.
* **N-ih-dat-rename** - ``sih-date`` becomes column ``IH-DAT``.
* **N-logsystem5-meaning** - code 5 means "Invoice" at
  ``[common/acas016.cbl:L248]`` but "Stock" at ``[common/acas013.cbl:L298]`` and
  ``[common/acas015.cbl:L291]``, and the shared
  :class:`acas_posting.dal.status.LogSystem` carries ``STOCK = 5``.
* **N-log** - the log file number is set to 12 [:L249] then overwritten with 22
  [:L567], and 12/22 collides three ways with ``acas006`` (system 2) and
  ``acas015`` (system 6).
* **N-noopenoutput** - a FOURTH Open-Output behaviour: absent entirely. Open
  with ``Open-Output`` deletes nothing here.
* **N-nobadal** - no ``ba020-*`` paragraph in the handler; the bridge ``CALL`` is
  inline in ``ba015-Test-Ends`` [:L621-L625].
* **N-noreread** - no reread paragraph in the handler.
* **N-stop** - a debugging ``stop "Cobol File EOF"`` ``[common/acas016.cbl:L379]``
  with the comment upper-cased ``*> FOR TESTING ONLY``, against
  ``acas015``'s lower-case form. Flat-file path, unreachable in the migrated
  cycle; recorded as anomaly AND omission, never a pause or ``input()``.
* **N-noparagraph-collision** - handler trace values 201..208 identical to
  ``acas013`` and ``acas015``.
* **N-nolog-on-dal** - ``Ca-Process-Logs.`` carries its comment on the label
  line, ``[common/acas016.cbl:L633]``: *"Not called on DAL access as it does it
  already"*.
* **N-996-comment** - the 996 comment [:L263] is a verbatim copy of the 998
  comment [:L257], never rewritten.
* **N-initialize** - two initialisation semantics in one bridge,
  ``initialize ... with filler`` [:L804] against plain [:L1496]; plus the lone
  British ``initialise`` [:L2501].
* **N-punctuation** - the header load's periods are irregular, [:L1455],
  [:L1457], [:L1458] then unpunctuated to [:L1486]. Never normalised.
* **N-keyname-padding** - ``'SINVOICE-KEY'`` is space-padded explicitly [:L297]
  while ``'IL-LINE-KEY'`` relies on ``pic x(30)`` [:L301].
* **N-kortype** - ``KOR-Type`` is ``'STR'`` [:L299], [:L303] while its own
  comment says "Not used currently" [:L310].
* **N-drychk** - both RG load/unload sections are headed ``*> Dry chk ?``
  [:L2776], [:L2810].
* **N-rg-todo** - an unresolved TODO inside the line load [:L2783], quoted and
  not acted on.
* **N-deadfields** - ``WS-Body-Key`` [:L348] and the ``RG-Table`` reminder.
* **N-recsize** - the 129 / 134 / 137 history and two shouted warnings,
  ``[copybooks/slwsinv.cob:L9-L12]`` and ``[copybooks/slwsinv2.cob:L25]``, plus
  the maintainer's own ``*> 42 ??? bytes`` / ``*> 95 ??? bytes``
  ``[copybooks/slwsinv2.cob:L39]``, [:L60]. Nothing resolved.
* **N-changelog-divergence** - ``[common/acas016.cbl:L78]`` lists three consumer
  programs for code 34 while ``[copybooks/wsfnctn.cob:L105]`` lists four. Cause
  found: ``[copybooks/wsfnctn.cob:L17]`` still carries the original 18/04/17
  three and [:L19] records ``sl820`` being added on 20/05/23 - a staged edit,
  not a contradiction.
* **N-cdftodo** - the unfinished compiler-directive TODO
  ``[common/acas016.cbl:L614-L619]``.
* **N-bridge-doc-vs-guard** - the bridge documents 998 as "not 1, 2 or 3"
  [:L186] and 996 as "not = 1 or 2" [:L188] while the handler rejects anything
  ``not = 1``. Documentation and code disagree; the code wins.
* **N-fetch-rg1-status-erased** - ``bc051-Fetch-RG1`` sets ``23`` on no-more-data
  [:L2503] and then unconditionally zeroes ``FS-Reply`` and ``WE-Error`` two
  statements later [:L2509], destroying it.

AMBIGUITIES FOR THE ORACLE (rule R-6, AAP section 0.6.8)
========================================================
* **Q-3, the stored value of a narrowed negative** - what an unsigned column
  receives when a signed value is moved through an unsigned host variable is a
  property of the bridge's C interface and must be measured, not assumed. The
  six :data:`SIGN_LOSS_KEYS` carry ``ambiguity_refs = ('Q-3',)``.
* **Q-edit-mask-sign** - the bridge renders every numeric host variable through
  ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` [:L271] and then takes a FIXED substring
  that always starts at position 11 or later, e.g.
  ``FUNCTION TRIM (WS-MYSQL-EDIT(14:07)) "." WS-MYSQL-EDIT(22:02)`` for signed
  money. The single ``-`` in that mask is fixed insertion, so the sign sits at
  position 1 and **no substring ever reads it**. This module binds the signed
  ``Decimal`` rather than transcribing the rendering, because AAP section 0.6.2
  requires reproducing the bridge's CONVERSION - and the ``MOVE`` into a signed
  ``S9(07)V9(02)`` host variable preserves the sign - while the drop is an
  artefact of the display mask. The divergence is recorded as an oracle question
  rather than settled here; the compiled oracle cannot arbitrate it in this
  checkout because ``copybooks/ACAS-SQLstate-error-list.cob`` is missing from the
  frozen archive and blocks the bridge build.
* **N-recsize** above is itself an oracle question, alongside AAP anomaly #15
  (``wsbatch.cob``'s 96-versus-98).
* **Q-order-overlay-blank-state** - what ``sih-Repeat`` and ``sih-Last-Date`` read
  as once ``sih-order`` has been blanked. ``initialize WS-Invoice-Record.``
  [:L1496] blanks the ten bytes, so ``sih-Repeat pic 99``
  [copybooks/slwsinv.cob:L36] holds two SPACE characters in a zoned field and
  ``sih-Last-Date binary-long`` [:L38] holds ``0x20202020``. Neither has an
  ``int`` form, and the record contract types both as ``int``. Both are modelled
  as zero - see :func:`_blank_order_overlay` for why the alternative is worse -
  and what the compiled program reports for a zoned field full of spaces is an
  oracle question rather than a decision made here. It is unobservable through
  this bridge either way: the overlay has no host variable and no column.
* **Q-order-overlay-nonascii** - what a ``utf8mb3 char(10)`` column stores when
  the projected ``sih-Last-Date`` bytes are not printable ASCII. The frozen bridge
  sends the same ten bytes through a quoted SQL literal, so the question is the
  transport's and not this module's; it can only arise for a header written
  through the overlay, which no in-scope program does.

TRANSLATION CORRECTIONS - WHERE PYTHON NEEDS A STATEMENT COBOL DID NOT
======================================================================
A translation correction is the inverse of an anomaly. An anomaly is behaviour
the compiled program HAS and this module reproduces (R-4); a correction is
behaviour the compiled program gets FOR FREE from a language feature Python
lacks, which this module must therefore write out. Omitting one is the defect.
This module has ONE.

* **C1, ``REDEFINES`` IS ONE BYTE AREA AND PYTHON HAS TWO OBJECTS.**
  ``03 sih-order pic x(10).`` [copybooks/slwsinv.cob:L27] is redefined by
  ``03 filler redefines sih-order.`` [:L28], whose four members - ``sih-Freq``
  [:L29], ``sih-Repeat`` [:L36], a ``filler xxx`` [:L37] and ``sih-Last-Date``
  [:L38] - tile the same ten bytes. In the compiled program a write through
  either name is a write through both, so
  ``move WS-Sih-Order to HV-IH-ORDER`` [:L1461] carries it either way and no
  synchronising statement exists to translate. Section 0.3.1 requires each
  ``REDEFINES`` to be its own view class and ``records/sales_invoice.py`` states
  outright that it declines to keep the pair in step, so the aliasing belongs to
  whoever observes it - this bridge. :func:`_project_order_overlay_into_base`
  runs immediately before the move and only when the overlay carries something,
  and :func:`_blank_order_overlay` reproduces the blanking the initialise of
  ``sih-order`` performs over the shared bytes. The reverse direction is
  deliberately omitted, with its reason, at the unload site. Direction is settled
  by the frozen source: the overlay's only writers are the out-of-scope autogen
  series [sales/sl810.cbl:L1636, :L1648, sales/sl830.cbl:L534, :L615], the base
  is what every in-scope reader reads [sales/sl055.cbl:L641,
  purchase/pl055.cbl:L554], and the autogen author cleared the overlay by
  blanking the base [sales/sl830.cbl:L540] under his own note at [:L505]. Nothing
  is added that R-3 forbids: no field, no column, no width, no validation.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
=========================================
No COBOL is executed, embedded or shelled out to (R-1). No accounting value
touches a binary float (R-2). No DDL, no ORM, no threads, no ``asyncio``, no
pooling, no explicit transaction control (R-3) - ``autocommit`` is per statement,
exactly as the bridge behaves. No clock, no randomness, no sleep (R-6).
Statement order is the COBOL's: header before lines, in the bridge's own
sequence.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from types import MappingProxyType
from typing import Any, Final

from acas_posting.dal.connection import (
    ConnectionPolicyError,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1980_close,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    TABLE_OF_KEYNAMES,
    TABLE_PRIMARY_KEYS,
    CursorSlot,
    CursorState,
    CursorStateTable,
    KeyOfReference,
    start_relation_for,
)
from acas_posting.dal.status import (
    DUPLICATE_KEY_ERRNOS,
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    FileFunction,
    FsReply,
    LogSystem,
    SqlState,
    WeError,
    is_duplicate_key_bridge_level,
    mysql_1100_db_error,
    redact_for_log,
    sanitise_for_log,
    start_access_type_is_valid,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess, LoggingData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.sales_invoice import (
    BRIDGE,
    ENTITY_FACADE,
    HANDLER,
    HEADER_TABLE,
    LINES_TABLE,
    IhCustomer,
    IhFig,
    IhInvoiceHeader,
    IhOrderView,
    IhPrime,
    IhSubPrime,
    IlInvoiceLine,
    SihCustomer,
    SihFig,
    SihOrderView,
    SihPrime,
    SihSubPrime,
    SilInvoiceLine,
    SilKey,
    SInvoiceHeader,
    WsInvoiceKey,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

_LOG: Final[logging.Logger] = logging.getLogger(__name__)

__all__: Final[tuple[str, ...]] = (
    # Identity, taken from records.sales_invoice so the two never drift apart.
    "BRIDGE",
    "ENTITY_FACADE",
    "HANDLER",
    "HEADER_TABLE",
    "LINES_TABLE",
    # Log identity and the trace-number maps.
    "BRIDGE_PARAGRAPH_TRACE",
    "HANDLER_PARAGRAPH_TRACE",
    "WS_LOG_FILE_NO_FLAT",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    # Status vocabulary this bridge adds to the shared set.
    "BRIDGE_BAD_FUNCTION_WE_ERROR",
    "BRIDGE_START_ACCESS_TYPE_RANGE",
    "HANDLER_BAD_FUNCTION_WE_ERROR",
    "HANDLER_START_ACCESS_TYPE_RANGE",
    "RG_FAMILY_DESCRIPTION",
    "RG_SECONDARY_KEY_RANGE_WE_ERROR",
    "RG_UNKNOWN_UNEXPECTED_WE_ERROR",
    # Column metadata, generated from the data dictionary.
    "HEADER_COLUMNS",
    "HEADER_LOAD_SEQUENCE",
    "LINE_COLUMNS",
    "LINE_LOAD_SEQUENCE",
    "SIGN_LOSS_KEYS",
    "ColumnBinding",
    # Keys of reference and the two cursors.
    "HEADER_KEY_OF_REFERENCE",
    "LINE_KEY_OF_REFERENCE",
    "KEYS_OF_REFERENCE",
    # Host-variable groups and the record areas.
    "BridgeState",
    "InvoiceBuffer",
    # The linkage projection - the `sih-`/`ih-` rename `COPY ... REPLACING`
    # performs at compile time [common/acas016.cbl:L218-L221].
    "linkage_buffer_for",
    "publish_linkage_buffer",
    "TdSainvLinesRec",
    "TdSainvoiceRec",
    "WsInvoiceLine",
    # Load / unload, named after their COBOL sections.
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "bc000_hv_load_rg1",
    "bc100_unload_hvs_rg1",
    "bc200_insert_rg1",
    "bc300_update_rg1",
    # Bridge paragraphs.
    "ba010_initialise",
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
    "bc050_process_read_indexed",
    "bc051_fetch_rg1",
    "bc058_restore_pointers",
    "bc070_process_write",
    "bc080_process_delete",
    "bc085_process_delete_all",
    "bc090_process_rewrite",
    "bc998_free",
    # Handler paragraphs.
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
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
    "ba010_test_ws_rec_size_handler",
    "ba012_test_ws_rec_size_2_handler",
    "ba015_test_ends_handler",
    "ba_process_rdbms_handler",
    "ba_rdbms_exit_handler",
    "ca_exit_handler",
    "ca_process_logs_handler",
    "HEADER_KEY_COLUMN",
    "LINES_KEY_COLUMN",
    "READ_INDEXED_NO_ERRNO_WE_ERROR",
    "REWRITE_ROW_COUNT_WE_ERROR",
    "DELETE_FAILURE_WE_ERROR",
    "StatementOutcome",
    "SPINE",
    "ca_process_logs",
    # The two published entry points.
    "dispatch",
    "slinvoice_mt",
    # Helpers a caller or a test legitimately needs.
    "narrow_signed_host_variable",
    # The WS-MYSQL-EDIT rendering  [common/slinvoiceMT.cbl:L271] - published
    # because it is the arbitrated resolution of Q-edit-mask-sign and
    # Q-edit-mask-truncation and the parity suite must be able to assert it.
    "EditMaskWindow",
    "MYSQL_EDIT_FRACTION_DIGITS",
    "MYSQL_EDIT_FRACTION_POSITION",
    "MYSQL_EDIT_INTEGER_POSITIONS",
    "MYSQL_EDIT_LOCATOR",
    "MYSQL_EDIT_PICTURE",
    "MYSQL_EDIT_POINT_POSITION",
    "MYSQL_EDIT_SIGN_POSITION",
    "MYSQL_EDIT_UNITS_POSITION",
    "MYSQL_EDIT_WIDTH",
    "MYSQL_EDIT_WINDOWS",
    "render_through_mysql_edit",
    "ws_mysql_edit",
)


# ---------------------------------------------------------------------------
# Log identity  [common/acas016.cbl:L248-L249] and [common/acas016.cbl:L567]
# ---------------------------------------------------------------------------
# [common/acas016.cbl:L248] verbatim:
#     move     3      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice used in FH logging
#
# N-logsystem5-meaning.  The subsystem legend in that comment DISAGREES WITH
# ITSELF across handlers.  Verified: [common/acas013.cbl:L298] and
# [common/acas015.cbl:L291] both say "5=Stock"; this file says "5=Invoice";
# [common/acas000.cbl] uses "0 = Params".  Three incompatible legends for code 5
# in one codebase, and the shared enum sides with the majority -
# acas_posting.dal.status.LogSystem carries STOCK = 5 and has no INVOICE member.
# Nothing is harmonised: this handler's OWN value is 3 (SL), which is what is
# reproduced, and the legend divergence is recorded here because logging
# comparison is the only place it can bite and it would look inexplicable
# undocumented.
WS_LOG_SYSTEM: Final[int] = int(LogSystem.SL)

# N-log.  The file number is set twice.  [common/acas016.cbl:L249] verbatim:
#     move     12     to WS-Log-File-No.  *> RDB, File/Table
# then [common/acas016.cbl:L567], inside ba010-Test-WS-Rec-Size, verbatim:
#     move     22 to WS-Log-File-no.        *> for FHlogger
# Note the "-No" / "-no" capitalisation flip between the two statements, which is
# preserved as a comment rather than normalised.  The RDB-path value is 22.
#
# The 12 -> 22 pair collides THREE ways: acas006 (log system 2), acas015 (log
# system 6) and acas016 (log system 3) all use it.  Only the (system, file) pair
# disambiguates a log record.
WS_LOG_FILE_NO_FLAT: Final[int] = 12
WS_LOG_FILE_NO_RDB: Final[int] = 22


# ---------------------------------------------------------------------------
# ws-No-Paragraph trace numbers
# ---------------------------------------------------------------------------
# N-noparagraph-collision.  The handler's values are 201..208 and are IDENTICAL
# to acas013's and acas015's, so a log line is ambiguous without WS-Log-System.
# Each locator below is the `move nnn to WS-No-Paragraph` statement itself.
HANDLER_PARAGRAPH_TRACE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "aa020-Process-Open": 201,  # [common/acas016.cbl:L318]
        "aa030-Process-Close": 202,  # [common/acas016.cbl:L355]
        "aa040-Process-Read-Next": 203,  # [common/acas016.cbl:L372]
        "aa050-Process-Read-Indexed": 204,  # [common/acas016.cbl:L418]
        "aa060-Process-Start": 205,  # [common/acas016.cbl:L446]
        "aa070-Process-Write": 206,  # [common/acas016.cbl:L501]
        "aa080-Process-Delete": 207,  # [common/acas016.cbl:L512]
        "aa090-Process-Rewrite": 208,  # [common/acas016.cbl:L524]
    }
)

# The bridge keeps its own, entirely disjoint, numbering - 1..20 for the header
# and 51..58 for the Repeating Group.  Its own comment block
# [common/slinvoiceMT.cbl:L545-L564] is the source, and
# [common/slinvoiceMT.cbl:L2376-L2379] states the convention verbatim:
#     *>   Note that ws-No-Paragraph start at 51 for RG processing.
#     *>    Each bc para must end with a bc0n0-Exit. Last para used is 58.
#
# ⭐ N-trace-gaps.  The numbering is NOT dense and its own documentation is wrong in
# two places.  A census of every `move n to ws-No-Paragraph` in the bridge gives
# exactly these eighteen assignments:
#   1  [:L595]   2  [:L614]   3  [:L658]   4  [:L711]   5  [:L855]   6  [:L877]
#   8  [:L1009]  57 [:L1081]  10 [:L1163]  13 [:L1218]  15 [:L1315]  17 [:L1367]
#   20 [:L1424]  51 [:L2416]  52 [:L2470]  53 [:L2530]  54 [:L2587]  55 [:L2679]
#   56 [:L2730]  58 [:L3240]
# so 7, 9, 11, 12, 14, 16, 18 and 19 are NEVER ASSIGNED - eight holes in a sequence
# the comment block presents as complete.  And the doc block itself documents 56
# TWICE, at [:L560-L562]: once as `bc070 P=53 INSERT / 56 UPDATE` and once as
# `bc090 P=56 UPDATE`.  Only the values actually moved are reproduced below; the
# holes are left as holes and the duplicate documentation is recorded, not resolved.
#
# ⭐ N-trace-inherited compounds this: the four statement-building sections
# bb200-Insert [:L1543-L1948], bb300-Update [:L1949-L2358],
# bc200-Insert-rg1 [:L2849-L3041] and bc300-Update-rg1 [:L3042-L3238] contain ZERO
# `move ... to ws-No-Paragraph` statements, so each INHERITS its caller's number -
# a failure inside bb200-Insert reports against ba070-Process-Write's 10.

# --------------------------------------------------------------------------
# THE FOURTEEN EXIT TERMINATORS - mapped to `return`, not to a no-op function
#
# R-5 requires every paragraph to map to a function.  These fourteen labels are
# the one class where the faithful mapping is a RETURN in the enclosing function
# rather than a function of their own, because each contains NOTHING but a
# control terminator - no business logic, no state change, nothing to reproduce:
#
#   `exit program.`   ba999-exit  [common/slinvoiceMT.cbl:L1442]
#   `exit section.`   bb000-Exit  [common/slinvoiceMT.cbl:L1488]
#                     bb100-Exit  [common/slinvoiceMT.cbl:L1540]
#                     bb200-Exit  [common/slinvoiceMT.cbl:L1946]
#                     bb300-Exit  [common/slinvoiceMT.cbl:L2356]
#                     bc000-Exit  [common/slinvoiceMT.cbl:L2807]
#                     bc100-Exit  [common/slinvoiceMT.cbl:L2846]
#                     bc200-Exit  [common/slinvoiceMT.cbl:L3039]
#                     bc300-Exit  [common/slinvoiceMT.cbl:L3236]
#   `Exit.`           bc059-Exit  [common/slinvoiceMT.cbl:L2519]
#                     bc070-Exit  [common/slinvoiceMT.cbl:L2561]
#                     bc080-Exit  [common/slinvoiceMT.cbl:L2630]
#                     bc085-Exit  [common/slinvoiceMT.cbl:L2721]
#   `exit.`           bc090-Exit  [common/slinvoiceMT.cbl:L2774]  (lower case here
#                                 only - N-initialize's spelling drift again)
#
# Two of them are also the terminus of a `PERFORM ... THRU`:
# `perform bc085-Process-Delete-ALL thru bc085-Exit` [common/slinvoiceMT.cbl:L1351]
# and `perform bc090-Process-ReWrite thru bc090-Exit`
# [common/slinvoiceMT.cbl:L1360].  AAP section 0.1.1 rule 3 requires PERFORM THRU
# to become explicit function composition; because the spanned range here is a
# single working paragraph plus its own terminator, the composition is that one
# function call and the terminator is its `return`.
#
# Emitting fourteen empty functions instead would satisfy the letter of R-5 while
# breaking the Zero Placeholder Policy's ban on stub methods and empty bodies, and
# would add fourteen call sites the COBOL does not have.  The mapping is therefore
# RECORDED here rather than materialised - the same treatment AAP section 0.4.3
# gives gl072's unused facade stub block, which "maps to nothing" and is recorded
# so a reader comparing the two files does not conclude something was lost.
#
# The GO TO sites that target these labels are Class 3 (section/paragraph exit) in
# the AAP section 0.4.2 taxonomy and are `return` at their site: L2713 -> bc085-Exit
# and L2766 -> bc090-Exit.  Note also the only BACKWARD `GO TO` in the whole
# bridge, L2622 -> ba999-End [common/slinvoiceMT.cbl:L1435]: it is still Class 3,
# because ba999-End is a shared cleanup terminator ("Any Clean ups before
# quiting") and not a loop head.  A full census of both source files finds
# acas016.cbl forward=34/backward=0 and slinvoiceMT.cbl forward=40/backward=1, so
# there is NO Class 1 (loop-back) site anywhere in this module's sources - which
# is why no Class 1 annotation appears in this file.
# --------------------------------------------------------------------------
BRIDGE_PARAGRAPH_TRACE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ba020-Process-Open": 1,
        "ba030-Process-Close": 2,
        "ba040-Process-Read-Next": 3,
        "ba041-Reread": 4,
        "ba050-Process-Read-Indexed-select": 5,
        "ba050-Process-Read-Indexed-fetch": 6,
        "ba060-Process-Start-header": 8,
        "ba070-Process-Write": 10,
        "ba080-Process-Delete": 13,
        "ba085-Process-Delete-All": 15,
        "ba090-Process-Rewrite": 17,
        "ba998-Free": 20,
        "bc050-Process-Read-Indexed": 51,
        "bc051-Fetch-RG1": 52,
        "bc070-Process-Write": 53,
        "bc080-Process-Delete": 54,
        "bc085-Process-Delete-All": 55,
        "bc090-Process-Rewrite": 56,
        "ba060-Process-Start-rg1": 57,  # [common/slinvoiceMT.cbl:L1078]
        "bc998-Free": 58,  # [common/slinvoiceMT.cbl:L3240]
    }
)


# ---------------------------------------------------------------------------
# Status vocabulary
# ---------------------------------------------------------------------------
# The two bad-function paragraphs return DIFFERENT We-Error values, and both are
# reachable, so both are named.
#   handler [common/acas016.cbl:L535-L536]:  move 999 to WE-Error / move 99 to fs-reply
#   bridge  [common/slinvoiceMT.cbl:L1414-L1415]: move 990 to WE-Error / move 99 to Fs-Reply
# Note the handler's 999 is the value the bridge's own documentation calls
# "Not used here - Yet" [common/slinvoiceMT.cbl:L185] - a further divergence
# between the two layers' vocabularies, recorded and not harmonised.
HANDLER_BAD_FUNCTION_WE_ERROR: Final[int] = int(WeError.NOT_USED)
BRIDGE_BAD_FUNCTION_WE_ERROR: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)

# The START Access-Type guards ALSO differ between the layers, and the handler's
# is the odd one out in two ways: a wider range, and it sets We-Error WITHOUT
# setting FS-Reply.
#   handler [common/acas016.cbl:L448-L452] verbatim:
#       if       access-type < 5 or > 9      *> NOT using 'not >' - might be 08/08/23
#                move 998 to WE-Error        *> 998 Invalid calling parameter settings
#                go to aa999-main-exit
#   bridge  [common/slinvoiceMT.cbl:L954-L958]:  < 5 or > 8  ->  99 / 997
# The bridge's own comment block agrees with the bridge, not the handler:
# "997* = Access-Type wrong (< 5 or > 8)" [common/slinvoiceMT.cbl:L187].
HANDLER_START_ACCESS_TYPE_RANGE: Final[tuple[int, int]] = (5, 9)
BRIDGE_START_ACCESS_TYPE_RANGE: Final[tuple[int, int]] = (5, 8)

#: ``989`` - set by ``ba050-Process-Read-Indexed`` when the fetch returns nothing
#: AND the driver reported no errno [common/slinvoiceMT.cbl:L930], as the else-arm
#: of the ``990`` case at [:L925].  It has no name in
#: :class:`acas_posting.dal.status.WeError` because it appears in NO other handler
#: or bridge in the checkout - verified by searching ``common/`` for non-comment
#: uses - so it is declared locally rather than pushed into the shared enum.
READ_INDEXED_NO_ERRNO_WE_ERROR: Final[int] = 989

#: ``994`` - set by ``ba090-Process-Rewrite`` [common/slinvoiceMT.cbl:L1400] and
#: ``bc090-Process-Rewrite`` [:L2762] when an UPDATE does not affect exactly one
#: row.  Both carry the same maintainer aside, verbatim:
#: ``*> this may need changing for val in WE-Error!!``
REWRITE_ROW_COUNT_WE_ERROR: Final[int] = 994

#: ``35`` - moved to ``fs-Reply`` when ``open input Invoice-File`` fails
#: [common/acas016.cbl:L322].  Not a member of
#: :class:`acas_posting.dal.status.FsReply`, whose value set is 0/10/21/22/23/99
#: [copybooks/wsfnctn.cob:L23-L38]; 35 is a raw COBOL file status the handler passes
#: straight through on the ISAM path only, so it is declared locally.
_OPEN_INPUT_FAILED_FS_REPLY: Final[int] = 35

#: The five function codes ``aa045-Eval-Keys`` sets a key for
#: [common/acas016.cbl:L400-L404]: read-indexed, write, re-write, delete and start.
#: ⭐ 3 and 34 are ABSENT, so a read-next leaves ``WS-File-Key`` untouched by this
#: paragraph.  Order preserved as the COBOL lists it.
_AA045_KEYED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {
        int(FileFunction.READ_INDEXED),  # when 4
        int(FileFunction.WRITE),  # when 5
        int(FileFunction.RE_WRITE),  # when 7
        int(FileFunction.DELETE),  # when 8  *> For delete can ignore Desc key
        int(FileFunction.START),  # when 9
    }
)

#: ``995`` - the DELETE failure code, shared by ``ba080`` [:L1243], ``ba085``
#: [:L1338], ``bc080`` and ``bc085`` [:L2713].  This one IS named in the shared
#: enum, as ``WeError.DELETE_SQLSTATE_NOT_00000``, and is referenced through it.
DELETE_FAILURE_WE_ERROR: Final[int] = int(WeError.DELETE_SQLSTATE_NOT_00000)

# N-rg-status-codes.  The 8nn family exists in NO single-table bridge; it belongs
# to slinvoiceMT and plinvoiceMT alone.  Authoritative comment block
# [common/slinvoiceMT.cbl:L204-L207], verbatim:
#     *>                                     8nn  = Processing on RG Table & rows.
#     *>                                     890  = Unknown and unexpected error, again ^^ see above on RG processing
#     *>                                     880  = Unexpected range error in Rg1 secondary key.
#     *>                                            Report to programming team.
# (The agent prompt cites L473-L481 for this block; that span is the
#  `screen section`.  The correction is recorded, not silently applied.)
RG_FAMILY_DESCRIPTION: Final[str] = "Processing on RG Table & rows"

# 890 IS assigned - exactly once, in bc050-Process-Read-Indexed when the lines
# SELECT returns no rows: [common/slinvoiceMT.cbl:L2446].
RG_UNKNOWN_UNEXPECTED_WE_ERROR: Final[int] = 890

# 880 is DOCUMENTED AND NEVER ASSIGNED in this bridge.  Verified by exhaustive
# search: the only non-comment `move 880 to WE-Error` in the whole frozen tree is
# [common/paymentsMT.cbl:L1741], which belongs to an out-of-scope bridge.  It is
# therefore declared here for completeness and NEVER emitted - emitting it would
# add a code path the COBOL does not have, which rule R-3 forbids.
RG_SECONDARY_KEY_RANGE_WE_ERROR: Final[int] = 880

# Widths of the log fields, so every string this module writes truncates exactly
# as the COBOL MOVE would.  Taken from the frozen copybook, NOT from
# acas_posting.dal.status.LOG_FIELD_MAX_CHARS, which is that module's own
# redaction policy (200) and a different thing entirely.
#     05  WS-File-Key     pic x(64)  value spaces.   [copybooks/wsfnctn.cob:L52]
#     05  WS-Log-Where    pic x(231) value spaces.   [copybooks/wsfnctn.cob:L53]
_WS_FILE_KEY_WIDTH: Final[int] = 64
_WS_LOG_WHERE_WIDTH: Final[int] = 231


# ---------------------------------------------------------------------------
# Keys of reference and the TWO cursors
# ---------------------------------------------------------------------------
# [common/slinvoiceMT.cbl:L294-L310], verbatim:
#
#     *> Metadata on primary keys...   for SAINVOICE-REC & SAINV-LINES-REC
#     01  Table-Of-KeyNames.
#         03  filler         pic x(30) value 'SINVOICE-KEY                  '.   *> In SAINVOICE-REC
#         03  filler         pic x(8)  value '00010010'.  *> offset/length
#         03  filler         pic x(3)  value 'STR'.       *> data type
#         03  filler         pic x(30) value 'IL-LINE-KEY'.                      *> In SAINV-LINES-REC
#         03  filler         pic x(8)  value '00010010'.  *> offset/length
#         03  filler         pic x(3)  value 'STR'.       *> data type
#     01  filler redefines Table-Of-KeyNames.
#         03  KeyOfReference occurs 2
#                             indexed by KOR-x1.
#             05  keyname    pic x(30).
#             05  KOR-offset pic 9(4).
#             05  KOR-length pic 9(4).
#             05  KOR-Type   pic XXX.                    *> Not used currently
#
# N-keyname-padding.  'SINVOICE-KEY' is space-padded to 30 characters EXPLICITLY
# at [:L297] while 'IL-LINE-KEY' at [:L301] is written unpadded and relies on
# `pic x(30)`'s automatic space fill.  Both work.  Not normalised - the padded
# form survives in KeyOfReference.key_name for the header and the short form for
# the lines, exactly as declared.
#
# N-kortype.  KOR-Type is 'STR' for both while the comment on the redefine
# [:L310] says "Not used currently" - the same contradiction as in nominalMT,
# glpostingMT, glbatchMT and analMT; only slpostingMT says 'BNT'.
#
# Both keys are offset 0001 length 0010 because both are the first ten bytes of
# the SAME 137-byte union buffer - see InvoiceBuffer.
#
# N-key2-unreachable.  Two keys are declared here, but the handler's guard at
# [common/acas016.cbl:L256] and [common/acas016.cbl:L262] rejects any
# File-Key-No other than 1, so key 2 is NEVER selectable through fn-read-indexed,
# fn-start or fn-delete.  The lines are reached only through the header's cursor
# and the Repeating-Group path.  The guard is not relaxed.
HEADER_KEY_OF_REFERENCE: Final[KeyOfReference] = TABLE_OF_KEYNAMES[HEADER_TABLE][0]
LINE_KEY_OF_REFERENCE: Final[KeyOfReference] = TABLE_OF_KEYNAMES[LINES_TABLE][0]

# N-two-cursors.  [common/slinvoiceMT.cbl:L329-L336], verbatim:
#     01  DAL-Data.
#             05  MOST-Relation     pic xxx.             *> valid are >=, <=, <, >, =
#             05  Most-Cursor-Set   pic 9    value zero.
#                 88  Cursor-Not-Active      value zero.
#                 88  Cursor-Active          value 1.
#             05  Most-Cursor-Set-2 pic 9    value zero. *> RG 1
#                 88  Cursor-Not-Active-2    value zero.
#                 88  Cursor-Active-2        value 1.
# TWO cursors with their own 88 pairs, one per table.  Every single-table bridge
# has one.  They are never collapsed: the header uses CursorSlot.PRIMARY and the
# lines use CursorSlot.SECONDARY, which is exactly how
# acas_posting.dal.cursor_state already models this bridge's two keys.
KEYS_OF_REFERENCE: Final[Mapping[int, KeyOfReference]] = MappingProxyType(
    {1: HEADER_KEY_OF_REFERENCE, 2: LINE_KEY_OF_REFERENCE}
)

#: ``SINVOICE-KEY`` - the header primary key [mysql/ACASDB.sql:L876], and the
#: name the bridge's first key of reference carries
#: [common/slinvoiceMT.cbl:L297].  Taken from
#: :data:`acas_posting.dal.cursor_state.TABLE_PRIMARY_KEYS` rather than retyped,
#: so the two modules cannot drift apart.
HEADER_KEY_COLUMN: Final[str] = TABLE_PRIMARY_KEYS[HEADER_TABLE]
#: ``IL-LINE-KEY`` - the lines primary key [mysql/ACASDB.sql:L825] and the second
#: key of reference [common/slinvoiceMT.cbl:L301].  Declared, yet unreachable
#: through the handler's guarded verbs: N-key2-unreachable.
LINES_KEY_COLUMN: Final[str] = TABLE_PRIMARY_KEYS[LINES_TABLE]

# TWO INDEPENDENT AUTHORITIES, CROSS-CHECKED AT IMPORT.  The primary-key names above
# come from the frozen DDL by way of dal/cursor_state.TABLE_PRIMARY_KEYS, while the
# keys of reference come from the bridge's own Table-Of-KeyNames
# [common/slinvoiceMT.cbl:L296-L310].  Nothing guarantees a priori that the DDL's
# PRIMARY KEY and the bridge's key of reference name the same column - and where the
# three layers disagree elsewhere in this bridge they disagree loudly (see
# N-triple-order-mismatch, N-signloss).  Here they agree, so the agreement is asserted
# rather than assumed: a future divergence becomes an ImportError at the boundary
# instead of a silently wrong WHERE clause.
if HEADER_KEY_OF_REFERENCE.column_name != HEADER_KEY_COLUMN:  # pragma: no cover
    raise ImportError(
        "SAINVOICE-REC key of reference "
        f"{HEADER_KEY_OF_REFERENCE.column_name!r} "
        f"[common/slinvoiceMT.cbl:L297] disagrees with its DDL primary key "
        f"{HEADER_KEY_COLUMN!r} [mysql/ACASDB.sql:L876]"
    )
if LINE_KEY_OF_REFERENCE.column_name != LINES_KEY_COLUMN:  # pragma: no cover
    raise ImportError(
        "SAINV-LINES-REC key of reference "
        f"{LINE_KEY_OF_REFERENCE.column_name!r} "
        f"[common/slinvoiceMT.cbl:L301] disagrees with its DDL primary key "
        f"{LINES_KEY_COLUMN!r} [mysql/ACASDB.sql:L825]"
    )



# ---------------------------------------------------------------------------
# The entity-to-table spine, published for traceability (R-5)
# ---------------------------------------------------------------------------
# AAP section 0.2.1.1's spine table for this row, resolved to live values rather
# than restated in prose, so a reader - or a traceability generator - can obtain the
# mapping from the module itself:
#
#     entity facade  Invoice   ->  handler acas016  ->  bridge slinvoiceMT
#         ->  SAINVOICE-REC (header, 31 columns, PK SINVOICE-KEY)
#         ->  SAINV-LINES-REC (lines,  14 columns, PK IL-LINE-KEY)
#
# The four identity constants come from acas_posting.records.sales_invoice, which is
# the record layer's own declaration of them, so there is exactly ONE place in the
# package where each string literal lives.  ENTITY_FACADE is the name the entity-named
# facade vocabulary uses (`Invoice-Read-Next`, `Invoice-Write`, ... ,
# `Invoice-Delete-All` [copybooks/Proc-ACAS-FH-Calls.cob:L911]); HANDLER is the name
# the handler-named vocabulary uses (`acas016-Read-Next`, ...).  AAP section 0.3.3
# requires both to resolve to one implementation, and dal/facade.py aliases them onto
# the functions this module publishes.
SPINE: Final[Mapping[str, object]] = MappingProxyType(
    {
        "entity_facade": ENTITY_FACADE,  # 'Invoice'
        "handler": HANDLER,  # 'acas016'   [common/acas016.cbl]
        "bridge": BRIDGE,  # 'common/slinvoiceMT.cbl'
        "tables": (HEADER_TABLE, LINES_TABLE),
        "primary_keys": MappingProxyType(
            {HEADER_TABLE: HEADER_KEY_COLUMN, LINES_TABLE: LINES_KEY_COLUMN}
        ),
        "keys_of_reference": KEYS_OF_REFERENCE,
        # The handler's own extra function code, and the ONLY one it has - the AAP
        # section 0.4.1.5 correction recorded in this module's docstring.
        "extra_function_codes": (int(FileFunction.READ_NEXT_HEADER),),
    }
)

_HEADER_SLOT: Final[CursorSlot] = HEADER_KEY_OF_REFERENCE.cursor_slot
_LINE_SLOT: Final[CursorSlot] = LINE_KEY_OF_REFERENCE.cursor_slot

# ba040-Process-Read-Next opens the sequential walk with a low key rather than a
# caller-supplied one.  [common/slinvoiceMT.cbl:L646-L647], verbatim:
#     '` >= "'  ...  '0000000000'
_SEQUENTIAL_LOW_KEY: Final[str] = "0000000000"
_SEQUENTIAL_RELATION: Final[str] = ">="

# The six signed fields the bridge narrows to unsigned host variables.  Sourced
# from the generated dictionary rather than transcribed: every one of these
# carries drift.signedness True, anomaly_refs ('A-11',) and ambiguity_refs
# ('Q-3',).  See the module docstring for why this is SIX and not the agent
# prompt's seven.
SIGN_LOSS_KEYS: Final[tuple[str, ...]] = (
    f"{HEADER_TABLE}.IH-DAT",
    f"{HEADER_TABLE}.IH-DEDUCT-DAYS",
    f"{HEADER_TABLE}.IH-DAYS",
    f"{HEADER_TABLE}.IH-CR",
    f"{HEADER_TABLE}.IH-LINES",
    f"{LINES_TABLE}.IL-QTY",
)


# ---------------------------------------------------------------------------
# Column metadata, GENERATED from the data dictionary (rule R-5)
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class ColumnBinding:
    """One column of one table, with everything needed to bind it and cite it.

    Rule R-5 requires every field to map to a data-dictionary entry, and AAP
    section 0.8.1 makes the ordering a directive: *"Data dictionary first. ...
    every Python field definition cites its entry. This ordering is a directive,
    not a preference - it is what prevents fields being transcribed by eye."*
    Nothing in this class is hand-written; every attribute is read out of
    ``data_dictionary/acas_posting_dictionary.json`` at import time.
    """

    #: The dictionary key, e.g. ``SAINVOICE-REC.IH-LINES``.
    dictionary_key: str
    #: ``loader.cite(dictionary_key)`` - copybook, bridge and column locators.
    citation: str
    #: MySQL column name, unquoted.
    column_name: str
    #: MySQL column name already wrapped by :func:`quote_identifier`.  Every
    #: identifier in this schema contains a hyphen, so an unquoted name is a
    #: syntax error, not merely bad style.
    quoted_column_name: str
    #: 1-based ordinal in the frozen ``CREATE TABLE``.
    ordinal: int
    #: Bridge host-variable name, e.g. ``HV-IH-LINES`` / ``HV1-IL-QTY``.
    host_variable: str
    #: ``HV`` for the header group, ``HV1`` for the lines group
    #: [common/slinvoiceMT.cbl:L383-L384].
    host_variable_suffix: str
    #: Python storage class: ``"STR"``, ``"INT"``, ``"DECIMAL"`` or ``"NONE"``
    #: (group items).  Never a float - rule R-2.
    storage: str
    #: Declared scale of the column; ``0`` for integers and characters.
    scale: int
    #: Declared character length, for the space padding a ``char(n)`` needs.
    character_length: int
    #: Total declared digits of the host variable - the receiving field width a
    #: COBOL ``MOVE`` truncates high-order digits to.
    host_variable_digits: int
    #: Integer digits of the host variable, i.e. digits left of the ``V``.
    host_variable_integer_digits: int
    #: ``True`` when the column is ``unsigned``.
    column_unsigned: bool
    #: ``True`` when the copybook field is signed - so
    #: ``signed_source and column_unsigned`` is the narrowing.
    signed_source: bool
    #: ``True`` when this field loses its sign at the bridge (one of the six).
    sign_narrowed: bool
    #: The bridge statement that loads this host variable from the record.
    load_source: str | None
    #: The bridge statement that unloads it back, or ``None`` when there is
    #: none - which is the whole of N-il-invoice-never-unloaded and
    #: N-header-key-not-unloaded.
    unload_source: str | None

    @property
    def unloaded(self) -> bool:
        """Whether the bridge ever copies this host variable back to the record."""
        return self.unload_source is not None


def _column_bindings(table: str) -> tuple[ColumnBinding, ...]:
    """Build the binding tuple for ``table`` in COLUMN-ORDINAL order.

    ``loader.entries_for_table`` yields entries in the frozen ``CREATE TABLE``
    ordinal order, which is the order every generated ``INSERT`` and ``UPDATE``
    in this bridge names its columns - verified against ``bb200-Insert``
    [common/slinvoiceMT.cbl:L1543-L1946], ``bb300-Update`` [:L1949-L2356],
    ``bc200-Insert-rg1`` [:L2849-L3039] and ``bc300-Update-rg1`` [:L3042-L3236].

    Determinism (rule R-6): the dictionary is a committed artefact and the
    ordinal is a fixed integer, so this tuple is byte-identical between
    processes.  Nothing here reads a clock, a random source or the environment.
    """
    bindings: list[ColumnBinding] = []
    for entry in loader.entries_for_table(table):
        column = loader.column_for(entry.key)
        host_variable = loader.host_variable_for(entry.key)
        copybook_field = loader.copybook_field_for(entry.key)
        if column is None or host_variable is None:  # pragma: no cover - guard
            msg = (
                f"dictionary entry {entry.key!r} is missing its column or host "
                "variable; the generated dictionary is incomplete for "
                f"{table!r}"
            )
            raise loader.DictionaryLookupError(msg)
        drift = loader.drift_for(entry.key)
        bindings.append(
            ColumnBinding(
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                column_name=column.name,
                quoted_column_name=quote_identifier(column.name),
                ordinal=column.ordinal,
                host_variable=host_variable.name,
                host_variable_suffix=host_variable.hv_group_suffix,
                storage=str(entry.cobol_python_storage.value),
                scale=int(column.scale or 0),
                character_length=int(host_variable.character_length or 0),
                host_variable_digits=int(host_variable.digits or 0),
                host_variable_integer_digits=int(host_variable.integer_digits or 0),
                column_unsigned=bool(column.unsigned),
                signed_source=bool(
                    copybook_field.signed if copybook_field is not None else False
                ),
                sign_narrowed=bool(drift.signedness),
                load_source=host_variable.load_source,
                unload_source=host_variable.unload_source,
            )
        )
    return tuple(bindings)


def _load_sequence(bindings: Iterable[ColumnBinding]) -> tuple[ColumnBinding, ...]:
    """Order ``bindings`` by the bridge's LOAD-PARAGRAPH statement order.

    N-triple-order-mismatch.  This is deliberately a SECOND, independent
    ordering, never derived from :func:`_column_bindings`.  For the header the
    two differ at ``IH-LINES``: the load moves it at
    [common/slinvoiceMT.cbl:L1479], in copybook position 24, while the
    host-variable group declares it at [:L419] and the column list carries it at
    ordinal 29.  For the lines they differ at ``IL-INVOICE`` / ``IL-LINE``,
    which the load inverts at [:L2790-L2791].

    Entries the bridge never loads sort last; there are none today, but the
    fallback keeps the function total rather than raising on a partial
    dictionary.
    """

    def statement_line(binding: ColumnBinding) -> tuple[int, int]:
        source = binding.load_source
        if source is None:
            return (1, binding.ordinal)
        _, _, line_token = source.rpartition(":L")
        return (0, int(line_token)) if line_token.isdigit() else (1, binding.ordinal)

    return tuple(sorted(bindings, key=statement_line))


#: The 31 columns of ``SAINVOICE-REC`` in ordinal order - the order every
#: generated statement names them in.
HEADER_COLUMNS: Final[tuple[ColumnBinding, ...]] = _column_bindings(HEADER_TABLE)

#: The 14 columns of ``SAINV-LINES-REC`` in ordinal order.
LINE_COLUMNS: Final[tuple[ColumnBinding, ...]] = _column_bindings(LINES_TABLE)

#: ``bb000-HV-Load``'s move order [common/slinvoiceMT.cbl:L1455-L1486].
HEADER_LOAD_SEQUENCE: Final[tuple[ColumnBinding, ...]] = _load_sequence(HEADER_COLUMNS)

#: ``bc000-HV-Load-rg1``'s move order [common/slinvoiceMT.cbl:L2789-L2802],
#: which puts LINE before INVOICE.
LINE_LOAD_SEQUENCE: Final[tuple[ColumnBinding, ...]] = _load_sequence(LINE_COLUMNS)

_HEADER_BY_COLUMN: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.column_name: binding for binding in HEADER_COLUMNS}
)
_LINE_BY_COLUMN: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.column_name: binding for binding in LINE_COLUMNS}
)


# ---------------------------------------------------------------------------
# Storage coercion - the bridge's MOVE semantics, reproduced field by field
# ---------------------------------------------------------------------------
def narrow_signed_host_variable(binding: ColumnBinding, value: int) -> int:
    """Reproduce ``MOVE <signed source> TO <unsigned host variable>``.

    N-signloss, AAP anomaly #11 family.  Six of this bridge's 45 fields are
    declared SIGNED in the copybook and UNSIGNED in both the host variable and
    the column, so **the sign is lost at the bridge, before any SQL executes**.
    AAP section 0.6.2, verbatim: *"the Python data-access layer must reproduce
    the bridge's conversion, not merely write the computed value and let MySQL
    complain."*

    The six, each cited at all three layers:

    * ``IH-DAT`` - ``sih-date binary-long`` [copybooks/slwsinv.cob:L26] ->
      ``HV-IH-DAT PIC 9(10) COMP`` [common/slinvoiceMT.cbl:L395] ->
      ``IH-DAT int(8) unsigned`` [mysql/ACASDB.sql:L849].  Also renamed
      ``DATE`` -> ``DAT``; see N-ih-dat-rename.
    * ``IH-DEDUCT-DAYS`` - ``binary-char`` [copybooks/slwsinv.cob:L62] ->
      ``PIC 9(03) COMP`` [common/slinvoiceMT.cbl:L414] ->
      ``tinyint(3) unsigned`` [mysql/ACASDB.sql:L868].
    * ``IH-DAYS`` - ``binary-char`` [copybooks/slwsinv.cob:L65] ->
      ``PIC 9(03) COMP`` [common/slinvoiceMT.cbl:L417] ->
      ``tinyint(3) unsigned`` [mysql/ACASDB.sql:L871].
    * ``IH-CR`` - ``binary-long`` [copybooks/slwsinv.cob:L66] ->
      ``PIC 9(10) COMP`` [common/slinvoiceMT.cbl:L418] ->
      ``int(8) unsigned`` [mysql/ACASDB.sql:L872].
    * ``IH-LINES`` - ``binary-char`` [copybooks/slwsinv.cob:L61] ->
      ``PIC 9(03) COMP`` [common/slinvoiceMT.cbl:L419] ->
      ``tinyint(2) unsigned`` [mysql/ACASDB.sql:L873].
    * ``IL-QTY`` - ``binary-short`` [copybooks/slwsinv.cob:L87], restated as
      ``WS-Sil-Qty binary-short`` [common/slinvoiceMT.cbl:L367] ->
      ``HV1-IL-QTY PIC 9(05) COMP`` [:L432] ->
      ``smallint(6) unsigned`` [mysql/ACASDB.sql:L815].

    The conversion is the plain COBOL one: an unsigned receiver holds the
    MAGNITUDE, and a ``MOVE`` to a shorter numeric field truncates HIGH-ORDER
    digits.  Nothing raises, nothing clamps to a boundary and nothing is
    "corrected" - a negative simply arrives positive, which is the defect being
    preserved.

    The magnitude is taken as ``-value if value < 0 else value`` rather than with
    the built-in, because ``abs()`` is one of the tokens rule R-2's audit forbids
    outright in this layer; the expression is exact integer arithmetic either
    way.

    Q-3 (AAP section 0.6.8) remains open: the EXACT value an unsigned column
    receives depends on the conversion the bridge's C interface performs and must
    be measured against the compiled oracle rather than assumed.  The dictionary
    marks all six with ``ambiguity_refs = ('Q-3',)`` for exactly this reason, and
    the resolution belongs in ``docs/migration/ambiguity-resolutions.md``.
    """
    magnitude = -value if value < 0 else value
    digits = binding.host_variable_digits
    if digits > 0:
        # COBOL truncates HIGH-order digits on a MOVE into a shorter numeric
        # field.  For these six the source can never overflow the receiver, so
        # this is a faithful no-op today; it is written out because the rule is
        # the receiving field's, not the sending field's.
        magnitude %= 10**digits
    return magnitude


def _initial_value(binding: ColumnBinding) -> str | int | Decimal:
    """The value ``INITIALIZE`` leaves in a host variable - zero or spaces.

    ``initialize TD-SAINVOICE-REC.`` [common/slinvoiceMT.cbl:L1453] and
    ``initialize TD-SAINV-LINES-REC.`` [common/slinvoiceMT.cbl:L2787] are the
    FIRST statements of their load paragraphs, so a field the load never touches
    still reaches SQL as zero or space - never ``NULL``.  AAP section 0.6.2,
    verbatim: *"This is why every column in the schema can be declared `NOT NULL`
    and why the Python layer must default rather than omit."*
    """
    if binding.storage == "DECIMAL":
        return Decimal(0).quantize(Decimal(1).scaleb(-binding.scale))
    if binding.storage == "INT":
        return 0
    return " " * binding.character_length


def _coerce_for_bind(binding: ColumnBinding, value: object) -> str | int | Decimal:
    """Coerce ``value`` into exactly what this column's host variable would hold.

    This is the ONE place a value crosses from the record area into the host
    variable, so it is the one place the drift is applied.  Three rules, one per
    storage class, and no fourth - there is no floating-point path at all
    (rule R-2).

    ``STR``  Truncate or space-pad to the host variable's declared ``X(n)``
             width - what the host variable HOLDS.  The right-trim the statement
             applies is a separate, later step; see :func:`_render_for_bind`.

    ``INT``  Integer, with the six narrowings applied through
             :func:`narrow_signed_host_variable`.  Never a float, so the integer
             truncation the moving averages depend on elsewhere in the migration
             stays exact here too.

    ``DECIMAL``
             ``Decimal`` quantized DOWN to the column's declared scale.
             Truncation is the default because COBOL truncates on store unless
             ``ROUNDED`` is written, and none of this bridge's 45 fields is one
             of the migration's five ``ROUNDED`` sites - all five live in
             ``acas_posting/programs/``.  Quantizing here also discharges the
             obligation :mod:`acas_posting.dal.connection` places on its callers,
             since the server would round HALF-UP where COBOL truncates.
    """
    if binding.storage in {"STR", "NONE"}:
        text = "" if value is None else str(value)
        width = binding.character_length or len(text)
        return text[:width].ljust(width)

    if binding.storage == "INT":
        if isinstance(value, bool):  # pragma: no cover - defensive
            msg = (
                f"{binding.dictionary_key}: a boolean is not a COBOL numeric; "
                "the record layer must supply an int"
            )
            raise TypeError(msg)
        number = int(value) if value is not None else 0
        if binding.sign_narrowed:
            return narrow_signed_host_variable(binding, number)
        return number

    if binding.storage == "DECIMAL":
        amount = _as_decimal(binding, value)
        quantum = Decimal(1).scaleb(-binding.scale)
        # ROUND_DOWN is truncation toward zero, which is what a COBOL store
        # without ROUNDED does.  See AAP section 0.1.1 on the five ROUNDED sites.
        quantized = amount.quantize(quantum, rounding=ROUND_DOWN)
        if binding.sign_narrowed and quantized < 0:
            # No live case today - all six narrowings are integers - but the rule
            # belongs with the drift, not with the storage class.
            return -quantized
        return quantized

    msg = (  # pragma: no cover - the dictionary has only four storage classes
        f"{binding.dictionary_key}: unsupported storage class "
        f"{binding.storage!r}"
    )
    raise loader.DictionaryNumericPolicyError(msg)


@dataclass(frozen=True, slots=True)
class EditMaskWindow:
    """One numeric column's FIXED substring of ``WS-MYSQL-EDIT``.

    The bridge never binds a numeric host variable.  It ``MOVE``s the host
    variable into the single shared edit field ``01 WS-MYSQL-EDIT PIC
    -Z(18)9.9(9)`` [common/slinvoiceMT.cbl:L271] and then ``STRING``s a
    hard-coded substring of that field into the statement text.  This value
    object is that substring, transcribed from the render site named in
    ``render_locator``.

    ``integer_start`` / ``integer_length``
        The integer window, always wrapped in ``FUNCTION TRIM (...)``.
    ``decimal_start`` / ``decimal_length``
        The fraction window for a scaled column, ``(22:02)`` throughout, and
        ``0``-length for an unscaled one.  Verified to carry NO ``FUNCTION
        TRIM``: ``grep -c 'TRIM *( *WS-MYSQL-EDIT(22' common/slinvoiceMT.cbl``
        returns 0, so those two characters reach the statement raw.
    """

    host_variable: str
    integer_start: int
    integer_length: int
    decimal_start: int
    decimal_length: int
    render_locator: str


# --------------------------------------------------------------------------
# N-edit-mask-sign / N-edit-mask-truncation - the two anomalies this mask
# creates.  ARBITRATED AGAINST THE COMPILED ORACLE, not reasoned about.
#
# `01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)` [common/slinvoiceMT.cbl:L271] lays out
# 30 character positions:
#
#     position  1        the sign, a FIXED insertion `-`  ('-' or ' ')
#     positions 2..19    Z(18), leading zeros suppressed to spaces
#     position  20       9, the units digit - ALWAYS a digit
#     position  21       the '.'
#     positions 22..30   9(9), the fraction, always nine digits
#
# Every one of the 26 render windows below starts at 11, 14, 16, 18, 19 or 22.
# NOT ONE INCLUDES POSITION 1, so the sign is STRUCTURALLY UNREACHABLE for
# every numeric column of both tables.  Two consequences, both reproduced:
#
#   N-edit-mask-sign        A negative host variable is stored POSITIVE.  This
#                           hits the eleven signed `decimal(9,2)` money columns
#                           whose declarations are signed at all three layers -
#                           so the AAP section 0.4.1.5 brief's claim that "the
#                           signed money is genuinely clean here" is right about
#                           the DECLARATIONS and wrong about the BEHAVIOUR.
#   N-edit-mask-truncation  The window is narrower than the 19 integer
#                           positions, so a value with more integer digits than
#                           the window is silently HIGH-ORDER truncated.
#
# ORACLE EVIDENCE.  `common/slinvoiceMT.cbl` does not reference the missing
# `copybooks/ACAS-SQLstate-error-list.cob` (grep count 0), so - contrary to the
# environment's blanket note about blocked bridges - THIS bridge builds.  Built
# with `cobc -m -I copybooks common/slinvoiceMT.cbl cobmysqlapi.o
# -L/usr/local/mysql/lib -lmysqlclient` (exit 0, zero warnings) and driven
# against the frozen schema, the compiled bridge stored:
#
#     sih-net        -1234.56  ->  `IH-NET`         = +1234.56   <- sign DROPPED
#     sih-date             -5  ->  `IH-DAT`         =        5
#     sih-cr               -9  ->  `IH-CR`          =        9
#
# The `IH-DAT`/`IH-CR`-style results also settle Q-3 (AAP section 0.6.8): the
# unsigned receiver holds the MAGNITUDE, which is what
# `narrow_signed_host_variable` already did.  That step is UNCHANGED - it models
# the `MOVE` into the unsigned host variable, which happens first and is a
# separate, independently confirmed conversion.  Rule R-4 governs the outcome:
# *"A defect reproduced is correct; a defect fixed is a failure."*
# --------------------------------------------------------------------------
MYSQL_EDIT_PICTURE: Final[str] = "-Z(18)9.9(9)"
MYSQL_EDIT_LOCATOR: Final[str] = "[common/slinvoiceMT.cbl:L271]"
MYSQL_EDIT_WIDTH: Final[int] = 30
MYSQL_EDIT_SIGN_POSITION: Final[int] = 1
MYSQL_EDIT_INTEGER_POSITIONS: Final[int] = 19
MYSQL_EDIT_UNITS_POSITION: Final[int] = 20
MYSQL_EDIT_POINT_POSITION: Final[int] = 21
MYSQL_EDIT_FRACTION_POSITION: Final[int] = 22
MYSQL_EDIT_FRACTION_DIGITS: Final[int] = 9

MYSQL_EDIT_WINDOWS: Final[Mapping[str, EditMaskWindow]] = MappingProxyType(
    {
        # -- SAINVOICE-REC, bb200-Insert / bb300-Update ---------------------
        "IH-INVOICE": EditMaskWindow(
            "HV-IH-INVOICE", 11, 10, 0, 0, "[common/slinvoiceMT.cbl:L1569]"
        ),
        "IH-TEST": EditMaskWindow(
            "HV-IH-TEST", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1581]"
        ),
        "IH-DAT": EditMaskWindow(
            "HV-IH-DAT", 11, 10, 0, 0, "[common/slinvoiceMT.cbl:L1602]"
        ),
        "IH-TYPE": EditMaskWindow(
            "HV-IH-TYPE", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1623]"
        ),
        "IH-P-C": EditMaskWindow(
            "HV-IH-P-C", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1653]"
        ),
        "IH-NET": EditMaskWindow(
            "HV-IH-NET", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1670]"
        ),
        "IH-EXTRA": EditMaskWindow(
            "HV-IH-EXTRA", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1687]"
        ),
        "IH-CARRIAGE": EditMaskWindow(
            "HV-IH-CARRIAGE", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1704]"
        ),
        "IH-VAT": EditMaskWindow(
            "HV-IH-VAT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1721]"
        ),
        "IH-DISCOUNT": EditMaskWindow(
            "HV-IH-DISCOUNT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1738]"
        ),
        "IH-E-VAT": EditMaskWindow(
            "HV-IH-E-VAT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1755]"
        ),
        "IH-C-VAT": EditMaskWindow(
            "HV-IH-C-VAT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1772]"
        ),
        "IH-DEDUCT-DAYS": EditMaskWindow(
            "HV-IH-DEDUCT-DAYS", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1843]"
        ),
        "IH-DEDUCT-AMT": EditMaskWindow(
            "HV-IH-DEDUCT-AMT", 18, 3, 22, 2, "[common/slinvoiceMT.cbl:L1855]"
        ),
        "IH-DEDUCT-VAT": EditMaskWindow(
            "HV-IH-DEDUCT-VAT", 18, 3, 22, 2, "[common/slinvoiceMT.cbl:L1872]"
        ),
        "IH-DAYS": EditMaskWindow(
            "HV-IH-DAYS", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1889]"
        ),
        "IH-CR": EditMaskWindow(
            "HV-IH-CR", 11, 10, 0, 0, "[common/slinvoiceMT.cbl:L1901]"
        ),
        "IH-LINES": EditMaskWindow(
            "HV-IH-LINES", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1913]"
        ),
        # -- SAINV-LINES-REC, bc200-Insert-rg1 / bc300-Update-rg1 -----------
        "IL-INVOICE": EditMaskWindow(
            "HV1-IL-INVOICE", 11, 10, 0, 0, "[common/slinvoiceMT.cbl:L2875]"
        ),
        "IL-LINE": EditMaskWindow(
            "HV1-IL-LINE", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L2887]"
        ),
        "IL-QTY": EditMaskWindow(
            "HV1-IL-QTY", 16, 5, 0, 0, "[common/slinvoiceMT.cbl:L2917]"
        ),
        "IL-NET": EditMaskWindow(
            "HV1-IL-NET", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L2947]"
        ),
        "IL-UNIT": EditMaskWindow(
            "HV1-IL-UNIT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L2964]"
        ),
        "IL-DISCOUNT": EditMaskWindow(
            "HV1-IL-DISCOUNT", 19, 2, 22, 2, "[common/slinvoiceMT.cbl:L2981]"
        ),
        "IL-VAT": EditMaskWindow(
            "HV1-IL-VAT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L2998]"
        ),
        "IL-VAT-CODE": EditMaskWindow(
            "HV1-IL-VAT-CODE", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L3015]"
        ),
    }
)


def ws_mysql_edit(value: int | Decimal) -> str:
    """Return the 30 characters ``WS-MYSQL-EDIT`` holds after ``MOVE value``.

    Models ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)``
    [common/slinvoiceMT.cbl:L271] exactly, and is the only place the mask's
    layout is encoded.  The result is always ``MYSQL_EDIT_WIDTH`` characters so
    that a window can be taken by position with no bounds arithmetic.

    Three COBOL behaviours are reproduced deliberately:

    * The leading ``-`` is FIXED insertion, so position 1 is ``'-'`` for a
      negative value and ``' '`` for a positive one.  No caller reads it.
    * ``Z(18)`` suppresses leading zeros to spaces while the trailing ``9`` at
      ``MYSQL_EDIT_UNITS_POSITION`` always shows a digit, so a zero value
      renders as 18 spaces then ``'0'``.  Right-justifying the digits of an
      exact ``Decimal`` - which never carries a leading zero - in 19 positions
      is precisely that result.
    * A ``MOVE`` into a 19-integer-digit receiver truncates HIGH-ORDER excess,
      so more than 19 integer digits lose the leftmost ones.

    Rule R-2 holds throughout: the value is decomposed by exact ``Decimal``
    string formatting, never by ``float`` arithmetic.
    """
    exact = value if isinstance(value, Decimal) else Decimal(int(value))
    negative = exact < 0
    magnitude = -exact if negative else exact
    magnitude = magnitude.quantize(
        Decimal(1).scaleb(-MYSQL_EDIT_FRACTION_DIGITS), rounding=ROUND_DOWN
    )

    integer_digits, _, fraction_digits = f"{magnitude:f}".partition(".")
    # A MOVE into 19 integer positions drops the high-order excess.
    integer_digits = integer_digits[-MYSQL_EDIT_INTEGER_POSITIONS:]

    return (
        ("-" if negative else " ")
        + integer_digits.rjust(MYSQL_EDIT_INTEGER_POSITIONS)
        + "."
        + fraction_digits.ljust(MYSQL_EDIT_FRACTION_DIGITS, "0")
    )


def render_through_mysql_edit(
    binding: ColumnBinding, held: int | Decimal
) -> int | Decimal:
    """Return the value the bridge's ``STRING`` of the mask would put in the SQL.

    This is the second and final conversion a numeric column undergoes, after
    :func:`narrow_signed_host_variable` has modelled the ``MOVE`` into the host
    variable.  It reproduces N-edit-mask-sign and N-edit-mask-truncation for
    every numeric column of both tables; see the block comment above
    :data:`MYSQL_EDIT_WINDOWS` for the mask layout and the oracle evidence.

    The integer window is stripped to model ``FUNCTION TRIM (...)``; the
    fraction window is taken raw because no render site trims it.  The bound
    value - never an interpolated literal - is the exact number the rendered
    text denotes, so
    :func:`acas_posting.dal.connection.execute_statement` keeps binding
    parameters and the layer keeps its injection-free posture.
    """
    window = MYSQL_EDIT_WINDOWS[binding.column_name]
    mask = ws_mysql_edit(held)

    start = window.integer_start - 1
    integer_text = mask[start : start + window.integer_length].strip()
    if window.decimal_length == 0:
        return int(integer_text)

    fraction_start = window.decimal_start - 1
    fraction_text = mask[fraction_start : fraction_start + window.decimal_length]
    return Decimal(f"{integer_text}.{fraction_text}")


# The window census above is TRANSCRIBED from the 26 render sites so that each
# carries its own locator (rule R-4).  It is also DERIVABLE, because the
# translator emits the window from the host variable's picture: a host variable
# with N integer digits occupies mask positions 21-N .. 20.  Cross-checking the
# transcription against the dictionary catches a mis-typed window at import
# rather than in a posted figure, and proves the two sources agree - the same
# belt-and-braces the TABLE_PRIMARY_KEYS check applies to the key table.
for _mask_table in (HEADER_TABLE, LINES_TABLE):
    for _mask_binding in _column_bindings(_mask_table):
        _numeric = _mask_binding.storage in {"INT", "DECIMAL"}
        _window = MYSQL_EDIT_WINDOWS.get(_mask_binding.column_name)
        if _numeric != (_window is not None):
            raise ImportError(
                f"{_mask_binding.dictionary_key}: storage "
                f"{_mask_binding.storage!r} and MYSQL_EDIT_WINDOWS disagree on "
                f"whether {_mask_binding.column_name!r} is rendered through "
                f"WS-MYSQL-EDIT {MYSQL_EDIT_LOCATOR}"
            )
        if _window is None:
            continue
        _expected_start = (
            MYSQL_EDIT_POINT_POSITION - _mask_binding.host_variable_integer_digits
        )
        if (
            _window.integer_start != _expected_start
            or _window.integer_length != _mask_binding.host_variable_integer_digits
        ):
            raise ImportError(
                f"{_mask_binding.dictionary_key}: window "
                f"({_window.integer_start}:{_window.integer_length}) from "
                f"{_window.render_locator} does not match the "
                f"{_mask_binding.host_variable_integer_digits} integer digits of "
                f"{_window.host_variable} - expected "
                f"({_expected_start}:{_mask_binding.host_variable_integer_digits})"
            )
        if (
            _window.integer_start + _window.integer_length - 1
            != MYSQL_EDIT_UNITS_POSITION
        ):
            raise ImportError(
                f"{_mask_binding.dictionary_key}: window from "
                f"{_window.render_locator} does not end at the units position "
                f"{MYSQL_EDIT_UNITS_POSITION} of {MYSQL_EDIT_PICTURE}"
            )
        if _window.decimal_length not in {0, _mask_binding.scale}:
            raise ImportError(
                f"{_mask_binding.dictionary_key}: fraction window "
                f"({_window.decimal_start}:{_window.decimal_length}) from "
                f"{_window.render_locator} does not match scale "
                f"{_mask_binding.scale}"
            )
del _mask_table, _mask_binding, _numeric, _window, _expected_start


def _render_for_bind(
    binding: ColumnBinding, held: str | int | Decimal
) -> str | int | Decimal:
    """Render a held host variable exactly as the generated statement does.

    The bridge builds its statement text one host variable at a time, and the
    rendering is per storage class.  Every character host variable goes through
    ``FUNCTION TRIM (HV-x,TRAILING)`` - verified at
    [common/slinvoiceMT.cbl:L1560-L1563] for ``HV-SINVOICE-KEY`` and at every
    other character column of both tables - so the trailing spaces
    ``INITIALIZE`` and the ``MOVE`` padding put there do NOT reach the database.
    Reproducing that here rather than in :func:`_coerce_for_bind` keeps the two
    COBOL steps separate: what the field HOLDS, then what the statement SAYS.

    Numeric host variables never reach the statement directly.  Each is
    ``MOVE``d into ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)``
    [common/slinvoiceMT.cbl:L271] and a FIXED substring of that mask is
    ``STRING``ed into the text, so the rendering - not the host variable - is
    what the database receives.  :func:`render_through_mysql_edit` performs it
    from the per-column census in :data:`MYSQL_EDIT_WINDOWS`.

    Q-edit-mask-sign and Q-edit-mask-truncation (AAP section 0.6.8) are
    ARBITRATED, not deferred.  An earlier revision of this function bound the
    held value unchanged and recorded the divergence as an open question on the
    stated premise that the oracle could not be asked, because
    ``copybooks/ACAS-SQLstate-error-list.cob`` is missing from the frozen
    archive.  **That premise was false for this bridge**: ``slinvoiceMT`` does
    not reference that copybook at all, so it compiles.  The compiled bridge was
    built and driven against the frozen schema, and it stores ``+1234.56`` for a
    ``sih-net`` of ``-1234.56`` - the sign is dropped because no window reaches
    mask position 1.  Rule R-6 makes that observation the specification and rule
    R-4 forbids improving on it, so the rendering is reproduced here and the
    three reasons the earlier revision gave for binding the value are
    superseded.  In particular its claim that the drop was "an artefact of the
    DISPLAY mask, downstream of the conversion" had the direction backwards: for
    this bridge the display mask **is** the conversion the statement uses.

    What did NOT change is :func:`narrow_signed_host_variable`.  That models the
    ``MOVE`` into an unsigned host variable, which happens first and which the
    same oracle run confirmed independently (``-5`` stored as ``5``).  The two
    conversions compose: narrow on the way into the host variable, then render
    through the mask on the way into the statement.

    Binding stays parameterised.  The rendered *value* is bound, never an
    interpolated literal, so
    :func:`acas_posting.dal.connection.execute_statement` keeps its parameter
    binding and the layer keeps its injection-free posture.  The resolution is
    recorded in ``docs/migration/ambiguity-resolutions.md`` and the two
    anomalies in ``docs/migration/anomaly-log.md``.
    """
    if binding.storage in {"STR", "NONE"}:
        return str(held).rstrip()
    return render_through_mysql_edit(binding, held)


def _as_decimal(binding: ColumnBinding, value: object) -> Decimal:
    """Return ``value`` as a :class:`~decimal.Decimal`, refusing binary floats.

    Rule R-2, verbatim: *"No accounting value may pass through a
    binary floating-point type at any point - not in computation, not in storage,
    not in transport."*  A ``Decimal`` built from a binary float would silently
    carry that float's representation error into an accounting column, so the
    type is rejected outright rather than converted.
    """
    if value is None:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    msg = (
        f"{binding.dictionary_key}: {type(value).__name__} is not an exact "
        "numeric; accounting values must arrive as Decimal, int or str "
        "(rule R-2 forbids binary floating point in this layer)"
    )
    raise TypeError(msg)


def _truncate_move(text: str, width: int) -> str:
    """``MOVE`` a literal into a fixed ``PIC X(width)`` field, COBOL-style.

    Used for ``WS-File-Key`` (``pic x(64)`` [copybooks/wsfnctn.cob:L52]) and
    ``WS-Log-Where`` (``pic x(231)`` [copybooks/wsfnctn.cob:L53]).  A COBOL
    ``MOVE`` into a shorter alphanumeric field truncates on the RIGHT and pads
    with spaces, and every ``STRING ... INTO WS-File-Key`` in the handler and the
    bridge inherits that.  The trailing spaces are dropped on the way out because
    they are invisible in every consumer and would otherwise make two logically
    equal log lines compare unequal.
    """
    return text[:width].rstrip()


# ---------------------------------------------------------------------------
# The two host-variable groups
# ---------------------------------------------------------------------------
# [common/slinvoiceMT.cbl:L381-L385], verbatim:
#     *> /MYSQL VAR\
#     *>       ACASDB
#     *>       TABLE=SAINVOICE-REC,HV
#     *>       TABLE=SAINV-LINES-REC,HV1
#
# The twin TABLE= directives, and the HV / HV1 prefixes that keep them apart, are
# the only two-table directive form in the frozen tree besides plinvoiceMT.  The
# generated groups are 01 TD-SAINVOICE-REC [:L390-L421] and
# 01 TD-SAINV-LINES-REC [:L426-L440], each preceded by its USAGE POINTER
# [:L389], [:L425] which the Python layer has no counterpart for and which is
# recorded as a representation-only omission (rule R-5).
class _HostVariableGroup:
    """Shared behaviour of the two ``TD-`` groups: initialise, set, read, bind.

    Deliberately NOT a dataclass of 31 or 14 named attributes.  Rule R-5 makes
    the generated dictionary the single source of truth for field metadata
    ("**Data dictionary first** ... it is what prevents fields being transcribed
    by eye"), so the group is keyed by the column names the dictionary publishes
    and every coercion is driven by the matching :class:`ColumnBinding`.  Hand
    transcription of 45 pictures is exactly the error class that directive
    exists to prevent.
    """

    __slots__ = ("_bindings", "_by_column", "_group_name", "_values")

    def __init__(
        self,
        *,
        group_name: str,
        bindings: tuple[ColumnBinding, ...],
        by_column: Mapping[str, ColumnBinding],
    ) -> None:
        self._group_name = group_name
        self._bindings = bindings
        self._by_column = by_column
        self._values: dict[str, str | int | Decimal] = {}
        self.initialize()

    @property
    def group_name(self) -> str:
        """The COBOL group name, e.g. ``TD-SAINVOICE-REC``."""
        return self._group_name

    @property
    def bindings(self) -> tuple[ColumnBinding, ...]:
        """The group's columns in frozen ``CREATE TABLE`` ordinal order."""
        return self._bindings

    def initialize(self) -> None:
        """``INITIALIZE`` the whole group - zero or spaces, never ``NULL``."""
        self._values = {
            binding.column_name: _initial_value(binding) for binding in self._bindings
        }

    def move_in(self, column_name: str, value: object) -> None:
        """``MOVE value TO HV-<column>``, applying this field's drift."""
        binding = self._by_column[column_name]
        self._values[column_name] = _coerce_for_bind(binding, value)

    def __getitem__(self, column_name: str) -> str | int | Decimal:
        """Read a host variable back, as an unload ``MOVE`` would."""
        return self._values[column_name]

    def __contains__(self, column_name: object) -> bool:
        return column_name in self._values

    def as_parameters(self) -> tuple[str | int | Decimal, ...]:
        """Every host variable, in ordinal order, rendered and ready to bind.

        The tuple length always equals the table's column count, because
        :meth:`initialize` seeds every key.  No element is ever ``None``, which
        is the ``NOT NULL`` invariant of AAP section 0.6.2 made mechanical.
        """
        return tuple(
            _render_for_bind(binding, self._values[binding.column_name])
            for binding in self._bindings
        )

    def render_one(self, column_name: str) -> str | int | Decimal:
        """One host variable, rendered exactly as :meth:`as_parameters` renders it.

        Used for the ``WHERE`` value of an UPDATE or DELETE, where the bridge
        binds the SAME field it also SETs - ``bb300-Update`` appends
        ``FUNCTION TRIM (WS-Where (1:J))`` [common/slinvoiceMT.cbl:L2336] over a
        clause built from the key host variable.  Going through the one renderer
        guarantees the WHERE value and the SET value cannot disagree.
        """
        binding = self._by_column[column_name]
        return _render_for_bind(binding, self._values[column_name])

    def snapshot(self) -> Mapping[str, str | int | Decimal]:
        """A read-only view, for assertions and log records."""
        return MappingProxyType(dict(self._values))


class TdSainvoiceRec(_HostVariableGroup):
    """``01 TD-SAINVOICE-REC.`` [common/slinvoiceMT.cbl:L390-L421] - 31 HVs, ``HV`` prefix."""

    def __init__(self) -> None:
        super().__init__(
            group_name="TD-SAINVOICE-REC",
            bindings=HEADER_COLUMNS,
            by_column=_HEADER_BY_COLUMN,
        )


class TdSainvLinesRec(_HostVariableGroup):
    """``01 TD-SAINV-LINES-REC.`` [common/slinvoiceMT.cbl:L426-L440] - 14 HVs, ``HV1`` prefix."""

    def __init__(self) -> None:
        super().__init__(
            group_name="TD-SAINV-LINES-REC",
            bindings=LINE_COLUMNS,
            by_column=_LINE_BY_COLUMN,
        )


# ---------------------------------------------------------------------------
# The record areas
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class WsInvoiceLine:
    """``01 WS-Invoice-Line.`` [common/slinvoiceMT.cbl:L361-L377].

    N-copy-replacing.  The bridge does NOT use the copybook's line layout.
    [common/slinvoiceMT.cbl:L453-L459] copies ``slwsinv.cob`` with four
    replacements, verbatim::

        *>  Using the first record but not the 2nd as it uses occurs 40 but
        *>   to reduce Ram usage get rid of the occurs.

        copy "slwsinv.cob"   replacing SInvoice-Header   by WS-Invoice-Record
                                       leading ==sih-==  by ==WS-Sih-==
                                       ==occurs 40.==    by ==.==
                                       ==sil-==          by ==Un-Used-Sil-==.

    The third replacement DELETES the ``occurs 40`` from ``SInvoice-Bodies``
    [copybooks/slwsinv.cob:L81], collapsing 40 elements to one, and the fourth
    renames every ``sil-`` field ``Un-Used-Sil-`` to announce it is dead.  The
    bridge then declares this record in WORKING-STORAGE - not Linkage - as its
    own staging area, and copies the shared buffer into and out of it explicitly:

    * ``move WS-Invoice-Record to WS-Invoice-Line`` [:L2523] and [:L2726]
    * ``move WS-Invoice-Line to WS-Invoice-Record`` [:L2499] and [:L2842]

    N-back-ordered-dropped.  Field-by-field this record matches
    ``copybooks/slwsinv.cob:L82-L96`` EXCEPT its last line,
    ``[common/slinvoiceMT.cbl:L377]``, verbatim::

        03  filler             pic x.          *> size 80 to here -1 26/7/23 2 match slwsinv

    That bare ``filler`` sits exactly where ``copybooks/slwsinv.cob:L97-L98``
    declares ``sil-Back-Ordered`` - the field added on 03/03/24 to replace the
    old filler, ``*> value space, or B for a BO item.``  So the 2024 feature has
    NO host variable and NO column: ``SAINV-LINES-REC`` has 14 columns and none
    is ``IL-BACK-ORDERED`` [mysql/ACASDB.sql:L809-L826].  It stops dead at the
    bridge.  ``filler_80`` below preserves the byte; nothing propagates it.
    """

    #: ``03  WS-Sil-Key.`` [:L362] - 10 bytes, the SHARED key region.
    ws_sil_invoice: int = 0  # 05 WS-Sil-Invoice pic 9(8).   [:L363]
    ws_sil_line: int = 0  # 05 WS-Sil-Line    pic 99.     [:L364]
    ws_sil_product: str = ""  # 03 pic x(13)  *> +1 17/5/13 [:L365]
    ws_sil_pa: str = ""  # 03 pic xx                      [:L366]
    ws_sil_qty: int = 0  # 03 binary-short - SIGNED        [:L367]
    ws_sil_type: str = ""  # 03 pic x.    *> 28            [:L368]
    ws_sil_description: str = ""  # 03 pic x(32) *> 60      [:L369]
    ws_sil_net: Decimal = Decimal("0.00")  # s9(7)v99 comp-3 [:L370]
    ws_sil_unit: Decimal = Decimal("0.00")  # s9(7)v99 comp-3 [:L371]
    ws_sil_discount: Decimal = Decimal("0.00")  # 99v99 comp   [:L372]
    ws_sil_vat: Decimal = Decimal("0.00")  # s9(7)v99 comp-3   [:L373]
    ws_sil_vat_code: int = 0  # 03 pic 9                    [:L374]
    ws_sil_update: str = ""  # 03 pic x + 88 WS-Sil-Analyised value "Z" [:L375-L376]
    #: The bare ``filler pic x`` [:L377] standing where ``sil-Back-Ordered``
    #: lives in the copybook.  Declared so the omission is visible, never mapped.
    filler_80: str = " "

    @property
    def ws_sil_key(self) -> str:
        """``03 WS-Sil-Key.`` rendered as the 10 characters the PK column holds.

        ``move WS-Sil-Key to HV1-IL-LINE-KEY`` [common/slinvoiceMT.cbl:L2789] is a
        GROUP move, so the column receives the 8-digit invoice followed by the
        2-digit line, zero-filled - exactly the ten bytes
        ``KeyOfReference(offset 1, length 10)`` describes.
        """
        return f"{self.ws_sil_invoice:08d}{self.ws_sil_line:02d}"

    def ws_sil_analyised(self) -> bool:
        """``88 WS-Sil-Analyised value "Z".`` [common/slinvoiceMT.cbl:L376]."""
        return self.ws_sil_update == "Z"


def _new_header_record() -> SInvoiceHeader:
    """``initialize`` a header view - every field zero or space, nothing absent.

    COBOL's ``INITIALIZE`` sets numeric fields to zero and alphanumeric fields to
    spaces across the whole group, which is why every column of ``SAINVOICE-REC``
    can be declared ``NOT NULL`` and why AAP section 0.6.2 requires the Python layer
    to *"default rather than omit"*.  This factory is that rule applied to the record
    layer: it builds the nested groups of
    :class:`acas_posting.records.sales_invoice.SInvoiceHeader` at their COBOL initial
    values, so a buffer the caller never populated behaves like COBOL storage rather
    than like a missing object.

    ``Decimal("0.00")`` rather than ``Decimal(0)`` because the receiving fields are
    ``s9(7)v99`` and the SCALE is part of the field, not a formatting choice (R-2).
    The character widths are the copybook's, so the padding a table dump sees is the
    padding the COBOL wrote.

    ⭐ ``sil_back_ordered`` is NOT part of this record - it belongs to the LINE view -
    but note in passing that ``filler_37`` here IS a real declared filler
    [copybooks/slwsinv.cob:L34], not an omission.
    """
    return SInvoiceHeader(
        sih_prime=SihPrime(
            # sih-invoice 9(8) + sih-test 99  [copybooks/slwsinv.cob:L21-L22]
            ws_invoice_key=WsInvoiceKey(sih_invoice=0, sih_test=0),
            # sih-nos x(6) + sih-check 9      [copybooks/slwsinv.cob:L24-L25]
            sih_customer=SihCustomer(sih_nos=" " * 6, sih_check=0),
            # sih-date binary-long            [copybooks/slwsinv.cob:L26]
            sih_date=0,
            # sih-order x(10)                 [copybooks/slwsinv.cob:L27]
            sih_order=" " * 10,
            # The redefinition of sih-order   [copybooks/slwsinv.cob:L28-L38].
            # None of these four has a host variable or a column - recorded as a
            # deliberate omission (R-5) - but the layout still declares them.
            filler_28=SihOrderView(
                sih_freq=" ",
                sih_repeat=0,
                filler_37=" " * 3,
                sih_last_date=0,
            ),
            # sih-type 9 + sih-ref x(10)      [copybooks/slwsinv.cob:L39-L40]
            sih_type=0,
            sih_ref=" " * 10,
        ),
        sih_sub_prime=SihSubPrime(
            # sih-description x(32)           [copybooks/slwsinv.cob:L42]
            sih_description=" " * 32,
            # The eight s9(7)v99 comp-3 money fields
            # [copybooks/slwsinv.cob:L44-L51] - signed at all three layers, so
            # genuinely clean, and the ONE contrast that makes the six sign losses
            # legible.
            sih_fig=SihFig(
                sih_p_c=Decimal("0.00"),
                sih_net=Decimal("0.00"),
                sih_extra=Decimal("0.00"),
                sih_carriage=Decimal("0.00"),
                sih_vat=Decimal("0.00"),
                sih_discount=Decimal("0.00"),
                sih_e_vat=Decimal("0.00"),
                sih_c_vat=Decimal("0.00"),
            ),
            # sih-status x, then the five extra statuses
            # [copybooks/slwsinv.cob:L52], [:L56-L60] - the "5 byte increase" the
            # shouted warning at [:L12] is about.
            sih_status=" ",
            sih_status_p=" ",
            sih_status_l=" ",
            sih_status_c=" ",
            sih_status_a=" ",
            sih_status_i=" ",
            # sih-lines binary-char SIGNED    [copybooks/slwsinv.cob:L61]
            sih_lines=0,
            # sih-deduct-days binary-char SIGNED  [:L62]
            sih_deduct_days=0,
            # sih-deduct-amt / -vat 999v99 comp UNSIGNED  [:L63-L64]
            sih_deduct_amt=Decimal("0.00"),
            sih_deduct_vat=Decimal("0.00"),
            # sih-days binary-char SIGNED, sih-cr binary-long SIGNED  [:L65-L66]
            sih_days=0,
            sih_cr=0,
            # sih-day-book-flag x, sih-update x  [:L67], [:L69]
            sih_day_book_flag=" ",
            sih_update=" ",
        ),
    )


def _new_line_record() -> SilInvoiceLine:
    """``initialize`` a line view - every field zero or space, nothing absent.

    The counterpart of :func:`_new_header_record`, matching
    ``initialize WS-Invoice-Line`` [common/slinvoiceMT.cbl:L2820] and the British
    ``initialise WS-Invoice-Line`` at [:L2501] - the spelling divergence is recorded
    on those paragraphs and changes nothing, GnuCOBOL accepting both.

    ⭐⭐ N-back-ordered-dropped.  ``sil_back_ordered`` IS initialised here, because
    ``copybooks/slwsinv.cob:L97-L98`` declares it (added 03/03/24, replacing an older
    filler) - but it has NO host variable and NO column.  The bridge's own line record
    stops at a bare ``filler pic x`` in exactly that position
    [common/slinvoiceMT.cbl:L377], and ``SAINV-LINES-REC`` has 14 columns, none of
    them ``IL-BACK-ORDERED``.  So the 2024 feature exists in the copybook and dies at
    the bridge.  It is initialised and then never written anywhere - which is the
    anomaly, faithfully.
    """
    return SilInvoiceLine(
        # sil-invoice 9(8) + sil-line 99   [copybooks/slwsinv.cob:L88-L90]
        sil_key=SilKey(sil_invoice=0, sil_line=0),
        # sil-product x(13), sil-pa xx     [:L91-L92]
        sil_product=" " * 13,
        sil_pa=" " * 2,
        # sil-qty binary-short SIGNED -> smallint unsigned: the SIXTH sign loss
        sil_qty=0,
        sil_type=" ",
        sil_description=" " * 32,
        # sil-net / -unit / -vat s9(7)v99 comp-3, signed at all three layers
        sil_net=Decimal("0.00"),
        sil_unit=Decimal("0.00"),
        sil_discount=Decimal("0.00"),
        sil_vat=Decimal("0.00"),
        sil_vat_code=0,
        sil_update=" ",
        # ⭐ Declared, initialised, and never carried to any column.  See above.
        sil_back_ordered=" ",
    )



@dataclass(slots=True)
class InvoiceBuffer:
    """``WS-Invoice-Record`` - ONE record parameter for TWO tables.

    ``copybooks/slwsinv2.cob`` declares three views of the same 137 bytes:

    * ``01  Invoice-Record.`` [:L27] - the generic view;
    * ``01  Invoice-Header  redefines Invoice-Record.`` [:L38];
    * ``01  Invoice-Line   redefines Invoice-Record.`` [:L91].

    The handler links that copybook with its own renaming
    [common/acas016.cbl:L218-L221], and the bridge links the header layout under
    a fourth name, ``WS-Invoice-Record``.  The caller sets the buffer to whichever
    view the operation needs; the function code and ``WS-Sih-Test`` decide which
    table is touched.

    **The first ten bytes are the same field in every view**, which is why both
    keys of reference are offset 1 length 10 [common/slinvoiceMT.cbl:L296-L303]::

        header    sih-invoice pic 9(8)  +  sih-test pic 99
        line      sil-invoice pic 9(8)  +  sil-line pic 99
        generic   Invoice-Nos pic 9(8)  +  Item-Nos pic 99

    ``ba041-Reread`` proves the identity by USING it
    [common/slinvoiceMT.cbl:L724-L725], verbatim::

        add     1 WS-Last-Read-Line giving WS-Sih-Test
        move    WS-Last-Read-Invoice to WS-Sih-Invoice

    - it writes the LINE number into ``WS-Sih-Test`` and the invoice into
    ``WS-Sih-Invoice``, then reads a LINE.  And
    ``move WS-Invoice-Key to WS-File-Key.   *> Same as WS-Sil-Key``
    [common/slinvoiceMT.cbl:L2525] asserts it in a comment.

    So the shared region is modelled ONCE, here, and the two views hold only
    their own remaining fields.  This is one parameter with a discriminator, not
    two typed parameters - splitting it would remove the very mechanism the
    bridge dispatches on.
    """

    #: ``sih-invoice`` / ``sil-invoice`` / ``Invoice-Nos`` - bytes 1-8, shared.
    ws_sih_invoice: int = 0
    #: ``sih-test`` / ``sil-line`` / ``Item-Nos`` - bytes 9-10, shared, AND the
    #: header-versus-line discriminator every bridge paragraph tests.
    ws_sih_test: int = 0
    #: The header view.  ``SInvoiceHeader`` is ``copybooks/slwsinv.cob:L18``,
    #: which is what the bridge copied and renamed ``WS-Invoice-Record``.  Its
    #: own ``sih_prime.ws_invoice_key`` is kept in step with the shared region by
    #: :meth:`sync_key_into_views`.
    ws_invoice_record: SInvoiceHeader | None = None
    #: The line view, ``copybooks/slwsinv2.cob:L91``, published by the record
    #: layer as ``SilInvoiceLine``.
    invoice_line: SilInvoiceLine | None = None
    #: ``slinvoiceMT``'s OWN Working-Storage, which persists across ``CALL``s.
    #:
    #: A COBOL sub-program's Working-Storage survives between calls for as long as
    #: the module stays resident, and this bridge DEPENDS on that: the cursor flags
    #: [common/slinvoiceMT.cbl:L331-L336], ``WS-Last-Read-Invoice`` /
    #: ``WS-Last-Read-Line`` [:L285-L287] and ``WS-Actual-Lines-In-Row`` [:L288] are
    #: all read on a later call than the one that wrote them - that is the entire
    #: mechanism of the two-table walk in ``ba041-Reread`` [:L725-L741].
    #:
    #: It is anchored to the BUFFER rather than to module-level globals on purpose.
    #: Module state would be shared by every caller in the process, which would make
    #: two runs in one interpreter differ - and AAP section 0.6.6 requires that
    #: "there is no hidden time source, no random seed, and no ordering
    #: nondeterminism". Per-buffer state keeps the persistence the COBOL has while
    #: keeping runs independent.
    bridge_state: BridgeState = field(default_factory=lambda: BridgeState())
    #: The live connection, held here for the same reason: the COBOL bridge reaches
    #: it through the MySQL client library's own process state, so it outlives any
    #: single ``CALL``.  ``ba020-Process-Open`` sets it [:L596] and
    #: ``ba030-Process-Close`` clears it [:L620].
    connection: object = None

    @property
    def ws_invoice_key(self) -> str:
        """``03  WS-Invoice-Key.`` - the ten characters both PK columns hold."""
        return f"{self.ws_sih_invoice:08d}{self.ws_sih_test:02d}"

    def header_selected(self) -> bool:
        """Whether this buffer currently addresses the HEADER table.

        ``if WS-Sih-Test not = zero`` is the discriminator, tested at four
        separate bridge paragraphs - ``ba050-Process-Read-Indexed``
        [common/slinvoiceMT.cbl:L829], ``ba070-Process-Write`` [:L1150],
        ``ba080-Process-Delete`` [:L1192] and ``ba090-Process-Rewrite``
        [:L1359] - each of which hands off to its ``bc`` counterpart when the
        test is true.  A zero line number means the header.
        """
        return self.ws_sih_test == 0

    def select_header(self) -> SInvoiceHeader:
        """Address the header view, materialising it if the caller never set one.

        ⚠ COBOL HAS NO "UNSET VIEW" STATE, SO NEITHER DOES THIS.
        ``WS-Invoice-Record`` is 137 bytes of storage that always exists; the three
        redefinitions [copybooks/slwsinv2.cob:L27], [:L38], [:L91] are three ways of
        reading the SAME bytes, and an ``initialize`` leaves them zero and space
        rather than absent.  Python cannot overlay storage, so the views are separate
        objects and one of them can be ``None`` - a state the COBOL cannot reach.

        Materialising a zero-and-space view is therefore the faithful answer, and
        raising is not: a raise would break the contract at
        ``[common/acas016.cbl:L627]`` - *"Any errors leave it to caller to recover
        from"* - and would abort a posting run where the COBOL would quietly load a
        row of zeros.  The shared key components are carried in from the buffer so
        the ten-byte prefix is consistent across views, exactly as the redefinition
        makes it.
        """
        header = self.ws_invoice_record
        if header is None:
            header = _new_header_record()
            self.ws_invoice_record = header
        # The first ten bytes are the same field in every view, so keep them so.
        header.sih_prime.ws_invoice_key.sih_invoice = self.ws_sih_invoice
        header.sih_prime.ws_invoice_key.sih_test = self.ws_sih_test
        return header

    def select_line(self) -> SilInvoiceLine:
        """Address the line view, materialising it if the caller never set one.

        The counterpart of :meth:`select_header`, for the same reason.  The shared
        prefix is carried in as ``sil-invoice``/``sil-line`` because that is what the
        redefinition makes those bytes when read through the line view -
        ``ba041-Reread`` [common/slinvoiceMT.cbl:L724-L725] relies on precisely this
        identity when it writes a LINE number into ``WS-Sih-Test`` and then reads a
        line.
        """
        line = self.invoice_line
        if line is None:
            line = _new_line_record()
            self.invoice_line = line
        line.sil_key.sil_invoice = self.ws_sih_invoice
        line.sil_key.sil_line = self.ws_sih_test
        return line

    def sync_key_into_views(self) -> None:
        """Propagate the shared ten bytes into whichever views are present.

        The COBOL needs no such step because the views literally overlay the same
        storage.  Python has no ``REDEFINES``, so the propagation is explicit -
        and explicit is what AAP section 0.4.2 asks for anyway, since the bridge
        itself moves between the two areas with named ``MOVE`` statements rather
        than relying on the overlay.
        """
        header = self.ws_invoice_record
        if header is not None:
            header.sih_prime.ws_invoice_key.sih_invoice = self.ws_sih_invoice
            header.sih_prime.ws_invoice_key.sih_test = self.ws_sih_test
        line = self.invoice_line
        if line is not None:
            line.sil_key.sil_invoice = self.ws_sih_invoice
            line.sil_key.sil_line = self.ws_sih_test

    def adopt_key_from_header(self) -> None:
        """Take the shared ten bytes FROM the header view.

        Used when a caller has filled ``SInvoiceHeader`` directly, which is how
        every posting program in ``acas_posting/programs/`` will address this
        handler.
        """
        header = self.ws_invoice_record
        if header is not None:
            key = header.sih_prime.ws_invoice_key
            self.ws_sih_invoice = key.sih_invoice
            self.ws_sih_test = key.sih_test

    def adopt_key_from_line(self) -> None:
        """Take the shared ten bytes FROM the line view."""
        line = self.invoice_line
        if line is not None:
            self.ws_sih_invoice = line.sil_key.sil_invoice
            self.ws_sih_test = line.sil_key.sil_line


@dataclass(slots=True)
class BridgeState:
    """The bridge's Working-Storage that survives between calls.

    Everything here is declared in ``slinvoiceMT``'s Working-Storage and is
    stateful ACROSS calls, which is why it lives in one object the caller keeps
    rather than in locals.  There is no thread-safety machinery of any kind:
    AAP section 0.2.2, verbatim - *"No threads, no `asyncio`, no
    `multiprocessing`, no connection pooling. Execution is strictly sequential,
    matching the single-threaded COBOL."*

    [common/slinvoiceMT.cbl:L279-L288], verbatim::

        *>      we will need to also hold the value from WS-Sih-Lines in
        *>       the invoice table - stored in WS-Actual-Lines-In-Row.

        *>     Not used for writing but could be for deletes.

        01  WS-Last-Read-Key.
            03  WS-Last-Read-Invoice pic 9(8)    value zero.
            03  WS-Last-Read-Line    pic 99      value 40.
        01  WS-Actual-Lines-In-Row   pic 99      value zero.

    Note ``WS-Last-Read-Line`` starts at **40**, not zero - the ``occurs 40``
    upper bound - so a first ``ba041-Reread`` before any header has been read
    cannot enter the line-walking block.
    """

    #: ``03  WS-Last-Read-Invoice pic 9(8) value zero.`` [:L286].  Also the
    #: "have the DALs been called yet" flag: ``if WS-Last-Read-Invoice = zero
    #: go to ba042-Fetch.  *> DALS Not yet called`` [:L719-L720].
    ws_last_read_invoice: int = 0
    #: ``03  WS-Last-Read-Line pic 99 value 40.`` [:L287].
    ws_last_read_line: int = 40
    #: ``01  WS-Actual-Lines-In-Row pic 99 value zero.`` [:L288] - the header's
    #: own line count, cached by the unload so the line walk knows when to stop.
    ws_actual_lines_in_row: int = 0

    #: N-deadfields.  ``01  WS-Body-Key pic x(9). *> Not used``
    #: [common/slinvoiceMT.cbl:L348].  Declared and never referenced anywhere in
    #: the bridge; carried here so the reader sees it was not overlooked.  The
    #: ``01 RG-Table`` reminder block [:L316-L326] is the same kind of dead
    #: declaration and is described under :data:`RG_FAMILY_DESCRIPTION`.
    ws_body_key: str = " " * 9

    #: ``01 MOST-Relation pic xxx.`` [:L330] - ``>=``, ``<=``, ``<``, ``>``, ``=``.
    most_relation: str = ""
    #: ``ws-Where pic x(512)`` [:L273] rendered for the log, header cursor.
    ws_where: str = ""
    #: ``ws-Where-2 pic x(512). *> RG1`` [:L274] - the lines cursor's own clause.
    ws_where_2: str = ""

    #: The two host-variable groups.
    td_sainvoice_rec: TdSainvoiceRec = field(default_factory=TdSainvoiceRec)
    td_sainv_lines_rec: TdSainvLinesRec = field(default_factory=TdSainvLinesRec)

    #: ``01 WS-Invoice-Line.`` [:L361] - the bridge's own staging area.
    ws_invoice_line: WsInvoiceLine = field(default_factory=WsInvoiceLine)

    #: N-two-cursors.  ``Most-Cursor-Set`` [:L331] and ``Most-Cursor-Set-2``
    #: [:L334] are TWO independent cursors with their own ``88`` pairs, and they
    #: are never collapsed.  ``CursorStateTable`` keys by ``(table, slot)``, so
    #: the header's PRIMARY slot and the lines' SECONDARY slot are distinct
    #: entries by construction.
    cursors: CursorStateTable = field(default_factory=CursorStateTable)

    #: ``ba060-Process-Start`` saves and restores the primary result set around
    #: its RG1 SELECT [:L1064-L1140], and ``bc050``/``bc058`` do the same
    #: [:L2385-L2389], [:L2513-L2515].  These hold the saved snapshots.
    save_result_rows: tuple[Mapping[str, Any], ...] = ()
    save_count_rows: int = 0
    save_result_rows_rg1: tuple[Mapping[str, Any], ...] = ()
    save_count_rows_rg1: int = 0

    def header_cursor(self) -> CursorState:
        """``Most-Cursor-Set`` - the ``SAINVOICE-REC`` cursor [:L331-L333]."""
        return self.cursors.state_for(HEADER_TABLE, _HEADER_SLOT)

    def line_cursor(self) -> CursorState:
        """``Most-Cursor-Set-2`` - the ``SAINV-LINES-REC`` cursor [:L334-L336]."""
        return self.cursors.state_for(LINES_TABLE, _LINE_SLOT)


# ---------------------------------------------------------------------------
# TRANSLATION CORRECTION C1 - the `filler redefines sih-order` byte area
# ---------------------------------------------------------------------------
# `03 sih-order pic x(10).` [copybooks/slwsinv.cob:L27] is immediately redefined
# by `03 filler redefines sih-order.` [:L28] carrying four members that sum to
# the same ten bytes: `05 sih-Freq pic x.` [:L29], `05 sih-Repeat pic 99.`
# [:L36], `05 filler pic xxx.` [:L37] and `05 sih-Last-Date binary-long.` [:L38],
# whose own comment reads "4 bytes date an invoice was generated/posted".
#
# In the compiled program those are ONE byte area, so `move "M" to sih-Freq` has
# already written the first of `sih-order`'s ten bytes and
# `move WS-Sih-Order to HV-IH-ORDER` [common/slinvoiceMT.cbl:L1461] carries it to
# the column. Section 0.3.1 requires each `REDEFINES` to be modelled as its own
# view class, and `records/sales_invoice.py` is explicit that it declines to keep
# the pair in step - so the two are separate Python objects and whoever observes
# the aliasing owns re-establishing it. This bridge is that observer.
#
# Widths come from the dictionary rather than being transcribed (R-5). Only
# `sih-Last-Date`'s comes from the copybook's own annotation, because a
# `binary-long` declares no PICTURE for the dictionary to report a character
# length for; the import-time sum guard below is what proves the number.
_SIH_ORDER_WIDTH: Final[int] = int(
    loader.copybook_field_for("SAINVOICE-REC.IH-ORDER").character_length or 0
)
_SIH_FREQ_WIDTH: Final[int] = int(
    loader.copybook_field_for("SInvoice-Header.sih-Freq").character_length or 0
)
_SIH_REPEAT_DIGITS: Final[int] = int(
    loader.copybook_field_for("SInvoice-Header.sih-Repeat").digits or 0
)
_SIH_FILLER_37_WIDTH: Final[int] = int(
    loader.copybook_field_for("SInvoice-Header.filler#37").character_length or 0
)
#: `binary-long`, and the copybook says so in words [copybooks/slwsinv.cob:L38].
_SIH_LAST_DATE_BYTES: Final[int] = 4
#: The four bytes a `binary-long` actually is - see `_project_order_overlay_into_base`.
_SIH_LAST_DATE_MASK: Final[int] = (1 << (8 * _SIH_LAST_DATE_BYTES)) - 1

# The four members must tile the field they redefine exactly. `records/
# sales_invoice.py` records the same arithmetic in prose - "Its four members sum
# to 1 + 2 + 3 + 4 = 10 bytes, exactly the field they overlay" - and this is that
# claim enforced at import time, so a dictionary regeneration that changed any of
# the four widths would fail loudly here instead of silently mis-encoding.
if (
    _SIH_FREQ_WIDTH + _SIH_REPEAT_DIGITS + _SIH_FILLER_37_WIDTH + _SIH_LAST_DATE_BYTES
) != _SIH_ORDER_WIDTH:
    _MSG: Final[str] = (
        "filler redefines sih-order [copybooks/slwsinv.cob:L28-L38] must tile "
        f"sih-order [:L27] exactly: {_SIH_FREQ_WIDTH} + {_SIH_REPEAT_DIGITS} + "
        f"{_SIH_FILLER_37_WIDTH} + {_SIH_LAST_DATE_BYTES} != {_SIH_ORDER_WIDTH}"
    )
    raise loader.DictionaryLookupError(_MSG)


def _order_overlay_is_blank(view: SihOrderView) -> bool:
    """Is the autogen overlay still at the state ``INITIALIZE`` leaves it in?

    ``initialize WS-Invoice-Record.`` [common/slinvoiceMT.cbl:L1496] blanks the
    ten bytes of ``sih-order`` [copybooks/slwsinv.cob:L27], and the overlay IS
    those ten bytes, so after an initialise the overlay reads blank.  Both
    :func:`_new_header_record` and :func:`_initialize_header_record` put it there.

    The test is what makes correction C1 safe rather than sweeping.  A header the
    caller never touched the overlay of must reach ``HV-IH-ORDER`` with the
    caller's own ``sih_order``, not with an encoding of four blank members - so
    the projection fires only when the overlay carries something.
    """
    return (
        view.sih_freq == " " * _SIH_FREQ_WIDTH
        and view.sih_repeat == 0
        and view.filler_37 == " " * _SIH_FILLER_37_WIDTH
        and view.sih_last_date == 0
    )


def _blank_order_overlay(view: SihOrderView) -> None:
    """Blank the overlay, because blanking ``sih-order`` blanks it in COBOL.

    ``initialize WS-Invoice-Record.`` [common/slinvoiceMT.cbl:L1496] is the PLAIN
    form, which does not descend into a FILLER item - but it does name
    ``sih-order`` [copybooks/slwsinv.cob:L27], and the unnamed
    ``filler redefines sih-order`` [:L28] occupies exactly those bytes, so the
    compiled program blanks the overlay whether ``INITIALIZE`` walked into it or
    not.  Reproducing that here is what stops a stale overlay from surviving a
    read and then being projected over the row value the read just delivered.

    ⭐ THE BYTE STATE IS NOT EXACTLY REPRESENTABLE, and the difference is marked
    rather than papered over.  Ten blanks make ``sih-Repeat pic 99`` [:L36] read
    as two SPACE characters in a zoned field and ``sih-Last-Date binary-long``
    [:L38] read as ``0x20202020``; ``sih_repeat`` and ``sih_last_date`` are
    ``int`` per the record contract's scale rule and neither value has an ``int``
    form.  Both are set to zero, which is what the one construction site declares
    and what keeps :func:`_order_overlay_is_blank` true after an initialise.  The
    alternative - storing 538976288 for the date - would make the projection fire
    on every initialised header and overwrite every caller's ``sih_order``.  See
    Q-order-overlay-blank-state in the module docstring.
    """
    view.sih_freq = " " * _SIH_FREQ_WIDTH
    view.sih_repeat = 0
    view.filler_37 = " " * _SIH_FILLER_37_WIDTH
    view.sih_last_date = 0


def _project_order_overlay_into_base(prime: SihPrime) -> None:
    """CORRECTION C1 - make the overlay's bytes visible through ``sih-order``.

    The four members are laid down in declaration order, each at its declared
    width, exactly as the compiled program's storage already holds them:

    * ``sih-Freq pic x`` [copybooks/slwsinv.cob:L29] - one character.
    * ``sih-Repeat pic 99`` [:L36] - two ZONED digits, so the integer is rendered
      zero-padded; a ``DISPLAY`` field stores its digits as characters.
    * ``filler pic xxx`` [:L37] - three characters, carried rather than dropped,
      because a FILLER occupies bytes.
    * ``sih-Last-Date binary-long`` [:L38] - four bytes, big-endian and signed.
      Big-endian is GnuCOBOL's default ``binary-byteorder`` and no compile line in
      the repository sets one: neither ``comp-all.sh`` nor
      ``common/comp-common.sh`` passes ``-fbinary-byteorder``, ``-fbinary-size``
      or ``-fbinary-truncate``.  Signed because the copybook declares
      ``binary-long`` without ``UNSIGNED``.

    Nothing is written when the overlay is blank, so the ordinary posting path -
    where a caller sets ``sih_order`` and never touches the overlay - is byte for
    byte unchanged.

    ⭐ WHY THE DIRECTION IS overlay -> base AND NOT THE REVERSE, from the frozen
    source rather than from preference.  The overlay's only writers anywhere are
    ``accept sih-Repeat`` [sales/sl810.cbl:L1636], ``accept Sih-Freq`` [:L1648],
    ``subtract 1 from sih-Repeat`` [sales/sl830.cbl:L534] and
    ``move Sih-Date to Sih-Last-Date`` [:L615], plus the purchase twins - all in
    the autogen series, which AAP section 0.2.2 puts out of scope, and all of
    which reach this bridge only by having written the shared bytes.  The base is
    what every in-scope reader reads: ``move ih-order to oi-description``
    [sales/sl055.cbl:L641] and ``move ih-order to oi-order``
    [purchase/pl055.cbl:L554], neither of which writes it.  And the autogen
    author relied on the sharing knowingly - ``move spaces to ih-Order``
    [sales/sl830.cbl:L540] is how he clears the overlay, under his own note
    "Remember to NOT include content of sih-Order but space fill the invoice
    sih-order" [:L505].

    THE REVERSE DIRECTION IS DELIBERATELY NOT IMPLEMENTED (R-5, recorded as an
    omission).  Decoding ``sih-order`` back into the overlay after every read
    would leave the overlay non-blank, so the very next write would project those
    stale members over a caller's fresh ``sih_order`` - a new defect in place of
    the one being fixed.  No in-scope program reads the overlay, and
    :func:`_blank_order_overlay` keeps the read path from leaving a stale one.

    Args:
        prime: ``02 sih-prime.`` [copybooks/slwsinv.cob:L19], mutated in place -
            ``sih_order`` is rewritten from ``filler_28`` when the latter carries
            anything.
    """
    view = prime.filler_28
    if _order_overlay_is_blank(view):
        return
    # A COBOL alphanumeric MOVE truncates on the right and pads with spaces; the
    # overlay members are already at their widths, and fitting them again makes
    # this correct for a record a caller built by hand.
    freq = view.sih_freq.ljust(_SIH_FREQ_WIDTH)[:_SIH_FREQ_WIDTH]
    # `pic 99` is DISPLAY: the digits ARE the bytes.  A value wider than the
    # field truncates on the LEFT for a numeric receiving item, which is what the
    # negative slice reproduces.
    repeat = f"{int(view.sih_repeat):0{_SIH_REPEAT_DIGITS}d}"[-_SIH_REPEAT_DIGITS:]
    filler = view.filler_37.ljust(_SIH_FILLER_37_WIDTH)[:_SIH_FILLER_37_WIDTH]
    # A `binary-long` field IS four bytes, so a value outside its range keeps
    # only the low four bytes rather than raising - `to_bytes` alone would raise
    # `OverflowError`, and this module's contract is that a verb returns a status
    # pair and never propagates an exception.  The mask is the two's-complement
    # truth of the storage; a COBOL field could not have held the wider value at
    # all.  latin-1 is a byte-for-byte codec, so what follows is those four bytes
    # and not a re-encoding of them.
    stored = int(view.sih_last_date) & _SIH_LAST_DATE_MASK
    last_date = stored.to_bytes(_SIH_LAST_DATE_BYTES, "big", signed=False).decode(
        "latin-1"
    )
    prime.sih_order = f"{freq}{repeat}{filler}{last_date}"[:_SIH_ORDER_WIDTH]


# ---------------------------------------------------------------------------
# bb000-HV-Load  /  bb100-UnloadHVs   -  the HEADER table
# ---------------------------------------------------------------------------
def bb000_hv_load(state: BridgeState, buffer: InvoiceBuffer) -> None:
    """``bb000-HV-Load Section.`` [common/slinvoiceMT.cbl:L1445-L1486].

    Loads all 31 header host variables from ``WS-Invoice-Record``.  The move
    order below is the COBOL's, statement for statement, and is NOT the column
    order - see N-triple-order-mismatch and :data:`HEADER_LOAD_SEQUENCE`.

    Verbatim extract::

        L1453      initialize TD-SAINVOICE-REC.
        L1455      move     WS-Invoice-Key       to HV-SINVOICE-KEY.
        L1457      move     WS-Sih-Invoice       to HV-IH-INVOICE.
        L1458      move     WS-Sih-Test          to HV-IH-TEST.
        L1459      move     WS-Sih-Customer      to HV-IH-CUSTOMER
        ...
        L1479      move     WS-Sih-Lines         to HV-IH-LINES
        L1480      move     WS-Sih-Deduct-Days   to HV-IH-DEDUCT-DAYS
        ...
        L1486      move     WS-Sih-Update        to HV-IH-UPDATE.

    N-punctuation.  The punctuation is irregular: [:L1455], [:L1457] and [:L1458]
    each end with a period mid-block, then [:L1459] onward run unpunctuated to
    [:L1486] - four statement groups where one would do.  Preserved as a comment,
    never normalised, because normalising it would erase evidence of how the
    paragraph was edited.

    N-triple-key-materialisation.  ``WS-Invoice-Key`` - the 10-byte group - feeds
    ``HV-SINVOICE-KEY`` at [:L1455] while its two components separately feed
    ``HV-IH-INVOICE`` [:L1457] and ``HV-IH-TEST`` [:L1458], so **the key is
    materialised three times in one row**.  Reproduced, not deduplicated.

    N-signloss.  Five of the six narrowings happen here, inside
    :meth:`_HostVariableGroup.move_in` -> :func:`narrow_signed_host_variable`,
    which means they happen BEFORE any SQL text exists.  That is the point: AAP
    section 0.6.2 says the sign is lost *"at the bridge, not at the database"*.
    """
    header = buffer.select_header()
    group = state.td_sainvoice_rec
    # L1453  initialize TD-SAINVOICE-REC.   -> every field zero or space, so no
    #        column can reach SQL as NULL (AAP section 0.6.2).
    group.initialize()

    prime = header.sih_prime
    sub = header.sih_sub_prime
    fig = sub.sih_fig

    # L1455  move WS-Invoice-Key to HV-SINVOICE-KEY.        <- period here
    group.move_in("SINVOICE-KEY", buffer.ws_invoice_key)
    # L1457  move WS-Sih-Invoice to HV-IH-INVOICE.          <- period here
    group.move_in("IH-INVOICE", prime.ws_invoice_key.sih_invoice)
    # L1458  move WS-Sih-Test to HV-IH-TEST.                <- period here
    group.move_in("IH-TEST", prime.ws_invoice_key.sih_test)
    # L1459 onward run WITHOUT punctuation until L1486.
    # L1459  move WS-Sih-Customer to HV-IH-CUSTOMER
    #        The 7-byte group is flattened; sih-nos and sih-check
    #        [copybooks/slwsinv.cob:L24-L25] have no columns of their own.
    customer = prime.sih_customer
    group.move_in("IH-CUSTOMER", f"{customer.sih_nos:<6.6}{customer.sih_check:1d}")
    # L1460  move WS-Sih-Date to HV-IH-DAT      <- N-ih-dat-rename + N-signloss
    group.move_in("IH-DAT", prime.sih_date)
    # L1461  move WS-Sih-Order to HV-IH-ORDER
    #        The autogen redefinition's sub-fields - sih-Freq, sih-Repeat, the
    #        filler xxx and sih-Last-Date [copybooks/slwsinv.cob:L28-L38] - have
    #        no columns; only the raw ten bytes are stored.
    #
    #        CORRECTION C1.  Those four sub-fields ARE those ten bytes
    #        [copybooks/slwsinv.cob:L28], so in the compiled program this single
    #        move already carries whatever was written through either name.  The
    #        two views are separate objects here, so the aliasing is
    #        re-established immediately before the move and nowhere else - the
    #        operand of the move itself is untouched and still `WS-Sih-Order`.
    _project_order_overlay_into_base(prime)
    group.move_in("IH-ORDER", prime.sih_order)
    # L1462  move WS-Sih-Type to HV-IH-TYPE
    group.move_in("IH-TYPE", prime.sih_type)
    # L1463  move WS-Sih-Ref to HV-IH-REF
    group.move_in("IH-REF", prime.sih_ref)
    # L1464  move WS-Sih-Description to HV-IH-DESCRIPTION
    group.move_in("IH-DESCRIPTION", sub.sih_description)
    # L1465-L1472  the eight COMP-3 money fields.  Signed at copybook, host
    #              variable and column alike - the clean case, stated explicitly
    #              because it is the contrast that makes valueMT's money sign
    #              loss legible.
    group.move_in("IH-P-C", fig.sih_p_c)
    group.move_in("IH-NET", fig.sih_net)
    group.move_in("IH-EXTRA", fig.sih_extra)
    group.move_in("IH-CARRIAGE", fig.sih_carriage)
    group.move_in("IH-VAT", fig.sih_vat)
    group.move_in("IH-DISCOUNT", fig.sih_discount)
    group.move_in("IH-E-VAT", fig.sih_e_vat)
    group.move_in("IH-C-VAT", fig.sih_c_vat)
    # L1473-L1478  the status byte and its five companions.
    group.move_in("IH-STATUS", sub.sih_status)
    group.move_in("IH-STATUS-P", sub.sih_status_p)
    group.move_in("IH-STATUS-L", sub.sih_status_l)
    group.move_in("IH-STATUS-C", sub.sih_status_c)
    group.move_in("IH-STATUS-A", sub.sih_status_a)
    group.move_in("IH-STATUS-I", sub.sih_status_i)
    # L1479  move WS-Sih-Lines to HV-IH-LINES
    #        N-triple-order-mismatch: this is copybook position 24
    #        [copybooks/slwsinv.cob:L61], but HV position 29
    #        [common/slinvoiceMT.cbl:L419] and column ordinal 29
    #        [mysql/ACASDB.sql:L873].  The move happens HERE, before deduct-days,
    #        and the column list is built independently.  Also N-signloss.
    group.move_in("IH-LINES", sub.sih_lines)
    # L1480  move WS-Sih-Deduct-Days to HV-IH-DEDUCT-DAYS   <- N-signloss
    group.move_in("IH-DEDUCT-DAYS", sub.sih_deduct_days)
    # L1481-L1482  the two unsigned deduction amounts - clean at all three layers.
    group.move_in("IH-DEDUCT-AMT", sub.sih_deduct_amt)
    group.move_in("IH-DEDUCT-VAT", sub.sih_deduct_vat)
    # L1483  move WS-Sih-Days to HV-IH-DAYS                 <- N-signloss
    group.move_in("IH-DAYS", sub.sih_days)
    # L1484  move WS-Sih-CR to HV-IH-CR                     <- N-signloss
    group.move_in("IH-CR", sub.sih_cr)
    # L1485  move WS-Sih-Day-Book-Flag to HV-IH-DAY-BOOK-FLAG
    group.move_in("IH-DAY-BOOK-FLAG", sub.sih_day_book_flag)
    # L1486  move WS-Sih-Update to HV-IH-UPDATE.            <- period here
    group.move_in("IH-UPDATE", sub.sih_update)


def bb100_unload_hvs(state: BridgeState, buffer: InvoiceBuffer) -> None:
    """``bb100-UnloadHVs Section.`` [common/slinvoiceMT.cbl:L1491-L1538].

    Copies the header host variables back into ``WS-Invoice-Record`` and then
    seeds three pieces of cursor state.  Verbatim extract::

        L1496      initialize WS-Invoice-Record.
        L1498      move     HV-IH-INVOICE    to WS-Sih-Invoice
        ...
        L1518      move     HV-IH-LINES         to WS-Sih-Lines
        L1519      move     HV-IH-DEDUCT-DAYS   to WS-Sih-Deduct-Days
        ...
        L1527      move     HV-IH-UPDATE        to WS-Sih-Update.
        L1529 *>  THIS BLOCK SPECIAL FOR THIS DAL AS IT ALSO processes a RG.
        L1530 *>  ---------------------------------------------------------
        L1531 *>   Here save the ih-Lines to WS so we can keep track of body-lines.
        L1533      move     HV-IH-LINES         to WS-Actual-Lines-In-Row.
        L1535 *>   Save sih Invoice & test as last key read.
        L1537      move     HV-IH-INVOICE       to WS-Last-Read-Invoice.
        L1538      move     HV-IH-TEST          to WS-Last-Read-Line. *> should be zero

    N-header-key-not-unloaded.  ``HV-SINVOICE-KEY`` is loaded at [:L1455] and
    **never unloaded** - the unload does 30 moves, not 31, and the header key is
    reconstructed only from its two components.  The generated dictionary agrees:
    ``SAINVOICE-REC.SINVOICE-KEY`` has ``unloaded_to_record`` False and
    ``unload_source`` None.  The asymmetry is preserved, not completed.

    N-initialize.  ``initialize WS-Invoice-Record.`` at [:L1496] is PLAIN, while
    [:L804] in ``ba042-Fetch`` uses ``initialize WS-Invoice-Record with filler`` -
    two initialisation semantics in one bridge, the same divergence ``glbatchMT``,
    ``slpostingMT``, ``salesMT``, ``valueMT`` and ``analMT`` all show.  Neither is
    changed to match the other.
    """
    header = buffer.select_header()
    group = state.td_sainvoice_rec
    prime = header.sih_prime
    sub = header.sih_sub_prime
    fig = sub.sih_fig

    # L1496  initialize WS-Invoice-Record.   <- PLAIN, not `with filler`.
    _initialize_header_record(header)

    # L1498-L1499  the two key components.  HV-SINVOICE-KEY is NOT among the
    #              moves - see N-header-key-not-unloaded above.
    prime.ws_invoice_key.sih_invoice = int(group["IH-INVOICE"])
    prime.ws_invoice_key.sih_test = int(group["IH-TEST"])
    # L1500  move HV-IH-CUSTOMER to WS-Sih-Customer - the 7-byte group move.
    customer_text = str(group["IH-CUSTOMER"]).ljust(7)[:7]
    prime.sih_customer.sih_nos = customer_text[:6]
    prime.sih_customer.sih_check = _digit_or_zero(customer_text[6:7])
    # L1501-L1505
    prime.sih_date = int(group["IH-DAT"])
    # L1502  move HV-IH-ORDER to WS-Sih-Order
    #
    # CORRECTION C1, THE DIRECTION DELIBERATELY NOT IMPLEMENTED (R-5, recorded as
    # an omission).  In the compiled program this move also rewrites the overlay,
    # because the overlay is these ten bytes [copybooks/slwsinv.cob:L28].  It is
    # NOT decoded back into `filler_28` here, and the reason is that doing so
    # would leave the overlay non-blank after every read, so the very next
    # `bb000-HV-Load` would project those members over a caller's fresh
    # `sih_order` - trading the defect being fixed for a worse one.  Nothing in
    # scope reads the overlay: its only frozen readers are the autogen series
    # [sales/sl830.cbl:L571, :L574, :L581, sales/sl810.cbl:L1649], which AAP
    # section 0.2.2 excludes.  `_initialize_header_record` above has already
    # blanked the overlay, so a read leaves it in the state an `INITIALIZE`
    # leaves it in rather than in a stale one.
    prime.sih_order = str(group["IH-ORDER"])
    prime.sih_type = int(group["IH-TYPE"])
    prime.sih_ref = str(group["IH-REF"])
    sub.sih_description = str(group["IH-DESCRIPTION"])
    # L1506-L1513  the eight money fields.
    fig.sih_p_c = _decimal_of(group["IH-P-C"])
    fig.sih_net = _decimal_of(group["IH-NET"])
    fig.sih_extra = _decimal_of(group["IH-EXTRA"])
    fig.sih_carriage = _decimal_of(group["IH-CARRIAGE"])
    fig.sih_vat = _decimal_of(group["IH-VAT"])
    fig.sih_discount = _decimal_of(group["IH-DISCOUNT"])
    fig.sih_e_vat = _decimal_of(group["IH-E-VAT"])
    fig.sih_c_vat = _decimal_of(group["IH-C-VAT"])
    # L1514-L1519
    sub.sih_status = str(group["IH-STATUS"])
    sub.sih_status_p = str(group["IH-STATUS-P"])
    sub.sih_status_l = str(group["IH-STATUS-L"])
    sub.sih_status_c = str(group["IH-STATUS-C"])
    sub.sih_status_a = str(group["IH-STATUS-A"])
    sub.sih_status_i = str(group["IH-STATUS-I"])
    # L1518-L1519  the unload mirrors the LOAD's copybook ordering, so LINES
    #              comes before DEDUCT-DAYS here too.
    sub.sih_lines = int(group["IH-LINES"])
    sub.sih_deduct_days = int(group["IH-DEDUCT-DAYS"])
    # L1522-L1527
    sub.sih_deduct_amt = _decimal_of(group["IH-DEDUCT-AMT"])
    sub.sih_deduct_vat = _decimal_of(group["IH-DEDUCT-VAT"])
    sub.sih_days = int(group["IH-DAYS"])
    sub.sih_cr = int(group["IH-CR"])
    sub.sih_day_book_flag = str(group["IH-DAY-BOOK-FLAG"])
    sub.sih_update = str(group["IH-UPDATE"])

    # The shared ten bytes follow the header view, since that is what was just
    # rebuilt from the host variables.
    buffer.adopt_key_from_header()
    buffer.sync_key_into_views()

    # L1529-L1531, verbatim:
    #   *>  THIS BLOCK SPECIAL FOR THIS DAL AS IT ALSO processes a RG.
    #   *>  ---------------------------------------------------------
    #   *>   Here save the ih-Lines to WS so we can keep track of body-lines.
    # L1533  move HV-IH-LINES to WS-Actual-Lines-In-Row.
    #
    # ⭐ THE RECEIVING FIELD IS NARROWER THAN THE SENDER, and the MOVE rule is the
    # RECEIVER'S.  `HV-IH-LINES PIC 9(03) COMP` [:L419] sends three digits into
    # `01 WS-Actual-Lines-In-Row pic 99` [:L288], which holds two, so a header
    # declaring 100 lines leaves this counter at ZERO and the line walk at
    # [:L725] therefore never starts.  Storing 100 instead would compare
    # `WS-Last-Read-Line < 100` and walk for ever.
    state.ws_actual_lines_in_row = _move_to_actual_lines_in_row(int(group["IH-LINES"]))
    # L1535  *>   Save sih Invoice & test as last key read.
    # L1537  move HV-IH-INVOICE to WS-Last-Read-Invoice.
    state.ws_last_read_invoice = int(group["IH-INVOICE"])
    # L1538  move HV-IH-TEST to WS-Last-Read-Line. *> should be zero
    #
    # N-lines-cursor-from-ih-test.  This is the LINES cursor's position being
    # seeded from the HEADER's IH-TEST field - cursor state taken from a
    # semantically unrelated column, guarded by nothing, with the maintainer's own
    # hedge `*> should be zero` standing in for the guard.  Reproduced EXACTLY.
    # It is NOT corrected to zero: if IH-TEST is ever non-zero the line walk
    # starts part-way through the invoice, and what the compiled program then does
    # is an oracle question, not something to decide here.
    state.ws_last_read_line = int(group["IH-TEST"])


def _initialize_header_record(header: SInvoiceHeader) -> None:
    """``initialize WS-Invoice-Record.`` for the header view [:L1496].

    Plain ``INITIALIZE`` - numerics to zero, alphanumerics to spaces, and NOT the
    ``with filler`` form used at [:L804].  The field widths come from the frozen
    copybook through the generated dictionary, so nothing here is transcribed.

    CORRECTION C1 reaches here too.  Plain ``INITIALIZE`` does not descend into a
    FILLER item, so it never names ``filler redefines sih-order``
    [copybooks/slwsinv.cob:L28] - but it DOES name ``sih-order`` [:L27], and the
    overlay is those same ten bytes, so the compiled program blanks the overlay
    regardless.  Reproducing that is what keeps a stale overlay from surviving a
    read and being projected over the row value the read just delivered.
    """
    prime = header.sih_prime
    prime.ws_invoice_key.sih_invoice = 0
    prime.ws_invoice_key.sih_test = 0
    prime.sih_customer.sih_nos = " " * 6
    prime.sih_customer.sih_check = 0
    prime.sih_date = 0
    prime.sih_order = " " * 10
    # The ten bytes just blanked are the overlay's ten bytes - CORRECTION C1.
    _blank_order_overlay(prime.filler_28)
    prime.sih_type = 0
    prime.sih_ref = " " * 10
    sub = header.sih_sub_prime
    sub.sih_description = " " * 32
    zero_money = Decimal("0.00")
    fig = sub.sih_fig
    fig.sih_p_c = zero_money
    fig.sih_net = zero_money
    fig.sih_extra = zero_money
    fig.sih_carriage = zero_money
    fig.sih_vat = zero_money
    fig.sih_discount = zero_money
    fig.sih_e_vat = zero_money
    fig.sih_c_vat = zero_money
    sub.sih_status = " "
    sub.sih_status_p = " "
    sub.sih_status_l = " "
    sub.sih_status_c = " "
    sub.sih_status_a = " "
    sub.sih_status_i = " "
    sub.sih_lines = 0
    sub.sih_deduct_days = 0
    sub.sih_deduct_amt = zero_money
    sub.sih_deduct_vat = zero_money
    sub.sih_days = 0
    sub.sih_cr = 0
    sub.sih_day_book_flag = " "
    sub.sih_update = " "


def _initialize_line_record(line: SilInvoiceLine) -> None:
    """``initialize`` the line view IN PLACE - every field zero or space.

    The in-place counterpart of :func:`_new_line_record`, needed because the
    caller holds a reference to the view object: replacing it would leave the
    caller reading the record it held before the ``INITIALIZE``, where the COBOL
    leaves it reading zeros and spaces in the very same storage.
    """
    line.sil_key.sil_invoice = 0
    line.sil_key.sil_line = 0
    line.sil_product = " " * 13
    line.sil_pa = " " * 2
    line.sil_qty = 0
    line.sil_type = " "
    line.sil_description = " " * 32
    zero_money = Decimal("0.00")
    line.sil_net = zero_money
    line.sil_unit = zero_money
    line.sil_discount = zero_money
    line.sil_vat = zero_money
    line.sil_vat_code = 0
    line.sil_update = " "
    # Declared, initialised, and never carried to any column - see
    # `_new_line_record`'s N-back-ordered-dropped note.
    line.sil_back_ordered = " "


def _initialise_ws_invoice_record(buffer: InvoiceBuffer) -> None:
    """``initialise WS-Invoice-Record.`` - the WHOLE 137-byte linkage area.

    ⭐⭐ THE SHARED TEN BYTES ARE PART OF THE RECORD, so ``INITIALIZE`` clears
    them too.  ``WS-Invoice-Record`` is the bridge's linkage record - the whole
    137 bytes [copybooks/slwsinv2.cob:L27] - and the first ten of those bytes are
    ``Invoice-Nos``/``Item-Nos``, the very field the two views call
    ``sih-invoice``/``sih-test`` and ``sil-invoice``/``sil-line``.  A statement
    that names the ``01`` therefore zeroes the KEY as well as everything else,
    which is directly observable at the ``ba041-Reread`` not-found arm
    [common/slinvoiceMT.cbl:L730-L735], verbatim::

        initialise WS-Invoice-Record
        move spaces to WS-File-Key
        string WS-Invoice-Key
               " Not Found"
                    into WS-File-Key

    - the ``STRING`` runs AFTER the ``INITIALIZE`` and reads ``WS-Invoice-Key``,
    so the logged text is the ten ZERO characters and not the key that was just
    searched for.  Clearing only the two typed views would leave that key intact
    and the message would read ``0000010002 Not Found`` where the compiled
    program writes ``0000000000 Not Found``.

    ⭐ THE VIEWS ARE ZEROED, NOT DISCARDED.  In COBOL both "views" always exist,
    because both ARE the storage; there is no absent state to model.  The frozen
    bridge relies on that: ``initialise WS-Invoice-Record WS-Invoice-Line``
    [common/slinvoiceMT.cbl:L2452-L2453] carries the maintainer's own reason -
    *"Clear both in case called does not spot end of data for Invoice and to help
    debugging if so"* - which is a statement about what the CALLER will read
    next.  A caller reading a zeroed record is the behaviour; a caller finding no
    record at all is not, and would raise where the compiled program quietly
    processes a row of zeros.

    ``with filler`` versus plain makes NO difference in this model, and that is a
    fact about the record rather than a shortcut: the only FILLER in the area is
    ``filler redefines sih-order`` [copybooks/slwsinv.cob:L28], whose ten bytes
    the plain form already clears through ``sih-order`` itself (CORRECTION C1 on
    :func:`_initialize_header_record`), and the line view declares none.  Both
    spellings and both forms therefore route here, each keeping its own citation
    at its own site.

    Args:
        buffer: The linkage record area, mutated in place.
    """
    # The shared ten bytes first, so the two `select_*` calls below carry the
    # cleared key into whichever views the caller supplied.
    buffer.ws_sih_invoice = 0
    buffer.ws_sih_test = 0
    _initialize_header_record(buffer.select_header())
    _initialize_line_record(buffer.select_line())


def _digit_or_zero(text: str) -> int:
    """A single ``PIC 9`` read out of a group move, defaulting to zero.

    ``sih-check pic 9`` [copybooks/slwsinv.cob:L25] is the last byte of the
    7-character ``IH-CUSTOMER`` column.  A space there - which ``INITIALIZE``
    leaves and which real data legitimately carries - is not a digit, and COBOL
    reading it numerically yields zero rather than failing.  Reproduced, silently,
    because the COBOL is silent.
    """
    stripped = text.strip()
    return int(stripped) if stripped.isdigit() else 0


def _decimal_of(held: str | int | Decimal) -> Decimal:
    """Read a money host variable back as an exact ``Decimal`` (rule R-2)."""
    if isinstance(held, Decimal):
        return held
    return Decimal(str(held))


#: The digit count of ``01 WS-Actual-Lines-In-Row pic 99``
#: [common/slinvoiceMT.cbl:L288] - the bridge's own line counter, and the ONE
#: field in this module whose sending item is wider than it is.
_ACTUAL_LINES_IN_ROW_DIGITS: Final[int] = 2


def _move_to_actual_lines_in_row(value: int) -> int:
    """``move HV-IH-LINES to WS-Actual-Lines-In-Row.`` [common/slinvoiceMT.cbl:L1533].

    A NARROWING MOVE, and the rule is the RECEIVING field's:

    * sender   ``HV-IH-LINES PIC 9(03) COMP``  [common/slinvoiceMT.cbl:L419]
    * receiver ``01 WS-Actual-Lines-In-Row pic 99`` [common/slinvoiceMT.cbl:L288]
    * column   ``IH-LINES tinyint(2) unsigned`` [mysql/ACASDB.sql]

    COBOL discards HIGH-ORDER digits on a move into a shorter numeric item, so a
    header carrying 100 lines stores **zero** here, 123 stores 23, and 99 stores
    99.  Nothing clamps to the maximum and nothing raises - the same rule
    :func:`narrow_signed_host_variable` applies in the other direction, written
    out separately because that one is about SIGN and this one is about WIDTH.

    WHY IT MATTERS RATHER THAN BEING PEDANTRY.  This counter is the line walk's
    terminator: ``if WS-Last-Read-Line < WS-Actual-Lines-In-Row``
    [common/slinvoiceMT.cbl:L725] decides whether ``ba041-Reread`` fetches
    another line or moves on to the next header.  A stored 100 makes that test
    true for every reachable line number, so the walk never ends; the frozen
    zero makes it false at once and the reread falls through to ``ba042-Fetch``.

    The magnitude is taken without the builtin ``abs()``, which rule R-2's audit
    forbids in this layer; the sender is unsigned, so the expression is a
    faithful no-op for every value a column can hold.

    Args:
        value: What the host variable holds - the ``IH-LINES`` column's value.

    Returns:
        The two digits the receiving field keeps.
    """
    magnitude = -value if value < 0 else value
    return magnitude % 10**_ACTUAL_LINES_IN_ROW_DIGITS


# ---------------------------------------------------------------------------
# The two staging copies between the shared buffer and WS-Invoice-Line
# ---------------------------------------------------------------------------
def _move_ws_invoice_record_to_ws_invoice_line(
    state: BridgeState, buffer: InvoiceBuffer
) -> None:
    """``move WS-Invoice-Record to WS-Invoice-Line.`` [:L2523] and [:L2726].

    The bridge stages line data through its own Working-Storage record rather
    than working from the shared buffer directly, and it does so with named
    ``MOVE`` statements at exactly two sites: ``bc070-Process-Write``
    [common/slinvoiceMT.cbl:L2523] and ``bc090-Process-Rewrite`` [:L2726].  Both
    are reproduced in place rather than folded into the load, because the ORDER of
    "copy, then load" is what the paragraphs actually do.

    The shared ten bytes carry across unchanged - they are the same field in both
    views - and the remaining fields come from the line view of the buffer.
    """
    line_view = buffer.invoice_line
    staged = state.ws_invoice_line
    # The shared key region: sil-invoice / sil-line ARE sih-invoice / sih-test.
    staged.ws_sil_invoice = buffer.ws_sih_invoice
    staged.ws_sil_line = buffer.ws_sih_test
    if line_view is None:
        # A caller that set only the key has still addressed a line; the rest of
        # the staged record keeps whatever INITIALIZE left, which is what the
        # COBOL group move over an untouched buffer would produce.
        return
    staged.ws_sil_product = line_view.sil_product
    staged.ws_sil_pa = line_view.sil_pa
    staged.ws_sil_qty = line_view.sil_qty
    staged.ws_sil_type = line_view.sil_type
    staged.ws_sil_description = line_view.sil_description
    staged.ws_sil_net = line_view.sil_net
    staged.ws_sil_unit = line_view.sil_unit
    staged.ws_sil_discount = line_view.sil_discount
    staged.ws_sil_vat = line_view.sil_vat
    staged.ws_sil_vat_code = line_view.sil_vat_code
    staged.ws_sil_update = line_view.sil_update
    # N-back-ordered-dropped.  sil_back_ordered lands on the bridge's bare
    # `filler pic x` [common/slinvoiceMT.cbl:L377] and goes no further: there is
    # no HV1- host variable and no IL-BACK-ORDERED column.  The byte is carried
    # so the omission is visible; it is never propagated to SQL.
    staged.filler_80 = line_view.sil_back_ordered


def _move_ws_invoice_line_to_ws_invoice_record(
    state: BridgeState, buffer: InvoiceBuffer
) -> None:
    """``move WS-Invoice-Line to WS-Invoice-Record.`` [:L2499] and [:L2842].

    The reverse staging copy, at ``bc051-Fetch-RG1`` [common/slinvoiceMT.cbl:L2499]
    and at the very end of ``bc100-UnloadHVs-rg1`` [:L2842] - the line record is
    copied OVER the shared buffer after every unload, so the caller reads its line
    out of the same area a header would have arrived in.  That overwrite is the
    behaviour; it is reproduced, not softened.
    """
    staged = state.ws_invoice_line
    buffer.ws_sih_invoice = staged.ws_sil_invoice
    buffer.ws_sih_test = staged.ws_sil_line
    line_view = buffer.invoice_line
    if line_view is None:
        line_view = SilInvoiceLine(
            sil_key=_new_sil_key(staged.ws_sil_invoice, staged.ws_sil_line),
            sil_product=staged.ws_sil_product,
            sil_pa=staged.ws_sil_pa,
            sil_qty=staged.ws_sil_qty,
            sil_type=staged.ws_sil_type,
            sil_description=staged.ws_sil_description,
            sil_net=staged.ws_sil_net,
            sil_unit=staged.ws_sil_unit,
            sil_discount=staged.ws_sil_discount,
            sil_vat=staged.ws_sil_vat,
            sil_vat_code=staged.ws_sil_vat_code,
            sil_update=staged.ws_sil_update,
            sil_back_ordered=staged.filler_80,
        )
        buffer.invoice_line = line_view
        buffer.sync_key_into_views()
        return
    line_view.sil_key.sil_invoice = staged.ws_sil_invoice
    line_view.sil_key.sil_line = staged.ws_sil_line
    line_view.sil_product = staged.ws_sil_product
    line_view.sil_pa = staged.ws_sil_pa
    line_view.sil_qty = staged.ws_sil_qty
    line_view.sil_type = staged.ws_sil_type
    line_view.sil_description = staged.ws_sil_description
    line_view.sil_net = staged.ws_sil_net
    line_view.sil_unit = staged.ws_sil_unit
    line_view.sil_discount = staged.ws_sil_discount
    line_view.sil_vat = staged.ws_sil_vat
    line_view.sil_vat_code = staged.ws_sil_vat_code
    line_view.sil_update = staged.ws_sil_update
    # Still the bridge's `filler pic x` - never a column.
    line_view.sil_back_ordered = staged.filler_80
    buffer.sync_key_into_views()


def _new_sil_key(invoice: int, line: int) -> Any:
    """Build a ``sil-Key`` group [copybooks/slwsinv.cob:L82] for a fresh line view."""
    from acas_posting.records.sales_invoice import SilKey  # local: avoids a cycle

    return SilKey(sil_invoice=invoice, sil_line=line)


def _initialise_ws_invoice_line(state: BridgeState) -> None:
    """``initialise WS-Invoice-Line`` [common/slinvoiceMT.cbl:L2501] and [:L2820].

    N-initialize, second half.  [:L2501] is spelled the BRITISH way, verbatim::

        initialise WS-Invoice-Line   *> Incase called does not spot no more data for invoice.

    while [:L2820] and every other site in the bridge use ``initialize``.
    GnuCOBOL accepts both spellings, so the divergence is cosmetic - and it is
    recorded rather than normalised, because it is evidence of two editing
    sessions.
    """
    state.ws_invoice_line = WsInvoiceLine()


# ---------------------------------------------------------------------------
# bc000-HV-Load-rg1  /  bc100-UnloadHVs-rg1   -  the LINES table
# ---------------------------------------------------------------------------
def bc000_hv_load_rg1(state: BridgeState) -> None:
    """``bc000-HV-Load-rg1 Section.    *> Dry chk ?`` [common/slinvoiceMT.cbl:L2776-L2802].

    Loads all 14 line host variables from the bridge's own ``WS-Invoice-Line``.
    Verbatim::

        L2776  bc000-HV-Load-rg1 Section.     *> Dry chk ?
        L2782 *> Loading RG table: SAINV-LINES-REC
        L2783 *> <<<<  this should be a move from invoice-rec to line rec >>>>> <<>>
        L2787      initialize TD-SAINV-LINES-REC.
        L2789      move     WS-Sil-Key         to HV1-IL-LINE-KEY.
        L2790      move     WS-Sil-Line        to HV1-IL-LINE
        L2791      move     WS-Sil-Invoice     to HV1-IL-INVOICE
        L2792      move     WS-Sil-Product     to HV1-IL-PRODUCT
        L2793      move     WS-Sil-Pa          to HV1-IL-PA
        L2794      move     WS-Sil-Qty         to HV1-IL-QTY
        L2795      move     WS-Sil-Type        to HV1-IL-TYPE
        L2796      move     WS-Sil-Description to HV1-IL-DESCRIPTION
        L2797      move     WS-Sil-Net         to HV1-IL-NET
        L2798      move     WS-Sil-Unit        to HV1-IL-UNIT
        L2799      move     WS-Sil-Discount    to HV1-IL-DISCOUNT
        L2800      move     WS-Sil-Vat         to HV1-IL-VAT
        L2801      move     WS-Sil-Vat-Code    to HV1-IL-VAT-CODE
        L2802      move     WS-Sil-Update      to HV1-IL-UPDATE.

    N-drychk.  Both this section and :func:`bc100_unload_hvs_rg1` [:L2810] carry
    ``*> Dry chk ?`` on their header lines - the maintainer's own doubt about
    duplication between them.  Quoted, not resolved.

    N-rg-todo.  [:L2783] is an unresolved TODO INSIDE the load, verbatim:
    ``*> <<<<  this should be a move from invoice-rec to line rec >>>>> <<>>``.
    Quoted verbatim and NOT acted on - the migration reproduces the code as
    written, not as its author wished he had written it.

    N-lines-loadorder.  [:L2790] moves LINE **before** [:L2791] moves INVOICE,
    while the host-variable group declares INVOICE first
    [common/slinvoiceMT.cbl:L428-L429] and the frozen column list carries
    ``IL-INVOICE`` at ordinal 2 and ``IL-LINE`` at ordinal 3
    [mysql/ACASDB.sql:L811-L812].  Third load-order inversion in the tree, after
    ``nominalMT`` and ``glpostingMT``.  The move order below is the COBOL's; the
    statement's column order comes from :data:`LINE_COLUMNS` and is NOT derived
    from it.

    N-triple-key-materialisation.  ``WS-Sil-Key`` - the 10-byte group - feeds
    ``HV1-IL-LINE-KEY`` at [:L2789] while its two components feed
    ``HV1-IL-INVOICE`` and ``HV1-IL-LINE`` separately, so the key is stored three
    times in one row here too.
    """
    group = state.td_sainv_lines_rec
    staged = state.ws_invoice_line

    # L2787  initialize TD-SAINV-LINES-REC.  -> nothing can reach SQL as NULL.
    group.initialize()

    # L2789  move WS-Sil-Key to HV1-IL-LINE-KEY.   <- period here; group move.
    group.move_in("IL-LINE-KEY", staged.ws_sil_key)
    # L2790  move WS-Sil-Line to HV1-IL-LINE      <- LINE FIRST.  N-lines-loadorder.
    group.move_in("IL-LINE", staged.ws_sil_line)
    # L2791  move WS-Sil-Invoice to HV1-IL-INVOICE
    #        N-il-invoice-never-unloaded starts here: this host variable IS
    #        loaded, and bc100-UnloadHVs-rg1 [:L2822-L2834] never reads it back.
    group.move_in("IL-INVOICE", staged.ws_sil_invoice)
    # L2792-L2796
    group.move_in("IL-PRODUCT", staged.ws_sil_product)
    group.move_in("IL-PA", staged.ws_sil_pa)
    # L2794  WS-Sil-Qty is binary-short SIGNED -> HV1-IL-QTY PIC 9(05) COMP
    #        unsigned -> smallint(6) unsigned.  The sixth and last N-signloss.
    group.move_in("IL-QTY", staged.ws_sil_qty)
    group.move_in("IL-TYPE", staged.ws_sil_type)
    group.move_in("IL-DESCRIPTION", staged.ws_sil_description)
    # L2797-L2800  three signed COMP-3 money fields plus the unsigned discount -
    #              all clean at copybook, host variable and column.
    group.move_in("IL-NET", staged.ws_sil_net)
    group.move_in("IL-UNIT", staged.ws_sil_unit)
    group.move_in("IL-DISCOUNT", staged.ws_sil_discount)
    group.move_in("IL-VAT", staged.ws_sil_vat)
    # L2801-L2802
    group.move_in("IL-VAT-CODE", staged.ws_sil_vat_code)
    group.move_in("IL-UPDATE", staged.ws_sil_update)
    # There is NO fifteenth move.  sil-Back-Ordered / il-Back-Ordered has no host
    # variable [common/slinvoiceMT.cbl:L377 is a bare `filler pic x`] and no
    # column [mysql/ACASDB.sql:L809-L826 lists 14, none of them IL-BACK-ORDERED].
    # N-back-ordered-dropped: the 03/03/24 feature stops dead here.


def bc100_unload_hvs_rg1(state: BridgeState, buffer: InvoiceBuffer) -> None:
    """``bc100-UnloadHVs-rg1 Section.    *> Dry chk ?`` [common/slinvoiceMT.cbl:L2810-L2842].

    Copies THIRTEEN of the fourteen line host variables back.  Verbatim::

        L2810  bc100-UnloadHVs-rg1 Section.    *> Dry chk ?
        L2820      initialize WS-Invoice-Line.
        L2822      move     HV1-IL-LINE-KEY    to  WS-Sil-Key.
        L2823      move     HV1-IL-LINE        to  WS-Sil-Line
        L2824      move     HV1-IL-PRODUCT     to  WS-Sil-Product
        L2825      move     HV1-IL-PA          to  WS-Sil-Pa
        L2826      move     HV1-IL-QTY         to  WS-Sil-Qty
        L2827      move     HV1-IL-TYPE        to  WS-Sil-Type
        L2828      move     HV1-IL-DESCRIPTION to  WS-Sil-Description
        L2829      move     HV1-IL-NET         to  WS-Sil-Net
        L2830      move     HV1-IL-UNIT        to  WS-Sil-Unit
        L2831      move     HV1-IL-DISCOUNT    to  WS-Sil-Discount
        L2832      move     HV1-IL-VAT         to  WS-Sil-Vat
        L2833      move     HV1-IL-VAT-CODE    to  WS-Sil-Vat-Code
        L2834      move     HV1-IL-UPDATE      to  WS-Sil-Update.
        L2836 *> End of SAINV-LINES-REC unload... but save the last read line.
        L2838      move     HV1-IL-Line to WS-Last-Read-Line.
        L2840 *> Now move it to primary WS record area.
        L2842      move     WS-Invoice-Line to WS-Invoice-Record.

    **N-il-invoice-never-unloaded - the most consequential anomaly in this
    module.**  Count the moves: the load does FOURTEEN [:L2789-L2802], the unload
    does THIRTEEN [:L2822-L2834].  ``HV1-IL-INVOICE`` is loaded at [:L2791] and
    appears NOWHERE in the unload.  On a read, ``WS-Sil-Invoice`` is populated
    ONLY as the first eight characters of ``WS-Sil-Key`` by the group move at
    [:L2822] - the dedicated ``IL-INVOICE`` column is written on the way out and
    ignored on the way back.  The generated dictionary records the same fact
    independently: ``SAINV-LINES-REC.IL-INVOICE`` has ``unloaded_to_record``
    False and ``unload_source`` None.

    The asymmetry is reproduced EXACTLY - the column is written, and it is never
    read back into the record's own field.  It is not "completed".  This is the
    sharpest illustration in the folder of why a load and an unload are two
    different specifications that merely happen to share a table.
    """
    group = state.td_sainv_lines_rec

    # L2820  initialize WS-Invoice-Line.   (the American spelling, here)
    _initialise_ws_invoice_line(state)
    staged = state.ws_invoice_line

    # L2822  move HV1-IL-LINE-KEY to WS-Sil-Key.   <- period here; GROUP move, so
    #        WS-Sil-Invoice and WS-Sil-Line are both filled from these ten bytes.
    #        This is the ONLY way WS-Sil-Invoice gets a value on a read.
    key_text = str(group["IL-LINE-KEY"]).strip().rjust(10, "0")[:10]
    staged.ws_sil_invoice = _digits_or_zero(key_text[:8])
    staged.ws_sil_line = _digits_or_zero(key_text[8:10])
    # L2823  move HV1-IL-LINE to WS-Sil-Line
    staged.ws_sil_line = int(group["IL-LINE"])
    #
    # ---- NO L2823a.  There is deliberately NO
    # ----     staged.ws_sil_invoice = int(group["IL-INVOICE"])
    # ---- here, because [common/slinvoiceMT.cbl:L2822-L2834] has no such move.
    # ---- HV1-IL-INVOICE, loaded at [common/slinvoiceMT.cbl:L2791], is never
    # ---- unloaded.  N-il-invoice-never-unloaded.  Do not add it.
    #
    # L2824-L2834
    staged.ws_sil_product = str(group["IL-PRODUCT"])
    staged.ws_sil_pa = str(group["IL-PA"])
    staged.ws_sil_qty = int(group["IL-QTY"])
    staged.ws_sil_type = str(group["IL-TYPE"])
    staged.ws_sil_description = str(group["IL-DESCRIPTION"])
    staged.ws_sil_net = _decimal_of(group["IL-NET"])
    staged.ws_sil_unit = _decimal_of(group["IL-UNIT"])
    staged.ws_sil_discount = _decimal_of(group["IL-DISCOUNT"])
    staged.ws_sil_vat = _decimal_of(group["IL-VAT"])
    staged.ws_sil_vat_code = int(group["IL-VAT-CODE"])
    staged.ws_sil_update = str(group["IL-UPDATE"])
    # No fourteenth field: sil-Back-Ordered has no host variable to unload from,
    # so `filler_80` keeps whatever INITIALIZE left.  N-back-ordered-dropped.

    # L2836  *> End of SAINV-LINES-REC unload... but save the last read line.
    # L2838  move HV1-IL-Line to WS-Last-Read-Line.
    #        This OVERWRITES whatever bb100-UnloadHVs seeded from the header's
    #        IH-TEST at [common/slinvoiceMT.cbl:L1538].  The order of those two
    #        writes is behaviour - a header read seeds the line position from
    #        IH-TEST, and every subsequent line read corrects it to the line
    #        actually fetched.  N-lines-cursor-from-ih-test.
    state.ws_last_read_line = int(group["IL-LINE"])

    # L2840  *> Now move it to primary WS record area.
    # L2842  move WS-Invoice-Line to WS-Invoice-Record.
    _move_ws_invoice_line_to_ws_invoice_record(state, buffer)


def _digits_or_zero(text: str) -> int:
    """Read a fixed-width numeric slice of a group move, defaulting to zero.

    A ``PIC 9(n)`` region read out of a ten-byte group move can legitimately hold
    spaces before anything has been written to it, and COBOL reads that as zero
    rather than failing.  Silent, because the COBOL is silent.
    """
    stripped = text.strip()
    return int(stripped) if stripped.isdigit() else 0


# ---------------------------------------------------------------------------
# Statement construction
# ---------------------------------------------------------------------------
# Every table and column name in this schema contains a HYPHEN, so an unquoted
# identifier is a MySQL SYNTAX ERROR, not merely poor style.  Each of the 45
# column names is pre-quoted once, in ColumnBinding.quoted_column_name, and the
# two table names are quoted here.  No statement in this module interpolates a
# VALUE - values are bound as parameters by
# acas_posting.dal.connection.execute_statement.
_HEADER_TABLE_SQL: Final[str] = quote_identifier(HEADER_TABLE)
_LINES_TABLE_SQL: Final[str] = quote_identifier(LINES_TABLE)

_HEADER_KEY_SQL: Final[str] = quote_identifier(HEADER_KEY_COLUMN)
_LINES_KEY_SQL: Final[str] = quote_identifier(LINES_KEY_COLUMN)


def _select_all(table_sql: str, where: str) -> str:
    """``SELECT * FROM <table> WHERE <where>;`` - the bridge's own shape.

    Verified at ``ba040-Process-Read-Next`` [common/slinvoiceMT.cbl:L660-L672],
    ``ba050`` [:L860], ``ba060`` header [:L1010] and RG1 [:L1080], and
    ``bc050`` [:L2412].  ``SELECT *`` rather than a column list is what the
    bridge emits, and the fetch then reads the columns positionally in
    host-variable-group order - which is why :data:`HEADER_COLUMNS` is kept in
    ordinal order.  The trailing semicolon is present on SELECT, INSERT and
    UPDATE and ABSENT on DELETE; see :func:`_delete_from`.
    """
    return f"SELECT * FROM {table_sql} WHERE {where};"


def _delete_from(table_sql: str, where: str) -> str:
    """``DELETE FROM <table> WHERE <where>`` - with NO trailing semicolon.

    The bridge terminates its DELETE text with ``X"00"`` alone -
    ``ba080-Process-Delete`` [common/slinvoiceMT.cbl:L1216-L1222],
    ``ba085`` [:L1320], ``bc080`` [:L2596] and ``bc085`` [:L2688] - while its
    SELECT, INSERT and UPDATE all carry ``";"`` before the null terminator.  The
    inconsistency is reproduced rather than tidied, because statement text is
    exactly the kind of thing a log comparison would notice.
    """
    return f"DELETE FROM {table_sql} WHERE {where}"


def _insert_statement(
    table_sql: str, bindings: tuple[ColumnBinding, ...]
) -> str:
    """``INSERT INTO <table> SET \\`COL\\`=%s, ... ;`` - the bridge's ``SET`` form.

    ``bb200-Insert`` [common/slinvoiceMT.cbl:L1543-L1946] and
    ``bc200-Insert-rg1`` [:L2849-L3039] both use the MySQL ``INSERT ... SET``
    syntax rather than ``INSERT ... VALUES``, verified verbatim at [:L1552-L1553]::

        STRING 'INSERT INTO '
                 '`SAINVOICE-REC` SET '

    Every column is named - all 31 for the header, all 14 for the lines - because
    the group was ``INITIALIZE``d before the load and every column is
    ``NOT NULL`` with no ``DEFAULT``.  Nothing is omitted and nothing is bound
    ``None``; see AAP section 0.6.2 and :func:`_initial_value`.
    """
    assignments = ", ".join(f"{b.quoted_column_name}=%s" for b in bindings)
    return f"INSERT INTO {table_sql} SET {assignments};"


def _update_statement(
    table_sql: str, bindings: tuple[ColumnBinding, ...], where: str
) -> str:
    """``UPDATE <table> SET \\`COL\\`=%s, ... WHERE <where>;``.

    ``bb300-Update`` [common/slinvoiceMT.cbl:L1949-L2356] and
    ``bc300-Update-rg1`` [:L3042-L3236] emit the SAME column order as their
    INSERT counterparts - verified by extracting every ``'`COL`='`` literal from
    all four paragraphs - and then append
    ``" WHERE " FUNCTION TRIM (WS-Where (1:J)) ";"``.  The key column is
    therefore SET as well as matched, which is redundant but harmless and is
    reproduced.
    """
    assignments = ", ".join(f"{b.quoted_column_name}=%s" for b in bindings)
    return f"UPDATE {table_sql} SET {assignments} WHERE {where};"


#: ``bb200-Insert`` - 31 columns in ordinal order.
_HEADER_INSERT_SQL: Final[str] = _insert_statement(_HEADER_TABLE_SQL, HEADER_COLUMNS)
#: ``bc200-Insert-rg1`` - 14 columns in ordinal order.  Note the LOAD inverts
#: INVOICE and LINE [common/slinvoiceMT.cbl:L2790-L2791] but the STATEMENT does
#: not: ``bc200-Insert-rg1`` and ``bc300-Update-rg1`` both name them
#: INVOICE-then-LINE, matching the frozen column list.  The inversion is confined
#: to the load paragraph, which is why :data:`LINE_LOAD_SEQUENCE` and
#: :data:`LINE_COLUMNS` are separate tuples.
_LINES_INSERT_SQL: Final[str] = _insert_statement(_LINES_TABLE_SQL, LINE_COLUMNS)


def _equality_where(key_sql: str) -> str:
    """``\\`KeyName\\`=%s`` - the exact-match clause.

    ``[common/slinvoiceMT.cbl:L836-L843]`` for ``ba050-Process-Read-Indexed``,
    and the same shape in ``ba080``, ``ba085``, ``ba090``, ``bc050``, ``bc080``
    and ``bc090``.  Verbatim shape, with the value bound rather than
    interpolated::

        string   "`"  KeyName (KOR-x1)  "`"  '="'  WS-Invoice-Record (K:L)  '"'

    AAP section 0.1.1 on the START condition, quoted through
    :mod:`acas_posting.dal.cursor_state`: *"The START condition cannot be
    compounded"* - EXACTLY ONE predicate on EXACTLY ONE column, never an ``AND``.
    """
    return f"{key_sql}=%s"


def _start_where(key_sql: str, relation: str, *, quote_value: bool) -> str:
    """``\\`KeyName\\` <rel> %s ORDER BY \\`KeyName\\` ASC`` - the START clause.

    The header form ``[common/slinvoiceMT.cbl:L987-L1002]`` wraps the value in
    ``'"'`` on both sides.  The RG1 form ``[common/slinvoiceMT.cbl:L1061-L1072]``
    **does not** - its ``string`` has no ``'"'`` operands at all.  That asymmetry
    is real and is reproduced through ``quote_value``: the header binds the key as
    TEXT and the lines bind it as a NUMBER, which is what an unquoted literal
    makes MySQL do to a ``char(10)`` column.  It changes the comparison from
    lexicographic to numeric, and therefore the ordering a ``>=`` walk sees.
    Recorded as N-rg1-unquoted-start-value; not corrected.

    ``ORDER BY`` is the only structural difference from
    :func:`_equality_where`, and it exists because AAP section 0.6.4's strongest
    finding - ``gl072`` locating its nominal account by SEQUENTIAL read - makes
    cursor ordering load-bearing across the whole migration.
    """
    del quote_value  # affects the BOUND VALUE's type, not the clause text
    # MOST-Relation is 'pic xxx' [common/slinvoiceMT.cbl:L330], so ">= " carries a
    # trailing space - but the STRING operand is 'delimited by space'
    # [common/slinvoiceMT.cbl:L991], which truncates at the first space.  The
    # emitted operator is therefore ">=", NOT ">= ", and no space separates it
    # from either the backtick-quoted key or the value.
    operator = relation.split(" ", 1)[0]
    # ' ASC' at [common/slinvoiceMT.cbl:L651] for ba040 carries no trailing
    # spaces while ' ASC  ' at [:L999] and [:L1070] carries two.  Trailing spaces
    # are insignificant to the server and are not reproduced in the text.
    return f"{key_sql}{operator}%s ORDER BY {key_sql} ASC"


def _sequential_start_where(key_sql: str) -> str:
    """``\\`KeyName\\` >= %s ORDER BY \\`KeyName\\` ASC`` with the low key.

    ``ba040-Process-Read-Next`` opens its walk with a literal low key rather than
    a caller-supplied one.  ``[common/slinvoiceMT.cbl:L643-L654]``, verbatim::

        string   "`"                   delimited by size
                 KeyName (KOR-x1)      delimited by space
                 "`"                   delimited by size
                 " >= "                delimited by size
                 '"0000000000"'        delimited by size  *> for 1st time active only
                 ' ORDER BY '          delimited by size
                 "`"                   delimited by size
                 keyname (KOR-x1)      delimited by space
                 "`"                   delimited by size
                   ' ASC'              delimited by size

    ``acas_posting.dal.cursor_state.SEQUENTIAL_READ_START`` already records the
    relation and the low key for ``SAINVOICE-REC``, cited to [:L646] and [:L647],
    which is where they are taken from rather than retyped.
    """
    return f"{key_sql} {_SEQUENTIAL_RELATION} %s ORDER BY {key_sql} ASC"


def _delete_all_lines_where() -> str:
    """The clear-down clause for ``bc085`` - and it can never match a row.

    ``[common/slinvoiceMT.cbl:L2656-L2673]``, verbatim, INCLUDING the four
    commented-out lines that show what was meant::

         set      KOR-x1 to 2
         move     KOR-offset (KOR-x1) to K
         move     KOR-length (KOR-x1) to L

         move     spaces to WS-Where
         move     1   to J
         string
     *>             "`"                   delimited by size
     *>             KeyName (KOR-x1)      delimited by space    *>   ?????? should be SA
     *>             "`"                   delimited by size
     *>             WS-Invoice-Record (K:L)    delimited by size

                  "'IL-INVOICE'"        delimited by size
                  '="'                  delimited by size      *> was '<"'
                  WS-Sih-Invoice        delimited by size    *> Correct one ?
                  '"'                   delimited by size
                          into WS-Where
                            with pointer J
         end-string

    N-bc085-string-constant-predicate.  The identifier is written
    ``"'IL-INVOICE'"`` - **single quotes, so a STRING LITERAL, not a backtick
    identifier**.  The generated predicate is therefore
    ``'IL-INVOICE' = '00012345'``: a comparison between two constants that is
    ALWAYS FALSE, so the statement deletes ZERO rows every time.  Combined with
    the tail at [:L2701-L2717] - where the ``995``/``99`` pair is set only inside
    ``if WS-MYSQL-Error-Number not = "0  "``, which a successful zero-row DELETE
    does not satisfy, and where the ``go to bc085-Exit`` then SKIPS the
    ``move zero to FS-Reply WE-Error`` at [:L2718] - the caller is told nothing at
    all.  ``Invoice-Delete-All``'s line clear-down silently does nothing.

    Reproduced exactly: the constant stays a constant and the value stays bound,
    so the predicate is still always false.  The maintainer's own two question
    marks - ``*>   ?????? should be SA`` and ``*> Correct one ?`` - are quoted
    above and NOT acted on.  The correct clause would be
    ``\\`IL-INVOICE\\`=%s``; writing it would fix a defect, which rule R-4 defines
    as a failure.
    """
    # '="' is 'delimited by size' [common/slinvoiceMT.cbl:L2669], so no spaces
    # surround the operator, and the closing '"' at [:L2671] closes the value -
    # which is bound here rather than interpolated.
    return "'IL-INVOICE'=%s"


@dataclass(frozen=True, slots=True)
class StatementOutcome:
    """The result of one bridge statement - a status PAIR, never an exception.

    ``[common/acas016.cbl:L627]``, verbatim::

        *>   Any errors leave it to caller to recover from

    That single comment is the contract for this whole module, and it is why
    nothing here raises: :func:`acas_posting.dal.status.raise_for_status` exists
    but is opt-in and is deliberately never called.  Every path returns
    ``fs_reply``/``we_error`` and lets the caller decide, exactly as the COBOL
    handler chain does.

    ``statement`` and ``parameters`` are carried on the outcome so that the
    caller - and the ad-hoc tests, and any future oracle log comparison - can
    inspect the exact text and bindings that were issued without re-deriving
    them.
    """

    statement: str
    parameters: tuple[object, ...]
    fs_reply: int = int(FsReply.SUCCESS)
    we_error: int = int(WeError.SUCCESS)
    sql_err: str = ""
    sql_msg: str = ""
    sql_state: str = ""
    count_rows: int = 0
    #: Rows as POSITIONAL tuples, not mappings.  This is deliberate and is the
    #: faithful shape: the bridge fetches with
    #: ``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT HV-SINVOICE-KEY
    #: HV-IH-INVOICE ...`` [common/slinvoiceMT.cbl:L746-L780], binding each column
    #: to a host variable BY POSITION.  That operand list was diffed against the
    #: host-variable group declaration [:L391-L421] and found IDENTICAL, and both
    #: equal the frozen column ordinal order - so ``SELECT *`` and a positional
    #: read line up exactly.  Using a name-keyed row here would silently paper over
    #: any future ordinal drift instead of reproducing it.
    rows: tuple[tuple[object, ...], ...] = ()

    @property
    def succeeded(self) -> bool:
        """True when the COBOL would regard the call as clean.

        ``FS-Reply`` zero is the only success value in the ``File-Access``
        protocol [copybooks/wsfnctn.cob:L23-L38]; every other value is a
        condition the caller must inspect.
        """
        return self.fs_reply == int(FsReply.SUCCESS)


def _run_command(
    connection: object,
    logging_data: LoggingData,
    statement: str,
    parameters: Sequence[object],
    *,
    fetch: bool,
    delete_we_error: int = int(WeError.SUCCESS),
) -> StatementOutcome:
    """``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`` plus the errno check.

    Every bridge paragraph that touches the database follows one shape, verified
    identical at ``bb200-Insert`` [common/slinvoiceMT.cbl:L1930-L1946],
    ``bb300-Update`` [:L2340-L2356], ``bc200-Insert-rg1`` [:L3023-L3039],
    ``bc300-Update-rg1`` [:L3220-L3236] and every read paragraph: build the
    command text, run it, then interrogate ``MySQL_errno`` / ``MySQL_sqlstate``
    and translate the pair into ``FS-Reply`` / ``WE-Error``.  That translation is
    owned by :func:`acas_posting.dal.status.mysql_1100_db_error` and is called
    here rather than reimplemented, so this module carries no SQLSTATE table of
    its own.

    ``delete_we_error`` exists because the DELETE paragraphs pass ``995``
    (``WeError.DELETE_SQLSTATE_NOT_00000``) as the code to report on failure
    where the read and write paragraphs leave it at the default - see
    ``ba080-Process-Delete`` [common/slinvoiceMT.cbl:L1240] against
    ``bb200-Insert``'s plainer check.

    No ``COMMIT`` and no ``ROLLBACK`` is issued: the bridge issues neither, the
    connection is opened with the same autocommit posture the COBOL uses
    (:func:`acas_posting.dal.connection.mysql_1000_open`), and rule R-3 forbids
    introducing transaction semantics the original does not have.
    """
    bound = tuple(parameters)
    # WS-Log-Where is 'pic x(231)' [copybooks/wsfnctn.cob:L54] and is written for
    # test logging only.  sanitise_for_log is status.py's redaction pass; the
    # statement text carries no credential, but routing it through the shared
    # helper keeps one policy for every DAL module.
    logging_data.ws_log_where = sanitise_for_log(statement)
    try:
        with execute_statement(connection, statement, bound) as cursor:  # type: ignore[arg-type]
            if fetch:
                # PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT, then
                # MOVE WS-MYSQL-RESULT TO TP-SAINVOICE-REC
                # [common/slinvoiceMT.cbl:L668-L671].  The bridge materialises the
                # whole result set and then walks it; the row count it tests is the
                # STORED count, which is why the rows are collected here rather
                # than streamed.
                fetched = cursor.fetchall()
                rows = tuple(tuple(row) for row in (fetched or ()))
                return StatementOutcome(
                    statement=statement,
                    parameters=bound,
                    count_rows=len(rows),
                    rows=rows,
                )
            affected = cursor.rowcount
            return StatementOutcome(
                statement=statement,
                parameters=bound,
                count_rows=affected if affected and affected > 0 else 0,
            )
    except Exception as exc:  # noqa: BLE001 - the COBOL reports, it does not raise
        # 'call "MySQL_errno" using WS-MYSQL-Error-Number' and its siblings.  The
        # driver surfaces the same three facts on its exception object; where it
        # does not, the defaults keep the shape the COBOL would have seen.
        errno = getattr(exc, "errno", None)
        sql_state = getattr(exc, "sqlstate", None)
        message = getattr(exc, "msg", None) or str(exc)
        status = mysql_1100_db_error(
            errno="" if errno is None else str(errno),
            message=message,
            sql_state="" if sql_state is None else str(sql_state),
            command=statement,
            we_error=delete_we_error,
        )
        _LOG.debug(
            "acas016/slinvoiceMT statement failed: fs_reply=%s we_error=%s "
            "sql_err=%s sql_state=%s",
            status.fs_reply,
            status.we_error,
            status.sql_err,
            redact_for_log(status.sql_state),
        )
        return StatementOutcome(
            statement=statement,
            parameters=bound,
            fs_reply=status.fs_reply,
            we_error=status.we_error,
            sql_err=status.sql_err[:SQL_ERR_WIDTH],
            sql_msg=status.sql_msg[:SQL_MSG_WIDTH],
            sql_state=status.sql_state[:SQL_STATE_WIDTH],
        )


def _apply_statement_status(ctx: "_BridgeContext", outcome: StatementOutcome) -> None:
    """Copy a statement's status pair onto ``File-Access`` and ``Logging-Data``.

    The bridge's error blocks all do the same four moves -
    ``move WS-MYSQL-SqlState to SQL-State``,
    ``move WS-MYSQL-Error-Number to SQL-Err``,
    ``move WS-MYSQL-Error-Message to SQL-Msg`` and the ``FS-Reply``/``WE-Error``
    pair - for example at [common/slinvoiceMT.cbl:L682-L692].  Doing it in one
    place keeps every paragraph's error arm identical, which is what the COBOL's
    copy-pasted blocks amount to.

    A CLEAN statement is not allowed to clear a status the caller already had,
    because ``ba010-Initialise`` deliberately does not clear ``We-Error`` or
    ``Fs-Reply`` [common/slinvoiceMT.cbl:L502-L503].  So only a FAILING outcome
    writes here.
    """
    if outcome.fs_reply == int(FsReply.SUCCESS) and outcome.we_error == int(
        WeError.SUCCESS
    ):
        return
    ctx.file_access.fs_reply = outcome.fs_reply
    ctx.file_access.we_error = outcome.we_error
    logging_data = ctx.logging_data
    logging_data.sql_err = _truncate_move(outcome.sql_err, SQL_ERR_WIDTH)
    logging_data.sql_msg = _truncate_move(outcome.sql_msg, SQL_MSG_WIDTH)
    logging_data.sql_state = _truncate_move(outcome.sql_state, SQL_STATE_WIDTH)


def _fetch_into_group(
    group: _HostVariableGroup,
    bindings: tuple[ColumnBinding, ...],
    row: object,
) -> None:
    """Land one fetched row in its host-variable group, BY POSITION.

    This is ``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT`` followed by the
    host variables in order - 31 of them for the header
    [common/slinvoiceMT.cbl:L746-L780], 14 for the lines [:L2476-L2491].  The C
    interface fills each operand from the correspondingly POSITIONED column, so
    the mapping is ordinal, never by name.

    A short row is tolerated the way the C call is: operands past the end of the
    result keep whatever ``INITIALIZE`` left in them rather than raising, so a
    caller sees zeroes and spaces instead of an exception.  That matches
    ``[common/acas016.cbl:L627]``'s *"Any errors leave it to caller to recover
    from"*.
    """
    values = tuple(row) if isinstance(row, (tuple, list)) else ()
    for index, binding in enumerate(bindings):
        if index >= len(values):
            break
        group.move_in(binding.column_name, values[index])


def bb200_insert(
    connection: object, state: BridgeState, logging_data: LoggingData
) -> StatementOutcome:
    """``bb200-Insert Section.`` [common/slinvoiceMT.cbl:L1543]

    Writes the header row.  All 31 columns are named, in TABLE ORDINAL order,
    because the group was ``INITIALIZE``d by :func:`bb000_hv_load` and every
    column is ``NOT NULL`` with no ``DEFAULT`` - AAP section 0.6.2: *"the Python
    layer must default rather than omit."*  Nothing is ever bound ``None``.

    Note the column order here is NOT the load order.  ``IH-LINES`` is moved 24th
    by the load [common/slinvoiceMT.cbl:L1479] and named 29th by this statement,
    because the host-variable group [:L419] and the frozen column list agree with
    each other and disagree with the copybook [copybooks/slwsinv.cob:L61].
    N-triple-order-mismatch; the two tuples are built independently from the data
    dictionary and neither is derived from the other.

    THIS SECTION INTERPRETS NOTHING.  Verified at
    [common/slinvoiceMT.cbl:L1543-L1946]: the section builds the command text,
    appends ``";"`` then ``X"00"``, performs ``MYSQL-1210-COMMAND`` and ends - with
    the maintainer's own note on his period placement at [:L1943], verbatim::

           .     *> period here

    There is no errno call, no SQLSTATE test and no duplicate-key mapping here.
    All of that lives in :func:`ba070_process_write`
    [common/slinvoiceMT.cbl:L1164-L1180], which is where it is reproduced.  Keeping
    the split means a caller reading the Python sees the same division of
    responsibility the COBOL has.
    """
    # NO 'move nn to ws-No-Paragraph' here.  Verified by counting the moves in
    # [common/slinvoiceMT.cbl:L1543-L1948] (bb200), [:L1949-L2358] (bb300),
    # [:L2849-L3041] (bc200) and [:L3042-L3238] (bc300): ZERO in each.  All four
    # statement sections INHERIT the trace number their caller stamped, so a
    # failure inside bb200-Insert is reported against ba070-Process-Write (10),
    # not against bb200.  N-trace-inherited; do not stamp one here.
    parameters = state.td_sainvoice_rec.as_parameters()
    return _run_command(
        connection,
        logging_data,
        _HEADER_INSERT_SQL,
        parameters,
        fetch=False,
    )


def bb300_update(
    connection: object, state: BridgeState, logging_data: LoggingData
) -> StatementOutcome:
    """``bb300-Update Section.`` [common/slinvoiceMT.cbl:L1949]

    Rewrites the header row.  The SET list is byte-for-byte the same 31 columns
    in the same ordinal order as :func:`bb200_insert` - verified by extracting
    every ``'`COL`='`` literal from both paragraphs - so the primary key is SET as
    well as matched.  Redundant, harmless, reproduced.

    The clause is appended as
    ``" WHERE " FUNCTION TRIM (WS-Where (1:J)) ";"`` [common/slinvoiceMT.cbl:L2336],
    where ``WS-Where`` was built by the caller's own key move; here that is
    :func:`_equality_where` over the header key with the ten-byte key bound.
    """
    # NO 'move nn to ws-No-Paragraph' here.  Verified by counting the moves in
    # [common/slinvoiceMT.cbl:L1543-L1948] (bb200), [:L1949-L2358] (bb300),
    # [:L2849-L3041] (bc200) and [:L3042-L3238] (bc300): ZERO in each.  All four
    # statement sections INHERIT the trace number their caller stamped, so a
    # failure inside bb200-Insert is reported against ba070-Process-Write (10),
    # not against bb200.  N-trace-inherited; do not stamp one here.
    where = _equality_where(_HEADER_KEY_SQL)
    statement = _update_statement(_HEADER_TABLE_SQL, HEADER_COLUMNS, where)
    parameters = (
        *state.td_sainvoice_rec.as_parameters(),
        # FUNCTION TRIM on the WHERE value: the key is a char(10) holding exactly
        # ten significant digits, so the trim is a no-op, but it is the bridge's
        # own construction and the bound value matches it.
        state.td_sainvoice_rec.render_one(HEADER_KEY_COLUMN),
    )
    return _run_command(connection, logging_data, statement, parameters, fetch=False)


def bc200_insert_rg1(
    connection: object, state: BridgeState, logging_data: LoggingData
) -> StatementOutcome:
    """``bc200-Insert-rg1 Section.`` [common/slinvoiceMT.cbl:L2849]

    Writes one line row.  All 14 columns are named, in TABLE ORDINAL order -
    ``IL-INVOICE`` second, ``IL-LINE`` third - which is the opposite of the order
    :func:`bc000_hv_load_rg1` moves them in [common/slinvoiceMT.cbl:L2790-L2791].
    N-lines-loadorder is confined to the load paragraph and does NOT reach the
    statement; both orderings are reproduced in their own place.

    ``IL-INVOICE`` is written here from ``HV1-IL-INVOICE``, which
    :func:`bc100_unload_hvs_rg1` never reads back.  N-il-invoice-never-unloaded:
    the column is write-only from the record's point of view.

    Like :func:`bb200_insert` this section interprets nothing - the duplicate-key
    mapping lives in :func:`bc070_process_write` [common/slinvoiceMT.cbl:L2545-L2560].
    """
    # NO 'move nn to ws-No-Paragraph' here.  Verified by counting the moves in
    # [common/slinvoiceMT.cbl:L1543-L1948] (bb200), [:L1949-L2358] (bb300),
    # [:L2849-L3041] (bc200) and [:L3042-L3238] (bc300): ZERO in each.  All four
    # statement sections INHERIT the trace number their caller stamped, so a
    # failure inside bb200-Insert is reported against ba070-Process-Write (10),
    # not against bb200.  N-trace-inherited; do not stamp one here.
    parameters = state.td_sainv_lines_rec.as_parameters()
    return _run_command(
        connection,
        logging_data,
        _LINES_INSERT_SQL,
        parameters,
        fetch=False,
    )


def bc300_update_rg1(
    connection: object, state: BridgeState, logging_data: LoggingData
) -> StatementOutcome:
    """``bc300-Update-rg1 Section.`` [common/slinvoiceMT.cbl:L3042]

    Rewrites one line row, same 14 columns in the same ordinal order as
    :func:`bc200_insert_rg1`, matched on ``IL-LINE-KEY``.  The bound key comes
    from the host-variable group rather than from the record, because the group is
    what the statement's own SET list is built from and the two must agree.
    """
    # NO 'move nn to ws-No-Paragraph' here.  Verified by counting the moves in
    # [common/slinvoiceMT.cbl:L1543-L1948] (bb200), [:L1949-L2358] (bb300),
    # [:L2849-L3041] (bc200) and [:L3042-L3238] (bc300): ZERO in each.  All four
    # statement sections INHERIT the trace number their caller stamped, so a
    # failure inside bb200-Insert is reported against ba070-Process-Write (10),
    # not against bb200.  N-trace-inherited; do not stamp one here.
    where = _equality_where(_LINES_KEY_SQL)
    statement = _update_statement(_LINES_TABLE_SQL, LINE_COLUMNS, where)
    parameters = (
        *state.td_sainv_lines_rec.as_parameters(),
        state.td_sainv_lines_rec.render_one(LINES_KEY_COLUMN),
    )
    return _run_command(connection, logging_data, statement, parameters, fetch=False)


# ---------------------------------------------------------------------------
# The bridge: slinvoiceMT
# ---------------------------------------------------------------------------
# 'ba-Process-RDBMS' and everything below it.  These functions ARE the bridge
# program: one per COBOL paragraph, called in source order, sharing one mutable
# context exactly as the COBOL paragraphs share Working-Storage and Linkage.


@dataclass(slots=True)
class _BridgeContext:
    """What every bridge paragraph can see - the COBOL's shared storage.

    A COBOL paragraph reaches ``File-Access``, ``ACAS-DAL-Common-data`` and
    ``WS-Invoice-Record`` because they are Linkage, and reaches ``WS-Where``,
    the two host-variable groups and the cursor flags because they are
    Working-Storage.  Bundling them into one object passed to every paragraph
    keeps that visibility while making it explicit, rather than reproducing
    COBOL's implicit globals as Python module state - which would break the
    determinism requirement of AAP section 0.6.6 the moment two runs shared a
    process.
    """

    connection: object
    file_access: FileAccess
    dal_common: AcasDalCommonData
    state: BridgeState
    buffer: InvoiceBuffer
    #: ``System-Record``.  The bridge itself reads its credentials from the
    #: ``RDB-Data`` block inside ``File-Access`` [copybooks/wsfnctn.cob:L56-L62],
    #: which is how ``ba020-Process-Open`` fills ``WS-MYSQL-BASE-NAME`` and its
    #: five siblings [common/slinvoiceMT.cbl:L574-L599].
    #: :func:`acas_posting.dal.connection.mysql_1000_open` takes the system record
    #: because it owns that whole load, so it is carried here to hand over.
    system_record: SystemRecord | None = None
    #: ``K``/``L`` - the key offset and length the current paragraph selected
    #: from ``KeyOfReference`` [common/slinvoiceMT.cbl:L305-L310].  Held on the
    #: context because the paragraphs genuinely share them: ``bc051-Fetch-RG1``
    #: reads ``WS-Invoice-Record (K:L)`` [:L2506] using the ``K``/``L`` that
    #: ``bc050`` set [:L2399-L2400].
    k: int = 1
    ell: int = 10
    #: ``K2``/``L2`` - the second pair, used only by ``ba060``'s RG1 block
    #: [common/slinvoiceMT.cbl:L1057-L1058].
    k2: int = 1
    ell2: int = 10
    #: ``return-code`` - the fetch's own signal, ``-1`` meaning no more data
    #: [common/slinvoiceMT.cbl:L787].
    return_code: int = 0

    @property
    def logging_data(self) -> LoggingData:
        """``Logging-Data`` [copybooks/wsfnctn.cob:L44-L55], reached through File-Access."""
        return self.file_access.logging_data


def _key_of_reference(ctx: _BridgeContext, kor_x1: int) -> KeyOfReference:
    """``set KOR-x1 to n`` then ``move KOR-offset/KOR-length (KOR-x1) to K/L``.

    ``[common/slinvoiceMT.cbl:L296-L310]`` declares the two-entry table; every
    paragraph that builds a clause selects an entry and copies its offset and
    length.  Index 1 is ``SINVOICE-KEY``, index 2 is ``IL-LINE-KEY``, and both
    carry offset 0001 length 0010 [:L298], [:L302] because both are the first ten
    bytes of the SAME 137-byte union buffer.

    The table itself comes from :mod:`acas_posting.dal.cursor_state` rather than
    being retyped here, so the key metadata has one home.
    """
    # KOR-x1 is a COBOL INDEXED BY name, so it is 1-relative; KEYS_OF_REFERENCE is
    # keyed by that same 1-relative ordinal rather than by a Python offset, so `set
    # KOR-x1 to 2` reads as `KEYS_OF_REFERENCE[2]` and the code matches the COBOL
    # it transcribes.
    entry = KEYS_OF_REFERENCE[kor_x1]
    if kor_x1 == 1:
        ctx.k, ctx.ell = entry.kor_offset, entry.kor_length
    else:
        # ba060 keeps the RG1 pair separately in K2/L2 [:L1057-L1058] because its
        # header block is still using K/L; every other rg1 paragraph reuses K/L.
        ctx.k2, ctx.ell2 = entry.kor_offset, entry.kor_length
        ctx.k, ctx.ell = entry.kor_offset, entry.kor_length
    return entry


def _record_key_slice(ctx: _BridgeContext, offset: int, length: int) -> str:
    """``WS-Invoice-Record (K:L)`` - a reference-modified slice of the buffer.

    Every clause value in this bridge is taken this way rather than from a named
    field, which is precisely why the union buffer works: the first ten bytes are
    the key whichever of the three redefinitions is currently in view
    [copybooks/slwsinv2.cob:L27], [:L38], [:L91].  COBOL's reference modification
    is 1-based, so offset 1 length 10 is ``[0:10]`` here.
    """
    return ctx.buffer.ws_invoice_key[offset - 1 : offset - 1 + length]


def _move_to_ws_file_key(ctx: _BridgeContext, text: str) -> None:
    """``move <literal> to WS-File-Key`` - a MOVE into ``pic x(64)``.

    ``WS-File-Key`` is 64 characters [copybooks/wsfnctn.cob:L52], and a COBOL MOVE
    into an alphanumeric field left-justifies, pads with spaces and TRUNCATES
    anything longer.  Reproduced exactly, because the field's contents are logged
    and a log comparison would notice either a missing pad or an un-truncated
    overflow.  Every ``WS-File-Key`` literal in the bridge and the handler goes
    through here: ``"OPEN SL INVOICE"`` [common/slinvoiceMT.cbl:L605],
    ``"CLOSE SL INVOICE"`` [:L615], ``"0000000000"`` [:L674], ``"No Data"``
    [:L695], ``"EOF"`` [:L789], ``"EOF2"`` [:L805], ``"EOF3"`` [:L816] and the
    handler's own ``"EOF"`` [common/acas016.cbl:L388].
    """
    ctx.logging_data.ws_file_key = _truncate_move(text, _WS_FILE_KEY_WIDTH)


def _move_to_ws_log_where(ctx: _BridgeContext, text: str) -> None:
    """``move WS-Where (1:J) to WS-Log-Where`` - a MOVE into ``pic x(231)``.

    ``[common/slinvoiceMT.cbl:L657]`` and the same statement in every
    clause-building paragraph, each carrying the comment
    ``*>  For test logging``.  Same left-justify / pad / truncate rules as
    :func:`_move_to_ws_file_key`, at the wider size
    [copybooks/wsfnctn.cob:L54].
    """
    ctx.logging_data.ws_log_where = _truncate_move(text, _WS_LOG_WHERE_WIDTH)


def ba010_initialise(ctx: _BridgeContext) -> None:
    """``ba010-Initialise.`` [common/slinvoiceMT.cbl:L498]

    ``[common/slinvoiceMT.cbl:L500-L503]``, VERBATIM - and note what is commented
    out::

         move     zero   to SQL-State.
    *>
    *>                        We-Error
    *>                        Fs-Reply.

    N-noinit, SECOND INSTANCE.  ``We-Error`` and ``Fs-Reply`` are commented OUT of
    the bridge's initialise, exactly as they are commented out of the handler's at
    [common/acas016.cbl:L287-L288].  Both layers deliberately leave the caller's
    previous status in place, so a call that takes an early exit can return a
    status it never set.  Reproduced in both places; do NOT zero them.

    Everything at [:L505-L511] IS cleared, and is cleared here.
    """
    logging_data = ctx.logging_data
    # move zero to SQL-State.  [common/slinvoiceMT.cbl:L500]
    logging_data.sql_state = "0".ljust(SQL_STATE_WIDTH)
    # NOT cleared, deliberately: ctx.file_access.we_error and .fs_reply.
    # [common/slinvoiceMT.cbl:L502-L503] have them commented out.
    #
    # move spaces to WS-MYSQL-Error-Message WS-MYSQL-Error-Number WS-Log-Where
    #                WS-File-Key SQL-Msg SQL-Err.   [:L505-L511]
    logging_data.ws_log_where = " " * _WS_LOG_WHERE_WIDTH
    logging_data.ws_file_key = " " * _WS_FILE_KEY_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = " " * SQL_ERR_WIDTH


def ba020_process_open(ctx: _BridgeContext) -> None:
    """``ba020-Process-Open.`` [common/slinvoiceMT.cbl:L568]

    Header comment, verbatim: ``*> dry tested - no rg01 requirements.``

    The COBOL builds six null-terminated strings from ``DB-Schema``, ``DB-Host``,
    ``DB-UName``, ``DB-UPass``, ``DB-Port`` and ``DB-Socket``
    [common/slinvoiceMT.cbl:L574-L599] and then performs
    ``MYSQL-1000-OPEN THRU MYSQL-1090-EXIT``.  That whole sequence - including the
    credential load and the record-length guard - is owned by
    :func:`acas_posting.dal.connection.mysql_1000_open` and is CALLED here, not
    duplicated: the agent brief is explicit that ``dal/connection.py`` owns it.

    ⚠ THERE IS NO OPEN-OUTPUT BEHAVIOUR.  Neither this paragraph nor the handler
    contains an ``if fn-Open and fn-output`` block - verified by searching both
    files - so opening for output is a PLAIN OPEN that deletes nothing from either
    table.  This is the fourth of four Open-Output semantics across the handler
    family and the one that does least; ``acas008``'s coercion is NOT ported here.
    N-noopenoutput.

    ⚠ NEVER RAISES, INCLUDING FOR A REFUSED CONNECTION.
    ``[common/acas016.cbl:L627]``: *"Any errors leave it to caller to recover from"*.
    ``dal/connection.py`` enforces two POLICIES the COBOL does not have -
    :class:`~acas_posting.dal.connection.FrozenPlaceholderCredentialsError` for the
    placeholder credentials frozen into ``SYSTEM-REC``
    [copybooks/wssystem.cob:L138-L139], and
    :class:`~acas_posting.dal.connection.InsecureTransportError` for an unencrypted
    hop to a non-local server - and both are raised, not returned.  A raise would
    break this module's contract and would abort a posting run where the COBOL
    merely reports a failed open, so each is CAUGHT and rendered as the failed-open
    status pair the COBOL produces: ``FS-Reply 99`` with ``WE-Error 911``
    (``RDB-INIT-ERROR``), the refusal's own text preserved in ``SQL-Msg`` so nothing
    is hidden from the caller.  The policy is honoured - the connection is still
    refused - only its delivery changes from an exception to a status.
    """
    logging_data = ctx.logging_data
    # move 1 to ws-No-Paragraph.  [common/slinvoiceMT.cbl:L595]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba020-Process-Open"]
    try:
        outcome = mysql_1000_open(
            ctx.system_record,
            ws_no_paragraph=logging_data.ws_no_paragraph,
            we_error=ctx.file_access.we_error,
            transport=None,
        )
    except ConnectionPolicyError as refused:
        # A connection.py policy refusal.  Rendered as the COBOL's failed-open
        # status rather than propagated, per [common/acas016.cbl:L627].
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        ctx.file_access.we_error = int(WeError.RDB_INIT_ERROR)
        logging_data.sql_err = " " * SQL_ERR_WIDTH
        logging_data.sql_msg = _truncate_move(
            sanitise_for_log(str(refused)), SQL_MSG_WIDTH
        )
        logging_data.sql_state = " " * SQL_STATE_WIDTH
        ctx.connection = None
        # if fs-reply not = zero go to ba999-end.  [:L597-L598]  Class 3.
        ba999_end(ctx)
        return
    outcome.apply_to_logging_data(logging_data)
    ctx.file_access.fs_reply = outcome.fs_reply
    ctx.file_access.we_error = outcome.we_error
    ctx.connection = outcome.connection
    # if fs-reply not = zero go to ba999-end.  [common/slinvoiceMT.cbl:L597-L598]
    # Class 3 - section exit.
    if ctx.file_access.fs_reply != int(FsReply.SUCCESS):
        ba999_end(ctx)
        return
    # move "OPEN SL INVOICE" to WS-File-Key   [common/slinvoiceMT.cbl:L605]
    _move_to_ws_file_key(ctx, "OPEN SL INVOICE")
    # set Cursor-Not-Active to true            [:L606]
    ctx.state.header_cursor().set_cursor_not_active()
    ba999_end(ctx)


def ba030_process_close(ctx: _BridgeContext) -> None:
    """``ba030-Process-Close.`` [common/slinvoiceMT.cbl:L610]

    ``[common/slinvoiceMT.cbl:L611-L621]``, verbatim::

         if      Cursor-Active
                 perform ba998-Free.
    *>
         move     2 to ws-No-Paragraph.
         move    "CLOSE SL INVOICE" to WS-File-Key.

    Only the PRIMARY cursor is tested and freed.  The RG1 cursor is not, because
    the paragraph that would free it - ``bc998-Free`` - is never called from
    anywhere; see :func:`bc998_free`.  N-bc998-never-called.
    """
    logging_data = ctx.logging_data
    # if Cursor-Active perform ba998-Free.  [common/slinvoiceMT.cbl:L611-L612]
    if ctx.state.header_cursor().cursor_active():
        ba998_free(ctx)
    # move 2 to ws-No-Paragraph.  [common/slinvoiceMT.cbl:L614]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba030-Process-Close"]
    _move_to_ws_file_key(ctx, "CLOSE SL INVOICE")
    # PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT  [:L620]
    mysql_1980_close(ctx.connection)  # type: ignore[arg-type]
    ctx.connection = None
    ba999_end(ctx)


def ba040_process_read_next(ctx: _BridgeContext) -> None:
    """``ba040-Process-Read-Next.`` [common/slinvoiceMT.cbl:L624]

    Header comment: ``*> dry test.. - Has rg01 requirements.``  The maintainer's
    design note at [:L626-L633] explains the whole two-table walk, verbatim::

    *>  Here we have for a given key first read and transfer a inv header
    *>   then pass on for the same key all body lines all one at
    *>     a time. This will mean that the DAL has to keep track of the
    *>       original request. so lets look at for any given invoice read in
    *>           then read body into WS and pass back.

    Opens the walk ONLY when the cursor is not already active, then FALLS THROUGH
    into :func:`ba041_reread`.  The fall-through is real - there is no ``go to``
    between [:L704] and [:L706] - and it is reproduced by calling ``ba041_reread``
    at the end rather than by duplicating its body.

    On an empty table the paragraph sets ``FS-Reply`` 10 AND ``WE-Error`` 10, with
    the maintainer's own doubt attached at [:L694], verbatim:
    ``*> should be 0 'JIC' likewise the others``.  Both tens are reproduced.
    """
    logging_data = ctx.logging_data
    cursor = ctx.state.header_cursor()
    # if Cursor-Not-Active ...  [common/slinvoiceMT.cbl:L635]
    if cursor.cursor_not_active():
        # set KOR-x1 to 1  *> 1 = Primary   [:L636]
        entry = _key_of_reference(ctx, 1)
        where = _sequential_start_where(quote_identifier(entry.column_name))
        _move_to_ws_log_where(ctx, where)
        # move 3 to ws-No-Paragraph  [:L658]
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE[
            "ba040-Process-Read-Next"
        ]
        statement = _select_all(_HEADER_TABLE_SQL, where)
        # '"0000000000"' delimited by size  *> for 1st time active only  [:L647]
        outcome = _run_command(
            ctx.connection,
            logging_data,
            statement,
            (_SEQUENTIAL_LOW_KEY,),
            fetch=True,
        )
        # move "0000000000" to WS-File-Key  [:L674]
        _move_to_ws_file_key(ctx, _SEQUENTIAL_LOW_KEY)
        # PERFORM MYSQL-1220-STORE-RESULT / MOVE WS-MYSQL-RESULT TO
        # TP-SAINVOICE-REC  [common/slinvoiceMT.cbl:L669-L671].  The rows are
        # POSITIONAL tuples; CursorState stores whatever sequence it is handed and
        # its annotation naming Mapping is narrower than its behaviour, so the
        # frozen dependency is used as-is rather than modified.
        stored = cursor.store_result(outcome.rows)  # type: ignore[arg-type]
        _apply_statement_status(ctx, outcome)
        # if WS-MYSQL-Count-Rows = zero ...  [:L680]
        if stored == 0:
            # move 10 to fs-reply / move 10 to WE-Error
            # *> should be 0 'JIC' likewise the others   [:L693-L694]
            ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
            ctx.file_access.we_error = int(FsReply.END_OF_FILE)
            # move "No Data" to WS-File-Key  [:L695]
            _move_to_ws_file_key(ctx, "No Data")
            # go to ba999-End  *> can clear the dup code after testing  [:L696]
            # Class 3 - section exit.
            ba999_end(ctx)
            return
        # set Cursor-Active to true  [:L698]
        cursor.set_cursor_active()
        # The log line is built with the row count edited into WS-Temp-ED-Row,
        # then the literal " recs for INVOICE-REC Table" - note "INVOICE-REC",
        # which is NOT the table's name (SAINVOICE-REC).  [:L699-L702]
        _move_to_ws_file_key(ctx, f"> 0 got cnt={stored} recs for INVOICE-REC Table")
        # perform ba999-End  *> log it   [:L703]
        ba999_end(ctx)
    # FALL-THROUGH into ba041-Reread.  There is no transfer of control at
    # [common/slinvoiceMT.cbl:L704-L706] - the 'end-if.' simply ends and the next
    # paragraph runs.  AAP section 0.4.2 requires fall-through be made explicit,
    # so it is an explicit call.
    ba041_reread(ctx)


def ba041_reread(ctx: _BridgeContext) -> None:
    """``ba041-Reread.`` [common/slinvoiceMT.cbl:L706]

    ⭐ THIS IS THE ONLY PLACE FUNCTION 34 DIFFERS FROM FUNCTION 3.  The dispatch
    sends both to the same paragraph [common/slinvoiceMT.cbl:L523-L526], and the
    distinction is re-derived here from ``File-Function``
    ``[common/slinvoiceMT.cbl:L722-L723]``, verbatim::

         if       FN-Read-Next-Header
                  go to ba042-Fetch.

    ``fn-Read-Next-Header`` is 34 [copybooks/wsfnctn.cob:L105].  Its whole effect is
    to BYPASS line processing and fetch the next HEADER, which is what makes it
    useful to a caller that wants headers only.

    The line-walk branch [:L725-L741] is where the two-table cursor is driven:
    ``WS-Last-Read-Line`` is compared against ``WS-Actual-Lines-In-Row``, and if
    there are lines left it synthesises the next line key by putting
    ``WS-Last-Read-Line + 1`` into ``WS-Sih-Test`` and ``WS-Last-Read-Invoice``
    into ``WS-Sih-Invoice`` - writing the LINE number into a field named for the
    HEADER's test digit, which is the other half of N-lines-cursor-from-ih-test.

    The not-found arm carries the maintainer's own disbelief at [:L737],
    verbatim: ``*> This should NOT happen``.
    """
    logging_data = ctx.logging_data
    # move spaces to WS-Log-Where.  move 4 to ws-No-Paragraph.
    # move zero to return-code.   [common/slinvoiceMT.cbl:L710-L712]
    _move_to_ws_log_where(ctx, "")
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba041-Reread"]
    ctx.return_code = 0
    # if WS-Last-Read-Invoice = zero  *> DALS Not yet called
    #    go to ba042-Fetch.           *>  so get header rec.   [:L716-L717]
    # Class 4 - sibling re-dispatch: a named call followed by an explicit return.
    if ctx.state.ws_last_read_invoice == 0:
        ba042_fetch(ctx)
        return
    # if FN-Read-Next-Header go to ba042-Fetch.  [:L722-L723]
    # Class 4 again.  THE ONLY BEHAVIOURAL DIFFERENCE BETWEEN 3 AND 34.
    if ctx.file_access.file_function == int(FileFunction.READ_NEXT_HEADER):
        ba042_fetch(ctx)
        return
    # if WS-Last-Read-Line < WS-Actual-Lines-In-Row  [:L725]
    if ctx.state.ws_last_read_line < ctx.state.ws_actual_lines_in_row:
        # add 1 WS-Last-Read-Line giving WS-Sih-Test        [:L726]
        # move WS-Last-Read-Invoice to WS-Sih-Invoice       [:L727]
        # The LINE number goes into WS-Sih-TEST.  Same field the header's
        # IH-TEST seeded at [:L1538].  N-lines-cursor-from-ih-test.
        ctx.buffer.ws_sih_test = ctx.state.ws_last_read_line + 1
        ctx.buffer.ws_sih_invoice = ctx.state.ws_last_read_invoice
        ctx.buffer.sync_key_into_views()
        # perform bc050-Process-Read-Indexed thru bc059-Exit  [:L728]
        bc050_process_read_indexed(ctx)
        # if fs-Reply not = zero  *> = 23  *> no row found   [:L729]
        if ctx.file_access.fs_reply != int(FsReply.SUCCESS):
            # initialise WS-Invoice-Record   [:L730]
            # The WHOLE record, key included - which is what makes the STRING on
            # the next line read ten zeros.  See
            # `_initialise_ws_invoice_record`.
            _initialise_ws_invoice_record(ctx.buffer)
            # string WS-Invoice-Key " Not Found" into WS-File-Key  [:L731-L735]
            _move_to_ws_file_key(ctx, f"{ctx.buffer.ws_invoice_key} Not Found")
            # go to ba999-End  *> This should NOT happen   [:L736-L737]
            ba999_end(ctx)
            return
        # else *> got a row: move WS-Sih-Test to WS-Last-Read-Line  [:L738-L739]
        ctx.state.ws_last_read_line = ctx.buffer.ws_sih_test
        ba999_end(ctx)
        return
    # end-if.  *> Not, so get next invoice Header rec   [:L741-L744]
    # FALL-THROUGH into ba042-Fetch, made explicit.
    ba042_fetch(ctx)


def ba042_fetch(ctx: _BridgeContext) -> None:
    """``ba042-Fetch.`` [common/slinvoiceMT.cbl:L744]

    ``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT`` and then all 31 host
    variables BY POSITION [common/slinvoiceMT.cbl:L746-L780].  That operand list
    was extracted and diffed against the host-variable group declaration
    [:L391-L421]: IDENTICAL, and both equal the frozen column ordinal order.  The
    positional read is therefore reproduced positionally, against
    :data:`HEADER_COLUMNS`.

    Three EOF-ish exits, each with its own ``WS-File-Key`` marker so a log can
    tell them apart: ``"EOF"`` on ``return-code = -1`` [:L787-L792], ``"EOF2"``
    inside the zero-row branch [:L805], and ``"EOF3"`` on the
    ``fs-reply = 10`` re-test that carries the comment
    ``*> should not happen as tested prior`` [:L814-L817].  All three set
    ``FS-Reply`` 10, and the first two set ``WE-Error`` 10 as well - again with
    ``*> should be 0 likewise the others`` attached at [:L789].
    """
    logging_data = ctx.logging_data
    cursor = ctx.state.header_cursor()
    row = cursor.fetch_record()
    # if return-code = -1  *> no more data so free cursor & return   [:L787]
    if row is None:
        ctx.return_code = -1
        # move 10 to fs-Reply WE-Error  *> should be 0 likewise the others
        ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
        ctx.file_access.we_error = int(FsReply.END_OF_FILE)
        # move "EOF" to WS-File-Key.  set Cursor-Not-Active to true.  [:L790-L791]
        _move_to_ws_file_key(ctx, "EOF")
        cursor.set_cursor_not_active()
        ba999_end(ctx)
        return
    # if WS-MYSQL-Count-Rows = zero  *> no data but should not happen here  [:L795]
    if cursor.count_rows == 0:
        # initialize WS-Invoice-Record with filler   [:L804]
        # N-initialize: 'with filler' HERE, plain at [:L1496].  Two semantics in
        # one bridge; both reproduced in their own place - and in THIS model they
        # coincide, for the reason `_initialise_ws_invoice_record` records.
        _initialise_ws_invoice_record(ctx.buffer)
        _move_to_ws_file_key(ctx, "EOF2")
        ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
        ctx.file_access.we_error = int(FsReply.END_OF_FILE)
        cursor.set_cursor_not_active()
        ba999_end(ctx)
        return
    # if fs-reply = 10  *> should not happen as tested prior   [:L814]
    if ctx.file_access.fs_reply == int(FsReply.END_OF_FILE):
        cursor.set_cursor_not_active()
        _move_to_ws_file_key(ctx, "EOF3")
        ba999_end(ctx)
        return
    # The 31-operand positional fetch: each column of the row lands in its own
    # host variable, in ordinal order.   [:L746-L780]
    _fetch_into_group(ctx.state.td_sainvoice_rec, HEADER_COLUMNS, row)
    # perform bb100-UnloadHVs  *> transfer/move HV vars to Record layout  [:L819]
    bb100_unload_hvs(ctx.state, ctx.buffer)
    # move WS-Invoice-Key to WS-File-Key.  [:L820]
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    # move zero to fs-reply WE-Error.  [:L821]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    ba999_end(ctx)


def ba050_process_read_indexed(ctx: _BridgeContext) -> None:
    """``ba050-Process-Read-Indexed.`` [common/slinvoiceMT.cbl:L824]

    ``[common/slinvoiceMT.cbl:L826-L831]``, verbatim - the header/line
    discriminator that every write-side paragraph also uses::

    *>  Test what the key end is (Line or test) & if not zero
    *>   we do RG1 insead of primary table
    *>
         if       WS-Sih-test not = zero     *> if true  process line RG
                  perform  bc050-Process-Read-Indexed  thru bc059-Exit
                  go       to ba999-exit.

    ``WS-Sih-Test`` - the header record's own two-digit test field - is what
    decides WHICH TABLE is read.  Non-zero means "this is a line".  The same test
    appears at ``ba070`` [:L1149], ``ba080`` [:L1192] and ``ba090`` [:L1359], so a
    single field in the union buffer routes all four verbs.  No other
    discriminator exists.

    On a fetch that returns nothing the paragraph distinguishes two cases by
    ``WE-Error``: ``990`` when the driver reported an errno and ``989`` when it did
    not [:L925-L932], with ``FS-Reply`` 23 either way.  ``989`` appears in no other
    handler module.

    The tail is subtle and is reproduced exactly [:L938-L944]: unload, put
    ``HV-SINVOICE-KEY`` into ``WS-File-Key``, ``perform ba999-End`` to LOG the
    status just set, and only THEN zero ``FS-Reply``/``WE-Error`` and free the
    cursor.  So the log records a status the caller never sees.
    """
    logging_data = ctx.logging_data
    # if WS-Sih-test not = zero -> process the line table instead.  [:L829-L831]
    # Class 4 - sibling re-dispatch then explicit return.
    if ctx.buffer.ws_sih_test != 0:
        bc050_process_read_indexed(ctx)
        return
    entry = _key_of_reference(ctx, 1)
    where = _equality_where(quote_identifier(entry.column_name))
    _move_to_ws_log_where(ctx, where)
    # move 5 to ws-No-Paragraph  [:L855]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE[
        "ba050-Process-Read-Indexed-select"
    ]
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _select_all(_HEADER_TABLE_SQL, where),
        (key_value,),
        fetch=True,
    )
    cursor = ctx.state.header_cursor()
    stored = cursor.store_result(outcome.rows)  # type: ignore[arg-type]
    _apply_statement_status(ctx, outcome)
    # if WS-MYSQL-Count-Rows = zero
    #    move 23 to fs-Reply  *> could also be 21 or 14
    #    move zero to WE-Error
    #    go to ba998-Free      [:L872-L876]
    if stored == 0:
        ctx.file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
        ctx.file_access.we_error = int(WeError.SUCCESS)
        ba998_free(ctx)
        return
    # move 6 to ws-No-Paragraph  [:L877]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE[
        "ba050-Process-Read-Indexed-fetch"
    ]
    row = cursor.fetch_record()
    # if WS-MYSQL-Count-Rows not > zero  [:L920]
    if row is None:
        if str(outcome.sql_err).strip() not in ("", "0"):
            # move 990 to WE-Error  [:L925]
            ctx.file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
        else:
            # move 989 to WE-Error / zero SQL-Err / spaces SQL-Msg  [:L930-L932]
            ctx.file_access.we_error = READ_INDEXED_NO_ERRNO_WE_ERROR
            logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
            logging_data.sql_msg = " " * SQL_MSG_WIDTH
        # move 23 to fs-reply / move spaces to WS-File-Key / go to ba998-Free
        ctx.file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
        _move_to_ws_file_key(ctx, "")
        ba998_free(ctx)
        return
    _fetch_into_group(ctx.state.td_sainvoice_rec, HEADER_COLUMNS, row)
    # perform bb100-UnloadHVs  [:L937]
    bb100_unload_hvs(ctx.state, ctx.buffer)
    # move HV-SINVOICE-KEY to WS-File-Key.  [:L938]
    # ⭐ The header key host variable IS read - but only for LOGGING.  It is still
    # never moved into any WS-Sih-* field, which is N-header-key-not-unloaded.
    _move_to_ws_file_key(ctx, str(ctx.state.td_sainvoice_rec[HEADER_KEY_COLUMN]))
    # perform ba999-End.   *> logs the status set above   [:L939]
    ba999_end(ctx)
    # move zero to FS-Reply WE-Error.  perform ba998-Free.  [:L941-L942]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ba998_free(ctx)


def ba060_process_start(ctx: _BridgeContext) -> None:
    """``ba060-Process-Start.`` [common/slinvoiceMT.cbl:L946]

    Header comment, verbatim, doubts and all::

     ba060-Process-Start.    *>  coded for header & lines [ NEEDED ? check all calling code ].
    *>                           Need to see if bcnn-Read-Next is needed
    *>                           if not than rg1 processing can be removed.

    ⭐⭐ THE ACCESS-TYPE GUARD CONTRADICTS THE HANDLER'S.
    ``[common/slinvoiceMT.cbl:L952-L956]``, verbatim::

         if       access-type < 5 or > 8                   *> not using not < or not >
                  move 99 to FS-Reply
                  move 997 to WE-Error                     *> Invalid calling parameter settings     997
                  go to ba999-end
         end-if

    The bridge rejects anything outside 5..8, yet the ``evaluate`` immediately
    below still carries ``when 9  *> fn-not-greater-than`` [:L980-L981] - a branch
    the guard makes UNREACHABLE.  Meanwhile the HANDLER's own START guard admits
    5..9 [common/acas016.cbl:L446-L454].  So ``fn-not-greater-than`` passes the
    handler and dies at the bridge with 99/997.  N-access-type-9-unreachable; both
    guards reproduced as written, neither harmonised.

    ⭐ THE HEADER AND RG1 BLOCKS ARE NOT SYMMETRIC.  The header sets the cursor
    active on rows but never sets it INACTIVE on zero rows [:L1027-L1029]; the RG1
    block sets both [:L1099-L1103].  Reproduced.

    ⭐ THE RG1 CLAUSE DOES NOT QUOTE ITS VALUE.  See :func:`_start_where`.
    """
    logging_data = ctx.logging_data
    access_type = ctx.file_access.access_type
    # if access-type < 5 or > 8  *> not using not < or not >   [:L952]
    low, high = BRIDGE_START_ACCESS_TYPE_RANGE
    if access_type < low or access_type > high:
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        # move 997 to WE-Error  *> Invalid calling parameter settings   997
        ctx.file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        ba999_end(ctx)
        return
    # if Cursor-Active perform ba998-Free.  [:L961-L962]
    if ctx.state.header_cursor().cursor_active():
        ba998_free(ctx)
    # ---- Header records first.  [:L964] ----
    header_entry = _key_of_reference(ctx, 1)
    # The evaluate at [:L972-L983] maps Access-Type to a three-character
    # MOST-Relation.  cursor_state owns that table, so it is called rather than
    # retyped; 'padded=True' returns the 'pic xxx' form the COBOL moves.
    relation = start_relation_for(access_type, padded=True)
    ctx.state.most_relation = relation
    header_where = _start_where(
        quote_identifier(header_entry.column_name), relation, quote_value=True
    )
    ctx.state.ws_where = header_where
    _move_to_ws_log_where(ctx, header_where)
    header_key = _record_key_slice(ctx, ctx.k, ctx.ell)
    _move_to_ws_file_key(ctx, header_key)
    # move 8 to ws-No-Paragraph  [:L1009]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba060-Process-Start-header"]
    header_outcome = _run_command(
        ctx.connection,
        logging_data,
        _select_all(_HEADER_TABLE_SQL, header_where),
        # QUOTED in the COBOL, so bound as TEXT here.  [:L995-L997]
        (header_key,),
        fetch=True,
    )
    header_cursor = ctx.state.header_cursor()
    header_cursor.most_relation = relation
    header_rows = header_cursor.store_result(header_outcome.rows)  # type: ignore[arg-type]
    _apply_statement_status(ctx, header_outcome)
    # if WS-MYSQL-Count-Rows not zero set Cursor-Active to true end-if  [:L1027-L1029]
    if header_rows != 0:
        header_cursor.set_cursor_active()
        header_cursor.position_at(header_key)
    # ⭐ NO 'else set Cursor-Not-Active' here.  The header cursor is left as it
    # was found on an empty result.  Asymmetric with the RG1 block below; that
    # asymmetry is the COBOL's and is preserved.
    if header_rows == 0:
        # move 21 to fs-reply  *> this may need changing for val in WE-Error!!
        # move zero to WE-Error    [:L1039-L1040]
        ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
        ctx.file_access.we_error = int(WeError.SUCCESS)
    else:
        ctx.file_access.fs_reply = int(FsReply.SUCCESS)
        ctx.file_access.we_error = int(WeError.SUCCESS)
        _move_to_ws_file_key(
            ctx, f"{relation}{header_key} got {header_rows} recs"
        )
    # perform ba999-End.  *> Logging only   [:L1050]
    ba999_end(ctx)
    # ---- Extra code for RG1 table -- Line Body Items - ASSUMING here so ?  [:L1052] ----
    line_entry = _key_of_reference(ctx, 2)
    line_where = _start_where(
        quote_identifier(line_entry.column_name), relation, quote_value=False
    )
    ctx.state.ws_where_2 = line_where
    # Save the pointers (SAINVOICE-REC) [ and we will restore at end ]  [:L1075-L1078]
    ctx.state.save_result_rows = header_cursor.stored_rows
    ctx.state.save_count_rows = header_rows
    # move 57 to ws-No-Paragraph  [:L1081]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba060-Process-Start-rg1"]
    line_key = _record_key_slice(ctx, ctx.k2, ctx.ell2)
    line_outcome = _run_command(
        ctx.connection,
        logging_data,
        _select_all(_LINES_TABLE_SQL, line_where),
        # ⭐ UNQUOTED in the COBOL [:L1065], so bound as a NUMBER here.  This makes
        # MySQL coerce the char(10) column numerically instead of comparing text.
        # N-rg1-unquoted-start-value.
        (_digits_or_zero(line_key),),
        fetch=True,
    )
    line_cursor = ctx.state.line_cursor()
    line_cursor.most_relation = relation
    line_rows = line_cursor.store_result(line_outcome.rows)  # type: ignore[arg-type]
    # if WS-MYSQL-Count-Rows not zero set Cursor-Active-2 else
    # set Cursor-Not-Active-2 end-if   [:L1099-L1103]  -- BOTH branches, unlike above.
    if line_rows != 0:
        line_cursor.set_cursor_active()
        line_cursor.position_at(line_key)
    else:
        line_cursor.set_cursor_not_active()
    _apply_statement_status(ctx, line_outcome)
    if line_rows == 0:
        ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
        ctx.file_access.we_error = int(WeError.SUCCESS)
    else:
        ctx.file_access.fs_reply = int(FsReply.SUCCESS)
        ctx.file_access.we_error = int(WeError.SUCCESS)
        _move_to_ws_file_key(
            ctx, f"{relation}{line_key} got {line_rows} recs RG1 (Lines)"
        )
    # Save pointer and count for RG1 also Cursor2 active (or not)  [:L1128-L1133]
    ctx.state.save_result_rows_rg1 = line_cursor.stored_rows
    ctx.state.save_count_rows_rg1 = line_rows
    # Restore the Primary table pointer & row count.  [:L1137-L1138]
    header_cursor.store_result(ctx.state.save_result_rows)  # type: ignore[arg-type]
    ba999_end(ctx)


def _clear_sql_status(ctx: _BridgeContext) -> None:
    """``move zero to FS-Reply WE-Error SQL-State`` + ``spaces to SQL-Msg`` + ``zero to SQL-Err``.

    The five-move preamble the write-side paragraphs run before issuing their
    statement - ``ba070-Process-Write`` [common/slinvoiceMT.cbl:L1157-L1162] and
    ``bc070-Process-Write`` [:L2526-L2529].  Note this is the OPPOSITE of
    ``ba010-Initialise``, which deliberately leaves ``FS-Reply`` and ``WE-Error``
    alone [:L502-L503]: the write paths DO clear them, the initialise does not.
    """
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    logging_data = ctx.logging_data
    logging_data.sql_state = "0".ljust(SQL_STATE_WIDTH)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)


def _duplicate_key_seen(outcome: StatementOutcome, sql_state: str) -> bool:
    """``if Sql-State = "23000" or SQL-Err (1:4) = "1062" or = "1022"``.

    ``[common/slinvoiceMT.cbl:L1175-L1179]`` in ``ba070-Process-Write`` and
    ``[:L2543-L2546]`` in ``bc070-Process-Write``.  Both test the same three
    values; :func:`acas_posting.dal.status.is_duplicate_key_bridge_level` owns the
    test and :data:`acas_posting.dal.status.DUPLICATE_KEY_ERRNOS` owns the errno
    pair, so neither is retyped here.
    """
    return is_duplicate_key_bridge_level(outcome.sql_err, sql_state) or (
        outcome.sql_err[:4].strip() in DUPLICATE_KEY_ERRNOS
    )


def ba070_process_write(ctx: _BridgeContext) -> None:
    """``ba070-Process-Write.`` [common/slinvoiceMT.cbl:L1145]

    Header comment: ``*> dry test... - Has rg01 requirements.`` and, at [:L1147],
    the reminder that the record has not moved: ``*> but rec still in
    WS-Invoice-Record``.

    Routes on ``WS-Sih-Test`` exactly as :func:`ba050_process_read_indexed` does,
    then for a header: load the host variables, clear the status, stamp trace 10,
    insert, and interpret the row count.

    ⚠ THE DUPLICATE TEST IS NESTED HERE AND FLAT IN ``bc070``.  This paragraph puts
    the ``23000``/``1062``/``1022`` test INSIDE ``if WS-MYSQL-Error-Number not =
    "0  "`` [common/slinvoiceMT.cbl:L1174-L1180], so a duplicate reported with a
    zero errno would be missed and left as ``FS-Reply`` 99.  ``bc070`` instead ORs
    the SQLSTATE test into the outer condition [:L2544-L2545], so it catches that
    case.  Two different answers to the same question in one bridge.
    N-dup-test-asymmetry; both reproduced as written.
    """
    logging_data = ctx.logging_data
    # if WS-Sih-Test not = zero  *> It is a line row   [:L1149]
    # Class 4 - sibling re-dispatch, then 'go to ba999-Exit'  *> logging rec done.
    if ctx.buffer.ws_sih_test != 0:
        bc070_process_write(ctx)
        return
    # perform bb000-HV-Load.  *> move WS-Invoice-Record fields to HV fields  [:L1155]
    bb000_hv_load(ctx.state, ctx.buffer)
    # move WS-Invoice-Key to WS-File-Key.  [:L1156]
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    _clear_sql_status(ctx)
    # move 10 to ws-No-Paragraph.  [:L1163]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba070-Process-Write"]
    # perform bb200-Insert.  [:L1164]
    outcome = bb200_insert(ctx.connection, ctx.state, logging_data)
    # if WS-MYSQL-COUNT-ROWS not = 1  [:L1165]
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        logging_data.sql_state = _truncate_move(outcome.sql_state, SQL_STATE_WIDTH)
        # move 99 to fs-reply  *> this may need changing for val in WE-Error!!  [:L1169]
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        # if WS-MYSQL-Error-Number not = "0  " ... NESTED dup test  [:L1170-L1180]
        if outcome.sql_err.strip() not in ("", "0"):
            if _duplicate_key_seen(outcome, outcome.sql_state):
                # move 22 to fs-reply  [:L1179]
                ctx.file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
    # perform ba999-End.  go to ba999-Exit.  [:L1181-L1183]
    ba999_end(ctx)


def ba080_process_delete(ctx: _BridgeContext) -> None:
    """``ba080-Process-Delete.`` [common/slinvoiceMT.cbl:L1185]

    Header comment: ``*> dry tested. - Has rg01 requirements.``  And at [:L1190]
    the maintainer's own bracketed doubt, verbatim::

    *> [ Deleting all for a key should go to Delete-ALL   ???? ]

    Deletes ONE header row on an exact primary-key match.  The statement carries no
    trailing semicolon [:L1229]; see :func:`_delete_from`.  A row count other than
    exactly 1 is reported as 99/995.
    """
    logging_data = ctx.logging_data
    # if WS-Sih-Test not = zero -> line delete.  [:L1192-L1194]
    if ctx.buffer.ws_sih_test != 0:
        bc080_process_delete(ctx)
        return
    entry = _key_of_reference(ctx, 1)
    where = _equality_where(quote_identifier(entry.column_name))
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    # move WS-Invoice-Record (K:L) to WS-File-Key.  [:L1212]
    _move_to_ws_file_key(ctx, key_value)
    _move_to_ws_log_where(ctx, where)
    # move 13 to ws-No-Paragraph.  [:L1218]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba080-Process-Delete"]
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _delete_from(_HEADER_TABLE_SQL, where),
        (key_value,),
        fetch=False,
        delete_we_error=DELETE_FAILURE_WE_ERROR,
    )
    # if WS-MYSQL-COUNT-ROWS not = 1  [:L1232]
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        # move 99 to fs-reply / move 995 to WE-Error / go to ba999-End  [:L1241-L1244]
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        ctx.file_access.we_error = DELETE_FAILURE_WE_ERROR
        ba999_end(ctx)
        return
    # else move spaces to SQL-Msg / move zero to SQL-Err  [:L1245-L1247]
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    # perform ba999-End.  move zero to FS-Reply WE-Error.  [:L1249-L1251]
    ba999_end(ctx)
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)


def ba085_process_delete_all(ctx: _BridgeContext) -> None:
    """``ba085-Process-Delete-ALL.`` [common/slinvoiceMT.cbl:L1254]

    ⭐⭐ N-ba085-not-actually-all.  THE HEADER "DELETE ALL" DELETES AT MOST ONE ROW.

    The paragraph's own intent is spelled out in the commented-out dbpre equivalent
    at ``[common/slinvoiceMT.cbl:L1258-L1266]``, verbatim::

    *>           EXEC SQL
    *>              DELETE
    *>              FROM SAINVOICE-REC WHERE IH-INVOICE = {key value (1:8)}
    *>           END-EXEC.

    ``IH-INVOICE`` with the FIRST EIGHT bytes would match every test-suffix row for
    that invoice.  What the code actually builds [:L1294-L1308] is::

         string   "`"  KeyName (KOR-x1)  "`"  '="'  *> was '<"'
                  WS-Invoice-Record (K:L)  '"'

    - the FULL TEN-BYTE primary key, exact match.  So the header clear-down removes
    the single row it was handed, not "all" of anything, and the ``*> was '<"'``
    comment records that it used to be a ``<`` comparison which WOULD have swept a
    range.  Reproduced as written.

    Its row-count test is ``not > zero`` rather than ``not = 1`` [:L1329], carrying
    ``*> Changed for delete-ALL``, so deleting several rows is fine and deleting
    none is the error.  It then chains to :func:`bc085_process_delete_all` for the
    lines [:L1351] - which can never match anything either.
    """
    logging_data = ctx.logging_data
    entry = _key_of_reference(ctx, 1)
    where = _equality_where(quote_identifier(entry.column_name))
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    # move spaces to WS-File-Key / move WS-Invoice-Key to WS-File-Key  [:L1309-L1310]
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    _move_to_ws_log_where(ctx, where)
    # move 15 to ws-No-Paragraph.  [:L1315]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba085-Process-Delete-All"]
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _delete_from(_HEADER_TABLE_SQL, where),
        (key_value,),
        fetch=False,
        delete_we_error=DELETE_FAILURE_WE_ERROR,
    )
    # if WS-MYSQL-COUNT-ROWS not > zero  *> Changed for delete-ALL   [:L1329]
    if outcome.count_rows <= 0:
        _apply_statement_status(ctx, outcome)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        ctx.file_access.we_error = DELETE_FAILURE_WE_ERROR
        ba999_end(ctx)
        return
    # else  *> of course there could be no data in table   [:L1341-L1343]
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    # move zero to FS-Reply WE-Error.  perform ba999-End.  [:L1345-L1347]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ba999_end(ctx)
    # Process RG data where key is inv # for all lines within inv#  [:L1349-L1351]
    bc085_process_delete_all(ctx)


def ba090_process_rewrite(ctx: _BridgeContext) -> None:
    """``ba090-Process-Rewrite.`` [common/slinvoiceMT.cbl:L1354]

    Header comment: ``*> dry tested - Has rg01 requirements.``

    Loads the host variables, builds the exact-key clause, performs
    ``bb300-Update``, and requires exactly one affected row - otherwise 99 and
    ``994`` [:L1399-L1400].  Unlike the write path there is NO duplicate-key test
    here, because an UPDATE on the primary key cannot create one.
    """
    logging_data = ctx.logging_data
    # if WS-Sih-Test not = zero -> line rewrite.  [:L1359-L1361]
    if ctx.buffer.ws_sih_test != 0:
        bc090_process_rewrite(ctx)
        return
    # perform bb000-HV-Load.  [:L1365]
    bb000_hv_load(ctx.state, ctx.buffer)
    # move WS-Invoice-Key to WS-File-Key.  [:L1366]
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    # move 17 to ws-No-Paragraph.  [:L1367]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba090-Process-Rewrite"]
    entry = _key_of_reference(ctx, 1)
    where = _equality_where(quote_identifier(entry.column_name))
    _move_to_ws_log_where(ctx, where)
    # perform bb300-Update.  [:L1385]
    outcome = bb300_update(ctx.connection, ctx.state, logging_data)
    # if WS-MYSQL-COUNT-ROWS not = 1  [:L1391]
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        # move 994 to WE-Error  [:L1400]
        ctx.file_access.we_error = REWRITE_ROW_COUNT_WE_ERROR
        ba999_end(ctx)
        return
    # move zero to FS-Reply WE-Error SQL-Err.  move spaces to SQL-Msg.  [:L1403-L1406]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    ba999_end(ctx)


def ba100_bad_function(ctx: _BridgeContext) -> None:
    """``ba100-Bad-Function.`` [common/slinvoiceMT.cbl:L1412]

    ``[common/slinvoiceMT.cbl:L1413-L1417]``, verbatim::

    *> Houston; We have a problem
    *>
         move     990 to WE-Error.
         move     99 to Fs-Reply.
         go       to ba999-end.

    ⚠ The BRIDGE's bad-function pair is 990/99.  The HANDLER's is 999/99
    [common/acas016.cbl:L535-L539].  Different codes for the same condition at the
    two layers; both reproduced, neither harmonised.
    """
    # move 990 to WE-Error.  move 99 to Fs-Reply.
    ctx.file_access.we_error = BRIDGE_BAD_FUNCTION_WE_ERROR
    ctx.file_access.fs_reply = int(FsReply.ERROR)
    ba999_end(ctx)


def ba998_free(ctx: _BridgeContext) -> None:
    """``ba998-Free.`` [common/slinvoiceMT.cbl:L1421]

    ``MOVE TP-SAINVOICE-REC TO WS-MYSQL-RESULT`` then
    ``CALL "MySQL_free_result"`` [:L1428-L1429], then
    ``set Cursor-Not-Active to true`` [:L1431].

    ⚠ ONLY THE PRIMARY RESULT IS FREED.  The lines result
    (``TP-SAINV-LINES-REC``) is freed only by ``bc998-Free``, which nothing calls -
    see :func:`bc998_free`.  N-bc998-never-called.
    """
    # move 20 to ws-No-Paragraph.  [:L1422]
    ctx.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba998-Free"]
    cursor = ctx.state.header_cursor()
    cursor.free_result()
    # set Cursor-Not-Active to true.  [:L1431]
    cursor.set_cursor_not_active()


def ba999_end(ctx: _BridgeContext) -> None:
    """``ba999-end.`` [common/slinvoiceMT.cbl:L1433]

    ``[common/slinvoiceMT.cbl:L1434-L1438]``, verbatim - including the maintainer's
    doubled question marks about his own design::

     ba999-end.
    *>  Any Clean ups before quiting    move data record ?????  do so at the start as well ??????
    *>
         if       Testing-1
                  perform Ca-Process-Logs
         end-if.

    ``Testing-1`` is the compile-time switch from
    [copybooks/Test-Data-Flags.cob], surfaced as
    :attr:`acas_posting.records.test_data_flags.AcasDalCommonData.sw_testing`.
    Logging is gated on it exactly as here, and :func:`ca_process_logs` explains why
    the DAL path must not log at all.
    """
    # if Testing-1 perform Ca-Process-Logs end-if.
    if ctx.dal_common.sw_testing != 0:
        ca_process_logs(ctx)


# ---------------------------------------------------------------------------
# bc000-RG-Process - the Repeating-Group (lines) half of the bridge
# ---------------------------------------------------------------------------
# Section header comment [common/slinvoiceMT.cbl:L2360-L2379], the parts that
# constrain the implementation, verbatim:
#
# *> This section contains mirror processes in ba000 section that act
# *> in support of paragraph based process to only deal with the
# *> RG ( Repeat Group ) segments of data.
# *>
# *>  Like ba000 processes they handle one action at a time and do not
# *>  do multiple commands or row at once.  This may come later but only
# *>   on a as needed basis.
# *>
# *>  Note that ws-No-Paragraph start at 51 for RG processing.
# *>  Each bc para must end with a bc0n0-Exit
# *>
# *>   Last para used is 58.
#
# "handle one action at a time and do not do multiple commands or row at once" is
# the sequential-execution constraint of AAP section 0.2.2 stated by the original
# author, and it is honoured: no batching, no executemany, one statement per call.


def bc050_process_read_indexed(ctx: _BridgeContext) -> None:
    """``bc050-Process-Read-Indexed.`` [common/slinvoiceMT.cbl:L2381]

    Header comment: ``*> Dry chk complete.``  Design note at [:L2383-L2385],
    verbatim::

    *>  This routine is called by for both Read-Next ?? and Read-Indexed.
    *>
    *>    But first save the pointers [and we will restore at end].

    ⭐ THE POINTER SAVE/RESTORE IS THE WHOLE POINT.  Because one MySQL result
    pointer is shared, reading a line row would destroy the header walk's position.
    So the paragraph saves the primary result and count [:L2387-L2389], zeroes the
    count, does its work, and :func:`bc058_restore_pointers` puts them back
    [:L2521-L2523].  Reproduced with two independent
    :class:`acas_posting.dal.cursor_state.CursorState` slots plus the explicit save
    fields, because the COBOL has BOTH mechanisms and dropping either would change
    behaviour.

    ⭐ ``set KOR-x1 to 2.  *> was 1 = Primary now invoice line 12/07/23`` [:L2398] -
    a dated correction, preserved.

    On zero rows it sets ``FS-Reply`` 23 and ``WE-Error`` 890 [:L2445-L2446] - the
    ONLY assignment of the RG family in this bridge - and clears BOTH record areas
    with the comment at [:L2452-L2453], verbatim::

              initialise WS-Invoice-Record       *> Clear both in case called does not spot end of
                         WS-Invoice-Line         *> data for Invoice and to help debugging if so
    """
    logging_data = ctx.logging_data
    header_cursor = ctx.state.header_cursor()
    # move WS-Mysql-Result to WS-Mysql-Save-Result / count to Save-Count /
    # move zero to WS-Mysql-Count-Rows   [:L2387-L2389]
    ctx.state.save_result_rows = header_cursor.stored_rows
    ctx.state.save_count_rows = header_cursor.count_rows
    # set KOR-x1 to 2.  *> was 1 = Primary now invoice line 12/07/23   [:L2398]
    entry = _key_of_reference(ctx, 2)
    where = _equality_where(quote_identifier(entry.column_name))
    _move_to_ws_log_where(ctx, where)
    # move 51 to ws-No-Paragraph.  [:L2416]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc050-Process-Read-Indexed"]
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _select_all(_LINES_TABLE_SQL, where),
        (key_value,),
        fetch=True,
    )
    line_cursor = ctx.state.line_cursor()
    stored = line_cursor.store_result(outcome.rows)  # type: ignore[arg-type]
    _apply_statement_status(ctx, outcome)
    # if WS-MYSQL-Count-Rows = zero  *> This should not happen as have to be > 0  [:L2436]
    if stored == 0:
        # move 23 to fs-reply / move 890 to WE-Error   [:L2445-L2446]
        ctx.file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
        ctx.file_access.we_error = RG_UNKNOWN_UNEXPECTED_WE_ERROR
        # string "No RG1 Data for " WS-Invoice-Record (K:L) into WS-File-Key  [:L2448-L2451]
        _move_to_ws_file_key(ctx, f"No RG1 Data for {key_value}")
        # initialise WS-Invoice-Record WS-Invoice-Line   [:L2452-L2453]
        # TWO operands in ONE statement, in the source's own order - the shared
        # buffer first and the bridge's staging record second.
        _initialise_ws_invoice_record(ctx.buffer)
        _initialise_ws_invoice_line(ctx.state)
        # go to bc058-Restore-Pointers  *> do ba999-end at end   [:L2454]
        # Class 4 - sibling re-dispatch, then explicit return.
        bc058_restore_pointers(ctx)
        return
    # string "RG > 0 got cnt=" ... " recs, KEY=" ... into WS-File-Key  [:L2458-L2463]
    _move_to_ws_file_key(ctx, f"RG > 0 got cnt={stored} recs, KEY={key_value}")
    # perform ba999-End.  *> log it & continue   [:L2464]
    ba999_end(ctx)
    # FALL-THROUGH into bc051-Fetch-RG1 [:L2466].  Made explicit.
    bc051_fetch_rg1(ctx)


def bc051_fetch_rg1(ctx: _BridgeContext) -> None:
    """``bc051-Fetch-RG1.`` [common/slinvoiceMT.cbl:L2466]

    The 14-operand positional fetch [:L2476-L2491], then the unload and the copy
    over the shared buffer.

    ⭐⭐ N-fetch-rg1-status-erased.  ``[common/slinvoiceMT.cbl:L2495-L2510]``,
    verbatim::

         if       WS-MYSQL-Count-Rows  > zero
    *> transfer/move HV1 vars to ws-Invoice-Line then to ws-Invoice-Record
                  perform  bc100-UnloadHVs-rg1
                  move     WS-Invoice-Line to WS-Invoice-Record
         else
                  initialise WS-Invoice-Line   *> Incase called does not spot no more data for invoice.
                             WS-Invoice-Record
                  move 23 to FS-Reply
         end-if
    *>
    *> No more rows for key
    *>
         move     WS-Invoice-Record (K:L) to WS-File-Key.
         move     zero to FS-Reply WE-Error.

    The ``move 23 to FS-Reply`` in the else-arm is UNCONDITIONALLY OVERWRITTEN two
    statements later by ``move zero to FS-Reply WE-Error``.  A caller can therefore
    never observe the 23 this paragraph sets: an exhausted line cursor reports
    SUCCESS.  Reproduced exactly - the 23 is set, then cleared.

    ⭐ ``initialise`` at [:L2501] is the BRITISH spelling, used here and nowhere
    else in the bridge; every other site writes ``initialize``.  GnuCOBOL accepts
    both.  N-initialize.
    """
    logging_data = ctx.logging_data
    # move 52 to ws-No-Paragraph   [:L2470]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc051-Fetch-RG1"]
    line_cursor = ctx.state.line_cursor()
    row = line_cursor.fetch_record()
    # if WS-MYSQL-Count-Rows > zero  [:L2495]
    if row is not None and line_cursor.count_rows > 0:
        _fetch_into_group(ctx.state.td_sainv_lines_rec, LINE_COLUMNS, row)
        # perform bc100-UnloadHVs-rg1  [:L2498]
        # (which itself ends with 'move WS-Invoice-Line to WS-Invoice-Record'
        #  at [:L2842], so the [:L2499] move is the same transfer restated)
        bc100_unload_hvs_rg1(ctx.state, ctx.buffer)
        _move_ws_invoice_line_to_ws_invoice_record(ctx.state, ctx.buffer)
    else:
        # initialise WS-Invoice-Line WS-Invoice-Record  [:L2501-L2502]
        # The REVERSE order of [:L2452-L2453] - staging record first here - and
        # the order is kept because the source keeps it.
        _initialise_ws_invoice_line(ctx.state)
        _initialise_ws_invoice_record(ctx.buffer)
        # move 23 to FS-Reply  [:L2503]
        ctx.file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
    # move WS-Invoice-Record (K:L) to WS-File-Key.  [:L2506]
    _move_to_ws_file_key(ctx, _record_key_slice(ctx, ctx.k, ctx.ell))
    # move zero to FS-Reply WE-Error.   [:L2507]
    # ⭐⭐ THIS DESTROYS THE 23 SET ABOVE.  Unconditional, two lines after it was
    # set.  N-fetch-rg1-status-erased.  Do NOT guard this.
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    # FALL-THROUGH into bc058-Restore-Pointers [:L2509].  Made explicit.
    bc058_restore_pointers(ctx)


def bc058_restore_pointers(ctx: _BridgeContext) -> None:
    """``bc058-Restore-Pointers.`` [common/slinvoiceMT.cbl:L2509]

    ``[common/slinvoiceMT.cbl:L2511-L2515]``, verbatim::

    *> Restore the Primary table pointer & row count.
    *>
         move     WS-Mysql-Save-Result to WS-Mysql-Result.     *> primary Tbl
         move     WS-Mysql-Save-Count-Rows to WS-Mysql-Count-Rows.
         perform  ba999-End.

    Puts the header walk's position back so that a caller alternating header and
    line reads keeps its place.  The restore is the reason
    :func:`ba041_reread` can read a line and then still fetch the next header.
    """
    header_cursor = ctx.state.header_cursor()
    fetched_before = header_cursor.fetched_count
    header_cursor.store_result(ctx.state.save_result_rows)  # type: ignore[arg-type]
    # store_result rewinds; the COBOL restores a POINTER, which keeps its place.
    header_cursor.fetched_count = fetched_before
    # perform ba999-End.  [:L2515]
    ba999_end(ctx)


def bc070_process_write(ctx: _BridgeContext) -> None:
    """``bc070-Process-Write.`` [common/slinvoiceMT.cbl:L2519]

    Header comment: ``*> dry coded. tested - 1``

    ``[common/slinvoiceMT.cbl:L2523-L2531]``, verbatim::

         move     WS-Invoice-Record  to  WS-Invoice-Line.
         perform  bc000-HV-Load-rg1.
         move     WS-Invoice-Key to WS-File-Key.   *> Same as WS-Sil-Key
         move     zero to FS-Reply WE-Error.
         move     spaces to SQL-Msg
                            SQL-State.
         move     zero to SQL-Err.
         move     53  to ws-No-Paragraph.
         perform  bc200-Insert-rg1.          *> chgd 26/07/23

    ⭐ ``*> Same as WS-Sil-Key`` at [:L2525] asserts by COMMENT that the invoice key
    and the line key are the same ten bytes.  Nothing in the code checks it.  They
    coincide only because both are the first ten bytes of the union buffer.

    ⚠ THE DUPLICATE TEST IS FLAT HERE, NESTED IN ``ba070``.  ``[:L2543-L2545]`` ORs
    the SQLSTATE test into the OUTER condition::

              if    WS-MYSQL-Error-Number  not = "0  "
                 or Sql-State = "23000"      *> Dup key (rec already present)

    so a duplicate with a zero errno IS caught here and is NOT caught by
    ``ba070-Process-Write``.  N-dup-test-asymmetry.  It also has an ``else move 99``
    [:L2548] that ``ba070`` lacks.
    """
    logging_data = ctx.logging_data
    # move WS-Invoice-Record to WS-Invoice-Line.  [:L2523]
    _move_ws_invoice_record_to_ws_invoice_line(ctx.state, ctx.buffer)
    # perform bc000-HV-Load-rg1.  [:L2524]
    bc000_hv_load_rg1(ctx.state)
    # move WS-Invoice-Key to WS-File-Key.  *> Same as WS-Sil-Key   [:L2525]
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    _clear_sql_status(ctx)
    logging_data.sql_state = " " * SQL_STATE_WIDTH
    # move 53 to ws-No-Paragraph.  [:L2530]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc070-Process-Write"]
    # perform bc200-Insert-rg1.  *> chgd 26/07/23   [:L2531]
    outcome = bc200_insert_rg1(ctx.connection, ctx.state, logging_data)
    # if WS-MYSQL-COUNT-ROWS not = 1  [:L2533]
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        # move 99 to fs-reply  [:L2537]
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        # FLAT condition: errno non-zero OR SQLSTATE 23000.  [:L2543-L2545]
        if outcome.sql_err.strip() not in ("", "0") or outcome.sql_state.startswith(
            str(SqlState.DUPLICATE_KEY)
        ):
            if _duplicate_key_seen(outcome, outcome.sql_state):
                # move 22 to fs-reply  [:L2546]
                ctx.file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
            else:
                # else move 99 to fs-reply  [:L2548] - present here, absent in ba070.
                ctx.file_access.fs_reply = int(FsReply.ERROR)
        # string "Cant Re|WriteRG1 Data on " ... " RG=" WS-Sil-Line  [:L2552-L2557]
        # The literal's embedded pipe is the maintainer's own; kept verbatim.
        _move_to_ws_file_key(
            ctx,
            "Cant Re|WriteRG1 Data on "
            f"{_record_key_slice(ctx, ctx.k, ctx.ell)} RG="
            f"{ctx.state.ws_invoice_line.ws_sil_line:02d}",
        )
    # perform ba999-End.  [:L2559]
    ba999_end(ctx)


def bc080_process_delete(ctx: _BridgeContext) -> None:
    """``bc080-Process-Delete.`` [common/slinvoiceMT.cbl:L2563]

    Header comment: ``*> Dry tested.``  And at [:L2565], verbatim:
    ``*>  Delete one invoice-line (Item). But data is in WS-Invoice-Record`` - the
    union buffer again.

    ⚠ ITS TRACE COMMENT CONTRADICTS ITS NAME.  ``[:L2587]``, verbatim::

         move     54 to ws-No-Paragraph.           *> Delete all rows (9<=) for key

    The comment claims "Delete all rows (9<=) for key" while the clause it builds is
    an exact single-key match [:L2573-L2581] and the paragraph is named
    ``-Delete``, not ``-Delete-All``.  ``(9<=)`` refers to nothing in the code.
    N-bc080-comment-contradiction ``[common/slinvoiceMT.cbl:L2587]`` against the
    clause built at ``[common/slinvoiceMT.cbl:L2573-L2581]``; the comment is
    preserved and not acted on.

    Its row-count arm carries [:L2602], verbatim:
    ``*>  We could have from 0 to 1 so this Error report is moot.`` - and then
    reports anyway, WITHOUT setting ``FS-Reply`` or ``WE-Error`` at all: it only
    writes ``WS-File-Key`` and jumps to ``ba999-End`` [:L2614-L2622].  So a
    line-delete that matched nothing returns whatever status the caller arrived
    with.  N-bc080-silent-miss ``[common/slinvoiceMT.cbl:L2604-L2622]``, against
    ``ba080``'s 99/995 at ``[common/slinvoiceMT.cbl:L1240-L1241]``.
    """
    logging_data = ctx.logging_data
    # set KOR-x1 to 2.  *> inv.line   [:L2568]
    entry = _key_of_reference(ctx, 2)
    where = _equality_where(quote_identifier(entry.column_name))
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    # move WS-Invoice-Record (K:L) to WS-File-Key.  [:L2582]
    _move_to_ws_file_key(ctx, key_value)
    _move_to_ws_log_where(ctx, where)
    # move 54 to ws-No-Paragraph.  *> Delete all rows (9<=) for key   [:L2587]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc080-Process-Delete"]
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _delete_from(_LINES_TABLE_SQL, where),
        (key_value,),
        fetch=False,
        delete_we_error=DELETE_FAILURE_WE_ERROR,
    )
    # if WS-MYSQL-COUNT-ROWS not > zero  [:L2604]
    if outcome.count_rows <= 0:
        _apply_statement_status(ctx, outcome)
        # string "Delete for " ... " only found (rg01) " ... " Rows"  [:L2616-L2621]
        _move_to_ws_file_key(
            ctx,
            f"Delete for {key_value} only found (rg01) {outcome.count_rows} Rows",
        )
        # go to ba999-End  [:L2622]
        # ⭐ NO 'move 99 to fs-reply' and NO 'move 995 to WE-Error' on this arm,
        # unlike ba080/ba085/bc085.  The miss is silent.  N-bc080-silent-miss
        # [common/slinvoiceMT.cbl:L2604-L2622]; its own comment at
        # [common/slinvoiceMT.cbl:L2602] calls the report 'moot'.
        ba999_end(ctx)
        return
    # else move spaces to SQL-Msg SQL-State / move zero to SQL-Err  [:L2624-L2625]
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    # move zero to FS-Reply WE-Error.  perform ba999-End.  [:L2627-L2628]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ba999_end(ctx)


def bc085_process_delete_all(ctx: _BridgeContext) -> None:
    """``bc085-Process-Delete-ALL.`` [common/slinvoiceMT.cbl:L2632]

    Header comment, verbatim:
    ``*> THIS IS NON STANDARD - NEEDED (sl940) - Coded/ D.Tested.``  So the
    maintainer believed it tested.

    ⭐⭐ N-bc085-string-constant-predicate.  IT DELETES NOTHING, EVER, AND SAYS
    NOTHING ABOUT IT.  The clause is built in :func:`_delete_all_lines_where`,
    which carries the full verbatim quotation and the reasoning.  The short form:
    the column name is written ``"'IL-INVOICE'"`` in SINGLE quotes [:L2668], making
    it a STRING LITERAL, so the predicate compares two constants and is always
    false.

    ⭐ AND THE COMMENTED-OUT "EQUIVALENT" HAS THE SAME BUG.  ``[:L2640]``, verbatim::

    *>              FROM SAINV-LINES-REC WHERE 'IL-INVOICE' = WS-Sih-Invoice

    and again in the dbpre expansion at [:L2648].  The single quotes are in the
    INTENDED version too, so this was never a transcription slip - it is what the
    author meant to write.  That removes any argument for "obviously a typo, fix
    it": rule R-4 governs, and the constant stays a constant.

    ⭐ THE FAILURE ARM CANNOT FIRE EITHER.  ``[:L2701-L2718]``: the 99/995 pair is
    set only INSIDE ``if WS-MYSQL-Error-Number not = "0  "``, and a successful
    zero-row DELETE reports no errno - so the pair is never set, and the
    ``go to bc085-Exit`` at [:L2717] then SKIPS the
    ``move zero to FS-Reply WE-Error`` at [:L2718].  The caller is told nothing at
    all.  Reproduced exactly.
    """
    logging_data = ctx.logging_data
    # set KOR-x1 to 2  [:L2655] - selected, then NOT USED, because the clause
    # hard-codes its predicate instead.  The four commented-out lines at
    # [:L2662-L2665] are what would have used it.
    _key_of_reference(ctx, 2)
    where = _delete_all_lines_where()
    # move spaces to WS-File-Key  [:L2673]
    _move_to_ws_file_key(ctx, "")
    _move_to_ws_log_where(ctx, where)
    # move 55 to ws-No-Paragraph.  [:L2679]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc085-Process-Delete-All"]
    # WS-Sih-Invoice is the bound value [:L2670] - the HEADER's invoice number,
    # rendered as the eight-digit text the STRING would have produced.
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _delete_from(_LINES_TABLE_SQL, where),
        (f"{ctx.buffer.ws_sih_invoice:08d}",),
        fetch=False,
        delete_we_error=DELETE_FAILURE_WE_ERROR,
    )
    # if WS-MYSQL-COUNT-ROWS not > zero  *> Changed for delete-ALL   [:L2701]
    if outcome.count_rows <= 0:
        _apply_statement_status(ctx, outcome)
        # The 99/995 pair sits INSIDE the errno test [:L2705-L2712], so it fires
        # only on a genuine driver error - never on the always-empty delete.
        if outcome.sql_err.strip() not in ("", "0"):
            ctx.file_access.fs_reply = int(FsReply.ERROR)
            ctx.file_access.we_error = DELETE_FAILURE_WE_ERROR
        # perform ba999-End / go to bc085-Exit  [:L2716-L2717]
        # ⭐ This SKIPS the 'move zero to FS-Reply WE-Error' at [:L2718].
        ba999_end(ctx)
        return
    # else  *> of course there could be no data in table   [:L2718-L2720]
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    # move zero to FS-Reply WE-Error.  perform ba999-End.  [:L2718-L2719]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ba999_end(ctx)


def bc090_process_rewrite(ctx: _BridgeContext) -> None:
    """``bc090-Process-Rewrite section.`` [common/slinvoiceMT.cbl:L2723]

    Note this one is declared a SECTION while its ``bc*`` siblings are paragraphs -
    ``bc090-Process-Rewrite section.`` at [:L2723] against
    ``bc080-Process-Delete.`` at [:L2563].  Its exit is
    ``bc090-Exit.  exit.`` [:L2769] with a LOWER-CASE ``exit``, where
    ``bb200-Exit`` uses ``exit section`` [:L1946].  Recorded, not normalised.

    ⭐ IT USES ``WS-Sil-Key`` FOR THE LOG AND ``WS-Invoice-Record (K:L)`` FOR THE
    CLAUSE.  ``move WS-Sil-Key to WS-File-Key`` [:L2727] but
    ``WS-Invoice-Record (K:L)`` in the ``string`` [:L2741].  They are the same ten
    bytes, from two different views of the union buffer.
    """
    logging_data = ctx.logging_data
    # move WS-Invoice-Record to WS-Invoice-Line.  [:L2726]
    _move_ws_invoice_record_to_ws_invoice_line(ctx.state, ctx.buffer)
    # perform bc000-HV-Load-rg1.  [:L2727]
    bc000_hv_load_rg1(ctx.state)
    # move WS-Sil-Key to WS-File-Key.  [:L2728]
    _move_to_ws_file_key(ctx, ctx.state.ws_invoice_line.ws_sil_key)
    # move 56 to ws-No-Paragraph.  [:L2730]
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc090-Process-Rewrite"]
    # set KOR-x1 to 2  *> 2 = Lines   [:L2731]
    entry = _key_of_reference(ctx, 2)
    where = _equality_where(quote_identifier(entry.column_name))
    _move_to_ws_log_where(ctx, where)
    # perform bc300-Update-rg1.  [:L2749]
    outcome = bc300_update_rg1(ctx.connection, ctx.state, logging_data)
    # if WS-MYSQL-COUNT-ROWS not = 1  [:L2755]
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        # move 994 to WE-Error  [:L2762]
        ctx.file_access.we_error = REWRITE_ROW_COUNT_WE_ERROR
        # perform ba999-End / go to bc090-Exit  [:L2763-L2764]
        ba999_end(ctx)
        return
    # move zero to FS-Reply WE-Error SQL-Err.  move spaces to SQL-Msg.  [:L2765-L2768]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    ba999_end(ctx)


def bc998_free(ctx: _BridgeContext) -> None:
    """``bc998-Free.`` [common/slinvoiceMT.cbl:L3239] - AND NOTHING EVER CALLS IT.

    ⭐⭐ N-bc998-never-called.  Searching the whole 3259-line bridge for ``bc998``
    returns exactly ONE hit: its own label at [common/slinvoiceMT.cbl:L3239].  No
    ``perform``, no ``go to``, from any paragraph.  Consequences, all reproduced:

    * The lines result array (``TP-SAINV-LINES-REC``) is never freed.
    * ``Cursor-Not-Active-2`` is never set by this route, so the RG1 cursor flag is
      cleared only by ``ba060``'s explicit ``else`` branch [:L1102].
    * ``ba030-Process-Close`` frees ONLY the primary cursor [:L611-L612], so closing
      the file leaves the lines cursor active.
    * Trace number 58 is assigned [:L3240] and documented as "Last para used is 58"
      [:L2379], for a paragraph that never runs.

    It is implemented anyway, faithfully, because it EXISTS - deleting it would
    lose the fact that the author wrote it and forgot to wire it up.  It is simply
    never called from this module either, which is what reproducing the defect
    means.  Do NOT add a call to it.
    """
    # move 58 to ws-No-Paragraph.  [:L3240]
    ctx.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc998-Free"]
    cursor = ctx.state.line_cursor()
    cursor.free_result()
    # set Cursor-Not-Active-2 to true.  [:L3249]
    cursor.set_cursor_not_active()


def ca_process_logs(ctx: _BridgeContext) -> None:
    """``Ca-Process-Logs.`` [common/slinvoiceMT.cbl:L3251]

    ``[common/slinvoiceMT.cbl:L3252-L3256]``, verbatim::

     Ca-Process-Logs.
    *>**************
    *>
         call     "fhlogger" using File-Access
                                   ACAS-DAL-Common-data.

    ⚠ ``fhlogger`` is ``common/fhlogger.cbl``, which AAP section 0.2.2 lists as
    OUT OF SCOPE.  So the call is not reproduced as a call.  What IS reproduced is
    the fact that logging happens here and only here, and the data it would have
    been given, emitted through :mod:`logging` at debug level - AAP section 0.3.4's
    rule for a diagnostic with no database effect: *"become log records at a
    severity matching the original's intent.  They must not alter control flow and
    must not appear in any table dump."*

    ⚠ AND THE HANDLER MUST NOT REACH HERE AT ALL.  ``[common/acas016.cbl:L633]``
    carries its comment ON THE LABEL LINE, verbatim::

     Ca-Process-Logs. *> Not called on DAL access as it does it already

    so the HANDLER's own ``Ca-Process-Logs`` is not invoked on the RDB path -
    the bridge has already logged.  N-nolog-on-dal.
    """
    logging_data = ctx.logging_data
    _LOG.debug(
        "slinvoiceMT fhlogger: system=%s file=%s para=%s fs_reply=%s we_error=%s "
        "key=%s where=%s",
        logging_data.ws_log_system,
        logging_data.ws_log_file_no,
        logging_data.ws_no_paragraph,
        ctx.file_access.fs_reply,
        ctx.file_access.we_error,
        sanitise_for_log(logging_data.ws_file_key.rstrip()),
        sanitise_for_log(logging_data.ws_log_where.rstrip()),
    )


# ---------------------------------------------------------------------------
# The bridge entry point
# ---------------------------------------------------------------------------


def slinvoice_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    invoice: InvoiceBuffer,
    *,
    connection: object = None,
    system_record: SystemRecord | None = None,
) -> FileAccess:
    """``call "slinvoiceMT" using ...`` - the bridge, entered as the handler enters it.

    THIS FUNCTION *IS* ``ba-ACAS-DAL-Process section.``
    ``[common/slinvoiceMT.cbl:L483]`` - the bridge's single entry section, the one
    a ``CALL "slinvoiceMT"`` actually lands in. Named for the program rather than
    the section because the handler's ``CALL`` names the program, but the
    paragraph-to-function mapping R-5 requires is this one. Its first statement,
    ``accept ws-env-lines from lines.`` ``[common/slinvoiceMT.cbl:L484]``, reads
    the terminal geometry for the bridge's screen section and has no database
    effect, so it is a deliberate omission under AAP section 0.1.1's exclusion of
    presentation that produces no database effect.

    THE THREE-PARAMETER SIGNATURE IS THE COBOL'S.
    ``[common/acas016.cbl:L621-L625]``, VERBATIM::

         call     "slinvoiceMT" using File-Access
                                      ACAS-DAL-Common-data

                                      WS-Invoice-Record
         end-call.

    Note the ORDER: ``File-Access`` first, then ``ACAS-DAL-Common-data``, then the
    record - which is NOT the handler's own order
    (``System-Record`` first, record second, ``File-Access`` third).  Both orders
    are published as written, because AAP section 0.4.3 requires the argument lists
    be diffable against the COBOL, and silently harmonising them would defeat that.

    The call is INLINE in ``ba015-Test-Ends`` [common/acas016.cbl:L611-L628] - there
    is NO ``ba020-Process-DAL`` paragraph in this handler, unlike some of its
    siblings.  N-nobadal.

    Two keyword-only extras carry what COBOL passes implicitly: the open connection
    (COBOL reaches the live handle through the MySQL client's own global state) and
    the system record (which
    :func:`acas_posting.dal.connection.mysql_1000_open` needs and the bridge derives
    from ``RDB-Data`` inside ``File-Access``).  They are keyword-only precisely so
    they cannot be mistaken for positional bridge parameters.

    ⚠ THIS FUNCTION NEVER RAISES.  ``[common/acas016.cbl:L627]``, verbatim:
    ``*>   Any errors leave it to caller to recover from``.  Every outcome is
    reported through ``file_access.fs_reply`` and ``file_access.we_error``.

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L38], carrying the
            function code, the access type, the status pair and ``Logging-Data``.
        dal_common: ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob],
            whose ``sw-testing`` gates logging exactly as ``Testing-1`` does.
        invoice: ``WS-Invoice-Record`` - the ONE union buffer serving BOTH tables.
        connection: The live connection, or ``None`` to have function 1 open one.
        system_record: ``System-Record``, needed only by function 1.

    Returns:
        The same ``file_access`` object, mutated - which is what a COBOL ``CALL BY
        REFERENCE`` does.  Returning it as well makes the mutation visible to a
        reader without changing the semantics.
    """
    state = invoice.bridge_state
    ctx = _BridgeContext(
        connection=connection,
        file_access=file_access,
        dal_common=dal_common,
        state=state,
        buffer=invoice,
        system_record=system_record,
    )
    # ba010-Initialise, then the evaluate.  [common/slinvoiceMT.cbl:L498-L541]
    ba010_initialise(ctx)
    function_code = file_access.file_function
    # evaluate File-Function [common/slinvoiceMT.cbl:L513-L541].  Transcribed in the
    # COBOL's own order, with the shared 3/34 branch and the 'when other' arm.
    if function_code == int(FileFunction.OPEN):
        ba020_process_open(ctx)
    elif function_code == int(FileFunction.CLOSE):
        ba030_process_close(ctx)
    elif function_code in (
        int(FileFunction.READ_NEXT),
        # when 3 / when 34 SHARE the branch.  *> Read-Next-Header - Special
        # *> cursor active   [common/slinvoiceMT.cbl:L523-L526]
        int(FileFunction.READ_NEXT_HEADER),
    ):
        ba040_process_read_next(ctx)
    elif function_code == int(FileFunction.READ_INDEXED):
        ba050_process_read_indexed(ctx)
    elif function_code == int(FileFunction.WRITE):
        ba070_process_write(ctx)
    elif function_code == int(FileFunction.DELETE_ALL):
        # *> option 6 is a special to cleardown all LINE data for 1 invoice
        # [common/slinvoiceMT.cbl:L529-L532].  THE BRIDGE HONOURS 6.  The HANDLER
        # does not - it routes 6 to aa100-Bad-Function
        # [common/acas016.cbl:L309-L310].  Both reproduced; see
        # N-delete-all-bad-function.  Reachable only by calling this function
        # directly, which is exactly the asymmetry the COBOL has.
        ba085_process_delete_all(ctx)
    elif function_code == int(FileFunction.RE_WRITE):
        ba090_process_rewrite(ctx)
    elif function_code == int(FileFunction.DELETE):
        ba080_process_delete(ctx)
    elif function_code == int(FileFunction.START):
        ba060_process_start(ctx)
    else:
        # when other go to ba100-Bad-Function.  [common/slinvoiceMT.cbl:L538-L539]
        ba100_bad_function(ctx)
    # The connection the open established travels back on the buffer, because a
    # COBOL bridge keeps it in the MySQL client's own state across CALLs.
    invoice.connection = ctx.connection
    return file_access


# ---------------------------------------------------------------------------
# The handler: acas016
# ---------------------------------------------------------------------------
# 'aa-Process-Flat-File Section.' [common/acas016.cbl:L242] and everything under
# it.  Every paragraph gets a function (rule R-5), including the ones the migrated
# cycle can never reach - because a paragraph that exists in the COBOL and has no
# Python counterpart is exactly the kind of silent gap the traceability document
# is meant to make impossible.
#
# ⚠ THE ENTIRE aa020..aa090 RANGE IS THE ISAM PATH.  Those paragraphs issue COBOL
# file verbs against 'Invoice-File' - 'open input', 'read ... next record',
# 'write Invoice-Record', 'delete Invoice-File record', 'rewrite', 'start ... key'.
# They run ONLY when FS-Cobol-Files-Used is true, because the RDB branch at
# [common/acas016.cbl:L271-L275] exits before the function 'evaluate' at [:L291] is
# ever reached.  In the migrated cycle the system record always selects the RDB,
# so this whole range is unreachable - which is why the debugging 'stop' at [:L379]
# is harmless and why no ISAM store is needed.
#
# There is no ISAM layer in this migration and none may be added: the AAP freezes
# the MySQL schema as the one store and the DAL's remit is SQL against it.  So the
# ISAM verbs are NOT implemented, recorded as a deliberate omission per R-5, and
# each paragraph instead runs its own documented FAILURE path - which is faithful
# rather than invented, because a COBOL file verb against a file that is not there
# does fail, and the COBOL's handling of that failure is written out in full.


def _isam_file_available(_ctx: "_HandlerContext") -> bool:
    """Whether ``Invoice-File`` - the ISAM file - can be opened.  Always ``False``.

    ``Invoice-File`` is the indexed (ISAM) file declared in the handler's own
    ``FILE-CONTROL``.  This migration has ONE store, the frozen MySQL schema, and
    AAP section 0.2.2 forbids adding another; the ISAM verbs are therefore recorded
    as a deliberate omission rather than reimplemented.

    Returning ``False`` is not a stub and not a guess - it is the accurate answer
    for this deployment, and it makes each ISAM paragraph run the failure path the
    COBOL already spells out (``move 35 to fs-Reply`` for a failed
    ``open input`` [common/acas016.cbl:L322], the
    ``"Failed action in read-indexed for "`` arm [:L432-L435], and so on).  No status
    code is invented anywhere.

    It can never be consulted in the migrated cycle regardless, because
    :func:`dispatch` takes the RDB branch first [:L271-L275].
    """
    return False


@dataclass(slots=True)
class _HandlerContext:
    """What every ``acas016`` paragraph can see - the handler's five linkage items.

    ``[common/acas016.cbl:L233-L239]``, VERBATIM::

     L233   Procedure Division Using System-Record

                                     WS-Invoice-Record

                                     File-Access
                                     File-Defs
                                     ACAS-DAL-Common-data.

    Five parameters, and ONE record for TWO tables.
    """

    system_record: SystemRecord
    invoice: InvoiceBuffer
    file_access: FileAccess
    file_defs: FileDefs
    dal_common: AcasDalCommonData
    #: ``Cobol-File-Status`` and its ``88 Cobol-File-Eof`` - the handler's own
    #: end-of-file latch, set at [common/acas016.cbl:L385-L386] and tested at
    #: [:L373].  ISAM-path only.
    cobol_file_status: int = 0

    @property
    def logging_data(self) -> LoggingData:
        """``Logging-Data``, reached through ``File-Access``."""
        return self.file_access.logging_data

    def cobol_file_eof(self) -> bool:
        """``88 Cobol-File-Eof`` - the condition name tested at [common/acas016.cbl:L373]."""
        return self.cobol_file_status != 0


def _handler_file_key(ctx: _HandlerContext, text: str) -> None:
    """``move <x> to WS-File-Key`` at handler level - ``pic x(64)``, truncating."""
    ctx.logging_data.ws_file_key = _truncate_move(text, _WS_FILE_KEY_WIDTH)


def aa010_main(ctx: _HandlerContext) -> None:
    """``aa010-main.`` [common/acas016.cbl:L244]

    The handler's mainline.  Its full sequence, in the COBOL's order, is driven by
    :func:`dispatch`; this function performs the part that precedes the RDB branch.

    ``[common/acas016.cbl:L248-L249]``, VERBATIM::

         move     3      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice used in FH logging
         move     12     to WS-Log-File-No.  *> RDB, File/Table

    (The agent brief renders that comment as ``5 = Invoice`` with spaces; the file
    itself writes ``5=Invoice`` closed up.  The file wins - this is a verbatim
    quotation, so it matches the byte the maintainer typed.)

    ⭐⭐ N-logsystem5-meaning.  THE SUBSYSTEM LEGEND DISAGREES WITH ITSELF ACROSS
    HANDLERS.  This one says ``5=Invoice``; ``common/acas013.cbl:L298`` and
    ``common/acas015.cbl:L291`` both say ``5=Stock``; ``acas000`` uses
    ``0 = Params``.  Three incompatible legends for code 5 in one codebase.
    :class:`acas_posting.dal.status.LogSystem` carries ``STOCK = 5``, so this module
    uses ``LogSystem.SL`` (3) for its own value and records the disagreement rather
    than editing the shared enum.

    ⚠ N-log.  ``WS-Log-File-No`` is set to 12 here and OVERWRITTEN with 22 on the
    RDB path at [:L567] - note the capitalisation flip, ``-No`` here against
    ``-no`` there.  The pair (system 3, file 22) is what the RDB path logs.  The
    file number 12->22 is a THREE-WAY collision: ``acas006`` (system 2),
    ``acas015`` (system 6) and ``acas016`` (system 3) all use it, so only the
    ``(system, file)`` pair disambiguates.
    """
    logging_data = ctx.logging_data
    # move 3 to WS-Log-System.  [common/acas016.cbl:L248]
    logging_data.ws_log_system = WS_LOG_SYSTEM
    # move 12 to WS-Log-File-No.  *> RDB, File/Table   [:L249]
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT


def aa020_process_open(ctx: _HandlerContext) -> None:
    """``aa020-Process-Open.`` [common/acas016.cbl:L316]

    ISAM path.  Four access types, tested as a nest of ``if/else`` rather than an
    ``evaluate`` [:L320-L345]:

    * ``fn-input`` - ``open input``; on failure ``move 35 to fs-Reply``, close, exit
      [:L321-L327].
    * ``fn-i-o`` - ``open i-o``; on failure the recovery dance
      ``close / open output / close / open i-o`` with the comment
      ``*> Doesnt create in i-o`` [:L330-L336] and the trailing doubt
      ``*> file-status will NOT be updated   ????``.
    * ``fn-output`` - ``open output``, with ``*> should not need to be used`` and
      ``*> caller should check fs-reply`` [:L338-L339].
    * ``fn-extend`` - ``*> Must not be used for ISAM files``: 997 / 99 [:L341-L344].

    ⭐ THERE IS NO OPEN-OUTPUT DELETE.  ``fn-output`` here is a plain
    ``open output``; nothing clears either table.  Confirmed by finding no
    ``if fn-Open and`` anywhere in the file.  N-noopenoutput.

    ⭐ N-noinit.  ``[common/acas016.cbl:L347]``, verbatim - a dated commenting-out::

    *> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.

    The zeroing was deliberately disabled on 27 July 2016, so the caller's previous
    status survives an open.  Not reinstated.
    """
    logging_data = ctx.logging_data
    # move spaces to WS-File-Key.  *> for logging   [:L317]
    _handler_file_key(ctx, "")
    # move 201 to WS-No-Paragraph.  [:L318]
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa020-Process-Open"]
    access_type = ctx.file_access.access_type
    if access_type == int(AccessType.INPUT):
        if not _isam_file_available(ctx):
            # move 35 to fs-Reply / close / go to aa999-Main-Exit  [:L322-L326]
            ctx.file_access.fs_reply = _OPEN_INPUT_FAILED_FS_REPLY
            aa999_main_exit(ctx)
            return
    elif access_type == int(AccessType.I_O):
        # The close/open-output/close/open-i-o recovery [:L331-L335].  With no ISAM
        # file the sequence cannot succeed, and the COBOL's own comment at [:L336]
        # says the status is not updated by it either way.
        pass
    elif access_type == int(AccessType.OUTPUT):
        # open output Invoice-File  *> caller should check fs-reply   [:L338-L339]
        # A PLAIN OPEN.  No table is cleared.  N-noopenoutput.
        pass
    elif access_type == int(AccessType.EXTEND):
        # *> Must not be used for ISAM files: 997 / 99   [:L341-L343]
        ctx.file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        aa999_main_exit(ctx)
        return
    # NOT reinstated: 'move zeros to FS-Reply WE-Error' is commented out at [:L347].
    # move zero to Cobol-File-Status.  [:L348]
    ctx.cobol_file_status = 0
    # move "OPEN SL INVOICE File" to WS-File-Key.  [:L349]
    _handler_file_key(ctx, "OPEN SL INVOICE File")
    # if fs-reply not = zero move 999 to WE-Error.  [:L350-L351]
    if ctx.file_access.fs_reply != int(FsReply.SUCCESS):
        ctx.file_access.we_error = HANDLER_BAD_FUNCTION_WE_ERROR
    # go to aa999-main-exit.  *> with test for dup processing   [:L352]
    aa999_main_exit(ctx)


def aa030_process_close(ctx: _HandlerContext) -> None:
    """``aa030-Process-Close.`` [common/acas016.cbl:L354]

    ⭐ THIS IS THE ONLY PARAGRAPH THAT LOGS TWICE.  ``[common/acas016.cbl:L361-L365]``,
    verbatim::

         perform  aa999-main-exit.
         move     zero to  File-Function
                           Access-Type.              *> close log file
         perform  Ca-Process-Logs.
         go       to aa-main-exit.

    It performs ``aa999-main-exit`` (which itself logs when ``Testing-1``), then
    ZEROES ``File-Function`` and ``Access-Type`` and logs AGAIN unconditionally -
    the second call being what closes the log file.  Every other paragraph reaches
    ``aa999-main-exit`` once and stops.  Reproduced exactly, including the
    zeroing, which is observable to the caller.

    ⭐ N-noinit again: ``move zeros to FS-Reply WE-Error`` is commented out with the
    same 27/07/16 stamp at [:L359].
    """
    logging_data = ctx.logging_data
    # move 202 to WS-No-Paragraph.  [:L355]
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa030-Process-Close"]
    # move spaces to WS-File-Key.  *> for logging   [:L356]
    _handler_file_key(ctx, "")
    # close Invoice-File.  [:L357] - ISAM, omitted.
    # move zero to Cobol-File-Status.  [:L360]
    ctx.cobol_file_status = 0
    # move "CLOSE SL INVOICE File" to WS-File-Key   [:L361]
    _handler_file_key(ctx, "CLOSE SL INVOICE File")
    # perform aa999-main-exit.  [:L362]
    aa999_main_exit(ctx)
    # move zero to File-Function Access-Type.  *> close log file   [:L363-L364]
    ctx.file_access.file_function = 0
    ctx.file_access.access_type = 0
    # perform Ca-Process-Logs.  [:L365] - UNCONDITIONAL, unlike aa999-main-exit's.
    ca_process_logs_handler(ctx)


def aa040_process_read_next(ctx: _HandlerContext) -> None:
    """``aa040-Process-Read-Next.`` [common/acas016.cbl:L367]

    ⭐⭐ N-stop.  THIS PARAGRAPH CONTAINS A LIVE DEBUGGING ``STOP``.
    ``[common/acas016.cbl:L373-L380]``, VERBATIM::

         if       Cobol-File-Eof
                  move 10 to FS-Reply
                             WE-Error
                  move spaces to WS-Invoice-Key  *> 08/08/23
                                 SQL-Err
                                 SQL-Msg
                  stop "Cobol File EOF"               *> FOR TESTING ONLY
                  go to aa999-main-exit
         end-if

    ``stop "Cobol File EOF"`` halts the run and waits for the operator.  Its comment
    is UPPER-CASED here (``*> FOR TESTING ONLY``) where ``common/acas015.cbl:L424``
    writes the same thing in lower case.  It sits on the ISAM path, so the migrated
    cycle never reaches it.

    It is recorded as an anomaly AND as a deliberate omission, and is NOT reproduced
    as a pause: no ``input()``, no ``time.sleep``, no blocking of any kind - AAP
    section 0.3.4 is explicit that an accept whose only effect is to block a
    terminal is dropped while any control transfer around it is kept.  The control
    transfer to ``aa999-main-exit`` IS kept.

    ⭐ ``move spaces to WS-Invoice-Key  *> 08/08/23`` [:L376] is a dated later fix
    that blanks the key on the EOF path.  Preserved.
    """
    logging_data = ctx.logging_data
    # move 203 to WS-No-Paragraph.  [:L372]
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa040-Process-Read-Next"]
    # if Cobol-File-Eof ...  [:L373]
    if ctx.cobol_file_eof():
        # move 10 to FS-Reply WE-Error  [:L374-L375]
        ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
        ctx.file_access.we_error = int(FsReply.END_OF_FILE)
        # move spaces to WS-Invoice-Key *> 08/08/23 / SQL-Err / SQL-Msg  [:L376-L378]
        ctx.invoice.ws_sih_invoice = 0
        ctx.invoice.ws_sih_test = 0
        logging_data.sql_err = " " * SQL_ERR_WIDTH
        logging_data.sql_msg = " " * SQL_MSG_WIDTH
        # stop "Cobol File EOF"  *> FOR TESTING ONLY   [:L379]
        # DELIBERATELY NOT REPRODUCED as a pause.  The transfer below IS reproduced.
        _LOG.debug(
            "acas016 aa040: ISAM 'stop \"Cobol File EOF\"' site reached "
            "[common/acas016.cbl:L379] - recorded, not executed"
        )
        # go to aa999-main-exit  [:L380] - Class 3.
        aa999_main_exit(ctx)
        return
    # read Invoice-File next record at end ...  [:L383-L390] - ISAM verb, omitted.
    # With no ISAM file the read cannot succeed, so the 'at end' arm is what runs:
    # move 10 to we-error fs-reply  *> EOF
    ctx.file_access.we_error = int(FsReply.END_OF_FILE)
    ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
    # set Cobol-File-EoF to true / move 1 to Cobol-File-Status
    # *> JIC above dont work :)   [:L385-L386]
    ctx.cobol_file_status = 1
    # initialize Invoice-Record  [:L387]
    # The handler's own ISAM record area is the SAME linkage record the bridge
    # sees, so the whole of it clears - key included.
    _initialise_ws_invoice_record(ctx.invoice)
    # move "EOF" to WS-File-Key  *> for logging   [:L388]
    _handler_file_key(ctx, "EOF")
    # go to aa999-main-exit  [:L389]
    aa999_main_exit(ctx)


def aa045_eval_keys(ctx: _HandlerContext) -> None:
    """``aa045-Eval-Keys.`` [common/acas016.cbl:L398]

    ``evaluate File-Function  *> Set up keys just for logging`` [:L399].  Functions
    4, 5, 7, 8 and 9 fall through to a nested ``evaluate File-Key-No`` that moves
    the key for key 1 and spaces for anything else [:L405-L411]; every other
    function gets spaces [:L412-L413].

    ⭐ Note the comment on ``when 8`` at [:L403]:
    ``*> fn-delete    For delete can ignore Desc key`` - a reference to a
    descending key this table does not have.

    ⭐ AND NOTE WHICH FUNCTIONS ARE ABSENT: 3 and 34.  A read-next therefore leaves
    ``WS-File-Key`` at whatever the previous call put there, until the paragraph
    body overwrites it.  Reproduced by simply not listing them.
    """
    logging_data = ctx.logging_data
    del logging_data  # written only through the two helpers below
    function_code = ctx.file_access.file_function
    if function_code in _AA045_KEYED_FUNCTIONS:
        # evaluate File-Key-No: when 1 -> move the key; when other -> spaces.
        if ctx.logging_data.file_key_no == 1:
            # move WS-Invoice-Key to Invoice-Key / move Invoice-Key to WS-File-Key
            _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
        else:
            _handler_file_key(ctx, "")
    else:
        # when other move spaces to WS-File-Key  [:L412-L413]
        _handler_file_key(ctx, "")


def aa050_process_read_indexed(ctx: _HandlerContext) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas016.cbl:L416]

    ISAM read by key.  On failure it builds the message
    ``"Failed action in read-indexed for " ws-invoice-key`` [:L432-L435], which is
    the arm that runs here.

    ⭐ The trailing 998 at [:L437] carries the comment
    ``*> file seeks key type out of range but should never get here       998`` - the
    author knew the guard at [:L256] had already rejected key numbers other than 1,
    so this is defence in depth against his own dispatch.
    """
    logging_data = ctx.logging_data
    # move 204 to WS-No-Paragraph.  [:L418]
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa050-Process-Read-Indexed"]
    # perform aa045-Eval-keys.  [:L419]
    aa045_eval_keys(ctx)
    # move zero to Cobol-File-Status.  [:L420]
    ctx.cobol_file_status = 0
    # if File-Key-No = 1 ...  [:L422]
    if logging_data.file_key_no == 1:
        # read Invoice-File key Invoice-Key invalid key move 21 to we-error fs-reply
        if not _isam_file_available(ctx):
            ctx.file_access.we_error = int(FsReply.INVALID_KEY_ON_START)
            ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
        if ctx.file_access.fs_reply == int(FsReply.SUCCESS):
            _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
        else:
            # initialize WS-Invoice-Record / spaces / the message   [:L431-L435]
            _initialise_ws_invoice_record(ctx.invoice)
            _handler_file_key(
                ctx,
                f"Failed action in read-indexed for {ctx.invoice.ws_invoice_key}",
            )
        aa999_main_exit(ctx)
        return
    # move 998 to WE-Error  *> ... but should never get here   [:L437-L438]
    ctx.file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
    ctx.file_access.fs_reply = int(FsReply.ERROR)
    aa999_main_exit(ctx)


def aa060_process_start(ctx: _HandlerContext) -> None:
    """``aa060-Process-Start.`` [common/acas016.cbl:L442]

    ⭐⭐ ITS ACCESS-TYPE GUARD ADMITS 5..9; THE BRIDGE'S ADMITS ONLY 5..8.
    ``[common/acas016.cbl:L455-L458]``, VERBATIM::

         if       access-type < 5 or > 9                   *> NOT using 'not >' - might be 08/08/23
                  move 998 to WE-Error                     *> 998 Invalid calling parameter settings
                  go to aa999-main-exit
         end-if

    So ``fn-not-greater-than`` (9) passes HERE and is rejected by the bridge with
    99/997 [common/slinvoiceMT.cbl:L952-L956].  N-access-type-9-unreachable.

    ⭐ AND THIS GUARD SETS ``WE-Error`` WITHOUT SETTING ``FS-Reply``.  Compare the
    key guard at [:L256-L259], which sets both 998 AND ``fs-reply`` 99.  Here only
    998 is moved, and ``fs-reply`` was zeroed two statements earlier at [:L451], so
    the caller sees ``FS-Reply`` 0 - SUCCESS - alongside ``WE-Error`` 998.  A caller
    testing only ``FS-Reply`` proceeds as though the START worked.
    N-start-guard-no-fs-reply.  Reproduced exactly; do NOT add the 99.

    ⭐ THE FIVE RELATION TESTS ARE FIVE SEPARATE ``if`` BLOCKS, not an ``evaluate``
    [:L461-L494], and the fifth - ``fn-not-greater-than`` - carries
    ``*> Added 08/08/23``, matching the guard's own ``might be 08/08/23`` note.
    Each sets ``FS-Reply`` 21 on an invalid key.
    """
    logging_data = ctx.logging_data
    # move 205 to WS-No-Paragraph.  [:L446]
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa060-Process-Start"]
    # perform aa045-Eval-keys.  *> mv WS key to FD   [:L447]
    aa045_eval_keys(ctx)
    # move zeros to fs-reply WE-Error.  [:L448-L449]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    # move zero to Cobol-File-Status.  [:L450]
    ctx.cobol_file_status = 0
    # if access-type < 5 or > 9  *> NOT using 'not >' - might be 08/08/23   [:L455]
    low, high = HANDLER_START_ACCESS_TYPE_RANGE
    access_type = ctx.file_access.access_type
    if access_type < low or access_type > high:
        # move 998 to WE-Error - AND NOTHING TO FS-REPLY.  [:L456]
        ctx.file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        aa999_main_exit(ctx)
        return
    # The five 'start Invoice-File key <rel>' blocks [:L461-L494].  ISAM verbs,
    # omitted; each 'invalid key' arm moves 21 to Fs-Reply, which is what an
    # absent file produces.
    if logging_data.file_key_no == 1 and start_access_type_is_valid(access_type):
        if not _isam_file_available(ctx):
            ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
            aa999_main_exit(ctx)
            return
    # if File-Key-No = 1 move Invoice-Key to WS-File-Key.  [:L495-L496]
    if logging_data.file_key_no == 1:
        _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
    aa999_main_exit(ctx)


def aa070_process_write(ctx: _HandlerContext) -> None:
    """``aa070-Process-Write.`` [common/acas016.cbl:L500]

    ISAM ``write``; the ``invalid key`` arm moves 22 - DUPLICATE KEY - at [:L507].
    Note it zeroes ``FS-Reply`` and ``WE-Error`` explicitly at [:L503], unlike
    ``aa020``/``aa030`` where the same statement is commented out.
    """
    logging_data = ctx.logging_data
    # move 206 to WS-No-Paragraph.  [:L501]
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa070-Process-Write"]
    # move WS-Invoice-Record to Invoice-Record.  [:L502]
    # move zeros to FS-Reply WE-Error.  move zero to Cobol-File-Status.  [:L503-L504]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ctx.cobol_file_status = 0
    # write Invoice-Record invalid key move 22 to FS-Reply end-write.  [:L505-L507]
    if not _isam_file_available(ctx):
        ctx.file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
    # move Invoice-Key to WS-File-Key.  [:L508]
    _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
    aa999_main_exit(ctx)


def aa080_process_delete(ctx: _HandlerContext) -> None:
    """``aa080-Process-Delete.`` [common/acas016.cbl:L511]

    ISAM ``delete``; the ``invalid key`` arm moves 21 [:L518].
    """
    logging_data = ctx.logging_data
    # move 207 to WS-No-Paragraph.  [:L512]
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa080-Process-Delete"]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ctx.cobol_file_status = 0
    # delete Invoice-File record invalid key move 21 to FS-Reply.  [:L516-L518]
    if not _isam_file_available(ctx):
        ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
    aa999_main_exit(ctx)


def aa090_process_rewrite(ctx: _HandlerContext) -> None:
    """``aa090-Process-Rewrite.`` [common/acas016.cbl:L522]

    ISAM ``rewrite``; the ``invalid key`` arm moves 21 [:L529].  Note its
    ``end-rewrite`` at [:L530] carries NO terminating period where ``aa070``'s
    ``end-write.`` [:L507] and ``aa080``'s ``end-delete.`` [:L518] both do.
    N-punctuation.
    """
    logging_data = ctx.logging_data
    # move 208 to WS-No-Paragraph.  [:L524]
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa090-Process-Rewrite"]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ctx.cobol_file_status = 0
    # rewrite Invoice-Record invalid key move 21 to FS-Reply   [:L527-L529]
    if not _isam_file_available(ctx):
        ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
    aa999_main_exit(ctx)


def aa100_bad_function(ctx: _HandlerContext) -> None:
    """``aa100-Bad-Function.`` [common/acas016.cbl:L534]

    ``[common/acas016.cbl:L536-L539]``, VERBATIM::

    *> Houston; We have a problem
    *>
         move     999 to WE-Error.                         *> 999
         move     99  to fs-reply.

    ⭐⭐ N-delete-all-bad-function.  FUNCTION CODE 6 ARRIVES HERE.  The dispatch's
    ``when other`` comment claims ``*> 6 is spare / unused``
    [common/acas016.cbl:L309], yet ``fn-Delete-All value 6`` exists
    [copybooks/wsfnctn.cob:L94] and the facade publishes ``Invoice-Delete-All``
    [copybooks/Proc-ACAS-FH-Calls.cob:L911].  So a caller performing that facade
    verb reaches THIS paragraph and gets 999/99 - a published verb that cannot
    succeed through the handler, the same family as AAP Anomaly #6.  Reproduced; no
    Delete-All branch is added to :func:`dispatch`.

    ⚠ The bridge's own bad-function pair is 990/99 [common/slinvoiceMT.cbl:L1415-L1416],
    NOT 999/99.  Different codes at the two layers, both preserved.

    ⭐ THERE IS NO ``go to`` HERE.  Unlike the bridge's ``ba100-Bad-Function``,
    which ends ``go to ba999-end`` [:L1417], this paragraph simply ENDS and falls
    through into ``aa999-main-exit`` at [:L541].  Made explicit.
    """
    # move 999 to WE-Error.  move 99 to fs-reply.
    ctx.file_access.we_error = HANDLER_BAD_FUNCTION_WE_ERROR
    ctx.file_access.fs_reply = int(FsReply.ERROR)
    # FALL-THROUGH into aa999-main-exit [:L541] - no transfer of control.
    aa999_main_exit(ctx)


def aa999_main_exit(ctx: _HandlerContext) -> None:
    """``aa999-main-exit.`` [common/acas016.cbl:L541]

    ``[common/acas016.cbl:L542-L544]``, verbatim::

     aa999-main-exit.
         if       Testing-1
                  perform Ca-Process-Logs
         end-if.

    Then falls through to ``aa-main-exit`` [:L546] and ``aa-Exit`` [:L550].
    """
    # if Testing-1 perform Ca-Process-Logs end-if.
    if ctx.dal_common.sw_testing != 0:
        ca_process_logs_handler(ctx)
    aa_main_exit(ctx)


def aa_main_exit(ctx: _HandlerContext) -> None:
    """``aa-main-exit.`` [common/acas016.cbl:L546]

    ``[common/acas016.cbl:L547-L549]``, verbatim::

     aa-main-exit.
    *>
    *> Now have processed cobol flat file,  so ..

    A label with a comment and no statements - it exists only to be a ``go to``
    target and to fall through to ``aa-Exit``.  Kept as a function so the
    paragraph-to-function mapping is complete (R-5), and it does what the COBOL
    does: nothing but continue.
    """
    aa_exit(ctx)


def aa_exit(ctx: _HandlerContext) -> None:
    """``aa-Exit.`` [common/acas016.cbl:L550]

    ``exit program.`` [:L551] - returns to the caller.  In Python the return is the
    function returning; there is nothing to do, and doing nothing is correct.
    """
    del ctx


def aa_process_flat_file(ctx: _HandlerContext) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas016.cbl:L242]

    The section that owns ``aa010-main`` through ``aa-Exit``.  Entering the section
    means entering its first paragraph, so this is :func:`aa010_main` followed by
    the guards and the function ``evaluate`` - all of which
    :func:`dispatch` performs in the COBOL's order.  It is published for
    traceability and delegates rather than duplicating.
    """
    aa010_main(ctx)


def ca_process_logs_handler(ctx: _HandlerContext) -> None:
    """``Ca-Process-Logs.`` [common/acas016.cbl:L633] - the HANDLER's copy.

    ⭐⭐ N-nolog-on-dal.  ITS COMMENT IS ON THE LABEL LINE.
    ``[common/acas016.cbl:L633]``, VERBATIM::

     Ca-Process-Logs. *> Not called on DAL access as it does it already

    So on the RDB path this must NOT run - the bridge has already logged, and
    calling it again would double every log record.  :func:`dispatch` honours that
    by taking the RDB branch at [:L271-L275] before any ``aa`` paragraph runs, so
    nothing on the DAL path reaches here.

    The body is ``call "fhlogger" using File-Access ACAS-DAL-Common-data``
    [:L635-L636].  ``common/fhlogger.cbl`` is OUT OF SCOPE per AAP section 0.2.2,
    so the call is not reproduced as a call; the diagnostic it carries is emitted
    at debug level per AAP section 0.3.4.
    """
    logging_data = ctx.logging_data
    _LOG.debug(
        "acas016 fhlogger: system=%s file=%s para=%s fs_reply=%s we_error=%s key=%s",
        logging_data.ws_log_system,
        logging_data.ws_log_file_no,
        logging_data.ws_no_paragraph,
        ctx.file_access.fs_reply,
        ctx.file_access.we_error,
        sanitise_for_log(logging_data.ws_file_key.rstrip()),
    )


def ca_exit_handler(ctx: _HandlerContext) -> None:
    """``ca-Exit.`` [common/acas016.cbl:L639] - ``exit.``  A bare paragraph exit."""
    del ctx


# ---------------------------------------------------------------------------
# acas016's OWN 'ba' section - the RDBMS branch
# ---------------------------------------------------------------------------
# ⚠ N-paragraph-name-collision.  The HANDLER has a 'ba-Process-RDBMS section.'
# [common/acas016.cbl:L553] with paragraphs ba010, ba012, ba015 and ba-rdbms-exit,
# and the BRIDGE has an unrelated 'ba' family - ba010-Initialise,
# ba020-Process-Open ... ba999-end [common/slinvoiceMT.cbl:L498-L1440].  Two
# different programs, same prefix, different paragraphs.  Python has one namespace
# per module and this module owns both programs, so the handler's four carry a
# '_handler' suffix.  The COBOL names are quoted in each docstring so traceability
# resolves either way; nothing is renamed in the COBOL.


def ba010_test_ws_rec_size_handler(ctx: _HandlerContext) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas016.cbl:L561]

    ``[common/acas016.cbl:L563-L567]``, VERBATIM::

    *>     Test on very first call only  (So do NOT use var A & B again)
    *>       Lets test that Data-record size is = or > than declared Rec in DAL
    *>          as we cant adjust at compile/run time due to ALL Cobol compilers ?
    *>
         move     22 to WS-Log-File-no.        *> for FHlogger

    ⭐ N-log.  THE ONLY STATEMENT IN THIS PARAGRAPH IS THE LOG-FILE-NUMBER
    OVERWRITE: 12, set at [:L249], becomes 22 here.  Note the capitalisation flip -
    ``WS-Log-File-No`` at [:L249] against ``WS-Log-File-no`` at [:L567]; COBOL is
    case-insensitive so both name the same field.  22 is what the RDB path logs.

    ⚠ The file number 22 is a THREE-WAY collision - ``acas006`` (log system 2),
    ``acas015`` (log system 6) and ``acas016`` (log system 3) all use it - so only
    the ``(system, file)`` pair identifies the table in a log.

    The paragraph then FALLS THROUGH into ``ba012-Test-WS-Rec-Size-2`` [:L569] with
    no transfer of control.  ⚠ THE FALL-THROUGH IS DRIVEN BY
    :func:`ba_process_rdbms_handler`, NOT BY THIS FUNCTION, because COBOL's two
    PERFORM forms differ and both are used against this section:

    * ``perform ba-Process-RDBMS`` [:L273] is a SECTION perform, so it runs
      ba010 -> ba012 -> ba015 -> ba-rdbms-exit, fall-throughs included.
    * ``perform ba012-Test-WS-Rec-Size-2.`` [:L279] is a PARAGRAPH perform, so it
      runs ba012's body ALONE and returns - it does NOT reach ba015 and therefore
      does NOT call the bridge.

    Folding the fall-through into the paragraph functions themselves would make the
    ISAM path call the bridge, which the COBOL never does.  So each paragraph
    function holds only its own body and the section driver composes them - the AAP
    section 0.3.3 "paragraph-as-function composition" pattern, with fall-through made
    explicit.
    """
    # move 22 to WS-Log-File-no.  *> for FHlogger   [:L567]
    ctx.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB
    # FALL-THROUGH into ba012-Test-WS-Rec-Size-2 - composed by
    # ba_process_rdbms_handler, for the PERFORM-form reason given above.


def ba012_test_ws_rec_size_2_handler(ctx: _HandlerContext) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas016.cbl:L569]

    The first-call-only record-length guard and credential load.  ``if A = zero``
    [:L571] makes the whole block run ONCE per program activation, with the comment
    at [:L563] insisting ``(So do NOT use var A & B again)``.

    It compares ``function Length (WS-Invoice-Record)`` against
    ``function length (Invoice-Record)`` and on ``A < B`` sets ``901``/``99``
    [:L579-L581], with the aside
    ``*> COULD LET caller module deal with these errors !!!!!!!`` and the
    explanation ``*> allow for last field ( FILLER) not being present in layout.``
    Then it displays ``SL902``/``SL901``, accepts a keypress and jumps to
    ``ba-rdbms-exit`` [:L584-L597].

    On success it loads the six connection fields from the system record
    [:L604-L609] with the maintainer's hope attached at [:L602]:
    ``*>           hopefully once is enough  :)``

    ⚠ BOTH HALVES BELONG TO ``dal/connection.py`` AND ARE CALLED, NOT DUPLICATED.
    :func:`acas_posting.dal.connection.load_rdb_data_once` owns the once-only
    credential load and :func:`acas_posting.dal.connection.mysql_1000_open` owns the
    length guard and the ``901`` report.  The agent brief is explicit: *"call it, do
    not duplicate it."*

    Per AAP section 0.3.4 the ``accept Accept-Reply at 2433`` [:L596] is DROPPED -
    its only effect is to block a terminal - while the control transfer to
    ``ba-rdbms-exit`` that follows it IS preserved, and is what this function's
    return value reports.

    ⭐⭐ N-perform-range-violation (NEW).  ``go to ba-rdbms-exit`` at [:L596] leaves
    the PERFORM range whenever this paragraph was entered by the PARAGRAPH perform at
    [:L279] - the ISAM path - because ``ba-rdbms-exit`` is a DIFFERENT paragraph of
    the section and its statement is ``exit section``.  A ``GO TO`` out of a
    performed range makes the return undefined in the standard and
    implementation-dependent in practice.  Recorded, not resolved: reproducing an
    undefined return is not possible, so the Python returns normally and reports the
    jump to its caller, and the divergence is logged as an oracle question alongside
    N-recsize.

    ⭐ N-recsize.  The comparison this paragraph exists to make is disputed by its own
    author: ``copybooks/slwsinv.cob:L9-L11`` records the record size as 129
    (09/03/09), then 134 (24/03/12), then 137 (18/01/17), with a shouted warning at
    [:L12] ``*> WARNING UPDATE all layouts for 5 byte increase (extra statuses)`` and
    a second at ``copybooks/slwsinv2.cob:L25``
    ``*>  NEED TO DO A SIZING CHECK for all INVOICE copybooks.``  NOTHING IS RESOLVED
    HERE - it is an oracle question, exactly like AAP Anomaly #15's 96-versus-98.

    Returns:
        ``True`` when the paragraph took ``go to ba-rdbms-exit`` [:L596], so the
        section driver must NOT fall through into ``ba015-Test-Ends``; ``False`` on
        the normal path.
    """
    # if A = zero  *> so it is being called first time   [:L571]
    #     move function Length (WS-Invoice-Record) to A   [:L572-L574]
    #     move function length (Invoice-Record)    to B   [:L575-L577]
    #     if A < B  ->  901 / 99                          [:L578-L581]
    #
    # ⚠ DELIBERATE OMISSION, RECORDED (R-5).  The compare cannot be reproduced and
    # cannot fire.  In COBOL A and B are the byte lengths of two DIFFERENT
    # declarations of the same layout - the caller's WS-Invoice-Record and the
    # bridge's own Invoice-Record - and the guard exists because the two could drift
    # apart across separately compiled programs.  In Python there is ONE layout:
    # records/sales_invoice.py, generated from the dictionary, shared by caller and
    # bridge alike, so A and B are the same number by construction and `A < B` is
    # unreachable.  Fabricating a byte count to compare against itself would invent
    # a validation (forbidden by R-3) and could only ever produce a false 901.  The
    # 901 code itself is published and honoured - WeError.RECORD_SIZE_MISMATCH in
    # dal/status.py, with its fatal disposition in status.raise_for_status - so a 901
    # arriving from any layer is still treated exactly as the COBOL treats it.
    #
    # move RDBMS-DB-Name to DB-Schema / User to DB-UName / Passwd to DB-UPass /
    # Port to DB-Port / Host to DB-Host / Socket to DB-Socket   [:L604-L609]
    #   *>           hopefully once is enough  :)               [:L602]
    # connection.py owns the once-only latch; it is CALLED, not duplicated.
    ctx.file_access.rdb_data = load_rdb_data_once(ctx.system_record)
    # No 901 was raised here, so no 'go to ba-rdbms-exit' was taken.
    return False


def ba015_test_ends_handler(ctx: _HandlerContext) -> None:
    """``ba015-Test-Ends.`` [common/acas016.cbl:L611]

    ⭐ THE BRIDGE ``CALL`` IS INLINE HERE.  There is NO ``ba020-Process-DAL``
    paragraph in this handler - N-nobadal.  ``[common/acas016.cbl:L614-L627]``,
    VERBATIM::

    *>   HERE we need a CDF [Compiler Directive] to select the correct DAL based
    *>     on the pre SQL compiler e.g., JCs or dbpre or Prima conversions <<<<  ? >>>>>
    *>        Do this after system testing and pre code release.
    *>  NOW SET UP FOR JC pre-sql compiler system.
    *>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql
         call     "slinvoiceMT" using File-Access
                                      ACAS-DAL-Common-data

                                      WS-Invoice-Record
         end-call.
    *>   Any errors leave it to caller to recover from

    ⭐ N-cdftodo.  The compiler-directive TODO at [:L614-L616] was never finished.
    The migration does NOT act on it: there is exactly one bridge, it is the JC
    pre-SQL one, and inventing a selection mechanism would add behaviour.

    ⭐ ``*>   Any errors leave it to caller to recover from`` [:L627] IS THE CONTRACT
    for this whole module.  Nothing raises; the status pair is returned.
    """
    # call "slinvoiceMT" using File-Access ACAS-DAL-Common-data WS-Invoice-Record
    #
    # ⭐ THE PARAMETER ORDER IS THE BRIDGE'S, NOT THE HANDLER'S.  The handler was
    # entered with System-Record first and File-Access third; it calls the bridge
    # with File-Access FIRST and no System-Record at all.  Preserved as written.
    slinvoice_mt(
        ctx.file_access,
        ctx.dal_common,
        ctx.invoice,
        connection=ctx.invoice.connection,
        system_record=ctx.system_record,
    )
    # *> Any errors leave it to caller to recover from  [:L627] - no test, no raise.
    # FALL-THROUGH into ba-rdbms-exit [:L629] - composed by ba_process_rdbms_handler.


def ba_rdbms_exit_handler(ctx: _HandlerContext) -> None:
    """``ba-rdbms-exit.`` [common/acas016.cbl:L629]

    ``exit section.`` - the RDB branch's single exit, and the target of the
    ``go to ba-rdbms-exit`` the ``901`` length-error path takes [:L597].  Nothing to
    do but return, which is what ``exit section`` does.
    """
    del ctx


def ba_process_rdbms_handler(ctx: _HandlerContext) -> None:
    """``ba-Process-RDBMS section.`` [common/acas016.cbl:L553]

    ``[common/acas016.cbl:L556-L560]``, verbatim::

    *>********************************************************************
    *>  Here we call the relevent RDBMS module for this table            *
    *>   which will include processing any other joined tables as needed *
    *>********************************************************************

    "any other joined tables as needed" is this module's whole reason for owning
    TWO tables: ``SAINV-LINES-REC`` is the joined table, reached through the RG
    paragraphs of the bridge.

    Entering the section enters its first paragraph, ``ba010-Test-WS-Rec-Size``, and
    the remaining paragraphs run by fall-through until ``ba-rdbms-exit``'s
    ``exit section``.  That composition is written out here because it is the SECTION
    perform's semantics, and the same section's ba012 is ALSO reached by a PARAGRAPH
    perform from [:L279] where the fall-through must NOT happen.
    """
    # ba010-Test-WS-Rec-Size  [:L561]
    ba010_test_ws_rec_size_handler(ctx)
    # ... falls through into ba012-Test-WS-Rec-Size-2  [:L569]
    jumped_to_exit = ba012_test_ws_rec_size_2_handler(ctx)
    if jumped_to_exit:
        # go to ba-rdbms-exit  [:L596] - the 901 length-error path, which SKIPS the
        # bridge call entirely.  Class 2 forward terminator (AAP section 0.4.2).
        ba_rdbms_exit_handler(ctx)
        return
    # ... falls through into ba015-Test-Ends  [:L611]
    ba015_test_ends_handler(ctx)
    # ... falls through into ba-rdbms-exit  [:L629] -> exit section
    ba_rdbms_exit_handler(ctx)


# ---------------------------------------------------------------------------
# The handler entry point
# ---------------------------------------------------------------------------


def dispatch(
    system: SystemRecord,
    invoice: InvoiceBuffer,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> FileAccess:
    """``call "acas016" using ...`` - the handler, entered as its callers enter it.

    THE FIVE-PARAMETER SIGNATURE IS THE COBOL'S, IN THE COBOL'S ORDER.
    ``[common/acas016.cbl:L233-L239]``, VERBATIM::

     L233   Procedure Division Using System-Record

                                     WS-Invoice-Record

                                     File-Access
                                     File-Defs
                                     ACAS-DAL-Common-data.

    matching the AAP section 0.4.3 contract exactly::

        FROM:  call "acas016" using System-Record WS-Invoice-Record File-Access
                                   File-Defs ACAS-DAL-Common-data
        TO:    acas016_invoice.dispatch(system, invoice, file_access, file_defs,
                                       dal_common)

    ⭐⭐ ONE RECORD PARAMETER FOR TWO TABLES.  ``WS-Invoice-Record`` is a UNION
    buffer with three redefining views [copybooks/slwsinv2.cob:L27], [:L38], [:L91],
    and the function code together with ``WS-Sih-Test`` decides which table is
    touched.  It is NOT split into two typed parameters, because the discriminator
    IS the mechanism the bridge dispatches on.

    The sequence below is the COBOL's, statement for statement:

    1. ``aa010-main``'s log identity - system 3, file 12 [:L248-L249].
    2. The key guard [:L253-L267] - functions 4, 9 and 8 require ``File-Key-No`` 1.
    3. ⭐ NO Open-Output block.  There is none in this handler.  N-noopenoutput.
    4. The RDB branch [:L271-L275], WITH both maintainer comments preserved.
    5. ``ba012-Test-WS-Rec-Size-2`` [:L279].
    6. ⭐ NO zeroing of ``WE-Error``/``FS-Reply`` - commented out at [:L287-L288].
    7. ``move spaces to SQL-Err SQL-Msg SQL-State`` [:L289].
    8. The function ``evaluate`` [:L291-L312], where ``3`` and ``34`` SHARE a branch
       and ``aa100-Bad-Function`` is reachable BOTH from ``when other`` and from the
       unconditional fall-through at [:L314].

    ⚠ NEVER RAISES.  ``[common/acas016.cbl:L627]``: *"Any errors leave it to caller
    to recover from"*.  Read ``file_access.fs_reply`` and ``file_access.we_error``.

    Args:
        system: ``System-Record`` [copybooks/wssystem.cob], whose
            ``RDBMS-Flat-Statuses`` selects the ISAM or the RDB path and whose
            ``RDBMS-*`` fields carry the credentials.
        invoice: ``WS-Invoice-Record`` - the ONE union buffer for BOTH tables.
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L38].
        file_defs: ``File-Defs`` [copybooks/wsnames.cob].  Carried because the
            linkage carries it; the RDB path does not read it, which is itself
            recorded as a deliberate omission.
        dal_common: ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob].

    Returns:
        The same ``file_access``, mutated - a COBOL ``CALL BY REFERENCE``.
    """
    ctx = _HandlerContext(
        system_record=system,
        invoice=invoice,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=dal_common,
    )
    logging_data = ctx.logging_data
    # ---- aa010-main [common/acas016.cbl:L244] ----
    aa010_main(ctx)
    function_code = file_access.file_function
    # ---- The key guard [common/acas016.cbl:L253-L267] ----
    # evaluate File-Function
    #    when 4  *> fn-read-indexed
    #    when 9  *> fn-start
    #      if File-Key-No not = 1: 998 / 99 / exit
    #    when 8  *> fn-delete
    #      if File-Key-No not = 1: 996 / 99 / exit
    #
    # ⭐ N-key2-unreachable.  The guard admits ONLY key 1, yet the bridge declares
    # TWO keys of reference [common/slinvoiceMT.cbl:L296-L310].  So IL-LINE-KEY is
    # declared and can never be selected through a guarded verb; the lines are
    # reached only through the header's cursor and the RG paragraphs.  Do NOT relax
    # this to admit key 2.
    #
    # ⭐ N-996-comment.  The 996 comment at [:L263] is a VERBATIM COPY of the 998
    # comment at [:L257] - 'file seeks key type out of range' - which is wrong for a
    # delete.  Left as the author wrote it.
    if function_code in (int(FileFunction.READ_INDEXED), int(FileFunction.START)):
        if logging_data.file_key_no != 1:
            # move 998 to WE-Error / move 99 to fs-reply / go to aa999-main-exit
            file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            aa999_main_exit(ctx)
            return file_access
    elif function_code == int(FileFunction.DELETE):
        if logging_data.file_key_no != 1:
            # move 996 to WE-Error  *> file seeks key type out of range        996
            file_access.we_error = int(WeError.DELETE_KEY_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            aa999_main_exit(ctx)
            return file_access
    # ---- ⭐ NO 'if fn-Open and fn-output' BLOCK ----
    # Verified absent from the whole file.  Opening for output here is a PLAIN open
    # and clears NEITHER table.  acas005 comments its block out, acas006/acas007
    # make two bridge calls, acas008 coerces the function to delete-all - and
    # acas015/acas016 have no block at all.  Four semantics; this is the fourth.
    # N-noopenoutput.  Do not port acas008's coercion.
    #
    # ---- The RDB branch [common/acas016.cbl:L271-L275] ----
    # if       not FS-Cobol-Files-Used
    #          move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
    #                                  *> needed for DAL? not JC/dbpre versions
    #          perform ba-Process-RDBMS                        *>  Can't hurt
    #          go to AA-Main-Exit
    # end-if.
    #
    # Both maintainer comments are preserved above, verbatim - the questioning
    # '*> needed for DAL? not JC/dbpre versions' and the shrug '*> Can't hurt'.
    flat_statuses = system.system_data_block.rdbms_flat_statuses
    if not _fs_cobol_files_used(flat_statuses):
        # move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
        #
        # ⭐ A GROUP MOVE, NOT A REBIND.  `03 RDBMS-Flat-Statuses`
        # [copybooks/wssystem.cob] and `03 FA-RDBMS-Flat-Statuses`
        # [copybooks/wsfnctn.cob:L72-L83] are two SEPARATE storage areas of the
        # same shape, and a COBOL group `MOVE` copies the sending group's bytes
        # INTO the receiving group - it cannot make one name refer to the other's
        # storage, because COBOL has no such operation.  So each member is copied
        # into the group the caller already holds, which is what the other
        # sixteen handlers do (`acas013_value.py`'s transcription of
        # [common/acas013.cbl:L322] is the same two lines).
        #
        # Rebinding the attribute instead would ALIAS the caller's `File-Access`
        # onto `System-Record`'s own group - two records sharing one object where
        # the COBOL has two areas - so a later write through either name would be
        # visible through the other, and the receiving group would carry the
        # SENDING group's member names (`file_system_used` instead of
        # `fa_file_system_used`), which the next handler to read it cannot find.
        source_statuses = flat_statuses
        target_statuses = file_access.fa_rdbms_flat_statuses
        target_statuses.fa_file_system_used = source_statuses.file_system_used
        target_statuses.fa_file_duplicates_in_use = (
            source_statuses.file_duplicates_in_use
        )
        # perform ba-Process-RDBMS   *> Can't hurt
        ba_process_rdbms_handler(ctx)
        # go to AA-Main-Exit  - Class 3.  The ISAM 'evaluate' below is never
        # reached on this path, which is why aa020..aa090 are unreachable in the
        # migrated cycle and why the 'stop' at [:L379] is harmless.
        aa_main_exit(ctx)
        return file_access
    # ---- perform ba012-Test-WS-Rec-Size-2. [common/acas016.cbl:L279] ----
    # *> Test  Rec lengths first.   [:L277]
    #
    # ⚠ A PARAGRAPH PERFORM, NOT A SECTION PERFORM.  It runs ba012's body ALONE and
    # returns; it does NOT fall through into ba015-Test-Ends, so the ISAM path never
    # calls the bridge.  Contrast [:L273]'s `perform ba-Process-RDBMS`, a SECTION
    # perform that does fall through.  Both forms are honoured, which is why the
    # fall-through lives in ba_process_rdbms_handler and not in the paragraphs.
    #
    # ⭐ N-perform-range-violation.  On THIS path a 901 inside ba012 would take
    # `go to ba-rdbms-exit` [:L596] straight out of the PERFORM range into another
    # paragraph's `exit section` - undefined in the standard.  The return value is
    # read so the divergence is visible rather than silent; it cannot fire, for the
    # reason recorded on ba012 itself.
    if ba012_test_ws_rec_size_2_handler(ctx):
        # The 901 path left the PERFORM range.  Recorded as an oracle question; the
        # nearest faithful behaviour is to stop processing this call.
        aa999_main_exit(ctx)
        return file_access
    # ---- ⭐ NO ZEROING OF WE-Error / FS-Reply ----
    # [common/acas016.cbl:L287-L288], VERBATIM (the second line's leading space is
    # the maintainer's, not a transcription slip - L287 opens its comment in column
    # 1 and L288 in column 2, so even the commented-out block is misaligned):
    # *>  ?   move     zero   to  WE-Error
    #  *>  ?                      FS-Reply.
    # Commented out, question marks and all - a deliberate non-initialisation that
    # lets the caller's previous status survive.  N-noinit.  Do NOT zero them.
    # The same non-initialisation appears one layer down at the bridge's
    # ba010-Initialise [common/slinvoiceMT.cbl:L499-L503], which zeroes SQL-State
    # and comments out We-Error and Fs-Reply - two layers, one decision.
    #
    # ---- move spaces to SQL-Err SQL-Msg SQL-State [common/acas016.cbl:L289] ----
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH
    # ---- The function evaluate [common/acas016.cbl:L291-L312] ----
    # Transcribed in the COBOL's own order.  ⭐ 'when 3' FALLS THROUGH into
    # 'when 34' [:L295-L298], so Read-Next and Read-Next-Header share ONE branch and
    # whatever distinguishes them is re-derived inside it - which the bridge does at
    # ba041-Reread [common/slinvoiceMT.cbl:L722-L723], not here.
    #
    # ⛔ CODES 31, 32 and 33 APPEAR NOWHERE.  The AAP section 0.4.1.5 table claims
    # this module has "the extra by-name/by-batch/by-customer read functions"; that
    # is FACTUALLY WRONG and the correction is recorded in the module docstring.
    # fn-Read-By-Name (31) belongs to acas012, fn-Read-By-Batch (32) and
    # fn-Read-By-Cust (33) to acas019/acas029 [copybooks/wsfnctn.cob:L102-L104].
    # This handler's ONE extra code is 34 [common/acas016.cbl:L297].
    if function_code == int(FileFunction.OPEN):
        aa020_process_open(ctx)
    elif function_code == int(FileFunction.CLOSE):
        aa030_process_close(ctx)
    elif function_code in (
        int(FileFunction.READ_NEXT),  # when 3  *> (fall through)
        int(FileFunction.READ_NEXT_HEADER),  # when 34  *> fn-Read-Next-Header ???
    ):
        # ⭐ The maintainer's own '???' at [:L297] is his uncertainty about the code.
        # Recorded verbatim, not resolved.
        aa040_process_read_next(ctx)
    elif function_code == int(FileFunction.READ_INDEXED):
        aa050_process_read_indexed(ctx)
    elif function_code == int(FileFunction.WRITE):
        aa070_process_write(ctx)
    elif function_code == int(FileFunction.RE_WRITE):
        aa090_process_rewrite(ctx)
    elif function_code == int(FileFunction.DELETE):
        aa080_process_delete(ctx)
    elif function_code == int(FileFunction.START):
        aa060_process_start(ctx)
    else:
        # when other  *> 6 is spare / unused   [common/acas016.cbl:L309-L310]
        #
        # ⭐⭐⭐ N-delete-all-bad-function, AND THE TWO LAYERS DISAGREE.  Verified:
        #
        #   HANDLER  [common/acas016.cbl:L309]  `when other  *> 6 is spare / unused`
        #                                       -> aa100-Bad-Function -> 999 / 99
        #   BRIDGE   [common/slinvoiceMT.cbl:L529-L532], VERBATIM:
        #     *> option 6 is a special to cleardown all LINE data for 1 invoice
        #             when  6
        #                   go to ba085-Process-Delete-All
        #                        *> Coded / D.Tested --- DELETE-ALL  Special
        #
        # So function 6 is "spare / unused" to the handler and a tested special to
        # the bridge.  Because the RDB branch at [:L271-L275] leaves BEFORE this
        # evaluate, WHICH ANSWER A CALLER GETS DEPENDS ON `File-System-Used`:
        # Invoice-Delete-All [copybooks/Proc-ACAS-FH-Calls.cob:L911] WORKS on the RDB
        # path and dies with 999/99 on the ISAM path.  fn-Delete-All value 6 does
        # exist [copybooks/wsfnctn.cob:L94], which is what makes the handler's
        # comment wrong rather than merely terse.
        #
        # Both behaviours are reproduced exactly as written - AAP Anomaly #6's family
        # (a published facade verb that cannot succeed), here conditional on the file
        # system rather than absolute.  NO Delete-All branch is added to this
        # evaluate, because the COBOL's evaluate does not have one.
        #
        # ⚠ And even on the working path the verb does not do what its comment says:
        # ba085 deletes ONE header row by exact ten-byte key (N-ba085-not-actually-all)
        # and bc085's predicate is the string literal `'IL-INVOICE'`, always false, so
        # ZERO line rows are ever deleted (N-bc085-string-constant-predicate).  The
        # "cleardown all LINE data for 1 invoice" clears no line data at all.
        aa100_bad_function(ctx)
        return file_access
    # ---- The unconditional fall-through [common/acas016.cbl:L313-L314] ----
    # *>  Should never get here but in case :(
    # go       to aa100-Bad-Function.
    #
    # ⭐ aa100-Bad-Function is reachable BY TWO ROUTES - 'when other' above and this
    # unreachable-in-practice fall-through.  It is unreachable here because every
    # branch above ends at aa999-main-exit, exactly as the COBOL's 'go to's do; the
    # comment records the author's own belief that it cannot happen.  Both routes
    # are preserved: the branch calls, and this note documents the second route
    # rather than adding a call that the Python control flow makes dead.
    return file_access


# ---------------------------------------------------------------------------
# The linkage projection - `copy "slwsinv2.cob" replacing Invoice-Record by
# WS-Invoice-Record` [common/acas016.cbl:L218-L221]
# ---------------------------------------------------------------------------
#
# ⭐⭐ WHY THIS EXISTS AT ALL.  The handler's linkage record and its callers'
# record areas are THE SAME 137 BYTES DECLARED TWICE, under two prefixes:
#
#   * the handler copies `slwsinv2.cob` with a renaming clause
#     [common/acas016.cbl:L218-L221], so its parameter is `Invoice-Record` /
#     `Invoice-Header` / `Invoice-Line` - the `ih-` and `il-` names;
#   * the bridge copies `slwsinv.cob`, whose `SInvoice-Header` and
#     `SInvoice-Bodies` are the identical layout under the `sih-` and `sil-`
#     names, which is what :class:`InvoiceBuffer` models because the bridge is
#     the layer that touches the columns.
#
# Field for field the two are the same declarations: `pic 9(8)` + `pic 99` key,
# `pic x(6)` + `pic 9` customer, `binary-long` date, `pic x(10)` order with its
# four-item overlay, `pic 9` type, `pic x(10)` ref, `pic x(32)` description,
# eight `pic s9(7)v99 comp-3` money fields, six `pic x` status bytes, two
# `binary-char` counts, two `pic 999v99 comp` deductions, `binary-char` days,
# `binary-long` cr, and two `pic x` flags - compare [copybooks/slwsinv.cob:L18-L71]
# with [copybooks/slwsinv2.cob:L38-L89] and [:L91-L107].  So the projection below
# is a RENAME, and nothing else: no width is changed, no value is coerced,
# rounded, truncated or padded, and no field is added or dropped.  In COBOL the
# rename costs nothing because `COPY ... REPLACING` does it at compile time;
# Python has no such facility, so it is spelled out once, here, in the module
# that owns both shapes.
#
# ⭐ WHERE IT IS CALLED FROM.  `dal/facade.py`'s `acas016` dispatch paragraph,
# because that is the layer the Agent Action Plan section 0.4.3 makes responsible
# for handing a handler the parameter shape its `PROCEDURE DIVISION USING`
# declares - and the facade may not import a records module, so the conversion
# cannot live there.  A caller that already holds an :class:`InvoiceBuffer`
# passes straight through untouched.


def _projected_record_views(record: object) -> tuple[object, object] | None:
    """Return ``(header, line)`` if ``record`` is a caller's own record area.

    The area is recognised STRUCTURALLY, by the four names the copybook gives it -
    ``Invoice-Nos``, ``Item-Nos`` and the two redefining views - because the
    callers are ``programs/*`` modules this layer may not import. ``None`` means
    the object is not a caller area, and the only other thing it can be is an
    :class:`InvoiceBuffer`.
    """
    if isinstance(record, InvoiceBuffer):
        return None
    for attribute in ("invoice_nos", "item_nos", "invoice_header", "invoice_line"):
        if not hasattr(record, attribute):
            return None
    return getattr(record, "invoice_header"), getattr(record, "invoice_line")


def linkage_buffer_for(record: object) -> InvoiceBuffer:
    """Adopt the caller's record area as this handler's ``WS-Invoice-Record``.

    Returns the :class:`InvoiceBuffer` the handler is entered with, having first
    copied the caller's area into it - the ``ih-``/``il-`` names into the
    ``sih-``/``sil-`` names of the same 137 bytes, plus the shared ten-byte key.

    ⭐ THE BUFFER IS THE SAME ONE ON EVERY CALL for a given record area, and it
    has to be.  ``slinvoiceMT``'s Working-Storage survives between ``CALL``s -
    the cursor flags [common/slinvoiceMT.cbl:L331-L336], ``WS-Last-Read-Invoice``
    / ``WS-Last-Read-Line`` [:L285-L287] and ``WS-Actual-Lines-In-Row`` [:L288]
    are all written by one call and read by the next, which is the entire
    mechanism of the two-table walk at ``ba041-Reread`` [:L722-L741] - and the
    connection the C interface holds outlives a call for the same reason
    (anomaly A-8).  Both live on the buffer, so a fresh buffer per verb would
    reset the cursor on every read and the walk could never advance.

    ⭐ KEYED BY THE CALLER'S AREA, NOT MODULE-WIDE, which is what keeps two runs
    in one interpreter independent as section 0.6.6 requires: a run builds its
    own record area, so it gets its own buffer, and nothing a previous run left
    behind is visible to it.  The area is held by reference in the registry so
    that its identity cannot be recycled underneath the key while the run is
    live.

    Args:
        record: The second operand of the ``CALL`` - either a caller's record
            area or an :class:`InvoiceBuffer` the caller manages itself.

    Returns:
        The buffer to pass to :func:`dispatch`.
    """
    if isinstance(record, InvoiceBuffer):
        return record
    views = _projected_record_views(record)
    if views is None:
        raise TypeError(
            "acas016 takes WS-Invoice-Record [common/acas016.cbl:L218-L221] - "
            "either an InvoiceBuffer or a record area exposing invoice_nos, "
            f"item_nos, invoice_header and invoice_line; got {type(record).__name__}"
        )
    identity = id(record)
    held = _LINKAGE_BUFFERS.get(identity)
    if held is None or held[0] is not record:
        held = (record, InvoiceBuffer())
        _LINKAGE_BUFFERS[identity] = held
    buffer = held[1]
    _load_buffer_from_record(record, buffer)
    return buffer


def publish_linkage_buffer(buffer: InvoiceBuffer, record: object) -> None:
    """Copy the buffer back over the caller's record area, after the ``CALL``.

    ``File-Access`` is not the only thing a COBOL ``CALL`` passes by reference -
    the record area is passed the same way, so whatever the handler and the
    bridge left in ``WS-Invoice-Record`` is what the caller reads next.  A read
    verb loads it, ``INITIALIZE`` clears it, and a write verb leaves it alone;
    all three are reproduced by copying the buffer's state back out.

    BOTH VIEWS ARE PUBLISHED, because in COBOL both always hold data - they are
    one storage seen twice.  The shared ten bytes are taken from the buffer's own
    key, which the bridge keeps pointing at whichever record it last handled:
    ``move WS-Invoice-Line to WS-Invoice-Record`` [common/slinvoiceMT.cbl:L2842]
    is what puts a LINE's number into those bytes after a line read, and it is
    how a caller tells a header from a line - ``if ih-test = zero``
    [sales/sl055.cbl:L370].

    The caller's view objects are mutated IN PLACE rather than replaced, because
    a caller may hold a direct reference to one and the COBOL never gives it a
    new area.

    Args:
        buffer: The buffer :func:`dispatch` was given.
        record: The caller's record area, mutated in place. An
            :class:`InvoiceBuffer` is its own area and is left alone.
    """
    if isinstance(record, InvoiceBuffer):
        return
    if _projected_record_views(record) is None:
        return
    _store_record_from_buffer(buffer, record)


#: The buffer each caller record area is walked through, keyed by the area's
#: identity and holding the area itself so the key stays valid. Not a cache of
#: anything computed: it is `slinvoiceMT`'s Working-Storage, which the COBOL keeps
#: alive between `CALL`s for exactly as long as the module stays resident.
_LINKAGE_BUFFERS: Final[dict[int, tuple[object, InvoiceBuffer]]] = {}


def _load_buffer_from_record(record: object, buffer: InvoiceBuffer) -> None:
    """The `ih-`/`il-` area into the `sih-`/`sil-` buffer - a rename, field for field.

    ⭐ THE SHARED TEN BYTES ARE RECONCILED FIRST, AND ONCE. `Invoice-Key`
    [copybooks/slwsinv2.cob:L28-L30] and the two views' own key fields
    [:L40-L41], [:L92-L93] are ONE storage read three ways, so they cannot
    disagree in the compiled program - and a caller writes whichever name suits
    it: `sl055` positions its `Invoice-Start` by writing the GENERIC view,
    `move ws-invoice-nos to invoice-nos` [sales/sl055.cbl:L473-L474], while a
    caller that builds a header for a write fills the header view instead. The
    generic view therefore wins where it is set, and the typed view is adopted
    when the generic one is still at its `INITIALIZE` zero - the same
    "whichever is non-default" reconciliation `acas007`'s
    `synchronise_batch_key_views` applies to `WS-Batch-Key`/`WS-Batch-Key9`,
    and for the same reason: with one storage there is nothing else to go on.
    """
    header_view = getattr(record, "invoice_header")
    generic_invoice = int(getattr(record, "invoice_nos"))
    generic_test = int(getattr(record, "item_nos"))
    if header_view is not None and not generic_invoice and not generic_test:
        generic_invoice = int(header_view.ih_prime.ih_invoice)
        generic_test = int(header_view.ih_prime.ih_test)
    buffer.ws_sih_invoice = generic_invoice
    buffer.ws_sih_test = generic_test
    if header_view is not None:
        target = buffer.select_header()
        source_prime = header_view.ih_prime
        target_prime = target.sih_prime
        target_prime.sih_customer.sih_nos = source_prime.ih_customer.ih_nos
        target_prime.sih_customer.sih_check = source_prime.ih_customer.ih_check
        target_prime.sih_date = source_prime.ih_date
        target_prime.sih_order = source_prime.ih_order
        # `filler redefines sih-order` [copybooks/slwsinv.cob:L28] against
        # `filler redefines ih-order` [copybooks/slwsinv2.cob:L47] - the same
        # overlay, carried across so a stale one cannot survive a projection.
        source_overlay = source_prime.filler_47
        target_overlay = target_prime.filler_28
        target_overlay.sih_freq = source_overlay.ih_freq
        target_overlay.sih_repeat = source_overlay.ih_repeat
        target_overlay.filler_37 = source_overlay.filler_56
        target_overlay.sih_last_date = source_overlay.ih_last_date
        target_prime.sih_type = source_prime.ih_type
        target_prime.sih_ref = source_prime.ih_ref
        source_sub = header_view.ih_sub_prime
        target_sub = target.sih_sub_prime
        target_sub.sih_description = source_sub.ih_description
        source_fig = source_sub.ih_fig
        target_fig = target_sub.sih_fig
        target_fig.sih_p_c = source_fig.ih_p_c
        target_fig.sih_net = source_fig.ih_net
        target_fig.sih_extra = source_fig.ih_extra
        target_fig.sih_carriage = source_fig.ih_carriage
        target_fig.sih_vat = source_fig.ih_vat
        target_fig.sih_discount = source_fig.ih_discount
        target_fig.sih_e_vat = source_fig.ih_e_vat
        target_fig.sih_c_vat = source_fig.ih_c_vat
        target_sub.sih_status = source_sub.ih_status
        target_sub.sih_status_p = source_sub.ih_status_p
        target_sub.sih_status_l = source_sub.ih_status_l
        target_sub.sih_status_c = source_sub.ih_status_c
        target_sub.sih_status_a = source_sub.ih_status_a
        target_sub.sih_status_i = source_sub.ih_status_i
        target_sub.sih_lines = source_sub.ih_lines
        target_sub.sih_deduct_days = source_sub.ih_deduct_days
        target_sub.sih_deduct_amt = source_sub.ih_deduct_amt
        target_sub.sih_deduct_vat = source_sub.ih_deduct_vat
        target_sub.sih_days = source_sub.ih_days
        target_sub.sih_cr = source_sub.ih_cr
        target_sub.sih_day_book_flag = source_sub.ih_day_book_flag
        target_sub.sih_update = source_sub.ih_update
    line_view = getattr(record, "invoice_line")
    if line_view is not None:
        line = buffer.select_line()
        line.sil_product = line_view.il_product
        line.sil_pa = line_view.il_pa
        line.sil_qty = line_view.il_qty
        line.sil_type = line_view.il_type
        line.sil_description = line_view.il_description
        line.sil_net = line_view.il_net
        line.sil_unit = line_view.il_unit
        line.sil_discount = line_view.il_discount
        line.sil_vat = line_view.il_vat
        line.sil_vat_code = line_view.il_vat_code
        line.sil_update = line_view.il_update
        line.sil_back_ordered = line_view.il_back_ordered
    # The reconciled ten bytes into whichever views are present - the REDEFINES,
    # made explicit exactly as `InvoiceBuffer` documents.
    buffer.sync_key_into_views()


def _new_caller_header_view() -> IhInvoiceHeader:
    """``01 Invoice-Header redefines Invoice-Record.`` [copybooks/slwsinv2.cob:L38].

    The caller's own view of the shared area, at its ``INITIALIZE`` values.
    Needed because a Python record area can hold ``None`` where COBOL storage
    always exists: a caller that has performed no read yet has no view object,
    and after a read the compiled program leaves it reading real bytes. One is
    therefore materialised at the moment the buffer has something to publish -
    the same reason :meth:`InvoiceBuffer.select_header` materialises the other
    side.
    """
    return IhInvoiceHeader(
        ih_prime=IhPrime(
            ih_invoice=0,
            ih_test=0,
            ih_customer=IhCustomer(ih_nos=" " * 6, ih_check=0),
            ih_date=0,
            ih_order=" " * 10,
            filler_47=IhOrderView(
                ih_freq=" ", ih_repeat=0, filler_56=" " * 3, ih_last_date=0
            ),
            ih_type=0,
            ih_ref=" " * 10,
        ),
        ih_sub_prime=IhSubPrime(
            ih_description=" " * 32,
            ih_fig=IhFig(
                ih_p_c=Decimal("0.00"),
                ih_net=Decimal("0.00"),
                ih_extra=Decimal("0.00"),
                ih_carriage=Decimal("0.00"),
                ih_vat=Decimal("0.00"),
                ih_discount=Decimal("0.00"),
                ih_e_vat=Decimal("0.00"),
                ih_c_vat=Decimal("0.00"),
            ),
            ih_status=" ",
            ih_status_p=" ",
            ih_status_l=" ",
            ih_status_c=" ",
            ih_status_a=" ",
            ih_status_i=" ",
            ih_lines=0,
            ih_deduct_days=0,
            ih_deduct_amt=Decimal("0.00"),
            ih_deduct_vat=Decimal("0.00"),
            ih_days=0,
            ih_cr=0,
            ih_day_book_flag=" ",
            ih_update=" ",
        ),
    )


def _new_caller_line_view() -> IlInvoiceLine:
    """``01 Invoice-Line redefines Invoice-Record.`` [copybooks/slwsinv2.cob:L91].

    The line counterpart of :func:`_new_caller_header_view`, at its
    ``INITIALIZE`` values.
    """
    return IlInvoiceLine(
        il_invoice=0,
        il_line=0,
        il_product=" " * 13,
        il_pa=" " * 2,
        il_qty=0,
        il_type=" ",
        il_description=" " * 32,
        il_net=Decimal("0.00"),
        il_unit=Decimal("0.00"),
        il_discount=Decimal("0.00"),
        il_vat=Decimal("0.00"),
        il_vat_code=0,
        il_update=" ",
        il_back_ordered=" ",
    )


def _store_record_from_buffer(buffer: InvoiceBuffer, record: object) -> None:
    """The `sih-`/`sil-` buffer back into the `ih-`/`il-` area - the same rename."""
    setattr(record, "invoice_nos", buffer.ws_sih_invoice)
    setattr(record, "item_nos", buffer.ws_sih_test)
    header_view = getattr(record, "invoice_header")
    source = buffer.ws_invoice_record
    if header_view is None and source is not None:
        # COBOL storage always exists, so a caller that arrived with no view
        # object gets one rather than an exception. See
        # `_new_caller_header_view`.
        header_view = _new_caller_header_view()
        setattr(record, "invoice_header", header_view)
    if header_view is not None and source is not None:
        source_prime = source.sih_prime
        target_prime = header_view.ih_prime
        # The ten shared bytes read through the header view's own names.
        target_prime.ih_invoice = buffer.ws_sih_invoice
        target_prime.ih_test = buffer.ws_sih_test
        target_prime.ih_customer.ih_nos = source_prime.sih_customer.sih_nos
        target_prime.ih_customer.ih_check = source_prime.sih_customer.sih_check
        target_prime.ih_date = source_prime.sih_date
        target_prime.ih_order = source_prime.sih_order
        source_overlay = source_prime.filler_28
        target_overlay = target_prime.filler_47
        target_overlay.ih_freq = source_overlay.sih_freq
        target_overlay.ih_repeat = source_overlay.sih_repeat
        target_overlay.filler_56 = source_overlay.filler_37
        target_overlay.ih_last_date = source_overlay.sih_last_date
        target_prime.ih_type = source_prime.sih_type
        target_prime.ih_ref = source_prime.sih_ref
        source_sub = source.sih_sub_prime
        target_sub = header_view.ih_sub_prime
        target_sub.ih_description = source_sub.sih_description
        source_fig = source_sub.sih_fig
        target_fig = target_sub.ih_fig
        target_fig.ih_p_c = source_fig.sih_p_c
        target_fig.ih_net = source_fig.sih_net
        target_fig.ih_extra = source_fig.sih_extra
        target_fig.ih_carriage = source_fig.sih_carriage
        target_fig.ih_vat = source_fig.sih_vat
        target_fig.ih_discount = source_fig.sih_discount
        target_fig.ih_e_vat = source_fig.sih_e_vat
        target_fig.ih_c_vat = source_fig.sih_c_vat
        target_sub.ih_status = source_sub.sih_status
        target_sub.ih_status_p = source_sub.sih_status_p
        target_sub.ih_status_l = source_sub.sih_status_l
        target_sub.ih_status_c = source_sub.sih_status_c
        target_sub.ih_status_a = source_sub.sih_status_a
        target_sub.ih_status_i = source_sub.sih_status_i
        target_sub.ih_lines = source_sub.sih_lines
        target_sub.ih_deduct_days = source_sub.sih_deduct_days
        target_sub.ih_deduct_amt = source_sub.sih_deduct_amt
        target_sub.ih_deduct_vat = source_sub.sih_deduct_vat
        target_sub.ih_days = source_sub.sih_days
        target_sub.ih_cr = source_sub.sih_cr
        target_sub.ih_day_book_flag = source_sub.sih_day_book_flag
        target_sub.ih_update = source_sub.sih_update
    line_view = getattr(record, "invoice_line")
    line = buffer.invoice_line
    if line_view is None and line is not None:
        line_view = _new_caller_line_view()
        setattr(record, "invoice_line", line_view)
    if line_view is not None and line is not None:
        line_view.il_invoice = buffer.ws_sih_invoice
        line_view.il_line = buffer.ws_sih_test
        line_view.il_product = line.sil_product
        line_view.il_pa = line.sil_pa
        line_view.il_qty = line.sil_qty
        line_view.il_type = line.sil_type
        line_view.il_description = line.sil_description
        line_view.il_net = line.sil_net
        line_view.il_unit = line.sil_unit
        line_view.il_discount = line.sil_discount
        line_view.il_vat = line.sil_vat
        line_view.il_vat_code = line.sil_vat_code
        line_view.il_update = line.sil_update
        line_view.il_back_ordered = line.sil_back_ordered


def _fs_cobol_files_used(flat_statuses: object) -> bool:
    """``88  FS-Cobol-Files-Used  value zero.`` [copybooks/wssystem.cob:L113]

    The single condition name that chooses between the ISAM path and the RDB path.
    ``File-System-Used`` zero means COBOL files; anything else means an RDBMS, which
    is why the branch at [common/acas016.cbl:L271] is written in the NEGATIVE -
    ``if not FS-Cobol-Files-Used``.

    Read through :mod:`acas_posting.records.system_record`'s own
    ``RDBMS-Flat-Statuses`` group rather than re-deriving the rule, and defensively
    resolved so a caller that supplies a bare stand-in for the group still gets the
    RDB path - which is the path this module implements.
    """
    file_system_used = getattr(flat_statuses, "file_system_used", None)
    if file_system_used is None:
        return False
    return int(file_system_used) == 0
