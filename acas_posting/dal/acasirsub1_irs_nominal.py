"""`acasirsub1` and its bridge `irsnominalMT` - the `IRSNL-REC` IRS nominal ledger.

The data-access module for the IRS nominal entity, reached through the
handler-named facade aliases that the IRS convention uses
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob].

Two of `irs030`'s reproduced defects are visible from here and neither is
repaired. Its posting path rewrites the DEBIT account before it looks the credit
account up [irs/irs030.cbl:L1635-L1652], so a missing credit account leaves a
posted debit here with nothing balancing it. And the two VAT control accounts are
read into snapshots before the loop [irs/irs030.cbl:L1602],
[irs/irs030.cbl:L1612] and rewritten from those snapshots at end of job
[irs/irs030.cbl:L1704-L1708], so an in-loop rewrite of the same account is lost.

Nothing in that list is modified. They are read as specification and cited by
path and line at every site below, which is what makes rule R-5 checkable
rather than asserted.

KEY LOCATORS
    handler linkage         [common/acasirsub1.cbl:L211-L217]
    handler key guard       [common/acasirsub1.cbl:L231-L245]
    handler RDB branch      [common/acasirsub1.cbl:L264-L268]
    handler record size     [common/acasirsub1.cbl:L691-L731]
    handler open-output     [common/acasirsub1.cbl:L733-L742]
    bridge ``USING``        [common/irsnominalMT.cbl:L267-L269]
    edit field              [common/irsnominalMT.cbl:L129]
    key metadata            [common/irsnominalMT.cbl:L139-L151]
    cursor block            [common/irsnominalMT.cbl:L157-L162]
    host-variable group     [common/irsnominalMT.cbl:L186-L210]
    bridge record           [common/irsnominalMT.cbl:L224-L247]
    bridge dispatch         [common/irsnominalMT.cbl:L302-L328]
    load paragraph          [common/irsnominalMT.cbl:L1189-L1222]
    unload paragraph        [common/irsnominalMT.cbl:L1224-L1255]
    insert section          [common/irsnominalMT.cbl:L1257-L1503]
    update section          [common/irsnominalMT.cbl:L1505-L1747]
    table                   [mysql/ACASDB.sql:L238-L255]

WHICH OF THE TWO PROGRAMS IS THE SPECIFICATION
    Both, but not equally, and the split is not the one a reader expects. The
    handler decides between its indexed-file code and the database code before
    it looks at the function code at all: ``if not FS-Cobol-Files-Used ...
    perform ba-Process-RDBMS / go to AA-Main-Exit``
    [common/acasirsub1.cbl:L264-L268] leaves the paragraph at L268, and the
    handler's own ``evaluate File-Function`` does not begin until L286. So on
    the database path EVERY ``aa0nn`` paragraph is unreachable, including
    ``aa100-Bad-Function`` and its ``(99, 999)``
    [common/acasirsub1.cbl:L657-L662], and including the whole of the indexed
    ``READ``/``WRITE``/``REWRITE``/``DELETE`` code.

    What the handler DOES contribute on this path is exactly four things: the
    calling convention and parameter order [:L211-L217]; the log identity
    [:L226-L227] and its second, higher file number [:L689]; the key-number
    guard [:L231-L245]; and the record-size gate together with the one-time
    capture of the connection block [:L691-L731]. Everything else on this path
    is the bridge's. The bridge is therefore the specification for every verb,
    and the handler's indexed-file verbs are recorded here as deliberate
    omissions rather than migrated.

    That reading corrects the assignment brief in five places, each of which
    would otherwise have produced wrong behaviour. They are listed under
    CORRECTIONS below, and each correction is annotated at its code site.

THREE RECORD VIEWS OF THE SAME BYTES, WITH THREE SETS OF FIELD NAMES
    The same 105 bytes are declared three times, and the three declarations
    disagree on almost every name. Getting the provenance wrong mis-maps
    fourteen of the fifteen columns, so it is tabulated rather than described.

    ==================  ==========================  ==========================  ==========================
    column              LINKAGE irswsnl.cob         FD irsfdwsnl.cob            BRIDGE irsnominalMT.cbl
    ==================  ==========================  ==========================  ==========================
    -                   ``NL-Record`` L8            ``Record-1`` L4             ``WS-IRSNL-Record`` L224
    ``KEY-1``           ``NL-Key`` group L9         ``Key-1`` L5                ``NL-Key pic 9(10)`` L225
    (key high half)     ``NL-Owning`` L10           ``Owning`` L6               ``NL-Owning`` L227
    (key low half)      ``NL-Sub-Nominal`` L11      ``Sub-Nominal`` L7          ``NL-Sub-Nominal`` L228
    ``TIPE``            ``NL-Type`` L12             ``Tipe`` L8                 ``NL-Tipe`` L229
    (condition names)   ``Owner``/``Sub`` L13-L14   ``NL-Sub-AC`` L9            ``Sub``/``Owner`` L230-L231
    ``NL-NAME``         ``NL-Name`` L16             ``NL-Name`` L11             ``NL-Name`` L233
    ``DR``              ``NL-DR`` L17               ``DR`` L12                  ``NL-DR`` L234
    ``CR``              ``NL-CR`` L18               ``CR`` L13                  ``NL-CR`` L235
    ``DR-LAST-01..04``  ``NL-DR-Last occurs 4`` L19 ``DR-Last occurs 4`` L14    ``DR-Last-01..04`` L237-L240
    ``CR-LAST-01..04``  ``NL-CR-Last occurs 4`` L20 ``CR-Last occurs 4`` L15    ``CR-Last-01..04`` L241-L244
    ``AC``              ``NL-AC`` L21               ``AC`` L16                  ``NL-AC`` L245
    ``REC-POINTER``     ``NL-Pointer`` L23          ``Rec-Pointer`` L18         ``NL-Pointer`` L247
    ==================  ==========================  ==========================  ==========================

    THE COLUMN NAMES COME FROM THE FD VIEW. ``KEY-1``, ``TIPE``, ``DR``,
    ``CR``, ``DR-LAST-nn``, ``CR-LAST-nn``, ``AC`` and ``REC-POINTER`` are the
    spellings of ``copybooks/irsfdwsnl.cob``, letter for letter, and
    ``NL-NAME`` keeps a prefix only because that copybook happens to call that
    one field ``NL-Name`` [copybooks/irsfdwsnl.cob:L11]. This is what settles
    the question the schema otherwise raises - why the least-qualified column
    names in the entire frozen dump sit on this one table. Nothing was
    stripped; a second, unprefixed view was used. The misspelling ``TIPE``
    likewise ORIGINATES in the FD copybook at L8, not in the bridge.

    The dictionary attributes each field's copybook view to the LINKAGE
    copybook, because that is the one the handler ``COPY``s
    [common/acasirsub1.cbl:L201]. Both facts are true at once and both are
    needed: the column NAME is the FD view's, the field METADATA is looked up
    under the column name, and every lookup in this module is by column name
    for exactly that reason.

    Two further structural disagreements matter. The copybooks declare the key
    as a GROUP of two ``pic 9(5)`` halves while the bridge declares it as ONE
    ``pic 9(10)`` with the halves as a ``REDEFINES``
    [copybooks/irswsnl.cob:L9-L11] against [common/irsnominalMT.cbl:L225-L228]
    - the same ten bytes with opposite emphasis, and the bridge's single-field
    view is why the column is a ``bigint``. And the bridge EXPANDS the
    ``occurs 4`` pair into eight separately named fields under a group it
    annotates ``*> occurs 4.`` to mark what it replaced
    [common/irsnominalMT.cbl:L236], keeping them GROUPED - all four debits,
    then all four credits - where the table INTERLEAVES them.

THE OVERLAY, AND WHY IT DECIDES WHAT GETS STORED
    ``NL-Pointer`` is not a field beside the data; it REDEFINES the whole of
    ``NL-Data`` [copybooks/irswsnl.cob:L22-L23]. Twenty-four bytes of name,
    eighty bytes of money and one byte of status are overlaid by one five-digit
    number, so ``NL-Pointer`` IS the first five characters of ``NL-Name``. Both
    views nonetheless get a column of their own, ``NL-NAME`` and
    ``REC-POINTER``, and the bridge chooses between them per row.

    It chooses by CLASS-TESTING THE NAME. ``if NL-Pointer numeric and
    NL-Pointer > zero`` [common/irsnominalMT.cbl:L1200-L1201] asks whether the
    first five characters of the account name are digits, and it never looks at
    ``NL-Type`` at all. An account whose name begins with five non-zero digits
    is therefore written as a pointer row: its name, both current balances, its
    status flag and all eight quarterly balances are left at the values the
    group's ``INITIALIZE`` [:L1197] put there, which is spaces and zeros, and
    those are what reach the table. ``"10001 Petty Cash"`` loses everything but
    its key and its type byte.

    That is anomaly A1 and it is REPRODUCED, not repaired (rule R-4): "A defect
    reproduced is correct; a defect fixed is a failure." Because Python cannot
    overlay two attributes on one byte range, the overlay is made explicit by
    three helpers - :func:`_pointer_digits`, :func:`_read_pointer_overlay` and
    :func:`_apply_pointer_overlay` - which keep ``nl_name[:5]`` and
    ``nl_pointer`` in step exactly as one byte range would.

THE VERB SET IS NOT ORDINARY CRUD
    This is the module the plan's rule about mirroring the handler boundary
    "rather than flattening them" was written for. Six verbs behave in ways no
    other handler in the folder does, and flattening any of them breaks the
    IRS posting section that consumes them.

    ``fn-read-next`` (3)   FILTERS. Sub-nominal rows are excluded twice over -
                           once by the SQL predicate ``` `TIPE`='O' ```
                           [common/irsnominalMT.cbl:L405] and again at record
                           level by ``if Sub / go to ba041-Reread``
                           [:L541-L542]. The ordinary sequential read can
                           never return an ``"S"`` row.
    ``fn-start`` (9)       READS. The paragraph ends
                           ``perform ba999-end`` then ``go to ba041-Reread``
                           [common/irsnominalMT.cbl:L773, :L777], so one call
                           both positions the cursor and delivers the first
                           qualifying record - and, because it lands in the
                           FILTERED loop, the sub-nominal filter applies to a
                           positioning call as well. It also zeroes the low
                           half of the key first, on the handler side
                           [common/acasirsub1.cbl:L523], so a positioning call
                           always lands on an owning account's first entry.
    ``fn-write`` (5)       Issues up to FOUR statements: an insert, an update
                           that forces the type byte to ``"O"``, an insert of
                           the pointer row, and a "just in case" update if that
                           insert failed [common/irsnominalMT.cbl:L793, :L839,
                           :L856, :L863-L865]. It also mutates the caller's
                           record and restores only part of it.
    ``fn-delete`` (8)      Issues TWO deletes, the row and then the pointer row
                           under a mutated key [common/irsnominalMT.cbl:L899,
                           :L960], and leaves the mutated key in place.
    ``fn-re-write`` (7)    Issues ONE update and is not pointer-aware at all
                           [common/irsnominalMT.cbl:L1088] - the third,
                           different shape among the three mutating verbs.
    ``fn-Write-Raw`` (15)  Is an UPSERT: insert, and on failure the update
                           paragraph performed as a second statement
                           [common/irsnominalMT.cbl:L1149-L1151]. The only
                           upsert in the folder, and it is two statements, not
                           the server-side single-statement extension, because
                           statement order is what a state diff observes.

    Two function codes reach this pair that reach no other. ``fn-Write-Raw``
    (15) and ``fn-Read-Next-Raw`` (13) are declared out of numeric order in
    [copybooks/wsfnctn.cob:L99-L100], 15 before 13, and 13 is annotated
    "Special 4 LD." - it exists for the load programs. The handler dispatches
    both [common/acasirsub1.cbl:L303-L306]; THE BRIDGE DISPATCHES ONLY 15
    [common/irsnominalMT.cbl:L302-L328]. On this path, therefore, 13 is a bad
    function. See correction C2.

    ``fn-Delete-All`` (6) is the mirror image: no handler in the folder
    dispatches it, and the exhaustive census across all seventeen handlers
    finds it routed to bad-function everywhere. THE BRIDGE DISPATCHES IT
    [common/irsnominalMT.cbl:L316-L317], and because the handler leaves for the
    database path before its own ``evaluate``, a caller asking for 6 reaches
    the bridge's mass delete. It is also reached the way the frozen system
    actually reaches it: ``ba015-Test-Ends`` performs the bridge once for the
    open, sets ``fn-Delete-All`` and falls through into the same paragraph to
    perform it again [common/acasirsub1.cbl:L738-L742].

THE CALLING CONVENTION, AND WHY THIS MODULE NEVER RECOVERS
    Callers reach this handler through the IRS convention
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob], which names its paragraphs after
    the HANDLER - ``acasirsub1-Read-Next`` and so on, ten verbs at L169-L221 -
    and which, unlike the General/Sales/Purchase convention in
    ``copybooks/Proc-ACAS-FH-Calls.cob``, wraps each open in a per-handler
    error check [:L334-L339] that ends in a bare ``goback`` [:L355-L364]. That
    difference is behavioural and belongs to the facade, not here. What belongs
    here is the corollary: ``ba020-Process-DAL``'s own comment, "Any errors
    leave it to caller to recover from" [common/acasirsub1.cbl:L758]. So
    :func:`dispatch` reports its status pair and performs NO recovery, no
    retry and no repair, leaving the facade's check something honest to test.

DETERMINISM AND EXACT ARITHMETIC
    Every monetary column is ``decimal(10,2) unsigned`` and every value that
    touches one is a :class:`decimal.Decimal`; the two integer columns are
    ``int``. No binary floating-point type appears anywhere in this module, in
    computation, storage or transport (rule R-2). Nothing here reads a clock, a
    process identifier or an entropy source, and no ordering is applied that
    the frozen bridge does not itself apply (rule R-6): the table has a
    single-column primary key and no secondary index, the sequential read
    carries the bridge's own ``ORDER BY`` and the indexed read carries none.

    This table is the one in-scope table with NO signedness drift, because
    nothing about it is signed - ``pic 9(8)v99`` in both copybooks,
    ``9(08)V9(02)`` in the host variables, ``unsigned`` in the column. A
    nominal-ledger accumulator that cannot hold a negative value is itself the
    anomaly; see A6. Signedness is resolved per field from the dictionary and
    never generalised from a sibling table.

CORRECTIONS TO THE ASSIGNMENT BRIEF (rule R-6: compiled behaviour decides)
    C1  The brief states that the database path has no access-type guard and
        instructs that none be implemented. It has one:
        ``if access-type < 5 or > 8`` [common/irsnominalMT.cbl:L672] sets
        ``(99, 997)`` and returns [:L673-L675]. The bridge's guard IS
        implemented. The handler's flat-file variant, which sets ``We-Error``
        998 and leaves ``FS-Reply`` at zero [common/acasirsub1.cbl:L525-L528],
        is the one that is omitted.
    C2  The brief treats ``fn-Read-Next-Raw`` (13) as a working verb. The
        bridge has no ``when 13`` [common/irsnominalMT.cbl:L302-L328], so on
        this path it is a bad function returning ``(99, 990)``. The unfiltered
        read is still implemented, because the handler's flat-file paragraph
        specifies it and the load programs use it, but ``dispatch`` routes 13
        the way the bridge routes it.
    C3  The brief gives the bad-function pair as ``(99, 999)``. That is the
        handler's [common/acasirsub1.cbl:L661-L662] and is flat-file-only. The
        bridge's is ``(99, 990)`` [common/irsnominalMT.cbl:L1158-L1159].
    C4  The brief gives the trace numbers as 201-208 plus 213 and 216. Those
        are the handler's. The bridge writes 1, 2, 3, 4, 5, 6, 8, 10, 13, 14,
        15, 17, 18 and 20, with 7, 9, 11, 12, 16 and 19 never used. Both sets
        are published below; the bridge's are the ones written.
    C5  The brief says the type-forcing update and the pointer-row insert set
        no status. That is the handler's asymmetry
        [common/acasirsub1.cbl:L584-L586, :L598-L600]. On this path both go
        through paragraphs that DO set one - the update through
        ``ba090-Process-Rewrite``'s ``(99, 994)``
        [common/irsnominalMT.cbl:L1102-L1103], the insert through
        ``ba070-Process-Write``, which re-zeroes the pair on entry [:L789].
        The bridge's behaviour is reproduced and the handler's is recorded.

DELIBERATE OMISSIONS (rule R-5: an omission is recorded, not silent)
    * The ENTIRE indexed-file path of the handler, ``aa010-main`` through
      ``aa999-main-exit`` [common/acasirsub1.cbl:L219-L667]. Unreachable on
      the database path, per the control-flow fact above.
    * The handler's access-type guard [common/acasirsub1.cbl:L525-L528]; see
      correction C1.
    * ``88 NL-Sub-AC`` [copybooks/irsfdwsnl.cob:L9]. The FD view's only
      condition name, and it is referenced nowhere in the checkout - a dead
      name. The two live names are the linkage view's ``Owner`` and ``Sub``
      [copybooks/irswsnl.cob:L13-L14], which the module tests locally because
      the semantics package is outside this layer's import contract.
    * Both ``stop`` statements [common/acasirsub1.cbl:L393, :L433], declared in
      the message block as "during testing and should NOT happen"
      [:L185-L187] and yet live in shipped code. They sit in the indexed-file
      read paragraphs, so they are unreachable here; and a process-terminating
      call would be wrong in a library regardless.
    * ``aa047-Eval-Keys`` [common/acasirsub1.cbl:L463-L479]. Its only
      ``perform`` is commented out [:L490] and the maintainer's own comment at
      L461 suspects it: "The next block will never get executed unless
      performed so is it needed ?". Kept as :func:`_aa047_eval_keys`, dead and
      labelled, because rule R-5 records rather than deletes.
    * Every ``display`` and ``accept``. Diagnostics with no effect on the table
      become log records at a matching level; the pauses are dropped; the
      control transfer past them is preserved exactly.
    * The trailing ``";"`` and ``X"00"`` the bridge appends to each statement
      [common/irsnominalMT.cbl:L1490-L1493]. That pair is the C interface's
      string framing, not part of the logical statement, and transport belongs
      to ``connection.py`` - the same reasoning by which the key value travels
      as a bound placeholder rather than interpolated text.
    * ``File-Defs``. Accepted so that the parameter order of
      [common/acasirsub1.cbl:L211-L217] survives the migration, and never read,
      because neither the handler's database path nor the bridge reads it.

AMBIGUITIES FOR THE COMPILED ORACLE (rule R-6)
    Q1  The key metadata declares the key type ``"STR"`` and says so in a
        comment, "key is string" [common/irsnominalMT.cbl:L143-L144], while
        the column is ``bigint(10) unsigned``. Every predicate the bridge
        builds therefore compares a quoted string against a number and works
        only by the server's coercion. The quoting is reproduced exactly - the
        key binds as text, never as an integer.
        RESOLVED BY MEASUREMENT on MariaDB 10.11.7 [mysql/ACASDB.sql:L1]: the
        coercion is NUMERIC, so the quoted ten-character image returns exactly the
        rows an integer bind would. A NON-NUMERIC literal cannot arise from this
        module - see :func:`_key_image`, where both key halves pass through
        :func:`_narrow_unsigned_integer` and are rendered zero-filled - so only the
        numeric case is reachable. Full probes at the two functions.
    Q2  ``HV-KEY-1`` is ``PIC 9(18) COMP`` [common/irsnominalMT.cbl:L195] for a
        ten-digit source and a ``bigint(10)`` column, the widest host variable
        in the folder, rendered through the edit field ``PIC -Z(18)9.9(9)``
        [:L129] sliced from position 3.
        RESOLVED BY MEASUREMENT, AND BOTH HALVES OF THE OLD READING WERE WRONG.
        (a) The slice does NOT lose a leading digit: measured on GnuCOBOL 3.2.0,
        the edit field's nineteen integer positions run 2 to 20, so an
        eighteen-digit value sits at 3 to 20 and ``(3:18)`` captures all of it -
        A20 is a misalignment, not a truncation. (b) ``bigint(10)`` does NOT limit
        the key to ten digits: ``(10)`` is a DISPLAY WIDTH, and measured, ``bigint
        unsigned`` stored an eighteen-digit key intact.
        The negative-accumulation half is settled too: on ``decimal(10,2)
        unsigned`` the server raises ERROR 1264 / SQLSTATE 22003 and writes
        nothing, so a negative is refused at the server rather than wrapped - which
        is where the frozen bridge meets it as well. Full probes at
        :func:`_narrow_unsigned_integer` and ``_EDIT_KEY_WINDOW``.

ANOMALY REGISTER - ALL REPRODUCED, NONE FIXED (rule R-4)
    A1  pointer-versus-data decided by class-testing the NAME
    A2  the ``occurs 4`` pair flattened AND permuted, differently each way
    A3  load and unload guards that are not inverses
    A4  ``REC-POINTER`` and the twelve data columns mutually exclusive, with
        nothing tying either to ``TIPE``
    A5  the sequential read filters, twice over
    A6  an unsigned nominal-ledger accumulator
    A7  a positioning call that reads
    A8  a positioning call that zeroes the low half of the key
    A9  a write that issues three statements at the handler, four at the bridge
    A10 a write that mutates the caller's record and restores part of it
    A11 the handler's status asymmetry across the three write statements
    A12 two deletes, and a missing row that sets no status
    A13 an update that is neither pointer-aware nor guarded
    A14 the folder's only upsert
    A15 an indexed read that chases a pointer chain
    A16 dead status assignments, overwritten or commented out
    A17 ``We-Error`` 2 and 3, the folder's only single-digit values
    A18 handler trace numbers outside the range every sibling uses
    A19 a key declared ``"STR"`` for a numeric column
    A20 an eighteen-digit host variable for a ten-digit key, rendered through a
        window that starts one position late (measured lossless - see Q2)
    A21 a pointer widened five to eight digits and narrowed back to five
    A22 three record views with three sets of field names
    A23 three spellings of one byte, originating in the FD view
    A24 a condition name referenced nowhere
    A25 a key that is a group in one view and one field in another
    A26 a dead open-output coercion upstream of the live one
    A27 an open-output path that bypasses the flat-status copy
    A28 ``fn-Delete-All`` dispatched by no handler and by this bridge
    A29 an access-type guard on the handler that rejects a type the bridge
        accepts - and a second guard on the bridge that the brief missed
    A30 four positioning branches in the order 5, 8, 7, 6
    A31 a dead helper the maintainer himself suspected
    A32 two live ``stop`` statements documented as impossible
    A33 three missing message identifiers, and one lower-cased word
    A34 a bridge that duplicates three messages and not the other two
    A35 three conditionals closed by a period, in a file that uses ``end-if``
    A36 a stale comment, and one ``initialize`` in two flavours
    A37 a bridge attributed to a different generator from every sibling
    A38 a repeating-group note in a bridge with no repeating group
    A39 a published facade verb that can never succeed
    A40 a function code the handler dispatches and the bridge does not
    A41 a stale "spare" comment on a code that is handled
    A42 an unreachable positioning branch
    A43 a special that rewrites an owner row to a sub-nominal row
    A44 a "just in case" fourth statement on the write path
    A45 diagnostic text written into a data field
    A46 an update that sets the primary key
    A47 four distinct end-of-data tags in the log key field
    A48 an initialise that clears six fields and not the seventh
    A49 two disjoint sets of trace numbers for one logical operation

    Every entry has a reproduction or documentation site below carrying its
    number and a ``[<path>:L<n>]`` locator. A future correction of any of them
    is a regression.

This module holds no business logic. It owns the SQL for one table, the
bridge's own conversion of values on the way to that table, and the dispatch
the handler performs - nothing else.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Mapping, Sequence
from decimal import Decimal
from types import MappingProxyType
from typing import Final

from acas_posting.dal.connection import (
    OpenOutcome,
    TransportSecurity,
    cobol_string_delimited_by_space,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    # `MYSQL-1090-EXIT` and `MYSQL-1999-EXIT` are aliased on import for one reason only.
    mysql_1090_exit as mysql_1090_exit_paragraph,
    mysql_1980_close,
    mysql_1999_exit as mysql_1999_exit_paragraph,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    CursorSlot,
    CursorState,
    CursorStateTable,
    KeyOfReference,
    key_of_reference,
)
from acas_posting.dal.status import (
    AccessType,
    DbErrorStatus,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    is_duplicate_key_bridge_level,
    log_file_handler_record,
    log_handler_failure,
    mysql_1100_db_error,
    override_we_error_for_operation,
    start_access_type_is_valid,
    start_relation_for,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess, LoggingData, RdbData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.irs_nominal import WsIrsnlRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    "ACCESS_TYPE_STATUS",
    "BAD_FUNCTION_STATUS",
    "BRIDGE",
    "BRIDGE_TRACE_NUMBERS",
    "COLUMNS",
    "DELETE_ALL_HIGH_KEY",
    "DELETE_FAILED_WE_ERROR",
    "DELETE_KEY_NUMBER_STATUS",
    "DISPATCHED_FUNCTIONS",
    "DUPLICATE_KEY_STATUS",
    "END_OF_DATA_TAGS",
    "END_OF_FILE_STATUS",
    "ENTITY_FACADE",
    "HANDLER",
    "HANDLER_BAD_FUNCTION_STATUS",
    "HANDLER_TRACE_NUMBERS",
    "KEY_COUNT",
    "KEY_LENGTH",
    "KEY_METADATA_TYPE",
    "KEY_NUMBER_STATUS",
    "KEY_OFFSET",
    "KEY_OFFSET_LENGTH",
    "LOAD_TRAVERSAL",
    "NAME_COLUMN",
    "NOT_FOUND_LITERALS",
    "NOT_FOUND_STATUS",
    "NO_DRIVER_ERROR",
    "PARAGRAPHS",
    "POINTER_COLUMN",
    "POINTER_EXCLUSIVE_COLUMNS",
    "PRIMARY_KEY",
    "RECORD_SIZE_STATUS",
    "REWRITE_FAILED_WE_ERROR",
    "SEQUENTIAL_LOW_KEY",
    "SEQUENTIAL_TYPE_FILTER",
    "TABLE",
    "TYPE_COLUMN",
    "TYPE_OWNER",
    "TYPE_SUB",
    "UNLOAD_TRAVERSAL",
    "WS_LOG_FILE_NO_FLAT",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "ca_process_logs",
    "citation",
    "close",
    "delete",
    "delete_all",
    "dispatch",
    "open_",
    "open_extend",
    "open_input",
    "open_output",
    "read_indexed",
    "read_next",
    "read_next_raw",
    "reset_bridge_storage",
    "rewrite",
    "start",
    "write",
    "write_raw",
)

_LOG: Final = logging.getLogger(__name__)


# The "IRS nominal" row of the entity-to-table spine, written out once so that no string
# below can name a different table, handler or bridge.

TABLE: Final[str] = "IRSNL-REC"

PRIMARY_KEY: Final[str] = "KEY-1"

HANDLER: Final[str] = "acasirsub1"

BRIDGE: Final[str] = "irsnominalMT"

ENTITY_FACADE: Final[str] = "IRS nominal"


# `01 Table-Of-Keynames` [common/irsnominalMT.cbl:L139-L151], whose casing drifts three
# ways inside six lines - `Table-Of-Keynames` at L141, `table-of-keynames` at L146,
# `keyOfReference` at L147.

KEY_OFFSET_LENGTH: Final[str] = "00010010"

KEY_OFFSET: Final[int] = 1

KEY_LENGTH: Final[int] = 10

#: ANOMALY A19 - the metadata declares the key type ``"STR"`` and the bridge
#: editorialises on it in a comment, "key is string" [common/irsnominalMT.cbl:L144], yet
#: the column is ``bigint(10) unsigned`` [mysql/ACASDB.sql:L239].
KEY_METADATA_TYPE: Final[str] = "STR"

KEY_COUNT: Final[int] = 1


#: ``move 1 to WS-Log-System`` [common/acasirsub1.cbl:L226].
WS_LOG_SYSTEM: Final[int] = int(LogSystem.IRS)

WS_LOG_FILE_NO_FLAT: Final[int] = 11

WS_LOG_FILE_NO_RDB: Final[int] = 21


#: The fifteen columns in the ordinal order the frozen dump fixes
#: [mysql/ACASDB.sql:L239-L253], which is also the order of the host-variable group
#: [common/irsnominalMT.cbl:L195-L209] and of the ``SET`` list the insert section emits
#: [common/irsnominalMT.cbl:L1272-L1487].
COLUMNS: Final[tuple[str, ...]] = (
    "KEY-1",
    "TIPE",
    "NL-NAME",
    "DR",
    "CR",
    "DR-LAST-01",
    "CR-LAST-01",
    "DR-LAST-02",
    "CR-LAST-02",
    "DR-LAST-03",
    "CR-LAST-03",
    "DR-LAST-04",
    "CR-LAST-04",
    "AC",
    "REC-POINTER",
)

#: The twelve columns the load paragraph's ``else`` branch fills
#: [common/irsnominalMT.cbl:L1204-L1215], and which a pointer row therefore leaves at
#: the values ``initialize TD-IRSNL-REC`` [:L1197] put in them.
POINTER_EXCLUSIVE_COLUMNS: Final[tuple[str, ...]] = (
    "NL-NAME",
    "DR",
    "CR",
    "DR-LAST-01",
    "CR-LAST-01",
    "DR-LAST-02",
    "CR-LAST-02",
    "DR-LAST-03",
    "CR-LAST-03",
    "DR-LAST-04",
    "CR-LAST-04",
    "AC",
)

POINTER_COLUMN: Final[str] = "REC-POINTER"

#: The type byte [mysql/ACASDB.sql:L240]. ANOMALY A23 - three spellings of one byte.
TYPE_COLUMN: Final[str] = "TIPE"

#: The account name [mysql/ACASDB.sql:L241] - the only column on this table that keeps
#: an ``NL-`` prefix, and it keeps it because the FD view spells that one field ``NL-
#: Name`` [copybooks/irsfdwsnl.cob:L11].
NAME_COLUMN: Final[str] = "NL-NAME"

_QUARTERS: Final[int] = 4

_QUARTER_COLUMNS_INTERLEAVED: Final[tuple[str, ...]] = (
    "DR-LAST-01",
    "CR-LAST-01",
    "DR-LAST-02",
    "CR-LAST-02",
    "DR-LAST-03",
    "CR-LAST-03",
    "DR-LAST-04",
    "CR-LAST-04",
)

#: The same eight in the order the UNLOAD paragraph reads them
#: [common/irsnominalMT.cbl:L1244-L1251] - grouped. ANOMALY A2.
_QUARTER_COLUMNS_GROUPED: Final[tuple[str, ...]] = (
    "DR-LAST-01",
    "DR-LAST-02",
    "DR-LAST-03",
    "DR-LAST-04",
    "CR-LAST-01",
    "CR-LAST-02",
    "CR-LAST-03",
    "CR-LAST-04",
)

#: The full statement order of ``bb000-HV-Load`` [common/irsnominalMT.cbl:L1198-L1215]:
#: key, type byte, then EITHER the pointer column OR the twelve data columns with the
#: quarters interleaved.
LOAD_TRAVERSAL: Final[tuple[str, ...]] = (
    "KEY-1",
    "TIPE",
    "REC-POINTER",
    "NL-NAME",
    "DR",
    "CR",
    "AC",
    *_QUARTER_COLUMNS_INTERLEAVED,
)

UNLOAD_TRAVERSAL: Final[tuple[str, ...]] = (
    "KEY-1",
    "TIPE",
    "REC-POINTER",
    "NL-NAME",
    "DR",
    "CR",
    "AC",
    *_QUARTER_COLUMNS_GROUPED,
)


# `88 Owner value is "O"` and `88 Sub value is "S"` [copybooks/irswsnl.cob:L13-L14].

TYPE_OWNER: Final[str] = "O"

TYPE_SUB: Final[str] = "S"


#: ``'"0000000000"'`` [common/irsnominalMT.cbl:L410] - the low key the sequential read
#: positions above.
SEQUENTIAL_LOW_KEY: Final[str] = "0000000000"

#: ``move 9999999999 to NL-Key`` [common/irsnominalMT.cbl:L1009], described there as
#: "The last possible data", and used as ``< "9999999999"`` [:L1015-L1025].
DELETE_ALL_HIGH_KEY: Final[str] = "9999999999"

#: The literal the sequential-read predicate carries [common/irsnominalMT.cbl:L404].
SEQUENTIAL_TYPE_FILTER: Final[str] = TYPE_OWNER


#: End of data. ``move 10 to fs-reply`` then ``move 3 to WE-Error``
#: [common/irsnominalMT.cbl:L453, :L455], with the paragraph's own comment stating the
#: intent outright.
END_OF_FILE_STATUS: Final[tuple[FsReply, int]] = (FsReply.END_OF_FILE, 3)

#: Key not found. ``move 21 to fs-Reply`` then ``move 2 to WE-Error``
#: [common/irsnominalMT.cbl:L591-L592], the 21 carrying the maintainer's own hedge,
#: "could also be 23 or 14".
NOT_FOUND_STATUS: Final[tuple[FsReply, int]] = (FsReply.INVALID_KEY_ON_START, 2)

DUPLICATE_KEY_STATUS: Final[tuple[FsReply, int]] = (FsReply.DUPLICATE_KEY, 0)

BAD_FUNCTION_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.UNKNOWN_UNEXPECTED),
)

HANDLER_BAD_FUNCTION_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.NOT_USED),
)

#: The record-size abort [common/acasirsub1.cbl:L701-L702] - ``move 901 to WE-Error``
#: then ``move 99 to fs-reply``, after which the handler jumps to its own exit and the
#: bridge is NEVER called [:L718].
RECORD_SIZE_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.RECORD_SIZE_MISMATCH),
)

ACCESS_TYPE_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.ACCESS_TYPE_WRONG),
)

#: The handler's key-number guard for ``fn-read-indexed`` and ``fn-start``
#: [common/acasirsub1.cbl:L235-L236] - ``move 998 to WE-Error`` then ``move 99 to fs-
#: reply``.
KEY_NUMBER_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
)

#: The handler's key-number guard for ``fn-delete`` [common/acasirsub1.cbl:L241-L242] -
#: a DIFFERENT code, 996, for the same condition, with the extra comment "1 is only for
#: RDB as Cobol does it on primary key" [:L240] repeated verbatim from
#: ``common/acas022.cbl:L307``.
DELETE_KEY_NUMBER_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.DELETE_KEY_OUT_OF_RANGE),
)

#: A failed delete [common/irsnominalMT.cbl:L915-L916, :L1057-L1058] and a failed update
#: [:L1102-L1103]. Both are the generic (99, 911) narrowed afterwards by the verb, which
#: is what :func:`status.override_we_error_for_operation` reproduces.
DELETE_FAILED_WE_ERROR: Final[int] = int(WeError.DELETE_SQLSTATE_NOT_00000)
REWRITE_FAILED_WE_ERROR: Final[int] = int(WeError.REWRITE_SQLSTATE_NOT_00000)

#: The errno the bridge treats as "no driver error", written with its two trailing
#: spaces exactly as the source compares it.
NO_DRIVER_ERROR: Final[str] = "0  "


BRIDGE_TRACE_NUMBERS: Final[Mapping[str, int]] = MappingProxyType(
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
        "ba080-Delete-Pointer": 14,
        "ba085-Process-Delete-ALL": 15,
        "ba090-Process-Rewrite": 17,
        "ba170-Process-Write-Raw": 18,
        "ba998-Free": 20,
    }
)

#: ``WS-No-Paragraph`` as the HANDLER writes it on its indexed-file path.
HANDLER_TRACE_NUMBERS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "aa020-Process-Open": 201,
        "aa030-Process-Close": 202,
        "aa040-Process-Read-Next": 203,
        "aa045-Process-Read-Next-Raw": 213,
        "aa050-Process-Read-Indexed": 204,
        "aa060-Process-Start": 205,
        "aa070-Process-Write": 206,
        "aa080-Process-Delete": 207,
        "aa090-Process-Rewrite": 208,
        "aa170-Process-Write-Raw": 216,
    }
)


#: ANOMALY A47 - FOUR distinct end-of-data tags reach ``WS-File-Key`` on the read path,
#: and which one a caller sees says where the walk stopped.
END_OF_DATA_TAGS: Final[tuple[str, ...]] = ("No Data", "EOF", "EOF2", "EOF3")

#: ANOMALY A45 - the indexed read writes DIAGNOSTIC TEXT INTO THE NAME FIELD.
NOT_FOUND_LITERALS: Final[tuple[str, ...]] = (
    "Not found 1",
    "Not found 2",
    "Not found",
)

_OPEN_TAG: Final[str] = "OPEN IRSNOMINAL (RDB)"
_CLOSE_TAG: Final[str] = "CLOSE IRSNOMINAL (RDB)"


#: Every COBOL paragraph this module reproduces, mapped to the function that reproduces
#: it, with its line span.
PARAGRAPHS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "common/irsnominalMT.cbl:L282-L292 ba010-Initialise": "_ba010_initialise",
        "common/irsnominalMT.cbl:L302-L328 dispatch": "dispatch",
        "common/irsnominalMT.cbl:L330-L372 ba020-Process-Open": "open_",
        "common/irsnominalMT.cbl:L374-L387 ba030-Process-Close": "close",
        "common/irsnominalMT.cbl:L389-L467 ba040-Process-Read-Next": "read_next",
        "common/irsnominalMT.cbl:L469-L547 ba041-Reread": "_ba041_reread",
        "common/irsnominalMT.cbl:L549-L663 ba050-Process-Read-Indexed": "read_indexed",
        "common/irsnominalMT.cbl:L665-L777 ba060-Process-Start": "start",
        "common/irsnominalMT.cbl:L783-L813 ba070-Process-Write": "_ba070_process_write",
        "common/irsnominalMT.cbl:L815-L852 ba072-Proc-Write-Subs": "_ba072_proc_write_subs",
        "common/irsnominalMT.cbl:L854-L868 ba073-Fix-Up-Subs": "_ba073_fix_up_subs",
        "common/irsnominalMT.cbl:L870-L985 ba080-Process-Delete": "delete",
        "common/irsnominalMT.cbl:L987-L1066 ba085-Process-Delete-ALL": "delete_all",
        "common/irsnominalMT.cbl:L1068-L1114 ba090-Process-Rewrite": "rewrite",
        "common/irsnominalMT.cbl:L1120-L1152 ba170-Process-Write-Raw": "write_raw",
        "common/irsnominalMT.cbl:L1154-L1160 ba100-Bad-Function": "_ba100_bad_function",
        "common/irsnominalMT.cbl:L1166-L1177 ba998-Free": "_ba998_free",
        "common/irsnominalMT.cbl:L1189-L1222 bb000-HV-Load": "_load_host_variables",
        "common/irsnominalMT.cbl:L1224-L1255 bb100-UnloadHVs": "_unload_host_variables",
        "common/irsnominalMT.cbl:L1257-L1499 bb200-Insert": "_bb200_insert",
        "common/irsnominalMT.cbl:L1501-L1747 bb300-Update": "_bb300_update",
        "common/irsnominalMT.cbl:L1749-L1755 Ca-Process-Logs": "ca_process_logs",
        "common/acasirsub1.cbl:L211-L217 Procedure Division Using": "dispatch",
        "common/acasirsub1.cbl:L231-L245 key-number guard": "_key_number_guard",
        "common/acasirsub1.cbl:L463-L479 aa047-Eval-Keys": "_aa047_eval_keys",
        "common/acasirsub1.cbl:L691-L731 ba012-Test-WS-Rec-Size-2": "_record_size_gate",
        "common/acasirsub1.cbl:L733-L742 ba015-Test-Ends": "open_output",
    }
)

DISPATCHED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {
        int(FileFunction.OPEN),
        int(FileFunction.CLOSE),
        int(FileFunction.READ_NEXT),
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.DELETE_ALL),
        int(FileFunction.RE_WRITE),
        int(FileFunction.DELETE),
        int(FileFunction.START),
        int(FileFunction.WRITE_RAW),
    }
)


# THE FIELD METADATA (rule R-5 - resolved, never transcribed) Every one of the fifteen
# columns is looked up in the generated dictionary, under the key form
# `<TABLE>.<COLUMN>` - which for this table means under the FD copybook's column
# spellings (ANOMALY A22), because that is what the frozen dump declares.


def _entry(column: str) -> loader.DictionaryEntry:
    """Return the dictionary entry for one column of this table.

    Args:
        column: The column name as [mysql/ACASDB.sql:L239-L253] spells it.

    Returns:
        The entry, carrying the copybook view, the bridge host variable, the column, the
            drift flags and the derivation guard.

    Raises:
        DictionaryLookupError: If the artefact holds no such entry, which would mean the
            dictionary and this module disagree about the table - a condition to fail on
            rather than paper over.
    """
    return loader.get_entry(f"{TABLE}.{column}")


def citation(column: str) -> str:
    """Return the three-layer provenance line for one column.

    The rendered form is the dictionary's own, e.g. ``IRSNL-REC.KEY-1
    copybook=copybooks/irswsnl.cob:L9 bridge=common/irsnominalMT.cbl:L195
    column=mysql/ACASDB.sql:L239``.

    Args:
        column: The column name.

    Returns:
        The provenance line.
    """
    return loader.cite(f"{TABLE}.{column}")


_ENTRIES: Final[Mapping[str, loader.DictionaryEntry]] = MappingProxyType(
    {column: _entry(column) for column in COLUMNS}
)

#: Columns whose host variable declares a fractional scale - the ten money columns,
#: every one of them ``9(08)V9(02)`` and UNSIGNED [common/irsnominalMT.cbl:L198-L207].
_MONEY_COLUMNS: Final[tuple[str, ...]] = tuple(
    column
    for column in COLUMNS
    if (_ENTRIES[column].bridge_host_variable.scale or 0) > 0
)

_CHARACTER_COLUMNS: Final[tuple[str, ...]] = tuple(
    column
    for column in COLUMNS
    if _ENTRIES[column].bridge_host_variable.character_length is not None
)

_INTEGER_COLUMNS: Final[tuple[str, ...]] = tuple(
    column
    for column in COLUMNS
    if column not in _MONEY_COLUMNS and column not in _CHARACTER_COLUMNS
)

_CHARACTER_WIDTHS: Final[Mapping[str, int]] = MappingProxyType(
    {
        column: int(_ENTRIES[column].bridge_host_variable.character_length or 0)
        for column in _CHARACTER_COLUMNS
    }
)

_MONEY_DIGITS: Final[Mapping[str, tuple[int, int]]] = MappingProxyType(
    {
        column: (
            int(_ENTRIES[column].bridge_host_variable.integer_digits or 0),
            int(_ENTRIES[column].bridge_host_variable.scale or 0),
        )
        for column in _MONEY_COLUMNS
    }
)

#: Digit count of each whole-number host variable. [common/irsnominalMT.cbl:L195] for a
#: ten-digit source [copybooks/irswsnl.cob:L10-L11] and a ``bigint(10)`` column
#: [mysql/ACASDB.sql:L239]: eight digits of inflation, then narrowing.
_INTEGER_DIGITS: Final[Mapping[str, int]] = MappingProxyType(
    {
        column: int(_ENTRIES[column].bridge_host_variable.digits or 0)
        for column in _INTEGER_COLUMNS
    }
)

#: The name field's declared width, needed by the overlay helpers because the pointer
#: occupies its first five characters.
_NAME_WIDTH: Final[int] = _CHARACTER_WIDTHS[NAME_COLUMN]

#: A money host variable at its initialised value, at the declared scale so that a zero
#: renders ``"0.00"`` and not ``"0"``.
_ZERO_MONEY: Final[Decimal] = Decimal(0).scaleb(0).quantize(
    Decimal(1).scaleb(-_MONEY_DIGITS["DR"][1])
)

#: ``05 NL-Pointer pic 9(5)`` [copybooks/irswsnl.cob:L23] - the width of the alternative
#: view, and therefore how many characters of the name the class test in ANOMALY A1
#: inspects.
_POINTER_DIGITS_IN_RECORD: Final[int] = 5

#: The two halves of the key, each ``pic 9(5)`` [copybooks/irswsnl.cob:L10-L11].
_KEY_HALF_DIGITS: Final[int] = 5

#: ASCII digits, spelled out rather than delegated to ``str.isdigit``, which also
#: accepts superscripts and other Unicode digit forms.
_ASCII_DIGITS: Final[frozenset[str]] = frozenset("0123456789")


# "The bridge is not a transparent pipe." Where the copybook declaration, the host
# variable and the column disagree, the value CHANGES on the way through, before any SQL
# executes - so this layer must reproduce the bridge's conversion rather than write the
# computed value and let the server complain.

_EDIT_WIDTH: Final[int] = 30

_EDIT_SUPPRESSED_DIGITS: Final[int] = 18

_EDIT_INTEGER_DIGITS: Final[int] = 19

_EDIT_FRACTION_DIGITS: Final[int] = 9

#: ``FUNCTION TRIM (WS-MYSQL-EDIT(03:18))``
#: [common/irsnominalMT.cbl:L1276] - the window the key is rendered through.
#:
#: ANOMALY A20, second half. The window STARTS AT POSITION 3, so it omits
#: position 2 - the most significant of the nineteen integer positions.
#:
#: ⭐ CORRECTION, MEASURED ON GnuCOBOL 3.2.0 [common/comp-common.sh:L9]. This note
#: used to conclude that "a key filling all eighteen digits ``HV-KEY-1`` can hold
#: would therefore lose its leading digit before the statement was even sent". IT
#: DOES NOT, and the arithmetic says why: ``WS-MYSQL-EDIT`` is
#: ``PIC -Z(18)9.9(9)`` [common/irsnominalMT.cbl:L228], which is 1 + 18 + 1 + 1 + 9
#: = THIRTY characters with its nineteen integer positions at 2 through 20. An
#: eighteen-digit value therefore occupies positions 3 to 20 and position 2 stays
#: blank. Compiled, ``123456789012345678`` renders as::
#:
#:     [  123456789012345678.000000000]
#:      window (3:18) -> [123456789012345678]   COMPLETE
#:
#: Position 2 is reached only by a NINETEEN-digit value, and ``PIC 9(18) COMP``
#: cannot hold one. So the window is lossless over the whole domain the host
#: variable has, and the anomaly is that the window is MISALIGNED rather than that
#: it truncates. It is reproduced as written either way. See ambiguity Q2, which
#: settles the storage side.
_EDIT_KEY_WINDOW: Final[tuple[int, int]] = (3, 18)

_EDIT_INTEGER_WINDOW: Final[tuple[int, int]] = (13, 8)

#: ``WS-MYSQL-EDIT(22:02)`` [common/irsnominalMT.cbl:L1311] - the fractional window, NOT
#: trimmed, so it is always two digits and a value of zero renders ``"00"`` rather than
#: an empty string.
_EDIT_FRACTION_WINDOW: Final[tuple[int, int]] = (22, 2)


def _narrow_unsigned_integer(value: int, digits: int) -> int:
    """Reproduce a ``move`` into an unsigned ``PIC 9(digits) COMP`` item.

    Digit-position semantics, not arithmetic: the sending value's digits are
    right-aligned in the receiving positions, so the LOW-ORDER ``digits``
    digits survive and anything more significant is discarded, and the sign is
    dropped because the receiving item is unsigned. That is what a COBOL store
    does, and it is why no check is made here - a check would be a new
    validation (rule R-3).

    AMBIGUITY Q2 - RESOLVED BY MEASUREMENT against MariaDB 10.11.7, the server
    version the frozen schema records as its producer [mysql/ACASDB.sql:L1, :L5],
    with the frozen ``ENGINE=InnoDB`` (all 33 tables) and the server's DEFAULT
    ``sql_mode``,
    ``STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION``.
    That default is what the bridge's C interface gets, and the one ``SET SQL_MODE``
    in the frozen dump does not change it: ``SQL_MODE='NO_AUTO_VALUE_ON_ZERO'``
    [mysql/ACASDB.sql:L21] is SESSION-scoped - measured, it leaves
    ``@@global.sql_mode`` untouched - and the dump restores it at [:L1451] anyway,
    so it governs only the schema load. It is inert even there: the schema's ONLY
    ``AUTO_INCREMENT`` column is ``STOCKAUDIT-REC.AUDIT-ID``
    [mysql/ACASDB.sql:L1107], and that table is out of scope entirely (plan
    section 0.2.2). Two out-of-range cases were open on this table and both are now
    settled; nothing below is assumed.

    (1) THE KEY. ``HV-KEY-1`` is ``PIC 9(18) COMP``
        [common/irsnominalMT.cbl:L195] for a ten-digit source, and the concern was
        that a ``bigint(10)`` column could not carry eighteen digits. IT CAN:
        ``(10)`` IS A DISPLAY WIDTH, NOT A CONSTRAINT. Measured, ``bigint
        unsigned`` holds 0 through 18446744073709551615, and an eighteen-digit key
        stored intact. AND THE COBOL SIDE DOES NOT TRUNCATE EITHER: measured on
        GnuCOBOL 3.2.0, the edit window ``(3:18)`` [:L1276] captures an
        eighteen-digit value COMPLETE, because the edit field's integer positions
        run 2 to 20 - see the correction on ``_EDIT_KEY_WINDOW``. So there is no
        narrowing anywhere on the key path within the host variable's domain, and
        ANOMALY A20 is a misalignment rather than a truncation.

    (2) THE MONEY ITEMS. Every one is unsigned at all three layers - ANOMALY A6 -
        so a negative accumulation has no representation on the path, and the
        question was what the server does with one. Measured on ``decimal(10,2)
        unsigned``: ``-1.00`` and ``100000000.00`` each raise **ERROR 1264,
        SQLSTATE 22003, "Out of range value"** and THE ROW IS NOT WRITTEN. The
        server neither clamps nor stores a wrapped value. Note the contrast, also
        measured: SCALE overflow ROUNDS instead - ``1.005`` stores ``1.01`` and
        ``1.004`` stores ``1.00`` - so precision and scale have different
        dispositions.

    WHAT THAT MEANS FOR THIS FUNCTION, AND WHY IT IS UNCHANGED. It reproduces the
    DECLARED COBOL storage and adds no check, which is exactly right: the refusal
    lives at the server, where the frozen bridge also meets it, and it arrives as
    a driver error the bridge's own error path already handles. Adding a Python
    check would move the refusal to a layer the frozen source has nothing at
    (rule R-3), and would also HIDE it - the frozen bridge gets an error and this
    module must get the same one.

    Args:
        value: The sending value.
        digits: The receiving item's declared digit count.

    Returns:
        The stored value, always zero or greater.
    """
    magnitude = -value if value < 0 else value
    text = format(magnitude, "d")
    return int(text.rjust(digits, "0")[-digits:])


def _narrow_unsigned_money(value: Decimal, column: str) -> Decimal:
    """Reproduce a ``move`` into an unsigned ``PIC 9(08)V9(02) COMP`` item.

    The receiving digit counts come from the dictionary (:data:`_MONEY_DIGITS`), never
    from a literal here. Three things happen at once, exactly as one COBOL store does
    them.

    Args:
        value: The sending value.
        column: The receiving column, whose host variable supplies the widths.

    Returns:
        A non-negative :class:`~decimal.Decimal` at the declared scale.
    """
    integer_digits, scale = _MONEY_DIGITS[column]
    text = format(value.copy_abs(), "f")
    whole, _, fraction = text.partition(".")
    whole = whole.rjust(integer_digits, "0")[-integer_digits:]
    fraction = (fraction + "0" * scale)[:scale]
    return Decimal(f"{whole}.{fraction}")


def _ws_mysql_edit(value: Decimal) -> str:
    """Build the thirty-character image of ``01 WS-MYSQL-EDIT``.

    Reproduces ``move <host variable> to WS-MYSQL-EDIT``
    [common/irsnominalMT.cbl:L1274-L1275] against the picture at
    [common/irsnominalMT.cbl:L129], ``PIC -Z(18)9.9(9)``.

    Args:
        value: The host-variable value, already narrowed.

    Returns:
        Exactly :data:`_EDIT_WIDTH` characters.
    """
    negative = value < 0
    text = format(value.copy_abs(), "f")
    whole, _, fraction = text.partition(".")
    whole = whole.rjust(_EDIT_INTEGER_DIGITS, "0")[-_EDIT_INTEGER_DIGITS:]
    fraction = (fraction + "0" * _EDIT_FRACTION_DIGITS)[:_EDIT_FRACTION_DIGITS]

    suppressed: list[str] = []
    significant_seen = False
    for character in whole[:_EDIT_SUPPRESSED_DIGITS]:
        if character != "0":
            significant_seen = True
        suppressed.append(character if significant_seen else " ")

    return (
        ("-" if negative else " ")
        + "".join(suppressed)
        + whole[_EDIT_SUPPRESSED_DIGITS:]
        + "."
        + fraction
    )


def _edit_window(image: str, window: tuple[int, int]) -> str:
    """Slice one reference-modified window out of the edit image.

    Args:
        image: The output of :func:`_ws_mysql_edit`.
        window: The one-based position and the length.

    Returns:
        The window, with no trimming applied.
    """
    position, length = window
    return image[position - 1 : position - 1 + length]


def _render_key(value: int) -> str:
    """Render ``HV-KEY-1`` the way the insert and update sections render it.

    Args:
        value: The key as one number.

    Returns:
        The rendered text, ready to bind.
    """
    narrowed = _narrow_unsigned_integer(value, _INTEGER_DIGITS[PRIMARY_KEY])
    image = _ws_mysql_edit(Decimal(narrowed))
    return _edit_window(image, _EDIT_KEY_WINDOW).strip()


def _render_integer(value: int, column: str) -> str:
    """Render an unsigned whole-number host variable other than the key.

    ``move HV-REC-POINTER to WS-MYSQL-EDIT`` then ``FUNCTION TRIM (WS-MYSQL-
    EDIT(13:08))`` [common/irsnominalMT.cbl:L1483-L1487] - ANOMALY A21's eight-digit
    window over a five-digit source and a five-digit column.

    Args:
        value: The value to store.
        column: The receiving column, whose host variable supplies the width.

    Returns:
        The rendered text, ready to bind.
    """
    narrowed = _narrow_unsigned_integer(value, _INTEGER_DIGITS[column])
    image = _ws_mysql_edit(Decimal(narrowed))
    return _edit_window(image, _EDIT_INTEGER_WINDOW).strip()


def _render_money(value: Decimal, column: str) -> str:
    """Render an unsigned money host variable.

    ``FUNCTION TRIM (WS-MYSQL-EDIT(13:08))``, then a literal ``"."``, then
    [common/irsnominalMT.cbl:L1305-L1313]. So the integer part loses its leading zeros
    while the fraction keeps both digits: zero renders ``"0.00"``, five pence renders
    ``"0.05"``.

    Args:
        value: The value to store.
        column: The receiving column, whose host variable supplies the widths.

    Returns:
        The rendered text, ready to bind.
    """
    narrowed = _narrow_unsigned_money(value, column)
    image = _ws_mysql_edit(narrowed)
    whole = _edit_window(image, _EDIT_INTEGER_WINDOW).strip()
    fraction = _edit_window(image, _EDIT_FRACTION_WINDOW)
    return f"{whole}.{fraction}"


def _render_character(value: str, column: str) -> str:
    """Render an alphanumeric host variable.

    A consequence worth stating because it looks like a defect and is not: a single-
    character field holding a space renders as the EMPTY STRING, and that empty string
    is what reaches a ``char(1) NOT NULL`` column.

    Args:
        value: The value to store.
        column: The receiving column, whose host variable supplies the width.

    Returns:
        The rendered text, ready to bind.
    """
    image = _character_image(value, _CHARACTER_WIDTHS[column])
    return image.rstrip()


# `03 filler redefines NL-Data. / 05 NL-Pointer pic 9(5)`
# [copybooks/irswsnl.cob:L22-L23].


def _character_image(value: str, width: int) -> str:
    """Return ``value`` as it sits in a ``pic x(width)`` field.

    A COBOL alphanumeric move left-justifies and space-fills, and truncates on the right
    when the sending item is longer.

    Args:
        value: The current attribute value.
        width: The declared width, from the dictionary.

    Returns:
        Exactly ``width`` characters.
    """
    return value.ljust(width)[:width]


def _pointer_digits(nl: WsIrsnlRecord) -> str:
    """Return the five characters ``NL-Pointer`` occupies.

    They are the FIRST FIVE CHARACTERS OF THE ACCOUNT NAME, because the pointer view
    redefines the data group [copybooks/irswsnl.cob:L22-L23].

    Args:
        nl: The record.

    Returns:
        Five characters, space-filled if the name is shorter.
    """
    name = _character_image(nl.nl_data.nl_name, _NAME_WIDTH)
    return name[:_POINTER_DIGITS_IN_RECORD]


def _pointer_is_numeric(nl: WsIrsnlRecord) -> bool:
    """Reproduce the ``NL-Pointer numeric`` class test.

    Args:
        nl: The record.

    Returns:
        True when the overlaid characters form a valid unsigned integer.
    """
    digits = _pointer_digits(nl)
    return len(digits) == _POINTER_DIGITS_IN_RECORD and all(
        character in _ASCII_DIGITS for character in digits
    )


def _read_pointer_overlay(nl: WsIrsnlRecord) -> int:
    """Return ``NL-Pointer`` as a number, or zero when it is not numeric.

    Args:
        nl: The record.

    Returns:
        The overlaid value, or zero when the characters are not all digits.
    """
    if not _pointer_is_numeric(nl):
        return 0
    return int(_pointer_digits(nl))


def _apply_pointer_overlay(nl: WsIrsnlRecord, value: int) -> None:
    """Write ``NL-Pointer``, which writes the name's first five characters too.

    Reproduces ``move NL-Owning to NL-Pointer`` [common/irsnominalMT.cbl:L850] - a five-
    digit store into a field that overlays the name, so the name's first five characters
    become those digits and the account name is corrupted in the caller's own record.

    Args:
        nl: The record to mutate in place.
        value: The pointer value. Stored into ``pic 9(5)``, so the low-order five digits
            are what survive - a COBOL move, not a check.
    """
    digits = _narrow_unsigned_integer(value, _POINTER_DIGITS_IN_RECORD)
    text = f"{digits:0{_POINTER_DIGITS_IN_RECORD}d}"
    name = _character_image(nl.nl_data.nl_name, _NAME_WIDTH)
    nl.nl_data.nl_name = text + name[_POINTER_DIGITS_IN_RECORD:]
    nl.nl_pointer_view.nl_pointer = digits


def _is_pointer_row(nl: WsIrsnlRecord) -> bool:
    """THE DISCRIMINATOR. Reproduce ``if NL-Pointer numeric and > zero``.

    ``if NL-Pointer numeric and NL-Pointer > zero``
    [common/irsnominalMT.cbl:L1200-L1201] is the single most consequential line in this
    module, and IT DOES NOT LOOK AT ``NL-Type``.

    Args:
        nl: The record about to be written.

    Returns:
        True when the row is stored as a pointer row and the twelve data columns are
            left at their initialised values.
    """
    return _pointer_is_numeric(nl) and _read_pointer_overlay(nl) > 0


def _owner(nl: WsIrsnlRecord) -> bool:
    """``88 Owner value is "O"`` [copybooks/irswsnl.cob:L13].

    Tested here rather than imported: the semantics package that declares the condition
    names is outside this layer's import contract, so the one-byte comparison is made
    locally against the value the copybook gives.

    Args:
        nl: The record.

    Returns:
        True for an owning account.
    """
    return nl.nl_type == TYPE_OWNER


def _sub(nl: WsIrsnlRecord) -> bool:
    """``88 Sub value is "S"`` [copybooks/irswsnl.cob:L14].

    The FD view's own condition name for the same value, ``88 NL-Sub-AC``
    [copybooks/irsfdwsnl.cob:L9], is referenced nowhere in the checkout - ANOMALY A24,
    recorded as a deliberate omission.

    Args:
        nl: The record.

    Returns:
        True for a sub-nominal, i.e. a pointer row.
    """
    return nl.nl_type == TYPE_SUB


def _key_image(nl: WsIrsnlRecord) -> str:
    """Return the ten raw characters the bridge slices out of the record.

    Every predicate the bridge builds interpolates ``WS-IRSNL-Record (K:L)``
    [common/irsnominalMT.cbl:L563, :L716, :L881], where ``K`` and ``L`` are the
    offset and length the key metadata declares - 1 and 10
    [common/irsnominalMT.cbl:L143]. Those ten bytes are the two ``pic 9(5)``
    halves of the key, so the image is each half rendered zero-filled at its
    declared width and concatenated.

    ANOMALY A19 - this text is what the predicate compares against a
    ``bigint(10) unsigned`` column, because the key metadata declares the key
    type ``"STR"`` with the comment "key is string"
    [common/irsnominalMT.cbl:L143-L144]. It is bound as TEXT and never as an
    integer, because that is what the bridge sends and binding an integer
    "because the column is a bigint" would be a different statement.

    AMBIGUITY Q1 - RESOLVED BY MEASUREMENT against MariaDB 10.11.7
    [mysql/ACASDB.sql:L1]. A ten-character decimal string compared against a
    ``bigint(10) unsigned`` works by the server's implicit coercion, and this is
    the only key in the handler set where the declared key type and the column
    type disagree, so which direction the coercion goes decides which rows a
    predicate returns.

    IT COERCES TO A NUMBER, proved with a probe whose two readings disagree:
    against a numeric column holding 9 and 10, ``k > "10"`` returns NO rows and
    ``k < "10"`` returns 9 - the opposite of what a lexical comparison gives. And
    ``9 > "10"`` evaluates 0 while ``"9" > "10"`` evaluates 1, so it is the
    presence of a numeric operand that decides. Applied to this key: ``KEY-1 =
    '0000000001'`` matched the row holding 1, and ``KEY-1 < '1000100001'`` returned
    {0, 1} in numeric order. So the zero-filled ten-character image below produces
    exactly the row set an integer bind would, and the leading zeros are harmless.
    Binding it as TEXT therefore stays - that is what the bridge sends, and binding
    an integer "because the column is a bigint" would be a different statement for
    no gain.

    THE MALFORMED-KEY SUB-QUESTION IS UNREACHABLE FROM HERE, which the source
    settles without any server. The old note asked what the server does with "a
    partially spaced key, or one carrying a sign"; this function cannot produce
    one. Both halves pass through :func:`_narrow_unsigned_integer`, which returns
    a non-negative ``int``, and each is then rendered zero-filled at its declared
    width - so the image is always exactly ten decimal digits. A non-numeric key
    could only arise from a caller that left the record's ``pic 9(5)`` halves
    non-numeric, which is a precondition on the caller and not behaviour of this
    module.

    Args:
        nl: The record whose key is wanted.

    Returns:
        Exactly ten characters.
    """
    owning = _narrow_unsigned_integer(nl.nl_key.nl_owning, _KEY_HALF_DIGITS)
    sub_nominal = _narrow_unsigned_integer(
        nl.nl_key.nl_sub_nominal, _KEY_HALF_DIGITS
    )
    return (
        f"{owning:0{_KEY_HALF_DIGITS}d}{sub_nominal:0{_KEY_HALF_DIGITS}d}"
    )


def _set_name(nl: WsIrsnlRecord, value: str) -> None:
    """Write ``NL-Name``, which writes ``NL-Pointer`` too.

    The mirror image of :func:`_apply_pointer_overlay`. ``move HV-NL-NAME to NL-Name``
    [common/irsnominalMT.cbl:L1240] stores 24 bytes over storage whose first five are
    also ``NL-Pointer`` [copybooks/irswsnl.cob:L22-L23], so the decoded pointer
    attribute is re-derived from the new characters.

    Args:
        nl: The record to mutate in place.
        value: The name as read back or as supplied.
    """
    nl.nl_data.nl_name = _character_image(value, _NAME_WIDTH)
    nl.nl_pointer_view.nl_pointer = _read_pointer_overlay(nl)


def _key_number(nl: WsIrsnlRecord) -> int:
    """Return the key as one number, the way ``NL-Key pic 9(10)`` holds it.

    The bridge's own view of the key [common/irsnominalMT.cbl:L225] - ANOMALY A25. Used
    where the bridge moves the whole key into a host variable rather than slicing the
    record image.

    Args:
        nl: The record.

    Returns:
        The ten digits as an integer.
    """
    return int(_key_image(nl))


def _set_key_from_number(nl: WsIrsnlRecord, value: int) -> None:
    """Split a ten-digit key back into the two ``pic 9(5)`` halves.

    Reproduces ``move HV-KEY-1 to NL-Key`` [common/irsnominalMT.cbl:L1235], where the
    receiving item is the ten-byte group and the two halves are a ``REDEFINES`` of it,
    so one store fills both.

    Args:
        nl: The record to fill.
        value: The key value read back from the table.
    """
    digits = _narrow_unsigned_integer(value, KEY_LENGTH)
    text = f"{digits:0{KEY_LENGTH}d}"
    nl.nl_key.nl_owning = int(text[:_KEY_HALF_DIGITS])
    nl.nl_key.nl_sub_nominal = int(text[_KEY_HALF_DIGITS:])


# `bb000-HV-Load Section.` [common/irsnominalMT.cbl:L1189-L1216]. Called before every
# non-fetch action, it copies the caller's record into the host-variable group that the
# statement text is then rendered from.


def _initialise_host_variables() -> dict[str, object]:
    """Reproduce ``initialize TD-IRSNL-REC``.

    ``initialize`` sets each elementary item to the figurative constant for its category
    - zero for numeric, space for alphanumeric [common/irsnominalMT.cbl:L1197].

    Returns:
        All fifteen host variables at their initialised values. Every entry is an
            :class:`int`, a :class:`~decimal.Decimal` or a :class:`str`; never ``None``.
    """
    host_variables: dict[str, object] = {}
    for column in COLUMNS:
        if column in _MONEY_COLUMNS:
            host_variables[column] = _ZERO_MONEY
        elif column in _CHARACTER_COLUMNS:
            host_variables[column] = " " * _CHARACTER_WIDTHS[column]
        else:
            host_variables[column] = 0
    return host_variables


def _load_host_variables(
    nl: WsIrsnlRecord,
    *,
    traversal: list[str] | None = None,
) -> dict[str, object]:
    """Reproduce ``bb000-HV-Load`` [common/irsnominalMT.cbl:L1189-L1216].

    ANOMALY A38 - the section closes with "Loading HVs implies a non-Fetch action. RGs
    are handled separately for all such actions so they must not be loaded here."
    [common/irsnominalMT.cbl:L1218-L1219] IN A BRIDGE THAT HAS NO REPEATING GROUP.

    Args:
        nl: The caller's record, read and never modified here.
        traversal: When supplied, each column is appended as it is assigned, so that the
            ORDER of the assignments is observable to a caller.

    Returns:
        The fifteen host variables.
    """
    host_variables = _initialise_host_variables()

    def assign(column: str, value: object) -> None:
        host_variables[column] = value
        if traversal is not None:
            traversal.append(column)

    # `move NL-Key to HV-KEY-1.` [common/irsnominalMT.cbl:L1198]
    #
    # ANOMALY A20 - the receiving host variable is `PIC 9(18) COMP`
    # [common/irsnominalMT.cbl:L195] for a ten-digit source and a `bigint(10)`
    # column, the widest host variable in the handler set. The widening is
    # harmless, and MEASURED, SO IS EVERYTHING AFTER IT: the edit window
    # `(3:18)` carries all eighteen digits (GnuCOBOL 3.2.0) and `bigint(10)
    # unsigned` stores all eighteen (MariaDB 10.11.7), because `(10)` is a
    # display width. Ambiguity Q2 is resolved; nothing narrows within the host
    # variable's domain.
    assign(PRIMARY_KEY, _narrow_unsigned_integer(
        _key_number(nl), _INTEGER_DIGITS[PRIMARY_KEY]
    ))

    # `move NL-Tipe to HV-TIPE.` [common/irsnominalMT.cbl:L1199] ANOMALY A23 - one byte
    # with three spellings across the three record views: `NL-Type`
    # [copybooks/irswsnl.cob:L12], `Tipe` [copybooks/irsfdwsnl.cob:L8] and `NL-Tipe`
    # [common/irsnominalMT.cbl:L229].
    assign(TYPE_COLUMN, _character_image(nl.nl_type, _CHARACTER_WIDTHS[TYPE_COLUMN]))

    # `if NL-Pointer numeric and NL-Pointer > zero`
    # [common/irsnominalMT.cbl:L1200-L1201] - ANOMALY A1.
    if _is_pointer_row(nl):
        # `move NL-Pointer to HV-REC-POINTER` [common/irsnominalMT.cbl:L1202]. ANOMALY
        # A21 - `pic 9(5)` widened into `PIC 9(08) COMP` [common/irsnominalMT.cbl:L209]
        # and then narrowed again by a `mediumint(5)` column.
        assign(POINTER_COLUMN, _narrow_unsigned_integer(
            _read_pointer_overlay(nl), _INTEGER_DIGITS[POINTER_COLUMN]
        ))
        return host_variables

    # The `else` branch [common/irsnominalMT.cbl:L1204-L1215].
    assign(NAME_COLUMN, _character_image(
        nl.nl_data.nl_name, _CHARACTER_WIDTHS[NAME_COLUMN]
    ))
    assign("DR", _narrow_unsigned_money(nl.nl_data.nl_dr, "DR"))
    assign("CR", _narrow_unsigned_money(nl.nl_data.nl_cr, "CR"))
    assign("AC", _character_image(nl.nl_data.nl_ac, _CHARACTER_WIDTHS["AC"]))
    for quarter in range(_QUARTERS):
        debit_column = _QUARTER_COLUMNS_INTERLEAVED[quarter * 2]
        credit_column = _QUARTER_COLUMNS_INTERLEAVED[quarter * 2 + 1]
        assign(debit_column, _narrow_unsigned_money(
            nl.nl_data.nl_dr_last[quarter], debit_column
        ))
        assign(credit_column, _narrow_unsigned_money(
            nl.nl_data.nl_cr_last[quarter], credit_column
        ))
    return host_variables


# `bb100-UnloadHVs Section.` [common/irsnominalMT.cbl:L1224-L1252]. Called after every
# fetch, it copies the host-variable group back into the caller's record.


def _host_variables_from_row(row: Mapping[str, object]) -> dict[str, object]:
    """Populate the host-variable group from one fetched row.

    The bridge's fetch moves each result column into its host variable before
    ``bb100-UnloadHVs`` runs; this does the same, coercing whatever the driver handed
    back into the host variable's declared storage.

    Args:
        row: One row, keyed on column name.

    Returns:
        The fifteen host variables.
    """
    host_variables = _initialise_host_variables()
    for column in COLUMNS:
        if column not in row:
            continue
        value = row[column]
        if value is None:
            continue
        if column in _MONEY_COLUMNS:
            host_variables[column] = _narrow_unsigned_money(
                value if isinstance(value, Decimal) else Decimal(str(value)),
                column,
            )
        elif column in _CHARACTER_COLUMNS:
            text = value.decode("utf-8") if isinstance(value, bytes) else str(value)
            host_variables[column] = _character_image(
                text, _CHARACTER_WIDTHS[column]
            )
        else:
            host_variables[column] = _narrow_unsigned_integer(
                int(value), _INTEGER_DIGITS[column]
            )
    return host_variables


def _unload_host_variables(
    row: Mapping[str, object],
    nl: WsIrsnlRecord,
    *,
    traversal: list[str] | None = None,
) -> None:
    """Reproduce ``bb100-UnloadHVs`` [common/irsnominalMT.cbl:L1224-L1252].

    Args:
        row: The fetched row, keyed on column name.
        nl: The caller's record, filled in place - because the COBOL fills the caller's
            own linkage item and a caller may hold references into it.
        traversal: When supplied, each field is appended as it is assigned, so that the
            GROUPED order is observable. See :data:`UNLOAD_TRAVERSAL`.
    """
    host_variables = _host_variables_from_row(row)

    def note(column: str) -> None:
        """Record that ``column`` has just been moved into the record."""
        if traversal is not None:
            traversal.append(column)

    # `initialize WS-IRSNL-Record.` [common/irsnominalMT.cbl:L1233], plain - ANOMALY
    # A36, because the same bridge writes `initialize WS-IRSNL-Record with filler`
    # elsewhere [common/irsnominalMT.cbl:L524], and the stale comment `*> (init moved
    # lower)` [:L1229] sits directly above an `initialize` that is not lower but
    # immediately below.
    nl.nl_key.nl_owning = 0
    nl.nl_key.nl_sub_nominal = 0
    nl.nl_type = " "
    nl.nl_data.nl_name = " " * _NAME_WIDTH
    nl.nl_data.nl_dr = _ZERO_MONEY
    nl.nl_data.nl_cr = _ZERO_MONEY
    nl.nl_data.nl_dr_last = (_ZERO_MONEY,) * _QUARTERS
    nl.nl_data.nl_cr_last = (_ZERO_MONEY,) * _QUARTERS
    nl.nl_data.nl_ac = " "
    nl.nl_pointer_view.nl_pointer = 0

    # `move HV-KEY-1 to NL-Key.` [common/irsnominalMT.cbl:L1235] - one store into the
    # ten-byte group, which fills both `pic 9(5)` halves because they are a REDEFINES of
    # it.
    key_value = host_variables[PRIMARY_KEY]
    _set_key_from_number(nl, int(key_value) if isinstance(key_value, int) else 0)
    note(PRIMARY_KEY)

    type_value = host_variables[TYPE_COLUMN]
    nl.nl_type = type_value[:1] if isinstance(type_value, str) else " "
    note(TYPE_COLUMN)

    # `if HV-REC-POINTER > zero` [common/irsnominalMT.cbl:L1237] - ANOMALY A3.
    pointer_value = host_variables[POINTER_COLUMN]
    pointer = int(pointer_value) if isinstance(pointer_value, int) else 0
    if pointer > 0:
        _apply_pointer_overlay(nl, pointer)
        note(POINTER_COLUMN)
        return

    # The `else` branch [common/irsnominalMT.cbl:L1240-L1251]: name, balances, status
    # flag, then the quarters GROUPED - all four debits, then all four credits.
    name_value = host_variables[NAME_COLUMN]
    _set_name(nl, name_value if isinstance(name_value, str) else "")
    note(NAME_COLUMN)
    debit = host_variables["DR"]
    nl.nl_data.nl_dr = debit if isinstance(debit, Decimal) else _ZERO_MONEY
    note("DR")
    credit = host_variables["CR"]
    nl.nl_data.nl_cr = credit if isinstance(credit, Decimal) else _ZERO_MONEY
    note("CR")
    status = host_variables["AC"]
    nl.nl_data.nl_ac = status[:1] if isinstance(status, str) else " "
    note("AC")

    debits: list[Decimal] = []
    for column in _QUARTER_COLUMNS_GROUPED[:_QUARTERS]:
        value = host_variables[column]
        debits.append(value if isinstance(value, Decimal) else _ZERO_MONEY)
        note(column)
    nl.nl_data.nl_dr_last = tuple(debits)

    credits: list[Decimal] = []
    for column in _QUARTER_COLUMNS_GROUPED[_QUARTERS:]:
        value = host_variables[column]
        credits.append(value if isinstance(value, Decimal) else _ZERO_MONEY)
        note(column)
    nl.nl_data.nl_cr_last = tuple(credits)


@dataclasses.dataclass(slots=True)
class _BridgeStorage:
    """Everything the two programs keep in WORKING-STORAGE between calls.

    Attributes:
        connection: What ``Ws-Mysql-Cid`` refers to once ``MYSQL-1000-OPEN`` has run
            [common/irsnominalMT.cbl:L360]. ``None`` before the open and after the
            close.
        cursors: ``01 DAL-Data`` [common/irsnominalMT.cbl:L157-L162] plus the stored
            result ``TP-IRSNL-REC`` [:L193].
        record_size_a: ``77 A pic 9(4) value zero`` [common/acasirsub1.cbl:L178], whose
            being zero is also the once-only latch [common/acasirsub1.cbl:L693].
        record_size_b: ``77 B pic 9(4) value zero`` [common/acasirsub1.cbl:L179].
        transport: How the connection may cross the network.
    """

    connection: object | None = None
    cursors: CursorStateTable = dataclasses.field(
        default_factory=CursorStateTable
    )
    record_size_a: int = 0
    record_size_b: int = 0
    transport: TransportSecurity | None = None


_STORAGE: _BridgeStorage = _BridgeStorage()


def reset_bridge_storage(*, transport: TransportSecurity | None = None) -> None:
    """Discard the working storage, as ending the run unit would.

    THIS FUNCTION HAS NO COUNTERPART IN THE FROZEN SOURCE and is recorded as an addition
    in the module docstring.

    Args:
        transport: The transport policy for the next run.
    """
    global _STORAGE
    if _STORAGE.connection is not None:
        mysql_1980_close(_STORAGE.connection)
        mysql_1999_exit_paragraph()
    _STORAGE = _BridgeStorage(transport=transport)


def _cursor_state() -> CursorState:
    """Return ``01 DAL-Data`` for this table.

    Returns:
        The single cursor state.
    """
    return _STORAGE.cursors.state_for(TABLE, CursorSlot.PRIMARY)


# `MYSQL-1210-COMMAND`, `MYSQL-1220-STORE-RESULT`, `MySQL_fetch_record` and
# `MySQL_free_result` are foreign calls into the C interface object the frozen build
# links.


def _cursor_column_names(cursor: object) -> tuple[str, ...]:
    """Return the result's column names, in the order the server sent them.

    Args:
        cursor: The cursor :func:`execute_statement` yielded.

    Returns:
        One name per column, or an empty tuple for a statement that returned no result
            set - an ``INSERT``, an ``UPDATE`` or a ``DELETE``.
    """
    description = getattr(cursor, "description", None)
    if not description:
        return ()
    return tuple(str(column[0]) for column in description)


def _row_mapping(
    row: object,
    names: tuple[str, ...],
) -> dict[str, object]:
    """Shape one driver row into a mapping keyed on column name.

    Args:
        row: Whatever the driver's ``fetchone`` returned - a mapping when the cursor is
            dictionary-shaped, a sequence otherwise.
        names: The column names from :func:`_cursor_column_names`.

    Returns:
        The row, keyed on column name.
    """
    if isinstance(row, Mapping):
        return {str(key): value for key, value in row.items()}
    values = tuple(row) if isinstance(row, Sequence) else (row,)
    if len(names) == len(values):
        return dict(zip(names, values, strict=True))
    return {str(index): value for index, value in enumerate(values)}


def _fetch_all_rows(cursor: object) -> list[dict[str, object]]:
    """Materialise the whole result, as ``mysql_store_result`` does.

    ``MYSQL-1220-STORE-RESULT`` brings the ENTIRE qualifying result to the client
    [common/irsnominalMT.cbl:L434] and ``MySQL_num_rows`` then reports its size, which
    is why the bridge can test ``WS-MYSQL-Count-Rows`` before fetching anything.

    Args:
        cursor: The cursor :func:`execute_statement` yielded.

    Returns:
        Every row, in the order the statement returned them.
    """
    names = _cursor_column_names(cursor)
    if not names:
        return []
    fetchone = getattr(cursor, "fetchone", None)
    if fetchone is None:
        return []
    rows: list[dict[str, object]] = []
    while True:
        row = fetchone()
        if row is None:
            break
        rows.append(_row_mapping(row, names))
    return rows


def _affected_rows(cursor: object) -> int:
    """Return ``WS-MYSQL-Count-Rows`` after a non-select statement.

    Args:
        cursor: The cursor :func:`execute_statement` yielded.

    Returns:
        The row count the driver reported, or zero when it reported none.
    """
    count = getattr(cursor, "rowcount", 0)
    if isinstance(count, int) and count > 0:
        return count
    return 0


def _driver_failure(
    error: Exception,
    *,
    command: str,
    file_function: int,
) -> DbErrorStatus:
    """Map a driver exception onto the bridge's error fields.

    Reproduces the ``MYSQL-1100-DB-Error`` ladder every guarded arm of the bridge
    performs, then the per-operation ``We-Error`` substitution the delete and rewrite
    arms apply [common/irsnominalMT.cbl:L916, :L1103]. Delegated to ``dal/status.py`` so
    that the ladder exists once.

    Args:
        error: Whatever the driver raised. Caught broadly and deliberately.
        command: The statement text, for the log line.
        file_function: The function code in play, which selects the substitution.

    Returns:
        The five error fields plus the duplicate-key verdict.
    """
    errno = getattr(error, "errno", "") or ""
    sql_state = str(getattr(error, "sqlstate", "") or "")
    status = mysql_1100_db_error(
        errno=str(errno),
        message=str(getattr(error, "msg", None) or error),
        sql_state=sql_state,
        command=command,
    )
    #  NO RECORD HERE. `mysql_1100_db_error` has just emitted THE operator record
    #  for this failure, at the layer that stands in for the frozen
    #  `Mysql-1110-Report-Problem` [copybooks/mysql-procedures.cpy:L130-L137], and
    #  it carries the same status pair, the same SQLSTATE, the same error number
    #  and the same stable category. A second record here added nothing an
    #  operator could act on and two things that must not be logged at all: the
    #  `command`, which is the full statement text with its literal host-variable
    #  values, and the driver's own message, which can name the account and echo a
    #  row key (CWE-532). One failure, one record - see the safe-event schema in
    #  `dal/status.py`.
    return override_we_error_for_operation(status, file_function)


# `WS-File-Key`, `WS-Log-Where`, `SQL-Err`, `SQL-Msg` and `SQL-State` are alphanumeric
# items of `Logging-Data` [copybooks/wsfnctn.cob:L44-L56] that both programs write on
# almost every path.

_LOGGING_WIDTHS: Final[Mapping[str, int]] = MappingProxyType(
    {
        field.name: len(value)
        for field in dataclasses.fields(LoggingData)
        for value in (getattr(LoggingData(), field.name),)
        if isinstance(value, str)
    }
)


def _move_to_log_field(file_access: FileAccess, attribute: str, text: str) -> None:
    """``move <text> to <Logging-Data field>``, with COBOL truncation.

    Args:
        file_access: The linkage block whose ``Logging-Data`` is written.
        attribute: The field to write.
        text: The sending value. Space-padded and right-truncated to the receiving
            width, which is what an alphanumeric move does.
    """
    width = _LOGGING_WIDTHS[attribute]
    setattr(file_access.logging_data, attribute, _character_image(text, width))


def _set_trace(file_access: FileAccess, paragraph: str) -> None:
    """``move <n> to ws-No-Paragraph`` for one bridge paragraph.

    ANOMALY A49 - the bridge and the handler carry TWO DISJOINT trace-number sets for
    the same logical operations.

    Args:
        file_access: The linkage block whose ``Logging-Data`` is written.
        paragraph: The bridge paragraph name, a key of :data:`BRIDGE_TRACE_NUMBERS`.
    """
    file_access.logging_data.ws_no_paragraph = BRIDGE_TRACE_NUMBERS[paragraph]


def _apply_status(file_access: FileAccess, status: tuple[int, int]) -> None:
    """Write one ``(FS-Reply, We-Error)`` pair.

    The pair is written in that order because the frozen code writes it in that order,
    and because two of this bridge's paths write a value into ``We-Error`` and then
    immediately overwrite it - ANOMALY A16 - which only reads correctly if the order is
    preserved.

    Args:
        file_access: The linkage block to write.
        status: The reply and the error code.
    """
    fs_reply, we_error = status
    file_access.fs_reply = fs_reply
    file_access.we_error = we_error


def _apply_driver_status(
    file_access: FileAccess,
    status: DbErrorStatus,
) -> None:
    """Write the five fields ``MYSQL-1100-DB-Error`` leaves behind.

    Args:
        file_access: The linkage block to write.
        status: The mapped driver failure.
    """
    file_access.fs_reply = status.fs_reply
    file_access.we_error = status.we_error
    _move_to_log_field(file_access, "sql_err", status.sql_err)
    _move_to_log_field(file_access, "sql_msg", status.sql_msg)
    _move_to_log_field(file_access, "sql_state", status.sql_state)


def _ba010_initialise(file_access: FileAccess) -> None:
    """``ba010-Initialise`` [common/irsnominalMT.cbl:L282-L292].

    ANOMALY A48 - it clears SIX fields and ``SQL-State`` IS NOT ONE OF THEM. ``WS-MYSQL-
    Error-Message``, ``WS-MYSQL-Error-Number``, ``WS-Log-Where``, ``WS-File-Key``,
    ``SQL-Msg`` and ``SQL-Err`` are all set to spaces [:L287-L292] while ``SQL-State``
    is left holding whatever the PREVIOUS call put there.

    Args:
        file_access: The linkage block to initialise.
    """
    file_access.we_error = int(WeError.SUCCESS)
    file_access.fs_reply = int(FsReply.SUCCESS)
    # `move spaces to ...` [:L287-L292]. The two WS-MYSQL-* items are the bridge's own
    # working storage rather than linkage, so they have no counterpart to clear here.
    _move_to_log_field(file_access, "ws_log_where", "")
    _move_to_log_field(file_access, "ws_file_key", "")
    _move_to_log_field(file_access, "sql_msg", "")
    _move_to_log_field(file_access, "sql_err", "")


def _ba100_bad_function(file_access: FileAccess) -> tuple[int, int]:
    """``ba100-Bad-Function`` [common/irsnominalMT.cbl:L1154-L1160].

    Args:
        file_access: The linkage block to write.

    Returns:
        ``(99, 990)``.
    """
    # ONE ERROR, through the shared reporter, so this failure renders with the same
    # fields in the same order as every other handler's. `File-Function` is an
    # operation code from the frozen vocabulary [copybooks/wsfnctn.cob:L88-L118].
    log_handler_failure(
        _LOG,
        program="irsnominalMT",
        paragraph="ba100-Bad-Function",
        locator="[common/irsnominalMT.cbl:L1179-L1188]",
        fs_reply=int(BAD_FUNCTION_STATUS[0]),
        we_error=int(BAD_FUNCTION_STATUS[1]),
        detail="File-Function %s is not one this bridge implements"
        % int(file_access.file_function),
    )
    _apply_status(file_access, BAD_FUNCTION_STATUS)
    return BAD_FUNCTION_STATUS


def _ba998_free(file_access: FileAccess) -> None:
    """``ba998-Free`` [common/irsnominalMT.cbl:L1166-L1177].

    ``MySQL_free_result`` [:L1173-L1174] then ``set Cursor-Not-Active to true``
    [:L1177].

    Args:
        file_access: The linkage block, for the trace number.
    """
    _set_trace(file_access, "ba998-Free")
    _cursor_state().free()


# The bridge builds every predicate the same way.


_KEY: Final[KeyOfReference] = key_of_reference(TABLE, 1)

#: ``KeyName(KOR-x1)`` is ``pic x(30)``, and every `string` of it is ``delimited by
#: space`` [common/irsnominalMT.cbl:L406], so the trailing spaces of the declared width
#: never reach the statement.
_KEY_NAME: Final[str] = cobol_string_delimited_by_space(_KEY.key_name)

_QUOTED_TABLE: Final[str] = quote_identifier(TABLE)
_QUOTED_KEY: Final[str] = quote_identifier(_KEY_NAME)
_QUOTED_TYPE: Final[str] = quote_identifier(TYPE_COLUMN)

#: ``" ORDER BY " "`" keyname "`" " ASC "`` [common/irsnominalMT.cbl:L413-L418] -
#: present on the read-next and start predicates and ABSENT from the indexed one.
_ORDER_BY_KEY_ASC: Final[str] = f" ORDER BY {_QUOTED_KEY} ASC "


def _where_sequential() -> tuple[str, tuple[object, ...]]:
    """``ba040-Process-Read-Next``'s predicate [common/irsnominalMT.cbl:L404-L418].

    * the ``TIPE`` conjunct. The sequential read filters sub-nominal rows OUT IN SQL -
    ANOMALY A5, first half - so a plain ``SELECT *`` would return rows the frozen bridge
    never returns.

    Returns:
        The predicate text and its bound parameters.
    """
    predicate = (
        f"{_QUOTED_TYPE}=%s AND {_QUOTED_KEY} > %s{_ORDER_BY_KEY_ASC}"
    )
    return predicate, (SEQUENTIAL_TYPE_FILTER, SEQUENTIAL_LOW_KEY)


def _where_key_equal(nl: WsIrsnlRecord) -> tuple[str, tuple[object, ...]]:
    """The ``=`` predicate shared by read-indexed, delete and rewrite.

    ``string "`" KeyName "`" '="' WS-IRSNL-Record (K:L) '"'``
    [common/irsnominalMT.cbl:L558-L568, :L876-L887, :L1076-L1086].

    Args:
        nl: The record whose key positions the statement.

    Returns:
        The predicate text and its bound parameters.
    """
    return f"{_QUOTED_KEY}=%s", (_key_image(nl),)


def _where_start(
    nl: WsIrsnlRecord,
    access_type: int,
) -> tuple[str, tuple[object, ...]]:
    """``ba060-Process-Start``'s predicate [common/irsnominalMT.cbl:L690-L721].

    * ANOMALY A42 - the ``when 9`` arm is DEAD.

    Args:
        nl: The record whose key positions the statement.
        access_type: The relation selector, already validated.

    Returns:
        The predicate text and its bound parameters.
    """
    relation = cobol_string_delimited_by_space(
        start_relation_for(access_type, padded=True)
    )
    predicate = f"{_QUOTED_KEY}{relation}%s{_ORDER_BY_KEY_ASC}"
    return predicate, (_key_image(nl),)


def _where_delete_all(nl: WsIrsnlRecord) -> tuple[str, tuple[object, ...]]:
    """``ba085-Process-Delete-ALL``'s predicate [common/irsnominalMT.cbl:L1015-L1025].

    The paragraph first does ``move 9999999999 to NL-Key`` [:L1009], annotated "The last
    possible data", and then deletes everything strictly BELOW it.

    Args:
        nl: The record whose key is overwritten in place.

    Returns:
        The predicate text and its bound parameters.
    """
    _set_key_from_number(nl, int(DELETE_ALL_HIGH_KEY))
    return f"{_QUOTED_KEY}<%s", (DELETE_ALL_HIGH_KEY,)


def _select_statement(predicate: str) -> str:
    """``"SELECT * FROM " "`IRSNL-REC`" " WHERE " ws-Where(1:J) ";"``.

    [common/irsnominalMT.cbl:L427-L432, :L579-L587, :L734-L742]. ``SELECT *`` and not a
    column list, so the result's column order is the schema's - which is why
    :func:`_host_variables_from_row` keys on name and never on position.

    Args:
        predicate: The output of one of the ``_where_*`` builders.

    Returns:
        The statement text.
    """
    return f"SELECT * FROM {_QUOTED_TABLE} WHERE {predicate};"


def _delete_statement(predicate: str) -> str:
    """``"DELETE FROM " "`IRSNL-REC`" " WHERE " ws-Where(1:J) ";"``.

    Args:
        predicate: The output of one of the ``_where_*`` builders.

    Returns:
        The statement text.
    """
    return f"DELETE FROM {_QUOTED_TABLE} WHERE {predicate};"


def _bb200_insert_statement() -> str:
    """``bb200-Insert``'s statement [common/irsnominalMT.cbl:L1257-L1500].

    ``INSERT INTO `IRSNL-REC` SET `` then every column as ``` `COL`="value" ``` joined
    by ``", "``, then ``";"``.

    Returns:
        The statement text, with one placeholder per column in schema order.
    """
    assignments = ", ".join(f"{quote_identifier(column)}=%s" for column in COLUMNS)
    return f"INSERT INTO {_QUOTED_TABLE} SET {assignments};"


def _bb300_update_statement(predicate: str) -> str:
    """``bb300-Update``'s statement [common/irsnominalMT.cbl:L1505-L1747].

    ANOMALY A46 - the ``SET`` list carries ALL FIFTEEN COLUMNS INCLUDING THE PRIMARY KEY
    [:L1512 onward], so every update assigns ``KEY-1`` to the value it is simultaneously
    matching on in the ``WHERE``.

    Args:
        predicate: The output of :func:`_where_key_equal`.

    Returns:
        The statement text, with one placeholder per column plus the key.
    """
    assignments = ", ".join(f"{quote_identifier(column)}=%s" for column in COLUMNS)
    return (
        f"UPDATE {_QUOTED_TABLE} SET {assignments} WHERE {predicate.strip()};"
    )


def _rendered_parameters(host_variables: Mapping[str, object]) -> tuple[str, ...]:
    """Render the fifteen host variables into the text the bridge transmits.

    Args:
        host_variables: The output of :func:`_load_host_variables`.

    Returns:
        Fifteen strings. Never ``None`` for any column.
    """
    parameters: list[str] = []
    for column in COLUMNS:
        value = host_variables[column]
        if column == PRIMARY_KEY:
            parameters.append(_render_key(int(value) if isinstance(value, int) else 0))
        elif column in _MONEY_COLUMNS:
            parameters.append(_render_money(
                value if isinstance(value, Decimal) else _ZERO_MONEY, column
            ))
        elif column in _CHARACTER_COLUMNS:
            parameters.append(_render_character(
                value if isinstance(value, str) else "", column
            ))
        else:
            parameters.append(_render_integer(
                int(value) if isinstance(value, int) else 0, column
            ))
    return tuple(parameters)


# Only two things the handler does survive onto the RDB path, because its RDB branch
# leaves through `go to AA-Main-Exit` [common/acasirsub1.cbl:L267] before its own
# `evaluate File-Function` [:L286] is reached.


def _declared_record_length() -> int:
    """``length of WS-NL-Record``, and equally ``length of Record-1``.

    ``77 A`` receives the first [common/acasirsub1.cbl:L694-L696] and ``77 B`` the
    second [:L697-L699], and ``if A < B`` [:L700] then aborts. THE TEST CAN NEVER FIRE.

    Returns:
        The declared position count of the record.
    """
    total = 0
    for key in ("NL-Record.NL-Owning", "NL-Record.NL-Sub-Nominal"):
        total += int(loader.get_entry(key).copybook.digits or 0)
    for column in COLUMNS:
        if column in (PRIMARY_KEY, POINTER_COLUMN):
            continue
        field = _ENTRIES[column].copybook
        total += int(field.character_length or field.digits or 0)
    return total


def _record_size_gate(
    system: SystemRecord,
    file_access: FileAccess,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2`` [common/acasirsub1.cbl:L691-L731].

    Once-only, latched on ``if A = zero`` [:L693], and it does two unrelated jobs in
    that one guarded block.

    Args:
        system: ``SYSTEM-REC``, the first linkage parameter.
        file_access: The linkage block, whose ``RDB-Data`` is filled.

    Returns:
        True when the bridge may be called; False when the gate aborted, which means the
            caller must return the status pair without calling it.
    """
    if _STORAGE.record_size_a == 0:
        _STORAGE.record_size_a = _declared_record_length()
        _STORAGE.record_size_b = _declared_record_length()
        if _STORAGE.record_size_a < _STORAGE.record_size_b:
            _LOG.error(
                "acasirsub1 ba012: IR902 record size mismatch, "
                "WS-NL-Record=%s Record-1=%s",
                _STORAGE.record_size_a,
                _STORAGE.record_size_b,
            )
            _apply_status(file_access, RECORD_SIZE_STATUS)
            return False
        rdb_data: RdbData = load_rdb_data_once(system)
        file_access.rdb_data = rdb_data
    return True


def _key_number_guard(file_access: FileAccess) -> tuple[int, int] | None:
    """``evaluate File-Function`` at [common/acasirsub1.cbl:L231-L245].

    Two codes for one condition is the anomaly; there is one key on this table
    [common/irsnominalMT.cbl:L147], so 1 is the only legal value either way.

    Args:
        file_access: The linkage block carrying the function and key number.

    Returns:
        The rejecting status pair, or ``None`` when the call may proceed.
    """
    function = file_access.file_function
    key_number = file_access.logging_data.file_key_no
    if key_number == KEY_COUNT:
        return None
    if function in (int(FileFunction.READ_INDEXED), int(FileFunction.START)):
        _apply_status(file_access, KEY_NUMBER_STATUS)
        return KEY_NUMBER_STATUS
    if function == int(FileFunction.DELETE):
        _apply_status(file_access, DELETE_KEY_NUMBER_STATUS)
        return DELETE_KEY_NUMBER_STATUS
    # Every other function code reaches neither arm, so a wrong key number is simply not
    # noticed - the `evaluate` has no `when other` [common/acasirsub1.cbl:L245].
    return None


def _aa047_eval_keys(file_access: FileAccess, nl: WsIrsnlRecord) -> None:
    """``aa047-Eval-Keys`` [common/acasirsub1.cbl:L463-L479]. DEAD CODE.

    ANOMALY A31 - this paragraph is unreachable. Its ONLY reference anywhere is a
    ``perform`` that is commented out [common/acasirsub1.cbl:L490], and the maintainer's
    own comment ten lines above it says so.

    Args:
        file_access: The linkage block whose log key is written.
        nl: The record supplying the key.
    """
    if file_access.file_function in (
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.RE_WRITE),
        int(FileFunction.DELETE),
        int(FileFunction.START),
    ):
        if file_access.logging_data.file_key_no == KEY_COUNT:
            _move_to_log_field(file_access, "ws_file_key", _key_image(nl))
        else:
            _move_to_log_field(file_access, "ws_file_key", "")
    else:
        _move_to_log_field(file_access, "ws_file_key", "")


# `MYSQL-1210-COMMAND` issues the statement and every guarded arm that follows it has
# the identical shape.


def _fill_log_field(file_access: FileAccess, attribute: str, character: str) -> None:
    """``move <figurative constant> to <field>``.

    A figurative constant moved to an alphanumeric item repeats to fill the receiving
    width, so ``move zero to SQL-Err`` on ``pic x(5)`` yields five zero characters and
    not one.

    Args:
        file_access: The linkage block to write.
        attribute: The ``Logging-Data`` field.
        character: The single character to repeat.
    """
    setattr(
        file_access.logging_data,
        attribute,
        character * _LOGGING_WIDTHS[attribute],
    )


def _require_connection(
    file_access: FileAccess,
    command: str,
) -> DbErrorStatus | None:
    """Return the mapped failure when no connection has been opened.

    The frozen bridge does not check.

    Args:
        file_access: The linkage block to write on failure.
        command: The statement that was about to be issued.

    Returns:
        The mapped failure, or ``None`` when a connection is held.
    """
    if _STORAGE.connection is not None:
        return None
    status = mysql_1100_db_error(
        errno=str(int(WeError.RDB_INIT_ERROR)),
        message="no connection: MYSQL-1000-OPEN has not run",
        sql_state="",
        command=command,
        we_error=int(WeError.RDB_INIT_ERROR),
    )
    _apply_driver_status(file_access, status)
    return status


def _driver_reported_error(failure: DbErrorStatus | None) -> bool:
    """``if WS-MYSQL-Error-Number not = "0 "``.

    Every guarded arm in the bridge tests the errno before it writes a status
    [common/irsnominalMT.cbl:L448, :L622, :L751, :L907, :L1051, :L1096], and the
    comparison is against the three-character literal ``"0 "`` -
    :data:`NO_DRIVER_ERROR`.

    Args:
        failure: The mapped failure, or ``None`` when the statement ran cleanly.

    Returns:
        True when the driver reported an error number other than ``"0 "``.
    """
    if failure is None:
        return False
    return failure.sql_err.strip() != NO_DRIVER_ERROR.strip()


def _run_query(
    file_access: FileAccess,
    statement: str,
    parameters: tuple[object, ...],
) -> tuple[list[dict[str, object]], DbErrorStatus | None]:
    """Issue a ``SELECT`` and store the whole result.

    Args:
        file_access: The linkage block, whose ``WS-Log-Where`` records the text.
        statement: The statement text, identifiers already quoted.
        parameters: The bound values.

    Returns:
        The rows and ``None``, or an empty list and the mapped failure.
    """
    failure = _require_connection(file_access, statement)
    if failure is not None:
        return [], failure
    try:
        with execute_statement(
            _STORAGE.connection, statement, parameters
        ) as cursor:
            rows = _fetch_all_rows(cursor)
    except Exception as error:
        return [], _driver_failure(
            error,
            command=statement,
            file_function=file_access.file_function,
        )
    return rows, None


def _run_update(
    file_access: FileAccess,
    statement: str,
    parameters: tuple[object, ...],
) -> tuple[int, DbErrorStatus | None]:
    """Issue an ``INSERT``, ``UPDATE`` or ``DELETE``.

    Args:
        file_access: The linkage block.
        statement: The statement text, identifiers already quoted.
        parameters: The bound values.

    Returns:
        ``WS-MYSQL-Count-Rows`` and ``None``, or zero and the mapped failure.
    """
    failure = _require_connection(file_access, statement)
    if failure is not None:
        return 0, failure
    try:
        with execute_statement(
            _STORAGE.connection, statement, parameters
        ) as cursor:
            affected = _affected_rows(cursor)
    except Exception as error:
        return 0, _driver_failure(
            error,
            command=statement,
            file_function=file_access.file_function,
        )
    return affected, None


def _bb200_insert(
    file_access: FileAccess,
    host_variables: Mapping[str, object],
) -> tuple[int, DbErrorStatus | None]:
    """``bb200-Insert`` [common/irsnominalMT.cbl:L1257-L1503].

    Args:
        file_access: The linkage block.
        host_variables: The output of :func:`_load_host_variables`.

    Returns:
        The affected-row count and the mapped failure, if any.
    """
    statement = _bb200_insert_statement()
    _move_to_log_field(file_access, "ws_log_where", statement)
    return _run_update(file_access, statement, _rendered_parameters(host_variables))


def _bb300_update(
    file_access: FileAccess,
    host_variables: Mapping[str, object],
    nl: WsIrsnlRecord,
) -> tuple[int, DbErrorStatus | None]:
    """``bb300-Update`` [common/irsnominalMT.cbl:L1505-L1747].

    Args:
        file_access: The linkage block.
        host_variables: The output of :func:`_load_host_variables`.
        nl: The record, for the ``WHERE`` key image.

    Returns:
        The affected-row count and the mapped failure, if any.
    """
    predicate, key_parameters = _where_key_equal(nl)
    statement = _bb300_update_statement(predicate)
    _move_to_log_field(file_access, "ws_log_where", statement)
    parameters = _rendered_parameters(host_variables) + key_parameters
    return _run_update(file_access, statement, parameters)


def open_(
    system: SystemRecord,
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """``ba020-Process-Open`` [common/irsnominalMT.cbl:L330-L372].

    The paragraph strings the six ``RDB-Data`` fields into the ``WS-MYSQL-*`` names
    [:L335-L358], sets its trace number [:L359], performs ``MYSQL-1000-OPEN THRU
    MYSQL-1090-EXIT`` [:L360], and returns early on a non-zero reply [:L361-L362].

    Args:
        system: ``SYSTEM-REC``, which carries the connection parameters.
        file_access: The linkage block.
        nl: The record. Not read - accepted so that every verb takes the bridge's own
            ``USING`` shape.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    del nl
    _set_trace(file_access, "ba020-Process-Open")
    outcome: OpenOutcome = mysql_1090_exit_paragraph(
        mysql_1000_open(
            system,
            ws_no_paragraph=file_access.logging_data.ws_no_paragraph,
            we_error=file_access.we_error,
            transport=_STORAGE.transport,
        )
    )
    file_access.logging_data.ws_no_paragraph = outcome.ws_no_paragraph
    file_access.fs_reply = outcome.fs_reply
    file_access.we_error = outcome.we_error
    _move_to_log_field(file_access, "sql_err", outcome.sql_err)
    _move_to_log_field(file_access, "sql_msg", outcome.sql_msg)
    _move_to_log_field(file_access, "sql_state", outcome.sql_state)
    if outcome.fs_reply != int(FsReply.SUCCESS):
        return (file_access.fs_reply, file_access.we_error)
    _STORAGE.connection = outcome.connection
    _move_to_log_field(file_access, "ws_file_key", _OPEN_TAG)
    _cursor_state().set_cursor_not_active()
    return (file_access.fs_reply, file_access.we_error)


def open_input(
    system: SystemRecord,
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """The facade's ``-Open-Input`` verb.

    The facade sets ``access-type`` and then the function code [copybooks/Proc-ACAS-FH-
    Calls.cob:L465-L469]; the BRIDGE ignores the access type on an open, because its
    ``when 1`` arm routes every open to the one paragraph
    [common/irsnominalMT.cbl:L303].

    Args:
        system: ``SYSTEM-REC``.
        file_access: The linkage block, whose access type is set.
        nl: The record. Not read.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    file_access.access_type = int(AccessType.INPUT)
    return open_(system, file_access, nl)


def open_extend(
    system: SystemRecord,
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """The facade's ``-Open-Extend`` verb.

    ANOMALY, recorded rather than reproduced: the HANDLER rejects extend outright,
    ``move 997 to WE-Error`` and ``move 99 to fs-reply``
    [common/acasirsub1.cbl:L354-L355], but that arm is inside ``aa020-Process-Open`` and
    therefore on the indexed-file path.

    Args:
        system: ``SYSTEM-REC``.
        file_access: The linkage block, whose access type is set.
        nl: The record. Not read.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    file_access.access_type = int(AccessType.EXTEND)
    return open_(system, file_access, nl)


def open_output(
    system: SystemRecord,
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """``ba015-Test-Ends`` [common/acasirsub1.cbl:L733-L742] - TWO bridge calls.

    The ``perform`` is of the paragraph the code then FALLS INTO, so the bridge is
    entered twice: once with the open, once with function 6.

    Args:
        system: ``SYSTEM-REC``.
        file_access: The linkage block, whose function code ends as 6.
        nl: The record. Its key is overwritten by the delete-all sweep and NOT restored,
            exactly as the frozen paragraph leaves it.

    Returns:
        The ``(FS-Reply, We-Error)`` pair of the SECOND call.
    """
    file_access.access_type = int(AccessType.OUTPUT)
    # `perform ba020-Process-Dal` [common/acasirsub1.cbl:L740] - CALL one, with the
    # function still Open.
    file_access.file_function = int(FileFunction.OPEN)
    _bridge_call(system, file_access, nl)
    file_access.file_function = int(FileFunction.DELETE_ALL)
    return _bridge_call(system, file_access, nl)


def close(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba030-Process-Close`` [common/irsnominalMT.cbl:L374-L387].

    Args:
        file_access: The linkage block.
        nl: The record. Not read.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    del nl
    state = _cursor_state()
    if state.cursor_active():
        _ba998_free(file_access)
    _set_trace(file_access, "ba030-Process-Close")
    _move_to_log_field(file_access, "ws_file_key", _CLOSE_TAG)
    mysql_1980_close(_STORAGE.connection)
    mysql_1999_exit_paragraph()
    _STORAGE.connection = None
    return (file_access.fs_reply, file_access.we_error)


def _ba041_reread(
    file_access: FileAccess,
    nl: WsIrsnlRecord,
    *,
    filter_sub_nominal: bool,
) -> tuple[int, int]:
    """``ba041-Reread`` [common/irsnominalMT.cbl:L469-L547].

    Three separate end-of-data paths, all answering ``(10, 3)`` and distinguishable only
    by the log tag they leave - ANOMALY A47, and :data:`END_OF_DATA_TAGS` lists all four
    including ``ba040``'s.

    Args:
        file_access: The linkage block.
        nl: The record, filled in place on success.
        filter_sub_nominal: True for the ordinary read, which skips ``"S"`` records;
            False for the raw read, whose two filter lines are commented out
            [common/acasirsub1.cbl:L454-L455].

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    state = _cursor_state()
    while True:
        # `move spaces to WS-Log-Where` [:L473] - the fetch issues no statement, so the
        # predicate that positioned the cursor is cleared rather than left to look as
        # though it had just run.
        _move_to_log_field(file_access, "ws_log_where", "")
        _set_trace(file_access, "ba041-Reread")

        row = state.fetch_record()
        if row is None:
            _apply_status(file_access, END_OF_FILE_STATUS)
            _move_to_log_field(file_access, "ws_file_key", END_OF_DATA_TAGS[1])
            state.set_cursor_not_active()
            return END_OF_FILE_STATUS

        # `if WS-MYSQL-Count-Rows = zero` [:L512-L528] guards a driver failure DURING
        # the fetch and leaves the tag "EOF2" plus `initialize WS-IRSNL-Record with
        # filler` [:L524].
        if file_access.fs_reply == int(FsReply.END_OF_FILE):
            state.set_cursor_not_active()
            _move_to_log_field(file_access, "ws_file_key", END_OF_DATA_TAGS[3])
            return END_OF_FILE_STATUS

        _unload_host_variables(row, nl)

        if filter_sub_nominal and _sub(nl):
            continue

        _move_to_log_field(file_access, "ws_file_key", _render_key(_key_number(nl)))
        _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
        return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


def read_next(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba040-Process-Read-Next`` [common/irsnominalMT.cbl:L389-L467].

    Positions once and then walks. ANOMALY A5 - the predicate excludes sub-nominal rows,
    so THIS VERB CAN NEVER RETURN ONE, however many the table holds.

    Args:
        file_access: The linkage block.
        nl: The record, filled in place on success.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    state = _cursor_state()
    if state.cursor_not_active():
        predicate, parameters = _where_sequential()
        _set_trace(file_access, "ba040-Process-Read-Next")
        statement = _select_statement(predicate)
        _move_to_log_field(file_access, "ws_log_where", statement)
        rows, failure = _run_query(file_access, statement, parameters)
        _move_to_log_field(file_access, "ws_file_key", f"> {SEQUENTIAL_LOW_KEY}")
        count = state.store_result(rows)
        if count == 0:
            # `if WS-MYSQL-Count-Rows = zero` [:L443-L457].
            if _driver_reported_error(failure):
                _apply_driver_status(file_access, failure)
            _apply_status(file_access, END_OF_FILE_STATUS)
            _move_to_log_field(file_access, "ws_file_key", END_OF_DATA_TAGS[0])
            return END_OF_FILE_STATUS
        state.set_cursor_active()
        state.position_at(SEQUENTIAL_LOW_KEY)
        _move_to_log_field(
            file_access, "ws_file_key", f"> 0 got cnt={count} recs"
        )
    return _ba041_reread(file_access, nl, filter_sub_nominal=True)


def read_next_raw(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``aa045-Process-Read-Next-Raw`` [common/acasirsub1.cbl:L421-L459], on SQL.

    This function is therefore the traceable counterpart of ``aa045``, reachable only by
    a direct call, and it is what the raw read WOULD be on SQL: both filters absent.

    Args:
        file_access: The linkage block.
        nl: The record, filled in place on success.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    state = _cursor_state()
    if state.cursor_not_active():
        predicate = f"{_QUOTED_KEY} > %s{_ORDER_BY_KEY_ASC}"
        _set_trace(file_access, "ba040-Process-Read-Next")
        statement = _select_statement(predicate)
        _move_to_log_field(file_access, "ws_log_where", statement)
        rows, failure = _run_query(
            file_access, statement, (SEQUENTIAL_LOW_KEY,)
        )
        _move_to_log_field(file_access, "ws_file_key", f"> {SEQUENTIAL_LOW_KEY}")
        count = state.store_result(rows)
        if count == 0:
            if _driver_reported_error(failure):
                _apply_driver_status(file_access, failure)
            _apply_status(file_access, END_OF_FILE_STATUS)
            _move_to_log_field(
                file_access, "ws_file_key", "Read Raw failure on IRS NL File"
            )
            return END_OF_FILE_STATUS
        state.set_cursor_active()
        state.position_at(SEQUENTIAL_LOW_KEY)
    # `*> if Sub` / `*> go to aa041-Reread.` [common/acasirsub1.cbl:L454-L455] are
    # commented out, so the record-level filter is absent as well.
    return _ba041_reread(file_access, nl, filter_sub_nominal=False)


def read_indexed(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba050-Process-Read-Indexed`` [common/irsnominalMT.cbl:L549-L663].

    ``NL-Pointer`` is the first five characters of the name
    [copybooks/irswsnl.cob:L22-L23], so the account number the chase follows is read out
    of the NAME FIELD of the row just fetched.

    Args:
        file_access: The linkage block.
        nl: The record.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    state = _cursor_state()
    while True:
        predicate, parameters = _where_key_equal(nl)
        _set_trace(file_access, "ba050-Process-Read-Indexed")
        statement = _select_statement(predicate)
        _move_to_log_field(file_access, "ws_log_where", statement)
        rows, failure = _run_query(file_access, statement, parameters)
        count = state.store_result(rows)
        if count == 0:
            # `if WS-MYSQL-Count-Rows = zero` [:L590-L593]. The maintainer's own comment
            # on the 21 is "could also be 23 or 14", so the choice is his.
            _apply_status(file_access, NOT_FOUND_STATUS)
            _ba998_free(file_access)
            return NOT_FOUND_STATUS

        _set_trace(file_access, "ba050-Fetch")
        row = state.fetch_record()
        if row is None:
            _apply_status(file_access, NOT_FOUND_STATUS)
            if _driver_reported_error(failure):
                _apply_driver_status(file_access, failure)
                _apply_status(file_access, NOT_FOUND_STATUS)
                _move_to_log_field(file_access, "ws_file_key", "")
                _set_name(nl, NOT_FOUND_LITERALS[0])
            else:
                _fill_log_field(file_access, "sql_err", "0")
                _set_name(nl, NOT_FOUND_LITERALS[1])
                _move_to_log_field(file_access, "sql_msg", "")
                _move_to_log_field(file_access, "ws_file_key", "")
            _ba998_free(file_access)
            return NOT_FOUND_STATUS

        _unload_host_variables(row, nl)
        _move_to_log_field(file_access, "ws_file_key", _render_key(_key_number(nl)))

        if _sub(nl):
            # THE CHASE [:L653-L660], in the frozen order.
            owning = nl.nl_key.nl_owning
            nl.nl_key.nl_sub_nominal = owning
            nl.nl_key.nl_owning = _read_pointer_overlay(nl)
            _set_name(nl, NOT_FOUND_LITERALS[2])
            continue

        _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
        _ba998_free(file_access)
        return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


def start(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba060-Process-Start`` [common/irsnominalMT.cbl:L665-L777].

    so one invocation positions the cursor AND returns the first qualifying record, and
    the caller's record buffer comes back filled. And because it lands in ``ba041``
    rather than anywhere else, THE SUB-NOMINAL FILTER APPLIES TO A START.

    Args:
        file_access: The linkage block, carrying the access type.
        nl: The record, whose key positions the cursor and which is filled in place by
            the read that follows.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    access_type = file_access.access_type
    if not start_access_type_is_valid(access_type):
        _apply_status(file_access, ACCESS_TYPE_STATUS)
        return ACCESS_TYPE_STATUS

    state = _cursor_state()
    if state.cursor_active():
        # `if Cursor-Active / perform ba998-Free.` [:L680-L681] - closed by the period
        # with no `end-if`, one of the several such sites ANOMALY A35 records.
        _ba998_free(file_access)

    predicate, parameters = _where_start(nl, access_type)
    statement = _select_statement(predicate)
    _move_to_log_field(file_access, "ws_log_where", statement)
    _move_to_log_field(file_access, "ws_file_key", _render_key(_key_number(nl)))
    _set_trace(file_access, "ba060-Process-Start")

    rows, failure = _run_query(file_access, statement, parameters)
    count = state.store_result(rows)
    if count != 0:
        state.set_cursor_active()
        state.position_at(parameters[0])
        _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
        relation = cobol_string_delimited_by_space(
            start_relation_for(access_type, padded=True)
        )
        _move_to_log_field(
            file_access,
            "ws_file_key",
            f"{relation}{parameters[0]} got ={count} recs",
        )
    elif _driver_reported_error(failure):
        _apply_driver_status(file_access, failure)
        _apply_status(file_access, NOT_FOUND_STATUS)
        return NOT_FOUND_STATUS

    return _ba041_reread(file_access, nl, filter_sub_nominal=True)


def rewrite(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba090-Process-Rewrite`` [common/irsnominalMT.cbl:L1068-L1114].

    ONE statement, no pointer handling of any kind. ANOMALY A13 - and the asymmetry
    among the three mutating verbs is the point.

    Args:
        file_access: The linkage block.
        nl: The record to store.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    host_variables = _load_host_variables(nl)
    _set_trace(file_access, "ba090-Process-Rewrite")
    affected, failure = _bb300_update(file_access, host_variables, nl)
    if affected != 1:
        if _driver_reported_error(failure):
            _apply_driver_status(file_access, failure)
            _apply_status(
                file_access,
                (int(FsReply.ERROR), REWRITE_FAILED_WE_ERROR),
            )
        return (file_access.fs_reply, file_access.we_error)
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
    _fill_log_field(file_access, "sql_err", "0")
    _move_to_log_field(file_access, "sql_msg", "")
    return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


# A single `fn-write` runs three paragraphs by fall-through and can issue FOUR SQL
# statements: 1. `bb200-Insert` [:L793] INSERT the record as passed 2.


def _ba070_process_write(
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """``ba070-Process-Write`` [common/irsnominalMT.cbl:L783-L813].

    Statement one: load the host variables and insert. ANOMALY A11 - THIS ARM SETS ONLY
    ``FS-Reply``.

    Args:
        file_access: The linkage block.
        nl: The record to insert.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    host_variables = _load_host_variables(nl)
    _move_to_log_field(file_access, "ws_file_key", _render_key(_key_number(nl)))
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
    _move_to_log_field(file_access, "sql_msg", "")
    _fill_log_field(file_access, "sql_err", "0")
    _set_trace(file_access, "ba070-Process-Write")
    affected, failure = _bb200_insert(file_access, host_variables)
    if affected != 1 and _driver_reported_error(failure):
        _move_to_log_field(file_access, "sql_state", failure.sql_state)
        _move_to_log_field(file_access, "sql_err", failure.sql_err)
        _move_to_log_field(file_access, "sql_msg", failure.sql_msg)
        # `if SQL-Err (1:4) = "1062" or = "1022" or Sql-State = "23000"` [:L805-L808] -
        # the BRIDGE-level duplicate test, on the copied text rather than on the
        # driver's own error number.
        if is_duplicate_key_bridge_level(
            file_access.logging_data.sql_err,
            file_access.logging_data.sql_state,
        ):
            file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
        else:
            file_access.fs_reply = int(FsReply.ERROR)
    return (file_access.fs_reply, file_access.we_error)


def _ba072_proc_write_subs(
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int] | None:
    """``ba072-Proc-Write-Subs`` [common/irsnominalMT.cbl:L815-L852].

    An owning row with no sub-nominal and NO NAME is rewritten as type ``"S"`` and the
    write ends there - one insert and one update, and the row now claims to be a sub-
    nominal.

    Args:
        file_access: The linkage block.
        nl: The record, mutated in place.

    Returns:
        The pair when the write ends here, or ``None`` to fall through into ``ba073-Fix-
            Up-Subs``.
    """
    if is_duplicate_key_bridge_level(
        file_access.logging_data.sql_err,
        file_access.logging_data.sql_state,
    ) or file_access.fs_reply == int(FsReply.DUPLICATE_KEY):
        #  THE KEY IS NOT LOGGED. The frozen `display` shows the LITERAL
        #  ALONE - `display IR90n at 2401 with foreground-color 4` - so naming
        #  the record added a business key the frozen source never showed, and
        #  `NL-KEY` identifies a nominal account (CWE-532). The caller already
        #  holds the record it passed in.
        _LOG.error(
            "irsnominalMT ba072: IR906 Link/record exists on owning write"
        )

    if (
        _owner(nl)
        and nl.nl_key.nl_sub_nominal == 0
        and nl.nl_type == TYPE_OWNER
        and _character_image(nl.nl_data.nl_name, _NAME_WIDTH).strip() == ""
    ):
        nl.nl_type = TYPE_SUB
        rewrite(file_access, nl)
        return (file_access.fs_reply, file_access.we_error)

    if _owner(nl):
        return (file_access.fs_reply, file_access.we_error)

    nl.nl_type = TYPE_OWNER
    rewrite(file_access, nl)
    if file_access.we_error == REWRITE_FAILED_WE_ERROR:
        #  THE KEY IS NOT LOGGED. The frozen `display` shows the LITERAL
        #  ALONE - `display IR90n at 2401 with foreground-color 4` - so naming
        #  the record added a business key the frozen source never showed, and
        #  `NL-KEY` identifies a nominal account (CWE-532). The caller already
        #  holds the record it passed in.
        _LOG.error(
            "irsnominalMT ba072: IR907 Link/record exists on rewrite (S->O)"
        )

    if nl.nl_key.nl_sub_nominal == 0:
        return (file_access.fs_reply, file_access.we_error)

    owning = nl.nl_key.nl_owning
    _apply_pointer_overlay(nl, owning)
    nl.nl_key.nl_owning = nl.nl_key.nl_sub_nominal
    nl.nl_key.nl_sub_nominal = 0
    return None


def _ba073_fix_up_subs(
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """``ba073-Fix-Up-Subs`` [common/irsnominalMT.cbl:L854-L868].

    ``move "S" to NL-Tipe`` [:L855] then ``perform ba070-Process-Write`` [:L856] - a
    PERFORM of the first paragraph of the chain, which ends at [:L813], so only the load
    and the insert re-run and the fall-through does NOT recurse.

    Args:
        file_access: The linkage block.
        nl: The record, mutated in place.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    nl.nl_type = TYPE_SUB
    _ba070_process_write(file_access, nl)
    if is_duplicate_key_bridge_level(
        file_access.logging_data.sql_err,
        file_access.logging_data.sql_state,
    ) or file_access.fs_reply == int(FsReply.DUPLICATE_KEY):
        #  THE KEY IS NOT LOGGED. The frozen `display` shows the LITERAL
        #  ALONE - `display IR90n at 2401 with foreground-color 4` - so naming
        #  the record added a business key the frozen source never showed, and
        #  `NL-KEY` identifies a nominal account (CWE-532). The caller already
        #  holds the record it passed in.
        _LOG.error(
            "irsnominalMT ba073: IR908 link/record exists on sub write"
        )

    if file_access.fs_reply != int(FsReply.SUCCESS):
        # ANOMALY A44 - the "JIC" fourth statement [:L862-L865].
        rewrite(file_access, nl)

    nl.nl_key.nl_sub_nominal = nl.nl_key.nl_owning
    nl.nl_key.nl_owning = _read_pointer_overlay(nl)
    return (file_access.fs_reply, file_access.we_error)


def write(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``fn-write`` - the three-paragraph fall-through chain.

    ``ba070-Process-Write`` [common/irsnominalMT.cbl:L783] ends and ``ba072-Proc-Write-
    Subs`` [:L815] begins, which ends and ``ba073-Fix-Up-Subs`` [:L854] begins.

    Args:
        file_access: The linkage block.
        nl: The record. MUTATED - see :func:`_ba073_fix_up_subs`.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    _ba070_process_write(file_access, nl)
    ended = _ba072_proc_write_subs(file_access, nl)
    if ended is not None:
        return ended
    return _ba073_fix_up_subs(file_access, nl)


def write_raw(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba170-Process-Write-Raw`` [common/irsnominalMT.cbl:L1120-L1152].

    ``TWO SEPARATE STATEMENTS``, in that order. It is deliberately NOT expressed as a
    single upsert statement.

    Args:
        file_access: The linkage block.
        nl: The record to store. NOT mutated - this verb has no key mutation.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    host_variables = _load_host_variables(nl)
    _move_to_log_field(file_access, "ws_file_key", _render_key(_key_number(nl)))
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
    _move_to_log_field(file_access, "sql_msg", "")
    _fill_log_field(file_access, "sql_err", "0")
    _set_trace(file_access, "ba170-Process-Write-Raw")
    affected, failure = _bb200_insert(file_access, host_variables)
    if affected != 1 and _driver_reported_error(failure):
        _move_to_log_field(file_access, "sql_state", failure.sql_state)
        _move_to_log_field(file_access, "sql_err", failure.sql_err)
        _move_to_log_field(file_access, "sql_msg", failure.sql_msg)
        if is_duplicate_key_bridge_level(
            file_access.logging_data.sql_err,
            file_access.logging_data.sql_state,
        ):
            file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
        else:
            file_access.fs_reply = int(FsReply.ERROR)
        #  THE KEY IS NOT LOGGED. The frozen `display` shows the LITERAL
        #  ALONE - `display IR90n at 2401 with foreground-color 4` - so naming
        #  the record added a business key the frozen source never showed, and
        #  `NL-KEY` identifies a nominal account (CWE-532). The caller already
        #  holds the record it passed in.
        _LOG.error(
            "irsnominalMT ba170: IR909 Link/record exists on owning write, "
            "rewriting"
        )
    if file_access.fs_reply != int(FsReply.SUCCESS):
        rewrite(file_access, nl)
        if file_access.we_error == REWRITE_FAILED_WE_ERROR:
            _LOG.error("irsnominalMT ba170: IR910 Rewrite failed as well")
    return (file_access.fs_reply, file_access.we_error)


def delete(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba080-Process-Delete`` [common/irsnominalMT.cbl:L870-L985].

    ANOMALY A12 - TWO ``DELETE`` STATEMENTS for one logical delete: the row itself
    [:L899-L905], and then, for anything that is not an owning account, the pointer row
    under a mutated key [:L960-L966].

    Args:
        file_access: The linkage block.
        nl: The record whose key selects the row. MUTATED and not restored.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    predicate, parameters = _where_key_equal(nl)
    statement = _delete_statement(predicate)
    _move_to_log_field(file_access, "ws_log_where", statement)
    _move_to_log_field(file_access, "ws_file_key", _render_key(_key_number(nl)))
    _set_trace(file_access, "ba080-Process-Delete")
    affected, failure = _run_update(file_access, statement, parameters)
    if affected != 1:
        if _driver_reported_error(failure):
            _apply_driver_status(file_access, failure)
            _apply_status(
                file_access,
                (int(FsReply.ERROR), DELETE_FAILED_WE_ERROR),
            )
        # `go to ba999-End` [:L918] - unconditional, so a clean no-op delete returns
        # here with whatever status it arrived with.
        return (file_access.fs_reply, file_access.we_error)
    _move_to_log_field(file_access, "sql_msg", "")
    _move_to_log_field(file_access, "sql_state", "")
    _fill_log_field(file_access, "sql_err", "0")
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))

    if _owner(nl):
        return (int(FsReply.SUCCESS), int(WeError.SUCCESS))

    # `move NL-Sub-Nominal to NL-Owning` [:L935] then `move zero to NL-Sub-Nominal`
    # [:L936]. Note that this is NOT the write path's mutation.
    nl.nl_key.nl_owning = nl.nl_key.nl_sub_nominal
    nl.nl_key.nl_sub_nominal = 0

    _set_trace(file_access, "ba080-Delete-Pointer")
    pointer_predicate, pointer_parameters = _where_key_equal(nl)
    pointer_statement = _delete_statement(pointer_predicate)
    _move_to_log_field(file_access, "ws_log_where", pointer_statement)
    pointer_affected, pointer_failure = _run_update(
        file_access, pointer_statement, pointer_parameters
    )
    if pointer_affected != 1 and _driver_reported_error(pointer_failure):
        _apply_driver_status(file_access, pointer_failure)
        _apply_status(file_access, (int(FsReply.ERROR), DELETE_FAILED_WE_ERROR))
        return (file_access.fs_reply, file_access.we_error)
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
    return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


def delete_all(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba085-Process-Delete-ALL`` [common/irsnominalMT.cbl:L987-L1066].

    The paragraph's own header calls it what it is: "THIS IS NON STANDARD". It exists so
    that opening the table for output can mean what opening an indexed file for output
    means - see :func:`open_output`.

    Args:
        file_access: The linkage block.
        nl: The record. ITS KEY IS OVERWRITTEN WITH TEN NINES and not restored.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    predicate, parameters = _where_delete_all(nl)
    statement = _delete_statement(predicate)
    _move_to_log_field(file_access, "ws_log_where", statement)
    _move_to_log_field(
        file_access,
        "ws_file_key",
        f"Deleting back from {_render_key(_key_number(nl))}",
    )
    _set_trace(file_access, "ba085-Process-Delete-ALL")
    affected, failure = _run_update(file_access, statement, parameters)
    if affected <= 0:
        if _driver_reported_error(failure):
            _apply_driver_status(file_access, failure)
            _apply_status(
                file_access,
                (int(FsReply.ERROR), DELETE_FAILED_WE_ERROR),
            )
            return (file_access.fs_reply, file_access.we_error)
    else:
        _move_to_log_field(file_access, "sql_msg", "")
        _fill_log_field(file_access, "sql_err", "0")
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
    return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


def _bridge_call(
    system: SystemRecord,
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """One entry into ``irsnominalMT``: ``ba010-Initialise`` then the dispatch.

    Note the blank line inside the parameter list - the family's habit - and note the
    PARAMETER-NAME MISMATCH.

    Args:
        system: ``SYSTEM-REC``, needed by the open.
        file_access: The linkage block.
        nl: The record.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    _ba010_initialise(file_access)
    function = file_access.file_function
    if function == int(FileFunction.OPEN):
        return open_(system, file_access, nl)
    if function == int(FileFunction.CLOSE):
        return close(file_access, nl)
    if function == int(FileFunction.READ_NEXT):
        return read_next(file_access, nl)
    if function == int(FileFunction.READ_INDEXED):
        return read_indexed(file_access, nl)
    if function == int(FileFunction.WRITE):
        return write(file_access, nl)
    if function == int(FileFunction.DELETE_ALL):
        # `when 6 *> special to cleardown all data` [:L314-L317] - ANOMALY A28,
        # dispatched by the bridge and by no handler.
        return delete_all(file_access, nl)
    if function == int(FileFunction.RE_WRITE):
        return rewrite(file_access, nl)
    if function == int(FileFunction.DELETE):
        return delete(file_access, nl)
    if function == int(FileFunction.START):
        return start(file_access, nl)
    if function == int(FileFunction.WRITE_RAW):
        return write_raw(file_access, nl)
    # `when other / go to ba100-Bad-Function` [:L325-L327]. Function 13 lands here -
    # ANOMALY A40 - and so does anything the facade should never send.
    return _ba100_bad_function(file_access)


def dispatch(
    system: SystemRecord,
    nl: WsIrsnlRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> tuple[int, int]:
    """``acasirsub1``'s entry point [common/acasirsub1.cbl:L211-L217].

    so that a reviewer can diff this signature against the frozen one - which is the
    contract AAP section 0.4.3 sets for every handler call.

    Args:
        system: ``SYSTEM-REC``.
        nl: ``WS-NL-Record``. Several verbs MUTATE it; each says so.
        file_access: ``File-Access``, carrying the function code, the access type,
            ``File-Key-No`` and every status and log field.
        file_defs: ``File-Defs``. Accepted and never read, because the RDB path has no
            file name to resolve - the table name is a literal in the bridge.
        dal_common: ``ACAS-DAL-Common-data``, whose ``SW-Testing`` gates the FH logger
            [common/acasirsub1.cbl:L209].

    Returns:
        The ``(FS-Reply, We-Error)`` pair, written into ``file_access`` as well as
            returned.
    """
    del file_defs

    file_access.logging_data.ws_log_system = WS_LOG_SYSTEM
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT

    # 2. The key-number guard [:L231-L245].
    rejected = _key_number_guard(file_access)
    if rejected is not None:
        return rejected

    open_for_output = file_access.file_function == int(
        FileFunction.OPEN
    ) and file_access.access_type == int(AccessType.OUTPUT)
    if not open_for_output:
        statuses = system.system_data_block.rdbms_flat_statuses
        file_access.fa_rdbms_flat_statuses.fa_file_system_used = (
            statuses.file_system_used
        )
        file_access.fa_rdbms_flat_statuses.fa_file_duplicates_in_use = (
            statuses.file_duplicates_in_use
        )

    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB

    if not _record_size_gate(system, file_access):
        return RECORD_SIZE_STATUS

    #  NO PER-CALL TRACE HERE. The frozen `CALL "irsnominalMT"`
    #  [common/acasirsub1.cbl:L756] displays nothing, so the record that used to sit
    #  on this line was invented (R-4) - and it named `NL-KEY`, the nominal account
    #  (CWE-532). What `SW-Testing` actually gates is `Ca-Process-Logs`, and that is
    #  reproduced below, on the exit path where the frozen source performs it.

    if open_for_output:
        status = open_output(system, file_access, nl)
    else:
        status = _bridge_call(system, file_access, nl)

    # `ba999-end.` [common/irsnominalMT.cbl:L1179-L1184]::
    #
    #     if       Testing-1
    #              perform Ca-Process-Logs
    #     end-if.
    #
    # The bridge's common exit, reached by every verb, and the ONE site of the
    # FH log record on this path. It was previously not reproduced at all - this
    # module emitted no `fhlogger` record and never advanced
    # `Log-File-Rec-Written`, which is the incoherence OBS-010 names. The frozen
    # source ALSO performs `Ca-Process-Logs` from five error arms [:L655, :L812,
    # :L925, :L1107, :L1146]; those five remain a recorded omission, because the
    # verbs they sit in do not receive `ACAS-DAL-Common-data` and inventing a
    # route for it would change this module's linkage (R-3).
    if int(dal_common.sw_testing) == 1:
        ca_process_logs(file_access, dal_common)
    return status


def ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs`` [common/irsnominalMT.cbl:L1749-L1755].

    Two statements, ``call "fhlogger" using File-Access ACAS-DAL-Common-data``,
    followed by ``ca-Exit.     exit.`` [:L1755].

    ``common/fhlogger.cbl`` is out of scope per Agent Action Plan section 0.2.2 and
    rule R-1 forbids calling a COBOL program, so the record it would have appended to
    its flat log is emitted through
    :func:`acas_posting.dal.status.log_file_handler_record` - THE ONE ADAPTER every
    handler in this package shares, at one level, with one field set.

    ``WS-File-Key`` is WITHHELD: on this table it is ``NL-KEY``, a nominal account
    number, and the safe-event schema admits no record key (CWE-532). So are
    ``WS-Log-Where`` and ``SQL-Msg``.

    ``Log-File-Rec-Written`` is advanced by one modulo a million - the range of the
    frozen ``pic 9(6)`` [copybooks/Test-Data-Flags.cob:L20] - once per record, by the
    adapter. It lives in ``ACAS-DAL-Common-data``, which the CALLER owns and carries
    across calls, so it is part of the linkage this module reproduces rather than the
    logger's private state.

    Args:
        file_access: The block the record is built from.
        dal_common: The block carrying ``SW-Testing`` and the counter.
    """
    logging_data = file_access.logging_data
    log_file_handler_record(
        _LOG,
        program="irsnominalMT",
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(file_access.file_function),
        access_type=int(file_access.access_type),
        fs_reply=int(file_access.fs_reply),
        we_error=int(file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=dal_common,
    )


# --- traceability ------------------------------------------------------------
#
# Rule R-5 requires every program to map to a module, every paragraph to a
# function and every field to a data-dictionary entry. The field mapping is
# mechanical - `_ENTRIES` resolves all fifteen columns through
# `dictionary.loader` and `citation()` renders any of them - so what remains is
# the paragraph mapping, below, and the `GO TO` class at every transfer site.
#
# PROGRAM -> MODULE
#   common/acasirsub1.cbl      (773 lines)  ->  this module, entry `dispatch`
#   common/irsnominalMT.cbl   (1757 lines)  ->  this module, everything else
#   copybooks/irswsnl.cob       (24 lines)  ->  records/irs_nominal.py  (linkage)
#   copybooks/irsfdwsnl.cob     (19 lines)  ->  the COLUMN NAMES, via the
#                                               dictionary - see ANOMALY A22
#   mysql/ACASDB.sql:L238                   ->  TABLE, COLUMNS
#
# PARAGRAPH -> FUNCTION.  `PARAGRAPHS` carries this same mapping as data, so a
# test can assert it rather than a reader having to trust it.
#
#   BRIDGE - common/irsnominalMT.cbl, the path this module implements
#     L282-L292   ba010-Initialise            -> _ba010_initialise
#     L302-L328   evaluate File-Function      -> _bridge_call
#     L330-L372   ba020-Process-Open          -> open_          (+ open_input,
#                                                 open_extend, open_output)
#     L374-L387   ba030-Process-Close         -> close
#     L389-L467   ba040-Process-Read-Next     -> read_next
#     L469-L547   ba041-Reread                -> _ba041_reread
#     L549-L663   ba050-Process-Read-Indexed  -> read_indexed
#     L665-L777   ba060-Process-Start         -> start
#     L783-L813   ba070-Process-Write         -> _ba070_process_write
#     L815-L852   ba072-Proc-Write-Subs       -> _ba072_proc_write_subs
#     L854-L868   ba073-Fix-Up-Subs           -> _ba073_fix_up_subs
#                 (the three above, as one verb) -> write
#     L870-L985   ba080-Process-Delete        -> delete
#     L987-L1066  ba085-Process-Delete-ALL    -> delete_all
#     L1068-L1114 ba090-Process-Rewrite       -> rewrite
#     L1116-L1118 ba092-Finish-1 / ba093-Finish-2
#                                             -> the `return` of `rewrite`;
#                                                both are pure GO TO relays
#     L1120-L1152 ba170-Process-Write-Raw     -> write_raw
#     L1154-L1160 ba100-Bad-Function          -> _ba100_bad_function
#     L1166-L1177 ba998-Free                  -> _ba998_free
#     L1179-L1184 ba999-end                   -> the log fields each verb writes,
#                                                plus the `if Testing-1 perform
#                                                Ca-Process-Logs` at the tail of
#                                                `dispatch`
#     L1186-L1187 ba999-exit                  -> the `return` of each verb
#     L1189-L1222 bb000-HV-Load               -> _load_host_variables
#     L1224-L1255 bb100-UnloadHVs             -> _unload_host_variables
#     L1257-L1499 bb200-Insert                -> _bb200_insert
#     L1501-L1747 bb300-Update                -> _bb300_update
#     L1749-L1755 Ca-Process-Logs             -> ca_process_logs. The CALL it
#                                                makes is to `fhlogger`, which
#                                                rule R-1 forbids invoking and
#                                                which AAP 0.2.2 puts out of
#                                                scope, so the record it would
#                                                append is emitted through the
#                                                one shared adapter instead.
#
#   HANDLER - common/acasirsub1.cbl, only the part that runs on this path
#     L211-L217   Procedure Division Using    -> dispatch  (parameter order kept)
#     L226-L227   log identity                -> dispatch
#     L231-L245   key-number guard            -> _key_number_guard
#     L253-L260   Open+Output block  [DEAD]   -> recorded only - ANOMALY A26
#     L264-L268   RDB branch                  -> dispatch
#     L463-L479   aa047-Eval-Keys    [DEAD]   -> _aa047_eval_keys - ANOMALY A31
#     L675-L689   ba-Process-RDBMS / ba010    -> dispatch, the 11 -> 21 bump
#     L691-L731   ba012-Test-WS-Rec-Size-2    -> _record_size_gate
#     L733-L742   ba015-Test-Ends             -> open_output
#     L751-L756   ba020-Process-DAL           -> _bridge_call
#     L314-L673   aa020 .. aa170, aa100       -> OMITTED, indexed-file only
#
# GO TO CLASSES, per AAP section 0.4.2, at every transfer site on this path
#
#   Class 1, loop-back -> `continue` inside `while True:`
#     [common/irsnominalMT.cbl:L542]  ba041  `go to ba041-Reread` after `if Sub`
#           -> the `continue` in `_ba041_reread`. Target is the head of the
#              paragraph the statement is in, so nothing is skipped.
#     [common/irsnominalMT.cbl:L660]  ba050  `go to ba050-Process-Read-Indexed`
#           -> the `continue` in `read_indexed`. Target is the head of the
#              SECTION, so the predicate is rebuilt from the mutated key - which
#              is the point of the chase, and is why the loop encloses the whole
#              body rather than only the fetch.
#
#   Class 2, forward terminator -> `break` plus the post-loop block
#     Does not occur on this path. Recorded as absent rather than omitted: the
#     bridge's loops all terminate by returning, and its two `if
#     WS-MYSQL-Count-Rows` arms are tests rather than transfers.
#
#   Class 3, section or paragraph exit -> `return`
#     [common/irsnominalMT.cbl:L362]  ba020  `go to ba999-end` on a failed open
#     [:L457]   ba040  `go to ba999-End` on no data
#     [:L510, :L528, :L535]  ba041  the three end-of-data exits
#     [:L593, :L635, :L644, :L663]  ba050  every exit, each via ba998-Free
#     [:L675, :L760]  ba060  the access-type rejection and the errno arm
#     [:L832, :L836, :L848, :L868]  ba072 / ba073  the write's early exits
#     [:L918, :L931, :L985]  ba080  the delete's exits
#     [:L1060]  ba085  the delete-all's error exit
#     [:L1109, :L1114]  ba090  both arms, via ba092-Finish-1
#     [:L1152]  ba170  the raw write's exit
#     [common/acasirsub1.cbl:L237, :L243]  the two key-guard rejections
#     [common/acasirsub1.cbl:L259, :L267]  the two RDB-path exits
#     [common/acasirsub1.cbl:L718]  the record-size abort, which also SKIPS the
#           CALL - so `_record_size_gate` returns False and `dispatch` returns
#           without entering `_bridge_call`.
#
#   Class 4, sibling re-dispatch -> named call, then an explicit continue/return
#     [common/irsnominalMT.cbl:L773-L777]  ba060  `perform ba999-end.` and then
#           `go to ba041-Reread.`  THE ONLY CLASS 4 SITE HERE, and the one AAP
#           section 0.4.2 requires be proved individually. The proof: `ba999-end`
#           writes log fields and performs `Ca-Process-Logs` and contains no
#           transfer of its own, so performing it is a pure side effect and
#           control returns to L777 in every case; `ba041-Reread` never returns
#           to `ba060`, because each of its own exits is a Class 3 `go to
#           ba999-End`. Therefore `perform X. go to Y.` is equivalent to
#           `X(); return Y()`, which is what `start` does on its last line.
#           The frozen behaviour this preserves is ANOMALY A7: a START returns a
#           RECORD, and the sub-nominal filter applies to it.
#     [common/acasirsub1.cbl:L740-L751]  ba015  `perform ba020-Process-Dal` and
#           then FALL-THROUGH into the paragraph just performed. Proof: the
#           performed paragraph is the CALL and nothing else, and the
#           fall-through re-enters it with the function code changed by the
#           intervening `set fn-Delete-All to true` - so it is two calls, in
#           order, which is what `open_output` does.
#
# DELIBERATE OMISSIONS - recorded so a reader comparing the two files does not
# conclude something was lost. Each is argued at its site or in the docstring.
#   * the whole indexed-file path of the handler, unreachable when a table is in
#     use [common/acasirsub1.cbl:L267]
#   * both `stop` statements [:L393, :L433], which are on that path - ANOMALY A32
#   * every `display` and `accept` - presentation with no database effect. The
#     diagnostics survive as `_LOG` records; the acknowledgement pauses are
#     dropped; the control flow past them is preserved.
#   * `88 NL-Sub-AC` [copybooks/irsfdwsnl.cob:L9], referenced nowhere in the
#     checkout - ANOMALY A24
#   * the `x"00"` terminator on every statement [common/irsnominalMT.cbl:L432],
#     which exists only for the foreign call rule R-1 forbids
#   * `File-Defs`, accepted by `dispatch` and never read: the RDB path resolves
#     no file name, the table being a literal in the bridge
#   * the handler's own `move zero to Sub-Nominal` [common/acasirsub1.cbl:L523]
#     - ANOMALY A8, indexed-file only, verified absent from the bridge
#
# ADDITIONS - the one thing here with no counterpart in the frozen source
#   * `reset_bridge_storage()`, because a COBOL run unit ends and a Python
#     process does not. Argued at the function.
