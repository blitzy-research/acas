"""GL-Posting data access: COBOL file handler ``acas006`` and bridge ``glpostingMT``.

This module is the Python reimplementation of one handler-and-bridge pair of the
ACAS file-handler layer, serving the ``GLPOSTING-REC`` table.  The Agent Action
Plan describes the boundary in §0.3.1: "One data-access module per handler, not
per table. ... Mirroring the handler boundary rather than the table boundary
keeps the Python module set in exact correspondence with the COBOL programs that
the traceability document must map, and preserves the dispatch semantics rather
than flattening them."

The spine, from AAP §0.2.1.1:

===================  ===============================================
Entity facade        ``GL-Posting``
Handler              ``acas006``          [common/acas006.cbl]
Bridge               ``glpostingMT``      [common/glpostingMT.cbl]
                                          [common/glpostingMT.scb]
Table                ``GLPOSTING-REC``    [mysql/ACASDB.sql:L154-L170]
Record copybook      ``wspost.cob``       [copybooks/wspost.cob:L12-L28]
Record class         :class:`acas_posting.records.gl_posting.WsPostingRecord`
File description     ``fdpost.cob``       [copybooks/fdpost.cob:L10-L28]
SELECT clause        ``selpost.cob``      [copybooks/selpost.cob]
===================  ===============================================

``glpostingMT`` is the canonical bridge of this migration.  The AAP quotes its
host-variable group, its load paragraph, its cursor comment and its status table
in §0.4.1.5, §0.6.2 and §0.9.4, and :mod:`acas_posting.dal.status` was built
from its status table.  The transcription here is therefore the reference the
remaining nineteen bridges are checked against.

There is no user rules document for this project: ``review_rules`` reports "No
user rules provided."  The six binding rules R-1 to R-6 live in AAP §0.7.2 and
are restated where they bear on the code below.  Anything the AAP is silent on
is held to enterprise-standard best practice.


The two published signatures
============================

Both calling conventions the COBOL uses are published, per R-5 ("Every program
must map to a module, every paragraph to a function, and every field to a
data-dictionary entry") and AAP §0.4.3.

The handler linkage takes **five** parameters [common/acas006.cbl:L273-L279]::

    L273   Procedure Division Using System-Record
    L275                            WS-Posting-Record
    L277                            File-Access
    L278                            File-Defs
    L279                            ACAS-DAL-Common-data.

    FROM:  call "acas006" using System-Record WS-Posting-Record File-Access
                                File-Defs ACAS-DAL-Common-data
    TO:    acas006_gl_posting.dispatch(system, posting, file_access,
                                       file_defs, dal_common)

The bridge call takes **three**, with ``File-Access`` **first**.  The ``CALL``
statement and its three parameters occupy [common/acas006.cbl:L654-L657]; the
``end-call`` closes it at [common/acas006.cbl:L658], so the paragraph as a whole
is [common/acas006.cbl:L653-L658]::

    L653   ba020-Process-DAL.
    L654       call     "glpostingMT" using File-Access
    L655                                    ACAS-DAL-Common-data
    L657                                    WS-Posting-Record
    L658       end-call.

    TO:    acas006_gl_posting.glposting_mt(file_access, dal_common, posting)

The caller of the handler is the entity facade, whose dispatch paragraph sets
the key number before the ``CALL`` [copybooks/Proc-ACAS-FH-Calls.cob:L43-L49]:
``move 1 to File-Key-No.``  Both entry points mutate ``file_access`` in place
and return ``None``, exactly as a COBOL ``CALL ... USING`` does; there is no
return value to inspect.


Paragraph inventory and the naming rule
=======================================

R-5 requires one function per paragraph.  Each function below carries its
``[common/acas006.cbl:L<n>]`` or ``[common/glpostingMT.cbl:L<n>]`` locator, and
every ``GO TO`` transfer site is annotated with its class from the AAP §0.4.2
four-class taxonomy: Class 1 loop-back becomes ``continue`` inside
``while True:``; Class 2 forward terminator becomes ``break`` plus faithful
placement of the post-loop work; Class 3 section or paragraph exit becomes
``return``; Class 4 sibling re-dispatch becomes a named call followed by an
explicit ``continue`` or ``return``.

Python names are derived from the **full** COBOL paragraph name, which resolves
the two programs' apparent collisions on their own: the handler's
``ba010-Test-WS-Rec-Size`` and the bridge's ``ba010-Initialise`` are distinct
names, as are ``ba020-Process-DAL`` and ``ba020-Process-Open``.  Only
``Ca-Process-Logs`` and ``ca-Exit`` appear identically in both programs; the
bridge's copies carry an ``mt_`` prefix after the bridge program name.

Handler ``acas006`` (24 paragraphs):

===============================  =====  =============================
``aa-Process-Flat-File`` section  L282  :func:`aa_process_flat_file`
``aa010-main``                    L284  :func:`aa010_main`
``aa020-Process-Open``            L368  :func:`aa020_process_open`
``aa030-Process-Close``           L406  :func:`aa030_process_close`
``aa040-Process-Read-Next``       L419  :func:`aa040_process_read_next`
``aa041-Reread``                  L436  :func:`aa041_reread`
``aa050-Process-Read-Indexed``    L452  :func:`aa050_process_read_indexed`
``aa051-Reread``                  L461  :func:`aa051_reread`
``aa060-Process-Start``           L473  :func:`aa060_process_start`
``aa070-Process-Write``           L522  :func:`aa070_process_write`
``aa080-Process-Delete``          L534  :func:`aa080_process_delete`
``aa090-Process-Rewrite``         L547  :func:`aa090_process_rewrite`
``aa100-Bad-Function``            L557  :func:`aa100_bad_function`
``aa999-main-exit``               L564  :func:`aa999_main_exit`
``aa-main-exit``                  L569  :func:`aa_main_exit`
``aa-Exit``                       L573  :func:`aa_exit`
``ba-Process-RDBMS`` section      L576  :func:`ba_process_rdbms`
``ba010-Test-WS-Rec-Size``        L584  :func:`ba010_test_ws_rec_size`
``ba012-Test-WS-Rec-Size-2``      L592  :func:`ba012_test_ws_rec_size_2`
``ba015-Test-Ends``               L635  :func:`ba015_test_ends`
``ba020-Process-DAL``             L653  :func:`ba020_process_dal`
``ba-rdbms-exit``                 L662  :func:`ba_rdbms_exit`
``Ca-Process-Logs``               L666  :func:`ca_process_logs`
``ca-Exit``                       L672  :func:`ca_exit`
===============================  =====  =============================

``acas006`` has **two** reread paragraphs — ``aa041-Reread`` after read-next and
``aa051-Reread`` after read-indexed.  Its sibling ``acas005`` has only
``aa041-Reread``, plus an ``aa047-Eval-Keys`` that ``acas006`` lacks entirely.
The divergence is recorded, not harmonised.

Bridge ``glpostingMT`` (24 paragraphs and sections):

=================================  ======  ===============================
``ba-ACAS-DAL-Process`` section      L334  :func:`ba_acas_dal_process`
``ba010-Initialise``                 L345  :func:`ba010_initialise`
``ba020-Process-Open``               L389  :func:`ba020_process_open`
``ba030-Process-Close``              L433  :func:`ba030_process_close`
``ba040-Process-Read-Next``          L448  :func:`ba040_process_read_next`
``ba041-Reread``                     L523  :func:`ba041_reread`
``ba050-Process-Read-Indexed``       L591  :func:`ba050_process_read_indexed`
``ba060-Process-Start``              L691  :func:`ba060_process_start`
``ba070-Process-Write``              L802  :func:`ba070_process_write`
``ba080-Process-Delete``             L829  :func:`ba080_process_delete`
``ba085-Process-Delete-ALL``         L885  :func:`ba085_process_delete_all`
``ba090-Process-Rewrite``            L966  :func:`ba090_process_rewrite`
``ba100-Bad-Function``              L1011  :func:`ba100_bad_function`
``ba998-Free``                      L1023  :func:`ba998_free`
``ba999-end``                       L1035  :func:`ba999_end`
``ba999-exit``                      L1042  :func:`ba999_exit`
``bb000-HV-Load`` section           L1045  :func:`bb000_hv_load`
``bb100-UnloadHVs`` section         L1074  :func:`bb100_unload_hvs`
``bb200-Insert`` section            L1105  :func:`bb200_insert`
``bb300-Update`` section            L1294  :func:`bb300_update`
``Ca-Process-Logs``                 L1487  :func:`mt_ca_process_logs`
``ca-Exit``                         L1493  :func:`mt_ca_exit`
=================================  ======  ===============================


The verb set and the dispatch order
===================================

The handler dispatches **eight** functions, in the ``when`` order
``1, 2, 3, 4, 5, 7, 8, 9`` [common/acas006.cbl:L344-L363] — re-write (7) is
dispatched **before** delete (8), and the order is preserved under R-6 because
statement order is part of the specification::

    when 1 -> aa020-Process-Open          when 5 -> aa070-Process-Write
    when 2 -> aa030-Process-Close         when 7 -> aa090-Process-Rewrite
    when 3 -> aa040-Process-Read-Next     when 8 -> aa080-Process-Delete
    when 4 -> aa050-Process-Read-Indexed  when 9 -> aa060-Process-Start
    when other  *> 6 is unused  -> aa100-Bad-Function

``aa100-Bad-Function`` is reached two ways: by ``when other`` [L362-L363] and by
the unconditional ``go to aa100-Bad-Function.`` that follows the ``evaluate``
[common/acas006.cbl:L366], under the maintainer's comment "Should never get here
but in case :(".  There is no ``when 6``: ``fn-Delete-All`` never traverses this
dispatch, because it is set internally by ``ba015-Test-Ends`` and passed
straight to the bridge.  ``fn-Write-Raw`` (15), ``fn-Read-Next-Raw`` (13) and
``fn-Read-By-Name`` / ``-Batch`` / ``-Cust`` / ``fn-Read-Next-Header`` (31..34)
likewise reach ``aa100-Bad-Function``; none of them is implemented here.

``Open``-``extend`` is rejected: the ISAM ``open extend`` is commented out in the
source [common/acas006.cbl:L392] and the branch yields ``WE-Error 997`` /
``FS-Reply 99`` [L393-L395].  ``fn-extend`` itself is annotated "not valid for
ISAM" [copybooks/wsfnctn.cob:L110].


The fourteen columns and the drift at each layer
================================================

R-5, AAP §0.8.1: "Data dictionary first. ... every Python field definition cites
its entry.  This ordering is a directive, not a preference — it is what prevents
fields being transcribed by eye."  The preserved user requirement in AAP §0.8.2:
"The maintainer's one-way COBOL-to-MySQL bridge defines the authoritative
record-layout <-> table mapping — it is the data dictionary for this migration."

Accordingly :data:`COLUMNS` is built at import time from
``loader.entries_for_table("GLPOSTING-REC")`` in **column-ordinal** order, and
every conversion decision is read from ``loader.drift_for(...)`` rather than
re-derived here.  AAP §0.6.2 establishes that the drift is "specific rather than
systemic ... and must be handled field by field from the dictionary."

The table below is the dictionary's content, reproduced for the reader; the code
does not depend on it.  The bridge host-variable name is ``HV-`` prefixed to the
column name in ALL FOURTEEN rows without exception -- ``POST-DAT`` giving
``HV-POST-DAT`` and so on -- so the host variable is not given its own column
here; the invariant is asserted against :data:`COLUMNS` rather than transcribed:

== ============== ============= ==================== ===========================
#  Copybook field Column        Column type          Drift
== ============== ============= ==================== ===========================
1  WS-Post-rrn    POST-RRN      mediumint(5) uns. PK 5 -> 8 -> 5; NEVER LOADED
2  WS-Post-Key    POST-KEY      bigint(10) unsigned  group concat 10 -> 18 -> 10
3  Post-Code      POST-CODE     char(2)              clean
4  Post-Date      POST-DAT      char(8)              name truncated Date -> DAT
5  Post-DR        POST-DR       mediumint(6) uns.    6 -> 8 -> 6
6  DR-PC          DR-PC         tinyint(2) uns.      2 -> 3 -> 2
7  Post-CR        POST-CR       mediumint(6) uns.    6 -> 8 -> 6
8  CR-PC          CR-PC         tinyint(2) uns.      2 -> 3 -> 2
9  Post-Amount    POST-AMOUNT   decimal(10,2)        signed x3; zoned->COMP->dec
10 Post-Legend    POST-LEGEND   char(32)             clean
11 Vat-AC         VAT-AC        mediumint(6) uns.    6 -> 8 -> 6
12 Vat-PC         VAT-PC        tinyint(2) uns.      2 -> 3 -> 2
13 Post-Vat-Side  POST-VAT-SIDE char(2)              clean
14 Vat-Amount     VAT-AMOUNT    decimal(10,2)        signed x3; zoned->COMP->dec
== ============== ============= ==================== ===========================

Column 1 is the headline anomaly and column 4 is the one name that does not
survive intact: the copybook calls the field ``Post-Date`` and both the bridge
host variable [common/glpostingMT.cbl:L285] and the schema column
[mysql/ACASDB.sql:L158] truncate it to ``POST-DAT``.

``Post-Amount`` and ``Vat-Amount`` are declared ``pic s9(8)v99`` with **no**
``usage`` clause [copybooks/wspost.cob:L23, :L28], so they are zoned ``DISPLAY``,
not ``COMP-3``; the sibling nominal-ledger record uses ``COMP-3`` for the same
shape.  Storage class is per field and comes from the dictionary.  Both are
``decimal(10,2)`` in the schema and are :class:`~decimal.Decimal` end to end
here, per R-2: "No accounting value may pass through a binary floating-point
type at any point — not in computation, not in storage, not in transport."


Deliberate omissions, recorded as omissions (R-5)
=================================================

* ``Batch`` and ``Post-Number`` [copybooks/wspost.cob:L15-L16] have no column of
  their own.  They survive only inside the concatenated ``POST-KEY``, which the
  bridge builds with a single group ``move`` [common/glpostingMT.cbl:L1054].
  :class:`~acas_posting.records.gl_posting.WsPostKey` states the same thing from
  the record side: "joining the key is the ``acas006`` handler module's work, at
  the bridge boundary where the COBOL does it."
* There is **no** ``filler`` anywhere in ``wspost.cob``, so nothing else is
  dropped on the way to the table.
* ``HV-POST-RRN`` is neither loaded nor unloaded; see anomaly N-RRN and N-UNLOAD.
* The screen section [common/glpostingMT.cbl:L312-L327], the ``display`` and
  ``accept`` statements, and the ``stop`` literal [common/acas006.cbl:L432] carry
  no database effect.  Per AAP §0.3.4 the diagnostics become log records and the
  acknowledgement pauses are dropped, while every control transfer they guard is
  preserved.
* ``call "fhlogger"`` [common/acas006.cbl:L669, common/glpostingMT.cbl:L1489]
  writes an external log file that is not part of the schema and not part of any
  table dump.  R-1 forbids calling the COBOL program, so the paragraph emits a
  structured log record carrying the same ``File-Access`` fields instead.


Deliberate non-reproduction: the Cobol flat-file branch
=======================================================

``acas006`` has two halves.  The ``aa-Process-Flat-File`` section drives an ISAM
file through ``open`` / ``read`` / ``start`` / ``write`` / ``rewrite`` /
``delete`` verbs [copybooks/selpost.cob, copybooks/fdpost.cob]; the
``ba-Process-RDBMS`` section calls the bridge.  Which half runs is decided by
``FS-Cobol-Files-Used`` [common/acas006.cbl:L315, :L322].

The migrated artifact has no ISAM store: AAP §0.2.1.2 scopes the Python target
to SQL against the frozen schema, and R-1 forbids reaching back into the COBOL
runtime that provides the ISAM organisation.  The flat-file paragraphs are
therefore reproduced faithfully up to the point of the ISAM verb itself — the
paragraph number, the ``WS-File-Key`` tag, the key moves, the guards and the
status codes all behave exactly as the COBOL — and the verb itself raises
:class:`CobolFlatFileStoreUnavailableError`.  This is a documented refusal when
the store is absent, not a new validation: it adds no accept/reject decision the
COBOL does not have (R-3), and it cannot be reached on the RDB path that the
posting cycle actually uses.


Anomalies reproduced, never fixed (R-4)
=======================================

AAP §0.8.2: "There is no test suite: compiled COBOL execution is the behavioral
specification, defects included.  A defect reproduced is correct; a defect fixed
is a failure."  AAP §0.7.4 C-4 requires a comment at each reproduction site
citing the COBOL locator, and every entry below also appears in
``docs/migration/anomaly-log.md`` naming this module as the reproducing module.

``N-RRN`` — **the primary key is never loaded.**  ``HV-POST-RRN`` is declared
[common/glpostingMT.cbl:L282] and appears in no ``move`` of ``bb000-HV-Load``
[:L1053-L1066], yet ``POST-RRN`` is the ``PRIMARY KEY``
[mysql/ACASDB.sql:L155, :L169].  It **is** named in both fetch column lists
[:L538, :L645] and in both the ``INSERT`` [:L1120-L1130] and the ``UPDATE``
[:L1309-L1319], so it is written from the host-variable group — which
``initialize TD-GLPOSTING-REC`` [:L1053] has just zeroed.  Every insert and
every rewrite therefore stamps ``POST-RRN`` to zero rather than to the record's
``WS-Post-rrn``.  The maintainer left his own note beside the key table:
"WARNING POST-KEY MAY WELL NEED CHANGING TO POST-RRN & RDB made to index fld."
[common/glpostingMT.scb:L229], and a third in the SELECT clause: ``record key
Post-Rrn    *> MAY NEED CHANGING <<<`` [copybooks/selpost.cob].  The key is not
loaded here, not auto-incremented, not derived and not defaulted to anything
else; the duplicate-key consequence is arbitrated by the oracle under R-6 and
belongs in ``docs/migration/ambiguity-resolutions.md``.  The consequence, which
this module was observed to reproduce against the frozen schema on a live
MariaDB 10.11.7 server, is that **the bridge can hold at most ONE row of**
``GLPOSTING-REC`` **at a time**: every insert offers the same primary key, so
the second collides and comes back ``FS-Reply 22`` [:L818-L823], and every
rewrite re-stamps the surviving row's key to zero.

``N-UNLOAD`` — ``bb100-UnloadHVs`` [common/glpostingMT.cbl:L1074-L1103] does
``initialize WS-Posting-Record`` [:L1083] and then only **thirteen** moves
[:L1085-L1097].  ``HV-POST-RRN`` is not unloaded either, so after any read
``WS-Post-rrn`` is zero regardless of what the row held.

``N-loadorder`` — the load moves ``Post-CR`` **before** ``DR-PC``: ``Post-DR``
[:L1057], ``Post-CR`` [:L1058], ``DR-PC`` [:L1059], ``CR-PC`` [:L1060].  That is
inverted against the host-variable group, which declares ``HV-DR-PC`` [:L287]
before ``HV-POST-CR`` [:L288], and against the column ordinals, where ``DR-PC``
is 6 and ``POST-CR`` is 7.  The unload paragraph carries the same inversion:
``POST-DR`` [:L1088], ``POST-CR`` [:L1089], ``DR-PC`` [:L1090], ``CR-PC``
[:L1091].  The statement order is preserved; the emitted column list is in table
ordinal order, as the bridge's own ``INSERT`` is.

``N17`` — the ``move`` at [common/glpostingMT.cbl:L1060] omits its terminating
period.  In COBOL the sentence simply continues into the next ``move``, so the
semantics are unaffected; it is recorded as a style anomaly.

``N18b`` — **one Open-Output request calls the bridge twice.**  Stage 1
[common/acas006.cbl:L313-L318] performs ``ba-Process-RDBMS`` **without** setting
``fn-delete-all``.  Stage 2 [:L640-L644] performs ``ba020-Process-Dal``, then
sets ``fn-Delete-All to true``, and then ``ba015-Test-Ends`` falls through in
source order into ``ba020-Process-DAL`` [:L653], calling the bridge a second
time with ``File-Function = 6``.  Three sibling handlers behave three different
ways at this point and all three are preserved: ``acas005`` has the whole block
commented out with "NOT used with GL." [common/acas005.cbl:L310-L317];
``acas008`` sets ``fn-delete-all`` in stage 1 and so makes a single coerced call
[common/acas008.cbl:L313-L319]; ``acas006`` calls twice.

``N-DELETE-ALL`` — ``ba085-Process-Delete-ALL`` [common/glpostingMT.cbl:L885-
L964] is not a truncate.  It moves ``9999999999`` into ``ws-Post-Key`` [:L907]
and issues ``DELETE ... WHERE `POST-KEY` < "<key>"`` [:L915-L944], and its
success test is ``if WS-MYSQL-COUNT-ROWS not > zero`` [:L947], so an
already-empty table takes the error path.  Because of ``N-KOR`` the key text in
that predicate is not ``"9999999999"``: the ``string`` takes
``WS-Posting-Record (K:L)`` [:L919], which is ``WS-Post-rrn`` followed by
``Batch``, and [:L907] has just set ``Batch`` to ``99999``.  For a caller
passing a fresh record the predicate is therefore ``< "0000099999"``, so an
``Open``-``Output`` does **not** empty a table whose keys lie above that bound
-- observed live against the frozen schema, where a row keyed ``9900199001``
survived the clear and one keyed ``42`` did not.  When the count comes back
zero with no driver error, the errno branch [:L951-L957] writes nothing and
``go to ba999-End`` [:L958] skips the ``move zero to FS-Reply WE-Error``
[:L963] -- so a failed clear returns whatever status the caller passed in
(``N-NOSTATUS``).

``N-KOR`` — the key table declares offset 0001 length 0010
[common/glpostingMT.scb:L233], so every ``WHERE`` the bridge builds slices
``WS-Posting-Record (1:10)``.  Since ``WS-Post-rrn pic 9(5)`` was added at the
**front** of the record on 06/01/17 [copybooks/wspost.cob:L9, :L13] that slice is
``WS-Post-rrn`` followed by ``Batch`` — **not** ``WS-Post-Key``, which now
occupies bytes 6..15.  The keyed predicate is nonetheless labelled ``POST-KEY``
[:L232].  Affects read-indexed [common/glpostingMT.cbl:L606], start [:L734],
delete [:L841], delete-all [:L919] and rewrite [:L981].
:class:`acas_posting.dal.cursor_state.KeyOfReference` already models the slice;
this module uses ``key_from_record`` rather than reading ``ws_post_key``.

``N-EDIT`` — ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` [common/glpostingMT.cbl:L217]
is thirty characters whose **first** position is the sign.  Every numeric
rendering in ``bb200-Insert`` and ``bb300-Update`` takes a window that starts at
position 3 or later and so **excludes the sign**: ``(13:08)`` for the
eight-digit integers, ``(03:18)`` for the eighteen-digit key, ``(18:03)`` for the
three-digit percentages, and ``(13:08)`` plus ``"."`` plus ``(22:02)`` for the
two money fields.  A negative ``POST-AMOUNT`` or ``VAT-AMOUNT`` is therefore
written as its absolute value.  This is the same class of defect as AAP §0.6.7
entry 11: the sign is lost at the bridge, before any SQL executes.

``N2`` — ``FS-Reply 23`` is documented in the authoritative table
[common/glpostingMT.cbl:L129] and never returned.  Both sites that the table
describes write 21 instead, under the maintainer's own annotation: ``move 21 to
fs-reply  *> from 23`` at [:L668] paired with ``WE-Error 990`` [:L669], and again
at [:L676] paired with ``WE-Error 989`` [:L677].  A third site notes the same
uncertainty differently: ``move 21 to fs-Reply  *> could also be 23 or 14``
[:L634].

``N-DEAD-READ-INDEXED-ERRNO`` — **both of N2's sites are unreachable**, which
makes ``FS-Reply 23`` doubly absent.  ``ba050-Process-Read-Indexed`` tests the
same count twice: ``if WS-MYSQL-Count-Rows = zero ... go to ba998-Free``
[common/glpostingMT.cbl:L633-L636] and then ``if WS-MYSQL-Count-Rows not > zero``
[:L663].  ``Ws-Mysql-Count-Rows`` is ``binary-double unsigned``
[copybooks/mysql-variables.cpy:L73]; it is written only by
``MySQL_affected_rows`` [copybooks/mysql-procedures.cpy:L178] and
``MySQL_num_rows`` [:L191-L192]; and ``CALL "MySQL_fetch_record"``
[common/glpostingMT.cbl:L643-L658] does not pass it.  For an unsigned count "not
greater than zero" **is** "equal to zero", which the first guard has already
jumped away from, so the whole block [:L663-L683] is dead — carrying the
maintainer's own trailing doubt ``*> row count zero should show up as a MYSQL
error ?`` [:L683].  The only reachable ``FS-Reply 21`` from that paragraph is
[:L634], which writes ``FS-Reply`` and **no** ``We-Error``.
:mod:`acas_posting.dal.cursor_state` records the same finding as its anomalies
A13 and A14, A14 being the mismatched pair ``(21, 911)`` a broken statement
produces when the 21 overwrites the 99 and the 911 survives.

``N-COUNTROWS-NEG-DEAD`` — ``01 WS-Mysql-Count-Rows-Neg redefines
WS-Mysql-Count-Rows binary-double signed.``
[copybooks/mysql-variables.cpy:L74-L75] is declared and referenced **nowhere** in
the frozen tree, although the copybook's own version log records "version
007--Changes for Count-Rows / -neg" [:L35].  It is the redefinition a reader
would have to invoke for the second guard above to be live, and nothing invokes
it.  Recorded only.

``N-WE21`` — the flat-file indexed read writes a ``We-Error`` the error list
cannot explain.  ``aa051-Reread`` does ``move 21 to we-error fs-reply``
[common/acas006.cbl:L466] — one statement, both fields — and 21 appears nowhere
among the authoritative table's values 999, 998, 997, 996, 995, 994, 992, 990,
989, 988, 911, 910 and 901 [common/glpostingMT.cbl:L125-L158].  Recorded;
:mod:`acas_posting.dal.status` gains no member for it.

``N-BRIDGE-BAD-FN`` — the two "bad function" paragraphs in one call chain return
different codes: the handler's ``aa100-Bad-Function`` gives ``WE-Error 999``
[common/acas006.cbl:L561] while the bridge's ``ba100-Bad-Function`` gives
``WE-Error 990`` [common/glpostingMT.cbl:L1015].  Both give ``FS-Reply 99``.

``N-901-DEAD`` — ``ba012-Test-WS-Rec-Size-2`` compares the working-storage record
against the file-description record and raises ``WE-Error 901`` when the former
is shorter [common/acas006.cbl:L601-L603].  The two records are declared field
for field identically at 103 bytes each [copybooks/wspost.cob:L12-L28,
copybooks/fdpost.cob:L12-L28], differing only in the ``WS-`` name prefixes, so
``if A < B`` can never be true and the whole 901 branch — the ``GL903`` message
[:L606-L612], the two displays [:L613-L614], the ``SQL-Msg`` copy [:L615] and
the ``go to ba-rdbms-exit`` [:L620] — is unreachable.  The comparison is
reproduced so that it stays dead for the same reason.  Both copybook headers
claim "98 bytes" and "96 bytes"; the byte-offset comments on the trailing fields
describe a pre-2017 layout in which ``Post-Legend`` was ``x(30)``.

``N-log`` — the log file number is set to 12 on the Cobol path
[common/acas006.cbl:L289] and overwritten with 22 the moment the RDB path is
entered [:L590], with the field's capitalisation differing between the two sites
(``WS-Log-File-No`` then ``WS-Log-File-no``).  The series is systematic across
the family — ``acas005`` 11 -> 21, ``acas006`` 12 -> 22, ``acas007`` 13 -> 23,
``acas008`` 15 -> 25 — and skips 14.  The RDB-path value is what this module
reports.

``N-guard`` — the guarded function set differs per handler and is not unified.
``acas006`` guards read-indexed (4), start (9) and delete (8)
[common/acas006.cbl:L293-L307]; ``acas000`` guards read-indexed (4), write (5)
and re-write (7), with a range test rather than an equality test
[common/acas000.cbl:L330-L338].

``N-REREAD-ASYMMETRY`` — the sibling handlers do not share a reread shape.
``acas006`` has TWO reread paragraphs, ``aa041-Reread`` after the sequential read
[common/acas006.cbl:L436] and ``aa051-Reread`` after the indexed read [:L461];
``acas005`` has only ``aa041-Reread`` and adds an ``aa047-Eval-Keys`` that this
handler does not have, because the nominal ledger has key evaluation to do and
the posting file does not.  Both of this handler's rereads are implemented and
the divergence is recorded rather than smoothed.

``N-998`` — ``WE-Error 998`` carries three meanings.  The authoritative table
says "File-Key-No Out Of Range not 1, 2 or 3"
[common/glpostingMT.cbl:L141]; the key guard's comment says "file seeks key type
out of range" [common/acas006.cbl:L297]; and ``aa060-Process-Start`` uses it for
"998 Invalid calling parameter settings" [:L488].  The bridge's equivalent start
guard uses 997 for that same condition [common/glpostingMT.cbl:L697].

``N-996-comment`` — the comment on the delete branch's ``move 996 to WE-Error``
is a copy-paste of the 998 branch's comment [common/acas006.cbl:L303].

``N-START-NO-FSREPLY`` — **the handler's start guard reports success and an error
at the same time.**  ``aa060-Process-Start`` clears both status fields
[common/acas006.cbl:L480-L481] and its parameter guard then writes ONE of them::

    L487      if       access-type < 5 or > 8  *> NOT using 'not >'
    L488               move 998 to WE-Error    *> 998 Invalid calling parameter settings
    L489               go to aa999-main-exit

There is no ``move 99 to fs-reply``, so an invalid access type returns
``(0, 998)``.  The bridge's equivalent guard writes both, 99 and 997
[common/glpostingMT.cbl:L695-L697].  Reproduced in both programs as written.

``N-relation`` — nine relations are implemented and eight documented.
``Access-Type`` condition names run 5..9 [copybooks/wsfnctn.cob:L111-L116], the
bridge's ``evaluate`` has an arm for all five symbols including
``fn-not-greater-than`` [common/glpostingMT.cbl:L715-L726], the ``DAL-Data``
comment lists five [:L248], and both start guards test ``< 5 or > 8``
[common/acas006.cbl:L487, common/glpostingMT.cbl:L695] so value 9 is rejected
despite having an arm.  ``Access-Type`` is passed through unmodified;
:mod:`acas_posting.dal.cursor_state` owns the mapping and reproduces the
rejection.

``N10`` — ``copy "ACAS-SQLstate-error-list.cob".``
[common/glpostingMT.cbl:L160] names a copybook that is absent from the entire
checkout; 49 files reference it.  It is a second missing build input, alongside
the bridge's C interface object that AAP §0.5.2 names and records as having no
build rule anywhere in the repository.  Recorded only; nothing is invented to
fill it.
``status.MISSING_SQLSTATE_COPYBOOK`` carries the same fact.

``N-STALE-COMMENT`` — ``bb100-UnloadHVs`` closes with "We do not need to unload
POST4- DAY, MONTH or YEAR as only used in select statements instead of a sort."
[common/glpostingMT.cbl:L1099-L1100].  Those columns belong to ``irspostingMT``,
not to ``GLPOSTING-REC``; the comment is a copy-paste leftover.

``N-LOCK-LADDER-DEAD`` — the four-rung lock-retry ladder
[copybooks/mysql-procedures.cpy:L209-L255] is commented out of
``Mysql-1210-Command`` [:L167-L175], so ``WE-Error 910`` is unreachable through
this bridge.  :mod:`acas_posting.dal.status` owns the ladder; here it is dead.

``N-DUPKEY-TWO-PLACES`` — a duplicate key is detected twice.  At driver level
``Mysql-1100-Db-Error`` tests errno 1062 or 1022 **and** that the command begins
``INSERT`` or ``insert``, then sets ``FS-Reply 22`` and exits early without
setting ``SQL-Msg`` or ``SQL-State`` [copybooks/mysql-procedures.cpy:L99-L105].
At bridge level ``ba070-Process-Write`` tests ``SQL-Err (1:4) = "1062" or =
"1022" or Sql-State = "23000"`` [common/glpostingMT.cbl:L818-L824].  Both are
reproduced; :mod:`acas_posting.dal.status` owns both predicates.

``N-NOSTATUS`` — **the statements that would clear the status are commented out,
in BOTH programs, and paths exist that then write none.**  Three sites carry the
omission::

     *>    move     zero   to  WE-Error          [common/acas006.cbl:L340]
     *>  ?                      FS-Reply.        [common/acas006.cbl:L341]
     *> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.   [:L410]
     *>    move     zero   to We-Error           [common/glpostingMT.cbl:L347]
     *>                       Fs-Reply.          [common/glpostingMT.cbl:L348]

— the handler's mainline keeping the maintainer's own ``?``, the handler's close
keeping a date, and the bridge's initialise.  So only ``SQL-Err``, ``SQL-Msg``
and ``SQL-State`` are cleared on entry [common/acas006.cbl:L342,
common/glpostingMT.cbl:L350-L356] and the caller's incoming ``FS-Reply`` and
``We-Error`` survive into the verb.  Several verbs then leave them untouched: a
delete matching no row whose driver error number begins ``0`` transfers at
[common/glpostingMT.cbl:L877] having written neither, the delete-all does the
same at [:L958], the rewrite at [:L1004], the reachable read-indexed miss writes
only ``FS-Reply`` [:L634], and the flat-file delete and rewrite carry no
``invalid key`` clause at all [common/acas006.cbl:L544, :L554].  The net effect is
that a caller can read back the status it passed in and take it for a result.
Every one of those paths is reproduced, and each carries a log record naming the
locator so the silence is visible without being corrected.
:mod:`acas_posting.dal.cursor_state` records the same family as its anomaly A7.

``N-DELETE-TERMINATOR`` — the two ``DELETE`` statements are terminated with
``X"00"`` alone, [common/glpostingMT.cbl:L863] for ``ba080-Process-Delete`` and
[:L944] for ``ba085-Process-Delete-ALL``, where the ``SELECT`` [:L627], the
``INSERT`` [:L1283-L1286] and the ``UPDATE`` [:L1478] all write ``";"`` and then
``X"00"``.  Both terminators are transport for the C interface rather than part
of the statement, so the difference has no effect on the server and none on the
table state — see :data:`STATEMENT_TERMINATORS_ARE_TRANSPORT_ONLY`.  Recorded
rather than reproduced, because reproducing it would mean sending text this layer
does not send.


The authoritative status table
==============================

The status table this whole layer is built from lives in this bridge
[common/glpostingMT.cbl:L125-L158].  :mod:`acas_posting.dal.status` owns it, and
no code is duplicated here: ``FsReply``, ``WeError``, ``FileFunction``,
``AccessType``, ``LogSystem`` and the SQLSTATE predicates are imported.  This
module owns only the *sites* at which each code is written, and those sites match
the frozen source line for line.


Determinism, sequencing and layering
====================================

R-6, AAP §0.6.6 in paraphrase: the cycle has no hidden time source, no seeded
pseudo-randomness, and no ordering nondeterminism from a secondary index -- the
frozen schema declares none.  Accordingly nothing here reads a clock, draws an
unpredictable value or mints an identifier; :data:`COLUMNS` is built from the
dictionary in ordinal order, so the emitted column list is byte-identical
across processes.

R-3 forbids concurrency: execution is strictly sequential, there is no pool, no
thread and no event loop, and the bridge's connection state is a single
module-level slot corresponding to the COBOL's ``Ws-Mysql-Cid``.  Only
``SELECT``, ``INSERT``, ``UPDATE`` and ``DELETE`` are issued; no DDL, no ORM
entity layer, no migration tooling.  The schema is frozen, so this module never
names a data-definition verb at all -- where the table definition in
``mysql/ACASDB.sql`` is the authority for a column, for its type or for the
ordinal order every statement emits, it is cited by locator instead, so that a
DDL scan over this file returns nothing to read.  Every table and column name
in this schema
contains a hyphen, so every identifier is routed through
:func:`acas_posting.dal.connection.quote_identifier`; unquoted, each would be a
MySQL syntax error.

Imports are confined to this file's declared dependencies: the three ``dal``
peers, five ``records`` modules and the dictionary loader.  Nothing is imported
from ``dal.facade``, another ``dal.acas*``, ``acas_posting.cobol``, ``programs``,
``cli`` or ``harness``.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import ClassVar, Final

from acas_posting.dal.connection import (
    BinaryFloatingPointError,
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
)
from acas_posting.dal.cursor_state import (
    CursorSlot,
    CursorStateTable,
    KeyOfReference,
    key_of_reference,
    read_indexed,
    read_next,
    start,
)
from acas_posting.dal.status import (
    START_ACCESS_TYPE_RANGE,
    AccessType,
    AcasFileHandlerFatalError,
    DbErrorStatus,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    mysql_1100_db_error,
    override_we_error_for_operation,
    sanitise_for_log,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_posting import WsPostingRecord, WsPostKey
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    # ---- identity ---------------------------------------------------------
    "HANDLER_NAME",
    "BRIDGE_NAME",
    "TABLE_NAME",
    "ENTITY_FACADE",
    "RECORD_COPYBOOK",
    "FILE_DESCRIPTION_COPYBOOK",
    "MYSQL_VAR_DIRECTIVE",
    "MISSING_SQLSTATE_COPYBOOK_SITE",
    # ---- logging identity and field widths -------------------------------
    "WS_LOG_SYSTEM",
    "WS_LOG_FILE_NO_COBOL_PATH",
    "WS_LOG_FILE_NO_RDB_PATH",
    "WS_FILE_KEY_WIDTH",
    "WS_FILE_KEY_LITERALS",
    "SQL_ERR_FIELD_WIDTH",
    "SQL_MSG_FIELD_WIDTH",
    "SQL_STATE_FIELD_WIDTH",
    "DISPLAY_BLK_WIDTH",
    "GL901_MESSAGE",
    "GL903_MESSAGE",
    "MINIMUM_SCREEN_LINES",
    # ---- paragraph numbers, for the log field and for traceability -------
    "HANDLER_PARAGRAPH_NUMBERS",
    "BRIDGE_PARAGRAPH_NUMBERS",
    # ---- `WS-MYSQL-EDIT`, the field every numeric value is rendered through
    "EDIT_FIELD_PICTURE",
    "EDIT_FIELD_WIDTH",
    "EDIT_FIELD_SIGN_POSITION",
    "EDIT_FIELD_INTEGER_END",
    "EDIT_FIELD_FRACTION_START",
    "EDIT_FIELD_SIGN_IS_NEVER_RENDERED",
    # ---- dictionary-driven data ------------------------------------------
    "GlPostingColumn",
    "COLUMNS",
    "COLUMNS_BY_NAME",
    "COLUMN_NAMES",
    "KEY_OF_REFERENCE",
    "TABLE_OF_KEYNAMES_LITERALS",
    "KEY_OF_REFERENCE_SLICE_IS_NOT_THE_POST_KEY",
    "PRIMARY_KEY_COLUMN",
    "HOST_VARIABLE_NAMES_ARE_HV_PREFIXED",
    "PRIMARY_KEY_IS_NEVER_LOADED",
    "WS_POSTING_RECORD_BYTES",
    "POSTING_RECORD_BYTES",
    "POSTING_RECORD_DECLARED_FIELDS",
    "RECORD_SIZE_GUARD_IS_UNREACHABLE",
    "STATEMENT_TERMINATORS_ARE_TRANSPORT_ONLY",
    # ---- the COBOL host-variable group -----------------------------------
    "TdGlpostingRec",
    # ---- errors -----------------------------------------------------------
    "CobolFlatFileStoreUnavailableError",
    "BridgeNotOpenError",
    # ---- entry points -----------------------------------------------------
    "dispatch",
    "glposting_mt",
    # ---- `CANCEL <program>`, one per program ------------------------------
    "cancel_acas006",
    "cancel_glposting_mt",
    # ---- handler paragraphs, acas006 -------------------------------------
    "aa_process_flat_file",
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
    "aa_main_exit",
    "aa_exit",
    "ba_process_rdbms",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba020_process_dal",
    "ba_rdbms_exit",
    "ca_process_logs",
    "ca_exit",
    # ---- bridge paragraphs, glpostingMT ----------------------------------
    "ba_acas_dal_process",
    "ba010_initialise",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba041_reread",
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
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "mt_ca_process_logs",
    "mt_ca_exit",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Identity of the handler, the bridge and the table
# ---------------------------------------------------------------------------

#: `77  prog-name          pic x(20)  value "acas006 (3.3.00)".`
#: [common/acas006.cbl:L244]
HANDLER_NAME: Final[str] = "acas006"

#: `77  prog-name          pic x(22)  value "postingMT (3.3.00)".`
#: [common/glpostingMT.cbl:L207] - note that the program-id is `glpostingMT`
#: [common/glpostingMT.cbl:L1495] while the version literal says `postingMT`.
BRIDGE_NAME: Final[str] = "glpostingMT"

#: The table this pair serves [mysql/ACASDB.sql:L154].
TABLE_NAME: Final[str] = "GLPOSTING-REC"

#: The facade entity name [copybooks/Proc-ACAS-FH-Calls.cob], AAP section 0.2.1.1.
ENTITY_FACADE: Final[str] = "GL-Posting"

#: The record layout [copybooks/wspost.cob:L12-L28].
RECORD_COPYBOOK: Final[str] = "copybooks/wspost.cob"

#: The file description of the same record [copybooks/fdpost.cob:L10-L28].
FILE_DESCRIPTION_COPYBOOK: Final[str] = "copybooks/fdpost.cob"

#: The bridge's own table/host-variable directive, transcribed VERBATIM from the
#: pre-translation source [common/glpostingMT.scb:L273-L276]. The generated
#: program carries the same three lines as comments with the `BASE=` prefix
#: dropped, followed by `COPY "mysql-variables.cpy".`
#: [common/glpostingMT.cbl:L273-L276].
MYSQL_VAR_DIRECTIVE: Final[tuple[str, ...]] = (
    "/MYSQL VAR\\",
    "      BASE=ACASDB",
    "      TABLE=GLPOSTING-REC,HV",
    "/MYSQL-END\\",
)

#: `copy "ACAS-SQLstate-error-list.cob".` [common/glpostingMT.cbl:L160] names a
#: copybook ABSENT from the entire checkout - anomaly N10, a second missing build
#: input, alongside the bridge's C interface object that AAP section 0.5.2 names
#: and records as having no build rule in the repository. Recorded, never
#: invented.
#: :data:`acas_posting.dal.status.MISSING_SQLSTATE_COPYBOOK` carries the same
#: fact; this constant records the citation of the reference site in THIS bridge.
MISSING_SQLSTATE_COPYBOOK_SITE: Final[str] = "common/glpostingMT.cbl:L160"


# ---------------------------------------------------------------------------
# Log identity, paragraph numbers and the WS-File-Key field
# ---------------------------------------------------------------------------

#: `move 2 to WS-Log-System.` with the maintainer's own key
#: "1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock - used in FH logging"
#: [common/acas006.cbl:L288].
WS_LOG_SYSTEM: Final[LogSystem] = LogSystem.GL

#: ANOMALY N-log. `move 12 to WS-Log-File-No.` on the Cobol path
#: [common/acas006.cbl:L289] ...
WS_LOG_FILE_NO_COBOL_PATH: Final[int] = 12

#: ... and `move 22 to WS-Log-File-no.` the moment the RDB path is entered
#: [common/acas006.cbl:L590], with the field's capitalisation differing between
#: the two sites. The series is systematic across the family and skips 14:
#: acas005 11 -> 21, acas006 12 -> 22, acas007 13 -> 23, acas008 15 -> 25. The
#: RDB-path value is the one the posting cycle observes, because the cycle runs
#: with `FS-RDBMS-Used` set.
WS_LOG_FILE_NO_RDB_PATH: Final[int] = 22

#: `WS-File-Key        pic x(64).` [copybooks/wsfnctn.cob:L52]. Every literal
#: moved into this field is truncated to 64 characters, as a COBOL `MOVE` to a
#: shorter alphanumeric receiving field truncates on the right. Trailing spaces
#: are NOT added here: `CursorOutcome.apply_to` writes the same field unpadded,
#: so padding at this one site would give the field two different shapes
#: depending on which verb last wrote it. The truncation is the observable part;
#: the padding is representation.
WS_FILE_KEY_WIDTH: Final[int] = 64

#: `SQL-Err            pic x(5).` [copybooks/wsfnctn.cob:L49]
SQL_ERR_FIELD_WIDTH: Final[int] = 5

#: `SQL-Msg            pic x(512).` [copybooks/wsfnctn.cob:L50]
SQL_MSG_FIELD_WIDTH: Final[int] = 512

#: `SQL-State          pic x(5).` [copybooks/wsfnctn.cob:L51]
SQL_STATE_FIELD_WIDTH: Final[int] = 5

#: `WS-No-Paragraph` values the HANDLER writes, one per verb paragraph
#: [common/acas006.cbl:L370, :L407, :L424, :L454, :L479, :L523, :L535, :L549].
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

#: `WS-No-Paragraph` values the BRIDGE writes [common/glpostingMT.cbl:L418,
#: :L437, :L476, :L528, :L616, :L637, :L750, :L808, :L852, :L933, :L970,
#: :L1024]. The numbering is the bridge's own and is not contiguous: 7, 9, 11,
#: 12, 14, 16, 18 and 19 are unused in this bridge.
BRIDGE_PARAGRAPH_NUMBERS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ba020-Process-Open": 1,
        "ba030-Process-Close": 2,
        "ba040-Process-Read-Next": 3,
        "ba041-Reread": 4,
        "ba050-Process-Read-Indexed": 5,
        "ba050-Process-Read-Indexed-Fetch": 6,
        "ba060-Process-Start": 8,
        "ba070-Process-Write": 10,
        "ba080-Process-Delete": 13,
        "ba085-Process-Delete-ALL": 15,
        "ba090-Process-Rewrite": 17,
        "ba998-Free": 20,
    }
)

#: Every literal the two programs move into `WS-File-Key`, at its own site. They
#: are collected here so the traceability document can check them off, and used
#: by name below rather than re-spelt at each site.
WS_FILE_KEY_LITERALS: Final[Mapping[str, str]] = MappingProxyType(
    {
        # Handler [common/acas006.cbl]
        "handler-open": "OPEN GL POSTING file",  # :L401
        "handler-close": "CLOSE GL POSTING file",  # :L412
        "handler-eof": "EOF",  # :L442
        # Bridge [common/glpostingMT.cbl]
        "bridge-open": "OPEN GLPOSTING",  # :L429
        "bridge-close": "CLOSE GLPOSTING",  # :L438
        "bridge-eof": "EOF",  # :L558
        "bridge-eof2": "EOF2",  # :L574
        "bridge-eof3": "EOF3",  # :L582
        "bridge-no-data": "No Data",  # :L510
        "bridge-read-next-low-key": "00000",  # :L492
        "bridge-delete-all": "Deleting back from ",  # :L925-L927
    }
)


# ---------------------------------------------------------------------------
# `WS-MYSQL-EDIT` - the numeric-rendering field, and ANOMALY N-EDIT
# ---------------------------------------------------------------------------

#: `01  WS-MYSQL-EDIT       PIC -Z(18)9.9(9).` [common/glpostingMT.cbl:L217].
#: Thirty character positions:
#:
#: ===========  ==============================================================
#: position 1   the sign: space when positive, ``-`` when negative
#: 2 .. 19      ``Z(18)`` - zero-suppressed integer digits, blank when leading
#: 20           ``9``     - the units digit, always printed
#: 21           ``.``     - the decimal point
#: 22 .. 30     ``9(9)``  - fractional digits, never suppressed
#: ===========  ==============================================================
EDIT_FIELD_PICTURE: Final[str] = "-Z(18)9.9(9)"
EDIT_FIELD_WIDTH: Final[int] = 30
EDIT_FIELD_SIGN_POSITION: Final[int] = 1
#: The integer field ends at position 20, so an ``n``-digit integer window starts
#: at ``21 - n``. This single expression reproduces every integer window the
#: bridge writes: ``(13:08)`` for the eight-digit COMP items, ``(03:18)`` for the
#: eighteen-digit key, ``(18:03)`` for the three-digit percentages.
EDIT_FIELD_INTEGER_END: Final[int] = 20
#: The fractional digits always begin at position 22, which is why every money
#: window is ``(22:02)``.
EDIT_FIELD_FRACTION_START: Final[int] = 22

#: ANOMALY N-EDIT, recorded once here and cited again at
#: :func:`_render_numeric_through_edit_field`. Every ``STRING FUNCTION TRIM
#: (WS-MYSQL-EDIT (s:l))`` in `bb200-Insert` and `bb300-Update` starts at
#: position 3 or later, so position 1 - the sign - is never part of any window.
#: A negative ``POST-AMOUNT`` or ``VAT-AMOUNT`` therefore reaches the column as
#: its ABSOLUTE VALUE. Same class as AAP section 0.6.7 entry 11: the sign is
#: lost at the bridge, before any SQL executes.
EDIT_FIELD_SIGN_IS_NEVER_RENDERED: Final[bool] = True


# ---------------------------------------------------------------------------
# The key of reference, and ANOMALY N-KOR
# ---------------------------------------------------------------------------

#: The three literals of `01 Table-Of-Keynames.`, transcribed VERBATIM from
#: [common/glpostingMT.scb:L231-L234]:
#:
#: * ``03  filler pic x(30) value "POST-KEY                      ".  *> in RDB``
#: * ``03  filler pic x(8)  value "00010010".  *> offset/length in ws rec``
#: * ``03  filler pic xxx   value "STR".       *> key is string``
#:
#: redefined as ``03 keyOfReference occurs 1 indexed by KOR-x1.`` with
#: ``KeyName pic x(30)``, ``KOR-Offset pic 9(4)``, ``KOR-Length pic 9(4)`` and
#: ``KOR-Type pic XXX.  *> Not used currently``
#: [common/glpostingMT.scb:L236-L241]. There is exactly ONE key of reference:
#: ``occurs 1``.
#:
#: Note that the offset and the length are ONE eight-character literal, not two
#: separate ``9(4)`` values; the redefinition splits it.
TABLE_OF_KEYNAMES_LITERALS: Final[tuple[str, str, str]] = (
    "POST-KEY                      ",
    "00010010",
    "STR",
)

#: Read from :mod:`acas_posting.dal.cursor_state`, which owns the cursor
#: contract, rather than re-declared here. AAP section 0.1.1: "Indexed-file read
#: semantics must be emulated, not approximated ... The Python data-access layer
#: must reproduce cursor positioning and the ``FS-Reply`` status protocol, not
#: merely issue equivalent SQL."
KEY_OF_REFERENCE: Final[KeyOfReference] = key_of_reference(TABLE_NAME)

#: ANOMALY N-KOR. Offset 0001 length 0010 means every ``WHERE`` the bridge builds
#: slices ``WS-Posting-Record (1:10)``. Since ``WS-Post-rrn pic 9(5)`` was added
#: at the FRONT of the record on 06/01/17 [copybooks/wspost.cob:L9, :L13] that
#: slice is ``WS-Post-rrn`` followed by ``Batch`` - NOT ``WS-Post-Key``, which
#: now occupies bytes 6..15 - even though the key is labelled ``POST-KEY``
#: [common/glpostingMT.scb:L232]. The maintainer's own note sits two lines above
#: the table: "WARNING POST-KEY MAY WELL NEED CHANGING TO POST-RRN & RDB made to
#: index fld." [common/glpostingMT.scb:L229], and a third note says the same in
#: the SELECT clause: ``record key Post-Rrn    *> MAY NEED CHANGING <<<``
#: [copybooks/selpost.cob]. Affects read-indexed
#: [common/glpostingMT.cbl:L606], start [:L734], delete [:L841], delete-all
#: [:L919] and rewrite [:L981].
KEY_OF_REFERENCE_SLICE_IS_NOT_THE_POST_KEY: Final[bool] = True

#: `PRIMARY KEY (`POST-RRN`)` [mysql/ACASDB.sql:L169] - the column that
#: `bb000-HV-Load` never loads. See anomaly N-RRN.
PRIMARY_KEY_COLUMN: Final[str] = "POST-RRN"



# ---------------------------------------------------------------------------
# Declared record lengths, and ANOMALY N-901-DEAD
# ---------------------------------------------------------------------------


def _declared_bytes(dictionary_key: str) -> int:
    """Return the declared byte length of one elementary copybook field.

    ``WS-Posting-Record`` contains only zoned ``DISPLAY`` numerics and
    ``ALPHANUMERIC`` items - :class:`WsPostingRecord` records the same fact from
    the record side, that "no COMP/COMP-3/binary item appears anywhere" - so a
    zoned numeric occupies one byte per declared digit and an alphanumeric item
    occupies its character length. The two money fields are
    ``pic s9(8)v99`` with ``SignPosition.TRAILING_INCLUDED``
    [copybooks/wspost.cob:L23, :L28], meaning the sign shares the final digit's
    byte, so they are ten bytes and not eleven.

    Args:
        dictionary_key: The data-dictionary key of an elementary field.

    Returns:
        The field's declared length in bytes.

    Raises:
        ValueError: If the field is a group, or declares a storage class this
            record does not contain. Unreachable for ``wspost.cob``; present so
            that a dictionary regeneration that changed the record would fail
            loudly instead of silently producing a wrong length.
    """
    field_view = loader.get_entry(dictionary_key).copybook
    if field_view.is_group:
        raise ValueError(
            f"{dictionary_key} is a group item; its children carry the bytes"
        )
    if field_view.character_length is not None:
        return int(field_view.character_length)
    if field_view.digits is not None:
        return int(field_view.digits)
    raise ValueError(
        f"{dictionary_key} declares neither a character length nor a digit "
        f"count, so its byte length cannot be derived from the dictionary"
    )


def _ws_posting_record_bytes() -> int:
    """Sum the declared bytes of ``WS-Posting-Record`` [copybooks/wspost.cob].

    Reproduces ``function Length (WS-Posting-Record)``
    [common/acas006.cbl:L595-L597]. Derived from the dictionary rather than
    transcribed, per the AAP section 0.8.1 directive that field metadata be read
    from the dictionary and never by eye. Group items are skipped because their
    children carry the bytes: ``WS-Post-Key`` contributes through ``Batch`` and
    ``Post-Number`` [copybooks/wspost.cob:L15-L16], the two fields the table has
    no column for.
    """
    total = 0
    for entry in loader.entries_for_copybook_record("WS-Posting-Record"):
        if entry.copybook.is_group:
            continue
        total += _declared_bytes(entry.key)
    return total


#: `function Length (WS-Posting-Record)` [common/acas006.cbl:L595-L597].
WS_POSTING_RECORD_BYTES: Final[int] = _ws_posting_record_bytes()

#: The field-description record's declared fields, transcribed from
#: [copybooks/fdpost.cob:L12-L28] as ``(name, bytes)``. The dictionary does not
#: catalogue ``fdpost.cob`` - it is the file description of the same record and
#: has no table of its own - so this list is transcribed from the frozen source
#: and derived independently of :data:`WS_POSTING_RECORD_BYTES`, which is what
#: makes the comparison in :func:`ba012_test_ws_rec_size_2` a genuine comparison
#: rather than an identity.
POSTING_RECORD_DECLARED_FIELDS: Final[tuple[tuple[str, int], ...]] = (
    ("Post-rrn", 5),  # pic 9(5)        [copybooks/fdpost.cob:L13]
    ("Batch", 5),  # pic 9(5)        [copybooks/fdpost.cob:L15]
    ("Post-Number", 5),  # pic 9(5)        [copybooks/fdpost.cob:L16]
    ("Post-Code", 2),  # pic xx          [copybooks/fdpost.cob:L17]
    ("Post-Date", 8),  # pic x(8)        [copybooks/fdpost.cob:L18]
    ("Post-DR", 6),  # pic 9(6)        [copybooks/fdpost.cob:L19]
    ("DR-PC", 2),  # pic 99          [copybooks/fdpost.cob:L20]
    ("Post-CR", 6),  # pic 9(6)        [copybooks/fdpost.cob:L21]
    ("CR-PC", 2),  # pic 99          [copybooks/fdpost.cob:L22]
    ("Post-Amount", 10),  # pic s9(8)v99   [copybooks/fdpost.cob:L23]
    ("Post-Legend", 32),  # pic x(32)       [copybooks/fdpost.cob:L24]
    ("Vat-AC", 6),  # pic 9(6)        [copybooks/fdpost.cob:L25]
    ("Vat-PC", 2),  # pic 99          [copybooks/fdpost.cob:L26]
    ("Post-Vat-Side", 2),  # pic xx          [copybooks/fdpost.cob:L27]
    ("Vat-Amount", 10),  # pic s9(8)v99   [copybooks/fdpost.cob:L28]
)

#: `function length (Posting-Record)` [common/acas006.cbl:L598-L600].
POSTING_RECORD_BYTES: Final[int] = sum(
    declared for _name, declared in POSTING_RECORD_DECLARED_FIELDS
)

#: ANOMALY N-901-DEAD. The two records are declared field for field identically,
#: differing only in the ``WS-`` name prefixes, so both lengths are 103 and
#: ``if A < B`` [common/acas006.cbl:L601] can never be true. ``WE-Error 901``
#: [:L602], ``FS-Reply 99`` [:L603], the ``GL903`` message [:L606-L612], the two
#: displays [:L613-L614], the ``SQL-Msg`` copy [:L615] and the
#: ``go to ba-rdbms-exit`` [:L620] are therefore unreachable. Both copybook
#: headers claim "98 bytes 26/03/09" and "96 bytes 20/12/11 (leading sign
#: removed)", and the trailing byte-offset comments describe a pre-2017 layout in
#: which ``Post-Legend`` was ``x(30)``; the record has been 103 bytes since
#: ``WS-Post-rrn`` was added [copybooks/wspost.cob:L9].
RECORD_SIZE_GUARD_IS_UNREACHABLE: Final[bool] = (
    WS_POSTING_RECORD_BYTES >= POSTING_RECORD_BYTES
)


# ---------------------------------------------------------------------------
# Errors this module raises
# ---------------------------------------------------------------------------


class CobolFlatFileStoreUnavailableError(AcasFileHandlerFatalError):
    """Raised where the Cobol flat-file branch would execute an ISAM verb.

    ``acas006`` has two halves: ``aa-Process-Flat-File`` drives an indexed file
    declared by [copybooks/selpost.cob] and [copybooks/fdpost.cob], and
    ``ba-Process-RDBMS`` calls the bridge. Which half runs is decided by
    ``FS-Cobol-Files-Used`` [common/acas006.cbl:L315, :L322].

    The migrated artifact has no ISAM store - AAP section 0.2.1.2 scopes the
    Python target to SQL against the frozen schema, and rule R-1 forbids reaching
    back into the COBOL runtime that provides the indexed organisation - so this
    is a documented non-reproduction, recorded in the module docstring. It adds
    no accept/reject decision the COBOL does not have, so it is not a new
    validation under R-3, and it is unreachable on the RDB path the posting cycle
    runs on.
    """

    def __init__(self, detail: str, *, operation: str = "", table: str = "") -> None:
        """Carry the explanation, and a status pair that claims nothing.

        ``FS-Reply`` is 99, the vocabulary's only general failure
        [common/glpostingMT.cbl:L131], and ``We-Error`` is left at zero BECAUSE
        THE FROZEN SOURCE WRITES NONE HERE: no paragraph of either program has a
        status for "the indexed organisation is absent", so inventing a detail
        code would be inventing behaviour (rule R-3). The same reasoning the
        ANOMALY N-NOSTATUS sites embody, applied to a condition the COBOL cannot
        reach.

        Args:
            detail: What could not be done, and what to configure instead.
            operation: The COBOL verb, for the base class message.
            table: The table involved, for the base class message.
        """
        super().__init__(
            FsReply.ERROR,
            WeError.SUCCESS,
            operation=operation,
            table=table,
        )
        self.detail = detail
        self.args = (detail,)

    def __str__(self) -> str:
        """The explanation, which is the only useful thing to print."""
        return self.detail


class BridgeNotOpenError(AcasFileHandlerFatalError):
    """Raised when a bridge verb other than ``Open`` runs with no connection.

    ``glpostingMT`` keeps its connection in ``Ws-Mysql-Cid``, set by
    ``MYSQL-1000-OPEN`` [copybooks/mysql-procedures.cpy:L63-L86] and used by
    every later statement. A COBOL run that issued a ``Read-Next`` before an
    ``Open`` would pass a null connection identifier to the C interface, whose
    behaviour is undefined; this exception replaces undefined behaviour with a
    named failure rather than inventing a status code the frozen source does not
    write at that point.
    """

    def __init__(self, detail: str, *, operation: str = "", table: str = "") -> None:
        """Carry the explanation, with ``FS-Reply`` 99 and no detail code.

        ``We-Error`` stays zero for the same reason as
        :class:`CobolFlatFileStoreUnavailableError`: the frozen source writes no
        code for a statement issued against a null connection identifier, and
        rule R-3 forbids adding one.

        Args:
            detail: What was attempted, and what must happen first.
            operation: The COBOL verb, for the base class message.
            table: The table involved, for the base class message.
        """
        super().__init__(
            FsReply.ERROR,
            WeError.SUCCESS,
            operation=operation,
            table=table,
        )
        self.detail = detail
        self.args = (detail,)

    def __str__(self) -> str:
        """The explanation, which is the only useful thing to print."""
        return self.detail


# ---------------------------------------------------------------------------
# `WS-MYSQL-EDIT` rendering - the exact text the bridge builds
# ---------------------------------------------------------------------------


def _edit_field_image(value: Decimal) -> str:
    """Build the thirty-character ``WS-MYSQL-EDIT`` image for ``value``.

    Reproduces ``MOVE HV-<field> TO WS-MYSQL-EDIT`` where
    ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` [common/glpostingMT.cbl:L217]:

    * position 1 is the sign - a space when positive, ``-`` when negative;
    * positions 2..19 are ``Z(18)``, so a leading zero prints as a space;
    * position 20 is ``9``, so the units digit always prints, and a value of
      zero renders as eighteen spaces then ``0``;
    * position 21 is the decimal point;
    * positions 22..30 are ``9(9)`` and are never suppressed.

    Args:
        value: The host variable's value, already stored into the host variable
            with COBOL ``MOVE`` semantics by :func:`_store_numeric_into_hv`.

    Returns:
        The thirty-character image, exactly as the COBOL field would hold it.
    """
    sign = "-" if value < 0 else " "
    magnitude = -value if value < 0 else value
    integer_part = int(magnitude)
    # Nine fractional digits, taken EXACTLY. Both the subtraction and `scaleb`
    # are Decimal operations, so no binary floating point is involved anywhere
    # (R-2), and no rounding occurs because the host variable never carries more
    # than two fractional digits in this table.
    fraction_digits = str(int((magnitude - integer_part).scaleb(9))).rjust(
        EDIT_FIELD_WIDTH - EDIT_FIELD_FRACTION_START + 1, "0"
    )
    # Positions 2..20: nineteen character positions, the value right-aligned so
    # that its units digit lands on position 20.
    integer_image = str(integer_part).rjust(
        EDIT_FIELD_INTEGER_END - EDIT_FIELD_SIGN_POSITION
    )
    return f"{sign}{integer_image}.{fraction_digits}"


def _edit_window(image: str, start: int, length: int) -> str:
    """Take ``WS-MYSQL-EDIT (start:length)`` and apply ``FUNCTION TRIM``.

    COBOL reference modification is one-based, so position ``start`` is index
    ``start - 1``. ``FUNCTION TRIM`` with no direction removes leading and
    trailing spaces, which is what turns the ``Z``-suppressed leading positions
    into nothing.

    Args:
        image: The thirty-character edit-field image.
        start: The one-based starting position of the window.
        length: The window length in characters.

    Returns:
        The trimmed window text.
    """
    return image[start - 1 : start - 1 + length].strip()



def _as_exact_decimal(value: object, *, where: str) -> Decimal:
    """Coerce a caller value to :class:`~decimal.Decimal`, exactly.

    Rule R-2 is absolute: "No accounting value may pass through a binary
    floating-point type at any point - not in computation, not in storage, not in
    transport." A binary floating-point argument is refused rather than
    converted, because ``Decimal(0.1)`` would silently carry the binary
    approximation into the column. The guard is an ALLOW-list - ``int``,
    ``Decimal`` and digit strings - so it refuses every inexact numeric type,
    not merely the ones anticipated here.

    Args:
        value: An ``int``, a ``Decimal``, or a digit string.
        where: The host-variable name, for the error message.

    Returns:
        The value as an exact :class:`~decimal.Decimal`.

    Raises:
        BinaryFloatingPointError: If ``value`` is an inexact numeric type -
            anything other than ``int``, ``Decimal`` or a digit string.
        TypeError: If ``value`` is a boolean, which is an ``int`` subclass but
            never a posting amount.
    """
    if isinstance(value, bool):
        # `bool` is an `int` subclass; a condition flag is not a posting amount.
        raise TypeError(f"{where}: a boolean is not a numeric host-variable value")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    raise BinaryFloatingPointError(
        f"{where}: {type(value).__name__} is not an exact numeric type; rule R-2 "
        f"admits only int, Decimal and digit strings into a host variable"
    )


def _store_numeric_into_hv(
    value: object,
    *,
    name: str,
    digits: int,
    scale: int,
    signed: bool,
) -> Decimal:
    """Reproduce ``MOVE <record field> TO <numeric host variable>``.

    Three COBOL store rules apply, in this order:

    1. **Low-order truncation.** A ``MOVE`` into a field with fewer fractional
       digits than the sender truncates toward zero; it does not round. AAP
       section 0.6.1 settles the direction: rounding happens only at the five
       annotated ``ROUNDED`` sites in the whole migration, none of which is in
       this bridge.
    2. **High-order truncation.** Digits that do not fit the receiving field's
       integer positions are discarded. Every host variable in this group is at
       least as wide as its record field [see the drift table in the module
       docstring], so this never fires for a record the copybook describes; it is
       reproduced so that an out-of-range value behaves as the COBOL would rather
       than raising.
    3. **Sign stripping.** A ``MOVE`` of a signed value into an UNSIGNED field
       stores the absolute value. Eleven of the thirteen loaded host variables
       here are unsigned, so this is the same drift class as AAP section 0.6.7
       entry 11 - the sign is lost at the bridge, before any SQL executes.

    Args:
        value: The record field's value.
        name: The host-variable name, for diagnostics.
        digits: The host variable's total declared digits.
        scale: The host variable's declared fractional digits.
        signed: Whether the host variable's picture carries ``S``.

    Returns:
        The value as the host variable would hold it, scaled to ``scale``.
    """
    exact = _as_exact_decimal(value, where=name)
    # Rule 1: truncate toward zero to the receiving scale. `int()` on the shifted
    # Decimal truncates by definition, so no rounding mode is consulted and the
    # direction cannot drift with the ambient decimal context.
    truncated_units = int(exact.scaleb(scale))
    # Rule 2: discard digits that do not fit the receiving field. The modulus is
    # 10 ** total declared digits because `truncated_units` is already expressed
    # in the field's smallest unit. Taking the magnitude first keeps the
    # operation sign-agnostic, so a negative value truncates its high-order
    # digits exactly as a positive one does.
    magnitude = abs(truncated_units) % (10**digits)
    # Rule 3: an unsigned receiving field keeps no sign at all.
    if signed and truncated_units < 0:
        magnitude = -magnitude
    return Decimal(magnitude).scaleb(-scale)


def _store_alphanumeric_into_hv(value: object, *, name: str, length: int) -> str:
    """Reproduce ``MOVE <record field> TO <alphanumeric host variable>``.

    A COBOL alphanumeric ``MOVE`` is left-justified: the sender is truncated on
    the right when it is longer than the receiver and space-filled on the right
    when it is shorter. The receiving field always holds exactly ``length``
    characters, which is why the ``FUNCTION TRIM (..., TRAILING)`` that follows
    in the ``INSERT`` has something to trim.

    Args:
        value: The record field's value.
        name: The host-variable name, for diagnostics.
        length: The host variable's declared character length.

    Returns:
        Exactly ``length`` characters.

    Raises:
        TypeError: If ``value`` is not a string.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{name}: an alphanumeric host variable takes str, not "
            f"{type(value).__name__}"
        )
    return value[:length].ljust(length)


@dataclass(frozen=True, slots=True)
class GlPostingColumn:
    """One column of ``GLPOSTING-REC``, described entirely from the dictionary.

    Every attribute is read from ``data_dictionary/acas_posting_dictionary.json``
    at import time; nothing is transcribed by eye. That is the AAP section 0.8.1
    directive: "Data dictionary first. ... every Python field definition cites
    its entry. This ordering is a directive, not a preference - it is what
    prevents fields being transcribed by eye."

    The three views the dictionary joins are the authoritative triple of this
    migration: the copybook picture clause [copybooks/wspost.cob], the bridge
    host-variable declaration [common/glpostingMT.cbl:L280-L296] and the
    column definition in the frozen schema [mysql/ACASDB.sql:L154-L170].
    """

    #: `ordinal` of the column in the frozen table definition, 1-based
    #: [mysql/ACASDB.sql:L155-L168].
    ordinal: int
    #: The column name, hyphens and all [mysql/ACASDB.sql:L155-L168].
    name: str
    #: The data-dictionary key, e.g. ``GLPOSTING-REC.POST-AMOUNT``.
    dictionary_key: str
    #: ``loader.cite(dictionary_key)`` - the three-source citation, verbatim.
    citation: str
    #: ``loader.drift_for(dictionary_key).details`` - never re-derived here.
    drift_details: tuple[str, ...]
    #: The declared SQL type, e.g. ``decimal(10,2)``.
    sql_type: str
    #: Whether the column is the table's primary key.
    is_primary_key: bool
    #: Whether the column is declared ``unsigned``.
    column_unsigned: bool
    #: The DDL ``COMMENT``, present on ``POST-RRN`` alone in this table.
    column_comment: str | None
    #: The copybook field name, e.g. ``Post-Amount`` [copybooks/wspost.cob].
    cb_name: str
    #: The copybook picture, e.g. ``s9(8)v99``; ``None`` for the group item.
    cb_picture: str | None
    #: The copybook ``USAGE``: ``DISPLAY``, ``ALPHANUMERIC`` or ``GROUP``. Both
    #: money fields are ``DISPLAY`` - zoned, NOT ``COMP-3``
    #: [copybooks/wspost.cob:L23, :L28].
    cb_usage: str
    #: Whether the copybook picture carries ``S``.
    cb_signed: bool
    #: Copybook total digits, or ``None`` for an alphanumeric or group item.
    cb_digits: int | None
    #: Copybook fractional digits, or ``None``.
    cb_scale: int | None
    #: Copybook character length, or ``None`` for a numeric or group item.
    cb_character_length: int | None
    #: Whether the copybook side is a group item, as ``WS-Post-Key`` is.
    cb_is_group: bool
    #: The bridge host-variable name, e.g. ``HV-POST-AMOUNT``.
    hv_name: str
    #: The host variable's picture, e.g. ``S9(08)V9(02)``.
    hv_picture: str
    #: The host variable's ``USAGE``, e.g. ``COMP``.
    hv_usage: str
    #: Whether the host variable's picture carries ``S``.
    hv_signed: bool
    #: Total declared digits, or ``None`` for an alphanumeric host variable.
    hv_digits: int | None
    #: Declared fractional digits, or ``None`` for an alphanumeric.
    hv_scale: int | None
    #: Declared character length, or ``None`` for a numeric host variable.
    hv_character_length: int | None
    #: Whether ``bb000-HV-Load`` moves the record field into this host variable.
    loaded_from_record: bool
    #: The load statement's locator, or ``None`` when there is no load.
    load_source: str | None
    #: Whether ``bb100-UnloadHVs`` moves this host variable back into the record.
    unloaded_to_record: bool
    #: The unload statement's locator, or ``None`` when there is no unload.
    unload_source: str | None
    #: The :class:`WsPostingRecord` attribute this column corresponds to.
    record_attribute: str
    #: ``CobolPythonStorage`` for the record side: ``INT``, ``DECIMAL``, ``STR``
    #: or ``NONE`` for the group item. The record class holds the non-money
    #: numerics as ``int`` and the two money fields as
    #: :class:`~decimal.Decimal`, so an unload coerces to whichever the
    #: dictionary names.
    python_storage: str

    @property
    def quoted_name(self) -> str:
        """The column name, backtick-quoted.

        Every identifier in this schema contains a hyphen, so an unquoted name is
        a MySQL syntax error. Quoting is delegated to
        :func:`acas_posting.dal.connection.quote_identifier`, which owns the
        escaping rule.
        """
        return quote_identifier(self.name)

    @property
    def is_alphanumeric(self) -> bool:
        """Whether the host variable is ``PIC X(n)`` rather than numeric."""
        return self.hv_character_length is not None

    @property
    def edit_integer_window(self) -> tuple[int, int]:
        """The ``WS-MYSQL-EDIT`` integer window as ``(start, length)``.

        Derived, not transcribed: the edit field's integer positions end at
        position 20 [common/glpostingMT.cbl:L217], so an ``n``-digit integer
        starts at ``21 - n``. That single expression yields every window the
        bridge writes - ``(13:08)`` for the eight-digit items, ``(03:18)`` for
        the eighteen-digit key, ``(18:03)`` for the three-digit percentages.
        """
        digits = self.hv_digits or 0
        scale = self.hv_scale or 0
        integer_digits = digits - scale
        return (EDIT_FIELD_INTEGER_END + 1 - integer_digits, integer_digits)

    @property
    def edit_fraction_window(self) -> tuple[int, int]:
        """The ``WS-MYSQL-EDIT`` fraction window as ``(start, length)``.

        Always starts at position 22, which is why both money fields render
        ``(22:02)``. A zero-scale column has a zero-length window and renders no
        decimal point at all.
        """
        return (EDIT_FIELD_FRACTION_START, self.hv_scale or 0)

    def store(self, value: object) -> Decimal | str:
        """Reproduce the ``MOVE`` of a record field into this host variable."""
        if self.is_alphanumeric:
            return _store_alphanumeric_into_hv(
                value, name=self.hv_name, length=int(self.hv_character_length or 0)
            )
        return _store_numeric_into_hv(
            value,
            name=self.hv_name,
            digits=int(self.hv_digits or 0),
            scale=int(self.hv_scale or 0),
            signed=self.hv_signed,
        )

    def store_into_record(self, hv_value: Decimal | str) -> Decimal | str:
        """Reproduce the ``MOVE`` of this host variable back into the record.

        This is the reverse direction of :meth:`store` and it is not symmetric,
        because the host variable is WIDER than the record field for every
        numeric column in this table except the two money fields: the record
        declares ``9(6)`` where the host variable declares ``9(08)``, and ``99``
        where it declares ``9(03)`` [see the drift table in the module
        docstring]. An unload therefore truncates the high-order digits of any
        value the column carried beyond the record's declared width, exactly as a
        COBOL ``MOVE`` into the narrower field would.

        The group item ``WS-Post-Key`` has no picture of its own, so it is not
        handled here; :func:`bb100_unload_hvs` splits it into ``Batch`` and
        ``Post-Number`` as the group ``MOVE`` does.
        """
        if self.cb_character_length is not None:
            return _store_alphanumeric_into_hv(
                hv_value,
                name=self.cb_name,
                length=int(self.cb_character_length),
            )
        if self.cb_digits is None:
            raise ValueError(
                f"{self.cb_name} is a group item; bb100-UnloadHVs splits it "
                f"rather than moving it as one field"
            )
        return _store_numeric_into_hv(
            hv_value,
            name=self.cb_name,
            digits=int(self.cb_digits),
            scale=int(self.cb_scale or 0),
            signed=self.cb_signed,
        )

    def render(self, hv_value: Decimal | str) -> str:
        """Build the literal text the bridge would place in the statement.

        For an alphanumeric host variable this is ``FUNCTION TRIM (HV-x,
        TRAILING)`` [common/glpostingMT.cbl:L1146-L1148 and siblings]: only
        trailing spaces go, so a leading space survives.

        For a numeric host variable it is ``MOVE HV-x TO WS-MYSQL-EDIT``
        followed by ``STRING FUNCTION TRIM (WS-MYSQL-EDIT (s:l))``, with a
        literal ``"."`` between the two windows when the column has a scale
        [common/glpostingMT.cbl:L1196-L1210 for ``POST-AMOUNT``].

        ANOMALY N-EDIT is reproduced here rather than worked around: the sign
        occupies position 1 of the edit field [common/glpostingMT.cbl:L217] and
        no window the bridge takes starts before position 3, so a negative
        ``POST-AMOUNT`` or ``VAT-AMOUNT`` renders as its absolute value and is
        stored that way.
        """
        if isinstance(hv_value, str):
            # `FUNCTION TRIM (..., TRAILING)` - spaces only, and only on the
            # right.
            return hv_value.rstrip(" ")
        image = _edit_field_image(hv_value)
        integer_start, integer_length = self.edit_integer_window
        integer_text = _edit_window(image, integer_start, integer_length)
        fraction_start, fraction_length = self.edit_fraction_window
        if fraction_length == 0:
            return integer_text
        fraction_text = _edit_window(image, fraction_start, fraction_length)
        return f"{integer_text}.{fraction_text}"

    def bind(self, hv_value: Decimal | str) -> Decimal | int | str:
        """The value to bind for this column, derived from :meth:`render`.

        The bridge interpolates its rendered text straight into the statement
        [common/glpostingMT.cbl:L1120-L1287]. This module binds instead, matching
        the decision :mod:`acas_posting.dal.cursor_state` already documents for
        the positioning statements: interpolation is transport, and a bound
        parameter yields the same logical value while removing an injection route
        the frozen source left open.

        The bound value is derived FROM the rendered text and not from the host
        variable, so every rendering anomaly - N-EDIT above all - reaches the
        column exactly as the COBOL would have sent it. Nothing is ever bound as
        ``None``: all fourteen columns are ``NOT NULL``
        [mysql/ACASDB.sql:L155-L168] and ``initialize TD-GLPOSTING-REC``
        [common/glpostingMT.cbl:L1053] guarantees a zero or a space instead.
        """
        text = self.render(hv_value)
        if self.is_alphanumeric:
            return text
        if (self.hv_scale or 0) > 0:
            return Decimal(text)
        return int(text)


def _build_columns() -> tuple[GlPostingColumn, ...]:
    """Build :data:`COLUMNS` from the dictionary, in COLUMN-ORDINAL order.

    ``loader.entries_for_table`` returns the table's entries; they are sorted on
    the column ordinal so that the emitted column list matches the declared
    order of the frozen table [mysql/ACASDB.sql:L155-L168] and, with it, the
    order of the bridge's own ``INSERT``
    [common/glpostingMT.cbl:L1120-L1287]. The ordering is fixed data, which is
    what makes the generated statement byte-identical across processes (R-6).

    The record attribute for each column comes from
    ``loader.field_keys_for(WsPostingRecord())``, so the column-to-attribute
    correspondence is dictionary-derived too.
    """
    attribute_by_key = {
        key: attribute
        for attribute, key in loader.field_keys_for(WsPostingRecord()).items()
    }
    built: list[GlPostingColumn] = []
    for entry in sorted(
        loader.entries_for_table(TABLE_NAME), key=lambda item: item.column.ordinal
    ):
        host_variable = entry.bridge_host_variable
        column = entry.column
        copybook_field = entry.copybook
        built.append(
            GlPostingColumn(
                ordinal=int(column.ordinal),
                name=column.name,
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                drift_details=tuple(loader.drift_for(entry.key).details),
                sql_type=column.sql_type,
                is_primary_key=bool(column.is_primary_key),
                column_unsigned=bool(column.unsigned),
                column_comment=column.comment,
                cb_name=copybook_field.name,
                cb_picture=copybook_field.picture,
                cb_usage=copybook_field.usage.value,
                cb_signed=bool(copybook_field.signed),
                cb_digits=copybook_field.digits,
                cb_scale=copybook_field.scale,
                cb_character_length=copybook_field.character_length,
                cb_is_group=bool(copybook_field.is_group),
                hv_name=host_variable.name,
                hv_picture=str(host_variable.picture),
                hv_usage=host_variable.usage.value,
                hv_signed=bool(host_variable.signed),
                hv_digits=host_variable.digits,
                hv_scale=host_variable.scale,
                hv_character_length=host_variable.character_length,
                loaded_from_record=bool(host_variable.loaded_from_record),
                load_source=host_variable.load_source,
                unloaded_to_record=bool(host_variable.unloaded_to_record),
                unload_source=host_variable.unload_source,
                record_attribute=attribute_by_key[entry.key],
                python_storage=entry.cobol_python_storage.value,
            )
        )
    return tuple(built)


#: The fourteen columns, in the frozen table's declared ordinal order
#: [mysql/ACASDB.sql:L155-L168].
COLUMNS: Final[tuple[GlPostingColumn, ...]] = _build_columns()

#: The same columns, reachable by column name.
COLUMNS_BY_NAME: Final[Mapping[str, GlPostingColumn]] = MappingProxyType(
    {column.name: column for column in COLUMNS}
)

#: The column names in ordinal order - the order every statement emits.
COLUMN_NAMES: Final[tuple[str, ...]] = tuple(column.name for column in COLUMNS)

#: ANOMALY N-RRN, asserted from the dictionary rather than assumed. ``POST-RRN``
#: is the primary key [mysql/ACASDB.sql:L169] and is the one host variable
#: ``bb000-HV-Load`` never moves into [common/glpostingMT.cbl:L282 declared,
#: absent from :L1053-L1066], nor does ``bb100-UnloadHVs`` move it back
#: [:L1083-L1097]. It IS named in both fetch lists [:L538, :L645] and in both
#: the ``INSERT`` [:L1120-L1130] and the ``UPDATE`` [:L1309-L1319], so it is
#: written from whatever ``initialize TD-GLPOSTING-REC`` [:L1053] left - zero.
PRIMARY_KEY_IS_NEVER_LOADED: Final[bool] = not COLUMNS_BY_NAME[
    PRIMARY_KEY_COLUMN
].loaded_from_record

#: The host-variable naming invariant, asserted from the dictionary rather than
#: transcribed. In the host-variable group [common/glpostingMT.cbl:L282-L295]
#: every one of the fourteen names is ``HV-`` prefixed to its column name from
#: the frozen table definition [mysql/ACASDB.sql:L155-L168] without exception
#: - which
#: is why the drift table in the module docstring omits a host-variable column.
#: It is a regularity of the generator, not a guarantee, so it is checked here
#: instead of relied upon: nothing in this module derives one name from the
#: other, every statement takes its identifiers from :data:`COLUMN_NAMES` and
#: every host variable from :attr:`GlPostingColumn.hv_name`.
HOST_VARIABLE_NAMES_ARE_HV_PREFIXED: Final[bool] = all(
    column.hv_name == "HV-" + column.name for column in COLUMNS
)



# ---------------------------------------------------------------------------
# `01 TD-GLPOSTING-REC.` - THE CANONICAL HOST-VARIABLE GROUP
# ---------------------------------------------------------------------------


def _initialised_hv_value(column_name: str) -> Decimal | str:
    """The value ``initialize TD-GLPOSTING-REC`` leaves in one host variable.

    COBOL ``INITIALIZE`` sets numeric items to zero and alphanumeric items to
    spaces. This is the statement that makes every column of the table
    declarable ``NOT NULL``: AAP section 0.6.2 puts it as "unset fields become
    zero or space rather than SQL ``NULL`` ... This is why every column in the
    schema can be declared ``NOT NULL`` and why the Python layer must default
    rather than omit."

    Args:
        column_name: The column whose host variable is being initialised.

    Returns:
        Zero at the host variable's declared scale, or its width in spaces.
    """
    column = COLUMNS_BY_NAME[column_name]
    if column.is_alphanumeric:
        return " " * int(column.hv_character_length or 0)
    return Decimal(0).scaleb(-(column.hv_scale or 0))


@dataclass(slots=True)
class TdGlpostingRec:
    """``01 TD-GLPOSTING-REC.`` - the host-variable group, VERBATIM.

    Transcribed from [common/glpostingMT.cbl:L280-L296]::

        L280         01  TP-GLPOSTING-REC                      USAGE POINTER.
        L281         01  TD-GLPOSTING-REC.
        L282             05  HV-POST-RRN                       PIC  9(08) COMP.
        L283             05  HV-POST-KEY                       PIC  9(18) COMP.
        L284             05  HV-POST-CODE                      PIC X(2).
        L285             05  HV-POST-DAT                       PIC X(8).
        L286             05  HV-POST-DR                        PIC  9(08) COMP.
        L287             05  HV-DR-PC                          PIC  9(03) COMP.
        L288             05  HV-POST-CR                        PIC  9(08) COMP.
        L289             05  HV-CR-PC                          PIC  9(03) COMP.
        L290             05  HV-POST-AMOUNT                    PIC S9(08)V9(02) COMP.
        L291             05  HV-POST-LEGEND                    PIC X(32).
        L292             05  HV-VAT-AC                         PIC  9(08) COMP.
        L293             05  HV-VAT-PC                         PIC  9(03) COMP.
        L294             05  HV-POST-VAT-SIDE                  PIC X(2).
        L295             05  HV-VAT-AMOUNT                     PIC S9(08)V9(02) COMP.
        L296  *> /MYSQL-END\\

    The group is declared by the JC preSQL directive
    [common/glpostingMT.scb:L273-L276], reproduced in
    :data:`MYSQL_VAR_DIRECTIVE`. ``TP-GLPOSTING-REC USAGE POINTER`` [:L280] is
    the C-interface pointer to the group and has no Python counterpart: the
    driver binds values directly, so there is no address to pass. Recorded as a
    deliberate omission (R-5).

    Constructing the class with no arguments IS ``initialize
    TD-GLPOSTING-REC``: every default is derived from the dictionary by
    :func:`_initialised_hv_value`, so the zeros and spaces come from the declared
    pictures rather than being written out here.

    NOTE ON THE FIELD ORDER: the attributes below are in the group's DECLARATION
    order, which is also the column order. The order in which
    :func:`bb000_hv_load` WRITES them is different, and that difference is
    anomaly N-loadorder.
    """

    #: `05  HV-POST-RRN  PIC 9(08) COMP.` [common/glpostingMT.cbl:L282].
    #: ANOMALY N-RRN: never loaded [absent from :L1053-L1066], never unloaded
    #: [absent from :L1083-L1097], yet the table's ``PRIMARY KEY``
    #: [mysql/ACASDB.sql:L169].
    hv_post_rrn: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-RRN")
    )
    #: `05  HV-POST-KEY  PIC 9(18) COMP.` [common/glpostingMT.cbl:L283].
    hv_post_key: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-KEY")
    )
    #: `05  HV-POST-CODE  PIC X(2).` [common/glpostingMT.cbl:L284].
    hv_post_code: str = field(
        default_factory=lambda: _initialised_hv_value("POST-CODE")
    )
    #: `05  HV-POST-DAT  PIC X(8).` [common/glpostingMT.cbl:L285].
    hv_post_dat: str = field(
        default_factory=lambda: _initialised_hv_value("POST-DAT")
    )
    #: `05  HV-POST-DR  PIC 9(08) COMP.` [common/glpostingMT.cbl:L286].
    hv_post_dr: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-DR")
    )
    #: `05  HV-DR-PC  PIC 9(03) COMP.` [common/glpostingMT.cbl:L287].
    hv_dr_pc: Decimal = field(
        default_factory=lambda: _initialised_hv_value("DR-PC")
    )
    #: `05  HV-POST-CR  PIC 9(08) COMP.` [common/glpostingMT.cbl:L288].
    hv_post_cr: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-CR")
    )
    #: `05  HV-CR-PC  PIC 9(03) COMP.` [common/glpostingMT.cbl:L289].
    hv_cr_pc: Decimal = field(
        default_factory=lambda: _initialised_hv_value("CR-PC")
    )
    #: `05  HV-POST-AMOUNT  PIC S9(08)V9(02) COMP.`
    #: [common/glpostingMT.cbl:L290]. Signed here, signed in the copybook and
    #: signed in the column - yet ANOMALY N-EDIT drops the sign on the way out.
    hv_post_amount: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-AMOUNT")
    )
    #: `05  HV-POST-LEGEND  PIC X(32).` [common/glpostingMT.cbl:L291].
    hv_post_legend: str = field(
        default_factory=lambda: _initialised_hv_value("POST-LEGEND")
    )
    #: `05  HV-VAT-AC  PIC 9(08) COMP.` [common/glpostingMT.cbl:L292].
    hv_vat_ac: Decimal = field(
        default_factory=lambda: _initialised_hv_value("VAT-AC")
    )
    #: `05  HV-VAT-PC  PIC 9(03) COMP.` [common/glpostingMT.cbl:L293].
    hv_vat_pc: Decimal = field(
        default_factory=lambda: _initialised_hv_value("VAT-PC")
    )
    #: `05  HV-POST-VAT-SIDE  PIC X(2).` [common/glpostingMT.cbl:L294].
    hv_post_vat_side: str = field(
        default_factory=lambda: _initialised_hv_value("POST-VAT-SIDE")
    )
    #: `05  HV-VAT-AMOUNT  PIC S9(08)V9(02) COMP.`
    #: [common/glpostingMT.cbl:L295].
    hv_vat_amount: Decimal = field(
        default_factory=lambda: _initialised_hv_value("VAT-AMOUNT")
    )

    #: Column name to attribute name, so that the statement builders can walk
    #: :data:`COLUMNS` in ordinal order and reach the matching host variable
    #: without a second hand-written table. ``ClassVar`` so that ``dataclass``
    #: treats it as a lookup table and not as a fifteenth host variable.
    ATTRIBUTE_BY_COLUMN: ClassVar[Mapping[str, str]] = MappingProxyType(
        {
            "POST-RRN": "hv_post_rrn",
            "POST-KEY": "hv_post_key",
            "POST-CODE": "hv_post_code",
            "POST-DAT": "hv_post_dat",
            "POST-DR": "hv_post_dr",
            "DR-PC": "hv_dr_pc",
            "POST-CR": "hv_post_cr",
            "CR-PC": "hv_cr_pc",
            "POST-AMOUNT": "hv_post_amount",
            "POST-LEGEND": "hv_post_legend",
            "VAT-AC": "hv_vat_ac",
            "VAT-PC": "hv_vat_pc",
            "POST-VAT-SIDE": "hv_post_vat_side",
            "VAT-AMOUNT": "hv_vat_amount",
        }
    )

    def value_for(self, column: GlPostingColumn) -> Decimal | str:
        """The host variable corresponding to ``column``."""
        return getattr(self, self.ATTRIBUTE_BY_COLUMN[column.name])

    def set_for(self, column: GlPostingColumn, value: Decimal | str) -> None:
        """Store ``value`` into the host variable corresponding to ``column``."""
        setattr(self, self.ATTRIBUTE_BY_COLUMN[column.name], value)


def _join_post_key(key: WsPostKey) -> Decimal:
    """Reproduce ``move WS-Post-Key to HV-POST-KEY`` - the group concatenation.

    ``WS-Post-Key`` is a group of two ``pic 9(5)`` items, ``Batch`` and
    ``Post-Number`` [copybooks/wspost.cob:L14-L16]. Moving a group to a numeric
    item is an alphanumeric-to-numeric ``MOVE``, so the ten digit characters are
    taken as one unsigned ten-digit number and land right-justified in the
    eighteen-digit host variable. The dictionary records the same thing:
    ``Derivation(kind=GROUP_CONCATENATION, expression='move WS-Post-Key to
    HV-POST-KEY', source='common/glpostingMT.cbl:L1054')``.

    ``Batch`` and ``Post-Number`` have no column of their own; they survive only
    inside this concatenation, which the module docstring records as a deliberate
    omission (R-5).

    Args:
        key: The record's ``ws_post_key`` group.

    Returns:
        The concatenated key as an exact :class:`~decimal.Decimal`.
    """
    batch = abs(int(key.batch)) % 100000
    post_number = abs(int(key.post_number)) % 100000
    return Decimal(f"{batch:05d}{post_number:05d}")


def bb000_hv_load(posting: WsPostingRecord) -> TdGlpostingRec:
    """``bb000-HV-Load Section.`` [common/glpostingMT.cbl:L1045].

    THE CANONICAL LOAD PARAGRAPH of this migration - the AAP quotes it in
    sections 0.4.1.5, 0.6.2 and 0.9.4. Transcribed VERBATIM from
    [common/glpostingMT.cbl:L1053-L1066]::

        L1053      initialize TD-GLPOSTING-REC.
        L1054      move     WS-Post-Key      to HV-POST-KEY.
        L1055      move     Post-Code     to HV-POST-CODE.
        L1056      move     Post-Date     to HV-POST-DAT.
        L1057      move     Post-DR       to HV-POST-DR.
        L1058      move     Post-CR       to HV-POST-CR.
        L1059      move     DR-PC         to HV-DR-PC.
        L1060      move     CR-PC         to HV-CR-PC
        L1061      move     Post-Amount   to HV-POST-AMOUNT.
        L1062      move     Post-Legend   to HV-POST-LEGEND.
        L1063      move     Vat-AC        to HV-VAT-AC.
        L1064      move     Vat-PC        to HV-VAT-PC.
        L1065      move     Post-Vat-Side to HV-POST-VAT-SIDE.
        L1066      move     Vat-Amount    to HV-VAT-AMOUNT.

    Four facts about that paragraph, all reproduced below:

    1. ANOMALY N-RRN. ``HV-POST-RRN`` is declared
       [common/glpostingMT.cbl:L282] and appears in NO ``move`` here, yet
       ``POST-RRN`` is the table's ``PRIMARY KEY`` [mysql/ACASDB.sql:L169]. It
       is named in both fetch lists [:L538, :L645], so it is read, and in both
       the ``INSERT`` [:L1120-L1130] and the ``UPDATE`` [:L1309-L1319], so it is
       written - from whatever ``initialize`` left, which is zero. The key is NOT
       loaded here. Loading it "properly" would change every posted row.
    2. ANOMALY N-loadorder. ``Post-CR`` [:L1058] is moved BEFORE ``DR-PC``
       [:L1059], inverted against the host-variable group, which declares
       ``HV-DR-PC`` [:L287] before ``HV-POST-CR`` [:L288], and against the column
       ordinals, where ``DR-PC`` is 6 and ``POST-CR`` is 7. The statement order
       below is the source's, not the column order.
    3. ANOMALY N17. The ``move`` at [:L1060] omits its terminating period. The
       COBOL sentence simply continues into [:L1061], so the semantics are
       unaffected; it is recorded as a style anomaly and the quotation above
       shows the line exactly as it stands.
    4. ``initialize TD-GLPOSTING-REC.`` is the FIRST statement [:L1053], which is
       why every column can be ``NOT NULL`` and why nothing is ever bound as
       ``None`` - see :data:`_initialised_hv_value`.

    The maintainer's closing comment [:L1068-L1069], VERBATIM: "Loading HVs
    implies a non-Fetch action. RGs are handled separately for all such actions
    so they must not be loaded here."

    Args:
        posting: The record the handler was passed.

    Returns:
        A freshly initialised host-variable group with the thirteen loaded
        values in it.
    """
    # `initialize TD-GLPOSTING-REC.` [common/glpostingMT.cbl:L1053] - FIRST, so
    # every host variable holds a zero or a space before anything is moved. This
    # is what leaves HV-POST-RRN at zero.
    host_variables = TdGlpostingRec()

    # The moves below are in the SOURCE's order, which is NOT the column order.
    # HV-POST-RRN is deliberately absent - ANOMALY N-RRN
    # [common/glpostingMT.cbl:L282 declared, :L1053-L1066 never loaded].

    # L1054  move WS-Post-Key to HV-POST-KEY.  - group concatenation
    host_variables.hv_post_key = _join_post_key(posting.ws_post_key)
    # L1055  move Post-Code to HV-POST-CODE.
    host_variables.hv_post_code = COLUMNS_BY_NAME["POST-CODE"].store(
        posting.post_code
    )
    # L1056  move Post-Date to HV-POST-DAT.  - name truncation Date -> DAT
    host_variables.hv_post_dat = COLUMNS_BY_NAME["POST-DAT"].store(posting.post_date)
    # L1057  move Post-DR to HV-POST-DR.
    host_variables.hv_post_dr = COLUMNS_BY_NAME["POST-DR"].store(posting.post_dr)
    # L1058  move Post-CR to HV-POST-CR.   <-- ANOMALY N-loadorder: BEFORE DR-PC
    host_variables.hv_post_cr = COLUMNS_BY_NAME["POST-CR"].store(posting.post_cr)
    # L1059  move DR-PC to HV-DR-PC.       <-- ... which is moved second
    host_variables.hv_dr_pc = COLUMNS_BY_NAME["DR-PC"].store(posting.dr_pc)
    # L1060  move CR-PC to HV-CR-PC        <-- ANOMALY N17: no terminating period
    host_variables.hv_cr_pc = COLUMNS_BY_NAME["CR-PC"].store(posting.cr_pc)
    # L1061  move Post-Amount to HV-POST-AMOUNT.
    host_variables.hv_post_amount = COLUMNS_BY_NAME["POST-AMOUNT"].store(
        posting.post_amount
    )
    # L1062  move Post-Legend to HV-POST-LEGEND.
    host_variables.hv_post_legend = COLUMNS_BY_NAME["POST-LEGEND"].store(
        posting.post_legend
    )
    # L1063  move Vat-AC to HV-VAT-AC.
    host_variables.hv_vat_ac = COLUMNS_BY_NAME["VAT-AC"].store(posting.vat_ac)
    # L1064  move Vat-PC to HV-VAT-PC.
    host_variables.hv_vat_pc = COLUMNS_BY_NAME["VAT-PC"].store(posting.vat_pc)
    # L1065  move Post-Vat-Side to HV-POST-VAT-SIDE.
    host_variables.hv_post_vat_side = COLUMNS_BY_NAME["POST-VAT-SIDE"].store(
        posting.post_vat_side
    )
    # L1066  move Vat-Amount to HV-VAT-AMOUNT.
    host_variables.hv_vat_amount = COLUMNS_BY_NAME["VAT-AMOUNT"].store(
        posting.vat_amount
    )
    return host_variables


def bb100_unload_hvs(
    host_variables: TdGlpostingRec, posting: WsPostingRecord
) -> None:
    """``bb100-UnloadHVs Section.`` [common/glpostingMT.cbl:L1074].

    The reverse of :func:`bb000_hv_load`, run after a successful fetch
    [common/glpostingMT.cbl:L585 for read-next, :L684 for read-indexed].
    Transcribed from [common/glpostingMT.cbl:L1083-L1097]::

        L1083      initialize WS-Posting-Record.
        L1085      move     HV-POST-KEY      to WS-Post-Key.
        L1086      move     HV-POST-CODE     to Post-Code.
        L1087      move     HV-POST-DAT      to Post-Date.
        L1088      move     HV-POST-DR       to Post-DR.
        L1089      move     HV-POST-CR       to Post-CR.
        L1090      move     HV-DR-PC         to DR-PC.
        L1091      move     HV-CR-PC         to CR-PC.
        L1092      move     HV-POST-AMOUNT   to Post-Amount.
        L1093      move     HV-POST-LEGEND   to Post-Legend.
        L1094      move     HV-VAT-AC        to Vat-AC.
        L1095      move     HV-VAT-PC        to Vat-PC.
        L1096      move     HV-POST-VAT-SIDE to Post-Vat-Side.
        L1097      move     HV-VAT-AMOUNT    to Vat-Amount.

    ANOMALY N-UNLOAD: there are only THIRTEEN moves. ``HV-POST-RRN`` is not
    unloaded either, so ``WS-Post-rrn`` keeps the zero that ``initialize
    WS-Posting-Record`` [:L1083] put there, whatever the row's ``POST-RRN``
    held. The caller therefore never learns the relative record number it just
    read.

    ANOMALY N-loadorder appears here too, in the same shape: ``POST-DR`` [:L1088]
    then ``POST-CR`` [:L1089] then ``DR-PC`` [:L1090] then ``CR-PC`` [:L1091].

    ANOMALY N-STALE-COMMENT: the section closes [:L1099-L1100] with "We do not
    need to unload POST4- DAY, MONTH or YEAR as only used in select statements
    instead of a sort." Those columns belong to ``irspostingMT``, not to
    ``GLPOSTING-REC``; the comment is a copy-paste leftover.

    The maintainer's opening note [:L1080-L1081], VERBATIM: "NULL fields must not
    be returned in the buffer. SQL filters each column to ensure it has a proper
    value. This saves using indicator variables."

    Args:
        host_variables: The group a fetch has just populated.
        posting: The record to unload into. MUTATED IN PLACE, exactly as the
            COBOL linkage mutates the caller's record.
    """
    # `initialize WS-Posting-Record.` [common/glpostingMT.cbl:L1083]. The record
    # class's own defaults ARE the initialize semantics - zero for a numeric,
    # spaces at the declared width for an alphanumeric - so a fresh instance is
    # copied field by field rather than a new object being returned, because the
    # COBOL mutates the caller's record rather than replacing it.
    initialised = WsPostingRecord()
    posting.ws_post_rrn = initialised.ws_post_rrn
    posting.ws_post_key.batch = initialised.ws_post_key.batch
    posting.ws_post_key.post_number = initialised.ws_post_key.post_number
    posting.post_code = initialised.post_code
    posting.post_date = initialised.post_date
    posting.post_dr = initialised.post_dr
    posting.dr_pc = initialised.dr_pc
    posting.post_cr = initialised.post_cr
    posting.cr_pc = initialised.cr_pc
    posting.post_amount = initialised.post_amount
    posting.post_legend = initialised.post_legend
    posting.vat_ac = initialised.vat_ac
    posting.vat_pc = initialised.vat_pc
    posting.post_vat_side = initialised.post_vat_side
    posting.vat_amount = initialised.vat_amount

    # ANOMALY N-UNLOAD: no `move HV-POST-RRN to WS-Post-rrn` exists
    # [common/glpostingMT.cbl:L1083-L1097], so ws_post_rrn keeps the zero above.

    # L1085  move HV-POST-KEY to WS-Post-Key.  - the group split, the reverse of
    # the concatenation at :L1054. The eighteen-digit host variable is rendered
    # as ten digits and the halves land in Batch and Post-Number.
    joined = f"{int(host_variables.hv_post_key) % 10**10:010d}"
    posting.ws_post_key.batch = int(joined[:5])
    posting.ws_post_key.post_number = int(joined[5:])
    # L1086  move HV-POST-CODE to Post-Code.
    posting.post_code = _unloaded(host_variables, "POST-CODE")
    # L1087  move HV-POST-DAT to Post-Date.
    posting.post_date = _unloaded(host_variables, "POST-DAT")
    # L1088  move HV-POST-DR to Post-DR.
    posting.post_dr = _unloaded(host_variables, "POST-DR")
    # L1089  move HV-POST-CR to Post-CR.    <-- N-loadorder, mirrored
    posting.post_cr = _unloaded(host_variables, "POST-CR")
    # L1090  move HV-DR-PC to DR-PC.
    posting.dr_pc = _unloaded(host_variables, "DR-PC")
    # L1091  move HV-CR-PC to CR-PC.
    posting.cr_pc = _unloaded(host_variables, "CR-PC")
    # L1092  move HV-POST-AMOUNT to Post-Amount.
    posting.post_amount = _unloaded(host_variables, "POST-AMOUNT")
    # L1093  move HV-POST-LEGEND to Post-Legend.
    posting.post_legend = _unloaded(host_variables, "POST-LEGEND")
    # L1094  move HV-VAT-AC to Vat-AC.
    posting.vat_ac = _unloaded(host_variables, "VAT-AC")
    # L1095  move HV-VAT-PC to Vat-PC.
    posting.vat_pc = _unloaded(host_variables, "VAT-PC")
    # L1096  move HV-POST-VAT-SIDE to Post-Vat-Side.
    posting.post_vat_side = _unloaded(host_variables, "POST-VAT-SIDE")
    # L1097  move HV-VAT-AMOUNT to Vat-Amount.
    posting.vat_amount = _unloaded(host_variables, "VAT-AMOUNT")


def _unloaded(host_variables: TdGlpostingRec, column_name: str) -> Decimal | int | str:
    """One ``move <host variable> to <record field>`` of ``bb100-UnloadHVs``.

    Applies the receiving field's own ``MOVE`` semantics through
    :meth:`GlPostingColumn.store_into_record` - which truncates the high-order
    digits of anything wider than the record declares - and then coerces to the
    Python storage class the dictionary names for the record side, so that an
    ``int`` field receives an ``int`` and a money field a
    :class:`~decimal.Decimal`.
    """
    column = COLUMNS_BY_NAME[column_name]
    stored = column.store_into_record(host_variables.value_for(column))
    if column.python_storage == "INT":
        return int(stored)
    return stored



# ---------------------------------------------------------------------------
# `WS-Posting-Record (K:L)` - the record image, and ANOMALY N-KOR
# ---------------------------------------------------------------------------

#: The record's elementary fields in declaration order, as
#: ``(dictionary key, attribute path)``. Built from the dictionary so the layout
#: is derived rather than transcribed; the two group children ``Batch`` and
#: ``Post-Number`` [copybooks/wspost.cob:L15-L16] carry their own keys under the
#: record's own namespace because the table has no column for either.
_RECORD_IMAGE_LAYOUT: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("GLPOSTING-REC.POST-RRN", ("ws_post_rrn",)),
    ("WS-Posting-Record.Batch", ("ws_post_key", "batch")),
    ("WS-Posting-Record.Post-Number", ("ws_post_key", "post_number")),
    ("GLPOSTING-REC.POST-CODE", ("post_code",)),
    ("GLPOSTING-REC.POST-DAT", ("post_date",)),
    ("GLPOSTING-REC.POST-DR", ("post_dr",)),
    ("GLPOSTING-REC.DR-PC", ("dr_pc",)),
    ("GLPOSTING-REC.POST-CR", ("post_cr",)),
    ("GLPOSTING-REC.CR-PC", ("cr_pc",)),
    ("GLPOSTING-REC.POST-AMOUNT", ("post_amount",)),
    ("GLPOSTING-REC.POST-LEGEND", ("post_legend",)),
    ("GLPOSTING-REC.VAT-AC", ("vat_ac",)),
    ("GLPOSTING-REC.VAT-PC", ("vat_pc",)),
    ("GLPOSTING-REC.POST-VAT-SIDE", ("post_vat_side",)),
    ("GLPOSTING-REC.VAT-AMOUNT", ("vat_amount",)),
)


def _ws_posting_record_image(posting: WsPostingRecord) -> str:
    """Build the fixed-width character image of ``WS-Posting-Record``.

    Needed because the bridge addresses the record by BYTE OFFSET, not by field:
    every ``WHERE`` it builds interpolates ``WS-Posting-Record (K:L)`` with ``K``
    and ``L`` taken from the key table [common/glpostingMT.cbl:L606, :L734,
    :L841, :L919, :L981].

    A zoned ``DISPLAY`` numeric occupies one byte per declared digit, right
    justified and zero filled; an alphanumeric occupies its declared width, left
    justified and space filled.

    ONE DELIBERATE OMISSION, recorded under R-5. The two money fields are
    ``pic s9(8)v99`` with the sign included in the final digit's byte
    [copybooks/wspost.cob:L23, :L28], so a negative value overpunches that byte.
    The exact overpunch character depends on the compiler's sign representation,
    which no flag in this repository selects (AAP section 0.5.2 records that no
    ``-std=`` and no arithmetic directive appears anywhere), and NO code path in
    this bridge or handler slices a byte beyond position 10 - the only key of
    reference spans bytes 1..10. The magnitude digits are therefore emitted and
    the overpunch is not modelled; it is an entry for
    ``docs/migration/ambiguity-resolutions.md`` if a future key of reference ever
    reaches those bytes.

    Args:
        posting: The record to render.

    Returns:
        The 103-character image [see :data:`WS_POSTING_RECORD_BYTES`].
    """
    pieces: list[str] = []
    for dictionary_key, attribute_path in _RECORD_IMAGE_LAYOUT:
        field_view = loader.get_entry(dictionary_key).copybook
        value: object = posting
        for attribute in attribute_path:
            value = getattr(value, attribute)
        if field_view.character_length is not None:
            width = int(field_view.character_length)
            pieces.append(str(value)[:width].ljust(width))
            continue
        digits = int(field_view.digits or 0)
        scale = int(field_view.scale or 0)
        units = abs(int(_as_exact_decimal(value, where=field_view.name).scaleb(scale)))
        pieces.append(f"{units % (10**digits):0{digits}d}")
    return "".join(pieces)


def _key_of_reference_value(posting: WsPostingRecord) -> str:
    """``WS-Posting-Record (K:L)`` - the value every keyed statement compares.

    ANOMALY N-KOR, reproduced here and nowhere else so that all five keyed
    statements inherit it from one place. The key table declares offset 0001 and
    length 0010 [common/glpostingMT.scb:L233], and ``WS-Post-rrn pic 9(5)`` was
    added at the FRONT of the record on 06/01/17 [copybooks/wspost.cob:L9, :L13],
    so those ten bytes are ``WS-Post-rrn`` followed by ``Batch`` - NOT
    ``WS-Post-Key``, which now occupies bytes 6..15. The predicate is still
    LABELLED ``POST-KEY`` [common/glpostingMT.scb:L232], and the bridge's own
    commented-out ``*> Post-Key`` beside two of the five sites
    [common/glpostingMT.cbl:L607, :L842] shows the maintainer weighing exactly
    this. His warning sits two lines above the key table: "WARNING POST-KEY MAY
    WELL NEED CHANGING TO POST-RRN & RDB made to index fld."
    [common/glpostingMT.scb:L229].

    Nothing is corrected. The slice is taken as declared.

    Args:
        posting: The record the caller passed.

    Returns:
        The ten-character key text, leading zeros intact.
    """
    return KEY_OF_REFERENCE.key_from_record(_ws_posting_record_image(posting))


def _where_equal_to(posting: WsPostingRecord) -> tuple[str, tuple[object, ...]]:
    """``\\`POST-KEY\\`="<key>"`` - the equality predicate, four sites share it.

    Reproduces the identical ``string`` block at read-indexed
    [common/glpostingMT.cbl:L602-L611], delete [:L837-L846] and rewrite
    [:L977-L985]. ``KeyName (KOR-x1) delimited by space`` drops the key name's
    trailing spaces, giving ``POST-KEY``.

    The frozen source quotes the value even though the column is a ``bigint``
    [:L605, :L608]; MySQL coerces the quoted digits, and a bound parameter
    carrying the same ten-character text coerces identically, so the predicate is
    observationally the same while the injection route the frozen source left
    open is closed. That is the decision
    :mod:`acas_posting.dal.cursor_state` already documents for the positioning
    statements, followed here for consistency.

    Returns:
        The predicate text with one placeholder, and the parameters to bind.
    """
    return (
        f"{quote_identifier(KEY_OF_REFERENCE.name)}=%s",
        (_key_of_reference_value(posting),),
    )


def _where_less_than(posting: WsPostingRecord) -> tuple[str, tuple[object, ...]]:
    """``\\`POST-KEY\\`<"<key>"`` - the ``Delete-All`` predicate.

    Reproduces [common/glpostingMT.cbl:L915-L923], the ONE site that uses ``<``
    rather than ``=``: ``'<"'`` at :L918 where the other four write ``'="'``.
    """
    return (
        f"{quote_identifier(KEY_OF_REFERENCE.name)}<%s",
        (_key_of_reference_value(posting),),
    )


# ---------------------------------------------------------------------------
# `bb200-Insert` and `bb300-Update` - the statements this module owns
# ---------------------------------------------------------------------------

#: `STRING ";" ... STRING X"00"` [common/glpostingMT.cbl:L1283-L1286] terminate
#: the command for the C interface: the semicolon ends the SQL text and the NUL
#: byte ends the C string. Both are transport rather than logical content - the
#: driver takes a Python ``str`` and needs neither - so neither is emitted, and
#: the omission is recorded here rather than left implicit. The same pair appears
#: on the SELECT [:L627], the DELETE [:L944] and the UPDATE [:L1478].
STATEMENT_TERMINATORS_ARE_TRANSPORT_ONLY: Final[bool] = True


def _column_assignments() -> tuple[str, ...]:
    """``\\`<column>\\`=%s`` for all fourteen columns, in ordinal order.

    The bridge emits ``'`POST-RRN`="'`` then the rendered value then ``'"'`` then
    ``', '`` [common/glpostingMT.cbl:L1120-L1130], repeating for each column in
    the frozen table's declared order [mysql/ACASDB.sql:L155-L168].
    ``POST-RRN`` is FIRST [:L1120],
    which is why anomaly N-RRN reaches the column at all.

    Derived from :data:`COLUMNS`, so the list is fixed data and the generated
    statement is byte-identical across processes (R-6).
    """
    return tuple(f"{column.quoted_name}=%s" for column in COLUMNS)


def _bound_values(host_variables: TdGlpostingRec) -> tuple[object, ...]:
    """The fourteen bound values, in the same ordinal order.

    Every column is supplied, ``POST-RRN`` included, because all fourteen are
    ``NOT NULL`` [mysql/ACASDB.sql:L155-L168] and ``initialize
    TD-GLPOSTING-REC`` [common/glpostingMT.cbl:L1053] guarantees a zero or a
    space rather than a ``NULL``. AAP section 0.6.2: "the Python layer must
    default rather than omit." Nothing here can be ``None``.
    """
    return tuple(
        column.bind(host_variables.value_for(column)) for column in COLUMNS
    )


def _literal_command(prefix: str, host_variables: TdGlpostingRec) -> str:
    """The statement text the bridge would build, for the log only.

    Reproduced so that the rendered values - and with them anomaly N-EDIT - are
    visible in the diagnostic record, matching ``move WS-Where (1:J) to
    WS-Log-Where.  *> For test logging`` [common/glpostingMT.cbl:L612, :L848,
    :L929, :L986]. It is never executed: :func:`bb200_insert` and
    :func:`bb300_update` issue the bound form.
    """
    assignments = ", ".join(
        f'{column.quoted_name}="{column.render(host_variables.value_for(column))}"'
        for column in COLUMNS
    )
    return f"{prefix}{assignments}"


def bb200_insert(
    connection: object, host_variables: TdGlpostingRec
) -> int:
    """``bb200-Insert Section.`` [common/glpostingMT.cbl:L1105].

    Reproduces the ``/MYSQL INSERT\\`` block [common/glpostingMT.cbl:L1108-L1289]:
    ``INSERT INTO `GLPOSTING-REC` SET `` [:L1115-L1118] followed by all fourteen
    columns in the frozen table's ordinal order, each as
    ``\\`<column>\\`="<value>"``
    separated by ``', '`` [:L1120-L1282], then ``";"`` and ``X"00"``
    [:L1283-L1286], then ``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``
    [:L1287].

    ``POST-RRN`` is the FIRST assignment [:L1120-L1130] and carries whatever
    ``initialize TD-GLPOSTING-REC`` left - zero - because ``bb000-HV-Load`` never
    loads it. That is ANOMALY N-RRN reaching the database: the table's primary key
    is written as zero on every insert. It is not derived, not auto-incremented
    and not defaulted to anything else.

    ``MYSQL-1210-COMMAND`` ends with ``call "MySQL_affected_rows" using
    WS-Mysql-Count-Rows`` [copybooks/mysql-procedures.cpy:L178], which is the
    count the caller tests, so the affected-row count is returned.

    Args:
        connection: The open connection from :func:`ba020_process_open`.
        host_variables: The group :func:`bb000_hv_load` populated.

    Returns:
        ``WS-MYSQL-COUNT-ROWS`` - the number of rows the statement affected.
    """
    statement = (
        f"INSERT INTO {quote_identifier(TABLE_NAME)} SET "
        f"{', '.join(_column_assignments())}"
    )
    _LOG.debug(
        "bb200-Insert [common/glpostingMT.cbl:L1105]: %s",
        sanitise_for_log(
            _literal_command(
                f"INSERT INTO {quote_identifier(TABLE_NAME)} SET ", host_variables
            )
        ),
    )
    parameters = _bound_values(host_variables)
    with execute_statement(connection, statement, parameters) as cursor:
        return int(cursor.rowcount)


def bb300_update(
    connection: object,
    host_variables: TdGlpostingRec,
    where_clause: str,
    where_parameters: Sequence[object],
) -> int:
    """``bb300-Update Section.`` [common/glpostingMT.cbl:L1294].

    Reproduces the ``/MYSQL UPDATE\\`` block [common/glpostingMT.cbl:L1297-L1482]:
    ``UPDATE `GLPOSTING-REC` SET `` followed by THE SAME fourteen columns in the
    same ordinal order - ``POST-RRN`` among them [:L1309-L1319] - then
    ``" WHERE "`` [:L1472-L1474], then ``FUNCTION TRIM (WS-Where (1:J))``
    [:L1475-L1477], then ``";" X"00"`` [:L1478], then ``PERFORM
    MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`` [:L1480].

    Because ``POST-RRN`` is in the ``SET`` list and ``bb000-HV-Load`` never loads
    it, A REWRITE ALSO STAMPS THE PRIMARY KEY BACK TO ZERO. ANOMALY N-RRN is
    therefore not confined to inserts; it reaches every rewritten row too. Not
    corrected.

    Args:
        connection: The open connection from :func:`ba020_process_open`.
        host_variables: The group :func:`bb000_hv_load` populated.
        where_clause: The predicate text, identifiers already quoted.
        where_parameters: The predicate's bound values.

    Returns:
        ``WS-MYSQL-COUNT-ROWS`` - the number of rows the statement affected.
    """
    statement = (
        f"UPDATE {quote_identifier(TABLE_NAME)} SET "
        f"{', '.join(_column_assignments())} WHERE {where_clause}"
    )
    _LOG.debug(
        "bb300-Update [common/glpostingMT.cbl:L1294]: %s WHERE %s",
        sanitise_for_log(
            _literal_command(
                f"UPDATE {quote_identifier(TABLE_NAME)} SET ", host_variables
            )
        ),
        sanitise_for_log(where_clause),
    )
    parameters = (*_bound_values(host_variables), *where_parameters)
    with execute_statement(connection, statement, parameters) as cursor:
        return int(cursor.rowcount)



# ---------------------------------------------------------------------------
# Bridge working storage - `Ws-Mysql-Cid` and `01 DAL-Data`
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _BridgeLink:
    """The bridge's own connection handle, the ``Ws-Mysql-Cid`` analogue.

    ``MYSQL-1000-OPEN`` stores the connection identifier in working storage
    [copybooks/mysql-procedures.cpy:L63-L86] and every later statement uses it;
    ``MYSQL-1980-CLOSE`` [:L264-L265] releases it. A compiled COBOL module keeps
    that identifier for the life of the run unless the caller ``CANCEL``s the
    program, so the Python counterpart is module-level state with an explicit
    reset - see :func:`cancel_glposting_mt`.

    Rule R-3 forbids concurrency, so ONE slot is correct and no lock is needed:
    "Execution is strictly sequential, matching the single-threaded COBOL."
    """

    #: The open connection, or ``None`` before ``Open`` and after ``Close``.
    connection: object | None = None
    #: `ws-env-lines` / `ws-lines` [common/glpostingMT.cbl:L335-L340]. Screen
    #: geometry, kept because the paragraph that computes it is in scope; it has
    #: no database effect and nothing below reads it for a decision.
    ws_lines: int = 24


#: The bridge's `01 DAL-Data.` [common/glpostingMT.scb:L247-L251]. Every bridge
#: holds its own copy in working storage, so this module owns its own cursor
#: table rather than sharing the one :mod:`acas_posting.dal.cursor_state` keeps
#: for callers that pass none. The cursor contract itself - "The cursor must be
#: closed and reopened whenever the relation or the key value changes, otherwise
#: READ NEXT continues from the old position" [common/glpostingMT.scb:L243-L245]
#: - is implemented there and consumed here.
_BRIDGE_CURSORS: Final[CursorStateTable] = CursorStateTable()

#: `Ws-Mysql-Cid` [copybooks/mysql-procedures.cpy]. One slot, no pool (R-3).
_LINK: Final[_BridgeLink] = _BridgeLink()

#: `accept ws-env-lines from lines.` with the floor of 24
#: [common/glpostingMT.cbl:L335-L340]. The terminal is not consulted: the
#: migrated artifact is headless (AAP section 0.3.4), so the floor is the value.
MINIMUM_SCREEN_LINES: Final[int] = 24


def cancel_glposting_mt() -> None:
    """Discard the bridge's working storage - the COBOL ``CANCEL`` equivalent.

    A COBOL ``CALL`` leaves the called program's working storage intact between
    calls; ``CANCEL "glpostingMT"`` is what resets it. Rule R-6 requires two runs
    of one scenario to be byte-identical, which they cannot be if a connection or
    a cursor survives from the first into the second, so the reset is part of the
    published surface rather than an implementation detail.

    Closes nothing: :func:`ba030_process_close` is the close path, and calling it
    from here would issue a statement the COBOL does not issue at ``CANCEL``.
    """
    _LINK.connection = None
    _LINK.ws_lines = MINIMUM_SCREEN_LINES
    _BRIDGE_CURSORS.reset(TABLE_NAME)


def _states(states: CursorStateTable | None) -> CursorStateTable:
    """The cursor table to use: the caller's when given, the bridge's otherwise."""
    return states if states is not None else _BRIDGE_CURSORS


def _write_file_key(file_access: FileAccess, text: str) -> None:
    """``move <literal> to WS-File-Key`` - truncated to the declared width.

    ``WS-File-Key pic x(64)`` [copybooks/wsfnctn.cob:L52], and a COBOL ``MOVE``
    into a shorter alphanumeric receiving field truncates on the right. The
    truncation is reproduced; the space padding is not, because
    :meth:`acas_posting.dal.cursor_state.CursorOutcome.apply_to` writes the same
    field unpadded and one field must not carry two shapes.
    """
    file_access.logging_data.ws_file_key = text[:WS_FILE_KEY_WIDTH]


def _driver_error_status(
    error: BaseException, *, command: str, we_error: int = WeError.SUCCESS
) -> DbErrorStatus:
    """Turn a driver exception into the status ``Mysql-1100-Db-Error`` produces.

    The three ``call "MySQL_errno"`` / ``"MySQL_sqlstate"`` / ``"MySQL_error"``
    sequences the bridge writes after a failed command
    [common/glpostingMT.cbl:L811-L817, :L867-L873, :L994-L1000] read the fields
    this helper extracts, and :func:`acas_posting.dal.status.mysql_1100_db_error`
    owns the mapping from them to a status pair - including the driver-level
    duplicate-key short circuit [copybooks/mysql-procedures.cpy:L99-L105], which
    is anomaly N-DUPKEY-TWO-PLACES.

    The per-verb narrowing to 995 and 994 is NOT applied here. That is the second
    stage, and it belongs to the calling paragraph
    [common/glpostingMT.cbl:L874-L875, :L1001-L1002] through
    :func:`acas_posting.dal.status.override_we_error_for_operation`, because the
    generic paragraph cannot know which verb invoked it. Collapsing the two stages
    would hide the fact that a verb WITHOUT an override silently keeps 911.

    ANOMALY N-LOCK-LADDER-DEAD applies at exactly this point. ``Mysql-1210-Command``
    reaches the generic paragraph directly [copybooks/mysql-procedures.cpy:L176]
    because the four-rung lock-retry ladder that used to stand between them is
    commented out [:L167-L175], along with the ``if WE-Error = 910`` test that would
    have read its result [:L168-L170] - so a locked table arrives here and leaves as
    the same ``(99, 911)`` as a missing table, and ``WeError.TABLE_LOCKED`` is
    unreachable through this bridge. Nothing is retried, and no backoff is
    introduced: :mod:`acas_posting.dal.status` carries the ladder as dead data for
    the same reason the COBOL carries it as dead comment.

    The driver's exception TYPE is deliberately not imported: ``dal/connection.py``
    owns the driver dependency, and every field needed here is reachable by
    attribute. That is also why the call sites catch ``Exception`` - the bridge's
    own behaviour is that any failure of the command takes this path.

    Args:
        error: The exception the driver raised.
        command: The statement's leading verb, which the duplicate-key short
            circuit tests [copybooks/mysql-procedures.cpy:L100-L103].
        we_error: The value ``We-Error`` already holds. Returned unchanged on the
            duplicate path, where the COBOL jump skips the ``move 911``
            [copybooks/mysql-procedures.cpy:L104].

    Returns:
        The status the COBOL would have reported.
    """
    return mysql_1100_db_error(
        errno=str(getattr(error, "errno", "") or ""),
        message=str(error),
        sql_state=str(getattr(error, "sqlstate", "") or ""),
        command=command,
        we_error=we_error,
    )


def _apply_db_error_status(file_access: FileAccess, status: DbErrorStatus) -> None:
    """Write a :class:`DbErrorStatus` into the caller's ``File-Access`` block."""
    file_access.fs_reply = int(status.fs_reply)
    file_access.we_error = int(status.we_error)
    status.apply_to_logging_data(file_access.logging_data)


def _require_connection() -> object:
    """The open connection, or a named failure.

    Raises:
        BridgeNotOpenError: If no ``Open`` has succeeded. See the class docstring
            for why this replaces the COBOL's undefined behaviour rather than
            inventing a status code the frozen source does not write.
    """
    if _LINK.connection is None:
        raise BridgeNotOpenError(
            f"{BRIDGE_NAME}: no connection; File-Function 1 (fn-Open) must "
            f"succeed before any other verb [common/glpostingMT.cbl:L419]",
            operation="any verb before fn-Open",
            table=TABLE_NAME,
        )
    return _LINK.connection


def _positioning_cursor(connection: object) -> object:
    """A cursor for :mod:`acas_posting.dal.cursor_state` to issue its statement on.

    The positioning verbs are the one case where this module does NOT own the
    statement: ``cursor_state`` builds and executes it, so it needs the cursor
    itself rather than the statement-plus-cursor that
    :func:`acas_posting.dal.connection.execute_statement` yields. One cursor per
    call, closed by the caller's ``finally`` - the same one-statement-per-cursor
    discipline ``execute_statement`` documents, and no prefetch or reuse.

    A CONNECTION ANOTHER BRIDGE HAS CLOSED DOES NOT RAISE HERE. Anomaly A-8
    means any bridge's ``Mysql-1980-Close`` closes the one process handle
    [presql2-package/cobmysqlapi38.c:L230-L234], and the frozen bridge reports
    that from its statement [copybooks/mysql-procedures.cpy:L165-L166], having no
    acquisition step of its own to fail at. ``acquire_cursor`` therefore carries
    the failure to the ``execute`` that ``cursor_state`` issues, where this
    module's existing failure arm maps it.
    """
    return acquire_cursor(connection)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# `bb100`'s input side - `CALL "MySQL_fetch_record"`
# ---------------------------------------------------------------------------


def _mysql_fetch_record(
    row: Mapping[str, object], host_variables: TdGlpostingRec
) -> None:
    """``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT <14 HVs>``.

    The same fourteen host variables appear in both fetch lists - read-next
    [common/glpostingMT.cbl:L537-L554] and read-indexed [:L644-L661] - in COLUMN
    ordinal order, and ``HV-POST-RRN`` IS among them [:L538, :L645]. So the
    primary key is READ into the host-variable group even though
    ``bb000-HV-Load`` never writes it and ``bb100-UnloadHVs`` never moves it back
    into the record. That asymmetry is anomaly N-RRN seen from the read side, and
    it is why the value visible here never reaches the caller.

    Each column's value passes through the receiving host variable's own ``MOVE``
    semantics, so a value wider than the host variable declares truncates exactly
    as the C interface's store would.

    Args:
        row: One row of the stored result, keyed by column name.
        host_variables: The group to populate. MUTATED IN PLACE, as the COBOL
            ``CALL`` populates the group by reference.
    """
    for column in COLUMNS:
        if column.name not in row:
            # A column absent from the result is left at whatever the group
            # already held, which is what a `CALL` with a short result list would
            # leave. No validation is added (R-3); the SELECT is `SELECT *`
            # [common/glpostingMT.cbl:L483-L484, :L623-L624] so this cannot
            # happen for a statement this module issued.
            continue
        host_variables.set_for(column, column.store(row[column.name]))


# ---------------------------------------------------------------------------
# Bridge `glpostingMT` - the paragraphs, in source order
# ---------------------------------------------------------------------------


def ba_acas_dal_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba-ACAS-DAL-Process  section.`` [common/glpostingMT.cbl:L334].

    The bridge's entry section. Reproduces [common/glpostingMT.cbl:L335-L343]:
    ``accept ws-env-lines from lines`` with a floor of 24, then two
    ``set ENVIRONMENT`` statements that force ``Esc``, ``PgUp``, ``PgDown`` and
    ``PrtSc`` to be detected by the curses screen handler. The screen handler is
    out of scope (AAP section 0.3.4 removes the presentation layer), so the two
    ``set ENVIRONMENT`` statements have no counterpart and are recorded as a
    representation-only omission; the line count is kept because the paragraph
    computes it and it costs nothing to be faithful.

    Falls through in source order into :func:`ba010_initialise`, which is where
    the function dispatch lives.
    """
    # `accept ws-env-lines from lines.` [common/glpostingMT.cbl:L335] with the
    # `if ws-env-lines < 24 move 24 ...` floor [:L336-L340]. Headless, so the
    # floor is the value.
    _LINK.ws_lines = MINIMUM_SCREEN_LINES
    # [:L342-L343] `set ENVIRONMENT "COB_SCREEN_EXCEPTIONS"/"COB_SCREEN_ESC"` -
    # curses key handling for a screen section this migration does not have.
    # Deliberate omission, recorded in the module docstring.

    # Paragraph fall-through, in source order [:L344 -> :L345].
    ba010_initialise(
        file_access,
        dal_common,
        posting,
        system_record=system_record,
        transport=transport,
        states=states,
    )


def ba010_initialise(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba010-Initialise.`` [common/glpostingMT.cbl:L345].

    Clears the diagnostic fields [common/glpostingMT.cbl:L350-L356] and then
    dispatches on ``File-Function`` [:L363-L387].

    ANOMALY N-NOSTATUS. The two lines that would clear the STATUS fields are
    commented out in the frozen source [common/glpostingMT.cbl:L347-L348]::

         *>    move     zero   to We-Error
         *>                       Fs-Reply.

    So a path that writes no status leaves the caller's INCOMING ``FS-Reply`` and
    ``We-Error`` in place. That is reachable: a delete matching no row with a
    driver error number beginning ``0`` falls through [:L866-L877] having written
    neither, and so does the delete-all [:L947-L958]. The same family as anomaly
    A7 in :mod:`acas_posting.dal.cursor_state`, where the START path leaves both
    fields untouched. Not corrected: the commented-out lines stay commented out.

    The dispatch order is ``1, 2, 3, 4, 5, 6, 7, 8, 9`` [:L363-L387] - note that
    the BRIDGE has a ``when 6`` for ``fn-Delete-All`` [:L377-L378] under the
    comment "option 6 is a special to cleardown all data", while the HANDLER has
    none [common/acas006.cbl:L344-L363]. That is not a contradiction: ``6`` is set
    internally by ``ba015-Test-Ends`` [common/acas006.cbl:L643] and passed
    straight to the bridge, so it never traverses the handler's dispatch. Also
    note that re-write (7) is dispatched before delete (8) in BOTH programs.

    Every arm is a ``go to`` [:L365 and siblings], which is AAP section 0.4.2
    Class 4 - sibling re-dispatch - rendered as a named call followed by an
    explicit ``return``. ``when other`` [:L385-L386] is exhaustive, so unlike the
    handler the bridge has no unconditional fall-through line after the
    ``evaluate``.
    """
    # `move spaces to WS-MYSQL-Error-Message WS-MYSQL-Error-Number WS-Log-Where
    #  WS-File-Key SQL-Msg SQL-Err SQL-State.` [common/glpostingMT.cbl:L350-L356]
    logging_data = file_access.logging_data
    logging_data.ws_log_where = ""
    logging_data.ws_file_key = ""
    logging_data.sql_msg = ""
    logging_data.sql_err = ""
    logging_data.sql_state = ""
    # ANOMALY N-NOSTATUS: `move zero to We-Error Fs-Reply` is commented out at
    # [common/glpostingMT.cbl:L347-L348]. The incoming values are left alone.

    function_code = int(file_access.file_function)

    # `evaluate File-Function` [common/glpostingMT.cbl:L363-L387]. Every arm is a
    # Class 4 `go to`: a named call, then `return`.
    if function_code == FileFunction.OPEN:  # when 1  [:L364-L365]
        ba020_process_open(
            file_access,
            dal_common,
            system_record=system_record,
            transport=transport,
            states=states,
        )
        return
    if function_code == FileFunction.CLOSE:  # when 2  [:L366-L367]
        ba030_process_close(file_access, dal_common, states=states)
        return
    if function_code == FileFunction.READ_NEXT:  # when 3  [:L368-L369]
        ba040_process_read_next(file_access, dal_common, posting, states=states)
        return
    if function_code == FileFunction.READ_INDEXED:  # when 4  [:L370-L371]
        ba050_process_read_indexed(file_access, dal_common, posting, states=states)
        return
    if function_code == FileFunction.WRITE:  # when 5  [:L372-L373]
        ba070_process_write(file_access, dal_common, posting)
        return
    if function_code == FileFunction.DELETE_ALL:  # when 6  [:L377-L378]
        # "option 6 is a special to cleardown all data" [:L375]. Reached only
        # through the handler's ba015-Test-Ends [common/acas006.cbl:L643], never
        # through the handler's own dispatch.
        ba085_process_delete_all(file_access, dal_common, posting)
        return
    if function_code == FileFunction.RE_WRITE:  # when 7  [:L379-L380]
        ba090_process_rewrite(file_access, dal_common, posting)
        return
    if function_code == FileFunction.DELETE:  # when 8  [:L381-L382]
        ba080_process_delete(file_access, dal_common, posting)
        return
    if function_code == FileFunction.START:  # when 9  [:L383-L384]
        ba060_process_start(file_access, dal_common, posting, states=states)
        return
    # when other  [:L385-L386]
    ba100_bad_function(file_access, dal_common)


def ba020_process_open(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba020-Process-Open.`` [common/glpostingMT.cbl:L389].

    Six ``string ... X"00"`` statements marshal the credentials from the
    ``RDB-Data`` block into the C interface's NUL-terminated buffers -
    ``DB-Schema`` to ``WS-MYSQL-BASE-NAME`` [:L394-L397], ``DB-Host`` to
    ``WS-MYSQL-HOST-NAME`` [:L398-L401], ``DB-UName`` to
    ``WS-MYSQL-IMPLEMENTATION`` [:L402-L405], ``DB-UPass`` to
    ``WS-MYSQL-PASSWORD`` [:L406-L409], ``DB-Port`` to ``WS-MYSQL-PORT-NUMBER``
    [:L410-L413] and ``DB-Socket`` to ``WS-MYSQL-SOCKET`` [:L414-L417] - and then
    ``move 1 to ws-No-Paragraph`` [:L418] and ``PERFORM MYSQL-1000-OPEN THRU
    MYSQL-1090-EXIT`` [:L419].

    All of that is owned by :mod:`acas_posting.dal.connection`:
    :func:`~acas_posting.dal.connection.mysql_1000_open` performs the three
    connect steps [copybooks/mysql-procedures.cpy:L63-L86] and pins the numeric
    converter so that no column can arrive as binary floating point (R-2). It is
    CALLED,
    not duplicated. The commented-out ``/MYSQL INIT\\`` block [:L423-L427] carries
    the maintainer's own development credentials as a directive comment; they are
    not reproduced - they are frozen placeholder credentials and
    ``connection.py`` refuses them by default.

    On failure ``go to ba999-end`` [:L420-L421] - AAP section 0.4.2 Class 3. On
    success ``move "OPEN GLPOSTING" to WS-File-Key`` [:L429] and ``move zero to
    Most-Cursor-Set`` [:L430], the statement that guarantees the first
    ``Read-Next`` after an open self-positions.

    Args:
        file_access: The caller's linkage block. Mutated in place.
        dal_common: The testing switches [copybooks/Test-Data-Flags.cob].
        system_record: The record the credentials come from. Required, because
            the COBOL smuggles them through ``RDB-Data`` after
            ``ba012-Test-WS-Rec-Size-2`` copied them there
            [common/acas006.cbl:L627-L632]; passing the record down instead
            lets ``connection.py`` own the load.
        transport: The caller's transport policy. ``None`` means the fail-closed
            default, which admits only loopback or a Unix socket.
        states: The cursor table, for the ``Most-Cursor-Set`` reset.

    Raises:
        ValueError: If ``system_record`` is absent. There is no credential source
            without it, and inventing one would be a fabrication.
    """
    if system_record is None:
        raise ValueError(
            f"{BRIDGE_NAME} ba020-Process-Open: the system record supplies the "
            f"RDBMS credentials [common/acas006.cbl:L627-L632]; none was passed"
        )
    # [:L394-L417] the six credential buffers, and [:L418-L419] the open itself.
    # `mysql_1000_open` marshals and connects; `mysql_1090_exit` is the THRU
    # target that normalises the outcome.
    outcome: OpenOutcome = mysql_1090_exit(
        mysql_1000_open(
            system_record,
            ws_no_paragraph=BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"],
            transport=transport,
        )
    )
    outcome.apply_to_logging_data(file_access.logging_data)
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    if not outcome.opened or int(outcome.fs_reply) != FsReply.SUCCESS:
        # `if fs-reply not = zero go to ba999-end.` [:L420-L421] - Class 3.
        ba999_end(file_access, dal_common)
        return
    _LINK.connection = outcome.connection
    # `move "OPEN GLPOSTING" to WS-File-Key` [:L429]
    _write_file_key(file_access, WS_FILE_KEY_LITERALS["bridge-open"])
    # `move zero to Most-Cursor-Set` [:L430]
    _states(states).state_for(TABLE_NAME, CursorSlot.PRIMARY).set_cursor_not_active()
    # `go to ba999-end.` [:L431] - Class 3.
    ba999_end(file_access, dal_common)


def ba030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    states: CursorStateTable | None = None,
) -> None:
    """``ba030-Process-Close.`` [common/glpostingMT.cbl:L433].

    ``if Cursor-Active perform ba998-Free.`` [:L434-L435], then ``move 2 to
    ws-No-Paragraph`` [:L437], ``move "CLOSE GLPOSTING" to WS-File-Key`` [:L438],
    ``PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT`` [:L443] and ``go to
    ba999-end`` [:L446] - Class 3.

    Note the order: the paragraph number is set AFTER the conditional free, so a
    close that frees a live cursor logs 20 from ``ba998-Free`` [:L1024] and then
    20 is replaced by 2. Reproduced as written.
    """
    cursor_state_for_table = _states(states).state_for(TABLE_NAME, CursorSlot.PRIMARY)
    if cursor_state_for_table.cursor_active():
        # `perform ba998-Free.` [:L435]
        ba998_free(file_access, states=states)
    # `move 2 to ws-No-Paragraph.` [:L437]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba030-Process-Close"
    ]
    # `move "CLOSE GLPOSTING" to WS-File-Key.` [:L438]
    _write_file_key(file_access, WS_FILE_KEY_LITERALS["bridge-close"])
    # `PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT` [:L443]
    mysql_1980_close(_LINK.connection)
    mysql_1999_exit()
    _LINK.connection = None
    # `go to ba999-end.` [:L446] - Class 3.
    ba999_end(file_access, dal_common)


def ba040_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    states: CursorStateTable | None = None,
) -> None:
    """``ba040-Process-Read-Next.`` [common/glpostingMT.cbl:L448].

    When the cursor is not active the paragraph self-positions: it builds
    ``\\`POST-KEY\\` >= "0000000000" ORDER BY \\`POST-KEY\\` ASC``
    [:L459-L473] - note the maintainer's ``*> nom uses >  ??`` beside the ``>=``
    [:L464] - issues ``SELECT * FROM \\`GLPOSTING-REC\\` WHERE ...``
    [:L482-L488], stores the whole result [:L489] and tags the log ``"00000"``
    [:L492]. An empty table gives ``FS-Reply 10`` and ``WE-Error 10`` with the tag
    ``"No Data"`` [:L499-L512]; otherwise the cursor goes active and the tag
    becomes ``"> 0 got cnt=<n> recs"`` [:L513-L519]. Then ``end-if.`` [:L521] and
    the paragraph FALLS THROUGH in source order into ``ba041-Reread`` [:L523],
    which fetches one record.

    All of that positioning behaviour - the statement text, the ``>=`` relation,
    the low key, the unconditional ``ASC``, the store-the-whole-result semantics,
    the end-of-file protocol AND the driver-failure path that
    ``Mysql-1210-Command`` routes through ``Mysql-1100-Db-Error``
    [copybooks/mysql-procedures.cpy:L165-L177] - is owned by
    :func:`acas_posting.dal.cursor_state.read_next`, which reproduces it paragraph
    by paragraph and writes the status into ``File-Access`` itself. It is called,
    not duplicated; it reports a driver failure through its return value exactly
    as the COBOL reports one through ``FS-Reply``, so there is nothing to catch.
    What remains here is the bridge's own work: the host-variable fetch and the
    unload, in :func:`ba041_reread`.
    """
    connection = _require_connection()
    cursor = _positioning_cursor(connection)
    try:
        outcome = read_next(
            cursor,
            TABLE_NAME,
            slot=CursorSlot.PRIMARY,
            states=_states(states),
            file_access=file_access,
        )
    finally:
        cursor.close()

    # Paragraph fall-through [:L521 -> :L523] into ba041-Reread.
    ba041_reread(file_access, dal_common, posting, outcome_row=outcome.row)


def ba041_reread(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    outcome_row: Mapping[str, object] | None,
) -> None:
    """``ba041-Reread.`` [common/glpostingMT.cbl:L523].

    ``move spaces to WS-Log-Where.`` [:L527], ``move 4 to ws-No-Paragraph.``
    [:L528], ``move zero to return-code.`` [:L529], then ``CALL
    "MySQL_fetch_record"`` with the fourteen host variables [:L536-L554].

    ``if return-code = -1`` [:L556] is end of snapshot: ``move 10 to fs-Reply
    WE-Error`` [:L557] - one statement writing BOTH fields, which is why end of
    file sets ``WE-Error`` to 10 as well as ``FS-Reply`` - the tag becomes
    ``"EOF"`` [:L558], the cursor goes inactive [:L559] and control transfers to
    ``ba999-End`` [:L560], Class 3. Two further guarded branches tag ``"EOF2"``
    [:L574] and ``"EOF3"`` [:L582].

    On success: ``perform bb100-UnloadHVs`` [:L585] then ``move HV-POST-KEY to
    WS-File-Key.`` [:L587] and ``move zero to fs-reply WE-Error.`` [:L588].

    :func:`acas_posting.dal.cursor_state.read_next` has already reproduced the
    snapshot walk and written the status, so this paragraph does the part that
    belongs to the bridge: the host-variable fetch and the unload.

    Args:
        outcome_row: The record the snapshot walk returned, or ``None`` for the
            ``return-code = -1`` end of snapshot.
    """
    # `move spaces to WS-Log-Where.` is written by `read_next` through
    # `CursorOutcome.apply_to`, which sets the field to the statement text
    # [common/glpostingMT.cbl:L475]. `move 4 to ws-No-Paragraph.` [:L528]:
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba041-Reread"
    ]
    if outcome_row is None:
        # `if return-code = -1` [:L556-L560] - the status, the "EOF" tag and the
        # inactive cursor are all written by `read_next`. Class 3 transfer to
        # ba999-End.
        ba999_end(file_access, dal_common)
        return
    # `CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT <14 HVs>` [:L536-L554]
    host_variables = TdGlpostingRec()
    _mysql_fetch_record(outcome_row, host_variables)
    # `perform bb100-UnloadHVs` [:L585]
    bb100_unload_hvs(host_variables, posting)
    # `move HV-POST-KEY to WS-File-Key.` [:L587]
    _write_file_key(
        file_access, COLUMNS_BY_NAME["POST-KEY"].render(host_variables.hv_post_key)
    )
    # `move zero to fs-reply WE-Error.` [:L588] - already written by `read_next`,
    # which reports success as (0, 0). `go to ba999-end.` [:L589] - Class 3.
    ba999_end(file_access, dal_common)


def ba050_process_read_indexed(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    states: CursorStateTable | None = None,
) -> None:
    """``ba050-Process-Read-Indexed.`` [common/glpostingMT.cbl:L591].

    Builds ``\\`POST-KEY\\`="<WS-Posting-Record (1:10)>"`` [:L602-L611] - the
    ANOMALY N-KOR slice, with the maintainer's commented-out ``*> Post-Key``
    beside it [:L607] - issues the ``SELECT`` [:L622-L628] and stores the result
    [:L629]. Then TWO guards on the same count, and only the first can fire::

        L633      if     WS-MYSQL-Count-Rows = zero
        L634             move 21  to fs-Reply       *> could also be 23 or 14
        L635             go to ba998-Free
        L636      end-if
        ...
        L663      if       WS-MYSQL-Count-Rows not > zero

    ANOMALY N-DEAD-READ-INDEXED-ERRNO. ``Ws-Mysql-Count-Rows`` is declared
    ``binary-double unsigned`` [copybooks/mysql-variables.cpy:L73] - and ANOMALY
    N-COUNTROWS-NEG-DEAD is that the signed redefinition which would make the
    second guard live, ``01 WS-Mysql-Count-Rows-Neg redefines WS-Mysql-Count-Rows
    binary-double signed.`` [copybooks/mysql-variables.cpy:L74-L75], is referenced
    NOWHERE in the frozen tree. Between the two guards nothing can change it:
    it is written only by ``MySQL_affected_rows`` and ``MySQL_num_rows``
    [copybooks/mysql-procedures.cpy:L178, :L191-L192], and the fetch call does NOT
    pass it [common/glpostingMT.cbl:L643-L658]. For an unsigned count "not greater
    than zero" IS "equal to zero", which the first guard has already jumped away
    from - so the whole block [:L663-L683] IS DEAD CODE, carrying the maintainer's
    own trailing doubt ``*> row count zero should show up as a MYSQL error ?``
    [:L683].

    That deepens ANOMALY N2 rather than merely restating it. ``FS-Reply 23`` is
    documented in the authoritative table [:L129] and never returned; the two
    sites the maintainer converted FROM 23 - ``move 21 to fs-reply  *> from 23``
    at [:L668] with ``WE-Error 990`` [:L669], and again at [:L676] with ``WE-Error
    989`` [:L677] - cannot execute at all. So the ONLY reachable 21 from this
    paragraph is [:L634], which writes ``FS-Reply`` and NO ``We-Error``, leaving
    the caller's incoming value in place: ANOMALY N-NOSTATUS again, and the reason
    a broken statement here surfaces the mismatched pair ``(21, 911)``.

    EVERY path leaves through ``ba998-Free`` [:L635, :L674, :L681, :L689], so a
    read-indexed always frees the cursor - which is why a read-indexed cannot be
    followed by a read-next that resumes from it.

    The statement, both guards, the dead-code reproduction and the whole status
    protocol - including the driver-failure path - are owned by
    :func:`acas_posting.dal.cursor_state.read_indexed`, where they are recorded as
    its anomalies A2, A13 and A14. It is called, not duplicated, and it reports a
    driver failure through its return value, so there is nothing to catch. The
    host-variable fetch and the unload are the bridge's own and are done here.
    """
    connection = _require_connection()
    cursor = _positioning_cursor(connection)
    key_number = int(file_access.logging_data.file_key_no) or 1
    try:
        outcome = read_indexed(
            cursor,
            TABLE_NAME,
            _key_of_reference_value(posting),
            key_number=key_number,
            slot=CursorSlot.PRIMARY,
            states=_states(states),
            file_access=file_access,
        )
    finally:
        cursor.close()

    if outcome.row is not None:
        # `CALL "MySQL_fetch_record"` [:L644-L661]
        file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
            "ba050-Process-Read-Indexed-Fetch"
        ]
        host_variables = TdGlpostingRec()
        _mysql_fetch_record(outcome.row, host_variables)
        # `perform bb100-UnloadHVs` [:L684]
        bb100_unload_hvs(host_variables, posting)
        # `move HV-POST-KEY to ws-temp-ed.  move ws-temp-ed to WS-File-Key.`
        # [:L685-L686] - the two-step move through the edited field, which is why
        # the tag carries the key's digits rather than its packed value.
        _write_file_key(
            file_access,
            COLUMNS_BY_NAME["POST-KEY"].render(host_variables.hv_post_key),
        )
    # `go to ba998-Free.` [:L689] - and [:L635] on the no-row path. Class 4:
    # ba998-Free does work and then control reaches ba999-end. The free itself is
    # idempotent here: `cursor_state.read_indexed` reproduces the same
    # `go to ba998-Free` internally, and what this call adds is the paragraph
    # number 20 that [:L1024] writes and that the log record then carries.
    ba998_free(file_access, states=states)
    ba999_end(file_access, dal_common)


def ba060_process_start(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    states: CursorStateTable | None = None,
) -> None:
    """``ba060-Process-Start.`` [common/glpostingMT.cbl:L691].

    ``if access-type < 5 or > 8`` [:L695] - the maintainer's own note reads "not
    using not < or not >" - yields ``FS-Reply 99`` [:L696] and ``WE-Error 997``
    [:L697], where the HANDLER's equivalent guard uses ``WE-Error 998`` for the
    same condition [common/acas006.cbl:L488]. That is part of ANOMALY N-998.

    ANOMALY N-relation: the guard rejects ``Access-Type 9``
    (``fn-not-greater-than``) even though the ``evaluate`` immediately below has
    an arm for it [:L715-L726] and ``wsfnctn.cob`` declares it
    [copybooks/wsfnctn.cob:L116]; the arm carries the maintainer's own "[ not
    currently used in ACAS ]". Nine relations implemented, eight accepted, five
    documented [:L248].

    ANOMALY A6, owned and documented by
    :mod:`acas_posting.dal.cursor_state`: ``' ASC  '`` is emitted for all five
    relations [:L740] with no descending branch, so a ``<`` or ``<=`` START
    positions at the LOWEST qualifying key rather than the highest.

    The relation arrives through ``Access-Type`` UNMODIFIED, because the facade
    clears that field for every verb except ``-Start``
    [copybooks/Proc-ACAS-FH-Calls.cob:L456-L463]. It is passed through untouched;
    ``cursor_state`` owns the mapping.

    The commented-out ``go to ba041-Reread`` [:L795-L800] under "Changed to do
    start then read next / As per irsub4 operations" records that a START used to
    fetch and now does not: it positions only, and the caller must follow with a
    read-next. :attr:`acas_posting.dal.cursor_state.CursorOutcome.row` is
    therefore always ``None`` on this path, and the caller that wants the record
    performs a read-next - which is what the in-scope programs do.

    :func:`acas_posting.dal.cursor_state.start` owns the guard, the relation
    mapping, the statement and the status protocol, including the path where the
    frozen source writes NO status at all (its anomaly A7, the same family as
    N-NOSTATUS here) and the driver-failure path. It is called, not duplicated.
    """
    connection = _require_connection()
    cursor = _positioning_cursor(connection)
    try:
        start(
            cursor,
            TABLE_NAME,
            _key_of_reference_value(posting),
            # `Access-Type` is passed through UNMODIFIED: the facade clears it for
            # every verb except `-Start`, so for a START it carries the relation
            # [copybooks/Proc-ACAS-FH-Calls.cob:L456-L463]. Mapping it here would
            # duplicate `START_RELATION_BY_ACCESS_TYPE`.
            int(file_access.access_type),
            key_number=int(file_access.logging_data.file_key_no) or 1,
            slot=CursorSlot.PRIMARY,
            states=_states(states),
            file_access=file_access,
        )
    finally:
        cursor.close()
    # `go to ba999-end.` [:L793] - Class 3. START returns no row: the row is the
    # following read-next's business.
    ba999_end(file_access, dal_common)


def ba070_process_write(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
) -> None:
    """``ba070-Process-Write.`` [common/glpostingMT.cbl:L802].

    Transcribed from [common/glpostingMT.cbl:L803-L827]::

        L803      perform  bb000-HV-Load.
        L804      move     ws-Post-Key to WS-File-Key.
        L805      move     zero to FS-Reply WE-Error SQL-State.
        L806      move     spaces to SQL-Msg
        L807      move     zero to SQL-Err
        L808      move     10 to ws-No-Paragraph.
        L809      perform  bb200-Insert.

    Then ``if WS-MYSQL-COUNT-ROWS not = 1`` [:L810] enters the errno branch, whose
    inner test is the BRIDGE-LEVEL duplicate-key rule [:L818-L824]::

        if    SQL-Err (1:4) = "1062"
                         or = "1022"   *> Dup key (rec already present)
            or Sql-State = "23000"     *> Dup key (rec already present)
              move 22 to fs-reply
        else
              move 99 to fs-reply

    ANOMALY N-DUPKEY-TWO-PLACES: the same condition is ALSO tested at driver
    level, where ``Mysql-1100-Db-Error`` short-circuits on errno 1062 or 1022
    **and** a command beginning ``INSERT``, setting ``FS-Reply 22`` and returning
    before ``SQL-Msg`` or ``SQL-State`` is filled
    [copybooks/mysql-procedures.cpy:L99-L105]. Both are reproduced;
    :mod:`acas_posting.dal.status` owns both predicates.

    Note the tag at [:L804]: ``move ws-Post-Key to WS-File-Key`` uses the record's
    OWN ten-digit post key, while the ``WHERE`` predicates elsewhere use the
    ANOMALY N-KOR slice. The two differ whenever ``WS-Post-rrn`` is non-zero, and
    both are reproduced as written.

    ANOMALY N-RRN reaches the table here: ``bb200-Insert`` names ``POST-RRN``
    first [:L1120-L1130] and ``bb000-HV-Load`` never loaded it, so the primary key
    is written as zero.
    """
    # L803  perform bb000-HV-Load.
    host_variables = bb000_hv_load(posting)
    # L804  move ws-Post-Key to WS-File-Key.  - the record's key, NOT the N-KOR
    # slice the WHERE clauses use.
    _write_file_key(file_access, _post_key_tag(posting))
    # L805-L807  move zero to FS-Reply WE-Error SQL-State / spaces to SQL-Msg /
    # zero to SQL-Err
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    file_access.logging_data.sql_state = ""
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_err = ""
    # L808  move 10 to ws-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba070-Process-Write"
    ]
    try:
        # L809  perform bb200-Insert.
        affected = bb200_insert(_require_connection(), host_variables)
    except Exception as error:  # any driver error takes this path - see below
        # [:L810-L826] the count test and its errno branch. The duplicate-key
        # rule of [:L818-L824] is applied by `is_duplicate_key_bridge_level`, and
        # the driver-level short circuit by `mysql_1100_db_error`.
        status = _driver_error_status(error, command="INSERT")
        status.apply_to_logging_data(file_access.logging_data)
        if status.duplicate_key or is_duplicate_key_bridge_level(
            status.sql_err, status.sql_state
        ):
            file_access.fs_reply = int(FsReply.DUPLICATE_KEY)  # [:L821]
        else:
            file_access.fs_reply = int(FsReply.ERROR)  # [:L823]
        file_access.we_error = int(status.we_error)
        # `go to ba999-End.` [:L827] - Class 3.
        ba999_end(file_access, dal_common)
        return
    if affected != 1:
        # The count test [:L810] with no driver error to report: the inner `if
        # WS-MYSQL-Error-Number (1:1) not = "0"` [:L814] is false, so NOTHING is
        # written - ANOMALY N-NOSTATUS. The values set at [:L805] stand, which
        # here means success is reported for a row that was not inserted.
        _LOG.warning(
            "ba070-Process-Write [common/glpostingMT.cbl:L810]: "
            "WS-MYSQL-COUNT-ROWS = %d, not 1, with no driver error to report; "
            "the frozen source writes no status on this path",
            affected,
        )
    # `go to ba999-End.` [:L827] - Class 3.
    ba999_end(file_access, dal_common)


def _post_key_tag(posting: WsPostingRecord) -> str:
    """``move ws-Post-Key to WS-File-Key`` [common/glpostingMT.cbl:L804, :L969].

    The record's own ten-digit post key, ``Batch`` then ``Post-Number``. Distinct
    from :func:`_key_of_reference_value`, which is the ANOMALY N-KOR slice the
    ``WHERE`` clauses compare. Two sites use this one - write and rewrite - and
    five use the slice.
    """
    return f"{int(_join_post_key(posting.ws_post_key)):010d}"


def ba080_process_delete(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
) -> None:
    """``ba080-Process-Delete.`` [common/glpostingMT.cbl:L829].

    Builds ``\\`POST-KEY\\`="<WS-Posting-Record (1:10)>"`` [:L837-L846] - the
    ANOMALY N-KOR slice again, with the same commented-out ``*> Post-Key``
    [:L842] - tags the log with the slice [:L847], sets paragraph 13 [:L852] and
    issues ``DELETE FROM \\`GLPOSTING-REC\\` WHERE ...`` [:L858-L864].

    ``if WS-MYSQL-COUNT-ROWS not = 1`` [:L866] enters the errno branch, which on a
    real driver error writes ``FS-Reply 99`` [:L874] and ``WE-Error 995``
    [:L875] - the code the authoritative table glosses "During Delete SQLSTATE not
    '00000'" - and then transfers to ``ba999-End`` [:L877]. On the ``else``
    [:L878-L880] only ``SQL-Msg`` and ``SQL-Err`` are cleared, and success is
    reported at [:L882].

    ANOMALY N-NOSTATUS is reachable here: a delete matching NO row whose driver
    error number begins ``0`` skips the inner ``if`` [:L870] entirely and
    transfers at [:L877] having written neither status field, so the caller's
    INCOMING ``FS-Reply`` and ``We-Error`` survive - ``ba010-Initialise`` having
    had its clearing statement commented out [:L347-L348].

    ANOMALY N-DELETE-TERMINATOR: this statement is terminated with ``X"00"``
    alone [:L863], where the SELECT [:L487], the INSERT [:L1283-L1285] and the
    UPDATE [:L1478] all write ``";" X"00"``. Both terminators are transport, so
    the difference has no effect and is recorded rather than reproduced.
    """
    where_clause, where_parameters = _where_equal_to(posting)
    # `move WS-Posting-Record (K:L) to WS-File-Key.` [:L847] - the N-KOR slice.
    _write_file_key(file_access, _key_of_reference_value(posting))
    # `move WS-Where (1:J) to WS-Log-Where.` [:L848]
    file_access.logging_data.ws_log_where = where_clause
    # `move 13 to ws-No-Paragraph.` [:L852]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba080-Process-Delete"
    ]
    statement = (
        f"DELETE FROM {quote_identifier(TABLE_NAME)} WHERE {where_clause}"
    )
    try:
        with execute_statement(
            _require_connection(), statement, where_parameters
        ) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:  # any driver error takes this path - see below
        # [:L867-L876] with `move 99 to fs-reply` [:L874] and `move 995 to
        # WE-Error` [:L875].
        # TWO STAGES, as the frozen source has them: the generic paragraph
        # reports (99, 911) [copybooks/mysql-procedures.cpy:L127-L128] and the
        # verb then narrows We-Error to 995 [:L874-L875]. Pre-setting 995 here
        # would collapse the distinction and would also surface 995 on the
        # duplicate-key path, which the COBOL never does.
        status = override_we_error_for_operation(
            _driver_error_status(error, command="DELETE"), FileFunction.DELETE
        )
        _apply_db_error_status(file_access, status)
        # `go to ba999-End` [:L877] - Class 3.
        ba999_end(file_access, dal_common)
        return
    if affected != 1:
        # ANOMALY N-NOSTATUS [:L866-L877]: the count is wrong but there is no
        # driver error, so the inner `if` [:L870] is false and NEITHER status
        # field is written. The caller's incoming values survive.
        _LOG.warning(
            "ba080-Process-Delete [common/glpostingMT.cbl:L866]: "
            "WS-MYSQL-COUNT-ROWS = %d, not 1, with no driver error; the frozen "
            "source writes no status on this path and ba010-Initialise's "
            "clearing statement is commented out [:L347-L348]",
            affected,
        )
        ba999_end(file_access, dal_common)
        return
    # `else move spaces to SQL-Msg / move zero to SQL-Err` [:L878-L880]
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_err = ""
    # `move zero to FS-Reply WE-Error.` [:L882]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `go to ba999-End.` [:L883] - Class 3.
    ba999_end(file_access, dal_common)


def ba085_process_delete_all(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
) -> None:
    """``ba085-Process-Delete-ALL.`` [common/glpostingMT.cbl:L885].

    The maintainer labels the whole paragraph "THIS IS NON STANDARD". ANOMALY
    N-DELETE-ALL: it is NOT a truncate. It moves ``9999999999`` into
    ``ws-Post-Key`` [:L907] under the comment "as its the last posting", builds
    ``\\`POST-KEY\\`<"<WS-Posting-Record (1:10)>"`` [:L915-L923] - the ONE site
    that writes ``'<"'`` [:L918] rather than ``'="'`` - tags the log "Deleting
    back from <key>" [:L924-L928], sets paragraph 15 [:L933] and issues ``DELETE
    FROM \\`GLPOSTING-REC\\` WHERE ...`` [:L939-L945].

    TWO consequences follow, and both are reproduced:

    * The ``move`` at [:L907] writes ``ws-Post-Key``, but the predicate slices
      ``WS-Posting-Record (1:10)``, which because of ANOMALY N-KOR is
      ``WS-Post-rrn`` followed by ``Batch`` - so the literal in the predicate is
      the record's rrn followed by ``99999``, NOT ``9999999999``. The rows deleted
      are therefore those whose key of reference sorts below that, which is not
      "all rows" unless the rrn happens to be at its maximum.
    * The success test is ``if WS-MYSQL-COUNT-ROWS not > zero`` [:L947] with the
      maintainer's own "Changed for delete-ALL", so an ALREADY-EMPTY table takes
      the failure branch and reports ``FS-Reply 99`` / ``WE-Error 995``
      [:L955-L956] if the driver has an error number to give - and ANOMALY
      N-NOSTATUS if it has not [:L951, :L958].

    ANOMALY N-DELETE-TERMINATOR, second site: this statement too is terminated
    with ``X"00"`` alone [:L944], where the ``SELECT``, ``INSERT`` and ``UPDATE``
    all write ``";" X"00"``. Transport only, so recorded rather than reproduced -
    see :data:`STATEMENT_TERMINATORS_ARE_TRANSPORT_ONLY`.

    ANOMALY N-NOSTATUS, third bridge site: the zero-row path [:L951, :L958] writes
    neither status field, and ``ba010-Initialise``'s clearing statement is
    commented out [:L347-L348], so the caller reads back what it passed in.

    This paragraph is reachable only through the handler's ``ba015-Test-Ends``
    [common/acas006.cbl:L640-L644], never through the handler's own dispatch,
    which has no ``when 6``.
    """
    # `move 9999999999 to ws-Post-Key.` [:L907] - "as its the last posting". The
    # record is mutated, exactly as the COBOL mutates the caller's record, and
    # that mutation is visible to the caller after the call returns.
    posting.ws_post_key.batch = 99999
    posting.ws_post_key.post_number = 99999
    where_clause, where_parameters = _where_less_than(posting)
    # `move spaces to WS-File-Key` then the string [:L924-L928].
    _write_file_key(
        file_access,
        f"{WS_FILE_KEY_LITERALS['bridge-delete-all']}{_post_key_tag(posting)}",
    )
    # `move WS-Where (1:J) to WS-Log-Where.` [:L929]
    file_access.logging_data.ws_log_where = where_clause
    # `move 15 to ws-No-Paragraph.` [:L933]
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba085-Process-Delete-ALL"
    ]
    statement = f"DELETE FROM {quote_identifier(TABLE_NAME)} WHERE {where_clause}"
    try:
        with execute_statement(
            _require_connection(), statement, where_parameters
        ) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:  # any driver error takes this path - see below
        # [:L948-L957] with `move 99 to fs-reply` [:L955] and `move 995 to
        # WE-Error` [:L956] - the SAME 995 the single-row delete uses, not a
        # code of its own.
        # The same two stages, and the same 995: this paragraph writes the code
        # the single-row delete writes [:L956 against :L875], not one of its own.
        status = override_we_error_for_operation(
            _driver_error_status(error, command="DELETE"), FileFunction.DELETE
        )
        _apply_db_error_status(file_access, status)
        # `go to ba999-End` [:L958] - Class 3.
        ba999_end(file_access, dal_common)
        return
    if affected <= 0:
        # ANOMALY N-DELETE-ALL's own half: `not > zero` [:L947] means an empty
        # table is a failure. With no driver error the inner `if` [:L951] is
        # false, so nothing is written - ANOMALY N-NOSTATUS again - and control
        # transfers at [:L958].
        _LOG.warning(
            "ba085-Process-Delete-ALL [common/glpostingMT.cbl:L947]: "
            "WS-MYSQL-COUNT-ROWS = %d, not > zero, with no driver error; an "
            "already-empty table takes this path and the frozen source writes "
            "no status on it",
            affected,
        )
        ba999_end(file_access, dal_common)
        return
    # `else move spaces to SQL-Msg / move zero to SQL-Err` [:L959-L961]
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_err = ""
    # `move zero to FS-Reply WE-Error.` [:L963]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `go to ba999-End.` [:L964] - Class 3.
    ba999_end(file_access, dal_common)


def ba090_process_rewrite(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
) -> None:
    """``ba090-Process-Rewrite.`` [common/glpostingMT.cbl:L966].

    ``perform bb000-HV-Load.`` [:L968], ``move ws-Post-Key to WS-File-Key.``
    [:L969], ``move 17 to ws-No-Paragraph.`` [:L970], the key-of-reference
    ``WHERE`` [:L977-L985], ``move WS-Where (1:J) to WS-Log-Where.`` [:L986] and
    ``perform bb300-Update.`` [:L987].

    ``if WS-MYSQL-COUNT-ROWS not = 1`` [:L993] gives ``FS-Reply 99`` [:L1001] and
    ``WE-Error 994`` [:L1002] - the maintainer's own note beside the 99 reads
    "this may need changing for val in WE-Error!!" - then transfers to
    ``ba999-End`` [:L1004]. Success clears the four fields [:L1006-L1008] and
    transfers at [:L1009].

    ANOMALY N-RRN reaches the table on this path too, and that is easy to miss:
    ``bb300-Update`` puts ``POST-RRN`` in its ``SET`` list [:L1309-L1319] and
    ``bb000-HV-Load`` never loaded it, so EVERY REWRITE STAMPS THE PRIMARY KEY
    BACK TO ZERO. Not corrected.

    ANOMALY N-NOSTATUS is reachable here as well: a rewrite matching no row with
    no driver error to report skips [:L997] and transfers at [:L1004] having
    written neither status field.
    """
    # L968  perform bb000-HV-Load.
    host_variables = bb000_hv_load(posting)
    # L969  move ws-Post-Key to WS-File-Key.
    _write_file_key(file_access, _post_key_tag(posting))
    # L970  move 17 to ws-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba090-Process-Rewrite"
    ]
    # L977-L985  the WHERE, on the N-KOR slice.
    where_clause, where_parameters = _where_equal_to(posting)
    # L986  move WS-Where (1:J) to WS-Log-Where.
    file_access.logging_data.ws_log_where = where_clause
    try:
        # L987  perform bb300-Update.
        affected = bb300_update(
            _require_connection(), host_variables, where_clause, where_parameters
        )
    except Exception as error:  # any driver error takes this path - see below
        # [:L994-L1003] with `move 99 to fs-reply` [:L1001] and `move 994 to
        # WE-Error` [:L1002].
        # Two stages again: (99, 911) generically, narrowed to 994 by the verb
        # [:L1001-L1002].
        status = override_we_error_for_operation(
            _driver_error_status(error, command="UPDATE"), FileFunction.RE_WRITE
        )
        _apply_db_error_status(file_access, status)
        # `go to ba999-End` [:L1004] - Class 3.
        ba999_end(file_access, dal_common)
        return
    if affected != 1:
        # ANOMALY N-NOSTATUS [:L993-L1005].
        _LOG.warning(
            "ba090-Process-Rewrite [common/glpostingMT.cbl:L993]: "
            "WS-MYSQL-COUNT-ROWS = %d, not 1, with no driver error; the frozen "
            "source writes no status on this path",
            affected,
        )
        ba999_end(file_access, dal_common)
        return
    # `move zero to FS-Reply WE-Error / zero to SQL-Err / spaces to SQL-Msg`
    # [:L1006-L1008]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    file_access.logging_data.sql_err = ""
    file_access.logging_data.sql_msg = ""
    # `go to ba999-End.` [:L1009] - Class 3.
    ba999_end(file_access, dal_common)


def ba100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``ba100-Bad-Function.`` [common/glpostingMT.cbl:L1011].

    Under the maintainer's "Houston; We have a problem" [:L1013]: ``move 990 to
    WE-Error.`` [:L1015] and ``move 99 to Fs-Reply.`` [:L1016], then ``go to
    ba999-end.`` [:L1017] - Class 3.

    ANOMALY N-BRIDGE-BAD-FN: the HANDLER's ``aa100-Bad-Function`` reports
    ``WE-Error 999`` for the same condition [common/acas006.cbl:L561], so one call
    chain carries two different "bad function" codes depending on which program
    detected it. The authoritative table has a THIRD code for the idea, 992
    "Invalid Function requested" [common/glpostingMT.cbl:L146], which neither
    program writes. Not harmonised.
    """
    # L1015  move 990 to WE-Error.
    file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
    # L1016  move 99 to Fs-Reply.
    file_access.fs_reply = int(FsReply.ERROR)
    # L1017  go to ba999-end.  - Class 3.
    ba999_end(file_access, dal_common)


def ba998_free(
    file_access: FileAccess, *, states: CursorStateTable | None = None
) -> None:
    """``ba998-Free.`` [common/glpostingMT.cbl:L1023].

    ``move 20 to ws-No-Paragraph.`` [:L1024], ``CALL "MySQL_free_result" USING
    WS-MYSQL-RESULT`` [:L1030-L1031] and ``set Cursor-Not-Active to true.``
    [:L1033]. This is the ONLY paragraph that frees the stored result; the
    end-of-file sites merely set the flag and leave the snapshot allocated, a leak
    that :mod:`acas_posting.dal.cursor_state` documents and reproduces.

    Falls through in source order into :func:`ba999_end` at the call sites, which
    is why each caller invokes both.
    """
    # L1024  move 20 to ws-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba998-Free"]
    # L1030-L1033  free the result and set the cursor inactive.
    _states(states).state_for(TABLE_NAME, CursorSlot.PRIMARY).free()


def ba999_end(file_access: FileAccess, dal_common: AcasDalCommonData) -> None:
    """``ba999-end.`` [common/glpostingMT.cbl:L1035].

    ``if Testing-1 perform Ca-Process-Logs end-if.`` [:L1038-L1040].
    ``Testing-1`` is ``SW-Testing value 1`` [copybooks/Test-Data-Flags.cob:L10-L11]
    and its declared default is ONE, so logging is on unless a caller turns it
    off - the maintainer's own note says "When testing comlete you can set
    SW-Testing to zero to stop the logging file being produced" [:L3-L4].

    Falls through into :func:`ba999_exit`, ``exit program.`` [:L1042-L1043].
    """
    if int(dal_common.sw_testing) == 1:
        mt_ca_process_logs(file_access, dal_common)
    ba999_exit()


def ba999_exit() -> None:
    """``ba999-exit.  exit program.`` [common/glpostingMT.cbl:L1042-L1043].

    Returns control to the handler. Nothing to do: the Python call returns, and
    the caller's ``File-Access`` block already carries every field the COBOL
    would have left in it.
    """
    return


def mt_ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs.`` of the BRIDGE [common/glpostingMT.cbl:L1487].

    ``call "fhlogger" using File-Access ACAS-DAL-Common-data.`` [:L1489-L1490].

    ``common/fhlogger.cbl`` is explicitly out of scope (AAP section 0.2.2 lists it
    among the non-posting utilities) and rule R-1 forbids calling it, so the
    external log file it writes is not reproduced. It carries no database effect
    and appears in no table dump, which is why AAP section 0.3.4 classes such
    output as a log record rather than behaviour. A structured record with the
    same fields is emitted instead, and ``Log-File-Rec-Written``
    [copybooks/Test-Data-Flags.cob:L18] is left alone because ``fhlogger`` owns
    it and ``fhlogger`` is out of scope.

    Every field is passed through
    :func:`acas_posting.dal.status.sanitise_for_log`, because ``SQL-Msg`` is
    built by the server out of material that can include account names, host names
    and data values.
    """
    logging_data = file_access.logging_data
    _LOG.info(
        "fhlogger %s sys=%d file=%d para=%d fs=%d we=%d key=%s state=%s "
        "err=%s msg=%s where=%s testing=%d/%d",
        BRIDGE_NAME,
        int(logging_data.ws_log_system),
        int(logging_data.ws_log_file_no),
        int(logging_data.ws_no_paragraph),
        int(file_access.fs_reply),
        int(file_access.we_error),
        sanitise_for_log(str(logging_data.ws_file_key)),
        sanitise_for_log(str(logging_data.sql_state)),
        sanitise_for_log(str(logging_data.sql_err)),
        sanitise_for_log(str(logging_data.sql_msg)),
        sanitise_for_log(str(logging_data.ws_log_where)),
        int(dal_common.sw_testing),
        int(dal_common.sw_testing_2),
    )
    mt_ca_exit()


def mt_ca_exit() -> None:
    """``ca-Exit.  exit.`` of the BRIDGE [common/glpostingMT.cbl:L1493]."""
    return


def glposting_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``glpostingMT`` - the bridge, entered at its ``PROCEDURE DIVISION``.

    The bridge's linkage takes THREE parameters with ``File-Access`` FIRST
    [common/glpostingMT.cbl:L330-L332], and the handler calls it in exactly that
    order [common/acas006.cbl:L653-L658]::

        L653   ba020-Process-DAL.
        L654       call     "glpostingMT" using File-Access
        L655                                    ACAS-DAL-Common-data
        L657                                    WS-Posting-Record
        L658       end-call.

    This is the handler-named half of the dual vocabulary R-5 requires: a reader
    following the bridge's own calling convention finds a function of this name
    and this signature, while a reader following the facade's finds
    :func:`dispatch`. One implementation, two published entry points.

    ALL SQL for ``GLPOSTING-REC`` is owned here and below - the host-variable
    group [common/glpostingMT.cbl:L280-L296], the load and unload paragraphs, the
    ``INSERT``, the ``UPDATE``, the two ``DELETE``s - under the directive that
    declares the table [common/glpostingMT.scb:L273-L276], reproduced in
    :data:`MYSQL_VAR_DIRECTIVE`. The positioning statements are owned by
    :mod:`acas_posting.dal.cursor_state`, which reproduces the cursor contract
    [common/glpostingMT.scb:L243-L245].

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L22]. Carries the
            requested ``File-Function`` and ``Access-Type`` in and the status
            out. MUTATED IN PLACE.
        dal_common: ``ACAS-DAL-Common-data``
            [copybooks/Test-Data-Flags.cob:L6].
        posting: ``WS-Posting-Record`` [copybooks/wspost.cob:L12]. Read on a
            write, mutated on a read.
        system_record: Needed by ``fn-Open`` alone, to reach the credentials the
            COBOL had already copied into ``RDB-Data``.
        transport: The transport policy for the open; ``None`` is fail-closed.
        states: The cursor table; ``None`` uses the bridge's own, which is the
            faithful analogue of its ``01 DAL-Data`` working storage.
    """
    ba_acas_dal_process(
        file_access,
        dal_common,
        posting,
        system_record=system_record,
        transport=transport,
        states=states,
    )



# ===========================================================================
# HANDLER `acas006` - `common/acas006.cbl`
# ===========================================================================
#
# The handler is a SEPARATE COBOL PROGRAM from the bridge above, with its own
# working storage, its own paragraph numbering series (201..208 against the
# bridge's 1..20) and its own five-parameter linkage
# [common/acas006.cbl:L273-L279]. It is placed after the bridge in this file
# purely so that its call into :func:`glposting_mt` needs no forward reference;
# within each program the paragraphs appear in SOURCE order, which is what the
# traceability document maps. `77 prog-name pic x(20) value "acas006 (3.3.00)"`
# [common/acas006.cbl:L244].
#
# ---------------------------------------------------------------------------
# Handler working storage - `77 A`, `77 B`, `77 Cobol-File-Status`
# ---------------------------------------------------------------------------


#: `77  Display-Blk        pic x(75)             value spaces.`
#: [common/acas006.cbl:L250]. The receiving field of the record-length
#: diagnostic, and therefore the width that diagnostic truncates to.
DISPLAY_BLK_WIDTH: Final[int] = 75

#: `03  GL901          pic x(31) value "GL901 Note error and hit return".`
#: [common/acas006.cbl:L257]. Displayed at 2401 beside the record-length error
#: [:L614]; the "hit return" it asks for is the `accept` at [:L619], which Agent
#: Action Plan section 0.3.4 drops. Carried so the log record can name what the
#: operator would have seen.
GL901_MESSAGE: Final[str] = "GL901 Note error and hit return"

#: `03  GL903          pic x(32) value "GL903 Program Error: Temp rec = ".`
#: [common/acas006.cbl:L258], with the maintainer's own template for what follows
#: on the next comment line, `*>  yyy < Posting-Rec = zzz` [:L259] - written with
#: three digits although `A` and `B` are `pic 9(4)`, so the rendered text carries
#: four. Prefix of the ANOMALY N-901-DEAD diagnostic built at [:L607-L611].
GL903_MESSAGE: Final[str] = "GL903 Program Error: Temp rec = "


@dataclass(slots=True)
class _HandlerWorkingStorage:
    """The handler's own working storage, the three fields with run-long state.

    Transcribed from [common/acas006.cbl:L248-L252]::

        L248 77  A                 pic 9(4)  value zero.  *> A & B used in 1st test ONLY
        L249 77  B                 pic 9(4)  value zero.  *>  in ba-Process-RDBMS
        L250 77  Display-Blk       pic x(75) value spaces.
        L251 77  Cobol-File-Status pic 9     value zero.
        L252     88  Cobol-File-Eof          value 1.

    ``A`` and ``B`` are the record lengths, and the maintainer's own comment
    "A & B used in 1st test ONLY" is the whole point of them: ``if A = zero``
    [common/acas006.cbl:L594] makes the block that follows run once per program
    activation and never again. A COBOL ``CALL`` preserves working storage between
    calls, so these persist for the life of the run - see :func:`cancel_acas006`.

    ``Cobol-File-Status`` and its ``88`` belong to the flat-file path alone; every
    ISAM verb clears it and the sequential read sets it at end of file
    [:L439-L440]. It is modelled because the paragraphs that write it also write
    the status the caller sees, and skipping it would drop statements from those
    paragraphs.

    ``Display-Blk`` is not a field here: it holds a diagnostic for one display and
    is rebuilt from scratch each time [:L606-L612], so it is a local string in
    :func:`ba012_test_ws_rec_size_2` and its width is
    :data:`DISPLAY_BLK_WIDTH`. ``77 WS-Reply pic x value space.`` [:L246] is
    likewise absent, because nothing in the program ever reads or writes it -
    recorded as a deliberate omission rather than carried as an unused field.
    """

    #: `77 A pic 9(4) value zero.` [common/acas006.cbl:L248] - the WS record's
    #: length, measured once.
    a: int = 0
    #: `77 B pic 9(4) value zero.` [common/acas006.cbl:L249] - the FD record's.
    b: int = 0
    #: `77 Cobol-File-Status pic 9 value zero.` [common/acas006.cbl:L251].
    cobol_file_status: int = 0

    def cobol_file_eof(self) -> bool:
        """``88 Cobol-File-Eof value 1.`` [common/acas006.cbl:L252]."""
        return self.cobol_file_status == 1

    def set_cobol_file_eof(self) -> None:
        """``set Cobol-File-EoF to true`` [common/acas006.cbl:L439]."""
        self.cobol_file_status = 1


#: The handler's working storage. ONE instance, no lock: rule R-3 forbids
#: concurrency, so the single-threaded COBOL's single copy is the faithful model.
_HANDLER: Final[_HandlerWorkingStorage] = _HandlerWorkingStorage()


def cancel_acas006() -> None:
    """Discard the handler's working storage - the COBOL ``CANCEL`` equivalent.

    Resets ``A``, ``B`` and ``Cobol-File-Status`` to their ``VALUE`` clauses. Rule
    R-6 requires two runs of one scenario to be byte-identical, and a non-zero
    ``A`` carried from a previous run would skip the record-length test and the
    credential load on the next run's first call, so the reset is published rather
    than private. Does NOT cancel the bridge; :func:`cancel_glposting_mt` is
    separate because ``CANCEL`` names one program.
    """
    _HANDLER.a = 0
    _HANDLER.b = 0
    _HANDLER.cobol_file_status = 0


def _flat_file_store_unavailable(
    verb: str, locator: str
) -> CobolFlatFileStoreUnavailableError:
    """The failure raised where the COBOL would have issued an ISAM verb.

    ``Posting-File`` is an indexed file declared by ``copybooks/selpost.cob`` over
    ``copybooks/fdpost.cob``, and the migration's store is the frozen MySQL schema:
    Agent Action Plan section 0.2.1.1 lists twenty-two tables and no ISAM
    emulation, and the twenty ``dal/acas*.py`` modules "reimplement each
    handler-and-bridge pair as SQL against the frozen schema" (section 0.7.2 R-1).
    So this branch has no target, and saying so by name is the honest outcome - a
    silent success would fabricate a write, and a fabricated status would be a new
    behaviour that rule R-3 forbids.

    Unreachable in every migrated configuration: ``File-System-Used`` is 1 for
    RDBMS use [copybooks/wssystem.cob:L116], and the RDB branch
    [common/acas006.cbl:L322-L326] transfers to the exit before the flat-file
    dispatch [:L344] is reached.
    """
    return CobolFlatFileStoreUnavailableError(
        f"{HANDLER_NAME}: the COBOL flat-file store is not part of this "
        f"migration, so `{verb} Posting-File` [{locator}] has no target; the "
        f"in-scope store is `{TABLE_NAME}` reached through {BRIDGE_NAME}. Set "
        f"File-System-Used to 1 (FS-RDBMS-Used) "
        f"[copybooks/wssystem.cob:L116] so that the RDB branch "
        f"[common/acas006.cbl:L322-L326] is taken.",
        operation=verb,
        table=TABLE_NAME,
    )


# ---------------------------------------------------------------------------
# Handler `acas006` - `aa-Process-Flat-File`, in source order
# ---------------------------------------------------------------------------


def aa_process_flat_file(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas006.cbl:L282].

    A label only: the section header carries no statements, so control falls
    straight into :func:`aa010_main` at [:L284]. Kept as its own function because
    rule R-5 requires every paragraph AND section to map to one, and because the
    section is what ``exit section`` at [:L663] refers to.
    """
    aa010_main(
        system,
        posting,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def aa010_main(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``aa010-main.`` [common/acas006.cbl:L284] - the handler's whole mainline.

    Six things happen, in this order, and the order is the contract (rule R-6).

    **1. The log identity** [:L288-L289]::

        L288      move     2      to WS-Log-System.
        L289      move     12     to WS-Log-File-No.

    ANOMALY N-log: the 12 is overwritten with 22 the moment the RDB path is
    entered [:L590], so 12 is what the FLAT-FILE path logs and 22 is what the
    migrated path logs. Both values are published -
    :data:`WS_LOG_FILE_NO_COBOL_PATH` and :data:`WS_LOG_FILE_NO_RDB_PATH` - and
    the series is systematic across the family: ``acas005`` 11 to 21, ``acas006``
    12 to 22, ``acas007`` 13 to 23, ``acas008`` 15 to 25, with 14 skipped. Note
    also the capitalisation drift between ``WS-Log-File-No`` here and
    ``WS-Log-File-no`` at [:L590].

    **2. The key guard** [:L293-L307]. ``evaluate File-Function`` covering 4, 9 and
    8 ONLY - not write (5), not re-write (7). Read-indexed and start share one
    guard writing ``WE-Error 998`` [:L297]; delete has its own writing ``996``
    [:L303].

    ANOMALY N-guard: ``acas000`` guards a DIFFERENT set - 4, 5 and 7 - and tests a
    range rather than equality, ``if File-Key-No < 1 or > 5``
    [common/acas000.cbl:L330-L338], because it dispatches to four tables and
    therefore has four valid key numbers. Not harmonised: each handler's guard is
    the guard its own tables need.

    ANOMALY N-996-comment: the comment beside the 996 is a copy-paste of the one
    beside the 998 - both read "file seeks key type out of range" [:L297, :L303] -
    even though the authoritative table glosses 996 as a delete-specific code
    [common/glpostingMT.cbl:L138].

    **3. The Open-Output stage-1 branch** [:L313-L318]. See :func:`ba015_test_ends`
    for the second half of ANOMALY N18b. What matters here is what is ABSENT:
    there is no ``set fn-delete-all to true`` at this point, where
    ``common/acas008.cbl:L316`` does have one.

    **4. The RDB branch** [:L322-L326]::

        L322      if       not FS-Cobol-Files-Used
        L323               move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
        L324               perform ba-Process-RDBMS
        L325               go to AA-Main-Exit
        L326      end-if.

    This is the branch every migrated run takes, and it means the flat-file
    dispatch below is unreachable whenever the system record says RDBMS.

    **5. The status clear that is not there.** ANOMALY N-NOSTATUS, handler side
    [:L340-L342]::

         *>    move     zero   to  WE-Error
         *>  ?                      FS-Reply.
        L342      move     spaces to SQL-Err SQL-Msg SQL-State.

    The two status lines are commented out - carrying the maintainer's own ``?`` -
    so ONLY the three diagnostic fields are cleared and the caller's incoming
    ``FS-Reply`` and ``We-Error`` survive into the verb. The bridge has the same
    omission at [common/glpostingMT.cbl:L347-L348]. Both are reproduced.

    **6. The function dispatch** [:L344-L363] in the order 1, 2, 3, 4, 5, 7, 8, 9
    with re-write (7) BEFORE delete (8), then ``when other`` [:L361] annotated
    "6 is unused", and then the unconditional fall-through [:L366] under "Should
    never get here but in case :(".

    Args:
        system: ``System-Record`` - the first linkage parameter. Read for
            ``RDBMS-Flat-Statuses`` [:L323] and for the six credentials [:L627].
        posting: ``WS-Posting-Record`` - the second. Read on a write, mutated on
            a read.
        file_access: ``File-Access`` - the third. Mutated in place; this is how
            the status reaches the caller.
        file_defs: ``File-Defs`` - the fourth. Carries the file and work-file
            names [copybooks/wsnames.cob]; consulted by the flat-file store only,
            which is why nothing below reads it. Accepted so the signature matches
            the linkage exactly (rule R-5), and named in the log record so a
            reader can see it was received.
        dal_common: ``ACAS-DAL-Common-data`` - the fifth.
        transport: The transport policy handed to the open.
        states: The cursor table; ``None`` uses the bridge's own.
    """
    # 1. The log identity [:L288-L289].
    file_access.logging_data.ws_log_system = int(WS_LOG_SYSTEM)
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_COBOL_PATH

    # 2. The key guard [:L293-L307]. `evaluate File-Function` over 4, 9 and 8.
    function_code = int(file_access.file_function)
    key_number = int(file_access.logging_data.file_key_no)
    if function_code in (FileFunction.READ_INDEXED, FileFunction.START):
        # when 4 / when 9 share ONE `if` [:L294-L300].
        if key_number != 1:
            # `move 998 to WE-Error` [:L297] - ANOMALY N-998, meaning 2 of 3.
            file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)  # [:L298]
            # `go to aa999-main-exit` [:L299] - Class 3.
            aa999_main_exit(file_access, dal_common)
            return
    elif function_code == FileFunction.DELETE:
        # when 8 [:L301-L306], with the maintainer's "1 is only for RDB as Cobol
        # does it on primary key" [:L302].
        if key_number != 1:
            # `move 996 to WE-Error` [:L303] - and ANOMALY N-996-comment, the
            # copy-pasted gloss.
            file_access.we_error = int(WeError.DELETE_KEY_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)  # [:L304]
            # `go to aa999-main-exit` [:L305] - Class 3.
            aa999_main_exit(file_access, dal_common)
            return

    flat_statuses = system.system_data_block.rdbms_flat_statuses
    cobol_files_used = int(flat_statuses.file_system_used) == 0

    # 3. ANOMALY N18b, stage 1 [:L313-L318]. Note the ABSENCE of any
    # `set fn-delete-all to true` here, where common/acas008.cbl:L316 has one.
    if (
        function_code == FileFunction.OPEN
        and int(file_access.access_type) == AccessType.OUTPUT
        and not cobol_files_used
    ):
        # `perform ba-Process-RDBMS` [:L316] - which itself calls the bridge
        # TWICE, once here and once through the ba015 fall-through.
        ba_process_rdbms(
            system,
            posting,
            file_access,
            dal_common,
            transport=transport,
            states=states,
        )
        # `go to AA-Main-Exit` [:L317] - Class 3. NOTE: it bypasses
        # aa999-main-exit, so an Open-Output does NOT take the handler's own log
        # record; the bridge's ba999-end has already taken two.
        aa_main_exit()
        return

    # 4. The RDB branch [:L322-L326] - the path every migrated run takes.
    if not cobol_files_used:
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses` [:L323], with the
        # maintainer's "needed for DAL? not JC/dbpre versions".
        flat_statuses = system.system_data_block.rdbms_flat_statuses
        file_access.fa_rdbms_flat_statuses.fa_file_system_used = int(
            flat_statuses.file_system_used
        )
        file_access.fa_rdbms_flat_statuses.fa_file_duplicates_in_use = int(
            flat_statuses.file_duplicates_in_use
        )
        # `perform ba-Process-RDBMS` [:L324], "Can't hurt".
        ba_process_rdbms(
            system,
            posting,
            file_access,
            dal_common,
            transport=transport,
            states=states,
        )
        # `go to AA-Main-Exit` [:L325] - Class 3.
        aa_main_exit()
        return

    # 5. `perform ba012-Test-WS-Rec-Size-2.` [:L330] - the COBOL-files path runs
    # the record-length test WITHOUT the log-file-number overwrite of ba010, so a
    # flat-file run logs 12 and an RDB run logs 22. That is ANOMALY N-log's
    # mechanism.
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        # `go to ba-rdbms-exit` [:L620] left the section, so the flat-file
        # dispatch below is not reached.
        return

    # ANOMALY N-NOSTATUS, handler side: [:L340-L341] are COMMENTED OUT, so only
    # the three diagnostic fields are cleared here.
    #      *>    move     zero   to  WE-Error
    #      *>  ?                      FS-Reply.
    # `move spaces to SQL-Err SQL-Msg SQL-State.` [:L342]
    file_access.logging_data.sql_err = ""
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_state = ""

    # 6. The flat-file dispatch [:L344-L363].
    fired = _aa010_dispatch_flat_file(posting, file_access, dal_common)
    if not fired:
        # `go to aa100-Bad-Function.` [:L366], the maintainer's belt and braces:
        # "Should never get here but in case :(". Unreachable by construction -
        # every arm of the `evaluate`, `when other` included, is a `go to` - and
        # kept because the frozen source keeps it.
        aa100_bad_function(file_access, dal_common)


def _aa010_dispatch_flat_file(
    posting: WsPostingRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> bool:
    """``evaluate File-Function`` of ``aa010-main`` [common/acas006.cbl:L344-L363].

    Split out so that the unconditional ``go to aa100-Bad-Function.`` at [:L366]
    can be modelled as the guarded statement it is rather than as dead text. Every
    arm is a ``go to``, which is Agent Action Plan section 0.4.2 Class 4 - sibling
    re-dispatch - so each becomes a named call followed by ``return True``.

    The arm ORDER is preserved exactly: 1, 2, 3, 4, 5, **7, 8**, 9. Re-write comes
    before delete, and there is no ``when 6`` - the maintainer's own comment on the
    ``when other`` says so, "6 is unused" [:L361]. ``fn-Delete-All`` is set
    internally by :func:`ba015_test_ends` [:L643] and handed straight to the
    bridge, so it never traverses this dispatch; the bridge, which does receive it,
    has the ``when 6`` this program lacks
    [common/glpostingMT.cbl:L377-L378]. Functions 13, 15 and 31 through 34 are
    declared [copybooks/wsfnctn.cob:L99-L105] and reach ``when other`` here.

    Returns:
        ``True`` if any arm fired, which is always: ``when other`` is an arm too.
    """
    function_code = int(file_access.file_function)
    if function_code == FileFunction.OPEN:  # when 1  [:L345-L346]
        aa020_process_open(file_access, dal_common)
        return True
    if function_code == FileFunction.CLOSE:  # when 2  [:L347-L348]
        aa030_process_close(file_access, dal_common)
        return True
    if function_code == FileFunction.READ_NEXT:  # when 3  [:L349-L350]
        aa040_process_read_next(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.READ_INDEXED:  # when 4  [:L351-L352]
        aa050_process_read_indexed(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.WRITE:  # when 5  [:L353-L354]
        aa070_process_write(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.RE_WRITE:  # when 7  [:L355-L356]
        aa090_process_rewrite(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.DELETE:  # when 8  [:L357-L358]
        aa080_process_delete(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.START:  # when 9  [:L359-L360]
        aa060_process_start(posting, file_access, dal_common)
        return True
    # when other  [:L361-L362], "6 is unused".
    aa100_bad_function(file_access, dal_common)
    return True


def aa020_process_open(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa020-Process-Open.`` [common/acas006.cbl:L368].

    ``move spaces to WS-File-Key.`` [:L369] and ``move 201 to WS-No-Paragraph.``
    [:L370], then a four-deep nested ``if`` on ``Access-Type``:

    * ``fn-input`` [:L371-L377]: ``open input``, and on failure ``move 35 to
      fs-Reply`` - a RAW COBOL FILE STATUS, not one of the six ACAS ``FS-Reply``
      values [common/glpostingMT.cbl:L126-L131] - then ``close`` and exit.
    * ``fn-i-o`` [:L379-L386]: ``open i-o``, and on failure the create dance -
      close, ``open output`` ("Doesnt create in i-o"), close, ``open i-o`` again.
    * ``fn-output`` [:L388-L389]: ``open output``, with "caller should check
      fs-reply" and no test at all.
    * ``fn-extend`` [:L391-L396]: THE ONE BRANCH WITH NO FILE VERB. ``open extend``
      is commented out at [:L392] under "Must not be used for ISAM files", and the
      branch writes status only::

        L393               move 997 to WE-Error
        L394               move 99  to FS-Reply
        L395               go to aa999-main-exit

    Then [:L400-L404] ``move zero to Cobol-File-Status``, the log tag, and ``if
    fs-reply not = zero move 999 to we-error.`` - whose period ends the ``if``, so
    the ``go to aa999-main-exit.`` at [:L404] is unconditional.

    Only the extend branch is reachable without the flat-file store, so it is the
    one implemented in full; the other three do their non-file work and then fail
    by name at the verb. See :func:`_flat_file_store_unavailable`.

    Raises:
        CobolFlatFileStoreUnavailableError: For input, i-o and output, where the
            COBOL issues an ISAM ``open``.
    """
    # L369  move spaces to WS-File-Key.     *> for logging
    _write_file_key(file_access, "")
    # L370  move 201 to WS-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa020-Process-Open"
    ]
    access_type = int(file_access.access_type)
    if access_type == AccessType.EXTEND:
        # L391-L395. `open extend Posting-File` is COMMENTED OUT at [:L392].
        # `move 997 to WE-Error` [:L393]
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        # `move 99  to FS-Reply` [:L394]
        file_access.fs_reply = int(FsReply.ERROR)
        # `go to aa999-main-exit` [:L395] - Class 3. Reached BEFORE [:L400], so
        # neither the log tag nor the 999 override applies to an extend.
        aa999_main_exit(file_access, dal_common)
        return
    if access_type == AccessType.INPUT:
        raise _flat_file_store_unavailable("open input", "common/acas006.cbl:L372")
    if access_type == AccessType.I_O:
        raise _flat_file_store_unavailable("open i-o", "common/acas006.cbl:L380")
    if access_type == AccessType.OUTPUT:
        raise _flat_file_store_unavailable("open output", "common/acas006.cbl:L389")
    # No arm matched, which the COBOL's nested `if` also allows: an Access-Type of
    # 5 through 9 on an Open falls straight through the whole nest to [:L400] with
    # no file opened and no status written. Reproduced by falling through.
    # L400  move zero to Cobol-File-Status.
    _HANDLER.cobol_file_status = 0
    # L401  move "OPEN GL POSTING file" to WS-File-Key.
    _write_file_key(file_access, WS_FILE_KEY_LITERALS["handler-open"])
    # L402-L403  if fs-reply not = zero move 999 to we-error.
    if int(file_access.fs_reply) != FsReply.SUCCESS:
        file_access.we_error = int(WeError.NOT_USED)
    # L404  go to aa999-main-exit.   - unconditional; the period at [:L403] ended
    # the `if`. Class 3.
    aa999_main_exit(file_access, dal_common)


def aa030_process_close(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa030-Process-Close.`` [common/acas006.cbl:L406].

    Transcribed [:L407-L417]::

        L407      move     202 to WS-No-Paragraph.
        L408      move     spaces to WS-File-Key.     *> for logging
        L409      close    Posting-File.
        L410  *> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
        L411      move     zero to Cobol-File-Status.
        L412      move     "CLOSE GL POSTING file" to WS-File-Key.
        L413      perform  aa999-main-exit.
        L414      move     zero to  File-Function
        L415                        Access-Type.      *> close log file
        L416      perform  Ca-Process-Logs.
        L417      go       to aa-main-exit.

    Three things here are worth naming.

    ``[:L410]`` is a dated commented-out ``move zeros to FS-Reply WE-Error`` - a
    THIRD member of the ANOMALY N-NOSTATUS family, alongside [:L340-L341] here and
    [common/glpostingMT.cbl:L347-L348] in the bridge. The close therefore reports
    whatever the ``close`` verb left.

    ``[:L413]`` is a ``perform``, not a ``go to``: the exit paragraph runs and
    control COMES BACK. This is the only paragraph in the program that reaches the
    exit that way.

    ``[:L414-L416]`` then zeroes ``File-Function`` and ``Access-Type`` and logs a
    SECOND time. So a close writes TWO log records - one from the performed
    ``aa999-main-exit`` if ``Testing-1``, and one unconditional - and the second
    carries zeros in both function fields, which is the "close log file" signal to
    ``fhlogger``. The zeroing also MUTATES the caller's ``File-Access``, so a
    caller that inspects ``File-Function`` after a close finds zero, not 2.

    Raises:
        CobolFlatFileStoreUnavailableError: At ``close Posting-File`` [:L409].
    """
    # L407  move 202 to WS-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa030-Process-Close"
    ]
    # L408  move spaces to WS-File-Key.
    _write_file_key(file_access, "")
    # L409  close Posting-File.
    raise _flat_file_store_unavailable("close", "common/acas006.cbl:L409")


def aa040_process_read_next(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa040-Process-Read-Next.`` [common/acas006.cbl:L419].

    The maintainer's header explains the shape: "This is processed after Start code
    as its really Start/Read next at point aa041" [:L421-L422].

    ``move 203 to WS-No-Paragraph.`` [:L424], then a guard the maintainer himself
    labels "This block should NOT occur" [:L425-L434]::

        L425      if       Cobol-File-Eof
        L426               move 10 to FS-Reply
        L427                          WE-Error
        L428               move spaces to
        L429                              SQL-Err
        L430                              SQL-Msg
        L431               move zeros to Post-Key
        L432               stop "Cobol File EOF"               *> for testing
        L433               go to aa999-main-exit
        L434      end-if.

    ``move 10 to FS-Reply WE-Error`` is one statement writing BOTH fields, the same
    idiom the bridge uses at [common/glpostingMT.cbl:L557], which is why end of
    file carries ``We-Error`` 10 rather than zero.

    ``stop "Cobol File EOF"`` [:L432] is a ``STOP`` with a literal, which displays
    the text and suspends until the operator resumes - it does NOT end the run, so
    [:L433] does execute afterwards. Agent Action Plan section 0.3.4 rules that an
    accept or pause whose only effect is to block a terminal is dropped while its
    control transfer is preserved, so the pause becomes a log record and the
    transfer stands. Note also that ``move zeros to Post-Key`` [:L431] zeroes the
    FD record's key, not the WS record's, so the caller's record is untouched by
    it.

    Falls through in source order into :func:`aa041_reread` [:L436].
    """
    # L424  move 203 to WS-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa040-Process-Read-Next"
    ]
    if _HANDLER.cobol_file_eof():
        # L426-L427  move 10 to FS-Reply WE-Error - one statement, both fields.
        fs_reply, we_error = end_of_file_status()
        file_access.fs_reply = int(fs_reply)
        file_access.we_error = int(we_error)
        # L428-L430  move spaces to SQL-Err SQL-Msg
        file_access.logging_data.sql_err = ""
        file_access.logging_data.sql_msg = ""
        # L431  move zeros to Post-Key - the FD record's key, which this
        # migration does not carry; the WS record the caller passed is NOT
        # touched, so nothing is written here.
        # L432  stop "Cobol File EOF"  *> for testing - the operator pause is
        # dropped per Agent Action Plan section 0.3.4; the transfer is kept.
        _LOG.warning(
            "aa040-Process-Read-Next [common/acas006.cbl:L425-L432]: "
            'Cobol-File-Eof was already set - the frozen source calls this '
            '"This block should NOT occur" and pauses the run with '
            'stop "Cobol File EOF"; the pause is dropped, the transfer kept'
        )
        # L433  go to aa999-main-exit - Class 3.
        aa999_main_exit(file_access, dal_common)
        return
    # Paragraph fall-through [:L434 -> :L436].
    aa041_reread(posting, file_access, dal_common)


def aa041_reread(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa041-Reread.`` [common/acas006.cbl:L436].

    ``read Posting-File next record at end`` [:L437] with the end clause writing
    ``move 10 to WE-Error FS-Reply`` [:L438], ``set Cobol-File-EoF to true``
    [:L439], ``move 1 to Cobol-File-Status`` under "JIC above dont work :)"
    [:L440] - the maintainer setting by hand the field the ``88`` had just set -
    ``initialize WS-Posting-Record`` [:L441], ``move "EOF" to WS-File-Key`` [:L442]
    and the transfer [:L443]. On a read that succeeded: ``if FS-Reply not = zero go
    to aa999-main-exit.`` [:L445-L446], ``move Posting-Record to
    WS-Posting-Record.`` [:L447], ``move Post-Key to WS-File-Key.`` [:L448],
    ``move zeros to WE-Error.`` [:L449] - note ``FS-Reply`` is NOT cleared here -
    and the transfer [:L450].

    ANOMALY N-REREAD-ASYMMETRY. ``acas006`` has TWO reread paragraphs, this one
    and :func:`aa051_reread` after the indexed read. ``acas005`` has only
    ``aa041-Reread`` and adds an ``aa047-Eval-Keys`` that this handler does not
    have, because the nominal ledger has key evaluation to do and the posting file
    does not. The divergence is recorded, and what is here is what is reproduced.

    Raises:
        CobolFlatFileStoreUnavailableError: At ``read ... next record`` [:L437].
    """
    # L437  read Posting-File next record at end ...
    raise _flat_file_store_unavailable(
        "read ... next record", "common/acas006.cbl:L437"
    )


def aa050_process_read_indexed(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas006.cbl:L452].

    One statement, ``move 204 to WS-No-Paragraph.`` [:L454], then a comment block
    that is itself evidence - "USING POST-RRN / We are reading/writing/deleting RRN
    relative <<<<<<<<<<<<<<" [:L457-L459] - and a fall-through into
    :func:`aa051_reread` [:L461].

    That comment block is the flat-file side of the ``POST-RRN`` question the
    ``.scb`` raises at [common/glpostingMT.scb:L229] and ``copybooks/selpost.cob``
    raises a third time with ``record key Post-Rrn    *> MAY NEED CHANGING <<<``.
    Three files, three notes, one unresolved design question - and the reason
    ANOMALY N-RRN exists at all.
    """
    # L454  move 204 to WS-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa050-Process-Read-Indexed"
    ]
    # Paragraph fall-through [:L460 -> :L461].
    aa051_reread(posting, file_access, dal_common)


def aa051_reread(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa051-Reread.`` [common/acas006.cbl:L461].

    Transcribed [:L462-L471]::

        L462      move     WS-Post-rrn    to Post-Rrn.    *> USING THIS ???   <<<<
        L463      move     WS-Post-Key to Post-Key WS-File-Key.
        L464      move     zero to Cobol-File-Status.
        L465      read     Posting-File    invalid key
        L466               move 21 to we-error fs-reply
        L467               go to aa999-main-exit
        L468      end-read
        L469      move     Posting-Record  to  WS-Posting-Record.
        L470      move     Post-Key to WS-File-Key.
        L471      go       to aa999-main-exit.

    ANOMALY N-WE21. ``move 21 to we-error fs-reply`` [:L466] writes 21 into BOTH
    fields, and ``We-Error`` 21 appears NOWHERE in the authoritative table
    [common/glpostingMT.cbl:L125-L158], whose values are 999, 998, 997, 996, 995,
    994, 992, 990, 989, 988, 911, 910 and 901. So the flat-file path can hand its
    caller a ``We-Error`` the error list cannot explain. Recorded, not corrected;
    ``dal/status.py`` owns the enumeration and does not gain a member for it.

    Note also that [:L463] is one ``MOVE`` with TWO receiving fields, and [:L470]
    then re-moves the FD record's key over the same log tag - so on success the tag
    is written twice from two different records, which agree only when the read
    returned the row that was asked for.

    Raises:
        CobolFlatFileStoreUnavailableError: At ``read ... invalid key`` [:L465].
    """
    # L462  move WS-Post-rrn to Post-Rrn.  - the FD record, not carried here.
    # L463  move WS-Post-Key to Post-Key WS-File-Key.  - the log half IS carried.
    _write_file_key(file_access, _post_key_tag(posting))
    # L464  move zero to Cobol-File-Status.
    _HANDLER.cobol_file_status = 0
    # L465  read Posting-File invalid key ...
    raise _flat_file_store_unavailable(
        "read ... invalid key", "common/acas006.cbl:L465"
    )


def aa060_process_start(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa060-Process-Start.`` [common/acas006.cbl:L473].

    The header carries its own warning, "Check for Param error 1st on start
    WARNING Not logging starts" [:L475], and then "USING POST-RRN" [:L477].

    ``move 205 to WS-No-Paragraph.`` [:L479], ``move zeros to fs-reply WE-Error.``
    [:L480-L481] - this paragraph DOES clear the status, unlike ``aa010-main`` -
    ``move zero to Cobol-File-Status.`` [:L482], ``move WS-Post-Key to WS-File-Key
    Post-Key.`` [:L483-L484] and ``move WS-Post-rrn to Post-Rrn.`` [:L485].

    ANOMALY N-START-NO-FSREPLY. The parameter guard writes ONE field [:L487-L490]::

        L487  if       access-type < 5 or > 8  *> NOT using 'not >'
        L488           move 998 to WE-Error    *> 998 Invalid calling parameter settings
        L489           go to aa999-main-exit
        L490  end-if

    There is no ``move 99 to fs-reply``. Since [:L480] had just cleared
    ``FS-Reply`` to zero, an invalid access type returns ``(0, 998)`` - SUCCESS
    paired with an error code. The BRIDGE's equivalent guard writes both, ``99``
    and ``997`` [common/glpostingMT.cbl:L695-L697]. Reproduced exactly, in both
    programs.

    ANOMALY N-998, meaning 3 of 3: the comment here glosses 998 as "Invalid calling
    parameter settings" [:L488], the key guard glosses the SAME code as "file seeks
    key type out of range" [:L297], and the authoritative table glosses it as
    "File-Key-No out of range" [common/glpostingMT.cbl:L141]. One code, three
    meanings.

    ANOMALY N-relation, flat-file side. Four ``start`` variants follow
    [:L494-L518] - equal-to, not-less-than, greater-than, less-than - and
    ``fn-not-greater-than`` (9) has NO arm, consistent with the guard's upper bound
    of 8 but NOT with the bridge, which does have an arm for 9
    [common/glpostingMT.cbl:L715-L726] while its own guard also rejects it. Nine
    relations declared [copybooks/wsfnctn.cob:L108-L116], eight accepted, four
    implemented here, five in the bridge.

    ANOMALY N-KOR, flat-file side. Every one of the four starts positions on
    ``Post-Rrn``, with ``*> Post-Key invalid key`` commented out beside each
    [:L495, :L501, :L507, :L514]. So the flat-file START keys on the relative
    record number while the bridge's START keys on the ten-byte slice that begins
    with it - the same disagreement, from the other side.

    Raises:
        CobolFlatFileStoreUnavailableError: At the first ``start`` verb reached.
    """
    # L479  move 205 to WS-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa060-Process-Start"
    ]
    # L480-L481  move zeros to fs-reply WE-Error.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # L482  move zero to Cobol-File-Status.
    _HANDLER.cobol_file_status = 0
    # L483-L484  move WS-Post-Key to WS-File-Key Post-Key.
    _write_file_key(file_access, _post_key_tag(posting))
    # L485  move WS-Post-rrn to Post-Rrn.  - the FD record, not carried here.
    access_type = int(file_access.access_type)
    # L487  if access-type < 5 or > 8   *> NOT using 'not >'
    lowest, highest = START_ACCESS_TYPE_RANGE
    if access_type < lowest or access_type > highest:
        # ANOMALY N-START-NO-FSREPLY: `move 998 to WE-Error` [:L488] and NOTHING
        # to FS-Reply, which [:L480] left at zero. Success paired with an error.
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        # L489  go to aa999-main-exit - Class 3.
        aa999_main_exit(file_access, dal_common)
        return
    # L494-L518  the four `start` variants, on Post-Rrn.
    if access_type == AccessType.EQUAL_TO:
        raise _flat_file_store_unavailable(
            "start ... key =", "common/acas006.cbl:L495"
        )
    if access_type == AccessType.NOT_LESS_THAN:
        raise _flat_file_store_unavailable(
            "start ... key not <", "common/acas006.cbl:L501"
        )
    if access_type == AccessType.GREATER_THAN:
        raise _flat_file_store_unavailable(
            "start ... key >", "common/acas006.cbl:L507"
        )
    if access_type == AccessType.LESS_THAN:
        raise _flat_file_store_unavailable(
            "start ... key <", "common/acas006.cbl:L514"
        )
    # L520  go to aa999-main-exit.   *> logging  - Class 3. Unreachable given the
    # guard above admits only 5 through 8 and all four have arms; kept because the
    # frozen source keeps it, and reached in the COBOL only if a new Access-Type
    # were ever added inside the accepted range without an arm.
    aa999_main_exit(file_access, dal_common)


def aa070_process_write(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa070-Process-Write.`` [common/acas006.cbl:L522].

    Transcribed [:L523-L532]::

        L523      move     206 to WS-No-Paragraph.
        L524      move     WS-Posting-Record to Posting-Record.
        L525      move     zeros to FS-Reply  WE-Error.
        L526      move     zero to Cobol-File-Status.
        L527      move     Post-Key to WS-File-Key.
        L528      write    Posting-Record invalid key
        L529               move 22 to FS-Reply
        L530               go to aa999-main-exit.
        L531      move     Post-Key to WS-File-Key.
        L532      go       to aa999-main-exit.

    The period at the end of [:L530] terminates the ``write``, so [:L531] is
    reached only when the write succeeded - and it re-moves the SAME value [:L527]
    already moved, a redundancy the bridge mirrors at
    [common/glpostingMT.cbl:L685-L686]. The duplicate-key status 22 [:L529] agrees
    with the bridge's [common/glpostingMT.cbl:L821], which is one of the few places
    the two programs do agree.

    Raises:
        CobolFlatFileStoreUnavailableError: At ``write ... invalid key`` [:L528].
    """
    # L523  move 206 to WS-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa070-Process-Write"
    ]
    # L524  move WS-Posting-Record to Posting-Record.  - the FD record.
    # L525  move zeros to FS-Reply WE-Error.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # L526  move zero to Cobol-File-Status.
    _HANDLER.cobol_file_status = 0
    # L527  move Post-Key to WS-File-Key.  - the FD key, which [:L524] had just
    # filled from the WS record, so the value is the WS record's own key.
    _write_file_key(file_access, _post_key_tag(posting))
    # L528  write Posting-Record invalid key ...
    raise _flat_file_store_unavailable(
        "write ... invalid key", "common/acas006.cbl:L528"
    )


def aa080_process_delete(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa080-Process-Delete.`` [common/acas006.cbl:L534].

    Transcribed [:L535-L545]::

        L535      move     207 to WS-No-Paragraph.
        L536      move     WS-Post-Key to Post-Key.
        L537      move     WS-Post-Key to WS-File-Key.
        L538      move     WS-Post-rrn to Post-rrn.       *>   NEW for relative ?? <<
        L539      move     zeros to FS-Reply  WE-Error.
        L540      move     zero to Cobol-File-Status.
        L544      delete   Posting-File record.
        L545      go       to aa999-main-exit.

    ``delete`` carries NO ``invalid key`` clause [:L544], so a delete that matches
    nothing reports whatever the file status left in ``FS-Reply`` - the flat-file
    twin of ANOMALY N-NOSTATUS, where the bridge's zero-row delete writes no status
    either [common/glpostingMT.cbl:L866-L877]. The maintainer's ``*> NEW for
    relative ?? <<`` at [:L538] is a fourth note in the ``POST-RRN`` family.

    Raises:
        CobolFlatFileStoreUnavailableError: At ``delete ... record`` [:L544].
    """
    # L535  move 207 to WS-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa080-Process-Delete"
    ]
    # L536  move WS-Post-Key to Post-Key.  - the FD record.
    # L537  move WS-Post-Key to WS-File-Key.
    _write_file_key(file_access, _post_key_tag(posting))
    # L538  move WS-Post-rrn to Post-rrn.  - the FD record.
    # L539  move zeros to FS-Reply WE-Error.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # L540  move zero to Cobol-File-Status.
    _HANDLER.cobol_file_status = 0
    # L544  delete Posting-File record.   - no `invalid key` clause.
    raise _flat_file_store_unavailable("delete ... record", "common/acas006.cbl:L544")


def aa090_process_rewrite(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa090-Process-Rewrite.`` [common/acas006.cbl:L547].

    Transcribed [:L549-L555]::

        L549      move     208 to WS-No-Paragraph.
        L550      move     WS-Posting-Record to Posting-Record.
        L551      move     zeros to FS-Reply  WE-Error.
        L552      move     zero to Cobol-File-Status.
        L553      move     Post-Key to WS-File-Key.
        L554      rewrite  Posting-Record.
        L555      go       to aa999-main-exit.

    Like the delete, ``rewrite`` carries no ``invalid key`` clause [:L554]. Note
    that it does NOT move ``WS-Post-rrn`` to ``Post-rrn`` the way the delete does
    at [:L538], even though the record it rewrites is keyed on the rrn - so a
    rewrite depends entirely on the rrn the FD record already held. That is the
    flat-file counterpart of ANOMALY N-RRN, where the bridge's rewrite stamps the
    primary key back to zero.

    Raises:
        CobolFlatFileStoreUnavailableError: At ``rewrite`` [:L554].
    """
    # L549  move 208 to WS-No-Paragraph.
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa090-Process-Rewrite"
    ]
    # L550  move WS-Posting-Record to Posting-Record.  - the FD record.
    # L551  move zeros to FS-Reply WE-Error.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # L552  move zero to Cobol-File-Status.
    _HANDLER.cobol_file_status = 0
    # L553  move Post-Key to WS-File-Key.
    _write_file_key(file_access, _post_key_tag(posting))
    # L554  rewrite Posting-Record.   - no `invalid key` clause.
    raise _flat_file_store_unavailable("rewrite", "common/acas006.cbl:L554")


def aa100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa100-Bad-Function.`` [common/acas006.cbl:L557].

    Under the same "Houston; We have a problem" the bridge uses [:L559]::

        L561      move     999 to WE-Error.                         *> 999
        L562      move     99  to fs-reply.

    ANOMALY N-BRIDGE-BAD-FN, handler side: 999 here against the bridge's 990
    [common/glpostingMT.cbl:L1015], and the authoritative table's own
    "Invalid Function requested" code 992 [:L146] written by neither. Three codes
    for one condition; none harmonised.

    Falls through in source order into :func:`aa999_main_exit` [:L564] - it is the
    only paragraph that reaches the exit by fall-through rather than by transfer.
    """
    # L561  move 999 to WE-Error.
    file_access.we_error = int(WeError.NOT_USED)
    # L562  move 99 to fs-reply.
    file_access.fs_reply = int(FsReply.ERROR)
    # Paragraph fall-through [:L563 -> :L564].
    aa999_main_exit(file_access, dal_common)


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa999-main-exit.`` [common/acas006.cbl:L564].

    ``if Testing-1 perform Ca-Process-Logs end-if.`` [:L565-L567], then
    fall-through into :func:`aa_main_exit`.

    ``Testing-1`` is ``88 Testing-1 value 1`` over ``SW-Testing pic 9 value 1``
    [copybooks/Test-Data-Flags.cob:L10-L11], so the DECLARED DEFAULT IS ON and the
    maintainer's note says how to turn it off: "set sw-testing to zero to stop
    logging" [common/acas006.cbl:L271].
    """
    if int(dal_common.sw_testing) == 1:
        ca_process_logs(file_access, dal_common)
    # Paragraph fall-through [:L568 -> :L569].
    aa_main_exit()


def aa_main_exit() -> None:
    """``aa-main-exit.`` [common/acas006.cbl:L569].

    Carries no statements - only the comment "Now have processed cobol flat file,
    so .." [:L571] - and falls through into :func:`aa_exit`. It exists as a
    transfer target: the two RDB branches jump straight here [:L317, :L325], which
    is how they bypass the handler's own log record.
    """
    # Paragraph fall-through [:L572 -> :L573].
    aa_exit()


def aa_exit() -> None:
    """``aa-Exit.  exit program.`` [common/acas006.cbl:L573-L574].

    Returns control to the caller. Nothing to do: the status already sits in the
    caller's ``File-Access`` block, which is how a COBOL ``CALL`` returns it.
    """
    return


def ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs.`` of the HANDLER [common/acas006.cbl:L666].

    ``call "fhlogger" using File-Access ACAS-DAL-Common-data.`` [:L669-L670],
    under the maintainer's "Not called on DAL access as it does it already"
    [:L666] - which is exactly right and exactly why a close produces several
    records: the bridge's ``ba999-end`` has already logged before the handler's
    ``aa999-main-exit`` logs again.

    Distinct from :func:`mt_ca_process_logs`, the bridge's paragraph of the same
    name [common/glpostingMT.cbl:L1487]. The two are separate programs, so the
    COBOL names do not collide; in one Python module they would, and the bridge's
    copies carry the ``mt_`` prefix for that reason - recorded here because a
    reader looking for ``Ca-Process-Logs`` will find two.

    ``common/fhlogger.cbl`` is out of scope (Agent Action Plan section 0.2.2) and
    rule R-1 forbids calling it, so a structured record stands in for the file it
    writes. It reaches no table and appears in no dump.
    """
    logging_data = file_access.logging_data
    _LOG.info(
        "fhlogger %s sys=%d file=%d para=%d fn=%d access=%d fs=%d we=%d "
        "key=%s state=%s err=%s msg=%s testing=%d/%d",
        HANDLER_NAME,
        int(logging_data.ws_log_system),
        int(logging_data.ws_log_file_no),
        int(logging_data.ws_no_paragraph),
        int(file_access.file_function),
        int(file_access.access_type),
        int(file_access.fs_reply),
        int(file_access.we_error),
        sanitise_for_log(str(logging_data.ws_file_key)),
        sanitise_for_log(str(logging_data.sql_state)),
        sanitise_for_log(str(logging_data.sql_err)),
        sanitise_for_log(str(logging_data.sql_msg)),
        int(dal_common.sw_testing),
        int(dal_common.sw_testing_2),
    )
    ca_exit()


def ca_exit() -> None:
    """``ca-Exit.     exit.`` of the HANDLER [common/acas006.cbl:L672]."""
    return


# ---------------------------------------------------------------------------
# Handler `acas006` - `ba-Process-RDBMS`, in source order
# ---------------------------------------------------------------------------


def ba_process_rdbms(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba-Process-RDBMS section.`` [common/acas006.cbl:L576].

    "Here we call the relevent RDBMS module for this table which will include
    processing any other joined tables as needed" [:L579-L582]. A label only, so
    control falls into :func:`ba010_test_ws_rec_size` at [:L584].

    THE WHOLE SECTION IS A CHAIN OF FALL-THROUGHS: ``ba010-Test-WS-Rec-Size``
    [:L584] into ``ba012-Test-WS-Rec-Size-2`` [:L592] into ``ba015-Test-Ends``
    [:L635] into ``ba020-Process-DAL`` [:L653] into ``ba-rdbms-exit`` [:L662].
    There is not one ``go to`` between them except the record-length escape at
    [:L620]. That chain is what produces the TWO bridge calls of ANOMALY N18b, and
    modelling it as a chain rather than as an ``if`` is the whole point.
    """
    ba010_test_ws_rec_size(
        system,
        posting,
        file_access,
        dal_common,
        transport=transport,
        states=states,
    )


def ba010_test_ws_rec_size(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas006.cbl:L584].

    ONE statement, and it is ANOMALY N-log [:L590]::

        L590      move     22 to WS-Log-File-no.        *> for FHlogger

    The 12 written by ``aa010-main`` at [:L289] is replaced by 22 the instant the
    RDB path is entered, so every migrated run logs 22 and only a flat-file run
    logs 12. The paragraph's own header comments describe the record-length test
    that lives in the NEXT paragraph - "Test on very first call only (So do NOT use
    var A & B again)" [:L586-L588] - which is why the two are one logical step
    split across two labels.

    Falls through into :func:`ba012_test_ws_rec_size_2` [:L592].
    """
    # L590  move 22 to WS-Log-File-no.   - ANOMALY N-log. Note the lower-case
    # `no` here against `No` at [:L289].
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB_PATH
    # Paragraph fall-through [:L591 -> :L592].
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        # `go to ba-rdbms-exit` [:L620] left the section before ba015.
        ba_rdbms_exit()
        return
    # Paragraph fall-through [:L634 -> :L635].
    ba015_test_ends(
        file_access,
        dal_common,
        posting,
        system_record=system,
        transport=transport,
        states=states,
    )


def ba012_test_ws_rec_size_2(
    system: SystemRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas006.cbl:L592].

    Two jobs under ONE first-call-only gate, ``if A = zero`` [:L594] - "so it is
    being called first time".

    **Job 1, the record-length test** [:L595-L621]. ``function Length
    (WS-Posting-Record)`` into ``A`` and ``function length (Posting-Record)`` into
    ``B``, then ``if A < B`` writes ``WE-Error 901`` [:L602] and ``FS-Reply 99``
    [:L603], and the ``if WE-Error = 901`` block that follows builds the ``GL903``
    diagnostic, displays it, copies it to ``SQL-Msg``, logs it if ``Testing-1``,
    ``accept``s and transfers to ``ba-rdbms-exit`` [:L620].

    ANOMALY N-901-DEAD. THAT WHOLE BRANCH IS UNREACHABLE.
    ``copybooks/fdpost.cob`` and ``copybooks/wspost.cob`` declare the SAME fifteen
    fields with the same pictures, differing only in the ``WS-`` name prefixes, so
    both records are 103 bytes and ``A < B`` can never hold. The comparison is
    reproduced anyway - :data:`WS_POSTING_RECORD_BYTES` against
    :data:`POSTING_RECORD_BYTES`, each derived independently so that the equality
    is a measurement and not an identity - and it stays dead for the same reason
    the COBOL's is. Note that both copybook headers still claim "98 bytes" and
    "96 bytes", offsets that describe a legend field of ``x(30)`` from before the
    2017 change.

    The ``accept Accept-Reply at 2433`` [:L619] is dropped per Agent Action Plan
    section 0.3.4 - its only effect is to block a terminal - while the transfer at
    [:L620] is preserved, which is what this function's return value is for.

    **Job 2, the credential load** [:L627-L632]. Six moves from the system record's
    ``RDBMS-*`` fields into the ``RDB-Data`` block, under "Load up the DB settings
    from the system record as its not passed on / hopefully once is enough  :)"
    [:L624-L625]. That half is owned by
    :func:`acas_posting.dal.connection.load_rdb_data_once`, which supplies the same
    once-only semantics and the same six fields; it is CALLED, not duplicated.

    Note the ORDER the COBOL uses - schema, user, password, port, host, socket -
    which is not the declaration order of ``RDB-Data``
    [copybooks/wsfnctn.cob:L57-L62]. Nothing depends on it, and ``connection.py``
    records it.

    Reached from TWO places: the flat-file path performs it directly [:L330], and
    the RDB path falls into it from :func:`ba010_test_ws_rec_size`. The COBOL-path
    call is why the log file number can still be 12 when this runs.

    Returns:
        ``True`` if the record-length branch transferred to ``ba-rdbms-exit``
        [:L620], which by ANOMALY N-901-DEAD it never does.
    """
    # L594  if A = zero    *> so it is being called first time
    if _HANDLER.a == 0:
        # L595-L597  move function Length (WS-Posting-Record) to A
        _HANDLER.a = WS_POSTING_RECORD_BYTES
        # L598-L600  move function length (Posting-Record) to B
        _HANDLER.b = POSTING_RECORD_BYTES
        # L601  if A < B    *> COULD LET caller module deal with these errors !!!!!!!
        if _HANDLER.a < _HANDLER.b:
            # ANOMALY N-901-DEAD: unreachable, because both records are
            # WS_POSTING_RECORD_BYTES == POSTING_RECORD_BYTES == 103 bytes.
            # `move 901 to WE-Error` [:L602], `move 99 to fs-reply` [:L603].
            file_access.we_error = int(WeError.RECORD_SIZE_MISMATCH)
            file_access.fs_reply = int(FsReply.ERROR)
        # L605  if WE-Error = 901
        if int(file_access.we_error) == WeError.RECORD_SIZE_MISMATCH:
            # L606-L612  the GL903 diagnostic, built into Display-Blk.
            display_blk = (
                f"{GL903_MESSAGE}{_HANDLER.a:04d} < Posting-Rec = "
                f"{_HANDLER.b:04d}"
            )[:DISPLAY_BLK_WIDTH]
            # L613-L614  two `display ... with erase eol` - presentation, dropped.
            # L615  move Display-Blk to SQL-Msg
            file_access.logging_data.sql_msg = display_blk
            # L616-L618  if Testing-1 perform Ca-Process-Logs
            if int(dal_common.sw_testing) == 1:
                ca_process_logs(file_access, dal_common)
            # L619  accept Accept-Reply at 2433 - the pause is dropped per Agent
            # Action Plan section 0.3.4; the transfer at [:L620] is kept.
            _LOG.error(
                "ba012-Test-WS-Rec-Size-2 [common/acas006.cbl:L601-L620]: %s "
                "- WE-Error 901; the frozen source displays %r and waits for "
                "the operator before leaving the section",
                display_blk,
                GL901_MESSAGE,
            )
            # L620  go to ba-rdbms-exit - Class 3, out of the whole section.
            return True
        # L627-L632  the six credential moves, owned by connection.py.
        load_rdb_data_once(system)
    # L633  end-if.
    return False


def ba015_test_ends(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba015-Test-Ends.`` [common/acas006.cbl:L635] - ANOMALY N18b, stage 2.

    Transcribed [:L637-L644]::

        L637  *>  First check if there is an open output and if so open 1st then
        L638  *>   we need to force a DELETE-ALL call to the DAL. [ Backup code ].
        L640      if       fn-Open
        L641         and   fn-Output
        L642               perform ba020-Process-Dal
        L643               set fn-Delete-All to true
        L644      end-if.

    And then the paragraph ENDS. There is no ``go to``, so control falls through in
    source order into ``ba020-Process-DAL`` at [:L653] - which means the bridge is
    called a SECOND time, now with ``File-Function`` set to 6.

    *** ONE Open-Output REQUEST PRODUCES TWO SEQUENTIAL BRIDGE INVOCATIONS ***
    first with ``fn-Open`` / ``fn-Output``, then with ``fn-Delete-All``. Modelled as
    Agent Action Plan section 0.4.2 Class 2 - the terminator's post-loop work
    placed faithfully after it - because the second call IS the fall-through and
    collapsing it would lose a statement the database sees.

    THREE SIBLING HANDLERS BEHAVE THREE DIFFERENT WAYS at this point, and all
    three are preserved in their own modules:

    * ``acas006`` - this one - calls the bridge twice
      [common/acas006.cbl:L642-L643, :L653].
    * ``acas008`` COERCES instead: it sets ``fn-Delete-All`` up front, in the
      stage-1 block, so there is ONE call and it is a delete-all
      [common/acas008.cbl:L313-L319].
    * ``acas005`` does NOTHING: its whole Open-Output block is commented out under
      "-- NOT used with GL." [common/acas005.cbl:L307, :L310-L317].

    Agent Action Plan section 0.8.2 is the reason all three stand: "A defect
    reproduced is correct; a defect fixed is a failure."

    Note also what the ``set`` at [:L643] does to the CALLER: ``File-Function``
    lives in the ``File-Access`` block the caller passed, so after an Open-Output
    the caller's own block reads 6, not 1. That mutation is visible and is
    reproduced.
    """
    # L640-L641  if fn-Open and fn-Output
    if (
        int(file_access.file_function) == FileFunction.OPEN
        and int(file_access.access_type) == AccessType.OUTPUT
    ):
        # L642  perform ba020-Process-Dal   - BRIDGE CALL ONE, as fn-Open/fn-Output.
        ba020_process_dal(
            file_access,
            dal_common,
            posting,
            system_record=system_record,
            transport=transport,
            states=states,
        )
        # L643  set fn-Delete-All to true   - mutates the CALLER's File-Access.
        file_access.file_function = int(FileFunction.DELETE_ALL)
    # L644  end-if.  Then paragraph fall-through [:L652 -> :L653] - BRIDGE CALL
    # TWO. On an Open-Output it now carries fn-Delete-All (6); on every other verb
    # this is the one and only call.
    ba020_process_dal(
        file_access,
        dal_common,
        posting,
        system_record=system_record,
        transport=transport,
        states=states,
    )
    # Paragraph fall-through [:L659 -> :L662].
    ba_rdbms_exit()


def ba020_process_dal(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba020-Process-DAL.`` [common/acas006.cbl:L653].

    The one and only call out of the handler [:L654-L658]::

        L653   ba020-Process-DAL.
        L654       call     "glpostingMT" using File-Access
        L655                                    ACAS-DAL-Common-data
        L657                                    WS-Posting-Record
        L658       end-call.

    THREE parameters with ``File-Access`` FIRST, where the handler's own linkage
    takes five with ``System-Record`` first [:L273-L279]. The blank line between
    the second and third arguments is the maintainer's own [:L656]; the parameter
    ORDER is what matters and it is preserved exactly, so a reviewer can diff the
    two argument lists.

    "Any errors leave it to caller to recover from" [:L660] - so nothing is tested
    here, and whatever the bridge left in ``File-Access`` is what the handler's
    caller receives. The comment block above [:L646-L651] records the compiler
    directive the maintainer wanted for selecting between pre-SQL translators, and
    that there is only one target today: "NOW SET UP FOR JC pre-sql compiler
    system."
    """
    glposting_mt(
        file_access,
        dal_common,
        posting,
        system_record=system_record,
        transport=transport,
        states=states,
    )


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit.  exit section.`` [common/acas006.cbl:L662-L663].

    Leaves ``ba-Process-RDBMS``, returning to whichever ``perform`` entered it -
    [:L316], [:L324] or [:L330].
    """
    return


def dispatch(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``acas006`` - the file handler, entered at its ``PROCEDURE DIVISION``.

    FIVE parameters, in exactly this order [common/acas006.cbl:L273-L279]::

        L273   Procedure Division Using System-Record
        L275                            WS-Posting-Record
        L277                            File-Access
        L278                            File-Defs
        L279                            ACAS-DAL-Common-data.

    Which is the Agent Action Plan section 0.4.3 ``CALL`` contract::

        FROM:  call "acas006" using System-Record WS-Posting-Record File-Access
                                   File-Defs ACAS-DAL-Common-data
        TO:    acas006_gl_posting.dispatch(system, posting, file_access,
                                          file_defs, dal_common)

    This is the entity-named half of the dual vocabulary rule R-5 requires: the
    GL-Posting facade verbs [copybooks/Proc-ACAS-FH-Calls.cob] reach the table
    through here, while a reader following the bridge's own convention uses
    :func:`glposting_mt`. One implementation, two published entry points.

    The facade's dispatch paragraph sets ``move 1 to File-Key-No`` before the
    ``CALL`` [copybooks/Proc-ACAS-FH-Calls.cob:L43-L49], which is what makes the
    key guard of :func:`aa010_main` pass; a caller reaching this function directly
    must set it the same way, because reproducing the guard means reproducing its
    failure too.

    Returns ``None`` and reports through ``file_access``, mutated in place, exactly
    as the COBOL reports through the linkage block. Note two mutations a caller may
    not expect, both faithful: an Open-Output leaves ``File-Function`` at 6
    [:L643], and a Close leaves both ``File-Function`` and ``Access-Type`` at zero
    [:L414-L415].

    Args:
        system: ``System-Record``. Read for ``RDBMS-Flat-Statuses`` and the six
            RDBMS credentials.
        posting: ``WS-Posting-Record``. Read on a write, mutated on a read.
        file_access: ``File-Access``. Carries the verb in and the status out.
        file_defs: ``File-Defs``. Part of the linkage; consulted by the flat-file
            store alone.
        dal_common: ``ACAS-DAL-Common-data``, the two testing switches and the log
            counter.
        transport: Transport policy for the open. Keyword-only, and NOT part of the
            COBOL linkage - the compiled system reaches its connection through
            ``RDB-Data`` and a C interface that has no transport policy at all, so
            this is the migration's own fail-closed guard rather than a
            reproduction of anything.
        states: The cursor table. Keyword-only for the same reason: the bridge's
            ``01 DAL-Data`` is its own working storage, and this parameter exists so
            a test can supply an isolated copy.

    Raises:
        CobolFlatFileStoreUnavailableError: If ``File-System-Used`` says COBOL
            files [copybooks/wssystem.cob:L113] and the verb reaches an ISAM
            statement. Every migrated configuration takes the RDB branch instead.
        BridgeNotOpenError: If a verb other than ``fn-Open`` is issued before an
            open has succeeded.
    """
    aa_process_flat_file(
        system,
        posting,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )
