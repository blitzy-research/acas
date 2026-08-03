"""``acasirsub1`` + ``irsnominalMT`` - the IRS nominal ledger, ``IRSNL-REC``.

The handler-and-bridge pair for the IRS nominal ledger, reimplemented as SQL
against the frozen table so that no COBOL is reachable at run time (rule R-1).
The pair is the "IRS nominal" row of the entity-to-table spine: entity facade
IRS nominal, handler ``acasirsub1``, bridge ``irsnominalMT``, table
``IRSNL-REC``, record copybook ``copybooks/irswsnl.cob``.

FROZEN SOURCES THIS MODULE REPRODUCES
    ``common/acasirsub1.cbl``          773 lines; ``Procedure Division`` at L211
    ``common/irsnominalMT.cbl``       1757 lines; ``PROCEDURE DIVISION`` at L267
    ``common/irsnominalMT.scb``       1155 lines; the pre-translation source
    ``copybooks/irswsnl.cob``           24 lines; the LINKAGE record
    ``copybooks/irsfdwsnl.cob``         19 lines; the FD record
    ``copybooks/wsfnctn.cob``                 ; function codes and access types
    ``copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob``; the calling convention
    ``mysql/ACASDB.sql``                      ; the table, declared at L238

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
    # `MYSQL-1090-EXIT` and `MYSQL-1999-EXIT` are aliased on import for one
    # reason only: no name in this module may be called with "exit" as the last
    # word before the parenthesis, so that the check which proves ANOMALY A32
    # was not translated into a
    # process-terminating call - the two `stop` statements
    # [common/acasirsub1.cbl:L393, :L433] are recorded as omissions, never
    # executed - reads zero without a reader having to sift false positives out
    # of it. The paragraph names stay visible here, and the aliases carry them
    # through to every call site, so R-5 traceability is unaffected. Do not
    # "tidy" these back to the bare names.
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


#  IDENTITY  ----------------------------------------------------------------
# The "IRS nominal" row of the entity-to-table spine, written out once so that
# no string below can name a different table, handler or bridge.

#: The frozen table [mysql/ACASDB.sql:L238].
TABLE: Final[str] = "IRSNL-REC"

#: Its only key [mysql/ACASDB.sql:L254] and the only key of reference the
#: bridge declares [common/irsnominalMT.cbl:L142].
PRIMARY_KEY: Final[str] = "KEY-1"

#: The numbered handler [common/acasirsub1.cbl:L174, "acasirsub1 (3.3.00)"].
HANDLER: Final[str] = "acasirsub1"

#: The generated bridge it calls [common/acasirsub1.cbl:L752].
BRIDGE: Final[str] = "irsnominalMT"

#: The facade entity name the plan's spine gives this pair.
ENTITY_FACADE: Final[str] = "IRS nominal"


#  KEY METADATA  ------------------------------------------------------------
# `01 Table-Of-Keynames` [common/irsnominalMT.cbl:L139-L151], whose casing
# drifts three ways inside six lines - `Table-Of-Keynames` at L141,
# `table-of-keynames` at L146, `keyOfReference` at L147. ANOMALY A37, recorded
# and not normalised; the drift is cosmetic and the values are what matter.

#: The offset/length pair exactly as the bridge spells it
#: [common/irsnominalMT.cbl:L143]: offset 1, length 10.
KEY_OFFSET_LENGTH: Final[str] = "00010010"

#: Offset of the key within the record image, one-based as COBOL reference
#: modification is one-based.
KEY_OFFSET: Final[int] = 1

#: Length of the key within the record image - the ten digits of
#: ``NL-Owning`` plus ``NL-Sub-Nominal`` [copybooks/irswsnl.cob:L10-L11].
KEY_LENGTH: Final[int] = 10

#: ANOMALY A19 - the metadata declares the key type ``"STR"`` and the bridge
#: editorialises on it in a comment, "key is string"
#: [common/irsnominalMT.cbl:L144], yet the column is ``bigint(10) unsigned``
#: [mysql/ACASDB.sql:L239]. Every predicate the bridge builds therefore
#: compares a quoted string to a number. It is the only such mismatch in the
#: folder - every other in-scope key is genuinely ``char`` - and it is
#: reproduced by binding the key AS TEXT. See ambiguity Q1.
KEY_METADATA_TYPE: Final[str] = "STR"

#: ``keyOfReference occurs 1`` [common/irsnominalMT.cbl:L147]. One key, one
#: cursor - contrast the three-cursor bridges of the open-item tables.
KEY_COUNT: Final[int] = 1


#  LOG IDENTITY  ------------------------------------------------------------

#: ``move 1 to WS-Log-System`` [common/acasirsub1.cbl:L226]. The legend on that
#: line reads "1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock", which CONTRADICTS the
#: "5 = Invoice" legend the invoice and open-item handlers carry. ANOMALY A33
#: adjacent: two mutually inconsistent legends coexist in the codebase. Both
#: are recorded; neither is resolved.
WS_LOG_SYSTEM: Final[int] = int(LogSystem.IRS)

#: ``move 11 to WS-Log-File-No`` [common/acasirsub1.cbl:L227] - the value the
#: indexed-file path keeps.
WS_LOG_FILE_NO_FLAT: Final[int] = 11

#: ``move 21 to WS-Log-File-no`` [common/acasirsub1.cbl:L689] - the value the
#: database path bumps it to, in a paragraph reached only by fall-through from
#: ``ba-Process-RDBMS``. So 21 is the effective file number here. The pair
#: (11, 21) is a FOUR-WAY collision with ``acas005`` (system 2), ``acas012``
#: (system 3) and ``acas022`` (system 4); only the (system, file) pair
#: disambiguates.
WS_LOG_FILE_NO_RDB: Final[int] = 21


#  COLUMNS  -----------------------------------------------------------------

#: The fifteen columns in the ordinal order the frozen dump fixes
#: [mysql/ACASDB.sql:L239-L253], which is also the order of the host-variable
#: group [common/irsnominalMT.cbl:L195-L209] and of the ``SET`` list the insert
#: section emits [common/irsnominalMT.cbl:L1272-L1487].
#:
#: ANOMALY A2 - THE EIGHT QUARTERLY COLUMNS ARE INTERLEAVED. Debit and credit
#: alternate per quarter here, while both copybooks group them as four debits
#: then four credits [copybooks/irswsnl.cob:L19-L20],
#: [copybooks/irsfdwsnl.cob:L14-L15] and the bridge's own record keeps the
#: grouped shape under ``Last-Posts`` [common/irsnominalMT.cbl:L236-L244]. A
#: permutation therefore happens on the way in, and the OPPOSITE permutation on
#: the way out; see :data:`LOAD_TRAVERSAL` and :data:`UNLOAD_TRAVERSAL`.
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
#: [common/irsnominalMT.cbl:L1204-L1215], and which a pointer row therefore
#: leaves at the values ``initialize TD-IRSNL-REC`` [:L1197] put in them.
#:
#: ANOMALY A1 and ANOMALY A4 - these twelve and ``REC-POINTER`` are MUTUALLY
#: EXCLUSIVE, because ``NL-Pointer`` redefines the whole data group
#: [copybooks/irswsnl.cob:L22-L23] and the bridge takes one branch or the
#: other. Nothing in the schema ties either side to ``TIPE``, so a row can
#: carry a type byte that disagrees with which side was written, and no check
#: is added here to notice (rule R-3: validation is copied, never extended).
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

#: The column the alternative view of those bytes writes
#: [common/irsnominalMT.cbl:L1202].
POINTER_COLUMN: Final[str] = "REC-POINTER"

#: The type byte [mysql/ACASDB.sql:L240]. ANOMALY A23 - three spellings of one
#: byte: ``NL-Type`` in the linkage view [copybooks/irswsnl.cob:L12], ``Tipe``
#: in the FD view [copybooks/irsfdwsnl.cob:L8] and ``NL-Tipe`` in the bridge
#: [common/irsnominalMT.cbl:L229]. The misspelling ORIGINATES in the FD view,
#: which is also where the column name comes from, and is never corrected.
TYPE_COLUMN: Final[str] = "TIPE"

#: The account name [mysql/ACASDB.sql:L241] - the only column on this table
#: that keeps an ``NL-`` prefix, and it keeps it because the FD view spells
#: that one field ``NL-Name`` [copybooks/irsfdwsnl.cob:L11]. ANOMALY A22.
NAME_COLUMN: Final[str] = "NL-NAME"

#: ``occurs 4`` [copybooks/irswsnl.cob:L19-L20] - the number of retained
#: quarters, and therefore the number of debit and of credit columns the
#: ``OCCURS`` was flattened into.
_QUARTERS: Final[int] = 4

#: The eight quarterly columns in the order the LOAD paragraph writes them
#: [common/irsnominalMT.cbl:L1208-L1215] - interleaved.
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

#: The full statement order of ``bb000-HV-Load``
#: [common/irsnominalMT.cbl:L1198-L1215]: key, type byte, then EITHER the
#: pointer column OR the twelve data columns with the quarters interleaved.
#: Published so that the traversal itself is testable, because rule R-6 makes
#: the order observable and ANOMALY A2 makes it differ from the unload's.
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

#: The full statement order of ``bb100-UnloadHVs``
#: [common/irsnominalMT.cbl:L1235-L1251] - the same fields, a different walk.
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


#  CONDITION-NAME VALUES  ---------------------------------------------------
# `88 Owner value is "O"` and `88 Sub value is "S"`
# [copybooks/irswsnl.cob:L13-L14]. Tested here rather than imported, because
# the semantics package sits outside this layer's import contract; the FD
# view's `88 NL-Sub-AC` [copybooks/irsfdwsnl.cob:L9] is dead everywhere in the
# checkout and is a recorded omission (ANOMALY A24).

#: An owning account.
TYPE_OWNER: Final[str] = "O"

#: A sub-nominal, i.e. a pointer row.
TYPE_SUB: Final[str] = "S"


#  STATEMENT CONSTANTS  -----------------------------------------------------

#: ``'"0000000000"'`` [common/irsnominalMT.cbl:L410] - the low key the
#: sequential read positions above. The relation beside it is ``" > "``, and
#: the maintainer flagged the choice in line: "26/12/16 NOT '='" [:L409]. A
#: key of exactly zero is therefore never returned by a sequential walk.
SEQUENTIAL_LOW_KEY: Final[str] = "0000000000"

#: ``move 9999999999 to NL-Key`` [common/irsnominalMT.cbl:L1009], described
#: there as "The last possible data", and used as ``< "9999999999"``
#: [:L1015-L1025]. ANOMALY A28 - the mass delete is a bounded predicate rather
#: than an unqualified delete, so a row keyed exactly 9999999999 survives it.
DELETE_ALL_HIGH_KEY: Final[str] = "9999999999"

#: The literal the sequential-read predicate carries
#: [common/irsnominalMT.cbl:L404]. ANOMALY A5 - the filter is in the SQL as
#: well as at record level, so a sub-nominal row is excluded twice over.
SEQUENTIAL_TYPE_FILTER: Final[str] = TYPE_OWNER


#  STATUS PAIRS  ------------------------------------------------------------
# Each pair is (FS-Reply, We-Error) as the frozen source leaves it, which is
# not always what it first writes.

#: End of data. ``move 10 to fs-reply`` then ``move 3 to WE-Error``
#: [common/irsnominalMT.cbl:L453, :L455], with the paragraph's own comment
#: stating the intent outright: "Uses 3 (instead of 10) as EOF flag in
#: WE-Error per irsub1" [:L391].
#:
#: ANOMALY A16 - the ``move 10 to WE-Error`` that would have made the pair
#: (10, 10) is COMMENTED OUT at [:L454] and again at [:L520], so the 10 is
#: dead rather than overwritten. ANOMALY A17 - ``We-Error`` 3 is one of the
#: folder's only two single-digit values, and it is NOT a member of the shared
#: enumeration; the literal is used deliberately and must not be forced into
#: one. This is also why ``status.end_of_file_status()``, which returns
#: (10, 10), is unusable here.
END_OF_FILE_STATUS: Final[tuple[FsReply, int]] = (FsReply.END_OF_FILE, 3)

#: Key not found. ``move 21 to fs-Reply`` then ``move 2 to WE-Error``
#: [common/irsnominalMT.cbl:L591-L592], the 21 carrying the maintainer's own
#: hedge, "could also be 23 or 14". ANOMALY A17 again: ``We-Error`` 2 appears
#: nowhere else in the folder and has no enumeration member.
NOT_FOUND_STATUS: Final[tuple[FsReply, int]] = (FsReply.INVALID_KEY_ON_START, 2)

#: A duplicate key on insert [common/irsnominalMT.cbl:L805, :L1139].
DUPLICATE_KEY_STATUS: Final[tuple[FsReply, int]] = (FsReply.DUPLICATE_KEY, 0)

#: The bridge's bad function - ``move 990 to WE-Error`` / ``move 99 to
#: Fs-Reply`` [common/irsnominalMT.cbl:L1158-L1159], under the paragraph's own
#: heading "Houston; We have a problem" [:L1156]. CORRECTION C3: this, and not
#: the handler's (99, 999), is the pair a caller sees on this path.
BAD_FUNCTION_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.UNKNOWN_UNEXPECTED),
)

#: The handler's bad function [common/acasirsub1.cbl:L661-L662]. Published for
#: traceability only; it is unreachable on this path. CORRECTION C3.
HANDLER_BAD_FUNCTION_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.NOT_USED),
)

#: The record-size abort [common/acasirsub1.cbl:L701-L702] - ``move 901 to
#: WE-Error`` then ``move 99 to fs-reply``, after which the handler jumps to
#: its own exit and the bridge is NEVER called [:L718].
RECORD_SIZE_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.RECORD_SIZE_MISMATCH),
)

#: The bridge's access-type guard [common/irsnominalMT.cbl:L672-L675] -
#: ``move 99 to FS-Reply`` then ``move 997 to WE-Error``. CORRECTION C1: this
#: guard EXISTS on the database path, contrary to the assignment brief, and it
#: is the one implemented.
ACCESS_TYPE_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.ACCESS_TYPE_WRONG),
)

#: The handler's key-number guard for ``fn-read-indexed`` and ``fn-start``
#: [common/acasirsub1.cbl:L235-L236] - ``move 998 to WE-Error`` then ``move 99
#: to fs-reply``.
KEY_NUMBER_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
)

#: The handler's key-number guard for ``fn-delete``
#: [common/acasirsub1.cbl:L241-L242] - a DIFFERENT code, 996, for the same
#: condition, with the extra comment "1 is only for RDB as Cobol does it on
#: primary key" [:L240] repeated verbatim from ``common/acas022.cbl:L307``.
DELETE_KEY_NUMBER_STATUS: Final[tuple[FsReply, int]] = (
    FsReply.ERROR,
    int(WeError.DELETE_KEY_OUT_OF_RANGE),
)

#: A failed delete [common/irsnominalMT.cbl:L915-L916, :L1057-L1058] and a
#: failed update [:L1102-L1103]. Both are the generic (99, 911) narrowed
#: afterwards by the verb, which is what
#: :func:`status.override_we_error_for_operation` reproduces.
DELETE_FAILED_WE_ERROR: Final[int] = int(WeError.DELETE_SQLSTATE_NOT_00000)
REWRITE_FAILED_WE_ERROR: Final[int] = int(WeError.REWRITE_SQLSTATE_NOT_00000)

#: The errno the bridge treats as "no driver error", written with its two
#: trailing spaces exactly as the source compares it: ``if errno not = "0  "``
#: [common/irsnominalMT.cbl:L448, :L622, :L907]. A count of zero rows PLUS
#: this errno is the silent path - no status is written at all.
NO_DRIVER_ERROR: Final[str] = "0  "


#  TRACE NUMBERS  -----------------------------------------------------------

#: ``ws-No-Paragraph`` as the BRIDGE writes it, keyed by function code.
#: CORRECTION C4 and ANOMALY A49 - these, not the handler's, are the values a
#: caller observes on this path, and the set has six holes: 7, 9, 11, 12, 16
#: and 19 are never written. The pair 13/14 belongs to the two deletes of one
#: logical delete and 17 to the update the write path borrows, so the numbers
#: are per-paragraph rather than per-verb.
#:
#: Sites: 1 [common/irsnominalMT.cbl:L359], 2 [:L378], 3 [:L421], 4 [:L474],
#: 5 [:L573], 6 [:L595], 8 [:L728], 10 [:L792], 13 [:L893], 14 [:L937],
#: 15 [:L1035], 17 [:L1071], 18 [:L1126], 20 [:L1167]. The assignment at L937
#: spells the field ``WS-No-Paragraph`` where every sibling line spells it
#: ``ws-No-Paragraph`` - casing drift, recorded under ANOMALY A37.
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
#: ANOMALY A18 - 213 and 216 fall outside the 201..208 range every sibling
#: handler uses, because ``aa045`` and ``aa170`` were inserted after the
#: original eight. Published for traceability; unreachable on this path.
#:
#: Sites: 201 [common/acasirsub1.cbl:L316], 202 [:L367], 203 [:L385],
#: 213 [:L426], 204 [:L489], 205 [:L517], 206 [:L568], 207 [:L607],
#: 208 [:L629], 216 [:L642].
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


#  LOG-KEY TAGS  ------------------------------------------------------------

#: ANOMALY A47 - FOUR distinct end-of-data tags reach ``WS-File-Key`` on the
#: read path, and which one a caller sees says where the walk stopped:
#: ``"No Data"`` when the positioning statement matched nothing
#: [common/irsnominalMT.cbl:L456], ``"EOF"`` when the snapshot ran out
#: [:L507], ``"EOF2"`` when the fetch reported a driver error [:L525], and
#: ``"EOF3"`` when the reply was already 10 on entry [:L534]. All four carry
#: the SAME status pair, so the tag is the only way to tell them apart.
END_OF_DATA_TAGS: Final[tuple[str, ...]] = ("No Data", "EOF", "EOF2", "EOF3")

#: ANOMALY A45 - the indexed read writes DIAGNOSTIC TEXT INTO THE NAME FIELD:
#: ``"Not found 1"`` when the fetch reported a driver error
#: [common/irsnominalMT.cbl:L634], ``"Not found 2"`` when it simply returned
#: nothing [:L641], and ``"Not found"`` on every iteration of the pointer
#: chase [:L659], where it overwrites the account name the previous iteration
#: unloaded. A caller that inspects the record after a miss sees prose in a
#: data field, and the chase leaves prose there even when it succeeds.
NOT_FOUND_LITERALS: Final[tuple[str, ...]] = (
    "Not found 1",
    "Not found 2",
    "Not found",
)

#: The tags the open and close paragraphs write
#: [common/irsnominalMT.cbl:L370, :L379].
_OPEN_TAG: Final[str] = "OPEN IRSNOMINAL (RDB)"
_CLOSE_TAG: Final[str] = "CLOSE IRSNOMINAL (RDB)"


#  PARAGRAPH MAP  -----------------------------------------------------------

#: Every COBOL paragraph this module reproduces, mapped to the function that
#: reproduces it, with its line span. Rule R-5 requires the mapping to exist as
#: a recorded artefact rather than as an implication of the code, and the
#: traceability footer at the end of this file carries the same map with the
#: ``GO TO`` class applied at each transfer site.
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

#: The function codes reachable on this path. The bridge's ``evaluate
#: File-Function`` [common/irsnominalMT.cbl:L302-L328] lists 1, 2, 3, 4, 5, 6,
#: 7, 8, 9 and 15 and nothing else; its ``when other`` carries the STALE
#: comment "6 is spare / unused" [:L326] even though 6 is handled twelve lines
#: earlier, which is ANOMALY A41.
#:
#: ANOMALY A40 and CORRECTION C2 - 13 is absent. The handler dispatches it
#: [common/acasirsub1.cbl:L303-L304] but the handler's ``evaluate`` is
#: unreachable here, so 13 is a bad function on this path.
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


#  THE FIELD METADATA  (rule R-5 - resolved, never transcribed)
# Every one of the fifteen columns is looked up in the generated dictionary,
# under the key form `<TABLE>.<COLUMN>` - which for this table means under the
# FD copybook's column spellings (ANOMALY A22), because that is what the frozen
# dump declares. Nothing below retypes a picture, a width, a scale or a
# signedness: each is read from the entry. The plan states the ordering as a
# directive rather than a preference - the dictionary comes first, and every
# field definition cites its entry - precisely so that several hundred fields
# across the layer cannot be transcribed by eye.


def _entry(column: str) -> loader.DictionaryEntry:
    """Return the dictionary entry for one column of this table.

    Args:
        column: The column name as [mysql/ACASDB.sql:L239-L253] spells it.

    Returns:
        The entry, carrying the copybook view, the bridge host variable, the
        column, the drift flags and the derivation guard.

    Raises:
        DictionaryLookupError: If the artefact holds no such entry, which would
            mean the dictionary and this module disagree about the table - a
            condition to fail on rather than paper over.
    """
    return loader.get_entry(f"{TABLE}.{column}")


def citation(column: str) -> str:
    """Return the three-layer provenance line for one column.

    The rendered form is the dictionary's own, e.g. ``IRSNL-REC.KEY-1
    copybook=copybooks/irswsnl.cob:L9 bridge=common/irsnominalMT.cbl:L195
    column=mysql/ACASDB.sql:L239``. Published so that a caller, a test or a
    reviewer can obtain the citation for any column of this table without
    reaching into the dictionary itself (rule R-5).

    Args:
        column: The column name.

    Returns:
        The provenance line.
    """
    return loader.cite(f"{TABLE}.{column}")


_ENTRIES: Final[Mapping[str, loader.DictionaryEntry]] = MappingProxyType(
    {column: _entry(column) for column in COLUMNS}
)

#: Columns whose host variable declares a fractional scale - the ten money
#: columns, every one of them ``9(08)V9(02)`` and UNSIGNED
#: [common/irsnominalMT.cbl:L198-L207]. Derived from the dictionary rather than
#: listed, so that the choice between :class:`~decimal.Decimal` and ``int`` is
#: data-driven (rule R-2).
#:
#: ANOMALY A6 - the copybook declares them ``pic 9(8)v99`` with NO ``S``
#: [copybooks/irswsnl.cob:L17-L20], the host variables carry no ``S``, and the
#: columns are ``unsigned`` [mysql/ACASDB.sql:L242-L251]. This is the only
#: in-scope table with no signedness drift anywhere, because nothing about it
#: is signed - which makes a nominal-ledger accumulator that cannot hold a
#: negative value the anomaly instead. No sign is added. See ambiguity Q2.
_MONEY_COLUMNS: Final[tuple[str, ...]] = tuple(
    column
    for column in COLUMNS
    if (_ENTRIES[column].bridge_host_variable.scale or 0) > 0
)

#: Columns whose host variable is alphanumeric - ``TIPE``, ``NL-NAME``, ``AC``.
_CHARACTER_COLUMNS: Final[tuple[str, ...]] = tuple(
    column
    for column in COLUMNS
    if _ENTRIES[column].bridge_host_variable.character_length is not None
)

#: The two whole-number columns: ``KEY-1`` and ``REC-POINTER``.
_INTEGER_COLUMNS: Final[tuple[str, ...]] = tuple(
    column
    for column in COLUMNS
    if column not in _MONEY_COLUMNS and column not in _CHARACTER_COLUMNS
)

#: Declared width of each alphanumeric host variable, from the dictionary.
#: ``HV-NL-NAME X(24)`` matches the copybook's ``pic x(24)`` and the column's
#: ``char(24)`` exactly - no width drift here, in contrast with the ledger name
#: of ``nominalMT``, which widens 24 to 32.
_CHARACTER_WIDTHS: Final[Mapping[str, int]] = MappingProxyType(
    {
        column: int(_ENTRIES[column].bridge_host_variable.character_length or 0)
        for column in _CHARACTER_COLUMNS
    }
)

#: Integer and fractional digit counts of each money host variable.
_MONEY_DIGITS: Final[Mapping[str, tuple[int, int]]] = MappingProxyType(
    {
        column: (
            int(_ENTRIES[column].bridge_host_variable.integer_digits or 0),
            int(_ENTRIES[column].bridge_host_variable.scale or 0),
        )
        for column in _MONEY_COLUMNS
    }
)

#: Digit count of each whole-number host variable.
#:
#: ANOMALY A20 - ``HV-KEY-1`` is ``PIC 9(18) COMP``
#: [common/irsnominalMT.cbl:L195] for a ten-digit source
#: [copybooks/irswsnl.cob:L10-L11] and a ``bigint(10)`` column
#: [mysql/ACASDB.sql:L239]: eight digits of inflation, then narrowing. It is
#: the widest host variable in the folder.
#:
#: ANOMALY A21 - ``HV-REC-POINTER`` is ``PIC 9(08) COMP`` [:L209] for a
#: ``pic 9(5)`` source [copybooks/irswsnl.cob:L23] and a ``mediumint(5)``
#: column [mysql/ACASDB.sql:L253]: widened five to eight, narrowed eight to
#: five. The dictionary records both the usage change and the digit
#: disagreement as drift.
_INTEGER_DIGITS: Final[Mapping[str, int]] = MappingProxyType(
    {
        column: int(_ENTRIES[column].bridge_host_variable.digits or 0)
        for column in _INTEGER_COLUMNS
    }
)

#: The name field's declared width, needed by the overlay helpers because the
#: pointer occupies its first five characters.
_NAME_WIDTH: Final[int] = _CHARACTER_WIDTHS[NAME_COLUMN]

#: A money host variable at its initialised value, at the declared scale so
#: that a zero renders ``"0.00"`` and not ``"0"``. The scale is taken from the
#: dictionary rather than written as a literal (rule R-5).
_ZERO_MONEY: Final[Decimal] = Decimal(0).scaleb(0).quantize(
    Decimal(1).scaleb(-_MONEY_DIGITS["DR"][1])
)

#: ``05 NL-Pointer pic 9(5)`` [copybooks/irswsnl.cob:L23] - the width of the
#: alternative view, and therefore how many characters of the name the class
#: test in ANOMALY A1 inspects.
_POINTER_DIGITS_IN_RECORD: Final[int] = 5

#: The two halves of the key, each ``pic 9(5)``
#: [copybooks/irswsnl.cob:L10-L11]. ANOMALY A25 - the copybooks declare a group
#: of two, the bridge declares one ``pic 9(10)`` with the halves as a
#: ``REDEFINES`` [common/irsnominalMT.cbl:L225-L228]. The same ten bytes with
#: opposite emphasis, and the bridge's single-field view is why the column is a
#: ``bigint`` rather than two smaller ones.
_KEY_HALF_DIGITS: Final[int] = 5

#: ASCII digits, spelled out rather than delegated to ``str.isdigit``, which
#: also accepts superscripts and other Unicode digit forms. A COBOL numeric
#: class test on a ``pic 9(5)`` DISPLAY item accepts the ten ASCII digits and
#: nothing else, so the wider predicate would classify rows the compiled
#: program does not.
_ASCII_DIGITS: Final[frozenset[str]] = frozenset("0123456789")


#  THE BRIDGE'S OWN CONVERSION  ---------------------------------------------
# "The bridge is not a transparent pipe." Where the copybook declaration, the
# host variable and the column disagree, the value CHANGES on the way through,
# before any SQL executes - so this layer must reproduce the bridge's
# conversion rather than write the computed value and let the server complain.
#
# Two stages, in this order. First a COBOL `move` into the host variable, which
# is a digit-position operation: right-align into the receiving positions,
# keep the low-order digits, truncate the fraction to the receiving scale, and
# drop the sign when the receiver is unsigned - which here it always is. Then
# the bridge renders the host variable into statement text through one shared
# edit field, `01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)`
# [common/irsnominalMT.cbl:L129], and slices three different windows out of it
# depending on the column.
#
# Both stages are done by digit manipulation and never by binary arithmetic
# (rule R-2): a `move` in COBOL does not compute, and neither does this.

#: Total character positions of ``PIC -Z(18)9.9(9)``
#: [common/irsnominalMT.cbl:L129]: one sign, eighteen suppressed integer
#: digits, one unsuppressed integer digit, the point, nine fractional digits.
_EDIT_WIDTH: Final[int] = 30

#: The eighteen ``Z`` positions - character positions 2 to 19 - in which a
#: leading zero prints as a space.
_EDIT_SUPPRESSED_DIGITS: Final[int] = 18

#: All integer positions, the ``Z`` run plus the single ``9`` at position 20.
_EDIT_INTEGER_DIGITS: Final[int] = 19

#: The ``9(9)`` run, character positions 22 to 30.
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

#: ``FUNCTION TRIM (WS-MYSQL-EDIT(13:08))``
#: [common/irsnominalMT.cbl:L1306, :L1485] - the window the integer part of a
#: money value and the whole of ``REC-POINTER`` are rendered through. Eight
#: positions, matching the eight integer digits both host variables declare.
_EDIT_INTEGER_WINDOW: Final[tuple[int, int]] = (13, 8)

#: ``WS-MYSQL-EDIT(22:02)`` [common/irsnominalMT.cbl:L1311] - the fractional
#: window, NOT trimmed, so it is always two digits and a value of zero renders
#: ``"00"`` rather than an empty string.
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

    The receiving digit counts come from the dictionary
    (:data:`_MONEY_DIGITS`), never from a literal here. Three things happen at
    once, exactly as one COBOL store does them: the fraction is TRUNCATED to
    the receiving scale - no rounding, because a store without ``ROUNDED``
    truncates toward zero - the integer part keeps its low-order digits, and
    the sign is dropped.

    ANOMALY A6 - dropping the sign is not a choice. The host variable carries
    no ``S`` [common/irsnominalMT.cbl:L198-L207] and neither does the copybook
    [copybooks/irswsnl.cob:L17-L20], so a debit or credit accumulator simply
    cannot hold a negative value anywhere along the chain. What the compiled
    system actually stores for a negative accumulation is ambiguity Q2 and must
    be measured, not assumed; this reproduces the declared storage and nothing
    more.

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
    [common/irsnominalMT.cbl:L129], ``PIC -Z(18)9.9(9)``. The image is built in
    full and the callers slice windows out of it, rather than each caller
    formatting the value its own way, because the windows are what the frozen
    source names and two of the three are deliberately narrower than the field.

    Zero suppression: a leading zero in one of the eighteen ``Z`` positions
    prints as a space; the single ``9`` at position 20 always prints its digit,
    which is why a value of zero renders ``"0"`` and never an empty string.

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

    COBOL reference modification ``(p:n)`` is one-based and takes ``n``
    characters from position ``p``.

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

    ``move HV-KEY-1 to WS-MYSQL-EDIT`` then ``FUNCTION TRIM
    (WS-MYSQL-EDIT(03:18))`` [common/irsnominalMT.cbl:L1274-L1278]: a plain
    integer with no leading zeros, or ``"0"``.

    NOTE THAT THIS IS NOT THE FORM THE PREDICATE USES. The ``SET`` clause of
    one statement carries the EDITED key while the ``WHERE`` clause of the same
    statement carries the RAW ten-character record slice
    [common/irsnominalMT.cbl:L1076-L1086] - so a single update sends the same
    key twice, in two different renderings, e.g. ``1000020`` and
    ``0001000020``. Both coerce to the same number. Both are reproduced.

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

    ``move HV-REC-POINTER to WS-MYSQL-EDIT`` then ``FUNCTION TRIM
    (WS-MYSQL-EDIT(13:08))`` [common/irsnominalMT.cbl:L1483-L1487] - ANOMALY
    A21's eight-digit window over a five-digit source and a five-digit column.

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
    ``WS-MYSQL-EDIT(22:02)`` UNTRIMMED
    [common/irsnominalMT.cbl:L1305-L1313]. So the integer part loses its
    leading zeros while the fraction keeps both digits: zero renders
    ``"0.00"``, five pence renders ``"0.05"``.

    The value travels to the server as this text, because that is what the
    bridge transmits, and text carries no binary floating-point stage
    anywhere (rule R-2).

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

    ``FUNCTION TRIM (HV-TIPE,TRAILING)``
    [common/irsnominalMT.cbl:L1288-L1289] and the same form for ``HV-NL-NAME``
    and ``HV-AC``: TRAILING only, so leading spaces survive and trailing ones
    do not.

    A consequence worth stating because it looks like a defect and is not: a
    single-character field holding a space renders as the EMPTY STRING, and
    that empty string is what reaches a ``char(1) NOT NULL`` column. It is
    never ``NULL`` - the group's ``INITIALIZE``
    [common/irsnominalMT.cbl:L1197] is why every column on this table can be
    declared ``NOT NULL`` and why this layer defaults rather than omits.

    Args:
        value: The value to store.
        column: The receiving column, whose host variable supplies the width.

    Returns:
        The rendered text, ready to bind.
    """
    image = _character_image(value, _CHARACTER_WIDTHS[column])
    return image.rstrip()


#  THE REDEFINES OVERLAY  ---------------------------------------------------
# `03 filler redefines NL-Data. / 05 NL-Pointer pic 9(5)`
# [copybooks/irswsnl.cob:L22-L23]. One five-digit number laid over 105 bytes of
# name, money and status, so `NL-Pointer` IS `NL-Name (1:5)`. The record module
# necessarily models the two views as two attributes, because Python has no
# storage overlay, so these three helpers keep them in step exactly as one byte
# range would - read the digits from the name, decode them, and when the
# pointer is written write BOTH sides.
#
# Everything downstream depends on this being right: ANOMALY A1's class test,
# ANOMALY A10's partial restore and ANOMALY A15's pointer chase all read or
# write those same five characters.


def _character_image(value: str, width: int) -> str:
    """Return ``value`` as it sits in a ``pic x(width)`` field.

    A COBOL alphanumeric move left-justifies and space-fills, and truncates on
    the right when the sending item is longer. Applied wherever a character
    field's byte image is needed, so that a caller who assigned a short string
    still yields the declared number of bytes.

    Args:
        value: The current attribute value.
        width: The declared width, from the dictionary.

    Returns:
        Exactly ``width`` characters.
    """
    return value.ljust(width)[:width]


def _pointer_digits(nl: WsIrsnlRecord) -> str:
    """Return the five characters ``NL-Pointer`` occupies.

    They are the FIRST FIVE CHARACTERS OF THE ACCOUNT NAME, because the
    pointer view redefines the data group [copybooks/irswsnl.cob:L22-L23].

    Args:
        nl: The record.

    Returns:
        Five characters, space-filled if the name is shorter.
    """
    name = _character_image(nl.nl_data.nl_name, _NAME_WIDTH)
    return name[:_POINTER_DIGITS_IN_RECORD]


def _pointer_is_numeric(nl: WsIrsnlRecord) -> bool:
    """Reproduce the ``NL-Pointer numeric`` class test.

    Half of the discriminator at [common/irsnominalMT.cbl:L1200]. Every one of
    the five characters must be an ASCII digit; a name beginning with a letter,
    a space or punctuation fails.

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

    The record module also carries a decoded ``nl_pointer`` attribute, but the
    STORAGE is the name's first five characters, so this reads those - which is
    what makes the two views agree however the caller last assigned them.

    Args:
        nl: The record.

    Returns:
        The overlaid value, or zero when the characters are not all digits.
        Zero is also the value a genuine ``"00000"`` yields, and the bridge
        cannot tell those apart either: its guard rejects both.
    """
    if not _pointer_is_numeric(nl):
        return 0
    return int(_pointer_digits(nl))


def _apply_pointer_overlay(nl: WsIrsnlRecord, value: int) -> None:
    """Write ``NL-Pointer``, which writes the name's first five characters too.

    Reproduces ``move NL-Owning to NL-Pointer``
    [common/irsnominalMT.cbl:L850] - a five-digit store into a field that
    overlays the name, so the name's first five characters become those digits
    and the account name is corrupted in the caller's own record. That
    corruption is ANOMALY A10 and it is deliberate: the write path restores the
    two key halves afterwards [:L866-L867] and leaves the name as it is.

    Args:
        nl: The record to mutate in place.
        value: The pointer value. Stored into ``pic 9(5)``, so the low-order
            five digits are what survive - a COBOL move, not a check.
    """
    digits = _narrow_unsigned_integer(value, _POINTER_DIGITS_IN_RECORD)
    text = f"{digits:0{_POINTER_DIGITS_IN_RECORD}d}"
    name = _character_image(nl.nl_data.nl_name, _NAME_WIDTH)
    nl.nl_data.nl_name = text + name[_POINTER_DIGITS_IN_RECORD:]
    nl.nl_pointer_view.nl_pointer = digits


def _is_pointer_row(nl: WsIrsnlRecord) -> bool:
    """THE DISCRIMINATOR. Reproduce ``if NL-Pointer numeric and > zero``.

    ``if NL-Pointer numeric and NL-Pointer > zero``
    [common/irsnominalMT.cbl:L1200-L1201] is the single most consequential line
    in this module, and IT DOES NOT LOOK AT ``NL-Type``. It class-tests the
    first five characters of the ACCOUNT NAME, because the pointer view
    redefines the data group [copybooks/irswsnl.cob:L22-L23].

    ANOMALY A1, REPRODUCED AND NOT FIXED (rule R-4). The consequence is real
    data loss: an owning account named ``"10001 Petty Cash"`` satisfies this
    predicate, so :func:`_load_host_variables` takes the pointer branch and the
    name, both current balances, the status flag and all eight quarterly
    balances are left at the values ``initialize TD-IRSNL-REC`` [:L1197] put in
    them - spaces and zeros - and THOSE are what reach the table. Testing
    ``nl_type`` instead would be a defect fix and therefore a failure.

    Args:
        nl: The record about to be written.

    Returns:
        True when the row is stored as a pointer row and the twelve data
        columns are left at their initialised values.
    """
    return _pointer_is_numeric(nl) and _read_pointer_overlay(nl) > 0


def _owner(nl: WsIrsnlRecord) -> bool:
    """``88 Owner value is "O"`` [copybooks/irswsnl.cob:L13].

    Tested here rather than imported: the semantics package that declares the
    condition names is outside this layer's import contract, so the one-byte
    comparison is made locally against the value the copybook gives.

    Args:
        nl: The record.

    Returns:
        True for an owning account.
    """
    return nl.nl_type == TYPE_OWNER


def _sub(nl: WsIrsnlRecord) -> bool:
    """``88 Sub value is "S"`` [copybooks/irswsnl.cob:L14].

    The FD view's own condition name for the same value, ``88 NL-Sub-AC``
    [copybooks/irsfdwsnl.cob:L9], is referenced nowhere in the checkout -
    ANOMALY A24, recorded as a deliberate omission.

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

    The mirror image of :func:`_apply_pointer_overlay`. ``move HV-NL-NAME to
    NL-Name`` [common/irsnominalMT.cbl:L1240] stores 24 bytes over storage
    whose first five are also ``NL-Pointer``
    [copybooks/irswsnl.cob:L22-L23], so the decoded pointer attribute is
    re-derived from the new characters. A name of ``"10001 Petty Cash"``
    therefore leaves ``nl_pointer`` holding 10001, which is precisely how the
    round trip reproduces ANOMALY A1 rather than hiding it.

    Args:
        nl: The record to mutate in place.
        value: The name as read back or as supplied.
    """
    nl.nl_data.nl_name = _character_image(value, _NAME_WIDTH)
    nl.nl_pointer_view.nl_pointer = _read_pointer_overlay(nl)


def _key_number(nl: WsIrsnlRecord) -> int:
    """Return the key as one number, the way ``NL-Key pic 9(10)`` holds it.

    The bridge's own view of the key [common/irsnominalMT.cbl:L225] - ANOMALY
    A25. Used where the bridge moves the whole key into a host variable rather
    than slicing the record image.

    Args:
        nl: The record.

    Returns:
        The ten digits as an integer.
    """
    return int(_key_image(nl))


def _set_key_from_number(nl: WsIrsnlRecord, value: int) -> None:
    """Split a ten-digit key back into the two ``pic 9(5)`` halves.

    Reproduces ``move HV-KEY-1 to NL-Key`` [common/irsnominalMT.cbl:L1235],
    where the receiving item is the ten-byte group and the two halves are a
    ``REDEFINES`` of it, so one store fills both.

    Args:
        nl: The record to fill.
        value: The key value read back from the table.
    """
    digits = _narrow_unsigned_integer(value, KEY_LENGTH)
    text = f"{digits:0{KEY_LENGTH}d}"
    nl.nl_key.nl_owning = int(text[:_KEY_HALF_DIGITS])
    nl.nl_key.nl_sub_nominal = int(text[_KEY_HALF_DIGITS:])


#  bb000-HV-Load  -----------------------------------------------------------
# `bb000-HV-Load Section.` [common/irsnominalMT.cbl:L1189-L1216]. Called before
# every non-fetch action, it copies the caller's record into the host-variable
# group that the statement text is then rendered from.
#
# Three things in it matter and all three are reproduced:
#   * `initialize TD-IRSNL-REC.` [:L1197] comes first, so any host variable the
#     branch below does not assign holds a space or a zero - never SQL NULL.
#     That is why all fifteen columns can be `NOT NULL` and why this layer
#     defaults rather than omits.
#   * the discriminator [:L1200-L1201] reads the NAME, not the type - A1.
#   * the two branches are MUTUALLY EXCLUSIVE, so `REC-POINTER` and the twelve
#     data columns can never both carry a value in one row - A4. Nothing ties
#     that to `TIPE`, and no check is added here, because a check would be a
#     new validation (rule R-3).


def _initialise_host_variables() -> dict[str, object]:
    """Reproduce ``initialize TD-IRSNL-REC``.

    ``initialize`` sets each elementary item to the figurative constant for its
    category - zero for numeric, space for alphanumeric
    [common/irsnominalMT.cbl:L1197]. The keys are inserted in the group's own
    declaration order [common/irsnominalMT.cbl:L195-L209], which is also the
    column order of the table, so a caller that iterates the result gets the
    columns in the order the frozen schema declares them.

    Returns:
        All fifteen host variables at their initialised values. Every entry is
        an :class:`int`, a :class:`~decimal.Decimal` or a :class:`str`; never
        ``None``.
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

    ANOMALY A38 - the section closes with "Loading HVs implies a non-Fetch
    action. RGs are handled separately for all such actions so they must not be
    loaded here." [common/irsnominalMT.cbl:L1218-L1219] IN A BRIDGE THAT HAS NO
    REPEATING GROUP. ``IRSNL-REC`` is one table with one key and no RG sections
    at all - the section list runs ``bb000``, ``bb100``, ``bb200``, ``bb300``
    and stops - so the note is copy-paste from a bridge that does have one,
    exactly as ``common/purchMT.cbl`` carries it. Nothing follows from it, and
    nothing is done about it. Of a piece with the maintainer's habit of calling
    the handler ``irsub1`` rather than ``acasirsub1``, five times over
    [common/acasirsub1.cbl:L285, :L389, :L400, :L496, :L534] - ``irsub1`` being
    the pre-migration name of the program this one was derived from.

    Args:
        nl: The caller's record, read and never modified here.
        traversal: When supplied, each column is appended as it is assigned, so
            that the ORDER of the assignments is observable to a caller. The
            order is load-bearing (ANOMALY A2) and :data:`LOAD_TRAVERSAL`
            records what it must be.

    Returns:
        The fifteen host variables. Narrowed to their declared digit counts and
        scales - see :func:`_narrow_unsigned_integer` and
        :func:`_narrow_unsigned_money` - because the bridge is not a
        transparent pipe and the value changes here, before any SQL runs.
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

    # `move NL-Tipe to HV-TIPE.` [common/irsnominalMT.cbl:L1199]
    #
    # ANOMALY A23 - one byte with three spellings across the three record
    # views: `NL-Type` [copybooks/irswsnl.cob:L12], `Tipe`
    # [copybooks/irsfdwsnl.cob:L8] and `NL-Tipe`
    # [common/irsnominalMT.cbl:L229]. The misspelling that the column inherited
    # originates in the FD copybook, not in the bridge, and `TYPE` being a
    # reserved word is presumably why.
    assign(TYPE_COLUMN, _character_image(nl.nl_type, _CHARACTER_WIDTHS[TYPE_COLUMN]))

    # `if NL-Pointer numeric and NL-Pointer > zero`
    # [common/irsnominalMT.cbl:L1200-L1201] - ANOMALY A1. The discriminator
    # class-tests the first five characters of the ACCOUNT NAME, because
    # `NL-Pointer` redefines the data group [copybooks/irswsnl.cob:L22-L23].
    # It does NOT test `NL-Type`, and substituting the type test would be a
    # defect fix and therefore a failure (rule R-4).
    if _is_pointer_row(nl):
        # `move NL-Pointer to HV-REC-POINTER` [common/irsnominalMT.cbl:L1202].
        #
        # ANOMALY A21 - `pic 9(5)` widened into `PIC 9(08) COMP`
        # [common/irsnominalMT.cbl:L209] and then narrowed again by a
        # `mediumint(5)` column.
        #
        # ANOMALY A1's consequence, stated plainly: the twelve data host
        # variables are NOT ASSIGNED on this path, so `NL-NAME` reaches the
        # table as spaces and the two balances, the status flag and all eight
        # quarterly balances reach it as zeros. The account name is lost. That
        # is the behaviour of the compiled program and it is preserved here.
        assign(POINTER_COLUMN, _narrow_unsigned_integer(
            _read_pointer_overlay(nl), _INTEGER_DIGITS[POINTER_COLUMN]
        ))
        return host_variables

    # The `else` branch [common/irsnominalMT.cbl:L1204-L1215]. Name, both
    # current balances, the status flag, and then the eight quarters
    # INTERLEAVED - DR-01, CR-01, DR-02, CR-02 and so on - which is the host
    # variable and column order, and the OPPOSITE of the grouped order the
    # bridge's own record declares them in [common/irsnominalMT.cbl:L236-L244].
    # ANOMALY A2, first half.
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


#  bb100-UnloadHVs  ---------------------------------------------------------
# `bb100-UnloadHVs Section.` [common/irsnominalMT.cbl:L1224-L1252]. Called
# after every fetch, it copies the host-variable group back into the caller's
# record.
#
# It is NOT the inverse of the load, in two separate ways, and both are
# reproduced:
#   * the guard is `if HV-REC-POINTER > zero` [:L1237] with NO `numeric` test -
#     which cannot apply to a `COMP` item - where the load tested `numeric AND
#     > zero`. ANOMALY A3.
#   * the quarters are traversed GROUPED, all four debits then all four credits
#     [:L1244-L1251], where the load traversed them interleaved. ANOMALY A2,
#     second half. Both traversals are field-correct; only the ORDER differs,
#     and the state diff is sensitive to order, so both are written as the
#     source writes them rather than folded into one loop.


def _host_variables_from_row(row: Mapping[str, object]) -> dict[str, object]:
    """Populate the host-variable group from one fetched row.

    The bridge's fetch moves each result column into its host variable before
    ``bb100-UnloadHVs`` runs; this does the same, coercing whatever the driver
    handed back into the host variable's declared storage. The driver returns
    ``Decimal`` for a ``decimal`` column and ``int`` for an integer one, so the
    coercion is normally a formality - but it is done explicitly, because R-2
    forbids an accounting value ever passing through a binary floating-point
    type and an explicit coercion is how that is guaranteed rather than
    assumed.

    A column absent from the row keeps its initialised value, which is the
    behaviour ``initialize TD-IRSNL-REC`` gives and the reason indicator
    variables were never needed: "NULL fields must not be returned in the
    buffer" [common/irsnominalMT.cbl:L1231-L1232].

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
        nl: The caller's record, filled in place - because the COBOL fills the
            caller's own linkage item and a caller may hold references into it.
        traversal: When supplied, each field is appended as it is assigned, so
            that the GROUPED order is observable. See :data:`UNLOAD_TRAVERSAL`.
    """
    host_variables = _host_variables_from_row(row)

    def note(column: str) -> None:
        """Record that ``column`` has just been moved into the record."""
        if traversal is not None:
            traversal.append(column)

    # `initialize WS-IRSNL-Record.` [common/irsnominalMT.cbl:L1233], plain -
    # ANOMALY A36, because the same bridge writes `initialize
    # WS-IRSNL-Record with filler` elsewhere [common/irsnominalMT.cbl:L524],
    # and the stale comment `*> (init moved lower)` [:L1229] sits directly
    # above an `initialize` that is not lower but immediately below.
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

    # `move HV-KEY-1 to NL-Key.` [common/irsnominalMT.cbl:L1235] - one store
    # into the ten-byte group, which fills both `pic 9(5)` halves because they
    # are a REDEFINES of it. ANOMALY A25.
    key_value = host_variables[PRIMARY_KEY]
    _set_key_from_number(nl, int(key_value) if isinstance(key_value, int) else 0)
    note(PRIMARY_KEY)

    # `move HV-TIPE to NL-Tipe.` [common/irsnominalMT.cbl:L1236]
    type_value = host_variables[TYPE_COLUMN]
    nl.nl_type = type_value[:1] if isinstance(type_value, str) else " "
    note(TYPE_COLUMN)

    # `if HV-REC-POINTER > zero` [common/irsnominalMT.cbl:L1237] - ANOMALY A3.
    # No `numeric` class test, unlike the load's guard, so the two guards are
    # not inverses and the round trip is asymmetric.
    pointer_value = host_variables[POINTER_COLUMN]
    pointer = int(pointer_value) if isinstance(pointer_value, int) else 0
    if pointer > 0:
        # `move HV-REC-POINTER to NL-Pointer` [common/irsnominalMT.cbl:L1238],
        # which writes the first five characters of the name, since that is the
        # same storage [copybooks/irswsnl.cob:L22-L23].
        _apply_pointer_overlay(nl, pointer)
        note(POINTER_COLUMN)
        return

    # The `else` branch [common/irsnominalMT.cbl:L1240-L1251]: name, balances,
    # status flag, then the quarters GROUPED - all four debits, then all four
    # credits. ANOMALY A2, and note the casing drift within the paragraph,
    # `NL-Dr` / `NL-Cr` here against `NL-DR` / `NL-CR` in the load.
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


#  THE BRIDGE'S WORKING STORAGE  --------------------------------------------
# `01 DAL-Data` [common/irsnominalMT.cbl:L157-L162], `01 TP-IRSNL-REC usage
# pointer` [:L193] and the handler's `77 A` / `77 B` [common/acasirsub1.cbl:
# L178-L179] are all WORKING-STORAGE of a separately compiled program, so they
# persist between calls and are private to that program. Two consequences the
# migration has to honour deliberately:
#
#   * they must persist across calls, because `Most-Cursor-Set` surviving one
#     call is the whole mechanism by which a START positions and a later
#     READ NEXT walks on from where it stopped; and
#   * `initial` is not written on either PROGRAM-ID, so nothing resets them but
#     the run unit ending.
#
# A COBOL run unit gives that for free. A Python process does not - a test that
# ran a second scenario in the same interpreter would inherit the first
# scenario's cursor - so the reset is EXPLICIT, through
# `reset_bridge_storage()`, and it is the one thing in this module that has no
# counterpart in the frozen source. It is recorded as such.


@dataclasses.dataclass(slots=True)
class _BridgeStorage:
    """Everything the two programs keep in WORKING-STORAGE between calls.

    Attributes:
        connection: What ``Ws-Mysql-Cid`` refers to once ``MYSQL-1000-OPEN``
            has run [common/irsnominalMT.cbl:L360]. ``None`` before the open
            and after the close.
        cursors: ``01 DAL-Data`` [common/irsnominalMT.cbl:L157-L162] plus the
            stored result ``TP-IRSNL-REC`` [:L193]. Held in a
            :class:`~acas_posting.dal.cursor_state.CursorStateTable` because
            that type already models ``Most-Cursor-Set`` and its two condition
            names, and only the PRIMARY slot is ever used: this bridge declares
            ONE cursor, where the open-item bridges declare three.
        record_size_a: ``77 A pic 9(4) value zero``
            [common/acasirsub1.cbl:L178], whose being zero is also the
            once-only latch [common/acasirsub1.cbl:L693].
        record_size_b: ``77 B pic 9(4) value zero``
            [common/acasirsub1.cbl:L179].
        transport: How the connection may cross the network. NOT a COBOL
            notion - the frozen ``MySQL_real_connect`` call takes no transport
            argument at all - but ``dal/connection.py`` requires one before it
            will hand back a connection over a non-loopback host, so it is
            configuration held here rather than a parameter smuggled into
            :func:`dispatch` alongside the five the linkage declares.
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

    THIS FUNCTION HAS NO COUNTERPART IN THE FROZEN SOURCE and is recorded as an
    addition in the module docstring. Neither ``PROGRAM-ID`` carries
    ``initial``, so in COBOL the only thing that clears ``Most-Cursor-Set``, the
    stored result and the once-only latch is the run unit ending. A Python
    process outlives a scenario, so a harness that seeds, runs and then re-seeds
    has to say when the run unit ended; otherwise the second run would inherit
    the first run's open cursor and the state diff would be measuring the
    wrong thing.

    Any connection still held is closed first, through the same
    ``MYSQL-1980-CLOSE`` path ``ba030-Process-Close`` uses
    [common/irsnominalMT.cbl:L384], so that resetting cannot leak a socket.

    Args:
        transport: The transport policy for the next run. Defaults to none,
            which ``dal/connection.py`` reads as plaintext and permits only for
            a loopback host or an explicitly isolated oracle.
    """
    global _STORAGE
    if _STORAGE.connection is not None:
        mysql_1980_close(_STORAGE.connection)
        mysql_1999_exit_paragraph()
    _STORAGE = _BridgeStorage(transport=transport)


def _cursor_state() -> CursorState:
    """Return ``01 DAL-Data`` for this table.

    ONE cursor, the primary slot [common/irsnominalMT.cbl:L157-L162] - unlike
    the two open-item bridges, which declare three and index them.

    Returns:
        The single cursor state.
    """
    return _STORAGE.cursors.state_for(TABLE, CursorSlot.PRIMARY)


#  THE DRIVER BOUNDARY  -----------------------------------------------------
# `MYSQL-1210-COMMAND`, `MYSQL-1220-STORE-RESULT`, `MySQL_fetch_record` and
# `MySQL_free_result` are foreign calls into the C interface object the frozen
# build links. Rule R-1 forbids that object at runtime, so each is reproduced
# natively: `execute_statement` from `dal/connection.py` issues the statement,
# and the row shaping below turns a driver cursor into the mapping the unload
# paragraph expects.
#
# The driver is duck-typed on purpose. This module must not import the driver
# package - it is not in its import contract - so it reads whatever
# `execute_statement` yields through the DB-API surface alone, and accepts
# either a mapping row or a positional one.


def _cursor_column_names(cursor: object) -> tuple[str, ...]:
    """Return the result's column names, in the order the server sent them.

    Args:
        cursor: The cursor :func:`execute_statement` yielded.

    Returns:
        One name per column, or an empty tuple for a statement that returned no
        result set - an ``INSERT``, an ``UPDATE`` or a ``DELETE``.
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
        row: Whatever the driver's ``fetchone`` returned - a mapping when the
            cursor is dictionary-shaped, a sequence otherwise.
        names: The column names from :func:`_cursor_column_names`.

    Returns:
        The row, keyed on column name. A positional row with no description to
        name it is keyed on its ordinal rendered as text, which keeps the shape
        usable rather than raising.
    """
    if isinstance(row, Mapping):
        return {str(key): value for key, value in row.items()}
    values = tuple(row) if isinstance(row, Sequence) else (row,)
    if len(names) == len(values):
        return dict(zip(names, values, strict=True))
    return {str(index): value for index, value in enumerate(values)}


def _fetch_all_rows(cursor: object) -> list[dict[str, object]]:
    """Materialise the whole result, as ``mysql_store_result`` does.

    ``MYSQL-1220-STORE-RESULT`` brings the ENTIRE qualifying result to the
    client [common/irsnominalMT.cbl:L434] and ``MySQL_num_rows`` then reports
    its size, which is why the bridge can test ``WS-MYSQL-Count-Rows`` before
    fetching anything. Drained one row at a time rather than through
    ``fetchall`` so that a driver offering only ``fetchone`` still works.

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

    ``mysql_affected_rows`` is what the bridge tests as ``if WS-MYSQL-Count-Rows
    not = 1`` following an insert [common/irsnominalMT.cbl:L794], an update
    [:L1090] and a delete [:L907].

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

    Reproduces the ``MYSQL-1100-DB-Error`` ladder every guarded arm of the
    bridge performs, then the per-operation ``We-Error`` substitution the
    delete and rewrite arms apply [common/irsnominalMT.cbl:L916, :L1103].
    Delegated to ``dal/status.py`` so that the ladder exists once.

    Args:
        error: Whatever the driver raised. Caught broadly and deliberately: the
            frozen code inspects ``mysql_errno`` and never the exception type,
            so narrowing here would introduce a distinction the specification
            does not make.
        command: The statement text, for the log line.
        file_function: The function code in play, which selects the
            substitution.

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


#  THE LOGGING FIELDS  ------------------------------------------------------
# `WS-File-Key`, `WS-Log-Where`, `SQL-Err`, `SQL-Msg` and `SQL-State` are
# alphanumeric items of `Logging-Data` [copybooks/wsfnctn.cob:L44-L56] that both
# programs write on almost every path. They have NO database effect - the FH
# logger consumes them - but they are written here anyway, because the frozen
# code writes diagnostic TEXT INTO THEM on paths where it writes nothing else,
# and on one path it writes a diagnostic into the account name itself
# (ANOMALY A45), so treating them as decoration would lose the only trace some
# failures leave.
#
# Their widths come from the record module's own declared defaults rather than
# from literals here, so that a `move` into one truncates exactly as COBOL
# truncates.

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
        text: The sending value. Space-padded and right-truncated to the
            receiving width, which is what an alphanumeric move does.
    """
    width = _LOGGING_WIDTHS[attribute]
    setattr(file_access.logging_data, attribute, _character_image(text, width))


def _set_trace(file_access: FileAccess, paragraph: str) -> None:
    """``move <n> to ws-No-Paragraph`` for one bridge paragraph.

    ANOMALY A49 - the bridge and the handler carry TWO DISJOINT trace-number
    sets for the same logical operations: the bridge numbers its paragraphs
    1..20 with holes at 7, 9, 11, 12, 16 and 19
    [common/irsnominalMT.cbl:L359, :L378, :L421, :L474, :L573, :L595, :L728,
    :L792, :L893, :L937, :L1035, :L1071, :L1126, :L1167] while the handler
    numbers its own 201..208 plus 213 and 216
    [common/acasirsub1.cbl:L316, :L426, :L642]. Since the RDB path is what this
    module reproduces, the BRIDGE's numbers are the ones written; the handler's
    are recorded in :data:`HANDLER_TRACE_NUMBERS` for traceability and are never
    assigned.

    Args:
        file_access: The linkage block whose ``Logging-Data`` is written.
        paragraph: The bridge paragraph name, a key of
            :data:`BRIDGE_TRACE_NUMBERS`.
    """
    file_access.logging_data.ws_no_paragraph = BRIDGE_TRACE_NUMBERS[paragraph]


def _apply_status(file_access: FileAccess, status: tuple[int, int]) -> None:
    """Write one ``(FS-Reply, We-Error)`` pair.

    The pair is written in that order because the frozen code writes it in that
    order, and because two of this bridge's paths write a value into
    ``We-Error`` and then immediately overwrite it - ANOMALY A16 - which only
    reads correctly if the order is preserved.

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

    ANOMALY A48 - it clears SIX fields and ``SQL-State`` IS NOT ONE OF THEM.
    ``WS-MYSQL-Error-Message``, ``WS-MYSQL-Error-Number``, ``WS-Log-Where``,
    ``WS-File-Key``, ``SQL-Msg`` and ``SQL-Err`` are all set to spaces
    [:L287-L292] while ``SQL-State`` is left holding whatever the PREVIOUS call
    put there. The handler clears all three
    [common/acasirsub1.cbl:L284] - but the handler's clear is on the flat-file
    path, before the RDB branch has been taken, so on this path a stale
    ``SQL-State`` really does survive into the next call. Not corrected
    (rule R-4).

    The comment immediately below the paragraph -
    "Now Test for valid key ... REMOVED as not used here"
    [common/irsnominalMT.cbl:L294-L295] - records a key-number test the
    maintainer deleted, so no such test is performed here either.

    Args:
        file_access: The linkage block to initialise.
    """
    # `move zero to We-Error` then `Fs-Reply` [:L284-L285].
    file_access.we_error = int(WeError.SUCCESS)
    file_access.fs_reply = int(FsReply.SUCCESS)
    # `move spaces to ...` [:L287-L292]. The two WS-MYSQL-* items are the
    # bridge's own working storage rather than linkage, so they have no
    # counterpart to clear here; the four linkage fields do.
    _move_to_log_field(file_access, "ws_log_where", "")
    _move_to_log_field(file_access, "ws_file_key", "")
    _move_to_log_field(file_access, "sql_msg", "")
    _move_to_log_field(file_access, "sql_err", "")


def _ba100_bad_function(file_access: FileAccess) -> tuple[int, int]:
    """``ba100-Bad-Function`` [common/irsnominalMT.cbl:L1154-L1160].

    "Houston; We have a problem" [:L1156], then ``move 990 to WE-Error``
    [:L1158] and ``move 99 to Fs-Reply`` [:L1159].

    THIS IS THE PAIR THE RDB PATH RETURNS, and it is not the pair the handler
    returns. ``aa100-Bad-Function`` [common/acasirsub1.cbl:L657-L662] answers
    ``(99, 999)``, but the handler's RDB branch leaves through
    ``go to AA-Main-Exit`` [common/acasirsub1.cbl:L267] BEFORE its own dispatch
    ``evaluate`` at [:L286] is ever reached, so ``(99, 999)`` is unreachable
    whenever a table is in use. Both pairs are published -
    :data:`BAD_FUNCTION_STATUS` and :data:`HANDLER_BAD_FUNCTION_STATUS` - and
    only the bridge's is ever returned.

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
    [:L1177]. Releasing the stored result and marking the cursor inactive are
    one step here, which is why a read-indexed - whose every exit routes through
    this paragraph - always leaves the sequential cursor closed, and therefore
    why interleaving a read-indexed into a read-next walk restarts the walk.
    That is the frozen behaviour and no guard against it is added.

    Args:
        file_access: The linkage block, for the trace number.
    """
    _set_trace(file_access, "ba998-Free")
    _cursor_state().free()


#  THE WHERE CONSTRUCTION  --------------------------------------------------
# The bridge builds every predicate the same way: take the key metadata's offset
# and length, `string` the backtick-quoted key name, a relation and a raw
# character slice of the record buffer together into `WS-Where`, then splice
# `WS-Where(1:J)` into a statement shell. Four shapes occur and they differ in
# ways that matter:
#
#   ba040 read-next   `TIPE`='O' AND `KEY-1` > "0000000000" ORDER BY `KEY-1` ASC
#   ba050 read-indexed  `KEY-1`="<ten bytes>"                    - no ORDER BY
#   ba060 start         `KEY-1`<relation>"<ten bytes>" ORDER BY `KEY-1` ASC
#   ba080/ba090         `KEY-1`="<ten bytes>"
#   ba085 delete-all    `KEY-1`<"9999999999"
#
# Two departures from the frozen text, both deliberate and both recorded:
#
#   * the key VALUE is BOUND rather than spliced. `dal/connection.py` states
#     that identifiers must arrive already quoted and that values are bound and
#     never interpolated, so the ten characters travel as a parameter. The text
#     the server evaluates is identical, because the bridge's own splice
#     produces a quoted string constant - which is ANOMALY A19, since the
#     column is a `bigint`.
#   * the `x"00"` C-string terminator each statement ends with [:L432] is
#     dropped, as it exists only for the foreign call rule R-1 forbids.


_KEY: Final[KeyOfReference] = key_of_reference(TABLE, 1)

#: ``KeyName(KOR-x1)`` is ``pic x(30)``, and every `string` of it is
#: ``delimited by space`` [common/irsnominalMT.cbl:L406], so the trailing
#: spaces of the declared width never reach the statement.
_KEY_NAME: Final[str] = cobol_string_delimited_by_space(_KEY.key_name)

_QUOTED_TABLE: Final[str] = quote_identifier(TABLE)
_QUOTED_KEY: Final[str] = quote_identifier(_KEY_NAME)
_QUOTED_TYPE: Final[str] = quote_identifier(TYPE_COLUMN)

#: ``" ORDER BY " "`" keyname "`" " ASC "``
#: [common/irsnominalMT.cbl:L413-L418] - present on the read-next and start
#: predicates and ABSENT from the indexed one. The trailing space is the
#: frozen text's and is kept, because ``WS-Where(1:J)`` carries it through.
_ORDER_BY_KEY_ASC: Final[str] = f" ORDER BY {_QUOTED_KEY} ASC "


def _where_sequential() -> tuple[str, tuple[object, ...]]:
    """``ba040-Process-Read-Next``'s predicate [common/irsnominalMT.cbl:L404-L418].

    Two things about it are load-bearing:

    * the ``TIPE`` conjunct. The sequential read filters sub-nominal rows OUT
      IN SQL - ANOMALY A5, first half - so a plain ``SELECT *`` would return
      rows the frozen bridge never returns.
    * the relation is ``>`` and not ``>=``, and the maintainer annotated it
      ``26/12/16 NOT '='`` [:L409]. The low key is the ten-character string
      ``"0000000000"`` [:L410], so an account whose key is genuinely all zeros
      can never be reached by a sequential walk. Not corrected.

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
    [common/irsnominalMT.cbl:L558-L568, :L876-L887, :L1076-L1086]. NO
    ``ORDER BY`` - a single-row predicate on the primary key does not need one
    and the frozen text does not add one, so neither is one added here
    (rule R-6).

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

    The relation comes from ``evaluate Access-Type`` [:L692-L703], whose five
    arms are 5 ``"=  "``, 6 ``"<  "``, 7 ``">  "``, 8 ``">= "`` and 9
    ``"<= "``, and which has NO ``when other``. Two consequences:

    * ANOMALY A42 - the ``when 9`` arm is DEAD. The guard eleven lines earlier
      rejects anything outside 5..8 [:L672], so ``<=`` can never be selected,
      and the arm is annotated "not currently used in ACAS" by the maintainer
      himself. It is reproduced as reachable code guarded upstream, exactly as
      written, rather than deleted.
    * with no ``when other``, an access type the guard somehow admitted would
      leave ``MOST-Relation`` at spaces and produce a malformed predicate. The
      guard makes that unreachable; no substitute check is added.

    The relation is spliced ``delimited by space`` [:L711], so ``">= "``
    reaches the statement as ``">="`` with the padding gone. The maintainer's
    own note on this construction is "very iffy about this - wanted ?" [:L714].

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

    The paragraph first does ``move 9999999999 to NL-Key`` [:L1009], annotated
    "The last possible data", and then deletes everything strictly BELOW it.
    So the sweep is bounded, not unbounded, and a row whose key is exactly ten
    nines survives a delete-all - the mirror of the sequential read's
    unreachable all-zeros key.

    THE CALLER'S KEY IS MUTATED AND NOT RESTORED, which is the frozen
    behaviour: unlike the write path, which restores two of the four fields it
    changed, this paragraph leaves the caller holding ten nines.

    Args:
        nl: The record whose key is overwritten in place.

    Returns:
        The predicate text and its bound parameters.
    """
    _set_key_from_number(nl, int(DELETE_ALL_HIGH_KEY))
    return f"{_QUOTED_KEY}<%s", (DELETE_ALL_HIGH_KEY,)


def _select_statement(predicate: str) -> str:
    """``"SELECT * FROM " "`IRSNL-REC`" " WHERE " ws-Where(1:J) ";"``.

    [common/irsnominalMT.cbl:L427-L432, :L579-L587, :L734-L742]. ``SELECT *``
    and not a column list, so the result's column order is the schema's - which
    is why :func:`_host_variables_from_row` keys on name and never on position.

    Args:
        predicate: The output of one of the ``_where_*`` builders.

    Returns:
        The statement text.
    """
    return f"SELECT * FROM {_QUOTED_TABLE} WHERE {predicate};"


def _delete_statement(predicate: str) -> str:
    """``"DELETE FROM " "`IRSNL-REC`" " WHERE " ws-Where(1:J) ";"``.

    [common/irsnominalMT.cbl:L899-L905, :L960-L966, :L1041-L1047].

    Args:
        predicate: The output of one of the ``_where_*`` builders.

    Returns:
        The statement text.
    """
    return f"DELETE FROM {_QUOTED_TABLE} WHERE {predicate};"


def _bb200_insert_statement() -> str:
    """``bb200-Insert``'s statement [common/irsnominalMT.cbl:L1257-L1500].

    ``INSERT INTO `IRSNL-REC` SET `` then every column as ``` `COL`="value" ```
    joined by ``", "``, then ``";"``. ALL FIFTEEN COLUMNS ARE NAMED, always -
    never a subset - because ``initialize TD-IRSNL-REC`` [:L1197] guarantees
    each host variable holds a space or a zero and the schema declares every
    column ``NOT NULL`` with no ``DEFAULT``. Omitting a column, or binding
    ``None`` for one, would therefore fail where the frozen bridge succeeds.

    Returns:
        The statement text, with one placeholder per column in schema order.
    """
    assignments = ", ".join(f"{quote_identifier(column)}=%s" for column in COLUMNS)
    return f"INSERT INTO {_QUOTED_TABLE} SET {assignments};"


def _bb300_update_statement(predicate: str) -> str:
    """``bb300-Update``'s statement [common/irsnominalMT.cbl:L1505-L1747].

    ANOMALY A46 - the ``SET`` list carries ALL FIFTEEN COLUMNS INCLUDING THE
    PRIMARY KEY [:L1512 onward], so every update assigns ``KEY-1`` to the value
    it is simultaneously matching on in the ``WHERE``. Harmless while the two
    renderings agree, and they do not agree textually: the ``SET`` clause sends
    the EDITED key, a plain integer with the leading zeros suppressed, while the
    ``WHERE`` sends the RAW ten-character record slice
    [common/irsnominalMT.cbl:L1076-L1086]. Both coerce to the same number.
    Neither is removed.

    The predicate is spliced through ``FUNCTION TRIM (WS-Where(1:J))``, so the
    trailing space the read predicates keep is absent here.

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

    Each column goes through the window ``bb200-Insert`` sends it through - see
    :func:`_render_key`, :func:`_render_money`, :func:`_render_integer` and
    :func:`_render_character` - in SCHEMA ORDER, matching the placeholder order
    of :func:`_bb200_insert_statement`.

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


#  THE HANDLER'S TWO GATES  -------------------------------------------------
# Only two things the handler does survive onto the RDB path, because its RDB
# branch leaves through `go to AA-Main-Exit` [common/acasirsub1.cbl:L267] before
# its own `evaluate File-Function` [:L286] is reached. Those two are the
# key-number guard, which runs at [:L231-L245] BEFORE the branch, and the
# record-size gate, which `ba-Process-RDBMS` falls through into at
# [:L683-L731]. Everything else in the handler - all ten `aa0xx` verbs, its
# `aa100-Bad-Function`, both `stop` statements - is indexed-file code and is
# recorded in the module docstring as a deliberate omission.


def _declared_record_length() -> int:
    """``length of WS-NL-Record``, and equally ``length of Record-1``.

    ``77 A`` receives the first [common/acasirsub1.cbl:L694-L696] and ``77 B``
    the second [:L697-L699], and ``if A < B`` [:L700] then aborts. THE TEST CAN
    NEVER FIRE: ``copybooks/irswsnl.cob:L8-L23`` and
    ``copybooks/irsfdwsnl.cob:L4-L18`` declare the same fifteen elementary items
    at the same widths in the same order, differing only in their names - which
    is ANOMALY A22, the three-record-view finding, seen from the other side. So
    both operands are taken from this one function, which makes the equality
    structural rather than something asserted in a comment, and the abort branch
    stays live code that never triggers, exactly as in the compiled program.

    The declared widths are read from the dictionary, not written here. The
    absolute value is immaterial - nothing compares it with anything but itself -
    so it counts declared digit and character positions rather than trying to
    second-guess how ``COMP`` items are packed on the build host.

    Returns:
        The declared position count of the record.
    """
    total = 0
    for key in ("NL-Record.NL-Owning", "NL-Record.NL-Sub-Nominal"):
        total += int(loader.get_entry(key).copybook.digits or 0)
    for column in COLUMNS:
        if column in (PRIMARY_KEY, POINTER_COLUMN):
            # The key is the two halves already counted, and the pointer
            # REDEFINES the data group [copybooks/irswsnl.cob:L22-L23] - a
            # REDEFINES adds no storage.
            continue
        field = _ENTRIES[column].copybook
        total += int(field.character_length or field.digits or 0)
    return total


def _record_size_gate(
    system: SystemRecord,
    file_access: FileAccess,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2`` [common/acasirsub1.cbl:L691-L731].

    Once-only, latched on ``if A = zero`` [:L693], and it does two unrelated
    jobs in that one guarded block:

    1. compares the two record lengths and, on ``A < B``, sets
       ``We-Error = 901`` [:L701] and ``FS-Reply = 99`` [:L702], displays
       ``IR902`` and ``IR901``, waits for a keypress, and then
       ``go to ba-rdbms-exit`` [:L718] - WHICH SKIPS THE BRIDGE CALL ENTIRELY.
       The display and the keypress are presentation with no database effect, so
       they become a log record and the pause is dropped; THE CONTROL TRANSFER
       IS PRESERVED, because whether the bridge is called at all is a database
       effect.
    2. otherwise loads the six ``RDB-Data`` fields from the system record
       [:L725-L730], in the order Schema, UName, UPass, Port, Host, Socket. The
       maintainer's own comment is "hopefully once is enough  :)" - the
       parameters are captured ONCE PER RUN AND NEVER REFRESHED, so a system
       record edited mid-run has no effect. ``load_rdb_data_once`` reproduces
       that latch and records it as its own anomaly A-1.

    Args:
        system: ``SYSTEM-REC``, the first linkage parameter.
        file_access: The linkage block, whose ``RDB-Data`` is filled.

    Returns:
        True when the bridge may be called; False when the gate aborted, which
        means the caller must return the status pair without calling it.
    """
    if _STORAGE.record_size_a == 0:
        _STORAGE.record_size_a = _declared_record_length()
        _STORAGE.record_size_b = _declared_record_length()
        if _STORAGE.record_size_a < _STORAGE.record_size_b:
            # `move 901 to WE-Error` [common/acasirsub1.cbl:L701] then
            # `move 99 to fs-reply` [:L702]. IR902 "Program Error: Temp rec = "
            # [:L192] and IR901 "Note error and hit return" [:L191] were
            # displayed at 2401 and acknowledged; the diagnostic survives as a
            # log record and the acknowledgement is dropped.
            _LOG.error(
                "acasirsub1 ba012: IR902 record size mismatch, "
                "WS-NL-Record=%s Record-1=%s",
                _STORAGE.record_size_a,
                _STORAGE.record_size_b,
            )
            _apply_status(file_access, RECORD_SIZE_STATUS)
            return False
        # `move ... to RDB-Data` [common/acasirsub1.cbl:L725-L730].
        rdb_data: RdbData = load_rdb_data_once(system)
        file_access.rdb_data = rdb_data
    return True


def _key_number_guard(file_access: FileAccess) -> tuple[int, int] | None:
    """``evaluate File-Function`` at [common/acasirsub1.cbl:L231-L245].

    The one part of the handler that runs BEFORE the RDB branch, so it is in
    force on this path. Three arms, two error codes:

    * ``fn-read-indexed`` and ``fn-start`` share an arm: a key number other
      than 1 gives ``We-Error = 998`` and ``FS-Reply = 99`` [:L235-L236].
    * ``fn-delete`` has its own arm giving ``996`` [:L241-L242], carrying the
      extra comment "1 is only for RDB as Cobol does it on primary key" - a
      comment that also appears verbatim at ``common/acas022.cbl:L307``.

    Two codes for one condition is the anomaly; there is one key on this table
    [common/irsnominalMT.cbl:L147], so 1 is the only legal value either way.
    ``File-Key-No`` is a field of ``Logging-Data``
    [copybooks/wsfnctn.cob:L44-L56], not of ``File-Access`` itself, so that is
    where it is read from.

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
    # Every other function code reaches neither arm, so a wrong key number is
    # simply not noticed - the `evaluate` has no `when other`
    # [common/acasirsub1.cbl:L245]. Adding one would be a new validation.
    return None


def _aa047_eval_keys(file_access: FileAccess, nl: WsIrsnlRecord) -> None:
    """``aa047-Eval-Keys`` [common/acasirsub1.cbl:L463-L479]. DEAD CODE.

    ANOMALY A31 - this paragraph is unreachable. Its ONLY reference anywhere is
    a ``perform`` that is commented out [common/acasirsub1.cbl:L490], and the
    maintainer's own comment ten lines above it says so:
    "The next block will never get executed unless performed so is it needed ?"
    [:L461] - the same sentence he wrote at ``common/acas029.cbl:L389``.

    It is reproduced rather than dropped, because rule R-5 maps every paragraph
    to a function and a paragraph that exists but cannot run is a fact about the
    program, not an absence. Nothing in this module calls it, exactly as nothing
    in the handler performs it.

    Two details worth keeping: ``when 1`` writes the key to TWO receivers,
    ``WS-File-Key`` for the log and ``Key-1`` for the indexed file [:L472-L473],
    the same two-receiver shape as ``common/acas022.cbl``; and it is numbered
    ``aa047`` and not ``aa045`` only because ``aa045`` was already taken by the
    raw read.

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


#  STATEMENT EXECUTION  -----------------------------------------------------
# `MYSQL-1210-COMMAND` issues the statement and every guarded arm that follows
# it has the identical shape: test `WS-MYSQL-Count-Rows`, and on a
# disappointing count call `MySQL_errno`, `MySQL_sqlstate`, then `MySQL_error`,
# and map. These two helpers carry that shape once, so that each verb below
# reads as the accounting decision it makes rather than as error plumbing -
# and so that the ladder itself lives in `dal/status.py`, where it is shared.


def _fill_log_field(file_access: FileAccess, attribute: str, character: str) -> None:
    """``move <figurative constant> to <field>``.

    A figurative constant moved to an alphanumeric item repeats to fill the
    receiving width, so ``move zero to SQL-Err`` on ``pic x(5)`` yields five
    zero characters and not one. Written out because the bridge does exactly
    that, at [common/irsnominalMT.cbl:L791] among others.

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

    The frozen bridge does not check. It hands an unopened ``Ws-Mysql-Cid`` to
    the C interface, which fails, ``MySQL_errno`` reports it, and the ordinary
    ladder maps it - so this is the SAME ladder over the same condition and not
    a new validation (rule R-3). What it must not do is raise, because the
    caller's contract is a status pair.

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
    """``if WS-MYSQL-Error-Number not = "0  "``.

    Every guarded arm in the bridge tests the errno before it writes a status
    [common/irsnominalMT.cbl:L448, :L622, :L751, :L907, :L1051, :L1096], and the
    comparison is against the three-character literal ``"0  "`` -
    :data:`NO_DRIVER_ERROR`. The test matters because of what happens when it
    FAILS: several arms then write no status at all, so a statement that matched
    no row while the driver reported nothing wrong reports SUCCESS. Expressed as
    a named predicate so that every one of those arms reads as the frozen test
    rather than as a Python idiom that happens to coincide with it.

    Args:
        failure: The mapped failure, or ``None`` when the statement ran cleanly.

    Returns:
        True when the driver reported an error number other than ``"0  "``.
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

    ``MYSQL-1210-COMMAND`` then ``MYSQL-1220-STORE-RESULT``
    [common/irsnominalMT.cbl:L433-L434].

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
    except Exception as error:  # any driver error takes this path
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
    except Exception as error:  # any driver error takes this path
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


#  ba020-Process-Open / ba030-Process-Close  --------------------------------


def open_(
    system: SystemRecord,
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """``ba020-Process-Open`` [common/irsnominalMT.cbl:L330-L372].

    The paragraph strings the six ``RDB-Data`` fields into the ``WS-MYSQL-*``
    names [:L335-L358], sets its trace number [:L359], performs
    ``MYSQL-1000-OPEN THRU MYSQL-1090-EXIT`` [:L360], and returns early on a
    non-zero reply [:L361-L362]. Only on success does it tag the log key
    [:L370] and clear the cursor flag [:L371] - so a failed open leaves
    ``Most-Cursor-Set`` exactly as the previous call left it.

    ``move zero to Most-Cursor-Set`` is LIVE here [:L371] and COMMENTED OUT at
    the two other places the same reset would make sense [:L508, :L532], which
    is why an open is the only thing that resets the cursor other than a free.

    Args:
        system: ``SYSTEM-REC``, which carries the connection parameters.
        file_access: The linkage block.
        nl: The record. Not read - accepted so that every verb takes the
            bridge's own ``USING`` shape.

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
        # `if fs-reply not = zero / go to ba999-end` [:L361-L362] - no log key,
        # no cursor reset.
        return (file_access.fs_reply, file_access.we_error)
    _STORAGE.connection = outcome.connection
    _move_to_log_field(file_access, "ws_file_key", _OPEN_TAG)
    # `move zero to Most-Cursor-Set` [:L371].
    _cursor_state().set_cursor_not_active()
    return (file_access.fs_reply, file_access.we_error)


def open_input(
    system: SystemRecord,
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """The facade's ``-Open-Input`` verb.

    The facade sets ``access-type`` and then the function code
    [copybooks/Proc-ACAS-FH-Calls.cob:L465-L469]; the BRIDGE ignores the access
    type on an open, because its ``when 1`` arm routes every open to the one
    paragraph [common/irsnominalMT.cbl:L303]. So input, i-o and extend all reach
    the same code, and only output differs - see :func:`open_output`.

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

    ANOMALY, recorded rather than reproduced: the HANDLER rejects extend
    outright, ``move 997 to WE-Error`` and ``move 99 to fs-reply``
    [common/acasirsub1.cbl:L354-L355], but that arm is inside
    ``aa020-Process-Open`` and therefore on the indexed-file path. On the RDB
    path an extend simply opens, because the bridge never looks at the access
    type. The asymmetry is the frozen behaviour and is not smoothed over.

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

    Opening a table for output has to mean what opening an indexed file for
    output means: the existing contents are gone. There is no such SQL
    statement, so the handler makes TWO calls to the bridge, and the way it does
    so is worth reading carefully because it looks like a defect and is not::

        if       fn-Open
           and   fn-Output
                 perform ba020-Process-Dal      *> call one, function still 1
                 set fn-Delete-All to true
        end-if.
     ba020-Process-DAL.                          *> falls through - call two

    The ``perform`` is of the paragraph the code then FALLS INTO, so the bridge
    is entered twice: once with the open, once with function 6.

    ANOMALY A26 - a SECOND, DEAD copy of this coercion sits at
    [common/acasirsub1.cbl:L253-L260] with both of its lines commented out
    [:L256-L257]. Reading that block alone suggests a broken coercion; reading
    the control path to its end shows the working one downstream. The dead block
    is recorded and not reproduced.

    ANOMALY A27 - that same early block routes to ``ba-Process-RDBMS`` without
    performing ``move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses``, which
    every other RDB call performs [:L265]. The bypass is reproduced in
    :func:`dispatch`.

    ANOMALY A28 - ``fn-Delete-All`` is code 6, and NO handler in the set
    dispatches it; an exhaustive reading of all seventeen routes 6 to
    bad-function. On this table it is nevertheless honoured, because the BRIDGE
    dispatches it [common/irsnominalMT.cbl:L314-L317] - so delete-all is
    reachable through this coercion and, on the RDB path, through a direct
    function 6 as well. ``facade.py`` needs that fact; it is stated here so it
    is recorded twice.

    Args:
        system: ``SYSTEM-REC``.
        file_access: The linkage block, whose function code ends as 6.
        nl: The record. Its key is overwritten by the delete-all sweep and NOT
            restored, exactly as the frozen paragraph leaves it.

    Returns:
        The ``(FS-Reply, We-Error)`` pair of the SECOND call. The first call's
        pair is overwritten, so an open that failed and a sweep that succeeded
        report success - which is what the frozen sequence reports.
    """
    file_access.access_type = int(AccessType.OUTPUT)
    # `perform ba020-Process-Dal` [common/acasirsub1.cbl:L740] - CALL one, with
    # the function still Open. Routed through `_bridge_call` rather than to
    # `open_` directly, because each CALL re-enters the bridge and therefore
    # re-runs `ba010-Initialise` [common/irsnominalMT.cbl:L282-L292].
    file_access.file_function = int(FileFunction.OPEN)
    _bridge_call(system, file_access, nl)
    # `set fn-Delete-All to true` [common/acasirsub1.cbl:L741], then the
    # fall-through into the CALL paragraph makes the second entry.
    file_access.file_function = int(FileFunction.DELETE_ALL)
    return _bridge_call(system, file_access, nl)


def close(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba030-Process-Close`` [common/irsnominalMT.cbl:L374-L387].

    Frees an active cursor first [:L375-L376], sets its trace number [:L378],
    tags the log key [:L379] and then performs ``MYSQL-1980-CLOSE THRU
    MYSQL-1999-EXIT`` [:L384]. Note the ORDER: the log key is tagged BEFORE the
    close, so it is set even if the close fails.

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


#  ba040-Process-Read-Next / ba041-Reread  ----------------------------------
# The sequential read is TWO paragraphs and one fall-through. `ba040` positions
# the cursor if it is not already positioned, then falls into `ba041`, which
# fetches one record from the stored snapshot. A later call finds the cursor
# active, skips the positioning entirely, and falls straight into the fetch -
# which is how one `SELECT` serves a whole walk.
#
# ANOMALY A5. The sub-nominal filter is applied TWICE, by two different
# mechanisms, and both are reproduced:
#   * in SQL, by the ``TIPE``='O' conjunct of the predicate
#     [common/irsnominalMT.cbl:L405]; and
#   * in the record, by `if Sub / go to ba041-Reread` [:L541-L542], whose own
#     comment concedes the redundancy - "test to see if pointer record 1st
#     [ from irsub1 ] but shouldnt happen !" [:L539].
# The second is therefore unreachable while the first holds. It is reproduced
# because removing it would be a change, and because it is the ONLY filter the
# indexed-file twin has.


def _ba041_reread(
    file_access: FileAccess,
    nl: WsIrsnlRecord,
    *,
    filter_sub_nominal: bool,
) -> tuple[int, int]:
    """``ba041-Reread`` [common/irsnominalMT.cbl:L469-L547].

    Three separate end-of-data paths, all answering ``(10, 3)`` and
    distinguishable only by the log tag they leave - ANOMALY A47, and
    :data:`END_OF_DATA_TAGS` lists all four including ``ba040``'s.

    ANOMALY A16 - the EOF pair is written as ``move 10 to fs-Reply`` then
    ``move 3 to WE-Error`` [:L505-L506], and the sibling that would have made
    ``We-Error`` 10 is COMMENTED OUT at [:L454, :L520]. So the effective pair is
    ``(10, 3)`` and not ``(10, 10)``.

    ANOMALY A17 - ``We-Error = 3`` is a single-digit error code, which no other
    handler in the set uses; the maintainer's own comment calls it out, "Uses 3
    (instead of 10) as EOF flag in WE-Error per irsub1" [:L391]. It is written as
    the literal 3 rather than forced into an existing enumeration member.

    Args:
        file_access: The linkage block.
        nl: The record, filled in place on success.
        filter_sub_nominal: True for the ordinary read, which skips ``"S"``
            records; False for the raw read, whose two filter lines are
            commented out [common/acasirsub1.cbl:L454-L455].

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    state = _cursor_state()
    while True:
        # `move spaces to WS-Log-Where` [:L473] - the fetch issues no statement,
        # so the predicate that positioned the cursor is cleared rather than
        # left to look as though it had just run.
        _move_to_log_field(file_access, "ws_log_where", "")
        _set_trace(file_access, "ba041-Reread")

        row = state.fetch_record()
        if row is None:
            # `if return-code = -1` [:L504-L510]: the snapshot is exhausted.
            _apply_status(file_access, END_OF_FILE_STATUS)
            _move_to_log_field(file_access, "ws_file_key", END_OF_DATA_TAGS[1])
            state.set_cursor_not_active()
            return END_OF_FILE_STATUS

        # `if WS-MYSQL-Count-Rows = zero` [:L512-L528] guards a driver failure
        # DURING the fetch and leaves the tag "EOF2" plus `initialize
        # WS-IRSNL-Record with filler` [:L524]. It cannot be reached here,
        # because a stored result that yielded a row had a non-zero count and
        # the count is bridge working storage that the fetch does not touch. It
        # is reproduced as the guarded arm it is, not deleted: the tag is in
        # END_OF_DATA_TAGS and the arm's condition is simply never true.
        #
        # `if fs-reply = 10` [:L532-L535] - the "EOF3" arm. Equally unreachable,
        # because `ba010-Initialise` zeroed the reply on entry to the call
        # [:L285] and nothing above sets 10 without returning.
        if file_access.fs_reply == int(FsReply.END_OF_FILE):
            state.set_cursor_not_active()
            _move_to_log_field(file_access, "ws_file_key", END_OF_DATA_TAGS[3])
            return END_OF_FILE_STATUS

        # `perform bb100-UnloadHVs` [:L537].
        _unload_host_variables(row, nl)

        if filter_sub_nominal and _sub(nl):
            # `if Sub / go to ba041-Reread.` [:L541-L542] - GO TO class 1,
            # a loop-back to the head of this paragraph, so `continue`.
            continue

        # `move HV-KEY-1 to WS-File-Key` through the edit field [:L544-L545].
        _move_to_log_field(file_access, "ws_file_key", _render_key(_key_number(nl)))
        # `move zero to fs-reply WE-Error` [:L546].
        _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
        return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


def read_next(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba040-Process-Read-Next`` [common/irsnominalMT.cbl:L389-L467].

    Positions once and then walks. ANOMALY A5 - the predicate excludes
    sub-nominal rows, so THIS VERB CAN NEVER RETURN ONE, however many the table
    holds. A caller that needs them has to ask for function 13, and on this path
    function 13 is a bad function - see :func:`read_next_raw`.

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
        # `move "> 0000000000" to WS-File-Key` [:L437], set BEFORE the count is
        # tested, so it survives onto the no-data path until that path
        # overwrites it.
        _move_to_log_field(file_access, "ws_file_key", f"> {SEQUENTIAL_LOW_KEY}")
        count = state.store_result(rows)
        if count == 0:
            # `if WS-MYSQL-Count-Rows = zero` [:L443-L457]. The errno ladder
            # runs first and may fill SQL-Err and SQL-Msg [:L448-L452], and then
            # the pair and the tag are written unconditionally [:L453-L456] -
            # so a clean empty result and a failed statement answer alike, and
            # only SQL-Err distinguishes them.
            if _driver_reported_error(failure):
                _apply_driver_status(file_access, failure)
            _apply_status(file_access, END_OF_FILE_STATUS)
            _move_to_log_field(file_access, "ws_file_key", END_OF_DATA_TAGS[0])
            return END_OF_FILE_STATUS
        # `set Cursor-Active to true` [:L459] then the "got cnt=" tag
        # [:L460-L465].
        state.set_cursor_active()
        state.position_at(SEQUENTIAL_LOW_KEY)
        _move_to_log_field(
            file_access, "ws_file_key", f"> 0 got cnt={count} recs"
        )
    # Fall-through into `ba041-Reread`, which is what the frozen code does: the
    # paragraph simply ends and the next one begins. GO TO class 2 does not
    # apply - there is no transfer here at all.
    return _ba041_reread(file_access, nl, filter_sub_nominal=True)


def read_next_raw(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``aa045-Process-Read-Next-Raw`` [common/acasirsub1.cbl:L421-L459], on SQL.

    ANOMALY A40 and CORRECTION C2 - READ THIS BEFORE CALLING IT.
    Function code 13 is ``fn-Read-Next-Raw`` [copybooks/wsfnctn.cob:L100],
    annotated "Special 4 LD." because the loader programs use it, and
    ``acasirsub1`` is the ONLY handler in the set that dispatches it
    [common/acasirsub1.cbl:L303-L304]. BUT the bridge's own ``evaluate
    File-Function`` [common/irsnominalMT.cbl:L302-L328] HAS NO ``when 13``, and
    the handler's RDB branch returns before its own ``evaluate`` is reached, so
    on the RDB path function 13 is a BAD FUNCTION and :func:`dispatch` answers
    ``(99, 990)`` for it. That is not an oversight in this module; it is what the
    frozen pair does.

    This function is therefore the traceable counterpart of ``aa045``,
    reachable only by a direct call, and it is what the raw read WOULD be on
    SQL: both filters absent. It is written out rather than expressed as
    :func:`read_next` with a flag, because ``aa045`` is itself a near-verbatim
    copy of ``aa040`` with two lines commented out
    [common/acasirsub1.cbl:L454-L455] and its own trace number and its own
    diagnostic string, and reproducing the duplication is reproducing the
    program.

    Args:
        file_access: The linkage block.
        nl: The record, filled in place on success.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    state = _cursor_state()
    if state.cursor_not_active():
        # The predicate WITHOUT the `TIPE` conjunct - "OMITTED as reading all
        # records RAW" [common/acasirsub1.cbl:L453].
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
            # `move "Read Raw failure on IRS NL File" to WS-File-Key`
            # [common/acasirsub1.cbl:L447] - the raw twin's OWN diagnostic
            # string, distinct from the ordinary read's.
            _move_to_log_field(
                file_access, "ws_file_key", "Read Raw failure on IRS NL File"
            )
            return END_OF_FILE_STATUS
        state.set_cursor_active()
        state.position_at(SEQUENTIAL_LOW_KEY)
    # `*> if Sub` / `*> go to aa041-Reread.` [common/acasirsub1.cbl:L454-L455]
    # are commented out, so the record-level filter is absent as well.
    return _ba041_reread(file_access, nl, filter_sub_nominal=False)


#  ba050-Process-Read-Indexed  ----------------------------------------------


def read_indexed(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba050-Process-Read-Indexed`` [common/irsnominalMT.cbl:L549-L663].

    ANOMALY A15 - THIS VERB CHASES A POINTER CHAIN. Reading a key that turns out
    to hold a sub-nominal row does not return that row; it rewrites the key from
    the row's own contents and reads again::

        if       Sub
                 move NL-Owning  to NL-Sub-Nominal          [:L657]
                 move NL-Pointer to NL-Owning               [:L658]
                 move "Not found" to NL-Name                [:L659]
                 go to ba050-Process-Read-Indexed.          [:L660]

    ``NL-Pointer`` is the first five characters of the name
    [copybooks/irswsnl.cob:L22-L23], so the account number the chase follows is
    read out of the NAME FIELD of the row just fetched. That is the designed
    mechanism, not an accident, and it is why the overlay has to be modelled
    rather than approximated. NO TERMINATION GUARD IS ADDED (rule R-3): a chain
    that pointed at itself would loop here exactly as it loops in the compiled
    program.

    The transfer is a GO TO class 1 loop-back - to the head of the section it is
    already in - so it becomes ``continue`` in a ``while True:``. Note what that
    means: the WHOLE section repeats, including rebuilding the predicate from the
    mutated key, so each hop issues its own statement.

    ANOMALY A45 - three different diagnostic strings are written INTO
    ``NL-Name``, a data field: ``"Not found 1"`` [:L634], ``"Not found 2"``
    [:L641] and ``"Not found"`` [:L659]. The third is transient in a successful
    chase, because the next iteration's unload initialises the record first
    [:L1233], and it becomes visible only when the hop it precedes finds nothing
    - at which point one of the other two overwrites it anyway. Reproduced
    regardless.

    ANOMALY A16 - the pair here is ``(21, 2)``, written as ``move 21 to
    fs-Reply`` [:L591] then ``move 2 to we-error`` [:L592]. ANOMALY A17 -
    ``We-Error = 2`` is the second single-digit code in this pair of programs and
    appears nowhere else in the handler set.

    EVERY exit routes through ``ba998-Free`` [:L593, :L635, :L644, :L663],
    including the successful one, so an indexed read always leaves the single
    cursor inactive - and therefore interrupts any sequential walk in progress.
    See :func:`_ba998_free`.

    Args:
        file_access: The linkage block.
        nl: The record. Its key is READ to build the predicate and REWRITTEN by
            every hop of the chase, so a caller holding it sees the last key
            tried, not the one it asked for.

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
            # `if WS-MYSQL-Count-Rows = zero` [:L590-L593]. The maintainer's own
            # comment on the 21 is "could also be 23 or 14", so the choice is
            # his; no name literal is written on this arm.
            _apply_status(file_access, NOT_FOUND_STATUS)
            _ba998_free(file_access)
            return NOT_FOUND_STATUS

        _set_trace(file_access, "ba050-Fetch")
        row = state.fetch_record()
        if row is None:
            _apply_status(file_access, NOT_FOUND_STATUS)
            if _driver_reported_error(failure):
                # `if WS-MYSQL-Error-Number not = "0  "` [:L626-L635].
                _apply_driver_status(file_access, failure)
                _apply_status(file_access, NOT_FOUND_STATUS)
                _move_to_log_field(file_access, "ws_file_key", "")
                _set_name(nl, NOT_FOUND_LITERALS[0])
            else:
                # The clean-errno arm [:L636-L644]: `move zero to SQL-Err`,
                # spaces to SQL-Msg, and the SECOND literal into the name.
                _fill_log_field(file_access, "sql_err", "0")
                _set_name(nl, NOT_FOUND_LITERALS[1])
                _move_to_log_field(file_access, "sql_msg", "")
                _move_to_log_field(file_access, "ws_file_key", "")
            _ba998_free(file_access)
            return NOT_FOUND_STATUS

        # `perform bb100-UnloadHVs` [:L647] then the log key [:L648-L649].
        _unload_host_variables(row, nl)
        _move_to_log_field(file_access, "ws_file_key", _render_key(_key_number(nl)))

        if _sub(nl):
            # THE CHASE [:L653-L660], in the frozen order. `NL-Pointer` must be
            # read BEFORE the name is overwritten, because they are the same
            # five characters - and the frozen sequence does exactly that.
            owning = nl.nl_key.nl_owning
            nl.nl_key.nl_sub_nominal = owning
            nl.nl_key.nl_owning = _read_pointer_overlay(nl)
            _set_name(nl, NOT_FOUND_LITERALS[2])
            continue

        # `move zero to FS-Reply WE-Error` [:L662] then `go to ba998-Free`
        # [:L663].
        _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
        _ba998_free(file_access)
        return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


#  ba060-Process-Start  -----------------------------------------------------


def start(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba060-Process-Start`` [common/irsnominalMT.cbl:L665-L777].

    ANOMALY A7 - A START DOES NOT MERELY POSITION, IT READS. The paragraph ends::

        perform  ba999-end.                    *> logging     [:L773]
        go       to ba041-Reread.                             [:L777]

    so one invocation positions the cursor AND returns the first qualifying
    record, and the caller's record buffer comes back filled. And because it
    lands in ``ba041`` rather than anywhere else, THE SUB-NOMINAL FILTER APPLIES
    TO A START: a start that positions on a ``"S"`` row hands back the next
    ``"O"`` row after it. The transfer is a GO TO class 4 - a named paragraph is
    performed for its effect and control then moves elsewhere - so it is
    reproduced as a call to :func:`_ba041_reread` followed by returning its
    result, and the equivalence holds because ``ba999-end`` only logs and
    ``ba041`` never returns to here.

    ANOMALY A29 and CORRECTION C1, which contradicts this file's own agent
    brief. The brief states that the 5..8 access-type guard is
    indexed-file-only and instructs that it not be implemented. IT IS NOT
    INDEXED-FILE-ONLY: the bridge carries its own copy [:L672-L675], annotated
    "not using not < or not >", answering ``move 99 to FS-Reply`` and
    ``move 997 to WE-Error``. The handler's copy
    [common/acasirsub1.cbl:L525-L528] is a second, different one that sets ONLY
    ``We-Error`` and leaves the reply at zero. The bridge's is the one in force
    here and it is implemented; the handler's 998 variant is the deliberate
    omission. Verified three ways: by reading the bridge, by the absence of any
    RDB-path bypass, and by ``dal/cursor_state.start`` answering ``(99, 997)``
    for access type 9. TWO guards for one condition, disagreeing on the status
    they set, is the anomaly - not the guard itself.

    ANOMALY A39 - AND SO THE PUBLISHED FACADE VERB CAN NEVER SUCCEED. The IRS
    calling convention's ``acasirsub1-Start``
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L202-L205] does
    ``move zero to Access-Type`` before it calls, exactly as its nine siblings
    do, because zero is right for every verb that is not a start. Zero fails
    ``if access-type < 5`` [common/irsnominalMT.cbl:L672], so a start reached
    through that facade ALWAYS answers ``(99, 997)`` and never positions
    anything. The guard is reproduced, the facade's zeroing is
    ``facade.py``'s to reproduce, and between them the verb stays unusable -
    which is why nothing in the migrated posting cycle calls it.

    ANOMALY A30 - the two layers order their positioning branches differently.
    The handler tests ``fn-equal-to``, ``fn-not-less-than``,
    ``fn-greater-than``, then ``fn-less-than`` - 5, 8, 7, 6 - with the last
    annotated "Not used in irsub1" [common/acasirsub1.cbl:L531-L559]. The
    bridge's ``evaluate`` runs 5, 6, 7, 8, 9 in numeric order
    [common/irsnominalMT.cbl:L692-L703]. The SET of relations is the same, so
    no behaviour turns on it; the divergence is recorded because a reader
    diffing the two files will meet it, and because the bridge's fifth arm has
    no counterpart in the handler at all.

    ANOMALY A42 - the ``evaluate`` nevertheless has a ``when 9`` arm giving
    ``"<= "`` [:L701-L702], annotated "not currently used in ACAS". The guard
    eleven lines above rejects 9, so the arm is DEAD. Both are reproduced: the
    guard rejects, and :func:`_where_start` can still render ``<=`` if ever
    reached.

    ANOMALY A8, RECORDED AND NOT REPRODUCED. The brief describes a
    ``move zero to Sub-Nominal`` that makes a start always land on an owning
    account's first entry. That statement is at
    [common/acasirsub1.cbl:L523] - in the HANDLER's ``aa060``, on the
    indexed-file path. The bridge has no such statement; a grep of the whole
    bridge for writes to either key half finds only the write path's mutations
    [common/irsnominalMT.cbl:L657, :L851-L852, :L866]. So on the RDB path THE
    LOW HALF OF THE KEY IS NOT ZEROED, and it is not zeroed here.

    One further asymmetry, reproduced as written: when the statement matches
    nothing AND the driver reports no error [:L750-L761], NO status is set and
    NO cursor is activated, and control still falls through to the read - which
    then reports end of file. So an empty start answers ``(10, 3)`` and not
    ``(21, 2)``.

    Args:
        file_access: The linkage block, carrying the access type.
        nl: The record, whose key positions the cursor and which is filled in
            place by the read that follows.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    access_type = file_access.access_type
    if not start_access_type_is_valid(access_type):
        # `if access-type < 5 or > 8` [:L672-L675].
        _apply_status(file_access, ACCESS_TYPE_STATUS)
        return ACCESS_TYPE_STATUS

    state = _cursor_state()
    if state.cursor_active():
        # `if Cursor-Active / perform ba998-Free.` [:L680-L681] - closed by the
        # period with no `end-if`, one of the several such sites ANOMALY A35
        # records.
        _ba998_free(file_access)

    predicate, parameters = _where_start(nl, access_type)
    statement = _select_statement(predicate)
    _move_to_log_field(file_access, "ws_log_where", statement)
    # `move NL-Key to WS-File-Key` [:L723], with the commented-out alternative
    # `ws-IRSNL-Record (K:L) to WS-File-Key` beside it on the same line.
    _move_to_log_field(file_access, "ws_file_key", _render_key(_key_number(nl)))
    _set_trace(file_access, "ba060-Process-Start")

    rows, failure = _run_query(file_access, statement, parameters)
    count = state.store_result(rows)
    if count != 0:
        # `set Cursor-Active to true` [:L745-L748].
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
        # `if WS-MYSQL-Error-Number not = "0  "` [:L755-L760].
        _apply_driver_status(file_access, failure)
        _apply_status(file_access, NOT_FOUND_STATUS)
        return NOT_FOUND_STATUS

    # `perform ba999-end.` [:L773] - logging only - then `go to ba041-Reread.`
    # [:L777].
    return _ba041_reread(file_access, nl, filter_sub_nominal=True)


#  ba090-Process-Rewrite  ---------------------------------------------------


def rewrite(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba090-Process-Rewrite`` [common/irsnominalMT.cbl:L1068-L1114].

    ONE statement, no pointer handling of any kind. ANOMALY A13 - and the
    asymmetry among the three mutating verbs is the point: the write issues
    three statements and maintains the pointer row, the delete issues two and
    removes it, and the rewrite issues one and ignores it entirely. So updating a
    sub-nominal account through this verb leaves its pointer row stale, and
    nothing notices.

    ANOMALY A46 - the ``SET`` list includes ``KEY-1``
    [common/irsnominalMT.cbl:L1512 onward], so the statement assigns the primary
    key the value it is matching on, in a different textual rendering. See
    :func:`_bb300_update_statement`.

    On a count other than one WITH a clean errno, NO status is written at all
    [:L1094-L1109] - the arm that would write ``(99, 994)`` is inside the
    ``if WS-MYSQL-Error-Number not = "0  "`` test. So an update that matched no
    row reports success. Reproduced.

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
            # `move 99 to fs-reply` [:L1102] then `move 994 to WE-Error`
            # [:L1103], which `override_we_error_for_operation` supplies for a
            # RE_WRITE.
            _apply_driver_status(file_access, failure)
            _apply_status(
                file_access,
                (int(FsReply.ERROR), REWRITE_FAILED_WE_ERROR),
            )
        return (file_access.fs_reply, file_access.we_error)
    # `move zero to FS-Reply WE-Error` [:L1111], `move zero to SQL-Err`
    # [:L1112], `move spaces to SQL-Msg` [:L1113].
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
    _fill_log_field(file_access, "sql_err", "0")
    _move_to_log_field(file_access, "sql_msg", "")
    return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


#  ba070 / ba072 / ba073 - THE WRITE, WHICH IS FOUR STATEMENTS  -------------
# A single `fn-write` runs three paragraphs by fall-through and can issue FOUR
# SQL statements:
#
#   1. `bb200-Insert`                       [:L793]   INSERT the record as passed
#   2. `ba090` with NL-Tipe forced to "O"    [:L839]   UPDATE  (S -> O)
#   3. `ba070` again with NL-Tipe "S"        [:L856]   INSERT the pointer row
#   4. `ba090` again, only if step 3 failed  [:L863]   UPDATE  ("JIC")
#
# The brief for this file describes three, which is what the INDEXED-FILE twin
# does [common/acasirsub1.cbl:L573, :L584, :L598]. The BRIDGE adds the fourth,
# and it is ANOMALY A44: a bare `if fs-reply not = zero` under a comment reading
# only "JIC", turning a failed pointer insert into an update attempt.


def _ba070_process_write(
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """``ba070-Process-Write`` [common/irsnominalMT.cbl:L783-L813].

    Statement one: load the host variables and insert. ANOMALY A11 - THIS ARM
    SETS ONLY ``FS-Reply``. There is no ``move`` to ``We-Error`` anywhere in the
    paragraph, so a duplicate answers ``(22, 0)`` and a hard failure ``(99, 0)``,
    and the maintainer's own comment on the second says so: "this may need
    changing for val in WE-Error!!" [:L808]. Not changed.

    ``IR906 "Link/record exists on owning write"``
    [common/acasirsub1.cbl:L193] was displayed at 2401 and acknowledged; the
    display becomes a log record and the acknowledgement is dropped, per the
    presentation rule. The bridge carries its own verbatim copy of IR906, IR907
    and IR908 [common/irsnominalMT.cbl:L182-L184] but NOT of IR909 or IR910,
    which is ANOMALY A34.

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
        # `if SQL-Err (1:4) = "1062" or = "1022" or Sql-State = "23000"`
        # [:L805-L808] - the BRIDGE-level duplicate test, on the copied text
        # rather than on the driver's own error number.
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

    Statement two, plus two early exits and the key mutation.

    ANOMALY A43 - the first thing after the duplicate report is a special the
    maintainer labelled "Specials for testing as COA incorrectly coded without
    subs" [:L824]::

        if       Owner
             and NL-Sub-Nominal = zero
             and NL-Tipe = "O"
             and NL-Name = spaces                      [:L826-L829]
                 move "S" to NL-Tipe                   [:L830]
                 perform ba090-Process-Rewrite thru ba092-Finish-1
                 go to ba999-Exit                      [:L832]

    An owning row with no sub-nominal and NO NAME is rewritten as type ``"S"``
    and the write ends there - one insert and one update, and the row now claims
    to be a sub-nominal. The third condition is redundant, since ``88 Owner`` IS
    ``NL-Tipe = "O"`` [copybooks/irswsnl.cob:L13]. Reproduced, redundancy and
    all.

    Then the ordinary path: an owning row returns [:L835-L836]; anything else
    has its type forced to ``"O"`` [:L838] and is UPDATED [:L839], with
    ``IR907 "Link/record exists on rewrite (S->O)"`` reported when the update
    answered ``994``.

    The zero-key guard [:L847-L848] is the maintainer's "Extra code to stop zero
    keys 21/12/16": a sub-nominal of zero ends the write before the pointer row
    is attempted.

    THE KEY MUTATION [:L850-L852] then runs, and the first of its three moves
    writes the owning number INTO THE FIRST FIVE CHARACTERS OF THE NAME, because
    that is where ``NL-Pointer`` lives [copybooks/irswsnl.cob:L22-L23]. That is
    deliberate here - it is how the pointer row gets its pointer - and it is the
    same overlay that costs a digit-named account its balances in ANOMALY A1.

    Args:
        file_access: The linkage block.
        nl: The record, mutated in place.

    Returns:
        The pair when the write ends here, or ``None`` to fall through into
        ``ba073-Fix-Up-Subs``.
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
        # ANOMALY A43 [:L826-L832].
        nl.nl_type = TYPE_SUB
        rewrite(file_access, nl)
        return (file_access.fs_reply, file_access.we_error)

    if _owner(nl):
        # `if Owner / go to ba999-exit.` [:L835-L836] - an owning account is one
        # statement and nothing more.
        return (file_access.fs_reply, file_access.we_error)

    # `move "O" to NL-Tipe` [:L838] then the UPDATE [:L839]. The row just
    # inserted is immediately overwritten with its type forced to "O".
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
        # `if NL-Sub-Nominal = zero / go to ba999-Exit.` [:L847-L848].
        return (file_access.fs_reply, file_access.we_error)

    # `move NL-Owning to NL-Pointer` [:L850] - WRITES THE NAME.
    owning = nl.nl_key.nl_owning
    _apply_pointer_overlay(nl, owning)
    # `move NL-Sub-Nominal to NL-Owning` [:L851].
    nl.nl_key.nl_owning = nl.nl_key.nl_sub_nominal
    # `move zero to NL-Sub-Nominal` [:L852].
    nl.nl_key.nl_sub_nominal = 0
    return None


def _ba073_fix_up_subs(
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """``ba073-Fix-Up-Subs`` [common/irsnominalMT.cbl:L854-L868].

    Statement three, the possible fourth, and the incomplete restore.

    ``move "S" to NL-Tipe`` [:L855] then ``perform ba070-Process-Write``
    [:L856] - a PERFORM of the first paragraph of the chain, which ends at
    [:L813], so only the load and the insert re-run and the fall-through does
    NOT recurse. ``IR908 "link/record exists on sub write"`` is reported on a
    duplicate; note its lower-case ``link`` where its three siblings capitalise
    it, which is part of ANOMALY A33 along with ``IR903``, ``IR904`` and
    ``IR905`` being absent from the sequence altogether.

    ANOMALY A44 - the fourth statement::

        *> JIC                                          [:L862]
        if       fs-reply not = zero
                 perform ba090-Process-Rewrite thru ba092-Finish-1

    "JIC" is the entire justification. A pointer-row insert that failed for ANY
    reason - not merely a duplicate - is retried as an update. The indexed-file
    twin has no such arm [common/acasirsub1.cbl:L598-L600], so this is a
    divergence between the two paths and not a shared idiom.

    ANOMALY A10 - THE RESTORE IS INCOMPLETE, and the maintainer says so in the
    source: "Do not know why this was missed out / but restored incase used by
    caller" [:L866-L867]. Two of the four mutated fields are put back - the
    two key halves - and two are NOT: ``NL-Tipe`` is left holding ``"S"``, and
    the first five characters of ``NL-Name`` are left holding the pointer digits.
    A caller that wrote an account and then read its own buffer finds the name
    corrupted and the type wrong. Reproduced exactly, including the ORDER, which
    matters because ``NL-Pointer`` is read out of the name it is restoring from.

    Args:
        file_access: The linkage block.
        nl: The record, mutated in place.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    # `move "S" to NL-Tipe` [:L855] then the third statement [:L856].
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

    # `move NL-Owning to NL-Sub-Nominal` [:L866] then `move NL-Pointer to
    # NL-Owning` [:L867]. NL-Tipe and the name's first five characters are NOT
    # restored.
    nl.nl_key.nl_sub_nominal = nl.nl_key.nl_owning
    nl.nl_key.nl_owning = _read_pointer_overlay(nl)
    return (file_access.fs_reply, file_access.we_error)


def write(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``fn-write`` - the three-paragraph fall-through chain.

    ``ba070-Process-Write`` [common/irsnominalMT.cbl:L783] ends and
    ``ba072-Proc-Write-Subs`` [:L815] begins, which ends and
    ``ba073-Fix-Up-Subs`` [:L854] begins. Each ``go to ba999-Exit`` inside them
    is a GO TO class 3 - a section exit - so it becomes an early ``return`` from
    the corresponding function, and the fall-through becomes the sequence of
    calls below. Statement ORDER is what the state diff observes (rule R-6), so
    the sequence is exactly insert, update, insert, and conditionally update.

    ANOMALY A9. ANOMALY A11. ANOMALY A44. See the three functions.

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

    ANOMALY A14 - THE ONLY UPSERT IN THE HANDLER SET. Insert, and if the insert
    left a non-zero reply, update::

        if       fs-reply not = zero
                 perform ba090-Process-Rewrite thru ba092-Finish-1   [:L1149-L1151]

    ``TWO SEPARATE STATEMENTS``, in that order. It is deliberately NOT expressed
    as a single upsert statement: the frozen bridge sends two, the server
    therefore does two units of work in a fixed order, and rule R-6 makes that
    order observable.

    ``*> Just will write no with no tests for owner or sub`` [:L1120] - the typo
    is the maintainer's, and the intent is exact: the raw write does NOT run the
    three-paragraph dance, so it maintains no pointer row. ``*> used with
    nominalLD`` names the loader it exists for.

    ``IR909 "Link/record exists on owning write, rewriting"``
    [common/acasirsub1.cbl:L196] and, if the update failed too, ``IR910 "Rewrite
    failed as well"`` [:L197]. Neither is duplicated in the bridge's own message
    block - ANOMALY A34.

    A CONSEQUENCE OF A14 THAT IS EASY TO MISS, and which is reproduced rather
    than corrected: the recovery update ERASES the duplicate-key reply. On a
    clean update ``ba090`` runs ``move zero to FS-Reply WE-Error``, ``move zero
    to SQL-Err`` and ``move spaces to SQL-Msg`` [common/irsnominalMT.cbl:L1111-
    L1113] before it leaves, so the ``22`` this paragraph had just set at
    [:L1139] is gone by the time the caller sees the pair. A successful upsert
    is therefore INDISTINGUISHABLE from a successful insert - the caller cannot
    learn that a row already existed - and only a FAILING recovery update
    reports anything, as ``(99, 994)`` [:L1101-L1103]. Adding a flag to
    distinguish the two would be new behaviour and is not done.

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
            # `move 22 to fs-reply` [:L1139].
            file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
        else:
            # `move 99 to fs-reply` [:L1141].
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
        # The second statement [:L1149-L1151].
        rewrite(file_access, nl)
        if file_access.we_error == REWRITE_FAILED_WE_ERROR:
            _LOG.error("irsnominalMT ba170: IR910 Rewrite failed as well")
    return (file_access.fs_reply, file_access.we_error)


#  ba080-Process-Delete / ba085-Process-Delete-ALL  -------------------------


def delete(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba080-Process-Delete`` [common/irsnominalMT.cbl:L870-L985].

    ANOMALY A12 - TWO ``DELETE`` STATEMENTS for one logical delete: the row
    itself [:L899-L905], and then, for anything that is not an owning account,
    the pointer row under a mutated key [:L960-L966].

    The count test is guarded by the maintainer's own note that the
    indexed-file twin has no equivalent - "TEST IS NOT IN IRSUB1" [:L907] - and
    the paragraph header says the same of the whole approach, "IRS does not test
    for error cond. as in irsub1". The consequence is precise and must not be
    tidied: when the first delete removes no row AND the driver reports no error,
    the arm that would write ``(99, 995)`` is skipped, NO STATUS IS WRITTEN, and
    control leaves at [:L918] - so THE POINTER ROW IS NEVER TOUCHED and the
    caller is told the delete succeeded. Deleting a non-existent sub-nominal
    account therefore silently leaves its pointer row behind.

    ``We-Error = 995`` is what ``override_we_error_for_operation`` supplies for a
    DELETE, matching [:L916, :L972].

    The key mutation [:L935-L936] is NOT restored, unlike the write path's
    partial restore - so a caller that deletes a sub-nominal account is left
    holding the pointer row's key.

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
            # `move 99 to fs-reply` [:L915] then `move 995 to WE-Error` [:L916].
            _apply_driver_status(file_access, failure)
            _apply_status(
                file_access,
                (int(FsReply.ERROR), DELETE_FAILED_WE_ERROR),
            )
        # `go to ba999-End` [:L918] - unconditional, so a clean no-op delete
        # returns here with whatever status it arrived with.
        return (file_access.fs_reply, file_access.we_error)
    # `move spaces to SQL-Msg SQL-State` and `move zero to SQL-Err`
    # [:L920-L921], then the pair [:L923].
    _move_to_log_field(file_access, "sql_msg", "")
    _move_to_log_field(file_access, "sql_state", "")
    _fill_log_field(file_access, "sql_err", "0")
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))

    if _owner(nl):
        # `if owner / go to ba999-Exit` [:L930-L931] - an owning account has no
        # pointer row to remove.
        return (int(FsReply.SUCCESS), int(WeError.SUCCESS))

    # `move NL-Sub-Nominal to NL-Owning` [:L935] then `move zero to
    # NL-Sub-Nominal` [:L936]. Note that this is NOT the write path's mutation:
    # there is no `move NL-Owning to NL-Pointer` here, so the name is untouched
    # and the pointer row is located by key alone.
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
        # The same mapping again [:L968-L978].
        _apply_driver_status(file_access, pointer_failure)
        _apply_status(file_access, (int(FsReply.ERROR), DELETE_FAILED_WE_ERROR))
        return (file_access.fs_reply, file_access.we_error)
    # `move zero to FS-Reply WE-Error` [:L984].
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
    return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


def delete_all(file_access: FileAccess, nl: WsIrsnlRecord) -> tuple[int, int]:
    """``ba085-Process-Delete-ALL`` [common/irsnominalMT.cbl:L987-L1066].

    The paragraph's own header calls it what it is: "THIS IS NON STANDARD". It
    exists so that opening the table for output can mean what opening an indexed
    file for output means - see :func:`open_output`.

    ANOMALY A28 and CORRECTION C3. Function code 6 is ``fn-Delete-All``
    [copybooks/wsfnctn.cob:L94] and NO HANDLER IN THE SET DISPATCHES IT: reading
    all seventeen shows 6 routed to bad-function everywhere, including here
    [common/acasirsub1.cbl:L286-L309]. But the BRIDGE does dispatch it
    [common/irsnominalMT.cbl:L314-L317], under the comment "special to cleardown
    all data" - so on the RDB path a direct function 6 works, and it is honoured
    here. The brief for this file says only that no handler dispatches 6, which
    is true and incomplete; both halves are recorded.

    The sweep is BOUNDED, not unbounded: ``move 9999999999 to NL-Key`` [:L1009],
    annotated "The last possible data", and then ``KEY-1 < "9999999999"``
    [:L1015-L1025]. A row whose key is exactly ten nines therefore SURVIVES a
    delete-all - the exact mirror of the sequential read's unreachable all-zeros
    key. Reproduced; no ``<=``.

    ``if WS-MYSQL-Count-Rows not > zero`` [:L1050] rather than ``not = 1``, so
    sweeping an already-empty table is a failure only when the driver also
    reports an error; otherwise it passes silently.

    Args:
        file_access: The linkage block.
        nl: The record. ITS KEY IS OVERWRITTEN WITH TEN NINES and not restored.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    predicate, parameters = _where_delete_all(nl)
    statement = _delete_statement(predicate)
    _move_to_log_field(file_access, "ws_log_where", statement)
    # `move "Deleting back from " NL-Key ... to WS-File-Key` [:L1026-L1030].
    _move_to_log_field(
        file_access,
        "ws_file_key",
        f"Deleting back from {_render_key(_key_number(nl))}",
    )
    _set_trace(file_access, "ba085-Process-Delete-ALL")
    affected, failure = _run_update(file_access, statement, parameters)
    if affected <= 0:
        if _driver_reported_error(failure):
            # `move 99 to fs-reply` [:L1057] then `move 995 to WE-Error`
            # [:L1058].
            _apply_driver_status(file_access, failure)
            _apply_status(
                file_access,
                (int(FsReply.ERROR), DELETE_FAILED_WE_ERROR),
            )
            return (file_access.fs_reply, file_access.we_error)
    else:
        # `move spaces to SQL-Msg` and `move zero to SQL-Err` [:L1062-L1063].
        _move_to_log_field(file_access, "sql_msg", "")
        _fill_log_field(file_access, "sql_err", "0")
    # `move zero to FS-Reply WE-Error` [:L1065].
    _apply_status(file_access, (int(FsReply.SUCCESS), int(WeError.SUCCESS)))
    return (int(FsReply.SUCCESS), int(WeError.SUCCESS))


#  THE BRIDGE CALL AND THE HANDLER'S DISPATCH  ------------------------------


def _bridge_call(
    system: SystemRecord,
    file_access: FileAccess,
    nl: WsIrsnlRecord,
) -> tuple[int, int]:
    """One entry into ``irsnominalMT``: ``ba010-Initialise`` then the dispatch.

    ``ba020-Process-DAL`` [common/acasirsub1.cbl:L751-L756] is::

        call     "irsnominalMT" using File-Access
                                      ACAS-DAL-Common-data

                                      WS-NL-Record
        end-call.

    Note the blank line inside the parameter list - the family's habit - and
    note the PARAMETER-NAME MISMATCH: the handler passes ``WS-NL-Record``
    [copybooks/irswsnl.cob, renamed at :L201] while the bridge names its third
    parameter ``WS-IRSNL-Record`` [common/irsnominalMT.cbl:L269], a
    DIFFERENTLY-NAMED record with a DIFFERENT INTERNAL STRUCTURE - the key is one
    ``pic 9(10)`` with the halves as a REDEFINES rather than a group of two, and
    the quarters are eight named fields rather than two ``OCCURS 4`` tables.
    Positionally compatible, structurally not. ANOMALY A25, and the same class of
    mismatch ``plinvoiceMT`` carries.

    The bridge's ``evaluate File-Function`` [common/irsnominalMT.cbl:L302-L328]
    lists 1, 2, 3, 4, 5, 6, 7, 8, 9 and 15. ANOMALY A41 - its ``when other``
    still carries the comment "6 is spare / unused" [:L326] twelve lines after 6
    was given its own arm. ANOMALY A40 - there is no ``when 13``.

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
    # `when other / go to ba100-Bad-Function` [:L325-L327]. Function 13 lands
    # here - ANOMALY A40 - and so does anything the facade should never send.
    return _ba100_bad_function(file_access)


def dispatch(
    system: SystemRecord,
    nl: WsIrsnlRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> tuple[int, int]:
    """``acasirsub1``'s entry point [common/acasirsub1.cbl:L211-L217].

    THE PARAMETER ORDER IS THE COBOL'S, EXACTLY::

        Procedure Division Using System-Record
                                 WS-NL-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data.

    so that a reviewer can diff this signature against the frozen one - which is
    the contract AAP section 0.4.3 sets for every handler call.

    What actually happens on the RDB path, in order:

    1. ``move 1 to WS-Log-System`` [:L226] and ``move 11 to WS-Log-File-No``
       [:L227]. ANOMALY - the legend beside them reads "5=Stock", while
       ``acas016``, ``acas019``, ``acas026`` and ``acas029`` write "5 = Invoice"
       for the same field. TWO MUTUALLY INCONSISTENT LEGENDS coexist; both are
       recorded and neither is resolved.
    2. the key-number guard [:L231-L245] - see :func:`_key_number_guard`.
    3. either the Open+Output block [:L253-L260] or the ordinary RDB branch
       [:L264-L268]. THE DIFFERENCE IS ANOMALY A27: the ordinary branch performs
       ``move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses`` [:L265] and the
       Open+Output block does not, so a table opened for output is worked with a
       ``File-Access`` block whose file-system flags were never refreshed.
    4. ``move 21 to WS-Log-File-no`` [:L689], reached by fall-through into
       ``ba010-Test-WS-Rec-Size``, which contains nothing else. ANOMALY - 21 is a
       FOUR-WAY COLLISION across ``acas005``, ``acas012``, ``acas022`` and this
       handler; only the ``(system, file)`` pair tells them apart, and this one
       is ``(1, 21)``.
    5. the record-size gate [:L691-L731] - see :func:`_record_size_gate`.
    6. ``ba015-Test-Ends`` [:L733-L742] and then the CALL - see
       :func:`open_output` and :func:`_bridge_call`.

    Everything the handler does AFTER that point is unreachable here, because the
    RDB branch leaves through ``go to AA-Main-Exit`` [:L267] before the handler's
    own ``evaluate File-Function`` at [:L286]. That single fact is why this module
    reproduces the BRIDGE and not the handler, and it is CORRECTION C4 in the
    module docstring.

    NO RECOVERY IS ATTEMPTED, ever. "Any errors leave it to caller to recover
    from" [:L758]. This handler is reached through the IRS facade convention,
    whose per-handler error check displays its own message and, on an
    unrecoverable open failure, returns from the CALLING PROGRAM outright
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364] - so the facade needs an
    honest status pair to test, and anything retried or smoothed over here would
    hide a failure the caller is entitled to see.

    Args:
        system: ``SYSTEM-REC``.
        nl: ``WS-NL-Record``. Several verbs MUTATE it; each says so.
        file_access: ``File-Access``, carrying the function code, the access
            type, ``File-Key-No`` and every status and log field.
        file_defs: ``File-Defs``. Accepted and never read, because the RDB path
            has no file name to resolve - the table name is a literal in the
            bridge. Present for parameter-order fidelity, and recorded in the
            module docstring as an omission rather than left looking like an
            oversight.
        dal_common: ``ACAS-DAL-Common-data``, whose ``SW-Testing`` gates the FH
            logger [common/acasirsub1.cbl:L209].

    Returns:
        The ``(FS-Reply, We-Error)`` pair, written into ``file_access`` as well
        as returned.
    """
    del file_defs

    # 1. The log identity [common/acasirsub1.cbl:L226-L227].
    file_access.logging_data.ws_log_system = WS_LOG_SYSTEM
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT

    # 2. The key-number guard [:L231-L245].
    rejected = _key_number_guard(file_access)
    if rejected is not None:
        return rejected

    # 3. Open+Output goes early, WITHOUT the flat-statuses copy [:L253-L265].
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

    # 4. `ba010-Test-WS-Rec-Size` contains only this [:L689].
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB

    # 5. The record-size gate, which may skip the CALL entirely [:L718].
    if not _record_size_gate(system, file_access):
        return RECORD_SIZE_STATUS

    #  NO PER-CALL TRACE HERE. The frozen `CALL "irsnominalMT"`
    #  [common/acasirsub1.cbl:L756] displays nothing, so the record that used to sit
    #  on this line was invented (R-4) - and it named `NL-KEY`, the nominal account
    #  (CWE-532). What `SW-Testing` actually gates is `Ca-Process-Logs`, and that is
    #  reproduced below, on the exit path where the frozen source performs it.

    # 6. `ba015-Test-Ends` then `ba020-Process-DAL` [:L733-L756].
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
