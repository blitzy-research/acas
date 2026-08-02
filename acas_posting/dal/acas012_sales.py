"""Sales Ledger file handler ``acas012`` and its bridge ``salesMT``.

The Python reimplementation of two frozen COBOL programs, read as specification
and never executed (rule R-1):

* ``common/acas012.cbl`` - the numbered file handler the Sales entity facade
  calls. 679 lines, program-id ``acas012``, ``prog-name pic x(17) value
  "acas012 (3.3.00)"`` [common/acas012.cbl:L248].
* ``common/salesMT.cbl`` - the JC preSQL 1.14f generated bridge it dispatches
  to on the RDB path. 2269 lines, program-id ``salesMT``, ``prog-name pic x(17)
  value "SalesMT (3.3.00)"`` [common/salesMT.cbl:L206].

Together they serve one table, ``SALEDGER-REC``: 37 columns, primary key
``SALES-KEY``, ``ENGINE=InnoDB`` [mysql/ACASDB.sql:L945-L985]. The record layout
is ``copybooks/wssl.cob`` (68 lines, "rec size 300 bytes"), reimplemented as
:class:`~acas_posting.records.sales_ledger.WsSalesRecord`.

The spine, per Agent Action Plan 0.2.1.1::

    entity Sales -> handler acas012 -> bridge salesMT -> table SALEDGER-REC
                 -> copybook copybooks/wssl.cob -> WsSalesRecord

Agent Action Plan 0.3.1 fixes the module boundary at the HANDLER, not the table:
"One data-access module per handler, not per table. ... preserves the dispatch
semantics rather than flattening them."


THE LINKAGE - THREE SIGNATURES, ALL PUBLISHED
=============================================

The handler takes FIVE parameters [common/acas012.cbl:L276-L282]::

    Procedure Division Using System-Record
                             WS-Sales-Record
                             File-Access
                             File-Defs
                             ACAS-DAL-Common-data.

reached as :func:`dispatch`. Its caller is the facade's own dispatch paragraph
[copybooks/Proc-ACAS-FH-Calls.cob:L82-L88], which forces the key number first::

     acas012.       *> Sales Ledger
         move     1  to File-Key-No.
         call     "acas012" using System-Record WS-Sales-Record File-Access
                                  File-Defs ACAS-DAL-Common-Data.

The bridge takes THREE, in a different order [common/salesMT.cbl:L354-L356], and
is called from the handler's ``ba015-Test-Ends`` [common/acas012.cbl:L648-L662]::

    call     "salesMT" using File-Access
                            ACAS-DAL-Common-data
                            WS-Sales-Record

reached as :func:`sales_mt`. Note what the bridge does NOT receive: no
``System-Record`` and no ``File-Defs``. Its credentials arrive through
``File-Access.RDB-Data``, which the handler loaded in
``ba012-Test-WS-Rec-Size-2`` [common/acas012.cbl:L606-L646]; its connection is
process-global state in the compiled C interface, modelled here by
:class:`BridgeSession`.

Eleven Sales facade verbs sit above :func:`dispatch`
[copybooks/Proc-ACAS-FH-Calls.cob:L652-L707], each a ``File-Function`` plus an
``Access-Type``: ``Sales-Open`` (1, i-o), ``-Open-Input`` (1, input),
``-Open-Output`` (1, output), ``-Close`` (2), ``-Delete`` (8), ``-Start`` (9),
``-Read-Next`` (3), ``-Read-Next-Sorted-By-Name`` (31), ``-Read-Indexed`` (4),
``-Write`` (5), ``-Rewrite`` (7). There is no ``-Open-Extend`` verb and no
``-Delete-All`` verb; both absences are deliberate and are recorded below.


THE NINE FUNCTION CODES - AND WHY IT IS NINE, NOT EIGHT
=======================================================

``evaluate File-Function`` [common/acas012.cbl:L336-L356]::

    when  1        -> aa020-Process-Open
    when  2        -> aa030-Process-Close
    when  3
    when  31       -> aa040-Process-Read-Next      <== TWO CODES, ONE BRANCH
    when  4        -> aa050-Process-Read-Indexed
    when  5        -> aa070-Process-Write
    when  7        -> aa090-Process-Rewrite
    when  8        -> aa080-Process-Delete
    when  9        -> aa060-Process-Start
    when  other                          *> 6 is spare / unused
                   -> aa100-Bad-Function

then, after ``end-evaluate``, an unreachable-by-design fall-through
``go to aa100-Bad-Function.`` [common/acas012.cbl:L359] under the comment
"Should never get here but in case :(" [:L358]. Both routes are reproduced.

Code 31 is ``fn-Read-By-Name`` [copybooks/wsfnctn.cob:L102], added by the
handler's own changelog entry "15/01/17 vbc - .05 Allow for fn-Read-By-Name used
in SL165." [common/acas012.cbl:L139]. The evaluate order 1, 2, 3/31, 4, 5, 7, 8,
9 is preserved verbatim (rule R-6).


ANOMALIES REPRODUCED, NEVER FIXED (rule R-4)
============================================

Agent Action Plan 0.8.2, verbatim: "There is no test suite: compiled COBOL
execution is the behavioral specification, defects included. A defect reproduced
is correct; a defect fixed is a failure." Every entry below carries an inline
locator at its reproduction site, as Agent Action Plan 0.7.4 C-4 requires, and
every entry belongs in ``docs/migration/anomaly-log.md`` naming this module.

**A-11 - SIGN LOSS AT THE BRIDGE. Eleven fields. This module is the Agent Action
Plan's named reproduction site for it** (0.7.2 R-4, verbatim: "the sign loss at
the bridge is reproduced in ``dal/acas012_sales.py``"). ``copybooks/wssl.cob``
declares eleven fields ``binary-short`` / ``binary-long``, which are SIGNED in
COBOL, while annotating each with the UNSIGNED equivalent the maintainer had in
mind - ``*> 9999 comp`` and ``*> 9(8) comp`` [copybooks/wssl.cob:L43-L53]. The
bridge then declares every one of them ``PIC 9(nn) COMP``, unsigned
[common/salesMT.cbl:L302-L312], and the schema declares every column
``unsigned``. So the sign is lost AT THE BRIDGE, before any SQL executes.
Reproduced by :func:`_sign_loss_at_the_bridge`, applied in
:func:`bb000_hv_load` to exactly the eleven columns of
:data:`SIGN_LOSS_COLUMNS` and to no others.

    CORRECTION TO THE AGENT ACTION PLAN, RECORDED AS REQUIRED. The plan cites
    the block as ``[common/salesMT.cbl:L305-L312]`` in both 0.4.1.5 and 0.6.2.
    That span is EIGHT host variables. The verified span is
    ``L302-L312``, ELEVEN: ``HV-SALES-LATE-MIN`` [:L302],
    ``HV-SALES-LATE-MAX`` [:L303] and ``HV-SALES-LIMIT`` [:L304] narrow
    identically and the plan's citation omits them. The source is trusted over
    the plan. The generated data dictionary agrees independently: exactly
    eleven ``SALEDGER-REC`` entries carry anomaly reference ``A-11``, and the
    same eleven are selected by ``copybook.signed and not
    bridge_host_variable.signed`` - see :data:`SIGN_LOSS_COLUMNS`.

    THE RESULTING STORED VALUE WAS MEASURED, NOT ASSUMED. Agent Action Plan
    0.6.8 lists this as an open question, verbatim: "what the resulting stored
    value *is* depends on the conversion the bridge's C interface performs,
    which must be measured rather than assumed." Measured on GnuCOBOL 3.2.0
    with the bridge's own declarations: ``binary-long -42`` arrives in
    ``PIC 9(10) COMP`` as ``0000000042``; ``-1`` as ``0000000001``;
    ``-2147483648`` as ``2147483648``; ``binary-short -7`` in ``PIC 9(05)
    COMP`` as ``00007``; ``-32768`` as ``32768``. The conversion is therefore
    the DECIMAL ABSOLUTE VALUE with high-order truncation to the receiving
    field's digit count - a COBOL ``MOVE``, not a two's-complement
    reinterpretation. Recorded as ambiguity ``Q-3`` in
    ``docs/migration/ambiguity-resolutions.md``.

**A-11-clean - the seven signed money fields pass cleanly, and must not be
"fixed" in either direction.** ``Sales-Current``, ``Sales-Last``,
``Turnover-Q1`` through ``Q4`` and ``Sales-Unapplied`` are ``s9(8)v99 comp-3``
in the copybook, ``S9(08)V9(02) COMP`` in the bridge
[common/salesMT.cbl:L313-L319] and signed ``decimal(10,2)`` in the schema. This
side-by-side contrast inside one record is Agent Action Plan 0.6.2's proof that
the drift is "specific rather than systemic and must be handled field by field
from the dictionary", so it is an explicit, named distinction here:
:data:`MONEY_COLUMNS` versus :data:`SIGN_LOSS_COLUMNS`, and
:func:`_store_into_signed_host_variable` versus
:func:`_sign_loss_at_the_bridge`.

    A PRECISION NOTE ON THE COUNT. The eight ``decimal`` columns are those
    seven SIGNED money columns plus ``SALES-DISCOUNT``, which is
    ``decimal(4,2) unsigned`` and unsigned at all three layers. So: eight
    decimal columns, of which seven are signed money.

**N-signdrop - NEW, undocumented by the Agent Action Plan, and it qualifies the
plan's claim above.** The declarations of the seven money fields do pass
cleanly, but the SQL TEXT the bridge generates still drops their sign.
``WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` [common/salesMT.cbl:L216] carries the sign in
character position 1, and NO generated statement ever reads position 1: the only
windows used anywhere in ``salesMT`` are ``(11:10)``, ``(13:08)``, ``(16:05)``,
``(18:03)``, ``(19:02)`` and ``(22:02)``. Measured on GnuCOBOL 3.2.0:
``HV-SALES-CURRENT = -12345.67`` edits to ``"-              12345.670000000"``,
and ``TRIM(WS-MYSQL-EDIT(13:08)) + "." + WS-MYSQL-EDIT(22:02)``
[common/salesMT.cbl:L1636-L1642] yields ``12345.67`` - byte-identical to the
rendering of ``+12345.67``. A negative balance is therefore STORED POSITIVE.
Verified systemic, not a ``salesMT`` typo: ``WS-MYSQL-EDIT(1:`` appears in none
of the 28 frozen bridges, and ``nominalMT`` renders ``HV-LEDGER-BALANCE`` the
same way [common/nominalMT.cbl:L1074-L1080]. Reproduced by
:func:`_render_numeric_for_sql`, which is why :func:`bb200_insert` and
:func:`bb300_update` bind the RENDERED TEXT rather than the ``Decimal`` - binding
the ``Decimal`` would silently repair the anomaly.

    So declaration drift (A-11, eleven statistics fields) and rendering drift
    (N-signdrop, every signed numeric including the money fields) are TWO
    SEPARATE MECHANISMS in two separate places. Both are reproduced.

**N-2fields-lost - NEW, undocumented by the Agent Action Plan. Two columns are
both write-blind and read-blind.** ``bb000-HV-Load`` moves 35 fields, stopping
at ``Sales-UNAPPLIED`` [common/salesMT.cbl:L1204-L1239]; ``bb100-UnloadHVs``
moves the same 35, stopping at the same field [:L1256-L1292]. Neither touches
``HV-SALES-STATS-DATE`` or ``HV-SALES-PARTIAL-SHIP-FLAG``, yet both host
variables ARE declared [:L320-L321], ARE filled by every fetch [:L598-L599,
:L728-L729, :L1121-L1122] and ARE written by ``bb200-Insert`` [:L1751-L1762] and
``bb300-Update`` [:L2231-L2242]. Consequences, both reproduced:

* ON WRITE, ``initialize TD-SALEDGER-REC`` [:L1204] leaves both host variables
  SPACES, so every ``INSERT`` and ``UPDATE`` stores ``TRIM("")`` - the empty
  string - into ``SALES-STATS-DATE char(4)`` and
  ``SALES-PARTIAL-SHIP-FLAG char(1)``. The record's own values never reach the
  database.
* ON READ, the fetch fills both host variables and nothing copies them back, so
  after ``initialize WS-Sales-Record`` [:L1256] the caller sees
  ``Sales-Stats-Date`` zero and ``Sales-Partial-Ship-Flag`` space. The stored
  values never reach the caller.

Both fields were added to the copybook late - ``Sales-Stats-Date`` on 15/01/18
and ``Sales-Partial-Ship-Flag`` on 06/02/24 [copybooks/wssl.cob:L64-L66] - and
the two paragraphs were never extended. The generated data dictionary agrees
independently: ordinals 36 and 37 are the only two entries whose host variable
reports neither ``loaded_from_record`` nor ``unloaded_to_record``. See
:data:`UNLOADED_COLUMNS`.

**N-addrconcat - a two-field group flattened into one column.**
``Sales-Address`` is a group of ``Sales-Addr1 pic x(48)`` and
``Sales-Addr2 pic x(48)`` [copybooks/wssl.cob:L18-L20]; the bridge declares one
``HV-SALES-ADDRESS PIC X(96)`` [common/salesMT.cbl:L287] and moves the whole
group into it [:L1207]; the schema has one ``SALES-ADDRESS char(96)``. The two
sub-fields survive only inside the concatenation and have no column of their
own - recorded in :data:`OMITTED_COPYBOOK_FIELDS`.

**N-nametrunc - a name truncated by three characters.** ``Sales-Create-Date``
[copybooks/wssl.cob:L53] becomes ``HV-SALES-CREATE-DAT``
[common/salesMT.cbl:L312], moved at [:L1232], and the column is
``SALES-CREATE-DAT``. The same three-character pattern as ``Post-Date`` ->
``POST-DAT`` in ``glpostingMT`` and ``WS-IRS-Post-Date`` -> ``IRS-POST-DAT`` in
``slpostingMT``. Handled by the dictionary-driven name map, never by hand.

**N-numtochar - a numeric field stored as characters.**
``Sales-Stats-Date pic 9(4)`` [copybooks/wssl.cob:L64] becomes
``HV-SALES-STATS-DATE PIC X(4)`` [common/salesMT.cbl:L320] and
``SALES-STATS-DATE char(4)``. It is rendered as characters, never as an integer.
Its own load is absent, so N-2fields-lost decides what is actually stored.

**N-initialize - two initialisation semantics in one bridge, and the ``with
filler`` form appears twice.** ``initialize WS-Sales-Record with filler``
[common/salesMT.cbl:L619] inside ``ba041-Reread``'s errno branch and again
[:L1142] inside ``ba141-Reread``'s, against a plain ``initialize
WS-Sales-Record`` [:L1256] at the head of ``bb100-UnloadHVs``. Not normalised;
each is reproduced at its own site.

**N-when31 - two function codes share one handler branch but NOT one bridge
branch.** The handler collapses 3 and 31 into ``aa040-Process-Read-Next``
[common/acas012.cbl:L341-L343]; the bridge SEPARATES them, 3 to ``ba040`` and 31
to ``ba140-Process-Read-Next`` [common/salesMT.cbl:L995-L1070]. ``ba140`` is
"Like 040 except we do order by SALES-NAME" [:L997] and drives a SECOND cursor
flag ``Most-Cursor-Set-2`` [:L252-L254]. So on the flat-file path code 31
degrades to a plain ``read next``, while on the RDB path it is a
name-ordered scan. Both reproduced.

**N-cursor2-leak - NEW. The second cursor is never freed.** ``ba998-Free``
resets only the primary flag, ``set Cursor-Not-Active to true``
[common/salesMT.cbl:L1184], and ``ba030-Process-Close`` tests only
``if Cursor-Active`` [:L461]. A read-by-name result set therefore survives
``ba998-Free`` and ``Cursor-Active-2`` survives a close.

**N-start-stale and N-delete-stale - NEW. Two verbs can return a stale
status.** ``ba010-Initialise``'s ``move zero to We-Error`` and ``move zero to
Fs-Reply`` are COMMENTED OUT [common/salesMT.cbl:L374-L375], so nothing clears
those fields on entry. In ``ba060-Process-Start``, when the statement matches no
row AND ``MySQL_errno`` is ``"0  "``, the inner ``if`` never fires and NEITHER
status field is written [:L841-L852]. In ``ba080-Process-Delete``, when the
affected-row count is not 1 AND errno is ``"0  "`` - deleting a row that is not
there - the same thing happens [:L931-L942]. Both callers see whatever the
previous call left behind.

**N-998 - one code, three meanings, and the handler contradicts its own
header.** ``WE-Error 998`` is documented "File-Key-No Out Of Range - not 1"
[common/acas012.cbl:L168] and used that way in the key guard [:L300] and in
``aa050`` [:L484]; then ``aa060-Process-Start`` reuses it for "998 Invalid
calling parameter settings" [:L500]. Worse, that site sets NO ``FS-Reply``,
contradicting the header's own rule that a starred code implies ``FS-Reply``
99 [:L189]; the handler's header even documents ``997 = Access-Type wrong (< 5
or > 8)`` [:L169], which is what the BRIDGE uses for the identical test -
``move 99 to FS-Reply`` / ``move 997 to WE-Error``
[common/salesMT.cbl:L765-L768]. Both sides reproduced as written.

**N-accesstype9 - a legal access type both guards reject.** ``fn-not-greater-
than`` (9) was "Activated ... (for Stock file)" [copybooks/wsfnctn.cob:L20] and
is declared [:L117], but both START guards test ``< 5 or > 8``, so 9 is refused -
which makes the bridge's own ``when 9 ... "<= "`` branch
[common/salesMT.cbl:L794-L795] dead code. Reproduced, with the dead branch left
in place as data.

**N-badfn-divergence - the same failure, two different codes.**
``aa100-Bad-Function`` sets ``WE-Error`` 999 [common/acas012.cbl:L575];
``ba100-Bad-Function`` sets 990 [common/salesMT.cbl:L1166]. Both keep
``FS-Reply`` 99.

**N-guard - the guarded function set differs per handler and must not be
unified.** ``acas012`` guards 4 and 9 to ``WE-Error`` 998 and 8 to 996
[common/acas012.cbl:L296-L308]; ``acas000`` guards 4, 5 and 7. Also: the 996
comment [:L306] is a copy-paste of the 998 comment [:L300]. And because the
facade forces ``File-Key-No`` to 1 before every call
[copybooks/Proc-ACAS-FH-Calls.cob:L83], this guard is unreachable through the
facade - reproduced anyway, for a caller that reaches the handler directly.

**N-openoutput - a FOURTH Open-Output variant.** ``acas000``-family handlers
show three shapes; ``acas012`` shows a fourth: NO Open-Output special case at
all. The RDB fan-out is one unconditional bridge call with the function
uncoerced [common/acas012.cbl:L314-L318]; the flat-file path is a bare
``open output Sales-File`` whose comment says "caller should check fs-reply"
[:L383]; and ``ba020-Process-Open`` only connects and zeroes the cursor flag
[common/salesMT.cbl:L416-L458]. Opening for output does NOT delete every row
here, unlike ``acas008``.

**N-log - the log identity, and a copy-pasted file number.**
``move 3 to WS-Log-System`` and ``move 11 to WS-Log-File-No``
[common/acas012.cbl:L291-L292], then ``move 21 to WS-Log-File-no`` on the RDB
path [:L604]. 11 is the STOCK CONTROL file - ``copy "file11.cob"  *>
"stockctl"`` [copybooks/wsnames.cob] - while this handler's own ``SELECT``
assigns ``file-12``, "salesled" [copybooks/selsl.cob]. The number is inherited
from ``acas011``, from which the changelog says this program was created
[:L135]. The ``L291`` comment is also missing the comma after ``5=Stock`` that
its siblings carry.

**N-provenance - the header describes a different program.**
[common/acas012.cbl:L28-L31] says the module was written "specifically for stock
control" and [:L59-L61] explains the ``acas011``/file-11 naming; both are
copy-pasted. The changelog then says "acas012 created from acas011 source"
[:L135] and, four lines later, "Taken from acas22" [:L138]. Entry ".09 Chgd Vars
A & B to pic 999" [:L143] never happened - they are ``pic 9(4)``
[:L251-L252].

**N-emptypara - a paragraph named for a test it does not contain.**
``ba010-Test-WS-Rec-Size`` [common/acas012.cbl:L598] holds one statement,
``move 21 to WS-Log-File-no`` [:L604]; the record-size test its name and its
header comment describe lives in ``ba012-Test-WS-Rec-Size-2`` [:L606].

**N-evalname - the same paragraph, two names.** ``aa045-Eval-Keys`` here
[common/acas012.cbl:L447]; ``aa047-Eval-Keys`` in ``acas005``. And its own
preceding comment doubts it: "The next block will never get executed unless
performed so is it needed ?" [:L445].

**N-stopliteral - an operator pause in a batch handler.**
``stop "Cobol File EOF"`` [common/acas012.cbl:L425], marked "for testing".
Agent Action Plan 0.3.4 drops a pause with no database effect; the ``go to
aa999-main-exit`` that follows it is preserved.

**N-close-double-log - close logs twice.** ``aa030-Process-Close`` spaces
``WS-File-Key`` [common/acas012.cbl:L402], closes, then sets "CLOSE Sales Ledger
File" AFTER the close [:L406], then ``perform aa999-main-exit`` - a PERFORM, not
a ``go to`` - which logs once when testing [:L407], then zeroes the two function
fields and performs ``Ca-Process-Logs`` again, unconditionally [:L408-L410].

**N-logkey-render - one key, two renderings.** ``ba041-Reread`` moves
``HV-Sales-Key`` straight into ``WS-File-Key`` [common/salesMT.cbl:L635];
``ba050-Process-Read-Indexed`` routes the same value through ``ws-temp-ed``,
which is ``pic 9(10)`` [:L220], and then into ``WS-File-Key``
[:L756-L757] - a character key coerced through a ten-digit numeric field.

**N-lowkey-quoting - the low key is quoted on one path and not the other.**
``ba040`` emits ``'"0000000"'`` [common/salesMT.cbl:L491], a quoted string;
``ba140`` emits ``"0000000"`` [:L1014], which reaches MySQL UNQUOTED and is
parsed as the integer zero, turning a string comparison into a numeric one
against a ``char(7)`` column. Reproduced: see
:func:`ba140_process_read_next`.

**N-eof3-stale - a successfully fetched row is thrown away because the
CALLER's status field was never cleared.** Both reread paragraphs test
``if fs-reply = 10`` AFTER the fetch has already succeeded and, on a hit, set
the cursor inactive, move ``"EOF3"`` to ``WS-File-Key`` and jump to
``ba999-End`` - primary path [common/salesMT.cbl:L628-L632], by-name path
[:L1151-L1155]. The test is only reachable because ``ba010-Initialise`` has its
status clears **commented out** - ``*> move zero to We-Error`` /
``*> Fs-Reply.`` [:L374-L375] - so ``FS-Reply`` still holds whatever the caller
passed in. CONFIRMED LIVE: a ``fn-Read-By-Name`` issued straight after a
``fn-Read-Next`` walk had reported EOF selected three rows
(``> 0 got cnt=0000000003 recs in NAME order``, cursor activated) and then
answered ``(10, 10)`` with ``WS-File-Key`` = ``"EOF3"``, returning nothing. A
caller that zeroes ``FS-Reply`` between calls never sees it; one that does not
silently loses a row. Reproduced in :func:`ba041_reread` and
:func:`ba141_reread`, never fixed.

**N-readindexed-23 - this bridge answers a missing key differently from
``glpostingMT``.** ``ba050`` sets ``move 23 to fs-Reply  *> could also be 21 or
14`` and ``move zero to WE-Error`` [common/salesMT.cbl:L680-L683], where
``glpostingMT`` sets 21 and leaves ``We-Error`` untouched
[common/glpostingMT.cbl:L633-L636]. Because
:mod:`acas_posting.dal.cursor_state` reproduces the ``glpostingMT`` form, this
module implements ``ba050`` itself rather than delegating - delegating would
change the observable status and so "fix" the divergence.

**N-kortype - a key attribute declared and documented unused.**
``KOR-Type pic XXX. *> Not used currently`` [common/salesMT.cbl:L238], yet the
value differs per bridge - ``"STR"`` here [:L231], ``"BNT"`` in ``slpostingMT``.
Carried as data in :data:`KEY_TABLE`, never acted on.

**N-recsize-unreachable - a guard that cannot fire.**
``ba012-Test-WS-Rec-Size-2`` compares ``function Length(WS-Sales-Record)``
against ``function length(Sales-Record)`` and raises ``WE-Error`` 901 when the
first is smaller [common/acas012.cbl:L606-L620]. ``copybooks/wssl.cob`` and
``copybooks/fdsl.cob`` are field-for-field identical, both 300 bytes, so the
comparison is always equal. Reproduced, and its unreachability recorded.


WHAT IS DELIBERATELY NOT REPRODUCED
===================================

Agent Action Plan 0.1.1 excludes three categories, and 0.3.4 gives the rule for
display and accept statements entangled with logic. Applied here:

* Screen output with no database effect becomes a log record: the ``display
  Display-Blk at 2301`` / ``display SL901 at 2401`` pair on the record-size
  path [common/acas012.cbl:L617-L618] and every ``display Display-Message-1``
  in the bridge.
* The ``accept Accept-Reply at 2433`` that only blocks a terminal
  [common/acas012.cbl:L621] is dropped; the ``go to ba-rdbms-exit`` that
  follows it [:L622] is preserved.
* ``stop "Cobol File EOF"`` [common/acas012.cbl:L425] - see N-stopliteral.
* The eight ``88``-level condition names of ``copybooks/wssl.cob`` -
  ``Customer-Live``, ``Customer-Dead``, ``Late-Charges``, ``Dunning-Letters``,
  ``Email-Invoicing``, ``Email-Statementing``, ``Email-Dunning`` and
  ``Sales-BO-Set`` - belong to
  :mod:`acas_posting.records.sales_ledger` and are NOT redeclared here. (The
  agent brief says nine; the copybook declares eight, and the record module
  publishes eight across seven fields.)
* The whole flat-file ISAM path - ``open``/``read``/``start``/``write``/
  ``rewrite``/``delete`` against ``Sales-File`` - has no Python counterpart
  that touches a file: only the RDB path reaches storage, because Agent Action
  Plan 0.2.1.1 puts the MySQL bridge in scope and the indexed files out of it.
  The handler paragraphs that own those verbs are still present, still named,
  and still set the statuses the frozen source sets, so the dispatch and status
  protocol are complete; what they do not do is create a ``.dat`` file.

Copybook fields with no host variable and no column, each recorded as a
deliberate omission in :data:`OMITTED_COPYBOOK_FIELDS`: ``Sales-Addr1`` and
``Sales-Addr2`` (inside the concatenation); ``filler pic xxx``
[copybooks/wssl.cob:L40]; the ``filler redefines Quarters`` /
``STurnover-Q ... occurs 4`` pair [:L61-L62], which is the same storage as
``Turnover-Q1`` through ``Q4`` and correctly not duplicated; ``filler pic x(5)``
[:L68]; and the three commented-out ``redefines`` lines [:L14-L16].


RULE COMPLIANCE
===============

There is no user rules document for this project - ``review_rules`` reports
"No user rules provided." The six binding rules are Agent Action Plan 0.7.2.

* **R-1, no COBOL at runtime.** No ``subprocess``, ``ctypes``, ``cffi``,
  ``os.system``, ``os.popen``, ``os.exec*``, ``cobc``, ``cobcrun`` or
  ``cobmysqlapi``, and no import of ``harness``. Every COBOL construct is
  reimplemented natively.
* **R-2, zero binary floating point.** The eight ``decimal`` columns are
  :class:`decimal.Decimal`; the eleven ``binary-short``/``binary-long``
  statistics fields are :class:`int`, which is what keeps the integer
  truncation of the moving-average defect reproducible three programs away in
  ``sl060``, ``sl100``, ``pl060`` and ``pl100`` [copybooks/wssl.cob:L46-L52].
  No ``float``, no ``complex``, no ``round()``, no ``math``, and no
  ``Decimal`` ever built from a ``float``.
* **R-3, no new validations, fields, schema or concurrency.** Only
  ``SELECT``, ``INSERT``, ``UPDATE`` and ``DELETE``; no DDL, no migration
  tool, no ORM entity layer, no threads, no ``asyncio``, no
  ``multiprocessing``, no pooling.
* **R-4, anomalies reproduced.** See above; each site carries its locator.
* **R-5, full traceability.** One Python function per COBOL paragraph, named
  after it and carrying its locator. Every field is driven from the generated
  data dictionary, per Agent Action Plan 0.8.1: "Data dictionary first. ... This
  ordering is a directive, not a preference - it is what prevents fields being
  transcribed by eye." Nothing in this module enumerates the 37 columns by
  hand; :data:`COLUMN_ORDER` and every derived table come from
  :func:`acas_posting.dictionary.loader.entries_for_table`, in the
  ``mysql/ACASDB.sql`` ordinal order, and :func:`citations` publishes
  ``loader.cite`` for every one of them.
* **R-6, compiled behaviour decides, and runs are deterministic.** Statement
  order is the COBOL's. No clock, no randomness, no sleep. The two measured
  resolutions above came from the compiled oracle.

Layering, per Agent Action Plan 0.4.3: this module imports
``dal.connection``, ``dal.status``, ``dal.cursor_state``, one ``records``
module per linkage parameter and ``dictionary.loader``. It imports no other
``dal.acas*``, no ``dal.facade``, no ``programs``, no ``cli``, no ``harness``
and - deliberately - nothing from ``acas_posting.cobol``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from dataclasses import fields as dataclass_fields
from decimal import ROUND_DOWN, Decimal
from types import MappingProxyType
from typing import Any, Final, cast

from acas_posting.dal.connection import (
    OpenOutcome,
    TransportSecurity,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
)
from acas_posting.dal import cursor_state as _cursor_state
from acas_posting.dal.cursor_state import (
    EXTRA_READ_ORDERS,
    SEQUENTIAL_READ_START,
    TABLE_OF_KEYNAMES,
    CursorOutcome,
    CursorSlot,
    CursorState,
    CursorStateTable,
    DatabaseCursor,
    ExtraReadOrder,
    KeyOfReference,
    OrderQuoting,
    SequentialReadStart,
    key_of_reference,
)
# `Mysql-1100-Db-Error` and its per-operation `We-Error` override are
# DELIBERATELY NOT IMPORTED, and the omission is recorded here because R-5
# requires omissions to be visible rather than silent. `salesMT` contains no
# `perform Mysql-1100-Db-Error` at all: it writes its own codes inline at every
# failure site - 990 [common/salesMT.cbl:L740], 989 [:L748], 997 [:L767], 995
# [:L940], 994 [:L986], 10 [:L1166] - whereas `glpostingMT`, which those two
# helpers were written from, funnels everything through the generic paragraph and
# then corrects it. Importing them here would graft another bridge's control flow
# onto this one and collapse a distinction the frozen sources make, which is the
# same harmonisation the Agent Action Plan forbids for the differing key guards.
from acas_posting.dal.status import (
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    FileFunction,
    FsReply,
    LogSystem,
    SqlState,
    WeError,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    sanitise_for_log,
    start_access_type_is_valid,
)
from acas_posting.dictionary import loader as _loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.sales_ledger import (
    BRIDGE_PROGRAM,
    COPYBOOK_FILE,
    COPYBOOK_RECORD,
    DICTIONARY_KEYS,
    ENTITY_FACADE,
    FILE_HANDLER,
    MYSQL_TABLE,
    WsSalesRecord,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

_LOG: Final[logging.Logger] = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. IDENTITY
#
# Everything a reader needs to locate this module's two frozen originals, and
# everything the log record carries. Nothing here is computed; every value is
# transcribed from a cited line.
# ---------------------------------------------------------------------------

#: ``Program-Id. acas012.`` [common/acas012.cbl:L12]; re-exported from the record
#: module so the handler name is stated once in the migration.
HANDLER: Final[str] = FILE_HANDLER

#: ``program-id. salesMT`` [common/salesMT.cbl:L10].
BRIDGE: Final[str] = BRIDGE_PROGRAM

#: ``TABLE=SALEDGER-REC,HV`` [common/salesMT.cbl:L278-L279].
TABLE_NAME: Final[str] = MYSQL_TABLE

#: The Sales entity facade [copybooks/Proc-ACAS-FH-Calls.cob:L652].
FACADE: Final[str] = ENTITY_FACADE

#: The record layout, ``01 WS-Sales-Record`` in ``copybooks/wssl.cob:L12``.
RECORD_COPYBOOK: Final[str] = COPYBOOK_FILE
RECORD_GROUP: Final[str] = COPYBOOK_RECORD

#: ``77 prog-name pic x(17) value "acas012 (3.3.00)"`` [common/acas012.cbl:L248].
PROG_NAME: Final[str] = "acas012 (3.3.00)"

#: ``77 prog-name pic x(17) value "SalesMT (3.3.00)"`` [common/salesMT.cbl:L206].
#: Capital ``S``, where the program-id is lower case - transcribed as written.
BRIDGE_PROG_NAME: Final[str] = "SalesMT (3.3.00)"

#: ``/MYSQL VAR\ BASE=ACASDB TABLE=SALEDGER-REC,HV``
#: [common/salesMT.cbl:L276-L279]; uncommented in the ``.scb`` source at the
#: same lines [common/salesMT.scb:L276-L279].
BRIDGE_DIRECTIVE_LOCATOR: Final[str] = "[common/salesMT.cbl:L276-L279]"

#: ``01 TD-SALEDGER-REC`` - the host-variable group
#: [common/salesMT.cbl:L284-L321], preceded by its result pointer
#: ``01 TP-SALEDGER-REC USAGE POINTER`` [:L283].
HOST_VARIABLE_GROUP: Final[str] = "TD-SALEDGER-REC"
HOST_VARIABLE_GROUP_LOCATOR: Final[str] = "[common/salesMT.cbl:L283-L321]"

#: ``move 3 to WS-Log-System`` [common/acas012.cbl:L291]. The comment there
#: reads ``*> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock used in FH logging`` and is
#: missing the comma after ``5=Stock`` that the sibling handlers carry - see
#: anomaly N-log.
LOG_SYSTEM: Final[LogSystem] = LogSystem.SL

#: ``move 11 to WS-Log-File-No`` [common/acas012.cbl:L292] - the number this
#: handler sets FIRST. 11 is ``copy "file11.cob"  *> "stockctl"``
#: [copybooks/wsnames.cob], not the Sales Ledger, which is ``file-12``
#: [copybooks/file12.cob] and is what this handler's own ``SELECT`` assigns
#: [copybooks/selsl.cob]. Inherited from ``acas011`` - see anomaly N-provenance.
LOG_FILE_NO_COBOL: Final[int] = 11

#: ``move 21 to WS-Log-File-no.  *> for FHlogger`` [common/acas012.cbl:L604],
#: reached on the RDB path only and overwriting the 11 above. Same 11 -> 21 pair
#: as ``acas005``, because the number is scoped WITHIN the subsystem.
LOG_FILE_NO_RDB: Final[int] = 21

#: ``05 WS-File-Key pic x(64) value spaces`` [copybooks/wsfnctn.cob:L52]. Every
#: log tag this module writes is truncated to this width, as a COBOL ``MOVE``
#: into the field would truncate it.
WS_FILE_KEY_WIDTH: Final[int] = 64

#: ``05 WS-Log-Where pic x(231)`` [copybooks/wsfnctn.cob:L53].
WS_LOG_WHERE_WIDTH: Final[int] = 231

#: ``select Sales-File assign file-12`` [copybooks/selsl.cob], resolved through
#: ``File-Defs.file-defs-a.file-12`` = ``"salesled.dat"``
#: [copybooks/file12.cob].
FLAT_FILE_DEFS_MEMBER: Final[str] = "file_12"

#: ``fd Sales-File. 01 Sales-Record.`` [copybooks/fdsl.cob] - field-for-field
#: identical to ``WS-Sales-Record``; both copybook headers state "rec size 300
#: bytes". These two numbers are what ``ba012-Test-WS-Rec-Size-2`` compares, and
#: their equality is why the 901 path is unreachable - anomaly
#: N-recsize-unreachable.
WS_SALES_RECORD_BYTES: Final[int] = 300
SALES_RECORD_BYTES: Final[int] = 300

#: ``move NNN to WS-No-Paragraph`` in the HANDLER, one per verb
#: [common/acas012.cbl:L364, :L401, :L414, :L466, :L489, :L538, :L549, :L560].
WS_NO_PARAGRAPH_HANDLER: Final[Mapping[str, int]] = MappingProxyType(
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

#: ``move N to ws-No-Paragraph`` in the BRIDGE - a different, unrelated
#: numbering [common/salesMT.cbl:L437, :L463, :L505, :L1077, :L1030, :L554,
#: :L684, :L691, :L788, :L874, :L918, :L963, :L1175].
WS_NO_PARAGRAPH_BRIDGE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ba020-Process-Open": 1,
        "ba030-Process-Close": 2,
        "ba040-Process-Read-Next": 3,
        "ba041-Reread": 4,
        "ba050-Process-Read-Indexed": 5,
        "ba050-Fetch": 6,
        "ba060-Process-Start": 8,
        "ba070-Process-Write": 10,
        "ba080-Process-Delete": 13,
        "ba090-Process-Rewrite": 17,
        "ba998-Free": 20,
        "ba140-Process-Read-Next": 21,
        "ba141-Reread": 22,
    }
)

#: The nine ``File-Function`` codes ``evaluate File-Function`` accepts
#: [common/acas012.cbl:L336-L356], in the order the ``when`` clauses appear.
#: ``READ_NEXT`` and ``READ_BY_NAME`` share one branch - anomaly N-when31 - and
#: ``DELETE_ALL`` (6) is absent: ``*> 6 is spare / unused`` [:L354].
SUPPORTED_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    FileFunction.OPEN,
    FileFunction.CLOSE,
    FileFunction.READ_NEXT,
    FileFunction.READ_BY_NAME,
    FileFunction.READ_INDEXED,
    FileFunction.WRITE,
    FileFunction.RE_WRITE,
    FileFunction.DELETE,
    FileFunction.START,
)

#: The key guard [common/acas012.cbl:L296-L308]: each of these three functions
#: is refused with ``FS-Reply`` 99 when ``File-Key-No not = 1``, and the two
#: ``WE-Error`` codes differ. ``acas000`` guards a DIFFERENT set (4, 5, 7); the
#: two must not be unified - anomaly N-guard. The 996 comment [:L306] is a
#: copy-paste of the 998 comment [:L300].
GUARDED_KEY_FUNCTIONS: Final[Mapping[FileFunction, WeError]] = MappingProxyType(
    {
        FileFunction.READ_INDEXED: WeError.FILE_KEY_NO_OUT_OF_RANGE,
        FileFunction.START: WeError.FILE_KEY_NO_OUT_OF_RANGE,
        FileFunction.DELETE: WeError.DELETE_KEY_OUT_OF_RANGE,
    }
)

#: ``move 1 to File-Key-No`` [copybooks/Proc-ACAS-FH-Calls.cob:L83] - the only
#: key number the facade ever passes, and the only one ``aa045-Eval-Keys``
#: recognises [common/acas012.cbl:L451-L457].
ONLY_FILE_KEY_NO: Final[int] = 1

#: The eleven published Sales facade verbs and the ``(File-Function,
#: Access-Type)`` pair each sets [copybooks/Proc-ACAS-FH-Calls.cob:L652-L707].
#: ``Sales-Start`` is the ONLY one that does not ``move zero to Access-Type``
#: first [:L680-L682], which is why 5..9 survives into ``aa060`` and IS the
#: START relation; its Access-Type is therefore recorded as ``None``, meaning
#: "whatever the caller set". There is no ``-Open-Extend`` and no
#: ``-Delete-All`` verb.
FACADE_VERBS: Final[Mapping[str, tuple[FileFunction, AccessType | None]]] = (
    MappingProxyType(
        {
            "Sales-Open": (FileFunction.OPEN, AccessType.I_O),
            "Sales-Open-Input": (FileFunction.OPEN, AccessType.INPUT),
            "Sales-Open-Output": (FileFunction.OPEN, AccessType.OUTPUT),
            "Sales-Close": (FileFunction.CLOSE, None),
            "Sales-Delete": (FileFunction.DELETE, None),
            "Sales-Start": (FileFunction.START, None),
            "Sales-Read-Next": (FileFunction.READ_NEXT, None),
            "Sales-Read-Next-Sorted-By-Name": (FileFunction.READ_BY_NAME, None),
            "Sales-Read-Indexed": (FileFunction.READ_INDEXED, None),
            "Sales-Write": (FileFunction.WRITE, None),
            "Sales-Rewrite": (FileFunction.RE_WRITE, None),
        }
    )
)


# ---------------------------------------------------------------------------
# 2. THE THIRTY-SEVEN COLUMNS - DRIVEN FROM THE DATA DICTIONARY, NEVER BY HAND
#
# Agent Action Plan 0.8.1: "Data dictionary first. ... This ordering is a
# directive, not a preference - it is what prevents fields being transcribed by
# eye." Thirty-seven columns is well past the point of safe hand-transcription,
# so every table below is derived at import time from
# `dictionary.loader.entries_for_table`, which returns the entries in
# `mysql/ACASDB.sql` COLUMN-ORDINAL order, and from the record module's own
# `DICTIONARY_KEYS` map. Nothing here is a literal list of column names.
# ---------------------------------------------------------------------------

_ENTRIES: Final[tuple[_loader.DictionaryEntry, ...]] = tuple(
    _loader.entries_for_table(TABLE_NAME)
)

#: Every ``SALEDGER-REC`` dictionary entry, keyed by column name, in
#: ``mysql/ACASDB.sql`` ordinal order. The single source for every conversion
#: this module performs.
ENTRIES: Final[Mapping[str, _loader.DictionaryEntry]] = MappingProxyType(
    {entry.column.name: entry for entry in _ENTRIES}
)

#: The 37 column names in ordinal order - the order ``bb200-Insert``
#: [common/salesMT.cbl:L1297-L1775], ``bb300-Update`` [:L1777-L2259] and the
#: ``CREATE TABLE`` [mysql/ACASDB.sql:L945-L985] all agree on. Verified: all
#: three sequences are identical.
COLUMN_ORDER: Final[tuple[str, ...]] = tuple(ENTRIES)

#: ``PRIMARY KEY (`SALES-KEY`)`` [mysql/ACASDB.sql:L983], taken from the
#: dictionary's own table record rather than restated.
PRIMARY_KEY_COLUMN: Final[str] = _loader.table_for(TABLE_NAME).primary_key

#: Column name -> the dotted ``WsSalesRecord`` attribute path that holds it,
#: inverted from :data:`~acas_posting.records.sales_ledger.DICTIONARY_KEYS`.
#: Includes the nested ``quarters.turnover_q1`` form and the group
#: ``sales_address``; excludes every copybook-only key, which is what
#: :data:`OMITTED_COPYBOOK_FIELDS` collects instead.
RECORD_ATTRIBUTE_FOR_COLUMN: Final[Mapping[str, str]] = MappingProxyType(
    {
        key.split(".", 1)[1]: attribute
        for attribute, key in DICTIONARY_KEYS.items()
        if key.startswith(f"{TABLE_NAME}.")
    }
)

#: The copybook fields of ``WS-Sales-Record`` that reach neither a host variable
#: nor a column, each with why. Rule R-5: "Deliberate omissions are recorded as
#: omissions." Keyed by the record attribute path so a reader can find them.
OMITTED_COPYBOOK_FIELDS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "sales_address.sales_addr1": (
            "inside the N-addrconcat group concatenation - moved as part of "
            "Sales-Address [common/salesMT.cbl:L1207] into one X(96) host "
            "variable [:L287] and one char(96) column; no column of its own "
            "[copybooks/wssl.cob:L19]"
        ),
        "sales_address.sales_addr2": (
            "inside the N-addrconcat group concatenation, as above "
            "[copybooks/wssl.cob:L20]"
        ),
        "filler_l40": (
            "filler pic xxx, three bytes of alignment padding with no host "
            "variable and no column [copybooks/wssl.cob:L40]"
        ),
        "quarters_view": (
            "filler redefines Quarters - the same storage as TURNOVER-Q1 "
            "through Q4 under a second name, correctly not duplicated as "
            "columns [copybooks/wssl.cob:L61]"
        ),
        "quarters_view.sturnover_q": (
            "STurnover-Q pic s9(8)v99 comp-3 occurs 4 - the subscripted view "
            "of the same four quarters [copybooks/wssl.cob:L62]"
        ),
        "filler_l68": (
            "filler pic x(5), the trailing five bytes that bring the record to "
            "its declared 300 [copybooks/wssl.cob:L68]"
        ),
    }
)

#: The three commented-out lines of ``copybooks/wssl.cob`` - a ``redefines`` of
#: the key into a six-element array plus a check digit. Never compiled, so never
#: migrated; recorded so a reader comparing the two files is not surprised.
COMMENTED_OUT_COPYBOOK_LINES: Final[str] = (
    "filler redefines WS-Sales-Key / Array-K pic x occurs 6 / Check-Digit "
    "pic 9 [copybooks/wssl.cob:L14-L16]"
)


def _columns_where(predicate: Any) -> tuple[str, ...]:
    """Select column names in ordinal order by a predicate on their entry.

    The one place this module turns dictionary metadata into a column set, so
    that every set below is demonstrably derived rather than typed out.

    Args:
        predicate: Called with each :class:`~acas_posting.dictionary.loader.\
DictionaryEntry` in ordinal order; truthy selects the column.

    Returns:
        The selected column names, in ``mysql/ACASDB.sql`` ordinal order.
    """
    return tuple(name for name, entry in ENTRIES.items() if predicate(entry))


#: **ANOMALY A-11.** The eleven columns whose copybook field is SIGNED and whose
#: bridge host variable is UNSIGNED - ``copybooks/wssl.cob:L43-L53`` against
#: ``common/salesMT.cbl:L302-L312``. Derived from the declarations themselves,
#: not from the anomaly reference, so the set cannot drift from the source; the
#: dictionary's own ``anomaly_refs`` agree exactly, and so does its
#: ``ambiguity_refs`` tag ``Q-3``, which is asserted below.
SIGN_LOSS_COLUMNS: Final[tuple[str, ...]] = _columns_where(
    lambda entry: (
        entry.copybook.signed and not entry.bridge_host_variable.signed
    )
)

#: The seven columns that are signed at ALL THREE layers and therefore keep
#: their sign through the host variable - ``s9(8)v99 comp-3`` ->
#: ``S9(08)V9(02) COMP`` [common/salesMT.cbl:L313-L319] -> signed
#: ``decimal(10,2)``. Agent Action Plan 0.6.2 uses this set against
#: :data:`SIGN_LOSS_COLUMNS` to prove the drift is "specific rather than
#: systemic". Their sign survives the host variable and is then dropped again by
#: the SQL rendering - anomaly N-signdrop, a different mechanism in a different
#: place.
MONEY_COLUMNS: Final[tuple[str, ...]] = _columns_where(
    lambda entry: entry.copybook.signed and entry.bridge_host_variable.signed
)

#: **ANOMALY N-2fields-lost.** The columns whose host variable is neither loaded
#: from the record before a write nor unloaded to it after a read -
#: ``SALES-STATS-DATE`` and ``SALES-PARTIAL-SHIP-FLAG``, absent from both
#: ``bb000-HV-Load`` [common/salesMT.cbl:L1196-L1239] and ``bb100-UnloadHVs``
#: [:L1256-L1292] while declared, fetched and written.
UNLOADED_COLUMNS: Final[tuple[str, ...]] = _columns_where(
    lambda entry: not (
        entry.bridge_host_variable.loaded_from_record
        or entry.bridge_host_variable.unloaded_to_record
    )
)

#: The 35 columns ``bb000-HV-Load`` and ``bb100-UnloadHVs`` DO move, in ordinal
#: order - the complement of :data:`UNLOADED_COLUMNS`.
LOADED_COLUMNS: Final[tuple[str, ...]] = tuple(
    name for name in COLUMN_ORDER if name not in UNLOADED_COLUMNS
)

#: The alphanumeric host variables - ``PIC X(n)`` [common/salesMT.cbl:L285-L291,
#: :L320-L321]. Rendered into SQL by ``FUNCTION TRIM (HV-xxx,TRAILING)``
#: [:L1315], so trailing spaces go and leading spaces stay.
CHARACTER_COLUMNS: Final[tuple[str, ...]] = _columns_where(
    lambda entry: entry.bridge_host_variable.character_length is not None
)

#: The numeric host variables - every ``COMP`` form [common/salesMT.cbl:L292-
#: L319]. Rendered through ``WS-MYSQL-EDIT`` - see
#: :func:`_render_numeric_for_sql`.
NUMERIC_COLUMNS: Final[tuple[str, ...]] = tuple(
    name for name in COLUMN_ORDER if name not in CHARACTER_COLUMNS
)

# The dictionary is authoritative and this module is built on it, so the three
# facts it is built on are asserted at import time rather than assumed. They are
# statements about the FROZEN SOURCE, which cannot change under us, so a failure
# here means the dictionary was regenerated from something else - which must
# stop the run rather than silently reshape every conversion below.
if len(COLUMN_ORDER) != 37:  # pragma: no cover - guards a frozen fact
    raise AssertionError(
        f"{TABLE_NAME} must have 37 columns [mysql/ACASDB.sql:L945-L985]; the "
        f"data dictionary reports {len(COLUMN_ORDER)}"
    )
if len(SIGN_LOSS_COLUMNS) != 11:  # pragma: no cover - guards a frozen fact
    raise AssertionError(
        "anomaly A-11 covers exactly 11 columns "
        "[copybooks/wssl.cob:L43-L53] -> [common/salesMT.cbl:L302-L312]; the "
        f"data dictionary reports {len(SIGN_LOSS_COLUMNS)}: "
        f"{SIGN_LOSS_COLUMNS}"
    )
if len(MONEY_COLUMNS) != 7:  # pragma: no cover - guards a frozen fact
    raise AssertionError(
        "exactly 7 columns are signed at all three layers "
        "[common/salesMT.cbl:L313-L319]; the data dictionary reports "
        f"{len(MONEY_COLUMNS)}: {MONEY_COLUMNS}"
    )


# Every one of the eleven A-11 columns must also carry the dictionary's own
# ambiguity tag Q-3, because Agent Action Plan 0.6.8 makes the stored value of a
# negative-through-unsigned a question the compiled oracle had to settle. If the
# two ever disagree, the dictionary and this module have drifted apart.
_A11_WITHOUT_Q3: Final[tuple[str, ...]] = tuple(
    name
    for name in SIGN_LOSS_COLUMNS
    if "Q-3" not in ENTRIES[name].ambiguity_refs
    or "A-11" not in ENTRIES[name].anomaly_refs
)
if _A11_WITHOUT_Q3:  # pragma: no cover - guards a frozen fact
    raise AssertionError(
        "every sign-loss column must carry both anomaly A-11 and ambiguity "
        f"Q-3 in the data dictionary; these do not: {_A11_WITHOUT_Q3}"
    )


def citations() -> tuple[str, ...]:
    """Publish the dictionary citation for all 37 columns, in ordinal order.

    Rule R-5 requires that every field cite its data-dictionary entry, and the
    agent brief directs that the citation come from
    :func:`acas_posting.dictionary.loader.cite` rather than being hand-written.
    Each line names the copybook field, the bridge host variable and the MySQL
    column with a locator for each, so the copybook-bridge-column triple behind
    every conversion in this module is inspectable from the module itself.

    Returns:
        One ``loader.cite`` line per column, in ``mysql/ACASDB.sql`` ordinal
        order. Deterministic: the same tuple in every process.
    """
    return tuple(_loader.cite(entry.key) for entry in _ENTRIES)


def drift_report() -> tuple[str, ...]:
    """Publish the copybook-to-bridge-to-column drift for all 37 columns.

    The full drift table of the module docstring, generated rather than
    transcribed, so it cannot fall out of step with the dictionary. Every
    conversion this module performs is taken from
    :func:`acas_posting.dictionary.loader.drift_for`, never inferred from a
    picture clause - which is the whole point of Agent Action Plan 0.8.1's "Data
    dictionary first" directive.

    Returns:
        One line per column, in ordinal order, naming the drift dimensions the
        dictionary reports and flagging the two anomaly sets by name.
    """
    lines: list[str] = []
    for entry in _ENTRIES:
        drift = _loader.drift_for(entry.key)
        dimensions = tuple(
            name
            for name in (
                "signedness",
                "usage",
                "digits",
                "scale",
                "character_length",
                "name",
            )
            if getattr(drift, name)
        )
        column = entry.column.name
        tags: list[str] = []
        if column in SIGN_LOSS_COLUMNS:
            tags.append("A-11 SIGN LOST AT THE BRIDGE")
        if column in MONEY_COLUMNS:
            tags.append("signed at all three layers; N-signdrop on render")
        if column in UNLOADED_COLUMNS:
            tags.append("N-2fields-lost: never loaded, never unloaded")
        lines.append(
            f"{entry.column.ordinal:2d} {column:<26} "
            f"{entry.copybook.name} {entry.copybook.picture or entry.copybook.usage}"
            f" -> {entry.bridge_host_variable.name} "
            f"{entry.bridge_host_variable.picture or ''}"
            f" -> {entry.column.sql_type}"
            f"  drift={','.join(dimensions) or 'none'}"
            + (f"  [{'; '.join(tags)}]" if tags else "")
        )
    return tuple(lines)


# ---------------------------------------------------------------------------
# 3. THE KEY TABLE - `01 Table-Of-Keynames` [common/salesMT.cbl:L228-L238]
#
# The bridge navigates with a substring of the WHOLE RECORD taken at a declared
# offset and length, not with a named field:
#
#     set      KOR-x1 to 1                *> 1 = Primary
#     move     KOR-offset (KOR-x1) to K
#     move     KOR-length (KOR-x1) to L
#     ... WS-Sales-Record (K:L) ...
#
# [common/salesMT.cbl:L645-L646, :L780-L781, :L898-L899, :L956-L957]. That is
# exactly what `dal/cursor_state.py` implements, so the metadata is taken from
# there rather than restated - which also means a `.scb` correction reaches this
# module without an edit.
# ---------------------------------------------------------------------------

#: ``03 keyOfReference occurs 1 indexed by KOR-x1``
#: [common/salesMT.cbl:L233-L238]. ONE key: ``'SALES-KEY'`` with the packed
#: literal ``'00010007'`` [:L230] giving offset 1, length 7, and
#: ``KOR-Type 'STR'`` [:L231] which the declaration itself calls unused -
#: anomaly N-kortype. Because there is only one, ``aa045-Eval-Keys`` has nothing
#: but ``File-Key-No = 1`` to discriminate, and asking
#: :func:`~acas_posting.dal.cursor_state.key_of_reference` for key 2 raises.
KEY_TABLE: Final[tuple[KeyOfReference, ...]] = TABLE_OF_KEYNAMES[TABLE_NAME]

#: The primary key of reference, ``KOR-x1 = 1``, the only one this bridge has.
PRIMARY_KEY_OF_REFERENCE: Final[KeyOfReference] = key_of_reference(
    TABLE_NAME, ONLY_FILE_KEY_NO
)

#: ``KOR-offset (1)`` -> ``K``: the 1-based start of the key inside the record.
KEY_OFFSET: Final[int] = PRIMARY_KEY_OF_REFERENCE.kor_offset

#: ``KOR-length (1)`` -> ``L``: the key's length in characters.
KEY_LENGTH: Final[int] = PRIMARY_KEY_OF_REFERENCE.kor_length

#: ``KOR-Type`` as declared - carried, never acted on. See anomaly N-kortype.
KEY_TYPE: Final[str] = PRIMARY_KEY_OF_REFERENCE.kor_type

#: ``ba040``'s hard-coded self-positioning relation and low key
#: [common/salesMT.cbl:L490-L491]: ``>=`` against the QUOTED literal
#: ``'"0000000"'``. Nine of the twenty in-scope bridges use ``>`` and eleven
#: ``>=``; this one is a ``>=``.
SEQUENTIAL_READ: Final[SequentialReadStart] = SEQUENTIAL_READ_START[TABLE_NAME]

#: ``ba140``'s read order - ``ORDER BY `SALES-NAME` ASC`` on a SECOND cursor
#: [common/salesMT.cbl:L1016-L1019], reached only by ``fn-Read-By-Name`` (31).
#: The ordering column is not indexed and its predicate is still on
#: ``SALES-KEY``, with the low key emitted UNQUOTED [:L1014] - anomaly
#: N-lowkey-quoting.
READ_BY_NAME_ORDER: Final[ExtraReadOrder] = EXTRA_READ_ORDERS[TABLE_NAME][
    FileFunction.READ_BY_NAME
]

#: ``ba140``'s low key exactly as the bridge emits it: the COBOL alphanumeric
#: literal ``"0000000"`` [common/salesMT.cbl:L1014] reaches the SQL text WITHOUT
#: quotes, so MySQL parses it as the INTEGER ZERO and compares a ``char(7)``
#: column numerically. Bound as :class:`int` for that reason - see
#: :func:`ba140_process_read_next`.
READ_BY_NAME_LOW_KEY: Final[int] = 0

#: ``ba140``'s low key as it appears in the COBOL literal and in the log tag
#: ``move "0000000" to WS-File-Key`` [common/salesMT.cbl:L1041].
READ_BY_NAME_LOW_KEY_TEXT: Final[str] = "0000000"

#: ``05 MOST-Relation pic xxx.  *> valid are >=, <=, <, >, =``
#: [common/salesMT.cbl:L248-L249]. Sourced from ``dal/cursor_state.py`` so the
#: relation vocabulary is stated once; ``Access-Type`` is passed through
#: UNMODIFIED because ``Sales-Start`` deliberately does not zero it
#: [copybooks/Proc-ACAS-FH-Calls.cob:L680-L682], so 5..9 IS the relation.
RELATION_FOR_ACCESS_TYPE: Final[Mapping[int, str]] = MappingProxyType(
    dict(_cursor_state.ACCESS_TYPE_TO_RELATION)
)

if READ_BY_NAME_ORDER.cursor_slot is not CursorSlot.SECONDARY:
    raise AssertionError(  # pragma: no cover - guards a frozen fact
        "fn-Read-By-Name must drive Most-Cursor-Set-2 "
        "[common/salesMT.cbl:L252-L254]; cursor_state reports "
        f"{READ_BY_NAME_ORDER.cursor_slot}"
    )


# ---------------------------------------------------------------------------
# 4. THE BRIDGE'S PROCESS-GLOBAL STATE
#
# `salesMT` receives no connection handle and no `System-Record`: its connection
# lives in the compiled C interface's globals, established by an earlier
# `MYSQL-1000-OPEN` [common/salesMT.cbl:L438] and torn down by
# `MYSQL-1980-CLOSE` [:L470], and its two cursor flags live in `DAL-Data`
# [:L244-L254], which is working storage, not linkage. One session object holds
# exactly those three things, so the Python module is stateful in the same places
# and only in those places.
#
# Rule R-3 forbids concurrency, and this design depends on that: a single
# process-global session is correct precisely because execution is strictly
# sequential, as it is in the single-threaded COBOL.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class BridgeSession:
    """The state ``salesMT`` keeps between calls.

    Attributes:
        system_record: The row ``ba012-Test-WS-Rec-Size-2`` read the credentials
            from [common/acas012.cbl:L637-L645]. The bridge itself never sees
            it; it is held here because
            :func:`~acas_posting.dal.connection.mysql_1000_open` owns the
            connect and takes the row. ``None`` until the handler has run once,
            which is the state in which the frozen ``RDB-Data`` block is still
            spaces and a connect would fail.
        connection: The live connection, or ``None`` before an open and after a
            close - the C interface's global connection id.
        cursors: ``DAL-Data``'s two cursor flags, ``Most-Cursor-Set`` and
            ``Most-Cursor-Set-2`` [common/salesMT.cbl:L250-L254], as the primary
            and secondary slots of one table. ONE table, because the frozen
            block is one block: freeing the primary must be visibly unable to
            reach the secondary, which is anomaly N-cursor2-leak.
        transport: How the connection may cross the network. Has no COBOL
            counterpart - transport policy is compiled into ``cobmysqlapi.c`` -
            so it is settable here, at the one place the connect happens.
        allow_frozen_placeholder_credentials: Passed through to the open.
            ``copybooks/wssystem.cob:L138-L139`` still ships ``"ACAS-User"`` and
            ``"PaSsWoRd"``, and the connection module refuses them unless the
            caller says the target is disposable.
        open_access_type: The ``Access-Type`` the last successful open used, kept
            for diagnostics only. It changes no status and no statement.
    """

    system_record: SystemRecord | None = None
    connection: Any | None = None
    cursors: CursorStateTable = field(default_factory=CursorStateTable)
    transport: TransportSecurity | None = None
    allow_frozen_placeholder_credentials: bool = False
    open_access_type: int = 0

    def is_open(self) -> bool:
        """Report whether a connection is established.

        Returns:
            ``True`` when :attr:`connection` holds a live connection.
        """
        return self.connection is not None

    def require_connection(self) -> Any:
        """Return the live connection, or refuse.

        The bridge has no equivalent test: it calls ``MySQL_query`` on whatever
        the global connection id holds, and a closed one fails inside the C
        interface, which ``Mysql-1100-Db-Error`` then reports as ``(99, 911)``
        [copybooks/mysql-procedures.cpy:L127-L128]. Callers here translate this
        exception into the same pair, so the observable status matches; the
        exception exists only so the mistake is not silent.

        Returns:
            The live connection.

        Raises:
            ConnectionError: If no open has succeeded, or a close has run.
        """
        if self.connection is None:
            raise ConnectionError(
                f"{BRIDGE} has no open connection: fn-open (File-Function 1) "
                f"must succeed before any other verb, exactly as "
                f"MYSQL-1000-OPEN must precede MySQL_query "
                f"[common/salesMT.cbl:L438]"
            )
        return self.connection


_SESSION: Final[BridgeSession] = BridgeSession()


def session() -> BridgeSession:
    """Return the module's single :class:`BridgeSession`.

    Returns:
        The process-global session - the Python counterpart of the C interface's
        global connection plus the bridge's ``DAL-Data`` block.
    """
    return _SESSION


def reset_session() -> None:
    """Discard every cursor and forget the connection, without closing it.

    Not a COBOL paragraph: it exists so a test or a harness scenario can start
    from the state a freshly loaded ``salesMT`` is in, which rule R-6's
    determinism requirement needs. It deliberately does NOT close the
    connection, because closing is ``ba030-Process-Close``'s job and stealing it
    here would make a close happen where the frozen source has none.
    """
    _SESSION.cursors.reset(TABLE_NAME)
    _SESSION.system_record = None
    _SESSION.connection = None
    _SESSION.open_access_type = 0
    _LOG.debug("%s session reset; no close was issued", BRIDGE)


@contextmanager
def _bridge_cursor(connection: Any) -> Iterator[DatabaseCursor]:
    """Yield a cursor for a statement the callee issues, and close it.

    :func:`~acas_posting.dal.connection.execute_statement` executes the
    statement itself, which suits every statement this module builds. The three
    verbs delegated to :mod:`acas_posting.dal.cursor_state` build and issue
    their own, so they need the cursor rather than the result - and they get the
    same lifecycle: one cursor, one statement, closed on every path.

    Args:
        connection: The live connection from :func:`BridgeSession.require_\
connection`.

    Yields:
        A cursor satisfying
        :class:`~acas_posting.dal.cursor_state.DatabaseCursor`.
    """
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        discard_unread = getattr(connection, "consume_results", None)
        if discard_unread is not None:
            try:
                discard_unread()
            except Exception as error:  # noqa: BLE001 - cleanup must not mask
                _LOG.debug("discarding the unread result reported %s", error)
        try:
            cursor.close()
        except Exception as error:  # noqa: BLE001 - cleanup must not mask
            _LOG.debug("closing the bridge cursor reported %s", error)



# ---------------------------------------------------------------------------
# 5. COBOL STORAGE SEMANTICS AT THE BRIDGE BOUNDARY
#
# These are the primitives that make the two sign-loss mechanisms reproducible.
# They live here rather than in `acas_posting/cobol/` because Agent Action Plan
# 0.4.3's import table forbids `dal` -> `cobol`, and because what they model is
# not the language in general but THIS bridge's boundary: the picture clause of a
# host variable and the edit field the generated SQL is rendered through. Both
# are read from the data dictionary, never from a literal picture string.
#
# Rule R-2 governs every line of this section: `Decimal` and `int` only, never
# `float`, and no `Decimal` ever constructed from a `float`.
# ---------------------------------------------------------------------------

#: ``77 WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` [common/salesMT.cbl:L216]. Its measured
#: character layout, from GnuCOBOL 3.2.0: position 1 the sign, positions 2..20
#: nineteen integer positions of which the first eighteen suppress leading zeros
#: to spaces, position 21 the decimal point, positions 22..30 nine fraction
#: digits. Total width 30, measured with ``function length``.
MYSQL_EDIT_PICTURE: Final[str] = "-Z(18)9.9(9)"
MYSQL_EDIT_WIDTH: Final[int] = 30
MYSQL_EDIT_SIGN_POSITION: Final[int] = 1
MYSQL_EDIT_INTEGER_POSITIONS: Final[int] = 19
MYSQL_EDIT_POINT_POSITION: Final[int] = 21
MYSQL_EDIT_FRACTION_POSITIONS: Final[int] = 9

#: The 1-based position one past the last integer digit of the edit field - the
#: end of every integer window the generated SQL takes. ``(11:10)``, ``(13:08)``,
#: ``(16:05)``, ``(18:03)`` and ``(19:02)`` all end here, which is why the window
#: for a host variable is derived as ``(21 - integer_digits : integer_digits)``.
MYSQL_EDIT_INTEGER_END: Final[int] = 21

#: The six integer windows that actually appear in ``salesMT``, verified by
#: enumerating every ``WS-MYSQL-EDIT(n:m)`` in the file: ``(11:10)`` 18 times,
#: ``(13:08)`` 14, ``(16:05)`` 4, ``(18:03)`` 18, ``(19:02)`` 2 and ``(22:02)``
#: 16. ``(1:`` appears NOWHERE - not in this bridge and not in any of the 28
#: frozen bridges - which is anomaly N-signdrop.
MYSQL_EDIT_WINDOWS_IN_USE: Final[tuple[str, ...]] = (
    "(11:10)",
    "(13:08)",
    "(16:05)",
    "(18:03)",
    "(19:02)",
    "(22:02)",
)


def _sign_loss_at_the_bridge(
    value: int,
    *,
    column: str,
) -> int:
    """**ANOMALY A-11.** Drop the sign of a signed binary field. THE ONE HELPER.

    Agent Action Plan 0.7.2 R-4 names this module as the reproduction site for
    this anomaly, and 0.6.2 states the requirement, verbatim: "the Python
    data-access layer must reproduce the bridge's conversion, NOT MERELY WRITE
    THE COMPUTED VALUE AND LET MYSQL COMPLAIN."

    ``copybooks/wssl.cob:L43-L53`` declares eleven fields ``binary-short`` or
    ``binary-long``, both SIGNED in COBOL, and annotates each with the unsigned
    equivalent the maintainer had in mind - ``*> 9999 comp`` on the two
    ``binary-short`` and ``*> 9(8) comp`` on the nine ``binary-long``. The bridge
    then receives each into ``PIC 9(05) COMP`` or ``PIC 9(10) COMP``, UNSIGNED
    [common/salesMT.cbl:L302-L312], by a plain ``MOVE``
    [:L1220-L1232]. A COBOL ``MOVE`` into an unsigned receiver stores the
    ABSOLUTE VALUE and truncates HIGH-ORDER digits that do not fit. The sign is
    therefore gone BEFORE any SQL text is built, and gone before the unsigned
    column is ever reached.

    MEASURED, NOT ASSUMED. Agent Action Plan 0.6.8 lists the resulting stored
    value as one of five questions the compiled oracle must settle. A probe
    reproducing the bridge's own declarations, compiled and run under GnuCOBOL
    3.2.0, gave::

        binary-long  -42          -> PIC 9(10) COMP = 0000000042
        binary-long  -1           -> PIC 9(10) COMP = 0000000001
        binary-long  -2147483648  -> PIC 9(10) COMP = 2147483648
        binary-long  +123456789   -> PIC 9(10) COMP = 0123456789
        binary-short -7           -> PIC 9(05) COMP = 00007
        binary-short -32768       -> PIC 9(05) COMP = 32768

    so the conversion is the decimal absolute value with high-order truncation -
    NOT a two's-complement reinterpretation, which would have made ``-42`` into
    ``4294967254``. Recorded as ambiguity ``Q-3`` in
    ``docs/migration/ambiguity-resolutions.md``.

    It does not raise, does not clamp to zero and does not reject: the loss is
    the specification, and rule R-4 makes reproducing it correct.

    Args:
        value: The record's value, an ``int`` because ``binary-short`` and
            ``binary-long`` are integers - see rule R-2 in the module docstring
            for why they are not ``Decimal``.
        column: The column being loaded. Must be one of
            :data:`SIGN_LOSS_COLUMNS`; the digit count comes from that column's
            host variable in the data dictionary, never from a literal.

    Returns:
        The value as the unsigned host variable holds it.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        ValueError: If ``column`` is not one of the eleven. The seven signed
            money columns must go through
            :func:`_store_into_signed_host_variable` instead, and confusing the
            two would either invent a sign loss or repair one.
    """
    if column not in SIGN_LOSS_COLUMNS:
        raise ValueError(
            f"{column} is not one of the eleven anomaly A-11 columns "
            f"[copybooks/wssl.cob:L43-L53] -> "
            f"[common/salesMT.cbl:L302-L312]; applying the sign loss to it "
            f"would invent an anomaly the frozen bridge does not have. The "
            f"eleven are {SIGN_LOSS_COLUMNS}."
        )
    host_variable = ENTRIES[column].bridge_host_variable
    digits = host_variable.digits
    if digits is None:  # pragma: no cover - guards a frozen fact
        raise ValueError(
            f"{host_variable.name} declares no digit count in the data "
            f"dictionary [{host_variable.source}]"
        )
    # `MOVE` into an unsigned receiver: absolute value, then drop the digits
    # that do not fit - HIGH-order, because a COBOL MOVE aligns on the decimal
    # point and the receiver here has no decimal places.
    stored = abs(int(value)) % (10**digits)
    if stored != value:
        _LOG.debug(
            "A-11 sign loss at the bridge: %s %s -> %s %s = %s "
            "[copybooks/wssl.cob:L43-L53] -> [common/salesMT.cbl:L302-L312]",
            ENTRIES[column].copybook.name,
            value,
            host_variable.name,
            host_variable.picture,
            stored,
        )
    return stored


def _store_into_unsigned_host_variable(
    value: Decimal | int,
    *,
    column: str,
) -> Decimal | int:
    """Store into an unsigned host variable whose copybook field is ALSO unsigned.

    Ten columns: the eight ``pic 9`` flags and ``Sales-Credit pic 99``
    [copybooks/wssl.cob:L25-L41], all widened to ``PIC 9(03) COMP``
    [common/salesMT.cbl:L292-L300], plus ``Sales-Discount pic 99v99 comp`` ->
    ``PIC 9(02)V9(02) COMP`` [:L301], the one unsigned decimal.

    There is no sign to lose here, and that is exactly why this is a SEPARATE
    function from :func:`_sign_loss_at_the_bridge`: Agent Action Plan 0.6.2
    requires the drift be handled "field by field from the dictionary", and
    collapsing the two would erase the distinction the plan rests its argument
    on. The digit widening the dictionary reports - one digit to three and back
    down to ``tinyint(1) unsigned`` - changes no value; the only conversions
    performed are the truncations any COBOL ``MOVE`` performs.

    Args:
        value: The record's value - ``int`` for the nine integer columns, a
            :class:`~decimal.Decimal` for ``SALES-DISCOUNT``.
        column: The column being loaded.

    Returns:
        The value as the host variable holds it: an ``int`` when the host
        variable has no decimal places, a :class:`~decimal.Decimal` at the host
        variable's own scale when it has.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        ValueError: If the host variable declares no digit count.
    """
    host_variable = ENTRIES[column].bridge_host_variable
    scale = host_variable.scale or 0
    if scale == 0:
        digits = host_variable.digits
        if digits is None:  # pragma: no cover - guards a frozen fact
            raise ValueError(
                f"{host_variable.name} declares no digit count "
                f"[{host_variable.source}]"
            )
        return abs(int(value)) % (10**digits)
    integer_digits = host_variable.integer_digits
    if integer_digits is None:  # pragma: no cover - guards a frozen fact
        raise ValueError(
            f"{host_variable.name} declares no integer digit count "
            f"[{host_variable.source}]"
        )
    quantum = Decimal(1).scaleb(-scale)
    # Truncate toward zero, then take the absolute value and drop the high-order
    # digits that do not fit - a MOVE into an unsigned scaled receiver.
    truncated = Decimal(value).quantize(quantum, rounding=ROUND_DOWN)
    limit = Decimal(10) ** integer_digits
    return (truncated.copy_abs() % limit).quantize(
        quantum, rounding=ROUND_DOWN
    )


def _store_into_signed_host_variable(
    value: Decimal,
    *,
    column: str,
) -> Decimal:
    """Store into a host variable that is SIGNED, like its copybook field.

    The seven money fields of :data:`MONEY_COLUMNS`: ``s9(8)v99 comp-3`` ->
    ``S9(08)V9(02) COMP`` [common/salesMT.cbl:L313-L319] -> signed
    ``decimal(10,2)``. **The sign survives this step**, which is Agent Action
    Plan 0.6.2's evidence that the drift is "specific rather than systemic".

    The sign is then dropped anyway, one step later, by
    :func:`_render_numeric_for_sql` - anomaly N-signdrop. Two mechanisms, two
    functions, so that a reader can see which one is doing what.

    Truncation is toward zero, never rounding: COBOL stores an over-scaled value
    into ``V9(02)`` by discarding the excess digits unless ``ROUNDED`` is
    written, and none is written anywhere in this bridge. High-order digits that
    do not fit ``S9(08)`` are discarded too.

    Args:
        value: The record's value as a :class:`~decimal.Decimal`.
        column: The column being loaded.

    Returns:
        The value as the signed host variable holds it, at the host variable's
        own scale.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    host_variable = ENTRIES[column].bridge_host_variable
    scale = host_variable.scale or 0
    integer_digits = host_variable.integer_digits
    if integer_digits is None:  # pragma: no cover - guards a frozen fact
        raise ValueError(
            f"{host_variable.name} declares no integer digit count "
            f"[{host_variable.source}]"
        )
    quantum = Decimal(1).scaleb(-scale)
    # ROUND_DOWN is truncation toward zero, which is what an unROUNDED COBOL
    # store does; Agent Action Plan 0.6.1 finds exactly five ROUNDED sites in
    # the whole in-scope cycle and none of them is in a bridge.
    truncated = Decimal(value).quantize(quantum, rounding=ROUND_DOWN)
    limit = Decimal(10) ** integer_digits
    if truncated.copy_abs() >= limit:
        # High-order truncation, sign preserved - the receiver is signed.
        sign = -1 if truncated < 0 else 1
        truncated = (truncated.copy_abs() % limit).copy_sign(Decimal(sign))
        truncated = truncated.quantize(quantum, rounding=ROUND_DOWN)
    return truncated


def _store_into_character_host_variable(text: str, *, column: str) -> str:
    """Store into an alphanumeric host variable - ``PIC X(n)``.

    A COBOL ``MOVE`` into ``PIC X(n)`` is left-justified: it truncates on the
    RIGHT when the sender is longer and pads with spaces on the right when it is
    shorter. Applied to :data:`CHARACTER_COLUMNS`, whose widths come from the
    dictionary - which is how ``Sales-Address``'s 96 characters
    [common/salesMT.cbl:L287] are reached without this module knowing that the
    group happens to be two fields of 48.

    Args:
        text: The record's value.
        column: The column being loaded.

    Returns:
        Exactly ``character_length`` characters.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    width = ENTRIES[column].bridge_host_variable.character_length
    if width is None:  # pragma: no cover - guards a frozen fact
        raise ValueError(
            f"{ENTRIES[column].bridge_host_variable.name} declares no "
            f"character length [{ENTRIES[column].bridge_host_variable.source}]"
        )
    return str(text)[:width].ljust(width)


def _ws_mysql_edit(value: Decimal | int) -> str:
    """Render a host variable into ``WS-MYSQL-EDIT``, character for character.

    ``MOVE HV-xxx TO WS-MYSQL-EDIT`` where ``WS-MYSQL-EDIT PIC -Z(18)9.9(9)``
    [common/salesMT.cbl:L216]. The measured layout, from GnuCOBOL 3.2.0::

        position   1  sign: '-' when negative, ' ' otherwise
        positions  2..19  eighteen Z, leading zeros suppressed to spaces
        position  20  a 9, so the units digit always shows
        position  21  '.'
        positions 22..30  nine fraction digits, zero filled

    Two measurements pin it::

        HV-SALES-CURRENT = -12345.67
            -> "-              12345.670000000"
        HV-SALES-CURRENT = 0
            -> "                   0.000000000"

    **This function is where anomaly N-signdrop becomes visible**: the sign
    lands in position 1, and :func:`_render_numeric_for_sql` never reads
    position 1 because no generated statement in any of the 28 frozen bridges
    does. See :data:`MYSQL_EDIT_WINDOWS_IN_USE`.

    Args:
        value: The host variable's value - :class:`int` for a ``COMP`` integer,
            :class:`~decimal.Decimal` for a scaled one. Never a ``float``
            (rule R-2).

    Returns:
        Exactly :data:`MYSQL_EDIT_WIDTH` characters.
    """
    amount = Decimal(value)
    sign_character = "-" if amount < 0 else " "
    magnitude = amount.copy_abs()
    # Nine fraction positions: truncate rather than round, then split. Using
    # Decimal shifting keeps every digit exact; no float appears anywhere.
    scaled = magnitude.quantize(
        Decimal(1).scaleb(-MYSQL_EDIT_FRACTION_POSITIONS),
        rounding=ROUND_DOWN,
    )
    digits = format(scaled, "f")
    if "." in digits:
        integer_text, fraction_text = digits.split(".", 1)
    else:  # pragma: no cover - quantize always yields a point at scale 9
        integer_text, fraction_text = digits, ""
    fraction_text = fraction_text[:MYSQL_EDIT_FRACTION_POSITIONS].ljust(
        MYSQL_EDIT_FRACTION_POSITIONS, "0"
    )
    # `Z` suppression: leading zeros become spaces, but the final `9` at
    # position 20 always prints, so a zero value shows a single '0' there.
    integer_text = integer_text.lstrip("0") or "0"
    integer_text = integer_text[-MYSQL_EDIT_INTEGER_POSITIONS:].rjust(
        MYSQL_EDIT_INTEGER_POSITIONS
    )
    return f"{sign_character}{integer_text}.{fraction_text}"


def _render_numeric_for_sql(value: Decimal | int, *, column: str) -> str:
    """Render a numeric host variable exactly as the generated SQL renders it.

    ``bb200-Insert`` and ``bb300-Update`` never interpolate a host variable
    directly. They move it into ``WS-MYSQL-EDIT`` and then take a FIXED WINDOW
    of that character field. Three shapes, all verified in the frozen source::

        `SALES-STATUS`="  MOVE HV-SALES-STATUS TO WS-MYSQL-EDIT
                          STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
                                                    [common/salesMT.cbl:L1377-L1379]

        `SALES-AVERAGE`=" MOVE HV-SALES-AVERAGE TO WS-MYSQL-EDIT
                          STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
                                                    [common/salesMT.cbl:L1574-L1576]

        `SALES-CURRENT`=" MOVE HV-SALES-CURRENT TO WS-MYSQL-EDIT
                          STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
                          STRING "."
                          STRING WS-MYSQL-EDIT(22:02)
                                                    [common/salesMT.cbl:L1634-L1642]

    The window is not hard-coded here. Every one of the five integer windows in
    use ends at edit-field position 20, so the window is exactly
    ``(21 - integer_digits : integer_digits)`` - which the data dictionary
    supplies per host variable. Checked against the frozen source: 3 digits ->
    ``(18:03)``, 5 -> ``(16:05)``, 10 -> ``(11:10)``, 2 -> ``(19:02)``, 8 ->
    ``(13:08)``. All five appear in ``salesMT`` and all five agree.

    Two details of the frozen rendering that change the stored value and are
    therefore reproduced exactly:

    * The INTEGER window is trimmed, so no leading zeros survive. ``FUNCTION
      TRIM`` with no direction trims both ends, and the window carries only
      leading spaces.
    * The FRACTION window is **not** trimmed [common/salesMT.cbl:L1641], so
      trailing zeros survive: a zero balance renders ``0.00``, never ``0.``.

    **ANOMALY N-signdrop.** No window starts at position 1, so the sign is never
    emitted. ``-12345.67`` and ``+12345.67`` produce the identical literal
    ``12345.67``, and the negative is stored positive.

    Args:
        value: The host variable's value.
        column: The column being rendered.

    Returns:
        The literal text the bridge would have placed between the double quotes
        of ``\\`COLUMN\\`="..."``.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        ValueError: If the column is alphanumeric - those go through
            :func:`_render_character_for_sql`.
    """
    host_variable = ENTRIES[column].bridge_host_variable
    integer_digits = host_variable.integer_digits
    if integer_digits is None:
        raise ValueError(
            f"{host_variable.name} is not a numeric host variable "
            f"[{host_variable.source}]; alphanumeric host variables are "
            f"rendered by FUNCTION TRIM (HV-xxx,TRAILING)"
        )
    edit = _ws_mysql_edit(value)
    window_start = MYSQL_EDIT_INTEGER_END - integer_digits
    # COBOL reference modification is 1-based inclusive; Python slicing is
    # 0-based half-open. `(start:length)` is therefore `[start-1:start-1+length]`
    # and, since every integer window ends at position 20, `[:20]`.
    integer_text = edit[window_start - 1 : MYSQL_EDIT_INTEGER_END - 1].strip()
    scale = host_variable.scale or 0
    if scale == 0:
        return integer_text
    fraction_start = MYSQL_EDIT_POINT_POSITION + 1
    fraction_text = edit[fraction_start - 1 : fraction_start - 1 + scale]
    return f"{integer_text}.{fraction_text}"


def _render_character_for_sql(text: str, *, column: str) -> str:
    """Render an alphanumeric host variable as the generated SQL renders it.

    ``STRING FUNCTION TRIM (HV-SALES-KEY,TRAILING)``
    [common/salesMT.cbl:L1314] - TRAILING only, so trailing spaces are stripped
    and any LEADING space survives into the stored value. Applied to every
    column of :data:`CHARACTER_COLUMNS`, including the two of
    :data:`UNLOADED_COLUMNS`, whose host variables ``initialize`` left as spaces
    and which therefore render as the empty string - anomaly N-2fields-lost.

    Args:
        text: The host variable's value.
        column: The column being rendered - used only for the log record, since
            the rendering itself is width-independent.

    Returns:
        The literal text, right-trimmed.
    """
    rendered = str(text).rstrip(" ")
    if column in UNLOADED_COLUMNS and rendered == "":
        _LOG.debug(
            "N-2fields-lost: %s renders as the empty string because "
            "bb000-HV-Load never loads it [common/salesMT.cbl:L1204-L1239]",
            column,
        )
    return rendered



# ---------------------------------------------------------------------------
# 6. `01 TD-SALEDGER-REC` - THE HOST-VARIABLE GROUP
#    [common/salesMT.cbl:L283-L321]
#
# Thirty-seven host variables, each with the picture the bridge declares. Held as
# one mapping keyed by COLUMN name rather than as thirty-seven attributes,
# because every operation on the group - `initialize`, load, unload, render,
# fetch - is a per-column operation driven by the data dictionary, and thirty-
# seven named attributes would be thirty-seven chances to transcribe one wrong.
# The host-variable NAMES are still published, from the dictionary, so
# traceability is unaffected: see `HOST_VARIABLE_NAMES`.
# ---------------------------------------------------------------------------

#: Column name -> the bridge's own host-variable name, from the dictionary.
#: This is where the N-nametrunc anomaly shows: ``SALES-CREATE-DAT`` ->
#: ``HV-SALES-CREATE-DAT``, three characters short of the copybook's
#: ``Sales-Create-Date`` [copybooks/wssl.cob:L53].
HOST_VARIABLE_NAMES: Final[Mapping[str, str]] = MappingProxyType(
    {name: entry.bridge_host_variable.name for name, entry in ENTRIES.items()}
)


def _initial_host_variable_value(column: str) -> Decimal | int | str:
    """The value ``initialize TD-SALEDGER-REC`` leaves in one host variable.

    ``initialize`` sets every alphanumeric item to SPACES and every numeric item
    to ZERO, and it is the FIRST statement of ``bb000-HV-Load``
    [common/salesMT.cbl:L1204]. Agent Action Plan 0.6.2 draws the consequence,
    verbatim: "unset fields become zero or space rather than SQL ``NULL``. This
    is why every column in the schema can be declared ``NOT NULL`` and why the
    Python layer must DEFAULT RATHER THAN OMIT."

    Args:
        column: The column whose host variable is being initialised.

    Returns:
        Spaces at the declared width for an alphanumeric host variable, integer
        zero for an unscaled numeric one, and ``Decimal`` zero at the declared
        scale for a scaled one.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    host_variable = ENTRIES[column].bridge_host_variable
    width = host_variable.character_length
    if width is not None:
        return " " * width
    scale = host_variable.scale or 0
    if scale == 0:
        return 0
    return Decimal(0).quantize(Decimal(1).scaleb(-scale))


@dataclass(slots=True)
class HostVariables:
    """``01 TD-SALEDGER-REC`` [common/salesMT.cbl:L283-L321].

    The bridge's own working copy of a row, between the record layout and the
    SQL text. Every value in it has already been through the receiving host
    variable's picture clause, which is where anomaly A-11's sign loss has
    already happened by the time :func:`bb200_insert` runs.

    Attributes:
        values: Column name -> the host variable's value. Keyed by column rather
            than by host-variable name so that the column order of
            :data:`COLUMN_ORDER` drives every traversal; the host-variable name
            for any column is in :data:`HOST_VARIABLE_NAMES`.
    """

    values: dict[str, Decimal | int | str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Fill the group at construction, as loading the program does.

        A COBOL ``01`` group in WORKING-STORAGE with no ``VALUE`` clause is
        zero- or space-filled when the program is loaded, so the group is never
        readable-but-unset. Reproducing that here means no path can raise a
        :class:`KeyError` for a column simply because no load has run yet -
        which matters for ``ba090-Process-Rewrite``, whose ``bb000-HV-Load``
        could in principle have been skipped.
        """
        if not self.values:
            self.initialize()

    def initialize(self) -> None:
        """``initialize TD-SALEDGER-REC`` [common/salesMT.cbl:L1204].

        Every host variable to zero or spaces. Run first by
        :func:`bb000_hv_load`, which is why the two columns of
        :data:`UNLOADED_COLUMNS` reach every ``INSERT`` and ``UPDATE`` as the
        empty string - anomaly N-2fields-lost.
        """
        self.values = {
            column: _initial_host_variable_value(column)
            for column in COLUMN_ORDER
        }

    def __getitem__(self, column: str) -> Decimal | int | str:
        """Read one host variable.

        Args:
            column: The column whose host variable is wanted.

        Returns:
            The host variable's current value.

        Raises:
            KeyError: If the group has not been initialised, or ``column`` is
                not a ``SALEDGER-REC`` column.
        """
        return self.values[column]

    def __setitem__(self, column: str, value: Decimal | int | str) -> None:
        """Write one host variable, without conversion.

        Used by the fetch path, which receives values already shaped by the
        pinned driver converter. The LOAD path goes through
        :func:`_move_to_host_variable` instead, because that is where the
        picture-clause conversions - and anomaly A-11 - live.

        Args:
            column: The column whose host variable is being written.
            value: The value to store.

        Raises:
            KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        """
        if column not in ENTRIES:
            raise KeyError(
                f"{column} is not a {TABLE_NAME} column "
                f"[mysql/ACASDB.sql:L945-L985]"
            )
        self.values[column] = value


def _record_value(sales: WsSalesRecord, column: str) -> Any:
    """Read the record field that feeds one column, by its dictionary path.

    The attribute path comes from
    :data:`~acas_posting.records.sales_ledger.DICTIONARY_KEYS` through
    :data:`RECORD_ATTRIBUTE_FOR_COLUMN`, so a column reaches its field without
    this module naming the field. That is how ``TURNOVER-Q1`` finds
    ``quarters.turnover_q1`` and how ``SALES-ADDRESS`` finds the
    ``sales_address`` GROUP rather than either of its two halves.

    ``SALES-ADDRESS`` is the one column whose field is a group, so it is the one
    column that needs assembling: ``move Sales-Address to HV-SALES-ADDRESS``
    [common/salesMT.cbl:L1207] concatenates ``Sales-Addr1 pic x(48)`` and
    ``Sales-Addr2 pic x(48)`` [copybooks/wssl.cob:L18-L20] into one 96-character
    host variable - anomaly N-addrconcat. The concatenation is performed from the
    group's own fields in declaration order, which is what a COBOL group ``MOVE``
    does.

    Args:
        sales: The ``WS-Sales-Record`` linkage record.
        column: The column whose feeding field is wanted.

    Returns:
        The field's value, with the address group already concatenated.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        AttributeError: If the record does not carry the dictionary's attribute
            path - which would mean the record module and the dictionary have
            drifted apart.
    """
    path = RECORD_ATTRIBUTE_FOR_COLUMN[column]
    value: Any = sales
    for part in path.split("."):
        value = getattr(value, part)
    if ENTRIES[column].copybook.is_group:
        # N-addrconcat: a group MOVE is the concatenation of its members, in
        # declaration order, at their declared widths.
        return "".join(
            str(getattr(value, member.name)).ljust(48)
            for member in value.__dataclass_fields__.values()
        )
    return value


def _assign_record_value(sales: WsSalesRecord, column: str, value: Any) -> None:
    """Write the record field that one column unloads into, by its dictionary path.

    The inverse of :func:`_record_value`. ``SALES-ADDRESS`` is again the special
    case: ``move HV-SALES-ADDRESS to Sales-Address``
    [common/salesMT.cbl:L1260] splits the 96 characters back across
    ``Sales-Addr1`` and ``Sales-Addr2`` at the group's own field boundaries,
    because that is what a group ``MOVE`` into a group does.

    Args:
        sales: The ``WS-Sales-Record`` linkage record.
        column: The column being unloaded.
        value: The host variable's value.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        AttributeError: If the record does not carry the dictionary's attribute
            path.
    """
    path = RECORD_ATTRIBUTE_FOR_COLUMN[column]
    parts = path.split(".")
    target: Any = sales
    for part in parts[:-1]:
        target = getattr(target, part)
    if ENTRIES[column].copybook.is_group:
        group = getattr(target, parts[-1])
        text = str(value)
        offset = 0
        for member in group.__dataclass_fields__.values():
            setattr(group, member.name, text[offset : offset + 48].ljust(48))
            offset += 48
        return
    setattr(target, parts[-1], value)


def _move_to_host_variable(
    host_variables: HostVariables,
    sales: WsSalesRecord,
    column: str,
) -> None:
    """One ``move <record field> to HV-<column>`` of ``bb000-HV-Load``.

    The single dispatch point for every picture-clause conversion this module
    performs, and therefore the single place anomaly A-11 can happen. The four
    branches are mutually exclusive and are chosen from the data dictionary, not
    from the column's name:

    1. :data:`SIGN_LOSS_COLUMNS` - eleven columns, signed source and unsigned
       host variable -> :func:`_sign_loss_at_the_bridge`. **ANOMALY A-11.**
    2. :data:`MONEY_COLUMNS` - seven columns, signed at both ends ->
       :func:`_store_into_signed_host_variable`. The sign SURVIVES here.
    3. :data:`CHARACTER_COLUMNS` -> :func:`_store_into_character_host_variable`.
    4. everything else, unsigned at both ends ->
       :func:`_store_into_unsigned_host_variable`.

    Args:
        host_variables: The group being loaded.
        sales: The ``WS-Sales-Record`` linkage record.
        column: The column being loaded.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    value = _record_value(sales, column)
    if column in SIGN_LOSS_COLUMNS:
        # ANOMALY A-11 - the sign is lost HERE, before any SQL is built.
        # [copybooks/wssl.cob:L43-L53] -> [common/salesMT.cbl:L302-L312]
        host_variables.values[column] = _sign_loss_at_the_bridge(
            int(value), column=column
        )
        return
    if column in MONEY_COLUMNS:
        # Signed at all three layers [common/salesMT.cbl:L313-L319]; the sign is
        # kept here and dropped later by the rendering - anomaly N-signdrop.
        host_variables.values[column] = _store_into_signed_host_variable(
            Decimal(value), column=column
        )
        return
    if column in CHARACTER_COLUMNS:
        host_variables.values[column] = _store_into_character_host_variable(
            str(value), column=column
        )
        return
    host_variables.values[column] = _store_into_unsigned_host_variable(
        value, column=column
    )


def bb000_hv_load(
    sales: WsSalesRecord,
    host_variables: HostVariables | None = None,
) -> HostVariables:
    """``bb000-HV-Load Section.`` [common/salesMT.cbl:L1196-L1245].

    Load the record into the host-variable group, ready for an ``INSERT`` or an
    ``UPDATE``. Performed from ``ba070-Process-Write`` [:L869] and
    ``ba090-Process-Rewrite`` [:L952], and from nowhere else - the maintainer's
    own closing comment says why [:L1241-L1242]: "Loading HVs implies a non-Fetch
    action. RGs are handled separately for all such actions so they must not be
    loaded here."

    THE STATEMENT ORDER IS THE FROZEN ORDER. ``initialize TD-SALEDGER-REC``
    [:L1204] first, then **thirty-five** moves [:L1205-L1239] in the sequence
    below, which is the column ordinal sequence of the first thirty-five
    columns:

    ==== ==================================== ==================================
    line record field                         host variable
    ==== ==================================== ==================================
    1205 ``WS-Sales-Key``                     ``HV-SALES-KEY``
    1206 ``Sales-Name``                       ``HV-SALES-NAME``
    1207 ``Sales-Address``  (group, 48+48)    ``HV-SALES-ADDRESS``  X(96)
    1208 ``Sales-Phone``                      ``HV-SALES-PHONE``
    1209 ``Sales-Ext``                        ``HV-SALES-EXT``
    1210 ``Sales-Email``                      ``HV-SALES-EMAIL``
    1211 ``Sales-Fax``                        ``HV-SALES-FAX``
    1212 ``Sales-Status``                     ``HV-SALES-STATUS``
    1213 ``Sales-Late``                       ``HV-SALES-LATE``
    1214 ``Sales-Dunning``                    ``HV-SALES-DUNNING``
    1215 ``Email-Invoice``                    ``HV-EMAIL-INVOICE``
    1216 ``Email-Statement``                  ``HV-EMAIL-STATEMENT``
    1217 ``Email-Letters``                    ``HV-EMAIL-LETTERS``
    1218 ``Delivery-Tag``                     ``HV-DELIVERY-TAG``
    1219 ``Notes-Tag``                        ``HV-NOTES-TAG``
    1220 ``Sales-Credit``                     ``HV-SALES-CREDIT``
    1221 ``Sales-Discount``                   ``HV-SALES-DISCOUNT``
    1222 ``Sales-Late-Min``     **A-11**      ``HV-SALES-LATE-MIN``
    1223 ``Sales-Late-Max``     **A-11**      ``HV-SALES-LATE-MAX``
    1224 ``Sales-Limit``        **A-11**      ``HV-SALES-LIMIT``
    1225 ``Sales-Activety``     **A-11**      ``HV-SALES-ACTIVETY``
    1226 ``Sales-Last-Inv``     **A-11**      ``HV-SALES-LAST-INV``
    1227 ``Sales-Last-Pay``     **A-11**      ``HV-SALES-LAST-PAY``
    1228 ``Sales-Average``      **A-11**      ``HV-SALES-AVERAGE``
    1229 ``Sales-Pay-Activety`` **A-11**      ``HV-SALES-PAY-ACTIVETY``
    1230 ``Sales-Pay-Average``  **A-11**      ``HV-SALES-PAY-AVERAGE``
    1231 ``Sales-Pay-Worst``    **A-11**      ``HV-SALES-PAY-WORST``
    1232 ``Sales-Create-Date``  **A-11**      ``HV-SALES-CREATE-DAT``  N-nametrunc
    1233 ``Sales-Current``                    ``HV-SALES-CURRENT``
    1234 ``Sales-Last``                       ``HV-SALES-LAST``
    1235 ``Turnover-Q1``                      ``HV-TURNOVER-Q1``
    1236 ``Turnover-Q2``                      ``HV-TURNOVER-Q2``
    1237 ``Turnover-Q3``                      ``HV-TURNOVER-Q3``
    1238 ``Turnover-Q4``                      ``HV-TURNOVER-Q4``
    1239 ``Sales-Unapplied``                  ``HV-SALES-UNAPPLIED``
    ==== ==================================== ==================================

    **THIRTY-FIVE, NOT THIRTY-SEVEN - ANOMALY N-2fields-lost.** The paragraph
    ends at ``Sales-UNAPPLIED`` [:L1239]. ``HV-SALES-STATS-DATE`` and
    ``HV-SALES-PARTIAL-SHIP-FLAG`` are never loaded, although both are declared
    [:L320-L321] and both are written by ``bb200-Insert`` [:L1751-L1762] and
    ``bb300-Update`` [:L2231-L2242]. Since ``initialize`` left them SPACES, every
    write stores the empty string and the record's own values never reach the
    database. The set is taken from the dictionary's own
    ``loaded_from_record`` flag, so it cannot drift - see
    :data:`LOADED_COLUMNS`.

    **ANOMALY A-11 happens in this function**, at the eleven lines marked above,
    through :func:`_move_to_host_variable` and :func:`_sign_loss_at_the_bridge`.
    It happens BEFORE any SQL is built, as Agent Action Plan 0.6.2 requires.

    Args:
        sales: The ``WS-Sales-Record`` linkage record to load from.
        host_variables: The group to load into. A fresh one when omitted, which
            is the normal case; the bridge's group is working storage that only
            this paragraph and the fetch ever write.

    Returns:
        The loaded group.
    """
    group = HostVariables() if host_variables is None else host_variables
    # `initialize TD-SALEDGER-REC.` [common/salesMT.cbl:L1204] - FIRST, which is
    # what makes N-2fields-lost store the empty string rather than NULL.
    group.initialize()
    # The thirty-five moves [common/salesMT.cbl:L1205-L1239], in the frozen
    # order, which is the column ordinal order of columns 1..35.
    for column in LOADED_COLUMNS:
        _move_to_host_variable(group, sales, column)
    return group


def bb100_unload_hvs(
    host_variables: HostVariables,
    sales: WsSalesRecord,
) -> WsSalesRecord:
    """``bb100-UnloadHVs Section.`` [common/salesMT.cbl:L1247-L1295].

    Move the host-variable group back into the record after a fetch. Performed
    from ``ba041-Reread`` [:L634], ``ba050-Process-Read-Indexed`` [:L755] and
    ``ba141-Reread`` [:L1157].

    ``initialize WS-Sales-Record.`` [:L1256] first - a PLAIN ``initialize``,
    where the two error paths of the two rereads use ``initialize
    WS-Sales-Record WITH FILLER`` [:L619, :L1142]. Two initialisation semantics
    in one bridge, the ``with filler`` form appearing twice: anomaly
    N-initialize. Not normalised; each is reproduced at its own site, so this one
    leaves the record's ``filler`` fields untouched.

    Then **thirty-five** moves [:L1258-L1292], the exact inverse of
    :func:`bb000_hv_load`'s thirty-five and in the same column order, ending at
    ``move HV-SALES-UNAPPLIED to Sales-UNAPPLIED``. ``HV-SALES-STATS-DATE`` and
    ``HV-SALES-PARTIAL-SHIP-FLAG`` are again absent - the READ half of anomaly
    N-2fields-lost: the fetch fills both host variables, nothing copies them
    back, so the caller sees ``Sales-Stats-Date`` zero and
    ``Sales-Partial-Ship-Flag`` space however the row was stored.

    The paragraph's own header comments record why no ``NULL`` can arrive
    [:L1250-L1254]: "NULL fields must not be returned in the buffer. SQL filters
    each column to ensure it has a proper value. This saves using indicator
    variables." Every column of the frozen schema is ``NOT NULL``, so the
    guarantee holds.

    ``move HV-SALES-ADDRESS to Sales-Address`` [:L1260] splits the 96 characters
    back into ``Sales-Addr1`` and ``Sales-Addr2`` - the reverse of anomaly
    N-addrconcat, and lossless in this direction only because both halves are
    fixed width.

    Args:
        host_variables: The group a fetch has just filled.
        sales: The ``WS-Sales-Record`` linkage record to unload into. Mutated in
            place, as a COBOL ``MOVE`` into a linkage item is.

    Returns:
        The same record, for convenience.
    """
    # `initialize WS-Sales-Record.` [common/salesMT.cbl:L1256] - PLAIN, not
    # `with filler`. Anomaly N-initialize: the two sibling sites differ.
    _initialize_sales_record(sales, with_filler=False)
    # The thirty-five moves [common/salesMT.cbl:L1258-L1292].
    for column in LOADED_COLUMNS:
        _assign_record_value(
            sales, column, _unload_host_variable(host_variables, column)
        )
    return sales


def _unload_host_variable(
    host_variables: HostVariables,
    column: str,
) -> Any:
    """Shape one host variable for the record field it unloads into.

    The record field's own storage class decides, and it comes from the
    dictionary's ``cobol_python_storage``: ``INT`` for the eleven statistics
    fields and the nine unsigned integers, ``DECIMAL`` for the eight scaled
    money and discount fields, ``STR`` for the character fields, and ``NONE``
    for the one group.

    Two details matter. First, the eleven A-11 fields come back through a
    ``PIC 9(nn) COMP`` host variable and an ``unsigned`` column, so they can only
    ever be non-negative on this path: the sign was lost on the way out and
    nothing restores it. Second, ``SALES-STATS-DATE`` is ``pic 9(4)`` in the
    record but ``X(4)`` in the host variable [common/salesMT.cbl:L320] - anomaly
    N-numtochar - so an unload would have to parse it; it never happens, because
    the column is one of :data:`UNLOADED_COLUMNS`.

    Args:
        host_variables: The group a fetch filled.
        column: The column being unloaded.

    Returns:
        The value shaped for the record field.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    value = host_variables[column]
    storage = ENTRIES[column].cobol_python_storage
    if storage is _loader.CobolPythonStorage.INT:
        return int(value)
    if storage is _loader.CobolPythonStorage.DECIMAL:
        scale = ENTRIES[column].copybook.scale or 0
        return Decimal(value).quantize(
            Decimal(1).scaleb(-scale), rounding=ROUND_DOWN
        )
    # STR and the one NONE (the SALES-ADDRESS group) both travel as text; the
    # group is split across its members by `_assign_record_value`.
    return str(value)


def _initialize_sales_record(
    sales: WsSalesRecord,
    *,
    with_filler: bool,
) -> None:
    """``initialize WS-Sales-Record`` - both forms. **ANOMALY N-initialize.**

    ``salesMT`` uses two different initialisation statements on the same record:

    * plain ``initialize WS-Sales-Record`` at the head of ``bb100-UnloadHVs``
      [common/salesMT.cbl:L1256], which by COBOL's rules leaves ``FILLER``
      items UNTOUCHED;
    * ``initialize WS-Sales-Record with filler`` on the errno branch of
      ``ba041-Reread`` [:L619] and again on the errno branch of ``ba141-Reread``
      [:L1142], which clears the ``FILLER`` items too.

    Three ``FILLER`` items are affected: ``filler pic xxx``
    [copybooks/wssl.cob:L40], the ``filler redefines Quarters`` view [:L61] and
    ``filler pic x(5)`` [:L68]. The first and third are the record's alignment
    and tail padding; the second is a redefinition of storage the four quarter
    fields already own, so clearing it clears them - which is why the two forms
    are not interchangeable and are not normalised here.

    Non-``FILLER`` items go to spaces or zero in both forms, per their category.

    ``Quarters`` and its unnamed redefinition are treated as two independent
    declarations over one area, exactly as
    :class:`~acas_posting.records.sales_ledger.QuartersView` documents: "no
    property switches between them, no value is copied across". So the plain
    form clears ``Quarters`` and leaves the redefinition, and the ``with filler``
    form clears both - which is what the two COBOL statements do.

    Args:
        sales: The record to initialise, mutated in place.
        with_filler: ``True`` for the ``with filler`` form.
    """
    for attribute, key in DICTIONARY_KEYS.items():
        if "." in attribute:
            # Group members are reached through their group, below.
            continue
        entry_is_filler = key.rsplit(".", 1)[-1].startswith("filler#")
        if entry_is_filler and not with_filler:
            continue
        _initialize_attribute(sales, attribute, with_filler=with_filler)


def _initialize_attribute(
    owner: Any,
    attribute: str,
    *,
    with_filler: bool,
) -> None:
    """Set one attribute to its ``initialize`` value, recursing into groups.

    Args:
        owner: The record or, on a recursive call, the nested group that carries
            ``attribute``.
        attribute: The attribute to initialise.
        with_filler: Passed down so a nested group's members follow the same rule
            as the top level.
    """
    current = getattr(owner, attribute)
    if isinstance(current, str):
        setattr(owner, attribute, " " * len(current))
        return
    if isinstance(current, int) and not isinstance(current, bool):
        setattr(owner, attribute, 0)
        return
    if isinstance(current, Decimal):
        setattr(owner, attribute, Decimal(0).quantize(current))
        return
    if isinstance(current, tuple):
        setattr(
            owner,
            attribute,
            tuple(Decimal(0).quantize(item) for item in current),
        )
        return
    # A nested group - `Sales-Address`, `Quarters` or the `Quarters` redefinition.
    # `initialize` reaches every elementary item inside it.
    for member in getattr(current, "__dataclass_fields__", {}):
        _initialize_attribute(current, member, with_filler=with_filler)



# ---------------------------------------------------------------------------
# 7. THE SQL - EVERY STATEMENT FOR `SALEDGER-REC`, AND NOTHING ELSE
#
# Rule R-3 permits SELECT, INSERT, UPDATE and DELETE and nothing else; there is
# no DDL here and no statement for any other table. Every identifier goes through
# `quote_identifier` because every one of them contains a HYPHEN and would
# otherwise be a MySQL syntax error - the table itself, all thirty-seven columns
# and the key.
#
# WHAT IS BOUND IS THE RENDERED TEXT, NOT THE VALUE. The bridge interpolates
# `\`COLUMN\`="<rendered>"` into the statement, so what reaches MySQL is the
# rendered STRING; binding a `Decimal` instead would restore the sign the
# rendering drops and quietly repair anomaly N-signdrop. So each of the
# thirty-seven placeholders is bound to the output of
# `_render_numeric_for_sql` or `_render_character_for_sql`, which is
# byte-for-byte what the bridge would have written between the quotes.
# ---------------------------------------------------------------------------


def _log_key(text: object) -> str:
    """``move <something> to WS-File-Key`` - truncated to the declared width.

    ``05 WS-File-Key pic x(64) value spaces`` [copybooks/wsfnctn.cob:L52], so a
    ``MOVE`` of anything longer truncates on the right. Reproduced so that the
    log record carries what the frozen program's log record would carry, and no
    more.

    Args:
        text: Whatever the frozen source moves into the field.

    Returns:
        The field's contents: at most :data:`WS_FILE_KEY_WIDTH` characters,
        rendered through :func:`~acas_posting.dal.status.sanitise_for_log` so a
        control character in driver-supplied text cannot forge a log record. The
        limit is the COBOL field's own width, because the field cannot hold more
        than that however the escaping expands.
    """
    return sanitise_for_log(
        str(text)[:WS_FILE_KEY_WIDTH], limit=WS_FILE_KEY_WIDTH
    )


def _log_where(text: object) -> str:
    """``move WS-Where (1:J) to WS-Log-Where`` - the test-logging copy.

    ``05 WS-Log-Where pic x(231)`` [copybooks/wsfnctn.cob:L53]. Written by every
    positioning verb of the bridge [common/salesMT.cbl:L503, :L668, :L797,
    :L1028] and cleared by both rereads [:L551, :L1076].

    Args:
        text: The predicate the verb built.

    Returns:
        The field's contents: at most :data:`WS_LOG_WHERE_WIDTH` characters,
        rendered through :func:`~acas_posting.dal.status.sanitise_for_log`.
    """
    return sanitise_for_log(
        str(text)[:WS_LOG_WHERE_WIDTH], limit=WS_LOG_WHERE_WIDTH
    )


def _set_paragraph(file_access: FileAccess, number: int) -> None:
    """``move NNN to ws-No-Paragraph`` - and the field is the CALLER's.

    ``05 ws-No-Paragraph pic 999`` is declared inside ``03 Logging-Data``
    inside ``01 File-Access`` [copybooks/wsfnctn.cob:L22, L44-L48], and ``File-Access``
    is a LINKAGE item in both the handler [common/acas012.cbl:L276-L282] and the
    bridge [common/salesMT.cbl:L336-L339]. So neither program owns the storage:
    every ``move NNN to ws-No-Paragraph`` writes through the linkage into the
    caller's own record, where it stays after the callee returns. Anything that
    kept the number in a module-private variable instead would lose an
    observable side effect the frozen program has.

    Reproduced as a one-line helper rather than inlined so that a reader can
    grep one name and find all twenty-one sites at which either program stamps
    its position for the log record.

    Args:
        file_access: The caller's ``File-Access`` block.
        number: The paragraph number the frozen source moves in. Truncated to
            the field's three digits exactly as ``pic 999`` would, so a value
            above 999 stores its low-order three digits rather than raising.
    """
    file_access.logging_data.ws_no_paragraph = abs(int(number)) % 1000


def _record_key(sales: WsSalesRecord) -> str:
    """``WS-Sales-Record (K:L)`` - the key as a substring of the WHOLE record.

    ``set KOR-x1 to 1`` / ``move KOR-offset (KOR-x1) to K`` /
    ``move KOR-length (KOR-x1) to L`` and then ``WS-Sales-Record (K:L)``
    [common/salesMT.cbl:L645-L646 with :L657, :L780-L781 with :L806,
    :L898-L899 with :L907, :L956-L957]. The bridge does NOT read the named
    ``WS-Sales-Key`` field; it takes characters :data:`KEY_OFFSET` through
    ``KEY_OFFSET + KEY_LENGTH - 1`` of the record's storage, which for this
    layout is the key field because the key happens to be first. Reproduced as a
    substring of the record's leading field so that the offset and length
    metadata is what decides - which is what
    :mod:`acas_posting.dal.cursor_state` also does.

    Args:
        sales: The ``WS-Sales-Record`` linkage record.

    Returns:
        Exactly :data:`KEY_LENGTH` characters.
    """
    storage = str(sales.ws_sales_key).ljust(KEY_OFFSET - 1 + KEY_LENGTH)
    return storage[KEY_OFFSET - 1 : KEY_OFFSET - 1 + KEY_LENGTH]


def _quoted_columns() -> tuple[str, ...]:
    """Every column name, backtick-quoted, in ordinal order.

    Thirty-seven hyphenated identifiers, each of which is a MySQL syntax error
    unquoted. Built from :data:`COLUMN_ORDER`, which comes from the dictionary,
    so the list is never typed out.

    Returns:
        The quoted names, in ``mysql/ACASDB.sql`` ordinal order.
    """
    return tuple(quote_identifier(name) for name in COLUMN_ORDER)


#: ``\`SALEDGER-REC\`` - the table name, quoted once.
QUOTED_TABLE: Final[str] = quote_identifier(TABLE_NAME)

#: ``\`SALES-KEY\`` - the key of reference's column, quoted once.
QUOTED_KEY_COLUMN: Final[str] = quote_identifier(
    PRIMARY_KEY_OF_REFERENCE.column_name
)


def _rendered_parameters(
    host_variables: HostVariables,
) -> tuple[str, ...]:
    """Render all thirty-seven host variables into their SQL literals.

    The values ``bb200-Insert`` and ``bb300-Update`` place between the double
    quotes, in ordinal order. **All thirty-seven, always** - Agent Action Plan
    0.6.2: "the Python layer must default rather than omit", because
    ``initialize TD-SALEDGER-REC`` [common/salesMT.cbl:L1204] guarantees that
    every host variable holds a value and every column of the frozen schema is
    ``NOT NULL``. **No element is ever ``None``.**

    Args:
        host_variables: The loaded group.

    Returns:
        Thirty-seven strings, in :data:`COLUMN_ORDER`.
    """
    rendered: list[str] = []
    for column in COLUMN_ORDER:
        value = host_variables[column]
        if column in CHARACTER_COLUMNS:
            rendered.append(_render_character_for_sql(str(value), column=column))
        else:
            # N-signdrop lives in here: the sign in edit-field position 1 is
            # never emitted [common/salesMT.cbl:L1636-L1642].
            rendered.append(
                _render_numeric_for_sql(
                    value if isinstance(value, (Decimal, int)) else Decimal(0),
                    column=column,
                )
            )
    return tuple(rendered)


def bb200_insert(
    connection: Any,
    host_variables: HostVariables,
) -> int:
    """``bb200-Insert Section.`` [common/salesMT.cbl:L1297-L1775].

    The generated ``INSERT``. The bridge assembles it into ``WS-MYSQL-COMMAND``
    with a ``STRING ... WITH POINTER WS-MYSQL-I`` per fragment
    [:L1305-L1310], one ``\\`COLUMN\\`="..."`` group per column separated by
    ``", "``, then ``";"`` [:L1766] and the ``X"00"`` terminator [:L1768], and
    performs ``MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`` [:L1770]::

        INSERT INTO `SALEDGER-REC` SET `SALES-KEY`="...", `SALES-NAME`="...",
            ... `SALES-PARTIAL-SHIP-FLAG`="...";

    **ALL THIRTY-SEVEN COLUMNS ARE NAMED, ALWAYS.** The column list is the
    dictionary's ordinal order, verified identical to the frozen ``INSERT``'s own
    order and to the ``CREATE TABLE``'s. Nothing is omitted and nothing is
    ``None``: see :func:`_rendered_parameters`.

    The ``X"00"`` terminator has no Python counterpart - it terminates a C string
    for ``cobmysqlapi.c`` - and is recorded as an omission. The trailing ``";"``
    IS reproduced, because the bridge writes one here and deliberately does not
    in ``ba080-Process-Delete`` [:L928].

    Two of the thirty-seven literals are always the empty string, whatever the
    record held - anomaly N-2fields-lost. That is not corrected here.

    Args:
        connection: The live connection.
        host_variables: The group :func:`bb000_hv_load` filled.

    Returns:
        ``WS-MYSQL-COUNT-ROWS`` - the affected-row count
        ``ba070-Process-Write`` tests against 1 [:L879].

    Raises:
        Exception: Whatever the driver raises. ``ba070-Process-Write`` translates
            it, because that is where the frozen source tests the outcome.
    """
    assignments = ", ".join(
        f"{quoted}=%s" for quoted in _quoted_columns()
    )
    statement = f"INSERT INTO {QUOTED_TABLE} SET {assignments};"
    parameters = _rendered_parameters(host_variables)
    with execute_statement(connection, statement, parameters) as cursor:
        rowcount = int(getattr(cursor, "rowcount", 0) or 0)
    _LOG.debug(
        "bb200-Insert on %s affected %d row(s) [common/salesMT.cbl:L1297]",
        TABLE_NAME,
        rowcount,
    )
    return rowcount


def bb300_update(
    connection: Any,
    host_variables: HostVariables,
    where_key: str,
) -> int:
    """``bb300-Update Section.`` [common/salesMT.cbl:L1777-L2259].

    The generated ``UPDATE``, assembled exactly like the ``INSERT`` and then
    given ``" WHERE "`` [:L2246] plus ``FUNCTION TRIM (WS-Where (1:J))``
    [:L2249] - the predicate ``ba090-Process-Rewrite`` built - and ``";" X"00"``
    [:L2252]::

        UPDATE `SALEDGER-REC` SET `SALES-KEY`="...", ...
            `SALES-PARTIAL-SHIP-FLAG`="..." WHERE `SALES-KEY`="...";

    **THE PRIMARY KEY IS IN THE SET LIST.** ``\\`SALES-KEY\\`="..."`` is the
    first assignment [:L1791-L1796] as well as the whole of the predicate, so a
    rewrite re-asserts the key it is keyed on. Harmless because the predicate
    comes from the same host variable, and reproduced because the frozen
    statement does it - rule R-4 makes the shape the specification.

    All thirty-seven columns are set, including the two of
    :data:`UNLOADED_COLUMNS` - so a rewrite ERASES whatever
    ``SALES-STATS-DATE`` and ``SALES-PARTIAL-SHIP-FLAG`` held, replacing each
    with the empty string. That is the sharpest observable consequence of anomaly
    N-2fields-lost, and it is not corrected.

    Args:
        connection: The live connection.
        host_variables: The group :func:`bb000_hv_load` filled.
        where_key: The key value for the predicate -
            ``WS-Sales-Record (K:L)`` as ``ba090`` built it [:L956-L965].

    Returns:
        ``WS-MYSQL-COUNT-ROWS`` - the affected-row count
        ``ba090-Process-Rewrite`` tests against 1 [:L975].

    Raises:
        Exception: Whatever the driver raises; ``ba090-Process-Rewrite``
            translates it.
    """
    assignments = ", ".join(
        f"{quoted}=%s" for quoted in _quoted_columns()
    )
    statement = (
        f"UPDATE {QUOTED_TABLE} SET {assignments} "
        f"WHERE {QUOTED_KEY_COLUMN}=%s;"
    )
    parameters = (*_rendered_parameters(host_variables), where_key)
    with execute_statement(connection, statement, parameters) as cursor:
        rowcount = int(getattr(cursor, "rowcount", 0) or 0)
    _LOG.debug(
        "bb300-Update on %s affected %d row(s) [common/salesMT.cbl:L1777]",
        TABLE_NAME,
        rowcount,
    )
    return rowcount


def _row_into_host_variables(
    row: Mapping[str, object],
    host_variables: HostVariables,
) -> HostVariables:
    """``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT`` + all 37 host variables.

    The fetch call names every one of the thirty-seven host variables as an
    argument - [common/salesMT.cbl:L563-L599] in ``ba041-Reread``,
    [:L693-L729] in ``ba050-Process-Read-Indexed`` and [:L1086-L1122] in
    ``ba141-Reread``. So all thirty-seven are filled by every fetch, INCLUDING
    the two that ``bb100-UnloadHVs`` will then ignore - which is the read half of
    anomaly N-2fields-lost.

    Values arrive from the pinned driver converter as :class:`~decimal.Decimal`
    for a ``decimal`` column, :class:`int` for an integer one and :class:`str`
    for a ``char`` one (rule R-2: never a ``float``), and are then shaped by the
    receiving host variable's picture. A ``char`` column arrives already
    right-trimmed by MySQL, so it is padded back to the host variable's declared
    width, which is what a ``MOVE`` into ``PIC X(n)`` gives.

    Args:
        row: One stored row, keyed by column name.
        host_variables: The group to fill.

    Returns:
        The same group, filled.

    Raises:
        KeyError: If the row is missing a ``SALEDGER-REC`` column - which would
            mean the ``SELECT *`` did not come from the frozen table.
    """
    for column in COLUMN_ORDER:
        value = row[column]
        host_variable = ENTRIES[column].bridge_host_variable
        width = host_variable.character_length
        if width is not None:
            host_variables[column] = str(value).ljust(width)[:width]
            continue
        scale = host_variable.scale or 0
        if scale == 0:
            host_variables[column] = int(value)  # type: ignore[arg-type]
            continue
        host_variables[column] = Decimal(str(value)).quantize(
            Decimal(1).scaleb(-scale), rounding=ROUND_DOWN
        )
    return host_variables



# ---------------------------------------------------------------------------
# 8. `salesMT` - THE BRIDGE PROGRAM
#
# ONE FUNCTION PER PARAGRAPH, in the frozen program's own order, each carrying
# its locator (rule R-5). The bridge's WORKING-STORAGE is static across calls in
# COBOL, so it lives on the module's single :class:`BridgeSession` rather than
# being rebuilt per call - which is exactly how `ba041-Reread` can find a cursor
# a previous call opened.
#
# THE `GO TO` TAXONOMY, per Agent Action Plan section 0.4.2, applied at every
# transfer site in this section:
#   * `go to ba999-end`   -> Class 3, section exit -> `return`, and the caller
#     (`ba_acas_dal_process`) performs `ba999_end` afterwards. Faithful because
#     `ba999-end` is the last paragraph before `ba999-exit`, so reaching it and
#     falling out of the section are the same thing.
#   * `go to ba998-Free`  -> Class 4, sibling re-dispatch -> a named call to
#     :func:`ba998_free` followed by `return`, because `ba998-Free` does work
#     (frees the cursor, sets the flag) and then FALLS THROUGH to `ba999-end`.
#   * `go to ba100-Bad-Function` from the evaluate -> Class 4.
#   * `ba040`/`ba140` falling out of `if Cursor-Not-Active ... end-if` into
#     `ba041`/`ba141` -> Class 2's mirror image: no transfer at all, an explicit
#     sequential call, because the frozen source ends the SELECT stage with
#     `perform ba999-End` (a PERFORM, which returns) and NOT a `go to`.
#   * There is no Class 1 site in this section: the bridge contains no loop.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class BridgeWorkingStorage:
    """``salesMT``'s WORKING-STORAGE, which is static across calls.

    Attributes:
        host_variables: ``01 TD-SALEDGER-REC``
            [common/salesMT.cbl:L284-L321]. Static, so a value survives from one
            call to the next until the next ``initialize``.
        stored_rows_pointer: ``01 TP-SALEDGER-REC USAGE POINTER``
            [common/salesMT.cbl:L283] - the result-set handle
            ``MOVE WS-MYSQL-RESULT TO TP-SALEDGER-REC`` saves and
            ``MOVE TP-SALEDGER-REC TO WS-MYSQL-RESULT`` restores. Modelled as the
            :class:`~acas_posting.dal.cursor_state.CursorState` slot the rows are
            stored in, since a Python object reference is what a pointer is here.
        ws_where: ``WS-Where`` - the predicate under construction.
        j: ``J`` - ``WITH POINTER J``'s value, so ``WS-Where (1:J)`` is the
            predicate's used length. One PAST the last character written, which
            is why the frozen source always slices ``(1:J)`` and never ``(1:J-1)``
            and so always carries one trailing space.
        k: ``K`` - ``KOR-offset``, copied per verb.
        l: ``L`` - ``KOR-length``, copied per verb.
        most_relation: ``MOST-Relation pic xxx`` - the START comparison.
        ws_mysql_count_rows: ``WS-MYSQL-Count-Rows`` - what ``MySQL_num_rows``
            or the affected-row count left.
        ws_mysql_error_number: ``WS-MYSQL-Error-Number pic x(4)`` - what
            ``MySQL_errno`` left. **The frozen source compares it against the
            three-character literal** ``"0  "``, so "no error" is the string
            ``"0"`` space-padded, never the integer zero.
        ws_mysql_error_message: ``WS-MYSQL-Error-Message`` - ``MySQL_error``.
        ws_mysql_sqlstate: ``WS-MYSQL-SQLstate`` - ``MySQL_sqlstate``.
        return_code: ``RETURN-CODE``, which ``MySQL_fetch_record`` sets to -1 at
            end of result [common/salesMT.cbl:L604].
        ws_temp_ed: ``WS-Temp-Ed`` - the edited count the log strings embed.
    """

    host_variables: HostVariables = field(default_factory=HostVariables)
    stored_rows_pointer: CursorState | None = None
    ws_where: str = ""
    j: int = 1
    k: int = 0
    l: int = 0
    most_relation: str = "   "
    ws_mysql_count_rows: int = 0
    ws_mysql_error_number: str = "0  "
    ws_mysql_error_message: str = ""
    ws_mysql_sqlstate: str = ""
    return_code: int = 0
    ws_temp_ed: str = ""


#: ``salesMT``'s single WORKING-STORAGE instance - static, as COBOL's is.
_WORKING_STORAGE: Final[BridgeWorkingStorage] = BridgeWorkingStorage()


def working_storage() -> BridgeWorkingStorage:
    """Return the bridge's single :class:`BridgeWorkingStorage`.

    Returns:
        The static working storage, so a test can inspect ``WS-Where``,
        ``ws-No-Paragraph`` or the host variables the last call left - which is
        what the frozen program's screen displays exist to show.
    """
    return _WORKING_STORAGE


def reset_working_storage() -> None:
    """Return the bridge's working storage to its ``VALUE`` clauses.

    Not a COBOL paragraph - a freshly loaded program simply starts this way. It
    exists so that rule R-6's determinism requirement can be met by a caller that
    runs the same scenario twice in one process.
    """
    _WORKING_STORAGE.host_variables.initialize()
    _WORKING_STORAGE.stored_rows_pointer = None
    _WORKING_STORAGE.ws_where = ""
    _WORKING_STORAGE.j = 1
    _WORKING_STORAGE.k = 0
    _WORKING_STORAGE.l = 0
    _WORKING_STORAGE.most_relation = "   "
    _WORKING_STORAGE.ws_mysql_count_rows = 0
    _WORKING_STORAGE.ws_mysql_error_number = "0  "
    _WORKING_STORAGE.ws_mysql_error_message = ""
    _WORKING_STORAGE.ws_mysql_sqlstate = ""
    _WORKING_STORAGE.return_code = 0
    _WORKING_STORAGE.ws_temp_ed = ""


#: What ``MySQL_errno`` leaves when there is no error. The frozen source's own
#: literal: ``if WS-MYSQL-Error-Number not = "0  "``
#: [common/salesMT.cbl:L529, :L613, :L737, :L845, :L878, :L933, :L982].
NO_DRIVER_ERROR: Final[str] = "0  "


def _driver_error_fields(error: BaseException) -> tuple[str, str, str]:
    """The three C calls the bridge makes after a failed statement.

    ``call "MySQL_errno" using WS-MYSQL-Error-Number``,
    ``call "MySQL_sqlstate" using WS-MYSQL-SQLstate`` and
    ``call "MySQL_error" using WS-MYSQL-Error-Message`` - three separate
    interrogations of the same connection, e.g. [common/salesMT.cbl:L876-L884].
    Reproduced as three reads of the driver's exception, which is where the same
    three values live on this side.

    Widths are the frozen fields': ``WS-MYSQL-Error-Number pic x(4)`` truncates a
    longer errno, and the errno is rendered as TEXT because the frozen comparison
    is against a text literal.

    Args:
        error: What the driver raised.

    Returns:
        ``(errno, sqlstate, message)`` - errno space-padded to the width of
        :data:`NO_DRIVER_ERROR` so a comparison against it behaves as the COBOL's
        does, and the message sanitised for logging.
    """
    errno = getattr(error, "errno", None)
    sqlstate = getattr(error, "sqlstate", None) or ""
    message = getattr(error, "msg", None)
    if message is None:
        message = str(error)
    errno_text = (
        "0" if errno is None else str(errno)
    ).ljust(len(NO_DRIVER_ERROR))[:4]
    return (
        errno_text,
        str(sqlstate)[:SQL_STATE_WIDTH],
        sanitise_for_log(str(message), limit=SQL_MSG_WIDTH),
    )


def _column_names(cursor: DatabaseCursor) -> tuple[str, ...]:
    """The result's column names, or ``()`` when the driver gave no metadata.

    Args:
        cursor: The cursor a ``SELECT`` was issued on.

    Returns:
        The names in the result's own order.
    """
    description = getattr(cursor, "description", None)
    if not description:
        return ()
    return tuple(str(column[0]) for column in description)


def _fetch_one_row(cursor: DatabaseCursor) -> Mapping[str, object] | None:
    """``CALL "MySQL_fetch_record"`` - one row, keyed by column name.

    THE FROZEN CALL IS POSITIONAL. It names all thirty-seven host variables as
    arguments [common/salesMT.cbl:L563-L599] and the C interface copies result
    field *n* into argument *n*; there is no name matching anywhere in it. So
    when the driver supplies no column metadata the row is keyed by
    :data:`COLUMN_ORDER` - the ``mysql/ACASDB.sql`` ordinal order, which is what
    ``SELECT *`` returns and therefore what the positional copy would have used.

    Args:
        cursor: The cursor the ``SELECT`` was issued on.

    Returns:
        The row keyed by column name, or ``None`` at end of result.

    Raises:
        ValueError: If the row has a different number of fields from the frozen
            table's column count. The C interface would have copied into
            whichever host variables it had and left the rest, silently; refusing
            is not a new validation of DATA but a refusal to guess at a
            structural mismatch that cannot arise from the frozen schema.
    """
    row = cursor.fetchone()
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row
    names = _column_names(cursor) or COLUMN_ORDER
    if len(row) != len(names):
        raise ValueError(
            f"{BRIDGE}: a row of {len(row)} field(s) cannot fill "
            f"{len(names)} host variable(s); the frozen "
            f"`{TABLE_NAME}` has {len(COLUMN_ORDER)} columns "
            f"[common/salesMT.cbl:L563-L599]"
        )
    return MappingProxyType(dict(zip(names, row, strict=True)))


def _store_result(cursor: DatabaseCursor) -> tuple[Mapping[str, object], ...]:
    """``PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT``.

    ``mysql_store_result`` pulls every qualifying row to the client
    [copybooks/mysql-procedures.cpy:L187-L192] before ``MySQL_num_rows`` counts
    it, which is why ``WS-MYSQL-Count-Rows`` is meaningful the instant the
    ``SELECT`` returns and why a subsequent statement on the same connection
    cannot disturb the walk.

    Args:
        cursor: The cursor the ``SELECT`` was issued on.

    Returns:
        Every row, in the order the statement returned them.
    """
    rows: list[Mapping[str, object]] = []
    while True:
        row = _fetch_one_row(cursor)
        if row is None:
            return tuple(rows)
        rows.append(row)


def _primary(session_state: BridgeSession) -> CursorState:
    """``Most-Cursor-Set`` - the primary cursor flag and its stored rows.

    Args:
        session_state: The session holding ``DAL-Data``.

    Returns:
        The primary slot's state.
    """
    return session_state.cursors.state_for(TABLE_NAME, CursorSlot.PRIMARY)


def _secondary(session_state: BridgeSession) -> CursorState:
    """``Most-Cursor-Set-2`` - the by-name cursor flag and its stored rows.

    ``03 Most-Cursor-Set-2 pic 9 value zero.`` with ``88 Cursor-Active-2``
    [common/salesMT.cbl:L252-L254]. A second, independent cursor that only
    ``ba140``/``ba141`` use.

    Args:
        session_state: The session holding ``DAL-Data``.

    Returns:
        The secondary slot's state.
    """
    return session_state.cursors.state_for(TABLE_NAME, CursorSlot.SECONDARY)


def ca_process_logs(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``Ca-Process-Logs.`` [common/salesMT.cbl:L2261-L2265].

    ``call "fhlogger" using File-Access ACAS-DAL-Common-data``.

    **``fhlogger`` IS OUT OF SCOPE** - Agent Action Plan section 0.2.2 lists
    ``common/fhlogger.cbl`` among the non-posting utilities - and it writes a
    flat log file, not a table, so it has no database effect. Per section 0.3.4
    the diagnostic therefore becomes a Python log record at a severity matching
    the original's intent, carrying the same fields the frozen program builds its
    record from [common/fhlogger.cbl:L221-L235]: the two status fields, the log
    system and file number, the function, the paragraph, the access type, the
    key, the predicate and the three SQL fields.

    TWO THINGS THE FROZEN LOGGER DOES ARE DELIBERATELY NOT REPRODUCED, and both
    are recorded as omissions. It reads ``function Current-Date``
    [common/fhlogger.cbl:L219] - a clock read, which rule R-6 bars from this
    module and which is safe to drop precisely because the value reaches only the
    log file. And on a failed ``open extend`` it displays a message and waits for
    a keystroke [:L239-L244], which section 0.3.4 drops as a pause with no
    database effect.

    ONE THING IT DOES **IS** REPRODUCED: ``add 1 to Log-File-Rec-Written``
    [common/fhlogger.cbl:L249]. That counter lives in the CALLER's
    ``ACAS-DAL-Common-data`` block, so it is observable to the caller through the
    linkage, and the frozen loaders print it [common/salesLD.cbl:L499].

    Args:
        file_access: The block the record is built from.
        dal_common: The block carrying the testing switches and the counter.
    """
    logging_data = file_access.logging_data
    _LOG.info(
        "fhlogger: system=%s file=%s fn=%s para=%s access=%s "
        "fs=%s we=%s key=%s where=%s errno=%s state=%s msg=%s",
        logging_data.ws_log_system,
        logging_data.ws_log_file_no,
        file_access.file_function,
        logging_data.ws_no_paragraph,
        file_access.access_type,
        file_access.fs_reply,
        file_access.we_error,
        logging_data.ws_file_key,
        logging_data.ws_log_where,
        logging_data.sql_err,
        logging_data.sql_state,
        logging_data.sql_msg,
    )
    # `add 1 to Log-File-Rec-Written.` [common/fhlogger.cbl:L249], in the
    # caller's own linkage block. `pic 9(6)`, so it wraps at a million.
    dal_common.log_file_rec_written = (
        int(dal_common.log_file_rec_written) + 1
    ) % 1_000_000


def ba999_end(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba999-end.`` [common/salesMT.cbl:L1186-L1191].

    ::

        if       Testing-1
                 perform Ca-Process-Logs
        end-if.

    The bridge's single exit-time action. ``Testing-1`` is
    ``88 Testing-1 value 1`` over ``03 SW-Testing pic 9 value 1``
    [copybooks/Test-Data-Flags.cob], so logging is ON by default and the
    maintainer's own comment says a completed test run may set it to zero.

    The maintainer's question mark above this paragraph is preserved as evidence
    rather than answered - anomaly N-emptypara's sibling::

        *>  Any Clean ups before quiting    move data record ?????
        *>    do so at the start as well ??????

    Args:
        file_access: The block the log record is built from.
        dal_common: The block carrying ``SW-Testing``.
    """
    if int(dal_common.sw_testing) == TESTING_1_VALUE:
        ca_process_logs(file_access, dal_common)


def ba999_exit() -> None:
    """``ba999-exit.`` [common/salesMT.cbl:L1193-L1194].

    ``exit program.`` - control returns to ``acas012``. Nothing else happens
    here, and in particular NOTHING IS CLEANED UP: the connection, the cursors
    and every host variable survive the return, which is what makes
    ``ba041-Reread`` able to continue a walk a previous call began.
    """
    _LOG.debug(
        "%s exit program [common/salesMT.cbl:L1195]; connection and cursors "
        "survive the return",
        BRIDGE,
    )


def ba998_free(file_access: FileAccess, session_state: BridgeSession) -> None:
    """``ba998-Free.`` [common/salesMT.cbl:L1174-L1186].

    ::

        move     20 to ws-No-Paragraph.
        MOVE TP-SALEDGER-REC TO WS-MYSQL-RESULT
        CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call
        set      Cursor-Not-Active to true.

    **ANOMALY N-cursor2-leak - REPRODUCED, NOT FIXED.** The paragraph frees ONE
    result and clears ONE flag: ``Cursor-Not-Active`` is
    ``88 Cursor-Not-Active`` over ``Most-Cursor-Set``
    [common/salesMT.cbl:L246], the PRIMARY. It never mentions
    ``Most-Cursor-Set-2``, so a by-name walk left active by ``ba140`` survives
    every ``ba998-Free`` - including the one at the end of every read-indexed,
    and the one ``ba030-Process-Close`` performs before closing the connection.
    Nothing in the frozen program can clear the secondary flag except
    ``ba141-Reread`` reaching end of result. Widening this to both slots would
    fix a defect, and rule R-4 makes a defect fixed a failure.

    There is NO ``go to`` at the end: the paragraph FALLS THROUGH to
    ``ba999-end``. Callers reproduce that by calling this and then returning, so
    that :func:`ba_acas_dal_process` performs :func:`ba999_end`.

    Args:
        file_access: The caller's block, stamped with paragraph 20.
        session_state: The session holding both cursor slots.
    """
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba998-Free"])
    # `CALL "MySQL_free_result"` - the stored snapshot is released.
    _primary(session_state).free()
    _WORKING_STORAGE.stored_rows_pointer = None
    _LOG.debug(
        "ba998-Free released the PRIMARY result only; Most-Cursor-Set-2 is "
        "untouched (anomaly N-cursor2-leak) [common/salesMT.cbl:L1184]"
    )


def ba100_bad_function(file_access: FileAccess) -> None:
    """``ba100-Bad-Function.`` [common/salesMT.cbl:L1162-L1171].

    ::

        *> Houston; We have a problem
        move     990 to WE-Error.
        move     99 to Fs-Reply.

    **ANOMALY N-badfn-divergence - REPRODUCED, NOT FIXED.** The BRIDGE reports an
    unsupported function as ``(99, 990)`` - ``WeError.UNKNOWN_UNEXPECTED``, whose
    documented meaning is "Unknown/unexpected" - while its own HANDLER reports the
    same condition as ``(99, 999)`` [common/acas012.cbl:L573-L575], and
    ``dal/status.py`` carries a third code, ``992`` ``INVALID_FUNCTION``, that
    neither uses. Three codes for one condition, and the pair a caller sees
    depends on which layer rejected it: the handler's ``evaluate`` runs first, so
    a function it does not know never reaches the bridge and the caller sees
    ``999``; only a function the handler dispatches and the bridge does not know
    yields ``990``. Given both ``evaluate`` sets are the same nine codes plus 31,
    that second case is unreachable - which is itself worth recording, and is not
    corrected.

    Args:
        file_access: The block to write the status pair into.
    """
    file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
    file_access.fs_reply = int(FsReply.ERROR)


def ba020_process_open(
    file_access: FileAccess,
    session_state: BridgeSession,
) -> None:
    """``ba020-Process-Open.`` [common/salesMT.cbl:L416-L458].

    Six ``STRING ... X"00" INTO`` statements build the null-terminated C strings
    from the ``RDB-Data`` block - schema, host, user name, password, port and
    socket [:L419-L448] - then::

        move     1 to ws-No-Paragraph.
        PERFORM  MYSQL-1000-OPEN  THRU MYSQL-1090-EXIT.
        if       fs-reply not = zero
                 go   to ba999-end.
        move    "OPEN SALEDGER" to WS-File-Key
        move    zero   to Most-Cursor-Set

    The six ``STRING``s, the connect and its status are all
    :func:`~acas_posting.dal.connection.mysql_1000_open`'s: it takes the system
    record, reads the same six values from it, connects in the frozen source's own
    three steps and returns the frozen source's ``(99, 911)`` on any failure.
    Duplicating that here would put the credential handling in two places, which
    the agent brief forbids.

    ``move zero to Most-Cursor-Set`` clears the PRIMARY flag ONLY - the same
    one-sided treatment as ``ba998-Free``, so a stale ``Most-Cursor-Set-2`` also
    survives an open. Recorded with anomaly N-cursor2-leak.

    Args:
        file_access: The caller's block; the status and log fields are written
            into it.
        session_state: The session to store the connection on. Its
            :attr:`BridgeSession.system_record` must have been set by the
            handler's ``ba012-Test-WS-Rec-Size-2``, which is where the frozen
            program loads the credentials [common/acas012.cbl:L606-L646].
    """
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba020-Process-Open"])
    system_record = session_state.system_record
    if system_record is None:
        # The frozen program cannot reach this state: `ba012-Test-WS-Rec-Size-2`
        # always runs before the bridge is called. With `RDB-Data` still spaces
        # `mysql_real_connect` fails, and `Mysql-1100-Db-Error` reports
        # `(99, 911)` [copybooks/mysql-procedures.cpy:L127-L128]. The same pair
        # is reported here, so the observable status matches.
        _LOG.error(
            "%s open attempted with no system record: the credentials come "
            "from ba012-Test-WS-Rec-Size-2 [common/acas012.cbl:L637-L645]",
            BRIDGE,
        )
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.RDB_INIT_ERROR)
        file_access.logging_data.ws_file_key = _log_key("OPEN SALEDGER")
        return

    # `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT.` [common/salesMT.cbl:L446]
    # is a paragraph RANGE, not a single paragraph. Under the Agent Action Plan's
    # transformation rule 3 (§0.4.2) a `PERFORM ... THRU` becomes explicit
    # sequential calls to the spanned functions, so both ends of the range are
    # called here: the worker, then its convergence label. `Mysql-1090-Exit` is
    # `exit.` and nothing else [copybooks/mysql-procedures.cpy:L87-L88] - it
    # exists because two of the three failure arms `go to` it - so the second
    # call is an identity. It is written out rather than elided because R-5
    # requires the paragraph-to-function correspondence to survive even where the
    # paragraph has no statements, exactly as `aa_main_exit` does on the
    # handler side.
    outcome: OpenOutcome = mysql_1090_exit(
        mysql_1000_open(
            system_record,
            transport=session_state.transport,
            allow_frozen_placeholder_credentials=(
                session_state.allow_frozen_placeholder_credentials
            ),
        )
    )
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    if outcome.connection is None:
        # `if fs-reply not = zero  go to ba999-end.` [common/salesMT.cbl:L447-L448]
        # Class 3 - the section exits, and `WS-File-Key` is NOT written, so the
        # log record carries whatever the previous call left in it.
        _LOG.warning(
            "%s open failed with (%s, %s) [common/salesMT.cbl:L447-L448]",
            BRIDGE,
            outcome.fs_reply,
            outcome.we_error,
        )
        return

    session_state.connection = outcome.connection
    session_state.open_access_type = int(file_access.access_type)
    # `move "OPEN SALEDGER" to WS-File-Key` [common/salesMT.cbl:L456]
    file_access.logging_data.ws_file_key = _log_key("OPEN SALEDGER")
    # `move zero to Most-Cursor-Set` [common/salesMT.cbl:L457] - PRIMARY only.
    _primary(session_state).free()
    _WORKING_STORAGE.stored_rows_pointer = None


def ba030_process_close(
    file_access: FileAccess,
    session_state: BridgeSession,
) -> None:
    """``ba030-Process-Close.`` [common/salesMT.cbl:L460-L472].

    ::

        if      Cursor-Active
                perform ba998-Free.
        move     2 to ws-No-Paragraph.
        move    "CLOSE SALEDGER" to WS-File-Key.
        PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT

    The order matters and is preserved: the cursor is freed BEFORE the paragraph
    number and the log key are set, and the connection is closed last. The test
    is on ``Cursor-Active``, the PRIMARY flag, so an active ``Most-Cursor-Set-2``
    neither triggers the free nor is cleared by it - the sharpest observable form
    of anomaly N-cursor2-leak, since the connection then closes underneath a
    cursor the program still believes is active.

    The maintainer's changelog records that a second close used to live here:
    ``Remove fhlogger file close in Process-Close.``
    [common/salesMT.cbl:L106]. It is gone from the frozen source, so it is not
    reproduced - recorded as anomaly N-close-double-log.

    Args:
        file_access: The caller's block.
        session_state: The session whose connection is closed.
    """
    # `if Cursor-Active perform ba998-Free.` [common/salesMT.cbl:L459-L460]
    if _primary(session_state).cursor_active():
        ba998_free(file_access, session_state)

    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba030-Process-Close"])
    file_access.logging_data.ws_file_key = _log_key("CLOSE SALEDGER")

    connection = session_state.connection
    if connection is None:
        # `MYSQL-1980-CLOSE` calls `MySQL_close` on the global connection id
        # whatever it holds [copybooks/mysql-procedures.cpy]. With no connection
        # there is nothing to close and no status is written, which is what the
        # frozen paragraph does: it tests nothing after the close.
        _LOG.debug(
            "%s close with no open connection; nothing to do and no status "
            "written [common/salesMT.cbl:L468]",
            BRIDGE,
        )
        return
    mysql_1980_close(connection)
    mysql_1999_exit()
    session_state.connection = None
    session_state.open_access_type = 0


def ba010_initialise(
    file_access: FileAccess,
) -> FileFunction | None:
    """``ba010-Initialise.`` [common/salesMT.cbl:L372-L414].

    Clears the diagnostic text fields and then dispatches::

        *>     move     zero   to We-Error
        *>                        Fs-Reply.
        move     spaces to WS-MYSQL-Error-Message
                           WS-MYSQL-Error-Number
                           WS-Log-Where
                           WS-File-Key
                           SQL-Msg
                           SQL-Err
                           SQL-State.

    **ANOMALY N-start-stale AND N-delete-stale DEPEND ON THE COMMENTED-OUT LINES
    ABOVE, AND THEY STAY COMMENTED OUT.** [common/salesMT.cbl:L380-L382] would
    have zeroed both status fields on entry to every call. Because it does not
    run, a verb that writes neither field leaves the CALLER's previous pair
    visible - and two verbs do exactly that: ``ba060-Process-Start`` when the
    predicate matches no row and the driver reports no error [:L840-L853], and
    ``ba080-Process-Delete`` when the row is absent and the driver reports no
    error [:L931-L942]. Both then look like whatever happened last, typically
    success. Restoring the two lines would fix both defects at once, and rule R-4
    makes a defect fixed a failure.

    The maintainer's own note that the key guard belongs here and is absent is
    preserved as evidence [:L392-L393]::

        *>   Now Test for valid key for start, read-indexed and delete
        *>      REMOVED as not used here

    ``WS-MYSQL-Error-Number`` is cleared to SPACES here, not to the ``"0  "`` the
    later comparisons treat as "no error" [:L529 and its siblings]. So between
    this paragraph and the first ``MySQL_errno`` call the field holds a value that
    compares NOT EQUAL to ``"0  "`` - which no path observes, because every
    comparison is preceded by the call. Reproduced exactly, spaces and all.

    Args:
        file_access: The caller's block whose diagnostic fields are cleared.

    Returns:
        The function to dispatch, or ``None`` when the ``evaluate``'s
        ``when other`` arm is taken - ``go to ba100-Bad-Function``
        [common/salesMT.cbl:L413], whose ``*> 6 is spare / unused``
        comment names the gap.
    """
    # The two commented-out `move zero` statements are NOT reproduced - see the
    # docstring. [common/salesMT.cbl:L380-L382]
    _WORKING_STORAGE.ws_mysql_error_message = ""
    _WORKING_STORAGE.ws_mysql_error_number = "    "
    logging_data = file_access.logging_data
    logging_data.ws_log_where = ""
    logging_data.ws_file_key = ""
    logging_data.sql_msg = ""
    logging_data.sql_err = ""
    logging_data.sql_state = ""

    requested = int(file_access.file_function)
    for supported in SUPPORTED_FUNCTIONS:
        if requested == int(supported):
            return supported
    return None



#: ``01 ws-temp-ed pic 9(10).`` [common/salesMT.cbl:L220] - an unsigned ten-digit
#: DISPLAY field despite the ``-ed`` name. Every value logged through it is
#: rendered to exactly this width.
WS_TEMP_ED_DIGITS: Final[int] = 10


def _move_count_to_ws_temp_ed(count: int) -> str:
    """``move WS-MYSQL-Count-Rows to WS-Temp-Ed``.

    ``Ws-Mysql-Count-Rows`` is ``binary-double unsigned``
    [copybooks/mysql-variables.cpy:L73] and ``ws-temp-ed`` is ``pic 9(10)``, so
    the move renders the count as ten zero-padded digits and truncates any excess
    on the LEFT. Measured in the compiled oracle: 3 gives ``"0000000003"``, 0
    gives ``"0000000000"``, and 12345678901 gives ``"2345678901"``.

    Used by [common/salesMT.cbl:L540], [:L855] and [:L1063] - all three log tags.

    Args:
        count: ``WS-MYSQL-Count-Rows``.

    Returns:
        Exactly :data:`WS_TEMP_ED_DIGITS` digit characters.
    """
    return f"{abs(int(count)):0{WS_TEMP_ED_DIGITS}d}"[-WS_TEMP_ED_DIGITS:]


def _move_alphanumeric_to_ws_temp_ed(text: str) -> str:
    """``move HV-Sales-Key to ws-temp-ed`` - **ANOMALY N-tempedkey**.

    ``ba050-Process-Read-Indexed`` does not log the key it read directly. It
    routes it through the numeric ``ws-temp-ed`` first
    [common/salesMT.cbl:L756-L757]::

        move     HV-Sales-Key to ws-temp-ed.
        move    ws-temp-ed to WS-File-Key.

    while ``ba041-Reread`` [:L633] and ``ba141-Reread`` [:L1158] move
    ``HV-Sales-Key`` STRAIGHT into ``WS-File-Key``. So one program logs the same
    value two different ways, and because Sales customer keys are conventionally
    alphanumeric the read-indexed log record shows ten zeros for essentially every
    real key. **REPRODUCED, NOT FIXED** (rule R-4). Its blast radius is bounded
    and worth stating: ``WS-File-Key`` is a log field with no database effect, so
    this cannot move one column of any table dump - but it IS written back into
    the caller's ``Logging-Data`` through the linkage, so a caller can observe it
    and it is therefore reproduced exactly.

    THE RULE BELOW WAS MEASURED, NOT DERIVED. Twenty-three cases were run through
    the compiled GnuCOBOL 3.2 oracle and one rule fits all of them::

        "1234567" -> 0001234567    "12345 7" -> 0000123457    "12A4567" -> 0000000000
        "0000001" -> 0000000001    "1234 67" -> 0000123467    "1A34567" -> 0000000000
        "  12345" -> 0000012345    "12 4 67" -> 0000012467    "123A567" -> 0000000000
        " 123456" -> 0000123456    "123456A" -> 0000123456    "1234A67" -> 0000000000
        "123456 " -> 0000123456    "12345AB" -> 0000012345    "12345A7" -> 0000000000
        "-123456" -> 0000123456    "1234 AB" -> 0000001234    "A123456" -> 0000000000
        "+123456" -> 0000123456    "0000000" -> 0000000000    "ABCDEFG" -> 0000000000
                                   "       " -> 0000000000    "A      " -> 0000000000

    Note in particular that the SIGN IS DISCARDED rather than applied - the field
    is unsigned - and that interior SPACES ARE SKIPPED rather than terminating the
    scan, so ``"12 4 67"`` reads as 12467.

    Args:
        text: The sending alphanumeric field, ``HV-SALES-KEY PIC X(7)``.

    Returns:
        Exactly :data:`WS_TEMP_ED_DIGITS` digit characters.
    """
    body = text.lstrip(" ")
    if body[:1] in {"+", "-"}:
        # The sign is consumed and then thrown away: `pic 9(10)` is unsigned, and
        # the oracle returns +123456 for both "+123456" and "-123456".
        body = body[1:]
    digits: list[str] = []
    for position, character in enumerate(body):
        if character.isdigit():
            digits.append(character)
            continue
        if character == " ":
            # Interior spaces do not stop the scan: "12 4 67" reads as 12467.
            continue
        # The first character that is neither digit nor space stops the scan. What
        # happens next depends ENTIRELY on the remainder, per the measured cases:
        # trailing rubbish is tolerated and the digits so far stand, but a digit
        # after the rubbish voids the whole move.
        if any(rest.isdigit() for rest in body[position:]):
            digits = []
        break
    value = int("".join(digits)) if digits else 0
    return _move_count_to_ws_temp_ed(value)


def _select_rows(
    connection: Any,
    statement: str,
    parameters: Sequence[object],
) -> tuple[Mapping[str, object], ...]:
    """``PERFORM MYSQL-1210-COMMAND`` then ``PERFORM MYSQL-1220-STORE-RESULT``.

    The two paragraphs every ``SELECT`` in this bridge performs back to back,
    e.g. [common/salesMT.cbl:L512-L514]. One statement, one cursor, the whole
    result materialised, cursor closed.

    Args:
        connection: The live connection.
        statement: The assembled statement, identifiers already quoted.
        parameters: The values for its placeholders.

    Returns:
        Every qualifying row, in the order the statement returned them.

    Raises:
        Exception: Whatever the driver raises. Each caller translates it the way
            its own paragraph does, which is not the same way in every paragraph.
    """
    with execute_statement(connection, statement, parameters) as cursor:
        return _store_result(cursor)


def _sequential_where() -> str:
    """``ba040``'s predicate: the key at or after the lowest possible value.

    ``move spaces to WS-Where`` then one ``STRING`` with pointer J
    [common/salesMT.cbl:L485-L500]::

        `SALES-KEY` >= "0000000" ORDER BY `SALES-KEY` ASC

    The relation and the low key are the bridge's own hard-coded literals, taken
    from :data:`SEQUENTIAL_READ` so the vocabulary is stated once. The low key
    travels as a bound value rather than being formatted in, which is what
    :func:`~acas_posting.dal.connection.execute_statement` requires; the
    identifier is quoted, as the frozen ``STRING`` quotes it with backticks.

    Returns:
        The predicate, with one ``%s`` placeholder for the low key.
    """
    return (
        f"{QUOTED_KEY_COLUMN} {SEQUENTIAL_READ.relation.token} %s "
        f"ORDER BY {QUOTED_KEY_COLUMN} ASC"
    )


def _by_name_where() -> str:
    """``ba140``'s predicate: the same key range, ordered by name instead.

    [common/salesMT.cbl:L1010-L1022]::

        `SALES-KEY` >= 0000000 ORDER BY `SALES-NAME` ASC

    **ANOMALY N-lowkey-quoting - REPRODUCED, NOT FIXED.** ``ba040`` writes the
    low key as the COBOL literal ``'"0000000"'`` [:L491], with the SQL double
    quotes inside the COBOL literal, so MySQL receives a string. ``ba140`` writes
    ``"0000000"`` [:L1014] - a COBOL literal whose value is seven digit
    CHARACTERS with no SQL quotes - so MySQL parses it as the INTEGER ZERO and
    compares a ``char(7)`` column against a number. The two paragraphs are
    otherwise copies of each other. Reproduced by binding
    :data:`READ_BY_NAME_LOW_KEY`, an :class:`int`, where ``ba040`` binds a
    :class:`str`; see :func:`ba140_process_read_next`.

    The ordering column comes from
    :data:`~acas_posting.dal.cursor_state.EXTRA_READ_ORDERS` through
    :data:`READ_BY_NAME_ORDER`, and its declared quoting is honoured: this bridge
    declares :attr:`~acas_posting.dal.cursor_state.OrderQuoting.IDENTIFIER`, so
    the term is backtick-quoted and DOES order - unlike the single-quoted terms
    two other bridges declare, which order nothing.

    Returns:
        The predicate, with one ``%s`` placeholder for the low key.

    Raises:
        ValueError: If the declared ordering names no term, which would mean the
            frozen ``ORDER BY`` had been misread.
    """
    if not READ_BY_NAME_ORDER.order_terms:
        raise ValueError(
            f"{BRIDGE} declares no ORDER BY term for fn-Read-By-Name "
            f"{READ_BY_NAME_ORDER.source_locator}"
        )
    ordering: list[str] = []
    for term in READ_BY_NAME_ORDER.order_terms:
        if term.quoting is OrderQuoting.IDENTIFIER:
            rendered = quote_identifier(term.column_name)
        else:
            # A single-quoted term is a STRING CONSTANT and orders nothing. This
            # bridge does not declare one; the arm exists so that the declared
            # quoting decides, rather than this module assuming.
            rendered = f"'{term.column_name}'"
        ordering.append(f"{rendered} {term.direction}")
    return (
        f"{QUOTED_KEY_COLUMN} {SEQUENTIAL_READ.relation.token} %s "
        f"ORDER BY {', '.join(ordering)}"
    )


def _indexed_where() -> str:
    """``ba050``/``ba080``/``ba090``'s predicate: the key, exactly.

    One ``STRING`` producing ``\\`SALES-KEY\\`="<WS-Sales-Record (K:L)>"``
    [common/salesMT.cbl:L650-L658] for read-indexed, and character for character
    the same at [:L901-L910] for delete and [:L959-L968] for rewrite. All three
    use key of reference 1 and the same offset and length, so all three share this
    one builder.

    Returns:
        The predicate, with one ``%s`` placeholder for the key.
    """
    return f"{QUOTED_KEY_COLUMN}=%s"


def _start_where(relation_token: str) -> str:
    """``ba060``'s predicate: the key under the caller's relation, then ordered.

    [common/salesMT.cbl:L797-L812]::

        `SALES-KEY` <MOST-relation> "<WS-Sales-Record (K:L)>"
            ORDER BY `SALES-KEY` ASC

    The frozen ``STRING`` ends with ``' ASC  '`` - TWO trailing spaces where
    ``ba040`` has none [:L497 versus :L811] - which reaches MySQL as harmless
    whitespace and is preserved here so the assembled text matches.

    Args:
        relation_token: ``MOST-Relation`` trimmed, one of ``=``, ``<``, ``>``,
            ``>=``, ``<=``.

    Returns:
        The predicate, with one ``%s`` placeholder for the key.
    """
    return (
        f"{QUOTED_KEY_COLUMN} {relation_token} %s "
        f"ORDER BY {QUOTED_KEY_COLUMN} ASC  "
    )


def _record_diagnostics(
    file_access: FileAccess,
    errno: str,
    sqlstate: str,
    message: str,
) -> None:
    """The three-move block every failure path in this bridge writes.

    ``move WS-MYSQL-Error-Number to SQL-Err``,
    ``move WS-MYSQL-Error-Message to SQL-Msg`` and
    ``move WS-MYSQL-SqlState to SQL-State`` - e.g.
    [common/salesMT.cbl:L879-L884]. Each field is truncated to its own declared
    width [copybooks/wsfnctn.cob:L49-L51], because a ``MOVE`` into a shorter
    ``PIC X(n)`` truncates on the right.

    Args:
        file_access: The caller's block.
        errno: ``WS-MYSQL-Error-Number``.
        sqlstate: ``WS-MYSQL-SQLstate``.
        message: ``WS-MYSQL-Error-Message``.
    """
    logging_data = file_access.logging_data
    logging_data.sql_err = errno[:SQL_ERR_WIDTH]
    logging_data.sql_msg = message[:SQL_MSG_WIDTH]
    logging_data.sql_state = sqlstate[:SQL_STATE_WIDTH]


def ba040_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba040-Process-Read-Next.`` [common/salesMT.cbl:L474-L547].

    The SELECT stage of a sequential read, guarded by
    ``if Cursor-Not-Active`` so that it runs ONCE per walk. It positions with the
    bridge's own hard-coded relation and low key, stores the WHOLE result, logs
    the count, and then FALLS THROUGH into :func:`ba041_reread`, which delivers
    the first record.

    THE FALL-THROUGH IS NOT A ``GO TO``. The successful branch ends
    ``perform ba999-End`` [:L546] - a PERFORM, which returns - and the paragraph
    then simply ends, so control reaches ``ba041-Reread`` because it is the next
    paragraph. That mid-verb ``perform`` writes A SECOND LOG RECORD for one call,
    carrying the count tag; ``ba041`` then overwrites ``WS-File-Key`` with the key
    it fetched, so the count tag survives ONLY in the log. It is reproduced here,
    in place, because ``Log-File-Rec-Written`` is in the caller's linkage block
    and therefore counts twice for the call that opens a cursor.

    ``move "0000000" to WS-File-Key`` [:L521] runs BEFORE the count test and is
    overwritten by ``"No Data"`` on the empty path, so it is observable only when
    the driver raises between the two - which cannot happen here.

    **ANOMALY A11 (masked driver error) - REPRODUCED, NOT FIXED.** A failed
    statement does not surface as an error. ``Mysql-1210-Command`` performs
    ``Mysql-1100-Db-Error``, which sets ``(99, 911)``
    [copybooks/mysql-procedures.cpy:L127-L128] and does NOT transfer control, so
    execution continues with ``WS-MYSQL-Count-Rows`` at zero; the zero branch then
    OVERWRITES the pair with ``move 10 to fs-reply`` and ``move 10 to WE-Error``
    [common/salesMT.cbl:L534-L535]. So a broken statement and an empty table are
    indistinguishable to the caller, and only the ``"No Data"`` log tag
    distinguishes them at all.

    Args:
        file_access: The caller's block; the outcome is applied to it.
        dal_common: Needed because this paragraph performs ``ba999-End`` itself.
        sales: The record the fetch fills.
        session_state: The session holding the connection and the cursors.

    Returns:
        The outcome of the whole verb, SELECT stage and fetch together.
    """
    state = _primary(session_state)
    logging_data = file_access.logging_data

    if not state.cursor_not_active():
        # The guard did not fire, so the SELECT stage is skipped entirely and the
        # verb is just a fetch from the stored result. Class 2's mirror: no
        # transfer, an explicit sequential call.
        return ba041_reread(file_access, sales, session_state)

    # `set KOR-x1 to 1` / `move KOR-offset (KOR-x1) to K` /
    # `move KOR-length (KOR-x1) to L` [common/salesMT.cbl:L477-L479]
    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    _WORKING_STORAGE.ws_where = _sequential_where()
    # `WITH POINTER J` leaves J one PAST the last character written.
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba040-Process-Read-Next"])

    statement = (
        f"SELECT * FROM {QUOTED_TABLE} WHERE {_WORKING_STORAGE.ws_where};"
    )
    # `'"0000000"'` [common/salesMT.cbl:L491] - a STRING literal in the SQL text.
    parameters: tuple[object, ...] = (SEQUENTIAL_READ.low_key,)

    try:
        rows = _select_rows(session_state.require_connection(), statement, parameters)
    except Exception as error:  # noqa: BLE001 - every failure takes one path
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        _LOG.warning(
            "ba040-Process-Read-Next: the statement failed and is reported as "
            "end of file per [common/salesMT.cbl:L534-L535]; errno=%s state=%s",
            errno,
            sqlstate,
        )
        _record_diagnostics(file_access, errno, sqlstate, message)
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=sqlstate or str(SqlState.NO_DATA),
            file_key=_log_key("No Data"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        return outcome

    # `move "0000000" to WS-File-Key` [common/salesMT.cbl:L521] - before the test.
    logging_data.ws_file_key = _log_key(SEQUENTIAL_READ.low_key)
    _WORKING_STORAGE.ws_mysql_count_rows = state.store_result(rows)
    _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
    _WORKING_STORAGE.ws_mysql_sqlstate = ""
    _WORKING_STORAGE.ws_mysql_error_message = ""

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        # An empty table. `move 10 to fs-reply / move 10 to WE-Error /
        # move "No Data" to WS-File-Key / go to ba999-End` [:L525-L537]. The
        # cursor is deactivated by a bare `set Cursor-Not-Active`, NOT by
        # `ba998-Free`, so nothing is freed here.
        state.set_cursor_not_active()
        logging_data.sql_state = ""
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            file_key=_log_key("No Data"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        return outcome

    # `set Cursor-Active to true` [:L539] and the count tag [:L540-L545].
    state.key_of_reference = PRIMARY_KEY_OF_REFERENCE
    state.most_relation = SEQUENTIAL_READ.relation
    state.set_cursor_active()
    _WORKING_STORAGE.stored_rows_pointer = state
    _WORKING_STORAGE.ws_temp_ed = _move_count_to_ws_temp_ed(
        _WORKING_STORAGE.ws_mysql_count_rows
    )
    logging_data.ws_file_key = _log_key(
        f"> 0 got cnt={_WORKING_STORAGE.ws_temp_ed} recs"
    )
    # `perform ba999-End  *> log it` [:L546] - the mid-verb log record.
    ba999_end(file_access, dal_common)

    # Fall through into `ba041-Reread`, which is the next paragraph.
    return ba041_reread(file_access, sales, session_state)


def ba041_reread(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba041-Reread.`` [common/salesMT.cbl:L549-L637].

    The fetch stage of a sequential read: it advances the stored result and
    unloads one row into the caller's record. NO STATEMENT IS ISSUED HERE - the
    rows were all materialised by ``MYSQL-1220-STORE-RESULT``, which is why a
    walk survives other statements on the same connection.

    ``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT`` names all thirty-seven
    host variables [:L562-L599] and the copy is POSITIONAL - see
    :func:`_fetch_one_row`.

    Three exit tags, in the frozen source's own order, each reproduced:

    * ``"EOF"`` - ``return-code = -1``, the fetch found no further row
      [:L604-L609]. ``(10, 10)`` and the PRIMARY flag cleared.
    * ``"EOF2"`` - the count is zero AND the driver reports an error
      [:L611-L625]. This branch alone performs
      ``initialize WS-Sales-Record with filler``, which is anomaly N-initialize's
      second site: the ``with filler`` form CLEARS THE FILLERS, where
      ``bb100-UnloadHVs``'s plain ``initialize`` [:L1256] leaves them alone. Both
      forms are reproduced at their own sites and NOT normalised.
    * ``"EOF3"`` - **ANOMALY N-eof3-stale: the caller's own ``FS-Reply`` was
      already 10** [:L628-L632], with the identical test on the by-name path at
      [:L1151-L1155]. Nothing in this paragraph has written that field on the
      success path, and ``ba010-Initialise``'s status clears are commented out
      [:L374-L375], so the test reads what the CALLER passed in. A walk that has
      already reported end of file, and whose caller did not reset the field,
      reports end of file AGAIN - **discarding a row the fetch had already
      returned successfully** and freeing the cursor. CONFIRMED LIVE against the
      compiled oracle's schema: a ``fn-Read-By-Name`` issued straight after a
      ``fn-Read-Next`` walk hit EOF selected 3 rows
      (``> 0 got cnt=0000000003 recs in NAME order``) and then answered
      ``(10, 10)`` with ``WS-File-Key`` = ``"EOF3"``. Reproduced, not fixed.

    Args:
        file_access: The caller's block.
        sales: The record the unload fills.
        session_state: The session holding the cursors.

    Returns:
        The outcome, with :attr:`CursorOutcome.row` set on the success path.
    """
    state = _primary(session_state)
    logging_data = file_access.logging_data
    # `move spaces to WS-Log-Where.` [common/salesMT.cbl:L554]
    logging_data.ws_log_where = ""
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba041-Reread"])
    # `move zero to return-code.` [:L556]
    _WORKING_STORAGE.return_code = 0

    row = state.fetch_record()
    if row is None:
        # `if return-code = -1` [:L604-L609] - Class 3, section exit.
        _WORKING_STORAGE.return_code = -1
        end_fs_reply, end_we_error = end_of_file_status()
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement="",
            parameters=(),
            file_key=_log_key("EOF"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        # [:L611-L625]. Unreachable from `ba040`, which returns on a zero count -
        # but reachable in principle by a caller that calls this verb with a
        # cursor another path activated, so it is reproduced rather than dropped.
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            # `initialize WS-Sales-Record with filler` [:L619] - N-initialize.
            _initialize_sales_record(sales, with_filler=True)
            logging_data.ws_file_key = _log_key("EOF2")
        end_fs_reply, end_we_error = end_of_file_status()
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement="",
            parameters=(),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    if int(file_access.fs_reply) == int(FsReply.END_OF_FILE):
        # `if fs-reply = 10` [:L628-L632] - the CALLER's sticky end of file.
        # ANOMALY N-eof3-stale: a good fetched row is thrown away because
        # `ba010-Initialise` never clears the field [:L374-L375]. Not fixed.
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=FsReply.END_OF_FILE,
            we_error=int(file_access.we_error),
            row=None,
            statement="",
            parameters=(),
            file_key=_log_key("EOF3"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    # `perform bb100-UnloadHVs.` [:L633] then
    # `move HV-Sales-Key to WS-File-Key.` [:L634] and
    # `move zero to fs-reply WE-Error.` [:L635]
    _row_into_host_variables(row, _WORKING_STORAGE.host_variables)
    bb100_unload_hvs(_WORKING_STORAGE.host_variables, sales)
    state.position_at(row[PRIMARY_KEY_COLUMN])
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement="",
        parameters=(),
        file_key=_log_key(_WORKING_STORAGE.host_variables[PRIMARY_KEY_COLUMN]),
    )
    outcome.apply_to(file_access)
    logging_data.ws_log_where = ""
    return outcome


def ba050_process_read_indexed(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba050-Process-Read-Indexed.`` [common/salesMT.cbl:L639-L759].

    One row by exact key. SELECT, test, fetch, unload - and then
    ``go to ba998-Free`` on EVERY path, so a read-indexed always destroys the
    PRIMARY cursor and therefore any sequential walk in progress. That is not a
    side effect to be tidied away; it is the observable behaviour of the frozen
    program.

    **ANOMALY N-readindexed-23 - REPRODUCED, NOT FIXED, AND THE REASON THIS
    PARAGRAPH IS NOT DELEGATED.** When the key matches nothing this bridge
    writes ``23`` into ``FS-Reply`` and ZERO into ``We-Error``
    [common/salesMT.cbl:L680-L684]::

        if     WS-MYSQL-Count-Rows = zero
               move 23  to fs-Reply             *> could also be 21 or 14
               move zero to WE-Error
               go to ba998-Free

    while ``glpostingMT``'s same paragraph writes ``21`` and leaves ``We-Error``
    UNTOUCHED [common/glpostingMT.cbl:L633-L636], with the mirror-image comment
    ``*> could also be 23 or 14``. Two bridges, one condition, two different
    status pairs, and each maintainer comment names the other's value as an
    alternative. :func:`~acas_posting.dal.cursor_state.read_indexed` reproduces
    the ``glpostingMT`` form and has no per-table configuration to vary it, so
    calling it here would silently convert this bridge's ``(23, 0)`` into
    ``(21, unchanged)`` - a defect fixed, which rule R-4 makes a failure. Hence
    the paragraph is implemented here, against the same
    :class:`~acas_posting.dal.cursor_state.CursorState` primitives.

    Note also that the zero-count test does NOT consult ``errno`` at all, unlike
    every other zero-count test in this bridge. So a read-indexed whose statement
    FAILED reports ``(23, 0)`` - not found - with no diagnostic whatsoever.

    The two branches after the fetch [:L734-L753] carry ``(23, 990)`` and
    ``(23, 989)``. Both are unreachable, because a zero count has already
    returned above and ``WS-MYSQL-Count-Rows`` is not changed by a fetch. They are
    reproduced anyway: they are what the frozen program would do, and dropping
    them would make the paragraph's shape a judgement rather than a transcription.

    Args:
        file_access: The caller's block.
        sales: The record the unload fills.
        session_state: The session holding the connection and the cursors.

    Returns:
        The outcome. The cursor is freed before returning on every path.
    """
    state = _primary(session_state)
    logging_data = file_access.logging_data

    # `set KOR-x1 to 1` and the offset/length copy [common/salesMT.cbl:L645-L646]
    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    key_value = _record_key(sales)
    _WORKING_STORAGE.ws_where = _indexed_where()
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba050-Process-Read-Indexed"])

    statement = (
        f"SELECT * FROM {QUOTED_TABLE} WHERE {_WORKING_STORAGE.ws_where};"
    )
    parameters: tuple[object, ...] = (key_value,)

    try:
        rows = _select_rows(session_state.require_connection(), statement, parameters)
    except Exception as error:  # noqa: BLE001 - one path, per the docstring
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        # The zero-count test below does not consult errno, so a failed statement
        # reports `(23, 0)` with NO diagnostic: `SQL-Err`, `SQL-Msg` and
        # `SQL-State` are left as `ba010-Initialise` cleared them. The failure is
        # logged here so it is at least visible, which changes no status.
        _LOG.warning(
            "ba050-Process-Read-Indexed: the statement failed and is reported "
            "as not found with no diagnostic per "
            "[common/salesMT.cbl:L680-L684]; errno=%s state=%s",
            errno,
            sqlstate,
        )
        rows = ()

    if not rows:
        # `move 23 to fs-Reply / move zero to WE-Error / go to ba998-Free`
        # [:L681-L683] - Class 4: the named call, then return.
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        outcome = CursorOutcome(
            fs_reply=FsReply.KEY_NOT_FOUND,
            we_error=int(WeError.SUCCESS),
            row=None,
            statement=statement,
            parameters=parameters,
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        ba998_free(file_access, session_state)
        return outcome

    _WORKING_STORAGE.ws_mysql_count_rows = state.store_result(rows)
    _WORKING_STORAGE.stored_rows_pointer = state
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba050-Fetch"])
    row = state.fetch_record()

    if row is None or _WORKING_STORAGE.ws_mysql_count_rows <= 0:
        # [:L734-L753]. Unreachable, and reproduced - see the docstring.
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            we_error = int(WeError.UNKNOWN_UNEXPECTED)
        else:
            # `move zero to SQL-Err / move spaces to SQL-Msg` [:L747-L748]
            logging_data.sql_err = "0"
            logging_data.sql_msg = ""
            we_error = int(WeError.READ_INDEXED_UNEXPECTED)
        # `move spaces to WS-File-Key` on both arms [:L744, :L749]
        outcome = CursorOutcome(
            fs_reply=FsReply.KEY_NOT_FOUND,
            we_error=we_error,
            row=None,
            statement=statement,
            parameters=parameters,
        )
        outcome.apply_to(file_access)
        logging_data.ws_file_key = ""
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        ba998_free(file_access, session_state)
        return outcome

    # `perform bb100-UnloadHVs` [:L754], then the key through `ws-temp-ed`
    # [:L756-L757] - anomaly N-tempedkey - and `move zero to FS-Reply WE-Error`
    # [:L758].
    _row_into_host_variables(row, _WORKING_STORAGE.host_variables)
    bb100_unload_hvs(_WORKING_STORAGE.host_variables, sales)
    _WORKING_STORAGE.ws_temp_ed = _move_alphanumeric_to_ws_temp_ed(
        str(_WORKING_STORAGE.host_variables[PRIMARY_KEY_COLUMN])
    )
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement=statement,
        parameters=parameters,
        file_key=_log_key(_WORKING_STORAGE.ws_temp_ed),
    )
    outcome.apply_to(file_access)
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    ba998_free(file_access, session_state)
    return outcome


def ba060_process_start(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba060-Process-Start.`` [common/salesMT.cbl:L761-L865].

    Position the PRIMARY cursor and deliver nothing; the caller follows with a
    read-next. The cursor mechanics are DELEGATED to
    :func:`~acas_posting.dal.cursor_state.start`, which reproduces this
    paragraph step for step, and this function contributes only the parts that
    are specific to ``salesMT``: the paragraph number and the two ``WS-File-Key``
    writes.

    WHY THIS ONE IS DELEGATED AND ``ba050`` IS NOT. Delegation is only safe where
    the shared reproduction is exact. Here it is: both bridges guard with
    ``if access-type < 5 or > 8`` giving ``(99, 997)``, both free an active cursor
    first, both build one predicate with ``ORDER BY`` the key of reference, both
    set the cursor active before testing the count, both report a driver error as
    ``(21, 0)``, and both write NEITHER status field when the predicate simply
    matches nothing. ``ba050``'s zero-row pair differs between the two bridges, so
    it is implemented locally instead.

    **ANOMALY N-accesstype9 - REPRODUCED, NOT FIXED.** The guard's upper bound is
    8, so ``fn-not-greater-than`` (9) is refused with ``(99, 997)`` even though
    this very paragraph declares a relation arm for it
    [common/salesMT.cbl:L823-L824] labelled
    ``*> [ not currently used in ACAS ]`` and ``copybooks/wsfnctn.cob`` declares
    the condition name. The arm is dead and stays dead.

    **ANOMALY N-start-stale - REPRODUCED, NOT FIXED.** When the predicate matches
    no row and the driver reports no error, ``ba060`` writes neither status field
    [common/salesMT.cbl:L841-L853] - and because ``ba010-Initialise``'s two
    ``move zero`` statements are commented out [:L380-L382], the caller sees
    whatever it was carrying, typically the zero of a previous success. A START
    that found nothing therefore LOOKS like one that succeeded, while the cursor
    stays inactive.
    :attr:`~acas_posting.dal.cursor_state.CursorOutcome.status_written` is
    ``False`` on that path and nothing is written.

    ``Access-Type`` is passed through UNMODIFIED, because ``Sales-Start`` is the
    one facade verb that does not zero it
    [copybooks/Proc-ACAS-FH-Calls.cob:L680-L682] - so 5..9 IS the relation.

    Args:
        file_access: The caller's block, whose ``Access-Type`` carries the
            relation and to which the outcome is applied.
        sales: The record whose leading ``KEY_LENGTH`` characters are the key.
        session_state: The session holding the connection and the cursors.

    Returns:
        The outcome. :attr:`CursorOutcome.row` is always ``None``: the jump to the
        fetch is commented out in the frozen source, which is why a START must be
        followed by a read-next.
    """
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba060-Process-Start"])
    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    access_type = int(file_access.access_type)
    key_value = _record_key(sales)
    logging_data = file_access.logging_data

    # `move spaces to MOST-Relation.` [common/salesMT.cbl:L810] then the
    # evaluate. There is NO `when other`, so an Access-Type outside 5..9 leaves
    # the field as spaces - which the guard above makes unobservable.
    _WORKING_STORAGE.most_relation = RELATION_FOR_ACCESS_TYPE.get(
        access_type, "   "
    )
    if not start_access_type_is_valid(access_type):
        # `(99, 997)` and no statement issued [:L765-L769] - Class 3.
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            row=None,
            statement="",
            parameters=(),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        _LOG.debug(
            "ba060-Process-Start refused Access-Type %s; the guard at "
            "[common/salesMT.cbl:L765] admits 5..8 only, so 9 is dead "
            "(anomaly N-accesstype9)",
            access_type,
        )
        return outcome

    _WORKING_STORAGE.ws_where = _start_where(
        _WORKING_STORAGE.most_relation.strip()
    )
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    # `move WS-Sales-Record (K:L) to WS-File-Key` [:L815], before the SELECT.
    logging_data.ws_file_key = _log_key(key_value)

    connection = session_state.require_connection()
    with _bridge_cursor(connection) as cursor:
        outcome = _cursor_state.start(
            cursor,
            TABLE_NAME,
            key_value,
            access_type,
            key_number=ONLY_FILE_KEY_NO,
            slot=CursorSlot.PRIMARY,
            states=session_state.cursors,
            file_access=file_access,
        )

    state = _primary(session_state)
    _WORKING_STORAGE.stored_rows_pointer = state if state.cursor_active() else None
    # `CursorState.count_rows` is a PROPERTY, not a method: reading it is the
    # `move WS-Mysql-Count-Rows` equivalent, mirroring the bridge's
    # `MySQL-Count-Rows` host field rather than re-counting the result set.
    _WORKING_STORAGE.ws_mysql_count_rows = state.count_rows
    # `move WS-Where (1:J) to WS-Log-Where` [:L814] - the PREDICATE, not the
    # whole statement, which is what `CursorOutcome.apply_to` had just written.
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        # Either `(21, 0)` from the driver-error branch or, on the anomaly
        # N-start-stale path, nothing at all. `WS-File-Key` keeps the key written
        # above, since the frozen source only replaces it on the success branch.
        return outcome

    # `move zero to FS-Reply WE-Error` then the log tag [:L854-L862]:
    # `MOST-relation` + `WS-Sales-Record (K:L)` + `" got ="` + the count + `" recs"`.
    _WORKING_STORAGE.ws_temp_ed = _move_count_to_ws_temp_ed(
        _WORKING_STORAGE.ws_mysql_count_rows
    )
    logging_data.ws_file_key = _log_key(
        f"{_WORKING_STORAGE.most_relation}{key_value} got "
        f"={_WORKING_STORAGE.ws_temp_ed} recs"
    )
    return outcome


def ba070_process_write(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba070-Process-Write.`` [common/salesMT.cbl:L868-L893].

    ::

        perform  bb000-HV-Load.
        move     WS-Sales-Key to WS-File-Key.
        move     zero to FS-Reply WE-Error SQL-State
        move     spaces to SQL-Msg
        move     zero to SQL-Err
        move     10 to ws-No-Paragraph.
        perform  bb200-Insert.

    Note that ``SQL-State`` is cleared with ``move ZERO``, not ``move spaces``,
    even though it is ``pic x(5)`` [copybooks/wsfnctn.cob:L51] - so it becomes
    ``"0000 "``-shaped zero fill rather than blanks. Reproduced as the character
    zero fill a numeric move into an alphanumeric field gives.

    Duplicate-key classification is the frozen test, character for character
    [:L884-L889]::

        if    SQL-Err (1:4) = "1062" or = "1022" or Sql-State = "23000"
              move 22 to fs-reply
        else  move 99 to fs-reply

    and it is delegated to
    :func:`~acas_posting.dal.status.is_duplicate_key_bridge_level`, which states
    that test once for every bridge.

    **``We-Error`` IS NEVER WRITTEN ON THE FAILURE PATH.** The zero at the top
    stands, so a write that failed for any reason other than a duplicate reports
    ``(99, 0)`` - an error paired with "success". Reproduced, not fixed.

    Args:
        file_access: The caller's block.
        sales: The record to insert.
        session_state: The session holding the connection.

    Returns:
        The outcome, whose row is ``None``: a write returns no record.
    """
    logging_data = file_access.logging_data
    # `perform bb000-HV-Load.` [:L869] - where anomaly A-11's sign loss happens.
    bb000_hv_load(sales, _WORKING_STORAGE.host_variables)
    # `move WS-Sales-Key to WS-File-Key.` [:L870]
    logging_data.ws_file_key = _log_key(sales.ws_sales_key)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `move zero to ... SQL-State` [:L871] - a numeric move into `pic x(5)`.
    logging_data.sql_state = "0".rjust(SQL_STATE_WIDTH, "0")
    logging_data.sql_msg = ""
    logging_data.sql_err = "0".rjust(SQL_ERR_WIDTH, "0")
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba070-Process-Write"])

    try:
        _WORKING_STORAGE.ws_mysql_count_rows = bb200_insert(
            session_state.require_connection(), _WORKING_STORAGE.host_variables
        )
        _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
        _WORKING_STORAGE.ws_mysql_sqlstate = ""
        _WORKING_STORAGE.ws_mysql_error_message = ""
    except Exception as error:  # noqa: BLE001 - classified below, as the COBOL does
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message

    if _WORKING_STORAGE.ws_mysql_count_rows != 1:
        # `if WS-MYSQL-COUNT-ROWS not = 1` [:L876]. Everything inside depends on
        # errno being non-zero; when it is zero NOTHING is written and the
        # `(0, 0)` from the top of the paragraph stands.
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            duplicate = is_duplicate_key_bridge_level(
                logging_data.sql_err, logging_data.sql_state
            )
            file_access.fs_reply = int(
                FsReply.DUPLICATE_KEY if duplicate else FsReply.ERROR
            )
            # `We-Error` is deliberately NOT written here - see the docstring.
            _LOG.debug(
                "ba070-Process-Write: %s reported as %s with We-Error left at "
                "%s [common/salesMT.cbl:L884-L890]",
                "a duplicate key" if duplicate else "an error",
                file_access.fs_reply,
                file_access.we_error,
            )
    return CursorOutcome(
        fs_reply=FsReply(int(file_access.fs_reply)),
        we_error=int(file_access.we_error),
        row=None,
        statement="",
        parameters=(),
        status_written=False,
    )


def ba080_process_delete(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba080-Process-Delete.`` [common/salesMT.cbl:L895-L948].

    Delete one row by exact key.

    **THE STATEMENT HAS NO TRAILING SEMICOLON.**
    ``STRING "DELETE FROM " ... " WHERE " WS-Where (1:J) X"00"``
    [:L921-L929] - the ``";"`` that ``bb200-Insert`` [:L1766] and
    ``bb300-Update`` [:L2252] both write is absent here. Reproduced: the statement
    this module builds for a delete ends with the predicate.

    **ANOMALY N-delete-stale - REPRODUCED, NOT FIXED.** The failure block writes
    a status only when the driver reported an error [:L931-L942]::

        if       WS-MYSQL-COUNT-ROWS not = 1
                 call "MySQL_errno" ...
                 if    WS-MYSQL-Error-Number  not = "0  "
                       ... move 99 to fs-reply
                           move 995 to WE-Error
                 end-if
                 go to ba999-End
        else     move spaces to SQL-Msg
                 move zero   to SQL-Err
        end-if.
        move     zero to FS-Reply WE-Error.

    Deleting a row that is not there affects zero rows and raises nothing, so
    errno is ``"0  "``, the inner ``if`` does not fire, and ``go to ba999-End``
    jumps PAST the ``move zero to FS-Reply WE-Error`` two lines below. Neither
    status field is written, and because ``ba010-Initialise``'s clears are
    commented out [:L380-L382] the caller sees its previous pair - typically the
    zero of a success. **A delete of a non-existent row therefore reports
    success.** This is the same mechanism as anomaly N-start-stale and was not
    previously recorded anywhere; it is reproduced, and
    :attr:`CursorOutcome.status_written` is ``False`` on that path.

    Args:
        file_access: The caller's block.
        sales: The record whose key selects the row.
        session_state: The session holding the connection.

    Returns:
        The outcome, whose row is ``None``.
    """
    logging_data = file_access.logging_data
    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    key_value = _record_key(sales)
    _WORKING_STORAGE.ws_where = _indexed_where()
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    # `move WS-Sales-Record (K:L) to WS-File-Key.` [:L911]
    logging_data.ws_file_key = _log_key(key_value)
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba080-Process-Delete"])

    # No trailing `";"` - see the docstring.
    statement = (
        f"DELETE FROM {QUOTED_TABLE} WHERE {_WORKING_STORAGE.ws_where}"
    )
    parameters: tuple[object, ...] = (key_value,)

    try:
        with execute_statement(
            session_state.require_connection(), statement, parameters
        ) as cursor:
            _WORKING_STORAGE.ws_mysql_count_rows = int(
                getattr(cursor, "rowcount", 0) or 0
            )
        _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
        _WORKING_STORAGE.ws_mysql_sqlstate = ""
        _WORKING_STORAGE.ws_mysql_error_message = ""
    except Exception as error:  # noqa: BLE001 - classified below
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message

    if _WORKING_STORAGE.ws_mysql_count_rows != 1:
        status_written = False
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)
            status_written = True
        else:
            _LOG.warning(
                "ba080-Process-Delete affected %d row(s) with no driver error, "
                "so NEITHER status field is written and the caller keeps "
                "(%s, %s) - anomaly N-delete-stale "
                "[common/salesMT.cbl:L931-L942]",
                _WORKING_STORAGE.ws_mysql_count_rows,
                file_access.fs_reply,
                file_access.we_error,
            )
        # `go to ba999-End` - Class 3, jumping past the `move zero` below.
        return CursorOutcome(
            fs_reply=FsReply(int(file_access.fs_reply)),
            we_error=int(file_access.we_error),
            row=None,
            statement=statement,
            parameters=parameters,
            status_written=status_written,
        )

    # The `else` arm [:L940-L941] then the two `move zero`s [:L944].
    logging_data.sql_msg = ""
    logging_data.sql_err = "0".rjust(SQL_ERR_WIDTH, "0")
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    return CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=None,
        statement=statement,
        parameters=parameters,
        status_written=False,
    )


def ba090_process_rewrite(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba090-Process-Rewrite.`` [common/salesMT.cbl:L950-L993].

    Update one row by exact key, setting all thirty-seven columns.

    The order is the frozen order and it matters: ``bb000-HV-Load`` first [:L952],
    then the log key, then the paragraph number, then the predicate, and
    ``bb300-Update`` last [:L972]. The ``UPDATE``'s ``SET`` list includes the
    PRIMARY KEY, which is also the whole of its ``WHERE`` - see
    :func:`bb300_update`.

    On failure: ``(99, 994)``, but ONLY when the driver reported an error
    [:L977-L989]. When it did not - an ``UPDATE`` that matched no row, or one that
    changed nothing because every column already held the value being written -
    the block writes no status and ``go to ba999-End`` jumps past the
    ``move zero to FS-Reply WE-Error`` below, so the caller keeps its previous
    pair. The same stale-status mechanism again, and reproduced again.

    Args:
        file_access: The caller's block.
        sales: The record to write.
        session_state: The session holding the connection.

    Returns:
        The outcome, whose row is ``None``.
    """
    logging_data = file_access.logging_data
    # `perform bb000-HV-Load.` [:L952]
    bb000_hv_load(sales, _WORKING_STORAGE.host_variables)
    # `move WS-Sales-Key to WS-File-Key.` [:L953]
    logging_data.ws_file_key = _log_key(sales.ws_sales_key)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba090-Process-Rewrite"])
    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    key_value = _record_key(sales)
    _WORKING_STORAGE.ws_where = _indexed_where()
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)

    try:
        _WORKING_STORAGE.ws_mysql_count_rows = bb300_update(
            session_state.require_connection(),
            _WORKING_STORAGE.host_variables,
            key_value,
        )
        _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
        _WORKING_STORAGE.ws_mysql_sqlstate = ""
        _WORKING_STORAGE.ws_mysql_error_message = ""
    except Exception as error:  # noqa: BLE001 - classified below
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message

    statement_note = f"UPDATE {TABLE_NAME} WHERE {_WORKING_STORAGE.ws_where}"

    if _WORKING_STORAGE.ws_mysql_count_rows != 1:
        status_written = False
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.REWRITE_SQLSTATE_NOT_00000)
            status_written = True
        else:
            _LOG.warning(
                "ba090-Process-Rewrite affected %d row(s) with no driver error, "
                "so NEITHER status field is written and the caller keeps "
                "(%s, %s) [common/salesMT.cbl:L977-L990]",
                _WORKING_STORAGE.ws_mysql_count_rows,
                file_access.fs_reply,
                file_access.we_error,
            )
        return CursorOutcome(
            fs_reply=FsReply(int(file_access.fs_reply)),
            we_error=int(file_access.we_error),
            row=None,
            statement=statement_note,
            parameters=(key_value,),
            status_written=status_written,
        )

    # `move zero to FS-Reply WE-Error. move zero to SQL-Err.
    #  move spaces to SQL-Msg.` [:L991-L993]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = "0".rjust(SQL_ERR_WIDTH, "0")
    logging_data.sql_msg = ""
    return CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=None,
        statement=statement_note,
        parameters=(key_value,),
        status_written=False,
    )


def ba140_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba140-Process-Read-Next.`` [common/salesMT.cbl:L995-L1070].

    ``fn-Read-By-Name`` (31). The maintainer's own summary is the whole of it::

        *>  Like 040 except we do order by SALES-NAME

    and it is a copy of ``ba040`` with four differences, every one of which is
    preserved:

    1. It drives the SECOND cursor, ``Most-Cursor-Set-2``
       [:L1002 and :L1058], so a by-name walk and a by-key walk can be open at
       once - and ``ba998-Free`` can clear only the first, which is anomaly
       N-cursor2-leak.
    2. It orders by ``SALES-NAME`` [:L1016-L1019], a column with NO index in the
       frozen schema, while the predicate is still on ``SALES-KEY``.
    3. **ANOMALY N-lowkey-quoting** - its low key is unquoted, so MySQL compares
       a ``char(7)`` column against the integer zero. See :func:`_by_name_where`.
    4. Its paragraph number is 21 rather than 3, and its log tag ends
       ``" recs in NAME order"`` [:L1067].

    ``fn-Read-By-Name`` exists because ``sl165`` needed it; the handler's own
    changelog records the addition [common/acas012.cbl:L139]::

        *> 15/01/17 vbc - .05 Allow for fn-Read-By-Name used in SL165.

    Args:
        file_access: The caller's block.
        dal_common: Needed because this paragraph performs ``ba999-End`` itself.
        sales: The record the fetch fills.
        session_state: The session holding the connection and the cursors.

    Returns:
        The outcome of the whole verb.
    """
    state = _secondary(session_state)
    logging_data = file_access.logging_data

    if not state.cursor_not_active():
        return ba141_reread(file_access, sales, session_state)

    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    _WORKING_STORAGE.ws_where = _by_name_where()
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba140-Process-Read-Next"])

    statement = (
        f"SELECT * FROM {QUOTED_TABLE} WHERE {_WORKING_STORAGE.ws_where};"
    )
    # An `int`, not a `str` - anomaly N-lowkey-quoting.
    parameters: tuple[object, ...] = (READ_BY_NAME_LOW_KEY,)

    try:
        rows = _select_rows(session_state.require_connection(), statement, parameters)
    except Exception as error:  # noqa: BLE001 - masked as end of file, per ba040
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        _LOG.warning(
            "ba140-Process-Read-Next: the statement failed and is reported as "
            "end of file per [common/salesMT.cbl:L1057-L1058]; errno=%s "
            "state=%s",
            errno,
            sqlstate,
        )
        _record_diagnostics(file_access, errno, sqlstate, message)
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=sqlstate or str(SqlState.NO_DATA),
            file_key=_log_key("No Data"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        return outcome

    # `move "0000000" to WS-File-Key` [:L1041] - the TEXT form of the low key,
    # even though the predicate carried the unquoted integer.
    logging_data.ws_file_key = _log_key(READ_BY_NAME_LOW_KEY_TEXT)
    _WORKING_STORAGE.ws_mysql_count_rows = state.store_result(rows)
    _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
    _WORKING_STORAGE.ws_mysql_sqlstate = ""
    _WORKING_STORAGE.ws_mysql_error_message = ""

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        state.set_cursor_not_active()
        logging_data.sql_state = ""
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            file_key=_log_key("No Data"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        return outcome

    # `set Cursor-Active-2 to true` [:L1062] and the NAME-order log tag.
    state.key_of_reference = PRIMARY_KEY_OF_REFERENCE
    state.most_relation = SEQUENTIAL_READ.relation
    state.set_cursor_active()
    _WORKING_STORAGE.ws_temp_ed = _move_count_to_ws_temp_ed(
        _WORKING_STORAGE.ws_mysql_count_rows
    )
    logging_data.ws_file_key = _log_key(
        f"> 0 got cnt={_WORKING_STORAGE.ws_temp_ed} recs in NAME order"
    )
    # `perform ba999-End  *> log it` [:L1069]
    ba999_end(file_access, dal_common)

    return ba141_reread(file_access, sales, session_state)


def ba141_reread(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba141-Reread.`` [common/salesMT.cbl:L1072-L1161].

    ``ba041-Reread``'s twin for the by-name walk: the same three exit tags in the
    same order, the same thirty-seven-argument positional fetch
    [:L1085-L1122], the same ``initialize WS-Sales-Record with filler`` on the
    ``"EOF2"`` branch [:L1142], and the same sticky end-of-file test on the
    caller's own ``FS-Reply``. It differs in exactly two places: the paragraph
    number is 22, and every deactivation clears ``Most-Cursor-Set-2``.

    Args:
        file_access: The caller's block.
        sales: The record the unload fills.
        session_state: The session holding the cursors.

    Returns:
        The outcome, with :attr:`CursorOutcome.row` set on the success path.
    """
    state = _secondary(session_state)
    logging_data = file_access.logging_data
    logging_data.ws_log_where = ""
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba141-Reread"])
    _WORKING_STORAGE.return_code = 0

    row = state.fetch_record()
    if row is None:
        _WORKING_STORAGE.return_code = -1
        end_fs_reply, end_we_error = end_of_file_status()
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement="",
            parameters=(),
            file_key=_log_key("EOF"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            # `initialize WS-Sales-Record with filler` [:L1142] - the SECOND of
            # the two `with filler` sites, against the plain form at [:L1256].
            _initialize_sales_record(sales, with_filler=True)
            logging_data.ws_file_key = _log_key("EOF2")
        end_fs_reply, end_we_error = end_of_file_status()
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement="",
            parameters=(),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    # `if fs-reply = 10 / set Cursor-Not-Active-2 to true / move "EOF3" to
    # WS-File-Key / go to ba999-End` [common/salesMT.cbl:L1151-L1155] - the
    # by-name twin of the primary-path block at [:L628-L632], differing only in
    # setting `Cursor-Not-Active-2` rather than `Cursor-Not-Active`.
    # ANOMALY N-eof3-stale: the row fetched immediately above is DISCARDED
    # because the CALLER's stale `FS-Reply` still reads 10 and
    # `ba010-Initialise` never clears it [:L374-L375]. Not fixed.
    # AAP §0.4.2 Class 3 - `go to ba999-End` is a section exit -> `return`.
    if int(file_access.fs_reply) == int(FsReply.END_OF_FILE):
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=FsReply.END_OF_FILE,
            we_error=int(file_access.we_error),
            row=None,
            statement="",
            parameters=(),
            file_key=_log_key("EOF3"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    _row_into_host_variables(row, _WORKING_STORAGE.host_variables)
    bb100_unload_hvs(_WORKING_STORAGE.host_variables, sales)
    state.position_at(row[PRIMARY_KEY_COLUMN])
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement="",
        parameters=(),
        file_key=_log_key(_WORKING_STORAGE.host_variables[PRIMARY_KEY_COLUMN]),
    )
    outcome.apply_to(file_access)
    logging_data.ws_log_where = ""
    return outcome


def sales_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    sales: WsSalesRecord,
) -> CursorOutcome:
    """``PROCEDURE DIVISION using ...`` [common/salesMT.cbl:L354-L356].

    ::

        PROCEDURE DIVISION   using File-Access
                                   ACAS-DAL-Common-data
                                   WS-Sales-Record.   *>  Ws record

    **THREE parameters, in this order.** The bridge does NOT receive the system
    record or the file definitions the handler is given - which is why the
    credentials must already be in ``RDB-Data`` inside ``File-Access`` before the
    open, and why :class:`BridgeSession` carries the system record separately.
    The call site is ``call "salesMT" using File-Access ACAS-DAL-Common-data
    WS-Sales-Record`` [common/acas012.cbl:L658-L660].

    The section header ``ba-ACAS-DAL-Process section.`` [common/salesMT.cbl:L358]
    is reproduced as this function's prologue, minus its body: that body reads the
    terminal height and sets two curses environment variables
    [:L359-L369], which is presentation with no database effect and is dropped per
    Agent Action Plan section 0.3.4. Recorded as an omission.

    Args:
        file_access: ``File-Access``, carrying ``File-Function``, ``Access-Type``,
            the two status fields, ``RDB-Data`` and ``Logging-Data``.
        dal_common: ``ACAS-DAL-Common-data`` - the testing switches and the log
            record counter.
        sales: ``WS-Sales-Record`` - read on a write or rewrite, written on a
            read.

    Returns:
        The outcome, already applied to ``file_access``.
    """
    session_state = session()
    # `ba010-Initialise.` [common/salesMT.cbl:L378] - clears the diagnostics and
    # returns the dispatch decision. The two `move zero to We-Error / Fs-Reply`
    # statements above it stay commented out; see :func:`ba010_initialise`.
    requested = ba010_initialise(file_access)

    if requested is None:
        # `when other  go to ba100-Bad-Function` [:L409-L410] - Class 4.
        ba100_bad_function(file_access)
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.UNKNOWN_UNEXPECTED),
            row=None,
            statement="",
            parameters=(),
        )
        ba999_end(file_access, dal_common)
        ba999_exit()
        return outcome

    # `evaluate File-Function` [:L396-L411], in the frozen `when` order.
    if requested is FileFunction.OPEN:
        ba020_process_open(file_access, session_state)
        outcome = CursorOutcome(
            fs_reply=FsReply(int(file_access.fs_reply)),
            we_error=int(file_access.we_error),
            row=None,
            statement="",
            parameters=(),
            status_written=False,
        )
    elif requested is FileFunction.CLOSE:
        ba030_process_close(file_access, session_state)
        outcome = CursorOutcome(
            fs_reply=FsReply(int(file_access.fs_reply)),
            we_error=int(file_access.we_error),
            row=None,
            statement="",
            parameters=(),
            status_written=False,
        )
    elif requested is FileFunction.READ_NEXT:
        outcome = ba040_process_read_next(
            file_access, dal_common, sales, session_state
        )
    elif requested is FileFunction.READ_INDEXED:
        outcome = ba050_process_read_indexed(file_access, sales, session_state)
    elif requested is FileFunction.WRITE:
        outcome = ba070_process_write(file_access, sales, session_state)
    elif requested is FileFunction.RE_WRITE:
        outcome = ba090_process_rewrite(file_access, sales, session_state)
    elif requested is FileFunction.DELETE:
        outcome = ba080_process_delete(file_access, sales, session_state)
    elif requested is FileFunction.START:
        outcome = ba060_process_start(file_access, sales, session_state)
    else:
        # `when 31  go to ba140-Process-Read-Next` [:L407-L408]. The bridge gives
        # function 31 its OWN paragraph, unlike the handler, whose `when 3` and
        # `when 31` share one branch - anomaly N-when31 is a HANDLER anomaly, and
        # the two layers must not be made to agree.
        outcome = ba140_process_read_next(
            file_access, dal_common, sales, session_state
        )

    # Every arm reaches `ba999-end` and then `ba999-exit`.
    ba999_end(file_access, dal_common)
    ba999_exit()
    return outcome



# ===========================================================================
# SECTION 9 - THE HANDLER: `acas012`
# ===========================================================================
#
# `common/acas012.cbl` is a 679-line program with TWO halves, and the split is
# declared by a single test at [common/acas012.cbl:L316]:
#
#     if       not FS-Cobol-Files-Used
#              move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
#              perform ba-Process-RDBMS
#              go to AA-Main-Exit
#     end-if.
#
# Below that test the program drives an indexed (ISAM) file, `Sales-File`,
# declared by `copy "selsl.cob"` / `copy "fdsl.cob"` [:L238, :L243] and
# resolved to `salesled.dat` through `File-Defs.file-defs-a.file-12`. Above it
# the program hands the whole request to the bridge and returns.
#
# ---------------------------------------------------------------------------
# THE FLAT-FILE DECISION, RESOLVED IN WRITING
# ---------------------------------------------------------------------------
#
# The question this section had to settle before a line of it could be written
# is what the ISAM half becomes in a migration whose target store is MySQL.
# Four facts constrain the answer, and they point one way:
#
#   1. Agent Action Plan section 0.2.1.1 fixes the entity-to-table spine as
#      "Sales -> acas012 -> salesMT -> SALEDGER-REC", and section 0.2.2 freezes
#      the schema. Nothing anywhere in `acas_posting` implements an indexed
#      file: there is no ISAM module, no `Sales-File`, no `salesled.dat`. The
#      migrated system therefore always runs with `File-System-Used = 1`
#      (`88 FS-RDBMS-Used value 1` [copybooks/wsfnctn.cob:L79]), so the test at
#      [:L316] is always true and `dispatch` always takes the RDB branch.
#
#   2. The instructions for this file nevertheless require, item by item, one
#      Python function per paragraph of the frozen program - including every
#      `aa0NN` paragraph of the ISAM half - and require specifically that
#      `Open`-`extend` yield `WE-Error 997` / `FS-Reply 99`. That decision is
#      taken at [:L385-L389], BEFORE any file operation, so it is fully
#      reproducible with no ISAM anywhere.
#
#   3. The Zero Placeholder Policy forbids `pass`, `TODO`, a dummy return and
#      `NotImplementedError` standing in for work not done.
#
#   4. Rule R-4 makes silence the one unacceptable answer. A paragraph that
#      reported success without performing its `write` would not be a stub, it
#      would be a NEW behaviour - the exact class of change R-4 forbids.
#
# The resolution, applied uniformly below:
#
#   * Every paragraph of the ISAM half is a real function carrying its COMPLETE
#     status protocol, log-field writes and control flow. All of that is
#     storage-independent, and all of it is reproduced: the paragraph numbers,
#     the `WS-File-Key` tags, the `Cobol-File-Status` handling, the key moves
#     into the FD record area, the guards, the `WE-Error` / `FS-Reply` pairs and
#     every `GO TO` with its class.
#
#   * The FD record area `01 Sales-Record` [copybooks/fdsl.cob] IS modelled -
#     as a second :class:`~acas_posting.records.sales_ledger.WsSalesRecord` in
#     :class:`HandlerWorkingStorage`. The two copybooks are field-for-field
#     identical and both state "rec size 300 bytes", which is why
#     `ba012-Test-WS-Rec-Size-2`'s comparison can never fail (anomaly
#     N-recsize-unreachable). So `move WS-Sales-Record to Sales-Record`,
#     `move Sales-Record to WS-Sales-Record`, `move WS-Sales-Key to Sales-Key`
#     and `move Sales-Key to WS-File-Key` are all reproduced exactly.
#
#   * Only the eight ISAM VERBS themselves have no counterpart: `open`, `close`,
#     `read next`, `read ... key`, `start`, `write`, `rewrite`, `delete`. Each
#     is reached through :func:`_isam_verb`, which raises
#     :exc:`FlatFileStoreNotMigrated` naming the verb, the paragraph and the
#     locator. That is an explicit, documented refusal at exactly the point the
#     frozen program would have touched the file - never a silent success, never
#     a fabricated status. It is recorded as a deliberate omission per rule R-5,
#     and it is unreachable in the migrated system for the reason in fact 1.
#
#   * `dispatch` reproduces the [:L316] test verbatim rather than hard-wiring
#     the RDB branch, so a reader diffing the two programs finds the test where
#     the frozen program has it.
# ---------------------------------------------------------------------------

#: Whether an indexed-file store backs the flat-file half of this handler.
#:
#: Permanently ``False``. Agent Action Plan section 0.2.1.1 maps the Sales
#: entity onto ``SALEDGER-REC`` in MySQL and section 0.2.2 excludes schema
#: evolution and any new store, so no ISAM layer exists in ``acas_posting`` for
#: ``Sales-File`` [copybooks/selsl.cob, copybooks/fdsl.cob] to name. Declared as
#: a named constant rather than left implicit so that the one condition under
#: which :exc:`FlatFileStoreNotMigrated` can be raised is greppable.
FLAT_FILE_STORE_MIGRATED: Final[bool] = False

#: ``77 prog-name pic x(17) value "acas012 (3.3.00)"``
#: [common/acas012.cbl:L248].
HANDLER_PROG_NAME: Final[str] = "acas012 (3.3.00)"

#: ``03 SL901 pic x(31) value "SL901 Note error and hit return"``
#: [common/acas012.cbl:L260].
SL901: Final[str] = "SL901 Note error and hit return"

#: ``03 SL905 pic x(32) value "SL905 Program Error: Temp rec = "``
#: [common/acas012.cbl:L261].
SL905: Final[str] = "SL905 Program Error: Temp rec = "

#: ``77 Display-Blk pic x(75) value spaces`` [common/acas012.cbl:L253].
DISPLAY_BLK_WIDTH: Final[int] = 75

#: ``77 A pic 9(4) value zero`` / ``77 B pic 9(4) value zero``
#: [common/acas012.cbl:L251-L252], with the maintainer's own warning:
#: ``*> A & B used in 1st test ONLY`` / ``*> in ba-Process-RDBMS``, restated at
#: [:L600] as ``*> Test on very first call only (So do NOT use var A & B
#: again)``. Four digits, so a length above 9999 would truncate.
LENGTH_VARIABLE_DIGITS: Final[int] = 4

#: ``move 35 to fs-Reply`` [common/acas012.cbl:L368] - the open-input failure.
#:
#: ``FS-Reply`` is ``pic 99`` [copybooks/wsfnctn.cob:L25] and can hold any
#: two-digit value; :class:`~acas_posting.dal.status.FsReply` names only the six
#: the RDB path produces, and 35 is not among them. Kept as a plain ``int`` so
#: the value written into the caller's block is exactly the frozen program's.
FS_REPLY_OPEN_INPUT_FAILED: Final[int] = 35

#: ``move 1 to Cobol-File-Status  *> JIC above dont work :)``
#: [common/acas012.cbl:L433] - the value ``88 Cobol-File-Eof`` tests for
#: [:L254-L255].
COBOL_FILE_STATUS_EOF: Final[int] = 1

#: ``88 Testing-1 value 1`` over ``77 SW-Testing pic 9 value 1``
#: [copybooks/Test-Data-Flags.cob] - the condition both programs test before
#: writing a log record [common/acas012.cbl:L579, common/salesMT.cbl:L1190].
#: The VALUE clause is 1, so logging is ON by default; the maintainer's comment
#: on the handler's ``copy`` says how to stop it: ``*> set sw-testing to zero to
#: stop logging`` [common/acas012.cbl:L274].
TESTING_1_VALUE: Final[int] = 1


class FlatFileStoreNotMigrated(RuntimeError):
    """An ISAM verb on ``Sales-File`` was reached, and there is no ISAM store.

    Raised by :func:`_isam_verb` at the eight points in the flat-file half of
    ``acas012`` where the frozen program issues a COBOL file verb against
    ``Sales-File`` [copybooks/selsl.cob, copybooks/fdsl.cob]. Everything the
    paragraph does *around* the verb - the paragraph number, the log tags, the
    record and key moves, the status pairs - has already been performed when
    this is raised, so the caller's ``File-Access`` block holds exactly what the
    frozen program would have left in it up to that instant.

    Why an exception and not a status code: rule R-4 makes a fabricated success
    a new behaviour, and the Zero Placeholder Policy forbids a stub. Returning
    any ``FS-Reply`` here would be inventing one of those two. An exception is
    the only answer that neither invents a status nor hides the gap.

    Why not :exc:`~acas_posting.dal.status.AcasFileHandlerError`: that exception
    reproduces the IRS calling convention's per-handler error check, which
    ``goback``\\ s out of the program on an unrecoverable open
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364]. Agent Action Plan
    section 0.6.5 records that the General/Sales/Purchase convention has no such
    paragraph at all - its callers test the reply inline - so raising it from a
    Sales-convention handler would import behaviour this handler does not have.

    Unreachable in the migrated system: ``dispatch`` reaches the flat-file half
    only when ``File-System-Used`` is zero
    (``88 FS-Cobol-Files-Used`` [copybooks/wssystem.cob:L113]), and every migrated
    caller runs against MySQL. See :data:`FLAT_FILE_STORE_MIGRATED`.

    Attributes:
        verb: The COBOL verb the frozen program issues, quoted.
        paragraph: The paragraph it is issued from.
        locator: The ``[path:Lnnn]`` citation for that statement.
    """

    def __init__(self, verb: str, paragraph: str, locator: str) -> None:
        """Build the refusal with its three coordinates.

        Args:
            verb: The COBOL statement, e.g. ``"read Sales-File next record"``.
            paragraph: The frozen paragraph name, e.g. ``"aa041-Reread"``.
            locator: The ``[common/acas012.cbl:Lnnn]`` citation.
        """
        self.verb: Final[str] = verb
        self.paragraph: Final[str] = paragraph
        self.locator: Final[str] = locator
        super().__init__(
            f"{verb!r} in {paragraph} {locator} operates on the indexed file "
            "Sales-File (salesled.dat), which this migration does not "
            "implement: the Sales entity is mapped onto the MySQL table "
            f"{TABLE_NAME} for the whole of acas_posting (Agent Action Plan "
            "sections 0.2.1.1 and 0.2.2). Everything the paragraph does around "
            "the verb has already been applied to File-Access. Set "
            "File-System-Used to 1 (FS-RDBMS-Used) so acas012.dispatch takes "
            "the ba-Process-RDBMS branch [common/acas012.cbl:L316-L321]."
        )


def _isam_verb(verb: str, paragraph: str, locator: str) -> None:
    """Stand at an ISAM verb and refuse it, loudly and with citations.

    The single point through which every one of the eight COBOL file verbs in
    the flat-file half passes. Reaching it means the caller asked for
    ``File-System-Used = 0`` on a build that has no indexed store - see
    :class:`FlatFileStoreNotMigrated` for why that is answered with an exception
    rather than a status code.

    Args:
        verb: The COBOL statement being refused.
        paragraph: The paragraph issuing it.
        locator: Its ``[path:Lnnn]`` citation.

    Raises:
        FlatFileStoreNotMigrated: Always. The function has no success path;
            :data:`FLAT_FILE_STORE_MIGRATED` is a compile-time ``False``.
    """
    _LOG.error(
        "acas012 flat-file path reached %s in %s %s with no indexed store "
        "available; File-System-Used must be 1 for the migrated system",
        verb,
        paragraph,
        locator,
    )
    raise FlatFileStoreNotMigrated(
        verb=verb, paragraph=paragraph, locator=locator
    )


@dataclass
class HandlerWorkingStorage:
    """``working-storage section`` of ``acas012``
    [common/acas012.cbl:L245-L261] plus its ``file section`` [:L241-L243].

    One module-level instance stands for the loaded program's storage, which in
    COBOL persists between ``CALL``\\ s. That persistence is load-bearing here:
    ``A`` starting at zero is precisely how ``ba012-Test-WS-Rec-Size-2``
    recognises its first call [:L608], and ``Cobol-File-Status`` carrying the
    end-of-file flag across calls is how ``aa040`` recognises a walk that has
    already finished [:L419].

    Attributes:
        fd_record: ``fd Sales-File. 01 Sales-Record.`` [copybooks/fdsl.cob] -
            the FD record area, field-for-field identical to
            ``WS-Sales-Record``. Modelled because the handler moves whole
            records and single keys in both directions between it and the
            linkage record, and every one of those moves is observable.
        cobol_file_status: ``77 Cobol-File-Status pic 9 value zero`` [:L254].
        a: ``77 A pic 9(4) value zero`` [:L251] - the length of
            ``WS-Sales-Record``, and the first-call sentinel.
        b: ``77 B pic 9(4) value zero`` [:L252] - the length of
            ``Sales-Record``.
        display_blk: ``77 Display-Blk pic x(75) value spaces`` [:L253]. The
            frozen program only ever ``display``\\ s this, which Agent Action
            Plan section 0.3.4 drops as presentation with no database effect;
            the field is still built and retained so the diagnostic text is
            available to a log record and to a test.
    """

    fd_record: WsSalesRecord = field(default_factory=WsSalesRecord)
    cobol_file_status: int = 0
    a: int = 0
    b: int = 0
    display_blk: str = " " * DISPLAY_BLK_WIDTH

    @property
    def cobol_file_eof(self) -> bool:
        """``88 Cobol-File-Eof value 1`` [common/acas012.cbl:L255].

        Returns:
            ``True`` when ``Cobol-File-Status`` holds
            :data:`COBOL_FILE_STATUS_EOF`.
        """
        return int(self.cobol_file_status) == COBOL_FILE_STATUS_EOF

    def set_cobol_file_eof(self) -> None:
        """``set Cobol-File-EoF to true`` [common/acas012.cbl:L432]."""
        self.cobol_file_status = COBOL_FILE_STATUS_EOF


_HANDLER_STORAGE: HandlerWorkingStorage = HandlerWorkingStorage()


def handler_storage() -> HandlerWorkingStorage:
    """Return the loaded ``acas012`` program's WORKING-STORAGE.

    Returns:
        The single module-level :class:`HandlerWorkingStorage`. One instance,
        because a COBOL ``CALL`` re-enters a program that keeps its storage -
        and two of this program's decisions depend on that.
    """
    return _HANDLER_STORAGE


def reset_handler_storage() -> None:
    """Reload ``acas012``, restoring every VALUE clause.

    Equivalent to ``cancel "acas012"`` followed by a fresh ``CALL``: ``A`` and
    ``B`` return to zero so the next ``ba012-Test-WS-Rec-Size-2`` behaves as a
    first call [common/acas012.cbl:L608], ``Cobol-File-Status`` returns to zero
    [:L254], the FD record area is cleared and ``Display-Blk`` returns to spaces
    [:L253]. Exists for tests and for a harness driving several scenarios in one
    process; the frozen program has no such verb.
    """
    _HANDLER_STORAGE.fd_record = WsSalesRecord()
    _HANDLER_STORAGE.cobol_file_status = 0
    _HANDLER_STORAGE.a = 0
    _HANDLER_STORAGE.b = 0
    _HANDLER_STORAGE.display_blk = " " * DISPLAY_BLK_WIDTH


def _fs_reply_of(value: int) -> FsReply:
    """Present a raw ``FS-Reply pic 99`` value as the enum where it names one.

    ``03 Fs-Reply pic 99`` [copybooks/wsfnctn.cob:L25] holds any two-digit
    value, and the flat-file half writes one - 35, the open-input failure at
    [common/acas012.cbl:L368] - that :class:`~acas_posting.dal.status.FsReply`
    does not name. The authoritative channel is the caller's block, which always
    carries the exact integer; this helper only decides how the same integer is
    presented inside a :class:`~acas_posting.dal.cursor_state.CursorOutcome`.
    The value is never altered, so no diff can turn on this function.

    Args:
        value: Whatever ``File-Access.fs_reply`` holds.

    Returns:
        The matching :class:`~acas_posting.dal.status.FsReply` member, or the
        integer itself when no member has that value.
    """
    try:
        return FsReply(int(value))
    except ValueError:
        # `FsReply` is an `IntEnum`, so an `int` is interchangeable with a member
        # everywhere `CursorOutcome` uses the field. Preserving 35 exactly
        # matters more than the annotation.
        return cast(FsReply, int(value))


def _outcome_from_file_access(file_access: FileAccess) -> CursorOutcome:
    """Photograph the caller's block after a flat-file verb has written it.

    The flat-file half has no SQL and no row, so the returned outcome carries
    only the status pair, and ``status_written`` is ``False`` because the
    paragraphs have already written ``File-Access`` directly - exactly as the
    frozen program's ``MOVE``\\ s do, through the linkage.

    Args:
        file_access: The caller's ``File-Access`` block, already written.

    Returns:
        A :class:`~acas_posting.dal.cursor_state.CursorOutcome` mirroring
        ``FS-Reply``, ``WE-Error``, ``SQL-State`` and ``WS-File-Key``.
    """
    return CursorOutcome(
        fs_reply=_fs_reply_of(file_access.fs_reply),
        we_error=int(file_access.we_error),
        row=None,
        statement="",
        parameters=(),
        status_written=False,
        sql_state=str(file_access.logging_data.sql_state),
        file_key=str(file_access.logging_data.ws_file_key),
    )



def _move_record(source: WsSalesRecord, destination: WsSalesRecord) -> None:
    """``move Sales-Record to WS-Sales-Record`` and its inverse - a group MOVE.

    ``01 Sales-Record`` [copybooks/fdsl.cob] and ``01 WS-Sales-Record``
    [copybooks/wssl.cob] are field-for-field identical: same order, same picture
    clauses, same ``USAGE``, same ``REDEFINES``, same three ``FILLER`` items,
    both documented as "rec size 300 bytes". The ONLY textual difference is the
    key's name, ``Sales-Key`` against ``WS-Sales-Key``, which is why
    ``ba012-Test-WS-Rec-Size-2``'s length comparison can never fail (anomaly
    N-recsize-unreachable) and why one Python class can stand for both areas.

    A COBOL group ``MOVE`` between two identically described groups is a byte
    copy of the whole area, so every field crosses - including the ``FILLER``
    items that no ``MOVE`` of individual fields would carry. Reproduced by
    copying every declared field, deep-copying the three subordinate groups
    (``Sales-Address``, ``Quarters`` and its redefinition) so the two areas stay
    independent afterwards. Aliasing them would let a later write to the FD area
    silently alter the caller's linkage record, which no COBOL ``MOVE`` does.

    The four sites: ``move Sales-Record to WS-Sales-Record``
    [common/acas012.cbl:L440, :L477] on the two read paths, and
    ``move WS-Sales-Record to Sales-Record`` [:L539, :L562] on write and rewrite.

    Args:
        source: The area being read.
        destination: The area being written, mutated in place so the caller's
            own object identity survives - a COBOL ``MOVE`` never rebinds a
            linkage item.
    """
    for declared in dataclass_fields(source):
        setattr(
            destination, declared.name, deepcopy(getattr(source, declared.name))
        )


# ---------------------------------------------------------------------------
# 9.1 `aa-Process-Flat-File section.` [common/acas012.cbl:L285] - the ISAM half
#
# `select Sales-File assign file-12 / access dynamic / organization indexed /
#  status fs-reply / record key sales-key.` [copybooks/selsl.cob]
#
# Three facts from that SELECT govern every paragraph below:
#   * `status fs-reply` - the FILE STATUS field IS `Fs-Reply` inside the
#     CALLER's `File-Access` block [copybooks/wsfnctn.cob:L25]. So every COBOL
#     file verb writes the caller's status field directly, and `if Fs-Reply not
#     = zero` immediately after an `open` [:L367] is reading what the verb just
#     put there. Nothing copies it.
#   * `record key sales-key` - the single primary key, matching the one
#     `keyOfReference` the bridge declares [common/salesMT.cbl:L233] and the
#     lone `PRIMARY KEY (SALES-KEY)` of the frozen table [mysql/ACASDB.sql:L983].
#   * `access dynamic` - which is what makes `start` + `read next` legal, and is
#     the ISAM behaviour the bridge emulates with a stored result and a cursor.
# ---------------------------------------------------------------------------


def aa020_process_open(
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa020-Process-Open.`` [common/acas012.cbl:L361-L398].

    ::

         aa020-Process-Open.
         *>    move     spaces to WS-File-Key.     *> for logging
             move    "OPEN Sales Ledger File" to WS-File-Key
             move     201 to WS-No-Paragraph.
             if       fn-input
                      open input Sales-File
                      if   Fs-Reply not = zero
                           move 35 to fs-Reply
                           close Sales-File
                           go to aa999-Main-Exit
                      end-if
              else
               if     fn-i-o
                      open i-o Sales-File
                      if       fs-reply not = zero
                               close       Sales-File
                               open output Sales-File   *> Doesnt create in i-o
                               close       Sales-File
                               open i-o    Sales-File
                      end-if
               else
                if    fn-output
                      open output Sales-File   *> caller should check fs-reply
                else
                 if   fn-extend               *> Must not be used for ISAM files
        *>              open extend Sales-File
                      move 997 to WE-Error
                      move 99  to FS-Reply
                      go to aa999-main-exit
                 end-if
                end-if
               end-if
             end-if.
        *> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
             move     zero to Cobol-File-Status
             if       fs-reply not = zero
                      move 999 to WE-Error.
             go       to aa999-main-exit.  *> with test for dup processing

    **``fn-extend`` IS THE ONE BRANCH THAT NEEDS NO FILE.** The frozen program
    has commented the ``open extend`` out [:L386] - the comment
    ``*> Must not be used for ISAM files`` [:L385] says why - and replaced it
    with a pure status decision, ``997`` / ``99`` [:L387-L388]. So this branch
    is reproduced in full and returns; it never reaches :func:`_isam_verb`.
    Note that the facade publishes no ``Sales-Open-Extend`` verb at all
    [copybooks/Proc-ACAS-FH-Calls.cob:L652-L707], so 4 can only arrive from a
    caller that sets ``Access-Type`` by hand.

    **ANOMALY N-open-createdance - REPRODUCED, NOT FIXED.** The ``fn-i-o``
    branch answers a failed ``open i-o`` by ``close`` / ``open output`` /
    ``close`` / ``open i-o`` [:L376-L379], the maintainer's own comment being
    ``*> Doesnt create in i-o``. Two consequences survive: the intermediate
    ``open output`` TRUNCATES an existing file, and none of the four verbs' own
    statuses is tested, so the branch reports whatever the final ``open i-o``
    left. Widening it would fix a defect.

    **ANOMALY N-open-input-35 - REPRODUCED, NOT FIXED.** A failed ``open input``
    overwrites the driver's real status with a flat 35 [:L368] before closing,
    so the reason for the failure is destroyed and every cause reports the same
    code. 35 is not a value :class:`~acas_posting.dal.status.FsReply` names; see
    :data:`FS_REPLY_OPEN_INPUT_FAILED`.

    **ANOMALY N-open-nothing - REPRODUCED, NOT FIXED.** The four-way nest has no
    ``else`` of last resort: an ``Access-Type`` outside 1..4 falls straight
    through to [:L395] having opened nothing, and since ``FS-Reply`` was never
    written the paragraph reports whatever the caller left there. If that was
    zero, it reports SUCCESS for an open that did not happen.

    Args:
        file_access: ``File-Access``. ``Access-Type`` selects the branch;
            ``Fs-Reply`` is both the FILE STATUS field and the reported status.
        file_defs: ``File-Defs``, whose ``file-12`` names the file the SELECT
            assigns [copybooks/selsl.cob, copybooks/file12.cob]. Read for the
            log record; the frozen program relies on the main menu having set it
            (``*> File paths for Cobol File has already done in main menu
            module`` [:L328]).
        dal_common: ``ACAS-DAL-Common-data`` - carried so the paragraph's exit
            can log.

    Raises:
        FlatFileStoreNotMigrated: On ``fn-input``, ``fn-i-o`` or ``fn-output``,
            at the ``open`` itself. Every write the paragraph performs before
            that point has already been applied.
    """
    storage = handler_storage()
    # `move "OPEN Sales Ledger File" to WS-File-Key` [:L363]. The commented-out
    # `move spaces` above it [:L362] is NOT performed.
    file_access.logging_data.ws_file_key = _log_key("OPEN Sales Ledger File")
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa020-Process-Open"])

    access_type = int(file_access.access_type)
    flat_file_name = str(file_defs.file_defs_a.file_12).rstrip()

    if access_type == AccessType.INPUT:
        # `open input Sales-File` [:L366] - and its FILE STATUS is the caller's
        # `Fs-Reply` [copybooks/selsl.cob].
        _isam_verb(
            f"open input Sales-File ({flat_file_name})",
            "aa020-Process-Open",
            "[common/acas012.cbl:L366]",
        )
    elif access_type == AccessType.I_O:
        # `open i-o Sales-File` [:L374], then anomaly N-open-createdance.
        _isam_verb(
            f"open i-o Sales-File ({flat_file_name})",
            "aa020-Process-Open",
            "[common/acas012.cbl:L374]",
        )
    elif access_type == AccessType.OUTPUT:
        # `open output Sales-File  *> caller should check fs-reply` [:L383].
        _isam_verb(
            f"open output Sales-File ({flat_file_name})",
            "aa020-Process-Open",
            "[common/acas012.cbl:L383]",
        )
    elif access_type == AccessType.EXTEND:
        # `if fn-extend` [:L385] - the `open extend` is commented out [:L386] and
        # replaced by a status decision. Reproduced whole; no file is touched.
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        file_access.fs_reply = int(FsReply.ERROR)
        _LOG.warning(
            "aa020-Process-Open refused fn-extend with (99, 997): "
            "'Must not be used for ISAM files' "
            "[common/acas012.cbl:L385-L389]"
        )
        # `go to aa999-main-exit` [:L389] - Agent Action Plan 0.4.2 Class 3.
        aa999_main_exit(file_access, dal_common)
        return
    else:
        # ANOMALY N-open-nothing: no branch matched, nothing was opened, and
        # `FS-Reply` was never written [:L390-L393].
        _LOG.error(
            "aa020-Process-Open matched no branch for Access-Type %d: nothing "
            "was opened and FS-Reply was not written (anomaly N-open-nothing) "
            "[common/acas012.cbl:L390-L393]",
            access_type,
        )

    # `move zero to Cobol-File-Status` [:L395]. Unreachable for 1/2/3 because
    # the `open` above raises, and skipped for 4 because that branch returned;
    # retained so the paragraph is complete and so the `else` fall-through -
    # anomaly N-open-nothing - reaches it exactly as the frozen program does.
    storage.cobol_file_status = 0
    # `if fs-reply not = zero  move 999 to WE-Error.` [:L396-L397]. The
    # commented-out `move zeros to FS-Reply WE-Error` dated 27/07/16 [:L394] is
    # NOT performed, which is why a stale non-zero reply promotes to 999.
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        file_access.we_error = int(WeError.NOT_USED)
    # `go to aa999-main-exit.` [:L398] - Class 3.
    aa999_main_exit(file_access, dal_common)


def aa030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa030-Process-Close.`` [common/acas012.cbl:L400-L411].

    ::

         aa030-Process-Close.
             move     202 to WS-No-Paragraph.
             move     spaces to WS-File-Key.     *> for logging
             close    Sales-File.
        *> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
             move     zero to Cobol-File-Status.
             move    "CLOSE Sales Ledger File" to WS-File-Key.
             perform  aa999-main-exit.
             move     zero to  File-Function
                               Access-Type.              *> close log file
             perform  Ca-Process-Logs.
             go       to aa-main-exit.

    **TWO LOG RECORDS, THE SECOND WITH ITS FUNCTION ERASED.** This is the only
    paragraph in the program that ``perform``\\ s ``aa999-main-exit`` [:L407]
    instead of ``go``\\ ing to it, so control comes back; it then zeroes
    ``File-Function`` and ``Access-Type`` [:L408-L409] and logs a SECOND time
    [:L410]. Both records are written to the CALLER's block, so a caller
    inspecting ``File-Function`` after a close finds ZERO, not 2. That erasure is
    behaviour, not decoration, and is reproduced.

    **ANOMALY N-close-noclear - REPRODUCED, NOT FIXED.** The
    ``move zeros to FS-Reply WE-Error`` is commented out and dated [:L404], so a
    close reports whatever the previous verb left in the status pair. A close
    following a failure therefore looks like a failed close.

    Args:
        file_access: ``File-Access``. ``File-Function`` and ``Access-Type`` are
            both zeroed before the second log record.
        dal_common: ``ACAS-DAL-Common-data`` - both log records go through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``close`` [:L403]. Paragraph 202 and
            the blanked ``WS-File-Key`` have already been written, matching the
            frozen program's state at that instant exactly.
    """
    storage = handler_storage()
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa030-Process-Close"])
    # `move spaces to WS-File-Key.  *> for logging` [:L402].
    file_access.logging_data.ws_file_key = _log_key("")
    # `close Sales-File.` [:L403].
    _isam_verb(
        "close Sales-File",
        "aa030-Process-Close",
        "[common/acas012.cbl:L403]",
    )
    # Everything below reproduces the rest of the paragraph. Unreachable while
    # FLAT_FILE_STORE_MIGRATED is False, and retained because rule R-5 requires
    # the paragraph, not a fragment of it.
    storage.cobol_file_status = 0
    file_access.logging_data.ws_file_key = _log_key("CLOSE Sales Ledger File")
    # `perform aa999-main-exit.` [:L407] - a PERFORM, so control returns here.
    aa999_main_exit(file_access, dal_common)
    # `move zero to File-Function Access-Type.  *> close log file` [:L408-L409].
    file_access.file_function = 0
    file_access.access_type = 0
    # `perform Ca-Process-Logs.` [:L410] - the second record, function erased.
    ca_process_logs_acas012(file_access, dal_common)
    # `go to aa-main-exit.` [:L411] - Class 3, and it SKIPS `aa999-main-exit`,
    # which is why there are exactly two records and not three.
    aa_main_exit()


def aa040_process_read_next(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> bool:
    """``aa040-Process-Read-Next.`` [common/acas012.cbl:L413-L427].

    ::

         aa040-Process-Read-Next.
        *>
        *>   Process READs, 1st is read next then read by key This is processed
        *>    after Start code as its really Start/Read next
        *>
             move     203 to WS-No-Paragraph.
             if       Cobol-File-Eof
                      move 10 to FS-Reply
                                 WE-Error
                      move spaces to WS-Sales-Key
                                     SQL-Err
                                     SQL-Msg
                      stop "Cobol File EOF"               *> for testing
                      go to aa999-main-exit
             end-if.

    Reached by BOTH ``when 3`` and ``when 31`` [:L341-L343] - anomaly N-when31.
    The handler gives ``fn-Read-By-Name`` no separate paragraph, so on the
    flat-file path a by-name request performs a plain sequential read in KEY
    order, silently ignoring the ordering the caller asked for. The BRIDGE does
    honour it, in ``ba140-Process-Read-Next``
    [common/salesMT.cbl:L995-L1070], whose ``ORDER BY `SALES-NAME` ASC``
    [common/salesMT.cbl:L1015-L1019] is the ordering the handler drops; the
    two layers disagree and must not be made to agree.

    **ANOMALY N-stopliteral - REPRODUCED AS A LOG RECORD, NOT AS A HALT.** The
    end-of-file branch executes ``stop "Cobol File EOF"  *> for testing``
    [:L425] - debugging scaffolding left in a shipped handler, which in GnuCOBOL
    displays the literal and waits for a keystroke before continuing. Agent
    Action Plan section 0.3.4 rules that a prompt whose only effect is to block a
    terminal is dropped while the surrounding control transfer is preserved: the
    literal becomes a log record, the wait is an omission, and the
    ``go to aa999-main-exit`` after it is kept.

    **``WS-Sales-Key`` IS BLANKED, THE REST OF THE RECORD IS NOT.** [:L422] moves
    spaces to the key alone, leaving the previous customer's name, address and
    every figure in the caller's record. A caller that tests only the status is
    unaffected; one that reads the record after end of file sees a chimera. The
    reread has the same shape but clears the WHOLE record [:L434] - two different
    end-of-file dispositions in adjacent paragraphs.

    There is no ``go to`` at the end of the paragraph: it FALLS THROUGH to
    ``aa041-Reread`` [:L429]. Reproduced by returning ``None`` and having
    :func:`aa010_main` call :func:`aa041_reread` next.

    Args:
        file_access: ``File-Access``. ``FS-Reply``, ``WE-Error``, ``SQL-Err``
            and ``SQL-Msg`` are written on the end-of-file branch.
        sales: ``WS-Sales-Record`` - only ``WS-Sales-Key`` is blanked.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Returns:
        ``True`` when the end-of-file branch transferred to ``aa999-main-exit``
        [:L426] and the request is finished; ``False`` when the paragraph fell
        off its end into ``aa041-Reread`` [:L429]. COBOL expresses the difference
        with a ``GO TO`` and the absence of one; a Python caller needs it stated.
    """
    storage = handler_storage()
    _set_paragraph(
        file_access, WS_NO_PARAGRAPH_HANDLER["aa040-Process-Read-Next"]
    )
    if not storage.cobol_file_eof:
        # No `else`: fall through to `aa041-Reread` [:L429].
        return False

    # `move 10 to FS-Reply WE-Error` [:L420-L421] - the one status pair the
    # frozen sources write into BOTH fields, which is why
    # `end_of_file_status()` returns both halves.
    file_access.fs_reply, file_access.we_error = end_of_file_status()
    # `move spaces to WS-Sales-Key SQL-Err SQL-Msg` [:L422-L424]. The key only -
    # the other thirty-six fields of the record keep the previous row's values.
    _assign_record_value(
        sales,
        PRIMARY_KEY_COLUMN,
        _store_into_character_host_variable("", column=PRIMARY_KEY_COLUMN),
    )
    file_access.logging_data.sql_err = " " * SQL_ERR_WIDTH
    file_access.logging_data.sql_msg = " " * SQL_MSG_WIDTH
    # `stop "Cobol File EOF"  *> for testing` [:L425] - anomaly N-stopliteral.
    _LOG.info(
        'aa040-Process-Read-Next reached STOP "Cobol File EOF" - debugging '
        "scaffolding in a shipped handler; the literal is logged and the "
        "keystroke wait is omitted per Agent Action Plan 0.3.4 "
        "[common/acas012.cbl:L425]"
    )
    # `go to aa999-main-exit` [:L426] - Class 3.
    aa999_main_exit(file_access, dal_common)
    return True


def aa041_reread(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa041-Reread.`` [common/acas012.cbl:L429-L443].

    ::

         aa041-Reread.
             read     Sales-File next record at end
                      move 10 to we-error fs-reply        *> EOF
                      set Cobol-File-EoF to true
                      move 1 to Cobol-File-Status         *> JIC above dont work
                      initialize WS-Sales-Record
                      move "EOF" to WS-File-Key           *> for logging
                      go to aa999-main-exit
             end-read.
             if       FS-Reply not = zero
                      go to aa999-main-exit.
             move     Sales-Record to WS-Sales-Record.
             move     Sales-Key to WS-File-Key.
             move     zeros to WE-Error.
             go to    aa999-main-exit.

    **ONE reread, where ``acas006`` and ``acas007`` have two.** This program
    declares ``aa041-Reread`` only [common/acas012.cbl:L429]; the siblings
    declare ``aa041-Reread`` AND ``aa051-Reread``
    [common/acas006.cbl:L436, common/acas006.cbl:L461] and
    [common/acas007.cbl:L430, common/acas007.cbl:L451], the second serving
    their read-indexed path. Here ``aa050-Process-Read-Indexed`` reads inline
    instead [common/acas012.cbl:L465-L486]. Recorded as anomaly N-onereread;
    the handler cannot be made to match its siblings.

    **``set Cobol-File-EoF to true`` AND ``move 1 to Cobol-File-Status``, both.**
    [:L432-L433], the second carrying ``*> JIC above dont work :)``. The two
    statements are the same assignment written twice, because ``Cobol-File-Eof``
    is ``88 ... value 1`` over ``Cobol-File-Status`` [:L254-L255]. Reproduced as
    written - two calls, one effect - rather than collapsed, so the maintainer's
    distrust of his own condition name stays visible.

    **``initialize WS-Sales-Record`` - PLAIN, no ``with filler``** [:L434]. The
    bridge uses BOTH forms, ``with filler`` at [common/salesMT.cbl:L619] and
    [common/salesMT.cbl:L1142] and plain at [common/salesMT.cbl:L1256]; this
    handler uses only the plain form. The two are not interchangeable and are
    not normalised - anomaly N-initialize.

    **ANOMALY N-reread-noreply - REPRODUCED, NOT FIXED.** The success path clears
    ``WE-Error`` [:L442] but never touches ``FS-Reply``. It cannot be zero
    (the guard at [:L438] returned otherwise), so this is harmless as written -
    and it is asymmetric with every sibling paragraph, all of which move zeros to
    both. Left exactly as found.

    Args:
        file_access: ``File-Access``. ``FS-Reply`` is the FILE STATUS field the
            ``read`` itself writes [copybooks/selsl.cob].
        sales: ``WS-Sales-Record`` - the whole record is replaced from the FD
            area on success, or initialized on end of file.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``read ... next record`` [:L430], the
            paragraph's first statement.
    """
    storage = handler_storage()
    # `read Sales-File next record at end ... end-read.` [:L430-L437].
    _isam_verb(
        "read Sales-File next record",
        "aa041-Reread",
        "[common/acas012.cbl:L430]",
    )
    # --- The `at end` branch, reproduced in full [:L431-L436]. --------------
    if int(file_access.fs_reply) == int(FsReply.END_OF_FILE):
        # `move 10 to we-error fs-reply  *> EOF` [:L431] - note the frozen order
        # names WE-Error first here and FS-Reply first in `aa040` [:L420].
        file_access.fs_reply, file_access.we_error = end_of_file_status()
        # Both statements [:L432-L433], as written.
        storage.set_cobol_file_eof()
        storage.cobol_file_status = COBOL_FILE_STATUS_EOF
        # `initialize WS-Sales-Record` - plain [:L434].
        _initialize_sales_record(sales, with_filler=False)
        file_access.logging_data.ws_file_key = _log_key("EOF")
        # `go to aa999-main-exit` [:L436] - Class 3.
        aa999_main_exit(file_access, dal_common)
        return
    # `if FS-Reply not = zero  go to aa999-main-exit.` [:L438-L439] - Class 3.
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        aa999_main_exit(file_access, dal_common)
        return
    # `move Sales-Record to WS-Sales-Record.` [:L440] - the whole FD area.
    _move_record(storage.fd_record, sales)
    # `move Sales-Key to WS-File-Key.` [:L441] - the FD record's key, not the
    # linkage record's. See :func:`_move_record` on why both are the same class.
    file_access.logging_data.ws_file_key = _log_key(
        _record_value(storage.fd_record, PRIMARY_KEY_COLUMN)
    )
    # `move zeros to WE-Error.` [:L442] - WE-Error only; anomaly N-reread-noreply.
    file_access.we_error = int(WeError.SUCCESS)
    # `go to aa999-main-exit.` [:L443] - Class 3.
    aa999_main_exit(file_access, dal_common)


def aa045_eval_keys(file_access: FileAccess, sales: WsSalesRecord) -> None:
    """``aa045-Eval-Keys.`` [common/acas012.cbl:L447-L463].

    ::

        *>   The next block will never get executed unless performed  so is it
        *>    needed ?
         aa045-Eval-Keys.
             evaluate File-Function      *> Set up keys just for logging
                      when  4             *> fn-read-indexed
                      when  5             *> fn-write
                      when  7             *> fn-re-write
                      when  8             *> fn-delete    For delete can ignore
                      when  9             *> fn-start
                            evaluate  File-Key-No
                                      when   1
                                             move WS-Sales-Key to WS-File-Key
                                                                  Sales-Key
                                      when   other
                                             move spaces  to WS-File-Key
                            end-evaluate
                      when  other
                            move   spaces  to WS-File-Key
             end-evaluate.

    **NAMED ``aa045`` HERE AND ``aa047`` IN ``acas005``** - the same idea, two
    names, two digits apart. Recorded as anomaly N-evalname; neither is renamed.

    **THE MAINTAINER'S OWN COMMENT IS THE ANOMALY.** ``*> The next block will
    never get executed unless performed so is it needed ?`` [:L445]. He is right
    that only one paragraph performs it - ``aa050-Process-Read-Indexed`` at
    [:L470] - so the four other functions its ``when`` list covers (5 write,
    7 re-write, 8 delete, 9 start) NEVER reach it, and each of those paragraphs
    does its own key move instead. The dead arms are reproduced rather than
    pruned: the list is evidence of intent, and a future ``perform`` from
    ``aa070`` would change behaviour if they had been removed. Recorded as
    anomaly N-evalkeys-dead.

    **The comment ``*> Set up keys just for logging`` [:L448] understates it.**
    The ``when 1`` arm moves the key into ``Sales-Key`` as well as into
    ``WS-File-Key`` [:L456-L457], and ``Sales-Key`` is the FD record's key -
    the field the ``read ... key`` in ``aa050`` searches on [:L473]. So this
    paragraph does not merely prepare a log field, it positions the read. That
    is why it is performed there and only there.

    Args:
        file_access: ``File-Access``. ``File-Function`` and ``File-Key-No``
            select the arm; ``WS-File-Key`` receives the result.
        sales: ``WS-Sales-Record`` - ``WS-Sales-Key`` is the source.
    """
    storage = handler_storage()
    function = int(file_access.file_function)
    if function in _AA045_KEYED_FUNCTIONS:
        if int(file_access.logging_data.file_key_no) == ONLY_FILE_KEY_NO:
            # `move WS-Sales-Key to WS-File-Key, Sales-Key` [:L456-L457] - and
            # the second destination is the FD record's key, which positions the
            # indexed read in `aa050`.
            key_text = str(_record_value(sales, PRIMARY_KEY_COLUMN))
            file_access.logging_data.ws_file_key = _log_key(key_text)
            _assign_record_value(
                storage.fd_record,
                PRIMARY_KEY_COLUMN,
                _store_into_character_host_variable(
                    key_text, column=PRIMARY_KEY_COLUMN
                ),
            )
        else:
            # `when other  move spaces to WS-File-Key` [:L458-L459]. Note the
            # FD key is NOT cleared, so it keeps whatever the last call left.
            file_access.logging_data.ws_file_key = _log_key("")
    else:
        # `when other  move spaces to WS-File-Key` [:L461-L462].
        file_access.logging_data.ws_file_key = _log_key("")


#: The five ``when`` values ``aa045-Eval-Keys`` treats as keyed
#: [common/acas012.cbl:L449-L453]. Four of them are unreachable, because only
#: ``aa050-Process-Read-Indexed`` performs the paragraph [:L470] - anomaly
#: N-evalkeys-dead. Kept whole because the frozen list is whole.
_AA045_KEYED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.RE_WRITE),
        int(FileFunction.DELETE),
        int(FileFunction.START),
    }
)



# ---------------------------------------------------------------------------
# `move spaces to WS-Sales-Record` - ANOMALY N-spacesrecord, MEASURED
#
# `aa050-Process-Read-Indexed` answers a failed indexed read by moving SPACES
# over the whole record [common/acas012.cbl:L480]. A group MOVE of spaces sets
# every byte of the 300-byte area to 0x20 - it does NOT zero the twenty-three
# numeric fields, it fills them with space bytes, which then read back as data.
# Compare `aa041-Reread`, which answers end of file with a proper
# `initialize WS-Sales-Record` [:L434]: two different "empty record"
# dispositions in adjacent paragraphs, and only one of them is clean.
#
# What the numeric fields actually hold was MEASURED in the compiled oracle
# (GnuCOBOL 3.2.0), not reasoned about, per rule R-6. The measurements:
#
#     pic 9(n) / 9(n)V9(m) DISPLAY  -> n SPACE CHARACTERS; `IS NUMERIC` FALSE
#     COMP / BINARY-* width 1 byte  -> 32                    (0x20)
#     COMP / BINARY-* width 2 bytes -> 8224                  (0x2020)
#     COMP / BINARY-* width 4 bytes -> 538976288             (0x20202020)
#     COMP / BINARY-* width 8 bytes -> 2314885530818453536   (0x2020...20)
#     ... then scaled by the picture's implied decimal places
#     COMP-3 with D digits          -> ceil((D+1)/2) bytes of 0x20; nibbles
#                                      alternate 2,0; the value is the LAST D
#                                      nibbles and the sign nibble 0 reads as
#                                      POSITIVE. For s9(8)v99: 2020202.02
#
# Byte widths were measured too, because they decide the value:
#     9(1)->1  9(3)->2  9(5)->4  9(10)->8  binary-char->1
#     binary-short->2  binary-long->4  s9(8)v99 comp-3->6
# ---------------------------------------------------------------------------

#: ``move spaces`` over a binary field of W bytes, as an unsigned big-endian
#: integer of 0x20 repeated W times. Measured, not computed, so the table is
#: evidence rather than derivation - although ``int.from_bytes(b" " * w, "big")``
#: reproduces every entry, which is the cross-check.
SPACE_FILLED_BINARY_BY_WIDTH: Final[Mapping[int, int]] = MappingProxyType(
    {
        1: 32,
        2: 8224,
        4: 538976288,
        8: 2314885530818453536,
    }
)

#: The ``COMP`` byte width GnuCOBOL gives a field of N declared digits, measured
#: with ``function length`` against the compiled oracle: ``9(1)`` -> 1,
#: ``9(3)`` -> 2, ``9(5)`` -> 4, ``9(10)`` -> 8. Each row is an inclusive upper
#: bound on the digit count.
BINARY_WIDTH_BY_DIGITS: Final[tuple[tuple[int, int], ...]] = (
    (2, 1),
    (4, 2),
    (9, 4),
    (18, 8),
)

#: The byte width of each ``USAGE`` that declares its own size rather than
#: deriving one from a picture clause. ``BINARY-CHAR`` was measured directly
#: (``function length`` returned 1) and ``BINARY-SHORT`` / ``BINARY-LONG`` were
#: measured through their space-filled values, 8224 and 538976288, which are two
#: and four bytes of 0x20. ``COMP-5`` and ``POINTER`` do not occur in
#: ``SALEDGER-REC`` but are sized here so the table is total over
#: :class:`~acas_posting.dictionary.model.Usage` and a future record cannot fall
#: through it silently.
BINARY_WIDTH_BY_USAGE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "BINARY-CHAR": 1,
        "BINARY-SHORT": 2,
        "BINARY-LONG": 4,
        "COMP-5": 8,
        "POINTER": 8,
    }
)


def _space_filled_binary_width(digits: int) -> int:
    """The byte width of a ``COMP`` field of ``digits`` declared digits.

    From :data:`BINARY_WIDTH_BY_DIGITS`, whose four rows were measured with
    ``function length`` against the compiled oracle: 1-2 digits occupy one byte,
    3-4 two, 5-9 four, 10-18 eight.

    Args:
        digits: The picture clause's total digit count.

    Returns:
        The field's width in bytes.
    """
    for upper, width in BINARY_WIDTH_BY_DIGITS:
        if digits <= upper:
            return width
    return 8


def _space_filled_value(column: str) -> Decimal | int | str:
    """What one field of ``SALEDGER-REC`` holds after ``move spaces``.

    Drives entirely off the field's dictionary entry - its ``USAGE``, digit count
    and scale - so the answer for each of the thirty-seven columns is derived
    from the same authority every other conversion in this module uses, rather
    than from a hand-written table of thirty-seven values.

    Args:
        column: The column whose feeding field is being space-filled.

    Returns:
        For a character field, spaces at its declared width. For a
        DISPLAY-numeric field, spaces at its digit count - the frozen field is
        genuinely not a number, and ``IS NUMERIC`` reports false on it. For a
        ``COMP`` / ``BINARY-*`` field, the measured integer, divided by
        ``10 ** scale`` as a :class:`~decimal.Decimal` when the picture has an
        implied decimal point. For a ``COMP-3`` field, the packed reading of
        alternating 2 and 0 nibbles.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    entry = ENTRIES[column]
    copybook = entry.copybook
    if column in CHARACTER_COLUMNS or copybook.is_group:
        return _store_into_character_host_variable("", column=column)

    digits = int(copybook.digits or 0)
    scale = int(copybook.scale or 0)
    usage = getattr(copybook.usage, "value", str(copybook.usage)).upper()

    if usage == "COMP-3":
        # A packed field of D digits occupies ceil((D + 1) / 2) bytes, one nibble
        # per digit plus a trailing sign nibble, and any surplus nibble is the
        # HIGH-ORDER one. So of the 2 * width nibbles of alternating 2 and 0, the
        # used ones are the LAST D + 1: D digits then the sign. Sign nibble 0 is
        # not one of COBOL's three defined signs and the oracle reads it as
        # POSITIVE. Measured for `s9(8)v99` - 6 bytes, digits 0202020202, sign 0,
        # scale 2 - which is 2020202.02.
        width = (digits + 2) // 2
        used = ("20" * width)[-(digits + 1) :] if digits else ""
        unscaled = int(used[:digits]) if digits else 0
    elif usage in BINARY_WIDTH_BY_USAGE:
        # BINARY-CHAR / BINARY-SHORT / BINARY-LONG declare no picture clause, so
        # their width comes from the USAGE itself, not from a digit count. This
        # is the branch the eleven statistics fields take:
        # `03 Sales-Late-Min binary-short.` [copybooks/wssl.cob:L43] and the nine
        # `binary-long` fields [:L45-L53].
        unscaled = SPACE_FILLED_BINARY_BY_WIDTH[BINARY_WIDTH_BY_USAGE[usage]]
    elif usage == "COMP":
        unscaled = SPACE_FILLED_BINARY_BY_WIDTH[
            _space_filled_binary_width(digits)
        ]
    else:
        # DISPLAY numeric: the field holds space characters and is NOT numeric.
        # The oracle confirms it - `IS NUMERIC` reported false on both `pic 9`
        # and `pic 9(4)` after the move.
        return " " * digits

    if scale:
        return Decimal(unscaled).scaleb(-scale)
    return unscaled


#: Every column's value after ``move spaces to WS-Sales-Record``, resolved once
#: at import so the result is a constant a test can assert against and two
#: processes agree on byte for byte.
SPACE_FILLED_RECORD: Final[Mapping[str, Decimal | int | str]] = (
    MappingProxyType({column: _space_filled_value(column) for column in COLUMN_ORDER})
)


def _move_spaces_to_sales_record(sales: WsSalesRecord) -> None:
    """``move spaces to WS-Sales-Record`` [common/acas012.cbl:L480].

    **ANOMALY N-spacesrecord - REPRODUCED, NOT FIXED.** See the block comment
    above for the measured values. The caller's record comes back holding a
    82.24 discount, 8224 in both late-day limits, 538976288 in each of the nine
    ``binary-long`` statistics and 2020202.02 in each of the seven money fields -
    garbage that is indistinguishable from data to any caller that does not test
    the status first.

    **A RECORDED OMISSION (rule R-5).** Ten fields are DISPLAY numeric -
    ``Sales-Status`` through ``Notes-Tag``, ``Sales-Credit`` and
    ``Sales-Stats-Date`` - and in the frozen program they hold SPACE CHARACTERS,
    which ``IS NUMERIC`` reports false on. They are typed ``int`` in
    :mod:`acas_posting.records.sales_ledger`, so the measured space text is
    stored into them verbatim: that is what the frozen field contains. A caller
    that then uses one arithmetically raises a Python :exc:`TypeError` where
    COBOL would have produced silent garbage. The divergence is recorded rather
    than papered over with a zero, which would have invented a value the frozen
    program does not hold.

    Unreachable in this migration on two independent grounds:
    :data:`FLAT_FILE_STORE_MIGRATED` is ``False``, and even on the flat-file path
    the ``read ... key`` at [:L473] raises before [:L480] can run. Implemented in
    full and measured anyway, because rule R-5 requires the paragraph and rule
    R-6 requires the values to come from the oracle.

    Args:
        sales: ``WS-Sales-Record``, mutated in place. Only the thirty-seven
            dictionary-mapped fields are written; the three ``FILLER`` items also
            receive spaces in the frozen program, which is what they already
            hold, so nothing distinguishes them here.
    """
    for column, value in SPACE_FILLED_RECORD.items():
        _assign_record_value(sales, column, value)
    _LOG.warning(
        "aa050-Process-Read-Indexed moved SPACES over WS-Sales-Record: the "
        "twenty-three numeric fields now hold space BYTES read as data "
        "(anomaly N-spacesrecord) [common/acas012.cbl:L480]"
    )


def aa050_process_read_indexed(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas012.cbl:L465-L486].

    ::

         aa050-Process-Read-Indexed.
        *>
        *> copy the key to main file area
        *>
             move     204 to WS-No-Paragraph.
             perform  aa045-Eval-keys.
             move     zero to Cobol-File-Status.
             if       File-Key-No = 1
                      read     Sales-File key Sales-Key       invalid key
                               move 21 to we-error fs-reply
                      end-read
                      if       fs-Reply = zero
                               move     Sales-Record to WS-Sales-Record
                               move     Sales-Key to WS-File-Key
                      else
                               move     spaces     to WS-Sales-Record
                      end-if
                      go       to aa999-main-exit
             end-if.
             move     998 to WE-Error       *> file seeks key type out of range
             move     99 to fs-reply
             go       to aa999-main-exit.

    The ONLY paragraph that performs ``aa045-Eval-Keys`` [:L470], and it does so
    because that paragraph moves the key into the FD record's ``Sales-Key`` -
    the field this ``read`` searches on. The comment ``*> copy the key to main
    file area`` [:L467] says exactly that; the comment inside ``aa045`` calling
    it "just for logging" understates it.

    **``WE-Error 998`` HERE MEANS "SHOULD NEVER GET HERE".** The frozen comment
    is ``*> file seeks key type out of range but should never get here 998``
    [:L484], and it is unreachable through the facade, which always moves 1 into
    ``File-Key-No`` [copybooks/Proc-ACAS-FH-Calls.cob:L83] - and unreachable
    through ``aa010-main`` too, whose key guard already refused any other value
    with the same 998 [:L296-L302]. So this is the THIRD site at which 998
    appears in one program, and the second with this meaning; ``aa060`` gives it
    a third, "Invalid calling parameter settings" [:L500]. Anomaly N-998.

    **ANOMALY N-spacesrecord** on the failure branch - see
    :func:`_move_spaces_to_sales_record`.

    **``21`` GOES TO BOTH FIELDS HERE.** ``move 21 to we-error fs-reply``
    [:L474] writes the same value into both, so ``WE-Error`` carries 21 - a value
    the authoritative table does not define as a ``WE-Error`` at all. The bridge
    is different again: its read-indexed miss sets ``23`` and zeroes ``WE-Error``
    [common/salesMT.cbl:L681-L683] - anomaly N-readindexed-23.

    Args:
        file_access: ``File-Access``. ``File-Key-No`` selects the branch;
            ``Fs-Reply`` is the FILE STATUS field the ``read`` writes.
        sales: ``WS-Sales-Record`` - replaced from the FD area on success, or
            space-filled on failure.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``read ... key`` [:L473], after
            paragraph 204, the key move and the status clear have been applied.
    """
    storage = handler_storage()
    _set_paragraph(
        file_access, WS_NO_PARAGRAPH_HANDLER["aa050-Process-Read-Indexed"]
    )
    # `perform aa045-Eval-keys.` [:L470] - which positions the FD key.
    aa045_eval_keys(file_access, sales)
    # `move zero to Cobol-File-Status.` [:L471].
    storage.cobol_file_status = 0
    if int(file_access.logging_data.file_key_no) == ONLY_FILE_KEY_NO:
        # `read Sales-File key Sales-Key invalid key ... end-read` [:L473-L475].
        _isam_verb(
            "read Sales-File key Sales-Key",
            "aa050-Process-Read-Indexed",
            "[common/acas012.cbl:L473]",
        )
        # `invalid key  move 21 to we-error fs-reply` [:L474] - both fields.
        if int(file_access.fs_reply) == int(FsReply.SUCCESS):
            # `move Sales-Record to WS-Sales-Record` [:L477].
            _move_record(storage.fd_record, sales)
            # `move Sales-Key to WS-File-Key` [:L478] - the FD key again.
            file_access.logging_data.ws_file_key = _log_key(
                _record_value(storage.fd_record, PRIMARY_KEY_COLUMN)
            )
        else:
            # `move spaces to WS-Sales-Record` [:L480] - N-spacesrecord.
            _move_spaces_to_sales_record(sales)
        # `go to aa999-main-exit` [:L482] - Class 3.
        aa999_main_exit(file_access, dal_common)
        return
    # `move 998 to WE-Error / move 99 to fs-reply` [:L484-L485], the frozen
    # comment conceding `*> but should never get here`.
    file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
    file_access.fs_reply = int(FsReply.ERROR)
    _LOG.error(
        "aa050-Process-Read-Indexed reached its 'should never get here' branch "
        "with File-Key-No = %s; reporting (99, 998) "
        "[common/acas012.cbl:L484-L486]",
        file_access.logging_data.file_key_no,
    )
    # `go to aa999-main-exit.` [:L486] - Class 3.
    aa999_main_exit(file_access, dal_common)


def aa060_process_start(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa060-Process-Start.`` [common/acas012.cbl:L488-L534].

    ::

         aa060-Process-Start.
        *>
        *>  Check for Param error 1st on start   WARNING Not logging starts
        *>
             move     205 to WS-No-Paragraph.
             move     zeros to fs-reply
                               WE-Error.
             move     zero to Cobol-File-Status.
             move     WS-Sales-Key to WS-File-Key
                                      Sales-Key.
             if       access-type < 5 or > 8          *> NOT using 'not >'
                      move 998 to WE-Error   *> 998 Invalid calling parameter
                      go to aa999-main-exit
             end-if
             if       File-Key-No = 1
                and   fn-equal-to
                      start Sales-File key = Sales-Key invalid key
                            move 21 to Fs-Reply
                            go to aa999-main-exit
                      end-start
             end-if
             ... three more, for `<`, `>` and `not <` ...
             go       to aa999-main-exit.
         *>    go       to aa041-Reread.  *> if used then prev goto is perform

    **ANOMALY N-start998-noreply - REPRODUCED, NOT FIXED.** The parameter guard
    moves 998 into ``WE-Error`` and NOTHING into ``FS-Reply`` [:L499-L502], and
    ``FS-Reply`` was zeroed four lines earlier [:L493-L494]. So an invalid
    ``Access-Type`` is reported as ``(FS-Reply 0, WE-Error 998)`` - an error
    paired with success, which any caller testing only ``FS-Reply`` reads as a
    successful START. Every sibling refusal in this program sets both: the extend
    branch [:L387-L388], the key guard [:L297-L298], the read-indexed dead branch
    [:L484-L485]. This one does not.

    **THE SAME GUARD, TWO DIFFERENT CODES.** The bridge tests the identical
    condition, ``if access-type < 5 or > 8`` [common/salesMT.cbl:L765], and
    answers ``(99, 997)`` [common/salesMT.cbl:L766-L767]. The handler answers
    ``(0, 998)``. Neither is corrected toward the other;
    :func:`~acas_posting.dal.status.start_access_type_is_valid`
    supplies the shared predicate and each layer keeps its own answer.

    **ACCESS TYPE 9 IS REFUSED, THOUGH IT NAMES A RELATION.**
    ``88 fn-not-greater-than value 9`` [copybooks/wsfnctn.cob:L116] and
    :data:`~acas_posting.dal.cursor_state.ACCESS_TYPE_TO_RELATION` maps it to
    ``'<= '``, but both guards stop at 8 - the frozen comment
    ``*> NOT using 'not >'`` [:L499] confirms it is deliberate. So there is no
    ``fn-not-greater-than`` START block among the four, and there is no fifth
    ``if``. Pre-existing anomaly N5.

    **THE FOUR ``if`` BLOCKS ARE SEPARATE, NOT AN ``evaluate``** [:L506-L533].
    Each retests ``File-Key-No = 1``. Because exactly one relation condition can
    hold at a time and each block's ``invalid key`` path transfers out, the
    behaviour is a four-way selection - but the shape is preserved, because a
    caller with ``File-Key-No`` other than 1 would fall past all four and reach
    [:L534] having started nothing and reporting ``(0, 0)``: success for a START
    that did not happen. Recorded as anomaly N-start-nokey, and DOUBLY
    unreachable - the key guard in ``aa010-main`` already refuses ``fn-start``
    with any other key number [:L297-L302], and the facade never sets one
    [copybooks/Proc-ACAS-FH-Calls.cob:L83]. Confirmed by execution: a START with
    ``File-Key-No`` 2 returns ``(99, 998)`` from the guard and never enters this
    paragraph. It is reproduced for the same reason ``aa050``'s own "should never
    get here" branch is [:L484] - the frozen program has it, and both would come
    alive the moment a caller bypassed the facade.

    **``*> WARNING Not logging starts``** [:L490] is the maintainer's own note,
    and it is wrong: the paragraph reaches ``aa999-main-exit`` on every path and
    that paragraph logs whenever ``Testing-1``. What he means is that no START is
    given its own tag, so the log record carries the key and nothing else.

    Args:
        file_access: ``File-Access``. ``Access-Type`` chooses the relation;
            ``Fs-Reply`` is the FILE STATUS field.
        sales: ``WS-Sales-Record`` - ``WS-Sales-Key`` is copied to both
            ``WS-File-Key`` and the FD record's key.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At whichever of the four ``start`` verbs the
            relation selects [:L508, :L515, :L522, :L529].
    """
    storage = handler_storage()
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa060-Process-Start"])
    # `move zeros to fs-reply WE-Error.` [:L493-L494].
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `move zero to Cobol-File-Status.` [:L495].
    storage.cobol_file_status = 0
    # `move WS-Sales-Key to WS-File-Key, Sales-Key.` [:L496-L497] - two
    # destinations, the second being the FD record's key.
    key_text = str(_record_value(sales, PRIMARY_KEY_COLUMN))
    file_access.logging_data.ws_file_key = _log_key(key_text)
    _assign_record_value(
        storage.fd_record,
        PRIMARY_KEY_COLUMN,
        _store_into_character_host_variable(key_text, column=PRIMARY_KEY_COLUMN),
    )
    access_type = int(file_access.access_type)
    # `if access-type < 5 or > 8` [:L499] - the shared predicate, the handler's
    # own answer.
    if not start_access_type_is_valid(access_type):
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        _LOG.error(
            "aa060-Process-Start refused Access-Type %d with WE-Error 998 and "
            "FS-Reply left at zero (anomaly N-start998-noreply) "
            "[common/acas012.cbl:L499-L502]",
            access_type,
        )
        # `go to aa999-main-exit` [:L501] - Class 3.
        aa999_main_exit(file_access, dal_common)
        return

    keyed = int(file_access.logging_data.file_key_no) == ONLY_FILE_KEY_NO
    # The four `if` blocks [:L506-L533], in the frozen order: =, <, >, not <.
    for expected, relation, locator in _AA060_START_BLOCKS:
        if keyed and access_type == expected:
            _isam_verb(
                f"start Sales-File key {relation} Sales-Key",
                "aa060-Process-Start",
                locator,
            )
            # `invalid key  move 21 to Fs-Reply / go to aa999-main-exit`
            # [:L509-L510] - note FS-Reply only; WE-Error keeps the zero from
            # [:L494], the mirror image of the guard's asymmetry above.
            if int(file_access.fs_reply) != int(FsReply.SUCCESS):
                file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
                aa999_main_exit(file_access, dal_common)
                return
    if not keyed:
        _LOG.error(
            "aa060-Process-Start fell past all four start blocks with "
            "File-Key-No = %s: nothing was started and the paragraph reports "
            "(0, 0) (anomaly N-start-nokey) [common/acas012.cbl:L506-L534]",
            file_access.logging_data.file_key_no,
        )
    # `go to aa999-main-exit.` [:L534] - Class 3. The commented-out
    # `go to aa041-Reread.  *> if used then prev goto is perform` [:L535] shows
    # the maintainer considered chaining the first read onto the START and did
    # not; a START therefore positions only, and the caller must read next.
    aa999_main_exit(file_access, dal_common)


#: The four ``start`` blocks of ``aa060-Process-Start``, in the frozen source
#: order [common/acas012.cbl:L506-L533]: ``fn-equal-to``, ``fn-less-than``,
#: ``fn-greater-than``, ``fn-not-less-than``. There is deliberately no
#: ``fn-not-greater-than`` block - see the paragraph's docstring.
_AA060_START_BLOCKS: Final[tuple[tuple[int, str, str], ...]] = (
    (int(AccessType.EQUAL_TO), "=", "[common/acas012.cbl:L508]"),
    (int(AccessType.LESS_THAN), "<", "[common/acas012.cbl:L515]"),
    (int(AccessType.GREATER_THAN), ">", "[common/acas012.cbl:L522]"),
    (int(AccessType.NOT_LESS_THAN), "not <", "[common/acas012.cbl:L529]"),
)


def aa070_process_write(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa070-Process-Write.`` [common/acas012.cbl:L537-L546].

    ::

         aa070-Process-Write.
             move     206 to WS-No-Paragraph.
             move     WS-Sales-Record to Sales-Record.
             move     zeros to FS-Reply  WE-Error.
             move     zero to Cobol-File-Status.
             move     Sales-Key to WS-File-Key.
             write    Sales-Record invalid key
                      move 22 to FS-Reply
             end-write.
             go       to aa999-main-exit.

    The log tag is taken from ``Sales-Key`` [:L542] - the FD record's key, which
    the whole-record move on the line above has just filled from
    ``WS-Sales-Key``. So the tag is the key being written, arrived at
    indirectly. Contrast ``aa080``, which moves ``WS-Sales-Key`` into
    ``WS-File-Key`` directly [:L550-L551].

    **``WE-Error`` IS NEVER SET ON FAILURE.** The duplicate-key path writes 22
    into ``FS-Reply`` alone [:L544], leaving the zero from [:L540]. The bridge
    has the same asymmetry on its own write - anomaly N-write-noweerror - so a
    duplicate reports ``(22, 0)`` at both layers, consistently, and neither is
    corrected.

    Args:
        file_access: ``File-Access``. ``Fs-Reply`` is the FILE STATUS field.
        sales: ``WS-Sales-Record`` - copied wholesale into the FD area.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``write`` [:L543]. The record move, the
            status clear and the log tag have all been applied first.
    """
    storage = handler_storage()
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa070-Process-Write"])
    # `move WS-Sales-Record to Sales-Record.` [:L539].
    _move_record(sales, storage.fd_record)
    # `move zeros to FS-Reply WE-Error.` [:L540].
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `move zero to Cobol-File-Status.` [:L541].
    storage.cobol_file_status = 0
    # `move Sales-Key to WS-File-Key.` [:L542] - the FD key, just filled.
    file_access.logging_data.ws_file_key = _log_key(
        _record_value(storage.fd_record, PRIMARY_KEY_COLUMN)
    )
    # `write Sales-Record invalid key  move 22 to FS-Reply  end-write.`
    # [:L543-L545].
    _isam_verb(
        "write Sales-Record",
        "aa070-Process-Write",
        "[common/acas012.cbl:L543]",
    )
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        # FS-Reply only; WE-Error keeps its zero - anomaly N-write-noweerror.
        file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
    # `go to aa999-main-exit.` [:L546] - Class 3.
    aa999_main_exit(file_access, dal_common)


def aa080_process_delete(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa080-Process-Delete.`` [common/acas012.cbl:L548-L557].

    ::

         aa080-Process-Delete.
             move     207 to WS-No-Paragraph.
             move     WS-Sales-Key to Sales-Key
                                      WS-File-Key.
             move     zeros to FS-Reply  WE-Error.
             move     zero to Cobol-File-Status.
             delete   Sales-File record invalid key
                      move 21 to FS-Reply
             end-delete.
             go       to aa999-main-exit.

    The only verb that does NOT move the whole record - a delete needs the key
    alone [:L550-L551], and the one ``MOVE`` fills both the FD key and the log
    tag. The frozen comment inside ``aa045`` says the same thing from the other
    side: ``*> fn-delete  For delete can ignore Desc key`` [:L452].

    ``21`` goes into ``FS-Reply`` only [:L555], leaving ``WE-Error`` at the zero
    from [:L552] - the same asymmetry as ``aa070``. The bridge's own delete is
    worse: on a row that was not there it writes NEITHER field, so the caller
    sees a stale status and a delete of nothing reports whatever came before -
    anomaly N-delete-stale.

    Args:
        file_access: ``File-Access``. ``Fs-Reply`` is the FILE STATUS field.
        sales: ``WS-Sales-Record`` - only ``WS-Sales-Key`` is read.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``delete`` [:L554].
    """
    storage = handler_storage()
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa080-Process-Delete"])
    # `move WS-Sales-Key to Sales-Key, WS-File-Key.` [:L550-L551].
    key_text = str(_record_value(sales, PRIMARY_KEY_COLUMN))
    _assign_record_value(
        storage.fd_record,
        PRIMARY_KEY_COLUMN,
        _store_into_character_host_variable(key_text, column=PRIMARY_KEY_COLUMN),
    )
    file_access.logging_data.ws_file_key = _log_key(key_text)
    # `move zeros to FS-Reply WE-Error.` [:L552].
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `move zero to Cobol-File-Status.` [:L553].
    storage.cobol_file_status = 0
    # `delete Sales-File record invalid key  move 21 to FS-Reply` [:L554-L556].
    _isam_verb(
        "delete Sales-File record",
        "aa080-Process-Delete",
        "[common/acas012.cbl:L554]",
    )
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    # `go to aa999-main-exit.` [:L557] - Class 3.
    aa999_main_exit(file_access, dal_common)


def aa090_process_rewrite(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa090-Process-Rewrite.`` [common/acas012.cbl:L559-L569].

    ::

         aa090-Process-Rewrite.
        *>
             move     208 to WS-No-Paragraph.
             move     WS-Sales-Record to Sales-Record.
             move     Sales-Key to WS-File-Key.
             move     zeros to FS-Reply  WE-Error.
             move     zero to Cobol-File-Status.
             rewrite  Sales-Record invalid key
                      move 21 to FS-Reply
             end-rewrite
             go       to aa999-main-exit.

    **THE STATEMENT ORDER DIFFERS FROM ``aa070``, AND IT IS PRESERVED.** Write
    clears the status pair BEFORE taking the log tag [:L540-L542]; rewrite takes
    the tag FIRST and clears afterwards [:L563-L564]. Nothing observable turns on
    it here - the tag does not read the status - but rule R-6 makes statement
    order part of the specification, and a reader diffing the two paragraphs
    should find the difference where the frozen program has it.

    ``end-rewrite`` carries no terminating period [:L568], so the
    ``go to aa999-main-exit`` on the next line is part of the same sentence
    rather than a new one. Same effect, and worth noting because the sibling
    ``end-write`` [:L545] and ``end-delete`` [:L556] both do have their period -
    a third small inconsistency across three adjacent paragraphs.

    ``21`` reaches ``FS-Reply`` only [:L567]. The bridge's rewrite is the one
    that also has an SQLSTATE path, ``WE-Error 994``
    [common/salesMT.cbl:L986], which has no counterpart here at all.

    Args:
        file_access: ``File-Access``. ``Fs-Reply`` is the FILE STATUS field.
        sales: ``WS-Sales-Record`` - copied wholesale into the FD area.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``rewrite`` [:L566].
    """
    storage = handler_storage()
    _set_paragraph(
        file_access, WS_NO_PARAGRAPH_HANDLER["aa090-Process-Rewrite"]
    )
    # `move WS-Sales-Record to Sales-Record.` [:L562].
    _move_record(sales, storage.fd_record)
    # `move Sales-Key to WS-File-Key.` [:L563] - BEFORE the status clear, unlike
    # `aa070`.
    file_access.logging_data.ws_file_key = _log_key(
        _record_value(storage.fd_record, PRIMARY_KEY_COLUMN)
    )
    # `move zeros to FS-Reply WE-Error.` [:L564].
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # `move zero to Cobol-File-Status.` [:L565].
    storage.cobol_file_status = 0
    # `rewrite Sales-Record invalid key  move 21 to FS-Reply` [:L566-L568].
    _isam_verb(
        "rewrite Sales-Record",
        "aa090-Process-Rewrite",
        "[common/acas012.cbl:L566]",
    )
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    # `go to aa999-main-exit.` [:L569] - Class 3.
    aa999_main_exit(file_access, dal_common)


def aa100_bad_function(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa100-Bad-Function.`` [common/acas012.cbl:L571-L576].

    ::

         aa100-Bad-Function.
        *>
        *> Houston; We have a problem
        *>
             move     999 to WE-Error.                         *> 999
             move     99  to fs-reply.

    Reached from TWO places in ``aa010-main``: the ``when other`` of the function
    ``evaluate`` [:L354-L355], and the unconditional
    ``go to aa100-Bad-Function.`` immediately after ``end-evaluate`` [:L359],
    which the frozen comment introduces as ``*> Should never get here but in
    case :(`` [:L358]. Both are reproduced - the second is what catches a
    function that matched a ``when`` whose branch somehow returned.

    **``999`` HERE, ``990`` IN THE BRIDGE.** The bridge's own bad-function
    paragraph moves 990 [common/salesMT.cbl:L1166] under the same "Houston"
    comment. Two layers, one condition, two codes - anomaly
    N-badfn-divergence. The authoritative table calls 999 "undefined"
    [common/glpostingMT.cbl:L141], which is what makes it the odd choice of the
    two, and it is kept.

    There is no ``go to`` at the end: the paragraph FALLS THROUGH to
    ``aa999-main-exit`` [:L578], so a bad function is logged like any other
    outcome. Reproduced by calling :func:`aa999_main_exit` at the end.

    Args:
        file_access: ``File-Access``, receiving ``(99, 999)``.
        dal_common: ``ACAS-DAL-Common-data`` - the fall-through logs through it.
    """
    _LOG.error(
        "aa100-Bad-Function: File-Function %s is not one of the nine acas012 "
        "supports; reporting (99, 999) [common/acas012.cbl:L571-L576]",
        file_access.file_function,
    )
    # `move 999 to WE-Error.` [:L575] / `move 99 to fs-reply.` [:L576].
    file_access.we_error = int(WeError.NOT_USED)
    file_access.fs_reply = int(FsReply.ERROR)
    # Fall through to `aa999-main-exit` [:L578].
    aa999_main_exit(file_access, dal_common)


def aa999_main_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa999-main-exit.`` [common/acas012.cbl:L578-L581].

    ::

         aa999-main-exit.
             if       Testing-1
                      perform Ca-Process-Logs
             end-if.

    The destination of every ``go to`` in the flat-file half, and the ONE place
    that half writes a log record. ``Testing-1`` is
    ``88 Testing-1 value 1`` over ``77 SW-Testing pic 9 value 1``
    [copybooks/Test-Data-Flags.cob], so logging is ON by default and the
    maintainer's own comment on the ``copy`` says how to stop it:
    ``*> set sw-testing to zero to stop logging`` [:L274].

    **THE RDB PATH NEVER REACHES HERE.** ``aa010-main``'s RDB branch transfers to
    ``AA-Main-Exit`` [:L318], not to this paragraph, so the handler writes no log
    record of its own when the bridge did the work - which is exactly what the
    frozen comment on ``Ca-Process-Logs`` claims: ``*> Not called on DAL access
    as it does it already`` [:L670].

    Falls through to ``aa-main-exit`` [:L583], which is empty and itself falls
    through to ``aa-Exit`` [:L587]. Reproduced by returning: the caller chain
    ends at :func:`dispatch`.

    Args:
        file_access: ``File-Access`` - the log record's whole content.
        dal_common: ``ACAS-DAL-Common-data`` - carries ``SW-Testing`` and the
            record counter.
    """
    # `if Testing-1  perform Ca-Process-Logs  end-if.` [:L579-L581].
    if int(dal_common.sw_testing) == TESTING_1_VALUE:
        ca_process_logs_acas012(file_access, dal_common)


def aa_main_exit() -> None:
    """``aa-main-exit.`` [common/acas012.cbl:L583].

    ::

         aa-main-exit.
        *>
        *> Now have processed cobol flat file,  so ..
        *>

    **ANOMALY N-emptypara - REPRODUCED, NOT REMOVED.** The paragraph has NO
    statements at all: the three lines under its label are comments, and the next
    label is ``aa-Exit`` [:L587]. It exists purely as a ``GO TO`` target, and it
    is a meaningful one - two transfers aim here specifically to SKIP
    ``aa999-main-exit`` and its log record: the RDB branch [:L318], because the
    bridge has already logged, and the close paragraph [:L411], because it has
    already logged twice.

    Kept as a real function rather than elided, because rule R-5 requires one
    function per paragraph and because a reader following either of those two
    transfers must land somewhere named. It has no body for the same reason the
    frozen paragraph has none.
    """
    # No statements. The comment `*> Now have processed cobol flat file, so ..`
    # [:L585] is the whole of the paragraph's content, and falls through to
    # `aa-Exit` [:L587].
    return


def aa_exit() -> None:
    """``aa-Exit.`` [common/acas012.cbl:L587-L588].

    ::

         aa-Exit.
             exit program.

    The single return point of the program. Both halves reach it: the flat-file
    half by falling through ``aa999-main-exit`` and ``aa-main-exit``, and the RDB
    half by transferring to ``aa-main-exit`` and falling through.

    ``exit program`` returns to the caller with the linkage records as they
    stand - which is the whole output protocol of this handler, since every
    status, every log field and the record itself live in the caller's storage.
    Reproduced by returning from :func:`dispatch`; there is nothing to do here
    but mark the point.
    """
    return



# ---------------------------------------------------------------------------
# 9.2 `ba-Process-RDBMS section.` [common/acas012.cbl:L590] - the live half
#
#   *>  Here we call the relevent RDBMS module for this table            *
#   *>   which will include processing any other joined tables as needed *
#
# Four paragraphs, and control simply falls through them:
#     ba010-Test-WS-Rec-Size  [:L598]  -> ba012-Test-WS-Rec-Size-2 [:L606]
#                                      -> ba015-Test-Ends          [:L648]
#                                      -> ba-rdbms-exit            [:L666]
# The only escape is `go to ba-rdbms-exit` on the 901 branch [:L633].
#
# `Ca-Process-Logs.` [:L670] and `ca-Exit. exit.` [:L676] are ALSO paragraphs of
# this section - there is no section header between [:L666] and [:L670] - so
# they are reachable only by PERFORM, and `ba-rdbms-exit`'s `exit section`
# [:L667] stops control falling into them. Worth noting because it means the log
# paragraph belongs, structurally, to the RDB section even though the flat-file
# half is its only caller.
# ---------------------------------------------------------------------------


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas012.cbl:L598-L604].

    ::

         ba010-Test-WS-Rec-Size.
        *>
        *>     Test on very first call only  (So do NOT use var A & B again)
        *>       Lets test that Data-record size is = or > than declared Rec in
        *>          DAL as we cant adjust at compile/run time due to ALL Cobol
        *>          compilers ?
        *>
             move     21 to WS-Log-File-no.        *> for FHlogger

    **ONE STATEMENT, AND IT OVERWRITES THE HANDLER'S OWN LOG FILE NUMBER.**
    ``aa010-main`` moved 11 in [:L292]; this moves 21 [:L604]. So a log record
    written on the RDB path carries 21 and one written on the flat-file path
    carries 11 - anomaly N-log. The pair is the same 11 -> 21 that ``acas005``
    uses, because the number is scoped WITHIN the subsystem
    (``WS-Log-System`` = 3 for Sales) rather than being global.

    **THE PARAGRAPH'S NAME DESCRIBES ITS NEIGHBOUR, NOT ITSELF.** Every comment
    under the label is about the record-size test, and the record-size test is in
    the NEXT paragraph [:L606]. This one only sets the log number. The naming is
    left as found.

    Falls through to ``ba012-Test-WS-Rec-Size-2``; there is no ``go to``.

    Args:
        file_access: ``File-Access`` - ``WS-Log-File-No`` is in its
            ``Logging-Data``, so this writes the caller's block.
    """
    # `move 21 to WS-Log-File-no.  *> for FHlogger` [:L604].
    file_access.logging_data.ws_log_file_no = LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2(
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas012.cbl:L606-L646].

    ::

         ba012-Test-WS-Rec-Size-2.
             if       A = zero              *> so it is being called first time
                      move function Length (WS-Sales-Record) to A
                      move function length (Sales-Record)    to B
                      if   A < B            *> COULD LET caller module deal ...
                           move 901 to WE-Error   *> 901 Programming error; temp
                           move 99 to fs-reply    *> allow for last field ...
                      end-if
                      if       WE-Error = 901
                               move spaces to Display-Blk
                               string SL905          delimited by size
                                      A              delimited by size
                                      " < "          delimited by size
                                      "Sales-Rec = " delimited by size
                                      B              delimited by size
                                                              into Display-Blk
                               end-string
                               display Display-Blk at 2301 with erase eol
                               display SL901 at 2401 with erase eol
                               if  Testing-1
                                   perform Ca-Process-Logs
                               end-if
                               accept Accept-Reply at 2433
                               go to ba-rdbms-exit
                      end-if
        *>  Load up the DB settings from the system record as its not passed on
        *>           hopefully once is enough  :)
                      move     RDBMS-DB-Name to DB-Schema
                      move     RDBMS-User    to DB-UName
                      move     RDBMS-Passwd  to DB-UPass
                      move     RDBMS-Port    to DB-Port
                      move     RDBMS-Host    to DB-Host
                      move     RDBMS-Socket  to DB-Socket
             end-if.

    **ANOMALY N-recsize-unreachable - REPRODUCED, NOT FIXED.**
    ``function Length`` of a group returns its size in bytes, and
    ``WS-Sales-Record`` [copybooks/wssl.cob] and ``Sales-Record``
    [copybooks/fdsl.cob] are field-for-field identical - both copybook headers
    state "rec size 300 bytes" and both carry the same three ``FILLER`` items,
    the same ``REDEFINES`` and the same ``USAGE`` on every field. So ``A``
    always equals ``B``, ``A < B`` can never hold, and ``WE-Error 901`` is
    DEAD CODE together with its display, its log record and its keystroke wait.
    Reproduced in full rather than pruned: the maintainer's own comment
    ``*> COULD LET caller module deal with these errors !!!!!!!`` [:L615] shows
    he meant it to fire, and the branch is the only place 901 appears in the
    program.

    **ANOMALY A-1 - THE FIRST-CALL-ONLY GUARD SWALLOWS THE CREDENTIAL LOAD.**
    The ``end-if`` at [:L646] closes AFTER the six credential moves, so from the
    second call onward the whole block is skipped - the record-size test and the
    credentials together. A change to the ``SYSTEM-REC`` row part-way through a
    run therefore cannot affect that run. Reproduced twice over: by this
    paragraph's own ``A = zero`` test against
    :attr:`HandlerWorkingStorage.a`, and inside
    :func:`~acas_posting.dal.connection.load_rdb_data_once`, which reproduces the
    identical guard from ``acas008`` [common/acas008.cbl:L526]. The two agree,
    because in the frozen system ``RDB-Data`` lives in the CALLER's block: every
    handler writes the same destination from the same source, so one load per run
    and one load per handler are indistinguishable.

    **THE SIX MOVES ARE IN THE FROZEN ORDER, AND IT IS NOT THE OBVIOUS ONE:**
    schema, user, password, **port**, host, socket [:L640-L645]. Port before
    host. Preserved per rule R-6.

    **ONE ADDITION, DECLARED AS SUCH.** The bridge is called with three
    parameters and receives neither the system record nor the file definitions
    [common/acas012.cbl:L658-L661], yet
    :func:`~acas_posting.dal.connection.mysql_1000_open` needs the system record
    to open a connection. This paragraph is where the frozen program transfers
    everything the bridge will need about the database out of the system record -
    its comment says exactly that: ``*> Load up the DB settings from the system
    record as its not passed on`` [:L637] - so it is also where the system record
    is handed to :class:`BridgeSession`. Nothing about the frozen program's
    behaviour changes; the same information crosses the same boundary at the same
    point.

    **THE DISPLAYS AND THE ACCEPT ARE OMISSIONS.** ``display Display-Blk at
    2301`` and ``display SL901 at 2401`` [:L627-L628] are screen output with no
    database effect, and ``accept Accept-Reply at 2433`` [:L632] is a pause whose
    only effect is to block a terminal. Agent Action Plan section 0.3.4 drops all
    three while preserving the ``go to ba-rdbms-exit`` [:L633] that follows -
    which IS behaviour, since it abandons the request. ``Display-Blk`` is still
    built, so the diagnostic reaches a log record.

    Args:
        system: ``System-Record``, the first linkage parameter. Read only inside
            the first-call block, exactly as the frozen program reads it.
        file_access: ``File-Access``. ``RDB-Data`` receives the credentials and
            the status pair receives 901/99 on the dead branch.
        dal_common: ``ACAS-DAL-Common-data`` - the 901 branch logs through it.

    Returns:
        ``True`` when the frozen program would ``go to ba-rdbms-exit`` [:L633],
        abandoning the request; ``False`` when it falls through to
        ``ba015-Test-Ends``.
    """
    storage = handler_storage()
    # `if A = zero  *> so it is being called first time` [:L608].
    if storage.a != 0:
        return False

    # `move function Length (WS-Sales-Record) to A` [:L609-L611] and
    # `move function length (Sales-Record) to B` [:L612-L614]. `function Length`
    # of a group is its byte size; both records are 300 bytes.
    storage.a = WS_SALES_RECORD_BYTES % (10**LENGTH_VARIABLE_DIGITS)
    storage.b = SALES_RECORD_BYTES % (10**LENGTH_VARIABLE_DIGITS)
    # `if A < B  move 901 to WE-Error / move 99 to fs-reply  end-if` [:L615-L618].
    if storage.a < storage.b:  # pragma: no cover - N-recsize-unreachable
        file_access.we_error = int(WeError.RECORD_SIZE_MISMATCH)
        file_access.fs_reply = int(FsReply.ERROR)
    # `if WE-Error = 901` [:L619].
    if int(file_access.we_error) == int(
        WeError.RECORD_SIZE_MISMATCH
    ):  # pragma: no cover - N-recsize-unreachable
        # `move spaces to Display-Blk` then the five-part `string ... into
        # Display-Blk` [:L620-L626]. `A` and `B` are `pic 9(4)`, so each
        # contributes exactly four digits `delimited by size`.
        storage.display_blk = (
            f"{SL905}"
            f"{storage.a:0{LENGTH_VARIABLE_DIGITS}d}"
            " < "
            "Sales-Rec = "
            f"{storage.b:0{LENGTH_VARIABLE_DIGITS}d}"
        )[:DISPLAY_BLK_WIDTH].ljust(DISPLAY_BLK_WIDTH)
        # The two `display ... with erase eol` [:L627-L628] become one record.
        _LOG.error(
            "ba012-Test-WS-Rec-Size-2 record length mismatch: %s | %s "
            "[common/acas012.cbl:L615-L628]",
            storage.display_blk.rstrip(),
            SL901,
        )
        # `if Testing-1  perform Ca-Process-Logs  end-if` [:L629-L631].
        if int(dal_common.sw_testing) == TESTING_1_VALUE:
            ca_process_logs_acas012(file_access, dal_common)
        # `accept Accept-Reply at 2433` [:L632] is dropped per 0.3.4; the
        # `go to ba-rdbms-exit` [:L633] that follows it is NOT - Class 3.
        return True

    # The six credential moves [:L640-L645], in the frozen order: schema, user,
    # password, PORT, host, socket. Sourced through `load_rdb_data_once`, which
    # reproduces the same first-call-only guard and returns one `RdbData` per
    # run - see the docstring on anomaly A-1 above.
    loaded = load_rdb_data_once(system)
    rdb_data = file_access.rdb_data
    rdb_data.db_schema = loaded.db_schema
    rdb_data.db_uname = loaded.db_uname
    rdb_data.db_upass = loaded.db_upass
    rdb_data.db_port = loaded.db_port
    rdb_data.db_host = loaded.db_host
    rdb_data.db_socket = loaded.db_socket
    # The declared addition: the bridge is not given the system record
    # [:L658-L661], so it is handed over here, where the frozen program already
    # transfers everything about the database out of it.
    session().system_record = system
    return False


def ba015_test_ends(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    sales: WsSalesRecord,
) -> CursorOutcome:
    """``ba015-Test-Ends.`` [common/acas012.cbl:L648-L662].

    ::

         ba015-Test-Ends.
        *>   HERE we need a CDF [Compiler Directive] to select the correct DAL
        *>     based on the pre SQL compiler e.g., JCs or dbpre or Prima ... ?
        *>        Do this after system testing and pre code release.
        *>  NOW SET UP FOR JC pre-sql compiler system.
        *>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql
             call     "salesMT" using File-Access
                                     ACAS-DAL-Common-data

                                     WS-Sales-Record
             end-call.
        *>   Any errors leave it to caller to recover from

    The whole of the RDB half's work, in one ``CALL``. Three parameters, in this
    order - the bridge gets neither ``System-Record`` nor ``File-Defs``, which is
    why :func:`ba012_test_ws_rec_size_2` has to hand the system record over
    separately.

    Note the blank line inside the ``using`` list [:L660], between the second and
    third parameters. Harmless, and mentioned because a reader comparing the two
    argument lists will see it.

    ``*> Any errors leave it to caller to recover from`` [:L664] is the
    General/Sales/Purchase error convention stated outright: no per-handler check
    paragraph, no transfer out, the reply left in the caller's block for the
    caller to test. Agent Action Plan section 0.6.5 contrasts this with the IRS
    convention, which does ``goback`` on an unrecoverable open. It is why this
    module raises no status exception - see :class:`FlatFileStoreNotMigrated`.

    The paragraph name promises a test and the body has none; the comment block
    explains why - the intended compiler-directive selection between rival
    pre-SQL translators was deferred, and only the JC path was ever wired up.
    Left as found.

    Falls through to ``ba-rdbms-exit``; there is no ``go to``.

    Args:
        file_access: ``File-Access`` - first parameter of the ``CALL``.
        dal_common: ``ACAS-DAL-Common-data`` - second parameter.
        sales: ``WS-Sales-Record`` - third parameter.

    Returns:
        The bridge's outcome, already applied to ``file_access``.
    """
    # `call "salesMT" using File-Access ACAS-DAL-Common-data WS-Sales-Record`
    # [:L658-L662].
    return sales_mt(file_access, dal_common, sales)


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit.`` [common/acas012.cbl:L666-L667].

    ::

         ba-rdbms-exit.
             exit     section.

    The section's single exit, and the target of the 901 branch's
    ``go to`` [:L633]. ``exit section`` returns to whatever ``perform``\\ ed the
    section - ``aa010-main`` [:L317] - and, importantly, stops control falling
    into ``Ca-Process-Logs`` [:L670], which is declared inside this same section.
    Reproduced by returning from :func:`ba_process_rdbms`.
    """
    return


def ca_process_logs_acas012(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``Ca-Process-Logs.`` [common/acas012.cbl:L670-L676].

    ::

         Ca-Process-Logs. *> Not called on DAL access as it does it already
        *>**************
        *>
             call     "fhlogger" using File-Access
                                       ACAS-DAL-Common-data.
        *>
         ca-Exit.     exit.

    **NAMED ``ca_process_logs_acas012`` FOR ONE REASON: THE BRIDGE HAS A
    PARAGRAPH OF THE SAME NAME.** ``Ca-Process-Logs`` exists in both
    ``common/acas012.cbl`` [common/acas012.cbl:L670] and ``common/salesMT.cbl``
    [common/salesMT.cbl:L2261], which is legal because they are separate
    programs. In one Python module the two need
    distinct names, so the bridge's keeps the plain
    :func:`ca_process_logs` and the handler's carries the program suffix. This is
    the ONLY name collision between the two programs - every other paragraph name
    is distinct - and it is a representational choice, not a behavioural one.

    **THE FROZEN COMMENT IS TRUE, AND IT IS ENFORCED BY CONTROL FLOW.**
    ``*> Not called on DAL access as it does it already`` [:L670]. The RDB branch
    of ``aa010-main`` transfers to ``AA-Main-Exit`` [:L318], jumping over
    ``aa999-main-exit`` and therefore over the only unconditional caller of this
    paragraph. The bridge logs instead, through its own ``ba999-end``, whose
    ``if Testing-1 / perform Ca-Process-Logs`` [common/salesMT.cbl:L1189-L1191]
    is the bridge-side equivalent. The one exception is the 901 branch of
    ``ba012-Test-WS-Rec-Size-2`` [:L630], which is on the RDB path and does log
    here - and which is unreachable.

    Three callers in all: ``aa999-main-exit`` [:L580], the second close record
    [:L410], and that dead 901 branch [:L630].

    ``ca-Exit. exit.`` [:L676] uses the plain ``exit`` verb - a no-op
    continuation statement, not ``exit section`` or ``exit program``. It marks the
    end of the paragraph and nothing more, which is why this function simply
    returns.

    For what ``fhlogger`` does, what is reproduced of it and what is dropped, see
    :func:`ca_process_logs`; the two calls are identical in their arguments and
    their effect, so the behaviour is described once, there.

    Args:
        file_access: The block the log record is built from.
        dal_common: The block carrying ``SW-Testing`` and
            ``Log-File-Rec-Written``.
    """
    # `call "fhlogger" using File-Access ACAS-DAL-Common-data.` [:L673-L674].
    # Identical arguments to the bridge's call, so the same reproduction serves.
    ca_process_logs(file_access, dal_common)
    # `ca-Exit.  exit.` [:L676] - a no-op continuation.


def ba_process_rdbms(
    system: SystemRecord,
    sales: WsSalesRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> CursorOutcome:
    """``ba-Process-RDBMS section.`` [common/acas012.cbl:L590-L667].

    ::

         ba-Process-RDBMS section.
        *>********************************************************************
        *>  Here we call the relevent RDBMS module for this table            *
        *>   which will include processing any other joined tables as needed *
        *>********************************************************************

    ``perform``\\ ed from exactly one place, ``aa010-main`` [:L317], and its four
    paragraphs simply fall through one into the next:
    ``ba010-Test-WS-Rec-Size`` sets the log file number,
    ``ba012-Test-WS-Rec-Size-2`` runs the first-call block,
    ``ba015-Test-Ends`` calls the bridge, ``ba-rdbms-exit`` leaves. The single
    escape is the 901 branch's ``go to ba-rdbms-exit`` [:L633] - Agent Action
    Plan 0.4.2 Class 3 - which skips the bridge call entirely.

    The section header's promise about "processing any other joined tables as
    needed" is not kept for Sales: ``SALEDGER-REC`` is one table with one key, so
    there is nothing to join. ``acas016`` and ``acas026`` are the handlers where
    that comment earns its place, each owning a header table and a lines table.

    Args:
        system: ``System-Record`` - reaches ``ba012`` only.
        sales: ``WS-Sales-Record`` - reaches the bridge.
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.

    Returns:
        The bridge's outcome, or - on the unreachable 901 branch - a photograph
        of the block the 901 branch left behind, since no bridge call was made.
    """
    # `ba010-Test-WS-Rec-Size.` [:L598], falling through to `ba012`.
    ba010_test_ws_rec_size(file_access)
    # `ba012-Test-WS-Rec-Size-2.` [:L606].
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        # `go to ba-rdbms-exit` [:L633] - the bridge is never called.
        ba_rdbms_exit()
        return _outcome_from_file_access(file_access)
    # `ba015-Test-Ends.` [:L648].
    outcome = ba015_test_ends(file_access, dal_common, sales)
    # `ba-rdbms-exit. exit section.` [:L666-L667].
    ba_rdbms_exit()
    return outcome



# ---------------------------------------------------------------------------
# 9.3 `aa010-main.` [common/acas012.cbl:L287] and the PROCEDURE DIVISION
# ---------------------------------------------------------------------------


def aa010_main(
    system: SystemRecord,
    sales: WsSalesRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> CursorOutcome:
    """``aa010-main.`` [common/acas012.cbl:L287-L359] - the whole dispatcher.

    Seven steps, in the frozen order, every one of them reproduced:

    1. ``move 3 to WS-Log-System`` / ``move 11 to WS-Log-File-No``
       [:L291-L292] - the log identity.
    2. The key guard, ``evaluate File-Function`` over 4, 9 and 8
       [:L296-L308].
    3. ``if not FS-Cobol-Files-Used`` - the store test [:L316-L321].
    4. ``perform ba012-Test-WS-Rec-Size-2`` [:L330] - flat-file path only.
    5. ``move spaces to SQL-Err SQL-Msg SQL-State`` [:L342].
    6. ``evaluate File-Function`` over the nine supported codes [:L344-L356].
    7. ``go to aa100-Bad-Function`` unconditionally [:L359].

    **THE LOG IDENTITY - ANOMALY N-log.** ``WS-Log-System`` is 3, Sales, and the
    frozen comment enumerating the systems is missing its comma after
    ``5=Stock`` where the sibling handlers have one [:L291] - a copy-paste
    divergence, recorded, not corrected. ``WS-Log-File-No`` is set to 11 here and
    OVERWRITTEN with 21 by ``ba010-Test-WS-Rec-Size`` [:L604] on the RDB path,
    so the number a log record carries tells you which half handled the request.
    11 is ``file-11``, ``"stockctl"``, not the Sales Ledger, which is ``file-12``
    and is what this handler's own ``SELECT`` assigns [copybooks/selsl.cob] -
    inherited from ``acas011`` and left as found.

    **THE KEY GUARD IS DEAD CODE THROUGH THE FACADE, AND REPRODUCED ANYWAY.**
    Every one of the eleven published Sales verbs reaches this handler through a
    dispatch paragraph that does ``move 1 to File-Key-No`` first
    [copybooks/Proc-ACAS-FH-Calls.cob:L83], so ``File-Key-No not = 1`` can never
    hold for a facade caller. The guard covers 4 (read-indexed) and 9 (start)
    with ``WE-Error 998`` and 8 (delete) with ``996`` [:L296-L308]. It does NOT
    cover 5 (write) or 7 (re-write), while ``acas000`` guards a different set
    entirely - 4, 5 and 7 - which is anomaly N-guard: the two must not be
    unified. The 996 arm's comment is a verbatim copy-paste of the 998 arm's,
    ``*> file seeks key type out of range``, which does not describe a delete -
    anomaly N-996-comment.

    **STEP 3 IS THE ONE TEST THAT DECIDES EVERYTHING.** ``FS-Cobol-Files-Used``
    is ``88 ... value 0`` over ``File-System-Used`` in the SYSTEM record's
    ``RDBMS-Flat-Statuses`` [copybooks/wssystem.cob:L111-L113] - note the name has no
    ``FA-`` prefix, so it is the system record's copy that is tested, not the
    ``File-Access`` copy. The handler then COPIES the group into
    ``FA-RDBMS-Flat-Statuses`` [:L317] for the bridge's benefit, with the
    frozen comment ``*> needed for DAL? not JC/dbpre versions``, and the second
    comment on the ``perform`` is ``*> Can't hurt`` [:L318]. The migrated system
    always has ``File-System-Used`` = 1, so this branch is always taken - see
    :data:`FLAT_FILE_STORE_MIGRATED`.

    **THE RDB BRANCH TRANSFERS TO ``AA-Main-Exit``, NOT TO ``aa999-main-exit``**
    [:L319]. That skips the handler's only log record, which is exactly what the
    comment on ``Ca-Process-Logs`` claims: ``*> Not called on DAL access as it
    does it already`` [:L670]. Reproduced, and it is why a Sales RDB request
    produces one log record - the bridge's - and not two.

    **STEP 4 RUNS ``ba012`` FROM THE OTHER HALF.** The flat-file path performs
    a paragraph that lives inside ``ba-Process-RDBMS section`` [:L330], which is
    how ``A`` comes to be set and the credentials loaded even on a run that never
    touches the database. Recorded as anomaly N-performrange: if that paragraph's
    dead 901 branch ever fired it would ``go to ba-rdbms-exit`` [:L633], a
    transfer out of a ``PERFORM`` range into another paragraph of the same
    section, whose effect COBOL leaves undefined and GnuCOBOL permits only
    because the build suppresses the warning with ``-Wno-goto-section``. Treated
    here as returning from the performed paragraph, and unreachable either way
    because ``A`` always equals ``B``.

    **STEP 5 CLEARS THE THREE SQL FIELDS BUT NOT THE STATUS PAIR.** The two
    ``move zero to WE-Error / FS-Reply`` statements above it are commented out and
    each prefixed with the maintainer's own question mark - ``*>  ?`` [:L332-L333]
    - so a stale status survives into the verb. That is what makes
    ``aa020-Process-Open``'s ``if fs-reply not = zero`` [:L396] able to promote a
    previous verb's failure to 999. Anomaly N-nostatusclear.

    **STEP 6 - ANOMALY N-when31.** ``when 3`` and ``when 31`` share a single
    branch [:L341-L343], added per the changelog entry ``15/01/17 vbc - .05
    Allow for fn-Read-By-Name used in SL165.`` [:L139]. So on the flat-file path
    a by-name read is a plain sequential read in KEY order. The BRIDGE gives 31
    its own paragraph [common/salesMT.cbl:L995-L1070] and does honour the
    ordering, via ``ORDER BY `SALES-NAME` ASC`` [common/salesMT.cbl:L1015-L1019].
    The ``when other`` comment ``*> 6 is spare / unused`` [:L354] records that
    ``fn-Delete-All`` is not supported here at all, unlike ``acas006`` and
    ``acas007``.

    **STEP 7 IS A SECOND, UNCONDITIONAL ROUTE TO BAD-FUNCTION.** ``*> Should
    never get here but in case :(`` [:L358] then ``go to aa100-Bad-Function.``
    [:L359]. In COBOL every ``when`` arm is a ``go to``, so control cannot reach
    it; in Python a branch that returns normally would, so the fall-through is
    reproduced explicitly and reached only if a verb function returns without
    having transferred - which is the condition the frozen line exists to catch.

    Args:
        system: ``System-Record`` - first linkage parameter [:L276].
        sales: ``WS-Sales-Record`` - second [:L277].
        file_access: ``File-Access`` - third [:L278].
        file_defs: ``File-Defs`` - fourth [:L279].
        dal_common: ``ACAS-DAL-Common-data`` - fifth [:L280].

    Returns:
        A :class:`~acas_posting.dal.cursor_state.CursorOutcome`. The
        AUTHORITATIVE channel is ``file_access``, which every paragraph has
        already written through the linkage exactly as the frozen program does;
        the return value is a convenience for a Python caller and carries the
        same values.

    Raises:
        FlatFileStoreNotMigrated: If the flat-file half is entered and reaches an
            ISAM verb - see :class:`FlatFileStoreNotMigrated`.
    """
    logging_data = file_access.logging_data
    # --- 1. `move 3 to WS-Log-System / move 11 to WS-Log-File-No` [:L291-L292].
    logging_data.ws_log_system = int(LOG_SYSTEM)
    logging_data.ws_log_file_no = LOG_FILE_NO_COBOL

    function = int(file_access.file_function)
    # --- 2. The key guard [:L296-L308]. Each of the three functions appears in
    # exactly one `when` arm, so the mapping is equivalent to the `evaluate`; the
    # frozen arm order is 4/9 then 8, which `GUARDED_KEY_FUNCTIONS` preserves.
    guarded = GUARDED_KEY_FUNCTIONS.get(cast(FileFunction, function))
    if guarded is not None and (
        int(logging_data.file_key_no) != ONLY_FILE_KEY_NO
    ):
        file_access.we_error = int(guarded)
        file_access.fs_reply = int(FsReply.ERROR)
        _LOG.error(
            "acas012 key guard refused File-Function %d with File-Key-No %s: "
            "(99, %d) [common/acas012.cbl:L296-L308]",
            function,
            logging_data.file_key_no,
            int(guarded),
        )
        # `go to aa999-main-exit` [:L299, :L306] - Class 3.
        aa999_main_exit(file_access, dal_common)
        aa_main_exit()
        return _outcome_from_file_access(file_access)

    # --- 3. `if not FS-Cobol-Files-Used` [:L316] - the SYSTEM record's copy.
    flat_statuses = system.system_data_block.rdbms_flat_statuses
    if int(flat_statuses.file_system_used) != FS_COBOL_FILES_USED:
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses` [:L317] - a group
        # MOVE of the two fields into the caller's File-Access copy, for the
        # bridge. `*> needed for DAL? not JC/dbpre versions`.
        fa_statuses = file_access.fa_rdbms_flat_statuses
        fa_statuses.fa_file_system_used = int(flat_statuses.file_system_used)
        fa_statuses.fa_file_duplicates_in_use = int(
            flat_statuses.file_duplicates_in_use
        )
        # `perform ba-Process-RDBMS  *> Can't hurt` [:L318].
        outcome = ba_process_rdbms(system, sales, file_access, dal_common)
        # `go to AA-Main-Exit` [:L319] - Class 3, and it SKIPS
        # `aa999-main-exit`, so the handler writes no log record of its own.
        aa_main_exit()
        return outcome

    # ===================== the flat-file half, from here ====================
    _LOG.warning(
        "acas012 entered its flat-file half: File-System-Used is %s "
        "(FS-Cobol-Files-Used) and this migration maps Sales onto %s "
        "[common/acas012.cbl:L316]",
        flat_statuses.file_system_used,
        TABLE_NAME,
    )
    # --- 4. `perform ba012-Test-WS-Rec-Size-2.` [:L330] - a paragraph of the
    # OTHER section; anomaly N-performrange.
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        ba_rdbms_exit()
        aa_main_exit()
        return _outcome_from_file_access(file_access)

    # --- 5. `move spaces to SQL-Err SQL-Msg SQL-State.` [:L342]. The status pair
    # is deliberately NOT cleared - anomaly N-nostatusclear [:L332-L333].
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH

    # --- 6. `evaluate File-Function` [:L344-L356], in the frozen `when` order.
    #
    # EVERY `when` arm is a `go to`, not a `perform`, so control NEVER returns to
    # this paragraph once a verb has been entered: each verb ends by falling
    # through `aa999-main-exit` [:L578] into `aa-main-exit` [:L583] into
    # `aa-Exit` [:L587] and out of the program. `transferred` records that,
    # because a Python call DOES return and the difference decides whether step 7
    # below overwrites the status the verb just set.
    transferred = True
    if function == FileFunction.OPEN:
        # `when 1  go to aa020-Process-Open` [:L337-L338] - Class 4.
        aa020_process_open(file_access, file_defs, dal_common)
    elif function == FileFunction.CLOSE:
        # `when 2  go to aa030-Process-Close` [:L339-L340] - Class 4.
        aa030_process_close(file_access, dal_common)
    elif function in _AA040_SHARED_FUNCTIONS:
        # `when 3 / when 31  go to aa040-Process-Read-Next` [:L341-L343] - one
        # branch for two codes, anomaly N-when31 - Class 4.
        if not aa040_process_read_next(file_access, sales, dal_common):
            # `aa040` fell off its end into `aa041-Reread` [:L429] - Class 2's
            # mirror image: no transfer, so the next paragraph simply runs.
            aa041_reread(file_access, sales, dal_common)
    elif function == FileFunction.READ_INDEXED:
        # `when 4  go to aa050-Process-Read-Indexed` [:L344-L345] - Class 4.
        aa050_process_read_indexed(file_access, sales, dal_common)
    elif function == FileFunction.WRITE:
        # `when 5  go to aa070-Process-Write` [:L346-L347] - Class 4.
        aa070_process_write(file_access, sales, dal_common)
    elif function == FileFunction.RE_WRITE:
        # `when 7  go to aa090-Process-Rewrite` [:L348-L349] - Class 4.
        aa090_process_rewrite(file_access, sales, dal_common)
    elif function == FileFunction.DELETE:
        # `when 8  go to aa080-Process-Delete` [:L350-L351] - Class 4.
        aa080_process_delete(file_access, sales, dal_common)
    elif function == FileFunction.START:
        # `when 9  go to aa060-Process-Start` [:L352-L353] - Class 4.
        aa060_process_start(file_access, sales, dal_common)
    elif function not in _SUPPORTED_FUNCTION_CODES:
        # `when other  *> 6 is spare / unused  go to aa100-Bad-Function`
        # [:L354-L355] - Class 4. Function 6, `fn-Delete-All`, arrives here, as
        # does any code outside the nine.
        aa100_bad_function(file_access, dal_common)
    else:  # pragma: no cover - guards the frozen `when` list against drift
        # A code that `SUPPORTED_FUNCTIONS` claims is handled but that no arm
        # above matched. Impossible while the two agree; if they ever diverge the
        # frozen program's own last line is what catches it, so fall to step 7
        # rather than inventing a status here.
        transferred = False

    # --- 7. `*> Should never get here but in case :(` /
    # `go to aa100-Bad-Function.` [:L358-L359] - Class 4, UNCONDITIONAL in the
    # frozen source and unreachable there for the reason above: every arm has
    # already left the program. Reproduced with the same reachability - the guard
    # is false for all nine supported codes and for `when other` alike - so the
    # line exists exactly where the frozen program puts it and can no more
    # overwrite a verb's status here than it can there.
    if not transferred:
        _LOG.error(
            "acas012 reached the unconditional go to aa100-Bad-Function after "
            "the evaluate for File-Function %d - 'Should never get here but in "
            "case :(' [common/acas012.cbl:L358-L359]",
            function,
        )
        aa100_bad_function(file_access, dal_common)

    # Fall through `aa-main-exit` [:L583] to `aa-Exit` [:L587].
    aa_main_exit()
    return _outcome_from_file_access(file_access)


#: ``88 FS-Cobol-Files-Used value 0`` over ``File-System-Used``
#: [copybooks/wssystem.cob:L111-L113] - the value ``aa010-main``'s store test compares
#: against [common/acas012.cbl:L316]. Note the tested condition name has NO
#: ``FA-`` prefix, so it belongs to the SYSTEM record's ``RDBMS-Flat-Statuses``,
#: not to the ``File-Access`` copy the handler then fills [:L317].
FS_COBOL_FILES_USED: Final[int] = 0

#: :data:`SUPPORTED_FUNCTIONS` as plain ``int``, for the step-7 guard in
#: :func:`aa010_main`. Derived from the tuple rather than restated, so the
#: ``evaluate``'s ``when`` list and this set cannot drift apart.
_SUPPORTED_FUNCTION_CODES: Final[frozenset[int]] = frozenset(
    int(code) for code in SUPPORTED_FUNCTIONS
)

#: The two ``File-Function`` codes that share ``aa040-Process-Read-Next``
#: [common/acas012.cbl:L341-L343] - anomaly N-when31. The bridge does NOT share
#: them: it gives 31 its own ``ba140-Process-Read-Next``
#: [common/salesMT.cbl:L1018], and the two layers are left disagreeing.
_AA040_SHARED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {int(FileFunction.READ_NEXT), int(FileFunction.READ_BY_NAME)}
)


def dispatch(
    system: SystemRecord,
    sales: WsSalesRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> CursorOutcome:
    """``Procedure Division Using ...`` [common/acas012.cbl:L276-L282].

    ::

         Procedure Division Using System-Record
                                  WS-Sales-Record
                                  File-Access
                                  File-Defs
                                  ACAS-DAL-Common-data.

    **FIVE parameters, in exactly that order.** This is the whole public entry
    point of handler ``acas012``, and it satisfies the Agent Action Plan section
    0.4.3 contract verbatim::

        FROM:  call "acas012" using System-Record WS-Sales-Record File-Access
                                   File-Defs ACAS-DAL-Common-data
        TO:    acas012_sales.dispatch(system, sales, file_access, file_defs,
                                      dal_common)

    Note that the LINKAGE SECTION's ``copy`` order [:L264-L274] is different -
    ``wssl``, ``wssystem``, ``wsfnctn``, ``wsnames``, ``Test-Data-Flags`` - so a
    reader working from the copybook list would get the first two parameters the
    wrong way round. The ``USING`` list is authoritative.

    Control enters at ``aa010-main`` because ``aa-Process-Flat-File section``
    [:L285] is the program's first section, and leaves at ``aa-Exit``
    [:L587-L588], whose ``exit program`` returns with the linkage records as they
    stand. Every status, every log field and the record itself live in the
    caller's storage, so ``file_access`` and ``sales`` are the real outputs.

    The eleven published Sales facade verbs all arrive here, each having set
    ``File-Function`` and ``Access-Type`` and, in ten of the eleven cases, zeroed
    ``Access-Type`` first [copybooks/Proc-ACAS-FH-Calls.cob:L652-L707]. The
    exception is ``Sales-Start``, which leaves whatever relation the caller chose
    in place - which is why 5..9 survives into ``aa060`` and IS the START
    relation. See :data:`FACADE_VERBS`.

    Args:
        system: ``System-Record``. Its ``RDBMS-Flat-Statuses`` chooses the half
            of the program that runs, and its six ``RDBMS-*`` fields supply the
            connection parameters.
        sales: ``WS-Sales-Record``. Read by write, re-write, delete and start;
            written by every read.
        file_access: ``File-Access``. Carries the request in
            (``File-Function``, ``Access-Type``, ``File-Key-No``) and the whole
            response out (``FS-Reply``, ``WE-Error``, ``Logging-Data``,
            ``RDB-Data``).
        file_defs: ``File-Defs``. Only the flat-file half consults it, for
            ``file-12`` [copybooks/file12.cob]; the frozen program relies on the
            main menu having filled it (``*> File paths for Cobol File has
            already done in main menu module`` [:L328]).
        dal_common: ``ACAS-DAL-Common-data``. ``SW-Testing`` gates every log
            record and ``Log-File-Rec-Written`` counts them.

    Returns:
        A :class:`~acas_posting.dal.cursor_state.CursorOutcome` mirroring what
        was written into ``file_access``. Provided because a Python caller
        expects a return value; the frozen program has none, and
        ``file_access`` remains the authoritative channel.

    Raises:
        FlatFileStoreNotMigrated: Only from the flat-file half, and only when
            ``File-System-Used`` is 0. See :class:`FlatFileStoreNotMigrated`.

    Example:
        A read-indexed through the ``Sales-Read-Indexed`` facade verb, with the
        system record configured for the RDB path::

            file_access.file_function = FileFunction.READ_INDEXED
            file_access.access_type = 0
            file_access.logging_data.file_key_no = 1
            outcome = dispatch(system, sales, file_access, file_defs, dal_common)
            if outcome.is_ok:
                ...  # `sales` now holds the row
    """
    # `aa-Process-Flat-File Section.` [:L285] is the first section, so control
    # begins at `aa010-main.` [:L287].
    outcome = aa010_main(system, sales, file_access, file_defs, dal_common)
    # `aa-Exit.  exit program.` [:L587-L588].
    aa_exit()
    return outcome


# ===========================================================================
# THE PUBLIC API
# ===========================================================================
#
# Rule R-5 requires that every paragraph of both frozen programs map to a named
# function, and that the mapping be findable. So the paragraph functions are
# exported alongside the two entry points: a reader holding
# `docs/migration/traceability.md` must be able to import any name in it.
#
# Nothing here reaches upward. `dal` may import `dal.connection`, `dal.status`,
# `dal.cursor_state`, one `records` module and `dictionary.loader`, and nothing
# else - Agent Action Plan section 0.4.3's import table - and in particular NOT
# `acas_posting.cobol`, NOT `programs`, NOT `cli`, NOT another `dal.acas*`, NOT
# `dal.facade` and NOT `harness`.
# ===========================================================================

__all__ = (
    # --- the two entry points ------------------------------------------------
    "dispatch",
    "sales_mt",
    # --- identity and provenance --------------------------------------------
    "ENTITY_FACADE",
    "FILE_HANDLER",
    "BRIDGE_PROGRAM",
    "MYSQL_TABLE",
    "TABLE_NAME",
    "COPYBOOK_FILE",
    "COPYBOOK_RECORD",
    "HANDLER_PROG_NAME",
    "BRIDGE_DIRECTIVE_LOCATOR",
    "HOST_VARIABLE_GROUP",
    "HOST_VARIABLE_GROUP_LOCATOR",
    "LOG_SYSTEM",
    "LOG_FILE_NO_COBOL",
    "LOG_FILE_NO_RDB",
    # --- the thirty-seven columns, from the dictionary ----------------------
    "ENTRIES",
    "COLUMN_ORDER",
    "PRIMARY_KEY_COLUMN",
    "RECORD_ATTRIBUTE_FOR_COLUMN",
    "CHARACTER_COLUMNS",
    "SIGN_LOSS_COLUMNS",
    "MONEY_COLUMNS",
    "citations",
    "drift_report",
    # --- the key table and the cursor contract ------------------------------
    "KEY_TABLE",
    "PRIMARY_KEY_OF_REFERENCE",
    "KEY_OFFSET",
    "KEY_LENGTH",
    "KEY_TYPE",
    "READ_BY_NAME_LOW_KEY",
    "READ_BY_NAME_LOW_KEY_TEXT",
    # --- the request vocabulary --------------------------------------------
    "SUPPORTED_FUNCTIONS",
    "GUARDED_KEY_FUNCTIONS",
    "ONLY_FILE_KEY_NO",
    "FACADE_VERBS",
    "WS_NO_PARAGRAPH_HANDLER",
    "WS_NO_PARAGRAPH_BRIDGE",
    "FS_COBOL_FILES_USED",
    "FS_REPLY_OPEN_INPUT_FAILED",
    "TESTING_1_VALUE",
    "COBOL_FILE_STATUS_EOF",
    # --- session and storage -----------------------------------------------
    "BridgeSession",
    "session",
    "reset_session",
    "BridgeWorkingStorage",
    "working_storage",
    "reset_working_storage",
    "HandlerWorkingStorage",
    "handler_storage",
    "reset_handler_storage",
    "HostVariables",
    "HOST_VARIABLE_NAMES",
    # --- the flat-file boundary --------------------------------------------
    "FLAT_FILE_STORE_MIGRATED",
    "FlatFileStoreNotMigrated",
    "SPACE_FILLED_RECORD",
    "SPACE_FILLED_BINARY_BY_WIDTH",
    "BINARY_WIDTH_BY_DIGITS",
    "BINARY_WIDTH_BY_USAGE",
    # --- acas012 paragraphs, in frozen source order ------------------------
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_reread",
    "aa045_eval_keys",
    "aa050_process_read_indexed",
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
    "ba_rdbms_exit",
    "ca_process_logs_acas012",
    # --- salesMT paragraphs, in frozen source order ------------------------
    "ba010_initialise",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba041_reread",
    "ba050_process_read_indexed",
    "ba060_process_start",
    "ba070_process_write",
    "ba080_process_delete",
    "ba090_process_rewrite",
    "ba140_process_read_next",
    "ba141_reread",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "ba999_exit",
    "ca_process_logs",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
)
