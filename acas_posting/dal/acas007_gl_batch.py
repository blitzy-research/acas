r"""COBOL file handler ``acas007`` and its bridge ``glbatchMT`` over ``GLBATCH-REC``.

WHAT THIS MODULE OWNS
=====================
This module owns EVERY statement issued against the batch-control table, and
nothing else. It is the Python reimplementation of two frozen COBOL programs
taken together:

* ``common/acas007.cbl`` - the file handler the posting programs ``CALL``. It
  decides whether a request goes to the indexed file or to the relational
  store, guards the key number for three of the eight verbs, and hands the
  relational requests on.
* ``common/glbatchMT.cbl`` - the generated bridge the handler calls, which owns
  the host-variable group, the ``WHERE`` construction and the literal SQL.

Agent Action Plan section 0.4.1.5, verbatim table row::

    | `acas_posting/dal/acas007_gl_batch.py` | CREATE |
      `common/acas007.cbl` + `common/glbatchMT.cbl` | `GLBATCH-REC` |

THE SPINE
=========
Agent Action Plan section 0.2.1.1 fixes the whole chain, one row per hop::

    entity facade  GL-Batch          [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]
    handler        acas007           [common/acas007.cbl]
    bridge         glbatchMT         [common/glbatchMT.cbl] [common/glbatchMT.scb]
    table          GLBATCH-REC       [mysql/ACASDB.sql:L80-L103] 21 cols, PK BATCH-KEY
    record         WS-Batch-Record   [copybooks/wsbatch.cob:L13-L54]
    record class   GlBatchRecord     acas_posting/records/gl_batch.py

WHY ONE MODULE PER HANDLER AND NOT ONE PER TABLE
================================================
Agent Action Plan section 0.3.1, verbatim:

    "**One data-access module per handler, not per table.** ... Mirroring the
    handler boundary rather than the table boundary keeps the Python module set
    in exact correspondence with the COBOL programs that the traceability
    document must map, and **preserves the dispatch semantics rather than
    flattening them**."

``acas007`` happens to serve exactly one table, so nothing is flattened here -
but the boundary is still the handler's, which is why this module carries both
the handler's paragraphs and the bridge's rather than only the SQL.

WHY THIS TABLE IS LOAD-BEARING
==============================
``gl051``'s control-total gate, ``gl070``'s two batch passes and ``gl072``'s
batch stamping all reach the database through here. Agent Action Plan section
0.1.1 Goal 3, verbatim: "**Reproduce control-total semantics.** The
batch-control gate must accept and reject exactly the batches the COBOL accepts
and rejects." This module therefore carries the values faithfully and adds no
judgement of its own - the gate itself lives in
``acas_posting/programs/gl051_batch_control_check.py``, never here.

THE TWO PUBLISHED SIGNATURES
============================
The handler's linkage, verbatim from [common/acas007.cbl:L265-L271]::

    Procedure Division Using System-Record
                             WS-Batch-Record
                             File-Access
                             File-Defs
                             ACAS-DAL-Common-data.

and its caller, the facade dispatch exemplar, verbatim from
[copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]::

    acas007.
        move     1  to File-Key-No.
        call     "acas007" using System-Record
                                 WS-Batch-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-Data.

Agent Action Plan section 0.4.3 names the Python form of that ``CALL``
verbatim, and :func:`dispatch` is exactly it::

    FROM:  call "acas007" using System-Record WS-Batch-Record File-Access
                                File-Defs ACAS-DAL-Common-Data
    TO:    acas007_gl_batch.dispatch(system, batch, file_access, file_defs,
                                     dal_common)

The bridge's own ``CALL`` takes THREE parameters and ``File-Access`` comes
FIRST, verbatim from [common/acas007.cbl:L640-L645]::

    ba020-Process-DAL.
        call     "glbatchMT" using File-Access
                                     ACAS-DAL-Common-data

                                     WS-Batch-Record
        end-call.

so :func:`glbatch_mt` takes ``(file_access, dal_common, batch)`` in that order.
Both signatures are published because rule R-5 requires that a reader following
either the entity-named or the handler-named convention find a correspondingly
named function over ONE implementation.

THE EIGHT VERBS AND THE DISPATCH ORDER
======================================
[common/acas007.cbl:L338-L357] dispatches in this ``when`` order, and the order
is preserved because rule R-6 makes the compiled statement order the
specification::

    when 1 -> aa020-Process-Open           when 5 -> aa070-Process-Write
    when 2 -> aa030-Process-Close          when 7 -> aa090-Process-Rewrite
    when 3 -> aa040-Process-Read-Next      when 8 -> aa080-Process-Delete
    when 4 -> aa050-Process-Read-Indexed   when 9 -> aa060-Process-Start
    when other                             -> aa100-Bad-Function  *> 6 is unused

RE-WRITE (7) PRECEDES DELETE (8) in the source, which is why
:data:`DISPATCH_ORDER` reads ``1, 2, 3, 4, 5, 7, 8, 9``. There is NO
``when 6``: ``fn-Delete-All`` is set internally by the handler and never
travels through this ``evaluate`` - see ANOMALY N18b below. And
[common/acas007.cbl:L360] repeats the bad-function transfer unconditionally
immediately after the ``end-evaluate``, so :func:`aa100_bad_function` is
reachable by two routes, not one.

The bridge's own dispatch [common/glbatchMT.cbl:L371-L395] DOES carry a
``when 6``, going to ``ba085-Process-DELETE-ALL``, which is the only way that
paragraph is ever reached.

THE KEY GUARD - THREE VERBS, TWO CODES, AND NOT THE SAME SET AS acas000
=======================================================================
[common/acas007.cbl:L285-L299] tests ``File-Key-No not = 1`` for exactly three
functions and returns two different ``We-Error`` values::

    when 4  *> fn-read-indexed  -> 998 / FS-Reply 99 -> aa999-main-exit
    when 9  *> fn-start         -> 998 / FS-Reply 99 -> aa999-main-exit
    when 8  *> fn-delete        -> 996 / FS-Reply 99 -> aa999-main-exit

WRITE (5) AND RE-WRITE (7) ARE NOT GUARDED HERE, and ``acas000`` guards a
DIFFERENT set - 4, 5 and 7. ANOMALY N-guard: the two sets are not harmonised,
because harmonising them would change which requests this handler refuses.

THE DRIFT TABLE - COPYBOOK, HOST VARIABLE, COLUMN
=================================================
Every conversion below is read from ``loader.drift_for(...)`` at import rather
than transcribed, per the Agent Action Plan section 0.8.1 directive "**Data
dictionary first.** ... every Python field definition cites its entry. **This
ordering is a directive, not a preference** - it is what prevents fields being
transcribed by eye." The table is reproduced here so a reader can check the
generated data against the frozen sources without leaving the file::

    #  copybook field   pic          -> host variable    pic         -> column
    -- ---------------- ------------    ---------------- -----------    -----------------------
     1 WS-Batch-Key9    9(6) REDEF   -> HV-BATCH-KEY     9(08) COMP -> mediumint(6) unsigned PK
     2 Items            99           -> HV-ITEMS         9(03) COMP -> tinyint(2)   unsigned
     3 Batch-Status     9            -> HV-BATCH-STATUS  9(03) COMP -> tinyint(1)   unsigned
     4 Cleared-Status   9            -> HV-CLEARED-STAT. 9(03) COMP -> tinyint(1)   unsigned
     5 Bcycle           99           -> HV-BCYCLE        9(03) COMP -> tinyint(2)   unsigned
     6 Entered          binary-long  -> HV-ENTERED       9(10) COMP -> int(8)       unsigned  (*)
     7 Proofed          binary-long  -> HV-PROOFED       9(10) COMP -> int(8)       unsigned  (*)
     8 Posted           binary-long  -> HV-POSTED        9(10) COMP -> int(8)       unsigned  (*)
     9 Stored           binary-long  -> HV-STORED        9(10) COMP -> int(8)       unsigned  (*)
    10 Input-Gross      9(9)v99 C-3  -> HV-INPUT-GROSS   9(12)V9(02)-> decimal(14,2) unsigned (+)
    11 Input-Vat        9(9)v99 C-3  -> HV-INPUT-VAT     9(12)V9(02)-> decimal(14,2) unsigned (+)
    12 Actual-Gross     9(9)v99 C-3  -> HV-ACTUAL-GROSS  9(12)V9(02)-> decimal(14,2) unsigned (+)
    13 Actual-Vat       9(9)v99 C-3  -> HV-ACTUAL-VAT    9(12)V9(02)-> decimal(14,2) unsigned (+)
    14 Description      x(24)        -> HV-DESCRIPTION   X(24)      -> char(24)                clean
    15 bDefault         99           -> HV-BDEFAULT      9(03) COMP -> tinyint(2)   unsigned  (#)
    16 Convention       xx           -> HV-CONVENTION    X(2)       -> char(2)                 clean
    17 Batch-Def-AC     9(6)         -> HV-BATCH-DEF-AC  9(08) COMP -> mediumint(6) unsigned
    18 Batch-Def-PC     99           -> HV-BATCH-DEF-PC  9(03) COMP -> tinyint(2)   unsigned
    19 Batch-Def-Code   xx           -> HV-BATCH-DEF-CODE X(2)      -> char(2)                 clean
    20 Batch-Def-Vat    x            -> HV-BATCH-DEF-VAT X(1)       -> char(1)                 clean
    21 Batch-Start      9(5)         -> HV-BATCH-START   9(08) COMP -> mediumint(5) unsigned

    (*) THE SIGN IS LOST AT THE BRIDGE. See ANOMALY A-11 below.
    (+) Widened by three digits at the bridge and left widened at the column,
        11 -> 14 -> 14. See ANOMALY N-widen below.
    (#) A camelCase copybook name flattened to upper case at both the host
        variable [common/glbatchMT.cbl:L296] and the column
        [mysql/ACASDB.sql:L95]. See ANOMALY N-name below.

Only four of the twenty-one rows are clean, so Agent Action Plan section 0.6.2
is right that the drift is "specific rather than systemic" and must be handled
field by field from the dictionary rather than by one blanket rule.

FIELDS WITH NO HOST VARIABLE AND NO COLUMN - DELIBERATE OMISSIONS
=================================================================
Rule R-5, verbatim: "Deliberate omissions are recorded as omissions." Five
items of ``WS-Batch-Record`` reach neither the host-variable group nor the
table, and each is recorded in :data:`OMISSIONS`:

* ``WS-Ledger`` pic 9 [copybooks/wsbatch.cob:L15] and ``WS-Batch-Nos`` pic
  9(5) [:L19] survive ONLY inside the concatenated ``BATCH-KEY``, reachable
  through the ``WS-Batch-Key9`` redefinition [:L20-L21]. They are the same six
  bytes, so nothing is lost - but nothing carries their names either.
* the three group items ``Dates`` [:L35], ``Amounts`` [:L40] and
  ``posting-data`` [:L47] are groups, correctly not columns. ``Amounts``
  matters anyway: it is where ``comp-3`` is DECLARED, and its four elementary
  items inherit packed usage from it rather than declaring their own.

THE NINE 88-LEVEL CONDITION NAMES ARE NOT THIS MODULE'S BUSINESS
================================================================
``GL-Batch``, ``PL-Batch``, ``SL-Batch`` [copybooks/wsbatch.cob:L16-L18],
``Status-Open``, ``Status-Closed`` [:L26-L27] and ``Waiting``, ``Processed``,
``Archived`` [:L30-L32] are predicates over the record and belong to
``acas_posting/records/gl_batch.py``. They are neither re-declared nor imported
here, and ``acas_posting.cobol`` is not imported at all, because the Agent
Action Plan section 0.4.3 per-directory import table permits a ``dal`` module
to reach ``dal.connection``, ``dal.status``, ``dal.cursor_state`` and one
``records`` module - and forbids ``dal`` -> ``cobol``. Where this module must
test a condition name of its own linkage blocks - ``FS-Cobol-Files-Used``,
``fn-Open``, ``fn-Output``, ``Testing-1`` - it tests the underlying integer and
names the condition and its locator in a comment at the test.

THE START SEMANTICS, IN THE BRIDGE'S OWN WORDS
=============================================
[common/glbatchMT.scb:L644-L650] is the clearest statement of the positioning
contract anywhere in the checkout, and it is quoted here for that reason,
verbatim::

    move     spaces to WS-Where
    string   "`"                   delimited by size
             KeyName (KOR-x1)      delimited by space
             "`"                   delimited by size
             MOST-relation         delimited by space
             '"'                   delimited by size
             WS-Batch-Record (K:L)       delimited by size

Four things follow, and ``acas_posting/dal/cursor_state.py`` implements all
four:

1. The comparison identifier is BACKTICK-QUOTED. The bridge itself proves
   identifier quoting is mandatory, which is why every identifier in this
   module goes through :func:`~acas_posting.dal.connection.quote_identifier`.
2. The relation is TRIMMED - ``delimited by space`` - so the padded ``">= "``
   reaches the statement as ``>=``.
3. The key value is a RAW CHARACTER SUBSTRING of the record buffer,
   ``WS-Batch-Record (K:L)``, i.e. offset 1 length 6, and it is double-quoted
   rather than bound as a typed field. For this record those six characters are
   ``WS-Ledger`` (one digit) followed by ``WS-Batch-Nos`` (five digits).
4. There is no ``when other`` and no fallback, so an ``Access-Type`` outside
   5..9 leaves ``MOST-Relation`` as spaces - see ANOMALY N-relation-nodefault.

The key metadata itself, verbatim from [common/glbatchMT.scb:L231-L241]::

    01  Table-Of-Keynames.
        03  filler          pic x(30) value "BATCH-KEY                     ".
        03  filler          pic x(8)  value "00010006". *> offset/length in ws rec
        03  filler          pic xxx   value "STR".      *> key is string

    01  filler redefines table-of-keynames.
        03  keyOfReference occurs 1    indexed by KOR-x1.
            05 KeyName      pic x(30).
            05 KOR-Offset   pic 9(4).
            05 KOR-Length   pic 9(4).
            05 KOR-Type     pic XXX.                    *> Not used currently

One key of reference, ``BATCH-KEY``, offset 0001, length 0006, type ``STR``.
The table declaration is at [common/glbatchMT.scb:L273-L275]::

    *> /MYSQL VAR\
    *>       BASE=ACASDB
    *>       TABLE=GLBATCH-REC,HV

VALUES ARE BOUND, NOT INTERPOLATED - AND WHY THAT IS STILL FAITHFUL
===================================================================
The bridge renders every value as a DOUBLE-QUOTED STRING sliced out of one
edited field, ``WS-MYSQL-EDIT PIC -Z(18)9.9(9)``
[common/glbatchMT.cbl:L1150-L1160] and its twenty siblings. This module
reproduces the VALUE that rendering produces - the same truncation, the same
sign loss, the same trailing-space trim - and then hands it to the driver as a
bound parameter through
:func:`~acas_posting.dal.connection.execute_statement` instead of pasting it
into the statement text. The values that reach MySQL are identical; only the
transport differs, and the transport is not observable in a table dump. The
alternative - pasting rendered text - would reproduce nothing extra and would
introduce an injection surface the COBOL only avoids because its inputs are
fixed-width numerics.

The rendering rule is DERIVED, not transcribed. ``WS-MYSQL-EDIT`` is thirty
characters: position 1 is the sign, 2..20 are nineteen integer positions,
21 is the decimal point and 22..30 are nine fraction digits. An integer field
of ``n`` digits therefore right-aligns at position 20 and its slice starts at
``21 - n``. That single rule reproduces all seventeen numeric slices the
bridge writes, checked against every one of them::

    9(08) -> (13:08)   9(03) -> (18:03)   9(10) -> (11:10)
    9(12)V9(02) -> (09:12) then "." then (22:02) UNTRIMMED

POSITION 1 - THE SIGN - IS NEVER PART OF ANY SLICE, which is a second and
entirely independent route by which a negative value loses its sign on the way
to this table.

ANOMALIES REPRODUCED HERE, NEVER FIXED
======================================
Rule R-4 and Agent Action Plan section 0.8.2, verbatim: "There is no test
suite: compiled COBOL execution is the behavioral specification, defects
included. **A defect reproduced is correct; a defect fixed is a failure.**"
Every entry below is reproduced with a comment citing its locator at the
reproduction site, per Agent Action Plan section 0.7.4 C-4, and every one is
also registered in :data:`ANOMALIES` and in
``docs/migration/anomaly-log.md`` naming this module.

A-11  SIGN LOSS AT THE BRIDGE on all four date fields. ``Entered``,
      ``Proofed``, ``Posted`` and ``Stored`` are ``binary-long`` and therefore
      SIGNED [copybooks/wsbatch.cob:L36-L39]; the host variables are
      ``PIC 9(10) COMP`` and therefore UNSIGNED
      [common/glbatchMT.cbl:L287-L290]; the columns are ``int(8) unsigned``
      [mysql/ACASDB.sql:L86-L89]. The loss happens at
      :func:`bb000_hv_load`, BEFORE any statement is built. The RESULTING value
      was ambiguity Q-3 and is now measured - see below; the LOSS is the defect
      and stays here.
A-15  THE RECORD LENGTH CONTRADICTS THE FIELD SUM, in the maintainer's own
      words [copybooks/wsbatch.cob:L7-L9]. It matters here because
      ``ba012-Test-WS-Rec-Size-2`` [common/acas007.cbl:L579-L591] compares
      exactly those two lengths. See AMBIGUITY Q-4. Nothing is resolved.
N-widen   The four control totals are widened from eleven digits to fourteen
      at the host variable and stay widened at the column. In-range values are
      unaffected; the drift is recorded so traceability carries it.
N18b  ONE Open-plus-Output REQUEST CALLS THE BRIDGE TWICE. See the dedicated
      section below.
N-relation-nodefault  [common/glbatchMT.scb:L631-L642] has no ``when other``,
      so an ``Access-Type`` outside 5..9 leaves ``MOST-Relation`` as spaces and
      produces a malformed predicate. No default is added. In this bridge the
      spaces outcome is additionally unreachable - see N-start-dead-arm.
N-initialize  TWO INITIALISATION SEMANTICS IN ONE BRIDGE.
      ``initialize WS-Batch-Record with filler`` at
      [common/glbatchMT.cbl:L589] blanks ``FILLER`` items too; the plain
      ``initialize WS-Batch-Record.`` at [:L1106] does not. Each is reproduced
      at its own site and they are not normalised.
N-log The log file number is set to 13 on the indexed path
      [common/acas007.cbl:L281] and OVERWRITTEN to 23 on the relational path
      [:L577], where the maintainer also spells the field ``WS-Log-File-no``
      rather than ``WS-Log-File-No``. The family is systematic - ``acas005``
      11 to 21, ``acas006`` 12 to 22, ``acas007`` 13 to 23, ``acas008`` 15 to
      25 - and 14 is skipped.
N-guard   The guarded function set differs per handler; see THE KEY GUARD.
N-998 ``We-Error`` 998 carries THREE documented meanings: "file seeks key type
      out of range" [common/acas007.cbl:L289], "Invalid calling parameter
      settings" [:L473], and "File-Key-No out of range" in the authoritative
      table [common/glpostingMT.cbl:L141]. All three are recorded.
N-996-comment  The comment on the 996 branch [common/acas007.cbl:L295] is a
      copy-paste of the 998 comment at [:L289] and describes the wrong
      condition.
N-name    ``bDefault`` becomes ``BDEFAULT``; see the drift table.
N-deleteall-999999  ``ba085-Process-Delete-ALL`` IS NOT A BARE DELETE. It moves
      999999 into the key [common/glbatchMT.cbl:L922] and then deletes
      ``WHERE `BATCH-KEY` < "999999"`` [:L928-L938], so A BATCH KEYED EXACTLY
      999999 SURVIVES A DELETE-ALL. Its guard is ``not > zero`` rather than
      ``not = 1`` [:L962], with the maintainer's own note "of course there
      could be no data in table" [:L974].
N-close-double-log  ``aa030-Process-Close`` performs ``aa999-main-exit``
      [common/acas007.cbl:L407], whose whole body is
      ``if Testing-1 perform Ca-Process-Logs``, and then performs
      ``Ca-Process-Logs`` UNCONDITIONALLY [:L410]. A close therefore logs
      TWICE under ``Testing-1`` and once otherwise.
N-open-nomode  AN OPEN WITH NO RECOGNISED MODE SUCCEEDS SILENTLY. If
      ``Access-Type`` is none of 1, 2, 3 or 4, all four arms of
      ``aa020-Process-Open`` fall through [common/acas007.cbl:L365-L393] without
      touching a file, and the paragraph's tail runs anyway [:L394-L398] - so the
      caller is answered with ITS OWN incoming ``FS-Reply``, upgraded to
      ``We-Error 999`` only if that happened to be non-zero, and the log key
      still reads "OPEN GL BATCH file". No diagnostic, no counter.
N-fa-statuses-skipped  ``FA-RDBMS-Flat-Statuses`` REACHES THE BRIDGE UNSET ON
      EXACTLY ONE REQUEST. The Open-plus-Output branch [common/acas007.cbl:
      L305-L312] fires BEFORE the general branch's
      ``move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses`` [:L317] and makes no
      copy of its own, so that one request carries whatever the caller left in
      [copybooks/wsfnctn.cob:L72-L83] while every other relational request
      carries the copied value.
N-901-unreachable  ``ba012-Test-WS-Rec-Size-2``'s ``A < B`` CAN NEVER BE TRUE.
      ``copybooks/fdbatch.cob:L11-L49`` declares field for field the same layout
      as ``copybooks/wsbatch.cob:L13-L54``, the only difference being a
      ``REDEFINES``, which adds no length; GnuCOBOL 3.2 measures both at 96. See
      :data:`WS_BATCH_RECORD_LENGTH` and ambiguity Q-4.
N-901-sticky  A STALE ``We-Error`` 901 BREAKS THE WHOLE RUN. The second test in
      ``ba012-Test-WS-Rec-Size-2`` is ``if WE-Error = 901``
      [common/acas007.cbl:L592] on the CALLER's field, which nothing clears -
      ``aa010-main``'s own zeroing is commented out [:L334-L335] and runs later
      anyway. So a caller arriving with a stale 901 takes the display-and-exit
      branch even though the lengths agree; it is answered with its OWN incoming
      ``FS-Reply``, because only the ``A < B`` arm writes 99; the six credential
      moves are SKIPPED [:L614-L619]; and ``A`` was assigned before the test
      [:L582-L584], so the first-call guard is closed and THE CREDENTIALS ARE
      NEVER LOADED FOR THE REST OF THE RUN.
N-start-code-divergence  The handler's own access-type guard writes
      ``We-Error`` 998 and LEAVES ``FS-Reply`` UNTOUCHED
      [common/acas007.cbl:L472-L475] - and because [:L466-L467] zeroed both a
      moment earlier, a caller testing only ``FS-Reply`` sees success. The
      bridge writes ``(99, 997)`` for the same condition
      [common/glbatchMT.cbl:L715-L720], and the handler's own header documents
      997 for it [common/acas007.cbl:L155]. Three readings, all preserved.
N-start-dead-arm  Because the bridge rejects ``access-type < 5 or > 8`` BEFORE
      the relation ``evaluate`` [common/glbatchMT.cbl:L715-L720], the
      ``when 9 -> "<= "`` arm at [common/glbatchMT.scb:L640-L641] is
      UNREACHABLE DEAD CODE. ``dal/cursor_state.py`` already reproduces the
      rejection and ``dal/status.py`` already reports
      ``start_access_type_is_valid(9)`` as false.
N-badfunction-divergence  The handler's bad-function paragraph returns
      ``(99, 999)`` [common/acas007.cbl:L548-L549]; the bridge's returns
      ``(99, 990)`` [common/glbatchMT.cbl:L1030-L1031].
N-nostatus  FOUR WRITE-SIDE PARAGRAPHS LEAVE THE STATUS UNWRITTEN WHEN THE ROW
      COUNT IS WRONG BUT THE DRIVER REPORTS NO ERROR. ``ba010-Initialise`` has
      its status zeroing COMMENTED OUT [common/glbatchMT.cbl:L351-L352], so
      the bridge never clears the caller's values at entry. ``ba080`` [:L881-
      L896] and ``ba085`` [:L962-L977] then transfer to ``ba999-End`` from
      INSIDE the count test but OUTSIDE the errno test, so deleting a row that
      is not there returns the caller's incoming status unchanged; ``ba090``
      does the same [:L1008-L1020]; and ``ba070`` differs only because it
      zeroed the status itself at [:L821], so a write that inserts no row
      reports SUCCESS.
N-hv-render  Position 1 of ``WS-MYSQL-EDIT`` is the sign and no slice includes
      it; see VALUES ARE BOUND above.
N-insert-set-syntax  The bridge writes ``INSERT INTO `GLBATCH-REC` SET ...``
      [common/glbatchMT.cbl:L1145-L1148] rather than a column list with
      ``VALUES``, and ``bb300-Update`` re-SETs ALL TWENTY-ONE COLUMNS INCLUDING
      THE PRIMARY KEY before appending its ``WHERE`` [:L1428-L1697].
N-affected-rows-int32  A FAILED DELETE-ALL REPORTS COMPLETE SUCCESS. The C shim
      declares ``void MySQL_affected_rows(int *no)`` and assigns
      ``mysql_affected_rows(mysql)`` through it, so FOUR bytes are written into
      the EIGHT-byte ``Ws-Mysql-Count-Rows binary-double unsigned``
      [copybooks/mysql-variables.cpy:L73], which
      ``MYSQL-1210-COMMAND`` performs UNCONDITIONALLY - after the error
      paragraph, not instead of it [copybooks/mysql-procedures.cpy:L178].
      ``mysql_affected_rows`` returns ``(my_ulonglong)-1`` on failure, and cobc
      3.2 lays the field out little-endian, so the field then reads
      **4294967295**. Every ``not = 1`` guard is unaffected, but
      ``ba085-Process-Delete-ALL`` guards on ``not > zero``
      [common/glbatchMT.cbl:L962] - which 4294967295 satisfies - so control
      takes the ``else`` [:L974-L977] and the paragraph reports ``(0, 0)``.
      Encoded as :data:`AFFECTED_ROWS_ON_FAILURE`.
N-countrows-shared  ``Ws-Mysql-Count-Rows`` is ONE field with TWO writers -
      ``MYSQL-1210-COMMAND`` stores an affected-row count into it
      [copybooks/mysql-procedures.cpy:L178] and ``MYSQL-1220-STORE-RESULT``
      stores a selected-row count [:L196]. So a rewrite that changed nothing, or
      a delete that matched nothing, leaves ZERO there; and the NEXT
      ``fn-read-next`` on a live cursor reaches ``ba041-Reread``'s
      ``if WS-MYSQL-Count-Rows = zero`` [common/glbatchMT.cbl:L579] and ENDS THE
      WALK. Reachable in the posting cycle, because ``gl072`` rewrites each
      batch record while walking batches [general/gl072.cbl:L373-L377].

ANOMALY N18b IN FULL - ONE REQUEST, TWO BRIDGE CALLS
====================================================
Stage 1, [common/acas007.cbl:L305-L312], verbatim - note that the two lines
which would have coerced the function are COMMENTED OUT::

    if       fn-Open and
             fn-output
        and  not FS-Cobol-Files-Used  *> RDB processing
    *>             set fn-delete-all to true
    *>             move zero to access-type
             perform ba-Process-RDBMS
             go to AA-Main-Exit
    end-if.

Stage 2, [common/acas007.cbl:L622-L631], verbatim::

    ba015-Test-Ends.

    *>  First check if there is an open output and if so open 1st then
    *>   we need to force a DELETE-ALL call to the DAL. [ Backup code ].

        if       fn-Open
           and   fn-Output
                 perform ba020-Process-Dal
                 set fn-Delete-All to true
        end-if.

``ba015-Test-Ends`` then FALLS THROUGH IN SOURCE ORDER into
``ba020-Process-DAL`` at [:L640], so the bridge is called A SECOND TIME, this
time with ``File-Function = fn-Delete-All (6)``. One ``Open`` plus ``Output``
request therefore produces two sequential bridge invocations, in this order:

    1. ``fn-Open`` / ``fn-Output``  - opens the connection
    2. ``fn-Delete-All``           - deletes every row below key 999999

:func:`ba015_test_ends` models that fall-through explicitly rather than
letting it happen implicitly, so the order is visible in the code.

THREE HANDLERS OF ONE FAMILY BEHAVE THREE DIFFERENT WAYS, and all three are
preserved rather than harmonised:

* ``acas005`` has the block COMMENTED OUT [common/acas005.cbl:L307], with the
  note "NOT used with GL."
* ``acas006`` and ``acas007`` are TWO-STAGE, as above.
* ``acas008`` COERCES - it does ``set fn-delete-all to true`` BEFORE the
  perform [common/acas008.cbl:L313-L319], so it calls the bridge once.

AMBIGUITIES SENT TO THE COMPILED ORACLE
=======================================
Rule R-6 makes observed compiled behaviour the tie-breaker. Two of the five
questions in Agent Action Plan section 0.6.8 land on this table; BOTH have now
been ARBITRATED by compiling a probe against GnuCOBOL 3.2 - the version the
maintainer's own script targets [common/comp-common.sh:L9] - and both, with a
third question raised by this module's own reading, are registered in
:data:`AMBIGUITIES` and in ``docs/migration/ambiguity-resolutions.md``:

Q-3   RESOLVED. A negative binary value through an unsigned host variable into
      an unsigned column. Agent Action Plan section 0.6.8, verbatim: "section
      0.6.2 establishes that the sign is lost; what the resulting stored value
      *is* depends on the conversion the bridge's C interface performs, which
      must be measured rather than assumed."
      MEASURED on GnuCOBOL 3.2, moving a signed ``binary-long`` declared
      verbatim from [copybooks/wsbatch.cob:L36-L39] into a ``PIC 9(10) COMP``
      declared verbatim from [common/glbatchMT.cbl:L287-L290]::

          in=-0000000005  Entered=-0000000005  HV-ENTERED=0000000005
          in=-0000000001  Entered=-0000000001  HV-ENTERED=0000000001
          in=-0000000099  Entered=-0000000099  HV-ENTERED=0000000099
          in=-0020240101  Entered=-0020240101  HV-ENTERED=0020240101
          in=+0020240101  Entered=+0020240101  HV-ENTERED=0020240101
          in=-2147483648  Entered=-2147483648  HV-ENTERED=2147483648
          in=+0000000000  Entered=+0000000000  HV-ENTERED=0000000000

      The compiler applies ABSOLUTE-VALUE semantics - the ISO ``MOVE`` reading -
      and NOT a two's-complement reinterpretation of the source bytes. That is
      exactly what :func:`signed_to_unsigned_host_variable` already implemented,
      so the measurement CONFIRMS the implementation rather than changing it.
      Keeping it ONE named helper is what made the confirmation a one-function
      check. The probe also re-confirms N-hv-render: every rendered value above
      reached ``WS-MYSQL-EDIT`` right-aligned with position 1 empty, so no sign
      ever entered a transmitted slice.
Q-3'  The sign LOSS is not resolved by the above and is not resolvable - it is
      the defect. It remains registered as A-11 and reproduced at the load site.
Q-4   The record-length contradiction. Agent Action Plan section 0.6.8,
      verbatim: "Whether the declared length or the field sum governs the
      record actually read affects field alignment for the trailing fields, and
      only execution shows which."

DELIBERATE OMISSIONS BEYOND THE FIVE UNMAPPED FIELDS
====================================================
O-1   THE INDEXED-FILE STORE ITSELF. Every ``aa0NN`` paragraph is reproduced
      here in full - its paragraph number, its log key, its status writes and
      its guards - but the physical ISAM verb inside it routes through
      :func:`_indexed_file_verb`, which raises
      :class:`FlatFileStoreNotMigratedError`. The Agent Action Plan's target
      inventory contains no indexed-file store: MySQL is the store, the harness
      seeds MySQL and the scenarios diff MySQL tables. Fabricating a store
      would invent behaviour, and silently reporting success would hide a
      mis-configured caller, so the boundary is named and raised at instead.
      The paragraphs' NON-file decisions remain fully reachable and exact - the
      ``fn-extend`` refusal, the ``aa060`` access-type guard, the
      ``Cobol-File-Eof`` branch and ``aa100-Bad-Function`` all execute without
      touching a file.
O-2   ``call "fhlogger"`` [common/acas007.cbl:L656-L657] and
      [common/glbatchMT.cbl:L1708-L1709]. Rule R-1 forbids calling a COBOL
      program, and ``common/fhlogger.cbl`` is out of scope per Agent Action
      Plan section 0.2.2. :func:`ca_process_logs` emits one structured log
      record instead, gated exactly as the COBOL gates it, and changes no
      control flow.
O-3   THE SCREEN STATEMENTS. ``ba012``'s two ``display``s and its
      ``accept Accept-Reply at 2433`` [common/acas007.cbl:L600-L606], the
      ``stop "Cobol File EOF"`` [:L426], and the bridge's
      ``if Testing-2 display Display-Message-1`` at
      [common/glbatchMT.cbl:L864-L866], [:L945-L947] and [:L1004-L1006]. Agent
      Action Plan section 0.3.4 drops the pause and keeps the control transfer;
      the message text is still written to ``SQL-Msg`` where the COBOL writes
      it, because that field IS observable through ``File-Access``.
O-4   ``ba-ACAS-DAL-Process``'s terminal geometry and curses environment
      [common/glbatchMT.cbl:L339-L347]. Presentation with no database effect.
O-5   ``ba012``'s credential load [common/acas007.cbl:L614-L619] is DELEGATED
      to :func:`~acas_posting.dal.connection.load_rdb_data_once` rather than
      duplicated, and the record-length comparison is recorded rather than
      resolved - it is AMBIGUITY Q-4's own comparison.

WHY THE BRIDGE PARAGRAPHS CARRY AN ``mt_`` PREFIX
=================================================
Both programs declare paragraphs called ``ba010``, ``ba020``,
``Ca-Process-Logs`` and ``ca-Exit``, and Python has one namespace per module.
The handler's paragraphs therefore keep their bare COBOL names -
:func:`aa010_main`, :func:`ba020_process_dal`, :func:`ca_process_logs` - and
the bridge's carry ``mt_`` for ``glbatchMT``: :func:`mt_ba010_initialise`,
:func:`mt_ba020_process_open`, :func:`mt_ca_process_logs`. The two paragraphs
the Agent Action Plan names explicitly are exported UNPREFIXED as required:
:func:`bb000_hv_load` and :func:`bb100_unload_hvs`.

WHAT THIS MODULE MUST NOT DO
============================
R-1  No ``subprocess``, ``ctypes``, ``cffi``, ``os.system``, ``os.popen``,
     ``os.exec*``, ``cobc``, ``cobcrun`` or ``cobmysqlapi``, and no import of
     ``harness``. Nothing here executes, embeds or shells out to COBOL.
R-2  No ``float``, no ``complex``, no ``math``, no ``round``, no ``numpy`` and
     no ``pandas``. The four control totals are ``decimal.Decimal`` end to end
     and the four date fields are ``int``. A ``Decimal`` is never built from a
     binary float.
R-3  Only ``SELECT``, ``INSERT``, ``UPDATE`` and ``DELETE``. No DDL, no
     ``alembic``, no ORM machinery, no threading, no ``asyncio``, no
     ``multiprocessing``, no pool - and NO CONTROL-TOTAL VALIDATION, which
     belongs to ``programs/gl051_batch_control_check.py``.
R-6  No clock, no random source and no sleep. Statement order is the COBOL's.

AUTOCOMMIT - A CONSTRAINT ON THE HARNESS, NOT ON THIS MODULE
============================================================
[common/glbatchLD.cbl:L9-L13] carries the loader's instruction, verbatim:

    "This modules uses commit and rollback so you MUST ensure that autocommit
    is OFF in the rdb settings. It is as default set ON."

That binds ``harness/seed.sh``, not this module. A census of all twenty
in-scope bridges finds ZERO ``autocommit``, ``COMMIT``, ``ROLLBACK`` and
``START TRANSACTION`` statements: the bridges run under whatever the connection
declares, and ``acas_posting/dal/connection.py`` owns that declaration. No
transaction control is added here, and the loader's instruction is recorded
above so that a reader does not conclude it was missed.
"""

from __future__ import annotations

import dataclasses
import decimal
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, NoReturn

from acas_posting.dal import cursor_state
from acas_posting.dal.connection import (
    OpenOutcome,
    TransportSecurity,
    acquire_cursor,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
    transport_decimal_context,
)
from acas_posting.dal.status import (
    AccessType,
    DbErrorStatus,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    end_of_file_status,
    log_cobol_stop,
    log_file_handler_record,
    log_handler_failure,
    is_duplicate_key_bridge_level,
    mysql_1100_db_error,
    override_we_error_for_operation,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess, LoggingData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_batch import (
    BatchAmounts,
    BatchDates,
    GlBatchRecord,
    PostingData,
    WsBatchKey,
    WsBatchKey9,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    "AMBIGUITIES",
    "ANOMALIES",
    "BRIDGE",
    "BatchColumn",
    "BatchKeyViewsDisagreeError",
    "BridgeCalledOutsideHandlerError",
    "BridgeNotOpenError",
    "COLUMNS",
    "COLUMN_NAMES",
    "COPYBOOK",
    "DELETE_ALL_HIGH_KEY",
    "DISPATCH_ORDER",
    "ENTITY_FACADE",
    "ERROR_MESSAGE_GL901",
    "ERROR_MESSAGE_GL904",
    "FILE_KEY_NO_REQUIRED",
    "FlatFileStoreNotMigratedError",
    "GUARDED_FUNCTIONS",
    "HANDLER",
    "KEY_OF_REFERENCE",
    "MOST_RELATION_DEFAULT",
    "OMISSIONS",
    "PROG_NAME",
    "RECORD",
    "START_RELATION_BY_ACCESS_TYPE",
    "START_ACCESS_TYPE_RANGE",
    "TABLE",
    "TABLE_OF_KEYNAMES_ROW",
    "WS_LOG_FILE_NO_COBOL_PATH",
    "WS_LOG_FILE_NO_RDB_PATH",
    "WS_LOG_SYSTEM",
    "WS_NO_PARAGRAPH_BRIDGE",
    "WS_NO_PARAGRAPH_COBOL",
    "WS_BATCH_RECORD_LENGTH",
    "WS_BATCH_RECORD_LENGTH_COMMENT_CLAIM",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_reread",
    "aa050_process_read_indexed",
    "aa051_reread",
    "aa060_process_start",
    "aa070_process_write",
    "aa080_process_delete",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_exit",
    "aa_main_exit",
    "aa_process_flat_file",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba020_process_dal",
    "ba_process_rdbms",
    "ba_rdbms_exit",
    "batch_key_image",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "ca_exit",
    "ca_process_logs",
    "declare_connection_policy",
    "dispatch",
    "glbatch_mt",
    "mt_ba010_initialise",
    "mt_ba020_process_open",
    "mt_ba030_process_close",
    "mt_ba040_process_read_next",
    "mt_ba041_reread",
    "mt_ba050_process_read_indexed",
    "mt_ba060_process_start",
    "mt_ba070_process_write",
    "mt_ba080_process_delete",
    "mt_ba085_process_delete_all",
    "mt_ba090_process_rewrite",
    "mt_ba100_bad_function",
    "mt_ba998_free",
    "mt_ba999_end",
    "mt_ba999_exit",
    "mt_ba_acas_dal_process",
    "mt_bb200_insert",
    "mt_bb300_update",
    "mt_ca_process_logs",
    "reset_working_storage",
    "signed_to_unsigned_host_variable",
    "synchronise_batch_key_views",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# IDENTITY - the handler, the bridge, the table and the record it serves.
# ---------------------------------------------------------------------------

#: The COBOL handler this module reimplements [common/acas007.cbl:L12].
HANDLER: Final[str] = "acas007"

#: The generated bridge it calls [common/glbatchMT.cbl:L10].
BRIDGE: Final[str] = "glbatchMT"

#: The frozen table [mysql/ACASDB.sql:L80].
TABLE: Final[str] = "GLBATCH-REC"

#: The record layout both programs share [copybooks/wsbatch.cob:L13].
RECORD: Final[str] = "WS-Batch-Record"

#: The entity facade name [copybooks/Proc-ACAS-FH-Calls.cob:L51].
ENTITY_FACADE: Final[str] = "GL-Batch"

#: The copybook the record comes from.
COPYBOOK: Final[str] = "copybooks/wsbatch.cob"

#: ``prog-name pic x(20) value "acas007 (3.3.00)"`` [common/acas007.cbl:L236].
PROG_NAME: Final[str] = "acas007 (3.3.00)"

#: ``move 2 to WS-Log-System`` [common/acas007.cbl:L280]. The comment there
#: enumerates the whole family: ``1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock``.
WS_LOG_SYSTEM: Final[LogSystem] = LogSystem.GL

#: ``move 13 to WS-Log-File-No`` [common/acas007.cbl:L281] - the indexed path.
WS_LOG_FILE_NO_COBOL_PATH: Final[int] = 13

#: ``move 23 to WS-Log-File-no`` [common/acas007.cbl:L577] - ANOMALY N-log, the
#: relational path's overwrite, spelled with a lower-case ``no`` at that site.
WS_LOG_FILE_NO_RDB_PATH: Final[int] = 23

#: The only key number this handler accepts [common/acas007.cbl:L288, :L294].
FILE_KEY_NO_REQUIRED: Final[int] = 1

#: ``function Length (WS-Batch-Record)`` and ``function length (Batch-Record)``,
#: the two values ``ba012-Test-WS-Rec-Size-2`` compares [common/acas007.cbl:
#: L582-L587]. ONE constant serves both, because ``copybooks/fdbatch.cob:L11-L49``
#: declares FIELD FOR FIELD the same layout as ``copybooks/wsbatch.cob:L13-L54``
#: - the only difference is ``03 WS-Batch-Key9 redefines WS-Batch-Key``, and a
#: ``REDEFINES`` adds no length. So ``A`` and ``B`` are necessarily equal and
#: ``A < B`` can never be true: ANOMALY N-901-unreachable.
#:
#: AMBIGUITY Q-4, RESOLVED ON THE COMPILED ORACLE. GnuCOBOL 3.2 - the compiler
#: ``common/comp-common.sh:L9`` targets - measures BOTH records at 96, and every
#: sub-group at its naive sum with no padding anywhere: ``WS-Batch-Key`` 6,
#: ``Items`` 2, ``Batch-Status`` 1, ``Cleared-Status`` 1, ``Bcycle`` 2, ``Dates``
#: 16 (four four-byte ``binary-long``), ``Amounts`` 24 (four six-byte packed
#: ``pic 9(9)v99``), ``Description`` 24, ``posting-data`` 15, ``Batch-Start`` 5.
#: 6+2+1+1+2+16+24+24+15+5 = 96. The FIELD SUM GOVERNS and there is no
#: trailing-field alignment drift, which is what the Agent Action Plan section
#: 0.6.8 sent to the oracle.
WS_BATCH_RECORD_LENGTH: Final[int] = 96

#: What the maintainer's comment claims instead - ANOMALY A-15, kept on record
#: and NOT reconciled. The same three lines appear twice in the frozen source,
#: [copybooks/wsbatch.cob:L7-L9] and [copybooks/fdbatch.cob:L6-L8], verbatim::
#:
#:     *> 96 bytes 26/03/09
#:     *> 98 bytes 20/12/11 (no, dont understand as I count 96)
#:     *>   but function length (batch-record) says 98?
#:
#: 98 does not hold under the target compiler. The contradiction is recorded
#: because the comment is frozen text; only the BEHAVIOUR is settled, and the
#: behaviour is settled identically either way, because both operands of the
#: comparison move together.
WS_BATCH_RECORD_LENGTH_COMMENT_CLAIM: Final[int] = 98

#: ``move 901 to WE-Error`` [common/acas007.cbl:L589] and the value
#: ``ba012-Test-WS-Rec-Size-2`` then tests for at [:L592]. Named because the
#: test is on the CALLER's field, which nothing clears - ANOMALY N-901-sticky.
RECORD_SIZE_WE_ERROR: Final[int] = int(WeError.RECORD_SIZE_MISMATCH)

#: ``03 GL901 pic x(31) value "GL901 Note error and hit return".``
#: [common/acas007.cbl:L249]. The second of the two lines the 901 branch
#: displays [:L601]. Presentation, so the display itself is omission O-3, but the
#: literal is published because it is part of the frozen program's observable
#: text and a reader diffing the two programs will look for it.
ERROR_MESSAGE_GL901: Final[str] = "GL901 Note error and hit return"

#: ``03 GL904 pic x(32) value "GL904 Program Error: Temp rec = ".``
#: [common/acas007.cbl:L250], with the continuation of the message spelled out in
#: the comment beneath it [:L251] as ``yyy < Batch-Rec = zzz``. This one DOES
#: reach the caller: the assembled ``Display-Blk`` is copied into ``SQL-Msg``
#: [:L602], which is part of ``File-Access``.
ERROR_MESSAGE_GL904: Final[str] = "GL904 Program Error: Temp rec = "

#: ``77 Display-Blk pic x(75) value spaces.`` [common/acas007.cbl:L242].
_DISPLAY_BLK_WIDTH: Final[int] = 75

#: The four ``start Batch-File key ...`` verbs of ``aa060-Process-Start``, keyed
#: by the ``Access-Type`` that selects each. The ``if``s appear in the frozen
#: source in THIS order - equal-to, not-less-than, greater-than, less-than
#: [common/acas007.cbl:L479-L503] - which is NOT numeric order, and they are four
#: SEPARATE ``if``s rather than a chain, so the order is preserved here as the
#: insertion order of this mapping.
_START_VERB_LOCATORS: Final[Mapping[int, str]] = MappingProxyType(
    {
        int(AccessType.EQUAL_TO): "[common/acas007.cbl:L480]",
        int(AccessType.NOT_LESS_THAN): "[common/acas007.cbl:L486]",
        int(AccessType.GREATER_THAN): "[common/acas007.cbl:L492]",
        int(AccessType.LESS_THAN): "[common/acas007.cbl:L499]",
    }
)

#: ``77 A pic 9(4)`` and ``77 B pic 9(4)`` [common/acas007.cbl:L240-L241], the
#: width the two lengths are STRINGed at, so 96 renders as ``0096``.
_RECORD_LENGTH_PICTURE_DIGITS: Final[int] = 4


# ---------------------------------------------------------------------------
# THE KEY GUARD, AS DATA. ANOMALY N-guard: `acas000` guards 4, 5 and 7 instead,
# and the two sets are deliberately not harmonised [common/acas007.cbl:L285-
# L299]. ANOMALY N-996-comment: the comment on the 996 branch at [:L295] is a
# copy-paste of the 998 comment at [:L289] and describes the wrong condition.
# ---------------------------------------------------------------------------
GUARDED_FUNCTIONS: Final[Mapping[int, int]] = MappingProxyType(
    {
        # `when 4 *> fn-read-indexed` [common/acas007.cbl:L286-L292]
        int(FileFunction.READ_INDEXED): int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
        # `when 9 *> fn-start`, sharing the same `if` [common/acas007.cbl:L287]
        int(FileFunction.START): int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
        # `when 8 *> fn-delete` [common/acas007.cbl:L293-L298], a DIFFERENT code
        int(FileFunction.DELETE): int(WeError.DELETE_KEY_OUT_OF_RANGE),
    }
)

#: The handler's ``evaluate File-Function`` ``when`` order
#: [common/acas007.cbl:L338-L357]. RE-WRITE (7) precedes DELETE (8), and there
#: is no ``when 6`` - the source's own comment reads ``*> 6 is unused``.
DISPATCH_ORDER: Final[tuple[int, ...]] = (
    int(FileFunction.OPEN),           # 1 -> aa020-Process-Open        [:L339-L340]
    int(FileFunction.CLOSE),          # 2 -> aa030-Process-Close       [:L341-L342]
    int(FileFunction.READ_NEXT),      # 3 -> aa040-Process-Read-Next   [:L343-L344]
    int(FileFunction.READ_INDEXED),   # 4 -> aa050-Process-Read-Indexed[:L345-L346]
    int(FileFunction.WRITE),          # 5 -> aa070-Process-Write       [:L347-L348]
    int(FileFunction.RE_WRITE),       # 7 -> aa090-Process-Rewrite     [:L349-L350]
    int(FileFunction.DELETE),         # 8 -> aa080-Process-Delete      [:L351-L352]
    int(FileFunction.START),          # 9 -> aa060-Process-Start       [:L353-L354]
)

#: ``move NNN to WS-No-Paragraph`` on the indexed path, one per paragraph
#: [common/acas007.cbl:L364, :L401, :L418, :L448, :L465, :L512, :L523, :L536].
WS_NO_PARAGRAPH_COBOL: Final[Mapping[str, int]] = MappingProxyType(
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

#: ``move N to ws-No-Paragraph`` inside the bridge [common/glbatchMT.cbl:L426,
#: :L445, :L466, :L534, :L616, :L646, :L775, :L824, :L867, :L948, :L985,
#: :L1039]. The numbers are the bridge's own and share no scheme with the
#: handler's 201..208 - both are reproduced as declared.
WS_NO_PARAGRAPH_BRIDGE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ba020-Process-Open": 1,
        "ba030-Process-Close": 2,
        "ba040-Process-Read-Next": 3,
        "ba041-Reread": 4,
        "ba050-Process-Read-Indexed": 5,
        "ba050-Process-Read-Indexed-fetch": 6,
        "ba060-Process-Start": 8,
        "ba070-Process-Write": 10,
        "ba080-Process-Delete": 13,
        "ba085-Process-Delete-ALL": 15,
        "ba090-Process-Rewrite": 17,
        "ba998-Free": 20,
    }
)

#: ``move 999999 to ws-BATCH-KEY`` [common/glbatchMT.cbl:L922], the high key
#: ``ba085-Process-Delete-ALL`` deletes BELOW. Six characters, because the key
#: of reference is offset 1 length 6. ANOMALY N-deleteall-999999.
DELETE_ALL_HIGH_KEY: Final[str] = "999999"

#: ``move spaces to MOST-Relation`` [common/glbatchMT.scb:L629]. ANOMALY
#: N-relation-nodefault: the ``evaluate`` that follows has no ``when other``, so
#: an out-of-range ``Access-Type`` leaves the relation as spaces. Three
#: characters, matching ``MOST-Relation pic xxx`` [common/glbatchMT.scb:L248].
MOST_RELATION_DEFAULT: Final[str] = "   "

#: ``evaluate Access-Type`` for the START relation, verbatim from
#: [common/glbatchMT.scb:L631-L642]. Transcribed rather than imported so the
#: absence of a ``when other`` is visible here; the executable path uses
#: ``dal/cursor_state.py``, which reproduces the same table plus the bridge's
#: own 5..8 rejection. ANOMALY N-start-dead-arm: ``Access-Type`` 9 never
#: reaches this ``evaluate``, so its arm is dead code.
START_RELATION_BY_ACCESS_TYPE: Final[Mapping[int, str]] = MappingProxyType(
    {
        int(AccessType.EQUAL_TO): "=  ",         # when 5 [:L632-L633]
        int(AccessType.LESS_THAN): "<  ",        # when 6 [:L634-L635]
        int(AccessType.GREATER_THAN): ">  ",     # when 7 [:L636-L637]
        int(AccessType.NOT_LESS_THAN): ">= ",    # when 8 [:L638-L639]
        int(AccessType.NOT_GREATER_THAN): "<= ",  # when 9 - DEAD [:L640-L641]
    }
)

#: ``if access-type < 5 or > 8`` - the inclusive bounds BOTH programs test,
#: [common/acas007.cbl:L472] and [common/glbatchMT.cbl:L715]. Note the shared
#: source comments: ``*> NOT using 'not >'`` and ``*> not using not < or not >``.
START_ACCESS_TYPE_RANGE: Final[tuple[int, int]] = (5, 8)

#: The single row of ``Table-Of-Keynames``, transcribed field for field from
#: [common/glbatchMT.scb:L231-L241]: name, offset, length, type, occurs.
TABLE_OF_KEYNAMES_ROW: Final[Mapping[str, object]] = MappingProxyType(
    {
        "KeyName": "BATCH-KEY",
        "KOR-Offset": 1,
        "KOR-Length": 6,
        "KOR-Type": "STR",
        "occurs": 1,
        "offset-length-literal": "00010006",
        "source": "[common/glbatchMT.scb:L231-L241]",
    }
)

#: The same key as ``dal/cursor_state.py`` already holds it, so the positioning
#: verbs and this module can never disagree about offset, length or column.
KEY_OF_REFERENCE: Final[cursor_state.KeyOfReference] = cursor_state.key_of_reference(
    TABLE, FILE_KEY_NO_REQUIRED
)


# ---------------------------------------------------------------------------
# TRACEABILITY REGISTERS. Rule R-4 requires every reproduced defect be
# recorded, and rule R-6 requires every question sent to the oracle be
# recorded. These three tuples are the machine-readable half of that; the
# prose half is the module docstring and `docs/migration/anomaly-log.md`.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Note:
    """One registered anomaly, omission or ambiguity.

    Attributes:
        reference: The identifier used in the module docstring, in
            ``docs/migration/anomaly-log.md`` and in
            ``docs/migration/ambiguity-resolutions.md``.
        summary: What the frozen program does, in one sentence.
        locators: Every ``[<path>:L<n>]`` that evidences it.
    """

    reference: str
    summary: str
    locators: tuple[str, ...]


ANOMALIES: Final[tuple[_Note, ...]] = (
    _Note(
        "A-11",
        "Entered, Proofed, Posted and Stored are signed binary-long in the "
        "copybook and unsigned PIC 9(10) COMP in the host-variable group, so a "
        "negative loses its sign at the bridge before any SQL runs.",
        (
            "[copybooks/wsbatch.cob:L36-L39]",
            "[common/glbatchMT.cbl:L287-L290]",
            "[mysql/ACASDB.sql:L86-L89]",
        ),
    ),
    _Note(
        "A-15",
        "The maintainer records the record as 96 bytes, then 98, then says he "
        "counts 96 but function length reports 98; ba012-Test-WS-Rec-Size-2 "
        "compares exactly those two lengths.",
        ("[copybooks/wsbatch.cob:L7-L9]", "[common/acas007.cbl:L579-L591]"),
    ),
    _Note(
        "N-widen",
        "The four control totals are widened from 11 digits to 14 at the host "
        "variable and stay widened at the decimal(14,2) column.",
        (
            "[copybooks/wsbatch.cob:L41-L44]",
            "[common/glbatchMT.cbl:L291-L294]",
            "[mysql/ACASDB.sql:L90-L93]",
        ),
    ),
    _Note(
        "N18b",
        "One Open-plus-Output request calls the bridge twice: first fn-Open "
        "with fn-Output, then fn-Delete-All, because ba015-Test-Ends performs "
        "ba020-Process-Dal and then falls through into it again.",
        (
            "[common/acas007.cbl:L305-L312]",
            "[common/acas007.cbl:L622-L631]",
            "[common/acas007.cbl:L640-L645]",
            "[common/acas005.cbl:L307]",
            "[common/acas008.cbl:L313-L319]",
        ),
    ),
    _Note(
        "N-relation-nodefault",
        "The START relation evaluate has no when other, so an Access-Type "
        "outside 5..9 leaves MOST-Relation as spaces and builds a malformed "
        "predicate; no default is supplied.",
        ("[common/glbatchMT.scb:L631-L642]",),
    ),
    _Note(
        "N-initialize",
        "Two initialisation semantics in one bridge: initialize WS-Batch-Record "
        "with filler on the EOF2 path, and a plain initialize in bb100.",
        ("[common/glbatchMT.cbl:L589]", "[common/glbatchMT.cbl:L1106]"),
    ),
    _Note(
        "N-log",
        "WS-Log-File-No is set to 13 on the indexed path and overwritten to 23 "
        "on the relational path, where the field is also spelled with a "
        "lower-case no.",
        ("[common/acas007.cbl:L281]", "[common/acas007.cbl:L577]"),
    ),
    _Note(
        "N-guard",
        "acas007 guards File-Key-No for functions 4, 9 and 8; acas000 guards 4, "
        "5 and 7 instead. The sets are not harmonised.",
        ("[common/acas007.cbl:L285-L299]",),
    ),
    _Note(
        "N-998",
        "We-Error 998 carries three documented meanings across the codebase: "
        "file seeks key type out of range, invalid calling parameter settings, "
        "and File-Key-No out of range.",
        (
            "[common/acas007.cbl:L289]",
            "[common/acas007.cbl:L473]",
            "[common/glpostingMT.cbl:L141]",
        ),
    ),
    _Note(
        "N-996-comment",
        "The comment on the 996 branch is a copy-paste of the 998 comment and "
        "describes the wrong condition.",
        ("[common/acas007.cbl:L295]", "[common/acas007.cbl:L289]"),
    ),
    _Note(
        "N-name",
        "The camelCase copybook name bDefault is flattened to BDEFAULT at both "
        "the host variable and the column.",
        (
            "[copybooks/wsbatch.cob:L48]",
            "[common/glbatchMT.cbl:L296]",
            "[mysql/ACASDB.sql:L95]",
        ),
    ),
    _Note(
        "N-deleteall-999999",
        "Delete-All is not a bare DELETE: it moves 999999 into the key and "
        "deletes WHERE BATCH-KEY < 999999, so a batch keyed exactly 999999 "
        "survives, and its row-count guard is not > zero rather than not = 1.",
        (
            "[common/glbatchMT.cbl:L900]",
            "[common/glbatchMT.cbl:L922]",
            "[common/glbatchMT.cbl:L928-L938]",
            "[common/glbatchMT.cbl:L962]",
        ),
    ),
    _Note(
        "N-close-double-log",
        "aa030-Process-Close performs aa999-main-exit, whose body logs under "
        "Testing-1, and then performs Ca-Process-Logs unconditionally, so a "
        "close logs twice under Testing-1.",
        ("[common/acas007.cbl:L407-L410]", "[common/acas007.cbl:L551-L554]"),
    ),
    _Note(
        "N-start-code-divergence",
        "The handler's access-type guard writes We-Error 998 and leaves "
        "FS-Reply at the zero it had just moved, so a caller testing only "
        "FS-Reply sees success; the bridge writes (99, 997) for the same "
        "condition and the handler's own header documents 997.",
        (
            "[common/acas007.cbl:L466-L475]",
            "[common/glbatchMT.cbl:L715-L720]",
            "[common/acas007.cbl:L155]",
        ),
    ),
    _Note(
        "N-start-dead-arm",
        "The bridge rejects access-type < 5 or > 8 before the relation "
        "evaluate, so the when 9 arm mapping Access-Type 9 to <= is unreachable "
        "dead code.",
        ("[common/glbatchMT.cbl:L715-L720]", "[common/glbatchMT.scb:L640-L641]"),
    ),
    _Note(
        "N-badfunction-divergence",
        "The handler's bad-function paragraph returns (99, 999); the bridge's "
        "returns (99, 990).",
        ("[common/acas007.cbl:L548-L549]", "[common/glbatchMT.cbl:L1030-L1031]"),
    ),
    _Note(
        "N-nostatus",
        "ba010-Initialise has its status zeroing commented out, and ba080, "
        "ba085 and ba090 transfer to ba999-End from inside the row-count test "
        "but outside the errno test, so a delete or rewrite that matches no row "
        "returns the caller's incoming status unchanged; ba070 differs only in "
        "that it zeroed the status itself, so a write that inserts no row "
        "reports success.",
        (
            "[common/glbatchMT.cbl:L351-L352]",
            "[common/glbatchMT.cbl:L881-L896]",
            "[common/glbatchMT.cbl:L962-L977]",
            "[common/glbatchMT.cbl:L1008-L1020]",
            "[common/glbatchMT.cbl:L821]",
        ),
    ),
    _Note(
        "N-hv-render",
        "Every value is rendered through WS-MYSQL-EDIT PIC -Z(18)9.9(9) and no "
        "slice ever includes position 1, which holds the sign, so the sign "
        "cannot reach the statement even for a field that kept it.",
        ("[common/glbatchMT.cbl:L1150-L1160]", "[common/glbatchMT.cbl:L1262-L1269]"),
    ),
    _Note(
        "N-insert-set-syntax",
        "The insert uses MySQL's INSERT ... SET form rather than a column list "
        "with VALUES, and the update re-SETs all twenty-one columns including "
        "the primary key before appending its WHERE.",
        ("[common/glbatchMT.cbl:L1145-L1148]", "[common/glbatchMT.cbl:L1428-L1697]"),
    ),
    _Note(
        "N-affected-rows-int32",
        "MySQL_affected_rows writes four bytes through an int pointer into the "
        "eight-byte binary-double unsigned Ws-Mysql-Count-Rows, and "
        "mysql_affected_rows returns (my_ulonglong)-1 on failure, so a failed "
        "statement leaves 4294967295 there rather than zero; ba085-Process-"
        "Delete-ALL guards on not > zero instead of not = 1, so that value "
        "takes its else branch and A FAILED DELETE-ALL REPORTS COMPLETE "
        "SUCCESS.",
        (
            "[copybooks/mysql-procedures.cpy:L178]",
            "[copybooks/mysql-variables.cpy:L73]",
            "[common/glbatchMT.cbl:L962]",
            "[common/glbatchMT.cbl:L974-L978]",
        ),
    ),
    _Note(
        "N-open-nomode",
        "An Open whose Access-Type is none of input, i-o, output or extend falls "
        "through all four arms of aa020-Process-Open without touching a file and "
        "still reaches the paragraph's tail, so it is answered with the caller's "
        "own incoming FS-Reply, upgraded to We-Error 999 if that happened to be "
        "non-zero, with no diagnostic of any kind.",
        (
            "[common/acas007.cbl:L365-L393]",
            "[common/acas007.cbl:L394-L398]",
        ),
    ),
    _Note(
        "N-fa-statuses-skipped",
        "The Open-plus-Output special case reaches the bridge from a branch that "
        "precedes the move of RDBMS-Flat-Statuses into FA-RDBMS-Flat-Statuses, "
        "so on that one request - and only that one - File-Access reaches the "
        "bridge with the store selector still at its own default while every "
        "other relational request carries the copied value.",
        (
            "[common/acas007.cbl:L305-L312]",
            "[common/acas007.cbl:L316-L320]",
            "[copybooks/wsfnctn.cob:L72-L83]",
        ),
    ),
    _Note(
        "N-901-unreachable",
        "ba012-Test-WS-Rec-Size-2 compares function Length of WS-Batch-Record "
        "against function length of Batch-Record, but fdbatch.cob declares "
        "field for field the same layout as wsbatch.cob - the only difference "
        "is a REDEFINES, which adds no length - so A equals B always and the "
        "A < B arm can never fire; GnuCOBOL 3.2 measures both at 96.",
        (
            "[common/acas007.cbl:L581-L591]",
            "[copybooks/fdbatch.cob:L11-L49]",
            "[copybooks/wsbatch.cob:L13-L54]",
        ),
    ),
    _Note(
        "N-901-sticky",
        "The 901 display-and-exit branch tests WE-Error, which nothing clears - "
        "the handler's own status zeroing is commented out - so a caller "
        "arriving with a stale 901 takes that branch even though the lengths "
        "agree, is answered with its own incoming FS-Reply because only the "
        "A < B arm writes 99, and closes the first-call guard on the way out so "
        "the credentials are never loaded for the rest of the run.",
        (
            "[common/acas007.cbl:L334-L335]",
            "[common/acas007.cbl:L581-L584]",
            "[common/acas007.cbl:L592]",
            "[common/acas007.cbl:L607]",
            "[common/acas007.cbl:L614-L620]",
        ),
    ),
    _Note(
        "N-countrows-shared",
        "Ws-Mysql-Count-Rows is ONE working-storage field written both by "
        "MYSQL-1210-COMMAND, as an affected-row count, and by "
        "MYSQL-1220-STORE-RESULT, as a selected-row count, so a delete or "
        "rewrite that affected no row leaves zero in it and the NEXT "
        "fn-read-next on a live cursor ends the walk at ba041-Reread's zero "
        "test - silently, with the caller's incoming status unchanged.",
        (
            "[copybooks/mysql-variables.cpy:L73]",
            "[copybooks/mysql-procedures.cpy:L178]",
            "[copybooks/mysql-procedures.cpy:L196]",
            "[common/glbatchMT.cbl:L579-L594]",
            "[general/gl072.cbl:L373-L377]",
        ),
    ),
)

OMISSIONS: Final[tuple[_Note, ...]] = (
    _Note(
        "O-1",
        "The indexed-file store itself. Every aa0NN paragraph is reproduced, "
        "but the physical ISAM verb raises FlatFileStoreNotMigratedError "
        "because the Agent Action Plan's target inventory contains no "
        "indexed-file store.",
        ("[common/acas007.cbl:L362-L542]",),
    ),
    _Note(
        "O-2",
        "call fhlogger, in both programs. Rule R-1 forbids calling a COBOL "
        "program and fhlogger is out of scope, so one structured log record is "
        "emitted under the same gate instead.",
        ("[common/acas007.cbl:L656-L657]", "[common/glbatchMT.cbl:L1708-L1709]"),
    ),
    _Note(
        "O-3",
        "The screen statements: ba012's two displays and its accept, the "
        "stop for testing in aa040, and the bridge's Testing-2 displays. The "
        "pause is dropped and the control transfer preserved; the message text "
        "is still written to SQL-Msg where the COBOL writes it.",
        (
            "[common/acas007.cbl:L600-L606]",
            "[common/acas007.cbl:L426]",
            "[common/glbatchMT.cbl:L864-L866]",
        ),
    ),
    _Note(
        "O-4",
        "ba-ACAS-DAL-Process's terminal geometry and curses environment "
        "settings, which are presentation with no database effect.",
        ("[common/glbatchMT.cbl:L339-L347]",),
    ),
    _Note(
        "O-5",
        "ba012's credential load is delegated to connection.load_rdb_data_once "
        "rather than duplicated, and its record-length comparison is recorded "
        "rather than resolved because it is ambiguity Q-4's own comparison.",
        ("[common/acas007.cbl:L614-L619]",),
    ),
    _Note(
        "O-6",
        "WS-Ledger and WS-Batch-Nos have no host variable and no column: they "
        "survive only inside the concatenated BATCH-KEY, reachable through the "
        "WS-Batch-Key9 redefinition of the same six bytes.",
        ("[copybooks/wsbatch.cob:L15]", "[copybooks/wsbatch.cob:L19]"),
    ),
    _Note(
        "O-7",
        "The group items Dates, Amounts and posting-data are groups and "
        "correctly not columns. Amounts is where comp-3 is declared, and its "
        "four elementary items inherit packed usage from it.",
        (
            "[copybooks/wsbatch.cob:L35]",
            "[copybooks/wsbatch.cob:L40]",
            "[copybooks/wsbatch.cob:L47]",
        ),
    ),
    _Note(
        "O-8",
        "The nine 88-level condition names of WS-Batch-Record are predicates "
        "over the record and belong to records/gl_batch.py; they are neither "
        "re-declared nor imported here.",
        ("[copybooks/wsbatch.cob:L16-L18]", "[copybooks/wsbatch.cob:L26-L32]"),
    ),
)

AMBIGUITIES: Final[tuple[_Note, ...]] = (
    _Note(
        "Q-3",
        "RESOLVED ON THE COMPILED ORACLE. What a negative binary value actually "
        "stores after passing through an unsigned host variable into an unsigned "
        "column. GnuCOBOL 3.2 applies ABSOLUTE-VALUE semantics - the ISO MOVE "
        "reading - and NOT a two's-complement reinterpretation of the source "
        "bytes: moving a signed binary-long into PIC 9(10) COMP measured "
        "-5 to 5, -1 to 1, -99 to 99, -20240101 to 20240101 and -2147483648 to "
        "2147483648, with the receiving field's own digit count then bounding "
        "the magnitude. signed_to_unsigned_host_variable already implemented "
        "exactly that reading, so the measurement confirms the implementation "
        "rather than changing it. The same probe re-confirms N-hv-render: the "
        "WS-MYSQL-EDIT render carries no sign for any of those inputs. The sign "
        "loss itself stays on record as A-11 because it is the defect; only the "
        "resulting value is settled.",
        (
            "[copybooks/wsbatch.cob:L36-L39]",
            "[common/glbatchMT.cbl:L287-L290]",
            "[mysql/ACASDB.sql:L86-L89]",
        ),
    ),
    _Note(
        "Q-4",
        "RESOLVED ON THE COMPILED ORACLE. Whether the declared record length or "
        "the field sum governs, which changes field alignment for the trailing "
        "fields. GnuCOBOL 3.2 measures function length of BOTH WS-Batch-Record "
        "and Batch-Record at 96, matching the field sum exactly with no padding "
        "in any sub-group, so the field sum governs, there is no trailing-field "
        "drift, and the maintainer's 98 does not hold under the target "
        "compiler. The 96-versus-98 contradiction stays on record as A-15 "
        "because the comment is frozen text; only the behaviour is settled.",
        (
            "[copybooks/wsbatch.cob:L7-L9]",
            "[copybooks/fdbatch.cob:L6-L8]",
            "[common/acas007.cbl:L581-L591]",
        ),
    ),
    _Note(
        "Q-5",
        "Where control resumes when the 901 branch's go to ba-rdbms-exit leaves "
        "the range of the perform ba012-Test-WS-Rec-Size-2 issued from "
        "aa010-main. exit section runs off the end of the PROCEDURE DIVISION, "
        "because Ca-Process-Logs and ca-Exit are paragraphs inside "
        "ba-Process-RDBMS section and no section follows, which in a called "
        "subprogram is an implicit exit program. That reading is implemented - "
        "the handler returns to its caller and the flat-file dispatch is "
        "skipped - and recorded here because unwinding a live perform stack is "
        "implementation-specific.",
        (
            "[common/acas007.cbl:L324]",
            "[common/acas007.cbl:L607]",
            "[common/acas007.cbl:L649-L650]",
            "[common/acas007.cbl:L653-L662]",
        ),
    ),
)


# ---------------------------------------------------------------------------
# ERRORS. Three named boundaries, each unreachable through `dispatch` on a
# correctly configured caller, each raised rather than silently papered over.
# The handler's own error vocabulary is the (FS-Reply, We-Error) pair and is
# used for everything the compiled program can actually express.
# ---------------------------------------------------------------------------


class FlatFileStoreNotMigratedError(RuntimeError):
    """Raised when a request would reach the indexed-file store.

    OMISSION O-1. The handler serves two stores and only one of them is
    migrated: ``if not FS-Cobol-Files-Used`` routes to the bridge
    [common/acas007.cbl:L316-L320] and everything else falls through to the
    ``aa0NN`` paragraphs, which read and write ``Batch-File`` directly. The
    Agent Action Plan's target inventory has no indexed-file store - MySQL is
    the store, ``harness/seed.sh`` seeds MySQL and the scenario diffs compare
    MySQL tables - so there is nothing for those verbs to act on.

    Fabricating a store would invent behaviour the specification does not have,
    and returning a success status would hide a caller that left
    ``File-System-Used`` at its copybook default of zero
    [copybooks/wssystem.cob:L112-L113], which is exactly the mistake this error
    exists to make loud. Note that the paragraphs' non-file decisions are NOT
    affected: the ``fn-extend`` refusal, the ``aa060`` access-type guard, the
    ``Cobol-File-Eof`` branch and ``aa100-Bad-Function`` all complete normally
    because none of them touches a file.
    """


class BatchKeyViewsDisagreeError(ValueError):
    """Raised when the two readings of the six key bytes contradict each other.

    ``WS-Batch-Key`` [copybooks/wsbatch.cob:L14-L19] and ``WS-Batch-Key9``
    [:L20-L21] are the SAME SIX BYTES - the second is a ``REDEFINES`` of the
    first - so in COBOL they cannot disagree. Two Python attributes can, and
    ``acas_posting/records/gl_batch.py`` deliberately does not reconcile them,
    saying so in the docstring of :class:`~acas_posting.records.gl_batch.
    WsBatchKey9`: keeping the two readings in step at the moment a row is
    written or read is the business of the ``acas007`` handler module at the
    bridge boundary.

    :func:`synchronise_batch_key_views` does that reconciliation. It raises this
    error only when BOTH readings are non-default and they disagree, because
    that is the one case where no reading can be preferred without inventing a
    rule the copybook does not declare - and silently choosing one would move a
    posted batch to the wrong key.
    """


class BridgeCalledOutsideHandlerError(RuntimeError):
    """Raised when the bridge is asked to open with no system record resident.

    ``glbatchMT`` is only ever reached by ``call "glbatchMT"`` from inside
    ``acas007`` [common/acas007.cbl:L640-L645], so at the moment the bridge
    opens a connection the handler's ``System-Record`` is live in its LINKAGE
    SECTION [:L265]. ``ba012-Test-WS-Rec-Size-2`` is what copies the six
    credential items out of it into ``RDB-Data`` [:L614-L619], and the bridge
    then reads them [common/glbatchMT.cbl:L402-L425].

    :func:`dispatch` therefore records the system record for the duration of
    the call chain and :func:`glbatch_mt` reads it from there, which keeps
    :func:`glbatch_mt` at exactly the three parameters its ``CALL`` declares.
    Calling :func:`glbatch_mt` with ``fn-Open`` before any :func:`dispatch` is a
    state the compiled system cannot reach, so it raises here rather than
    inventing a credential source.
    """


class BridgeNotOpenError(RuntimeError):
    """Raised when a statement verb reaches the bridge with no connection open.

    ``Ws-Mysql-Cid`` is the connection handle ``MYSQL-1000-OPEN`` fills in
    [copybooks/mysql-variables.cpy:L65], and every statement paragraph performs
    ``MYSQL-1210-COMMAND`` with it. If ``fn-Open`` was never performed that
    handle is a NULL POINTER, and ``mysql_query(NULL, ...)`` is undefined
    behaviour in the C API - the compiled program does not reach a status, it
    faults. There is therefore no frozen behaviour to reproduce.

    Raising follows the precedent ``dal/connection.py`` sets for exactly this
    class of condition and states in its own section comment: a state the frozen
    program cannot be in has nothing to degrade to, and manufacturing
    ``(FS-Reply 99, We-Error 911)`` would make it indistinguishable from a server
    genuinely declining a statement. Rules R-3 and R-4 are untouched, because no
    status pair, stored value or statement text moves.
    """


# ---------------------------------------------------------------------------
# THE TWENTY-ONE COLUMNS, AS DATA, DERIVED FROM THE DATA DICTIONARY.
#
# Agent Action Plan section 0.8.1, verbatim: "**Data dictionary first.** The
# dictionary is generated from the bridge before record definitions are
# written, and every Python field definition cites its entry. This ordering is
# a directive, not a preference - it is what prevents fields being transcribed
# by eye."
#
# So nothing below is typed out from the sources. `loader.entries_for_table`
# supplies the columns in ORDINAL order, `loader.drift_for` supplies each
# conversion, `loader.cite` supplies each citation, and the record attribute
# path is walked out of `records/gl_batch.py` through `loader.trace_record`.
# The only thing this module computes is the `WS-MYSQL-EDIT` slice, and that is
# a single arithmetic rule checked against all seventeen slices the bridge
# writes - see the module docstring.
# ---------------------------------------------------------------------------

#: ``01 TD-GLBATCH-REC`` [common/glbatchMT.cbl:L281] - the host-variable group
#: name, and ``TP-GLBATCH-REC USAGE POINTER`` [:L280] its result pointer.
_HV_GROUP: Final[str] = "TD-GLBATCH-REC"

#: ``WS-MYSQL-EDIT PIC -Z(18)9.9(9)``: 1 sign, 2..20 integer, 21 point, 22..30
#: fraction. An integer field of n digits right-aligns at 20, so its slice
#: starts at ``_EDIT_INTEGER_END + 1 - n``.
_EDIT_INTEGER_END: Final[int] = 20

#: Where the fraction digits begin in the same edited field.
_EDIT_FRACTION_START: Final[int] = 22

#: Truncation is a DELIBERATE loss of digits, so it cannot be done inside
#: :func:`~acas_posting.dal.connection.transport_decimal_context`, which traps
#: ``Inexact`` and ``Rounded`` precisely to make accidental loss impossible.
#: This context truncates toward zero - which is what a COBOL store without
#: ``ROUNDED`` does - and still traps the conditions that indicate a bug.
_TRUNCATING: Final[decimal.Context] = decimal.Context(
    prec=64,
    rounding=decimal.ROUND_DOWN,
    traps=[decimal.InvalidOperation, decimal.DivisionByZero, decimal.Overflow],
)


@dataclass(frozen=True, slots=True)
class BatchColumn:
    """One column of ``GLBATCH-REC`` with its whole provenance attached.

    Every member is derived from the generated data dictionary rather than
    transcribed, so a change in the frozen sources reaches this module through
    ``data_dictionary/acas_posting_dictionary.json`` and not through an edit
    here. Rule R-5 is satisfied at the field level by :attr:`citation`, which
    is ``loader.cite(key)`` and names the copybook line, the host-variable line
    and the column line for this one field.

    Attributes:
        ordinal: The column's position in the frozen ``CREATE TABLE``, 1-based.
        column: The MySQL column name, hyphens and all.
        quoted: The same name backtick-quoted through
            :func:`~acas_posting.dal.connection.quote_identifier`.
        host_variable: The bridge's ``HV-`` item that carries it.
        copybook_field: The ``WS-Batch-Record`` item it comes from.
        dictionary_key: The dictionary key, ``GLBATCH-REC.<COLUMN>``.
        citation: ``loader.cite(dictionary_key)`` - the three-way locator.
        storage: ``INT``, ``DECIMAL`` or ``STR``; the carrier rule for R-2.
        hv_digits: Total digits of the host variable, or ``None`` if character.
        hv_integer_digits: Digits left of the implied point, or ``None``.
        hv_scale: Digits right of the implied point, or ``None``.
        hv_character_length: Character width, or ``None`` if numeric.
        hv_signed: Whether the HOST VARIABLE is signed. False for every
            numeric item of this group - there is not one ``S9`` in it.
        copybook_signed: Whether the COPYBOOK item is signed. True for the four
            ``binary-long`` dates, which is the whole of anomaly A-11.
        sql_type: The declared column type, verbatim from the schema.
        is_primary_key: True for ``BATCH-KEY`` alone.
        drift: One sentence per disagreement, from ``loader.drift_for``.
        record_path: The attribute path into :class:`GlBatchRecord`.
        anomaly_refs: Anomaly identifiers the dictionary already attaches.
        ambiguity_refs: Ambiguity identifiers the dictionary already attaches.
        edit_slice: The 1-based ``(offset, length)`` of the integer part in
            ``WS-MYSQL-EDIT``, or ``None`` for a character column.
        edit_fraction_slice: The same for the fraction part, or ``None``.
    """

    ordinal: int
    column: str
    quoted: str
    host_variable: str
    copybook_field: str
    dictionary_key: str
    citation: str
    storage: str
    hv_digits: int | None
    hv_integer_digits: int | None
    hv_scale: int | None
    hv_character_length: int | None
    hv_signed: bool
    copybook_signed: bool
    sql_type: str
    is_primary_key: bool
    drift: tuple[str, ...]
    record_path: tuple[str, ...]
    anomaly_refs: tuple[str, ...]
    ambiguity_refs: tuple[str, ...]
    edit_slice: tuple[int, int] | None
    edit_fraction_slice: tuple[int, int] | None

    @property
    def is_character(self) -> bool:
        """True when the host variable is ``PIC X(n)`` rather than numeric."""
        return self.hv_character_length is not None

    @property
    def is_decimal(self) -> bool:
        """True when the value is carried as :class:`decimal.Decimal`."""
        return self.storage == "DECIMAL"

    @property
    def loses_sign_at_the_bridge(self) -> bool:
        """True for the four date fields of anomaly A-11.

        Signed in the copybook and unsigned in the host variable, so the sign
        is discarded at :func:`bb000_hv_load` and never reaches the statement
        [copybooks/wsbatch.cob:L36-L39], [common/glbatchMT.cbl:L287-L290].
        """
        return self.copybook_signed and not self.hv_signed


def _record_paths() -> Mapping[str, tuple[str, ...]]:
    """Walk :class:`GlBatchRecord` for every field's dictionary key.

    ``loader.trace_record`` reports one entry per attribute of a record class,
    naming its dictionary key or, for a group item, the nested class to
    descend into. Recursing over the nested classes yields the full attribute
    path for every elementary item, which is how a column finds its Python
    home without a hand-written table that could drift from the record module.

    Returns:
        Dictionary key mapped to the attribute path into a
        :class:`GlBatchRecord` instance, e.g. ``GLBATCH-REC.INPUT-GROSS`` to
        ``("amounts", "input_gross")``.
    """
    found: dict[str, tuple[str, ...]] = {}

    def walk(record: type, prefix: tuple[str, ...]) -> None:
        for trace in loader.trace_record(record):
            path = (*prefix, trace.attribute)
            if trace.group_type is not None:
                walk(trace.group_type, path)
            elif trace.dictionary_key is not None:
                found[trace.dictionary_key] = path

    walk(GlBatchRecord, ())
    return MappingProxyType(found)


def _edit_slices(
    integer_digits: int | None, scale: int | None
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    """Derive a host variable's ``WS-MYSQL-EDIT`` slices from its picture.

    The bridge moves each host variable into one edited field and then strings
    a fixed substring of it into the statement, for example
    ``FUNCTION TRIM (WS-MYSQL-EDIT(13:08))`` for a ``9(08) COMP`` item
    [common/glbatchMT.cbl:L1154]. The offsets look arbitrary but are not: the
    integer part right-aligns at position 20, so an ``n``-digit field starts at
    ``21 - n``. That one rule reproduces every slice the bridge writes for this
    table, which the module docstring lists.

    ⭐ ANOMALY N-hv-render REPRODUCED HERE. ``WS-MYSQL-EDIT PIC -Z(18)9.9(9)``
    holds its sign at position 1 [common/glbatchMT.cbl:L1150-L1160], and the
    widest host variable in this table is fourteen digits, so the smallest
    offset this function can ever return is ``21 - 14 = 7``. POSITION 1 IS
    THEREFORE UNREACHABLE BY CONSTRUCTION and a sign cannot travel into the
    statement even for a host variable that kept one - which none in
    ``TD-GLBATCH-REC`` does [:L282-L302]. The same slicing appears in the
    ``WHERE`` builder [:L1262-L1269]. ⛔ The lower bound is not clamped and no
    sign position is spliced in: the loss is the specification (R-4), and it is
    the mechanism by which the four signed-to-unsigned date conversions of
    ANOMALY A-11 become invisible downstream.

    Args:
        integer_digits: Digits left of the implied decimal point, or ``None``
            for a character item.
        scale: Digits right of it, or ``None`` for a character item.

    Returns:
        The integer slice and the fraction slice, each as a 1-based
        ``(offset, length)`` pair, and ``None`` where the bridge writes none.
    """
    if integer_digits is None:
        return (None, None)
    integer = (_EDIT_INTEGER_END + 1 - integer_digits, integer_digits)
    if not scale:
        return (integer, None)
    return (integer, (_EDIT_FRACTION_START, scale))


def _build_columns() -> tuple[BatchColumn, ...]:
    """Assemble :data:`COLUMNS` from the dictionary, in table ordinal order.

    Raises:
        LookupError: If the dictionary and ``records/gl_batch.py`` disagree
            about which fields exist. That is a wiring fault in the generated
            artefacts rather than a data condition, so it is raised at import
            where it cannot be mistaken for a runtime status - the same stance
            ``dal/cursor_state.py`` takes over its key metadata.
    """
    paths = _record_paths()
    built: list[BatchColumn] = []
    for entry in loader.entries_for_table(TABLE):
        host_variable = entry.bridge_host_variable
        column = entry.column
        copybook = entry.copybook
        if host_variable is None or column is None or copybook is None:
            raise LookupError(
                f"{entry.key} is missing one of its three sides in the "
                f"generated dictionary; every column of {TABLE} must carry a "
                f"copybook field, a host variable and a column, because the "
                f"bridge is the authoritative mapping for this migration."
            )
        path = paths.get(entry.key)
        if path is None:
            raise LookupError(
                f"{entry.key} has no attribute on GlBatchRecord, so the "
                f"record module and the data dictionary disagree about "
                f"{TABLE}. Regenerate data_dictionary/"
                f"acas_posting_dictionary.json before using this module."
            )
        integer_slice, fraction_slice = _edit_slices(
            host_variable.integer_digits, host_variable.scale
        )
        built.append(
            BatchColumn(
                ordinal=column.ordinal,
                column=column.name,
                quoted=quote_identifier(column.name),
                host_variable=host_variable.name,
                copybook_field=copybook.name,
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                storage=str(entry.cobol_python_storage),
                hv_digits=host_variable.digits,
                hv_integer_digits=host_variable.integer_digits,
                hv_scale=host_variable.scale,
                hv_character_length=host_variable.character_length,
                hv_signed=bool(host_variable.signed),
                copybook_signed=bool(copybook.signed),
                sql_type=column.sql_type,
                is_primary_key=bool(column.is_primary_key),
                drift=tuple(loader.drift_for(entry.key).details),
                record_path=path,
                anomaly_refs=tuple(entry.anomaly_refs),
                ambiguity_refs=tuple(entry.ambiguity_refs),
                edit_slice=integer_slice,
                edit_fraction_slice=fraction_slice,
            )
        )
    return tuple(built)


#: The twenty-one columns of ``GLBATCH-REC`` in the ordinal order of the frozen
#: ``CREATE TABLE`` [mysql/ACASDB.sql:L80-L103], which is also the order
#: ``bb000-HV-Load`` moves them in [common/glbatchMT.cbl:L1069-L1089] and the
#: order ``bb200-Insert`` writes them in [:L1150-L1408].
COLUMNS: Final[tuple[BatchColumn, ...]] = _build_columns()

#: The same names alone, for callers that only need the list.
COLUMN_NAMES: Final[tuple[str, ...]] = tuple(column.column for column in COLUMNS)

#: Indexed by column name, for the load and unload paragraphs.
_BY_COLUMN: Final[Mapping[str, BatchColumn]] = MappingProxyType(
    {column.column: column for column in COLUMNS}
)

#: Indexed by host-variable name, because that is how ``bb200-Insert`` and
#: ``bb300-Update`` name their operands - ``MOVE HV-BATCH-KEY TO ...``.
_BY_HOST_VARIABLE: Final[Mapping[str, BatchColumn]] = MappingProxyType(
    {column.host_variable: column for column in COLUMNS}
)

#: ``GLBATCH-REC`` backtick-quoted once, since every statement names it. The
#: bridge quotes it too [common/glbatchMT.cbl:L1146], so this is reproduction
#: rather than an added precaution - though it is also the only correct way to
#: name a hyphenated identifier in MySQL.
_QUOTED_TABLE: Final[str] = quote_identifier(TABLE)

#: The primary key, quoted, for the ``WHERE`` clauses ``ba080``, ``ba085`` and
#: ``ba090`` build [common/glbatchMT.cbl:L853-L861, :L928-L938, :L992-L1000].
_QUOTED_KEY: Final[str] = quote_identifier(KEY_OF_REFERENCE.column_name)

#: The dictionary key of the primary-key column, DERIVED from the column table
#: rather than written out, so it cannot drift from
#: ``data_dictionary/acas_posting_dictionary.json`` (rule R-5). Its copybook side
#: is ``WS-Batch-Key9`` - the ``REDEFINES`` view [copybooks/wsbatch.cob:L20-L21] -
#: which is the field ``bb000-HV-Load`` actually reads
#: [common/glbatchMT.cbl:L1069], so its descriptor is the right receiving picture
#: for any store into the key.
_KEY_DICTIONARY_KEY: Final[str] = _BY_COLUMN[KEY_OF_REFERENCE.column_name].dictionary_key

#: The place value of ``WS-Ledger`` inside the six-digit key. ``WS-Batch-Key`` is
#: ``WS-Ledger pic 9`` followed by ``WS-Batch-Nos pic 9(5)``
#: [copybooks/wsbatch.cob:L15-L19], so the ledger digit sits five decimal places
#: above the batch number and the pair reads as one six-digit value through the
#: ``WS-Batch-Key9`` redefinition [:L20-L21].
_LEDGER_DIGIT_SCALE: Final[int] = 10**5


def _logging_descriptors() -> Mapping[str, Any]:
    """Index ``Logging-Data``'s field descriptors by their COBOL name.

    ``WS-File-Key`` is ``pic x(64)`` [copybooks/wsfnctn.cob:L52] and every
    handler paragraph moves a literal into it, so those literals must be
    fitted to sixty-four characters exactly as a COBOL ``MOVE`` would - padded
    on the right with spaces, truncated on the right when too long. The
    descriptors that know how to do that already exist on
    ``records/file_access.py``; taking them from there rather than importing
    ``acas_posting.cobol`` keeps this module inside the import table the Agent
    Action Plan section 0.4.3 permits for a ``dal`` module.
    """
    return MappingProxyType({field.name: field for field in LoggingData.FIELDS})


_LOGGING_FIELDS: Final[Mapping[str, Any]] = _logging_descriptors()


def _record_descriptors() -> Mapping[str, Any]:
    """Index every ``WS-Batch-Record`` field descriptor by dictionary key.

    Used by :func:`bb100_unload_hvs` to apply the RECEIVING field's own
    truncation on the way back from the host variables. That truncation is real
    and not decorative: ``move HV-BATCH-KEY to WS-BATCH-KEY9`` moves an eight
    digit item into a six digit one [common/glbatchMT.cbl:L1107], and
    ``move HV-BATCH-START to Batch-Start`` moves eight digits into five
    [:L1127], so the high-order digits are discarded exactly as COBOL discards
    them.
    """
    indexed: dict[str, Any] = {}
    for group in (
        WsBatchKey,
        WsBatchKey9,
        GlBatchRecord,
        BatchDates,
        BatchAmounts,
        PostingData,
    ):
        for field in getattr(group, "FIELDS", ()):
            indexed[field.dictionary_key] = field
    return MappingProxyType(indexed)


_RECORD_FIELDS: Final[Mapping[str, Any]] = _record_descriptors()


# ---------------------------------------------------------------------------
# WORKING STORAGE. Neither program is declared `IS INITIAL`
# [common/acas007.cbl:L12], [common/glbatchMT.cbl:L10], so WORKING-STORAGE
# PERSISTS ACROSS CALLS and both keep state the caller never sees: the
# handler's first-call length flags, and the bridge's connection handle and
# `WHERE` buffer. Module-level singletons reproduce that residency, which is
# also how `dal/cursor_state.py` keeps its cursor states and `dal/connection.py`
# its credential cache. `reset_working_storage` exists for test isolation and
# has no COBOL counterpart, because a COBOL run cannot restart a program's
# working storage without a fresh process.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _HandlerWorkingStorage:
    """The residue ``acas007`` keeps between calls.

    Attributes:
        a: ``77 A pic 9(4)`` [common/acas007.cbl:L240], the caller's record
            length. Zero means "not measured yet", which is exactly how
            ``ba012-Test-WS-Rec-Size-2`` decides it is on the first call
            [:L581]. The maintainer's own note at [:L573] reads "Test on very
            first call only (So do NOT use var A & B again)".
        b: ``77 B pic 9(4)`` [:L241], the handler's own record length.
        display_blk: ``Display-Blk pic x(75)``, the 901 message. Built and
            copied into ``SQL-Msg`` [:L593-L602]; the two ``display``s that
            follow are omission O-3.
        cobol_file_status: ``Cobol-File-Status pic 9`` with
            ``88 Cobol-File-Eof value 1``, the handler's own end-of-file flag.
        linkage_system_record: The ``System-Record`` of the call in progress.
            Reproduces LINKAGE residency, not added state: at the moment
            ``ba020-Process-DAL`` calls the bridge [:L641] the handler's own
            invocation is still on the stack, so its first parameter is live.
        transport: The caller's transport declaration, forwarded to
            :func:`~acas_posting.dal.connection.mysql_1000_open`. Has NO COBOL
            counterpart and is not compared - see
            :func:`declare_connection_policy`.
        allow_frozen_placeholder_credentials: The caller's declaration about the
            shipped placeholder user and password. Also has no COBOL
            counterpart - see :func:`declare_connection_policy`.
    """

    a: int = 0
    b: int = 0
    display_blk: str = ""
    cobol_file_status: int = 0
    linkage_system_record: SystemRecord | None = None
    transport: TransportSecurity | None = None
    allow_frozen_placeholder_credentials: bool | None = None


@dataclass(slots=True)
class _BridgeWorkingStorage:
    """The residue ``glbatchMT`` keeps between calls.

    Attributes:
        connection: The handle ``MYSQL-1000-OPEN`` leaves behind
            [common/glbatchMT.cbl:L427] and ``MYSQL-1980-CLOSE`` releases
            [:L451]. One connection per file-open, no pool - rule R-3.
        ws_where: ``WS-Where``, the single-predicate clause every positioning
            and write paragraph builds [:L851-L861 and siblings].
        j: ``J pic s9(4) comp-5``, the ``with pointer`` cursor into
            ``WS-Where``. Its final value is the clause length, which is why
            ``move WS-Where (1:J) to WS-Log-Where`` works [:L863].
        most_relation: ``MOST-Relation pic xxx``. Left as spaces unless the
            ``evaluate`` sets it - anomaly N-relation-nodefault.
        host_variables: ``01 TD-GLBATCH-REC`` [:L281-L302], keyed by host
            variable name. ``bb000-HV-Load`` fills it, ``bb200-Insert`` and
            ``bb300-Update`` read it, and a fetch overwrites it.
        dal_data: ``01 DAL-Data`` [common/glbatchMT.scb:L247-L251], the
            bridge's OWN cursor block. Held here rather than in
            :mod:`acas_posting.dal.cursor_state`'s module-level set because the
            ``.scb`` declares it inside each bridge - that module's own
            docstring says so: "Every bridge holds its ``01 DAL-Data`` in its
            own working storage". Owning it is also what lets
            ``ba041-Reread`` test ``WS-MYSQL-Count-Rows`` against the live
            cursor, which anomaly N-countrows-shared depends on.
            :func:`reset_working_storage` clears it.
        ws_mysql_count_rows: ``Ws-Mysql-Count-Rows``
            [copybooks/mysql-variables.cpy:L73], ONE field written by TWO
            things - ``MYSQL-1210-COMMAND`` stores the affected-row count of an
            insert, update or delete, and ``MYSQL-1220-STORE-RESULT`` stores the
            row count of a select. Every write-side paragraph tests it, and so
            does ``ba041-Reread`` [common/glbatchMT.cbl:L579]. ANOMALY
            N-countrows-shared: because it is shared, a delete or rewrite that
            affected no row leaves zero here, and the NEXT ``fn-read-next`` on a
            live cursor then ends the walk. See :func:`mt_ba041_reread`.
        ws_mysql_error_number: ``WS-MYSQL-Error-Number``, the three-character
            field compared against the literal ``"0  "`` [:L830].
        ws_mysql_error_message: ``WS-MYSQL-Error-Message``.
        ws_mysql_sqlstate: ``WS-MYSQL-SQLstate``.
    """

    connection: Any = None
    ws_where: str = ""
    j: int = 1
    most_relation: str = MOST_RELATION_DEFAULT
    host_variables: dict[str, int | decimal.Decimal | str] = dataclasses.field(
        default_factory=dict
    )
    dal_data: cursor_state.CursorStateTable = dataclasses.field(
        default_factory=cursor_state.CursorStateTable
    )
    ws_mysql_count_rows: int = 0
    ws_mysql_error_number: str = "0  "
    ws_mysql_error_message: str = ""
    ws_mysql_sqlstate: str = ""


_HANDLER: Final[_HandlerWorkingStorage] = _HandlerWorkingStorage()
_BRIDGE_WS: Final[_BridgeWorkingStorage] = _BridgeWorkingStorage()


def reset_working_storage() -> None:
    """Clear both programs' working storage and this table's cursor state.

    No COBOL counterpart: a compiled run cannot reset a program's
    WORKING-STORAGE without starting a new process. It exists so that a test
    can establish the first-call condition ``ba012-Test-WS-Rec-Size-2`` tests
    [common/acas007.cbl:L581] and the ``Cursor-Not-Active`` condition
    ``ba040-Process-Read-Next`` tests [common/glbatchMT.cbl:L457], both of
    which are otherwise reachable only once per process.

    Any open connection is closed through
    :func:`~acas_posting.dal.connection.mysql_1980_close` so the reset cannot
    leak a socket. No ``COMMIT`` precedes that close, because no in-scope
    bridge has one.
    """
    if _BRIDGE_WS.connection is not None:
        mysql_1980_close(_BRIDGE_WS.connection)
        mysql_1999_exit()
    _HANDLER.a = 0
    _HANDLER.b = 0
    _HANDLER.display_blk = ""
    _HANDLER.cobol_file_status = 0
    _HANDLER.linkage_system_record = None
    _HANDLER.transport = None
    _HANDLER.allow_frozen_placeholder_credentials = None
    _BRIDGE_WS.connection = None
    _BRIDGE_WS.ws_where = ""
    _BRIDGE_WS.j = 1
    _BRIDGE_WS.most_relation = MOST_RELATION_DEFAULT
    _BRIDGE_WS.host_variables.clear()
    _BRIDGE_WS.ws_mysql_count_rows = 0
    _BRIDGE_WS.ws_mysql_error_number = "0  "
    _BRIDGE_WS.ws_mysql_error_message = ""
    _BRIDGE_WS.ws_mysql_sqlstate = ""
    # The bridge's own `01 DAL-Data` [common/glbatchMT.scb:L247-L251], and then
    # this table's entry in the module-level set as well - the second call is
    # belt and braces for a caller that reached `cursor_state` directly, and
    # costs nothing.
    _BRIDGE_WS.dal_data.reset(TABLE)
    cursor_state.reset(TABLE)


def declare_connection_policy(
    *,
    transport: TransportSecurity | None = None,
    allow_frozen_placeholder_credentials: bool | None = None,
) -> None:
    """Record a per-handler connection-policy declaration for later opens.

    ⛔ NORMALLY THERE IS NOTHING TO CALL HERE. The connection policy of a run is
    ONE object installed once by the deployment -
    :func:`acas_posting.dal.connection.set_connection_policy` - and every open
    that declares nothing resolves to it, this handler's included. This function
    exists only to NARROW that policy for this one table, which no in-scope path
    does; leaving it uncalled is the ordinary case and is what keeps the twenty
    handlers of this package saying the same thing about the same connection.

    NO COBOL COUNTERPART, AND NOTHING COMPARED MOVES BY A CHARACTER.
    ``ba020-Process-Open`` marshals the six ``RDB-Data`` items and performs
    ``MYSQL-1000-OPEN`` [common/glbatchMT.cbl:L402-L427] with no notion of
    transport security at all - the C interface passes a literal zero client-flag
    word and no TLS arguments. A declaration therefore changes what
    :func:`~acas_posting.dal.connection.mysql_1000_open` reports about a
    connection, and in the opt-in strict configurations which connections it
    permits - never a stored value, a status pair, a statement text or a table
    dump (rules R-3, R-4).

    WHY IT IS DECLARED HERE RATHER THAN PASSED. ``glbatch_mt`` takes exactly the
    bridge's three parameters [common/acas007.cbl:L641-L644] and ``dispatch``
    exactly the handler's five [:L265-L271]; both are fixed by the Agent Action
    Plan section 0.4.3 and neither may grow a fourth. A declaration made once,
    out of band, before the run's first ``fn-Open`` is the only place left, and it
    matches how the harness genuinely works: one policy for a whole comparison
    run, not one per file operation.

    Args:
        transport: The transport declaration. ``None`` - the default - defers to
            the ONE installed policy, which is what every in-scope caller wants.
        allow_frozen_placeholder_credentials: ``True`` declares that the
            maintainer's shipped placeholder user and password in ``SYSTEM-REC``
            are the intended credentials and the server is disposable. ``None`` -
            the default - defers to the installed policy; ``False`` states
            positively that no declaration is made for this table.

    Examples:
        The declaration a deployment makes ONCE, and not here::

            from acas_posting.dal import connection

            connection.set_connection_policy(
                connection.ConnectionPolicy(
                    transport=connection.TransportSecurity(ca_file="/etc/ssl/ca.pem"),
                )
            )
    """
    _HANDLER.transport = transport
    #  NOT coerced with `bool(...)`: `None` is a THIRD state here - "this handler
    #  declares nothing, resolve it from the one installed policy" - and coercing
    #  it to False would turn an absent declaration into a positive refusal to
    #  declare, which is what made this handler's policy path diverge from its
    #  nineteen siblings. See `connection.set_connection_policy`.
    _HANDLER.allow_frozen_placeholder_credentials = (
        allow_frozen_placeholder_credentials
    )
    #  THE POLICY IS REPORTED, NOT THE PATHS IT NAMES. `%r` on a
    #  `TransportSecurity` renders `ca_file`, `certificate_file` and `key_file` -
    #  filesystem paths, one of which is a PRIVATE KEY (CWE-532). What an operator
    #  needs is whether the server will be authenticated and the session encrypted,
    #  and that is one boolean.
    _LOG.debug(
        "connection policy declared for %s: server_verified=%s "
        "placeholder_credentials=%s",
        BRIDGE,
        transport.verifies_the_server(),
        _HANDLER.allow_frozen_placeholder_credentials,
    )


# ---------------------------------------------------------------------------
# PRIMITIVES. Each one reproduces exactly one COBOL language behaviour that
# this module needs and that `acas_posting.cobol` would otherwise supply - it
# may not be imported here, per the Agent Action Plan section 0.4.3 import
# table, so the three behaviours that matter are implemented from the
# dictionary's own metadata and nothing more is implemented at all.
# ---------------------------------------------------------------------------


def _store_ws_file_key(logging_data: LoggingData, text: str) -> None:
    """``move <literal> to WS-File-Key`` with the receiving field's own fitting.

    ``WS-File-Key`` is ``pic x(64)`` [copybooks/wsfnctn.cob:L52], so a shorter
    literal is padded on the right with spaces and a longer one is truncated on
    the right. Every handler paragraph writes it - "OPEN GL BATCH file"
    [common/acas007.cbl:L395], "CLOSE GL BATCH file" [:L406], "EOF" [:L436] -
    and it is observable through ``File-Access``, so the fitting is reproduced
    rather than approximated with a bare assignment.

    Args:
        logging_data: The caller's ``Logging-Data`` block, mutated in place.
        text: The sending literal or field.
    """
    fitted = _LOGGING_FIELDS["WS-File-Key"].store(text)
    logging_data.ws_file_key = str(fitted)


def _store_sql_msg(logging_data: LoggingData, text: str) -> None:
    """``move <field> to SQL-Msg``, fitted to ``pic x(512)``.

    [copybooks/wsfnctn.cob:L51]. Used where the COBOL copies a diagnostic into
    the caller's block, including the 901 message ``ba012`` builds
    [common/acas007.cbl:L602] whose two ``display``s are omission O-3.
    """
    logging_data.sql_msg = str(_LOGGING_FIELDS["SQL-Msg"].store(text))


def signed_to_unsigned_host_variable(
    value: int, digits: int, *, dictionary_key: str
) -> int:
    """Move a signed value into an unsigned ``PIC 9(n) COMP`` host variable.

    ANOMALY A-11, AND THE ONLY PLACE THE SIGN IS DISCARDED. ``Entered``,
    ``Proofed``, ``Posted`` and ``Stored`` are ``binary-long`` and therefore
    signed [copybooks/wsbatch.cob:L36-L39]; ``HV-ENTERED`` and its three
    siblings are ``PIC 9(10) COMP`` and therefore unsigned
    [common/glbatchMT.cbl:L287-L290]; and the columns are ``int(8) unsigned``
    [mysql/ACASDB.sql:L86-L89]. Agent Action Plan section 0.6.2, verbatim: "a
    negative value computed in COBOL loses its sign **at the bridge**, not at
    the database - so the Python data-access layer must reproduce the bridge's
    conversion, not merely write the computed value and let MySQL complain."

    What is implemented here is the ISO ``MOVE`` reading: a value moved into an
    unsigned receiving item stores its ABSOLUTE VALUE, and a value with more
    digits than the receiving item has its HIGH-ORDER DIGITS DISCARDED. Neither
    step is an error condition - ``ON SIZE ERROR`` appears nowhere in the
    frozen handler or bridge, so there is no error path in the specification to
    reproduce, and nothing here raises, clamps or rejects.

    AMBIGUITY Q-3 IS RESOLVED, AND IT RESOLVES IN FAVOUR OF THE ABOVE. Agent
    Action Plan section 0.6.8 required the result be "measured rather than
    assumed", so it was measured: a probe declaring the copybook side verbatim
    from [copybooks/wsbatch.cob:L36-L39] and the bridge side verbatim from
    [common/glbatchMT.cbl:L287-L290], compiled by the GnuCOBOL 3.2 the
    maintainer's script targets [common/comp-common.sh:L9], yields::

        in=-0000000005  ->  HV-ENTERED=0000000005
        in=-0000000001  ->  HV-ENTERED=0000000001
        in=-0000000099  ->  HV-ENTERED=0000000099
        in=-0020240101  ->  HV-ENTERED=0020240101
        in=-2147483648  ->  HV-ENTERED=2147483648

    Absolute value, NOT a two's-complement reinterpretation of the source bytes.
    Keeping this as ONE named function is what let a single measurement confirm
    the whole conversion; ``docs/migration/ambiguity-resolutions.md`` carries the
    question and its resolution. The sign LOSS is not resolved and cannot be -
    it is the defect, and it stays registered as A-11.

    For the widths that actually occur the two steps do not compound: the
    receiving item holds ten digits and the widest ``binary-long`` magnitude is
    2147483648, also ten digits, so truncation never fires on a value the
    sending field could hold.

    Args:
        value: The signed value from the record, as an ``int``. Never a float -
            rule R-2 - and the four fields it applies to are ``int`` at every
            layer.
        digits: The receiving host variable's digit count, from the dictionary.
        dictionary_key: The field's dictionary key, used only in the log line
            that makes the loss visible to an operator.

    Returns:
        The value the host variable holds after the move: non-negative, and
        never wider than ``digits``.
    """
    magnitude = abs(int(value))
    stored = magnitude % (10**digits)
    if value < 0:
        # ANOMALY A-11 at the moment it happens. Neither raised nor reported,
        # because the compiled program neither refuses it nor reports it, and
        # either would be behaviour the specification does not have.
        #  IT IS SILENT, in both senses. The frozen bridge neither reports nor
        #  refuses the narrowing - its own comment is the only trace it leaves - so a
        #  record here is a diagnostic the compiled program cannot produce (rule
        #  R-4). And the record it used to emit interpolated the VALUE, twice: the
        #  signed figure and the unsigned figure actually stored, which for this
        #  record are batch control totals (CWE-532). The anomaly is reproduced by
        #  the narrowing itself and documented in
        #  `docs/migration/anomaly-log.md`; ambiguity Q-3, resolved against
        #  GnuCOBOL 3.2, is recorded in `docs/migration/ambiguity-resolutions.md`.
        #
        #  The frozen `if` is kept with an empty body so that rule R-5's reader
        #  finds the test and finds that it reports nothing.
        pass
    return stored


def _store_host_variable(
    column: BatchColumn, value: object
) -> int | decimal.Decimal | str:
    """Move one record field into its host variable, with the HV's own rules.

    The host variable's picture - not the copybook's - governs what is stored,
    which is the whole reason Agent Action Plan section 0.8.2 designates the
    bridge as authoritative: "The maintainer's one-way COBOL-to-MySQL bridge
    defines the authoritative record-layout to table mapping - it is the data
    dictionary for this migration." Every width, scale and sign used below is
    read from :class:`BatchColumn`, which read it from
    ``data_dictionary/acas_posting_dictionary.json``.

    Three cases, matching the three shapes present in ``TD-GLBATCH-REC``:

    * ``PIC X(n)`` - truncate or right-pad with spaces to ``n``.
    * ``PIC 9(n) COMP`` - absolute value, then discard high-order digits.
    * ``PIC 9(i)V9(s) COMP`` - truncate toward zero to ``s`` places, then
      absolute value, then discard integer digits beyond ``i``.

    Args:
        column: The column being loaded, carrying its host variable's metadata.
        value: The record field's current value.

    Returns:
        The value the host variable holds, as ``str``, ``int`` or
        :class:`decimal.Decimal` according to :attr:`BatchColumn.storage`.
    """
    if column.hv_character_length is not None:
        text = "" if value is None else str(value)
        width = column.hv_character_length
        return text[:width].ljust(width)

    digits = column.hv_digits or 0
    scale = column.hv_scale or 0
    integer_digits = column.hv_integer_digits or digits

    if column.is_decimal:
        # `Input-Gross` and its three siblings. The value arrives as a
        # `decimal.Decimal` because rule R-2 permits nothing else for money,
        # and the transport context is used only to CARRY it - it traps
        # `Inexact`, so the truncation below is done in `_TRUNCATING` instead.
        with decimal.localcontext(transport_decimal_context()):
            carried = value if isinstance(value, decimal.Decimal) else decimal.Decimal(
                str(value)
            )
        quantum = decimal.Decimal(1).scaleb(-scale)
        truncated = _TRUNCATING.quantize(carried, quantum)
        # Unsigned at all three layers for these four, so an absolute value is
        # the faithful move rather than the sign loss of anomaly A-11
        # [common/glbatchMT.cbl:L291-L294], [mysql/ACASDB.sql:L90-L93].
        magnitude = truncated.copy_abs()
        modulus = decimal.Decimal(10) ** integer_digits
        if magnitude >= modulus:
            # High-order digits beyond the host variable's twelve integer
            # positions are discarded, as a COBOL store does without
            # `ON SIZE ERROR`. `remainder` and not `remainder_near`: the
            # latter can return a negative and would invent a sign.
            magnitude = _TRUNCATING.remainder(magnitude, modulus)
            magnitude = _TRUNCATING.quantize(magnitude, quantum)
        return magnitude

    integer = 0 if value is None else int(value)
    if column.copybook_signed and not column.hv_signed:
        # The four date fields. ANOMALY A-11, applied here and nowhere else.
        return signed_to_unsigned_host_variable(
            integer, digits, dictionary_key=column.dictionary_key
        )
    return abs(integer) % (10**digits)


def _read_record_field(batch: GlBatchRecord, column: BatchColumn) -> object:
    """Read one field out of the record by its derived attribute path."""
    target: object = batch
    for attribute in column.record_path:
        target = getattr(target, attribute)
    return target


def _write_record_field(
    batch: GlBatchRecord, column: BatchColumn, value: object
) -> None:
    """Write one field into the record, applying the RECEIVING field's rules.

    ``bb100-UnloadHVs`` moves each host variable back into the record, and the
    receiving item is often NARROWER than the sending one - eight digits into
    six for the key [common/glbatchMT.cbl:L1107], eight into five for
    ``Batch-Start`` [:L1127], three into two for ``Items`` [:L1108]. Those
    moves discard high-order digits, so the record field's own descriptor from
    ``records/gl_batch.py`` does the store rather than a bare assignment.
    """
    descriptor = _RECORD_FIELDS[column.dictionary_key]
    stored = descriptor.store(value)
    target: object = batch
    for attribute in column.record_path[:-1]:
        target = getattr(target, attribute)
    setattr(target, column.record_path[-1], stored)


def batch_key_image(batch: GlBatchRecord) -> str:
    """Return the six characters ``WS-Batch-Record (1:6)`` holds.

    Every ``WHERE`` clause in the bridge takes its key value from a RAW
    CHARACTER SUBSTRING of the record buffer rather than from a typed field -
    ``WS-Batch-Record (K:L)`` with ``K`` 1 and ``L`` 6, from the key of
    reference [common/glbatchMT.scb:L231-L241]. Those six bytes are
    ``WS-Ledger`` pic 9 followed by ``WS-Batch-Nos`` pic 9(5)
    [copybooks/wsbatch.cob:L14-L19], which the ``WS-Batch-Key9`` redefinition
    reads as one ``pic 9(6)`` [:L20-L21].

    A zoned-decimal ``pic 9(6)`` is six digit characters with leading zeros
    present, so ``batch 1`` of the General Ledger is the text ``100001`` - and
    the comparison the bridge builds is a STRING comparison against that text,
    with the database left to coerce it. That is reproduced exactly, including
    the leading zeros, because dropping them would change the collation order a
    ``<`` or ``>=`` predicate resolves.

    Args:
        batch: The record whose key is wanted. Both readings are reconciled
            first, so it does not matter which one the caller populated.

    Returns:
        Exactly six characters.
    """
    synchronise_batch_key_views(batch)
    return f"{int(batch.ws_batch_key9.ws_batch_key9):06d}"


def synchronise_batch_key_views(batch: GlBatchRecord) -> int:
    """Reconcile ``WS-Batch-Key`` and ``WS-Batch-Key9`` and return the value.

    ``acas_posting/records/gl_batch.py`` assigns this job here, in the
    docstring of :class:`~acas_posting.records.gl_batch.WsBatchKey9`: the two
    are a ``REDEFINES`` pair over the same six bytes, nothing in the record
    module reconciles them because that would be logic the copybook does not
    declare, and "keeping the two readings in step at the moment a row is
    written or read is the business of the handler module at the bridge
    boundary, the ``acas007`` handler module."

    The rule, which is the only one the copybook supports:

    * If the two agree, or only one is non-default, that value wins and both
      readings are set to it. ``bb000-HV-Load`` reads ``WS-BATCH-KEY9``
      [common/glbatchMT.cbl:L1069] and ``ba070`` logs ``ws-BATCH-KEY``
      [:L820], so both must be right before either is used.
    * If both are non-default and they disagree, there is no basis in the
      copybook for preferring one, so :class:`BatchKeyViewsDisagreeError` is
      raised. In COBOL this state cannot arise - there is one storage - and
      silently picking a side would post a batch to the wrong key.

    Args:
        batch: The record, mutated in place so both readings agree.

    Returns:
        The reconciled six-digit key.

    Raises:
        BatchKeyViewsDisagreeError: If both readings are non-default and
            disagree.
    """
    grouped = int(batch.ws_batch_key.ws_ledger) * _LEDGER_DIGIT_SCALE + int(
        batch.ws_batch_key.ws_batch_nos
    )
    redefined = int(batch.ws_batch_key9.ws_batch_key9)
    if grouped and redefined and grouped != redefined:
        raise BatchKeyViewsDisagreeError(
            f"WS-Batch-Key reads {grouped:06d} and WS-Batch-Key9 reads "
            f"{redefined:06d}, but they redefine the same six bytes "
            f"[copybooks/wsbatch.cob:L14-L21] and so cannot differ. Set one "
            f"reading and let the acas007 handler derive the other."
        )
    value = redefined or grouped
    batch.ws_batch_key9.ws_batch_key9 = value
    batch.ws_batch_key.ws_ledger = value // _LEDGER_DIGIT_SCALE
    batch.ws_batch_key.ws_batch_nos = value % _LEDGER_DIGIT_SCALE
    return value


# ---------------------------------------------------------------------------
# bb000-HV-Load and bb100-UnloadHVs - the two halves of the bridge's data
# movement, named after the COBOL sections as the Agent Action Plan requires
# and exported unprefixed for the same reason.
# ---------------------------------------------------------------------------


def bb000_hv_load(batch: GlBatchRecord) -> Mapping[str, int | decimal.Decimal | str]:
    """``bb000-HV-Load Section.`` [common/glbatchMT.cbl:L1060-L1092].

    Loads the host-variable group from the record, in the order the bridge
    loads it. Verbatim, the frozen paragraph opens::

        initialize TD-GLBATCH-REC.
        move     WS-BATCH-KEY9      to HV-BATCH-KEY.
        move     Items              to HV-ITEMS
        move     Batch-Status       to HV-BATCH-STATUS
        ...
        move     Batch-Start        to HV-BATCH-START.

    Four things about it matter enough to state:

    1. ``initialize TD-GLBATCH-REC`` IS THE FIRST STATEMENT [:L1068], so an
       unset field becomes zero or space and NEVER SQL ``NULL``. Agent Action
       Plan section 0.6.2, verbatim: "This is why every column in the schema can
       be declared ``NOT NULL`` and why the Python layer must **default rather
       than omit**." Every one of the twenty-one host variables is present in
       the mapping this returns, always.
    2. THE KEY IS LOADED FROM THE REDEFINITION, ``WS-BATCH-KEY9`` [:L1069], not
       from the ``WS-Batch-Key`` group. :func:`synchronise_batch_key_views` runs
       first so the two readings cannot differ at that moment.
    3. THE LOAD ORDER IS THE COLUMN ORDER for this bridge, which is NOT true of
       its siblings - ``nominalMT`` loads the ledger name before the level and
       ``glpostingMT`` loads ``CR-PC`` before ``Post-CR``. ``glbatchMT`` is the
       well-behaved one; nobody should generalise from it.
    4. The maintainer's closing comment [:L1091-L1092], verbatim: "Loading HVs
       implies a non-Fetch action. RGs are handled separately for all such
       actions so they must not be loaded here."

    ANOMALY A-11 IS APPLIED HERE AND NOWHERE ELSE. The four
    ``binary-long`` date fields lose their sign in this paragraph, before any
    statement text exists, because the receiving host variables are unsigned
    [copybooks/wsbatch.cob:L36-L39] against [common/glbatchMT.cbl:L287-L290].
    See :func:`signed_to_unsigned_host_variable`, whose absolute-value semantics
    are confirmed by the ambiguity Q-3 measurement recorded there.

    Args:
        batch: The record to load from. Mutated only insofar as
            :func:`synchronise_batch_key_views` brings its two key readings
            into agreement.

    Returns:
        The host-variable group, keyed by host-variable name, with all
        twenty-one entries present.
    """
    # `initialize TD-GLBATCH-REC.` [common/glbatchMT.cbl:L1068]. Cleared rather
    # than replaced so the group keeps its identity across calls, which is what
    # WORKING-STORAGE residency means.
    _BRIDGE_WS.host_variables.clear()

    # `move WS-BATCH-KEY9 to HV-BATCH-KEY.` [:L1069] - the REDEFINES view.
    synchronise_batch_key_views(batch)

    for column in COLUMNS:
        _BRIDGE_WS.host_variables[column.host_variable] = _store_host_variable(
            column, _read_record_field(batch, column)
        )
    return MappingProxyType(dict(_BRIDGE_WS.host_variables))


def bb100_unload_hvs(
    row: Mapping[str, object] | None, batch: GlBatchRecord
) -> None:
    """``bb100-UnloadHVs Section.`` [common/glbatchMT.cbl:L1097-L1131].

    Moves the host variables back into the record after a fetch. The COBOL
    paragraph opens with the maintainer's own two notes, verbatim::

        *>  Load the data buffer in the interface with data from the host
        *>  variables. (init moved lower)
        *>
        *> NULL fields must not be returned in the buffer. SQL filters each
        *>  column to ensure it has a proper value.  This saves using
        *>  indicator variables.

        initialize WS-Batch-Record.
        move     HV-BATCH-KEY          to WS-BATCH-KEY9.
        ...
        move     HV-BATCH-START    to Batch-Start.

    ANOMALY N-initialize: that ``initialize`` at [:L1106] is the PLAIN form.
    The other one in this bridge, ``initialize WS-Batch-Record with filler``
    [:L589], additionally blanks ``FILLER`` items and belongs to the EOF2 path
    of ``ba041-Reread``; :func:`mt_ba041_reread` reproduces that one at its own
    site. The two are not normalised.

    The moves are NARROWING for several fields, and the narrowing is real:
    eight host-variable digits into a six-digit key [:L1107], eight into five
    for ``Batch-Start`` [:L1127], three into two for ``Items`` [:L1108]. Each
    receiving field's own descriptor performs the store, so the high-order
    digits are discarded exactly as COBOL discards them - see
    :func:`_write_record_field`.

    The trailing comment at [:L1129-L1130] mentions ``POST4-DAY``, ``MONTH``
    and ``YEAR``, which do not exist in this table at all; it is a copy-paste
    from ``irspostingMT``, and it is recorded here rather than acted on.

    Args:
        row: The fetched row, keyed by column name, or ``None`` for an
            end-of-result. ``None`` still performs the ``initialize``, because
            the COBOL paragraph is only ever entered after a successful fetch
            and the safest reproduction of "no data" is the initialised record
            the EOF paths also leave behind.
        batch: The record to unload into, mutated in place.
    """
    # `initialize WS-Batch-Record.` [common/glbatchMT.cbl:L1106] - PLAIN form.
    _initialize_ws_batch_record(batch, with_filler=False)
    if row is None:
        return

    # `move HV-BATCH-KEY to WS-BATCH-KEY9.` first [:L1107], then the remaining
    # twenty in column order [:L1108-L1127].
    for column in COLUMNS:
        if column.column not in row:
            # The bridge's own note says SQL filters every column so it always
            # has a proper value, and every column is `NOT NULL`, so a missing
            # key means the statement was not `SELECT *`. Left at its
            # initialised value rather than guessed at.
            continue
        value = row[column.column]
        _BRIDGE_WS.host_variables[column.host_variable] = _store_host_variable(
            column, value
        )
        _write_record_field(batch, column, value)

    # The key's two readings are one storage in COBOL, so the group reading is
    # brought into line with the redefinition the move above wrote
    # [copybooks/wsbatch.cob:L14-L21].
    synchronise_batch_key_views(batch)


def _initialize_ws_batch_record(batch: GlBatchRecord, *, with_filler: bool) -> None:
    """``initialize WS-Batch-Record``, in both of the bridge's two forms.

    ANOMALY N-initialize. The plain form [common/glbatchMT.cbl:L1106] sets every
    named elementary item to its category's zero - numerics to zero,
    alphanumerics to spaces - and LEAVES ``FILLER`` ITEMS ALONE. The
    ``with filler`` form [:L589] clears the ``FILLER`` items too. Both are
    reproduced; neither is normalised into the other.

    For THIS record the two forms produce the same result, because
    ``copybooks/wsbatch.cob`` declares no ``FILLER`` item anywhere in
    ``WS-Batch-Record`` [copybooks/wsbatch.cob:L13-L54]. That is exactly why the
    distinction is recorded rather than relied upon: it is a real semantic
    difference that happens to be inert here, and a reader comparing this module
    with a sibling handler over a record that DOES carry filler needs to know
    the difference was seen and kept.

    Args:
        batch: The record to initialise, mutated in place.
        with_filler: True for the ``with filler`` form, which is the EOF2 path.
    """
    for column in COLUMNS:
        descriptor = _RECORD_FIELDS[column.dictionary_key]
        blank: object = "" if column.storage == "STR" else 0
        _write_record_field(batch, column, descriptor.store(blank))
    batch.ws_batch_key.ws_ledger = 0
    batch.ws_batch_key.ws_batch_nos = 0
    batch.ws_batch_key9.ws_batch_key9 = 0
    if with_filler:
        # `initialize ... with filler` [common/glbatchMT.cbl:L589]. Nothing
        # further to clear: this record declares no FILLER item, so the two
        # forms coincide here. Recorded, not relied on - see the docstring.
        #  NO RECORD. `initialize ... with filler` displays nothing; that the
        #  with-filler and plain forms coincide for this record - it declares no
        #  FILLER item - is a fact about the layout, recorded in this comment where a
        #  reader of the code will find it, not in a run's log stream (rule R-4).
        #
        #  The frozen `if` is kept with an empty body so that rule R-5's reader
        #  finds the with-filler branch and finds that it has nothing to do.
        pass


# ---------------------------------------------------------------------------
# bb200-Insert and bb300-Update - the two statement builders. Both name all
# twenty-one columns, because `initialize TD-GLBATCH-REC` guarantees every host
# variable has a value and every column is `NOT NULL`
# [mysql/ACASDB.sql:L81-L101]. `None` is never bound.
# ---------------------------------------------------------------------------


def _bound_values() -> tuple[object, ...]:
    """Return the twenty-one host-variable values in column order.

    The bridge renders each of them into statement text through
    ``WS-MYSQL-EDIT``; this module binds the same values as parameters instead,
    for the reason the module docstring gives under VALUES ARE BOUND. The
    ORDER is the bridge's - column ordinal - because that is the order
    ``bb200-Insert`` emits its assignments in [common/glbatchMT.cbl:L1150-L1408]
    and ``bb300-Update`` repeats [:L1433-L1689].
    """
    return tuple(
        _BRIDGE_WS.host_variables[column.host_variable] for column in COLUMNS
    )


def mt_bb200_insert() -> tuple[str, tuple[object, ...]]:
    """``bb200-Insert Section.`` [common/glbatchMT.cbl:L1135-L1414].

    Builds the insert. ANOMALY N-insert-set-syntax: the bridge uses MySQL's
    ``SET`` form and not a column list with ``VALUES``, verbatim at
    [:L1145-L1148]::

        INITIALIZE WS-MYSQL-COMMAND
        MOVE 1 TO WS-MYSQL-I
        STRING 'INSERT INTO '
                 '`GLBATCH-REC` SET '
          INTO WS-MYSQL-COMMAND
          WITH POINTER WS-MYSQL-I end-string

    followed by one three-part group per column - the quoted name and an opening
    double quote, the value sliced out of ``WS-MYSQL-EDIT``, then a closing
    double quote and a comma - and finally ``";"`` and a ``X"00"`` terminator
    [:L1407-L1410]. The ``SET`` form and the ``VALUES`` form are equivalent to
    MySQL, so the statement below reproduces the bridge's and no behaviour turns
    on the choice; the form is preserved because rule R-6 makes the compiled
    statement the specification and a reader diffing the two should find the
    same shape.

    ALL TWENTY-ONE COLUMNS ARE NAMED and no value is ``None``. Both follow from
    ``initialize TD-GLBATCH-REC`` [:L1068] and from every column being
    ``NOT NULL`` [mysql/ACASDB.sql:L81-L101].

    Returns:
        The statement with ``%s`` placeholders, and the values to bind.
    """
    assignments = ", ".join(f"{column.quoted}=%s" for column in COLUMNS)
    statement = f"INSERT INTO {_QUOTED_TABLE} SET {assignments};"
    return (statement, _bound_values())


def mt_bb300_update() -> tuple[str, tuple[object, ...]]:
    """``bb300-Update Section.`` [common/glbatchMT.cbl:L1418-L1701].

    Builds the update, column for column exactly as :func:`mt_bb200_insert`
    builds the insert, and then appends the clause ``ba090-Process-Rewrite``
    left in ``WS-Where``, verbatim at [:L1690-L1697]::

        STRING " WHERE "
           INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
        STRING FUNCTION TRIM (WS-Where (1:J))
           INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
        STRING ";" X"00" INTO WS-MYSQL-COMMAND
          WITH POINTER WS-MYSQL-I end-string

    ANOMALY N-insert-set-syntax, second half: THE PRIMARY KEY IS AMONG THE
    COLUMNS IT SETS [:L1433-L1441]. An update therefore rewrites
    ``BATCH-KEY`` to the value the host variable already holds, which is the
    same value the ``WHERE`` selects on - so it is inert in practice and
    preserved anyway, because a caller that changed the key between the read
    and the rewrite would move the row, and that is behaviour.

    The ``WHERE`` text is trimmed, matching ``FUNCTION TRIM (WS-Where (1:J))``,
    and its key value is bound rather than pasted - see the module docstring.

    Returns:
        The statement with ``%s`` placeholders, and the values to bind: the
        twenty-one column values followed by the key the ``WHERE`` compares.
    """
    assignments = ", ".join(f"{column.quoted}=%s" for column in COLUMNS)
    statement = (
        f"UPDATE {_QUOTED_TABLE} SET {assignments} WHERE {_BRIDGE_WS.ws_where};"
    )
    return (statement, (*_bound_values(), _BRIDGE_WS.host_variables["HV-BATCH-KEY"]))


def _build_where(relation: str, key_value: str) -> str:
    """Build the single-predicate ``WHERE`` clause every paragraph builds.

    The construction is [common/glbatchMT.scb:L644-L650], quoted in full in the
    module docstring. Three properties are reproduced and one is deliberately
    changed:

    * the identifier is BACKTICK-QUOTED, through
      :func:`~acas_posting.dal.connection.quote_identifier`;
    * the relation is TRIMMED, matching ``delimited by space``, so a padded
      ``">= "`` reaches the statement as ``>=``;
    * the predicate is NEVER COMPOUNDED - one column, one relation, one value
      [common/glpostingMT.scb:L243-L245];
    * the value is BOUND as ``%s`` rather than pasted between double quotes.

    ANOMALY N-relation-nodefault: a relation of spaces produces
    ``` `BATCH-KEY` %s ```, which is malformed, and that is left exactly as the
    bridge leaves it [common/glbatchMT.scb:L631-L642]. No default is supplied.

    Args:
        relation: The relation, padded or not.
        key_value: The six-character key image. Recorded on the clause for
            logging; the caller binds it.

    Returns:
        The clause, without a leading ``WHERE``, as ``ba080`` and its siblings
        leave it in ``WS-Where``.
    """
    trimmed = relation.strip()
    clause = f"{_QUOTED_KEY} {trimmed} %s" if trimmed else f"{_QUOTED_KEY} %s"
    _BRIDGE_WS.ws_where = clause
    # `move 1 to J` then `with pointer J`, so J ends at the clause length plus
    # one and `WS-Where (1:J)` is the clause [common/glbatchMT.cbl:L852-L863].
    _BRIDGE_WS.j = len(clause) + 1
    _BRIDGE_WS.most_relation = relation
    #  NEITHER THE CLAUSE NOR THE KEY IS LOGGED. `WS-Where` is the composed SQL
    #  `WHERE` clause and `key_value` is the batch key it was built around, so
    #  together they name the exact batch being operated on (CWE-532). The clause is
    #  still BUILT and still stored, because the bridge stores it and the caller can
    #  read it; it simply does not reach a log record.
    return clause


# ===========================================================================
# THE BRIDGE - glbatchMT
#
# `Procedure Division using File-Access ACAS-DAL-Common-data WS-Batch-Record.`
# [common/glbatchMT.cbl:L334-L336], reached only by `call "glbatchMT"` from
# `ba020-Process-DAL` in the handler [common/acas007.cbl:L641-L644].
#
# One function per paragraph, in source order, each named `mt_<paragraph>` for
# the reason given in the module docstring: the handler has paragraphs of the
# same names, `ba010`, `ba020`, `ba100`, `ba999`, and they are DIFFERENT
# paragraphs of a DIFFERENT program.
#
# THE DISPATCH ORDER IS THE BRIDGE'S OWN, AND IT IS NOT THE HANDLER'S. The
# bridge evaluates 1, 2, 3, 4, 5, **6**, 7, 8, 9 [:L371-L395] - it HAS a
# `when 6` arm for `fn-Delete-All`, routing to `ba085-Process-DELETE-ALL`
# [:L385-L386], where the handler's `evaluate` has no such arm at all
# [common/acas007.cbl:L338-L357]. Delete-all therefore reaches SQL only through
# the two-stage Open-Output fall-through of anomaly N18b, never through the
# handler's own dispatch.
# ===========================================================================

#: ``01 Ws-Mysql-Error-Number pic x(5)``
#: [copybooks/mysql-variables.cpy:L84]. The maintainer's own note there records
#: it was "changed to 5 char 18/09/16", which matters: every bridge compares it
#: against the THREE-character literal ``"0  "`` [common/glbatchMT.cbl:L830],
#: and COBOL pads the shorter operand, so the comparison is against ``"0"``
#: followed by four spaces.
_WS_MYSQL_ERROR_NUMBER_WIDTH: Final[int] = 5

#: ``01 WS-Mysql-SqlState pic x(5)`` [copybooks/mysql-variables.cpy:L85].
_WS_MYSQL_SQLSTATE_WIDTH: Final[int] = 5

#: ``01 Ws-Mysql-Error-Message pic x(160)``
#: [copybooks/mysql-variables.cpy:L86], widened from 80 by the maintainer.
_WS_MYSQL_ERROR_MESSAGE_WIDTH: Final[int] = 160

#: The literal ``"0  "`` as the ``pic x(5)`` field actually compares it.
_WS_MYSQL_ERROR_NUMBER_ZERO: Final[str] = "0".ljust(_WS_MYSQL_ERROR_NUMBER_WIDTH)

#: ``move zero to SQL-Err`` [common/glbatchMT.cbl:L823] - a numeric zero moved
#: into ``SQL-Err pic x(5)`` [copybooks/wsfnctn.cob:L49] is an alphanumeric move
#: of the single character ``"0"``, space-filled to the right.
_SQL_ERR_ZERO: Final[str] = "0".ljust(5)


def _pic_x(text: str, width: int) -> str:
    """Fit ``text`` to ``pic x(width)`` - pad right with spaces, truncate right.

    The only COBOL ``MOVE`` rule this module needs that the dictionary's own
    descriptors do not already supply, because these three fields belong to
    ``mysql-variables.cpy`` rather than to any record in the data dictionary.
    """
    return text[:width] if len(text) >= width else text.ljust(width)


def _mysql_error_fields(error: BaseException | None) -> tuple[str, str, str]:
    """Stand in for the driver's three error-reporting entry points.

    Every write-side paragraph reports a failure with the same three calls, for
    example [common/glbatchMT.cbl:L827-L831]::

        call  "MySQL_errno" using WS-MYSQL-Error-Number
        call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
        move  WS-MYSQL-SqlState   to SQL-State
        if    WS-MYSQL-Error-Number  not = "0  "
              call "MySQL_error" using Ws-Mysql-Error-Message

    Those three C functions read the connection's last error, so their Python
    equivalent is the exception the driver raised. ``None`` means the statement
    succeeded, which is the case where ``MySQL_errno`` returns zero and the
    inner block is skipped - the situation that makes anomaly N-nostatus
    observable.

    Args:
        error: The driver's exception, or ``None`` when nothing failed.

    Returns:
        ``(WS-MYSQL-Error-Number, WS-MYSQL-SQLstate, WS-MYSQL-Error-Message)``,
        each fitted to its own picture width. The error number is
        :data:`_WS_MYSQL_ERROR_NUMBER_ZERO` when nothing failed, so the
        ``not = "0  "`` test behaves exactly as the frozen source's does.
    """
    if error is None:
        return (_WS_MYSQL_ERROR_NUMBER_ZERO, _pic_x("", _WS_MYSQL_SQLSTATE_WIDTH), "")
    errno = getattr(error, "errno", None)
    sqlstate = getattr(error, "sqlstate", None)
    message = getattr(error, "msg", None)
    # A driver exception with no error number at all still took the failure
    # path, and reporting it as "0" would send it through the errno test's
    # false arm and lose it. `MySQL_errno` cannot return zero after a failed
    # `mysql_query`, so a missing number is rendered as the unknown-error
    # number the client library itself uses for that case.
    errno_text = str(int(errno)) if isinstance(errno, int) and errno else "2000"
    return (
        _pic_x(errno_text, _WS_MYSQL_ERROR_NUMBER_WIDTH),
        _pic_x("" if sqlstate is None else str(sqlstate), _WS_MYSQL_SQLSTATE_WIDTH),
        _pic_x(
            str(error) if message is None else str(message),
            _WS_MYSQL_ERROR_MESSAGE_WIDTH,
        ),
    )


def _record_driver_error(error: BaseException | None) -> None:
    """Store the driver's three fields into the bridge's working storage.

    Separated from :func:`_mysql_error_fields` so that the storing and the
    reading are distinct, exactly as the ``call ... using`` statements and the
    later ``move``s of those same fields are distinct in the frozen source.
    """
    (
        _BRIDGE_WS.ws_mysql_error_number,
        _BRIDGE_WS.ws_mysql_sqlstate,
        _BRIDGE_WS.ws_mysql_error_message,
    ) = _mysql_error_fields(error)


def _errno_is_non_zero() -> bool:
    """``if WS-MYSQL-Error-Number not = "0  "`` [common/glbatchMT.cbl:L830].

    The identical test appears at [:L885] in ``ba080``, [:L966] in ``ba085``,
    [:L1012] in ``ba090``, [:L511] in ``ba040`` and [:L584] in ``ba041``. It is
    one predicate in one place here because it is one predicate written six
    times there, character for character.
    """
    return _BRIDGE_WS.ws_mysql_error_number != _WS_MYSQL_ERROR_NUMBER_ZERO


def _bridge_cursor() -> Any:
    """Hand out a cursor on the bridge's own connection.

    The positioning verbs are owned by :mod:`acas_posting.dal.cursor_state`,
    which issues the statement itself and therefore takes a cursor rather than a
    connection. That is the boundary the frozen source draws too:
    ``MYSQL-1210-COMMAND`` and ``MYSQL-1220-STORE-RESULT`` live in
    ``mysql-procedures.cpy``, copied in wholesale at
    [common/glbatchMT.cbl:L1035], and the paragraph merely performs them.

    A FRESH CURSOR PER CALL IS SAFE, AND IS NOT A DEPARTURE. The stored result
    the bridge fetches from one record at a time lives in
    ``Ws-Mysql-Result``/``TP-GLBATCH-REC`` [:L280, L498], which is
    WORKING-STORAGE and outlives any one statement;
    :mod:`acas_posting.dal.cursor_state` keeps that snapshot in its own
    ``CursorState`` for the same reason. So a read-next that delivers from the
    snapshot issues no statement and needs no cursor at all.

    A SESSION ANOTHER BRIDGE HAS CLOSED IS NOT THIS CASE, and does not raise.
    ``Ws-Mysql-Cid`` still being null is a caller error the frozen source never
    reaches; a live ``Cid`` whose connection another bridge closed is anomaly
    A-8, which every bridge CAN reach and which the frozen source reports from
    its statement [copybooks/mysql-procedures.cpy:L165-L166].
    ``acquire_cursor`` keeps the two apart by carrying the second to the
    ``execute`` ``cursor_state`` issues.

    Raises:
        BridgeNotOpenError: If ``fn-Open`` has not been performed.
    """
    if _BRIDGE_WS.connection is None:
        raise BridgeNotOpenError(
            f"{BRIDGE} was asked for a statement with Ws-Mysql-Cid still null: "
            f"perform fn-Open (File-Function 1) through "
            f"{HANDLER}.dispatch first"
        )
    return acquire_cursor(_BRIDGE_WS.connection)  # type: ignore[arg-type]


def mt_ba_acas_dal_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba-ACAS-DAL-Process section.`` [common/glbatchMT.cbl:L338-L347].

    The bridge's entry section. Its four statements are screen geometry and
    terminal key handling, verbatim at [:L339-L347]::

        accept   ws-env-lines from lines.
        if       ws-env-lines < 24
                 move  24 to ws-env-lines ws-lines
        else
                 move  ws-env-lines to ws-lines
        end-if
        set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
        set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".

    OMISSION O-4: none of it is reproduced. The Agent Action Plan excludes
    presentation entirely - section 0.3.4 records that the curses screen section
    "is removed rather than reimplemented" - and these four statements have no
    database effect whatsoever: they size a screen this module does not draw and
    arm two keys this module does not read. Recorded rather than dropped
    silently, per rule R-5's "Deliberate omissions are recorded as omissions".

    The section then FALLS THROUGH into ``ba010-Initialise``, which is the
    paragraph order itself - there is no ``go to`` between [:L347] and [:L349].
    Agent Action Plan section 0.4.2 Class 2 does not apply: nothing terminates
    here, so the fall-through is a plain sequential call.

    Args:
        file_access: ``File-Access``, the first bridge parameter.
        dal_common: ``ACAS-DAL-Common-data``, the second.
        batch: ``WS-Batch-Record``, the third.
    """
    # Fall-through into `ba010-Initialise` [common/glbatchMT.cbl:L349].
    mt_ba010_initialise(file_access, dal_common, batch)


def mt_ba010_initialise(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba010-Initialise.`` [common/glbatchMT.cbl:L349-L395].

    Clears the seven text fields and dispatches on ``File-Function``.

    ANOMALY N-nostatus, FIRST HALF - REPRODUCED, NOT FIXED. The two statements
    that would have cleared the caller's status pair are COMMENTED OUT, verbatim
    at [:L351-L352]::

         *>    move     zero   to We-Error
         *>                       Fs-Reply.

    So the bridge NEVER clears ``FS-Reply`` or ``We-Error`` on entry. Only the
    seven text fields are cleared [:L354-L360]::

        move     spaces to WS-MYSQL-Error-Message
                           WS-MYSQL-Error-Number
                           WS-Log-Where
                           WS-File-Key
                           SQL-Msg
                           SQL-Err
                           SQL-State.

    The consequence is load-bearing and shows up in three paragraphs: ``ba080``,
    ``ba085`` and ``ba090`` each jump to ``ba999-End`` from INSIDE their
    row-count test but OUTSIDE their error-number test [:L892], [:L973],
    [:L1019], so a delete or rewrite that matched no row and reported no driver
    error returns THE CALLER'S INCOMING STATUS UNCHANGED. Only ``ba070`` escapes
    it, and only because it zeroes the pair itself first [:L821] - which is why a
    write that inserts no row reports SUCCESS.

    Note also what the clearing does to ``WS-MYSQL-Error-Number``: it is set to
    SPACES here, not to ``"0  "``, so :func:`_errno_is_non_zero` would be true
    before any statement runs. Every paragraph that tests it calls
    ``MySQL_errno`` first [:L827-L828 and siblings], which is why that never
    matters - and it is reproduced faithfully rather than "corrected" to zero.

    THE DISPATCH [:L371-L395] evaluates 1, 2, 3, 4, 5, 6, 7, 8, 9 then
    ``when other``. Every arm is a ``go to``, so each is Agent Action Plan
    section 0.4.2 Class 3 - a transfer out of this paragraph that never returns
    to it - and becomes a call followed by ``return``. The ``end-evaluate.`` at
    [:L395] is followed by ``ba020-Process-Open`` at [:L397], but ``when other``
    covers every remaining value, so that fall-through is unreachable; unlike
    the handler, the bridge has no belt-and-braces ``go to`` after its evaluate.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``.
    """
    logging_data = file_access.logging_data
    # ANOMALY N-nostatus [common/glbatchMT.cbl:L351-L352]: `we_error` and
    # `fs_reply` are DELIBERATELY NOT touched here. Do not add them.
    _BRIDGE_WS.ws_mysql_error_message = ""
    _BRIDGE_WS.ws_mysql_error_number = _pic_x("", _WS_MYSQL_ERROR_NUMBER_WIDTH)
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store("")
    logging_data.ws_file_key = _LOGGING_FIELDS["WS-File-Key"].store("")
    logging_data.sql_msg = _LOGGING_FIELDS["SQL-Msg"].store("")
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store("")
    logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store("")

    function = int(file_access.file_function)
    # `evaluate File-Function` [common/glbatchMT.cbl:L371-L395]. Each arm is a
    # Class 3 transfer: call, then return.
    if function == FileFunction.OPEN:
        mt_ba020_process_open(file_access, dal_common, batch)
        return
    if function == FileFunction.CLOSE:
        mt_ba030_process_close(file_access, dal_common, batch)
        return
    if function == FileFunction.READ_NEXT:
        mt_ba040_process_read_next(file_access, dal_common, batch)
        return
    if function == FileFunction.READ_INDEXED:
        mt_ba050_process_read_indexed(file_access, dal_common, batch)
        return
    if function == FileFunction.WRITE:
        mt_ba070_process_write(file_access, dal_common, batch)
        return
    # `when 6 *> DELETE-ALL Special` [common/glbatchMT.cbl:L385-L386]. THE
    # HANDLER HAS NO SUCH ARM [common/acas007.cbl:L338-L357]; this arm is
    # reachable only because `ba015-Test-Ends` sets the function itself and
    # falls through into a second `call "glbatchMT"` - anomaly N18b.
    if function == FileFunction.DELETE_ALL:
        mt_ba085_process_delete_all(file_access, dal_common, batch)
        return
    # `when 7` BEFORE `when 8` - re-write precedes delete here exactly as it
    # does in the handler [common/glbatchMT.cbl:L387-L390].
    if function == FileFunction.RE_WRITE:
        mt_ba090_process_rewrite(file_access, dal_common, batch)
        return
    if function == FileFunction.DELETE:
        mt_ba080_process_delete(file_access, dal_common, batch)
        return
    if function == FileFunction.START:
        mt_ba060_process_start(file_access, dal_common, batch)
        return
    # `when other go to ba100-Bad-Function` [common/glbatchMT.cbl:L393-L394].
    mt_ba100_bad_function(file_access, dal_common, batch)


def mt_ba020_process_open(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba020-Process-Open.`` [common/glbatchMT.cbl:L397-L439].

    Marshals the six ``RDB-Data`` items into the client library's own fields and
    performs the open, verbatim in shape at [:L402-L427]::

        string   DB-Schema      delimited by space
                 X"00"          delimited by size
                                  into WS-MYSQL-BASE-NAME
        end-string.
        ...
        move     1 to ws-No-Paragraph.
        PERFORM  MYSQL-1000-OPEN  THRU MYSQL-1090-EXIT.

    THE OPEN MODE IS NOT TESTED HERE. ``fn-Input``, ``fn-I-O`` and ``fn-Output``
    all arrive as ``File-Function`` 1 and all open a database connection; the
    handler is where the mode is examined [common/acas007.cbl:L365-L392], and
    ``fn-Output``'s "delete every row" meaning is delivered by the SECOND bridge
    call of anomaly N18b rather than by anything in this paragraph.

    The six ``string ... delimited by space X"00"`` moves and their NUL
    termination are owned by
    :func:`~acas_posting.dal.connection.connection_parameters`, which reproduces
    them item for item including the port narrowing through ``pic x(4)``. This
    paragraph therefore performs the open and does not restate the marshalling -
    duplicating it would give two places for the same six items to drift apart.

    ``if fs-reply not = zero go to ba999-end`` [:L428-L429] is Agent Action Plan
    section 0.4.2 Class 3, and on success [:L437-L439] the log key becomes
    ``"OPEN GLBATCH"`` and the cursor is marked inactive BEFORE the same
    ``go to ba999-end``.

    Args:
        file_access: ``File-Access``; receives the status pair and log fields.
        dal_common: ``ACAS-DAL-Common-data``, forwarded to the logger.
        batch: ``WS-Batch-Record``. Untouched by this paragraph.
    """
    logging_data = file_access.logging_data
    system_record = _HANDLER.linkage_system_record
    if system_record is None:
        raise BridgeCalledOutsideHandlerError(
            f"{BRIDGE} was asked to open with no System-Record resident: "
            f"call {HANDLER}.dispatch, which is the only caller "
            f"[common/acas007.cbl:L640-L645]"
        )

    # `move 1 to ws-No-Paragraph.` [common/glbatchMT.cbl:L426]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba020-Process-Open"]
    )
    # `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT.` [:L427]. The six
    # `RDB-Data` items reach the driver inside it, and `load_rdb_data_once`
    # is the `ba012-Test-WS-Rec-Size-2` first-call copy [common/acas007.cbl:
    # L614-L619] that put them there.
    outcome: OpenOutcome = mysql_1000_open(
        system_record,
        ws_no_paragraph=int(logging_data.ws_no_paragraph),
        we_error=int(file_access.we_error),
        transport=_HANDLER.transport,
        allow_frozen_placeholder_credentials=(
            _HANDLER.allow_frozen_placeholder_credentials
        ),
    )
    mysql_1090_exit(outcome)
    _BRIDGE_WS.connection = outcome.connection
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        outcome.ws_no_paragraph
    )
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(outcome.sql_err)
    _store_sql_msg(logging_data, outcome.sql_msg)
    logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(outcome.sql_state)

    # `if fs-reply not = zero go to ba999-end.` [common/glbatchMT.cbl:L428-L429]
    # - Class 3. The log key is NOT written on this path, so it stays at the
    # spaces `ba010-Initialise` left [:L357].
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        mt_ba999_end(file_access, dal_common, batch)
        return

    # `move "OPEN GLBATCH" to WS-File-Key` [:L437] then
    # `set Cursor-Not-Active to true` [:L438].
    _store_ws_file_key(logging_data, "OPEN GLBATCH")
    cursor_state.reset(TABLE)
    # `go to ba999-end.` [:L439] - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba030-Process-Close.`` [common/glbatchMT.cbl:L441-L454].

    Verbatim [:L442-L454]::

        if      Cursor-Active
                perform ba998-Free.
        move     2 to ws-No-Paragraph.
        move    "CLOSE GLBATCH" to WS-File-Key.
              PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT
        go      to ba999-end.

    ``perform ba998-Free`` is a genuine ``PERFORM``, not a ``go to``, so control
    returns here - one of the few places in this bridge where it does. It frees
    the stored result and sets ``Cursor-Not-Active`` [:L1044-L1048].

    NO ``COMMIT`` AND NO ``ROLLBACK``, here or anywhere else in this module. A
    census of all twenty in-scope bridges finds none, and the connection carries
    the server's ambient autocommit, which ``dal/connection.py`` owns. The
    autocommit-OFF instruction the loaders carry - ``common/glbatchLD.cbl:L9-L13``
    - binds ``harness/seed.sh``, not this module; see the module docstring.

    ``MYSQL-1980-CLOSE`` is performed WHATEVER the state of the handle, and its
    status is not tested afterwards, so a close always reaches ``ba999-end``.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``. Untouched.
    """
    logging_data = file_access.logging_data
    # `if Cursor-Active perform ba998-Free.` [common/glbatchMT.cbl:L442-L443] -
    # a PERFORM, so control comes back.
    mt_ba998_free(file_access, dal_common, batch, only_if_active=True)
    # `move 2 to ws-No-Paragraph.` [:L445]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba030-Process-Close"]
    )
    # `move "CLOSE GLBATCH" to WS-File-Key.` [:L446]
    _store_ws_file_key(logging_data, "CLOSE GLBATCH")
    # `PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT` [:L451]
    mysql_1980_close(_BRIDGE_WS.connection)
    mysql_1999_exit()
    _BRIDGE_WS.connection = None
    # `go to ba999-end.` [:L454] - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba040_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba040-Process-Read-Next.`` [common/glbatchMT.cbl:L456-L529].

    The self-positioning half of ``fn-read-next``. Its whole body is inside
    ``if Cursor-Not-Active`` [:L462], so a walk already in progress skips it and
    goes straight on. When it does run it builds a hard-coded low-key predicate
    with an ``ORDER BY``, verbatim at [:L469-L479]::

        string   "`"                   delimited by size
                 KeyName (KOR-x1)      delimited by space
                 "`"                   delimited by size
                 " >= "                 delimited by size   *> nom uses >  ??
                 '"000000"'         delimited by size
                 ' ORDER BY '          delimited by size
                 "`"                   delimited by size
                 keyname (KOR-x1)      delimited by space
                 "`"                   delimited by size
                   ' ASC '              delimited by size
                                into ws-Where
                                with pointer J

    The maintainer's own inline ``*> nom uses >  ??`` at [:L472] is the record of
    anomaly A9 in :mod:`acas_posting.dal.cursor_state`: this relation and this
    low key are hard-coded PER BRIDGE and the twenty bridges disagree, some
    using ``>`` and some ``>=``. ``glbatchMT`` uses ``>=`` with ``"000000"``, and
    that is data in ``cursor_state.SEQUENTIAL_READ_START`` so the disagreement
    survives as fact rather than as a comment.

    THE ORDERING IS THE CORRECTNESS OF THE POSTING CYCLE. ``ORDER BY`` is the key
    of reference, ascending, one term, no tie-breaker; Agent Action Plan section
    0.6.4 records that perturbing it gives "silent misposting - no error, no
    diagnostic, wrong balances".

    ``move 3 to ws-No-Paragraph`` [:L484] is written here and then OVERWRITTEN
    with 4 by ``ba041-Reread`` [:L536] on every single call, because this
    paragraph FALLS THROUGH into that one - ``end-if.`` at [:L529] is followed
    directly by the paragraph header at [:L531], with no ``go to`` between them.
    Both writes are reproduced in that order so the observable value is the
    bridge's, which is 4.

    :func:`~acas_posting.dal.cursor_state.read_next` owns both stages, because
    the frozen source makes them two halves of one verb and the snapshot they
    share is working storage. It reproduces anomalies A1, A9, A10 and A11 - in
    particular A11, that a FAILED STATEMENT IS REPORTED AS END OF FILE, because
    the two status moves sit inside the zero-rows test but outside the
    error-number test [:L507-L517].

    Args:
        file_access: ``File-Access``; receives the status pair and log fields.
        dal_common: ``ACAS-DAL-Common-data``, forwarded to the logger.
        batch: ``WS-Batch-Record``; a delivered row is unloaded into it.
    """
    logging_data = file_access.logging_data
    state = _BRIDGE_WS.dal_data.state_for(TABLE, cursor_state.CursorSlot.PRIMARY)
    # `if Cursor-Not-Active` [common/glbatchMT.cbl:L462] - the whole
    # self-positioning body is inside it.
    if state.cursor_not_active():
        # `move 3 to ws-No-Paragraph` [:L484], overwritten with 4 by `ba041`.
        logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
            WS_NO_PARAGRAPH_BRIDGE["ba040-Process-Read-Next"]
        )
        _build_where(
            cursor_state.SEQUENTIAL_READ_START[TABLE].relation.padded,
            cursor_state.SEQUENTIAL_READ_START[TABLE].low_key,
        )
    # FALL THROUGH into `ba041-Reread` [:L529 -> :L531]. Not a Class 2 break:
    # nothing terminates here, the next paragraph simply follows.
    mt_ba041_reread(file_access, dal_common, batch)


def mt_ba041_reread(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba041-Reread.`` [common/glbatchMT.cbl:L531-L605].

    The delivering half of ``fn-read-next``: it fetches ONE record from the
    stored result and issues no statement of its own [:L545-L570]. Four exits,
    all Agent Action Plan section 0.4.2 Class 3:

    * ``return-code = -1`` - exhausted: ``move 10 to fs-Reply WE-Error``, log tag
      ``"EOF"``, cursor deactivated [:L572-L577]. ONE statement writes BOTH
      fields, so the pair is ``(10, 10)`` and ``We-Error`` is not left at zero.
    * zero rows with a driver error - ``(10, 10)`` again, log tag ``"EOF2"``, and
      ANOMALY N-initialize [:L579-L593].
    * ``fs-reply = 10`` on entry - the fetched row is DISCARDED, log tag
      ``"EOF3"``, no status written [:L596-L600]. That is anomaly A10 in
      :mod:`acas_posting.dal.cursor_state`: end of file is sticky.
    * delivered - ``perform bb100-UnloadHVs`` then the key into the log field and
      ``move zero to fs-reply WE-Error`` [:L601-L605].

    ANOMALY N-initialize - RECORDED, AND REPRODUCED AT ITS OWN SITE. This
    paragraph clears the record with ``initialize WS-Batch-Record with filler``
    [:L589], the WITH FILLER variant, which blanks ``FILLER`` items too, while
    ``bb100-UnloadHVs`` uses the plain form [:L1106]. TWO INITIALISATION
    SEMANTICS IN ONE BRIDGE. For ``WS-Batch-Record`` the two happen to coincide,
    because [copybooks/wsbatch.cob:L13-L54] declares no ``FILLER`` item anywhere -
    which is exactly why the distinction is recorded and carried as a parameter
    of :func:`_initialize_ws_batch_record` rather than relied upon to be
    harmless. Another record with filler would diverge.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; receives the row on the delivering path.
    """
    logging_data = file_access.logging_data
    state = _BRIDGE_WS.dal_data.state_for(TABLE, cursor_state.CursorSlot.PRIMARY)
    # `move spaces to WS-Log-Where.` [common/glbatchMT.cbl:L535]
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store("")
    # `move 4 to ws-No-Paragraph.` [:L536] - overwrites `ba040`'s 3.
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba041-Reread"]
    )

    # ANOMALY N-countrows-shared - REPRODUCED, NOT FIXED.
    #
    # `if WS-MYSQL-Count-Rows = zero ... set Cursor-Not-Active to true /
    #  go to ba999-End` [common/glbatchMT.cbl:L579-L594].
    #
    # That field is the SINGLE `Ws-Mysql-Count-Rows`
    # [copybooks/mysql-variables.cpy:L73] shared by every verb of this bridge, so
    # the value this test reads need not have come from a select at all. A
    # `ba090-Process-Rewrite` whose UPDATE changed nothing, or a
    # `ba080-Process-Delete` that matched no row, leaves it at zero - and the
    # NEXT `fn-read-next` on a still-live cursor therefore ENDS THE WALK, with no
    # message and, per anomaly N-nostatus, with the caller's own status pair
    # unchanged. `gl072` rewrites each batch record while walking batches
    # [general/gl072.cbl:L373-L377], so this is reachable in the posting cycle,
    # not a theoretical path.
    #
    # WHY THE TEST IS BEFORE THE FETCH HERE AND AFTER IT THERE. In the frozen
    # paragraph the fetch [:L545-L570] runs first and this test then discards its
    # result. The fetch's ONLY effect on this path is to advance the stored
    # result by one record - and `set Cursor-Not-Active to true` [:L592]
    # immediately abandons that stored result, so the next call self-positions
    # from `"000000"` regardless of where it had advanced to. Testing first is
    # therefore observably identical, and it is the only ordering available,
    # because the snapshot belongs to `cursor_state` and cannot be advanced
    # without also delivering.
    if state.cursor_active() and _BRIDGE_WS.ws_mysql_count_rows == 0:
        _record_driver_error(None)
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        # `if WS-MYSQL-Error-Number not = "0  "` [:L583-L591]. Nothing failed at
        # the driver on this path - the count is stale, not erroneous - so the
        # inner block is skipped and NO STATUS IS WRITTEN. That is the whole
        # defect: `fs_reply` and `we_error` keep the caller's incoming values.
        if _errno_is_non_zero():  # pragma: no cover - stale count, never errno
            # `move 10 to fs-reply *> EOF equivilent !!` / `move 10 to WE-Error`
            # [common/glbatchMT.cbl:L585-L586]. Ten in BOTH fields, and 10 is not
            # one of the named `We-Error` codes - `end_of_file_status` is the one
            # place that pair is written, for exactly this reason.
            eof_fs_reply, eof_we_error = end_of_file_status()
            file_access.fs_reply = int(eof_fs_reply)
            file_access.we_error = int(eof_we_error)
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
            # ANOMALY N-initialize [common/glbatchMT.cbl:L589]: the WITH FILLER
            # variant, where `bb100-UnloadHVs` uses the plain form [:L1106].
            _initialize_ws_batch_record(batch, with_filler=True)
            _store_ws_file_key(logging_data, "EOF2")
        # `set Cursor-Not-Active to true` [:L592] - a bare deactivation, NOT
        # `ba998-Free`, so the stored result stays allocated. That leak is the
        # frozen source's and is reproduced by discarding the snapshot without
        # freeing it.
        state.set_cursor_not_active()
        #  SILENT. [common/glbatchMT.cbl:L579-L594] writes no status and displays
        #  nothing: the caller's incoming pair survives per [:L351-L352], and a walk
        #  that a previous WRITE verb quietly ended looks to the caller exactly like
        #  an empty table. That indistinguishability is the anomaly, and reporting it
        #  would be a diagnostic the compiled program cannot produce (rule R-4).
        # `go to ba999-End` [:L593] - Class 3.
        mt_ba999_end(file_access, dal_common, batch)
        return

    # `move zero to return-code.` [:L538] then the fetch [:L545-L570], the
    # `return-code = -1` exhaustion test [:L572-L577] and the sticky
    # `fs-reply = 10` discard [:L596-L600] - all owned by `cursor_state`, which
    # also owns the stored result the fetch draws from.
    cursor = _bridge_cursor()
    try:
        outcome = cursor_state.read_next(
            cursor,
            TABLE,
            slot=cursor_state.CursorSlot.PRIMARY,
            states=_BRIDGE_WS.dal_data,
            file_access=file_access,
        )
    finally:
        cursor.close()
    # `MYSQL-1220-STORE-RESULT` wrote the count during any self-positioning this
    # call performed; the live cursor's own count is that value, and taking it
    # from there keeps the shared field and the snapshot in step.
    _BRIDGE_WS.ws_mysql_count_rows = state.count_rows

    if outcome.row is None:
        # `"EOF"` [:L574] or `"EOF3"` [:L598] - both Class 3 exits to
        # `ba999-End` [:L576], [:L599].
        mt_ba999_end(file_access, dal_common, batch)
        return

    # `perform bb100-UnloadHVs.` [:L601] - a PERFORM, so control returns.
    bb100_unload_hvs(outcome.row, batch)
    # `move HV-BATCH-KEY to WS-File-Key.` [:L603] and `move zero to fs-reply
    # WE-Error.` [:L604] are both applied by the outcome before it is returned.
    # `go to ba999-end.` [:L605] - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba050_process_read_indexed(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba050-Process-Read-Indexed.`` [common/glbatchMT.cbl:L607-L712].

    An equality read on the key of reference, verbatim at [:L618-L627]::

        string   "`"                   delimited by size
                 KeyName (KOR-x1)      delimited by space
                 "`"                   delimited by size
                 '="'                  delimited by size
                 WS-Batch-Record (K:L)  delimited by size
        *>             BATCH-KEY
                 '"'                   delimited by size
                         into WS-Where
                           with pointer J

    THE KEY VALUE IS A RAW CHARACTER SUBSTRING OF THE RECORD BUFFER -
    ``WS-Batch-Record (K:L)``, offset 1 length 6 - and it is compared as a
    DOUBLE-QUOTED STRING against a ``mediumint(6) unsigned`` column, letting the
    database coerce. :func:`batch_key_image` produces exactly those six
    characters and the value is bound rather than pasted; see the module
    docstring.

    ``move 5 to ws-No-Paragraph`` [:L632] then ``move 6`` [:L653] between the
    select and the fetch, so the observable value after a successful read is 6.

    ANOMALY A13 in :mod:`acas_posting.dal.cursor_state`: the ``We-Error`` 990 and
    989 branches at [:L690-L705] are UNREACHABLE, because the earlier
    ``if WS-MYSQL-Count-Rows = zero move 21 to fs-Reply go to ba998-Free``
    [:L649-L652] has already taken every zero-row case away. Both are carried as
    documented dead code there rather than deleted.

    EVERY EXIT FREES THE CURSOR - each is ``go to ba998-Free`` [:L651], [:L697],
    [:L704], [:L712] - so an indexed read taken in the middle of a sequential
    walk DESTROYS the walk's position. ``gl070`` and ``gl072`` both walk batches
    while reading other tables by key, so this matters and is reproduced.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies the key and receives the row.
    """
    logging_data = file_access.logging_data
    # The key is the six bytes at offset 1, read through the `WS-Batch-Key9`
    # REDEFINES so both views agree before the statement is built.
    synchronise_batch_key_views(batch)
    key_value = batch_key_image(batch)
    # `move 5 to ws-No-Paragraph` [common/glbatchMT.cbl:L632] before the select.
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba050-Process-Read-Indexed"]
    )
    _build_where("=  ", key_value)
    cursor = _bridge_cursor()
    try:
        outcome = cursor_state.read_indexed(
            cursor,
            TABLE,
            key_value,
            key_number=FILE_KEY_NO_REQUIRED,
            slot=cursor_state.CursorSlot.PRIMARY,
            states=_BRIDGE_WS.dal_data,
            file_access=file_access,
        )
    finally:
        cursor.close()
    # `move 6 to ws-No-Paragraph` [:L653], between the select and the fetch.
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba050-Process-Read-Indexed-fetch"]
    )
    _BRIDGE_WS.ws_mysql_count_rows = 0 if outcome.row is None else 1

    if outcome.row is not None:
        # `perform bb100-UnloadHVs` [:L707] then the key into the log field
        # [:L708-L709] and `move zero to FS-Reply WE-Error` [:L711], all applied
        # by the outcome.
        bb100_unload_hvs(outcome.row, batch)
    # `go to ba998-Free.` [:L712] - Class 3. `cursor_state.read_indexed` has
    # already freed the stored result on every path, so this reproduces the
    # paragraph number write and the fall-through into `ba999-end` that follows
    # it [:L1038-L1050].
    mt_ba998_free(file_access, dal_common, batch, only_if_active=False)
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba060_process_start(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba060-Process-Start.`` [common/glbatchMT.cbl:L714-L817].

    Positions the cursor and fetches nothing.

    THE RELATION ARRIVES THROUGH ``Access-Type``, BY DESIGN. Every facade verb
    clears that field before dispatching EXCEPT ``-Start``, and the copybook's
    own changelog records the deliberate change
    [copybooks/Proc-ACAS-FH-Calls.cob:L18]::

        *> 14/08/23 vbc - 1.08 - Remove 'move zero to access-type for Start, it is set !!!

    So the caller's access type IS the relation, and it is passed through
    unmodified.

    ANOMALY A5 / N-start-dead-arm - REPRODUCED, NOT FIXED. The guard is
    ``if access-type < 5 or > 8`` [:L718-L722], with the maintainer's own
    ``*> not using not < or not >`` beside it, and it yields ``(99, 997)``. It
    admits 5, 6, 7 and 8 ONLY - so the ``when 9 move "<= " to MOST-Relation``
    arm of the relation ``evaluate`` immediately below [:L747-L748] is
    UNREACHABLE DEAD CODE, and the ``[ not currently used in ACAS ]`` comment the
    maintainer wrote against it is an understatement: it cannot be used at all.

    ANOMALY N-relation-nodefault - REPRODUCED, NOT FIXED. That ``evaluate`` has
    NO ``when other`` [:L738-L749], so an access type the guard let through with
    no arm would leave ``MOST-Relation`` at the ``move spaces`` of [:L736] and
    produce a malformed predicate. The guard makes it unreachable HERE, but the
    same relation table drives ``ba085``'s ``<`` and the ``.scb``'s own
    generator, so the behaviour is carried in :func:`_build_where` rather than
    defaulted away.

    ANOMALY N-start-code-divergence. Three readings of a bad start parameter
    coexist: this paragraph writes ``(99, 997)`` [:L719-L720]; the handler's own
    ``aa060-Process-Start`` writes 998 to ``We-Error`` and NEVER TOUCHES
    ``FS-Reply`` [common/acas007.cbl:L472-L475]; and the handler's header
    comment documents 997 for it [:L155]. All three are recorded; each site
    reproduces its own.

    ``move 8 to ws-No-Paragraph`` [:L773] is the only paragraph number this verb
    writes.

    :func:`~acas_posting.dal.cursor_state.start` owns the statement, the guard,
    the relation table and the ``(21, 0)`` status of a failed statement.

    Args:
        file_access: ``File-Access``; ``access_type`` carries the relation.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies the key. NOT written - a start
            fetches nothing.
    """
    logging_data = file_access.logging_data
    access_type = int(file_access.access_type)
    # `if access-type < 5 or > 8 move 99 to FS-Reply / move 997 to WE-Error /
    # go to ba999-end` [common/glbatchMT.cbl:L718-L722] - Class 3. Reproduced
    # here as well as inside `cursor_state.start`, because this paragraph's
    # exit is `ba999-end` and therefore LOGS, where `cursor_state` returns an
    # outcome; the status pair the two produce is identical.
    lower, upper = START_ACCESS_TYPE_RANGE
    if access_type < lower or access_type > upper:
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba060-Process-Start",
            locator="[common/glbatchMT.cbl:L718-L722]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            detail="Access-Type %d rejected for %s; the guard admits %d..%d "
            "only, which is why the when 9 arm at [:L747] is dead code"
            % (access_type, TABLE, lower, upper),
        )
        mt_ba999_end(file_access, dal_common, batch)
        return

    synchronise_batch_key_views(batch)
    key_value = batch_key_image(batch)
    # `move spaces to MOST-Relation.` [:L736] then the `evaluate` [:L738-L749].
    relation = START_RELATION_BY_ACCESS_TYPE.get(access_type, MOST_RELATION_DEFAULT)
    _build_where(relation, key_value)
    # `move 8 to ws-No-Paragraph` [:L773]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba060-Process-Start"]
    )
    cursor = _bridge_cursor()
    try:
        #  The return value is deliberately not bound: `cursor_state.start` applies
        #  the status pair to `file_access` itself, which is where the frozen bridge
        #  leaves it, and nothing downstream in this paragraph reads the outcome
        #  object. It was bound only to be interpolated into a per-row trace that no
        #  longer exists.
        cursor_state.start(
            cursor,
            TABLE,
            key_value,
            access_type,
            key_number=FILE_KEY_NO_REQUIRED,
            slot=cursor_state.CursorSlot.PRIMARY,
            states=_BRIDGE_WS.dal_data,
            file_access=file_access,
        )
    finally:
        cursor.close()
    # `WS-MYSQL-Count-Rows` is left exactly as `MYSQL-1220-STORE-RESULT` set it
    # [common/glbatchMT.cbl:L779-L784]; it is the snapshot's row count, owned by
    # `cursor_state` along with the snapshot itself, and no write-side paragraph
    # reads it across a verb boundary. Shadowing it here would give the count two
    # homes and let them disagree.
    #  NO RECORD FOR A SUCCESSFUL POSITIONING. The frozen paragraph displays
    #  nothing on its success path, and a per-row trace of a batch walk is exactly
    #  the kind of invented event rule R-4 excludes - it would also be the highest
    #  volume record in the whole cycle. The status pair is returned to the caller,
    #  which is where the frozen source leaves it.
    # `go to ba999-end` on every path out of this paragraph - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


#: The value ``Ws-Mysql-Count-Rows`` holds after a FAILED statement. ANOMALY
#: N-affected-rows-int32, established by executing a probe against cobc 3.2
#: rather than by reasoning, and by reading the frozen C shim:
#:
#: * ``Mysql-1210-Command`` calls ``MySQL_affected_rows`` UNCONDITIONALLY, after
#:   the error path as well as the success path
#:   [copybooks/mysql-procedures.cpy:L176-L178].
#: * The shim is ``void MySQL_affected_rows(int *no) { *no =
#:   mysql_affected_rows(mysql); }`` - it writes FOUR bytes into a field declared
#:   ``binary-double unsigned``, eight bytes
#:   [copybooks/mysql-variables.cpy:L73], so the high four are never written and
#:   stay zero. ``mysql_affected_rows`` returns ``(my_ulonglong)-1`` on error.
#: * A probe compiled with the harness's own cobc 3.2 shows ``binary-double
#:   unsigned`` is NATIVE byte order on this platform - ``1`` lays out as
#:   ``01 00 00 00 00 00 00 00`` - and that a field whose low four bytes are
#:   ``FF FF FF FF`` and whose high four are zero reads as 4294967295.
#:
#: So the field is effectively an unsigned 32-bit view of the affected-row count.
#: It matters in exactly one paragraph: ``ba085-Process-Delete-ALL`` tests
#: ``not > zero`` [common/glbatchMT.cbl:L962] rather than ``not = 1``, and
#: 4294967295 IS greater than zero - so a FAILED DELETE-ALL skips the error block
#: and reports ``(0, 0)``. See :func:`mt_ba085_process_delete_all`.
AFFECTED_ROWS_ON_FAILURE: Final[int] = 0xFFFFFFFF


def _mysql_1210_command(
    file_access: FileAccess,
    statement: str,
    parameters: Sequence[object],
    *,
    file_function: int,
) -> BaseException | None:
    """``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``.

    The paragraph, verbatim [copybooks/mysql-procedures.cpy:L164-L181]::

        Mysql-1210-Command.
            call     "MySQL_query" using WS-Mysql-Command.
            if       Return-Code not = zero
                     perform Mysql-1100-Db-Error Thru Mysql-1190-Exit
            end-if
            call     "MySQL_affected_rows" using WS-Mysql-Count-Rows.

        Mysql-1219-Exit.     *> on return test for WE-Error = 910
            exit.

    THREE PROPERTIES ARE LOAD-BEARING AND ALL THREE ARE REPRODUCED:

    1. ``Mysql-1100-Db-Error`` writes ``(99, 911)`` for every non-duplicate
       failure and there is NO ``go to`` after it, so control continues.
       :func:`~acas_posting.dal.status.mysql_1100_db_error` owns that, and
       :func:`~acas_posting.dal.status.override_we_error_for_operation` applies
       the per-verb narrowing that ``ba080`` and ``ba090`` write afterwards.
    2. ``MySQL_affected_rows`` is called on BOTH paths, so a failure leaves
       :data:`AFFECTED_ROWS_ON_FAILURE` in the count rather than zero - anomaly
       N-affected-rows-int32.
    3. The lock-retry ladder above it is COMMENTED OUT [:L167-L175], so there is
       no retry and no ``We-Error`` 910 path. ``dal/status.py`` carries that
       ladder as documented dead code; nothing here retries.

    Args:
        file_access: ``File-Access``; receives the failure status and text
            fields, exactly as ``Mysql-1100-Db-Error`` writes them.
        statement: The statement, identifiers already backtick-quoted.
        parameters: The values to bind, in the statement's order.
        file_function: The verb, for the ``We-Error`` narrowing.

    Returns:
        ``None`` when the statement succeeded, or the driver's exception when it
        did not - which is what the later ``MySQL_errno`` calls read.
    """
    connection = _BRIDGE_WS.connection
    if connection is None:
        raise BridgeNotOpenError(
            f"{BRIDGE} was asked to issue {statement.split(' ', 1)[0]} with "
            f"Ws-Mysql-Cid still null: perform fn-Open (File-Function 1) "
            f"through {HANDLER}.dispatch first"
        )
    logging_data = file_access.logging_data
    # `move WS-Where (1:J) to WS-Log-Where` is written by the calling paragraph;
    # the statement itself is what the log record carries.
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            # `call "MySQL_affected_rows" using WS-Mysql-Count-Rows.` [:L178]
            row_count = cursor.rowcount
        _BRIDGE_WS.ws_mysql_count_rows = (
            AFFECTED_ROWS_ON_FAILURE
            if row_count is None or row_count < 0
            else int(row_count)
        )
        _record_driver_error(None)
        return None
    except Exception as error:  # any driver error takes this path - see below
        # `if Return-Code not = zero perform Mysql-1100-Db-Error` [:L166-L177].
        # Catching every exception rather than one driver type reproduces the
        # bridge's own "any non-zero return takes this path" behaviour, and is
        # what `dal/cursor_state.py` does at its three equivalent sites.
        _record_driver_error(error)
        status: DbErrorStatus = mysql_1100_db_error(
            errno=_BRIDGE_WS.ws_mysql_error_number.strip(),
            message=_BRIDGE_WS.ws_mysql_error_message,
            sql_state=_BRIDGE_WS.ws_mysql_sqlstate.strip(),
            command=statement,
            we_error=int(file_access.we_error),
        )
        status = override_we_error_for_operation(status, file_function)
        file_access.fs_reply = int(status.fs_reply)
        file_access.we_error = int(status.we_error)
        logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(status.sql_err)
        _store_sql_msg(logging_data, status.sql_msg)
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(status.sql_state)
        # ANOMALY N-affected-rows-int32 [copybooks/mysql-procedures.cpy:L178]:
        # the affected-row call happens on this path too, and the C shim's
        # `int *` narrowing of -1 leaves 4294967295 here, NOT zero.
        _BRIDGE_WS.ws_mysql_count_rows = AFFECTED_ROWS_ON_FAILURE
        return error


def mt_ba070_process_write(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba070-Process-Write.`` [common/glbatchMT.cbl:L818-L843].

    Verbatim [:L819-L843]::

        perform  bb000-HV-Load.
        move     ws-BATCH-KEY to WS-File-Key.
        move     zero to FS-Reply WE-Error SQL-State.
        move     spaces to SQL-Msg
        move     zero to SQL-Err
        move     10 to ws-No-Paragraph.
        perform  bb200-Insert.
        if       WS-MYSQL-COUNT-ROWS not = 1
                 call  "MySQL_errno" using WS-MYSQL-Error-Number
                 call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
                 move  WS-MYSQL-SqlState   to SQL-State
                 if    WS-MYSQL-Error-Number  not = "0  "
                       call "MySQL_error" using Ws-Mysql-Error-Message
                       move WS-MYSQL-Error-Number  to SQL-Err
                       move WS-MYSQL-Error-Message to SQL-Msg
                       if    SQL-Err (1:4) = "1062"
                                        or = "1022"   *> Dup key (rec already present)
                           or Sql-State = "23000"  *> Dup key (rec already present)
                             move 22 to fs-reply
                       else
                             move 99 to fs-reply
                       end-if
                 end-if
        end-if.
        go       to ba999-End.

    THIS IS THE ONE WRITE-SIDE PARAGRAPH THAT ESCAPES ANOMALY N-nostatus, and
    only because it zeroes the status pair ITSELF at [:L821] - the clearing
    ``ba010-Initialise`` would have done is commented out [:L351-L352]. The
    escape is partial and produces its own defect: because the inner
    error-number test is what decides a status, an INSERT THAT AFFECTED NO ROW
    AND REPORTED NO ERROR REPORTS SUCCESS, ``(0, 0)``, having written nothing.

    ``We-Error`` IS NOT WRITTEN BY THIS PARAGRAPH AT ALL on the failure path -
    only ``fs-reply`` is [:L837], [:L839] - so it keeps whatever
    ``Mysql-1100-Db-Error`` left, which is 911. That is why
    :func:`_mysql_1210_command` is passed ``FileFunction.WRITE``, for which
    :func:`~acas_posting.dal.status.override_we_error_for_operation` deliberately
    has no override.

    The duplicate-key test is the BRIDGE-LEVEL one -
    :func:`~acas_posting.dal.status.is_duplicate_key_bridge_level` - which tests
    ``SQL-Err (1:4)`` against ``"1062"`` and ``"1022"`` OR ``Sql-State`` against
    ``"23000"``, and is a different test from the driver-level one inside
    ``Mysql-1100-Db-Error``. Both are applied, in that order, as the frozen
    source applies them.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies every column. Not modified.
    """
    logging_data = file_access.logging_data
    # `perform bb000-HV-Load.` [common/glbatchMT.cbl:L819]
    synchronise_batch_key_views(batch)
    bb000_hv_load(batch)
    # `move ws-BATCH-KEY to WS-File-Key.` [:L820]
    _store_ws_file_key(logging_data, batch_key_image(batch))
    # `move zero to FS-Reply WE-Error SQL-State.` [:L821] - the self-clearing
    # that no other write-side paragraph has.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(_SQL_ERR_ZERO)
    # `move spaces to SQL-Msg` [:L822] and `move zero to SQL-Err` [:L823]
    _store_sql_msg(logging_data, "")
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(_SQL_ERR_ZERO)
    # `move 10 to ws-No-Paragraph.` [:L824]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba070-Process-Write"]
    )
    # `perform bb200-Insert.` [:L825]
    statement, parameters = mt_bb200_insert()
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store(statement)
    _mysql_1210_command(
        file_access, statement, parameters, file_function=FileFunction.WRITE
    )

    # `if WS-MYSQL-COUNT-ROWS not = 1` [:L826]
    if _BRIDGE_WS.ws_mysql_count_rows != 1:
        # `call "MySQL_sqlstate"` then `move WS-MYSQL-SqlState to SQL-State`
        # [:L828-L829] - written whether or not the error number is set.
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        # `if WS-MYSQL-Error-Number not = "0  "` [:L830]
        if _errno_is_non_zero():
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
            # `if SQL-Err (1:4) = "1062" or = "1022" or Sql-State = "23000"`
            # [:L834-L840]. `We-Error` is NOT touched on either arm, so it keeps
            # `Mysql-1100-Db-Error`'s 911.
            if is_duplicate_key_bridge_level(
                str(logging_data.sql_err), str(logging_data.sql_state)
            ):
                file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
            else:
                file_access.fs_reply = int(FsReply.ERROR)
        else:
            # THE DEFECT: no error and no row, so nothing is written and the
            # status pair stays at the `(0, 0)` of [:L821]. A write that
            # inserted nothing reports success. Reproduced, not fixed (R-4).
            #  SILENT: [common/glbatchMT.cbl:L821-L842] displays nothing, so a
            #  write that inserted nothing reports success and says so to nobody.
            #  Reproduced, not reported (rule R-4).
            pass
    # `go to ba999-End.` [:L843] - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba080_process_delete(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba080-Process-Delete.`` [common/glbatchMT.cbl:L845-L898].

    Deletes the one row the key of reference selects. The predicate is built
    exactly as ``ba050``'s is, from the six-character substring of the record
    buffer [:L853-L861], and the log key is that same substring [:L862].

    ANOMALY N-nostatus, SECOND HALF - REPRODUCED, NOT FIXED. The structure is
    verbatim [:L881-L898]::

        if       WS-MYSQL-COUNT-ROWS not = 1
                 call  "MySQL_errno" using WS-MYSQL-Error-Number
                 ...
                 if    WS-MYSQL-Error-Number  not = "0  "
                       ...
                       move 99 to fs-reply
                       move 995 to WE-Error
                 end-if
                 go to ba999-End                        *> and log it
        else
                 move spaces to SQL-Msg
                 move zero   to SQL-Err
        end-if.
        move     zero to FS-Reply WE-Error.
        go       to ba999-End.

    The ``go to ba999-End`` at [:L892] is INSIDE the row-count test and OUTSIDE
    the error-number test, and ``move zero to FS-Reply WE-Error`` at [:L897] is
    reachable ONLY through the ``else``. So a DELETE that matched no row and
    reported no driver error returns THE CALLER'S INCOMING STATUS PAIR
    UNCHANGED - not success, not failure, whatever the caller happened to be
    carrying - because ``ba010-Initialise`` never cleared it [:L351-L352].

    ``move 995 to WE-Error`` [:L890] is the per-verb narrowing of
    ``Mysql-1100-Db-Error``'s 911, applied here in
    :func:`_mysql_1210_command` through
    :func:`~acas_posting.dal.status.override_we_error_for_operation`, which is
    two-stage precisely because the frozen source is.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies the key. Not modified - a delete
            leaves the caller's record alone.
    """
    logging_data = file_access.logging_data
    synchronise_batch_key_views(batch)
    key_value = batch_key_image(batch)
    # `string ... '="' ... WS-Batch-Record (K:L) ... '"'` [:L853-L861]
    clause = _build_where("=  ", key_value)
    # `move WS-Batch-Record (K:L) to WS-File-Key.` [:L862]
    _store_ws_file_key(logging_data, key_value)
    # `move WS-Where (1:J) to WS-Log-Where.` [:L863]
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store(clause)
    # `move 13 to ws-No-Paragraph.` [:L867]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba080-Process-Delete"]
    )
    # `STRING "DELETE FROM " "`GLBATCH-REC`" " WHERE " WS-Where (1:J) X"00"`
    # [:L873-L878]. No trailing semicolon on this one, unlike `bb200-Insert`.
    statement = f"DELETE FROM {_QUOTED_TABLE} WHERE {clause}"
    _mysql_1210_command(
        file_access, statement, (key_value,), file_function=FileFunction.DELETE
    )

    # `if WS-MYSQL-COUNT-ROWS not = 1` [:L881]
    if _BRIDGE_WS.ws_mysql_count_rows != 1:
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        if _errno_is_non_zero():
            # `move 99 to fs-reply` / `move 995 to WE-Error` [:L889-L890], both
            # already applied by `_mysql_1210_command`'s narrowing. Restated so
            # the status is this paragraph's whatever the generic path left.
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
        else:
            # ANOMALY N-nostatus [common/glbatchMT.cbl:L892]: the jump is here,
            # inside the count test and outside the errno test, so the pair the
            # caller arrived with survives untouched. Do NOT write a status.
            #  SILENT, for the same reason as `fn-write` above: the count test sits
            #  inside the errno test's shadow and [:L892] writes nothing, so the
            #  caller's incoming pair survives untouched and undiagnosed (rule R-4).
            pass
        # `go to ba999-End` [:L892] - Class 3.
        mt_ba999_end(file_access, dal_common, batch)
        return

    # The `else` [:L893-L895]: `move spaces to SQL-Msg` / `move zero to SQL-Err`.
    _store_sql_msg(logging_data, "")
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(_SQL_ERR_ZERO)
    # `move zero to FS-Reply WE-Error.` [:L897] - reachable only through the
    # `else`, which is the whole of anomaly N-nostatus.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `go to ba999-End.` [:L898] - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba085_process_delete_all(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba085-Process-Delete-ALL.`` [common/glbatchMT.cbl:L900-L979].

    The paragraph the maintainer labelled ``*> THIS IS NON STANDARD`` [:L900],
    and the second of the two bridge invocations anomaly N18b produces. It is
    reachable ONLY through the bridge's own ``when 6`` arm [:L385-L386], which
    the handler's ``evaluate`` has no counterpart for.

    ANOMALY N-deleteall-999999 - REPRODUCED, NOT FIXED. This is not a bare
    ``DELETE FROM``. It moves a high key into the record and deletes STRICTLY
    BELOW it [:L922-L938]::

        move     999999  to ws-BATCH-KEY.         *> as its the last posting
        ...
        string   "`"                   delimited by size
                 KeyName (KOR-x1)      delimited by space
                 "`"                   delimited by size
                 '<"'                  delimited by size
                 WS-Batch-Record (K:L)    delimited by size
                 '"'                   delimited by size

    The relation is ``<``, so A ROW KEYED EXACTLY 999999 SURVIVES A "DELETE
    ALL". Since ``BATCH-KEY`` is one ledger digit plus five batch digits
    [copybooks/wsbatch.cob:L15-L19], 999999 is ledger 9 batch 99999 - not a
    valid ledger, so in practice nothing survives; the defect is nonetheless
    real and is preserved rather than turned into an unconditional delete.

    ANOMALY N-affected-rows-int32 - REPRODUCED, NOT FIXED, AND IT BITES HERE.
    The guard is ``not > zero`` [:L962], with the maintainer's own
    ``*> Changed for delete-ALL`` beside it, rather than the ``not = 1`` its
    siblings use. Because a failed statement leaves
    :data:`AFFECTED_ROWS_ON_FAILURE` in the count rather than zero - see that
    constant for the C shim and the compiled probe that establish it - the guard
    is FALSE after a failure, control takes the ``else`` at [:L974] whose comment
    reads ``*> of course there could be no data in table``, and [:L978] then
    reports ``(0, 0)``. **A FAILED DELETE-ALL REPORTS COMPLETE SUCCESS.**

    Also note the ``995`` at [:L971]: it is written INLINE here, and
    :func:`~acas_posting.dal.status.override_we_error_for_operation` maps only
    ``fn-Delete`` and ``fn-Re-Write``, so ``fn-Delete-All`` keeps 911 from the
    generic paragraph and this paragraph's own store is what makes it 995.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; ITS KEY IS OVERWRITTEN with the high key,
            exactly as [:L922] overwrites it. That is a real side effect on the
            caller's record and is preserved.
    """
    logging_data = file_access.logging_data
    # `move 999999 to ws-BATCH-KEY.` [:L922]. The literal goes into the GROUP
    # `WS-Batch-Key`, so the six bytes become the characters "999999" and BOTH
    # readings of the REDEFINES pair change at once
    # [copybooks/wsbatch.cob:L14-L21] - there is one storage, and a MOVE into it
    # OVERWRITES whatever either reading held.
    #
    # `synchronise_batch_key_views` is deliberately NOT used here. It reconciles
    # two readings that MAY disagree and raises when both are non-default and
    # differ; a MOVE never compares, so routing this store through it would
    # manufacture a failure for any caller that arrived holding a key - and
    # `ba010-Initialise` reaches this paragraph with exactly the caller's own
    # record [:L343-L346]. Both readings are therefore assigned directly, from
    # the one value the descriptor stored.
    high_key = int(_RECORD_FIELDS[_KEY_DICTIONARY_KEY].store(int(DELETE_ALL_HIGH_KEY)))
    batch.ws_batch_key9.ws_batch_key9 = high_key
    batch.ws_batch_key.ws_ledger = high_key // _LEDGER_DIGIT_SCALE
    batch.ws_batch_key.ws_batch_nos = high_key % _LEDGER_DIGIT_SCALE
    key_value = batch_key_image(batch)
    # `'<"'` [:L933] - STRICTLY LESS THAN, not `<=`, not unconditional.
    clause = _build_where("<  ", key_value)
    # `move spaces to WS-File-Key` then `string "Deleting back from " ws-BATCH-KEY`
    # [:L939-L943].
    _store_ws_file_key(logging_data, f"Deleting back from {key_value}")
    # `move WS-Where (1:J) to WS-Log-Where.` [:L944]
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store(clause)
    # `move 15 to ws-No-Paragraph.` [:L948]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba085-Process-Delete-ALL"]
    )
    statement = f"DELETE FROM {_QUOTED_TABLE} WHERE {clause}"
    _mysql_1210_command(
        file_access, statement, (key_value,), file_function=FileFunction.DELETE_ALL
    )

    # `if WS-MYSQL-COUNT-ROWS not > zero *> Changed for delete-ALL` [:L962].
    if not _BRIDGE_WS.ws_mysql_count_rows > 0:
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        if _errno_is_non_zero():
            # `move 99 to fs-reply` / `move 995 to WE-Error` [:L970-L971],
            # written inline because verb 6 has no generic override.
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
        # `go to ba999-End` [:L973] - Class 3, inside the count test and outside
        # the errno test, so an empty table returns the caller's incoming pair.
        mt_ba999_end(file_access, dal_common, batch)
        return

    # The `else *> of course there could be no data in table` [:L974-L976] -
    # AND, per anomaly N-affected-rows-int32, the path a FAILED delete-all takes.
    if _errno_is_non_zero():
        #  SILENT, AND THAT IS THE WHOLE OF ANOMALY N-affected-rows-int32: a
        #  delete-all that FAILED at the driver reports success, because
        #  `MySQL_affected_rows` narrowed -1 through an int, the `not > zero` guard
        #  at [common/glbatchMT.cbl:L962] is therefore false, and [:L978] zeroes the
        #  status. Nothing is displayed. A record here would tell an operator what
        #  the compiled program refuses to tell them, which is precisely the defect
        #  rule R-4 requires be reproduced rather than repaired.
        pass
    _store_sql_msg(logging_data, "")
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(_SQL_ERR_ZERO)
    # `move zero to FS-Reply WE-Error.` [:L978]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `go to ba999-End.` [:L979] - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba090_process_rewrite(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba090-Process-Rewrite.`` [common/glbatchMT.cbl:L981-L1024].

    Loads the host variables, builds the same equality predicate ``ba050`` and
    ``ba080`` build, and performs ``bb300-Update`` [:L983-L1002]. The paragraph
    number 17 is written BEFORE the predicate here [:L985], where ``ba080``
    writes 13 after it - the two paragraphs are not mirror images and are not
    made into mirror images.

    ANOMALY N-nostatus, THIRD HALF. Same shape as ``ba080``: the
    ``go to ba999-End`` at [:L1019] is inside the row-count test and outside the
    error-number test, so A REWRITE THAT CHANGED NOTHING RETURNS THE CALLER'S
    INCOMING STATUS. MySQL reports zero affected rows for an ``UPDATE`` whose
    values all match what is already stored, and ``CLIENT_FOUND_ROWS`` is not
    set on the connection, so this is reachable whenever a caller rewrites a
    record it did not modify. ``gl072`` rewrites every batch it posts
    [general/gl072.cbl:L373-L377].

    That same zero then persists in ``Ws-Mysql-Count-Rows`` and ends the NEXT
    sequential walk - anomaly N-countrows-shared, reproduced in
    :func:`mt_ba041_reread`.

    ``move 994 to WE-Error`` [:L1017] is the per-verb narrowing, applied through
    :func:`~acas_posting.dal.status.override_we_error_for_operation` with
    ``FileFunction.RE_WRITE``.

    On success the paragraph clears more than ``ba080`` does - ``move zero to
    FS-Reply WE-Error`` [:L1021], ``move zero to SQL-Err`` [:L1022] and
    ``move spaces to SQL-Msg`` [:L1023] - and those three statements are OUTSIDE
    the ``end-if``, not in an ``else``, which is the structural difference from
    ``ba080``. It makes no observable difference, because the only way to reach
    them is for the count test to have been false; it is preserved as written.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies every column and the key.
    """
    logging_data = file_access.logging_data
    # `perform bb000-HV-Load.` [:L983]
    synchronise_batch_key_views(batch)
    bb000_hv_load(batch)
    key_value = batch_key_image(batch)
    # `move ws-BATCH-KEY to WS-File-Key.` [:L984]
    _store_ws_file_key(logging_data, key_value)
    # `move 17 to ws-No-Paragraph.` [:L985] - BEFORE the predicate here.
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba090-Process-Rewrite"]
    )
    # `string ... '="' ... WS-Batch-Record (K:L) ... '"'` [:L992-L1000]
    clause = _build_where("=  ", key_value)
    # `move WS-Where (1:J) to WS-Log-Where.` [:L1001]
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store(clause)
    # `perform bb300-Update.` [:L1002]
    statement, parameters = mt_bb300_update()
    _mysql_1210_command(
        file_access, statement, parameters, file_function=FileFunction.RE_WRITE
    )

    # `if WS-MYSQL-COUNT-ROWS not = 1` [:L1008]
    if _BRIDGE_WS.ws_mysql_count_rows != 1:
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        if _errno_is_non_zero():
            # `move 99 to fs-reply` / `move 994 to WE-Error` [:L1016-L1017].
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.REWRITE_SQLSTATE_NOT_00000)
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
        else:
            # ANOMALY N-nostatus [common/glbatchMT.cbl:L1019]. Write NO status.
            #  SILENT, per N-nostatus [common/glbatchMT.cbl:L1019]. The zero also
            #  persists in `Ws-Mysql-Count-Rows` and will end the next sequential
            #  walk, which is the second-order effect the walk's own silent exit
            #  above then hides. Both are reproduced and neither is reported (R-4).
            pass
        # `go to ba999-End` [:L1019] - Class 3.
        mt_ba999_end(file_access, dal_common, batch)
        return

    # [:L1021-L1023], outside the `end-if` rather than in an `else`.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(_SQL_ERR_ZERO)
    _store_sql_msg(logging_data, "")
    # `go to ba999-End.` [:L1024] - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba100_bad_function(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba100-Bad-Function.`` [common/glbatchMT.cbl:L1026-L1032].

    Verbatim, comment included [:L1028-L1032]::

        *> Houston; We have a problem
        move     990 to WE-Error.
        move     99 to Fs-Reply.
        go       to ba999-end.

    ANOMALY N-badfunction-divergence - RECORDED, NOT RECONCILED. The bridge
    reports ``(99, 990)`` here, while the HANDLER's own ``aa100-Bad-Function``
    reports ``(99, 999)`` [common/acas007.cbl:L544-L549]. Same condition, two
    different ``We-Error`` codes, in two programs of the same call chain - and
    the authoritative code table names 990 "Unknown/Unexpected"
    [common/glpostingMT.cbl:L141 and siblings] and 999 "Not used". Each site
    reproduces its own value; neither is corrected to the other.

    In practice this paragraph is unreachable from :func:`dispatch`, because the
    handler's own ``aa100-Bad-Function`` catches an unknown function first and
    never calls the bridge. It is reachable by calling :func:`glbatch_mt`
    directly with a function outside 1..9, which is what makes it testable.

    Args:
        file_access: ``File-Access``; receives ``(99, 990)``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``. Untouched.
    """
    # `move 990 to WE-Error.` [:L1030] then `move 99 to Fs-Reply.` [:L1031] -
    # in that order, We-Error first, which is the opposite of the handler's.
    file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
    file_access.fs_reply = int(FsReply.ERROR)
    log_handler_failure(
        _LOG,
        program=BRIDGE,
        paragraph="ba100-Bad-Function",
        locator="[common/glbatchMT.cbl:L1030-L1031]",
        fs_reply=int(FsReply.ERROR),
        we_error=int(WeError.UNKNOWN_UNEXPECTED),
        detail="File-Function %d matched no arm; note (99, 990) here is NOT the "
        "(99, 999) the handler's own aa100-Bad-Function reports "
        "[common/acas007.cbl:L548-L549]" % int(file_access.file_function),
    )
    # `go to ba999-end.` [:L1032] - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba998_free(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
    *,
    only_if_active: bool,
) -> None:
    """``ba998-Free.`` [common/glbatchMT.cbl:L1038-L1048].

    Verbatim [:L1039-L1048]::

        move     20 to ws-No-Paragraph.
                   MOVE TP-GLBATCH-REC TO WS-MYSQL-RESULT
                   CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call
        set      Cursor-Not-Active to true.

    Releases the stored result and deactivates the cursor. Two callers reach it
    as a ``PERFORM`` and therefore return - ``ba030-Process-Close`` [:L442-L443]
    and ``ba060-Process-Start`` [:L726-L727], both guarded by
    ``if Cursor-Active`` - while ``ba050-Process-Read-Indexed`` reaches it as a
    ``go to`` on every one of its four exits, UNGUARDED.

    THIS PARAGRAPH FALLS THROUGH into ``ba999-end`` [:L1048 -> :L1050], so a
    ``go to ba998-Free`` also logs. The callers that ``PERFORM`` it do not,
    because a ``PERFORM`` of a paragraph returns at the next paragraph header.
    That asymmetry is COBOL's, not a choice, and it is why this function does
    not itself call :func:`mt_ba999_end` - the ``go to`` callers do.

    Note what ``ba041-Reread`` and ``ba040`` do NOT do: their end-of-data paths
    use a bare ``set Cursor-Not-Active to true`` [:L575], [:L592] rather than
    coming here, so THE STORED RESULT IS NEVER FREED on those paths. That leak
    is the frozen source's; :mod:`acas_posting.dal.cursor_state` reproduces it by
    deactivating without freeing.

    Args:
        file_access: ``File-Access``; receives the paragraph number.
        dal_common: ``ACAS-DAL-Common-data``. Unused here; carried so every
            paragraph function has the bridge's own three parameters.
        batch: ``WS-Batch-Record``. Untouched.
        only_if_active: ``True`` for the two ``if Cursor-Active perform``
            callers, ``False`` for ``ba050``'s unguarded ``go to``.
    """
    del dal_common, batch  # `ba998-Free` reads neither.
    state = _BRIDGE_WS.dal_data.state_for(TABLE, cursor_state.CursorSlot.PRIMARY)
    if only_if_active and state.cursor_not_active():
        # `if Cursor-Active perform ba998-Free.` [:L442-L443], [:L726-L727] -
        # the guard is the CALLER's, so nothing here runs, not even the
        # paragraph number.
        return
    # `move 20 to ws-No-Paragraph.` [:L1039]
    file_access.logging_data.ws_no_paragraph = _LOGGING_FIELDS[
        "ws-No-Paragraph"
    ].store(WS_NO_PARAGRAPH_BRIDGE["ba998-Free"])
    # `CALL "MySQL_free_result"` [:L1046] then `set Cursor-Not-Active to true.`
    # [:L1048]. `CursorState.free` does both - it releases the stored result and
    # clears the flag - which is why it is used here and a bare
    # `set_cursor_not_active` is used on the leak paths.
    state.free()


def mt_ba999_end(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba999-end.`` [common/glbatchMT.cbl:L1050-L1055].

    Verbatim [:L1053-L1055]::

        if       Testing-1
                 perform Ca-Process-Logs
        end-if.

    The single logging gate every paragraph of the bridge jumps to. It then FALLS
    THROUGH into ``ba999-exit`` [:L1057], which is ``exit program.`` - so
    reaching here is reaching the end of the bridge.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``.
    """
    # `if Testing-1 perform Ca-Process-Logs end-if.` [:L1053-L1055]
    mt_ca_process_logs(file_access, dal_common, batch)
    # FALL THROUGH into `ba999-exit` [:L1055 -> :L1057].
    mt_ba999_exit(file_access, dal_common, batch)


def mt_ba999_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba999-exit.`` [common/glbatchMT.cbl:L1057-L1058].

    ``exit program.`` - the bridge's single return point. Every status it
    reports has already been written into ``File-Access``, which is the caller's
    own storage passed by reference, so there is nothing to return.

    Args:
        file_access: ``File-Access``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
        batch: ``WS-Batch-Record``. Untouched.
    """
    del file_access, dal_common, batch  # `exit program.` reads nothing.


def mt_ca_process_logs(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``Ca-Process-Logs.`` [common/glbatchMT.cbl:L1705-L1709].

    Verbatim [:L1707-L1709]::

        call "fhlogger" using File-Access
                              ACAS-DAL-Common-data.

    OMISSION O-2. ``fhlogger`` is ``common/fhlogger.cbl``, which the Agent Action
    Plan lists as out of scope under "Non-posting utilities", so there is no
    module to call. It writes a log FILE and touches no in-scope table, so
    nothing a scenario diff compares depends on it. One structured log record
    stands in, carrying the same fields the COBOL passes: the status pair, the
    paragraph number, the log system and file number, the key and the statement.

    THE GATE IS ``Testing-1``, not this function. ``if Testing-1 perform
    Ca-Process-Logs`` [:L1053-L1054] reads ``88 Testing-1 value 1``
    [copybooks/Test-Data-Flags.cob:L11], declared over ``SW-Testing``, which
    reaches Python as
    :attr:`~acas_posting.records.test_data_flags.AcasDalCommonData.sw_testing`.
    Its default is the copybook's own ``value 1``, so logging is ON unless a
    caller turns it off. The gate is applied here rather than in every caller
    because every caller applies the identical test.

    THE CONDITION NAME IS EVALUATED INLINE, NOT IMPORTED AND NOT RE-DECLARED.
    ``acas_posting/cobol/condition_names.py`` owns the ``88``-level predicates,
    and the Agent Action Plan section 0.4.3 import table forbids ``dal`` from
    importing ``cobol`` - so what appears below is the integer comparison
    ``if Testing-1`` performs, at its one and only site, with no predicate
    published from here.

    The driver's own text is redacted before it reaches the log record, because
    a server message can carry the connection's account, host, key values and a
    line feed (CWE-117, CWE-532). The two ACAS status values are integers from
    this module's own enumerations and are interpolated as themselves. Nothing
    branches on any of it.

    Args:
        file_access: ``File-Access``; every field the log record reports.
        dal_common: ``ACAS-DAL-Common-data``; supplies the ``Testing-1`` gate.
        batch: ``WS-Batch-Record``. Not logged - the COBOL passes only the two
            blocks above - and carried so this function has the bridge's own
            three parameters.
    """
    del batch  # `call "fhlogger"` passes File-Access and ACAS-DAL-Common-data.
    # `88 Testing-1 value 1` over `SW-Testing`
    # [copybooks/Test-Data-Flags.cob:L10-L11], tested inline for the reason given
    # above. Equality against one, not truthiness: the condition name names ONE
    # value, so a switch holding 2 does not satisfy it.
    if int(dal_common.sw_testing) != 1:
        return
    logging_data = file_access.logging_data
    #  THE ONE ADAPTER, and three fields fewer than this record used to carry.
    #  `WS-File-Key` is the batch key, `WS-Log-Where` is the `WHERE` clause built
    #  around it and `SQL-Msg` is the driver's free text; `redact_for_log` was
    #  applied to the last two and removed nothing, because its rules recognise
    #  connection-message shapes and not a batch number (CWE-532). The adapter also
    #  advances `Log-File-Rec-Written` modulo one million, which this module used
    #  not to do at all.
    log_file_handler_record(
        _LOG,
        program=BRIDGE,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=file_access.file_function,
        access_type=file_access.access_type,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=str(logging_data.sql_err),
        sql_state=str(logging_data.sql_state),
        dal_common=dal_common,
    )


def glbatch_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``call "glbatchMT" using File-Access ACAS-DAL-Common-data WS-Batch-Record``.

    THE BRIDGE'S OWN THREE PARAMETERS, IN THE BRIDGE'S OWN ORDER, WITH
    ``File-Access`` FIRST. That order is not the handler's and must not be
    "tidied" to match it - the ``CALL`` is verbatim
    [common/acas007.cbl:L640-L645]::

        ba020-Process-DAL.
            call     "glbatchMT" using File-Access
                                         ACAS-DAL-Common-data
                                         WS-Batch-Record
            end-call.

    and the bridge's own heading agrees [common/glbatchMT.cbl:L334-L336]::

        Procedure Division using File-Access
                                 ACAS-DAL-Common-data
                                 WS-Batch-Record.   *>  Ws record

    Published as part of this module's public API under rule R-5, so that a
    reader following the HANDLER-named calling convention finds a function named
    for the handler - :func:`dispatch` - and a reader following the BRIDGE finds
    one named for the bridge, over one implementation.

    IT NEEDS NO ``System-Record`` AND MUST NOT GROW ONE. The credentials the
    open uses were copied into ``RDB-Data`` by the handler's own
    ``ba012-Test-WS-Rec-Size-2`` on the first call [common/acas007.cbl:L614-L619],
    and :func:`dispatch` records the resident ``System-Record`` for the duration
    of the call chain so :func:`mt_ba020_process_open` can reach it. Calling this
    function with ``fn-Open`` before any :func:`dispatch` raises
    :class:`BridgeCalledOutsideHandlerError`.

    ALL SQL FOR ``GLBATCH-REC`` LIVES BELOW THIS FUNCTION AND NOWHERE ELSE. No
    other module in the package issues a statement against this table, which is
    what makes the handler boundary of Agent Action Plan section 0.3.1
    enforceable rather than aspirational.

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L38]. Carries the
            verb in ``file_function``, the START relation in ``access_type``, and
            receives ``fs_reply``, ``we_error`` and every logging field.
        dal_common: ``ACAS-DAL-Common-data``, the ``Testing-1`` logging gate.
        batch: ``WS-Batch-Record`` [copybooks/wsbatch.cob:L13-L54]. Supplies the
            key and, for a write or rewrite, all twenty-one column values;
            receives a row on a successful read.

    Raises:
        BridgeCalledOutsideHandlerError: On ``fn-Open`` with no resident
            ``System-Record``.
        BridgeNotOpenError: On a statement verb with no connection open.

    Examples:
        Read the batch keyed ledger 1, batch 7, then close::

            #  The deployment installed the one policy already; nothing is
            #  declared per table.
            file_access.file_function = int(FileFunction.OPEN)
            file_access.access_type = int(AccessType.I_O)
            dispatch(system, batch, file_access, file_defs, dal_common)

            batch.ws_batch_key.ws_ledger = 1
            batch.ws_batch_key.ws_batch_nos = 7
            file_access.file_function = int(FileFunction.READ_INDEXED)
            file_access.access_type = 0
            dispatch(system, batch, file_access, file_defs, dal_common)

            file_access.file_function = int(FileFunction.CLOSE)
            dispatch(system, batch, file_access, file_defs, dal_common)
    """
    # `move 23 to WS-Log-File-no` was already done by the handler on the RDB path
    # [common/acas007.cbl:L577] - anomaly N-log. The bridge itself writes neither
    # the log system nor the file number.
    mt_ba_acas_dal_process(file_access, dal_common, batch)


# ===========================================================================
# THE HANDLER - `acas007` ITSELF.
#
# WHY IT IS BELOW THE BRIDGE. The handler CALLS the bridge, so the file reads
# bottom-up: column metadata, then host-variable movement, then the bridge's
# own paragraphs, then `glbatch_mt`, then the handler that calls it, and
# `dispatch` first within this section as the public face. Python resolves
# function names at call time, so the ordering is presentational only.
#
# ONE PYTHON FUNCTION PER COBOL PARAGRAPH, in the source order of
# [common/acas007.cbl:L274-L659], each carrying its own locator and each
# `GO TO` site annotated with its class from Agent Action Plan section 0.4.2:
#
#   Class 1  loop-back           -> `continue` inside `while True:`
#   Class 2  forward terminator  -> `break` PLUS the post-loop work
#   Class 3  section/para exit   -> `return`
#   Class 4  sibling re-dispatch -> a named call, then `continue`/`return`
#
# THE HANDLER HAS NO LOOP AT ALL, so no site is Class 1 or Class 2. Every
# `GO TO` in it is Class 3 (the `aa999-main-exit` / `aa-main-exit` /
# `ba-rdbms-exit` family) or Class 4 (`aa010-main`'s eight-way dispatch into
# the `aa0NN` paragraphs, and `aa100-Bad-Function` reached twice over).
#
# FALL-THROUGH IS MODELLED EXPLICITLY, never implied, at all four places the
# frozen source relies on it:
#   `aa100-Bad-Function` -> `aa999-main-exit` -> `aa-main-exit` -> `aa-Exit`
#   `ba010-Test-WS-Rec-Size` -> `ba012-Test-WS-Rec-Size-2` -> `ba015-Test-Ends`
#   `ba015-Test-Ends` -> `ba020-Process-DAL`      <- ANOMALY N18b's SECOND CALL
#   `ba020-Process-DAL` -> `ba-rdbms-exit`
# ===========================================================================


def _fs_cobol_files_used(system: SystemRecord) -> bool:
    """``FS-Cobol-Files-Used`` - is the indexed-file store the one in use?

    ``88 FS-Cobol-Files-Used value zero`` over ``07 File-System-Used pic 9``
    [copybooks/wssystem.cob:L112-L113]. The handler tests its NEGATION twice,
    once for the Open-Output special case [common/acas007.cbl:L307] and once for
    the general relational branch [:L316], and both times a true result routes
    to the bridge.

    Evaluated inline rather than imported: ``acas_posting.cobol.condition_names``
    owns the ``88``-level predicates, and Agent Action Plan section 0.4.3's
    import table forbids ``dal`` importing ``cobol``. Two ``88`` names share the
    value 1 here - ``FS-MySql-Used`` [:L114] and ``FS-RDBMS-Used`` [:L116] - and
    ``88 FS-Valid-Options values 0 thru 1`` [:L122] admits only those two, but
    NO VALIDATION IS ADDED: any non-zero routes to the bridge, exactly as
    ``not FS-Cobol-Files-Used`` does.

    Note the consequence for a caller that never sets the switch: the copybook
    default is zero, so A DEFAULT ``SystemRecord`` TAKES THE INDEXED-FILE PATH
    and reaches :class:`FlatFileStoreNotMigratedError`. That is deliberate - see
    that class's own docstring.

    Args:
        system: ``System-Record``, the handler's first parameter.

    Returns:
        ``True`` when ``File-System-Used`` is zero.
    """
    return int(system.system_data_block.rdbms_flat_statuses.file_system_used) == 0


def _indexed_file_verb(
    verb: str, paragraph: str, locator: str, file_defs: FileDefs
) -> NoReturn:
    """Refuse a physical verb against ``Batch-File`` - OMISSION O-1.

    Every ``open``/``close``/``read``/``start``/``write``/``rewrite``/``delete``
    in the ``aa0NN`` paragraphs acts on ``Batch-File``, the ISAM file
    ``copybooks/selbatch.cob`` declares - ``assign file-7``, ``organization
    indexed``, ``status fs-reply``, ``record key batch-key`` - whose OS path is
    ``File-Defs``' own ``file-7``, ``"batch.dat"`` [copybooks/file07.cob:L1].

    THAT STORE IS NOT IN THE MIGRATION. MySQL is the store the Agent Action Plan
    targets, ``harness/seed.sh`` seeds MySQL and the scenario diffs compare MySQL
    tables, so these verbs have nothing to act on. Every NON-file decision in the
    same paragraphs IS reproduced and reachable - the ``fn-extend`` refusal
    [common/acas007.cbl:L385-L389], ``aa060``'s access-type guard [:L472-L475],
    the ``Cobol-File-Eof`` branch [:L419-L428], ``aa100-Bad-Function``
    [:L544-L549] and every ``WS-File-Key`` and ``WS-No-Paragraph`` write - because
    none of those touches a file.

    Args:
        verb: The COBOL verb, spelled as the frozen source spells it.
        paragraph: The paragraph it sits in.
        locator: Its ``[common/acas007.cbl:L<n>]`` locator.
        file_defs: ``File-Defs``, consulted only to name the path in the message.
            This is the ONLY use the handler makes of that parameter, since the
            ``assign`` clause is the only other place it is read.

    Raises:
        FlatFileStoreNotMigratedError: Always.
    """
    raise FlatFileStoreNotMigratedError(
        f"{paragraph} reached `{verb} Batch-File` {locator}, which acts on the "
        f"indexed file {file_defs.file_defs_a.file_7.strip()!r} "
        f"[copybooks/selbatch.cob:L2-L6], [copybooks/file07.cob:L1]. That store "
        f"is omission O-1 and is not migrated. Set "
        f"System-Record.system_data_block.rdbms_flat_statuses.file_system_used "
        f"to 1 (`FS-RDBMS-Used` [copybooks/wssystem.cob:L116]) so the request "
        f"routes to {BRIDGE} [common/acas007.cbl:L316-L320]."
    )


def dispatch(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``call "acas007" using ...`` - THE HANDLER'S FIVE PARAMETERS, IN ORDER.

    This is the function the Agent Action Plan names, and it names it verbatim in
    section 0.4.3, as the worked example of the whole ``CALL``-to-call contract::

        FROM:  call "acas007" using System-Record WS-Batch-Record File-Access
                                    File-Defs ACAS-DAL-Common-Data
        TO:    acas007_gl_batch.dispatch(system, batch, file_access, file_defs,
                                         dal_common)

    The frozen heading it binds [common/acas007.cbl:L265-L271]::

        Procedure Division Using System-Record
                                 WS-Batch-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data.

    and the facade paragraph that issues it, which the plan cites as THE dispatch
    exemplar [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]::

        acas007.
            move     1  to File-Key-No.
            call     "acas007" using System-Record
                                     WS-Batch-Record
                                     File-Access
                                     File-Defs
                                     ACAS-DAL-Common-Data.

    Note what the facade does IMMEDIATELY BEFORE the call: ``move 1 to
    File-Key-No``. Key 1 is therefore always satisfied when the entity facade is
    the caller, which is why the key guard at [common/acas007.cbl:L285-L299] can
    only fire for a caller that reached this function directly.

    THE PARAMETER ORDER IS NOT THE BRIDGE'S. The bridge takes three, with
    ``File-Access`` FIRST [:L641-L644]; see :func:`glbatch_mt`. Neither list may
    be "tidied" towards the other - a reviewer diffs both against the frozen
    source character by character.

    WHAT IT DOES, in the handler's own order and nothing more: makes the
    ``System-Record`` resident for the duration of the call, exactly as COBOL
    LINKAGE makes it resident while the program is on the stack, then enters
    ``aa-Process-Flat-File Section``. Every status the caller reads back is
    written into ``File-Access`` by the paragraphs, never by this function.

    Args:
        system: ``System-Record`` [copybooks/wssystem.cob]. Supplies the store
            selector ``File-System-Used`` [:L112] and, on the first call of the
            run, the six ``RDB-Data`` credential items [common/acas007.cbl:
            L614-L619].
        batch: ``WS-Batch-Record`` [copybooks/wsbatch.cob:L13-L54]. Supplies the
            key, and for a write or rewrite all twenty-one column values;
            receives a row on a successful read.
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L38]. Carries the
            verb in ``file_function``, the open mode or START relation in
            ``access_type``, the key number in ``Logging-Data``'s
            ``file_key_no``, and receives ``fs_reply``, ``we_error`` and every
            logging field.
        file_defs: ``File-Defs`` [copybooks/wsnames.cob]. Read only by the
            indexed store's ``assign`` clause, which is omission O-1.
        dal_common: ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob].
            Its ``SW-Testing`` is the ``Testing-1`` logging gate; the copybook
            default is 1, so logging is ON unless a caller clears it.

    Raises:
        FlatFileStoreNotMigratedError: When the request reaches a physical verb
            against ``Batch-File`` - omission O-1.
        BatchKeyViewsDisagreeError: When the two readings of the six key bytes
            were both set and disagree.
        BridgeCalledOutsideHandlerError: Not reachable through this function,
            which is precisely what it exists to guarantee.

    Examples:
        Open the table for input, read the batch keyed ledger 1 batch 7, close::

            #  The deployment installed the one policy already; nothing is
            #  declared per table.
            system.system_data_block.rdbms_flat_statuses.file_system_used = 1

            file_access.file_function = int(FileFunction.OPEN)
            file_access.access_type = int(AccessType.INPUT)
            dispatch(system, batch, file_access, file_defs, dal_common)

            batch.ws_batch_key.ws_ledger = 1
            batch.ws_batch_key.ws_batch_nos = 7
            file_access.logging_data.file_key_no = 1
            file_access.file_function = int(FileFunction.READ_INDEXED)
            dispatch(system, batch, file_access, file_defs, dal_common)
    """
    # LINKAGE residency, not added state. While `acas007` is on the stack its
    # `System-Record` is live, which is how `ba012-Test-WS-Rec-Size-2` reaches
    # the credentials [common/acas007.cbl:L614-L619] and how the bridge's open
    # reaches them through `dal/connection.py`. Saved and restored rather than
    # simply cleared, so a caller nesting two dispatches - which the compiled
    # system cannot do, but a test can - cannot lose the outer one.
    previous_system_record = _HANDLER.linkage_system_record
    _HANDLER.linkage_system_record = system
    try:
        aa_process_flat_file(system, batch, file_access, file_defs, dal_common)
    finally:
        # `exit program` [common/acas007.cbl:L561] ends LINKAGE residency.
        _HANDLER.linkage_system_record = previous_system_record


def aa_process_flat_file(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas007.cbl:L274-L275].

    The section header. A COBOL SECTION is entered at its first paragraph and
    has no code of its own, so this function exists for traceability - rule R-5
    requires every paragraph AND section to map to a named function - and does
    exactly one thing: enter ``aa010-main``.

    The section's name is a leftover from before the relational store existed:
    it says "Flat-File", yet ``aa010-main`` is where BOTH stores are chosen
    between [:L305-L320]. The name is not corrected.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    aa010_main(system, batch, file_access, file_defs, dal_common)


def aa010_main(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa010-main.`` [common/acas007.cbl:L276-L360].

    Five things in five stages, in exactly this order.

    STAGE 1 - THE LOG IDENTITY [:L280-L281]::

        move     2      to WS-Log-System.
        move     13     to WS-Log-File-No.

    with the source's own comments naming the whole family, ``1 = IRS, 2=GL,
    3=SL, 4=PL, 5=Stock``, and ``Cobol/RDB, File/Table within sub System``.
    ANOMALY N-log: 13 here, then OVERWRITTEN TO 23 by
    ``ba010-Test-WS-Rec-Size`` on the relational path [:L577], where the
    receiving field is spelled ``WS-Log-File-no`` with a lower-case ``no``. The
    family is systematic - ``acas005`` 11 to 21, ``acas006`` 12 to 22,
    ``acas007`` 13 to 23, ``acas008`` 15 to 25 - and 14 is skipped.

    STAGE 2 - THE KEY GUARD [:L285-L299]. Functions 4 and 9 share one ``if`` and
    answer ``We-Error 998``; function 8 has its own and answers ``996``; both
    write ``FS-Reply 99`` and transfer to ``aa999-main-exit``. NOT write (5) and
    NOT re-write (7). ANOMALY N-guard: ``acas000`` guards 4, 5 and 7 instead, and
    the two sets are deliberately not harmonised. ANOMALY N-996-comment: the
    comment on the 996 branch [:L295] is a copy-paste of the 998 comment [:L289]
    and describes the wrong condition - both read "file seeks key type out of
    range". ANOMALY N-998: 998 carries a THIRD meaning at [:L473].

    STAGE 3 - THE OPEN-OUTPUT SPECIAL CASE [:L305-L312], which is stage one of
    ANOMALY N18b. See :func:`ba015_test_ends` for stage two, and note here that
    the two lines which WOULD have coerced the function are COMMENTED OUT, so
    the bridge is entered with ``fn-Open`` and ``fn-Output`` still set.

    STAGE 4 - THE GENERAL RELATIONAL BRANCH [:L316-L320]. Copies the store
    selector into ``File-Access`` - the source's comment asks "needed for DAL?
    not JC/dbpre versions" and answers itself "Can't hurt" - then calls the
    bridge and returns. ANOMALY N-fa-statuses-skipped: stage 3 fires FIRST and
    has no such copy, so an ``Open`` plus ``Output`` request is the one
    relational request that reaches the bridge without it.

    BOTH RELATIONAL BRANCHES TRANSFER TO ``aa-main-exit``, NOT to
    ``aa999-main-exit`` [:L311, :L319], so NEITHER LOGS FROM THE HANDLER. The
    bridge logged for itself at ``ba999-end`` [common/glbatchMT.cbl:L1053-L1055],
    which is what the logging paragraph's own comment means by "Not called on DAL
    access as it does it already" [:L653] - a claim ``ba012``'s 901 branch then
    contradicts by calling it [:L604].

    STAGE 5 - THE INDEXED PATH. ``perform ba012-Test-WS-Rec-Size-2`` [:L324],
    then ``move spaces to SQL-Err SQL-Msg SQL-State`` [:L336] - note that the
    two lines above it which would ALSO have zeroed ``WE-Error`` and ``FS-Reply``
    are COMMENTED OUT [:L334-L335], which is the root of anomalies N-nostatus and
    N-901-sticky - then the eight-way ``evaluate`` [:L338-L357] and, after it, an
    UNCONDITIONAL ``go to aa100-Bad-Function`` [:L360] under the comment "Should
    never get here but in case :(".

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    logging_data = file_access.logging_data

    # ---- STAGE 1: `move 2 to WS-Log-System.` [common/acas007.cbl:L280] ----
    logging_data.ws_log_system = _LOGGING_FIELDS["ws-Log-System"].store(
        int(WS_LOG_SYSTEM)
    )
    # `move 13 to WS-Log-File-No.` [:L281] - ANOMALY N-log, stage one of two.
    logging_data.ws_log_file_no = _LOGGING_FIELDS["WS-Log-File-No"].store(
        WS_LOG_FILE_NO_COBOL_PATH
    )

    # ---- STAGE 2: the key guard [:L285-L299] ----
    # `evaluate File-Function / when 4 / when 9 ... when 8 ...`. Held as data in
    # GUARDED_FUNCTIONS so the guarded SET is visible and cannot drift; the
    # `when` order 4, 9, 8 is that mapping's insertion order.
    function = int(file_access.file_function)
    guarded_we_error = GUARDED_FUNCTIONS.get(function)
    if guarded_we_error is not None:
        # `if File-Key-No not = 1` - the SAME test in both arms [:L288, :L294].
        if int(logging_data.file_key_no) != FILE_KEY_NO_REQUIRED:
            # `move 998 to WE-Error` / `move 99 to fs-reply` [:L289-L290], or
            # `move 996 to WE-Error` / `move 99 to fs-reply` [:L295-L296].
            # We-Error FIRST in the frozen source, so We-Error first here.
            file_access.we_error = guarded_we_error
            file_access.fs_reply = int(FsReply.ERROR)
            # `go to aa999-main-exit` [:L291, :L297] - Class 3.
            aa999_main_exit(system, batch, file_access, file_defs, dal_common)
            return
    # `end-evaluate.` [:L299]. No `when other`, and none is added: a function
    # outside 4, 8 and 9 is simply not key-checked here.

    # ---- STAGE 3: ANOMALY N18b, STAGE ONE [common/acas007.cbl:L305-L312] ----
    # Verbatim, including the two commented-out lines that would have coerced
    # the function - their absence is the whole of the anomaly:
    #
    #     if       fn-Open and
    #              fn-output
    #         and  not FS-Cobol-Files-Used  *> RDB processing
    #     *>             set fn-delete-all to true
    #     *>             move zero to access-type
    #              perform ba-Process-RDBMS
    #              go to AA-Main-Exit
    #     end-if.
    #
    # So the bridge is entered with File-Function still fn-Open and Access-Type
    # still fn-Output, and `ba015-Test-Ends` is what forces the Delete-All -
    # AFTER a first call the open already made. Contrast `acas008`, which DOES
    # coerce before its perform [common/acas008.cbl:L313-L319], and `acas005`,
    # whose whole block is commented out [common/acas005.cbl:L307].
    if (
        function == int(FileFunction.OPEN)
        and int(file_access.access_type) == int(AccessType.OUTPUT)
        and not _fs_cobol_files_used(system)
    ):
        # ANOMALY N-fa-statuses-skipped. This branch precedes the
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses` of the general
        # branch [:L317], and there is no equivalent move here, so an
        # Open-plus-Output request - and ONLY that request - reaches the bridge
        # with `FA-RDBMS-Flat-Statuses` still at whatever the caller had, while
        # every other relational request carries the copied value. No copy is
        # added: the frozen source does not make one.
        # `perform ba-Process-RDBMS` [:L310] - a PERFORM, so control returns.
        ba_process_rdbms(system, batch, file_access, file_defs, dal_common)
        # `go to AA-Main-Exit` [:L311] - Class 3. NOTE: `aa-main-exit`, NOT
        # `aa999-main-exit`, so THE RELATIONAL PATH DOES NOT LOG HERE. The
        # bridge logged for itself at `ba999-end` [common/glbatchMT.cbl:L1053].
        aa_main_exit(system, batch, file_access, file_defs, dal_common)
        return

    # ---- STAGE 4: the general relational branch [:L316-L320] ----
    if not _fs_cobol_files_used(system):
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses` [:L317] - a GROUP
        # move of two `pic 9` items [copybooks/wssystem.cob:L111-L124] into
        # [copybooks/wsfnctn.cob:L72-L83]. Reproduced item by item because the
        # two groups have different field names, so a whole-object assignment
        # would alias the caller's System-Record into File-Access.
        source_statuses = system.system_data_block.rdbms_flat_statuses
        target_statuses = file_access.fa_rdbms_flat_statuses
        target_statuses.fa_file_system_used = int(source_statuses.file_system_used)
        target_statuses.fa_file_duplicates_in_use = int(
            source_statuses.file_duplicates_in_use
        )
        # `perform ba-Process-RDBMS` [:L318] - the source's own comment on it
        # reads "Can't hurt".
        ba_process_rdbms(system, batch, file_access, file_defs, dal_common)
        # `go to AA-Main-Exit` [:L319] - Class 3, and again NOT `aa999`.
        aa_main_exit(system, batch, file_access, file_defs, dal_common)
        return

    # ---- STAGE 5: the indexed path [:L324-L360] ----
    # `perform ba012-Test-WS-Rec-Size-2.` [:L324] - a PERFORM of ONE PARAGRAPH
    # in another section, so it does NOT fall through into `ba015-Test-Ends` and
    # the bridge is NOT reached from here. That distinction is load-bearing:
    # falling through would call the bridge on the indexed path.
    if ba012_test_ws_rec_size_2(system, batch, file_access, file_defs, dal_common):
        # AMBIGUITY Q-5. The 901 branch's `go to ba-rdbms-exit` [:L607] left the
        # range of this PERFORM and reached `exit section` [:L650]. There is no
        # section after `ba-Process-RDBMS` - `Ca-Process-Logs` and `ca-Exit` are
        # paragraphs INSIDE it [:L653-L659] - so control runs off the end of the
        # PROCEDURE DIVISION, which in a called subprogram is an implicit
        # `exit program`. The handler therefore returns to its caller and
        # [:L326-L360] is skipped entirely. Recorded in AMBIGUITIES because
        # unwinding a live perform stack is implementation-specific.
        return

    # `move spaces to SQL-Err SQL-Msg SQL-State.` [:L336]. The two lines above
    # it are COMMENTED OUT in the frozen source [:L334-L335]::
    #
    #      *>    move     zero   to  WE-Error
    #      *>  ?                      FS-Reply.
    #
    # - complete with the maintainer's own question mark - so WE-ERROR AND
    # FS-REPLY ARRIVE HERE CARRYING WHATEVER THE CALLER LEFT IN THEM. That is
    # the root of anomalies N-nostatus and N-901-sticky and is not corrected.
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store("")
    _store_sql_msg(logging_data, "")
    logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store("")

    # `evaluate File-Function` [:L338-L357] - eight `when`s in the order
    # 1, 2, 3, 4, 5, 7, 8, 9, so RE-WRITE PRECEDES DELETE, and no `when 6`
    # because the source's own comment says `*> 6 is unused`. Every arm is a
    # `go to` into a sibling paragraph that performs work and then transfers
    # control itself, so every arm is Class 4: a named call, then `return`.
    if function == int(FileFunction.OPEN):
        aa020_process_open(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.CLOSE):
        aa030_process_close(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.READ_NEXT):
        aa040_process_read_next(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.READ_INDEXED):
        aa050_process_read_indexed(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.WRITE):
        aa070_process_write(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.RE_WRITE):
        aa090_process_rewrite(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.DELETE):
        aa080_process_delete(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.START):
        aa060_process_start(system, batch, file_access, file_defs, dal_common)
        return
    # `when other *> 6 is unused / go to aa100-Bad-Function` [:L355-L356] -
    # Class 4. `fn-Delete-All` (6) is SET INTERNALLY by `ba015-Test-Ends` and
    # never dispatched here, so it lands in this arm on the indexed path.
    aa100_bad_function(system, batch, file_access, file_defs, dal_common)
    # `go to aa100-Bad-Function.` [:L360], unconditional, under the comment
    # "Should never get here but in case :(". It is UNREACHABLE from the `when
    # other` arm above, which already transferred, so the second call it would
    # make is not made here either - the `return` reproduces the transfer that
    # every arm performs before reaching this statement. Kept as a comment
    # rather than as code because writing it as code would double the status
    # write, which the frozen program never does.
    return


def aa020_process_open(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa020-Process-Open.`` [common/acas007.cbl:L362-L398].

    Four nested ``if``s on ``Access-Type``, then a shared tail. Verbatim
    [:L363-L398], with the one commented-out line kept as the source has it::

        move     spaces to WS-File-Key.     *> for logging
        move     201 to WS-No-Paragraph.
        if       fn-input
                 open input Batch-File
                 if   Fs-Reply not = zero
                      move 35 to fs-Reply
                      close Batch-File
                      go to aa999-Main-Exit
                 end-if
         else
          if     fn-i-o
                 open i-o Batch-File
                 if       fs-reply not = zero
                          close       Batch-File
                          open output Batch-File           *> Doesnt create in i-o
                          close       Batch-File
                          open i-o    Batch-File
                 end-if
          else
           if    fn-output
                 open output Batch-File       *> caller should check fs-reply
           else
            if   fn-extend                      *> Must not be used for ISAM files
        *>              open extend Batch-File
                 move 997 to WE-Error
                 move 99  to FS-Reply
                 go to aa999-main-exit
            end-if
           end-if
          end-if
        end-if.
        move     zero to Cobol-File-Status.
        move     "OPEN GL BATCH file" to WS-File-Key.
        if       fs-reply not = zero
                 move 999 to we-error.
        go       to aa999-main-exit.        *> with test for dup processing

    Three things in that are worth stating.

    ``fn-extend`` IS A REFUSAL, NOT AN OPEN. Its ``open extend Batch-File`` is
    commented out [:L386] and the arm answers ``(FS-Reply 99, We-Error 997)``
    with the source's own reason: "Must not be used for ISAM files". It touches
    NO file, so it is fully reproduced here. 997 is the code the authoritative
    table reserves for a wrong access type [common/glpostingMT.cbl:L136], which
    makes it the one place in this handler where the code and the table agree.

    ANOMALY N-open-nomode. If ``Access-Type`` is none of 1, 2, 3 or 4 then ALL
    FOUR ``if``s fall through, NO file is touched, and control reaches the tail
    at [:L394] anyway - so the open reports the caller's own incoming
    ``FS-Reply``, upgraded to ``We-Error 999`` if that happened to be non-zero
    [:L396-L397]. No diagnostic, no counter. Reproduced exactly, and reachable
    here because it needs no file.

    THE ``fn-input`` FAILURE PATH HARD-CODES 35, whatever the real file status
    was [:L368] - 35 is "file not found on OPEN INPUT" - and then closes a file
    it failed to open. Both are inside the omission-O-1 region, so both are
    recorded rather than executed.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched by this paragraph.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``,
            ``ws_file_key`` and, on the ``fn-extend`` arm, the status pair.
        file_defs: ``File-Defs``. Names the indexed path in the O-1 refusal.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: On ``fn-input``, ``fn-i-o`` or
            ``fn-output``, each of which reaches a real ``open`` - omission O-1.
    """
    logging_data = file_access.logging_data
    # `move spaces to WS-File-Key.` [common/acas007.cbl:L363]
    _store_ws_file_key(logging_data, "")
    # `move 201 to WS-No-Paragraph.` [:L364]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa020-Process-Open"]
    )

    access_type = int(file_access.access_type)
    if access_type == int(AccessType.INPUT):
        # `open input Batch-File` [:L366] - omission O-1. The `if Fs-Reply not =
        # zero` block that follows [:L367-L371] hard-codes 35 and closes the
        # file it could not open; both are recorded in this docstring.
        _indexed_file_verb(
            "open input", "aa020-Process-Open", "[common/acas007.cbl:L366]", file_defs
        )
    elif access_type == int(AccessType.I_O):
        # `open i-o Batch-File` [:L374] - omission O-1, and with it the
        # close/open-output/close/open-i-o recovery at [:L375-L380] whose own
        # comment reads "Doesnt create in i-o".
        _indexed_file_verb(
            "open i-o", "aa020-Process-Open", "[common/acas007.cbl:L374]", file_defs
        )
    elif access_type == int(AccessType.OUTPUT):
        # `open output Batch-File` [:L383] - omission O-1. Note the source's
        # comment "caller should check fs-reply": no status test follows. On the
        # RELATIONAL path this combination never arrives here at all, having
        # been intercepted by anomaly N18b's stage one [:L305-L312].
        _indexed_file_verb(
            "open output", "aa020-Process-Open", "[common/acas007.cbl:L383]", file_defs
        )
    elif access_type == int(AccessType.EXTEND):
        # `if fn-extend` [:L385]. The `open extend Batch-File` is COMMENTED OUT
        # [:L386], so this arm touches no file and is reproduced in full.
        # `move 997 to WE-Error` [:L387] then `move 99 to FS-Reply` [:L388] -
        # We-Error first, as written.
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        file_access.fs_reply = int(FsReply.ERROR)
        # `go to aa999-main-exit` [:L389] - Class 3.
        aa999_main_exit(system, batch, file_access, file_defs, dal_common)
        return
    # `end-if.` x4 [:L390-L393]. ANOMALY N-open-nomode: an Access-Type outside
    # 1..4 reaches here having touched nothing, and the tail below still runs.

    # `move zero to Cobol-File-Status.` [:L394] - the HANDLER's own flag, not the
    # caller's, so it is working storage here.
    _HANDLER.cobol_file_status = 0
    # `move "OPEN GL BATCH file" to WS-File-Key.` [:L395]. Note the spacing:
    # "GL BATCH", two words, where the bridge writes "OPEN GLBATCH" as one
    # [common/glbatchMT.cbl:L437]. Both are reproduced as written.
    _store_ws_file_key(logging_data, "OPEN GL BATCH file")
    # `if fs-reply not = zero move 999 to we-error.` [:L396-L397]. The period on
    # [:L397] closes the `if`, so there is no `else`.
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        file_access.we_error = int(WeError.NOT_USED)
    # `go to aa999-main-exit.` [:L398] - Class 3, with the source's own comment
    # "with test for dup processing" describing a test that is not there.
    aa999_main_exit(system, batch, file_access, file_defs, dal_common)


def aa030_process_close(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa030-Process-Close.`` [common/acas007.cbl:L400-L411].

    Verbatim, including the dated comment the maintainer left in place
    [:L401-L411]::

        move     202 to WS-No-Paragraph.
        move     spaces to WS-File-Key.     *> for logging
        close    Batch-File.
        *> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
        move     zero to Cobol-File-Status.
        move     "CLOSE GL BATCH file" to WS-File-Key.
        perform  aa999-main-exit.
        move     zero to  File-Function  *> REMOVE THIS IF FILE CLOSED FIRST
                          Access-Type.      *> close log file
        perform  Ca-Process-Logs.
        go       to aa-main-exit.

    ANOMALY N-close-double-log, and it is the only paragraph in either program
    that logs twice. ``perform aa999-main-exit`` [:L407] is a PERFORM, so it runs
    that paragraph's ``if Testing-1 perform Ca-Process-Logs`` and RETURNS here
    rather than falling through to ``aa-main-exit``; three statements later
    ``perform Ca-Process-Logs`` [:L410] logs AGAIN, this time UNCONDITIONALLY.
    So under ``Testing-1`` a close writes two log records and without it exactly
    one - the reverse of every other paragraph, which writes one or none.

    The two records are not identical. Between them ``File-Function`` and
    ``Access-Type`` are ZEROED [:L408-L409], and the zeroing is a WRITE INTO THE
    CALLER'S ``File-Access``, so a caller that inspects either field after a
    close finds zero. The comments explain both halves: "REMOVE THIS IF FILE
    CLOSED FIRST" and "close log file" - zero is the log writer's own signal to
    close its file.

    Note also the dated commented-out line [:L404]: as of 27/07/2016 a close
    STOPPED zeroing the status pair, so a close now reports whatever the caller
    arrived with unless the ``close`` verb itself changes it. That is the
    handler's own contribution to anomaly N-nostatus.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Receives ``ws_no_paragraph`` and
            ``ws_file_key``, and has ``file_function`` and ``access_type``
            ZEROED between the two log records.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always - ``close Batch-File`` [:L403] is
            the third statement, and everything quoted after it is unreachable
            for exactly that reason. Omission O-1.
    """
    logging_data = file_access.logging_data
    # `move 202 to WS-No-Paragraph.` [common/acas007.cbl:L401]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa030-Process-Close"]
    )
    # `move spaces to WS-File-Key.` [:L402]
    _store_ws_file_key(logging_data, "")
    # `close Batch-File.` [:L403] - omission O-1. The paragraph's remaining
    # eight statements, including anomaly N-close-double-log, are quoted in the
    # docstring above rather than written as code that cannot be reached: they
    # depend on a close having happened, and no close can happen here.
    _indexed_file_verb(
        "close", "aa030-Process-Close", "[common/acas007.cbl:L403]", file_defs
    )


def aa040_process_read_next(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa040-Process-Read-Next.`` [common/acas007.cbl:L413-L428].

    Verbatim, with the maintainer's own heading comment [:L414-L428]::

        *>    This is processed after
        *>    Start code as its really Start/Read next at point aa041
        move     203 to WS-No-Paragraph.
        if       Cobol-File-Eof          *> This block should NOT occur
                 move 10 to FS-Reply
                            WE-Error
                 move zeros to WS-Batch-Key9
                 move spaces to
                                SQL-Err
                                SQL-Msg
                 stop "Cobol File EOF"               *> for testing
                 go to aa999-main-exit
        end-if.

    THE WHOLE BLOCK IS REPRODUCED, because it touches no file. Three observable
    effects, in this order: the status pair becomes ``(10, 10)``; the CALLER'S
    SIX KEY BYTES ARE ZEROED - ``move zeros to WS-Batch-Key9`` writes the
    ``REDEFINES`` view, which is the same storage as ``WS-Ledger`` and
    ``WS-Batch-Nos`` [copybooks/wsbatch.cob:L14-L21], so all three readings go to
    zero; and ``SQL-Err`` and ``SQL-Msg`` become spaces while ``SQL-State`` is
    left alone, which is a narrower clear than [:L336] performs.

    ``move 10 to ... WE-Error`` puts a FILE STATUS value into the DETAIL CODE
    field. 10 is ``FS-Reply``'s end-of-file value and has no entry at all in the
    authoritative ``We-Error`` table [common/glpostingMT.cbl:L132-L153]; the
    bridge does exactly the same thing [common/glbatchMT.cbl:L509-L510], which
    is why ``dal/status.py`` publishes ``end_of_file_status`` as the one place
    that pair is written.

    ``stop "Cobol File EOF"`` [:L426] is OMISSION O-3 - a console pause, marked
    "for testing" by the maintainer. Per Agent Action Plan section 0.3.4 a prompt
    whose only effect is to block a terminal is dropped while its CONTROL
    TRANSFER is preserved, so the ``go to aa999-main-exit`` that follows it is
    kept and the pause becomes a log record. ``Cobol-File-Eof`` is the HANDLER's
    own ``88`` over ``77 Cobol-File-Status pic 9`` [:L243-L244], not the
    caller's, and the maintainer's own comment on the branch says "This block
    should NOT occur".

    Control then FALLS THROUGH into ``aa041-Reread`` [:L430], which is where the
    read actually happens - the paragraph has no ``go to`` of its own on the
    non-EOF path.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Its key is ZEROED on the EOF branch.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: On the non-EOF path, raised from
            :func:`aa041_reread` - omission O-1.
    """
    logging_data = file_access.logging_data
    # `move 203 to WS-No-Paragraph.` [common/acas007.cbl:L418]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa040-Process-Read-Next"]
    )
    # `if Cobol-File-Eof` [:L419] - the handler's own flag [:L243-L244].
    if _HANDLER.cobol_file_status == 1:
        # `move 10 to FS-Reply WE-Error` [:L420-L421] - one statement, two
        # receivers. `end_of_file_status()` is the single writer of that pair.
        eof_fs_reply, eof_we_error = end_of_file_status()
        file_access.fs_reply = int(eof_fs_reply)
        file_access.we_error = int(eof_we_error)
        # `move zeros to WS-Batch-Key9` [:L422]. The REDEFINES makes this one
        # storage, so every reading of the six bytes goes to zero together
        # [copybooks/wsbatch.cob:L14-L21]. Written directly rather than through
        # `synchronise_batch_key_views`, because that function reconciles two
        # readings and here BOTH are being cleared.
        batch.ws_batch_key9.ws_batch_key9 = 0
        batch.ws_batch_key.ws_ledger = 0
        batch.ws_batch_key.ws_batch_nos = 0
        # `move spaces to SQL-Err SQL-Msg` [:L423-L425]. SQL-State is NOT in
        # this list and is deliberately left as the caller had it.
        logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store("")
        _store_sql_msg(logging_data, "")
        # `stop "Cobol File EOF"` [:L426] - OMISSION O-3, the pause dropped and
        # the diagnostic kept, per Agent Action Plan section 0.3.4.
        #  ONE ERROR, THROUGH THE ONE REPORTER, at the same level in every handler
        #  that carries this stop. The pause is omission O-3; the transfer to
        #  `aa999-main-exit` below is kept.
        log_cobol_stop(
            _LOG,
            program=HANDLER,
            paragraph="aa040-Process-Read-Next",
            literal="Cobol File EOF",
            locator="[common/acas007.cbl:L426]",
        )
        # `go to aa999-main-exit` [:L427] - Class 3.
        aa999_main_exit(system, batch, file_access, file_defs, dal_common)
        return
    # `end-if.` [:L428], then FALL-THROUGH into `aa041-Reread` [:L430] - modelled
    # as an explicit call because the frozen source relies on source order here.
    aa041_reread(system, batch, file_access, file_defs, dal_common)


def aa041_reread(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa041-Reread.`` [common/acas007.cbl:L430-L444].

    Verbatim [:L431-L444]::

        read     Batch-File next record at end
                 move 10 to WE-Error FS-Reply        *> EOF
                 set Cobol-File-EoF to true
                 move 1 to Cobol-File-Status         *> JIC above dont work :)
                 initialize WS-Batch-Record
                 move "EOF" to WS-File-Key           *> for logging
                 go to aa999-main-exit
        end-read.
        if       FS-Reply not = zero
                 go to aa999-main-exit.
        move     Batch-Record to  WS-Batch-Record.
        move     Batch-Key   to WS-File-Key.
        move     zeros to WE-Error.
        go to    aa999-main-exit.

    THE FIRST STATEMENT IS THE READ, so the whole paragraph sits inside omission
    O-1. Four details are recorded here because a reader comparing this module
    with the bridge will look for them.

    ``set Cobol-File-EoF to true`` and ``move 1 to Cobol-File-Status`` are THE
    SAME ASSIGNMENT WRITTEN TWICE [:L433-L434] - the ``88`` at [:L244] carries
    ``value 1`` over that very field - and the maintainer says why: "JIC above
    dont work :)". Belt and braces, not two effects.

    ``initialize WS-Batch-Record`` [:L435] is the PLAIN form, matching
    ``bb100-UnloadHVs`` [common/glbatchMT.cbl:L1106] and NOT the ``with filler``
    form of the bridge's EOF2 path [:L589] - anomaly N-initialize, whose two
    semantics are not normalised.

    ``if FS-Reply not = zero go to aa999-main-exit`` [:L439-L440] is a SECOND
    failure test after the ``at end`` phrase already handled end-of-file, and it
    exits WITHOUT touching ``We-Error``, so a read that fails for any other
    reason answers with the caller's incoming detail code. Handler-side
    N-nostatus.

    ``move zeros to WE-Error`` [:L443] clears the detail code only on the
    SUCCESS path, and ``FS-Reply`` is left exactly as the ``read`` set it.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always - omission O-1.
    """
    # `read Batch-File next record at end ... end-read.` [common/acas007.cbl:
    # L431-L438] - omission O-1, and the first statement of the paragraph, so
    # nothing precedes it to reproduce. The nine statements it guards and the
    # five that follow it are quoted in the docstring above.
    _indexed_file_verb(
        "read next record",
        "aa041-Reread",
        "[common/acas007.cbl:L431]",
        file_defs,
    )


def aa050_process_read_indexed(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas007.cbl:L446-L449].

    Two statements and then a fall-through. Verbatim [:L448-L449]::

        move     204 to WS-No-Paragraph.
        move     zero to Cobol-File-Status.

    Both touch no file, so both are reproduced. Control then FALLS THROUGH into
    ``aa051-Reread`` [:L451], which is where the keyed read happens.

    NOTE THE ASYMMETRY WITH ``acas005``. This handler has TWO reread paragraphs,
    ``aa041-Reread`` and ``aa051-Reread``, and NO ``aa047-Eval-Keys``;
    ``acas005`` is the reverse. ``acas006`` matches this handler. The divergence
    is structural, is not harmonised, and is recorded so that a reader moving
    between the three modules is not surprised by a missing paragraph.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Raised from :func:`aa051_reread` -
            omission O-1.
    """
    logging_data = file_access.logging_data
    # `move 204 to WS-No-Paragraph.` [common/acas007.cbl:L448]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa050-Process-Read-Indexed"]
    )
    # `move zero to Cobol-File-Status.` [:L449] - the handler's own flag.
    _HANDLER.cobol_file_status = 0
    # FALL-THROUGH into `aa051-Reread` [:L451], modelled explicitly.
    aa051_reread(system, batch, file_access, file_defs, dal_common)


def aa051_reread(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa051-Reread.`` [common/acas007.cbl:L451-L459].

    Verbatim [:L452-L459]::

        move     WS-Batch-Key to Batch-Key WS-File-Key.
        read     Batch-File    invalid key
                 move 21 to we-error fs-reply
                 go to aa999-main-exit
        end-read
        move     Batch-Record  to  WS-Batch-Record.
        move     Batch-Key to WS-File-Key.
        go       to aa999-main-exit.

    THE FIRST STATEMENT IS OBSERVABLE AND IS REPRODUCED. ``move WS-Batch-Key to
    Batch-Key WS-File-Key`` writes the caller's ``WS-File-Key`` with the six key
    characters - a ``pic 9(6)`` reading of the group, so leading zeros are
    present and batch 7 of the General Ledger is the text ``100007`` - before the
    read is attempted. The other receiver, ``Batch-Key``, is the FD record's own
    key and is not observable.

    ``move 21 to we-error fs-reply`` [:L454] writes 21 to BOTH fields. 21 is
    ``FS-Reply``'s "invalid key on START" value and has no entry in the
    authoritative ``We-Error`` table [common/glpostingMT.cbl:L132-L153].
    ``aa060-Process-Start`` writes the same 21 to ``Fs-Reply`` ONLY [:L481],
    so the two paragraphs disagree about whether the detail code is touched;
    neither is harmonised. The bridge answers a keyed read that finds nothing
    with ``FS-Reply 21`` and no detail code either [common/glbatchMT.cbl:
    L649-L652], so it agrees with ``aa060`` rather than with this paragraph.

    ``move Batch-Key to WS-File-Key`` at [:L458] repeats what [:L452] already
    did - the value cannot have changed, because a successful keyed read returns
    the record whose key was sought. Recorded as a redundancy, not removed.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies the key; would receive the row.
        file_access: ``File-Access``. Receives ``ws_file_key`` BEFORE the read.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always, at the ``read`` - omission O-1.
    """
    logging_data = file_access.logging_data
    # `move WS-Batch-Key to Batch-Key WS-File-Key.` [common/acas007.cbl:L452].
    # `batch_key_image` reconciles the two readings of the six bytes and renders
    # them as the `pic 9(6)` text the COBOL move produces.
    _store_ws_file_key(logging_data, batch_key_image(batch))
    # `read Batch-File invalid key ... end-read` [:L453-L456] - omission O-1.
    _indexed_file_verb(
        "read", "aa051-Reread", "[common/acas007.cbl:L453]", file_defs
    )


def aa060_process_start(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa060-Process-Start.`` [common/acas007.cbl:L461-L509].

    Verbatim through the guard [:L463-L475], with the maintainer's warning::

        *>  Check for Param error 1st on start   WARNING Not logging starts
        move     205 to WS-No-Paragraph.
        move     zeros to fs-reply
                          WE-Error.
        move     zero to Cobol-File-Status.
        move     WS-Batch-Key to WS-File-Key
                                 Batch-Key.
        if       access-type < 5 or > 8                   *> NOT using 'not >'
                 move 998 to WE-Error                     *> 998 Invalid calling parameter settings
                 go to aa999-main-exit
        end-if

    EVERYTHING ABOVE TOUCHES NO FILE AND IS REPRODUCED IN FULL.

    ANOMALY N-start-code-divergence, and it is the sharpest divergence in this
    module. The guard writes ``We-Error 998`` AND NEVER TOUCHES ``FS-Reply``
    [:L473], which two statements earlier was set to zero [:L466-L467] - so the
    caller is answered ``(FS-Reply 0, We-Error 998)``, a SUCCESS status carrying
    an error code. The bridge's identical guard answers ``(99, 997)``
    [common/glbatchMT.cbl:L718-L722], and the authoritative table says the code
    for a wrong access type is 997 [common/glpostingMT.cbl:L136]. Three readings
    of one condition, none corrected. ANOMALY N-998: this is 998's THIRD
    documented meaning, "Invalid calling parameter settings", against "file
    seeks key type out of range" [common/acas007.cbl:L289] and the table's
    "File-Key-No Out Of Range" [common/glpostingMT.cbl:L135].

    The bounds are INCLUSIVE 5..8, and both programs write them the same odd way
    with the same self-conscious comment - ``*> NOT using 'not >'`` here,
    ``*> not using not < or not >`` in the bridge. So ``Access-Type 9``
    (``fn-not-greater-than``) IS REJECTED by both, which is what makes the
    bridge's ``when 9`` relation arm dead code - anomaly N-start-dead-arm.

    The four ``start`` verbs that follow [:L479-L503] are FOUR SEPARATE ``if``s,
    not a chain, in the order equal-to (5), not-less-than (8), greater-than (7),
    less-than (6) - NOT numeric order. Only one can fire, because all four test
    one field. Each answers ``move 21 to Fs-Reply`` on ``invalid key`` and
    leaves ``We-Error`` alone, unlike ``aa051-Reread``.

    The paragraph ends ``go to aa999-main-exit`` [:L508] with the comment
    "logging", above a commented-out ``go to aa041-Reread`` [:L509] and the
    maintainer's own unanswered question at [:L505-L506]: "Now go back and read
    next record ?? or just exit ? / IS GL USING START if so HOW ???? LEFT AS
    EXIT". So a START does NOT read - it positions only - and the caller must
    issue its own read-next. That is exactly how the bridge behaves too.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies the key.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``,
            ``ws_file_key`` and the status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: When the access type is in 5..8, each of
            which reaches a real ``start`` - omission O-1.
    """
    logging_data = file_access.logging_data
    # `move 205 to WS-No-Paragraph.` [common/acas007.cbl:L465]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa060-Process-Start"]
    )
    # `move zeros to fs-reply WE-Error.` [:L466-L467] - one statement, two
    # receivers. This is one of only three places the handler clears the pair.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `move zero to Cobol-File-Status.` [:L468]
    _HANDLER.cobol_file_status = 0
    # `move WS-Batch-Key to WS-File-Key Batch-Key.` [:L469-L470] - the first
    # receiver is observable, the second is the FD record's key.
    _store_ws_file_key(logging_data, batch_key_image(batch))

    # `if access-type < 5 or > 8` [:L472] - INCLUSIVE bounds, held in
    # START_ACCESS_TYPE_RANGE so this module and the bridge cannot drift.
    access_type = int(file_access.access_type)
    lowest, highest = START_ACCESS_TYPE_RANGE
    if access_type < lowest or access_type > highest:
        # `move 998 to WE-Error` [:L473] - AND NOTHING ELSE. ANOMALY
        # N-start-code-divergence: FS-Reply stays at the zero [:L466] just set,
        # so the caller reads a SUCCESS status carrying an error code. The
        # bridge answers (99, 997) for the same condition
        # [common/glbatchMT.cbl:L718-L722]. Not harmonised - a caller that
        # tests only FS-Reply sees a rejected START as successful.
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        # `go to aa999-main-exit` [:L474] - Class 3.
        aa999_main_exit(system, batch, file_access, file_defs, dal_common)
        return
    # `end-if` [:L475].

    # The four `start` blocks [:L479-L503], in the frozen source's own order:
    # equal-to, not-less-than, greater-than, less-than. Each is a real `start`
    # against `Batch-File`, so each is omission O-1. The relation is named in
    # the refusal so the message identifies which arm was taken.
    relation = START_RELATION_BY_ACCESS_TYPE.get(access_type, MOST_RELATION_DEFAULT)
    _indexed_file_verb(
        f"start key {relation.strip()}",
        "aa060-Process-Start",
        _START_VERB_LOCATORS[access_type],
        file_defs,
    )


def aa070_process_write(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa070-Process-Write.`` [common/acas007.cbl:L511-L520].

    Verbatim [:L512-L520]::

        move     206 to WS-No-Paragraph.
        move     WS-Batch-Record to Batch-Record.
        move     zeros to FS-Reply  WE-Error.
        move     zero to Cobol-File-Status.
        move     Batch-Key to WS-File-Key.
        write    Batch-Record invalid key
                 go to  aa999-main-exit.   *> logging
        move     Batch-Key to WS-File-Key.
        go       to aa999-main-exit.

    ⭐ THE ``invalid key`` PHRASE CONTAINS NOTHING BUT A TRANSFER [:L517-L518].
    No ``We-Error`` is written and no ``FS-Reply`` is written - the only reason
    the caller learns anything is that ``copybooks/selbatch.cob:L5`` declares
    ``status fs-reply``, so the ``write`` verb itself deposits the file status
    there. A duplicate key therefore answers ``(FS-Reply 22, We-Error 0)``, which
    is what the bridge produces too [common/glbatchMT.cbl:L836-L840] - the one
    place the two stores agree by accident rather than by design.

    ``move Batch-Key to WS-File-Key`` appears TWICE, at [:L516] before the write
    and at [:L519] after it, and the value cannot change between them. Recorded
    as a redundancy, not removed.

    ``move zeros to FS-Reply WE-Error`` [:L514] is one of only three places the
    handler clears the pair, and it is why a write - unlike a close, a rewrite's
    caller or a read-next's - cannot inherit a stale detail code.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies all twenty-one column values.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``,
            ``ws_file_key`` and the cleared status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always, at the ``write`` - omission O-1.
    """
    logging_data = file_access.logging_data
    # `move 206 to WS-No-Paragraph.` [common/acas007.cbl:L512]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa070-Process-Write"]
    )
    # `move WS-Batch-Record to Batch-Record.` [:L513] - a group move into the FD
    # record, which is not observable through any parameter. The two layouts are
    # identical [copybooks/fdbatch.cob:L11-L49] against
    # [copybooks/wsbatch.cob:L13-L54], so the move is byte for byte.
    # `move zeros to FS-Reply WE-Error.` [:L514]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `move zero to Cobol-File-Status.` [:L515]
    _HANDLER.cobol_file_status = 0
    # `move Batch-Key to WS-File-Key.` [:L516] - `Batch-Key` now holds what
    # `WS-Batch-Key` holds, the group move above having copied it.
    _store_ws_file_key(logging_data, batch_key_image(batch))
    # `write Batch-Record invalid key go to aa999-main-exit.` [:L517-L518] -
    # omission O-1.
    _indexed_file_verb(
        "write", "aa070-Process-Write", "[common/acas007.cbl:L517]", file_defs
    )


def aa080_process_delete(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa080-Process-Delete.`` [common/acas007.cbl:L522-L532].

    Verbatim, with the maintainer's comment [:L523-L532]::

        move     207 to WS-No-Paragraph.
        move     WS-Batch-Key to Batch-Key.
        move     WS-Batch-Key to WS-File-Key.
        move     zeros to FS-Reply  WE-Error.
        move     zero to Cobol-File-Status.
        *> Delete record and pointer if neccessary
        delete   Batch-File record.
        go       to aa999-main-exit.

    ⭐ THERE IS NO ``invalid key`` PHRASE AT ALL. Deleting a record that is not
    there is answered only by whatever the ``delete`` verb deposits in
    ``FS-Reply`` through ``copybooks/selbatch.cob:L5``, which is 23, with
    ``We-Error`` left at the zero [:L526] just set. The bridge answers the same
    condition ``(99, 995)`` [common/glbatchMT.cbl:L889-L890], so the two stores
    disagree completely about a missing row. Neither is changed.

    The two receivers of the key are written by TWO SEPARATE statements here
    [:L524-L525], where ``aa051-Reread`` and ``aa060-Process-Start`` use one
    statement with two receivers. Same effect, different spelling, both left.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies the key.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``,
            ``ws_file_key`` and the cleared status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always, at the ``delete`` - omission O-1.
    """
    logging_data = file_access.logging_data
    # `move 207 to WS-No-Paragraph.` [common/acas007.cbl:L523]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa080-Process-Delete"]
    )
    # `move WS-Batch-Key to Batch-Key.` [:L524] - the FD key, not observable.
    # `move WS-Batch-Key to WS-File-Key.` [:L525] - a SEPARATE statement here.
    _store_ws_file_key(logging_data, batch_key_image(batch))
    # `move zeros to FS-Reply WE-Error.` [:L526]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `move zero to Cobol-File-Status.` [:L527]
    _HANDLER.cobol_file_status = 0
    # `delete Batch-File record.` [:L531] - omission O-1, and with NO
    # `invalid key` phrase, so nothing here would have tested its outcome.
    _indexed_file_verb(
        "delete record", "aa080-Process-Delete", "[common/acas007.cbl:L531]", file_defs
    )


def aa090_process_rewrite(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa090-Process-Rewrite.`` [common/acas007.cbl:L534-L542].

    Verbatim [:L536-L542]::

        move     208 to WS-No-Paragraph.
        move     WS-Batch-Record to Batch-Record.
        move     zeros to FS-Reply  WE-Error.
        move     zero to Cobol-File-Status.
        move     Batch-Key to WS-File-Key.
        rewrite  Batch-Record.
        go       to aa999-main-exit.

    ⭐ NO ``invalid key`` PHRASE, exactly as in ``aa080-Process-Delete``, so a
    rewrite of a record that is not there is answered by the file status alone.
    The bridge answers that condition ``(99, 994)``
    [common/glbatchMT.cbl:L1016-L1017].

    Note that this paragraph is reached from the ``when 7`` arm of the dispatch,
    which PRECEDES the ``when 8`` delete arm [:L349-L352] even though 7 is
    numerically after 8's position in the verb table. That ordering is preserved
    in :data:`DISPATCH_ORDER`.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies all twenty-one column values.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``,
            ``ws_file_key`` and the cleared status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always, at the ``rewrite`` - omission O-1.
    """
    logging_data = file_access.logging_data
    # `move 208 to WS-No-Paragraph.` [common/acas007.cbl:L536]
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa090-Process-Rewrite"]
    )
    # `move WS-Batch-Record to Batch-Record.` [:L537] - the FD record.
    # `move zeros to FS-Reply WE-Error.` [:L538]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `move zero to Cobol-File-Status.` [:L539]
    _HANDLER.cobol_file_status = 0
    # `move Batch-Key to WS-File-Key.` [:L540]
    _store_ws_file_key(logging_data, batch_key_image(batch))
    # `rewrite Batch-Record.` [:L541] - omission O-1.
    _indexed_file_verb(
        "rewrite", "aa090-Process-Rewrite", "[common/acas007.cbl:L541]", file_defs
    )


def aa100_bad_function(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa100-Bad-Function.`` [common/acas007.cbl:L544-L549].

    Verbatim, with the maintainer's own heading [:L546-L549]::

        *> Houston; We have a problem
        move     999 to WE-Error.                         *> 999
        move     99  to fs-reply.

    ANOMALY N-badfunction-divergence, THREE WAYS. This paragraph answers
    ``(FS-Reply 99, We-Error 999)``. The bridge's equivalent answers
    ``(99, 990)`` [common/glbatchMT.cbl:L1030-L1031], writing the two fields in
    the same order but with a different code. And the authoritative table
    reserves a THIRD code for exactly this condition - ``992* = Invalid Function
    requested in File-Function`` [common/glpostingMT.cbl:L140] - while
    describing 999 as ``Not used here - Yet`` [:L134] and 990 as ``Unknown and
    unexpected error`` [:L141]. So the handler answers with a code documented as
    unused, the bridge with a code documented as unknown, and the code documented
    for the condition is set by no statement anywhere in the frozen tree. That
    last point is ``dal/status.py``'s own anomaly N6; nothing is harmonised.

    IT HAS NO TRANSFER OF CONTROL. The paragraph ends after two moves, so control
    FALLS THROUGH into ``aa999-main-exit`` [:L551] and on through
    ``aa-main-exit`` [:L556] into ``aa-Exit`` [:L560]. That chain is modelled as
    explicit calls below.

    IT IS REACHED TWICE OVER from ``aa010-main``: once by the ``when other`` arm
    of the dispatch [:L355-L356] and once by an unconditional ``go to`` placed
    immediately after the ``end-evaluate`` [:L360], under the comment "Should
    never get here but in case :(". The second is unreachable, because every
    ``when`` arm transfers control away first - see :func:`aa010_main`.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Receives the status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    # `move 999 to WE-Error.` [common/acas007.cbl:L548] - We-Error FIRST, as
    # written, and the same order the bridge uses [common/glbatchMT.cbl:L1030].
    file_access.we_error = int(WeError.NOT_USED)
    # `move 99 to fs-reply.` [:L549]
    file_access.fs_reply = int(FsReply.ERROR)
    # FALL-THROUGH into `aa999-main-exit` [:L551] - no `go to` here, so the
    # transfer is by source order and is modelled as an explicit call.
    aa999_main_exit(system, batch, file_access, file_defs, dal_common)


def aa999_main_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    fall_through: bool = True,
) -> None:
    """``aa999-main-exit.`` [common/acas007.cbl:L551-L554].

    Verbatim [:L552-L554]::

        if       Testing-1
                 perform Ca-Process-Logs
        end-if.

    The handler's single logging gate, and the target of every Class 3 transfer
    in ``aa-Process-Flat-File Section``. ``Testing-1`` is ``88 Testing-1 value
    1`` over ``SW-Testing`` [copybooks/Test-Data-Flags.cob:L10-L11], whose
    COPYBOOK DEFAULT IS 1, so logging is ON unless a caller clears it - the
    handler's own ``copy`` carries the reminder "set sw-testing to zero to stop
    logging" [common/acas007.cbl:L263].

    WHY ``fall_through`` EXISTS, AND WHY IT IS NOT AN INVENTION. This label is
    reached two different ways in the frozen source, and COBOL treats them
    differently:

    * ``go to aa999-main-exit`` - eleven sites - lands on the label and then
      CONTINUES IN SOURCE ORDER into ``aa-main-exit`` [:L556] and ``aa-Exit``
      [:L560], ending the program. That is ``fall_through=True``.
    * ``perform aa999-main-exit`` - ONE site, in ``aa030-Process-Close``
      [:L407] - executes this paragraph ALONE and RETURNS to the statement
      after the ``perform``, because a paragraph ``PERFORM`` ends at the next
      paragraph label. That is ``fall_through=False``, and it is what lets
      ``aa030`` go on to zero the function and log a SECOND time - anomaly
      N-close-double-log.

    Collapsing the two would either lose the close's second log record or run
    the program's exit chain in the middle of a paragraph. The distinction is
    the frozen source's, not this module's.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Passed to the logger.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``. Its ``SW-Testing`` is the gate.
        fall_through: ``True`` for the ``go to`` sites, ``False`` for
            ``aa030-Process-Close``'s ``perform`` [:L407].
    """
    # `if Testing-1` [common/acas007.cbl:L552]. Evaluated inline: the `88`
    # predicates live in `acas_posting.cobol.condition_names`, which Agent
    # Action Plan section 0.4.3's import table forbids `dal` importing.
    if int(dal_common.sw_testing) == 1:
        # `perform Ca-Process-Logs` [:L553]
        ca_process_logs(system, batch, file_access, file_defs, dal_common)
    # `end-if.` [:L554]
    if fall_through:
        # FALL-THROUGH into `aa-main-exit` [:L556], in source order.
        aa_main_exit(system, batch, file_access, file_defs, dal_common)


def aa_main_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa-main-exit.`` [common/acas007.cbl:L556-L558].

    An EMPTY paragraph - a label and two comment lines, verbatim::

         aa-main-exit.
        *>
        *> Now have processed cobol flat file,  so ..

    It has no statements at all, so its only behaviour is to be a transfer
    target and then fall through into ``aa-Exit`` [:L560]. Reproduced as a
    named function because rule R-5 maps every paragraph to a function, and
    because it IS a distinct transfer target: ``aa010-main`` transfers here
    rather than to ``aa999-main-exit`` on both relational branches [:L311,
    :L319], which is how the relational path avoids logging twice, and
    ``aa030-Process-Close`` transfers here after its own second log [:L411].

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Untouched.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
    """
    # No statements [common/acas007.cbl:L556-L558]. FALL-THROUGH into `aa-Exit`
    # [:L560], in source order.
    aa_exit(system, batch, file_access, file_defs, dal_common)


def aa_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa-Exit.`` [common/acas007.cbl:L560-L561].

    One statement, verbatim::

         aa-Exit.
             exit program.

    ``exit program`` returns to the caller of ``acas007``, which in Python is
    :func:`dispatch` returning. Nothing is written, no status is set and no
    process is ended - a called COBOL subprogram's ``exit program`` is a return,
    not a ``stop run``, and treating it as a process exit would be a behaviour
    change of the most drastic kind.

    Reproduced as a named function rather than folded away because it is the
    LAST link of the fall-through chain ``aa100-Bad-Function`` ->
    ``aa999-main-exit`` -> ``aa-main-exit`` -> ``aa-Exit``, and a reader
    following that chain in the frozen source must find every link here.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Untouched.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
    """
    # `exit program.` [common/acas007.cbl:L561] - a return to the caller.
    #  NO RECORD. `exit program` [common/acas007.cbl:L561] displays nothing; a
    #  trace of reaching it is an invented event (rule R-4), and the status pair it
    #  reported is already in the caller's own `File-Access` block, which is where
    #  the frozen source leaves it.


def ba_process_rdbms(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba-Process-RDBMS section.`` [common/acas007.cbl:L563-L569].

    The relational section, and the ONLY route from this handler to the bridge.
    Its heading comment states the contract, verbatim [:L566-L569]::

        *>  Here we call the relevent RDBMS module for this table            *
        *>   which will include processing any other joined tables as needed *

    A SECTION ``PERFORM`` runs from the section's first paragraph to the end of
    the section, so ``perform ba-Process-RDBMS`` [:L310, :L318] executes the
    whole chain ``ba010-Test-WS-Rec-Size`` -> ``ba012-Test-WS-Rec-Size-2`` ->
    ``ba015-Test-Ends`` -> ``ba020-Process-DAL`` -> ``ba-rdbms-exit``, every link
    of it by FALL-THROUGH. Each fall-through is written as an explicit call in
    the function it happens in, and one of them - ``ba015`` into ``ba020`` -
    IS ANOMALY N18b's second bridge invocation.

    Note the section's name lowercases ``section`` [:L563] where
    ``aa-Process-Flat-File Section.`` capitalises it [:L274]. The same
    inconsistency appears in the bridge, whose ``ba-Process-RDBMS section`` is
    also lower case [common/glbatchMT.cbl:L336]. Left as written.

    Args:
        system: ``System-Record``. Supplies the credentials on the first call.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``. Not read on this path - the relational store
            has no ``assign`` clause.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    # A section PERFORM enters at the first paragraph [common/acas007.cbl:L571].
    ba010_test_ws_rec_size(system, batch, file_access, file_defs, dal_common)


def ba010_test_ws_rec_size(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas007.cbl:L571-L577].

    ONE STATEMENT, and it is not the one the paragraph is named for. Verbatim,
    comments and all [:L572-L577]::

        *>     Test on very first call only  (So do NOT use var A & B again)
        *>       Lets test that Data-record size is = or > than declared Rec in DAL
        *>          as we cant adjust at compile/run time due to ALL Cobol compilers ?
        move     23 to WS-Log-File-no.        *> for FHlogger

    The three comment lines describe the record-size test - which lives in the
    NEXT paragraph, ``ba012-Test-WS-Rec-Size-2`` - while the only statement here
    sets the log file number. The paragraph is a comment block with a stray
    ``move``, and the naming is left as it is.

    ANOMALY N-log, STAGE TWO. ``aa010-main`` set ``WS-Log-File-No`` to 13
    [:L281]; this overwrites it with 23, so EVERY LOG RECORD FROM THE RELATIONAL
    PATH CARRIES 23 AND EVERY LOG RECORD FROM THE INDEXED PATH CARRIES 13, from
    one handler serving one table. The family is systematic - ``acas005`` 11 to
    21, ``acas006`` 12 to 22, ``acas007`` 13 to 23, ``acas008`` 15 to 25, with 14
    skipped - and the receiving field is spelled ``WS-Log-File-no`` here against
    ``WS-Log-File-No`` at [:L281], a capitalisation difference COBOL ignores and
    a reader should not.

    Control then FALLS THROUGH into ``ba012-Test-WS-Rec-Size-2`` [:L579].

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``. Receives ``ws_log_file_no``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    logging_data = file_access.logging_data
    # `move 23 to WS-Log-File-no.` [common/acas007.cbl:L577] - ANOMALY N-log.
    logging_data.ws_log_file_no = _LOGGING_FIELDS["WS-Log-File-No"].store(
        WS_LOG_FILE_NO_RDB_PATH
    )
    # FALL-THROUGH into `ba012-Test-WS-Rec-Size-2` [:L579].
    if ba012_test_ws_rec_size_2(system, batch, file_access, file_defs, dal_common):
        # `ba012` took its `go to ba-rdbms-exit` [:L607], whose `exit section`
        # [:L650] ends this section, so `ba015-Test-Ends` and therefore the
        # bridge are NOT reached. ANOMALY N-901-sticky's second effect: no
        # bridge call at all for this request.
        return
    # FALL-THROUGH into `ba015-Test-Ends` [:L622].
    ba015_test_ends(system, batch, file_access, file_defs, dal_common)


def ba012_test_ws_rec_size_2(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas007.cbl:L579-L620].

    THE FIRST-CALL-ONLY BLOCK: the record-length comparison and the credential
    load, both inside one ``if A = zero``. Verbatim [:L581-L620]::

        if       A = zero                        *> so it is being called first time
                 move     function Length ( WS-Batch-Record ) to A
                 move     function length ( Batch-Record ) to B
                 if   A < B
                      move 901 to WE-Error
                      move 99 to fs-reply
                 end-if
                 if       WE-Error = 901
                          move spaces to Display-Blk
                          string GL904          delimited by size
                                 A              delimited by size
                                 " < "          delimited by size
                                 "Batch-Rec = " delimited by size
                                 B              delimited by size    into Display-Blk
                          end-string
                          display Display-Blk at 2301 with erase eol
                          display GL901 at 2401 with erase eol
                          move  Display-Blk to SQL-Msg
                          if  Testing-1
                              perform Ca-Process-Logs
                          end-if
                          accept Accept-Reply at 2433
                          go to ba-rdbms-exit
                 end-if
                 move     RDBMS-DB-Name to DB-Schema
                 move     RDBMS-User    to DB-UName
                 move     RDBMS-Passwd  to DB-UPass
                 move     RDBMS-Port    to DB-Port
                 move     RDBMS-Host    to DB-Host
                 move     RDBMS-Socket  to DB-Socket
        end-if.

    FOUR THINGS, and three of them are anomalies.

    ANOMALY A-1, WHICH ``dal/connection.py`` OWNS. ``A`` is assigned INSIDE the
    guarded block, so the block runs exactly once per run and from the second
    call onward the record check AND the credential load are BOTH skipped. A
    change to the ``SYSTEM-REC`` row part-way through a run therefore cannot
    affect that run. Delegated to
    :func:`~acas_posting.dal.connection.load_rdb_data_once`, which reproduces it
    and states it in full - OMISSION O-5, delegated rather than duplicated.

    ANOMALY N-901-unreachable. ``copybooks/fdbatch.cob:L11-L49`` declares FIELD
    FOR FIELD the same layout as ``copybooks/wsbatch.cob:L13-L54`` - the only
    difference is ``03 WS-Batch-Key9 redefines WS-Batch-Key``, and a ``REDEFINES``
    adds no length - so ``A`` and ``B`` are necessarily EQUAL and ``A < B`` CAN
    NEVER BE TRUE. GnuCOBOL 3.2 measures both at 96, which is AMBIGUITY Q-4
    RESOLVED ON THE COMPILED ORACLE and is why :data:`WS_BATCH_RECORD_LENGTH` is
    one constant serving both operands. ANOMALY A-15 - the maintainer's own
    "98 bytes ... but function length (Batch-record) says 98?" [:L7-L9 of both
    copybooks] - stays on record; the comment is frozen text and only the
    behaviour is settled.

    ⭐ ANOMALY N-901-STICKY, AND IT IS REACHABLE. The second ``if`` tests
    ``WE-Error = 901`` [:L592] - THE CALLER'S FIELD, which nothing has cleared,
    because ``aa010-main``'s own zeroing of ``WE-Error`` and ``FS-Reply`` is
    COMMENTED OUT [:L334-L335] and reaches this paragraph only afterwards anyway.
    So a caller arriving with a stale 901 takes this branch even though the
    lengths agree, and three consequences follow. It is answered with ITS OWN
    incoming ``FS-Reply``, because only the ``A < B`` arm writes 99 and that arm
    did not run. The credential moves [:L614-L619] are SKIPPED. And ``A`` was
    already assigned at [:L582-L584] before the test, so the first-call guard is
    now CLOSED FOR THE REST OF THE RUN and the credentials are never loaded at
    all. Reproduced exactly; nothing is cleared to prevent it.

    OMISSION O-3, the presentation. The two ``display``s at 2301 and 2401
    [:L600-L601] and the ``accept Accept-Reply at 2433`` [:L606] are screen work
    with no database effect. Per Agent Action Plan section 0.3.4 the diagnostic
    becomes a log record and the pause is dropped, while THE CONTROL TRANSFER
    THAT FOLLOWS IT IS PRESERVED - and so is the ``move Display-Blk to SQL-Msg``
    [:L602], because ``SQL-Msg`` is part of ``File-Access`` and the caller reads
    it. ``Accept-Reply`` is left exactly as the caller had it, since no operator
    replies.

    Returns:
        ``True`` when the 901 branch took its ``go to ba-rdbms-exit`` [:L607],
        which ends ``ba-Process-RDBMS section`` and so prevents ``ba015-Test-Ends``
        and the bridge from being reached at all. ``False`` on every other path,
        including the second and later calls of a run, which do nothing.

    Args:
        system: ``System-Record``. Its six ``RDBMS-`` items are the credentials.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. May receive ``sql_msg`` on the 901 branch.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Its ``SW-Testing`` gates the log.
    """
    logging_data = file_access.logging_data
    # `if A = zero` [common/acas007.cbl:L581] - the first-call sentinel. `A` is
    # `77 A pic 9(4) value zero` [:L240], WORKING-STORAGE, so it persists across
    # calls exactly as `_HANDLER` does.
    if _HANDLER.a != 0:
        # `end-if.` [:L620]. No `else` exists and none is added: a later call
        # simply does nothing here.
        return False

    # `move function Length (WS-Batch-Record) to A` [:L582-L584] and
    # `move function length (Batch-Record) to B` [:L585-L587]. ONE constant for
    # both operands - see WS_BATCH_RECORD_LENGTH for why that is faithful and
    # not a simplification: the two records have identical layouts.
    _HANDLER.a = WS_BATCH_RECORD_LENGTH
    _HANDLER.b = WS_BATCH_RECORD_LENGTH

    # `if A < B` [:L588] - ANOMALY N-901-unreachable, false by construction. Kept
    # as an executed comparison rather than folded away, because folding it would
    # hide that the frozen program still performs it, and because a future change
    # to either copybook would make it fire.
    if _HANDLER.a < _HANDLER.b:  # pragma: no cover - see N-901-unreachable
        # `move 901 to WE-Error` [:L589] then `move 99 to fs-reply` [:L590], with
        # the source's own comments naming the fault and the reason for the
        # tolerance: "901 Programming error; temp rec length is wrong caller must
        # stop" and "allow for last field ( FILLER) not being present in layout."
        file_access.we_error = RECORD_SIZE_WE_ERROR
        file_access.fs_reply = int(FsReply.ERROR)
    # `end-if` [:L591]

    # `if WE-Error = 901` [:L592] - ⭐ ANOMALY N-901-STICKY. The CALLER's field,
    # which nothing cleared, so a stale 901 arrives here intact and takes this
    # branch with the lengths in perfect agreement. The source's own comment on
    # the line reads "record length wrong so display error, accept and then stop
    # run" - and it does not stop the run; it exits the section.
    if int(file_access.we_error) == RECORD_SIZE_WE_ERROR:
        # `move spaces to Display-Blk` [:L593], then the STRING [:L594-L599].
        # Five sending items, all `delimited by size`, so each contributes its
        # FULL declared width: GL904 32 characters, `A` four digits, " < " three,
        # "Batch-Rec = " twelve, `B` four digits - 55 in all, and the receiver's
        # remaining 20 positions keep the spaces the `move` just put there,
        # because STRING does not pad.
        assembled = (
            f"{ERROR_MESSAGE_GL904}"
            f"{_HANDLER.a:0{_RECORD_LENGTH_PICTURE_DIGITS}d}"
            f" < "
            f"Batch-Rec = "
            f"{_HANDLER.b:0{_RECORD_LENGTH_PICTURE_DIGITS}d}"
        )
        _HANDLER.display_blk = assembled[:_DISPLAY_BLK_WIDTH].ljust(
            _DISPLAY_BLK_WIDTH
        )
        # `display Display-Blk at 2301 with erase eol` [:L600] and
        # `display GL901 at 2401 with erase eol` [:L601] - OMISSION O-3. The two
        # screen writes become one log record; neither alters control flow.
        #  ONLY THE SUBSTANTIVE HALF. `Display-Blk` is `GL902 Program Error: Temp
        #  rec = ` plus the two record lengths - a fault and its evidence, both
        #  compile-time constants. `GL901 Note error and hit return`
        #  [common/acas007.cbl:L601] is an acknowledgement prompt and nothing else,
        #  so it is dropped rather than quoted: quoting a prompt in a log record is
        #  still emitting the prompt. The transfer to `ba-rdbms-exit` is kept.
        _LOG.error(
            "%s [common/acas007.cbl:L600] - the caller must stop",
            _HANDLER.display_blk.rstrip(),
        )
        # `move Display-Blk to SQL-Msg` [:L602] - NOT presentation: `SQL-Msg` is
        # part of `File-Access` [copybooks/wsfnctn.cob:L51] and the caller reads
        # it, so the 75 characters are fitted into its `pic x(512)`.
        _store_sql_msg(logging_data, _HANDLER.display_blk)
        # `if Testing-1 perform Ca-Process-Logs end-if` [:L603-L605]. Note that
        # this is a DAL access logging through the handler's own logger, which
        # the logger paragraph's own comment says does not happen - see
        # :func:`ca_process_logs`.
        if int(dal_common.sw_testing) == 1:
            ca_process_logs(system, batch, file_access, file_defs, dal_common)
        # `accept Accept-Reply at 2433` [:L606] - OMISSION O-3. A pause whose
        # only effect is to block a terminal, so it is dropped and
        # `Accept-Reply` is left exactly as the caller had it. Per Agent Action
        # Plan section 0.3.4 the transfer that follows is preserved.
        # `go to ba-rdbms-exit` [:L607] - Class 3, out of this paragraph and out
        # of the section. Reported to the caller so the fall-through chain stops.
        ba_rdbms_exit(system, batch, file_access, file_defs, dal_common)
        return True
    # `end-if` [:L608]

    # The six credential moves [:L614-L619], under the maintainer's own comments
    # "Not a error comparing the length of records so - -" and "Load up the DB
    # settings from the system record as its not passed on / hopefully once is
    # enough  :)". DELEGATED, NOT DUPLICATED - omission O-5:
    # `connection.load_rdb_data_once` performs exactly these six moves, in this
    # order, and owns anomaly A-1's first-call-only semantics.
    load_rdb_data_once(system)
    # `end-if.` [:L620]
    return False


def ba015_test_ends(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba015-Test-Ends.`` [common/acas007.cbl:L622-L631].

    ⭐⭐ ANOMALY N18b, STAGE TWO - THE PARAGRAPH THAT MAKES ONE REQUEST INTO TWO
    BRIDGE CALLS. Verbatim, comments included [:L624-L631]::

         ba015-Test-Ends.
        *>
        *>  First check if there is an open output and if so open 1st then
        *>   we need to force a DELETE-ALL call to the DAL. [ Backup code ].
        *>
             if       fn-Open
                and   fn-Output
                      perform ba020-Process-Dal
                      set fn-Delete-All to true
             end-if.

    and then the paragraph ENDS - with no transfer of control - so execution
    CONTINUES IN SOURCE ORDER into ``ba020-Process-DAL`` [:L640]. The bridge is
    therefore called a SECOND time, and by then ``File-Function`` is 6.

    THE FULL SEQUENCE FOR ONE ``Open`` PLUS ``Output`` REQUEST:

    1. ``aa010-main`` sees ``fn-Open and fn-output and not FS-Cobol-Files-Used``
       and performs this section [:L305-L312] WITHOUT coercing the function - the
       two lines that would have done so are commented out.
    2. This paragraph's ``perform ba020-Process-Dal`` [:L629] calls the bridge
       with ``File-Function = fn-Open (1)`` and ``Access-Type = fn-Output (3)``,
       so the bridge opens a connection [common/glbatchMT.cbl:L397-L439].
    3. ``set fn-Delete-All to true`` [:L630] writes 6 into the CALLER'S
       ``File-Function``. It does NOT touch ``Access-Type``, which stays 3,
       because the ``move zero to access-type`` that would have cleared it is the
       other commented-out line [:L309].
    4. The fall-through into ``ba020-Process-DAL`` [:L640] calls the bridge a
       SECOND time, now reaching ``when 6 -> ba085-Process-DELETE-ALL``
       [common/glbatchMT.cbl:L385-L386], which deletes every row below the key
       999999 - anomaly N-deleteall-999999.
    5. The caller gets back a ``File-Function`` of 6 that it never set, and the
       status of the DELETE-ALL rather than of the open.

    THREE HANDLERS IN THE SAME FAMILY DO THREE DIFFERENT THINGS with this block,
    and all three are preserved as they are:

    * ``acas005`` has the whole block COMMENTED OUT, with the reason given
      inline - "NOT used with GL." [common/acas005.cbl:L307].
    * ``acas006`` and ``acas007`` are TWO-STAGE, as above.
    * ``acas008`` COERCES FIRST - ``set fn-delete-all to true`` comes BEFORE its
      ``perform`` [common/acas008.cbl:L313-L319] - so it makes ONE call, and that
      call is a DELETE-ALL rather than an open.

    Do not collapse the two calls, do not coerce the function early, and do not
    skip the block: a defect reproduced is correct and a defect fixed is a
    failure (rule R-4).

    Note also that this paragraph is unreachable from ``aa010-main``'s
    ``perform ba012-Test-WS-Rec-Size-2`` [:L324], which performs ONE PARAGRAPH
    and therefore does not fall through to here. So N18b belongs to the
    relational path alone.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``. Its ``file_function`` IS OVERWRITTEN with
            ``fn-Delete-All`` between the two calls.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    # `if fn-Open and fn-Output` [common/acas007.cbl:L627-L628].
    if int(file_access.file_function) == int(FileFunction.OPEN) and int(
        file_access.access_type
    ) == int(AccessType.OUTPUT):
        # `perform ba020-Process-Dal` [:L629] - BRIDGE CALL ONE, still carrying
        # fn-Open and fn-Output, so the bridge opens the connection.
        #  NO RECORD. The double call of anomaly N18b is reproduced by making the
        #  call twice, which is the behaviour; announcing it is a diagnostic the
        #  frozen source does not have (rule R-4). N18b is documented in
        #  `docs/migration/anomaly-log.md`.
        ba020_process_dal(system, batch, file_access, file_defs, dal_common)
        # `set fn-Delete-All to true` [:L630] - writes 6 into the CALLER's
        # `File-Function` AFTER the open has already happened. `Access-Type` is
        # deliberately left at fn-Output, because the `move zero to access-type`
        # that would have cleared it is commented out at [:L309].
        file_access.file_function = int(FileFunction.DELETE_ALL)
    # `end-if.` [:L631]
    # FALL-THROUGH into `ba020-Process-DAL` [:L640] - the SECOND bridge call on
    # the Open-plus-Output path, and the only call on every other path. Written
    # as an explicit call because the frozen source relies on source order and
    # nothing else marks the boundary.
    ba020_process_dal(system, batch, file_access, file_defs, dal_common)


def ba020_process_dal(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba020-Process-DAL.`` [common/acas007.cbl:L640-L645].

    THE CALL, verbatim, and the reason :func:`glbatch_mt` takes three parameters
    with ``File-Access`` first::

         ba020-Process-DAL.
             call     "glbatchMT" using File-Access
                                          ACAS-DAL-Common-data

                                          WS-Batch-Record
             end-call.

    ``System-Record`` and ``File-Defs`` are NOT passed. The bridge needs neither:
    the credentials reached it through ``RDB-Data``, which
    ``ba012-Test-WS-Rec-Size-2`` loaded on the first call of the run [:L614-L619],
    and the relational store has no ``assign`` clause. :func:`dispatch` keeps the
    ``System-Record`` resident for the duration of the call chain so that
    :func:`mt_ba020_process_open` can still reach it - see
    :class:`BridgeCalledOutsideHandlerError`.

    The comments around the call are worth keeping in view. Above it the
    maintainer plans a compiler directive that was never written [:L633-L638]:
    "HERE we need a CDF [Compiler Directive] to select the correct DAL based on
    the pre SQL compiler ... Do this after system testing and pre code release. /
    NOW SET UP FOR JC pre-sql compiler system." Below it, the error contract in
    one line [:L647]: "Any errors leave it to caller to recover from" - which is
    why this paragraph tests nothing after the call and why no status is
    manufactured here.

    Called TWICE for one ``Open`` plus ``Output`` request - once by
    ``ba015-Test-Ends``' ``perform`` and once by falling through into it. See
    :func:`ba015_test_ends` for anomaly N18b in full.

    Control then FALLS THROUGH into ``ba-rdbms-exit`` [:L649].

    Args:
        system: ``System-Record``. Not passed to the bridge; carried because
            every paragraph in this module has the handler's five parameters.
        batch: ``WS-Batch-Record``. The bridge's third parameter.
        file_access: ``File-Access``. The bridge's FIRST parameter.
        file_defs: ``File-Defs``. Not passed to the bridge.
        dal_common: ``ACAS-DAL-Common-data``. The bridge's second parameter.
    """
    # `call "glbatchMT" using File-Access ACAS-DAL-Common-data WS-Batch-Record`
    # [common/acas007.cbl:L641-L645] - THE BRIDGE'S OWN ORDER, File-Access first,
    # and `System-Record` and `File-Defs` deliberately NOT among the three.
    glbatch_mt(file_access, dal_common, batch)
    # `end-call.` [:L645]. No status test follows - "Any errors leave it to
    # caller to recover from" [:L647]. FALL-THROUGH into `ba-rdbms-exit` [:L649].
    ba_rdbms_exit(system, batch, file_access, file_defs, dal_common)


def ba_rdbms_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba-rdbms-exit.`` [common/acas007.cbl:L649-L650].

    One statement, verbatim, with the maintainer's own underline beneath it::

         ba-rdbms-exit.
             exit     section.
        *>   ****     *******

    ``exit section`` returns from ``ba-Process-RDBMS section``, so on the normal
    path control resumes at the statement after ``perform ba-Process-RDBMS`` in
    ``aa010-main`` - which is ``go to AA-Main-Exit`` on both branches [:L311,
    :L319].

    IT IS ALSO THE TARGET OF THE 901 BRANCH'S ``go to`` [:L607], and that is
    AMBIGUITY Q-5. Reached that way, the ``exit section`` unwinds a
    ``perform`` of a single paragraph rather than of the section, and since
    ``Ca-Process-Logs`` and ``ca-Exit`` are paragraphs INSIDE this section
    [:L653-L659] there is no following section to fall into - control runs off
    the end of the PROCEDURE DIVISION, which in a called subprogram is an
    implicit ``exit program``. That reading is the one implemented, in
    :func:`aa010_main`, and it is recorded rather than assumed because unwinding
    a live perform stack is implementation-specific.

    NOTE WHAT IT DOES NOT DO. It does not close the connection, does not free a
    cursor and does not commit: the bridge owns all three, and no in-scope bridge
    contains a ``COMMIT`` or ``ROLLBACK`` at all.

    Args:
        system: ``System-Record``. Untouched.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Untouched.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
    """
    del system, batch, file_defs, dal_common
    # `exit section.` [common/acas007.cbl:L650] - a return, nothing more.
    #  NO RECORD, for the same reason as `aa999-main-exit`: an exit paragraph that
    #  displays nothing has no diagnostic to reproduce (rule R-4).


def ca_process_logs(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``Ca-Process-Logs.`` [common/acas007.cbl:L653-L657].

    Verbatim, with the paragraph's own trailing comment [:L653-L657]::

         Ca-Process-Logs. *> Not called on DAL access as it does it already
        *>**************
        *>
             call     "fhlogger" using File-Access
                                       ACAS-DAL-Common-data.

    OMISSION O-2. ``fhlogger`` is a COBOL program, and rule R-1 forbids the
    Python implementation from executing, embedding or shelling out to one - "The
    shipped artifact must run on a host with no COBOL compiler and no COBOL
    runtime present." Its effect is a log record with no database effect, so per
    Agent Action Plan section 0.3.4 it becomes a log record here at the severity
    the original's intent implies. Nothing branches on it and it appears in no
    table dump.

    ⭐ THE PARAGRAPH'S OWN COMMENT IS WRONG. "Not called on DAL access as it does
    it already" describes the design - the bridge logs for itself at
    ``ba999-end`` [common/glbatchMT.cbl:L1053-L1055] - but
    ``ba012-Test-WS-Rec-Size-2`` calls this paragraph on its 901 branch [:L604],
    and that branch is squarely on the DAL path. So on that one route BOTH loggers
    can run for one request. Recorded, not corrected.

    Note also that ``File-Defs``, ``System-Record`` and ``WS-Batch-Record`` are
    NOT passed to ``fhlogger`` - only the two blocks the ``using`` list names -
    which is why nothing about the record or the credentials can reach a log
    record from here.

    Control then FALLS THROUGH into ``ca-Exit`` [:L659].

    Args:
        system: ``System-Record``. Not logged; not in the ``using`` list.
        batch: ``WS-Batch-Record``. Not logged; not in the ``using`` list.
        file_access: ``File-Access``. Every field the log record reports.
        file_defs: ``File-Defs``. Not logged; not in the ``using`` list.
        dal_common: ``ACAS-DAL-Common-data``. The second ``using`` item.
    """
    # `call "fhlogger" using File-Access ACAS-DAL-Common-data.`
    # [common/acas007.cbl:L656-L657] - OMISSION O-2 under rule R-1. Only the two
    # blocks the `using` list names reach the record; `System-Record`,
    # `WS-Batch-Record` and `File-Defs` are carried for the fall-through below
    # and contribute NOTHING to it, exactly as the CALL contributes nothing.
    logging_data = file_access.logging_data
    # The driver's own text is redacted before it reaches the record: a server
    # message can carry the connection's account, host, key values and a line
    # feed (CWE-117, CWE-532). The ACAS status values are integers from this
    # module's own enumerations and are interpolated as themselves.
    #  THE ONE ADAPTER - see the note on the bridge's own logging paragraph above
    #  for which fields are withheld and why.
    log_file_handler_record(
        _LOG,
        program=HANDLER,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=file_access.file_function,
        access_type=file_access.access_type,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=str(logging_data.sql_err),
        sql_state=str(logging_data.sql_state),
        dal_common=dal_common,
    )
    # FALL-THROUGH into `ca-Exit` [:L659].
    ca_exit(system, batch, file_access, file_defs, dal_common)


def ca_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ca-Exit.     exit.`` [common/acas007.cbl:L659].

    The last paragraph of the program, and the last statement before
    ``end program acas007.`` [:L662]. ``exit`` on its own is a COBOL no-operation
    - it is NOT ``exit program`` and NOT ``exit section`` - so its only purpose is
    to give ``Ca-Process-Logs`` a terminating label, which is what makes
    ``perform Ca-Process-Logs`` return to its caller rather than run on.

    Written on ONE LINE in the frozen source, label and statement together, which
    is why its locator is a single line rather than a range.

    Reproduced as a named function because rule R-5 maps every paragraph to a
    function and because a reader following ``perform Ca-Process-Logs`` must find
    where it ends. It carries the handler's five linkage parameters like every
    other paragraph in this section, uniformly, even though it reads none of
    them: a paragraph signature that varied by paragraph would defeat the
    mechanical check that every one of them binds the same linkage.

    Args:
        system: ``System-Record``. Untouched.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Untouched.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
    """
    del system, batch, file_access, file_defs, dal_common
    # `exit.` [common/acas007.cbl:L659] - a no-operation, then `end program`.
