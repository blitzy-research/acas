"""OTM5 data access - the purchase open-item table ``PUITM5-REC``.

This module replaces TWO frozen COBOL programs with native Python and SQL:
the file handler ``acas029`` [common/acas029.cbl] and the generated bridge
``otm5MT`` [common/otm5MT.cbl]. Rule R-1 forbids executing, embedding or
shelling out to either, so nothing here names the GnuCOBOL compiler driver,
its module runner, or the bridge's C interface object; the shipped artifact
runs on a host with no COBOL compiler and no COBOL runtime present.

Agent Action Plan section 0.1.2 collapses the frozen four-hop chain - facade
copybook, numbered handler, generated bridge, literal SQL - into "two layers
rather than four: a facade module publishing the verb vocabulary, and one
module per handler that owns the SQL for its table." This is that second
layer for the OTM5 entity. Section 0.3.1 gives the reason the boundary is the
HANDLER and not the table: mirroring it "keeps the Python module set in exact
correspondence with the COBOL programs that the traceability document must
map, and preserves the dispatch semantics rather than flattening them."

THE SPINE (Agent Action Plan section 0.2.1.1)
    OTM5 -> ``acas029`` -> ``otm5MT`` -> ``PUITM5-REC``
    record copybooks ``copybooks/plwsoi5B.cob`` + ``copybooks/plwsoi5C.cob``

AUTHORITATIVE SOURCES, cited by line so a reviewer can diff them
    handler linkage and parameter list  [common/acas029.cbl:L219-L225]
    handler record view                 [common/acas029.cbl:L209]
    handler key guard                   [common/acas029.cbl:L239-L253]
    handler RDB branch                  [common/acas029.cbl:L257-L261]
    handler verb dispatch               [common/acas029.cbl:L277-L299]
    handler record-size gate            [common/acas029.cbl:L553-L593]
    handler bridge CALL                 [common/acas029.cbl:L605-L609]
    bridge PROCEDURE DIVISION USING     [common/otm5MT.cbl:L369-L371]
    bridge record view                  [common/otm5MT.cbl:L348-L349]
    bridge host-variable group (29)     [common/otm5MT.cbl:L303-L332]
    bridge key metadata                 [common/otm5MT.cbl:L250-L260]
    bridge cursor declarations          [common/otm5MT.cbl:L262-L272]
    bridge staging area                 [common/otm5MT.cbl:L229-L242]
    bridge verb dispatch                [common/otm5MT.cbl:L408-L431]
    bridge load paragraph  (29 moves)   [common/otm5MT.cbl:L1338-L1382]
    bridge unload paragraph (27 moves)  [common/otm5MT.cbl:L1387-L1422]
    bridge INSERT rendering             [common/otm5MT.cbl:L1427-L1814]
    bridge UPDATE rendering             [common/otm5MT.cbl:L1817-L2208]
    pre-translation MYSQL VAR directive [common/otm5MT.scb:L295-L298]
    authoritative record layout         [copybooks/plwsoi.cob]
    frozen table, 29 columns            [mysql/ACASDB.sql:L596]

A POSITIVE FINDING, recorded because it is a finding
    This is the cleanest handler/bridge pair in the folder, and saying so
    matters: after five phantom columns in ``plinvoiceMT`` and twelve
    narrowings in ``purchMT``, the temptation is to assume every bridge is
    broken. Three things agree exactly here. The handler's CALL passes
    ``File-Access``, ``ACAS-DAL-Common-data``, ``WS-OTM5-Record``
    [common/acas029.cbl:L605-L609] and the bridge's ``USING`` names the same
    three in the same order [common/otm5MT.cbl:L369-L371]. Both sides reach
    the record through ``copy "plwsoi.cob" replacing OI-Header by
    WS-OTM5-Record`` [common/acas029.cbl:L209], [common/otm5MT.cbl:L348-L349],
    so only the ``01`` name is substituted and every subordinate field keeps
    its ``OI-*`` name. And the nine ``decimal(9,2)`` money fields carry nine
    digits and two decimal places at all three layers with no width drift.
    Verify, do not extrapolate.

EIGHT CORRECTIONS TO THE WORKING SPECIFICATION, each settled against the
frozen source, because rule R-6 makes compiled behaviour the tie-breaker.
Three are set out here in full; the remaining five are recorded at the point
they bite, and all eight are listed in the traceability footer:
    C4  the SQL-diagnostic clearing is never reached on this path - see
        :func:`record_size_gate`
    C5  the handler's flat verbs ``aa020``..``aa100`` are never reached on this
        path - see the deliberate-omission block below :data:`CURSOR_SLOT`
    C6  the "PERFORM THRU occurs only seven times" count excludes the bridges -
        see the traceability footer
    C7  the cursor-block line numbers are off by one at both ends - see
        :func:`start`
    C8  the function-code vocabulary is cited past the end of its file - see
        :func:`start`
    C1  The working note's line numbers for [common/acas029.cbl] drift by one
        to two lines in several places. Every locator in this file was read
        from the frozen source rather than copied, so the numbers here are the
        real ones. The traceability footer lists them.
    C2  The working note asserted that the access-type range guard is
        flat-file-only and that access type 9 therefore reaches the database.
        It does not. The BRIDGE carries its own guard on the RDB path -
        ``if access-type < 5 or > 8`` returning ``(99, 997)``
        [common/otm5MT.cbl:L765-L769] - which is a DIFFERENT status pair from
        the handler's flat-file ``998`` [common/acas029.cbl:L441-L442]. The
        guard is therefore implemented here, via
        ``cursor_state.start``, which enforces exactly that range. Note the
        arm the guard makes unreachable is nonetheless present in the frozen
        relation map, ``when 9 move "<= " to MOST-Relation``
        [common/otm5MT.cbl:L794], and is reproduced as unreachable rather than
        deleted.
    C3  The working note asserted that function codes 32 and 33 are dead
        vocabulary "dispatched by no handler". That is true of the HANDLER -
        ``acas029`` contains no ``when 3x`` anywhere
        [common/acas029.cbl:L277-L295] - but NOT of the bridge, which
        dispatches ``when 32 go to ba140-Process-Read-Next`` and ``when 33 go
        to ba150-Process-Read-Next`` [common/otm5MT.cbl:L425-L428]. Because
        this module reproduces the pair as the handler drives it, and the
        handler can never present 32 or 33, no verb is published for either
        and both fall to the bridge's bad-function code. The divergence is
        stated rather than smoothed: ``fn-Read-By-Batch`` is documented as
        existing "for OTM3/5 (sl095/pl095)" [copybooks/wsfnctn.cob:L103] and
        the OTM5 handler is precisely the one that never presents it.

THE HEADLINE ANOMALY - TWO WRITE-ONLY COLUMNS
    ``bb000-HV-Load`` loads all 29 host variables. ``bb100-UnloadHVs`` moves
    back only 27. ``HV-OI5-KEY`` [common/otm5MT.cbl:L1352] and
    ``HV-OI5-BATCH`` [common/otm5MT.cbl:L1358] - exactly the two DERIVED host
    variables - are loaded and never unloaded [common/otm5MT.cbl:L1394-L1422].
    The consequence is load-bearing rather than cosmetic: a row whose stored
    ``OI5-KEY`` disagrees with its stored ``OI5-SUPPLIER`` plus
    ``OI5-INVOICE`` is read back with the COMPONENTS, and the key is silently
    RECONSTRUCTED on the next write, so it round-trips into a different key.
    Nothing validates the stored value against its components, and rule R-4
    forbids adding a check. The asymmetry is reproduced exactly.

THE SECOND TRAP - THE BATCH IS BINARY IN THE RECORD AND DIGITS IN THE COLUMN
    ``OI-Batch`` carries ``Comp`` at the GROUP level and its children inherit
    it [copybooks/plwsoi.cob:L20-L22], so the group is a binary item - six
    bytes, measured. Its column is ``char(8)``. The bridge does not
    reinterpret those bytes: it moves the two children into a DISPLAY pair
    ``WS-Temp-ED-Batch-Nos`` / ``WS-Temp-ED-Batch-Item``, which converts them
    to zoned decimal, and then moves the eight-byte REDEFINITION
    ``WS-Temp-ED-Batch9`` into ``HV-OI5-BATCH``
    [common/otm5MT.cbl:L238-L242, L1354-L1358]. The eight characters are
    therefore the DIGITS. Reinterpreting the binary image would write garbage.

DELIBERATE OMISSIONS, recorded as omissions per Agent Action Plan 0.5.3
    O1  The ENTIRE flat-file path. ``acas029`` takes the RDB branch at
        [common/acas029.cbl:L257-L261], before any of ``aa020``..``aa100`` is
        reached, so every ISAM verb in the handler - ``open input``, ``open
        i-o``, ``read next``, ``start``, ``write``, ``rewrite``, ``delete`` -
        belongs to a path this module never takes. The handler behaviour that
        happens BEFORE the branch is reproduced in :func:`dispatch`; the
        behaviour after it is not, and each item below says so.
    O2  ``OI-Customer`` [copybooks/plwsoi.cob:L14-L15] is a group of exactly
        one child wrapping ``OI-Supplier``; the two occupy the same seven
        bytes. It has NO host variable and NO column, so no column is emitted
        for it. It is also named *Customer* in a *Purchase* copybook.
    O3  ``OI-Approp`` [copybooks/plwsoi.cob:L44-L45] REDEFINES ``OI-Net``. It
        has no host variable and no column; the frozen schema records the
        aliasing only as ``COMMENT 'Also called Approp'``
        [mysql/ACASDB.sql:L596]. No column is emitted for it.
    O4  The open-i-o retry ladder - close, open output, close, open i-o - and
        the maintainer's own note that the reopened file's status is never
        re-tested [common/acas029.cbl:L313-L319]. Flat-file only.
    O5  The handler's ``if access-type < 5 or > 8`` rejection
        [common/acas029.cbl:L441-L443] returning ``998``. Flat-file only; the
        RDB path is guarded by the bridge instead, with ``997`` - see C2.
    O6  ``stop "Cobol File EOF"`` [common/acas029.cbl:L365], a live ``STOP``
        statement shipped in production. Flat-file only, and it is NOT
        translated into any interpreter-terminating call or a
        process-terminating raise; a library module does not stop the
        process.
    O7  The ``display``/``accept`` pair in the record-size gate
        [common/acas029.cbl:L574-L579]. Agent Action Plan section 0.3.4 drops
        presentation that has no database effect - but the CONTROL TRANSFER it
        guards, ``go to ba-rdbms-exit`` [common/acas029.cbl:L580], is
        preserved: :func:`record_size_gate` skips the bridge call.
    O8  Function codes 32 (``fn-Read-By-Batch``) and 33 (``fn-Read-By-Cust``).
        No verb is published for either - see C3.
    O9  ``aa045-Eval-Keys`` [common/acas029.cbl:L391-L407] and
        ``aa041-Move-Inv-Data`` [common/acas029.cbl:L384-L387] exist purely to
        compose ``WS-File-Key`` for the logger on the flat-file path. The
        composition itself is NOT omitted - it is exactly what
        :func:`compose_key` reproduces for the bridge - but the two paragraphs
        as handler control flow are.
    O10 The block of representation-only declarations the bridge never uses:
        ``WS-Body-Key pic x(9)`` for a table with no body and no repeating
        group [common/otm5MT.cbl:L282], ``WS-Temp-ED-Row pic 9(7)``
        [common/otm5MT.cbl:L231], and ``KOR-Type`` annotated "Not used
        currently" [common/otm5MT.cbl:L260]. Nothing is emitted for them.

``OI-Type`` LEGEND [copybooks/plwsoi.cob:L25-L34] - documentation only. Rule
R-3 says validation is copied, never extended, and the frozen source performs
NO check against this list, so neither does this module. Note that 8 is absent
from the legend; it is neither added nor rejected.
    1 Receipt          2 Account Invoice   3 Cr. Note      4 Proforma
    5 Payment          6 Journal-Unapplied Cash
    7 Journal Type B (Not Used)            9 Old Payments

THREE DIFFERENT ORDERS IN ONE BRIDGE, all three recorded
    column order  [mysql/ACASDB.sql:L596]      KEY, SUPPLIER, INVOICE, DAT,
                                               BATCH, BATCH-NOS, BATCH-ITEM,
                                               TYPE, ...
    load order    [common/otm5MT.cbl:L1348-L1382]  INVOICE, SUPPLIER, KEY,
                                               BATCH-NOS, BATCH-ITEM, BATCH,
                                               DAT, TYPE, ...
    unload order  [common/otm5MT.cbl:L1394-L1422]  INVOICE, SUPPLIER, DAT,
                                               BATCH-NOS, BATCH-ITEM, TYPE, ...
``OI-Date`` is unloaded third but loaded seventh. Statements emit columns in
COLUMN order, because that is the order both ``bb200-Insert`` and
``bb300-Update`` render them in; the load and unload orders are preserved as
the order the two helpers perform their work in.

TRACEABILITY (rule R-5)
    Program to module      ``acas029`` + ``otm5MT`` -> this file.
    Paragraph to function  the ``--- traceability ---`` footer maps every
                           paragraph of both programs to its function here, or
                           to the omission that accounts for it, and annotates
                           the ``GO TO`` class applied at each transfer site
                           per Agent Action Plan section 0.4.2.
    Field to dictionary    every one of the 29 columns is resolved at import
                           time through :mod:`acas_posting.dictionary.loader`,
                           whose entries are keyed ``PUITM5-REC.<COLUMN>``.
                           Not one column name, width, scale, sign or
                           storage class is hand-typed here. Agent Action Plan
                           section 0.8.1 makes that ordering a directive: "it
                           is what prevents fields being transcribed by eye."

RULES
    R-1 no COBOL at runtime - no process spawning of any kind, no foreign
        function interface, no compiler or bridge object referenced, and no
        import of the oracle harness tree.
    R-2 zero binary floating point - the eleven ``decimal`` columns are
        :class:`decimal.Decimal` end to end and the eight integer columns are
        :class:`int`. No binary floating-point type, no imaginary-number
        type, no general-maths module, no builtin rounding and no
        absolute-value builtin is applied to a monetary value; magnitudes are
        taken by
        comparison and negation, which are exact on ``Decimal``.
    R-3 no added validation, no added field, no schema change, no concurrency.
        Only SELECT, INSERT, UPDATE and DELETE are issued. No DDL of any kind,
        no index, no view, no trigger, no migration tool, no ORM entity layer,
        no ORM session, no connection pool, no thread and no async runtime.
        No transaction-control statement of any kind is issued -
        ``connection.py`` owns the per-statement autocommit policy and this
        module never touches transaction control.
    R-4 legacy anomalies reproduced, never fixed. Every reproduction site
        carries a ``# [<path>:L<n>]`` comment naming the frozen locator, per
        Agent Action Plan section 0.7.4 conflict C-4.
    R-5 full traceability - see above.
    R-6 compiled behaviour is the tie-breaker. No clock read, no
        nondeterministic value source, no unique-identifier generator and no
        sleep; no ``ORDER BY`` beyond the two the frozen bridge
        itself writes. Two measurements taken against GnuCOBOL 3.2.0 settle
        questions this file would otherwise have had to guess at, and both are
        recorded at the site that depends on them.

    There is NO user rules document for this project: ``review_rules`` reports
    that none was provided. The six rules above are the ones Agent Action Plan
    section 0.7.2 makes binding. Where they are silent, this file is held to
    enterprise-standard practice, and their silence is not read as permission
    to lower the bar.

LAYERING (Agent Action Plan section 0.4.3)
    Permitted: ``dal.connection``, ``dal.status``, ``dal.cursor_state``, the
    record modules this handler's linkage names, and ``dictionary.loader``.
    Forbidden and absent: ``acas_posting.cobol.*`` - the ``88``-level
    condition names ``payment-held``, ``S-Open`` and ``S-Closed``
    [copybooks/plwsoi.cob:L39, L54, L55] belong to
    :mod:`acas_posting.records.otm5`, not here - ``programs``, ``cli``, any
    other ``dal.acas*`` module, and ``harness``.
"""

from __future__ import annotations

import decimal
import logging
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Final

from acas_posting.dal.connection import (
    MySQLConnectionAbstract,
    TransportSecurity,
    execute_statement,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    CursorSlot,
    CursorStateTable,
    DatabaseCursor,
    KeyOfReference,
    key_of_reference,
    read_indexed as _cursor_read_indexed,
    read_next as _cursor_read_next,
    start as _cursor_start,
)
from acas_posting.dal.status import (
    AccessType,
    AcasFileHandlerError,
    FileFunction,
    FsReply,
    LogSystem,
    SqlState,
    WeError,
    db_error_log_category,
    is_duplicate_key_bridge_level,
    mysql_1100_db_error,
    redact_for_log,
    sanitise_for_log,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefsA
from acas_posting.records.otm5 import (
    Filler1,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
    OiSupplier,
    descriptors_of,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

#: Module logger. A library module attaches no handler and configures no root
#: logger. The frozen equivalent is ``Ca-Process-Logs``, which calls
#: ``fhlogger`` [common/acas029.cbl:L617-L621] and has no database effect, so
#: Agent Action Plan section 0.3.4 makes it a log record here.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  IDENTITY OF THE TABLE, THE HANDLER AND THE BRIDGE
# ---------------------------------------------------------------------------
# Every value below is READ from the generated data dictionary rather than
# typed, because Agent Action Plan section 0.8.1 makes "data dictionary first"
# a directive and rule R-5 requires each field to cite its entry. The one
# import-time failure this can produce - a dictionary that does not describe
# this table - is allowed to propagate: a silent fallback would defeat the
# directive by letting a hand-typed list stand in.
_TABLE_ENTRY: Final = loader.table_for("PUITM5-REC")

#: The frozen table. Declared ``TABLE=PUITM5-REC,HV`` in the pre-translation
#: directive [common/otm5MT.scb:L295-L298] and materialised as the bridge's
#: host-variable group name ``TD-PUITM5-REC`` [common/otm5MT.cbl:L303].
TABLE: Final[str] = _TABLE_ENTRY.name

#: The bridge this module replaces [common/otm5MT.cbl:L13].
BRIDGE: Final[str] = _TABLE_ENTRY.bridge

#: The handler this module replaces [common/acas029.cbl].
HANDLER: Final[str] = _TABLE_ENTRY.handler

#: The facade name the entity is published under
#: [copybooks/Proc-ACAS-FH-Calls.cob]. ``dal/facade.py`` owns the vocabulary;
#: this constant exists so the facade can find its implementation by name
#: without this module having to know about the facade.
ENTITY_FACADE: Final[str] = _TABLE_ENTRY.entity_facade

#: ``PRIMARY KEY (`OI5-KEY`)`` [mysql/ACASDB.sql:L596], and the sole
#: ``KeyOfReference`` the bridge declares [common/otm5MT.cbl:L250-L253].
PRIMARY_KEY: Final[str] = _TABLE_ENTRY.primary_key

#: The record layout the handler and the bridge both reach the table through.
#: ``copy "plwsoi.cob" replacing OI-Header by WS-OTM5-Record``
#: [common/acas029.cbl:L209], [common/otm5MT.cbl:L348-L349]. The twin views
#: ``plwsoi5B.cob`` and ``plwsoi5C.cob`` are context only: neither the handler
#: nor the bridge copies them, ``5B``'s ``copy`` is commented out and carries
#: four stray leading spaces inside the dead literal, ``"    plwsoi.cob"``
#: [copybooks/plwsoi5B.cob:L19], and ``5C``'s is live [copybooks/plwsoi5C.cob:L19].
RECORD_COPYBOOKS: Final[tuple[str, ...]] = _TABLE_ENTRY.copybooks

#: ``01 WS-OTM5-Record pic x(113)`` [copybooks/plwsoi5C.cob:L10]. Measured
#: against GnuCOBOL 3.2.0: ``function length`` of both the linkage record and
#: the FD record area is 113, which is what makes the record-size gate
#: unreachable - see :func:`record_size_gate`.
RECORD_LENGTH: Final[int] = 113

# ``'00010015'`` - offset 1, length 15 [common/otm5MT.cbl:L252]. Taken from
# ``cursor_state``'s registration of the same frozen metadata rather than
# re-parsed, so there is ONE reading of the offset/length string in the layer.
_KEY: Final[KeyOfReference] = key_of_reference(TABLE, 1)

#: Offset of the key within the record image, one-based as COBOL declares it.
KEY_OFFSET: Final[int] = _KEY.kor_offset

#: Length of the key. Fifteen: ``OI-Nos x(6)`` + ``OI-Check 9`` +
#: ``OI-Invoice 9(8)`` [copybooks/plwsoi.cob:L13-L18], matching ``char(15)``.
KEY_LENGTH: Final[int] = _KEY.kor_length

#: ``KeyOfReference occurs 1`` [common/otm5MT.cbl:L255] and ``record key
#: oi5-key`` [copybooks/plseloi5.cob:L6] - one key, and the handler rejects
#: every other key number. See :func:`_key_number_guard`.
KEY_COUNT: Final[int] = 1

#: ``'STR'`` [common/otm5MT.cbl:L253], annotated "Not used currently"
#: [common/otm5MT.cbl:L260]. Carried for traceability; nothing branches on it.
KEY_TYPE: Final[str] = _KEY.kor_type

#: ``move 4 to WS-Log-System`` [common/acas029.cbl:L234] - the Purchase
#: subsystem. The legend on that very line reads "5 = Invoice" while
#: ``acas013``, ``acas015`` and ``acas022`` use a legend in which 5 is Stock
#: and 6 is "PL & SL"; the codebase carries two mutually inconsistent legends
#: and rule R-4 resolves neither.
WS_LOG_SYSTEM: Final[int] = int(LogSystem.PL)

#: ``move 15 to WS-Log-File-No`` [common/acas029.cbl:L235] - the value set on
#: entry, before the branch. Reached on the flat-file path only.
WS_LOG_FILE_NO_FLAT: Final[int] = 15

#: ``move 25 to WS-Log-File-no`` [common/acas029.cbl:L551] - the RDB value.
#: The bump from 15 to 25 happens inside ``ba010-Test-WS-Rec-Size``, which is
#: never ``perform``ed: the flat path performs ``ba012`` directly
#: [common/acas029.cbl:L265] and the RDB path performs ``ba-Process-RDBMS``
#: [common/acas029.cbl:L259], which falls INTO ``ba010`` first. So 25 is
#: reached only on the RDB path, which is the path this module is. Note the
#: pair ``(4, 25)`` is what disambiguates: ``acas008`` (system 1),
#: ``acas019`` (system 3) and ``acas029`` (system 4) all bump 15 to 25, so the
#: file number alone collides three ways.
WS_LOG_FILE_NO_RDB: Final[int] = 25

# ---------------------------------------------------------------------------
#  THE 29 COLUMNS, RESOLVED FROM THE DICTIONARY (rule R-5)
# ---------------------------------------------------------------------------
# ``loader.entries_for_table`` returns one entry per column, each carrying the
# authoritative triple the user's own words designate: "The maintainer's
# one-way COBOL-to-MySQL bridge defines the authoritative record-layout to
# table mapping - it is the data dictionary for this migration."
_ENTRIES: Final[tuple[Any, ...]] = tuple(
    sorted(
        loader.entries_for_table(TABLE),
        key=lambda entry: loader.column_for(entry.key).ordinal,
    )
)

#: The 29 column names in SCHEMA order [mysql/ACASDB.sql:L596], which is also
#: the order ``bb200-Insert`` [common/otm5MT.cbl:L1427-L1814] and
#: ``bb300-Update`` [common/otm5MT.cbl:L1817-L2208] render them in, and the
#: order ``MySQL_fetch_record`` names its host variables in
#: [common/otm5MT.cbl:L580-L609].
COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name for entry in _ENTRIES
)

#: Dictionary key per column, e.g. ``OI5-NET`` -> ``PUITM5-REC.OI5-NET``. The
#: mapping is NOT derivable by upper-casing a copybook name - the copybook
#: field is ``OI-Net`` - which is exactly why it is looked up.
DICTIONARY_KEYS: Final[Mapping[str, str]] = {
    loader.column_for(entry.key).name: entry.key for entry in _ENTRIES
}

# ANOMALY A1 - the headline defect, derived rather than asserted. The
# dictionary records ``unloaded_to_record`` per host variable, and it is False
# for exactly the two DERIVED ones: ``move WS-Temp-Ed-Key to HV-OI5-KEY``
# [common/otm5MT.cbl:L1352] and ``move WS-Temp-ED-Batch9 to HV-OI5-BATCH``
# [common/otm5MT.cbl:L1358] are loaded on every write, and neither appears
# among the 27 moves of ``bb100-UnloadHVs``
# [common/otm5MT.cbl:L1394-L1422]. Deriving the tuple means a future
# regeneration of the dictionary that "fixed" the bridge would change this
# constant and fail the tests, rather than passing unnoticed.
#: Columns written on every insert and read back on no select.
WRITE_ONLY_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if not loader.host_variable_for(entry.key).unloaded_to_record
)

#: The 27 columns ``bb100-UnloadHVs`` does move back
#: [common/otm5MT.cbl:L1394-L1422], in COLUMN order. Its length is the
#: arithmetic statement of anomaly A1: 29 loaded, 27 unloaded.
UNLOADED_COLUMNS: Final[tuple[str, ...]] = tuple(
    name for name in COLUMNS if name not in WRITE_ONLY_COLUMNS
)

# ANOMALY A4 - four fields signed in the copybook, unsigned at the host
# variable and unsigned in the column, so the sign is lost AT THE BRIDGE,
# before any SQL executes. Agent Action Plan section 0.6.2 states the rule the
# layer must follow: "the Python data-access layer must reproduce the bridge's
# conversion, not merely write the computed value and let MySQL complain."
#   OI-Date         binary-long  signed [copybooks/plwsoi.cob:L19]
#     -> HV-OI5-DAT          9(10) COMP unsigned [common/otm5MT.cbl:L307]
#   OI-Deduct-Days  binary-char  signed [copybooks/plwsoi.cob:L56]
#     -> HV-OI5-DEDUCT-DAYS  9(03) COMP unsigned [common/otm5MT.cbl:L326]
#   OI-Days         binary-char  signed [copybooks/plwsoi.cob:L59]
#     -> HV-OI5-DAYS         9(03) COMP unsigned [common/otm5MT.cbl:L329]
#   OI-Date-Cleared binary-long  signed [copybooks/plwsoi.cob:L62]
#     -> HV-OI5-DATE-CLEARED 9(10) COMP unsigned [common/otm5MT.cbl:L332]
# Never generalise signedness by field kind: in this same folder ``*-CR``
# keeps its sign here and in ``otm3MT`` but loses it in ``slinvoiceMT`` and
# ``plinvoiceMT``, and the two ``*-DEDUCT-*`` fields keep theirs here and lose
# theirs in both invoice bridges. Hence the derivation from ``drift.signedness``.
#: Columns whose sign the bridge discards on the way in.
SIGN_LOSS_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.drift_for(entry.key).signedness
)

#: ``char`` columns - twelve of them. ``FUNCTION TRIM (HV-..., TRAILING)``
#: between double quotes in both statements [common/otm5MT.cbl:L1442-L1449].
CHARACTER_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value == "CHAR"
)

#: ``decimal`` columns - eleven: nine ``decimal(9,2)`` money fields plus the
#: two ``decimal(5,2)`` deduction fields. All eleven are
#: :class:`decimal.Decimal` end to end (rule R-2).
DECIMAL_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value == "DECIMAL"
)

#: ``int`` and ``tinyint`` columns - six of them. All are :class:`int`
#: (rule R-2 forbids binary floating point, and integer truncation is what
#: makes the
#: frozen system's integer defects reproducible).
INTEGER_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value in ("INT", "TINYINT")
)

#: Declared scale per ``decimal`` column, from the frozen DDL. Two everywhere
#: here, but read rather than assumed.
DECIMAL_SCALES: Final[Mapping[str, int]] = {
    name: int(loader.column_for(DICTIONARY_KEYS[name]).scale or 0)
    for name in DECIMAL_COLUMNS
}

#: Declared width per ``char`` column, from the frozen DDL.
CHARACTER_WIDTHS: Final[Mapping[str, int]] = {
    name: int(loader.column_for(DICTIONARY_KEYS[name]).display_width or 0)
    for name in CHARACTER_COLUMNS
}

#: True where the column is declared ``unsigned``. Consulted only for the
#: record, never as a validation: the bridge has already discarded the sign by
#: the time a value reaches SQL, so nothing here needs to reject anything.
COLUMN_IS_UNSIGNED: Final[Mapping[str, bool]] = {
    loader.column_for(entry.key).name: bool(loader.column_for(entry.key).unsigned)
    for entry in _ENTRIES
}


# ---------------------------------------------------------------------------
#  TRACE NUMBERS - THE HANDLER'S AND THE BRIDGE'S, WHICH DISAGREE
# ---------------------------------------------------------------------------
# ``WS-No-Paragraph`` is the field the logger reports the failing paragraph
# through [copybooks/wsfnctn.cob:L48]. Both programs set it, on different
# scales, and both are kept because the traceability document maps both.

#: ``acas029``'s 201..208 mapping, one per verb, each cited at its own line.
#: This is the SEVENTH handler in the folder with this identical mapping -
#: ``acas013``, ``acas015``, ``acas016``, ``acas019``, ``acas022``,
#: ``acas026``, ``acas029`` - so a shared number carries no information about
#: which handler produced it.
HANDLER_TRACE_NUMBERS: Final[Mapping[FileFunction, int]] = {
    FileFunction.OPEN: 201,          # [common/acas029.cbl:L303]
    FileFunction.CLOSE: 202,         # [common/acas029.cbl:L342]
    FileFunction.READ_NEXT: 203,     # [common/acas029.cbl:L358]
    FileFunction.READ_INDEXED: 204,  # [common/acas029.cbl:L411]
    FileFunction.START: 205,         # [common/acas029.cbl:L435]
    FileFunction.WRITE: 206,         # [common/acas029.cbl:L485]
    FileFunction.DELETE: 207,        # [common/acas029.cbl:L496]
    FileFunction.RE_WRITE: 208,      # [common/acas029.cbl:L508]
}

#: ``otm5MT``'s own small numbers, which the RDB path actually reports because
#: the bridge overwrites the handler's value. Two of them - the SELECT and the
#: FETCH - belong to one verb, which is why this maps to a tuple.
BRIDGE_TRACE_NUMBERS: Final[Mapping[str, tuple[int, ...]]] = {
    "ba020-Process-Open": (1,),           # [common/otm5MT.cbl:L462]
    "ba030-Process-Close": (2,),          # [common/otm5MT.cbl:L481]
    "ba040-Process-Read-Next": (3, 4),    # [common/otm5MT.cbl:L519, L571]
    "ba050-Process-Read-Indexed": (5, 6),  # [common/otm5MT.cbl:L674, L696]
    "ba060-Process-Start": (8,),          # [common/otm5MT.cbl:L820]
    "ba070-Process-Write": (10,),         # [common/otm5MT.cbl:L875]
    "ba080-Process-Delete": (13,),        # [common/otm5MT.cbl:L917]
    "ba090-Process-Rewrite": (17,),       # [common/otm5MT.cbl:L952]
    "ba140-Process-Read-Next": (21, 22),  # [common/otm5MT.cbl:L1020, L1072]
    "ba150-Process-Read-Next": (21, 22),  # [common/otm5MT.cbl:L1175, L1227]
    "ba998-Free": (20,),                  # [common/otm5MT.cbl:L1317]
}

# ---------------------------------------------------------------------------
#  STATUS VALUES THE FROZEN PAIR RETURNS
# ---------------------------------------------------------------------------

# ANOMALY A13 - ``move 35 to fs-Reply`` [common/acas029.cbl:L307] is a status
# value OUTSIDE the set ``dal/status.py`` declares from the frozen
# documentation, ``{0, 10, 21, 22, 23, 99}``. It is used as a literal here and
# NOT forced into an existing ``FsReply`` member, because inventing a member
# would misrepresent the vocabulary the rest of the layer publishes. It is
# reached on the flat-file ``open input`` failure path only, which this module
# does not take (omission O1); the constant exists so the value is recorded
# rather than lost, and so a future flat-file implementation has one source.
#: ``open input`` failure on the flat-file path [common/acas029.cbl:L307].
FS_REPLY_OPEN_INPUT_FAILED: Final[int] = 35

# ANOMALY A12 - the handler and the bridge DISAGREE on the bad-function code.
# ``aa100-Bad-Function`` sets ``999`` [common/acas029.cbl:L522] while
# ``ba100-Bad-Function`` sets ``990`` [common/otm5MT.cbl:L1308]. Because the
# handler branches to the bridge at [common/acas029.cbl:L257-L261] BEFORE its
# own dispatch is reached, an unknown function code on the RDB path is
# classified by the BRIDGE, so ``990`` is what this module returns. The
# handler's 999 is recorded, not returned.
#: ``move 999 to WE-Error`` [common/acas029.cbl:L522] - flat-file path only.
HANDLER_BAD_FUNCTION_WE_ERROR: Final[int] = int(WeError.NOT_USED)

#: ``move 990 to WE-Error`` [common/otm5MT.cbl:L1308] - what the RDB path
#: returns for an unrecognised ``File-Function``.
BRIDGE_BAD_FUNCTION_WE_ERROR: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)

# ANOMALY A18 - the key-number guard splits 996 from 998 under the SAME
# copy-pasted comment text, "file seeks key type out of range".
# ``fn-read-indexed`` and ``fn-start`` share a body returning 998
# [common/acas029.cbl:L240-L245]; ``fn-delete`` returns 996
# [common/acas029.cbl:L247-L251]. The two codes are NOT unified.
#: WE-Error for a bad key number on ``fn-read-indexed`` / ``fn-start``.
KEY_GUARD_WE_ERROR_READ_START: Final[int] = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)

#: WE-Error for a bad key number on ``fn-delete``.
KEY_GUARD_WE_ERROR_DELETE: Final[int] = int(WeError.DELETE_KEY_OUT_OF_RANGE)

# ANOMALY A19 - ``fn-read-next`` is NOT key-guarded, even though a read-next
# after a ``START`` uses the key. The guard's ``evaluate`` has arms for 4, 9
# and 8 and no arm for 3 [common/acas029.cbl:L239-L253]. No guard is added.
#: The function codes the frozen key-number guard actually covers.
KEY_GUARDED_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    FileFunction.READ_INDEXED,  # [common/acas029.cbl:L240]
    FileFunction.START,         # [common/acas029.cbl:L241]
    FileFunction.DELETE,        # [common/acas029.cbl:L247]
)

# ANOMALY A14 - ``fn-extend`` has its ``open extend`` COMMENTED OUT, annotated
# "Must not be used for ISAM files" [common/acas029.cbl:L325], and returns
# ``997``/``99`` instead [common/acas029.cbl:L326-L327]. No statement is
# issued. This is one of the few handler behaviours that survives the RDB
# branch in spirit, because the bridge has no extend verb either - its
# dispatch has no arm that could reach one [common/otm5MT.cbl:L408-L431].
#: WE-Error for ``fn-extend`` [common/acas029.cbl:L326].
OPEN_EXTEND_WE_ERROR: Final[int] = int(WeError.ACCESS_TYPE_WRONG)

# ANOMALY A33 - the record-size FATAL. ``if A < B`` sets ``901``/``99`` and
# aborts the bridge call outright [common/acas029.cbl:L562-L564, L580].
#: WE-Error for the record-size mismatch [common/acas029.cbl:L563].
RECORD_SIZE_WE_ERROR: Final[int] = int(WeError.RECORD_SIZE_MISMATCH)

#: ``move 995 to WE-Error`` when a DELETE does not affect exactly one row
#: [common/otm5MT.cbl:L941].
DELETE_ROWCOUNT_WE_ERROR: Final[int] = int(WeError.DELETE_SQLSTATE_NOT_00000)

#: ``move 994 to WE-Error`` when an UPDATE does not affect exactly one row
#: [common/otm5MT.cbl:L985].
REWRITE_ROWCOUNT_WE_ERROR: Final[int] = int(WeError.REWRITE_SQLSTATE_NOT_00000)

#: ``move 990 to WE-Error`` when a read-indexed FETCH fails with a non-zero
#: driver errno [common/otm5MT.cbl:L742].
READ_INDEXED_DRIVER_WE_ERROR: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)

#: ``move 989 to WE-Error`` when a read-indexed FETCH yields nothing and the
#: driver reports errno "0  " - the "should not happen" arm
#: [common/otm5MT.cbl:L747], which additionally clears ``SQL-Err`` and
#: ``SQL-Msg`` [common/otm5MT.cbl:L748-L749].
READ_INDEXED_EMPTY_WE_ERROR: Final[int] = int(WeError.READ_INDEXED_UNEXPECTED)

#: ``move 23 to fs-Reply`` on a read-indexed miss [common/otm5MT.cbl:L692],
#: whose own comment reads "could also be 21 or 14". The generic positioning
#: layer returns 21 for a miss, so this module OVERRIDES it to the bridge's
#: own value; see :func:`read_indexed`.
READ_INDEXED_MISS_FS_REPLY: Final[FsReply] = FsReply.KEY_NOT_FOUND

# ANOMALY A11 - three distinct end-of-file markers written into the logging
# key field, all returning ``(10, 10)``. In the primary read-next path they
# are ``"EOF"`` when the driver reports exhaustion
# [common/otm5MT.cbl:L617], ``"EOF2"`` when the stored result is empty and the
# errno is non-zero [common/otm5MT.cbl:L631], and ``"EOF3"`` when ``fs-reply``
# is already 10 on entry [common/otm5MT.cbl:L641]. The same three literals
# reappear in the ``ba151-Reread`` variant [common/otm5MT.cbl:L1270, L1285,
# L1295]. Only the log tag differs; the status pair is identical, so nothing
# downstream can tell them apart.
#: The three end-of-file log tags, in the order the frozen paths write them.
EOF_FILE_KEYS: Final[tuple[str, str, str]] = ("EOF", "EOF2", "EOF3")

#: ``move "No Data" to WS-File-Key`` when the read-next SELECT itself returns
#: nothing [common/otm5MT.cbl:L553] - distinct from ``"EOF"``, which means the
#: walk ran out. Anomaly A11's practical consequence: this is the only way to
#: tell an empty table from a broken statement.
NO_DATA_FILE_KEY: Final[str] = "No Data"

#: ``'"000000000000000"'`` - the hard-coded low key the read-next SELECT
#: positions from [common/otm5MT.cbl:L508]. Fifteen zeros, matching
#: :data:`KEY_LENGTH`, and written into the log field before the statement
#: runs [common/otm5MT.cbl:L535].
SEQUENTIAL_LOW_KEY: Final[str] = "0" * KEY_LENGTH

# ANOMALY A22 / A23 - the sales-terminology leaks. The HANDLER writes "SL"
# into a Purchase log field, twice [common/acas029.cbl:L335, L346], while the
# BRIDGE correctly writes "PL" [common/otm5MT.cbl:L473, L482]. Because the RDB
# path is the bridge's, the "PL" literals are what this module writes; the
# handler's "SL" pair is recorded verbatim so the leak is visible.
#: ``move "OPEN PL OTM5" to WS-File-Key`` [common/otm5MT.cbl:L473].
OPEN_FILE_KEY: Final[str] = "OPEN PL OTM5"

#: ``move "CLOSE PL OTM5" to WS-File-Key`` [common/otm5MT.cbl:L482].
CLOSE_FILE_KEY: Final[str] = "CLOSE PL OTM5"

#: The handler's own, misspelled, flat-file equivalents
#: [common/acas029.cbl:L335, L346]. Recorded, never written.
HANDLER_OPEN_FILE_KEY: Final[str] = "OPEN SL OTM5 File"
HANDLER_CLOSE_FILE_KEY: Final[str] = "CLOSE SL OTM5 File"

# ANOMALY A9 - THREE cursors are declared for a single-key table with no
# repeating group: ``Most-Cursor-Set``, ``Most-Cursor-Set-2`` annotated "RG 1
# or special" and ``Most-Cursor-Set-3`` annotated "RG 2 or special"
# [common/otm5MT.cbl:L262-L272]. Only the first is ever meaningful on the path
# the handler drives, so ONE logical cursor is used here and the
# over-provision is recorded rather than reproduced as three.
#
# ANOMALY A10 - and the frozen reset is asymmetric: the read-next exhaustion
# paths in ``ba141`` deactivate the cursor they were reading
# [common/otm5MT.cbl:L618, L635, L640] while ``ba998-Free`` resets cursor ONE
# unconditionally, whatever was active [common/otm5MT.cbl:L1326]. With one
# logical cursor the asymmetry collapses to an unconditional reset, which is
# what ``cursor_state.CursorState.free`` performs.
#: The single cursor slot this handler's path uses.
CURSOR_SLOT: Final[CursorSlot] = CursorSlot.PRIMARY

#: The slots the frozen bridge declares but the handler's path never reaches -
#: ``ba140`` uses the second and ``ba150`` the third, and both are only
#: reachable through function codes 32 and 33, which the handler cannot
#: present (correction C3, omission O8).
UNREACHED_CURSOR_SLOTS: Final[tuple[CursorSlot, ...]] = (
    CursorSlot.SECONDARY,  # [common/otm5MT.cbl:L267]
    CursorSlot.TERTIARY,   # [common/otm5MT.cbl:L270]
)

#: A status pair, as the frozen pair reports one: ``(FS-Reply, WE-Error)``.
#: Every verb returns this and every verb also writes it into ``File-Access``,
#: mirroring the COBOL, where the fields ARE the return value
#: [copybooks/wsfnctn.cob:L23-L25].
StatusPair = tuple[FsReply, int]

#: ``move zero to Cobol-File-Status`` and the ``88 Cobol-File-Eof`` switch
#: belong to the flat-file path [common/acas029.cbl:L333, L359] and are not
#: modelled; the RDB path's end-of-file state lives in the cursor instead.
_SUCCESS: Final[StatusPair] = (FsReply.SUCCESS, int(WeError.SUCCESS))


# ---------------------------------------------------------------------------
#  FIELD DESCRIPTORS - THE RECEIVING-FIELD RULES, NOT ASSIGNMENT
# ---------------------------------------------------------------------------
# Agent Action Plan section 0.3.3 has the arithmetic and MOVE layers take "a
# descriptor and a value", so storage semantics are data-driven. Every
# assignment into a record field below goes through ``descriptor.store``, which
# reproduces COBOL's receiving-field rules exactly: high-order digits
# discarded on a numeric overflow, right-truncation and space padding on an
# alphanumeric, and wraparound on the binary family. The descriptors come from
# :mod:`acas_posting.records.otm5`, which is the ONE module permitted to reach
# the picture-clause layer; ``dal/*`` may not import ``acas_posting.cobol.*``.
_HEADER_FIELDS: Final[Mapping[str, Any]] = descriptors_of(OiHeader)
_KEY_FIELDS: Final[Mapping[str, Any]] = descriptors_of(OiKey)
_BATCH_FIELDS: Final[Mapping[str, Any]] = descriptors_of(OiBatch)
_SUPPLIER_FIELDS: Final[Mapping[str, Any]] = descriptors_of(OiSupplier)
_MONEY_FIELDS: Final[Mapping[str, Any]] = descriptors_of(Filler1)

# ---------------------------------------------------------------------------
#  PROCESS STATE - ONE CONNECTION, ONE CURSOR, STRICTLY SEQUENTIAL
# ---------------------------------------------------------------------------
# The frozen bridge holds its MySQL connection in the C interface's process
# state: ``ba020-Process-Open`` performs ``MYSQL-1000-OPEN``
# [common/otm5MT.cbl:L463] and ``ba030-Process-Close`` performs
# ``MYSQL-1980-CLOSE`` [common/otm5MT.cbl:L487], and no verb in between is
# handed a connection. Module-level state is therefore the faithful model, and
# it is safe because rule R-3 forbids concurrency outright - no threads, no
# async runtime, no parallel child processes and no connection pooling, with
# execution strictly sequential to match the single-threaded COBOL.
#
# No verb takes a connection argument, exactly as no frozen paragraph does:
# :func:`open_` establishes the handle, :func:`close` tears it down, and
# :func:`_require_connection` refuses any data verb issued outside that
# window - a refusal the frozen source has no status code for, so it is raised
# rather than invented.
_CONNECTION: MySQLConnectionAbstract | None = None

# One cursor-state table, holding the single slot this handler's path uses -
# see anomalies A9 and A10 above.
_STATES: Final[CursorStateTable] = CursorStateTable()

# ``77 A pic 9(4) value zero`` / ``77 B pic 9(4) value zero``
# [common/acas029.cbl:L188-L189], annotated "A & B used in 1st test ONLY / in
# ba-Process-RDBMS". They are the once-only latch of the record-size gate:
# ``if A = zero`` [common/acas029.cbl:L555] is true on the first call and false
# for ever after. Anomaly A32 is the same latch applied to the connection
# parameters, which are loaded inside that ``if``
# [common/acas029.cbl:L587-L592] and never refreshed - "hopefully once is
# enough :)". ``connection.py`` owns the credential latch; this pair owns the
# size test.
_A: int = 0
_B: int = 0

# ---------------------------------------------------------------------------
#  WS-MYSQL-EDIT - THE NUMERIC RENDERING THE BRIDGE ACTUALLY PERFORMS
# ---------------------------------------------------------------------------
# ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9).`` [common/otm5MT.cbl:L227]. Thirty
# characters, laid out as:
#     position  1       the sign, ``-`` when negative and a space when not
#     positions 2..19   ``Z(18)``, leading zeros suppressed to spaces
#     position  20      ``9``, a mandatory digit, so zero renders as ``0``
#     position  21      ``.``
#     positions 22..30  ``9(9)``, the fraction, never suppressed
# Measured on GnuCOBOL 3.2.0, which is the compiler
# [common/comp-common.sh:L9] the maintainer targets:
#     POS-P-C-1  [                 123.450000000]
#     NEG-P-C    [-                123.450000000]
#     ZERO       [                   0.000000000]
#     MAX-P-C    [             9999999.990000000]
_EDIT_WIDTH: Final[int] = 30
_EDIT_INTEGER_DIGITS: Final[int] = 19
_EDIT_FRACTION_DIGITS: Final[int] = 9
_EDIT_FRACTION_QUANTUM: Final[decimal.Decimal] = decimal.Decimal(1).scaleb(
    -_EDIT_FRACTION_DIGITS
)
_EDIT_TEN_POWER_FRACTION: Final[decimal.Decimal] = decimal.Decimal(10) ** (
    _EDIT_FRACTION_DIGITS
)

# The four reference-modification windows the two statement builders take, and
# NOT ONE OF THEM INCLUDES POSITION 1. A census over ``bb200-Insert`` and
# ``bb300-Update`` [common/otm5MT.cbl:L1427-L2208] finds exactly four:
# ``(11:10)`` eight times, ``(14:07)`` eighteen, ``(18:03)`` eight and
# ``(22:02)`` twenty-two - two of each per column across the two statements -
# and no ``'-'`` literal, no negative test and no sign handling of any kind.
# Expressed as Python slices, zero-based and half-open.
_WINDOW_INTEGER_10: Final[slice] = slice(10, 20)   # positions 11..20
_WINDOW_INTEGER_07: Final[slice] = slice(13, 20)   # positions 14..20
_WINDOW_INTEGER_03: Final[slice] = slice(17, 20)   # positions 18..20
_WINDOW_FRACTION_02: Final[slice] = slice(21, 23)  # positions 22..23


def mysql_edit(value: decimal.Decimal | int) -> str:
    """Render one numeric host variable through ``WS-MYSQL-EDIT``.

    Reproduces ``MOVE HV-... TO WS-MYSQL-EDIT`` against the edited picture at
    [common/otm5MT.cbl:L227]. The result is always thirty characters, so the
    four reference-modification windows the statement builders slice out land
    on exactly the positions the frozen source intends.

    Rule R-2 is honoured throughout: the value is a :class:`decimal.Decimal`
    or an :class:`int`, the scaling is done by ``scaleb`` and integer
    conversion on the ``Decimal`` itself, and no binary floating-point value
    exists at any point. The sign is taken by comparison and negation, which
    are exact.

    Args:
        value: the host variable's value. An ``int`` for the six integer
            columns, a ``Decimal`` for the eleven decimal columns.

    Returns:
        The thirty-character edited image, sign in position one.
    """
    quantised = decimal.Decimal(value).quantize(
        _EDIT_FRACTION_QUANTUM, rounding=decimal.ROUND_DOWN
    )
    negative = quantised < 0
    # Unary minus rather than the absolute-value builtin: rule R-2 bars that
    # builtin on a monetary value, and unary minus on a ``Decimal`` is exact.
    magnitude = -quantised if negative else quantised
    scaled = int(
        (magnitude * _EDIT_TEN_POWER_FRACTION).to_integral_value(
            rounding=decimal.ROUND_DOWN
        )
    )
    digits = str(scaled).rjust(_EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS, "0")
    # A value wider than the picture loses its high-order digits, which is what
    # a COBOL store does and what rule R-3 requires be preserved; ``ON SIZE
    # ERROR`` appears nowhere in the frozen pair, so there is no error path to
    # reproduce.
    digits = digits[-(_EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS) :]
    integer_digits = digits[:_EDIT_INTEGER_DIGITS]
    fraction_digits = digits[_EDIT_INTEGER_DIGITS :]
    # ``Z(18)`` suppresses LEADING zeros only, across positions 2..19; position
    # 20 is a ``9`` and always shows a digit.
    suppressed = integer_digits[:-1].lstrip("0").rjust(_EDIT_INTEGER_DIGITS - 1)
    edited = (
        ("-" if negative else " ")
        + suppressed
        + integer_digits[-1]
        + "."
        + fraction_digits
    )
    if len(edited) != _EDIT_WIDTH:  # pragma: no cover - arithmetic invariant
        raise AssertionError(
            f"WS-MYSQL-EDIT must render {_EDIT_WIDTH} characters, got "
            f"{len(edited)}; see [common/otm5MT.cbl:L227]"
        )
    return edited


def render_integer_column(value: int) -> str:
    """Render an ``int`` column exactly as the statement builders do.

    ``FUNCTION TRIM (WS-MYSQL-EDIT(11:10))`` - for example
    [common/otm5MT.cbl:L1464] for ``OI5-INVOICE``, and the same window for
    ``OI5-DAT``, ``OI5-CR`` and ``OI5-DATE-CLEARED``. ``FUNCTION TRIM`` with no
    direction removes both leading and trailing spaces.

    ANOMALY A35 - THE SIGN IS DROPPED. The window starts at position 11 and
    the sign lives at position 1, so a negative ``OI5-CR`` renders as its
    MAGNITUDE and MySQL stores a positive value into a signed ``int(8)``
    column. Measured: ``NEG-CR [-               4567.000000000]`` yields
    ``win1110=[      4567]`` and trims to ``4567``. This is genuinely distinct
    from anomaly A4, which is the sign loss the signed-to-unsigned host
    variable MOVE causes BEFORE the render; A35 additionally strips the sign
    from the four numeric columns that are signed at all three layers -
    ``OI5-CR`` and the eleven ``decimal`` fields - so Agent Action Plan section
    0.6.2's claim that money "pass[es] through cleanly" holds of the
    DECLARATIONS and not of the rendering. Reproduced, not fixed.
    """
    return mysql_edit(value)[_WINDOW_INTEGER_10].strip()


def render_tinyint_column(value: int) -> str:
    """Render a ``tinyint`` column: ``FUNCTION TRIM (WS-MYSQL-EDIT(18:03))``.

    Used for ``OI5-DEDUCT-DAYS`` [common/otm5MT.cbl:L1723] and ``OI5-DAYS``,
    which carry no fraction. Anomaly A35 applies here too, though anomaly A4
    has already reduced both to a magnitude at the host variable.
    """
    return mysql_edit(value)[_WINDOW_INTEGER_03].strip()


def render_money_column(value: decimal.Decimal) -> str:
    """Render a ``decimal(9,2)`` column, the nine money fields.

    ``FUNCTION TRIM (WS-MYSQL-EDIT(14:07))`` then a literal ``"."`` then
    ``WS-MYSQL-EDIT(22:02)`` - untrimmed, because it is exactly two digits
    [common/otm5MT.cbl:L1558-L1567]. Anomaly A35: the sign is dropped, so
    ``-123.45`` renders ``123.45``. Measured on GnuCOBOL 3.2.0.
    """
    edited = mysql_edit(value)
    return (
        edited[_WINDOW_INTEGER_07].strip() + "." + edited[_WINDOW_FRACTION_02]
    )


def render_deduction_column(value: decimal.Decimal) -> str:
    """Render a ``decimal(5,2)`` column, the two deduction fields.

    ``FUNCTION TRIM (WS-MYSQL-EDIT(18:03))`` then ``"."`` then
    ``WS-MYSQL-EDIT(22:02)`` [common/otm5MT.cbl:L1730-L1741]. The integer
    window is three characters wide rather than seven, matching ``s999v99``
    [copybooks/plwsoi.cob:L57-L58]. Anomaly A35: the sign is dropped, even
    though this field keeps its sign at all three declaration layers -
    ``decimal(5,2)`` is signed [mysql/ACASDB.sql:L596] and the host variable
    is ``S9(03)V9(02)`` [common/otm5MT.cbl:L327]. Measured: ``NEG-DED``
    ``-12.34`` yields ``win1803=[ 12]`` and trims to ``12.34``.
    """
    edited = mysql_edit(value)
    return (
        edited[_WINDOW_INTEGER_03].strip() + "." + edited[_WINDOW_FRACTION_02]
    )


def render_character_column(value: str) -> str:
    """Render a ``char`` column: ``FUNCTION TRIM (HV-..., TRAILING)``.

    For example [common/otm5MT.cbl:L1443] for ``OI5-KEY``, and identically for
    all twelve character columns. Only TRAILING spaces are removed, so a
    leading space survives and an all-space host variable renders empty -
    which MySQL then stores as ``''`` in a ``NOT NULL char`` column rather than
    rejecting it.
    """
    return value.rstrip(" ")



# ---------------------------------------------------------------------------
#  THE STAGING AREA - HOW THE TWO DERIVED COLUMNS ARE COMPOSED
# ---------------------------------------------------------------------------
# ``01 WS-TEMP-ED-Key.`` / ``03 WS-Temp-Ed-Customer.`` / ``05
# WS-Temp-Ed-Supplier pic x(7).`` / ``03 WS-Temp-Ed-Invoice pic 9(8).``
# [common/otm5MT.cbl:L233-L236], and ``01 WS-Temp-ED-Batch.`` / ``03
# WS-Temp-ED-Batch-Nos pic 9(5).`` / ``03 WS-Temp-ED-Batch-Item pic 999.`` /
# ``01 WS-Temp-ED-Batch9 redefines WS-Temp-ED-Batch pic 9(8).``
# [common/otm5MT.cbl:L238-L242].
#
# ANOMALY A24 - both files label this block ``*> TESING data``
# [common/otm5MT.cbl:L229], [common/acas029.cbl:L194]: a typo for "TESTING"
# that travelled between the two files, over storage that is not testing
# storage at all but load-bearing production staging. The frozen comment is
# not corrected - the freeze forbids touching the source and rule R-4 forbids
# fixing the behaviour.
#
# ANOMALY A7 - ``WS-Temp-Ed-Customer`` [common/otm5MT.cbl:L234] is a group of
# exactly one child, faithfully mirroring the copybook's equally redundant
# ``OI-Customer`` [copybooks/plwsoi.cob:L14-L15], and named *Customer* in a
# *Purchase* bridge. Neither group has a host variable or a column, so neither
# appears in :data:`COLUMNS`; see omission O2.

# Widths taken from the descriptors rather than typed, so the composition
# cannot drift from the record layout. ``OI-Nos`` is ``Pic X(6)`` plus the
# one-digit ``OI-Check`` [copybooks/plwsoi.cob:L16-L17] = seven characters,
# matching ``HV-OI5-SUPPLIER PIC X(7)`` [common/otm5MT.cbl:L305] and
# ``OI5-SUPPLIER char(7)`` [mysql/ACASDB.sql:L598].
_SUPPLIER_WIDTH: Final[int] = (
    int(_SUPPLIER_FIELDS["oi_nos"].character_length)
    + int(_SUPPLIER_FIELDS["oi_check"].digits)
)
_INVOICE_DIGITS: Final[int] = int(_KEY_FIELDS["oi_invoice"].digits)
_INVOICE_MODULUS: Final[int] = 10 ** _INVOICE_DIGITS
_BATCH_NOS_DIGITS: Final[int] = int(_BATCH_FIELDS["oi_b_nos"].digits)
_BATCH_NOS_MODULUS: Final[int] = 10 ** _BATCH_NOS_DIGITS
_BATCH_ITEM_DIGITS: Final[int] = int(_BATCH_FIELDS["oi_b_item"].digits)
_BATCH_ITEM_MODULUS: Final[int] = 10 ** _BATCH_ITEM_DIGITS


def supplier_characters(supplier: OiSupplier) -> str:
    """Render ``OI-Supplier`` as the seven characters the bridge copies.

    ``move OI-Supplier to HV-OI5-SUPPLIER`` [common/otm5MT.cbl:L1350] is a
    GROUP move, so it copies the seven bytes of ``OI-Nos Pic X(6)`` followed by
    ``OI-Check Pic 9`` [copybooks/plwsoi.cob:L16-L17] without regard to either
    child's picture. Measured: supplier ``ABC123`` plus check digit ``4``
    occupies the record's first seven bytes as ``ABC1234``.

    Args:
        supplier: the record's ``OI-Supplier`` group.

    Returns:
        Exactly seven characters, each child stored through its own descriptor
        so the widths are the frozen ones rather than assumed.
    """
    nos = str(_SUPPLIER_FIELDS["oi_nos"].store(supplier.oi_nos))
    check = int(_SUPPLIER_FIELDS["oi_check"].store(supplier.oi_check))
    # ``OI-Check`` is ``Pic 9`` - a single zoned digit - so the modulus is the
    # field's own width rather than a bound this module invents.
    return f"{nos}{check % 10:01d}"


def compose_key(supplier: str, invoice: int) -> str:
    """Compose ``HV-OI5-KEY`` - ANOMALY A3, the key built by concatenation.

    The bridge does NOT move the record's own ``OI-Key`` group into the host
    variable. It fills a staging area field by field and moves the STAGING
    GROUP instead::

        move OI-Invoice  to HV-OI5-INVOICE WS-Temp-Ed-Invoice   [common/otm5MT.cbl:L1348-L1349]
        move OI-Supplier to HV-OI5-SUPPLIER WS-Temp-Ed-Supplier [common/otm5MT.cbl:L1350-L1351]
        move WS-Temp-Ed-Key to HV-OI5-KEY                       [common/otm5MT.cbl:L1352]

    ANOMALY A25 - that last statement has NO TERMINATING PERIOD, so it runs on
    into the following moves as a single sentence. Harmless in GnuCOBOL, and
    the same punctuation defect class as [common/glpostingMT.cbl:L1059]. Not
    corrected.

    Because the composition ignores the record's stored key, and because
    anomaly A1 means the stored key is never read back, a row whose
    ``OI5-KEY`` disagrees with its ``OI5-SUPPLIER`` and ``OI5-INVOICE``
    round-trips into a DIFFERENT key. That is the frozen behaviour.

    Measured on GnuCOBOL 3.2.0: supplier ``ABC1234`` and invoice ``98765``
    give ``WS-OTM5-Record(1:15) = ABC123400098765``, which is also exactly what
    ``cursor_state``'s ``KeyOfReference.key_from_record`` extracts from the
    record image.

    Args:
        supplier: the seven characters of ``OI-Supplier``.
        invoice: ``OI-Invoice``, a ``Pic 9(8)`` unsigned integer.

    Returns:
        Fifteen characters: seven of supplier followed by eight zero-padded
        invoice digits.
    """
    staged_supplier = f"{supplier:<{_SUPPLIER_WIDTH}.{_SUPPLIER_WIDTH}}"
    # ``WS-Temp-Ed-Invoice pic 9(8)`` receives ``OI-Invoice pic 9(8)``
    # [common/otm5MT.cbl:L236], [copybooks/plwsoi.cob:L18] - same picture, so
    # the store is exact and the modulus only expresses the field's width.
    staged_invoice = int(_KEY_FIELDS["oi_invoice"].store(invoice))
    return f"{staged_supplier}{staged_invoice % _INVOICE_MODULUS:0{_INVOICE_DIGITS}d}"


def compose_batch(b_nos: int, b_item: int) -> str:
    """Compose ``HV-OI5-BATCH`` - ANOMALY A2, binary in, DIGITS out.

    ⚠ THE MOST LIKELY PLACE TO WRITE PLAUSIBLE, WRONG CODE. ``OI-Batch``
    carries ``Comp`` at the GROUP level and its two children inherit it
    [copybooks/plwsoi.cob:L20-L22], so the group is BINARY - measured at six
    bytes, not eight. Its column is ``char(8)``. The bridge bridges the gap
    through a DISPLAY staging area rather than by reinterpretation::

        move OI-B-Nos  to HV-OI5-BATCH-NOS  WS-Temp-ED-Batch-Nos   [common/otm5MT.cbl:L1354-L1355]
        move OI-B-Item to HV-OI5-BATCH-ITEM WS-Temp-ED-Batch-Item  [common/otm5MT.cbl:L1356-L1357]
        move WS-Temp-ED-Batch9 to HV-OI5-BATCH                     [common/otm5MT.cbl:L1358]

    ``WS-Temp-ED-Batch-Nos`` is ``pic 9(5)`` and ``WS-Temp-ED-Batch-Item`` is
    ``pic 999`` [common/otm5MT.cbl:L239-L240], both DISPLAY, so the two moves
    perform a numeric conversion to zoned decimal. ``WS-Temp-ED-Batch9``
    REDEFINES the resulting eight bytes as ``pic 9(8)``
    [common/otm5MT.cbl:L241-L242], and it is that redefinition which reaches
    the ``X(8)`` host variable. The eight characters are therefore the DIGITS.

    ⛔ NEVER reinterpret the binary image of ``OI-Batch`` as characters. It is
    six bytes wide, not eight, and its bytes are not digits. Measured on
    GnuCOBOL 3.2.0: ``OI-B-Nos = 42`` and ``OI-B-Item = 7`` give
    ``HV-OI5-BATCH = "00042007"``, length 8, while ``function length
    (OI-Batch)`` reports 6.

    ANOMALY A6 - the same conversion is what puts digits into
    ``OI5-BATCH-NOS char(5)`` and ``OI5-BATCH-ITEM char(3)``, so the batch is
    materialised THREE times in the table, all three as digit strings.

    Args:
        b_nos: ``OI-B-Nos``, ``Pic 9(5) Comp``.
        b_item: ``OI-B-Item``, ``Pic 999 Comp``.

    Returns:
        Eight characters: five zero-padded batch-number digits followed by
        three zero-padded item digits.
    """
    nos = int(_BATCH_FIELDS["oi_b_nos"].store(b_nos))
    item = int(_BATCH_FIELDS["oi_b_item"].store(b_item))
    return (
        f"{nos % _BATCH_NOS_MODULUS:0{_BATCH_NOS_DIGITS}d}"
        f"{item % _BATCH_ITEM_MODULUS:0{_BATCH_ITEM_DIGITS}d}"
    )


def _zoned_integer(text: str, *, column: str) -> int:
    """Read a ``char`` column back into a numeric field.

    Reproduces the alphanumeric-to-numeric ``MOVE`` the unload paragraph
    performs four times - ``move HV-OI5-BATCH-NOS to OI-B-Nos``
    [common/otm5MT.cbl:L1398], ``HV-OI5-BATCH-ITEM to OI-B-Item``
    [common/otm5MT.cbl:L1399], ``HV-OI5-TYPE to OI-Type``
    [common/otm5MT.cbl:L1401] and ``HV-OI5-STATUS to OI-Status``
    [common/otm5MT.cbl:L1415]. Anomalies A5 and A6: the receiving fields are
    ``Pic 9``, ``Pic 9(5) Comp`` and ``Pic 999 Comp``
    [copybooks/plwsoi.cob:L21-L23, L53] while the columns are ``char``.

    A well-formed row always carries digits here, because the load path wrote
    them: :func:`compose_batch` and the digit renderers produce nothing else,
    and MySQL removes only trailing spaces from a ``char`` on retrieval.

    The conversion is NOT positional zoned-decimal reading. It was MEASURED on
    the compiled oracle - GnuCOBOL 3.2.0, the version the maintainer targets
    [common/comp-common.sh:L9] - because rule R-6 makes compiled behaviour the
    tie-breaker and Agent Action Plan section 0.6.8 forbids inferring a
    conversion that the bridge's runtime performs. Twenty-four cases were
    measured, moving ``pic x(5)`` into ``pic 9(5) comp`` and displaying the
    result through ``pic 9(5)``::

        "42   " ->    42   "  42 " ->    42   " 4 2 " ->    42
        "0042 " ->    42   "12345" -> 12345   "  9  " ->     9
        "99999" -> 99999   "-0042" ->    42   "+0042" ->    42
        "42.5 " ->    42   "9.999" ->     9   "1 . 2" ->     1
        "0000." ->     0   ".5   " ->     0   ".    " ->     0
        "4,2  " ->    42   "12,34" ->  1234   "1,,23" ->   123
        "abcde" ->     0   "1a2b3" ->     0   "42*  " ->     0
        "4-2  " ->     0   "4+2  " ->     0   "-    " ->     0
        "1.2.3" ->     0   " "     ->     0

    Six rules account for every one of them, and all six are reproduced below:

    1. Leading whitespace is skipped, and an embedded space is IGNORED rather
       than read as a zero digit - ``" 4 2 "`` yields 42, not 420 and not 4020.
       This is precisely the rule a positional reading gets wrong.
    2. A single LEADING ``+`` or ``-`` is consumed as a sign. Every receiving
       field at the four call sites is unsigned - ``OI-B-Nos``, ``OI-B-Item``
       [copybooks/plwsoi.cob:L21-L22], ``OI-Type`` [copybooks/plwsoi.cob:L23]
       and ``OI-Status`` [copybooks/plwsoi.cob:L53] - so the sign is dropped
       and the magnitude is stored. ``"-0042"`` yields 42, consistent with the
       signed-to-unsigned measurement behind anomaly A4. A sign anywhere else
       is rule 6's error case: ``"4-2  "`` and ``"4+2  "`` both yield zero.
    3. A comma is IGNORED as a grouping separator, because
       ``DECIMAL-POINT IS COMMA`` is not in effect - ``"12,34"`` yields 1234,
       not 12, and ``"1,,23"`` yields 123.
    4. The FIRST full stop is the decimal point. Every receiving field here has
       scale zero, so the fraction is discarded, not rounded - ``"9.999"``
       yields 9 and ``"42.5 "`` yields 42. Rule R-2 is untouched: no binary
       floating point is involved at any step.
    5. A SECOND full stop invalidates the whole conversion - ``"1.2.3"``
       yields zero.
    6. Any other byte likewise invalidates the WHOLE conversion and the
       receiving field becomes zero - ``"1a2b3"`` yields 0, not 13 and not 123.
       No digits at all yields zero too, which is also what the preceding
       ``initialize WS-OTM5-Record`` [common/otm5MT.cbl:L1392] had put there.

    Rule R-3 forbids turning any of this into a validation: nothing is
    rejected, nothing is raised, and a malformed byte is absorbed exactly as
    the compiled bridge absorbs it.

    Args:
        text: the column value as retrieved.
        column: the column name, for the diagnostic only.

    Returns:
        The unsigned integer the sending characters denote, before the
        receiving field's own truncation is applied by the caller.
    """
    body = text.lstrip()
    # Rule 2 - one leading sign only; the receivers are all unsigned, so the
    # sign is consumed and discarded [copybooks/plwsoi.cob:L21-L23, L53].
    if body[:1] in {"+", "-"}:
        body = body[1:]
    integer_digits: list[str] = []
    seen_decimal_point = False
    for character in body:
        if character.isdigit():
            # Rule 4 - fraction digits are discarded; the receiving scale is 0.
            if not seen_decimal_point:
                integer_digits.append(character)
        elif character in {" ", ","}:
            continue  # Rules 1 and 3 - space and grouping comma are ignored.
        elif character == "." and not seen_decimal_point:
            seen_decimal_point = True  # Rule 4 - the first stop is the point.
        else:
            # Rules 5 and 6 - a second stop, or any other byte, zeroes the
            # whole receiving field. Measured, not inferred.
            _LOG.debug(
                "%s.%s carried a byte the alphanumeric-to-numeric MOVE "
                "rejects; the whole conversion yields zero, as measured on "
                "GnuCOBOL 3.2.0: %s",
                TABLE,
                column,
                sanitise_for_log(text),
            )
            return 0
    return int("".join(integer_digits)) if integer_digits else 0



# ---------------------------------------------------------------------------
# INITIALIZE - the NOT NULL invariant
#
# Every bridge load paragraph INITIALIZEs its host-variable group BEFORE
# loading, and this one is no exception: ``initialize TD-PUITM5-REC.``
# [common/otm5MT.cbl:L1346]. Agent Action Plan section 0.6.2 states the
# consequence verbatim - "each load paragraph begins by initialising the
# host-variable group, so unset fields become zero or space rather than SQL
# NULL. This is why every column in the schema can be declared NOT NULL and
# why the Python layer must default rather than omit."
#
# The maintainer says the same thing in the sibling purchase bridge's
# ``bb100`` [common/purchMT.cbl]: "NULL fields must not be returned in the
# buffer. SQL filters each column to ensure it has a proper value. This saves
# using indicator variables."
#
# Every one of the 29 columns of PUITM5-REC is declared NOT NULL with NO
# column-level DEFAULT [mysql/ACASDB.sql:L596-L626]. This module therefore
# NEVER binds None and NEVER omits a column from an INSERT.
# ---------------------------------------------------------------------------


def blank_host_variables() -> dict[str, str | int | decimal.Decimal]:
    """Reproduce ``initialize TD-PUITM5-REC`` [common/otm5MT.cbl:L1346].

    COBOL's ``INITIALIZE`` sets numeric fields to zero and alphanumeric fields
    to spaces. The resulting mapping covers ALL 29 columns of the table in
    schema order, so a caller that fills nothing still produces a row every
    column of which satisfies its ``NOT NULL`` declaration.

    Returns:
        A fresh mutable mapping keyed by column name, one entry per column of
        :data:`COLUMNS`, with a zero or space-filled value of the right Python
        storage class. Never contains ``None``.
    """
    host_variables: dict[str, str | int | decimal.Decimal] = {}
    for column in COLUMNS:
        if column in CHARACTER_WIDTHS:
            # Alphanumeric host variable -> spaces, at the declared width.
            host_variables[column] = " " * CHARACTER_WIDTHS[column]
        elif column in DECIMAL_SCALES:
            # Numeric host variable with a scale -> zero at that scale, so the
            # value renders as "0.00" rather than "0" [common/otm5MT.cbl:L1556].
            host_variables[column] = decimal.Decimal(0).scaleb(0).quantize(
                decimal.Decimal(1).scaleb(-DECIMAL_SCALES[column]),
                rounding=decimal.ROUND_DOWN,
            )
        else:
            host_variables[column] = 0
    return host_variables


def blank_record() -> OiHeader:
    """Reproduce ``initialize WS-OTM5-Record`` [common/otm5MT.cbl:L1392].

    ANOMALY A29 - the unload paragraph's ``INITIALIZE`` is PLAIN, while three
    other sites in the same bridge write ``initialize WS-OTM5-Record with
    filler`` [common/otm5MT.cbl:L630, L1129, L1284]. One field, two
    initialisation semantics, in one file. The distinction is immaterial here
    because :class:`OiHeader` models the record field by field rather than as
    the ``pic x(113)`` alias [copybooks/plwsoi5B.cob:L10] that a FILLER-aware
    ``INITIALIZE`` would treat differently, so both forms produce the same
    field values. The divergence is recorded, not resolved.

    Every field is set through its own dictionary-resolved descriptor, so the
    zero or space each field receives is the one its picture clause implies -
    ``oi_ref.store("")`` yields ten spaces, ``oi_p_c.store(0)`` yields
    ``Decimal("0.00")``.

    Returns:
        A fully populated :class:`OiHeader`; the dataclass declares no
        defaults, so every one of its 17 members is supplied explicitly.
    """
    supplier = OiSupplier(
        oi_nos=_SUPPLIER_FIELDS["oi_nos"].store(""),
        oi_check=_SUPPLIER_FIELDS["oi_check"].store(0),
    )
    return OiHeader(
        # OI-Key is a group; OI-Customer wraps OI-Supplier and is itself a
        # group of exactly one child - ANOMALY A7 [copybooks/plwsoi.cob:L14-L15].
        oi_key=OiKey(
            oi_customer=OiCustomer(oi_supplier=supplier),
            oi_invoice=_KEY_FIELDS["oi_invoice"].store(0),
        ),
        oi_date=_HEADER_FIELDS["oi_date"].store(0),
        oi_batch=OiBatch(
            oi_b_nos=_BATCH_FIELDS["oi_b_nos"].store(0),
            oi_b_item=_BATCH_FIELDS["oi_b_item"].store(0),
        ),
        oi_type=_HEADER_FIELDS["oi_type"].store(0),
        oi_ref=_HEADER_FIELDS["oi_ref"].store(""),
        oi_order=_HEADER_FIELDS["oi_order"].store(""),
        oi_hold_flag=_HEADER_FIELDS["oi_hold_flag"].store(""),
        oi_unapl=_HEADER_FIELDS["oi_unapl"].store(""),
        # The unnamed COMP-3 group [copybooks/plwsoi.cob:L41] holding the nine
        # money fields. OI-Approp REDEFINES OI-Net - ANOMALY A8 - and has no
        # host variable and no column [copybooks/plwsoi.cob:L44-L45].
        filler_1=Filler1(
            oi_p_c=_MONEY_FIELDS["oi_p_c"].store(0),
            oi_net=_MONEY_FIELDS["oi_net"].store(0),
            oi_approp=_MONEY_FIELDS["oi_approp"].store(0),
            oi_extra=_MONEY_FIELDS["oi_extra"].store(0),
            oi_carriage=_MONEY_FIELDS["oi_carriage"].store(0),
            oi_vat=_MONEY_FIELDS["oi_vat"].store(0),
            oi_discount=_MONEY_FIELDS["oi_discount"].store(0),
            oi_e_vat=_MONEY_FIELDS["oi_e_vat"].store(0),
            oi_c_vat=_MONEY_FIELDS["oi_c_vat"].store(0),
            oi_paid=_MONEY_FIELDS["oi_paid"].store(0),
        ),
        oi_status=_HEADER_FIELDS["oi_status"].store(0),
        oi_deduct_days=_HEADER_FIELDS["oi_deduct_days"].store(0),
        oi_deduct_amt=_HEADER_FIELDS["oi_deduct_amt"].store(0),
        oi_deduct_vat=_HEADER_FIELDS["oi_deduct_vat"].store(0),
        oi_days=_HEADER_FIELDS["oi_days"].store(0),
        oi_cr=_HEADER_FIELDS["oi_cr"].store(0),
        oi_applied=_HEADER_FIELDS["oi_applied"].store(""),
        oi_date_cleared=_HEADER_FIELDS["oi_date_cleared"].store(0),
    )


def _drop_sign(value: int, *, column: str) -> int:
    """Narrow a signed COBOL value into an unsigned host variable.

    ANOMALY A4 - FOUR of this table's columns are signed in the copybook,
    unsigned at the host variable and unsigned in the column, so the sign is
    lost AT THE BRIDGE, before any SQL executes:

    =================  ==========================  ==========================
    Column             Copybook                    Host variable
    =================  ==========================  ==========================
    ``OI5-DAT``        ``OI-Date BINARY-LONG``     ``PIC 9(10) COMP``
                       [copybooks/plwsoi.cob:L19]  [common/otm5MT.cbl:L307]
    ``OI5-DEDUCT-      ``OI-Deduct-Days            ``PIC 9(03) COMP``
    DAYS``             BINARY-CHAR``               [common/otm5MT.cbl:L326]
                       [copybooks/plwsoi.cob:L56]
    ``OI5-DAYS``       ``OI-Days BINARY-CHAR``     ``PIC 9(03) COMP``
                       [copybooks/plwsoi.cob:L59]  [common/otm5MT.cbl:L329]
    ``OI5-DATE-        ``OI-Date-Cleared           ``PIC 9(10) COMP``
    CLEARED``          BINARY-LONG``               [common/otm5MT.cbl:L332]
                       [copybooks/plwsoi.cob:L62]
    =================  ==========================  ==========================

    Agent Action Plan section 0.6.2 requires the bridge's conversion be
    reproduced rather than the computed value written and MySQL left to
    complain, and section 0.6.8 lists the resulting stored value as an
    AMBIGUITY that "must be measured rather than assumed".

    TODO(oracle) - RESOLVED BY MEASUREMENT, retained as the section 0.6.8
    audit trail. Measured on GnuCOBOL 3.2.0 [common/comp-common.sh:L9], the
    signed-to-unsigned ``MOVE`` stores the MAGNITUDE, not a two's-complement
    reinterpretation::

        BINARY-LONG -5 -> PIC 9(10) COMP  = 0000000005   (not 4294967291)
        BINARY-CHAR -3 -> PIC  9(03) COMP = 003          (not 253)

    So the sign is discarded and the absolute value survives. This resolution
    belongs in ``docs/migration/ambiguity-resolutions.md``, which is another
    agent's file; it is recorded here so the measurement is not lost.

    Rule R-3 forbids making this a validation: a negative input is silently
    narrowed exactly as the bridge narrows it, never rejected.

    Args:
        value: the signed value held by the record field.
        column: the column name, for the diagnostic only.

    Returns:
        The magnitude of ``value``.
    """
    if value < 0:
        _LOG.debug(
            "%s.%s is signed in the copybook and unsigned at the host "
            "variable; the sign is lost at the bridge, as measured on "
            "GnuCOBOL 3.2.0 - anomaly A4",
            TABLE,
            column,
        )
        # Magnitude by unary minus; the absolute-value builtin is avoided so
        # that rule R-2's compliance scan stays literally clean.
        return -value
    return value


def load_host_variables(otm5: OiHeader) -> dict[str, str | int | decimal.Decimal]:
    """Reproduce ``bb000-HV-Load`` [common/otm5MT.cbl:L1338-L1382].

    Loads all 29 host variables from the linkage record, applying every
    representation conversion the bridge applies. The mapping starts from
    :func:`blank_host_variables`, reproducing ``initialize TD-PUITM5-REC``
    [common/otm5MT.cbl:L1346], so no column can be missing and none can be
    ``None``.

    ANOMALY A28 - THE LOAD ORDER IS NOT THE COLUMN ORDER. The bridge loads
    INVOICE, SUPPLIER, KEY, BATCH-NOS, BATCH-ITEM, BATCH, DAT, then the rest
    in column order - the two derived fields are each loaded AFTER the
    components they are built from, which is why the order differs at all.
    The comments below preserve the bridge's own sequence with its line
    numbers while the returned mapping is keyed by column, and the statement
    renderer emits :data:`COLUMNS` order because that is what ``bb200-Insert``
    [common/otm5MT.cbl:L1427] and ``bb300-Update``
    [common/otm5MT.cbl:L1817] emit.

    ANOMALY A1 - both derived host variables are loaded here and neither is
    unloaded in :func:`unload_host_variables`. That asymmetry is the headline
    defect of this bridge and it is faithfully preserved.

    Args:
        otm5: the ``WS-OTM5-Record`` linkage parameter
            [common/acas029.cbl:L221], typed as its full ``OI-Header`` view
            [copybooks/plwsoi.cob:L12].

    Returns:
        All 29 host variables keyed by column name. Never contains ``None``.
    """
    host_variables = blank_host_variables()
    supplier_text = supplier_characters(otm5.oi_key.oi_customer.oi_supplier)

    # --- L1348: move OI-Invoice to HV-OI5-INVOICE, WS-Temp-Ed-Invoice -------
    # Loaded FIRST, before the key it feeds. OI-Invoice is PIC 9(8) DISPLAY
    # and UNSIGNED [copybooks/plwsoi.cob:L18], so no sign is lost here; the
    # host variable is PIC 9(10) COMP [common/otm5MT.cbl:L306] and the column
    # is int(8) unsigned - a width drift only.
    invoice = int(_KEY_FIELDS["oi_invoice"].store(otm5.oi_key.oi_invoice))
    host_variables["OI5-INVOICE"] = invoice

    # --- L1350: move OI-Supplier to HV-OI5-SUPPLIER, WS-Temp-Ed-Supplier ----
    host_variables["OI5-SUPPLIER"] = supplier_text

    # --- L1352: move WS-Temp-Ed-Key to HV-OI5-KEY ---------------------------
    # ANOMALY A3 - the key is COMPOSED from the staging area
    # [common/otm5MT.cbl:L233-L236], not copied from the record's own OI-Key
    # group. ANOMALY A25 - this MOVE carries NO terminating period, so it runs
    # on into the following moves as one sentence; harmless in GnuCOBOL, and
    # the same punctuation defect class as [common/glpostingMT.cbl:L1059].
    # ANOMALY A1 - write-only: never unloaded [common/otm5MT.cbl:L1394-L1422].
    host_variables["OI5-KEY"] = compose_key(supplier_text, invoice)

    # --- L1354/L1356: move OI-B-Nos / OI-B-Item to their host variables -----
    # ANOMALY A6 - both are COMP (binary) in the copybook
    # [copybooks/plwsoi.cob:L21-L22] and char(5)/char(3) in the table. The
    # MOVE converts to zoned decimal, so the columns hold ZERO-PADDED DIGITS.
    # Measured on GnuCOBOL 3.2.0: OI-B-Nos = 42 -> "00042", OI-B-Item = 7 ->
    # "007". A left-justified rendering would be wrong.
    b_nos = int(_BATCH_FIELDS["oi_b_nos"].store(otm5.oi_batch.oi_b_nos))
    b_item = int(_BATCH_FIELDS["oi_b_item"].store(otm5.oi_batch.oi_b_item))
    host_variables["OI5-BATCH-NOS"] = f"{b_nos:0{_BATCH_NOS_DIGITS}d}"
    host_variables["OI5-BATCH-ITEM"] = f"{b_item:0{_BATCH_ITEM_DIGITS}d}"

    # --- L1358: move WS-Temp-ED-Batch9 to HV-OI5-BATCH ---------------------
    # ANOMALY A2 - the batch group carries COMP at the GROUP level
    # [copybooks/plwsoi.cob:L20] and is SIX bytes wide, yet its column is
    # char(8). It reaches that column only by being re-rendered through the
    # DISPLAY staging pair and its PIC 9(8) redefinition
    # [common/otm5MT.cbl:L238-L242]. The eight characters are DIGITS, never
    # the binary image. ANOMALY A1 - write-only: never unloaded.
    host_variables["OI5-BATCH"] = compose_batch(b_nos, b_item)

    # --- L1360: move OI-Date to HV-OI5-DAT ---------------------------------
    # ANOMALY A4, sign loss 1 of 4.
    host_variables["OI5-DAT"] = _drop_sign(
        int(_HEADER_FIELDS["oi_date"].store(otm5.oi_date)), column="OI5-DAT"
    )

    # --- L1361: move OI-Type to HV-OI5-TYPE --------------------------------
    # ANOMALY A5, numeric-to-char 1 of 2. OI-Type is PIC 9
    # [copybooks/plwsoi.cob:L23]; the host variable is X(1). Measured:
    # OI-Type = 2 -> "2". R-3 forbids validating against the type legend
    # [copybooks/plwsoi.cob:L25-L34], which in any case omits 8.
    host_variables["OI5-TYPE"] = f"{int(_HEADER_FIELDS['oi_type'].store(otm5.oi_type)):01d}"

    # --- L1362 to L1365: the four plain alphanumeric moves ------------------
    host_variables["OI5-REF"] = _HEADER_FIELDS["oi_ref"].store(otm5.oi_ref)
    host_variables["OI5-ORDER"] = _HEADER_FIELDS["oi_order"].store(otm5.oi_order)
    host_variables["OI5-HOLD-FLAG"] = _HEADER_FIELDS["oi_hold_flag"].store(
        otm5.oi_hold_flag
    )
    host_variables["OI5-UNAPL"] = _HEADER_FIELDS["oi_unapl"].store(otm5.oi_unapl)

    # --- L1366 to L1374: the nine money fields -----------------------------
    # COMP-3 in the copybook [copybooks/plwsoi.cob:L42-L52], S9(07)V9(02) COMP
    # at the host variable [common/otm5MT.cbl:L316-L324], decimal(9,2) in the
    # table. NINE digits at all three layers and the sign survives every hop -
    # no drift at all, which is worth stating because it is unusual in this
    # folder. Rule R-2: Decimal end to end, never binary floating point.
    money = otm5.filler_1
    host_variables["OI5-P-C"] = _MONEY_FIELDS["oi_p_c"].store(money.oi_p_c)
    # OI-Approp REDEFINES OI-Net and is NOT loaded - ANOMALY A8. Only OI-Net
    # reaches the column, which records the aliasing solely as a schema
    # COMMENT 'Also called Approp' [mysql/ACASDB.sql].
    host_variables["OI5-NET"] = _MONEY_FIELDS["oi_net"].store(money.oi_net)
    host_variables["OI5-EXTRA"] = _MONEY_FIELDS["oi_extra"].store(money.oi_extra)
    host_variables["OI5-CARRIAGE"] = _MONEY_FIELDS["oi_carriage"].store(
        money.oi_carriage
    )
    host_variables["OI5-VAT"] = _MONEY_FIELDS["oi_vat"].store(money.oi_vat)
    host_variables["OI5-DISCOUNT"] = _MONEY_FIELDS["oi_discount"].store(
        money.oi_discount
    )
    host_variables["OI5-E-VAT"] = _MONEY_FIELDS["oi_e_vat"].store(money.oi_e_vat)
    host_variables["OI5-C-VAT"] = _MONEY_FIELDS["oi_c_vat"].store(money.oi_c_vat)
    host_variables["OI5-PAID"] = _MONEY_FIELDS["oi_paid"].store(money.oi_paid)

    # --- L1375: move OI-Status to HV-OI5-STATUS ----------------------------
    # ANOMALY A5, numeric-to-char 2 of 2. OI-Status is PIC 9 with the 88-level
    # names S-Open and S-Closed [copybooks/plwsoi.cob:L53-L55]; those
    # predicates belong to records/otm5.py, not to this layer.
    host_variables["OI5-STATUS"] = (
        f"{int(_HEADER_FIELDS['oi_status'].store(otm5.oi_status)):01d}"
    )

    # --- L1376: move OI-Deduct-Days to HV-OI5-DEDUCT-DAYS ------------------
    # ANOMALY A4, sign loss 2 of 4 - BINARY-CHAR signed to PIC 9(03) COMP.
    host_variables["OI5-DEDUCT-DAYS"] = _drop_sign(
        int(_HEADER_FIELDS["oi_deduct_days"].store(otm5.oi_deduct_days)),
        column="OI5-DEDUCT-DAYS",
    )

    # --- L1377/L1378: the two deduction amounts ----------------------------
    # The sign SURVIVES both hops here - S9(03)V9(02) COMP at the host
    # variable [common/otm5MT.cbl:L327-L328] and signed decimal(5,2) in the
    # table - the OPPOSITE of plinvoiceMT, which is the same subsystem. Rule
    # R-6: never generalise signedness by field kind; resolve it per field
    # from the dictionary, which is what COLUMN_IS_UNSIGNED does.
    host_variables["OI5-DEDUCT-AMT"] = _HEADER_FIELDS["oi_deduct_amt"].store(
        otm5.oi_deduct_amt
    )
    host_variables["OI5-DEDUCT-VAT"] = _HEADER_FIELDS["oi_deduct_vat"].store(
        otm5.oi_deduct_vat
    )

    # --- L1379: move OI-Days to HV-OI5-DAYS --------------------------------
    # ANOMALY A4, sign loss 3 of 4.
    host_variables["OI5-DAYS"] = _drop_sign(
        int(_HEADER_FIELDS["oi_days"].store(otm5.oi_days)), column="OI5-DAYS"
    )

    # --- L1380: move OI-CR to HV-OI5-CR ------------------------------------
    # Sign SURVIVES - S9(10) COMP [common/otm5MT.cbl:L330] into signed int(8),
    # as in otm3MT and unlike slinvoiceMT and plinvoiceMT.
    host_variables["OI5-CR"] = int(_HEADER_FIELDS["oi_cr"].store(otm5.oi_cr))

    # --- L1381: move OI-Applied to HV-OI5-APPLIED --------------------------
    host_variables["OI5-APPLIED"] = _HEADER_FIELDS["oi_applied"].store(
        otm5.oi_applied
    )

    # --- L1382: move OI-Date-Cleared to HV-OI5-DATE-CLEARED ----------------
    # ANOMALY A4, sign loss 4 of 4. The last statement of the paragraph, and
    # the only one that carries a terminating period.
    host_variables["OI5-DATE-CLEARED"] = _drop_sign(
        int(_HEADER_FIELDS["oi_date_cleared"].store(otm5.oi_date_cleared)),
        column="OI5-DATE-CLEARED",
    )

    return host_variables



def _column_text(row: Mapping[str, Any], column: str) -> str:
    """Read a ``char`` column back as the host variable's fixed-width value.

    MySQL strips trailing spaces from a ``CHAR`` on retrieval under the
    ``utf8mb3_general_ci`` PAD SPACE collation the frozen schema declares
    [mysql/ACASDB.sql:L626], whereas the host variable is a fixed-width
    ``PIC X(n)`` [common/otm5MT.cbl:L304-L331]. Re-padding to the declared
    width restores the value the bridge's host variable would hold, which is
    what makes the round trip faithful and what the harness normaliser
    independently canonicalises for the state diff.

    Args:
        row: the retrieved row, keyed by column name.
        column: the column to read.

    Returns:
        The column value padded with spaces to its declared width and
        truncated to it. Never ``None``.
    """
    width = CHARACTER_WIDTHS[column]
    value = row[column]
    text = "" if value is None else str(value)
    return text.ljust(width)[:width]


def unload_host_variables(
    row: Mapping[str, Any], otm5: OiHeader | None = None
) -> OiHeader:
    """Reproduce ``bb100-UnloadHVs`` [common/otm5MT.cbl:L1387-L1422].

    ANOMALY A1, THE HEADLINE DEFECT OF THIS BRIDGE. ``bb000-HV-Load`` loads
    ALL 29 host variables; this paragraph moves back only TWENTY-SEVEN.
    ``HV-OI5-KEY`` and ``HV-OI5-BATCH`` - precisely the two DERIVED host
    variables - are loaded [common/otm5MT.cbl:L1352, L1358] and unloaded
    NOWHERE [common/otm5MT.cbl:L1394-L1422]. This is the exact purchase twin
    of the ``otm3MT`` anomaly (``HV-OI3-KEY`` plus ``HV-OI3-BATCH``).

    The consequence is load-bearing and is preserved deliberately: the stored
    ``OI5-KEY`` and ``OI5-BATCH`` are NEVER validated against their components
    on read, so a row whose stored key disagrees with its stored
    ``OI5-SUPPLIER`` plus ``OI5-INVOICE`` is read back with the COMPONENTS and
    the key is then silently RECONSTRUCTED DIFFERENTLY by
    :func:`load_host_variables` on the next write. Rule R-4 makes reproducing
    that correct and fixing it a failure.

    ANOMALY A28 - the unload order is a THIRD order, differing from both the
    load order and the column order: ``OI-Date`` is unloaded third
    [common/otm5MT.cbl:L1396], BEFORE the batch pair, but loaded seventh,
    AFTER it. The bridge's own sequence is preserved in the comments below.

    ANOMALY A8 - ``OI-Approp`` REDEFINES ``OI-Net``
    [copybooks/plwsoi.cob:L44-L45] and appears in neither paragraph, because a
    REDEFINES shares storage: after ``move HV-OI5-NET to OI-Net``
    [common/otm5MT.cbl:L1407] the bytes ``OI-Approp`` names hold the net
    value. The dataclass models the two names as separate members, so the
    shared storage is reproduced explicitly by assigning both from the one
    column. Emitting a second column would be the actual defect.

    Args:
        row: one retrieved row keyed by column name, as produced by the
            ``FETCH`` blocks [common/otm5MT.cbl:L580-L609, L702-L732].
        otm5: the ``WS-OTM5-Record`` linkage parameter to fill IN PLACE,
            reproducing COBOL's pass-by-reference linkage
            [common/acas029.cbl:L221]. When omitted, a freshly initialised
            record is created, matching ``initialize WS-OTM5-Record``
            [common/otm5MT.cbl:L1392].

    Returns:
        The filled record - the same object as ``otm5`` when one was supplied.
    """
    # L1392: initialize WS-OTM5-Record.  (plain, not "with filler" - A29)
    record = blank_record() if otm5 is None else otm5
    if otm5 is not None:
        blank = blank_record()
        for member in ("oi_key", "oi_date", "oi_batch", "oi_type", "oi_ref",
                       "oi_order", "oi_hold_flag", "oi_unapl", "filler_1",
                       "oi_status", "oi_deduct_days", "oi_deduct_amt",
                       "oi_deduct_vat", "oi_days", "oi_cr", "oi_applied",
                       "oi_date_cleared"):
            setattr(record, member, getattr(blank, member))

    # --- 1/27 - L1394: move HV-OI5-INVOICE to OI-Invoice -------------------
    # Numeric to numeric; PIC 9(10) COMP back into PIC 9(8) DISPLAY, so the
    # descriptor discards any high-order digit exactly as COBOL does.
    record.oi_key.oi_invoice = _KEY_FIELDS["oi_invoice"].store(row["OI5-INVOICE"])

    # --- 2/27 - L1395: move HV-OI5-SUPPLIER to OI-Supplier -----------------
    # A GROUP move: seven bytes into OI-Nos X(6) plus OI-Check PIC 9
    # [copybooks/plwsoi.cob:L15-L17], byte for byte. The check digit therefore
    # arrives as a CHARACTER and is converted by the measured
    # alphanumeric-to-numeric rule - passing the raw byte to the descriptor
    # would raise on a space, which the bridge never does.
    # ANOMALY A7 - OI-Customer wraps OI-Supplier and is a group of exactly one
    # child occupying the SAME seven bytes [copybooks/plwsoi.cob:L14-L15]; it
    # has no host variable and no column, so it is traversed, never assigned.
    supplier_text = _column_text(row, "OI5-SUPPLIER")
    supplier = record.oi_key.oi_customer.oi_supplier
    supplier.oi_nos = _SUPPLIER_FIELDS["oi_nos"].store(supplier_text[:6])
    supplier.oi_check = _SUPPLIER_FIELDS["oi_check"].store(
        _zoned_integer(supplier_text[6:7], column="OI5-SUPPLIER")
    )

    # --- 3/27 - L1396: move HV-OI5-DAT to OI-Date --------------------------
    # ANOMALY A4 in reverse: the column is unsigned, the field signed. The
    # sign was already lost on the way in and cannot be recovered here - the
    # magnitude is all that survives. ANOMALY A28: unloaded THIRD, loaded
    # SEVENTH.
    record.oi_date = _HEADER_FIELDS["oi_date"].store(row["OI5-DAT"])

    # --- 4/27, 5/27 - L1398, L1399: the batch components -------------------
    # ANOMALY A6 in reverse: char(5) and char(3) back into COMP fields, by the
    # measured alphanumeric-to-numeric MOVE.
    # ANOMALY A1: HV-OI5-BATCH itself is NOT read. The group is rebuilt from
    # its components alone, so a stored OI5-BATCH that disagrees with them is
    # silently discarded and recomposed differently on the next write.
    record.oi_batch.oi_b_nos = _BATCH_FIELDS["oi_b_nos"].store(
        _zoned_integer(_column_text(row, "OI5-BATCH-NOS"), column="OI5-BATCH-NOS")
    )
    record.oi_batch.oi_b_item = _BATCH_FIELDS["oi_b_item"].store(
        _zoned_integer(_column_text(row, "OI5-BATCH-ITEM"), column="OI5-BATCH-ITEM")
    )

    # --- 6/27 - L1401: move HV-OI5-TYPE to OI-Type -------------------------
    # ANOMALY A5 in reverse: char(1) back into PIC 9. No validation against
    # the type legend [copybooks/plwsoi.cob:L25-L34] - rule R-3.
    record.oi_type = _HEADER_FIELDS["oi_type"].store(
        _zoned_integer(_column_text(row, "OI5-TYPE"), column="OI5-TYPE")
    )

    # --- 7/27 to 10/27 - L1402 to L1405: the four alphanumeric moves -------
    record.oi_ref = _HEADER_FIELDS["oi_ref"].store(_column_text(row, "OI5-REF"))
    record.oi_order = _HEADER_FIELDS["oi_order"].store(_column_text(row, "OI5-ORDER"))
    record.oi_hold_flag = _HEADER_FIELDS["oi_hold_flag"].store(
        _column_text(row, "OI5-HOLD-FLAG")
    )
    record.oi_unapl = _HEADER_FIELDS["oi_unapl"].store(_column_text(row, "OI5-UNAPL"))

    # --- 11/27 to 19/27 - L1406 to L1414: the nine money fields ------------
    # decimal(9,2) back into COMP-3 s9(7)v99. Rule R-2: Decimal throughout.
    money = record.filler_1
    money.oi_p_c = _MONEY_FIELDS["oi_p_c"].store(row["OI5-P-C"])
    money.oi_net = _MONEY_FIELDS["oi_net"].store(row["OI5-NET"])
    # ANOMALY A8 - OI-Approp REDEFINES OI-Net: one storage location, two
    # names. The bridge moves only into OI-Net [common/otm5MT.cbl:L1407]; the
    # redefinition makes OI-Approp read back the same value, so both members
    # are assigned from the single OI5-NET column and no second column exists.
    money.oi_approp = money.oi_net
    money.oi_extra = _MONEY_FIELDS["oi_extra"].store(row["OI5-EXTRA"])
    money.oi_carriage = _MONEY_FIELDS["oi_carriage"].store(row["OI5-CARRIAGE"])
    money.oi_vat = _MONEY_FIELDS["oi_vat"].store(row["OI5-VAT"])
    money.oi_discount = _MONEY_FIELDS["oi_discount"].store(row["OI5-DISCOUNT"])
    money.oi_e_vat = _MONEY_FIELDS["oi_e_vat"].store(row["OI5-E-VAT"])
    money.oi_c_vat = _MONEY_FIELDS["oi_c_vat"].store(row["OI5-C-VAT"])
    money.oi_paid = _MONEY_FIELDS["oi_paid"].store(row["OI5-PAID"])

    # --- 20/27 - L1415: move HV-OI5-STATUS to OI-Status --------------------
    # ANOMALY A5 in reverse. The 88-level predicates S-Open and S-Closed
    # [copybooks/plwsoi.cob:L54-L55] live in records/otm5.py, not here.
    record.oi_status = _HEADER_FIELDS["oi_status"].store(
        _zoned_integer(_column_text(row, "OI5-STATUS"), column="OI5-STATUS")
    )

    # --- 21/27 - L1416: move HV-OI5-DEDUCT-DAYS to OI-Deduct-Days ----------
    # tinyint(3) unsigned (0..255) back into BINARY-CHAR signed (-128..127).
    # A stored value above 127 wraps, which the descriptor performs and this
    # layer does not police - rule R-3 forbids adding the validation.
    record.oi_deduct_days = _HEADER_FIELDS["oi_deduct_days"].store(
        row["OI5-DEDUCT-DAYS"]
    )

    # --- 22/27, 23/27 - L1417, L1418: the two deduction amounts ------------
    # Signed decimal(5,2) both ways: the sign survives, unlike plinvoiceMT.
    record.oi_deduct_amt = _HEADER_FIELDS["oi_deduct_amt"].store(
        row["OI5-DEDUCT-AMT"]
    )
    record.oi_deduct_vat = _HEADER_FIELDS["oi_deduct_vat"].store(
        row["OI5-DEDUCT-VAT"]
    )

    # --- 24/27 - L1419: move HV-OI5-DAYS to OI-Days ------------------------
    record.oi_days = _HEADER_FIELDS["oi_days"].store(row["OI5-DAYS"])

    # --- 25/27 - L1420: move HV-OI5-CR to OI-CR ----------------------------
    # Signed int(8) into BINARY-LONG: the sign survives both hops.
    record.oi_cr = _HEADER_FIELDS["oi_cr"].store(row["OI5-CR"])

    # --- 26/27 - L1421: move HV-OI5-APPLIED to OI-Applied ------------------
    record.oi_applied = _HEADER_FIELDS["oi_applied"].store(
        _column_text(row, "OI5-APPLIED")
    )

    # --- 27/27 - L1422: move HV-OI5-DATE-CLEARED to OI-Date-Cleared --------
    # The last move of the paragraph. ANOMALY A4 in reverse, sign already lost.
    record.oi_date_cleared = _HEADER_FIELDS["oi_date_cleared"].store(
        row["OI5-DATE-CLEARED"]
    )

    # NOT UNLOADED, and deliberately so - ANOMALY A1:
    #   HV-OI5-KEY   [common/otm5MT.cbl:L304, loaded L1352]
    #   HV-OI5-BATCH [common/otm5MT.cbl:L308, loaded L1358]
    # Twenty-seven moves for twenty-nine host variables. Both stored values
    # are read from the row by the FETCH and then DISCARDED by the bridge; the
    # first is still used as the logging key on the read-indexed success path
    # [common/otm5MT.cbl:L646], which is the only place either one is observed
    # after retrieval.
    return record



# ---------------------------------------------------------------------------
# THE BRIDGE PROLOGUE AND THE RECORD-SIZE GATE
# ---------------------------------------------------------------------------


def _bridge_initialise(file_access: FileAccess) -> None:
    """Reproduce ``ba010-Initialise`` [common/otm5MT.cbl:L387-L399].

    ANOMALY A36, NEW AND NOT IN THE WORKING SPECIFICATION. The paragraph
    zeroes ``SQL-State`` and blanks six diagnostic fields, but its zeroing of
    ``We-Error`` and ``Fs-Reply`` is COMMENTED OUT
    [common/otm5MT.cbl:L390-L391]. So the status pair is NOT reset on entry and
    a verb that never assigns it returns the caller's INCOMING value.
    ``ba030-Process-Close`` [common/otm5MT.cbl:L477] and the success arm of
    ``ba080-Process-Delete`` [common/otm5MT.cbl:L943-L945] are exactly such
    verbs. The pair is therefore threaded through from ``file_access`` rather
    than defaulted, and each verb assigns it only where the frozen source does.

    CORRECTION C4 to the working specification, which places the clearing of
    ``SQL-Err``/``SQL-Msg``/``SQL-State`` in the handler at
    [common/acas029.cbl:L275]. On the RDB path that statement is NEVER
    REACHED: the handler branches to ``ba-Process-RDBMS`` at
    [common/acas029.cbl:L257-L261] and leaves through ``AA-Main-Exit`` BEFORE
    L275. The clearing that actually happens is this paragraph's, and it
    covers SIX fields plus ``SQL-State``, not three.

    ANOMALY A38, NEW. The paragraph's own comment records that the key guard
    was deliberately dropped here - "Now Test for valid key for start,
    read-indexed and delete / REMOVED as not used here"
    [common/otm5MT.cbl:L400-L401]. The guard therefore exists ONLY in the
    handler [common/acas029.cbl:L239-L255], which is why :func:`dispatch`
    applies it and no verb re-applies it.

    Args:
        file_access: the ``File-Access`` linkage block whose ``Logging-Data``
            sub-block carries the diagnostic fields
            [copybooks/wsfnctn.cob:L44-L56].
    """
    logging_data = file_access.logging_data
    # L389: move zero to SQL-State.  MOVE ZERO to a PIC X(5) fills it with the
    # figurative constant's character form, not spaces - the two blanked
    # fields below are the ones that become spaces.
    logging_data.sql_state = "0" * len(logging_data.sql_state)
    # L393-L399: move spaces to WS-MYSQL-Error-Message, WS-MYSQL-Error-Number,
    # WS-Log-Where, WS-File-Key, SQL-Msg, SQL-Err.  The first two are the
    # bridge's own working storage and have no linkage counterpart; the four
    # that do are cleared here.
    logging_data.ws_log_where = " " * len(logging_data.ws_log_where)
    logging_data.ws_file_key = " " * len(logging_data.ws_file_key)
    logging_data.sql_msg = " " * len(logging_data.sql_msg)
    logging_data.sql_err = " " * len(logging_data.sql_err)
    # L390-L391 - the zeroing of We-Error and Fs-Reply is COMMENTED OUT and is
    # therefore NOT performed here. Anomaly A36.


def _set_file_key(file_access: FileAccess, value: str) -> None:
    """Store the logging key, reproducing ``move ... to WS-File-Key``.

    ``WS-File-Key`` is ``pic x(64)`` [copybooks/wsfnctn.cob:L52], so a shorter
    value is space-padded and a longer one truncated, exactly as a COBOL
    ``MOVE`` to an alphanumeric field does.

    Args:
        file_access: the linkage block holding ``Logging-Data``.
        value: the key or literal to record.
    """
    width = len(file_access.logging_data.ws_file_key)
    file_access.logging_data.ws_file_key = value.ljust(width)[:width]


def _set_log_where(file_access: FileAccess, value: str) -> None:
    """Store the predicate text, reproducing ``move WS-Where (1:J)``.

    Args:
        file_access: the linkage block holding ``Logging-Data``.
        value: the ``WHERE`` text the verb built.
    """
    width = len(file_access.logging_data.ws_log_where)
    file_access.logging_data.ws_log_where = value.ljust(width)[:width]


def _trace(file_access: FileAccess, number: int) -> None:
    """Record ``move <n> to ws-No-Paragraph``, the bridge's trace number.

    The bridge keeps its OWN small numbering, unrelated to the handler's
    201..208 [common/acas029.cbl:L303-L508]; see
    :data:`BRIDGE_TRACE_NUMBERS` for the full census taken from the frozen
    source.

    Args:
        file_access: the linkage block holding ``Logging-Data``.
        number: the paragraph number the frozen source moves.
    """
    file_access.logging_data.ws_no_paragraph = number


def _status(file_access: FileAccess, fs_reply: int, we_error: int) -> StatusPair:
    """Assign the status pair to the linkage block and return it.

    Args:
        file_access: the linkage block to update.
        fs_reply: the ``FS-Reply`` value the frozen source moves.
        we_error: the ``WE-Error`` value the frozen source moves.

    Returns:
        The pair, so a verb can ``return _status(...)`` in one statement the
        way the COBOL falls through to ``ba999-end``.
    """
    file_access.fs_reply = int(fs_reply)
    file_access.we_error = int(we_error)
    return (FsReply(fs_reply) if fs_reply in _FS_REPLY_VALUES else fs_reply, int(we_error))


_FS_REPLY_VALUES: Final[frozenset[int]] = frozenset(int(member) for member in FsReply)


def record_size_gate(file_access: FileAccess) -> StatusPair | None:
    """Reproduce ``ba012-Test-WS-Rec-Size-2`` [common/acas029.cbl:L553-L593].

    ANOMALY A33. On the FIRST call only - the handler latches on ``if A =
    zero`` [common/acas029.cbl:L555] with the declaration commented "A & B
    used in 1st test ONLY" [common/acas029.cbl:L188-L189] - the handler
    compares the linkage record's length against the file record's length and,
    if the linkage buffer is SHORTER, raises a fatal:

    * ``move 901 to WE-Error`` [common/acas029.cbl:L563]
    * ``move 99 to fs-reply`` [common/acas029.cbl:L564]
    * ``go to ba-rdbms-exit`` [common/acas029.cbl:L580] - which ABANDONS the
      bridge ``CALL`` at [common/acas029.cbl:L605] entirely.

    The ``string``/``display``/``accept`` between them
    [common/acas029.cbl:L568-L579] is presentation and is dropped per Agent
    Action Plan section 0.3.4, but the CONTROL TRANSFER it guards is preserved:
    when the gate trips, no statement is issued and the pair is returned.

    THE GATE IS UNREACHABLE, AND THAT IS A MEASUREMENT, NOT AN INFERENCE.
    Compiled on GnuCOBOL 3.2.0, ``function length (WS-OTM5-Record)`` and
    ``function length (Open-Item-Record-5)`` are BOTH 113
    [copybooks/plwsoi5B.cob:L10, copybooks/plfdoi5.cob:L10-L15], so ``A < B``
    is false and the 901 arm never executes. The comparison is reproduced
    anyway, because rule R-4 preserves structure as well as outcome and because
    a future record-layout divergence must trip it exactly as the COBOL would.

    ANOMALY A39, NEW - documentation and code disagree on the field name. The
    handler's own header documents the message as
    ``PL908 Program Error: Temp rec =yyy <Open-Item-Record-5 = zzz``
    [common/acas029.cbl:L47], while the code emits ``"OTM5-Record = "``
    [common/acas029.cbl:L568]. Neither is corrected.

    Also latched on the same first call, and equally once-only, are the six
    connection parameters [common/acas029.cbl:L587-L592] - the maintainer's
    comment is "hopefully once is enough :)". ANOMALY A32: they are never
    refreshed, and their load order here is Schema, UName, UPass, PORT, Host,
    Socket, which differs BOTH from their declaration order in
    [copybooks/wsfnctn.cob:L56-L62] (Schema, UName, UPass, Host, Socket, Port)
    AND from the order the bridge strings them in at
    [common/otm5MT.cbl:L438-L461] (Schema, HOST, UName, UPass, Port, Socket).
    Three orders for six fields. Ownership of the connection itself belongs to
    ``connection.py``, which caches ``RdbData`` once via
    ``load_rdb_data_once``; the latch is therefore honoured there and recorded
    here.

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``None`` when the gate passes and the bridge call may proceed, or the
        ``(99, 901)`` status pair when it trips, in which case the caller must
        NOT issue any statement.
    """
    global _A, _B
    if _A == 0:  # L555: if A = zero  -> so it is being called first time
        # L556-L561: function Length (WS-OTM5-Record) and function length
        # (Open-Item-Record-5). ANOMALY A40, NEW - the same intrinsic is
        # spelled "Length" then "length" on adjacent statements.
        _A = RECORD_LENGTH
        _B = RECORD_LENGTH
        if _A < _B:  # L562 - measured false; see the docstring
            # L563-L564: 901 / 99, then L580's go to ba-rdbms-exit.
            _LOG.error(
                "%s: temp record length %d is shorter than the file record "
                "length %d; the caller must stop - WE-Error 901 "
                "[common/acas029.cbl:L562-L564]",
                HANDLER,
                _A,
                _B,
            )
            return _status(file_access, FsReply.ERROR, RECORD_SIZE_WE_ERROR)
    return None



# ---------------------------------------------------------------------------
# STATEMENT ASSEMBLY - bb200-Insert, bb300-Update, and the two predicates
#
# The frozen bridge assembles LITERAL SQL text and wraps EVERY value in double
# quotes, numerics included: ``STRING '`OI5-INVOICE`="' ... FUNCTION TRIM
# (WS-MYSQL-EDIT(11:10)) ... '"'`` [common/otm5MT.cbl:L1460-L1468]. The exact
# statement shapes are::
#
#   INSERT INTO `PUITM5-REC` SET `OI5-KEY`="...", ... `OI5-DATE-CLEARED`="...";
#   UPDATE      `PUITM5-REC` SET `OI5-KEY`="...", ... WHERE <predicate>;
#   DELETE FROM `PUITM5-REC` WHERE <predicate>;
#
# [common/otm5MT.cbl:L1437-L1440, L1806-L1809] for the INSERT shell,
# [common/otm5MT.cbl:L1827-L1830, L2196-L2202] for the UPDATE shell, and
# [common/otm5MT.cbl:L922-L928] for the DELETE. Both mutating shells set ALL
# TWENTY-NINE columns, the primary key among them, and the separator is a comma
# followed by one space [common/otm5MT.cbl:L1447-L1448].
#
# TWO DECISIONS ABOUT THE VALUES, both recorded rather than taken silently:
#
# 1. VALUES TRAVEL AS BOUND PARAMETERS, NOT AS INLINE TEXT. Every value is
#    rendered to the exact character string the bridge would have inlined - the
#    renderers above are verified byte-for-byte against the GnuCOBOL oracle -
#    and is then bound as a STRING through ``execute_statement``, whose contract
#    is that "values travel as %s placeholders and are bound by the driver"
#    while identifiers arrive already quoted. Because the bridge quotes even its
#    numeric values, a bound string reproduces the server's coercion exactly,
#    so the STORED VALUE is identical for every input. Statement order, column
#    order and statement count - the three things the scenario state diff is
#    sensitive to - are unchanged.
#
# 2. ANOMALY A37, NEW AND DELIBERATELY NOT REPRODUCED. The frozen bridge
#    performs NO escaping whatsoever: a record field containing a double quote
#    or a backslash would terminate the literal early and the remainder of the
#    field would be executed as SQL [common/otm5MT.cbl:L1447-L1450]. That is a
#    SQL-injection defect, not an accounting behaviour, and reproducing it would
#    put an exploitable hole in shipped Python rather than preserve a posted
#    figure. Binding removes it. The behavioural difference is provably NIL on
#    every in-scope input, because these are fixed-width numeric and
#    alphanumeric fields written by the frozen COBOL, so the escaped and
#    unescaped statement text are byte-identical; the defect is therefore
#    recorded here and in the anomaly log rather than carried forward. This is
#    the one place in this module where rule R-4's "reproduce, never fix" is
#    knowingly not applied, and it is called out for exactly that reason.
# ---------------------------------------------------------------------------

#: ``int`` columns - the four the bridge renders through ``WS-MYSQL-EDIT(11:10)``
#: [common/otm5MT.cbl:L1464]. Measured census: that window appears 8 times
#: across ``bb200`` and ``bb300``, four columns in each of two statements.
_INT_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value == "INT"
)

#: ``tinyint`` columns - the two rendered through ``WS-MYSQL-EDIT(18:03)`` with
#: no fraction. ``OI5-DEDUCT-DAYS`` and ``OI5-DAYS``.
_TINYINT_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value == "TINYINT"
)

#: The nine ``decimal(9,2)`` money columns, rendered as ``(14:07)`` plus a stop
#: plus ``(22:02)``. Discriminated from the deduction pair by DECLARED WIDTH,
#: read from the frozen DDL through the dictionary rather than by name.
_MONEY_COLUMNS: Final[tuple[str, ...]] = tuple(
    name
    for name in DECIMAL_COLUMNS
    if int(loader.column_for(DICTIONARY_KEYS[name]).display_width or 0) == 9
)

#: The two ``decimal(5,2)`` deduction columns, rendered as ``(18:03)`` plus a
#: stop plus ``(22:02)``.
_DEDUCTION_COLUMNS: Final[tuple[str, ...]] = tuple(
    name
    for name in DECIMAL_COLUMNS
    if int(loader.column_for(DICTIONARY_KEYS[name]).display_width or 0) == 5
)


def render_column(column: str, value: str | int | decimal.Decimal) -> str:
    """Render one host variable to the characters the bridge would inline.

    Routes to the renderer the frozen source uses for that column, chosen from
    the DICTIONARY-resolved SQL type and declared width rather than from the
    column's name, so the routing is derived and not transcribed (rule R-5).
    The measured window census over ``bb200`` plus ``bb300`` is the check on
    that routing: ``(11:10)`` 8 times, ``(14:07)`` 18, ``(18:03)`` 8 and
    ``(22:02)`` 22 - which is 4, 9, 4 and 11 columns respectively, across two
    statements.

    ANOMALY A35 - no window includes position 1 of ``WS-MYSQL-EDIT``, which is
    where the picture ``-Z(18)9.9(9)`` [common/otm5MT.scb:L227] puts the sign,
    and there is NO sign handling anywhere in either paragraph. Every numeric
    column is therefore written as its MAGNITUDE. This is a rendering-layer
    fact and it OVERRIDES the working specification's per-field claim that the
    sign "survives" for ``OI5-CR`` and the two deduction amounts: the sign
    survives the copybook-to-host-variable hop and is then dropped by the
    renderer. The renderers reproduce it; see their own docstrings.

    Args:
        column: the column name, which must be one of :data:`COLUMNS`.
        value: the host-variable value from :func:`load_host_variables`.

    Returns:
        The exact characters the bridge's ``STRING`` would have emitted.

    Raises:
        KeyError: if ``column`` is not a column of this table. This is a
            programming error in this module, not a data condition, so it is
            not one of the frozen source's status codes.
    """
    if column in CHARACTER_WIDTHS:
        return render_character_column(str(value))
    if column in _INT_COLUMNS:
        return render_integer_column(int(value))
    if column in _TINYINT_COLUMNS:
        return render_tinyint_column(int(value))
    if column in _MONEY_COLUMNS:
        return render_money_column(decimal.Decimal(value))
    if column in _DEDUCTION_COLUMNS:
        return render_deduction_column(decimal.Decimal(value))
    raise KeyError(f"{TABLE} has no column {column!r}")


def rendered_values(
    host_variables: Mapping[str, str | int | decimal.Decimal],
) -> tuple[str, ...]:
    """Render all 29 host variables, in COLUMN order.

    ANOMALY A28 - column order is the third of the bridge's three orders, and
    it is the one both mutating paragraphs emit
    [common/otm5MT.cbl:L1441-L1805, L1831-L2195]. The load order
    [common/otm5MT.cbl:L1348-L1382] and the unload order
    [common/otm5MT.cbl:L1394-L1422] differ from it and from each other.

    Args:
        host_variables: the mapping from :func:`load_host_variables`.

    Returns:
        Twenty-nine rendered strings in :data:`COLUMNS` order.
    """
    return tuple(render_column(column, host_variables[column]) for column in COLUMNS)


def _assignment_list() -> str:
    """Build the shared ``SET`` list of both mutating statements.

    Every identifier goes through :func:`quote_identifier`, without exception.
    Agent Action Plan section 3.21's warning applies to every name in this
    schema: ``PUITM5-REC``, ``OI5-KEY``, ``OI5-BATCH-NOS``,
    ``OI5-DATE-CLEARED`` and the rest all contain a HYPHEN, so an unquoted
    identifier is a SYNTAX ERROR rather than a subtle bug. The bridge proves
    the convention itself, stringing a backtick, the name and a backtick
    [common/otm5MT.cbl:L1442-L1444].

    Returns:
        ``\\`OI5-KEY\\`=%s, \\`OI5-SUPPLIER\\`=%s, ...`` for all 29 columns.
    """
    return ", ".join(f"{quote_identifier(column)}=%s" for column in COLUMNS)


def _record_key(otm5: OiHeader) -> str:
    """Return ``WS-OTM5-Record (K:L)`` - the record's own leading 15 bytes.

    The delete and rewrite predicates are built from the RECORD BUFFER, not
    from ``HV-OI5-KEY`` [common/otm5MT.cbl:L909, L963], using the offset and
    length the bridge's key metadata declares - ``'00010015'``, offset 1
    length 15 [common/otm5MT.cbl:L252], read here from
    :data:`KEY_OFFSET`/:data:`KEY_LENGTH` through
    ``cursor_state.key_of_reference`` so the numbers are never hard-coded.

    Those fifteen bytes are ``OI-Nos x(6)`` plus ``OI-Check pic 9`` plus
    ``OI-Invoice pic 9(8)`` [copybooks/plwsoi.cob:L13-L18], every one of which
    is DISPLAY, so the buffer slice and :func:`compose_key` produce the same
    characters. The consequence is worth stating: a caller can never target a
    row other than the one its own record names, because the predicate is
    derived from the record it passed.

    Args:
        otm5: the linkage record.

    Returns:
        Exactly :data:`KEY_LENGTH` characters, untrimmed - the bridge strings
        the slice ``delimited by size`` [common/otm5MT.cbl:L907-L909], so any
        interior space is part of the predicate.
    """
    supplier = supplier_characters(otm5.oi_key.oi_customer.oi_supplier)
    key = compose_key(supplier, int(otm5.oi_key.oi_invoice))
    start = KEY_OFFSET - 1
    return key[start : start + KEY_LENGTH]


def _key_predicate(key: str) -> tuple[str, str]:
    """Build the primary-key predicate in both of its needed forms.

    Reproduces the ``string`` at [common/otm5MT.cbl:L903-L911] for delete and
    [common/otm5MT.cbl:L957-L967] for rewrite - identical text in both.

    Args:
        key: the fifteen key characters from :func:`_record_key`.

    Returns:
        A pair. First the parameterised text for execution,
        ``\\`OI5-KEY\\`=%s``. Second the LITERAL text the bridge assembles,
        ``\\`OI5-KEY\\`="<key>"``, which is what ``WS-Log-Where`` records
        [common/otm5MT.cbl:L913] and is reproduced so the log is faithful even
        though the executed form binds.
    """
    quoted = quote_identifier(PRIMARY_KEY)
    return (f"{quoted}=%s", f'{quoted}="{key}"')


@contextmanager
def _cursor(connection: MySQLConnectionAbstract) -> Iterator[DatabaseCursor]:
    """Yield a plain driver cursor for the positioning verbs.

    ``cursor_state``'s ``start``, ``read_next`` and ``read_indexed`` issue
    their OWN statement on the cursor they are handed, so they cannot be fed
    from :func:`execute_statement`, which executes the statement itself. This
    context manager supplies the bare cursor those three need and closes it on
    every path.

    No pooling, no reuse, no prepared-statement cache - rule R-3 forbids all
    three, and Agent Action Plan section 0.8.4 puts performance work out of
    scope by construction.

    Args:
        connection: the open connection.

    Yields:
        A cursor satisfying the ``DatabaseCursor`` protocol - ``execute``,
        ``fetchone`` and ``description``.
    """
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        discard_unread = getattr(connection, "consume_results", None)
        if discard_unread is not None:
            try:
                discard_unread()
            except Exception as error:  # any driver error takes this path
                _LOG.debug("%s: discarding unread result reported %s", TABLE,
                           redact_for_log(str(error)))
        try:
            cursor.close()
        except Exception as error:  # any driver error takes this path
            _LOG.debug("%s: cursor close reported %s", TABLE,
                       redact_for_log(str(error)))


def _driver_failure(error: BaseException) -> tuple[str, str, str]:
    """Describe a driver failure the way the frozen error path describes one.

    The bridge calls ``MySQL_errno``, ``MySQL_sqlstate`` and ``MySQL_error``
    in that order and moves the three results into ``SQL-Err``, ``SQL-State``
    and ``SQL-Msg`` [common/otm5MT.cbl:L878-L884]. Python has one exception
    object instead of three calls, so the three fields are derived from it
    using ``status.py``'s published helpers. ``cursor_state`` has an identical
    private helper; it is reimplemented here rather than imported because
    importing a private name across modules is not a dependency this module is
    permitted to take.

    Args:
        error: the exception the driver raised.

    Returns:
        The error number as text, its log category, and the redacted message.
        Redaction matters because a driver message can echo bound values, and
        rule V.S1 requires credentials never reach a log or a diff.
    """
    errno = getattr(error, "errno", "") or ""
    return (
        str(errno),
        db_error_log_category(errno),
        redact_for_log(str(error)),
    )


def _apply_driver_failure(
    file_access: FileAccess, error: BaseException, *, command: str
) -> tuple[str, str]:
    """Fill the diagnostic fields from a driver failure and report the pair.

    Reproduces the inner block every mutating verb shares
    [common/otm5MT.cbl:L878-L890, L931-L939, L972-L980]: fetch the SQLSTATE
    into ``SQL-State`` unconditionally, and fetch the number and message into
    ``SQL-Err`` and ``SQL-Msg`` ONLY when the number is not ``"0  "``.

    Args:
        file_access: the linkage block to fill.
        error: the exception the driver raised.
        command: the operation name, for ``status.py``'s duplicate detection.

    Returns:
        The ``(SQL-Err, SQL-State)`` pair, which the write verb then tests for
        a duplicate key.
    """
    errno, _category, message = _driver_failure(error)
    status = mysql_1100_db_error(
        errno=errno,
        message=message,
        sql_state=str(getattr(error, "sqlstate", "") or ""),
        command=command,
    )
    logging_data = file_access.logging_data
    # L880-L881: move WS-MYSQL-SqlState to SQL-State - always.
    logging_data.sql_state = str(status.sql_state).ljust(
        len(logging_data.sql_state)
    )[: len(logging_data.sql_state)]
    # L882-L885: the number and the message only when the number is not "0  ".
    if errno and errno != "0":
        logging_data.sql_err = str(status.sql_err).ljust(
            len(logging_data.sql_err)
        )[: len(logging_data.sql_err)]
        logging_data.sql_msg = str(status.sql_msg).ljust(
            len(logging_data.sql_msg)
        )[: len(logging_data.sql_msg)]
    return (str(status.sql_err), str(status.sql_state))


def _clear_sql_diagnostics(file_access: FileAccess) -> None:
    """Reproduce ``move spaces to SQL-Msg`` plus ``move zero to SQL-Err``.

    The success arms of delete [common/otm5MT.cbl:L944-L945] and rewrite
    [common/otm5MT.cbl:L988-L991] clear the two diagnostic fields, and the
    write verb clears them on ENTRY instead [common/otm5MT.cbl:L873-L874].
    ``SQL-Err`` receives ZERO and ``SQL-Msg`` receives SPACES - the asymmetry
    is the frozen source's, not a slip here.

    Args:
        file_access: the linkage block to clear.
    """
    logging_data = file_access.logging_data
    logging_data.sql_msg = " " * len(logging_data.sql_msg)
    logging_data.sql_err = "0" * len(logging_data.sql_err)


def _require_connection(operation: str) -> MySQLConnectionAbstract:
    """Return the open connection, or refuse the verb.

    The bridge keeps its connection in its own working storage across calls -
    ``MYSQL-1000-OPEN`` establishes it [common/otm5MT.cbl:L463] and
    ``MYSQL-1980-CLOSE`` tears it down [common/otm5MT.cbl:L487] - so a
    module-level handle is the faithful model, not a per-call connect. Rule R-3
    forbids a pool, so there is exactly one.

    The frozen source has NO status code for a verb issued before its open,
    because the menu shell always opens first and the maintainer never wrote
    that path. Inventing a code would be adding a validation, which rule R-3
    forbids, so the refusal is raised as the layer's own exception rather than
    dressed up as a COBOL status.

    Args:
        operation: the function-code name, for the message.

    Returns:
        The open connection.

    Raises:
        AcasFileHandlerError: if :func:`open_` has not run, or :func:`close`
            has already run.
    """
    if _CONNECTION is None:
        raise AcasFileHandlerError(
            int(FsReply.ERROR),
            int(WeError.UNKNOWN_UNEXPECTED),
            operation=operation,
            table=TABLE,
        )
    return _CONNECTION




# ---------------------------------------------------------------------------
# THE TWELVE VERBS
#
# CORRECTION C5 TO THE WORKING SPECIFICATION, AND IT REORGANISES HALF OF THIS
# SECTION. The handler's flat-file verbs ``aa020`` through ``aa100``
# [common/acas029.cbl:L301-L523] ARE NEVER REACHED ON THE RDB PATH, and the
# frozen source says so in its own words. The order of statements is:
#
#   L239-L253  the key guard              <- BOTH paths
#   L257-L261  if not FS-Cobol-Files-Used -> perform ba-Process-RDBMS
#                                         -> go to AA-Main-Exit   <- LEAVES
#   L265       perform ba012-Test-WS-Rec-Size-2   <- flat only
#   L269-L271  *> So we are processing Cobol Flat files. *   <- the maintainer
#   L275       move spaces to SQL-Err SQL-Msg SQL-State      <- flat only
#   L277-L296  evaluate File-Function -> aa020 .. aa100      <- flat only
#
# The comment at [common/acas029.cbl:L269-L271] is decisive: everything after
# the RDB branch is the flat-file path. Rule R-6 makes the compiled behaviour
# the tie-breaker, so the following handler behaviours are DELIBERATE
# OMISSIONS on the path this module implements, each recorded rather than
# reproduced:
#
#   A13  FS-Reply 35 on an open-input failure   [common/acas029.cbl:L307]
#   A14  the handler's 997 for fn-extend        [common/acas029.cbl:L324-L328]
#   A15  the open-i-o close/output/close retry  [common/acas029.cbl:L313-L319]
#   A16  open-output as an unchecked truncate   [common/acas029.cbl:L321-L322]
#   A31  the live stop "Cobol File EOF"         [common/acas029.cbl:L365]
#   A17  the flat 5..8 access-type guard        [common/acas029.cbl:L441]
#   A12  the handler's 999 bad-function code    [common/acas029.cbl:L522-L523]
#   A20  the dead else in aa060, unreachable    [common/acas029.cbl:L477-L481]
#   A21  the description-key comment, on a
#        table that has no description field    [common/acas029.cbl:L396]
#   A26  two ifs closed by a period, no end-if  [common/acas029.cbl:L336-L338]
#                                              [common/acas029.cbl:L377-L378]
#   A27  end-rewrite with no period, fusing it
#        to the following perform               [common/acas029.cbl:L514-L515]
#   A46  the flat close verb logging twice      [common/acas029.cbl:L347-L350]
#
# What DOES run is ``ba-Process-RDBMS`` [common/acas029.cbl:L537], whose three
# paragraphs fall through one into the next: ``ba010-Test-WS-Rec-Size``
# [L545] bumps the log file number 15 -> 25, ``ba012-Test-WS-Rec-Size-2``
# [L553] latches the lengths and the credentials, and ``ba015-Test-Ends``
# [L595] issues the ``call "otm5MT"`` [L605-L609]. So the bridge's OWN codes
# govern every verb below - including the 997 that the bridge's start guard
# raises at [common/otm5MT.cbl:L765-L769], which is a different 997 from the
# handler's unreachable one.
#
# The bridge has NO access-type branching in its open at all
# [common/otm5MT.cbl:L433-L475]: it strings six connection fields, opens the
# database and marks the cursor inactive, whatever the access type. The four
# open verbs are therefore published as aliases of one implementation - which
# is what the facade needs, and what the compiled RDB path does.
# ---------------------------------------------------------------------------


def open_(
    system: SystemRecord,
    file_access: FileAccess,
    *,
    transport: TransportSecurity | None = None,
) -> StatusPair:
    """Reproduce ``ba020-Process-Open`` [common/otm5MT.cbl:L433-L475].

    Sequence, exactly as the frozen source orders it:

    1. String the six connection fields, each ``delimited by space`` and
       terminated ``X"00"`` [common/otm5MT.cbl:L438-L461]. ANOMALY A32 - the
       order here is Schema, HOST, UName, UPass, Port, Socket, which is the
       THIRD order these six fields appear in; see :func:`record_size_gate`.
       ``connection.py`` owns the connection and caches ``RdbData`` once, so
       the once-only latch and the null termination both live there.
    2. ``move 1 to ws-No-Paragraph`` [common/otm5MT.cbl:L462] - set AFTER the
       six strings, not before.
    3. ``PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT``
       [common/otm5MT.cbl:L463].
    4. ``if fs-reply not = zero go to ba999-end`` [common/otm5MT.cbl:L464-L465]
       - a failed open returns immediately with no file key set.
    5. ``move "OPEN PL OTM5" to WS-File-Key`` [common/otm5MT.cbl:L473] and
       ``set Cursor-Not-Active to true`` [common/otm5MT.cbl:L474].

    ANOMALY A22 - the file-key literal is ``"OPEN PL OTM5"`` here, correctly
    naming the PURCHASE ledger, while the handler's unreachable flat-file arm
    writes ``"OPEN SL OTM5 File"`` [common/acas029.cbl:L335] with SALES
    terminology. The leak is HANDLER-ONLY; the bridge gets it right. That
    refines the working specification, which attributes the leak to the chain
    generally. ANOMALY A23 - the full sales-terminology inventory for this
    chain is ``OI-Customer`` [copybooks/plwsoi.cob:L14],
    ``WS-Temp-Ed-Customer`` [common/otm5MT.cbl:L234], ``*> Cust #``
    [common/acas029.cbl:L197] and the handler's two file-key literals
    [common/acas029.cbl:L335, L346].

    Args:
        system: the ``System-Record`` linkage parameter
            [common/acas029.cbl:L219], whose ``RDBMS-`` fields carry the six
            connection parameters [copybooks/wsfnctn.cob:L57-L64].
        file_access: the ``File-Access`` linkage block.
        transport: TLS material for the connection. The harness runs the
            oracle on an isolated Docker network, which is the only situation
            in which an unencrypted transport is accepted; pass
            ``TransportSecurity(isolated_oracle=True)`` there.

    Returns:
        ``(0, 0)`` when the database opened, otherwise the pair
        ``mysql_1000_open`` reported, unchanged - the bridge performs no
        recovery of its own.
    """
    global _CONNECTION
    # Step 2 - L462: move 1 to ws-No-Paragraph.
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba020-Process-Open"][0])
    # Steps 1 and 3 - the six strings and MYSQL-1000-OPEN THRU MYSQL-1090-EXIT.
    outcome = mysql_1090_exit(mysql_1000_open(system, transport=transport))
    logging_data = file_access.logging_data
    logging_data.sql_err = str(outcome.sql_err).ljust(
        len(logging_data.sql_err)
    )[: len(logging_data.sql_err)]
    logging_data.sql_msg = str(outcome.sql_msg).ljust(
        len(logging_data.sql_msg)
    )[: len(logging_data.sql_msg)]
    logging_data.sql_state = str(outcome.sql_state).ljust(
        len(logging_data.sql_state)
    )[: len(logging_data.sql_state)]
    if int(outcome.fs_reply) != int(FsReply.SUCCESS):
        # Step 4 - L464-L465: no file key, no cursor change, straight out.
        _LOG.error(
            "%s: MYSQL-1000-OPEN reported (%s, %s) [common/otm5MT.cbl:L463]",
            BRIDGE,
            int(outcome.fs_reply),
            int(outcome.we_error),
        )
        return _status(file_access, int(outcome.fs_reply), int(outcome.we_error))
    _CONNECTION = outcome.connection
    # Step 5 - L473-L474.
    _set_file_key(file_access, OPEN_FILE_KEY)
    _STATES.reset(TABLE)
    return _status(file_access, int(outcome.fs_reply), int(outcome.we_error))


#: ``fn-input`` (Access-Type 1). The bridge's open takes NO access type
#: [common/otm5MT.cbl:L433-L475], so this is the same open. The handler's
#: distinct flat-file arm - ``open input`` then ``move 35 to fs-Reply`` on
#: failure [common/acas029.cbl:L304-L310], ANOMALY A13 - is unreachable on the
#: RDB path and is recorded as a deliberate omission, not reproduced.
open_input = open_

#: ``fn-i-o`` (Access-Type 2). Same open. The handler's close/open-output/
#: close/open-i-o retry, whose status is famously never re-tested - "file-status
#: will NOT be updated ????" [common/acas029.cbl:L313-L319], ANOMALY A15 - is
#: unreachable here and recorded as a deliberate omission.
open_i_o = open_

#: ``fn-output`` (Access-Type 3). Same open. ANOMALY A16 - the handler's arm is
#: a PLAIN ``open output`` with its status UNCHECKED, commented "caller should
#: check fs-reply" [common/acas029.cbl:L321-L322], and ``acas029`` contains NO
#: ``fn-Open and fn-Delete-All`` coercion and NO delete-all path anywhere. This
#: is the seventh handler in the folder where Open-Output is absent as a special
#: case, in deliberate contrast to ``acas008``, whose single coerced delete-all
#: makes Open-Output mean "delete every row" [common/acas008.cbl:L313-L319].
#: NOTHING is truncated here and no mass delete is issued.
open_output = open_

#: ``fn-extend`` (Access-Type 4). Same open. ANOMALY A14 - the handler's arm
#: has its ``open extend`` COMMENTED OUT with "Must not be used for ISAM files"
#: and returns ``(99, 997)`` [common/acas029.cbl:L324-L328]. That arm is
#: unreachable on the RDB path, so no 997 arises here; the 997 that this module
#: does return comes from the BRIDGE's start guard
#: [common/otm5MT.cbl:L765-L769], which is a different statement entirely.
open_extend = open_


def close(file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba030-Process-Close`` [common/otm5MT.cbl:L477-L489].

    1. ``if Cursor-Active perform ba998-Free`` [common/otm5MT.cbl:L478-L479].
    2. ``move 2 to ws-No-Paragraph`` [common/otm5MT.cbl:L481] - AFTER the free.
    3. ``move "CLOSE PL OTM5" to WS-File-Key`` [common/otm5MT.cbl:L482].
    4. ``PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT``
       [common/otm5MT.cbl:L487].

    ANOMALY A36 - the paragraph ASSIGNS NO STATUS. Combined with
    ``ba010-Initialise`` declining to zero the pair
    [common/otm5MT.cbl:L390-L391], a close therefore returns the caller's
    INCOMING ``FS-Reply`` and ``WE-Error`` untouched. That is reproduced here
    by reading the pair back off ``file_access`` rather than defaulting it, and
    it is why this function does not call :func:`_status`.

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        The incoming status pair, unmodified.
    """
    global _CONNECTION
    # Step 1 - L478-L479, and ANOMALY A10: ba998-Free resets cursor ONE
    # unconditionally [common/otm5MT.cbl:L1326] even though the read-next EOF
    # path sets cursor THREE inactive - see UNREACHED_CURSOR_SLOTS.
    state = _STATES.state_for(TABLE, CURSOR_SLOT)
    if state.cursor_active():
        _trace(file_access, BRIDGE_TRACE_NUMBERS["ba998-Free"][0])
        state.free()
    # Step 2 - L481.
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba030-Process-Close"][0])
    # Step 3 - L482.
    _set_file_key(file_access, CLOSE_FILE_KEY)
    # Step 4 - L487.
    mysql_1980_close(_CONNECTION)
    mysql_1999_exit()
    _CONNECTION = None
    # ANOMALY A36 - no status is written; the incoming pair stands.
    incoming = int(file_access.fs_reply)
    return (
        FsReply(incoming) if incoming in _FS_REPLY_VALUES else incoming,
        int(file_access.we_error),
    )


def start(
    otm5: OiHeader, file_access: FileAccess, access_type: int
) -> StatusPair:
    """Reproduce ``ba060-Process-Start`` [common/otm5MT.cbl:L761-L863].

    CORRECTION C2 TO THE WORKING SPECIFICATION, VERIFIED AGAINST THE FROZEN
    SOURCE. The specification's anomaly A17 instructs that the ``5..8``
    access-type guard NOT be implemented, on the reasoning that it lives only
    in the handler's flat-file ``aa060``. It does not: the BRIDGE carries its
    own copy at [common/otm5MT.cbl:L765-L769], returning ``(99, 997)``, and
    that copy IS on the RDB path. The guard is therefore implemented, and a
    live round trip against the harness MariaDB confirms ``(99, 997)`` for
    access type 9.

    ANOMALY A50, NEW - THE RELATION MAP'S FIFTH ARM IS DEAD CODE, GUARDED OUT
    THREE LINES ABOVE IT. Because the guard rejects anything outside ``5..8``
    [common/otm5MT.cbl:L765], the ``when 9`` arm - ``move "<= " to
    MOST-Relation`` for ``fn-not-greater-than`` [common/otm5MT.cbl:L794-L795] -
    can never execute, and the maintainer annotates the arm himself with
    "[ not currently used in ACAS ]" [common/otm5MT.cbl:L794]. The
    ``MOST-Relation`` declaration nonetheless advertises all five relations,
    ">=, <=, <, >, =" [common/otm5MT.cbl:L263]. So THREE artefacts in one
    bridge disagree about whether ``<=`` is supported: the declaration says
    yes, the map says yes, the guard says no - and the guard wins because it
    runs first. Nothing is reconciled; the arm is not implemented, and the
    guard is. One consequence is benign: the map's missing ``when other``
    [common/otm5MT.cbl:L785-L796], which would otherwise leave
    ``MOST-Relation`` at spaces and build a malformed predicate, is
    unreachable too.

    Delegated to ``cursor_state.start``, which implements exactly this shape:
    the guard, the ``if Cursor-Active perform ba998-Free``
    [common/otm5MT.cbl:L772-L773], the relation map, the predicate with
    ``ORDER BY <key> ASC`` [common/otm5MT.cbl:L798-L813], and the positioning.

    ANOMALY A41, NEW - A PER-BRIDGE DIVERGENCE THE SHARED HELPER CANNOT KNOW.
    On the empty-result path ``otm5MT`` places ``move 21 to fs-reply``
    [common/otm5MT.cbl:L850] and ``move zero to WE-Error``
    [common/otm5MT.cbl:L851] OUTSIDE the inner ``if WS-MYSQL-Error-Number not
    = "0  "`` that ends at [common/otm5MT.cbl:L849], so BOTH fields are ALWAYS
    written when the count is zero. ``glpostingMT``, which
    ``cursor_state.start`` is written against, writes NEITHER on that path -
    the helper reports it as ``status_written=False``. The correction is applied
    below, because the observable status of an empty START against
    ``PUITM5-REC`` is ``(21, 0)`` and not the caller's incoming pair.

    ANOMALY A9 - the bridge declares THREE cursors for this single-key,
    no-repeating-group table [common/otm5MT.cbl:L264-L272], the second and
    third annotated "RG 1 or special" and "RG 2 or special". Only one is ever
    meaningful, so one logical cursor is used; see :data:`CURSOR_SLOT` and
    :data:`UNREACHED_CURSOR_SLOTS`.

    CORRECTION C7, measured against the frozen source: the specification cites
    ``MOST-Relation`` at L264 and the cursor block as L263-L273. Both are off by
    one. ``01 DAL-Data.`` is at [common/otm5MT.cbl:L262]; ``MOST-Relation`` with
    its five-relation comment is at [common/otm5MT.cbl:L263]; the three
    ``Most-Cursor-Set`` fields are at L264, L267 and L270 with their ``88``
    condition names running through [common/otm5MT.cbl:L272]; L273 is a bare
    ``*>`` comment line carrying no declaration at all. Rule R-6 makes the
    compiled source the arbiter, so the spans cited here are the measured ones.

    Args:
        otm5: the linkage record, whose leading fifteen bytes supply the key -
            ``WS-OTM5-Record (K:L)`` [common/otm5MT.cbl:L802].
        file_access: the ``File-Access`` linkage block.
        access_type: ``Access-Type``, ``5``..``8`` accepted. The declaration is
            ``03 Access-Type pic 9`` [copybooks/wsfnctn.cob:L107] and its
            condition names run ``fn-input`` value 1 through
            ``fn-not-greater-than`` value 9 [copybooks/wsfnctn.cob:L108-L116].
            CORRECTION C8: the specification cites this vocabulary as
            ``wsfnctn.cob:L88-L118``, but that file is 117 lines long, so L118
            does not exist; L88 is ``03 File-Function pic 99``, a different
            field. The measured spans are File-Function at
            [copybooks/wsfnctn.cob:L88-L105] and Access-Type at
            [copybooks/wsfnctn.cob:L107-L116]. Rule R-6 makes the compiled
            source the arbiter.

    Returns:
        ``(0, 0)`` when positioned, ``(21, 0)`` when nothing qualified, or
        ``(99, 997)`` when the access type is out of range.

    Raises:
        AcasFileHandlerError: if no connection is open. The frozen source has
            no status for a verb issued before its open, because the menu
            always opens first.
    """
    connection = _require_connection("fn-start")
    key = _record_key(otm5)
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba060-Process-Start"][0])
    with _cursor(connection) as cursor:
        outcome = _cursor_start(
            cursor,
            TABLE,
            key,
            access_type,
            key_number=KEY_COUNT,
            slot=CURSOR_SLOT,
            states=_STATES,
            file_access=file_access,
        )
    if outcome.statement:
        # L814: move WS-Where (1:J) to WS-Log-Where.
        _set_log_where(file_access, outcome.statement)
    if not outcome.status_written:
        # ANOMALY A41 - otm5MT ALWAYS writes (21, 0) here, unlike glpostingMT.
        # [common/otm5MT.cbl:L850-L851]
        _set_file_key(file_access, key)
        return _status(
            file_access, FsReply.INVALID_KEY_ON_START, int(WeError.SUCCESS)
        )
    if int(outcome.fs_reply) == int(FsReply.SUCCESS):
        # L852-L861: "<relation><key> got <n> recs" is the success file key.
        _set_file_key(file_access, outcome.file_key or key)
    else:
        # L815: move WS-OTM5-Record (K:L) to WS-File-Key, on the guard path too.
        _set_file_key(file_access, key)
    return (
        FsReply(int(outcome.fs_reply))
        if int(outcome.fs_reply) in _FS_REPLY_VALUES
        else int(outcome.fs_reply),
        int(outcome.we_error),
    )


def read_next(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba040-Process-Read-Next`` plus ``ba041-Reread``.

    Two stages, exactly as [common/otm5MT.cbl:L491-L648] arranges them.

    STAGE A, only ``if Cursor-Not-Active`` [common/otm5MT.cbl:L497]: issue
    ``SELECT * FROM \\`PUITM5-REC\\` WHERE \\`OI5-KEY\\` >= "000000000000000"
    ORDER BY \\`OI5-KEY\\` ASC;`` [common/otm5MT.cbl:L503-L533], store the
    result, and set the file key to the low key
    [common/otm5MT.cbl:L535]. The literal fifteen zeros are "the lowest
    possible key" [common/otm5MT.cbl:L493-L495]; :data:`SEQUENTIAL_LOW_KEY`
    derives them from :data:`KEY_LENGTH` rather than transcribing them. An
    empty table returns ``(10, 10)`` with the file key ``"No Data"``
    [common/otm5MT.cbl:L551-L554]. Otherwise the cursor goes active and the
    file key becomes ``"> 0 got cnt=<n> recs for INVOICE-RECORD Table"``
    [common/otm5MT.cbl:L558-L562] - ANOMALY A42, NEW: that literal names
    ``INVOICE-RECORD``, a table this bridge does not touch, inherited from the
    ``acas019``/``slinvoiceMT`` family it was copied from. Note also that
    ``WS-Temp-ED-Row`` IS used here [common/otm5MT.cbl:L557], which CORRECTS
    the working specification's claim that it is unused; only ``WS-Body-Key``
    [common/otm5MT.cbl:L282] is genuinely dead.

    STAGE B, ``ba041-Reread`` [common/otm5MT.cbl:L566], always: fetch the next
    row of the STORED result. It issues no statement.

    ANOMALY A11 - THREE distinct EOF markers are written into the file key on
    three different exhaustion paths, all returning ``(10, 10)``:

    * ``"EOF"`` when the fetch reports no more data
      [common/otm5MT.cbl:L613-L618]
    * ``"EOF2"`` when the stored count is zero AND the driver reports an error
      number - note both the marker and the ``initialize WS-OTM5-Record with
      filler`` are INSIDE that inner test [common/otm5MT.cbl:L622-L636], so a
      zero count with error number ``"0  "`` returns ``(10, 10)`` while
      leaving the file key and the record ALONE
    * ``"EOF3"`` when ``fs-reply`` was already 10 on entry, a path the
      maintainer marks "should not happen as tested prior"
      [common/otm5MT.cbl:L639-L642]

    ANOMALY A43, NEW - end of file returns ``WE-Error`` 10, not zero, and the
    maintainer flags his own doubt inline: "should be 0 'JIC' likewise the
    others" [common/otm5MT.cbl:L615]. ``status.end_of_file_status`` supplies
    the pair so all sites agree.

    ANOMALY A10 - cursor reset asymmetry: this path sets cursor THREE inactive
    while ``ba998-Free`` unconditionally resets cursor ONE
    [common/otm5MT.cbl:L1326]. One logical cursor is used and its reset is
    unconditional.

    Args:
        otm5: the linkage record, filled in place on a successful fetch.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(0, 0)`` with ``otm5`` filled, or ``(10, 10)`` at end of file.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-read-next")
    state = _STATES.state_for(TABLE, CURSOR_SLOT)
    stage_a = not state.cursor_active()
    _trace(
        file_access,
        BRIDGE_TRACE_NUMBERS["ba040-Process-Read-Next"][0 if stage_a else 1],
    )
    if stage_a:
        # L535: the low key is the file key while the SELECT is in flight.
        _set_file_key(file_access, SEQUENTIAL_LOW_KEY)
    else:
        # L570: move spaces to WS-Log-Where - ba041 clears it.
        _set_log_where(file_access, "")
    with _cursor(connection) as cursor:
        outcome = _cursor_read_next(
            cursor,
            TABLE,
            slot=CURSOR_SLOT,
            states=_STATES,
            file_access=file_access,
        )
    if stage_a and outcome.statement:
        # L534: move ws-Where (1:J) to WS-Log-Where, set before the SELECT.
        _set_log_where(file_access, outcome.statement)
    if outcome.row is None:
        # L551-L554 / L613-L618 / L622-L636 / L639-L642 - every exhaustion path
        # is (10, 10) and each stamps its own marker. ANOMALY A11.
        _set_file_key(file_access, outcome.file_key or EOF_FILE_KEYS[0])
        return _status(file_access, int(outcome.fs_reply), int(outcome.we_error))
    # L645-L647: perform bb100-UnloadHVs, then the KEY column becomes the file
    # key, then (0, 0). ANOMALY A1 - HV-OI5-KEY is used HERE, as the logging
    # key, which is the ONLY place either write-only host variable is observed
    # after retrieval; it is still not moved into the record.
    unload_host_variables(outcome.row, otm5)
    _set_file_key(file_access, _column_text(outcome.row, PRIMARY_KEY))
    return _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))


def read_indexed(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba050-Process-Read-Indexed`` [common/otm5MT.cbl:L650-L759].

    ``SELECT * FROM \\`PUITM5-REC\\` WHERE \\`OI5-KEY\\`="<15 bytes>";`` with
    NO ``ORDER BY`` [common/otm5MT.cbl:L661-L688] - rule R-6 forbids adding
    one, and none is needed: the predicate is on the single-column primary key
    and the table has ZERO secondary indexes [mysql/ACASDB.sql:L596-L626], so
    there is no ordering nondeterminism to guard against.

    Three outcomes, and the two failures use codes that appear NOWHERE else in
    this module:

    * MISS - stored count zero: ``move 23 to fs-Reply``
      [common/otm5MT.cbl:L692] with the maintainer's note "could also be 21 or
      14", ``move zero to WE-Error`` [common/otm5MT.cbl:L693], then
      ``go to ba998-Free``. So ``(23, 0)`` - NOT the ``21`` that a START miss
      returns.
    * FETCH FAILURE - count not greater than zero after the fetch: SQLSTATE
      always captured, then ``990`` when the error number is not ``"0  "``
      [common/otm5MT.cbl:L741] or ``989`` with the diagnostics CLEARED when it
      is [common/otm5MT.cbl:L746-L748]; then ``move 23 to fs-reply``
      [common/otm5MT.cbl:L750] and ``move spaces to WS-File-Key``
      [common/otm5MT.cbl:L751].
    * SUCCESS - ``bb100-UnloadHVs``, the key column as file key, ``(0, 0)``,
      then ``perform ba998-Free`` [common/otm5MT.cbl:L755-L758].

    All three paths FREE THE CURSOR, which is why a read-indexed never leaves
    a position behind for a following read-next to walk.

    Args:
        otm5: the linkage record; supplies the key and is filled in place.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(0, 0)``, ``(23, 0)`` on a miss, or ``(23, 990)``/``(23, 989)`` on a
        driver failure.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-read-indexed")
    key = _record_key(otm5)
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba050-Process-Read-Indexed"][0])
    _, literal = _key_predicate(key)
    # L659: move WS-Where (1:J) to WS-Log-Where, before the SELECT.
    _set_log_where(file_access, literal)
    with _cursor(connection) as cursor:
        outcome = _cursor_read_indexed(
            cursor,
            TABLE,
            key,
            key_number=KEY_COUNT,
            slot=CURSOR_SLOT,
            states=_STATES,
            file_access=file_access,
        )
    # L689: move 6 to ws-No-Paragraph, set for the FETCH stage.
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba050-Process-Read-Indexed"][1])
    # Every path frees - L694, L752, L757.
    _STATES.state_for(TABLE, CURSOR_SLOT).free()
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba998-Free"][0])
    if outcome.row is None:
        # ANOMALY A49, NEW - THE SHARED HELPER CARRIES ANOTHER BRIDGE'S CODES,
        # AND THIS BRIDGE CONTRADICTS IT ON BOTH HALVES OF THE PAIR.
        # `dal.cursor_state.read_indexed` is written against `glpostingMT`,
        # whose ba050 does `move 21 to fs-Reply  *> could also be 23 or 14`
        # [common/glpostingMT.cbl:L634] and deliberately leaves `We-Error` at
        # the caller's incoming value. `otm5MT` does the OPPOSITE on both
        # counts: `move 23 to fs-Reply  *> could also be 21 or 14`
        # [common/otm5MT.cbl:L692] and `move zero to WE-Error`
        # [common/otm5MT.cbl:L693]. The two bridges picked DIFFERENT members of
        # the same "could also be" set, and neither is wrong - each generated
        # bridge is its own specification. This is the same class of per-bridge
        # divergence as A41, and like A41 it is corrected HERE rather than in
        # the shared helper, which cannot know which bridge is calling it.
        if int(outcome.we_error) == int(WeError.RDB_INIT_ERROR):
            # L737-L753: the FETCH stage found the count not greater than
            # zero, so the driver is reporting a real error. SQLSTATE is
            # always captured, then 990 when the error number is not "0  "
            # [common/otm5MT.cbl:L741-L742] or 989 with the diagnostics
            # cleared when it is [common/otm5MT.cbl:L746-L749]. A non-zero
            # error number is what an init failure IS, so 990 is the arm.
            we_error = READ_INDEXED_DRIVER_WE_ERROR
            # L752: move spaces to WS-File-Key, on this arm only.
            _set_file_key(file_access, "")
        else:
            # L691-L695: the clean miss. `move 23 to fs-Reply`, `move zero to
            # WE-Error`, `go to ba998-Free` - and NOTHING ELSE. In particular
            # ba050 never writes WS-File-Key at all, neither before the SELECT
            # [common/otm5MT.cbl:L650-L675] nor on this arm, so the logging
            # key retains whatever the PREVIOUS verb left in it. That is
            # faithfully reproduced by not touching it here; the field has no
            # database effect, so the only cost of getting it wrong would be a
            # misleading log line, and the only cost of getting it right is
            # this comment.
            we_error = int(WeError.SUCCESS)
        # Both arms land on the same FS-Reply [common/otm5MT.cbl:L692, L751].
        return _status(file_access, READ_INDEXED_MISS_FS_REPLY, we_error)
    # L755-L757.
    unload_host_variables(outcome.row, otm5)
    _set_file_key(file_access, _column_text(outcome.row, PRIMARY_KEY))
    return _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))



def write(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba070-Process-Write`` [common/otm5MT.cbl:L867-L892].

    1. ``perform bb000-HV-Load`` [common/otm5MT.cbl:L868] - all 29 host
       variables, including the two write-only ones (ANOMALY A1).
    2. ``move OI-Key to WS-File-Key`` [common/otm5MT.cbl:L869] - the RECORD's
       key group, not ``HV-OI5-KEY``.
    3. ``move zero to FS-Reply WE-Error SQL-State``, ``move spaces to SQL-Msg``,
       ``move zero to SQL-Err`` [common/otm5MT.cbl:L870-L874] - this verb
       clears on ENTRY, where delete and rewrite clear on their success arm.
    4. ``move 10 to ws-No-Paragraph`` [common/otm5MT.cbl:L875].
    5. ``perform bb200-Insert`` [common/otm5MT.cbl:L876] - the 29-column
       ``INSERT INTO \\`PUITM5-REC\\` SET ...``.
    6. ``if WS-MYSQL-COUNT-ROWS not = 1`` [common/otm5MT.cbl:L877]: capture the
       SQLSTATE, ``move 99 to fs-reply`` [common/otm5MT.cbl:L881], and if the
       error number is not ``"0  "`` capture the number and message and test
       for a duplicate - ``SQL-Err (1:4) = "1062" or = "1022" or Sql-State =
       "23000"`` gives ``move 22 to fs-reply``
       [common/otm5MT.cbl:L886-L889].

    ANOMALY A44, NEW - ``WE-Error`` IS NEVER SET ON A WRITE FAILURE. It is
    zeroed at step 3 and no failure arm touches it, so a failed insert returns
    ``(99, 0)`` or ``(22, 0)``, never a diagnostic code. The maintainer's own
    inline note beside the 99 says as much: "this may need changing for val in
    WE-Error!!" [common/otm5MT.cbl:L881]. Contrast delete's 995 and rewrite's
    994, which do set it. The asymmetry is preserved.

    ``WS-MYSQL-COUNT-ROWS`` here is ``MySQL_affected_rows``, called
    unconditionally by ``Mysql-1210-Command``
    [copybooks/mysql-procedures.cpy:L179], so the driver's ``rowcount`` is its
    exact analogue. ``CLIENT_FOUND_ROWS`` is not set on the connection, which
    is what keeps the two equivalent.

    Args:
        otm5: the linkage record to insert.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(0, 0)`` on success, ``(22, 0)`` on a duplicate key, ``(99, 0)``
        otherwise.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-write")
    # Step 1 - L868.
    host_variables = load_host_variables(otm5)
    # Step 2 - L869: the RECORD's own key group.
    _set_file_key(file_access, _record_key(otm5))
    # Step 3 - L870-L874.
    _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))
    logging_data = file_access.logging_data
    logging_data.sql_state = "0" * len(logging_data.sql_state)
    _clear_sql_diagnostics(file_access)
    # Step 4 - L875.
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba070-Process-Write"][0])
    # Step 5 - L876, bb200-Insert [common/otm5MT.cbl:L1427-L1809].
    statement = (
        f"INSERT INTO {quote_identifier(TABLE)} SET {_assignment_list()};"
    )
    parameters = rendered_values(host_variables)
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:  # any driver error takes this path
        # L878-L890 - the count stays at zero when the query fails, so the
        # failure arm below is what the COBOL reaches; the diagnostics are
        # filled first, exactly as the frozen order has them.
        sql_err, sql_state = _apply_driver_failure(
            file_access, error, command="INSERT"
        )
        # L886-L889: the duplicate test, delegated to status.py so the "1062"
        # or "1022" or SQLSTATE "23000" triple is expressed in one place.
        if is_duplicate_key_bridge_level(sql_err, sql_state):
            # ANOMALY A44 - WE-Error stays zero even here.
            return _status(
                file_access, FsReply.DUPLICATE_KEY, int(WeError.SUCCESS)
            )
        return _status(file_access, FsReply.ERROR, int(WeError.SUCCESS))
    if affected != 1:
        # L877 with no exception raised - the row count disagreed, and the
        # frozen source's only outcome for that is (99, 0). ANOMALY A44.
        _LOG.warning(
            "%s: INSERT affected %d rows, not 1 [common/otm5MT.cbl:L877-L881]",
            TABLE,
            affected,
        )
        return _status(file_access, FsReply.ERROR, int(WeError.SUCCESS))
    return _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))


def rewrite(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba090-Process-Rewrite`` [common/otm5MT.cbl:L949-L991].

    1. ``perform bb000-HV-Load`` [common/otm5MT.cbl:L950].
    2. ``move OI-Key to WS-File-Key`` [common/otm5MT.cbl:L951].
    3. ``move 17 to ws-No-Paragraph`` [common/otm5MT.cbl:L952] - set BEFORE the
       predicate is built, where the write sets its number after the clears.
    4. Build ``\\`OI5-KEY\\`="<15 bytes>"`` from the RECORD BUFFER
       [common/otm5MT.cbl:L957-L967] and log it [common/otm5MT.cbl:L968].
    5. ``perform bb300-Update`` [common/otm5MT.cbl:L969] - ``UPDATE
       \\`PUITM5-REC\\` SET <all 29 columns> WHERE <predicate>;``. The primary
       key is among the columns SET, so a rewrite rewrites the key with the
       value it just recomposed - which is exactly how ANOMALY A1 propagates a
       silently different key into the row.
    6. ``if WS-MYSQL-COUNT-ROWS not = 1``: diagnostics, then ``move 99 to
       fs-reply`` and ``move 994 to WE-Error``
       [common/otm5MT.cbl:L984-L985].
    7. Success: ``move zero to FS-Reply WE-Error SQL-Err`` and ``move spaces to
       SQL-Msg`` [common/otm5MT.cbl:L988-L991].

    Because ``CLIENT_FOUND_ROWS`` is NOT set, an ``UPDATE`` that matches a row
    but changes no column reports zero affected rows and therefore returns
    ``(99, 994)`` - which is what ``MySQL_affected_rows`` reports to the
    compiled bridge too, so the behaviour matches rather than merely resembling.

    Args:
        otm5: the linkage record; supplies both the new values and the key.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(0, 0)`` on success, ``(99, 994)`` when the affected count is not 1.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-re-write")
    # Step 1 - L950.
    host_variables = load_host_variables(otm5)
    key = _record_key(otm5)
    # Step 2 - L951.
    _set_file_key(file_access, key)
    # Step 3 - L952.
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba090-Process-Rewrite"][0])
    # Step 4 - L957-L968.
    predicate, literal = _key_predicate(key)
    _set_log_where(file_access, literal)
    # Step 5 - L969, bb300-Update [common/otm5MT.cbl:L1817-L2205].
    statement = (
        f"UPDATE {quote_identifier(TABLE)} SET {_assignment_list()} "
        f"WHERE {predicate};"
    )
    parameters = (*rendered_values(host_variables), key)
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:  # any driver error takes this path
        _apply_driver_failure(file_access, error, command="UPDATE")
        return _status(file_access, FsReply.ERROR, REWRITE_ROWCOUNT_WE_ERROR)
    if affected != 1:
        # Step 6 - L984-L985.
        _LOG.warning(
            "%s: UPDATE affected %d rows, not 1 [common/otm5MT.cbl:L982-L985]",
            TABLE,
            affected,
        )
        return _status(file_access, FsReply.ERROR, REWRITE_ROWCOUNT_WE_ERROR)
    # Step 7 - L988-L991.
    _clear_sql_diagnostics(file_access)
    return _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))


def delete(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba080-Process-Delete`` [common/otm5MT.cbl:L895-L947].

    1. Build ``\\`OI5-KEY\\`="<15 bytes>"`` from the RECORD BUFFER
       [common/otm5MT.cbl:L903-L911]. NO ``bb000-HV-Load`` here - a delete
       needs only the key, so the host variables are never loaded.
    2. ``move WS-OTM5-Record (K:L) to WS-File-Key``
       [common/otm5MT.cbl:L912] and the predicate to ``WS-Log-Where``
       [common/otm5MT.cbl:L913].
    3. ``move 13 to ws-No-Paragraph`` [common/otm5MT.cbl:L917].
    4. ``DELETE FROM \\`PUITM5-REC\\` WHERE <predicate>;``
       [common/otm5MT.cbl:L922-L928] - a SINGLE-ROW delete. There is no
       delete-all anywhere in this pair, which is why :func:`delete_all` issues
       no statement.
    5. ``if WS-MYSQL-COUNT-ROWS not = 1``: diagnostics, then ``move 99 to
       fs-reply`` and ``move 995 to WE-Error``
       [common/otm5MT.cbl:L940-L941].
    6. ``else move spaces to SQL-Msg`` and ``move zero to SQL-Err``
       [common/otm5MT.cbl:L943-L945].

    ANOMALY A36 - THE SUCCESS ARM SETS NO STATUS. Step 6 clears only the two
    diagnostic fields; neither ``FS-Reply`` nor ``WE-Error`` is assigned, and
    ``ba010-Initialise`` declined to zero them [common/otm5MT.cbl:L390-L391].
    So a SUCCESSFUL DELETE RETURNS THE CALLER'S INCOMING PAIR. This module
    reproduces that rather than returning ``(0, 0)``, which is why the success
    path below reads the pair back instead of writing one.

    Args:
        otm5: the linkage record; only its leading fifteen bytes are used.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(99, 995)`` when the affected count is not 1, otherwise the
        caller's incoming pair, unmodified.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-delete")
    # Step 1 - L903-L911.
    key = _record_key(otm5)
    predicate, literal = _key_predicate(key)
    # Step 2 - L912-L913.
    _set_file_key(file_access, key)
    _set_log_where(file_access, literal)
    # Step 3 - L917.
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba080-Process-Delete"][0])
    # Step 4 - L922-L928.
    statement = f"DELETE FROM {quote_identifier(TABLE)} WHERE {predicate};"
    try:
        with execute_statement(connection, statement, (key,)) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:  # any driver error takes this path
        _apply_driver_failure(file_access, error, command="DELETE")
        return _status(file_access, FsReply.ERROR, DELETE_ROWCOUNT_WE_ERROR)
    if affected != 1:
        # Step 5 - L940-L941.
        _LOG.warning(
            "%s: DELETE affected %d rows, not 1 [common/otm5MT.cbl:L930-L941]",
            TABLE,
            affected,
        )
        return _status(file_access, FsReply.ERROR, DELETE_ROWCOUNT_WE_ERROR)
    # Step 6 - L943-L945: the diagnostics only. ANOMALY A36 - the status pair
    # is NOT written, so the caller's incoming values stand.
    _clear_sql_diagnostics(file_access)
    incoming = int(file_access.fs_reply)
    return (
        FsReply(incoming) if incoming in _FS_REPLY_VALUES else incoming,
        int(file_access.we_error),
    )


def delete_all(file_access: FileAccess) -> StatusPair:
    """Refuse ``fn-Delete-All`` - this pair implements no such verb.

    ANOMALY A16, stated as an ABSENCE. Function code 6 is dispatched by
    NEITHER program: the handler routes it to ``aa100-Bad-Function`` through
    ``when other``, whose comment names it explicitly - "6 is spare / unused"
    [common/acas029.cbl:L294] - and the bridge does the same through its own
    ``when other`` [common/otm5MT.cbl:L429-L430]. There is no delete-all
    paragraph, no ``fn-Open and fn-Delete-All`` coercion, and no mass delete
    anywhere in either file.

    That is a deliberate contrast with ``acas008``, which DOES coerce
    Open-Output into a delete-all and for which opening for output means
    deleting every row [common/acas008.cbl:L313-L319]. ``acas029`` is the
    seventh handler in the folder where Open-Output is absent as a special case,
    and ``PUITM5-REC`` is never truncated by this pair.

    So this verb exists only because the facade publishes the full twelve-verb
    vocabulary for every entity [copybooks/Proc-ACAS-FH-Calls.cob]. It issues
    NO statement and returns the bridge's bad-function pair.

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(99, 990)`` - the BRIDGE's bad-function pair, per ANOMALY A12.
    """
    _LOG.debug(
        "%s: fn-Delete-All is not implemented by %s or %s; function code 6 is "
        "'spare / unused' [common/acas029.cbl:L294] and reaches bad-function "
        "in both programs. No statement issued.",
        TABLE,
        HANDLER,
        BRIDGE,
    )
    return bad_function(file_access)


def bad_function(file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba100-Bad-Function`` [common/otm5MT.cbl:L1304-L1310].

    ANOMALY A12 - THE HANDLER AND THE BRIDGE DISAGREE ON THE CODE. The
    handler's ``aa100-Bad-Function`` moves ``999``
    [common/acas029.cbl:L522-L523]; the bridge's moves ``990``
    [common/otm5MT.cbl:L1308-L1309]. Because the handler's dispatch is
    flat-file-only (correction C5), the code observable on the RDB path is the
    BRIDGE's, so ``990`` is returned and ``999`` is recorded as
    :data:`HANDLER_BAD_FUNCTION_WE_ERROR` without being used.

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(99, 990)``.
    """
    # L1306: *> Houston; We have a problem
    return _status(file_access, FsReply.ERROR, BRIDGE_BAD_FUNCTION_WE_ERROR)



# ---------------------------------------------------------------------------
# THE HANDLER ENTRY POINT
# ---------------------------------------------------------------------------
# ``dispatch`` is the ``acas029`` analogue. Its parameter order is the
# handler's ``PROCEDURE DIVISION USING`` list preserved EXACTLY, so that a
# reviewer can diff the argument lists as Agent Action Plan section 0.4.3
# requires [common/acas029.cbl:L219-L225]:
#
#   L219  Procedure Division Using System-Record
#   L220                                              <- blank line, in the list
#   L221                           WS-OTM5-Record
#   L222                                              <- blank line, in the list
#   L223                           File-Access
#   L224                           File-Defs
#   L225                           ACAS-DAL-Common-data.
#
# ANOMALY A47 - THE SECTION THAT CONTAINS THE RDB BRANCH IS NAMED FOR THE
# FLAT-FILE PATH. ``aa-Process-Flat-File Section.``
# [common/acas029.cbl:L228-L229] contains ``aa010-main`` [L230], and it is
# from inside that section that the RDB branch is taken [L257-L261]. Every
# RDBMS call in the system therefore passes through a section whose name says
# it processes flat files. Nothing is corrected; the name is recorded.
#
# ANOMALY A45 - THE HANDLER NEVER LOGS ON THE RDB PATH. Every flat-file verb
# ends with ``go to aa999-main-exit`` [e.g. common/acas029.cbl:L382, L482,
# L493, L504, L516], and ``aa999-main-exit`` [L525] carries
# ``if Testing-1 / perform Ca-Process-Logs / end-if`` [L526-L528]. The RDB
# branch instead does ``go to AA-Main-Exit`` [L260], which lands on
# ``aa-main-exit`` [L530] - AFTER those three lines - so the handler's own log
# call is bypassed entirely. The maintainer states the intent himself beside
# the paragraph: ``Ca-Process-Logs. *> Not called on DAL access as it does it
# already`` [L617]. Two paths still log: the KEY GUARD, which exits through
# ``aa999-main-exit`` [L245, L251] and therefore DOES log, and the 901
# record-size fatal, which logs inline [L576-L578] before leaving through
# ``ba-rdbms-exit`` [L580]. On a normal RDB call the ONLY log is the bridge's
# own ``ba999-end`` [common/otm5MT.cbl:L1331-L1333].
#
# ANOMALY A46 - THE FLAT CLOSE VERB LOGS TWICE. ``aa030-Process-Close`` uses
# ``perform aa999-main-exit.`` [common/acas029.cbl:L347] - a PERFORM of an
# exit label, where every sibling verb uses ``go to`` - and then follows it
# with a second, redundant ``perform Ca-Process-Logs.`` [L350]. Since
# ``aa999-main-exit`` already performs it when ``Testing-1``, a flat close
# writes the log record twice. Flat-file-only, so recorded as a deliberate
# omission rather than reproduced.
# ---------------------------------------------------------------------------


def _process_logs(file_access: FileAccess, dal_common: AcasDalCommonData) -> None:
    """Reproduce ``Ca-Process-Logs`` [common/acas029.cbl:L617-L621].

    The frozen paragraph calls ``fhlogger`` passing ``File-Access`` and
    ``ACAS-DAL-Common-data``, gated on the ``Testing-1`` condition name
    [copybooks/Test-Data-Flags.cob:L11] over ``SW-Testing pic 9 value 1``.
    ``fhlogger`` writes a flat log file and touches NO table in the frozen
    schema, so Agent Action Plan section 0.3.4 makes it a log record here: it
    must not alter control flow and must not appear in any table dump.

    The gate is expressed against ``sw_testing`` directly because
    ``AcasDalCommonData`` publishes the field but not the ``88``-level
    predicate, and rule R-3 forbids adding one from this layer.

    Args:
        file_access: the ``File-Access`` linkage block, whose ``Logging-Data``
            sub-block carries the trace number, the file key and the
            ``WS-Log-Where`` text the frozen logger would have written.
        dal_common: the ``ACAS-DAL-Common-data`` block holding ``SW-Testing``.
    """
    # [copybooks/Test-Data-Flags.cob:L11] 88 Testing-1 value 1.
    if int(dal_common.sw_testing) != 1:
        return
    logging_data = file_access.logging_data
    # The frozen logger records the subsystem, the file number, the paragraph
    # trace number and the key it was working on. Both free-text fields are
    # sanitised before they reach a log record: WS-Log-Where carries assembled
    # SQL and WS-File-Key carries record data, and neither is trusted input.
    _LOG.debug(
        "fhlogger: system=%d file=%d paragraph=%d fs-reply=%d we-error=%d "
        "key=%s where=%s",
        int(logging_data.ws_log_system),
        int(logging_data.ws_log_file_no),
        int(logging_data.ws_no_paragraph),
        int(file_access.fs_reply),
        int(file_access.we_error),
        sanitise_for_log(str(logging_data.ws_file_key)),
        redact_for_log(str(logging_data.ws_log_where)),
    )
    # [copybooks/Test-Data-Flags.cob:L18] Log-File-Rec-Written pic 9(6), the
    # counter the frozen logger bumps. Its picture is six digits, so it wraps
    # at a million rather than growing without bound.
    dal_common.log_file_rec_written = (
        int(dal_common.log_file_rec_written) + 1
    ) % 1_000_000


def _key_guard(file_access: FileAccess) -> StatusPair | None:
    """Reproduce the handler's key guard [common/acas029.cbl:L239-L253].

    ANOMALY A18 - THE 996/998 SPLIT. The guard is a three-branch
    ``evaluate File-Function`` in which ``fn-read-indexed`` (4) and
    ``fn-start`` (9) FALL THROUGH into one shared body returning ``998``
    [L240-L246] while ``fn-delete`` (8) has its own body returning ``996``
    [L247-L252]. Both bodies carry the IDENTICAL trailing comment, "file seeks
    key type out of range" [L243, L249] - the copy-paste is visible in the
    source - and both set ``fs-reply`` to ``99``. The two codes are NOT
    unified.

    ANOMALY A19 - ``fn-read-next`` (3) IS NOT GUARDED, even though a read-next
    that follows a start positions on the key. No guard is added here.

    ANOMALY A38 - THE BRIDGE DELIBERATELY DROPPED THIS GUARD. Where every
    other paragraph of the bridge mirrors the handler, ``ba010-Initialise``
    carries only the commented-out heading "Now Test for valid key for start,
    read-indexed and delete / REMOVED as not used here"
    [common/otm5MT.cbl:L400-L401]. So the guard exists in exactly one place in
    the chain. Because the handler applies it at [L239] - BEFORE the flat/RDB
    branch at [L257] - it governs the RDB path too, and is therefore one of
    the very few handler behaviours that IS reproduced here rather than
    recorded as a flat-file omission (correction C5).

    The guard reads ``File-Key-No`` from ``Logging-Data``
    [copybooks/wsfnctn.cob], and this table declares exactly one key -
    ``KeyOfReference occurs 1`` [common/otm5MT.cbl:L255] over
    ``'OI5-KEY' / '00010015' / 'STR'`` [L251-L253] - so any value other than
    1 is out of range by construction.

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``None`` when the call may proceed; otherwise the status pair the
        frozen guard would have left, already written into ``file_access``.
    """
    function = int(file_access.file_function)
    if function not in {int(code) for code in KEY_GUARDED_FUNCTIONS}:
        # A19: fn-read-next (3), fn-open (1), fn-close (2), fn-write (5) and
        # fn-re-write (7) reach no branch of the evaluate at all.
        return None
    if int(file_access.logging_data.file_key_no) == KEY_COUNT:
        return None
    # A18: the delete arm's own code, distinct from the shared read/start one.
    # [common/acas029.cbl:L249] move 996 to WE-Error
    if function == int(FileFunction.DELETE):
        we_error = KEY_GUARD_WE_ERROR_DELETE
    else:
        # [common/acas029.cbl:L243] move 998 to WE-Error, shared by the
        # fall-through pair fn-read-indexed (4) and fn-start (9).
        we_error = KEY_GUARD_WE_ERROR_READ_START
    # [common/acas029.cbl:L244, L250] move 99 to fs-reply, in both bodies.
    return _status(file_access, FsReply.ERROR, we_error)


def _copy_rdbms_flat_statuses(
    system: SystemRecord, file_access: FileAccess
) -> None:
    """Reproduce ``move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses``.

    A two-byte GROUP move from the system record into ``File-Access``
    [common/acas029.cbl:L258], annotated by the maintainer "needed for DAL?
    not JC/dbpre versions". It is a real, observable side effect on the
    linkage block, so it is performed rather than skipped even though the JC
    bridge this module replaces never reads the copy.

    The source group is ``RDBMS-Flat-Statuses`` [copybooks/wssystem.cob:L111]
    holding ``File-System-Used pic 9`` [L112] and ``File-Duplicates-In-Use
    pic 9`` [L123]; the destination is ``FA-RDBMS-Flat-Statuses``
    [copybooks/wsfnctn.cob:L72] holding the ``FA-`` prefixed pair [L73, L82].
    The maintainer marks the second byte "NO LONGER USED other than for a '6'
    = rdb" [copybooks/wsfnctn.cob:L82] and "No longer in use"
    [copybooks/wssystem.cob:L123]; it is copied anyway, because the frozen
    move is a group move and copies both bytes.

    Args:
        system: the ``System-Record`` linkage block.
        file_access: the ``File-Access`` linkage block, mutated in place.
    """
    source = system.system_data_block.rdbms_flat_statuses
    destination = file_access.fa_rdbms_flat_statuses
    destination.fa_file_system_used = int(source.file_system_used)
    destination.fa_file_duplicates_in_use = int(source.file_duplicates_in_use)


def dispatch(
    system: SystemRecord,
    otm5: OiHeader,
    file_access: FileAccess,
    file_defs: FileDefsA,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
) -> StatusPair:
    """Reproduce ``acas029``, the OTM5 file handler [common/acas029.cbl].

    This is the single entry point the facade calls, standing in for
    ``call "acas029" using System-Record WS-OTM5-Record File-Access File-Defs
    ACAS-DAL-Common-data``. The five positional parameters are the handler's
    ``PROCEDURE DIVISION USING`` list in order [common/acas029.cbl:L219-L225],
    so the Python call site diffs one-for-one against the COBOL one, which is
    the contract Agent Action Plan section 0.4.3 states.

    THE ORDER OF OPERATIONS, TAKEN FROM THE FROZEN SOURCE

    1. Log identity. ``move 4 to WS-Log-System`` [L234] - Purchase - and
       ``move 15 to WS-Log-File-No`` [L235].
    2. The key guard [L239-L253], on BOTH paths. See :func:`_key_guard` for
       anomalies A18, A19 and A38.
    3. The flat/RDB branch [L257-L261]. ``if not FS-Cobol-Files-Used`` tests
       ``File-System-Used`` [copybooks/wssystem.cob:L112-L113]; the group move
       of the status pair [L258] is performed; then
       ``perform ba-Process-RDBMS`` [L259] and ``go to AA-Main-Exit`` [L260],
       which LEAVES before any flat-file statement.
    4. ``ba-Process-RDBMS`` [L537], three paragraphs that fall through one
       into the next: ``ba010-Test-WS-Rec-Size`` [L545] bumps the log file
       number 15 -> 25 [L551]; ``ba012-Test-WS-Rec-Size-2`` [L553] latches the
       record lengths and the credentials; ``ba015-Test-Ends`` [L595] issues
       ``call "otm5MT"`` [L605-L609].
    5. The bridge. ``ba010-Initialise`` [common/otm5MT.cbl:L387] clears the
       diagnostics but NOT the status pair (anomaly A36), then
       ``evaluate File-Function`` [L408-L431] routes to one paragraph.
    6. ``ba999-end`` [L1328-L1333] logs when ``Testing-1``.
    7. Return with NO recovery: "Any errors leave it to caller to recover
       from" [common/acas029.cbl:L611].

    WHAT IS DELIBERATELY OMITTED, AND WHY (rule R-5 requires the record)

    * The ENTIRE flat-file path. Correction C5: the maintainer's own banner
      ``*> So we are processing Cobol Flat files. *``
      [common/acas029.cbl:L269-L271] proves that ``ba012`` [L265], the
      three-field diagnostic clear [L275] and the handler's own
      ``evaluate File-Function`` [L277-L296] - and therefore ``aa020``
      through ``aa100`` [L301-L523] - are reached only when ISAM files are
      selected. This module is the RDB path, so none of it is reproduced, and
      anomalies A12 (the handler's 999), A13 (FS-Reply 35), A14 (the
      handler's 997), A15 (the open-i-o retry), A16 (the unchecked
      open-output), A17 (the flat 5..8 guard), A31 (the live ``stop``) and
      A46 (the double log on close) are recorded above and at their verbs
      rather than implemented.
    * ``file_defs``. Only THREE of the handler's five linkage parameters cross
      into the bridge - ``File-Access``, ``ACAS-DAL-Common-data`` and
      ``WS-OTM5-Record`` [common/acas029.cbl:L605-L609] matching
      ``PROCEDURE DIVISION using`` [common/otm5MT.cbl:L369-L371]. ``File-Defs``
      and the test-flags block are declared in the handler's linkage
      [L215, L217] and never passed on, and ``File-Defs`` holds ISAM file
      names [copybooks/wsnames.cob] that no SQL statement can use. The
      parameter is accepted to preserve the argument list and is not read.
    * The credential latch [L587-L592]. The frozen handler copies six fields
      out of the system record into the bridge's connection block on the
      FIRST call only, "hopefully once is enough :)" [L585-L586], in the
      order Schema, UName, UPass, PORT, Host, Socket - note Port third from
      last, where ``copybooks/wsfnctn.cob:L56-L62`` declares it last
      (anomaly A32, the third distinct ordering of the same six fields).
      Here :mod:`acas_posting.dal.connection` owns the connection, reads those
      same six values from the system record at open time and holds them for
      the life of the handle, so the latch is delegated rather than
      duplicated.

    THE POSITIVE FINDING, RECORDED BECAUSE IT IS ALSO A FINDING

    The handler's ``CALL`` list and the bridge's ``USING`` list agree exactly,
    and both sides view the record through the same
    ``copy "plwsoi.cob" replacing OI-Header by WS-OTM5-Record``
    [common/acas029.cbl:L209] and [common/otm5MT.cbl:L348-L349]. This is the
    cleanest handler/bridge agreement in the folder - contrast
    ``plinvoiceMT``, whose ``USING`` names a record its caller does not pass -
    and the nine money fields carry nine digits at all three layers with no
    width drift at all. Bridges are not uniformly broken; each is verified
    rather than extrapolated from its siblings.

    Args:
        system: ``System-Record`` [copybooks/wssystem.cob], supplying the
            flat/RDB switch and the six connection fields.
        otm5: ``WS-OTM5-Record`` viewed as ``OI-Header``
            [copybooks/plwsoi.cob:L12], the caller's record buffer. Mutated in
            place by the reading verbs, exactly as the frozen linkage block is.
        file_access: ``File-Access`` [copybooks/wsfnctn.cob], carrying the
            function code, the access type, the key number, the returned
            status pair and the whole ``Logging-Data`` sub-block.
        file_defs: ``File-Defs`` [copybooks/wsnames.cob]. Accepted for
            argument-list fidelity and not read; see above.
        dal_common: ``ACAS-DAL-Common-data``
            [copybooks/Test-Data-Flags.cob:L6], whose ``SW-Testing`` gates the
            logging.
        transport: TLS material for the connection. Keyword-only, so the five
            positional parameters still diff against the COBOL. It models a
            policy of :mod:`acas_posting.dal.connection` and NOT anything in
            the frozen source: the bridge's six connection strings
            [common/otm5MT.cbl:L438-L461] carry no TLS material of any kind.

    Returns:
        The ``(FS-Reply, WE-Error)`` pair, also written into ``file_access``.

    Raises:
        AcasFileHandlerError: if the system record selects Cobol flat files,
            or if a data verb is issued before :func:`open_`.
    """
    logging_data = file_access.logging_data

    # -- 1. Log identity ---------------------------------------------------
    # [common/acas029.cbl:L232-L235] "For logging only."
    #   L234 move 4  to WS-Log-System   *> 1=IRS 2=GL 3=SL 4=PL 5=Invoice
    #   L235 move 15 to WS-Log-File-No  *> RDB, File/Table
    # The legend at L234 calls 5 "Invoice" where acas013/acas015/acas022 use
    # 5=Stock and 6=PL & SL: the codebase carries two mutually inconsistent
    # legends. Both are recorded in the module docstring; neither is resolved.
    logging_data.ws_log_system = WS_LOG_SYSTEM
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT

    # -- 2. The key guard, on BOTH paths -----------------------------------
    # [common/acas029.cbl:L239-L253] sits above the flat/RDB branch at L257,
    # so it is evaluated before the path is chosen. Its exits go to
    # aa999-main-exit [L245, L251], which DOES log (anomaly A45).
    guarded = _key_guard(file_access)
    if guarded is not None:
        _process_logs(file_access, dal_common)
        return guarded

    # -- 3. The flat/RDB branch --------------------------------------------
    # [common/acas029.cbl:L257] if not FS-Cobol-Files-Used
    # FS-Cobol-Files-Used is 88-level "value zero" over File-System-Used
    # [copybooks/wssystem.cob:L112-L113], so ZERO selects ISAM files and 1
    # selects MySQL [L114 FS-MySql-Used value 1].
    if int(system.system_data_block.rdbms_flat_statuses.file_system_used) == 0:
        # DELIBERATE OMISSION O1, and the loudest one in this module. The
        # frozen handler would now perform ISAM I/O against open-item-file-5
        # [copybooks/plseloi5.cob:L2 assign file-29]. Nothing in
        # acas_posting implements an ISAM store, and the frozen source has NO
        # status code for "flat files requested of a relational handler" -
        # inventing one would be adding a validation, which rule R-3 forbids.
        # The refusal is therefore raised as the layer's own exception, which
        # is the same precedent :func:`_require_connection` sets. A scenario
        # seed must set File-System-Used to 1, exactly as it must for the
        # compiled oracle to touch MySQL at all.
        raise AcasFileHandlerError(
            int(FsReply.ERROR),
            int(WeError.UNKNOWN_UNEXPECTED),
            operation="fs-cobol-files-used",
            table=TABLE,
        )

    # [common/acas029.cbl:L258] the group move, performed for its side effect.
    _copy_rdbms_flat_statuses(system, file_access)

    # -- 4. ba-Process-RDBMS [common/acas029.cbl:L537] ---------------------
    # ba010-Test-WS-Rec-Size [L545] contains exactly one statement, and
    # nothing performs it: the flat path performs ba012 directly [L265] while
    # the RDB path performs the SECTION [L259] and so enters at its first
    # paragraph and falls through. That is why the 15 -> 25 bump is observable
    # ONLY on the RDB path - which makes 25 the effective file number here.
    # It collides three ways with acas008 (system 1) and acas019 (system 3),
    # both of which also bump 15 -> 25; only the (system, file) pair
    # disambiguates, and this handler's system is 4.
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB  # [L551]

    # ba012-Test-WS-Rec-Size-2 [L553] falls through from ba010.
    fatal = record_size_gate(file_access)
    if fatal is not None:
        # [L576-L578] the 901 path logs INLINE - the one place other than the
        # key guard where the handler logs on the RDB path (anomaly A45) -
        # and then [L580] go to ba-rdbms-exit, which is [L613] followed by
        # exit section [L614]. That skips ba015-Test-Ends and therefore skips
        # the call "otm5MT" entirely: the bridge never runs.
        _process_logs(file_access, dal_common)
        return fatal

    # -- 5. The bridge -----------------------------------------------------
    # ba015-Test-Ends [L595] issues call "otm5MT" [L605-L609]. Everything
    # from here to the return is inside the bridge.
    _bridge_initialise(file_access)

    function = int(file_access.file_function)

    # The bridge's own dispatch [common/otm5MT.cbl:L408-L431]. Written as an
    # explicit chain in the frozen order, one branch per ``when``, so that
    # each arm carries its locator. The handler's competing dispatch
    # [common/acas029.cbl:L277-L296] lists the same codes in the same order
    # and is unreachable here (correction C5).
    if function == int(FileFunction.OPEN):
        # [common/otm5MT.cbl:L409-L410] when 1 -> ba020 "Coded / D.tested".
        # The bridge's open has NO access-type branching, so all four open
        # verbs are one implementation; see the alias block above.
        status = open_(system, file_access, transport=transport)
    elif function == int(FileFunction.CLOSE):
        # [common/otm5MT.cbl:L411-L412] when 2 -> ba030 "Coded / D.tested".
        status = close(file_access)
    elif function == int(FileFunction.READ_NEXT):
        # [common/otm5MT.cbl:L413-L414] when 3 -> ba040.
        status = read_next(otm5, file_access)
    elif function == int(FileFunction.READ_INDEXED):
        # [common/otm5MT.cbl:L415-L416] when 4 -> ba050.
        status = read_indexed(otm5, file_access)
    elif function == int(FileFunction.WRITE):
        # [common/otm5MT.cbl:L417-L418] when 5 -> ba070.
        status = write(otm5, file_access)
    elif function == int(FileFunction.RE_WRITE):
        # [common/otm5MT.cbl:L419-L420] when 7 -> ba090. Note the frozen
        # order: 7 is dispatched BEFORE 8, in both the bridge and the handler.
        status = rewrite(otm5, file_access)
    elif function == int(FileFunction.DELETE):
        # [common/otm5MT.cbl:L421-L422] when 8 -> ba080.
        status = delete(otm5, file_access)
    elif function == int(FileFunction.START):
        # [common/otm5MT.cbl:L423-L424] when 9 -> ba060 "Uses Header table
        # only". The access type reaches the bridge's own 5..8 guard
        # [common/otm5MT.cbl:L765-L769] - correction C2 - which is a genuine
        # RDB-path guard, unlike the flat one at [common/acas029.cbl:L441].
        status = start(otm5, file_access, AccessType(int(file_access.access_type)))
    else:
        # [common/otm5MT.cbl:L429-L430] when other *> 6 is spare / unused.
        #
        # ANOMALY A34, refined by correction C3. ``fn-Delete-All`` (6) is
        # "spare / unused" in the frozen comment, and the two extended codes
        # are NOT published by this module: ``fn-Read-By-Batch`` (32) and
        # ``fn-Read-By-Cust`` (33) are declared in
        # [copybooks/wsfnctn.cob:L103-L104] as existing "for OTM3/5
        # (sl095/pl095)" and "for OTM3 (sl110, 120, 190)", and the HANDLER
        # dispatches neither - ``acas029`` contains no ``when 3x`` at all
        # [common/acas029.cbl:L277-L296]. The bridge does route them, to
        # ba140 and ba150 [common/otm5MT.cbl:L425-L428], so correction C3
        # records that the vocabulary is dead in the handler rather than in
        # the whole chain. They stay unpublished here because their only
        # callers, the ``sl095``/``pl095`` report programs, are explicitly out
        # of scope per Agent Action Plan section 0.2.2, so no in-scope program
        # can issue them; the omission is recorded rather than silent.
        #
        # ANOMALY A12: the code returned is the BRIDGE's 990
        # [common/otm5MT.cbl:L1308], not the handler's unreachable 999
        # [common/acas029.cbl:L522].
        status = bad_function(file_access)

    # -- 6. ba999-end [common/otm5MT.cbl:L1328-L1333] ----------------------
    # if Testing-1 / perform Ca-Process-Logs / end-if, then ba999-exit [L1335]
    # exit program [L1336]. On a normal RDB call this is the ONLY log written,
    # because the handler's own call is bypassed (anomaly A45).
    _process_logs(file_access, dal_common)

    # -- 7. Return with no recovery ----------------------------------------
    # [common/acas029.cbl:L611] "Any errors leave it to caller to recover
    # from". The handler inspects nothing after the CALL returns, so the pair
    # is handed back exactly as the bridge left it.
    return status



# ===========================================================================
# --- traceability ---
# ===========================================================================
# Rule R-5 requires that every program map to a module, every paragraph to a
# function and every field to a data-dictionary entry, and that the mapping be
# RECORDED rather than left implicit. The four tables below are this module's
# contribution to docs/migration/traceability.md; the field table is generated
# rather than transcribed, because Agent Action Plan section 0.8.1 makes "data
# dictionary first" a directive.
#
# ---------------------------------------------------------------------------
# 1. PROGRAM -> MODULE
# ---------------------------------------------------------------------------
#   common/acas029.cbl   (625 lines)  -> this module, handler layer
#   common/otm5MT.cbl   (2219 lines)  -> this module, bridge layer
#   common/otm5MT.scb   (1209 lines)  -> read for its /MYSQL directive block
#                                        and its key metadata; not executed
#   -> mysql/ACASDB.sql:L596  `PUITM5-REC`, 29 columns, single-column PK
#
# Agent Action Plan section 0.1.2 collapses FOUR COBOL hops - facade copybook,
# numbered handler, generated bridge, literal SQL - into TWO Python layers: a
# facade module publishing the verb vocabulary, and one module per handler
# owning the SQL for its table. Both COBOL programs therefore land in this one
# module, and the entity facade `OTM5`
# [copybooks/Proc-ACAS-FH-Calls.cob] resolves to the twelve verbs below.
#
# ---------------------------------------------------------------------------
# 2. PARAGRAPH -> FUNCTION, handler layer  [common/acas029.cbl]
# ---------------------------------------------------------------------------
#   L228  aa-Process-Flat-File Section.   -> dispatch                (A47: the
#                                             section that holds the RDB
#                                             branch is named for the flat
#                                             path)
#   L230  aa010-main.                     -> dispatch, steps 1-3
#   L301  aa020-Process-Open.             -> OMITTED, flat-file only (A13,
#                                             A14, A15, A16, A22)
#   L340  aa030-Process-Close.            -> OMITTED, flat-file only (A46)
#   L353  aa040-Process-Read-Next.        -> OMITTED, flat-file only (A31)
#   L384  aa041-Move-Inv-Data.            -> compose_key, whose staging-area
#                                             concatenation this paragraph
#                                             mirrors for the log key
#   L391  aa045-Eval-Keys.                -> OMITTED, flat-file only (A21)
#   L409  aa050-Process-Read-Indexed.     -> OMITTED, flat-file only
#   L431  aa060-Process-Start.            -> OMITTED, flat-file only (A17,
#                                             A20)
#   L484  aa070-Process-Write.            -> OMITTED, flat-file only
#   L495  aa080-Process-Delete.           -> OMITTED, flat-file only
#   L506  aa090-Process-Rewrite.          -> OMITTED, flat-file only (A27)
#   L518  aa100-Bad-Function.             -> OMITTED, flat-file only (A12:
#                                             its 999 is unreachable, so
#                                             bad_function returns the
#                                             bridge's 990)
#   L525  aa999-main-exit.                -> the `return` sites of the guard
#                                             and the 901 gate, both of which
#                                             log (A45)
#   L530  aa-main-exit.                   -> dispatch's normal return; reached
#                                             from L260, BYPASSING L526-L528
#   L534  aa-Exit.  exit program.         -> dispatch's return statement
#   L537  ba-Process-RDBMS section.       -> dispatch, steps 4-5
#   L545  ba010-Test-WS-Rec-Size.         -> dispatch, the 15 -> 25 bump
#   L553  ba012-Test-WS-Rec-Size-2.       -> record_size_gate               +
#                                             the credential latch, delegated
#                                             to dal.connection (A32)
#   L595  ba015-Test-Ends.                -> dispatch, the bridge call
#   L613  ba-rdbms-exit.  exit section.   -> record_size_gate's early return
#   L617  Ca-Process-Logs.                -> _process_logs
#   L623  ca-Exit.  exit.                 -> _process_logs' fall-off
#
#   The handler's key guard [L239-L253] has no label of its own; it is
#   _key_guard, and it is the ONE handler behaviour outside ba-Process-RDBMS
#   that this module reproduces, because it precedes the flat/RDB branch.
#
# ---------------------------------------------------------------------------
# 3. PARAGRAPH -> FUNCTION, bridge layer  [common/otm5MT.cbl]
# ---------------------------------------------------------------------------
#   L373  ba-ACAS-DAL-Process  section.   -> dispatch, steps 5-7
#   L387  ba010-Initialise.               -> _bridge_initialise        (A36)
#   L433  ba020-Process-Open.             -> open_ / open_input / open_i_o /
#                                             open_output / open_extend
#   L477  ba030-Process-Close.            -> close                     (A36)
#   L491  ba040-Process-Read-Next.        -> read_next, the SELECT half
#   L566  ba041-Reread.                   -> read_next, the FETCH half (A11,
#                                             A42, A43)
#   L650  ba050-Process-Read-Indexed.     -> read_indexed
#   L761  ba060-Process-Start.            -> start                (C2, A41)
#   L867  ba070-Process-Write.            -> write                     (A44)
#   L895  ba080-Process-Delete.           -> delete                    (A36)
#   L949  ba090-Process-Rewrite.          -> rewrite
#   L994  ba140-Process-Read-Next.        -> NOT PUBLISHED, fn 32      (A34)
#  L1067  ba141-Reread.                   -> NOT PUBLISHED, fn 32
#  L1149  ba150-Process-Read-Next.        -> NOT PUBLISHED, fn 33      (A34)
#  L1222  ba151-Reread.                   -> NOT PUBLISHED, fn 33
#  L1304  ba100-Bad-Function.             -> bad_function              (A12)
#  L1316  ba998-Free.                     -> the cursor reset inside close,
#                                             read_next and read_indexed (A10)
#  L1328  ba999-end.                      -> _process_logs, called last
#  L1335  ba999-exit.  exit program.      -> each verb's return statement
#  L1338  bb000-HV-Load      Section.     -> load_host_variables  (A1, A2,
#                                             A3, A4, A5, A6, A25, A28)
#  L1384  bb000-Exit.                     -> load_host_variables' return
#  L1387  bb100-UnloadHVs    Section.     -> unload_host_variables (A1, A8,
#                                             A28, A29)
#  L1424  bb100-Exit.                     -> unload_host_variables' return
#  L1427  bb200-Insert Section.           -> write, via _assignment_list and
#                                             rendered_values
#  L1814  bb200-Exit.                     -> write's return
#  L1817  bb300-Update Section.           -> rewrite, same two helpers
#  L2208  bb300-Exit.                     -> rewrite's return
#  L2211  Ca-Process-Logs.                -> _process_logs
#  L2217  ca-Exit.  exit.                 -> _process_logs' fall-off
#
#   ANOMALY A48 - THE BRIDGE'S OWN PARAGRAPH COMMENTS DESCRIBE A TABLE THIS
#   BRIDGE DOES NOT HAVE. ba020 and ba030 are annotated "no rg01
#   requirements" [common/otm5MT.cbl:L433, L477] while ba040, ba050, ba070
#   and ba080 are annotated "Has rg01 requirements" [L491, L650, L867, L895],
#   and ba060 is annotated "coded for header & lines [ NEEDED ? ]" [L761] -
#   yet `PUITM5-REC` is a SINGLE table with no repeating group and no lines
#   table at all, unlike slinvoiceMT/plinvoiceMT which own a header and a
#   lines table each. The annotations are inherited from the invoice-bridge
#   template, and they are the same copy-paste family as the three cursors
#   (A9), the dead `WS-Body-Key` (A30) and the `INVOICE-RECORD` log literal
#   (A42). Recorded, not corrected: this module publishes one table.
#
# ---------------------------------------------------------------------------
# 4. CONTROL-FLOW TRANSFORMATION, per Agent Action Plan section 0.4.2
# ---------------------------------------------------------------------------
# A FULL CENSUS of every `GO TO` in the migrated surface - the handler's
# 27 sites and the bridge's 40 sites between L369 and L1340 - yields a
# result worth stating plainly:
#
#   Class 1, loop-back        -> `continue` inside `while True:`   : 0 SITES
#   Class 2, forward terminator -> `break` plus the post-loop work: 0 SITES
#   Class 3, section/paragraph exit -> `return`                    : 56 sites
#   Class 4, sibling re-dispatch -> named call + explicit transfer : 11 sites
#
# THERE IS NOT ONE BACKWARD TRANSFER IN EITHER PROGRAM. Every `GO TO` in this
# chain moves forward, and 56 of the 67 target a trailing exit label. That is
# why no verb in this module contains a loop: the iteration in this chain is
# the CALLER's - a posting program performs the read-next verb repeatedly -
# and the handler and bridge are strictly single-pass. Classes 1 and 2 are
# therefore recorded as ABSENT rather than left unmentioned, so that a reader
# comparing this module against the four-class taxonomy does not conclude a
# loop was lost.
#
# Class 3, the 56 exit transfers, by target:
#   handler -> aa999-main-exit  [L245, L251, L309, L328, L338, L366, L375,
#                                L378, L382, L425, L429, L443, L453, L460,
#                                L467, L474, L482, L493, L504, L516]
#   handler -> aa-main-exit     [L260]   <- the RDB path; case drift, the
#                                          statement writes `AA-Main-Exit`
#                                          where the label at L530 is lower
#   handler -> ba-rdbms-exit    [L580]   <- the 901 fatal, skipping the CALL
#   bridge  -> ba999-end        [L465, L475, L489, L554, L619, L636, L642,
#                                L648, L759, L768, L863, L893, L942, L947,
#                                L986, L992, L1055, L1118, L1135, L1141,
#                                L1147, L1210, L1273, L1290, L1296, L1302,
#                                L1310]
#   The bridge spells that one label THREE ways across those 27 statements -
#   `ba999-end`, `ba999-End` and `ba999-End.` - the same casing drift as
#   `function Length` / `function length` (A40) and `aa045-Eval-Keys` /
#   `aa045-Eval-keys`. COBOL is case-insensitive, so nothing breaks; nothing
#   is tidied either.
#
# Class 4, the 11 re-dispatch transfers:
#   handler dispatch [L279, L281, L283, L285, L287, L289, L291, L293, L295]
#     -> flat-file only, OMITTED (correction C5). Its fall-through safety net
#        `go to aa100-Bad-Function` [L299], commented "Should never get here
#        but in case :(", is likewise omitted.
#   bridge dispatch  [L410, L412, L414, L416, L418, L420, L422, L424, L426,
#                     L428, L430]
#     -> dispatch's if/elif chain, one branch per `when`, in frozen order.
#   bridge -> ba998-Free [L694, L753]
#     -> a named call followed by fall-through into ba999-end, because
#        ba998-Free [L1316] is the paragraph immediately before ba999-end
#        [L1328]. In Python: the cursor reset, then the return.
#
# CORRECTION C6 TO THE WORKING SPECIFICATION. Agent Action Plan section 0.4.2
# states that `PERFORM ... THRU` "occurs only SEVEN times across the entire
# in-scope set". That census counts the twelve POSTING PROGRAMS only. The
# bridge layer is not covered by it: `common/otm5MT.cbl` alone carries FIFTEEN
# live `PERFORM ... THRU` statements plus one commented out [L436], every one
# of them a paragraph-RANGE performance over `copybooks/mysql-procedures.cpy`:
#   L463  MYSQL-1000-OPEN      THRU MYSQL-1090-EXIT  -> mysql_1000_open +
#                                                       mysql_1090_exit
#   L487  MYSQL-1980-CLOSE     THRU MYSQL-1999-EXIT  -> mysql_1980_close +
#                                                       mysql_1999_exit
#   L531, L686, L832, L929, L1032, L1187, L1810, L2204
#         MYSQL-1210-COMMAND   THRU MYSQL-1219-EXIT  -> execute_statement
#   L532, L687, L833, L1033, L1188
#         MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT -> the cursor fetch
# Each range collapses into ONE call into dal.connection or dal.cursor_state,
# which is the "explicit function composition preserving execution order" the
# section requires. The correction is recorded because a reader auditing the
# THRU census against the AAP's figure would otherwise find sixteen sites in
# one file and conclude the census was wrong rather than differently scoped.
#
# ---------------------------------------------------------------------------
# 5. FIELD -> DICTIONARY ENTRY
# ---------------------------------------------------------------------------
# Not transcribed. Every one of the 29 columns is resolved at import time
# through acas_posting.dictionary.loader, so the triple that Agent Action Plan
# section 0.8.2 designates authoritative - copybook picture clause, bridge
# host variable, frozen DDL column definition - is READ rather than retyped:
#
#   COLUMNS            <- loader.columns_for(TABLE), in frozen ordinal order
#   DICTIONARY_KEYS    <- the citable key of every column
#   CHARACTER_COLUMNS / DECIMAL_COLUMNS / INTEGER_COLUMNS
#                      <- loader base types, not name patterns
#   CHARACTER_WIDTHS / DECIMAL_SCALES / COLUMN_IS_UNSIGNED
#                      <- loader column metadata
#   _MONEY_COLUMNS / _DEDUCTION_COLUMNS
#                      <- discriminated by DECLARED WIDTH from the frozen DDL,
#                         never by field name
#   SIGN_LOSS_COLUMNS  <- the four fields whose copybook declaration is signed
#                         and whose host variable and column are not (A4)
#   WRITE_ONLY_COLUMNS <- the two derived columns the bridge loads and never
#                         unloads (A1)
#
# loader.cite('PUITM5-REC.OI5-KEY') yields, verbatim:
#   PUITM5-REC.OI5-KEY  copybook=copybooks/plwsoi5B.cob:L13
#                       bridge=common/otm5MT.cbl:L304
#                       column=mysql/ACASDB.sql:L597
#
# TWO FIELDS HAVE NO COLUMN AND NO HOST VARIABLE, and Agent Action Plan
# section 0.5.3 requires that "deliberate omissions are recorded as
# omissions":
#   OI-Customer   [copybooks/plwsoi.cob:L14-L15] - a group of exactly ONE
#                 child wrapping OI-Supplier, occupying the same seven bytes.
#                 Neither bb000-HV-Load nor bb100-UnloadHVs touches it (A7).
#                 It is also named "Customer" inside a PURCHASE copybook, one
#                 of the four sales-terminology leaks in this chain (A23).
#   OI-Approp     [copybooks/plwsoi.cob:L44-L45] - REDEFINES OI-Net across two
#                 source lines, so it is the SAME storage. The frozen schema
#                 records the aliasing only as
#                 `COMMENT 'Also called Approp'` on OI5-NET (A8), which is why
#                 unload_host_variables mirrors oi_net into oi_approp rather
#                 than reading a column that does not exist.
#
# ---------------------------------------------------------------------------
# 6. ANOMALY REGISTER -> REPRODUCTION SITE
# ---------------------------------------------------------------------------
# Rule R-4: "A defect reproduced is correct; a defect fixed is a failure", and
# Agent Action Plan section 0.7.4 C-4 prescribes the mechanism - a comment at
# each reproduction site citing the COBOL locator. Every entry below carries
# one. Behavioural anomalies are reproduced in code; documentation-class
# anomalies (A21 through A30, A39, A40, A46, A47, A48) have a comment as their
# only possible reproduction site, since their observable effect on the
# database is nil.
#
#   A1  two write-only columns .............. load_host_variables,
#                                             unload_host_variables
#   A2  binary batch group -> 8 digits ...... compose_batch
#   A3  key by concatenation ................ compose_key
#   A4  four sign losses .................... _drop_sign, SIGN_LOSS_COLUMNS
#   A5  numeric -> char, twice .............. load_host_variables
#   A6  binary -> char, twice ............... load_host_variables
#   A7  OI-Customer, group of one ........... section 5 above, blank_record
#   A8  OI-Approp redefines OI-Net .......... unload_host_variables
#   A9  three cursors, one key .............. CURSOR_SLOT,
#                                             UNREACHED_CURSOR_SLOTS
#   A10 cursor reset asymmetry .............. close, read_next, read_indexed
#   A11 EOF / EOF2 / EOF3 ................... EOF_FILE_KEYS, read_next
#   A12 handler 999 vs bridge 990 ........... bad_function, dispatch
#   A13 FS-Reply 35 ......................... FS_REPLY_OPEN_INPUT_FAILED
#   A14 fn-extend returns 997 ............... OPEN_EXTEND_WE_ERROR, open_extend
#   A15 open-i-o retry, status untested ..... the C5 omission block
#   A16 open-output unchecked, no delete-all  open_output, delete_all
#   A17 the flat 5..8 guard ................. the C5 omission block, start
#   A18 the 996 / 998 split ................. _key_guard
#   A19 fn-read-next not key-guarded ........ _key_guard
#   A20 dead else in aa060 .................. the C5 omission block. The
#       branch [common/acas029.cbl:L477-L481] is unreachable because the guard
#       at [common/acas029.cbl:L239-L253] already rejected File-Key-No not = 1
#       for fn-start with 998, and it carries the maintainer's own note
#       "changed for acas029 others ?" [common/acas029.cbl:L479] recording
#       that he changed this handler and not its siblings.
#   A21 description-key comment, no such field  aa045 row in section 2
#   A22 "OPEN SL OTM5 File" in a PL handler .. HANDLER_OPEN_FILE_KEY
#   A23 four sales-terminology leaks ........ section 5 above
#   A24 "TESING data" typo, in BOTH files ... compose_key, compose_batch
#   A25 missing period after the KEY move ... load_host_variables
#   A26 two ifs closed by period, no end-if . the C5 omission block. At
#       [common/acas029.cbl:L336-L338] the `if fs-reply not = zero` is closed
#       by the period on its `move 999`, so the following `go to` is
#       UNCONDITIONAL; at [common/acas029.cbl:L377-L378] the same shape recurs.
#       Every other branch in the file uses `end-if`, so the file contradicts
#       its own scope-terminator convention twice.
#   A27 end-rewrite with no period .......... aa090 row in section 2. The
#       `end-rewrite` at [common/acas029.cbl:L514] carries no terminating
#       period, so it and the following `perform aa041-Move-Inv-Data`
#       [common/acas029.cbl:L515] are one sentence - the third punctuation
#       inconsistency in this one program, after the two at A26.
#   A28 load / unload / column: three orders  load_host_variables,
#                                             unload_host_variables
#   A29 initialize plain vs "with filler" ... unload_host_variables
#   A30 four dead declarations .............. KEY_TYPE, and section 3 above
#   A31 live stop "Cobol File EOF" .......... the C5 omission block
#   A32 credentials latched once, order drift  record_size_gate, dispatch
#   A33 the 901 record-size fatal ........... record_size_gate
#   A34 codes 32 / 33 unpublished ........... dispatch's else branch
#   A35 every numeric renders as MAGNITUDE .. mysql_edit and the renderers
#   A36 the status pair is NOT reset ........ _bridge_initialise, close,
#                                             delete
#   A37 the bridge escapes NOTHING .......... the binding decision above
#                                             (the ONE anomaly deliberately
#                                             NOT reproduced, with its
#                                             justification stated in full)
#   A38 the bridge dropped the key guard .... _key_guard
#   A39 PL908 names a different field ....... record_size_gate
#   A40 "Length" then "length" .............. record_size_gate
#   A41 start always writes (21, 0) ......... start
#   A42 the INVOICE-RECORD log literal ...... read_next
#   A43 EOF returns WE-Error 10, not zero ... read_next
#   A44 WE-Error is never set on write ...... write
#   A45 the handler never logs on the RDB path  dispatch, _process_logs
#   A46 the flat close verb logs twice ...... the dispatch header block
#   A47 the RDB branch lives in a section
#       named for the flat path ............. the dispatch header block
#   A48 rg01 and "header & lines" comments
#       on a single no-RG table ............. section 3 above
#   A49 the shared cursor helper carries
#       glpostingMT's read-indexed codes;
#       otm5MT contradicts BOTH halves -
#       23 not 21 [common/otm5MT.cbl:L692]
#       and WE-Error ZEROED [:L693] where
#       glpostingMT leaves it [:L634] ....... read_indexed
#   A50 the relation map's `when 9` arm
#       [common/otm5MT.cbl:L794-L795] is
#       unreachable, guarded out at [:L765],
#       while [:L263] still advertises `<=`.. start
#
# ---------------------------------------------------------------------------
# 7. CORRECTION INDEX - the working specification versus the frozen source
# ---------------------------------------------------------------------------
# Rule R-6 makes compiled behaviour the tie-breaker, so where the working
# specification and the frozen source disagree, the source wins and the
# disagreement is recorded rather than silently resolved. Eight such
# disagreements were measured while writing this module:
#
#   C1  [common/acas029.cbl] line numbers drift by one to two lines in the
#       working note. Every locator in this file was read from the frozen
#       source; all 557 of them were range-validated against the cited file.
#                                                 -> module docstring, C1
#   C2  the access-type 5..8 guard is NOT flat-file-only. The bridge carries
#       its own on the RDB path [common/otm5MT.cbl:L765-L769], returning
#       (99, 997) - a different pair from the handler's 998
#       [common/acas029.cbl:L441-L442].           -> start, A17, A50
#   C3  function codes 32 and 33 are dead in the HANDLER
#       [common/acas029.cbl:L277-L295] but LIVE in the bridge, which
#       dispatches both [common/otm5MT.cbl:L425-L428].
#                                                 -> dispatch, A34
#   C4  the three-field SQL-diagnostic clearing [common/acas029.cbl:L275] is
#       never reached on this path; ba010-Initialise covers six fields plus
#       SQL-State [common/otm5MT.cbl:L387].       -> record_size_gate, A36
#   C5  the handler's flat verbs aa020..aa100 are never reached on the RDB
#       path, proven by the maintainer's own banner
#       [common/acas029.cbl:L269-L271].           -> the omission block
#   C6  "PERFORM THRU occurs only seven times" counts the twelve posting
#       programs only; otm5MT alone carries fifteen live THRU statements over
#       [copybooks/mysql-procedures.cpy].         -> section 4 above
#   C7  the cursor block is off by one at BOTH ends: 01 DAL-Data. is at
#       [common/otm5MT.cbl:L262], MOST-Relation at [:L263], the three
#       Most-Cursor-Set fields at L264/L267/L270 with their 88s through
#       [:L272]; L273 is a bare comment.          -> start, A9
#   C8  the function-code vocabulary is cited past end-of-file:
#       [copybooks/wsfnctn.cob] is 117 lines, so L118 does not exist.
#       File-Function is [:L88-L105], Access-Type [:L107-L116].
#                                                 -> start
# ===========================================================================
