"""ISAM ``START`` / ``READ NEXT`` cursor emulation for the ACAS posting cycle.

WHAT THIS MODULE OWNS
=====================
This module owns cursor POSITIONING for the whole data-access layer: the key
metadata each generated bridge declares, the two-state cursor flag each bridge
keeps per read order, and the three positioning verbs the COBOL file handlers
publish - ``fn-start`` (9), ``fn-read-next`` (3) and ``fn-read-indexed`` (4).

It owns no business logic, no record layout and no connection. It is handed a
cursor-like object by the caller and hands back the ``(FS-Reply, We-Error)``
pair the compiled bridge would have left in the caller's ``File-Access`` block.

THE CONTRACT, IN THE MAINTAINER'S OWN WORDS
===========================================
Verbatim from [common/glpostingMT.scb:L243-L245]::

    *> The START condition cannot be compounded, and it must use a
    *> Key of Reference within the record. (These are COBOL rules...)
    *> The interface defines which key and the relation condition.

Everything here follows from those three sentences:

1. **Cannot be compounded** - the generated ``WHERE`` clause carries EXACTLY
   ONE predicate on EXACTLY ONE column. Never an ``AND``, never an ``OR``.
2. **Must use a Key of Reference within the record** - the column is always one
   of the table's declared ``Table-Of-Keynames`` entries, never an arbitrary
   column.
3. **The interface defines which key and the relation** - the caller supplies
   both, the key through the key-of-reference number and the relation through
   ``Access-Type``.

EMULATED, NOT APPROXIMATED
==========================
Agent Action Plan section 0.1.1, verbatim:

    "**Indexed-file read semantics must be emulated, not approximated.** The
    COBOL programs navigate data with ISAM verbs - `START`, `READ NEXT`, `READ`
    by key - expressed through a shared vocabulary of function codes and access
    types `[copybooks/wsfnctn.cob:L88-L118]`. The Python data-access layer must
    reproduce cursor positioning and the `FS-Reply` status protocol, **not
    merely issue equivalent SQL**."

That citation overruns the file: ``copybooks/wsfnctn.cob`` is **117 lines**.
The real spans, traced to the frozen copybook, are ``File-Function``
declared at [copybooks/wsfnctn.cob:L88] with its condition names on L89-L105,
and ``Access-Type`` declared at [copybooks/wsfnctn.cob:L107] with its condition
names on L108-L116. The correction is recorded here rather than silently
applied, because a reader checking L118 would find nothing there.

"Emulated, not approximated" is taken literally. Three examples of the
difference, each of which a merely-equivalent-SQL implementation would lose:

* The two-stage COBOL shape - issue the statement, test the row count, then
  fetch - is reproduced as issue, STORE THE RESULT AND COUNT THE SNAPSHOT, then
  fetch from it, because the COBOL branches DIFFERENTLY at each stage and
  returns a different ``We-Error`` from each. The count NEVER comes from the
  driver's own ``rowcount``; the paragraph above :func:`_column_names` records
  the frozen sequence that settles it and the measurement that makes any other
  reading a defect.
* ``START`` positions but does NOT fetch [common/glpostingMT.cbl:L795-L800], so
  the first ``READ NEXT`` after it must return the row AT the position, not the
  one after it. Modelled by leaving the stored result's first record UNFETCHED -
  :attr:`CursorState.position_inclusive` reports that state.
* A ``READ NEXT`` on an inactive cursor self-positions from a hard-coded low
  key rather than failing, and the relation it uses to do so DIFFERS BY BRIDGE.
  Modelled by :data:`SEQUENTIAL_READ_START`.

WHY NO INDEX MAY EVER BE INVENTED HERE
======================================
Agent Action Plan section 0.6.4, its first and strongest finding, verbatim:

    "**The sort feeds a sequential read.** `gl072` locates the nominal-ledger
    account for each posting with a sequential read-next rather than an indexed
    read `[general/gl072.cbl:L410-L412]`. It finds the correct account only
    because `gl071` has already emitted the transaction stream in nominal-key
    order. Any change in sort stability or key composition produces **silent
    misposting** - no error, no diagnostic, wrong balances."

That citation is off by a few lines. In the frozen program the ledger key is
moved at [general/gl072.cbl:L405] and the sequential read is the guarded
``perform GL-Nominal-Read-Next`` at [general/gl072.cbl:L407-L408]; L410-L412
is the ``move zero to tot-dr tot-cr`` that follows it. The correction is
recorded rather than silently applied, so that a reader who opens L410 and
finds a totals reset knows the finding itself still stands.

So the ordering this module emits IS the posting order, and a wrong ordering
fails silently rather than loudly. Two consequences are absolute:

* This module emits no schema-definition statement of any kind - no
  index-creation DDL, not even as a suggestion in a comment. Agent Action Plan
  section 0.8.4, verbatim: "the migration must not 'optimise' the sequential
  nominal read into an indexed one, even though that would obviously be
  faster, because section 0.6.4's first finding shows the sequential read is
  entangled with sort-order correctness. **Any performance work is therefore
  out of scope by construction, not merely unrequested.**"
* One statement per POSITIONING and none per subsequent fetch, matching the
  bridge exactly: ``mysql_store_result`` materialises the qualifying result once
  and ``MySQL_fetch_record`` then walks it. Nothing is prefetched BEYOND that
  snapshot and nothing is cached ACROSS positionings - see AMBIGUITY Q1 below
  for the measurement that settled the snapshot over a per-call ``LIMIT 1``.

THE ORDERING COLUMN IS THE KEY OF REFERENCE, NOT THE PRIMARY KEY
================================================================
Every one of the 22 in-scope tables has a single-column primary key and ZERO
secondary indexes, counted directly from the frozen ``mysql/ACASDB.sql``.
For 21 of them the primary key and the declared key of reference are the SAME
column, so the distinction never shows.

``GLPOSTING-REC`` is the exception, and it is the table the General Ledger
posting cycle walks. Its primary key is ``POST-RRN``; its key of reference is
``POST-KEY``. The bridge orders by the key of reference - ``KeyName (KOR-x1)``
at [common/glpostingMT.cbl:L466-L470] for the sequential read and
[common/glpostingMT.cbl:L736-L740] for the START - and therefore by
``POST-KEY``, NOT by the primary key. The maintainer flags exactly this at
[common/glpostingMT.scb:L229]::

    *>  WARNING POST-KEY MAY WELL NEED CHANGING TO POST-RRN & RDB made to index fld.

Ordering GL postings by ``POST-RRN`` would be a different sequence, which is
precisely the silent misposting described above. So every ``ORDER BY`` this
module emits names the KEY OF REFERENCE. It remains exactly one column, so the
"no tie-breaker" requirement is honoured in full: there is no second ordering
term anywhere in this file, and none may be added - a tie-breaker cannot be
corroborated by the compiled oracle because the compiled bridge has none.

CURSORS ARE PER (TABLE, SLOT), NOT PER TABLE
============================================
``01 DAL-Data`` declares ONE cursor flag in fourteen bridges and MORE THAN ONE
in six, one flag per read order:

* one slot - ``Most-Cursor-Set`` alone [common/glpostingMT.scb:L249-L251];
* two slots - ``salesMT`` [common/salesMT.cbl:L252-L254], ``purchMT``
  [common/purchMT.cbl:L252-L254], ``slinvoiceMT``
  [common/slinvoiceMT.cbl:L332-L334], ``plinvoiceMT``
  [common/plinvoiceMT.cbl:L333-L335];
* three slots - ``otm3MT`` [common/otm3MT.cbl:L265-L270], ``otm5MT``
  [common/otm5MT.cbl:L267-L272].

So cursor state is keyed by table AND slot. In the two-table bridges the
key-of-reference number selects the TABLE as well as the key: ``slinvoiceMT``
pairs slot 2 with ``set KOR-x1 to 2``, annotated ``*> 2 = Lines``
[common/slinvoiceMT.cbl:L2731].

ANOMALIES REPRODUCED HERE, NEVER FIXED  (RULE R-4)
==================================================
Rule R-4, verbatim: "A defect reproduced is correct; a defect fixed is a
failure." Each entry below is reproduced at a site carrying its locator, and
each belongs in the anomaly register at ``docs/migration/anomaly-log.md``, an
Agent Action Plan deliverable this checkout does not carry.

A1  A ``READ NEXT`` with no prior ``START`` is not defended. The frozen source
    names ``'99RNP'`` for "read next with no position (no start 1st)"
    [copybooks/mysql-procedures.cpy:L118] and then never tests for it. What it
    does instead is SELF-POSITION from a hard-coded low key
    [common/glpostingMT.cbl:L454-L473]. Settled by reading, not left open.
A2  ``FS-Reply 23`` is documented [common/glpostingMT.cbl:L130] and NEVER
    returned. The read-indexed paths return 21, the maintainer's own ``*> from
    23`` comment beside each [common/glpostingMT.cbl:L668, :L676].
A3  The internal SQLSTATE map was designed and never wired up
    [copybooks/mysql-procedures.cpy:L115-L119], and the one test that would
    have used it is commented out [copybooks/mysql-procedures.cpy:L124]. The
    codes are carried here for diagnostics; the RETURNED pair is the compiled
    system's ``(99, 911)`` [copybooks/mysql-procedures.cpy:L127-L128].
A4  ``KOR-Type`` is declared and ignored - "Not used currently"
    [common/glpostingMT.scb:L241], [common/otm5MT.cbl:L260]. Carried in the
    metadata; never branched on. The declared type is not merely unused, it is
    WRONG for half the cycle: counted over the frozen schema, 11 of the 22
    declared keys say ``"STR"`` over a NUMERIC column - ``SYSTEM-REC-KEY``,
    ``SYSDEFLT-REC.DEF-REC-KEY``, ``FINAL-ACC-REC-KEY``,
    ``LEDGER-TOTALS-REC-KEY``, ``LEDGER-KEY``, ``POST-KEY``, ``BATCH-KEY``,
    ``KEY-1``, ``IRSDFLT-REC.DEF-REC-KEY``, ``KEY-4`` and
    ``IRS-FINAL-ACC-REC-KEY`` [mysql/ACASDB.sql]. The single bridge that declares
    a non-string type, ``slpostingMT`` with ``"BNT"``
    [common/slpostingMT.scb:L216], is the ONLY one whose declaration matches its
    column. So a layer that did branch on ``KOR-Type`` would be wrong eleven
    times; the COBOL is accidentally correct BECAUSE it ignores the field.
    Branching on it here is therefore forbidden twice over - once because the
    COBOL does not, and once because the data would mislead.
A5  The ``Access-Type`` validity bound contradicts the declared relations. The
    executable guard is ``if access-type < 5 or > 8``
    [common/glpostingMT.cbl:L695], so 9 is REJECTED with ``(99, 997)`` even
    though ``fn-not-greater-than value 9`` is declared
    [copybooks/wsfnctn.cob:L116] and given a relation arm
    [common/glpostingMT.cbl:L724-L725].
A6  ``ORDER BY`` is ``ASC`` for ALL FIVE relations
    [common/glpostingMT.cbl:L736-L740]. There is no descending branch anywhere,
    so a ``<`` or ``<=`` START positions at the LOWEST qualifying key rather
    than the highest, which is not what ISAM ``START`` means.
A7  The ordinary no-rows ``START`` writes NEITHER status field
    [common/glpostingMT.cbl:L771-L781]. ``21`` is set only when the driver
    reports an error, and it is paired with ``We-Error`` ZERO, not 990/989.
A8  The two OTM sorted-read verbs are doubly broken
    [common/otm3MT.cbl:L1004-L1009, :L1022-L1026]: their ordering terms are
    SINGLE-quoted, so MySQL reads them as string constants and the ordering is
    inert; and their ``WHERE`` carries no predicate at all while the statement
    still concatenates ``" WHERE "``, yielding a syntax error.
A9  The self-positioning relation and low-key literal are hard-coded PER
    BRIDGE and disagree with each other and with the declared key length. Nine
    bridges use ``>`` and eleven use ``>=`` - so a row whose key is exactly the
    low value is silently SKIPPED by the nine and returned by the eleven.
    A TRANSCRIPTION TRAP for anyone checking the table below against the frozen
    source: some bridges carry a trailing comment that contradicts the executable
    ``string`` statement immediately above it. ``slpostingMT`` is the clearest -
    the code builds ``" >= "`` [common/slpostingMT.cbl:L443] while the comment
    two lines later reads ``IRS-POST-KEY > "0000000000" ORDER BY PSIRSPOST-REC
    ASC`` [common/slpostingMT.cbl:L465], which is wrong twice: the relation is
    ``>=`` not ``>``, and the ORDER BY names the KeyName ``IRS-POST-KEY``, not
    the table. Every value in this module is taken from the executable
    ``string``, never from the comment, and each locator points at the
    ``string`` line so the provenance is checkable.
A10 END OF FILE IS STICKY. After fetching a row, ``ba041-Reread`` re-tests the
    CALLER's ``FS-Reply`` and, if it still holds 10, DISCARDS the row unread
    [common/glpostingMT.cbl:L580-L583]. Nothing clears that field - not the
    read paragraphs, not ``ba020-Process-Open``, which only tests it
    [common/glpostingMT.cbl:L420-L421], and not ``Mysql-1000-Open``, which
    writes ``FS-Reply`` only on failure
    [copybooks/mysql-procedures.cpy:L63-L86]. So a second sequential pass in
    one run returns nothing until some unrelated successful operation happens
    to reset the shared linkage field.
A11 A FAILED STATEMENT IS REPORTED AS END OF FILE. In the self-positioning
    stage the two status moves sit inside the zero-rows test but OUTSIDE the
    errno test [common/glpostingMT.cbl:L508-L509], so they overwrite
    ``Mysql-1100-Db-Error``'s ``(99, 911)``
    [copybooks/mysql-procedures.cpy:L127-L128] with ``(10, 10)``. The caller's
    read loop ends cleanly, posts nothing, and reports success. Only the log
    tag distinguishes it - ``"No Data"`` [common/glpostingMT.cbl:L510] versus
    ``"EOF"`` [common/glpostingMT.cbl:L558].
A12 The self-positioning stage hard-codes ``set KOR-x1 to 1``
    [common/glpostingMT.cbl:L455] - identical in all twenty bridges - so it
    always walks key of reference 1 whatever the caller wanted. The two-table
    bridges consequently have NO sequential read for their lines table:
    ``slinvoiceMT``'s only such paragraph selects from ``SAINVOICE-REC``
    [common/slinvoiceMT.cbl:L646-L688].
A13 ``read_indexed``'s ``We-Error`` 990 and 989 branches are UNREACHABLE. The
    first guard filters every zero-row case
    [common/glpostingMT.cbl:L633-L636] and writes ``FS-Reply`` only, leaving
    ``We-Error`` untouched; the second guard, ``not > zero``
    [common/glpostingMT.cbl:L663], can then never be true because the count is
    written only by ``MySQL_affected_rows`` and ``MySQL_num_rows``
    [copybooks/mysql-procedures.cpy:L178, :L191-L192] and the fetch does not
    pass it [common/glpostingMT.cbl:L642-L658].
A14 A broken ``read_indexed`` statement returns the MISMATCHED pair
    ``(21, 911)``: the first guard's ``move 21 to fs-Reply``
    [common/glpostingMT.cbl:L634] overwrites the 99 while the 911 survives in
    ``We-Error`` [copybooks/mysql-procedures.cpy:L127-L128] - "invalid key on
    START" paired with "RDB init error" for a failed statement.
A15 A published facade verb that can NEVER succeed. ``acas008`` refuses FOUR
    verbs at its first act, before any statement exists - read-indexed,
    re-write, start and delete, all four sharing one ``evaluate`` body
    [common/acas008.cbl:L299-L307] - yet the facade still publishes
    ``SPL-Posting-Rewrite`` over it. All four are recorded in
    :data:`HANDLER_REJECTED_FUNCTIONS` even though this module implements only
    two of them, because the guard belongs to the handler rather than to any one
    verb. ``READ NEXT`` is deliberately NOT among them, which is what makes the
    sequential walk of ``PSIRSPOST-REC`` live and ambiguity Q2 reachable.

Rule R-6 governs every one of these: "Where a semantic question is ambiguous,
the compiled program's observed behavior decides it."

AMBIGUITIES FOR THE MIGRATION RECORD  (RULE R-6)
================================================
Most of what looked ambiguous in this module's brief turned out to be settled by
reading, and each such resolution is stated at its site: the ``<``/``<=``
positioning direction is settled by A6, the "does the cursor stay active after
end of file" question by the explicit ``set Cursor-Not-Active to true``
[common/glpostingMT.cbl:L559], the "does read-indexed disturb the sequential
cursor" question by every exit being ``go to ba998-Free``
[common/glpostingMT.cbl:L1033], and the 990-versus-989 question by A13's proof
that both are dead code. TWO questions genuinely cannot be settled by reading and
must be arbitrated against the compiled oracle.

AMBIGUITY Q1 - snapshot versus re-positioning.
    The bridge materialises the ENTIRE qualifying result at positioning time with
    ``mysql_store_result`` [copybooks/mysql-procedures.cpy:L187-L192], records its
    full row count with ``mysql_num_rows`` into ``WS-MYSQL-Count-Rows``, and then
    hands back one record per call from that snapshot with ``MySQL_fetch_record``
    [common/glpostingMT.cbl:L536-L554]. An earlier draft of this module instead
    re-positioned with a ``LIMIT 1`` statement on every call, on the stated ground
    that "rule R-3 forbids buffering a result".

    THAT GROUND WAS A MISREADING OF R-3, which bars added validations, added
    fields, schema change and concurrency - not buffering. Nothing in the rule set
    or in Agent Action Plan section 0.3.3 speaks against materialising a result;
    0.3.3 requires that STATEMENT ORDERING match, which the snapshot matches more
    closely than re-positioning does, since the bridge issues ONE statement per
    positioning and none at all per subsequent fetch.

    RESOLVED - arbitrated against MariaDB 10.11.7 on the frozen schema. Three
    divergence classes were separated and measured:

    * A row INSERTED ahead of the position is invisible to a snapshot and visible
      to re-positioning; a row DELETED ahead is returned by a snapshot and skipped
      by re-positioning. Both need a walk-and-modify, and a census of the frozen
      cycle found none reachable: ``gl080``'s ``del-process`` deletes only the row
      it has just read; its one in-walk insert returns immediately under the
      relational path; ``sl060`` and ``pl060`` always re-issue ``OTM3-Start`` /
      ``OTM5-Start`` before each read loop; and every rewrite targets the row just
      fetched. So these two classes are unreachable.
    * The THIRD class needs no modification at all and IS reachable. Where the key
      of reference is not unique, advancing with ``> last_key`` SKIPS EVERY ROW
      TIED ON THAT KEY. ``GLPOSTING-REC`` is exactly such a table: its key of
      reference ``POST-KEY`` is not its primary key [common/glpostingMT.scb:L232,
      mysql/ACASDB.sql]. Measured on six rows of which three shared one
      ``POST-KEY``, the ``LIMIT 1`` walk delivered FOUR rows where the bridge's
      snapshot delivers SIX. For a posting stream that is silent loss of
      postings - precisely the failure mode Agent Action Plan section 0.6.4 warns
      of - and it would show up as a non-empty state diff under section 0.8.5.

    A fourth, independent observable settles it beyond the row sequence:
    ``WS-MYSQL-Count-Rows`` is the count of the WHOLE qualifying result, which the
    bridge tests separately from the fetch [common/glpostingMT.cbl:L499, :L767].
    Under ``LIMIT 1`` that count can only ever be 0 or 1, so the observable cannot
    be reproduced at all.

    THE RESOLUTION ENCODED HERE. The client-side materialised snapshot is
    reproduced. :func:`start` and :func:`read_next`'s self-positioning stage issue
    the SAME statement the bridge issues - same single predicate, same
    ``ORDER BY`` on the key of reference, NO added tie-breaker and NO ``LIMIT`` -
    materialise every qualifying row, and record the full count. Each subsequent
    ``READ NEXT`` fetches from that snapshot and issues NO statement, as
    ``ba041-Reread`` does. ``ba998-Free`` drops it [:L1023-L1033]. No tie-breaking
    ``ORDER BY`` term is added: inventing one would be ordering the compiled
    system cannot express, and it would not restore the tied rows anyway.

AMBIGUITY Q2 - a quoted string key value against a numeric key column, for
    HALF the cycle.
    Every self-positioning low key in the frozen bridges is a DOUBLE-QUOTED
    STRING literal spliced into the SQL text - ``'"0000000000"'``
    [common/glpostingMT.cbl:L465], [common/slpostingMT.cbl:L444] - and
    ``KOR-Type`` is never consulted to decide otherwise (A4). Counted over the
    frozen schema, 11 of the 22 key-of-reference columns are NUMERIC, so for
    those eleven the compiled system asks MySQL to compare a quoted string
    against an integer column and relies on implicit coercion. That is not a
    one-table curiosity but the majority of the General Ledger and IRS path,
    ``POST-KEY``, ``LEDGER-KEY`` and ``BATCH-KEY`` among them.

    This module binds the same value as a driver PARAMETER rather than splicing a
    literal, because interpolating a key value into SQL text is prohibited
    outright. Both forms hand the server a string, so both should coerce
    identically - but "should" is not evidence. Two sub-cases needed separating:
    the ELEVEN numeric columns, where coercion is string-to-number, and
    ``PSIRSPOST-REC``, whose ``bigint(11)`` column is the only one whose
    ``KOR-Type`` admits it is not a string [common/slpostingMT.scb:L216] and
    whose low key is ten characters for an eight-byte key (A9). Reachability
    differs too: for the eleven both ``START`` and ``READ NEXT`` reach the
    comparison, while for ``PSIRSPOST-REC`` the handler refuses ``START``,
    read-indexed, ``REWRITE`` and ``DELETE`` [common/acas008.cbl:L299-L307] but
    NOT ``READ NEXT``, so only the sequential walk reaches it. A Python-side
    double cannot stand in for the server here - comparing ``int`` against
    ``str`` in process raises ``TypeError`` where MySQL coerces silently, which
    this module masks as end of file per A11. Only real SQL settles it.

    RESOLVED - arbitrated against MariaDB 10.11.7, the version that produced the
    frozen schema [mysql/ACASDB.sql:L1], on the frozen table definitions
    themselves. Both tables were seeded with keys straddling the low value AND
    with a row sitting exactly ON it, which is the boundary ``>=`` is sensitive
    to. The COBOL's string-built statement was issued verbatim - inline
    double-quoted literal, no ``LIMIT`` - beside this module's bound-parameter
    form:

        SELECT * FROM `GLPOSTING-REC` WHERE `POST-KEY` >= "0000000000"
            ORDER BY `POST-KEY` ASC ;            -> first POST-KEY = 0
        this module, bound parameter, LIMIT 1    -> first POST-KEY = 0

        SELECT * FROM `PSIRSPOST-REC` WHERE `IRS-POST-KEY` >= "0000000000"
            ORDER BY `IRS-POST-KEY` ASC ;        -> first IRS-POST-KEY = 0
        this module, bound parameter, LIMIT 1    -> first IRS-POST-KEY = 0

    Identical first row and identical ordering in both sub-cases - the
    ``bigint(10) unsigned`` column whose ``KOR-Type`` wrongly says ``"STR"`` and
    the ``bigint(11)`` column whose ``KOR-Type`` correctly says ``"BNT"``. The
    server applies the same string-to-number coercion to a quoted literal and to
    a bound string, so the transport difference is not observable, and the
    boundary row is included by ``>=`` in both. Q2 therefore resolves BENIGNLY:
    no behavioural divergence, and no change to this module is warranted. It
    still belongs in the ambiguity register, because the answer depends on server
    coercion rather than on anything either implementation controls - a future
    move to a stricter SQL mode could reopen it.

One interactive fragment is reachable from the frozen error path and is DROPPED,
not reproduced: ``display SM901`` followed by ``accept ws-reply``
[copybooks/mysql-procedures.cpy:L134-L137]. Agent Action Plan section 0.3.4 rules
that an accept whose only effect is to block a terminal after an error display is
dropped while its control transfer is preserved; this one falls straight through
to its exit, so no control flow is lost. Recorded as a deliberate omission per
rule R-5 rather than left for a reader to notice.

DETERMINISM  (RULE R-6)
=======================
Importing this module reads no clock, consumes no entropy, opens no connection
and touches no file. It declares no mutable module-level default that a run
could leave dirty for the next one: :func:`reset` exists so that two runs in
one process are independent. No collection whose iteration order reaches SQL
text is unordered, and no ordering anywhere depends on insertion order alone.

VERBATIM QUOTATIONS ARE NOT WRAPPED
===================================
A handful of lines here exceed the width the rest of the file keeps, and every
one of them is a VERBATIM quotation of the frozen COBOL inside a docstring or
comment. Three are longer than 88 characters in the frozen source itself -
[copybooks/wsfnctn.cob:L102], [common/glpostingMT.cbl:L779] and
[common/acas008.cbl:L304] - so no formatting choice makes them fit. Wrapping a
quotation falsifies it, and this module's authority rests on quoting the
specification exactly.

BINDING RULES OBSERVED  (NO USER RULES DOCUMENT EXISTS)
=======================================================
The Agent Action Plan records that this project has NO separate user rules
document; its six numbered rules are the binding ones. Those bearing here:
R-1, no COBOL at runtime - the COBOL is cited in prose only; nothing launches a
process, loads a foreign library or reaches the compiled oracle. R-2, zero
binary floating point - key values are ``str``, ``int`` or ``Decimal`` and are
compared exactly, because a key through a binary float would compare wrongly at
the boundaries, which for a positioning predicate means positioning on the wrong
row. R-3, no schema change and no concurrency - no schema-definition statement of
any kind, and execution is strictly sequential with no thread, event loop, worker
or connection pool. R-5, full traceability - the key metadata is DATA transcribed
from the frozen bridges, each entry carrying its own
``[common/<bridge>.<ext>:L<n>]`` locator and its
``<TABLE-NAME>.<COLUMN-NAME>`` dictionary key, and there is not one hand-written
per-table branch in this file.

FROZEN PATHS READ AS SPECIFICATION AND NEVER MODIFIED
=====================================================
``common/*.cbl``, ``common/*.scb``, ``copybooks/*.cob`` and
``mysql/ACASDB.sql``. Any diff touching them is a defect in the migration,
regardless of how harmless it appears.
"""

from __future__ import annotations

import enum
import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import ClassVar, Final, Protocol, runtime_checkable

from acas_posting.dal.connection import quote_identifier
from acas_posting.dal.status import (
    START_ACCESS_TYPE_RANGE,
    START_RELATION_BY_ACCESS_TYPE,
    START_RELATION_TOKEN_BY_ACCESS_TYPE,
    AccessType,
    FileFunction,
    FsReply,
    SqlState,
    WeError,
    end_of_file_status,
    log_handler_failure,
    start_access_type_is_valid,
    start_relation_for,
)
from acas_posting.records.file_access import FileAccess

__all__: Final[tuple[str, ...]] = (
    # Sorted as ruff's RUF022 orders a name list - SCREAMING_CASE constants,
    # then the types, then the callables - so the tuple is stable, reviewable,
    # and identical in every process (rule R-6).
    # `ACCESS_TYPE_TO_RELATION` and `ACCESS_TYPE_TO_RELATION_TOKEN` are
    # RE-EXPORTS: `dal/status.py` declares the `Access-Type` enum and its
    # relation mapping once and this module does not redeclare them. They are
    # published here so a caller of these verbs needs one import, and because the
    # module that BUILDS the `START` predicate should publish the table that
    # predicate is built from. `AccessType` below is the same re-export.
    # The relation reaches a `START` through `Access-Type` at all only because
    # the `-Start` facade verb refuses to zero the field, unlike every sibling
    # verb [copybooks/Proc-ACAS-FH-Calls.cob:L18, :L456-L463].
    "ACCESS_TYPE_TO_RELATION",
    "ACCESS_TYPE_TO_RELATION_TOKEN",
    "EXTRA_READ_ORDERS",
    "HANDLER_REJECTED_FUNCTIONS",
    "LEGAL_RELATIONS",
    "LEGAL_RELATION_TOKENS",
    "POSITIONING_FUNCTIONS",
    "SEQUENTIAL_READ_START",
    "TABLE_OF_KEYNAMES",
    "TABLE_PRIMARY_KEYS",
    "AccessType",
    "CursorOutcome",
    "CursorSlot",
    "CursorState",
    "CursorStateTable",
    "DatabaseCursor",
    "ExtraReadOrder",
    "KeyOfReference",
    "MostRelation",
    "OrderQuoting",
    "OrderTerm",
    "SequentialReadStart",
    "key_of_reference",
    "keys_for",
    "quote_identifier",
    "read_indexed",
    "read_next",
    "reset",
    "start",
)

#: Module logger. A library module attaches no handler and configures no root
#: logger; the application decides where diagnostics go. The COBOL equivalent
#: is `Mysql-1110-Report-Problem` [copybooks/mysql-procedures.cpy:L130-L137],
#: which only displays to a curses screen and has no database effect, so Agent
#: Action Plan section 0.3.4 makes it a log record here rather than output.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)

#: The bridge whose positioning paragraphs this module reproduces, named in every
#: record it emits so that a reader can put the record back against the frozen
#: source (rule R-5).
#:
#: ONE NAME FOR ALL TWENTY BRIDGES, and that is a fact about the frozen source
#: rather than a simplification: `presql2` generates the same `ba050`, `ba060` and
#: `ba070` paragraphs into every `*MT.cbl`, so `common/glpostingMT.cbl` is the
#: representative every locator in this module already cites.
_BRIDGE_PROGRAM: Final[str] = "glpostingMT"


#  IDENTIFIER QUOTING
# `acas_posting/dal/connection.py` owns identifier quoting for the layer, and
# this module defers to it so there is ONE implementation. The import is
# UNCONDITIONAL, and that is a correctness requirement rather than tidiness.
#
# A guarded import with a local fallback would be wrong twice over. First, the
# two implementations would not agree: the canonical helper applies the frozen
# bridge's `delimited by space` rule before quoting - a COBOL key name is a
# fixed-width, space-padded item, and the bridge quotes only its significant
# characters, stringing a backtick, the name `delimited by space`, and a
# backtick [common/glpostingMT.cbl:L602-L604] - so a padded name taken from a
# record layout would produce `` `BATCH-KEY` `` through one path and
# `` `BATCH-KEY   ` `` through the other, which are DIFFERENT identifiers to
# MySQL. Second, `except ImportError` is not selective: it would also swallow
# an ImportError raised from INSIDE connection.py, including a missing or
# broken database driver, and silently continue with a divergent helper instead
# of reporting the dependency that is actually absent.
#
# Backticks themselves are not cosmetic: EVERY ACAS table and column name
# contains a hyphen - the key column at [common/glpostingMT.cbl:L729-L731], the
# table at [common/glpostingMT.cbl:L758] (`"`GLPOSTING-REC`"`) - and MySQL
# parses an unquoted hyphen as subtraction, so an unquoted ACAS identifier is a
# syntax error.
#
# The layering permits this: Agent Action Plan section 0.4.3 allows a
# `dal/acas*.py` module to import `dal.connection`, and this positioning module
# sits in the same layer. What the import costs is stated exactly rather than
# glossed: it opens NO connection and no socket - connection.py defines its
# settings, converters and helpers at import time and connects only when asked -
# but it does pull in the pinned driver, `mysql-connector-python==26.7.0`, which
# connection.py imports at module level. That is a declared, mandatory
# dependency of this distribution, so requiring it here narrows nothing; and it
# does not reach the infrastructure-free parity suite, which section 0.4.3
# confines to `cobol` and `records` and forbids from importing `dal` at all. The
# positioning logic itself still needs no database: `DatabaseCursor` below is a
# protocol, not a driver type.
#
# The statement itself sits with the other imports at the head of the module,
# where every import belongs; `quote_identifier` is re-exported in `__all__`
# above so a reader of this module's surface still finds it named here.


#  THE DRIVER BOUNDARY


@runtime_checkable
class DatabaseCursor(Protocol):
    """The narrow slice of a DB-API cursor this module needs.

    Declared as a protocol rather than imported from a driver for three
    reasons. Connection handling belongs to ``connection.py`` and importing a
    driver here would duplicate that ownership. Rule R-3 forbids a connection
    pool, so there is no pool type to depend on. And a protocol keeps the
    positioning logic testable with no database at all, which is what lets the
    parity tests run anywhere.

    ``rowcount`` IS DELIBERATELY NOT A MEMBER, although the bridge's
    ``WS-MYSQL-Count-Rows`` looks like its analogue. The count the COBOL tests
    separately from the fetch at [common/glpostingMT.cbl:L499], [:L767],
    [:L771] and [:L633] is ``MySQL_num_rows`` over a STORED result, so this
    module derives it from the snapshot it materialised - see the paragraph
    above :func:`_column_names` for the frozen sequence and for the measurement
    that removed the driver's ``rowcount`` from the fetch decision. Requiring a
    member nothing reads would put a demand on ``connection.py``'s driver
    choice for no benefit, so the protocol stays at the two verbs and the one
    property the positioning logic actually uses.
    """

    @property
    def description(self) -> Sequence[Sequence[object]] | None:
        """Column metadata for the last statement, or ``None``."""

    def execute(
        self,
        operation: str,
        parameters: Sequence[object] | None = None,
        /,
    ) -> object:
        """Issue one statement with its parameters bound by the driver."""

    def fetchone(self) -> Sequence[object] | Mapping[str, object] | None:
        """Return the next row, or ``None`` at end of result.

        Deliberately the ONLY fetch verb in this protocol, so that any driver
        ``connection.py`` chooses satisfies it. Where the bridge's
        ``mysql_store_result`` has to be reproduced, :func:`_store_result` drains
        this verb in a loop rather than widening the protocol with ``fetchall``.
        """


#  MOST-RELATION  -  THE FIVE RELATION STRINGS


@dataclass(frozen=True, slots=True)
class MostRelation:
    """The ``MOST-Relation`` field, reproduced as a three-character value.

    Mirrors [common/glpostingMT.scb:L248] one-for-one, comment included::

        05  MOST-Relation   pic xxx.                  *> valid are >=, <=, <, >, =

    Three characters holding a one- or two-character token, so ``>=`` and ``<=``
    are SPACE-PADDED on the right and ``<``, ``>`` and ``=`` are padded by two.
    The bridge stores the padded literal - ``move spaces to MOST-Relation``
    followed by the relation arms [common/glpostingMT.cbl:L713-L726] - and then
    builds its ``WHERE`` clause with ``MOST-relation delimited by space``
    [common/glpostingMT.cbl:L732], which stops at the first space. So the field
    is three characters wide and the SQL sees the trimmed token, exactly as
    :attr:`padded` and :attr:`token` express here.

    The ``Access-Type`` to relation mapping is NOT redeclared: it is owned by
    ``dal/status.py`` and re-exported below, because that module owns the whole
    operation vocabulary and a second copy could only drift from it.
    """

    #: The three-character stored form, e.g. ``">= "``. The ONLY field, so a
    #: relation is constructed from its stored value and nothing else.
    padded: str

    #: Width of the field, from ``pic xxx``. Named rather than inlined so the
    #: padding assertions in the tests cite the declaration and not a literal.
    #: ``ClassVar`` and not ``Final``: inside a dataclass a bare ``Final``
    #: annotation would become a second FIELD with a default, which would let a
    #: caller construct a relation of the wrong declared width.
    WIDTH: ClassVar[int] = 3

    def __post_init__(self) -> None:
        """Enforce the ``pic xxx`` width and the five declared values."""
        if len(self.padded) != MostRelation.WIDTH:
            raise ValueError(
                f"MOST-Relation is pic xxx, so it holds exactly "
                f"{MostRelation.WIDTH} characters; got {self.padded!r}"
            )
        if self.padded.strip() not in LEGAL_RELATION_TOKENS:
            raise ValueError(
                f"{self.padded.strip()!r} is not one of the five relations "
                f"declared at [common/glpostingMT.scb:L248]: "
                f"{', '.join(LEGAL_RELATION_TOKENS)}"
            )

    @property
    def token(self) -> str:
        """The trimmed relation that reaches the SQL text.

        Reproduces ``MOST-relation delimited by space``
        [common/glpostingMT.cbl:L732].

            >>> MostRelation(">= ").token
            '>='
            >>> MostRelation("=  ").token
            '='
        """
        return self.padded.strip()

    @classmethod
    def of(cls, token: str) -> MostRelation:
        """Build from a trimmed token, padding to ``pic xxx`` as the bridge does.

        Args:
            token: One of ``>=``, ``<=``, ``<``, ``>``, ``=``.

        Returns:
            The relation in its stored, space-padded form.
        """
        return cls(token.ljust(cls.WIDTH))

    @classmethod
    def for_access_type(cls, access_type: AccessType | int) -> MostRelation:
        """Build from an ``Access-Type``, deferring to ``dal/status.py``.

        The relation table is consulted through
        :func:`acas_posting.dal.status.start_relation_for` rather than copied,
        so there is exactly one declaration of it in the package.

        ANOMALY A5 - REPRODUCED, NOT FIXED.  This accessor will happily map
        ``Access-Type`` 9 to ``"<= "``, because the frozen ``evaluate`` declares
        that arm [common/glpostingMT.cbl:L724-L725] and
        ``fn-not-greater-than value 9`` is declared
        [copybooks/wsfnctn.cob:L116]. Reaching it in the compiled system is
        impossible, because the parameter guard rejects 9 first
        [common/glpostingMT.cbl:L695]. :func:`start` therefore applies
        :func:`~acas_posting.dal.status.start_access_type_is_valid` BEFORE
        coming here, which keeps the arm exactly as dead as it is in COBOL
        while leaving the declaration intact. Widening the guard or deleting
        the arm would each be a defect fix.

        Args:
            access_type: An ``Access-Type`` in the 5-9 relation band.

        Returns:
            The relation in its stored, space-padded form.
        """
        return cls(start_relation_for(access_type, padded=True))


#: The five relations declared at [common/glpostingMT.scb:L248], trimmed, in the
#: order the comment lists them - ``>=``, ``<=``, ``<``, ``>``, ``=``. Declared
#: as a tuple rather than a set so that iteration order is fixed: rule R-6
#: forbids any ordering that a run could vary.
LEGAL_RELATION_TOKENS: Final[tuple[str, ...]] = (">=", "<=", "<", ">", "=")

#: Re-export of ``dal/status.py``'s ``Access-Type`` to relation mapping, under
#: the name the agent brief uses. ``dal/status.py`` OWNS it - declared there once
#: and not redeclared here - and this alias exists so the module that builds the
#: ``START`` predicate publishes the table that predicate is built from.
#:
#: The five entries are 5 to ``=``, 6 to ``<``, 7 to ``>``, 8 to ``>=`` and 9 to
#: ``<=``, matching ``fn-equal-to`` through ``fn-not-greater-than``
#: [copybooks/wsfnctn.cob:L112-L116]. ``NOT LESS THAN`` is ``>=`` and ``NOT
#: GREATER THAN`` is ``<=`` - not their inverses. Entry 9 is present and
#: UNUSABLE: :func:`start`'s guard rejects it (anomaly A5
#: [common/glpostingMT.cbl:L695]), but it stays because the frozen source
#: declares both the relation and an arm for it - removing it would hide that.
ACCESS_TYPE_TO_RELATION: Final[Mapping[int, str]] = START_RELATION_BY_ACCESS_TYPE

#: The same mapping with the relation TRIMMED to its token, for direct use in
#: statement text. The bridge trims by writing ``MOST-relation delimited by
#: space`` [common/glpostingMT.cbl:L732].
ACCESS_TYPE_TO_RELATION_TOKEN: Final[Mapping[int, str]] = (
    START_RELATION_TOKEN_BY_ACCESS_TYPE
)

#: The same five in their stored ``pic xxx`` form, aligned with the tuple above.
LEGAL_RELATIONS: Final[tuple[MostRelation, ...]] = tuple(
    MostRelation.of(token) for token in LEGAL_RELATION_TOKENS
)


#  CURSOR SLOTS  -  ONE PER READ ORDER, NOT ONE PER TABLE


class CursorSlot(enum.IntEnum):
    """Which ``Most-Cursor-Set`` flag of ``01 DAL-Data`` a read order uses.

    Fourteen of the twenty in-scope bridges declare one flag; six declare two
    or three, one per read order, and the suffix in the COBOL name IS the slot
    number. Reproduced as an enumeration so a caller names the read order
    rather than passing a bare integer.

        >>> [int(member) for member in CursorSlot]
        [1, 2, 3]
    """

    #: `05  Most-Cursor-Set pic 9    value zero.` [common/glpostingMT.scb:L249]
    #: The sequential cursor driven by `fn-start` and `fn-read-next`. Every
    #: bridge has this one.
    PRIMARY = 1

    #: `05  Most-Cursor-Set-2 pic 9    value zero.` under the maintainer's own
    #: heading `*> Special for selective read next.`
    #: [common/salesMT.cbl:L250-L254]. Serves `fn-Read-By-Name` in
    #: `salesMT`/`purchMT`, `fn-Read-By-Batch` in `otm3MT`/`otm5MT`, and the
    #: lines-table read in `slinvoiceMT`/`plinvoiceMT`, where it is paired with
    #: `set KOR-x1 to 2` annotated `*> 2 = Lines`
    #: [common/slinvoiceMT.cbl:L2731].
    SECONDARY = 2

    #: `03  Most-Cursor-Set-3 pic 9  value zero.      *> RG 2 or special`
    #: [common/otm3MT.cbl:L268-L270]. Declared only by `otm3MT` and `otm5MT`,
    #: where it serves `fn-Read-By-Cust`.
    TERTIARY = 3


#: The three ``File-Function`` codes this module implements, in the numeric
#: order [copybooks/wsfnctn.cob] declares them. Published so the facade and the
#: handler modules can test membership against data instead of a literal list.
POSITIONING_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    # `88  fn-read-next       value 3.`     [copybooks/wsfnctn.cob:L91]
    FileFunction.READ_NEXT,
    # `88  fn-read-indexed    value 4.`     [copybooks/wsfnctn.cob:L92]
    FileFunction.READ_INDEXED,
    # `88  fn-start           value 9.`     [copybooks/wsfnctn.cob:L97]
    FileFunction.START,
)


#  KEY OF REFERENCE  -  THE DECLARED METADATA AS A VALUE OBJECT

#: Width of the packed offset/length string, `pic x(8)`
#: [common/glpostingMT.scb:L233]. Two `9(4)` subfields redefined over it
#: [common/glpostingMT.scb:L239-L240].
_OFFSET_LENGTH_WIDTH: Final[int] = 8

#: Width of each `9(4)` half of that string.
_OFFSET_LENGTH_HALF: Final[int] = 4

#: Width of `KeyName pic x(30)` [common/glpostingMT.scb:L238]. Several bridges
#: write a literal shorter than this - `'DEF-REC-KEY              '` is 25
#: characters [common/dfltMT.scb:L259] and `'IL-LINE-KEY'` is 11
#: [common/slinvoiceMT.scb:L301] - and COBOL pads the remainder with spaces. The
#: padded form is what this module stores, so the declaration and the value
#: agree.
_KEY_NAME_WIDTH: Final[int] = 30

#: Width of `KOR-Type pic XXX` [common/glpostingMT.scb:L241].
_KOR_TYPE_WIDTH: Final[int] = 3

#: Largest value `KOR-Offset pic 9(4)` and `KOR-Length pic 9(4)` can hold
#: [common/glpostingMT.scb:L239-L240]. Four unsigned digits, so 0 through 9999.
#: Named rather than repeated so the picture clause is stated once.
_OFFSET_LENGTH_MAX: Final[int] = 9999


@dataclass(frozen=True, slots=True)
class KeyOfReference:
    """One ``keyOfReference`` slot, field-for-field as the bridges declare it.

    Mirrors [common/glpostingMT.scb:L237-L241] exactly::

        03  keyOfReference occurs 1    indexed by KOR-x1.
            05 KeyName      pic x(30).
            05 KOR-Offset   pic 9(4).
            05 KOR-Length   pic 9(4).
            05 KOR-Type     pic XXX.                    *> Not used currently

    which redefines the three ``filler`` literals above it
    [common/glpostingMT.scb:L231-L234] - the name, the packed eight-character
    offset/length string, and the type.

    ``kor_offset`` and ``kor_length`` describe BYTES OF THE WORKING-STORAGE
    RECORD, not a column ordinal and not a character index into anything else.
    They are load-bearing rather than documentation: the bridge slices the key
    VALUE straight out of the record with them, ``WS-Posting-Record (K:L)``
    after ``move KOR-offset (KOR-x1) to K`` and ``move KOR-length (KOR-x1) to
    L`` [common/glpostingMT.cbl:L710-L711, :L734]. The offset is ONE-BASED, as
    every COBOL reference modifier is; :attr:`record_slice` performs the
    conversion to Python's zero-based indexing in one named place so that no
    caller does it silently.

    ANOMALY A4 - REPRODUCED, NOT FIXED.  ``KOR-Type`` carries the maintainer's
    own comment "Not used currently" at [common/glpostingMT.scb:L241] and again
    at [common/otm5MT.cbl:L260]. It is carried here because the frozen source
    declares it, and it is never branched on anywhere in this module, because
    the frozen source never branches on it either. Note that it is NOT always
    ``"STR"``: ``slpostingMT`` declares ``"BNT"`` with the comment ``*> key is
    bigint`` [common/slpostingMT.scb:L216], so a reader who assumed one value
    would be wrong about one of the twenty-two keys.
    """

    #: `05 KeyName pic x(30).` [common/glpostingMT.scb:L238] - stored BLANK
    #: PADDED to the declared 30 characters, which is the form COBOL holds even
    #: where the source literal is shorter. Use :attr:`name` for the trimmed
    #: form.
    key_name: str

    #: `05 KOR-Offset pic 9(4).` [common/glpostingMT.scb:L239] - the ONE-BASED
    #: byte offset of the key within the working-storage record.
    kor_offset: int

    #: `05 KOR-Length pic 9(4).` [common/glpostingMT.scb:L240] - the key's
    #: length in bytes of that record.
    kor_length: int

    #: `05 KOR-Type pic XXX.` [common/glpostingMT.scb:L241] - declared, carried,
    #: never branched on. See anomaly A4 above.
    kor_type: str

    #: The MySQL table this key addresses. Held per key rather than per bridge
    #: because in the two-table bridges the key NUMBER selects the table too:
    #: `slinvoiceMT` key 1 is annotated `*> In SAINVOICE-REC` and key 2
    #: `*> In SAINV-LINES-REC` [common/slinvoiceMT.scb:L297, :L301].
    table_name: str

    #: The MySQL column the key name resolves to. Traced to the frozen
    #: `mysql/ACASDB.sql`: every one of the twenty-two key names IS a real
    #: column of its table.
    column_name: str

    #: `[common/<bridge>.<ext>:L<n>]` for the three declaring lines, required by
    #: rule R-5 so that every entry can be checked against the frozen source
    #: without searching for it.
    source_locator: str

    #: Which `Most-Cursor-Set` flag this read order uses. See :class:`CursorSlot`.
    cursor_slot: CursorSlot = CursorSlot.PRIMARY

    def __post_init__(self) -> None:
        """Enforce the declared PICTURE widths and the offset/length domain.

        These checks assert that the TRANSCRIPTION matches the declaration; they
        are not new validation of run-time data, which rule R-3 forbids. Every
        value they guard is a literal in this module, so a failure here is a
        transcription error caught at import rather than a caller's mistake.
        """
        if len(self.key_name) != _KEY_NAME_WIDTH:
            raise ValueError(
                f"KeyName is pic x({_KEY_NAME_WIDTH}); "
                f"{self.key_name!r} is {len(self.key_name)} characters"
            )
        if len(self.kor_type) != _KOR_TYPE_WIDTH:
            raise ValueError(
                f"KOR-Type is pic XXX; {self.kor_type!r} is "
                f"{len(self.kor_type)} characters"
            )
        # `pic 9(4)` is unsigned and four digits, so 0..9999; a key of zero
        # length or at offset zero could not be sliced out of the record.
        if not 1 <= self.kor_offset <= _OFFSET_LENGTH_MAX:
            raise ValueError(
                f"KOR-Offset is pic 9(4) and one-based; got {self.kor_offset}"
            )
        if not 1 <= self.kor_length <= _OFFSET_LENGTH_MAX:
            raise ValueError(
                f"KOR-Length is pic 9(4) and non-zero; got {self.kor_length}"
            )

    @property
    def name(self) -> str:
        """The key name with the ``pic x(30)`` padding removed.

        This is the form that reaches the SQL text, because the bridge writes
        ``KeyName (KOR-x1) delimited by space``
        [common/glpostingMT.cbl:L730], and ``delimited by space`` stops at the
        first space.
        """
        return self.key_name.strip()

    @property
    def dictionary_key(self) -> str:
        """The ``<TABLE-NAME>.<COLUMN-NAME>`` key for this field (rule R-5).

        Every record field must cite a data-dictionary entry; a key of
        reference cites the column it positions on.
        """
        return f"{self.table_name}.{self.column_name}"

    @property
    def offset_length_string(self) -> str:
        """The packed ``pic x(8)`` form, e.g. ``"00010010"``.

        Provided so the encoding ROUND-TRIPS:
        :meth:`from_offset_length_string` parses this form and this property
        regenerates it, which makes the transcription checkable against the
        frozen literal rather than merely plausible.
        """
        return (
            f"{self.kor_offset:0{_OFFSET_LENGTH_HALF}d}"
            f"{self.kor_length:0{_OFFSET_LENGTH_HALF}d}"
        )

    @property
    def record_slice(self) -> slice:
        """The key's span in the working-storage record, zero-based.

        The single place the one-based COBOL reference modifier
        ``WS-Posting-Record (K:L)`` [common/glpostingMT.cbl:L734] is converted
        to Python indexing. Stated explicitly rather than applied silently, as
        the offset's one-basedness is the kind of detail that goes wrong once
        and then goes wrong everywhere.

            >>> TABLE_OF_KEYNAMES["GLPOSTING-REC"][0].record_slice
            slice(0, 10, None)
        """
        begin = self.kor_offset - 1
        return slice(begin, begin + self.kor_length)

    def key_from_record(self, record_image: str) -> str:
        """Slice this key's value out of a working-storage record image.

        Reproduces ``WS-Posting-Record (K:L)``
        [common/glpostingMT.cbl:L734, :L606] where ``K`` and ``L`` are this
        key's offset and length [common/glpostingMT.cbl:L710-L711].

        Args:
            record_image: The record as its fixed-width character image.

        Returns:
            The ``kor_length`` bytes beginning at ``kor_offset``. A record image
            shorter than the key's span yields a short value, exactly as a
            COBOL reference modifier over a short field would, rather than an
            exception - no new validation is introduced (rule R-3).
        """
        return record_image[self.record_slice]

    @classmethod
    def from_offset_length_string(
        cls,
        *,
        key_name: str,
        offset_length: str,
        kor_type: str,
        table_name: str,
        column_name: str,
        source_locator: str,
        cursor_slot: CursorSlot = CursorSlot.PRIMARY,
    ) -> KeyOfReference:
        """Build from the raw declared literals, parsing the packed form.

        This is how every entry of :data:`TABLE_OF_KEYNAMES` is built, so the
        table below reads as a transcription of the frozen ``filler`` values
        rather than as pre-digested numbers: the eight-character string appears
        in the Python exactly as it appears in the COBOL.

        Args:
            key_name: The ``pic x(30)`` literal, padded here if the frozen
                source wrote it short - as ``'IL-LINE-KEY'``
                [common/slinvoiceMT.scb:L301] and
                ``'DEF-REC-KEY              '`` [common/dfltMT.scb:L259] both
                are.
            offset_length: The ``pic x(8)`` literal, e.g. ``"00010010"``, whose
                first four characters are ``KOR-Offset`` and last four
                ``KOR-Length`` [common/glpostingMT.scb:L233, :L239-L240].
            kor_type: The ``pic XXX`` literal - ``"STR"`` for twenty-one keys
                and ``"BNT"`` for ``slpostingMT``.
            table_name: The MySQL table this key addresses.
            column_name: The MySQL column the key name resolves to.
            source_locator: ``[common/<bridge>.<ext>:L<n>]``.
            cursor_slot: Which ``Most-Cursor-Set`` flag the read order uses.

        Returns:
            The parsed key of reference.

        Raises:
            ValueError: If the packed string is not eight characters or is not
                all digits. Both would mean the transcription had drifted from
                the frozen literal, which is worth failing at import for.

            >>> KeyOfReference.from_offset_length_string(
            ...     key_name="POST-KEY",
            ...     offset_length="00010010",
            ...     kor_type="STR",
            ...     table_name="GLPOSTING-REC",
            ...     column_name="POST-KEY",
            ...     source_locator="[common/glpostingMT.scb:L232]",
            ... ).offset_length_string
            '00010010'
        """
        if len(offset_length) != _OFFSET_LENGTH_WIDTH:
            raise ValueError(
                f"the offset/length filler is pic x({_OFFSET_LENGTH_WIDTH}); "
                f"{offset_length!r} is {len(offset_length)} characters"
            )
        if not offset_length.isdigit():
            raise ValueError(
                f"KOR-Offset and KOR-Length are pic 9(4), so the packed "
                f"filler must be all digits; got {offset_length!r}"
            )
        return cls(
            key_name=key_name.ljust(_KEY_NAME_WIDTH),
            kor_offset=int(offset_length[:_OFFSET_LENGTH_HALF]),
            kor_length=int(offset_length[_OFFSET_LENGTH_HALF:]),
            kor_type=kor_type,
            table_name=table_name,
            column_name=column_name,
            source_locator=source_locator,
            cursor_slot=cursor_slot,
        )


#  ORDERING AND SELF-POSITIONING METADATA


class OrderQuoting(enum.StrEnum):
    """How a bridge quotes an ordering term, which decides whether it works.

    Not a stylistic distinction. In MySQL a backtick-quoted name is an
    IDENTIFIER and a single-quoted name is a STRING CONSTANT, so an ordering
    term written with single quotes sorts every row by the same constant and
    orders nothing at all. Both spellings occur in the frozen bridges, so both
    are modelled - see anomaly A8 on :data:`EXTRA_READ_ORDERS`.
    """

    #: A real identifier, e.g. ``` `SALES-NAME` ``` [common/salesMT.cbl:L1016-L1018].
    IDENTIFIER = "BACKTICK"

    #: A string constant that MySQL will not treat as a column, e.g.
    #: ``'OI3-INVOICE'`` [common/otm3MT.cbl:L1005].
    STRING_CONSTANT = "SINGLE-QUOTE"


@dataclass(frozen=True, slots=True)
class OrderTerm:
    """One term of a declared ``ORDER BY``, transcribed with its quoting.

    The primary sequential read and the START both order by a single term - the
    key of reference, ascending [common/glpostingMT.cbl:L466-L470, :L736-L740].
    The extra read verbs declare several, and ``otm3MT``/``otm5MT`` mix
    directions within one clause [common/otm3MT.cbl:L1004-L1009].
    """

    #: The column named by the term, as the bridge spells it.
    column_name: str

    #: ``"ASC"`` or ``"DESC"`` as declared. Never inferred: the frozen source
    #: writes a direction on some terms and lets others inherit the previous
    #: one, and this records what is written.
    direction: str

    #: Whether the bridge wrote a real identifier or a string constant.
    quoting: OrderQuoting

    #: `[common/<bridge>.<ext>:L<n>]` for the declaring line.
    source_locator: str

    def __post_init__(self) -> None:
        """Enforce that the direction is one of the two SQL keywords."""
        if self.direction not in ("ASC", "DESC"):
            raise ValueError(
                f"an ORDER BY direction is ASC or DESC; got {self.direction!r}"
            )

    def to_sql(self) -> str:
        """Render the term as the bridge renders it, quoting included.

        A term the bridge single-quoted is rendered single-quoted, because
        rendering it as an identifier would FIX anomaly A8 and rule R-4 makes a
        defect fixed a failure. Callers that render an inert term get inert
        ordering, exactly as the compiled system does.
        """
        if self.quoting is OrderQuoting.STRING_CONSTANT:
            # Reproduced, not fixed: single quotes make this a constant.
            # [common/otm3MT.cbl:L1005-L1008]
            escaped = self.column_name.replace("'", "''")
            return f"'{escaped}' {self.direction}"
        return f"{quote_identifier(self.column_name)} {self.direction}"


@dataclass(frozen=True, slots=True)
class SequentialReadStart:
    """How one bridge self-positions a ``READ NEXT`` on an inactive cursor.

    ANOMALY A1 - REPRODUCED, NOT FIXED.  The frozen source names ``'99RNP'``
    for "read next with no position (no start 1st)"
    [copybooks/mysql-procedures.cpy:L118] and then never tests for it. What
    ``ba040-Process-Read-Next`` does instead, when ``Cursor-Not-Active``, is
    build its OWN positioning predicate from a hard-coded low key and fall
    through to the fetch [common/glpostingMT.cbl:L454-L473]. So the compiled
    behaviour is self-positioning, not diagnosis, and raising a helpful error
    here would be a defect fix.

    ANOMALY A9 - REPRODUCED, NOT FIXED.  The relation and the low-key literal
    are hard-coded PER BRIDGE and do not agree with each other:

    * Nine bridges use ``>`` and eleven use ``>=``. With an all-zeros low key
      that difference is observable - the nine SKIP a row whose key is exactly
      the low value, the eleven return it. ``nominalMT`` even annotates the
      choice, ``*> 26/12/16 NOT '='`` [common/nominalMT.cbl:L466], while
      ``glbatchMT`` annotates the opposite choice with a question,
      ``*> nom uses >  ??`` [common/glbatchMT.cbl:L472].
    * The literal's width does not always match ``KOR-Length``.
      ``slpostingMT`` declares an eight-byte key [common/slpostingMT.scb:L215]
      and self-positions with TEN zeros [common/slpostingMT.cbl:L444], and the
      five one-byte keys all self-position with THREE.

    Both are recorded as data so that neither can be normalised by accident.
    """

    #: The relation the bridge hard-codes, as a `MOST-Relation` value.
    relation: MostRelation

    #: The low-key literal the bridge hard-codes, e.g. ``"0000000000"``.
    low_key: str

    #: `[common/<bridge>.cbl:L<n>]` of the relation literal.
    relation_locator: str

    #: `[common/<bridge>.cbl:L<n>]` of the low-key literal.
    low_key_locator: str

    #: The maintainer's own comment beside the relation, verbatim, or ``""``.
    note: str = ""


@dataclass(frozen=True, slots=True)
class ExtraReadOrder:
    """One of the four extra read verbs, with its declared ordering.

    ``copybooks/wsfnctn.cob`` declares four ``File-Function`` codes beyond the
    twelve-verb set, each with the maintainer's own comment naming the programs
    that use it [copybooks/wsfnctn.cob:L102-L105]::

        88  fn-Read-By-Name    value 31.       *> 15/01/17 for Salesled (SL160), could be used for GL ledger?
        88  fn-Read-By-Batch   value 32.       *> 08/02/17 for OTM3/5 (sl095/pl095)
        88  fn-Read-By-Cust    value 33.       *> 09/02/17 for OTM3 (sl110, 120, 190)
        88  fn-Read-Next-Header value 34.      *> 18/04/17 for Invoice (sl020, 50, 140, 820)

    Only the handlers whose facade publishes the corresponding verb may use it,
    which is why :attr:`owning_handlers` is carried per entry rather than left
    to a reader to infer.

    These are NOT keys of reference: they order by NON-key columns, and the
    frozen schema declares zero secondary indexes on any of them. The compiled
    system nevertheless orders by them, so the absence of an index is the
    behaviour, and adding one is forbidden by rule R-3 and by Agent Action Plan
    section 0.8.4.
    """

    #: The `File-Function` code, from `dal/status.py`.
    file_function: FileFunction

    #: Which `Most-Cursor-Set` flag the verb drives.
    cursor_slot: CursorSlot

    #: The declared ordering, in declaration order.
    order_terms: tuple[OrderTerm, ...]

    #: Whether the bridge builds a WHERE predicate for this verb at all. ``False``
    #: for the two OTM sorted reads - see anomaly A8 below.
    predicate_present: bool

    #: The handler programs whose facade publishes the verb.
    owning_handlers: tuple[str, ...]

    #: `[common/<bridge>.cbl:L<n>]` of the paragraph that builds the clause.
    source_locator: str

    #: What is wrong with, or notable about, this verb as declared.
    note: str = ""


#  TABLE-OF-KEYNAMES  -  THE DECLARED METADATA, AS DATA  (RULE R-5)
# Transcribed from the `Table-Of-Keynames` block of all TWENTY in-scope bridges;
# every value appears in a frozen `.scb` at the cited line, and there is not one
# per-table branch in this module.
# DECLARATION ORDER IS HANDLER NUMBER, deliberately rather than tidily:
# `acas000` keys 1-4, then acas005 to acas029, then acasirsub1, 3, 4, 5. Rule
# R-6 forbids an ordering a run could vary, so `list(TABLE_OF_KEYNAMES)` is
# reproducible; it is NOT alphabetical, which would divorce it from the handler
# sequence traceability maps. THE COUNT: eighteen bridges declare `occurs 1` and
# two declare `occurs 2` [common/slinvoiceMT.scb:L305],
# [common/plinvoiceMT.scb:L306], giving 18 + 4 = 22 keys across exactly 22
# tables. `slpostingMT` DOES declare one [common/slpostingMT.scb:L213-L219].
TABLE_OF_KEYNAMES: Final[Mapping[str, tuple[KeyOfReference, ...]]] = (
    MappingProxyType(
        {
            # -- acas000 key 1 -> systemMT ------------------------------------
            "SYSTEM-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="SYSTEM-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="SYSTEM-REC",
                    column_name="SYSTEM-REC-KEY",
                    source_locator="[common/systemMT.scb:L271-L273]",
                ),
            ),
            # -- acas000 key 2 -> dfltMT --------------------------------------
            # The literal is written 25 characters wide, not 30, and COBOL pads
            # the rest [common/dfltMT.scb:L259].
            "SYSDEFLT-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="DEF-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="SYSDEFLT-REC",
                    column_name="DEF-REC-KEY",
                    source_locator="[common/dfltMT.scb:L259-L261]",
                ),
            ),
            # -- acas000 key 3 -> finalMT -------------------------------------
            "SYSFINAL-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="FINAL-ACC-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="SYSFINAL-REC",
                    column_name="FINAL-ACC-REC-KEY",
                    source_locator="[common/finalMT.scb:L257-L259]",
                ),
            ),
            # -- acas000 key 4 -> sys4MT --------------------------------------
            "SYSTOT-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="LEDGER-TOTALS-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="SYSTOT-REC",
                    column_name="LEDGER-TOTALS-REC-KEY",
                    source_locator="[common/sys4MT.scb:L259-L261]",
                ),
            ),
            # -- acas005 -> nominalMT -----------------------------------------
            "GLLEDGER-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="LEDGER-KEY",
                    offset_length="00010008",
                    kor_type="STR",
                    table_name="GLLEDGER-REC",
                    column_name="LEDGER-KEY",
                    source_locator="[common/nominalMT.scb:L245-L247]",
                ),
            ),
            # -- acas006 -> glpostingMT ---------------------------------------
            # THE ONE TABLE WHERE THE KEY OF REFERENCE IS NOT THE PRIMARY KEY.
            # `POST-KEY` here, `POST-RRN` in the schema. The maintainer flags it:
            # `*>  WARNING POST-KEY MAY WELL NEED CHANGING TO POST-RRN & RDB made
            # to index fld.` [common/glpostingMT.scb:L229]. The bridge orders by
            # THIS column [common/glpostingMT.cbl:L466-L470, :L736-L740], so this
            # module does too - see the module docstring.
            "GLPOSTING-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="POST-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="GLPOSTING-REC",
                    column_name="POST-KEY",
                    source_locator="[common/glpostingMT.scb:L232-L234]",
                ),
            ),
            # -- acas007 -> glbatchMT -----------------------------------------
            "GLBATCH-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="BATCH-KEY",
                    offset_length="00010006",
                    kor_type="STR",
                    table_name="GLBATCH-REC",
                    column_name="BATCH-KEY",
                    source_locator="[common/glbatchMT.scb:L232-L234]",
                ),
            ),
            # -- acas008 -> slpostingMT ---------------------------------------
            # The ONLY key declared `"BNT"` rather than `"STR"`, the bridge's own
            # comment being `*> key is bigint` [common/slpostingMT.scb:L216].
            # Carried, never branched on - anomaly A4.
            "PSIRSPOST-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="IRS-POST-KEY",
                    offset_length="00010008",
                    kor_type="BNT",
                    table_name="PSIRSPOST-REC",
                    column_name="IRS-POST-KEY",
                    source_locator="[common/slpostingMT.scb:L214-L216]",
                ),
            ),
            # -- acas012 -> salesMT -------------------------------------------
            "SALEDGER-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="SALES-KEY",
                    offset_length="00010007",
                    kor_type="STR",
                    table_name="SALEDGER-REC",
                    column_name="SALES-KEY",
                    source_locator="[common/salesMT.scb:L229-L231]",
                ),
            ),
            # -- acas013 -> valueMT -------------------------------------------
            "VALUEANAL-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="VA-CODE",
                    offset_length="00010003",
                    kor_type="STR",
                    table_name="VALUEANAL-REC",
                    column_name="VA-CODE",
                    source_locator="[common/valueMT.scb:L238-L240]",
                ),
            ),
            # -- acas015 -> analMT --------------------------------------------
            "ANALYSIS-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="PA-CODE",
                    offset_length="00010003",
                    kor_type="STR",
                    table_name="ANALYSIS-REC",
                    column_name="PA-CODE",
                    source_locator="[common/analMT.scb:L232-L234]",
                ),
            ),
            # -- acas016 -> slinvoiceMT, key 1 of 2 ---------------------------
            # `occurs 2` [common/slinvoiceMT.scb:L305]. Key 1 is annotated
            # `*> In SAINVOICE-REC` and key 2 `*> In SAINV-LINES-REC`, so the key
            # NUMBER selects the table as well as the column.
            "SAINVOICE-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="SINVOICE-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="SAINVOICE-REC",
                    column_name="SINVOICE-KEY",
                    source_locator="[common/slinvoiceMT.scb:L297-L299]",
                ),
            ),
            # -- acas016 -> slinvoiceMT, key 2 of 2 ---------------------------
            # Reached by `set KOR-x1 to 2`, annotated `*> 2 = Lines`
            # [common/slinvoiceMT.cbl:L2731], and driven by the second cursor
            # flag, hence `CursorSlot.SECONDARY`. The literal is written 11
            # characters wide [common/slinvoiceMT.scb:L301]; COBOL pads it.
            "SAINV-LINES-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="IL-LINE-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="SAINV-LINES-REC",
                    column_name="IL-LINE-KEY",
                    source_locator="[common/slinvoiceMT.scb:L301-L303]",
                    cursor_slot=CursorSlot.SECONDARY,
                ),
            ),
            # -- acas019 -> otm3MT --------------------------------------------
            "SAITM3-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="OI3-KEY",
                    offset_length="00010015",
                    kor_type="STR",
                    table_name="SAITM3-REC",
                    column_name="OI3-KEY",
                    source_locator="[common/otm3MT.scb:L249-L251]",
                ),
            ),
            # -- acas022 -> purchMT -------------------------------------------
            "PULEDGER-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="PURCH-KEY",
                    offset_length="00010007",
                    kor_type="STR",
                    table_name="PULEDGER-REC",
                    column_name="PURCH-KEY",
                    source_locator="[common/purchMT.scb:L228-L230]",
                ),
            ),
            # -- acas026 -> plinvoiceMT, key 1 of 2 ---------------------------
            "PUINVOICE-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="PINVOICE-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="PUINVOICE-REC",
                    column_name="PINVOICE-KEY",
                    source_locator="[common/plinvoiceMT.scb:L298-L300]",
                ),
            ),
            # -- acas026 -> plinvoiceMT, key 2 of 2 ---------------------------
            "PUINV-LINES-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="IL-LINE-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="PUINV-LINES-REC",
                    column_name="IL-LINE-KEY",
                    source_locator="[common/plinvoiceMT.scb:L302-L304]",
                    cursor_slot=CursorSlot.SECONDARY,
                ),
            ),
            # -- acas029 -> otm5MT --------------------------------------------
            "PUITM5-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="OI5-KEY",
                    offset_length="00010015",
                    kor_type="STR",
                    table_name="PUITM5-REC",
                    column_name="OI5-KEY",
                    source_locator="[common/otm5MT.scb:L251-L253]",
                ),
            ),
            # -- acasirsub1 -> irsnominalMT -----------------------------------
            "IRSNL-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="KEY-1",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="IRSNL-REC",
                    column_name="KEY-1",
                    source_locator="[common/irsnominalMT.scb:L142-L144]",
                ),
            ),
            # -- acasirsub3 -> irsdfltMT --------------------------------------
            "IRSDFLT-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="DEF-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="IRSDFLT-REC",
                    column_name="DEF-REC-KEY",
                    source_locator="[common/irsdfltMT.scb:L267-L269]",
                ),
            ),
            # -- acasirsub4 -> irspostingMT -----------------------------------
            "IRSPOSTING-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="KEY-4",
                    offset_length="00010005",
                    kor_type="STR",
                    table_name="IRSPOSTING-REC",
                    column_name="KEY-4",
                    source_locator="[common/irspostingMT.scb:L124-L126]",
                ),
            ),
            # -- acasirsub5 -> irsfinalMT -------------------------------------
            "IRSFINAL-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="IRS-FINAL-ACC-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="IRSFINAL-REC",
                    column_name="IRS-FINAL-ACC-REC-KEY",
                    source_locator="[common/irsfinalMT.scb:L115-L117]",
                ),
            ),
        }
    )
)


#  PRIMARY KEYS  -  RECORDED SO THE ONE DIVERGENCE IS VISIBLE
# Read from the frozen `mysql/ACASDB.sql`, whose twenty-two in-scope tables each
# declare a SINGLE-COLUMN primary key and ZERO secondary indexes. Held here for
# two reasons and used for neither ordering nor positioning:
#  1. It makes the `GLPOSTING-REC` divergence checkable rather than asserted.
#     For twenty-one tables this map agrees with the key of reference; for that
#     one it does not, and an anomaly-locking test can compare the two maps and
#     fail if a future edit "tidies" the ordering onto the primary key.
#  2. It documents that there IS no alternative ordering available - with one
#     key column and no secondary index, `ORDER BY <key of reference>` is both
#     sufficient and the only thing the compiled oracle can corroborate.
# Declared in the same handler order as `TABLE_OF_KEYNAMES` so the two zip.
TABLE_PRIMARY_KEYS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "SYSTEM-REC": "SYSTEM-REC-KEY",
        "SYSDEFLT-REC": "DEF-REC-KEY",
        "SYSFINAL-REC": "FINAL-ACC-REC-KEY",
        "SYSTOT-REC": "LEDGER-TOTALS-REC-KEY",
        "GLLEDGER-REC": "LEDGER-KEY",
        # The divergence. Key of reference `POST-KEY`, primary key `POST-RRN`.
        # [common/glpostingMT.scb:L229]
        "GLPOSTING-REC": "POST-RRN",
        "GLBATCH-REC": "BATCH-KEY",
        "PSIRSPOST-REC": "IRS-POST-KEY",
        "SALEDGER-REC": "SALES-KEY",
        "VALUEANAL-REC": "VA-CODE",
        "ANALYSIS-REC": "PA-CODE",
        "SAINVOICE-REC": "SINVOICE-KEY",
        "SAINV-LINES-REC": "IL-LINE-KEY",
        "SAITM3-REC": "OI3-KEY",
        "PULEDGER-REC": "PURCH-KEY",
        "PUINVOICE-REC": "PINVOICE-KEY",
        "PUINV-LINES-REC": "IL-LINE-KEY",
        "PUITM5-REC": "OI5-KEY",
        "IRSNL-REC": "KEY-1",
        "IRSDFLT-REC": "DEF-REC-KEY",
        "IRSPOSTING-REC": "KEY-4",
        "IRSFINAL-REC": "IRS-FINAL-ACC-REC-KEY",
    }
)


#  SELF-POSITIONING  -  ANOMALIES A1 AND A9, AS DATA
# One entry per bridge, transcribed from its `ba040-Process-Read-Next`. The
# relation and low key are what that paragraph hard-codes for the
# `Cursor-Not-Active` branch; see :class:`SequentialReadStart` for why both are
# anomalies rather than settings. The tally, so the split is on the record: `>`
# in nine bridges - systemMT, dfltMT, finalMT, sys4MT, nominalMT, analMT,
# irsnominalMT, irsdfltMT, irsfinalMT - and `>=` in eleven - glpostingMT,
# glbatchMT, slpostingMT, salesMT, valueMT, slinvoiceMT, otm3MT, purchMT,
# plinvoiceMT, otm5MT, irspostingMT.
# THE TWO LINES TABLES ARE DELIBERATELY ABSENT (rule R-5 records omissions as
# omissions): they have no `ba040`, being reached through their header bridge's
# SECOND slot with `set KOR-x1 to 2` [common/slinvoiceMT.cbl:L2731].
SEQUENTIAL_READ_START: Final[Mapping[str, SequentialReadStart]] = MappingProxyType(
    {
        "SYSTEM-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/systemMT.cbl:L669]",
            low_key_locator="[common/systemMT.cbl:L670]",
            # Three zeros for a one-byte key, and written UNQUOTED here where
            # every other bridge quotes it. Both differences are transport-level
            # only, because this module binds the value as a parameter.
            note="low key is 3 characters for a 1-byte key; emitted unquoted",
        ),
        "SYSDEFLT-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/dfltMT.cbl:L475]",
            low_key_locator="[common/dfltMT.cbl:L476]",
            note="low key is 3 characters for a 1-byte key",
        ),
        "SYSFINAL-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/finalMT.cbl:L476]",
            low_key_locator="[common/finalMT.cbl:L477]",
            note="low key is 3 characters for a 1-byte key",
        ),
        "SYSTOT-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/sys4MT.cbl:L502]",
            low_key_locator="[common/sys4MT.cbl:L503]",
            note="low key is 3 characters for a 1-byte key",
        ),
        "GLLEDGER-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="00000000",
            relation_locator="[common/nominalMT.cbl:L466]",
            low_key_locator="[common/nominalMT.cbl:L467]",
            note="26/12/16 NOT '='",
        ),
        "GLPOSTING-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000000",
            relation_locator="[common/glpostingMT.cbl:L464]",
            low_key_locator="[common/glpostingMT.cbl:L465]",
            note="nom uses >  ??",
        ),
        "GLBATCH-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="000000",
            relation_locator="[common/glbatchMT.cbl:L472]",
            low_key_locator="[common/glbatchMT.cbl:L473]",
            note="nom uses >  ??",
        ),
        "PSIRSPOST-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000000",
            relation_locator="[common/slpostingMT.cbl:L443]",
            low_key_locator="[common/slpostingMT.cbl:L444]",
            note="low key is 10 characters for the 8-byte IRS-POST-KEY",
        ),
        "SALEDGER-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000",
            relation_locator="[common/salesMT.cbl:L490]",
            low_key_locator="[common/salesMT.cbl:L491]",
        ),
        "VALUEANAL-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="000",
            relation_locator="[common/valueMT.cbl:L476]",
            low_key_locator="[common/valueMT.cbl:L477]",
        ),
        "ANALYSIS-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/analMT.cbl:L471]",
            low_key_locator="[common/analMT.cbl:L472]",
            # analMT and valueMT hold identically shaped 3-byte code keys and
            # disagree on the relation. Reproduced, not reconciled.
            note="uses > where valueMT, with the same 3-byte key shape, uses >=",
        ),
        "SAINVOICE-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000000",
            relation_locator="[common/slinvoiceMT.cbl:L646]",
            low_key_locator="[common/slinvoiceMT.cbl:L647]",
        ),
        "SAITM3-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="000000000000000",
            relation_locator="[common/otm3MT.cbl:L504]",
            low_key_locator="[common/otm3MT.cbl:L505]",
        ),
        "PULEDGER-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000",
            relation_locator="[common/purchMT.cbl:L521]",
            low_key_locator="[common/purchMT.cbl:L522]",
        ),
        "PUINVOICE-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000000",
            relation_locator="[common/plinvoiceMT.cbl:L645]",
            low_key_locator="[common/plinvoiceMT.cbl:L646]",
        ),
        "PUITM5-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="000000000000000",
            relation_locator="[common/otm5MT.cbl:L507]",
            low_key_locator="[common/otm5MT.cbl:L508]",
        ),
        "IRSNL-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="0000000000",
            relation_locator="[common/irsnominalMT.cbl:L409]",
            low_key_locator="[common/irsnominalMT.cbl:L410]",
            note="26/12/16 NOT '='",
        ),
        "IRSDFLT-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/irsdfltMT.cbl:L486]",
            low_key_locator="[common/irsdfltMT.cbl:L487]",
            # Same table shape as SYSDEFLT-REC and the SAME relation, but note
            # that its GL twin dfltMT also uses `>`; the pair agree here.
            note="low key is 3 characters for a 1-byte key",
        ),
        "IRSPOSTING-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="00000",
            relation_locator="[common/irspostingMT.cbl:L360]",
            low_key_locator="[common/irspostingMT.cbl:L361]",
            note="nom uses >",
        ),
        "IRSFINAL-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/irsfinalMT.cbl:L338]",
            low_key_locator="[common/irsfinalMT.cbl:L339]",
            note="low key is 3 characters for a 1-byte key",
        ),
    }
)


#  HANDLER-LEVEL VERB GUARDS
# Some tables cannot be positioned at all, and the refusal lives in the HANDLER
# rather than the bridge - which is why the bridge still declares perfectly good
# key metadata for them. `acas008` rejects four verbs unconditionally at entry,
# before any key is consulted, its `evaluate` listing `when 4` read-indexed,
# `when 7` re-write, `when 9` start and `when 8` delete into one body that moves
# 988 to `WE-Error` and 99 to `fs-reply` [common/acas008.cbl:L299-L307]. The
# underlying store is sequential, so `START` and `READ-INDEXED` return
# `(99, 988)` and never touch the table. `fn-read-next` is NOT in the list, so
# sequential reading of `PSIRSPOST-REC` works normally. Only the two verbs this
# module implements are listed; rewrite and delete belong to the handler modules
# that own those verbs.
HANDLER_REJECTED_FUNCTIONS: Final[
    Mapping[str, Mapping[FileFunction, tuple[FsReply, WeError, str]]]
] = MappingProxyType(
    {
        # `acas008` guards FOUR verbs in one body, in the order its `evaluate`
        # lists them - `when 4` read-indexed, `when 7` re-write, `when 9` start,
        # `when 8` delete - moving 988 to `WE-Error` and 99 to `fs-reply`
        # [common/acas008.cbl:L299-L307]; the transcription is above.
        # ANOMALY A15 - REPRODUCED, NOT FIXED. The facade nonetheless PUBLISHES
        # `SPL-Posting-Rewrite` over this handler, so a caller can invoke a verb
        # that CANNOT succeed - it fails at the handler's first act, before any
        # statement exists. Re-write and delete are recorded even though this
        # module implements neither, because the guard is the handler's property
        # rather than any one verb's (rule R-5). `read_next` is deliberately
        # ABSENT from it, which is why the sequential walk of this table is live
        # and why ambiguity Q2 is reachable.
        "PSIRSPOST-REC": MappingProxyType(
            {
                FileFunction.READ_INDEXED: (
                    FsReply.ERROR,
                    WeError.ACTION_TYPE_WRONG_FOR_SEQ,
                    "[common/acas008.cbl:L300]",
                ),
                FileFunction.RE_WRITE: (
                    FsReply.ERROR,
                    WeError.ACTION_TYPE_WRONG_FOR_SEQ,
                    "[common/acas008.cbl:L301]",
                ),
                FileFunction.START: (
                    FsReply.ERROR,
                    WeError.ACTION_TYPE_WRONG_FOR_SEQ,
                    "[common/acas008.cbl:L302]",
                ),
                FileFunction.DELETE: (
                    FsReply.ERROR,
                    WeError.ACTION_TYPE_WRONG_FOR_SEQ,
                    "[common/acas008.cbl:L303]",
                ),
            }
        ),
    }
)


#  THE FOUR EXTRA READ VERBS  -  POSITIONING SUPPORT, AS DATA
# Keyed by table, then by `File-Function`. Only the handlers named in each entry
# may use the verb, because only their facade publishes it - `acas012`/`acas022`
# by-name, `acas019`/`acas029` by-batch and by-customer, `acas016`/`acas026`
# read-next-header.
# NONE of these order by a key of reference: they order by NON-key columns, and
# the frozen schema declares no index on any of them. That absence IS the
# compiled system's behaviour, and adding an index is forbidden twice over - by
# rule R-3 and by Agent Action Plan section 0.8.4.
# NOT ON THE POSTING PATH. Verbs 31/32/33 serve report programs the migration
# excludes [copybooks/wsfnctn.cob:L102-L104]. They are declared so the handler
# modules that publish them have the metadata and the anomaly below is recorded.
EXTRA_READ_ORDERS: Final[Mapping[str, Mapping[FileFunction, ExtraReadOrder]]] = (
    MappingProxyType(
        {
            # -- acas012 -> salesMT, fn 31 ------------------------------------
            # The only pair of extra verbs that actually works: the ordering
            # term is BACKTICK-quoted, so MySQL treats it as a column.
            "SALEDGER-REC": MappingProxyType(
                {
                    FileFunction.READ_BY_NAME: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_NAME,
                        cursor_slot=CursorSlot.SECONDARY,
                        order_terms=(
                            OrderTerm(
                                column_name="SALES-NAME",
                                direction="ASC",
                                quoting=OrderQuoting.IDENTIFIER,
                                source_locator="[common/salesMT.cbl:L1016-L1019]",
                            ),
                        ),
                        predicate_present=True,
                        owning_handlers=("acas012",),
                        source_locator="[common/salesMT.cbl:L995-L1022]",
                        note=(
                            "predicate is on SALES-KEY, ordering on the "
                            "unindexed SALES-NAME; the low key is emitted "
                            "unquoted here [common/salesMT.cbl:L1014]"
                        ),
                    ),
                }
            ),
            # -- acas022 -> purchMT, fn 31 -----------------------------------
            "PULEDGER-REC": MappingProxyType(
                {
                    FileFunction.READ_BY_NAME: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_NAME,
                        cursor_slot=CursorSlot.SECONDARY,
                        order_terms=(
                            OrderTerm(
                                column_name="PURCH-NAME",
                                direction="ASC",
                                quoting=OrderQuoting.IDENTIFIER,
                                source_locator="[common/purchMT.cbl:L1031-L1034]",
                            ),
                        ),
                        predicate_present=True,
                        owning_handlers=("acas022",),
                        source_locator="[common/purchMT.cbl:L1010-L1037]",
                        note=(
                            "predicate is on PURCH-KEY, ordering on the "
                            "unindexed PURCH-NAME"
                        ),
                    ),
                }
            ),
            # -- acas019 -> otm3MT, fn 32 and 33 --------------------------
            # ANOMALY A8 - REPRODUCED, NOT FIXED. Two independent defects:
            #  (a) The ordering terms are SINGLE-quoted
            #      [common/otm3MT.cbl:L1005-L1008], so in MySQL each is a string
            #      CONSTANT rather than an identifier and the clause orders
            #      nothing. Every term carries `OrderQuoting.STRING_CONSTANT`,
            #      which `OrderTerm.to_sql` renders single-quoted, because
            #      rendering it as an identifier would fix the defect.
            #  (b) `ws-Where` holds the ORDER BY text ALONE with no predicate
            #      while the statement still concatenates `" WHERE "`
            #      [common/otm3MT.cbl:L1022-L1026], so MySQL rejects the text
            #      and `(99, 911)` results. Hence `predicate_present=False`.
            "SAITM3-REC": MappingProxyType(
                {
                    FileFunction.READ_BY_BATCH: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_BATCH,
                        cursor_slot=CursorSlot.SECONDARY,
                        order_terms=(
                            OrderTerm(
                                column_name="OI3-INVOICE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1005]",
                            ),
                            OrderTerm(
                                column_name="OI3-DAT",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1005]",
                            ),
                            OrderTerm(
                                column_name="OI3-TYPE",
                                direction="DESC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1007]",
                            ),
                            OrderTerm(
                                column_name="OI3-BATCH-ITEM",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1008]",
                            ),
                            OrderTerm(
                                column_name="OI3-BATCH-NOS",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1008]",
                            ),
                        ),
                        predicate_present=False,
                        owning_handlers=("acas019",),
                        source_locator="[common/otm3MT.cbl:L997-L1012]",
                        note=(
                            "anomaly A8: single-quoted terms order nothing, and "
                            "WHERE carries no predicate, so the statement is a "
                            "syntax error returning (99, 911)"
                        ),
                    ),
                    FileFunction.READ_BY_CUST: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_CUST,
                        cursor_slot=CursorSlot.TERTIARY,
                        order_terms=(
                            OrderTerm(
                                column_name="OI3-CUSTOMER",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1160]",
                            ),
                            OrderTerm(
                                column_name="OI3-DAT",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1160]",
                            ),
                            OrderTerm(
                                column_name="OI3-INVOICE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1161]",
                            ),
                            OrderTerm(
                                column_name="OI3-TYPE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1161]",
                            ),
                        ),
                        predicate_present=False,
                        owning_handlers=("acas019",),
                        source_locator="[common/otm3MT.cbl:L1153-L1166]",
                        note="anomaly A8, as for READ_BY_BATCH above",
                    ),
                }
            ),
            # -- acas029 -> otm5MT, fn 32 and 33 -----------------------------
            "PUITM5-REC": MappingProxyType(
                {
                    FileFunction.READ_BY_BATCH: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_BATCH,
                        cursor_slot=CursorSlot.SECONDARY,
                        order_terms=(
                            OrderTerm(
                                column_name="OI5-INVOICE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1008]",
                            ),
                            OrderTerm(
                                column_name="OI5-DAT",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1008]",
                            ),
                            OrderTerm(
                                column_name="OI5-TYPE",
                                direction="DESC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1010]",
                            ),
                            OrderTerm(
                                column_name="OI5-BATCH-ITEM",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1011]",
                            ),
                            OrderTerm(
                                column_name="OI5-BATCH-NOS",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1011]",
                            ),
                        ),
                        predicate_present=False,
                        owning_handlers=("acas029",),
                        source_locator="[common/otm5MT.cbl:L1000-L1015]",
                        note="anomaly A8, as for SAITM3-REC",
                    ),
                    FileFunction.READ_BY_CUST: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_CUST,
                        cursor_slot=CursorSlot.TERTIARY,
                        order_terms=(
                            OrderTerm(
                                column_name="OI5-SUPPLIER",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1166]",
                            ),
                            OrderTerm(
                                column_name="OI5-DAT",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1166]",
                            ),
                            OrderTerm(
                                column_name="OI5-INVOICE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1167]",
                            ),
                            OrderTerm(
                                column_name="OI5-TYPE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1167]",
                            ),
                        ),
                        predicate_present=False,
                        owning_handlers=("acas029",),
                        source_locator="[common/otm5MT.cbl:L1159-L1172]",
                        note="anomaly A8, as for SAITM3-REC",
                    ),
                }
            ),
            # -- acas016 -> slinvoiceMT, fn 34 -------------------------------
            # `fn-Read-Next-Header` (34) shares ONE `evaluate` body with
            # `fn-read-next` (3): the two `when` arms are consecutive and fall
            # into the same `go to ba040-Process-Read-Next`
            # [common/slinvoiceMT.cbl, the File-Function evaluate]. So despite
            # the `*> Read-Next-Header - Special` comment the bridge treats 34
            # EXACTLY as 3 - same cursor slot, same ordering on the key of
            # reference, same low key. Any header-versus-lines distinction lives
            # in the handler `acas016`, not here.
            # It therefore declares NO ordering of its own, and `order_terms` is
            # empty rather than invented: an empty tuple means "orders by the key
            # of reference, as the primary sequential read does".
            "SAINVOICE-REC": MappingProxyType(
                {
                    FileFunction.READ_NEXT_HEADER: ExtraReadOrder(
                        file_function=FileFunction.READ_NEXT_HEADER,
                        cursor_slot=CursorSlot.PRIMARY,
                        order_terms=(),
                        predicate_present=True,
                        owning_handlers=("acas016",),
                        source_locator="[common/slinvoiceMT.cbl:L624]",
                        note=(
                            "shares the fn-read-next body, so it is "
                            "behaviourally identical to function 3"
                        ),
                    ),
                }
            ),
            # -- acas026 -> plinvoiceMT, fn 34 -------------------------------
            "PUINVOICE-REC": MappingProxyType(
                {
                    FileFunction.READ_NEXT_HEADER: ExtraReadOrder(
                        file_function=FileFunction.READ_NEXT_HEADER,
                        cursor_slot=CursorSlot.PRIMARY,
                        order_terms=(),
                        predicate_present=True,
                        owning_handlers=("acas026",),
                        source_locator="[common/plinvoiceMT.cbl:L623]",
                        note=(
                            "shares the fn-read-next body, so it is "
                            "behaviourally identical to function 3"
                        ),
                    ),
                }
            ),
        }
    )
)


#  THE CURSOR  -  01 DAL-Data, REPRODUCED

#: `05  Most-Cursor-Set pic 9    value zero.` and `88  Cursor-Not-Active value
#: zero.` [common/glpostingMT.scb:L249-L250].
_CURSOR_NOT_ACTIVE: Final[int] = 0

#: `88  Cursor-Active        value 1.` [common/glpostingMT.scb:L251].
_CURSOR_ACTIVE: Final[int] = 1


@dataclass(slots=True)
class CursorState:
    """One cursor - one ``(table, slot)`` pair - reproducing ``01 DAL-Data``.

    Mirrors [common/glpostingMT.scb:L247-L251]::

        01  DAL-Data.
            05  MOST-Relation   pic xxx.                  *> valid are >=, <=, <, >, =
            05  Most-Cursor-Set pic 9    value zero.
                88  Cursor-Not-Active    value zero.
                88  Cursor-Active        value 1.

    Mutable, because the COBOL block is working storage the bridge writes as it
    positions. The two ``88``-level condition names become the predicates
    :meth:`cursor_not_active` and :meth:`cursor_active`, per Agent Action Plan
    section 0.1.2's transformation rule 12, verbatim: "``88``-level condition
    name -> Predicate function over the record".

    ``most_cursor_set`` starts at zero exactly as ``value zero`` declares, so a
    fresh cursor is not active and the first ``READ NEXT`` self-positions.

    The state BEYOND the COBOL block is what the compiled bridge keeps in the
    MySQL result set rather than in working storage: the STORED RESULT itself.
    ``mysql_store_result`` materialises every qualifying row at positioning time
    and ``MySQL_fetch_record`` then walks it one record per call
    [common/glpostingMT.cbl:L536-L554]. That snapshot is reproduced here by
    :meth:`store_result` and :meth:`fetch_record`, with :attr:`positioned_key`
    carrying the key last delivered - the value ``WS-File-Key`` receives
    [common/glpostingMT.cbl:L586] - for diagnostics. See AMBIGUITY Q1 in the
    module docstring for the measurement that settled snapshot over
    re-positioning.
    """

    #: The table this cursor walks.
    table_name: str

    #: Which `Most-Cursor-Set` flag of `01 DAL-Data` this is.
    slot: CursorSlot

    #: `05  MOST-Relation   pic xxx.` - the relation the last START used, or
    #: ``None`` before any START, matching the field's uninitialised spaces.
    most_relation: MostRelation | None = None

    #: `05  Most-Cursor-Set pic 9    value zero.` - the raw flag. Kept as the
    #: integer the COBOL holds rather than a bool so that
    #: `Cursor-Not-Active`/`Cursor-Active` remain tests on a `pic 9` value.
    most_cursor_set: int = _CURSOR_NOT_ACTIVE

    #: The key value the cursor is positioned at. Never a binary
    #: floating-point type (rule R-2): a key compared inexactly positions on the
    #: wrong row, silently.
    positioned_key: object | None = None

    #: The key of reference in use, so a caller can see WHICH key positioned the
    #: cursor and not merely that it is active.
    key_of_reference: KeyOfReference | None = None

    #: The stored result - every row ``mysql_store_result`` materialised at
    #: positioning time [copybooks/mysql-procedures.cpy:L187-L192], in the order
    #: the single ``ORDER BY`` term returned them. Empty before any positioning.
    stored_rows: tuple[Mapping[str, object], ...] = ()

    #: How many records of :attr:`stored_rows` ``MySQL_fetch_record`` has already
    #: handed back. The bridge holds this inside the result set; here it is
    #: explicit so that "START positions but does not fetch" is expressible as
    #: "the snapshot exists and nothing has been fetched from it".
    fetched_count: int = 0

    @property
    def count_rows(self) -> int:
        """``WS-MYSQL-Count-Rows`` - the FULL row count of the stored result.

        The count ``mysql_num_rows`` reports, which the bridge tests separately
        from the fetch and branches on differently at each stage
        [common/glpostingMT.cbl:L499, :L767]. It is the count of the WHOLE
        qualifying result and does not shrink as records are fetched.

        >>> CursorState("GLPOSTING-REC", CursorSlot.PRIMARY).count_rows
        0
        """
        return len(self.stored_rows)

    @property
    def position_inclusive(self) -> bool:
        """``True`` while the stored result's first record is still unfetched.

        This is how "START positions but does not fetch" is honoured. The bridge
        comments the design change itself [common/glpostingMT.cbl:L795-L800]::

            *> Here we need FETCH as SELECT has been issued & cursor active
             *>    go to ba041-Reread.
            *> Changed to do start then read next
            *>   As per irsub4 operations

        so a ``START`` stores the result and consumes nothing from it, and the
        first following ``READ NEXT`` returns the row the ``START`` found. Derived
        from the snapshot rather than tracked separately, so there is one source
        of truth for the position.

        >>> CursorState("GLPOSTING-REC", CursorSlot.PRIMARY).position_inclusive
        False
        """
        return bool(self.stored_rows) and self.fetched_count == 0

    def store_result(self, rows: Iterable[Mapping[str, object]]) -> int:
        """Reproduce ``Mysql-1220-Store-Result`` then ``MySQL_num_rows``.

        ``mysql_store_result`` materialises the ENTIRE qualifying result on the
        client [copybooks/mysql-procedures.cpy:L187-L192] and ``mysql_num_rows``
        then reports its size. Storing a fresh result REPLACES any previous one,
        exactly as re-issuing a statement does in the bridge.

        Args:
            rows: Every qualifying row, in the order the statement returned them.

        Returns:
            The full row count - the value ``WS-MYSQL-Count-Rows`` receives.
        """
        self.stored_rows = tuple(rows)
        self.fetched_count = 0
        return len(self.stored_rows)

    def fetch_record(self) -> Mapping[str, object] | None:
        """Reproduce ``MySQL_fetch_record`` [common/glpostingMT.cbl:L536-L554].

        Hands back the next record of the stored result and advances. Issues no
        statement: the bridge's ``ba041-Reread`` walks the snapshot the earlier
        positioning already materialised.

        Returns:
            The next record, or ``None`` once the snapshot is exhausted - the
            ``return-code = -1`` the bridge tests for
            [common/glpostingMT.cbl:L556-L557].
        """
        if self.fetched_count >= len(self.stored_rows):
            return None
        row = self.stored_rows[self.fetched_count]
        self.fetched_count += 1
        return row

    def free_result(self) -> None:
        """Reproduce ``CALL "MySQL_free_result"`` [common/glpostingMT.cbl:L1032].

        Releases the stored result. Called ONLY from :meth:`free`, because
        ``ba998-Free`` is the only paragraph that frees it - the end-of-file sites
        merely ``set Cursor-Not-Active to true`` and leave the result allocated.
        That leak is the frozen behaviour and is reproduced: the next
        self-positioning ``READ NEXT`` simply overwrites the snapshot.
        """
        self.stored_rows = ()
        self.fetched_count = 0

    def cursor_not_active(self) -> bool:
        """`88  Cursor-Not-Active    value zero.` [common/glpostingMT.scb:L250].

        >>> CursorState("GLPOSTING-REC", CursorSlot.PRIMARY).cursor_not_active()
        True
        """
        return self.most_cursor_set == _CURSOR_NOT_ACTIVE

    def cursor_active(self) -> bool:
        """`88  Cursor-Active        value 1.` [common/glpostingMT.scb:L251].

        >>> CursorState("GLPOSTING-REC", CursorSlot.PRIMARY).cursor_active()
        False
        """
        return self.most_cursor_set == _CURSOR_ACTIVE

    def set_cursor_active(self) -> None:
        """Reproduce ``set Cursor-Active to true`` [common/glpostingMT.cbl:L768]."""
        self.most_cursor_set = _CURSOR_ACTIVE

    def set_cursor_not_active(self) -> None:
        """Reproduce ``set Cursor-Not-Active to true``.

        Written at four sites, all of which this module reaches: end of file
        [common/glpostingMT.cbl:L559], the zero-row re-read
        [common/glpostingMT.cbl:L576], the belt-and-braces reply test
        [common/glpostingMT.cbl:L581], and the result-freeing paragraph
        [common/glpostingMT.cbl:L1033].
        """
        self.most_cursor_set = _CURSOR_NOT_ACTIVE

    def free(self) -> None:
        """Reproduce ``ba998-Free`` [common/glpostingMT.cbl:L1023-L1033].

        The paragraph releases the stored result and then, as its last act, sets
        the cursor inactive::

            ba998-Free.
                ...
                CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call
                set      Cursor-Not-Active to true.

        The stored result is released by :meth:`free_result` - this is the ONE
        paragraph that frees it - and the flag and the position go with it.
        Leaving the snapshot behind would let a later ``READ NEXT`` resume a
        cursor the COBOL had discarded.
        """
        self.free_result()
        self.set_cursor_not_active()
        self.positioned_key = None

    def position_at(self, key_value: object) -> None:
        """Record the key just positioned on and mark the cursor active.

        Whether the next ``READ NEXT`` returns the row AT this key or the one
        after it is NOT recorded here: it follows from how much of the stored
        result has been fetched, which :attr:`position_inclusive` reports.

        Args:
            key_value: The key of the row positioned on, exactly as the driver
                returned it - not re-parsed, not re-formatted.
        """
        self.positioned_key = key_value
        self.set_cursor_active()


class CursorStateTable:
    """The set of live cursors, one per ``(table, slot)``.

    Explicit and resettable by design. In COBOL each bridge is a separate
    program with its own ``01 DAL-Data`` in working storage, so cursors are
    naturally isolated per table; here they share a process, and the
    determinism requirement needs two runs in ONE process to be independent.
    :meth:`reset` is what makes that true.

    Not thread-safe, and deliberately so: rule R-3 requires strictly sequential
    execution matching the single-threaded COBOL, so a lock here would imply a
    concurrency this migration does not have.
    """

    __slots__ = ("_states",)

    def __init__(self) -> None:
        """Create an empty set of cursors. No I/O, no clock, no entropy."""
        # A plain dict keyed by (table, slot). Insertion order is never relied
        # upon: `live_cursors()` sorts, and no iteration of this mapping reaches
        # SQL text (rule R-6).
        self._states: dict[tuple[str, CursorSlot], CursorState] = {}

    def state_for(
        self, table_name: str, slot: CursorSlot = CursorSlot.PRIMARY
    ) -> CursorState:
        """Return the cursor for a table and slot, creating it inactive.

        Creating on demand reproduces the COBOL's own initial condition: a
        bridge that has never positioned has ``Most-Cursor-Set`` at its declared
        ``value zero``, which is indistinguishable from a cursor that does not
        exist yet.

        Args:
            table_name: An in-scope table name.
            slot: Which read order's flag is wanted.

        Returns:
            The live cursor, created inactive on first request.

        Raises:
            KeyError: If the table declares no key of reference. Unreachable
                from COBOL, where each bridge is compiled for its own table, so
                this can only be a Python caller's error.
        """
        if table_name not in TABLE_OF_KEYNAMES:
            raise KeyError(
                f"{table_name!r} declares no Table-Of-Keynames entry; the "
                f"in-scope tables are {', '.join(TABLE_OF_KEYNAMES)}"
            )
        key = (table_name, slot)
        state = self._states.get(key)
        if state is None:
            state = CursorState(table_name=table_name, slot=slot)
            self._states[key] = state
        return state

    def live_cursors(self) -> tuple[CursorState, ...]:
        """Return every cursor created so far, in a fixed order.

        Sorted by table name then slot so the result is reproducible across
        processes (rule R-6). Diagnostic only - nothing here reaches SQL text.
        """
        return tuple(
            self._states[key]
            for key in sorted(self._states, key=lambda pair: (pair[0], int(pair[1])))
        )

    def reset(self, table_name: str | None = None) -> None:
        """Discard cursor state, so a following run starts clean.

        Args:
            table_name: Reset only this table's cursors when given; reset every
                cursor when ``None``.
        """
        if table_name is None:
            self._states.clear()
            return
        for key in [pair for pair in self._states if pair[0] == table_name]:
            del self._states[key]


#: The cursors the module-level verbs use when a caller passes none.
#:
#: One shared set is correct rather than convenient: the COBOL handlers are
#: singletons too - a `CALL "acas006"` reaches ONE loaded program with ONE
#: `01 DAL-Data`, so two callers positioning `GLPOSTING-REC` in the compiled
#: system share a cursor exactly as they do here. Callers wanting isolation pass
#: their own :class:`CursorStateTable`; :func:`reset` clears this one.
_DEFAULT_STATES: Final[CursorStateTable] = CursorStateTable()


#  THE OUTCOME  -  THE STATUS PAIR THE BRIDGE WOULD HAVE LEFT


@dataclass(frozen=True, slots=True)
class CursorOutcome:
    """What one positioning verb returned, and what it wrote.

    The COBOL handler communicates by WRITING into the caller's ``File-Access``
    linkage block, so this value object carries the pair it would have written
    plus the row, and :meth:`apply_to` performs the write. Returning it rather
    than mutating unconditionally keeps the verbs testable with no
    ``File-Access`` at all.

    :attr:`status_written` is the subtle one and it is not decoration - see
    anomaly A7 on :func:`start`. One reachable COBOL path writes NEITHER status
    field, so the caller's incoming values survive; a value object that always
    reported a pair would silently invent one.
    """

    #: The `FS-Reply` the bridge would leave. Meaningful only when
    #: :attr:`status_written` is ``True``; when it is ``False`` this echoes the
    #: pair that was already there.
    fs_reply: FsReply

    #: The `We-Error` the bridge would leave, as a plain ``int`` because the
    #: COBOL field is `pic 999` and end-of-file stores the literal 10 into it
    #: [common/glpostingMT.cbl:L557] rather than a named error code.
    we_error: int

    #: The row, column-name keyed, or ``None`` when the verb positioned nowhere.
    row: Mapping[str, object] | None

    #: The statement issued, with parameter placeholders intact. Held for the
    #: file-handler log the COBOL keeps in `WS-Log-Where`
    #: [common/glpostingMT.cbl:L744] and for the traceability evidence.
    statement: str

    #: The values bound to that statement. Bound, never interpolated.
    parameters: tuple[object, ...]

    #: Whether the bridge writes the status pair on this path at all. ``False``
    #: only on the no-rows START of anomaly A7.
    status_written: bool = True

    #: The internal SQLSTATE that DESCRIBES this outcome, for diagnostics only -
    #: anomaly A3. The frozen source defines five such codes
    #: [copybooks/mysql-procedures.cpy:L115-L119] and never implements them, so
    #: the returned pair above is the compiled system's, not one derived from
    #: this. Empty where no internal code applies.
    sql_state: str = ""

    #: The bridge's own `WS-File-Key` log tag for this path, verbatim. The
    #: paragraphs distinguish their exits by it - `"No Data"`
    #: [common/glpostingMT.cbl:L510], `"EOF"` [common/glpostingMT.cbl:L558],
    #: `"EOF2"` [common/glpostingMT.cbl:L574], `"EOF3"`
    #: [common/glpostingMT.cbl:L582] - which is the only way to tell three
    #: identical-looking `(10, 10)` outcomes apart. Carried because it is the
    #: compiled system's own discrimination, not one invented here.
    file_key: str = ""

    def is_ok(self) -> bool:
        """Whether the verb succeeded, i.e. left ``FS-Reply`` zero."""
        return self.fs_reply == FsReply.SUCCESS

    def is_end_of_file(self) -> bool:
        """Whether the verb reported end of file, ``FS-Reply`` 10."""
        return self.fs_reply == FsReply.END_OF_FILE

    def apply_to(self, file_access: FileAccess) -> None:
        """Write this outcome into the caller's ``File-Access`` block.

        Reproduces the handler's side of the linkage contract: the bridge stores
        ``FS-Reply``, ``We-Error``, ``SQL-State`` and the logging fields into the
        block the caller passed [common/glpostingMT.cbl:L588, :L744-L745].

        Honours :attr:`status_written`: on the anomaly A7 path the COBOL leaves
        both status fields untouched, so this method leaves them untouched too.
        The logging fields are still written on that path, because the COBOL
        writes them before the status test [common/glpostingMT.cbl:L744-L745].

        Args:
            file_access: The caller's block, mutated in place.
        """
        if self.status_written:
            file_access.fs_reply = int(self.fs_reply)
            file_access.we_error = self.we_error
        if self.sql_state:
            # `move WS-MYSQL-SqlState to SQL-State`
            # [copybooks/mysql-procedures.cpy:L123]. Diagnostic; see A3.
            file_access.logging_data.sql_state = self.sql_state
        if self.file_key:
            # `move "EOF" to WS-File-Key` and its siblings
            # [common/glpostingMT.cbl:L558, :L574, :L582].
            file_access.logging_data.ws_file_key = self.file_key
        # `move WS-Where (1:J) to WS-Log-Where.  *>  For test logging`
        # [common/glpostingMT.cbl:L744]
        file_access.logging_data.ws_log_where = self.statement


#  INTERNAL HELPERS

# WHY `WS-MYSQL-Count-Rows` IS NEVER TAKEN FROM THE DRIVER'S `rowcount`
#
# ALL THREE VERBS COUNT THE STORED RESULT, and they must, for two independent
# reasons - one from the frozen source, one measured on the pinned driver.
#
# 1. THE FROZEN SEQUENCE. Every statement-issuing path in the bridge performs
#    `MYSQL-1210-COMMAND` and then, IMMEDIATELY, `MYSQL-1220-STORE-RESULT` -
#    for the sequential read at [common/glpostingMT.cbl:L488-L489], for the
#    START at [:L762-L763] and, no differently, for the indexed read at
#    [:L628-L629]. `Mysql-1210-Command` does write `WS-Mysql-Count-Rows`, from
#    `MySQL_affected_rows` [copybooks/mysql-procedures.cpy:L178], but
#    `Mysql-1220-Store-Result` then OVERWRITES it from `MySQL_num_rows` over the
#    materialised result [:L187-L192]. So the value every `if
#    WS-MYSQL-Count-Rows` test reads is the size of the stored snapshot, and the
#    affected-rows reading - the one a DB-API `rowcount` corresponds to - has
#    already been discarded by the time any branch looks at it. An indexed read
#    is not an exception to this: `ba050` stores its result like everything else
#    and `ba998-Free` releases it [:L1023-L1033].
#
# 2. THE MEASUREMENT, which turns the point from tidiness into correctness. On
#    the pinned driver (`mysql-connector-python` 26.7.0, C extension, and the
#    UNBUFFERED cursor `connection.py` opens) `cursor.rowcount` is `0`
#    immediately after `execute` of a `SELECT` and becomes the true count only
#    AFTER the first fetch. An earlier revision of this module gated the fetch
#    on that value in `read_indexed` alone, and the consequence was not a
#    rounding error but a silent one: EVERY PRESENT ROW WAS REPORTED ABSENT,
#    with a status triple byte-identical to a genuine miss, and the server's row
#    was left unread on the connection - which then made the NEXT `read_next`
#    return the clean-looking end of file of anomaly A11, so a posting walk
#    would stop early and report success. Some drivers report `-1` for "not yet
#    known" and some `0`; the sentinel is unusable either way, because the honest
#    count only exists once the rows have been drained.
#
# The lesson encoded here: draining is not an optimisation to be avoided, it is
# what the frozen `mysql_store_result` DOES, and it is also what leaves the
# connection usable. Anything that re-introduces a `cursor.rowcount` test in
# front of a fetch re-introduces both defects.


def _column_names(cursor: DatabaseCursor) -> tuple[str, ...]:
    """Return the column names of the last statement, or an empty tuple.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        The names in the order the driver reports them, which for ``SELECT *`` is
        the declared column order of the frozen table.
    """
    description = cursor.description
    if not description:
        return ()
    return tuple(str(column[0]) for column in description)


def _fetch_one_row(cursor: DatabaseCursor) -> Mapping[str, object] | None:
    """Fetch at most ONE row and return it keyed by column name.

    Accepts either row shape a driver may hand back - a sequence, or a mapping
    when the driver was configured to produce one - because
    ``connection.py`` owns that choice and this module must not constrain it.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        The row keyed by column name, or ``None`` at end of result.
    """
    row = cursor.fetchone()
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row
    names = _column_names(cursor)
    if not names:
        # Without column metadata a name cannot be invented. Positional keys are
        # honest about that and still let a caller reach the values.
        return MappingProxyType({str(index): value for index, value in enumerate(row)})
    return MappingProxyType(dict(zip(names, row, strict=False)))


def _store_result(cursor: DatabaseCursor) -> tuple[Mapping[str, object], ...]:
    """Materialise the ENTIRE result, reproducing ``mysql_store_result``.

    ``Mysql-1220-Store-Result`` pulls every qualifying row to the client
    [copybooks/mysql-procedures.cpy:L187-L192] before ``MySQL_num_rows`` counts it
    and ``MySQL_fetch_record`` walks it. Rule R-3 does not bar this: it bars added
    validations, added fields, schema change and concurrency. AMBIGUITY Q1 in the
    module docstring records the measurement that requires it.

    Drains with repeated :func:`_fetch_one_row` rather than ``fetchall`` so that
    the :class:`DatabaseCursor` protocol needs no widening and any driver
    ``connection.py`` chooses will work.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        Every row, keyed by column name, in the order the statement returned them.
    """
    rows: list[Mapping[str, object]] = []
    while True:
        row = _fetch_one_row(cursor)
        if row is None:
            return tuple(rows)
        rows.append(row)


def _deliver_from_stored_result(
    state: CursorState,
    key: KeyOfReference,
    *,
    empty_tag: str,
    incoming_fs_reply: FsReply,
    incoming_we_error: int,
    file_access: FileAccess | None,
    statement: str = "",
    parameters: tuple[object, ...] = (),
) -> CursorOutcome:
    """Reproduce ``ba041-Reread`` [common/glpostingMT.cbl:L523-L589].

    The paragraph ``ba040`` falls into, and the one a ``READ NEXT`` on an already
    active cursor enters directly. It issues NO statement: it advances the stored
    result and applies the two tests that follow the fetch.

    Args:
        state: The cursor whose stored result is being walked.
        key: The key of reference in force, whose column names the delivered key.
        empty_tag: The ``WS-File-Key`` tag for exhaustion - ``"EOF"`` when entered
            directly [common/glpostingMT.cbl:L558], ``"No Data"`` when reached
            through ``ba040``'s self-positioning [:L510].
        incoming_fs_reply: The caller's ``FS-Reply`` on entry, which anomaly A10
            tests AFTER the fetch.
        incoming_we_error: The caller's ``We-Error`` on entry, preserved unchanged
            on the A10 path where no status is written.
        file_access: Applied to before returning when given.
        statement: The statement that materialised the snapshot, for the outcome.
            Empty when this paragraph was entered directly, as the bridge issues
            none there.
        parameters: That statement's bound parameters, for the same reason.

    Returns:
        The outcome - a delivered row, exhaustion, or an A10 discard.
    """
    row = state.fetch_record()

    if row is None:
        # Exhausted. `if return-code = -1  move 10 to fs-Reply WE-Error`
        # [common/glpostingMT.cbl:L556-L557], where ONE statement writes BOTH
        # fields, so the pair is `(10, 10)` and `We-Error` is NOT left at zero.
        # The cursor is deactivated by a bare `set Cursor-Not-Active to true`
        # [:L559] and NOT by `ba998-Free`, so the stored result stays allocated -
        # the leak the frozen source has, reproduced.
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            file_key=empty_tag,
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    if incoming_fs_reply == FsReply.END_OF_FILE:
        # ANOMALY A10: the row was fetched and is now THROWN AWAY, because the
        # caller's `FS-Reply` still holds 10 from a previous end of file
        # [common/glpostingMT.cbl:L580-L583]. No status is written - the stale
        # pair simply persists - and the cursor is deactivated, so the next call
        # self-positions and discards a row all over again. The record IS consumed
        # from the stored result first, exactly as the bridge consumes it.
        #  AND IT IS SILENT. `if fs-reply = 10 ... set Cursor-Not-Active` writes
        #  no status and displays nothing [common/glpostingMT.cbl:L580-L583]; the
        #  row is consumed and dropped without a trace. A record here was an
        #  invented diagnostic on a path the compiled program says nothing about,
        #  which rule R-4 forbids - the anomaly is reproduced, and it is recorded
        #  as A10 in `docs/migration/anomaly-log.md`, which is where a reader is
        #  meant to learn about it rather than from a log line the original cannot
        #  produce.
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=incoming_fs_reply,
            we_error=incoming_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            status_written=False,
            file_key="EOF3",
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # Delivered. `perform bb100-UnloadHVs` then
    # `move HV-POST-KEY to WS-File-Key` and `move zero to fs-reply WE-Error`
    # [common/glpostingMT.cbl:L585-L588]. The snapshot has advanced by one record,
    # so `position_inclusive` now reports False and the next call fetches the
    # following record - including any row TIED on this key, which is what the
    # AMBIGUITY Q1 measurement showed a `LIMIT 1` walk lost.
    positioned = row[key.column_name]
    state.key_of_reference = key
    state.position_at(positioned)
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement=statement,
        parameters=parameters,
        file_key=str(positioned),
    )
    if file_access is not None:
        outcome.apply_to(file_access)
    return outcome


def keys_for(table_name: str) -> tuple[KeyOfReference, ...]:
    """Return every key of reference a table declares, in ``occurs`` order.

    Args:
        table_name: An in-scope table name.

    Returns:
        The declared keys, index 0 being ``KOR-x1`` of 1.

    Raises:
        KeyError: If the table is not in scope.

        >>> len(keys_for("GLPOSTING-REC"))
        1
    """
    try:
        return TABLE_OF_KEYNAMES[table_name]
    except KeyError:
        raise KeyError(
            f"{table_name!r} declares no Table-Of-Keynames entry; the in-scope "
            f"tables are {', '.join(TABLE_OF_KEYNAMES)}"
        ) from None


def key_of_reference(table_name: str, key_number: int = 1) -> KeyOfReference:
    """Return one key of reference by its ``KOR-x1`` number.

    The COBOL always sets the index by literal - ``set KOR-x1 to 1``, annotated
    ``*> 1 = Primary`` [common/glpostingMT.cbl:L455, :L709], and ``set KOR-x1 to
    2``, annotated ``*> 2 = Lines`` [common/slinvoiceMT.cbl:L2731] - so an
    out-of-range number is not reachable in the compiled system. It IS the
    situation the never-implemented ``'99NKS'`` code describes, "invalid key #
    used" [copybooks/mysql-procedures.cpy:L115], which is why the positioning
    verbs map it onto the compiled system's generic database-error pair rather
    than onto a code the compiled system never returns.

    Args:
        table_name: An in-scope table name.
        key_number: The one-based ``KOR-x1`` value.

    Returns:
        The requested key of reference.

    Raises:
        KeyError: If the table is not in scope.
        IndexError: If ``key_number`` is outside the table's ``occurs`` range.

        >>> key_of_reference("GLPOSTING-REC").name
        'POST-KEY'
    """
    keys = keys_for(table_name)
    if not 1 <= key_number <= len(keys):
        raise IndexError(
            f"{table_name} declares occurs {len(keys)}, so KOR-x1 must be "
            f"1..{len(keys)}; got {key_number}"
        )
    return keys[key_number - 1]


def _incoming_status(file_access: FileAccess | None) -> tuple[FsReply, int]:
    """Snapshot the status pair the caller already holds.

    Needed by exactly one path - the no-rows START of anomaly A7, where the
    bridge writes NEITHER status field [common/glpostingMT.cbl:L771-L781] and the
    caller's existing pair therefore survives the call. The snapshot is taken
    BEFORE the statement is issued, so what is reported is genuinely what was
    there rather than a value invented afterwards.

    An incoming value outside the declared ``FS-Reply`` set cannot be represented
    by the enum; it is reported as zero, and the authoritative signal remains
    :attr:`CursorOutcome.status_written` being ``False`` - which says "nothing was
    written, read the caller's block". The COBOL field is `pic 99`
    [copybooks/wsfnctn.cob:L31] and only the six documented values are ever
    stored into it [common/glpostingMT.cbl:L125-L131], so the situation is not
    reachable from the compiled system.

    Args:
        file_access: The caller's block, or ``None`` when the verb was called
            without one.

    Returns:
        The pair as ``(FS-Reply, We-Error)``.
    """
    if file_access is None:
        return (FsReply.SUCCESS, int(WeError.SUCCESS))
    try:
        fs_reply = FsReply(file_access.fs_reply)
    except ValueError:
        fs_reply = FsReply.SUCCESS
    return (fs_reply, int(file_access.we_error))


def _driver_failure_fields(error: BaseException) -> tuple[str, str]:
    """Render one driver exception as the two typed fields that may be logged.

    Three of the positioning verbs catch a driver failure and report it, and this
    helper is the one place the three share, so none can be the weak one.

    THE DRIVER'S MESSAGE IS NOT ONE OF THE FIELDS, AND THAT IS THE POINT. That
    text is built by the server and the client library out of material that can
    include the connection's account, the host, the failing statement and key
    values from the data, and it can carry a carriage return and a line feed - so
    interpolating it leaks and lets the failure forge a second log record
    (CWE-532, CWE-117). Redacting it was not sufficient either: the rules of
    ``redact_for_log`` recognise the connection-message shapes the client library
    is known to produce, and an arbitrary SQL literal or row key is not one of
    them. What is returned instead is the driver's error NUMBER and its SQLSTATE -
    both short closed-vocabulary fields - from which
    :func:`~acas_posting.dal.status.log_handler_failure` also derives the stable
    ``db_error_log_category`` token, which is identical for every occurrence of
    the same fault and therefore alertable in a way free text never was.

    NOTHING BRANCHES ON THE RESULT. The status pair each caller then reports is
    the one the frozen source dictates - ``(21, 0)`` for `fn-start`, end of file
    for `fn-read-next` (anomaly A11) and ``(21, 911)`` for `fn-read-indexed`
    (anomaly A14) - and it is chosen by the exception being caught at all, never
    by what the exception said. Rules R-3 and R-4 are therefore untouched: the
    only thing that changes is the rendering of a log line.

    Args:
        error: the exception the driver raised. Any exception type, because each
            call site catches ``Exception`` in order to reproduce the bridge's
            own "any error takes this path" behaviour.

    Returns:
        ``(error number, SQLSTATE)``, each as text and each empty when the
        exception does not carry it - which is the case for an exception raised
        before the driver reached a server.
    """
    return (
        str(getattr(error, "errno", "") or ""),
        str(getattr(error, "sqlstate", "") or ""),
    )



def _guarded_by_handler(
    table_name: str, file_function: FileFunction
) -> tuple[FsReply, WeError, str] | None:
    """Return the handler's refusal for a verb, or ``None`` if it permits it.

    Reproduces the unconditional entry guard of a handler whose store is
    sequential [common/acas008.cbl:L299-L307]. Data-driven from
    :data:`HANDLER_REJECTED_FUNCTIONS`, so a second such handler needs a table
    entry and no code change.
    """
    rejected = HANDLER_REJECTED_FUNCTIONS.get(table_name)
    if rejected is None:
        return None
    return rejected.get(file_function)


def _select_statement(key: KeyOfReference, relation: str) -> str:
    """Build the ONE-predicate positioning statement the bridge builds.

    Reproduces [common/glpostingMT.cbl:L729-L743] and the SELECT that consumes it
    [common/glpostingMT.cbl:L756-L761], with three deliberate fidelities:

    * ONE predicate on ONE column, because
      [common/glpostingMT.scb:L243] states the START condition cannot be
      compounded. There is no code path here that appends a second predicate.
    * ``ORDER BY`` names the KEY OF REFERENCE, matching ``keyname (KOR-x1)``
      [common/glpostingMT.cbl:L736-L739] - which for ``GLPOSTING-REC`` is NOT the
      primary key. One term, no tie-breaker.
    * ``ASC`` unconditionally - ANOMALY A6, reproduced not fixed. The bridge
      writes ``' ASC  '`` [common/glpostingMT.cbl:L740] for all five relations
      and has no descending branch, so a ``<`` or ``<=`` START positions at the
      LOWEST qualifying key. Real ISAM ``START ... KEY < value`` positions at the
      highest; emitting ``DESC`` to obtain that would be a defect fix.

    Every identifier goes through :func:`quote_identifier`, and the key VALUE is
    left as a placeholder for the driver to bind - the bridge interpolates it
    into the statement text [common/glpostingMT.cbl:L733-L735], but interpolation
    is transport, and a bound parameter yields the same logical predicate while
    removing an injection route the frozen source left open.

    There is NO ``LIMIT``, exactly as the bridge has none: ``mysql_store_result``
    materialises every qualifying row and ``ba041-Reread`` then walks the snapshot
    one record per call. Bounding the statement to a single row was measured to
    lose rows tied on a non-unique key of reference - see AMBIGUITY Q1 in the
    module docstring - and to make ``WS-MYSQL-Count-Rows`` unreproducible.

    Args:
        key: The key of reference to position on.
        relation: The trimmed relation token.

    Returns:
        The statement text, with one ``%s`` placeholder.
    """
    column = quote_identifier(key.column_name)
    return (
        f"SELECT * FROM {quote_identifier(key.table_name)} "
        f"WHERE {column} {relation} %s "
        f"ORDER BY {column} ASC"
    )


def start(
    cursor: DatabaseCursor,
    table_name: str,
    key_value: object,
    access_type: AccessType | int,
    *,
    key_number: int = 1,
    slot: CursorSlot = CursorSlot.PRIMARY,
    states: CursorStateTable | None = None,
    file_access: FileAccess | None = None,
) -> CursorOutcome:
    """``fn-start`` (``File-Function`` 9) - position the cursor, fetch nothing.

    Reproduces ``ba060-Process-Start`` [common/glpostingMT.cbl:L691-L793] step for
    step, in the order that paragraph performs them.

    THE RELATION ARRIVES THROUGH ``Access-Type``, AND ONLY BY DESIGN. Every facade
    verb clears the field before dispatching - ``move zero to Access-Type`` -
    EXCEPT ``-Start``: ``GL-Batch-Start`` is two statements with no clear
    [copybooks/Proc-ACAS-FH-Calls.cob:L456-L458] while ``GL-Batch-Read-Next`` right
    below it clears [:L460-L463], and the maintainer records the change in the
    copybook's own changelog [:L18]::

        *> 14/08/23 vbc - 1.08 - Remove 'move zero to access-type for Start, it is set !!!

    So on a START the caller's access type IS the relation. Without that one line
    this verb would have nowhere to get a relation from.

    ANOMALY A5 - REPRODUCED, NOT FIXED. The guard is ``if access-type < 5 or > 8``
    [common/glpostingMT.cbl:L695], carrying the comment ``*> not using not < or not
    >``. Its upper bound is 8, so ``fn-not-greater-than value 9`` is REJECTED with
    ``(99, 997)`` even though [copybooks/wsfnctn.cob:L116] declares it, [:L20]
    records it "Activated", and [common/glpostingMT.cbl:L724-L725] gives it a
    relation arm labelled ``*> [ not currently used in ACAS ]``; the prose at
    [:L136] agrees with the guard. The arm stays declared in ``dal/status.py`` and
    stays dead here, because widening the guard would fix a defect and rule R-4
    makes a defect fixed a failure.

    ANOMALY A7 - REPRODUCED, NOT FIXED. When the statement matches no row the
    bridge writes NEITHER status field. Only a driver-reported error sets a status,
    and it sets ``21`` paired with ``We-Error`` ZERO
    [common/glpostingMT.cbl:L771-L781]::

        if       WS-MYSQL-Count-Rows = zero
                 if    WS-MYSQL-Error-Number (1:1) not = "0"
                       move 21 to fs-reply    *> this may need changing ...
                       move zero to we-error
        else     move  zero to FS-Reply WE-Error

    So a START that finds nothing leaves whatever the caller had - typically the
    zero of a previous success - and LOOKS like success while the cursor stays
    inactive. :attr:`CursorOutcome.status_written` is ``False`` on that path and
    :meth:`CursorOutcome.apply_to` writes nothing, the only faithful reading.

    Args:
        cursor: A DB-API cursor from ``connection.py``.
        table_name: The in-scope table to position on.
        key_value: The key to compare against, as ``str``, ``int`` or ``Decimal``.
            Never a binary floating-point value (rule R-2): an inexact comparison
            positions on the wrong row without complaint.
        access_type: The caller's ``Access-Type``, which on a START is the
            relation. 5 ``=``, 6 ``<``, 7 ``>``, 8 ``>=``; 9 ``<=`` is declared
            and rejected by the guard above.
        key_number: The ``KOR-x1`` value; the COBOL always sets it by literal.
        slot: Which ``Most-Cursor-Set`` flag to drive.
        states: The cursors to use; the module-level set when ``None``.
        file_access: When given, the outcome is applied to it before returning,
            reproducing the handler's write into the caller's linkage block.

    Returns:
        The outcome, whose status pair is the one the bridge would have left.
        :attr:`CursorOutcome.row` is ALWAYS ``None``: a START positions and
        delivers no record, because the jump to the unload paragraph is commented
        out [common/glpostingMT.cbl:L795-L800]. The caller follows with
        :func:`read_next`, exactly as the in-scope programs do.
    """
    table = states if states is not None else _DEFAULT_STATES
    # Anomaly A7 needs the pair the caller ALREADY holds, so snapshot it before
    # anything is issued. [common/glpostingMT.cbl:L771-L781]
    incoming_fs_reply, incoming_we_error = _incoming_status(file_access)

    # --- Step 0: the handler's own entry guard, before any key is consulted.
    # [common/acas008.cbl:L299-L307] - `(99, 988)` for a sequential store.
    refusal = _guarded_by_handler(table_name, FileFunction.START)
    if refusal is not None:
        fs_reply, we_error, locator = refusal
        #  ONE ERROR, at the level a refusal deserves. The verb was rejected and
        #  `FS-Reply` 99 goes back to the caller, so this is a failure and not a
        #  trace - it used to be DEBUG, which made a permanently-failing verb
        #  (anomaly A6) invisible at the level an operator watches. Only the table
        #  name, the paragraph and the frozen locator are reported: no key, no
        #  statement, no value.
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba060-Process-Start",
            locator=locator,
            fs_reply=int(fs_reply),
            we_error=int(we_error),
            detail="fn-start refused by the handler for " + table_name,
        )
        outcome = CursorOutcome(
            fs_reply=fs_reply,
            we_error=int(we_error),
            row=None,
            statement="",
            parameters=(),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # --- Step 1: resolve the key of reference. An out-of-range key number is
    # the never-implemented `'99NKS'` situation, so it is reported with the
    # SQLSTATE for diagnostics and the compiled system's `(99, 911)` pair -
    # anomaly A3. [copybooks/mysql-procedures.cpy:L115, :L127-L128]
    try:
        key = key_of_reference(table_name, key_number)
    except IndexError:
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba060-Process-Start",
            locator="[copybooks/mysql-procedures.cpy:L115, :L127-L128]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            sql_state=str(SqlState.INVALID_KEY_NUMBER),
            detail="invalid key number %d for %s, which the frozen source "
            "describes and never implements" % (key_number, table_name),
        )
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.RDB_INIT_ERROR),
            row=None,
            statement="",
            parameters=(),
            sql_state=str(SqlState.INVALID_KEY_NUMBER),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    state = table.state_for(table_name, slot)

    # --- Step 2: the parameter guard. `if access-type < 5 or > 8`
    # [common/glpostingMT.cbl:L695-L699] -> `(99, 997)`, and no statement issued.
    if not start_access_type_is_valid(access_type):
        lower, upper = START_ACCESS_TYPE_RANGE
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba060-Process-Start",
            locator="[common/glpostingMT.cbl:L695-L699]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            detail="Access-Type %d rejected; the guard admits %d..%d only"
            % (access_type, lower, upper),
        )
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            row=None,
            statement="",
            parameters=(),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # --- Step 3: free any active cursor first.
    # `if Cursor-Active perform ba998-Free.` [common/glpostingMT.cbl:L703-L704]
    if state.cursor_active():
        state.free()

    # --- Step 4: the relation, from `dal/status.py`'s table.
    # `move spaces to MOST-Relation` then `evaluate Access-Type`
    # [common/glpostingMT.cbl:L713-L726]
    relation = MostRelation.for_access_type(access_type)
    state.most_relation = relation
    state.key_of_reference = key

    # --- Step 5: one predicate, one column, ORDER BY the key of reference ASC.
    statement = _select_statement(key, relation.token)
    parameters = (key_value,)

    # --- Step 6: issue it. A driver error is the bridge's
    # `WS-MYSQL-Error-Number (1:1) not = "0"` branch, which sets `(21, 0)`
    # [common/glpostingMT.cbl:L775-L781] and leaves the cursor inactive.
    try:
        cursor.execute(statement, parameters)
    except Exception as error:  # any driver error takes this path - see below
        # A failed statement reaches `(21, 0)` by being OVERWRITTEN, not by
        # being classified, and both steps are in the frozen source:
        #   1. `Mysql-1210-Command` calls `MySQL_query` and on a non-zero return
        #      performs `Mysql-1100-Db-Error`
        #      [copybooks/mysql-procedures.cpy:L165-L177], which sets `(99, 911)`
        #      [copybooks/mysql-procedures.cpy:L127-L128]. There is NO `go to`
        #      after it, so execution continues and leaves `WS-MYSQL-Count-Rows`
        #      at zero.
        #   2. Back in `ba060`, `if WS-MYSQL-Count-Rows = zero` is therefore
        #      true, errno is non-zero, and `move 21 to fs-reply` /
        #      `move zero to we-error` [common/glpostingMT.cbl:L779-L780]
        #      REPLACE the pair from step 1.
        #
        # So the observable status of a broken START statement is `(21, 0)` - not
        # `(99, 911)`, and not the `990`/`989` that belong to read-indexed. The
        # cursor is untouched on this path: `if ... not zero set Cursor-Active`
        # [common/glpostingMT.cbl:L767-L769] simply does not fire, and step 3
        # above has already left it inactive.
        errno, sql_state = _driver_failure_fields(error)
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba060-Process-Start",
            locator="[common/glpostingMT.cbl:L775-L781]",
            fs_reply=int(FsReply.INVALID_KEY_ON_START),
            we_error=int(WeError.SUCCESS),
            sql_err=errno,
            sql_state=sql_state,
            detail="the positioning statement failed at the driver for "
            + key.table_name
            + "."
            + key.column_name,
        )
        outcome = CursorOutcome(
            fs_reply=FsReply.INVALID_KEY_ON_START,
            we_error=int(WeError.SUCCESS),
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=str(SqlState.COULD_NOT_GENERATE_START),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # --- Step 7: store the result, then test its count - the bridge's two
    # stages. `Mysql-1220-Store-Result` materialises every qualifying row and
    # `MySQL_num_rows` counts it, then
    # `if WS-MYSQL-Count-Rows not zero  set Cursor-Active to true`
    # [common/glpostingMT.cbl:L767-L769]. The snapshot is what the following
    # `READ NEXT` walks; see AMBIGUITY Q1 in the module docstring.
    count = state.store_result(_store_result(cursor))
    # NOTHING is fetched from the snapshot here - see step 8. The first row is
    # only PEEKED at, to read the key the START positioned on.
    row = None if count == 0 else state.stored_rows[0]

    if row is None:
        # ANOMALY A7: no row, no driver error -> NEITHER status field written.
        # [common/glpostingMT.cbl:L771-L781]. The cursor is not touched here
        # either: L767's `if` does not fire and L771-L781 never mentions it, so
        # the inactive state established at step 3 stands.
        #
        # AND NOTHING IS REPORTED, because the bridge reports nothing. This is the
        # anomaly: a caller that asked where a key is gets its own stale status
        # pair back and no indication that the answer is stale. A log line here
        # would be a diagnostic the compiled program cannot produce and would make
        # the silence look like an oversight rather than the reproduced defect it
        # is (rule R-4). A7 is recorded in `docs/migration/anomaly-log.md`.
        outcome = CursorOutcome(
            fs_reply=incoming_fs_reply,
            we_error=incoming_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            status_written=False,
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # --- Step 8: positioned. `set Cursor-Active to true`
    # [common/glpostingMT.cbl:L769] and `move zero to FS-Reply WE-Error`
    # [common/glpostingMT.cbl:L783].
    # The position is INCLUSIVE and the row is DELIBERATELY NOT RETURNED. The
    # bridge unloads a record into the caller's record area only in
    # `ba041-Reread` [common/glpostingMT.cbl:L523-L589], and the jump that would
    # have reached it from here is commented out with the maintainer's note
    # [common/glpostingMT.cbl:L795-L800]:
    #
    #     *>           go to ba041-Reread.
    #     *> Changed to do start then read next
    #
    # So a START positions and delivers nothing; the caller must follow with
    # `read_next`, which is what every in-scope program does. Handing the row
    # back here would let a caller consume it AND have `read_next` return it
    # again from the stored result - the same posting twice. The positioned key
    # remains readable from the cursor for diagnostics.
    #
    # `fetched_count` stays at zero, so `position_inclusive` reports True and the
    # first following `READ NEXT` fetches THIS row from the snapshot.
    state.position_at(row[key.column_name])
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=None,
        statement=statement,
        parameters=parameters,
    )
    if file_access is not None:
        outcome.apply_to(file_access)
    return outcome


def read_next(
    cursor: DatabaseCursor,
    table_name: str,
    *,
    slot: CursorSlot = CursorSlot.PRIMARY,
    states: CursorStateTable | None = None,
    file_access: FileAccess | None = None,
) -> CursorOutcome:
    """``fn-read-next`` (``File-Function`` 3) - return the next row, one row.

    Reproduces ``ba040-Process-Read-Next`` [common/glpostingMT.cbl:L448-L521] and
    ``ba041-Reread`` [common/glpostingMT.cbl:L523-L589], which it falls into. The
    two are stages of one verb: ``ba040`` positions when there is no position,
    ``ba041`` delivers a row.

    THIS IS THE VERB THE POSTING CYCLE'S CORRECTNESS RESTS ON. ``gl072`` finds the
    nominal-ledger account for each posting SEQUENTIALLY rather than by key
    [general/gl072.cbl:L407-L408], so it lands on the right account only because
    ``gl071`` emitted the stream in nominal-key order first; Agent Action Plan
    0.6.4 records that changing that ordering gives "silent misposting - no error,
    no diagnostic, wrong balances". Hence ``ORDER BY`` is the key of reference,
    ascending, ONE term, no tie-breaker, matching ``keyname (KOR-x1) ... ' ASC '``
    [common/glpostingMT.cbl:L466-L470] - for ``GLPOSTING-REC`` that column is
    ``POST-KEY``, NOT the primary key [common/glpostingMT.scb:L232].

    AMBIGUITIES Q1 and Q2 both land here, stated in full in the module docstring.

    ONE ROW PER CALL, FROM A SNAPSHOT.  The bridge materialises the whole result
    at positioning time with ``mysql_store_result``
    [copybooks/mysql-procedures.cpy:L187-L193], records its full count, and then
    fetches ONE RECORD PER CALL from it - issuing no further statement. That is
    reproduced exactly: the self-positioning stage below issues the statement with
    no ``LIMIT`` and stores every qualifying row; each later call fetches from the
    stored result and executes nothing. AMBIGUITY Q1 in the module docstring
    records the measurement that settled this - a ``LIMIT 1`` walk was measured to
    deliver FOUR rows where the bridge delivers SIX, because advancing with
    ``> last_key`` skips every row tied on a non-unique key of reference, and
    ``POST-KEY`` is not this table's primary key.

    FIVE ANOMALIES ARE REPRODUCED, NOT FIXED; none may be tidied away:

    * A1 - a ``READ NEXT`` with no prior ``START`` is NOT diagnosed. The frozen
      source names ``'99RNP'`` [copybooks/mysql-procedures.cpy:L118] and never
      tests for it; ``if Cursor-Not-Active`` [common/glpostingMT.cbl:L454]
      self-positions from a hard-coded low key instead.
    * A9 - that self-positioning relation and low key are hard-coded PER BRIDGE
      and disagree, nine using ``>`` and eleven ``>=``. Driven from
      :data:`SEQUENTIAL_READ_START` so the disagreement survives as data.
    * A11 - A FAILED STATEMENT IS REPORTED AS END OF FILE: the status moves sit
      inside the zero-rows test but outside the errno test
      [common/glpostingMT.cbl:L499-L511], overwriting ``(99, 911)``
      [copybooks/mysql-procedures.cpy:L127-L128] with ``(10, 10)``. Only the log
      tag differs, ``"No Data"`` [:L510] versus ``"EOF"`` [:L558] - which is why
      :attr:`CursorOutcome.file_key` is carried.
    * A12 - ``set KOR-x1 to 1`` is hard-coded [common/glpostingMT.cbl:L455], so
      the walk always uses key of reference 1 whatever the caller asked for, and
      the two-table bridges have no sequential read for their lines table at all.
    * A10 - END OF FILE IS STICKY. After fetching, ``ba041`` re-tests the CALLER's
      own ``FS-Reply`` and, if it still holds 10, DISCARDS the row unread
      [common/glpostingMT.cbl:L580-L583]. Nothing clears that field.

    Args:
        cursor: A DB-API cursor from ``connection.py``.
        table_name: The in-scope table to read.
        slot: Which ``Most-Cursor-Set`` flag to drive; the multi-slot bridges keep
            one per read order [common/otm3MT.cbl:L265-L270].
        states: The cursors to use; the module-level set when ``None``.
        file_access: When given, the outcome is applied to it before returning and
            its incoming ``FS-Reply`` participates in the A10 test, as it must.
            Omitting it disables A10 - correct: no caller block, no stale status.

    Returns:
        The outcome. On success :attr:`CursorOutcome.row` holds the row keyed by
        column name; at end of file the pair is ``(10, 10)`` and row is ``None``.

    Raises:
        KeyError: If the table declares no key of reference.
        LookupError: If the table has no sequential read in the frozen bridges -
            the two lines tables of anomaly A12, unreachable from COBOL.
    """
    table = states if states is not None else _DEFAULT_STATES
    # Anomaly A10 reads the caller's own field, so snapshot before anything runs.
    incoming_fs_reply, incoming_we_error = _incoming_status(file_access)

    # The handler entry guard, data-driven. `fn-read-next` is NOT among the four
    # verbs the sequential handler refuses [common/acas008.cbl:L299-L307], so
    # this returns `None` for every in-scope table; it is consulted anyway
    # so that a second such handler needs a table entry and no code change.
    refusal = _guarded_by_handler(table_name, FileFunction.READ_NEXT)
    if refusal is not None:
        fs_reply, we_error, locator = refusal
        #  ONE ERROR: `FS-Reply` 99 goes back to the caller, so the verb failed.
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba050-Process-Read-Next",
            locator=locator,
            fs_reply=int(fs_reply),
            we_error=int(we_error),
            detail="fn-read-next refused by the handler for " + table_name,
        )
        outcome = CursorOutcome(
            fs_reply=fs_reply,
            we_error=int(we_error),
            row=None,
            statement="",
            parameters=(),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    state = table.state_for(table_name, slot)

    if not state.cursor_not_active():
        # --- STAGE B: `ba041`'s fetch [common/glpostingMT.cbl:L523-L555], which
        # advances the STORED RESULT an earlier positioning materialised. NO
        # STATEMENT IS ISSUED HERE - that is the whole of what `ba041` does, and
        # AMBIGUITY Q1 in the module docstring records the measurement that
        # required reproducing it this way rather than re-positioning.
        key = state.key_of_reference or key_of_reference(table_name, 1)
        # `move "EOF" to WS-File-Key` [common/glpostingMT.cbl:L558].
        return _deliver_from_stored_result(
            state,
            key,
            empty_tag="EOF",
            incoming_fs_reply=incoming_fs_reply,
            incoming_we_error=incoming_we_error,
            file_access=file_access,
        )

    # --- STAGE A: `ba040`'s self-positioning branch
    # [common/glpostingMT.cbl:L454-L473]. `set KOR-x1 to 1` - key 1 always, per
    # anomaly A12 - and the bridge's own hard-coded relation and low key, per
    # anomaly A9. This stage issues the statement and stores the result, then
    # falls THROUGH into `ba041` to deliver the first record.
    key = key_of_reference(table_name, 1)
    low = SEQUENTIAL_READ_START.get(table_name)
    if low is None:
        raise LookupError(
            f"{table_name} has no ba040-Process-Read-Next in the frozen "
            f"bridges, so the compiled system cannot read it sequentially; "
            f"see anomaly A12. Reach it through its header bridge's second "
            f"key of reference instead."
        )
    relation = low.relation
    key_value: object = low.low_key
    # `"No Data"` is the log tag `ba040` writes when this stage yields nothing
    # [common/glpostingMT.cbl:L510]; anomaly A11 makes it the ONLY way to tell a
    # broken statement from an empty table.
    empty_tag = "No Data"

    statement = _select_statement(key, relation.token)
    parameters = (key_value,)

    try:
        cursor.execute(statement, parameters)
    except Exception as error:  # any driver error takes this path - see below
        # ANOMALY A11: the error is MASKED as end of file, because the two
        # unconditional moves overwrite `Mysql-1100-Db-Error`'s `(99, 911)`
        # [common/glpostingMT.cbl:L508-L509]. Reported at ERROR - one record, with
        # the status pair that will actually be returned - so that the masking is
        # visible to an operator at the level failures are watched at. That
        # changes no status: the `(10, 200)` below is still what the caller sees.
        errno, sql_state = _driver_failure_fields(error)
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba050-Process-Read-Next",
            locator="[common/glpostingMT.cbl:L508-L509]",
            fs_reply=int(end_of_file_status()[0]),
            we_error=int(end_of_file_status()[1]),
            sql_err=errno,
            sql_state=sql_state,
            detail="the sequential read failed at the driver for "
            + key.table_name
            + "."
            + key.column_name
            + " and is MASKED as end of file (anomaly A11)",
        )
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=str(SqlState.NO_DATA),
            file_key=empty_tag,
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # `Mysql-1220-Store-Result` then `MySQL_num_rows`: the WHOLE qualifying
    # result, and its full count into `WS-MYSQL-Count-Rows`.
    count = state.store_result(_store_result(cursor))

    if count == 0:
        # `if WS-MYSQL-Count-Rows = zero ... move 10 to fs-reply / move 10 to
        # WE-Error` [common/glpostingMT.cbl:L499-L509]. The pair is `(10, 10)` -
        # `We-Error` is NOT left at zero - and the cursor is deactivated by a bare
        # `set Cursor-Not-Active to true` [:L511] rather than by `ba998-Free`.
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            file_key=empty_tag,
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # Positioned: `set Cursor-Active to true` [common/glpostingMT.cbl:L472], then
    # FALL THROUGH into `ba041-Reread`, which delivers the first record of the
    # snapshot. The fall-through is the paragraph order itself - `ba041` follows
    # `ba040` with no `go to` between them.
    state.key_of_reference = key
    state.most_relation = relation
    state.set_cursor_active()
    return _deliver_from_stored_result(
        state,
        key,
        empty_tag=empty_tag,
        incoming_fs_reply=incoming_fs_reply,
        incoming_we_error=incoming_we_error,
        file_access=file_access,
        statement=statement,
        parameters=parameters,
    )


def read_indexed(
    cursor: DatabaseCursor,
    table_name: str,
    key_value: object,
    *,
    key_number: int = 1,
    slot: CursorSlot = CursorSlot.PRIMARY,
    states: CursorStateTable | None = None,
    file_access: FileAccess | None = None,
) -> CursorOutcome:
    """``fn-read-indexed`` (``File-Function`` 4) - fetch one row by exact key.

    Reproduces ``ba050-Process-Read-Indexed`` [common/glpostingMT.cbl:L591-L689]:
    an equality fetch on the key of reference with NO ``ORDER BY`` and NO
    ``LIMIT``, matching the statement the bridge builds, `` `KeyName`="value" ``
    and nothing more [:L600-L611, :L623-L627]. The key is unique, so one row is the
    most that can qualify; either clause would be inventing statement text.

    IT STORES THE RESULT LIKE EVERY OTHER VERB. The paragraph performs
    ``MYSQL-1210-COMMAND`` and then ``MYSQL-1220-STORE-RESULT``
    [common/glpostingMT.cbl:L628-L629], the same pair the sequential read
    [:L488-L489] and the ``START`` [:L762-L763] perform, so the count it tests is
    ``MySQL_num_rows`` over a materialised snapshot
    [copybooks/mysql-procedures.cpy:L187-L192] and all three verbs share ONE
    counting strategy. The count is never taken from the driver's ``rowcount``;
    the paragraph above :func:`_column_names` records both the frozen sequence
    and the measurement that makes any other reading a silent defect. Storing
    also drains the result, so this verb leaves the connection usable on every
    exit - the hit, the miss and the driver failure alike.

    IT ALWAYS CLEARS THE SEQUENTIAL CURSOR. Every exit is ``go to ba998-Free`` -
    not found [:L635], both fetch failures [:L674, :L681] and success [:L689] - and
    ``ba998-Free`` ends with ``set Cursor-Not-Active to true`` [:L1033]. So an
    indexed read taken mid-walk DESTROYS the walk's position, on success as much as
    on failure, and the next ``READ NEXT`` restarts from the hard-coded low key.

    ANOMALY A2 - REPRODUCED, NOT FIXED. ``FS-Reply`` 23 is documented as "Key not
    found. from read indexed" [common/glpostingMT.cbl:L129] and is NEVER returned.
    The paragraph returns 21 and says so in its own comments - ``move 21 to
    fs-Reply  *> could also be 23 or 14`` [common/glpostingMT.cbl:L634], and twice
    more ``move 21 to fs-reply  *> from 23`` [:L668, :L676]. So 21 it is.

    ANOMALY A13 - REPRODUCED, NOT FIXED. The two ``We-Error`` values 990 and 989
    ARE UNREACHABLE, and the reachable not-found path writes NO ``We-Error`` at
    all. The first guard filters every zero-row case
    [common/glpostingMT.cbl:L633-L636]::

         if     WS-MYSQL-Count-Rows = zero
                move 21  to fs-Reply       *> could also be 23 or 14
                go to ba998-Free

    - it writes ``FS-Reply`` only, leaving ``We-Error`` untouched. The second guard
    is ``if WS-MYSQL-Count-Rows not > zero`` [:L663], and the count cannot have
    changed in between: it is written only by ``MySQL_affected_rows`` and
    ``MySQL_num_rows`` [copybooks/mysql-procedures.cpy:L178, :L191-L192], and the
    fetch call does not pass it [common/glpostingMT.cbl:L642-L658]. Not zero
    therefore means greater than zero, so the second guard can never be true and
    its ``990`` [:L668-L669] and ``989`` [:L676-L677] branches are dead code. Both
    stay declared in ``dal/status.py`` and stay unreachable here.

    ANOMALY A14 - REPRODUCED, NOT FIXED. A BROKEN STATEMENT RETURNS THE MISMATCHED
    PAIR ``(21, 911)``. ``Mysql-1100-Db-Error`` sets ``(99, 911)``
    [copybooks/mysql-procedures.cpy:L127-L128] and returns without jumping, so the
    count is then zero and the first guard's ``move 21 to fs-Reply`` [:L634]
    overwrites the 99 while the 911 SURVIVES. The caller sees "invalid key on
    START" paired with "RDB init error" for what was a failed statement.

    That path's interactive pause, ``display SM901`` then ``accept ws-reply``
    [copybooks/mysql-procedures.cpy:L134-L137], is dropped: Agent Action Plan 0.3.4
    rules that an accept whose only effect is to block a terminal after an error
    display is dropped while its control transfer is preserved, and this one falls
    straight through to the exit.

    Args:
        cursor: A DB-API cursor from ``connection.py``.
        table_name: The in-scope table to read.
        key_value: The exact key, as ``str``, ``int`` or ``Decimal`` - never a
            binary floating-point value, which rule R-2 forbids and which would
            make an equality test unreliable.
        key_number: The ``KOR-x1`` value. The paragraph hard-codes ``set KOR-x1 to
            1``, annotated ``*> 1 = only key`` [common/glpostingMT.cbl:L596]; the
            two-table bridges reach their lines table with ``set KOR-x1 to 2``,
            annotated ``*> 2 = Lines`` [common/slinvoiceMT.cbl:L2731], which this
            module expresses as a separate table entry instead.
        slot: Which ``Most-Cursor-Set`` flag is cleared.
        states: The cursors to use; the module-level set when ``None``.
        file_access: When given, the outcome is applied to it before returning.

    Returns:
        The outcome. On success the row keyed by column name and ``(0, 0)``; when
        the key is absent, ``(21, <the caller's We-Error>)`` and no row.

    Raises:
        KeyError: If the table declares no key of reference.
    """
    table = states if states is not None else _DEFAULT_STATES
    # The reachable not-found path writes FS-Reply only, so the caller's
    # `We-Error` survives it [common/glpostingMT.cbl:L634]. Snapshot it.
    _, incoming_we_error = _incoming_status(file_access)

    # The handler entry guard. `fn-read-indexed` IS one of the four verbs the
    # sequential handler refuses outright [common/acas008.cbl:L299-L307], so
    # PSIRSPOST-REC returns `(99, 988)` here without a statement being built.
    refusal = _guarded_by_handler(table_name, FileFunction.READ_INDEXED)
    if refusal is not None:
        fs_reply, we_error, locator = refusal
        #  ONE ERROR: `FS-Reply` 99 goes back to the caller, so the verb failed.
        #  This is the arm anomaly A6 travels on - `acas008` refuses read-indexed
        #  unconditionally - and reporting it at DEBUG made a verb that can never
        #  succeed invisible at the level an operator watches.
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba070-Process-Read-Indexed",
            locator=locator,
            fs_reply=int(fs_reply),
            we_error=int(we_error),
            detail="fn-read-indexed refused by the handler for " + table_name,
        )
        outcome = CursorOutcome(
            fs_reply=fs_reply,
            we_error=int(we_error),
            row=None,
            statement="",
            parameters=(),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # An out-of-range key number is the never-implemented `'99NKU'` situation,
    # "No valid key used" [copybooks/mysql-procedures.cpy:L116]. Anomaly A3: the
    # code is carried for diagnostics and the returned pair is the compiled
    # system's generic database-error pair
    # [copybooks/mysql-procedures.cpy:L127-L128].
    try:
        key = key_of_reference(table_name, key_number)
    except IndexError:
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba070-Process-Read-Indexed",
            locator="[copybooks/mysql-procedures.cpy:L116, :L127-L128]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            sql_state=str(SqlState.NO_VALID_KEY),
            detail="invalid key number %d for %s, which the frozen source "
            "describes and never implements" % (key_number, table_name),
        )
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.RDB_INIT_ERROR),
            row=None,
            statement="",
            parameters=(),
            sql_state=str(SqlState.NO_VALID_KEY),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    state = table.state_for(table_name, slot)

    # `\`KeyName\`="value"` and nothing else [common/glpostingMT.cbl:L602-L608].
    # The value is bound rather than interpolated into the text.
    column = quote_identifier(key.column_name)
    statement = (
        f"SELECT * FROM {quote_identifier(key.table_name)} WHERE {column} = %s"
    )
    parameters = (key_value,)

    try:
        cursor.execute(statement, parameters)
        # `PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT` follows the
        # command IMMEDIATELY [common/glpostingMT.cbl:L628-L629], exactly as it
        # does for the sequential read [:L488-L489] and the START [:L762-L763].
        # So this verb materialises the WHOLE qualifying result and counts THAT
        # with `MySQL_num_rows` [copybooks/mysql-procedures.cpy:L187-L192] -
        # never the driver's own `rowcount`, for the two reasons recorded above
        # :func:`_column_names`. Draining here is also what leaves the
        # connection usable: a result left unread would make the caller's next
        # statement fail and its next `read_next` report a false end of file.
        count = state.store_result(_store_result(cursor))
    except Exception as error:  # any driver error takes this path - see below
        # ANOMALY A14: `(21, 911)` - 21 overwrites the 99, 911 survives.
        # A FAILURE OF EITHER CALL LANDS HERE, and the frozen source is why:
        # `Mysql-1100-Db-Error` is performed both from `Mysql-1210-Command` on a
        # non-zero `MySQL_query` return [copybooks/mysql-procedures.cpy:L165-L177]
        # and from `Mysql-1220-Store-Result` when the result pointer comes back
        # null [:L188-L189]. Neither performs a `go to`, so in both cases the
        # count is left at zero and `ba050`'s first guard's `move 21 to fs-Reply`
        # [common/glpostingMT.cbl:L634] overwrites the 99 while the 911 survives.
        errno, sql_state = _driver_failure_fields(error)
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba070-Process-Read-Indexed",
            locator="[common/glpostingMT.cbl:L634] over "
            "[copybooks/mysql-procedures.cpy:L127-L128]",
            fs_reply=int(FsReply.INVALID_KEY_ON_START),
            we_error=int(WeError.RDB_INIT_ERROR),
            sql_err=errno,
            sql_state=sql_state,
            detail="the indexed read failed at the driver for "
            + key.table_name
            + "."
            + key.column_name
            + " and is reported as (21, 911) (anomaly A14)",
        )
        # `go to ba998-Free` -> `set Cursor-Not-Active to true`
        # [common/glpostingMT.cbl:L635, :L1033].
        state.free()
        outcome = CursorOutcome(
            fs_reply=FsReply.INVALID_KEY_ON_START,
            we_error=int(WeError.RDB_INIT_ERROR),
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=str(SqlState.NO_DATA),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # `if WS-MYSQL-Count-Rows = zero  move 21 to fs-Reply  go to ba998-Free`
    # [common/glpostingMT.cbl:L633-L636] is the FIRST guard and, per anomaly A13
    # in this function's docstring, the only reachable one - so the fetch is
    # reached only when the snapshot holds a record. `MySQL_fetch_record` then
    # takes that record
    # [common/glpostingMT.cbl:L642-L658]; an equality test on a key of reference
    # cannot qualify a second one, and the bridge fetches exactly once.
    row = state.fetch_record() if count > 0 else None

    # Every exit below frees the cursor, because every exit in the paragraph is
    # `go to ba998-Free` [common/glpostingMT.cbl:L635, :L674, :L681, :L689]. The
    # snapshot this verb just stored goes with it, which is what makes an indexed
    # read taken mid-walk destroy the walk's position.
    state.free()

    if row is None:
        # ANOMALY A2 and A13: 21, never 23; and `We-Error` is NOT written, so the
        # caller's value survives [common/glpostingMT.cbl:L633-L636].
        #
        # AND NOTHING IS REPORTED. "Key not found" is an ORDINARY outcome that
        # every caller in the cycle tests for and branches on - it is not a
        # failure - and the frozen guard displays nothing. The comment below
        # records that the reachable guard writes no log tag either, so a record
        # here would be the only diagnostic in the whole path and would come from
        # this migration rather than from the specification (rule R-4).
        outcome = CursorOutcome(
            fs_reply=FsReply.INVALID_KEY_ON_START,
            we_error=incoming_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            # `move spaces to WS-File-Key` is written only on the two dead
            # branches [common/glpostingMT.cbl:L673, :L680]; the reachable guard
            # writes no log tag, so none is reported.
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # `perform bb100-UnloadHVs` then `move HV-POST-KEY to ws-temp-ed` /
    # `move ws-temp-ed to WS-File-Key` and `move zero to FS-Reply WE-Error`
    # [common/glpostingMT.cbl:L684-L688].
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement=statement,
        parameters=parameters,
        file_key=str(row[key.column_name]),
    )
    if file_access is not None:
        outcome.apply_to(file_access)
    return outcome


def reset(table_name: str | None = None) -> None:
    """Clear cursor state on the module-level set of cursors.

    Every bridge holds its ``01 DAL-Data`` in its own working storage
    [common/glpostingMT.scb:L247-L251], so in the compiled system cursors are
    isolated by construction and a fresh run starts from ``value zero``. Here
    they share a process, so that reset has to be explicit.

    The determinism requirement is the reason this is part of the public
    surface: two runs of one scenario in ONE process must be
    independent, and a cursor surviving between them would let the second run
    resume a position the first left behind. Rule R-6 requires the two runs to be
    byte-identical, which they cannot be if state leaks.

    Args:
        table_name: Clear only this table's cursors when given, all of them when
            ``None``.

    Raises:
        KeyError: If ``table_name`` is given and declares no key of reference.
            A misspelled name would otherwise clear nothing and report success,
            which is the one failure mode a determinism test cannot detect. This
            guard is a Python API contract, not a validation of accounting data -
            rule R-3 forbids the latter and this reaches no table.
    """
    if table_name is not None and table_name not in TABLE_OF_KEYNAMES:
        raise KeyError(
            f"{table_name!r} declares no Table-Of-Keynames entry; the in-scope "
            f"tables are {', '.join(TABLE_OF_KEYNAMES)}"
        )
    _DEFAULT_STATES.reset(table_name)
