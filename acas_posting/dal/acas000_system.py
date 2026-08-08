"""`acas000` - the System file handler and the four bridges it reaches.

The one handler in the cycle that is not a single-table module: it dispatches on
`File-Key-No` 1 through 4 to four different bridges and four different tables -
`systemMT`/`SYSTEM-REC`, `dfltMT`/`SYSDEFLT-REC`, `finalMT`/`SYSFINAL-REC` and
`sys4MT`/`SYSTOT-REC`. The dispatch is reproduced rather than flattened into four
modules, because flattening it would lose the routing the COBOL performs.

`SYSTEM-REC` is also the carrier by which the six connection parameters reach the
data-access layer [common/acas008.cbl:L558-L563], which is why a real run must
load them before any handler opens anything.

Each bridge's load paragraph initialises its host-variable group before moving
fields in, so an unset field becomes zero or space rather than SQL NULL - which is
why every column in the frozen schema can be declared NOT NULL and why this layer
defaults rather than omits.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from types import MappingProxyType
from typing import Any, Final, Union, cast

from acas_posting.dal.connection import (
    OpenOutcome,
    TransportSecurity,
    acquire_cursor,
    cobol_string_delimited_by_space,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
    transport_category,
)
from acas_posting.dal.cursor_state import (
    SEQUENTIAL_READ_START,
    CursorOutcome,
    CursorSlot,
    CursorStateTable,
    key_of_reference,
    read_next,
)
from acas_posting.dal.status import (
    FILE_KEY_NO_DOCUMENTED_RANGE,
    FILE_KEY_NO_GUARD_RANGE,
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    DbErrorStatus,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    log_file_handler_record,
    mysql_1100_db_error,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.system_dflt import SysDefaultRecord
from acas_posting.records.system_final import SysFinalRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.system_record_4 import SystemRecord4
from acas_posting.records.test_data_flags import AcasDalCommonData

_LOG: Final = logging.getLogger(__name__)

#: The one buffer of anomaly N9, as a type. In the compiled handler this is a single
#: `01`-level item [common/acas000.cbl:L311] that four bridges each reinterpret.
SystemFileRecord = Union[
    SystemRecord,
    SysDefaultRecord,
    SysFinalRecord,
    SystemRecord4,
]


__all__: Final[tuple[str, ...]] = (
    "BRIDGES_BY_FILE_KEY_NO",
    "BridgeProfile",
    "ColumnPlan",
    "DFLT_MT",
    "FILE_KEY_NO_RANGES_AS_DOCUMENTED",
    "FINAL_MT",
    "HANDLER_PROGRAM",
    "HandlerState",
    "LOG_FILE_NO_FLAT_FILE_PATH",
    "LOG_FILE_NO_RDB_PATH",
    "NEVER_LOADED_HOST_VARIABLES",
    "NEVER_UNLOADED_HOST_VARIABLES",
    "OCCURS_LOOP_BOUNDS",
    "OCCURS_SUBSCRIPT_PRIMARY_KEYS",
    "PUBLISHED_VERBS",
    "RDBMS_STORE_SELECTOR",
    "RECORD_TYPE_BY_FILE_KEY_NO",
    "RelativeFileStoreNotMigratedError",
    "SYSTEM_MT",
    "SYSTEM_REC_ROUTES",
    "SYS4_MT",
    "SYSTOT_REC_ROUTES",
    "SystemFileRecord",
    "TABLES_BY_FILE_KEY_NO",
    "WS_FILE_KEY_WIDTH",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa050_process_read_indexed",
    "aa070_process_write",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_exit",
    "aa_main_exit",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba_process_rdbms",
    "ba_rdbms_exit",
    "ca_process_logs",
    "column_plans_for",
    "configure_transport",
    "dflt_mt",
    "dispatch",
    "final_mt",
    "handler_state",
    "key_range_guard_applies",
    "reset_handler_state",
    "sys4_mt",
    "system_mt",
)


HANDLER_PROGRAM: Final[str] = "acas000 (3.3.01)"

LOG_SYSTEM: Final[LogSystem] = LogSystem.PARAMS

#: `move 10 to WS-Log-File-No.` [common/acas000.cbl:L325] - what the relative-file path
#: is left with, because it enters the size-check section BELOW the overwrite. Anomaly
#: N-log.
LOG_FILE_NO_FLAT_FILE_PATH: Final[int] = 10

#: `move 20 to WS-Log-File-no.` [common/acas000.cbl:L521] - what the RDB path is left
#: with, because `perform ba-Process-RDBMS` [common/acas000.cbl:L353] enters the section
#: AT that statement. Anomaly N-log.
LOG_FILE_NO_RDB_PATH: Final[int] = 20

RDBMS_STORE_SELECTOR: Final[str] = "66"

WS_FILE_KEY_WIDTH: Final[int] = 64

#: `05 File-Key-No pic 9.` [copybooks/wsfnctn.cob:L46] - ONE digit, which is why `string
#: "Read Indexed " File-Key-No` contributes a single character and why 5 is the largest
#: value the field can hold beyond the four the handler documents.
FILE_KEY_NO_DIGITS: Final[int] = 1

#: The three function codes `aa010-main`'s key-range guard covers, and ONLY these three
#: [common/acas000.cbl:L333-L341]. Anomaly N8.
KEY_RANGE_GUARDED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.RE_WRITE),
    }
)

PARAGRAPH_NO_OPEN: Final[int] = 201
PARAGRAPH_NO_CLOSE: Final[int] = 202
PARAGRAPH_NO_READ_INDEXED: Final[int] = 204
PARAGRAPH_NO_WRITE: Final[int] = 206
PARAGRAPH_NO_REWRITE: Final[int] = 208

BRIDGE_PARAGRAPH_NO_OPEN: Final[int] = 1
BRIDGE_PARAGRAPH_NO_CLOSE: Final[int] = 2
BRIDGE_PARAGRAPH_NO_POSITION: Final[int] = 3
BRIDGE_PARAGRAPH_NO_FETCH: Final[int] = 4
BRIDGE_PARAGRAPH_NO_WRITE: Final[int] = 10
BRIDGE_PARAGRAPH_NO_REWRITE: Final[int] = 17

OCCURS_TABLE_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "SYSDEFLT-REC": ("def_group",),
        "SYSFINAL-REC": ("ar1",),
    }
)

WE_ERROR_FILE_ALREADY_OPEN: Final[int] = 941
FS_REPLY_FILE_ALREADY_OPEN: Final[int] = 41

#: `move 10 to WE-Error` on every end-of-data path in all four bridges
#: [common/systemMT.cbl:L905, :L919, common/dfltMT.cbl:L519, :L561, :L577,
#: common/finalMT.cbl:L515, :L549, :L565, common/sys4MT.cbl:L550, :L599, :L613].
FILE_KEY_NO_RANGES_AS_DOCUMENTED: Final[Mapping[str, tuple[int, int]]] = (
    MappingProxyType(
        {
            "copybooks/wsfnctn.cob:L42-L43": FILE_KEY_NO_DOCUMENTED_RANGE,
            "common/acas000.cbl:L330-L332": (1, 4),
            "common/acas000.cbl:L185": (1, 4),
            "common/acas000.cbl:L335": FILE_KEY_NO_GUARD_RANGE,
        }
    )
)

FS_REPLY_OPEN_INPUT_FAILED: Final[int] = 35

#: `move 1024 ...` is not in the source.
SYSTEM_RECORD_DECLARED_LENGTH: Final[int] = 1024

PUBLISHED_VERBS: Final[Mapping[str, tuple[FileFunction, AccessType | int]]] = (
    MappingProxyType(
        {
            "System-Open": (FileFunction.OPEN, AccessType.I_O),
            "System-Open-Input": (FileFunction.OPEN, AccessType.INPUT),
            "System-Open-Output": (FileFunction.OPEN, AccessType.OUTPUT),
            "System-Close": (FileFunction.CLOSE, 0),
            "System-Read-Indexed": (FileFunction.READ_INDEXED, 0),
            "System-Write": (FileFunction.WRITE, 0),
            "System-ReWrite": (FileFunction.RE_WRITE, 0),
        }
    )
)

#: The three functions the key-range guard covers, and ONLY those three
#: [common/acas000.cbl:L333-L335]. ANOMALY N8.
FILE_KEY_NO_GUARDED_FUNCTIONS: Final[frozenset[FileFunction]] = frozenset(
    {
        FileFunction.READ_INDEXED,
        FileFunction.WRITE,
        FileFunction.RE_WRITE,
    }
)

#: `File-Key-No` to table, from the handler's own comment [common/acas000.cbl:L330-L332]
#: plus the fifth arm [common/acas000.cbl:L595-L599], which aliases the first. Anomaly
#: N7.
TABLES_BY_FILE_KEY_NO: Final[Mapping[int, str]] = MappingProxyType(
    {
        1: "SYSTEM-REC",
        2: "SYSDEFLT-REC",
        3: "SYSFINAL-REC",
        4: "SYSTOT-REC",
        5: "SYSTEM-REC",
    }
)

#: The record layout each arm's buffer is to be read as. Key 5 repeats key 1 because it
#: calls the same bridge with the same record.
RECORD_TYPE_BY_FILE_KEY_NO: Final[Mapping[int, type]] = MappingProxyType(
    {
        1: SystemRecord,
        2: SysDefaultRecord,
        3: SysFinalRecord,
        4: SystemRecord4,
        5: SystemRecord,
    }
)

OCCURS_SUBSCRIPT_PRIMARY_KEYS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "SYSDEFLT-REC": "[common/dfltMT.cbl:L612]",
        "SYSFINAL-REC": "[common/finalMT.cbl:L613]",
    }
)

#: How far each bridge's own loops actually run. ANOMALY N-occurs33.
OCCURS_LOOP_BOUNDS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "SYSDEFLT-REC": 32,
        "SYSFINAL-REC": 26,
    }
)

#: ANOMALY N-hvload. Five `systemMT` host variables that neither `bb000-HV-Load`
#: [common/systemMT.cbl:L1061-L1240] nor `bb100-UnloadHVs`
#: [common/systemMT.cbl:L1245-L1298] mentions. Value is the declaration locator.
NEVER_LOADED_HOST_VARIABLES: Final[Mapping[str, Mapping[str, str]]] = (
    MappingProxyType(
        {
            "SYSTEM-REC": MappingProxyType(
                {
                    "COMPANY-EMAIL": "[common/systemMT.cbl:L346]",
                    "STATS-DATE-PERIOD": "[common/systemMT.cbl:L373]",
                    "PL-AUTOGEN": "[common/systemMT.cbl:L418]",
                    "PL-NEXT-REC": "[common/systemMT.cbl:L419]",
                    "PL-APPROP-AC6": "[common/systemMT.cbl:L490]",
                }
            ),
        }
    )
)

#: ANOMALY N-key1. Columns fetched from the database whose host variable is never moved
#: back into the record.
NEVER_UNLOADED_HOST_VARIABLES: Final[Mapping[str, Mapping[str, str]]] = (
    MappingProxyType(
        {
            "SYSTEM-REC": MappingProxyType(
                {"SYSTEM-REC-KEY": "[common/systemMT.cbl:L1255]"}
            ),
            "SYSTOT-REC": MappingProxyType(
                {"LEDGER-TOTALS-REC-KEY": "[common/sys4MT.cbl:L794-L822]"}
            ),
        }
    )
)


class RelativeFileStoreNotMigratedError(RuntimeError):
    """The relative-file store the other branch uses is out of scope.

    NOT A PLACEHOLDER AND NOT DEFERRED WORK. The compiled handler supports two stores
    and selects between them at run time [common/acas000.cbl:L352]; only the RDBMS
    selection is within the migration.
    """


@dataclass(slots=True)
class HandlerState:
    """``acas000``'s ``WORKING-STORAGE``, which outlives a single ``CALL``.

    A COBOL program without ``IS INITIAL`` keeps its ``WORKING-STORAGE`` between calls
    for the life of the run, and this handler depends on that in two places: the first-
    call sentinel ``A`` [common/acas000.cbl:L525] and the open/closed flag ``Cobol-File-
    Status`` [common/acas000.cbl:L273-L274].

    Attributes:
        cobol_file_status: ``77 Cobol-File-Status pic 9 value zero.``
            [common/acas000.cbl:L273], with ``88 Cobol-File-Eof value 1``
            [:L274]. Zero means the relative file is closed, 1 that it is open.
        a: ``77 A pic 9(4) value zero.`` [common/acas000.cbl:L270], the
            first-call sentinel and the length of the linkage record. Anomaly
            N-ab: the changelog at [common/acas000.cbl:L156] claims these
            became ``pic 999``; the declaration says otherwise and governs.
        b: ``77 B pic 9(4) value zero.`` [common/acas000.cbl:L271], the length
            of the FILE SECTION record [copybooks/fdsys.cob].
        connection: The one open database connection. The compiled bridges keep
            theirs in the C interface's own static storage, shared by all four,
            which is why there is one here and not one per bridge - and why
            there is no pool (rule R-3).
        cursors: The stored-result state the four bridges' positioning and
            fetching walk, owned by ``dal/cursor_state.py``.
        transport: The transport policy :func:`configure_transport` last set.
            NO COBOL COUNTERPART: the frozen source has no transport concept at
            all, it just connects. ``dal/connection.py`` refuses to cross a
            network in clear text, so the policy has to arrive from somewhere;
            it arrives here rather than as a fifth parameter on
            :func:`dispatch`, because the linkage list is four items and adding
            to it would break the diff a reader diffing the two needs.
        system_record: The last ``SystemRecord`` a caller passed. NO
            DIRECT COBOL COUNTERPART, and the reason is worth stating.
            ``ba012-Test-WS-Rec-Size-2`` loads the six connection
            parameters from ``RDBMS-DB-Name in System-Record`` and its
            five siblings [common/acas000.cbl:L557-L562] - and
            ``System-Record`` there is the FILE SECTION record
            [copybooks/fdsys.cob], NOT the linkage buffer, as its own
            comment says: "Load up the DB settings from the system
            record from COBOL file as its not passed on"
            [common/acas000.cbl:L554]. Anomaly N-fdcreds. The relative
            file that record is read from is out of scope, so the
            credentials have to come from the linkage buffer on the
            calls where it IS a ``SystemRecord`` - keys 1 and 5 - and be
            latched for the rest of the run, which is exactly the
            first-call-only behaviour ``ba012``'s ``if A = zero`` guard
            [common/acas000.cbl:L525] and
            :func:`load_rdb_data_once`'s anomaly A-1 already have.
        mysql_count_rows: ``WS-MYSQL-Count-Rows``, one per bridge, because
            each bridge gets its own copy of the procedure copybook that
            declares it [copybooks/mysql-procedures.cpy]. It is NOT part
            of any shared block, and it outlives a statement: the frozen
            fetch paragraphs test it long after the command that set it
            [common/systemMT.cbl:L908, common/dfltMT.cbl:L571,
            common/finalMT.cbl:L559, common/sys4MT.cbl:L604], which is
            what makes the EOF2 branch reachable at all - see
            :func:`_ba040_process_read_next` for the analysis.
        allow_frozen_placeholder_credentials: Whether an open may proceed with
            the placeholder credentials the copybook ships as ``VALUE`` clauses
            [copybooks/wssystem.cob:L137-L139]. Also no COBOL counterpart, for
            the same reason. ``None`` - the default - declares nothing and defers
            to the one policy
            :func:`acas_posting.dal.connection.set_connection_policy` installed.
    """

    cobol_file_status: int = 0
    a: int = 0
    b: int = 0
    connection: Any | None = None
    cursors: CursorStateTable = field(default_factory=CursorStateTable)
    transport: TransportSecurity | None = None
    allow_frozen_placeholder_credentials: bool | None = None
    mysql_count_rows: dict[str, int] = field(default_factory=dict)
    system_record: SystemRecord | None = None

    @property
    def cobol_file_eof(self) -> bool:
        """``88 Cobol-File-Eof value 1.`` [common/acas000.cbl:L274].

        The condition name is spelled "Eof" but the paragraph that tests it tests
        whether the file is OPEN [common/acas000.cbl:L395], and the paragraph that sets
        it sets it after a successful open [common/acas000.cbl:L431].

        Returns:
            ``True`` when ``Cobol-File-Status`` is 1.
        """
        return self.cobol_file_status == 1


_STATE: Final[HandlerState] = HandlerState()


def handler_state() -> HandlerState:
    """Return this run's ``WORKING-STORAGE``.

    Returns:
        The one :class:`HandlerState` for the process, so that a caller or a test can
            observe ``A``, ``Cobol-File-Status`` and the connection the way a COBOL
            debugger would.
    """
    return _STATE


def reset_handler_state() -> None:
    """Clear the handler's ``WORKING-STORAGE`` back to its ``VALUE`` clauses.

    THERE IS NO COBOL COUNTERPART, and that is stated rather than disguised: nothing in
    [common/acas000.cbl] clears ``A`` or ``Cobol-File-Status``, because a COBOL run is a
    process and both die with it.
    """
    if _STATE.connection is not None:
        mysql_1980_close(_STATE.connection)
        mysql_1999_exit()
    _STATE.cobol_file_status = 0
    _STATE.a = 0
    _STATE.b = 0
    _STATE.connection = None
    _STATE.cursors = CursorStateTable()
    _STATE.transport = None
    _STATE.allow_frozen_placeholder_credentials = None
    _LOG.debug("acas000 WORKING-STORAGE reset; A and Cobol-File-Status zeroed")


def configure_transport(
    transport: TransportSecurity | None,
    *,
    allow_frozen_placeholder_credentials: bool | None = None,
) -> None:
    """Set the transport policy the next open will use.

    NO COBOL COUNTERPART - see :class:`HandlerState`. It is a separate function rather
    than a parameter on :func:`dispatch` because the linkage list is four items
    [common/acas000.cbl:L309-L315] and a reader diffing the argument lists must find
    four on both sides.

    Args:
        transport: The policy to hand :func:`~acas_posting.dal.connection
            .mysql_1000_open`, or ``None`` - the ordinary case - to defer to the
            ONE policy the deployment installed with
            :func:`acas_posting.dal.connection.set_connection_policy`.
        allow_frozen_placeholder_credentials: Whether the placeholder
            credentials the copybook ships [copybooks/wssystem.cob:L137-L139]
            may be used to connect. ``None`` defers to that same policy.
    """
    _STATE.transport = transport
    _STATE.allow_frozen_placeholder_credentials = (
        allow_frozen_placeholder_credentials
    )


@dataclass(frozen=True, slots=True)
class BridgeProfile:
    """One bridge program's measured behaviour, as data not as a branch.

    The four bridges share one shape and diverge at thirteen measured points, each
    recorded below by the member that carries it, with its locator.

    Attributes:
        program, source, table: Its ``program-id``, path and MySQL table.
        file_key_no: The ``File-Key-No`` that reaches it; five also reaches ``systemMT``
            and this records the first arm [common/acas000.cbl:L595-L599].
        record_type: The layout the shared buffer must hold.
        open_tag, close_tag: The `WS-File-Key` tag each verb moves.
        open_tag_set_before_open: Divergence 13. ``sys4MT`` sets it BEFORE the open, so
            a failed open leaves it set [common/sys4MT.cbl:L456-L459].
        low_key_is_quoted: Divergence 2. Bare in ``systemMT``, quoted in the other
            three [common/systemMT.cbl:L670].
        positioned_tag: Divergence 3. ``">000"`` for ``systemMT``, ``"000"`` otherwise
            [common/systemMT.cbl:L697].
        errno_test_width: Divergence 4. One character in ``systemMT``, three otherwise
            [common/systemMT.cbl:L708].
        captures_sqlstate: Divergence 5. ``systemMT`` only [common/systemMT.cbl:L706].
        duplicate_test_includes_sqlstate: Divergence 6. ``systemMT`` only
            [common/systemMT.cbl:L959].
        free_paragraph_no: Divergence 7. 18 in ``systemMT``, 20 otherwise
            [common/systemMT.cbl:L1037].
        closes_log_on_close: Divergence 8. ``systemMT`` [common/systemMT.cbl:L1052].
        guards_on_incoming_status: Divergence 9. ``sys4MT`` only, three sites
            [common/sys4MT.cbl:L538-L541].
        duplicate_check_is_live: Divergence 10. Commented out in ``dfltMT``
            [common/dfltMT.cbl:L616-L632].
        clears_error_after_logging: Divergence 11. ``finalMT`` only
            [common/finalMT.cbl:L629-L633].
        rewrite_loop_exits_on_mismatch: Divergence 12a. ``dfltMT``
            [common/dfltMT.cbl:L699].
        rewrite_paragraph_no_inside_loop: Divergence 12b. Inside the loop in ``dfltMT``
            [common/dfltMT.cbl:L660], before it in ``finalMT``.
        rewrite_key_is_literal_one: The rewrite predicate names a bare ``"1"`` in
            ``sys4MT`` and ``systemMT``, the subscript otherwise
            [common/sys4MT.cbl:L688].
        has_hv_load_section: Divergence 1. ``dfltMT`` and ``finalMT`` have none and
            move their host variables inline.
        occurs_bound: How far its loops run; ``None`` for the two single-row bridges.
            Anomaly N-occurs33 lives here.
        clears_status_after_read_loop: Anomaly N-eofclear. ``dfltMT`` and ``finalMT``
            zero the status after the loop, discarding the end of file it set
            [common/dfltMT.cbl:L589].
        clears_record_on_end_of_data: Whether ``ba040``'s end-of-data branch blanks it.
        write_exits_via_ba999_end: Whether write and rewrite exit through the logging
            paragraph. ``systemMT`` alone does [common/systemMT.cbl:L971, :L1021].
        hv_group_locator: Where the host-variable group is declared.
    """

    program: str
    source: str
    table: str
    file_key_no: int
    record_type: type
    open_tag: str
    close_tag: str
    open_tag_set_before_open: bool
    low_key_is_quoted: bool
    positioned_tag: str
    errno_test_width: int
    captures_sqlstate: bool
    duplicate_test_includes_sqlstate: bool
    free_paragraph_no: int
    closes_log_on_close: bool
    guards_on_incoming_status: bool
    duplicate_check_is_live: bool
    clears_error_after_logging: bool
    rewrite_loop_exits_on_mismatch: bool
    rewrite_paragraph_no_inside_loop: bool
    rewrite_key_is_literal_one: bool
    has_hv_load_section: bool
    occurs_bound: int | None
    clears_status_after_read_loop: bool
    hv_group_locator: str
    write_exits_via_ba999_end: bool
    clears_record_on_end_of_data: bool

    def at(self, line: str) -> str:
        """Build a locator into this bridge's own source.

        Args:
            line: The line or span, such as ``"L940"`` or ``"L950-L965"``.

        Returns:
            A ``[<path>:<line>]`` locator in the form every other citation in this
                package uses.
        """
        return f"[{self.source}:{line}]"


SYSTEM_MT: Final[BridgeProfile] = BridgeProfile(
    program="systemMT",
    source="common/systemMT.cbl",
    table="SYSTEM-REC",
    file_key_no=1,
    record_type=SystemRecord,
    open_tag="OPEN SYSTEM",
    close_tag="CLOSE SYSTEM",
    open_tag_set_before_open=False,
    low_key_is_quoted=False,
    positioned_tag=">000",
    errno_test_width=1,
    captures_sqlstate=True,
    duplicate_test_includes_sqlstate=True,
    free_paragraph_no=18,
    closes_log_on_close=True,
    guards_on_incoming_status=False,
    duplicate_check_is_live=True,
    clears_error_after_logging=False,
    rewrite_loop_exits_on_mismatch=False,
    rewrite_paragraph_no_inside_loop=False,
    rewrite_key_is_literal_one=True,
    has_hv_load_section=True,
    occurs_bound=None,
    clears_status_after_read_loop=False,
    hv_group_locator="[common/systemMT.cbl:L323-L492]",
    clears_record_on_end_of_data=False,
    write_exits_via_ba999_end=True,
)

DFLT_MT: Final[BridgeProfile] = BridgeProfile(
    program="dfltMT",
    source="common/dfltMT.cbl",
    table="SYSDEFLT-REC",
    file_key_no=2,
    record_type=SysDefaultRecord,
    open_tag="OPEN DEFAULT",
    close_tag="CLOSE DEFAULT",
    open_tag_set_before_open=False,
    low_key_is_quoted=True,
    positioned_tag="000",
    errno_test_width=3,
    captures_sqlstate=False,
    duplicate_test_includes_sqlstate=False,
    free_paragraph_no=20,
    closes_log_on_close=False,
    guards_on_incoming_status=False,
    duplicate_check_is_live=False,
    clears_error_after_logging=False,
    rewrite_loop_exits_on_mismatch=True,
    rewrite_paragraph_no_inside_loop=True,
    rewrite_key_is_literal_one=False,
    has_hv_load_section=False,
    occurs_bound=32,  # ANOMALY N-occurs33 [common/dfltMT.cbl:L532]
    clears_status_after_read_loop=True,
    hv_group_locator="[common/dfltMT.cbl:L315-L319]",
    clears_record_on_end_of_data=False,
    write_exits_via_ba999_end=False,
)

FINAL_MT: Final[BridgeProfile] = BridgeProfile(
    program="finalMT",
    source="common/finalMT.cbl",
    table="SYSFINAL-REC",
    file_key_no=3,
    record_type=SysFinalRecord,
    open_tag="OPEN FINAL",
    close_tag="CLOSE FINAL",
    open_tag_set_before_open=False,
    low_key_is_quoted=True,
    positioned_tag="000",
    errno_test_width=3,
    captures_sqlstate=False,
    duplicate_test_includes_sqlstate=False,
    free_paragraph_no=20,
    closes_log_on_close=False,
    guards_on_incoming_status=False,
    duplicate_check_is_live=True,
    clears_error_after_logging=True,
    rewrite_loop_exits_on_mismatch=False,
    rewrite_paragraph_no_inside_loop=False,
    rewrite_key_is_literal_one=False,
    has_hv_load_section=False,
    occurs_bound=26,
    clears_status_after_read_loop=True,
    hv_group_locator="[common/finalMT.cbl:L313-L315]",
    clears_record_on_end_of_data=False,
    write_exits_via_ba999_end=False,
)

#: ``sys4MT`` for the 21-column ``SYSTOT-REC``. Host-variable group ``01 TD-SYSTOT-
#: REC.`` [common/sys4MT.cbl:L314-L335], whose twenty money items are SIGNED - which is
#: what makes anomaly N-sign visible here.
SYS4_MT: Final[BridgeProfile] = BridgeProfile(
    program="sys4MT",
    source="common/sys4MT.cbl",
    table="SYSTOT-REC",
    file_key_no=4,
    record_type=SystemRecord4,
    open_tag="OPEN SYS4",
    close_tag="CLOSE SYS4",
    open_tag_set_before_open=True,
    low_key_is_quoted=True,
    positioned_tag="000",
    errno_test_width=3,
    captures_sqlstate=False,
    duplicate_test_includes_sqlstate=False,
    free_paragraph_no=20,
    closes_log_on_close=False,
    guards_on_incoming_status=True,
    duplicate_check_is_live=True,
    clears_error_after_logging=False,
    rewrite_loop_exits_on_mismatch=False,
    rewrite_paragraph_no_inside_loop=False,
    rewrite_key_is_literal_one=True,
    has_hv_load_section=True,
    occurs_bound=None,
    clears_status_after_read_loop=False,
    hv_group_locator="[common/sys4MT.cbl:L314-L335]",
    clears_record_on_end_of_data=True,
    write_exits_via_ba999_end=False,
)

BRIDGES_BY_FILE_KEY_NO: Final[Mapping[int, BridgeProfile]] = MappingProxyType(
    {
        1: SYSTEM_MT,
        2: DFLT_MT,
        3: FINAL_MT,
        4: SYS4_MT,
        5: SYSTEM_MT,
    }
)


@dataclass(frozen=True, slots=True)
class ColumnPlan:
    """One column of one table, with everything needed to read and write it.

    Built from the generated dictionary, never transcribed by eye - Agent Action Plan
    section 0.8.1 makes that a directive, not a preference: "Data dictionary first.

    Attributes:
        key: The dictionary key, in ``<TABLE-NAME>.<COLUMN-NAME>`` form.
        column: The MySQL column name, hyphens and all.
        ordinal: Its 1-based position in the frozen table definition, which is also the
            order the bridge's own statement builders and its ``MySQL_fetch_record``
            argument list use - verified, not assumed.
        quoted: The column name already backtick-quoted, because every identifier in
            this schema contains a hyphen and an unquoted one is a syntax error.
        storage: ``DECIMAL``, ``INT``, ``STR`` or ``NONE`` from the dictionary.
        hv_usage: The host variable's own usage, ``COMP`` for every numeric item in
            these four groups and ``ALPHANUMERIC`` for every character one.
        scale: The host variable's declared scale, so a value can be coerced into it
            without consulting anything else.
        integer_digits: The host variable's integer digit count, which is also the width
            of the substring the bridge's statement builder takes.
        character_length: The declared width for a character column.
        host_variable: The host variable's name, for the anomaly registers.
        signed_host_variable: Whether the host variable itself is signed. Note that this
            does NOT mean a negative value survives.
        route: The attribute path from the record to the value, or ``None`` when the
            bridge derives the column instead of moving it.
        derivation: The dictionary's derivation record, present exactly for the columns
            no copybook declares and for the group and redefines alternatives.
        drift_details: The dictionary's own sentences about how the copybook, the host
            variable and the column disagree.
        loads_from_record: Whether the bridge moves the record into this host variable
            at all.
        unloads_to_record: Whether the bridge moves this host variable back into the
            record after a fetch.
        derivation_guard: The dictionary's record of the condition the bridge wraps the
            move in, or ``None``.
        copybook_signed: Whether the COPYBOOK field is signed, or ``None`` for the four
            columns no copybook declares.
        copybook_locator: Where the copybook declares the field, or ``None``.
        citation: ``loader.cite`` output - the three sources in one line.
    """

    key: str
    column: str
    ordinal: int
    quoted: str
    storage: str
    hv_usage: str
    scale: int
    integer_digits: int
    character_length: int
    host_variable: str
    signed_host_variable: bool
    route: tuple[str, ...] | None
    derivation: str | None
    drift_details: tuple[str, ...]
    loads_from_record: bool
    unloads_to_record: bool
    derivation_guard: str | None
    copybook_signed: bool | None
    copybook_locator: str | None
    citation: str

    @property
    def is_numeric(self) -> bool:
        """Whether this column carries a number rather than characters.

        Returns:
            ``True`` when the host variable is a numeric item.
        """
        return self.hv_usage != "ALPHANUMERIC"


#: ``bb000-HV-Load``'s move list for ``SYSTEM-REC``, one entry per COBOL ``move``
#: [common/systemMT.cbl:L1061-L1243].
SYSTEM_REC_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "SYSTEM-RECORD-VERSION-PRIME": (
            "system_data_block",
            "system_record_version_prime",
        ),
        "SYSTEM-RECORD-VERSION-SECONDAR": (
            "system_data_block",
            "system_record_version_secondary",
        ),
        "VAT-RATE-1": ("system_data_block", "vat_rates", "vat_rate_1"),
        "VAT-RATE-2": ("system_data_block", "vat_rates", "vat_rate_2"),
        "VAT-RATE-3": ("system_data_block", "vat_rates", "vat_rate_3"),
        "VAT-RATE-4": ("system_data_block", "vat_rates", "vat_rate_4"),
        "VAT-RATE-5": ("system_data_block", "vat_rates", "vat_rate_5"),
        "CYCLEA": ("system_data_block", "cyclea"),
        "PERIOD": ("system_data_block", "period"),
        "PAGE-LINES": ("system_data_block", "page_lines"),
        "NEXT-INVOICE": ("system_data_block", "next_invoice"),
        "RUN-DAT": ("system_data_block", "run_date"),
        "START-DAT": ("system_data_block", "start_date"),
        "END-DAT": ("system_data_block", "end_date"),
        "USER-CODE": ("system_data_block", "user_code"),
        "ADDRESS-1": ("system_data_block", "address_1"),
        "ADDRESS-2": ("system_data_block", "address_2"),
        "ADDRESS-3": ("system_data_block", "address_3"),
        "ADDRESS-4": ("system_data_block", "address_4"),
        "POST-CODE": ("system_data_block", "post_code"),
        "COMPANY-EMAIL": ("system_data_block", "company_email"),
        "COUNTRY": ("system_data_block", "country"),
        "PRINT-SPOOL-NAME": ("system_data_block", "print_spool_name"),
        "PASS-VALUE": ("system_data_block", "pass_value"),
        "LEVEL-1": ("system_data_block", "level", "level_1"),
        "LEVEL-2": ("system_data_block", "level", "level_2"),
        "LEVEL-3": ("system_data_block", "level", "level_3"),
        "LEVEL-4": ("system_data_block", "level", "level_4"),
        "LEVEL-5": ("system_data_block", "level", "level_5"),
        "LEVEL-6": ("system_data_block", "level", "level_6"),
        "PASS-WORD": ("system_data_block", "pass_word"),
        "HOST": ("system_data_block", "host"),
        "OP-SYSTEM": ("system_data_block", "op_system"),
        "CURRENT-QUARTER": ("system_data_block", "current_quarter"),
        "FILE-SYSTEM-USED": (
            "system_data_block",
            "rdbms_flat_statuses",
            "file_system_used",
        ),
        "FILE-DUPLICATES-IN-USE": (
            "system_data_block",
            "rdbms_flat_statuses",
            "file_duplicates_in_use",
        ),
        "DATE-FORM": ("system_data_block", "date_form"),
        "DATA-CAPTURE-USED": ("system_data_block", "data_capture_used"),
        "RDBMS-DB-NAME": ("system_data_block", "rdbms_db_name"),
        "RDBMS-USER": ("system_data_block", "rdbms_user"),
        "RDBMS-PASSWD": ("system_data_block", "rdbms_passwd"),
        "RDBMS-PORT": ("system_data_block", "rdbms_port"),
        "RDBMS-HOST": ("system_data_block", "rdbms_host"),
        "RDBMS-SOCKET": ("system_data_block", "rdbms_socket"),
        "VAT-REG-NUMBER": ("system_data_block", "vat_reg_number"),
        "PARAM-RESTRICT": ("system_data_block", "param_restrict"),
        "STATS-DATE-PERIOD": ("system_data_block", "stats_date_period"),
        "P-C": ("general_ledger_block", "p_c"),
        "P-C-GROUPED": ("general_ledger_block", "p_c_grouped"),
        "P-C-LEVEL": ("general_ledger_block", "p_c_level"),
        "COMPS": ("general_ledger_block", "comps"),
        "COMPS-ACTIVE": ("general_ledger_block", "comps_active"),
        "M-V": ("general_ledger_block", "m_v"),
        "ARCH": ("general_ledger_block", "arch"),
        "TRANS-PRINT": ("general_ledger_block", "trans_print"),
        "TRANS-PRINTED": ("general_ledger_block", "trans_printed"),
        "HEADER-LEVEL": ("general_ledger_block", "header_level"),
        "SALES-RANGE": ("general_ledger_block", "sales_range"),
        "PURCHASE-RANGE": ("general_ledger_block", "purchase_range"),
        "VAT": ("general_ledger_block", "vat"),
        "BATCH-ID": ("general_ledger_block", "batch_id"),
        "LEDGER-2ND-INDEX": ("general_ledger_block", "ledger_2nd_index"),
        "IRS-INSTEAD": ("general_ledger_block", "irs_instead"),
        "LEDGER-SEC": ("general_ledger_block", "ledger_sec"),
        "UPDATES": ("general_ledger_block", "updates"),
        "POSTINGS": ("general_ledger_block", "postings"),
        "NEXT-BATCH": ("general_ledger_block", "next_batch"),
        "EXTRA-CHARGE-AC": ("general_ledger_block", "extra_charge_ac"),
        "VAT-AC": ("general_ledger_block", "vat_ac"),
        "PRINT-SPOOL-NAME2": ("general_ledger_block", "print_spool_name2"),
        "NEXT-FOLIO": ("purchase_ledger_block", "next_folio"),
        "BL-PAY-AC": ("purchase_ledger_block", "bl_pay_ac"),
        "P-CREDITORS": ("purchase_ledger_block", "p_creditors"),
        "BL-PURCH-AC": ("purchase_ledger_block", "bl_purch_ac"),
        "GL-BL-PAY-AC": ("sales_ledger_block", "gl_bl_pay_ac"),
        "GL-P-CREDITORS": ("sales_ledger_block", "gl_p_creditors"),
        "GL-BL-PURCH-AC": ("sales_ledger_block", "gl_bl_purch_ac"),
        "GL-SL-PAY-AC": ("sales_ledger_block", "gl_sl_pay_ac"),
        "GL-S-DEBTORS": ("sales_ledger_block", "gl_s_debtors"),
        "GL-SL-SALES-AC": ("sales_ledger_block", "gl_sl_sales_ac"),
        "BL-END-CYCLE-DAT": ("purchase_ledger_block", "bl_end_cycle_date"),
        "BL-NEXT-BATCH": ("purchase_ledger_block", "bl_next_batch"),
        "AGE-TO-PAY": ("purchase_ledger_block", "age_to_pay"),
        "PURCHASE-LEDGER": ("purchase_ledger_block", "purchase_ledger"),
        "PL-DELIM": ("purchase_ledger_block", "pl_delim"),
        "ENTRY-LEVEL": ("purchase_ledger_block", "entry_level"),
        "P-FLAG-A": ("purchase_ledger_block", "p_flag_a"),
        "P-FLAG-I": ("purchase_ledger_block", "p_flag_i"),
        "P-FLAG-P": ("purchase_ledger_block", "p_flag_p"),
        "PL-STOCK-LINK": ("purchase_ledger_block", "pl_stock_link"),
        "PRINT-SPOOL-NAME3": ("purchase_ledger_block", "print_spool_name3"),
        "PL-AUTOGEN": ("purchase_ledger_block", "pl_autogen"),
        "PL-NEXT-REC": ("purchase_ledger_block", "pl_next_rec"),
        "SALES-LEDGER": ("sales_ledger_block", "sales_ledger"),
        "SL-DELIM": ("sales_ledger_block", "sl_delim"),
        "OI-3-FLAG": ("sales_ledger_block", "oi_3_flag"),
        "CUST-FLAG": ("sales_ledger_block", "cust_flag"),
        "OI-5-FLAG": ("sales_ledger_block", "oi_5_flag"),
        "S-FLAG-OI-3": ("sales_ledger_block", "s_flag_oi_3"),
        "FULL-INVOICING": ("sales_ledger_block", "full_invoicing"),
        "S-FLAG-A": ("sales_ledger_block", "s_flag_a"),
        "S-FLAG-I": ("sales_ledger_block", "s_flag_i"),
        "S-FLAG-P": ("sales_ledger_block", "s_flag_p"),
        "SL-DUNNING": ("sales_ledger_block", "sl_dunning"),
        "SL-CHARGES": ("sales_ledger_block", "sl_charges"),
        "SL-OWN-NOS": ("sales_ledger_block", "sl_own_nos"),
        "SL-STATS-RUN": ("sales_ledger_block", "sl_stats_run"),
        "SL-DAY-BOOK": ("sales_ledger_block", "sl_day_book"),
        "INVOICER": ("sales_ledger_block", "invoicer"),
        "EXTRA-DESC": ("sales_ledger_block", "extra_desc"),
        "EXTRA-TYPE": ("sales_ledger_block", "extra_type"),
        "EXTRA-PRINT": ("sales_ledger_block", "extra_print"),
        "SL-STOCK-LINK": ("sales_ledger_block", "sl_stock_link"),
        "SL-STOCK-AUDIT": ("sales_ledger_block", "sl_stock_audit"),
        "SL-LATE-PER": ("sales_ledger_block", "sl_late_per"),
        "SL-DISC": ("sales_ledger_block", "sl_disc"),
        "EXTRA-RATE": ("sales_ledger_block", "extra_rate"),
        "SL-DAYS-1": ("sales_ledger_block", "sl_days_1"),
        "SL-DAYS-2": ("sales_ledger_block", "sl_days_2"),
        "SL-DAYS-3": ("sales_ledger_block", "sl_days_3"),
        "SL-CREDIT": ("sales_ledger_block", "sl_credit"),
        "SL-MIN": ("sales_ledger_block", "sl_min"),
        "SL-MAX": ("sales_ledger_block", "sl_max"),
        "PF-RETENTION": ("sales_ledger_block", "pf_retention"),
        "FIRST-SL-BATCH": ("sales_ledger_block", "first_sl_batch"),
        "FIRST-SL-INV": ("sales_ledger_block", "first_sl_inv"),
        "SL-LIMIT": ("sales_ledger_block", "sl_limit"),
        "SL-PAY-AC": ("sales_ledger_block", "sl_pay_ac"),
        "S-DEBTORS": ("sales_ledger_block", "s_debtors"),
        "SL-SALES-AC": ("sales_ledger_block", "sl_sales_ac"),
        "S-END-CYCLE-DAT": ("sales_ledger_block", "s_end_cycle_date"),
        "SL-COMP-HEAD-PICK": ("sales_ledger_block", "sl_comp_head_pick"),
        "SL-COMP-HEAD-INV": ("sales_ledger_block", "sl_comp_head_inv"),
        "SL-COMP-HEAD-STAT": ("sales_ledger_block", "sl_comp_head_stat"),
        "SL-COMP-HEAD-LETS": ("sales_ledger_block", "sl_comp_head_lets"),
        "SL-VAT-PRINTED": ("sales_ledger_block", "sl_vat_printed"),
        "SL-INVOICE-LINES": ("sales_ledger_block", "sl_invoice_lines"),
        "SL-AUTOGEN": ("sales_ledger_block", "sl_autogen"),
        "SL-NEXT-REC": ("sales_ledger_block", "sl_next_rec"),
        "STK-ABREV-REF": ("stock_control_block", "stk_abrev_ref"),
        "STK-DEBUG": ("stock_control_block", "stk_debug"),
        "STK-MANU-USED": ("stock_control_block", "stk_manu_used"),
        "STK-OE-USED": ("stock_control_block", "stk_oe_used"),
        "STK-AUDIT-USED": ("stock_control_block", "stk_audit_used"),
        "STK-MOV-AUDIT": ("stock_control_block", "stk_mov_audit"),
        "STK-PERIOD-CUR": ("stock_control_block", "stk_period_cur"),
        "STK-PERIOD-DAT": ("stock_control_block", "stk_period_dat"),
        "STOCK-CONTROL": ("stock_control_block", "stock_control"),
        "STK-AVERAGING": ("stock_control_block", "stk_averaging"),
        "STK-ACTIVITY-REP-RUN": (
            "stock_control_block",
            "stk_activity_rep_run",
        ),
        "STK-PAGE-LINES": ("stock_control_block", "stk_page_lines"),
        "STK-AUDIT-NO": ("stock_control_block", "stk_audit_no"),
        "CLIENT": ("irs_entry_block", "client"),
        "NEXT-POST": ("irs_entry_block", "next_post"),
        "VAT1": ("irs_entry_block", "vat_rates2", "vat1"),
        "VAT2": ("irs_entry_block", "vat_rates2", "vat2"),
        "VAT3": ("irs_entry_block", "vat_rates2", "vat3"),
        "IRS-PASS-VALUE": ("irs_entry_block", "irs_pass_value"),
        "SAVE-SEQU": ("irs_entry_block", "save_sequ"),
        "SYSTEM-WORK-GROUP": ("irs_entry_block", "system_work_group"),
        "PL-APP-CREATED": ("irs_entry_block", "pl_app_created"),
        "PL-APPROP-AC": ("irs_entry_block", "filler_323", "pl_approp_ac"),
        "1ST-TIME-FLAG": ("irs_entry_block", "first_time_flag"),
        "PL-APPROP-AC6": ("irs_entry_block", "pl_approp_ac6"),
        "SL-BO-FLAG": ("sales_ledger_block", "sl_bo_flag"),
        "STK-BO-ACTIVE": ("stock_control_block", "stk_bo_active"),
    }
)

SYSTOT_REC_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "SL-OS-BAL-LAST-MONTH": ("sales_ledger_data", "sl_os_bal_last_month"),
        "SL-OS-BAL-THIS-MONTH": ("sales_ledger_data", "sl_os_bal_this_month"),
        "SL-INVOICES-THIS-MONTH": (
            "sales_ledger_data",
            "sl_invoices_this_month",
        ),
        "SL-CREDIT-NOTES-THIS-MONTH": (
            "sales_ledger_data",
            "sl_credit_notes_this_month",
        ),
        "SL-VARIANCE": ("sales_ledger_data", "sl_variance"),
        "SL-CREDIT-DEDUCTIONS": ("sales_ledger_data", "sl_credit_deductions"),
        "SL-CN-UNAPPL-THIS-MONTH": (
            "sales_ledger_data",
            "sl_cn_unappl_this_month",
        ),
        "SL-PAYMENTS": ("sales_ledger_data", "sl_payments"),
        "SL4-SPARE1": ("sales_ledger_data", "sl4_spare1"),
        "SL4-SPARE2": ("sales_ledger_data", "sl4_spare2"),
        "PL-OS-BAL-LAST-MONTH": (
            "purchase_ledger_data",
            "pl_os_bal_last_month",
        ),
        "PL-OS-BAL-THIS-MONTH": (
            "purchase_ledger_data",
            "pl_os_bal_this_month",
        ),
        "PL-INVOICES-THIS-MONTH": (
            "purchase_ledger_data",
            "pl_invoices_this_month",
        ),
        "PL-CREDIT-NOTES-THIS-MONTH": (
            "purchase_ledger_data",
            "pl_credit_notes_this_month",
        ),
        "PL-VARIANCE": ("purchase_ledger_data", "pl_variance"),
        "PL-CREDIT-DEDUCTIONS": (
            "purchase_ledger_data",
            "pl_credit_deductions",
        ),
        "PL-CN-UNAPPL-THIS-MONTH": (
            "purchase_ledger_data",
            "pl_cn_unappl_this_month",
        ),
        "PL-PAYMENTS": ("purchase_ledger_data", "pl_payments"),
        "SL4-SPARE3": ("purchase_ledger_data", "sl4_spare3"),
        "SL4-SPARE4": ("purchase_ledger_data", "sl4_spare4"),
    }
)

#: ``ba070-Process-Write``'s move list for ``SYSDEFLT-REC``
#: [common/dfltMT.cbl:L606-L614].
SYSDEFLT_REC_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "DEF-ACS": ("def_acs",),
        "DEF-CODES": ("def_codes",),
        "DEF-VAT": ("def_vat",),
    }
)

#: ``ba070-Process-Write``'s move list for ``SYSFINAL-REC``
#: [common/finalMT.cbl:L613-L614].
SYSFINAL_REC_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "AR1": (),
    }
)

ROUTES_BY_TABLE: Final[Mapping[str, Mapping[str, tuple[str, ...]]]] = (
    MappingProxyType(
        {
            "SYSTEM-REC": SYSTEM_REC_ROUTES,
            "SYSDEFLT-REC": SYSDEFLT_REC_ROUTES,
            "SYSFINAL-REC": SYSFINAL_REC_ROUTES,
            "SYSTOT-REC": SYSTOT_REC_ROUTES,
        }
    )
)

#: The three ``SYSTEM-REC`` columns ``bb000-HV-Load`` does NOT load with a plain move,
#: and what it does instead.
SYSTEM_REC_SPECIAL_LOADS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "SYSTEM-REC-KEY": "common/systemMT.cbl:L1070",
        "SUSER": "common/systemMT.cbl:L1085",
        "MAPS-SER": "common/systemMT.cbl:L1107-L1112",
    }
)

#: ``SUSER`` is a one-item group, so the group move reaches exactly one field.
SUSER_ROUTE: Final[tuple[str, ...]] = ("system_data_block", "suser", "usera")

MAPS_SER_ROUTE: Final[tuple[str, ...]] = ("system_data_block", "maps_ser")

MAPS_SER_NN_DIGITS: Final[int] = 4

#: The two columns whose value the bridge invents rather than moves, and the literal it
#: uses.
LITERAL_ONE_PRIMARY_KEYS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "SYSTEM-REC": "common/systemMT.cbl:L1070",
        "SYSTOT-REC": "common/sys4MT.cbl:L769",
    }
)

_COLUMN_PLAN_CACHE: dict[str, tuple[ColumnPlan, ...]] = {}


def column_plans_for(table: str) -> tuple[ColumnPlan, ...]:
    """Build (and cache) the column plan for one of the four tables.

    Args:
        table: One of ``SYSTEM-REC``, ``SYSDEFLT-REC``, ``SYSFINAL-REC`` or ``SYSTOT-
            REC``.

    Returns:
        One :class:`ColumnPlan` per column, in ordinal order.

    Raises:
        KeyError: If ``table`` is not one of this handler's four tables, or if the
            dictionary has an entry for it with no bridge host variable - which would
            mean the generated dictionary and this module have drifted apart and must be
            reconciled before anything is written.
    """
    cached = _COLUMN_PLAN_CACHE.get(table)
    if cached is not None:
        return cached
    routes = ROUTES_BY_TABLE[table]
    plans: list[ColumnPlan] = []
    for entry in loader.entries_for_table(table):
        host_variable = entry.bridge_host_variable
        if host_variable is None:
            raise KeyError(
                f"{entry.key}: the dictionary records no bridge host "
                "variable, so this module cannot know how the bridge "
                "converts it. Regenerate the dictionary before writing."
            )
        column = entry.column
        short_name = entry.key.split(".", 1)[1]
        derivation = entry.derivation
        copybook_field = entry.copybook
        plans.append(
            ColumnPlan(
                key=entry.key,
                column=column.name,
                ordinal=column.ordinal,
                quoted=quote_identifier(column.name),
                storage=entry.cobol_python_storage.value,
                hv_usage=host_variable.usage.value,
                scale=host_variable.scale or 0,
                integer_digits=host_variable.integer_digits or 0,
                character_length=host_variable.character_length or 0,
                host_variable=host_variable.name,
                signed_host_variable=bool(host_variable.signed),
                route=routes.get(short_name),
                derivation=(
                    None if derivation is None else derivation.expression
                ),
                drift_details=tuple(entry.drift.details),
                loads_from_record=bool(host_variable.loaded_from_record),
                unloads_to_record=bool(host_variable.unloaded_to_record),
                derivation_guard=(
                    None if derivation is None else derivation.guard
                ),
                copybook_signed=(
                    None
                    if copybook_field is None
                    else bool(copybook_field.signed)
                ),
                copybook_locator=(
                    None if copybook_field is None else copybook_field.source
                ),
                citation=loader.cite(entry.key),
            )
        )
    built = tuple(plans)
    _COLUMN_PLAN_CACHE[table] = built
    return built


def _route_value(record: object, route: Sequence[str]) -> Any:
    """Follow an attribute route from a record down to one value.

    Args:
        record: The record, or the ``OCCURS`` element for the two table-shaped layouts.
        route: The attribute names to follow. An empty route means the record argument
            IS the value, which is how ``SYSFINAL-REC.AR1`` reaches its ``pic x(16)``
            table element.

    Returns:
        The value the COBOL ``move`` would have taken as its sending field.
    """
    value: Any = record
    for attribute in route:
        value = getattr(value, attribute)
    return value


def _assign_route(record: object, route: Sequence[str], value: Any) -> None:
    """Store one value back through an attribute route.

    Reproduces the receiving half of a ``bb100-UnloadHVs`` move. An empty route cannot
    be assigned through - the two table-shaped layouts rebuild their tuple instead - so
    it is rejected loudly rather than silently dropped.

    Args:
        record: The record to store into.
        route: The attribute names to follow; the last one is assigned.
        value: The value to store.

    Raises:
        ValueError: If ``route`` is empty.
    """
    if not route:
        raise ValueError(
            "an empty route has no attribute to assign; the caller must "
            "rebuild the OCCURS tuple itself"
        )
    target: Any = record
    for attribute in route[:-1]:
        target = getattr(target, attribute)
    setattr(target, route[-1], value)


# Nothing in this section is business logic and nothing in it is inferred from a picture
# clause by reasoning.


def _blank_like(value: Any) -> Any:
    """Return the ``INITIALIZE ... WITH FILLER`` value for one elementary item.

    Args:
        value: The current value, which carries the item's declared shape.

    Returns:
        Spaces of the same length for a character item, a zero of the same scale for a
            decimal item, ``0`` for an integer item, and the value unchanged for
            anything this module does not model.
    """
    if isinstance(value, str):
        return " " * len(value)
    if isinstance(value, Decimal):
        return Decimal(0).quantize(value)
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return 0
    return value


def _initialize_with_filler(record: Any) -> None:
    """Reproduce ``INITIALIZE <record> WITH FILLER`` in place.

    ``dfltMT`` and ``finalMT`` clear BEFORE their read loop, so a partial sweep leaves
    the untouched entries blank rather than stale. ``systemMT`` and ``sys4MT`` clear
    inside ``bb100-UnloadHVs`` and, separately, on their end of file paths.

    Args:
        record: A record dataclass, or any nested group or ``OCCURS`` element of one.
    """
    for descriptor in dataclasses.fields(record):
        current = getattr(record, descriptor.name)
        if dataclasses.is_dataclass(current) and not isinstance(current, type):
            _initialize_with_filler(current)
            continue
        if isinstance(current, tuple):
            rebuilt: list[Any] = []
            for element in current:
                if dataclasses.is_dataclass(element) and not isinstance(
                    element, type
                ):
                    _initialize_with_filler(element)
                    rebuilt.append(element)
                else:
                    rebuilt.append(_blank_like(element))
            setattr(record, descriptor.name, tuple(rebuilt))
            continue
        setattr(record, descriptor.name, _blank_like(current))


def _zoned_display_digits(text: str) -> int:
    """Read a ``pic 9(n)`` DISPLAY item's digits the way the runtime does.

    A zoned decimal digit is the low four bits of the byte, so a space (0x20) reads as
    zero and a letter reads as its low nibble.

    Args:
        text: The characters occupying the digit positions.

    Returns:
        The integer the runtime would see.
    """
    total = 0
    for character in text:
        total = total * 10 + (ord(character) & 0x0F)
    return total


def _truncate_toward_zero(value: Decimal, scale: int) -> Decimal:
    """Store a value into a field of ``scale`` decimal places, unrounded.

    Args:
        value: The sending value.
        scale: The receiving field's decimal places.

    Returns:
        The value with its excess decimal places discarded.
    """
    return value.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_DOWN)


def _high_order_truncate(value: Decimal, integer_digits: int) -> Decimal:
    """Discard integer digits that do not fit the receiving field.

    COBOL drops high-order digits silently on an oversized store; there is no size error
    unless ``ON SIZE ERROR`` is written, and none of these bridges writes one.

    Args:
        value: The sending value, already at the receiving scale.
        integer_digits: How many integer digit positions the receiver has.

    Returns:
        The value with any excess high-order digits removed, sign preserved.
    """
    if integer_digits <= 0:
        return value
    limit = Decimal(10) ** integer_digits
    magnitude = value.copy_abs()
    if magnitude < limit:
        return value
    kept = magnitude % limit
    return -kept if value.is_signed() else kept


def _as_decimal(value: Any) -> Decimal:
    """Read any modelled record value as an exact decimal.

    Deliberately never accepts a binary approximation of a real number: Agent Action
    Plan section 0.7.2 R-2 forbids one at every point, "not in computation, not in
    storage, not in transport".

    Args:
        value: A :class:`~decimal.Decimal`, an :class:`int`, or the characters of a
            DISPLAY item.

    Returns:
        The exact value.

    Raises:
        TypeError: If the value is of a type this module does not model, which can only
            mean a record field was assigned something the copybook does not describe.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(int(value))
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(_zoned_display_digits(value.strip() or "0"))
    raise TypeError(
        f"{type(value).__name__} is not a modelled COBOL value; a record "
        "field holds something no copybook declares"
    )


def _host_variable_value(plan: ColumnPlan, value: Any) -> Decimal | int | str:
    """Reproduce one ``move <record field> to HV-<column>``.

    Args:
        plan: The column's plan, which carries the host variable's declared picture
            straight from the generated dictionary.
        value: The sending field's value.

    Returns:
        The value as the host variable would hold it: a left-justified, space-padded
            string of the declared width for a character item.
    """
    if not plan.is_numeric:
        text = value if isinstance(value, str) else str(value)
        width = plan.character_length
        if width <= 0:
            return text
        return text[:width].ljust(width)
    number = _as_decimal(value)
    number = _truncate_toward_zero(number, plan.scale)
    if not plan.signed_host_variable:
        number = number.copy_abs()
    number = _high_order_truncate(number, plan.integer_digits)
    if plan.scale == 0:
        return int(number)
    return number


def _bound_parameter(
    plan: ColumnPlan, host_value: Decimal | int | str
) -> Decimal | int | str:
    """Turn a host variable into the value the bridge's statement carries.

    ANOMALY N-sign, reproduced here and nowhere else. The bridges build their statement
    text by MOVEing the host variable into ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)``
    [common/systemMT.cbl:L260, common/sys4MT.cbl:L250] and then taking substrings of it.
    That edited field is thirty characters.

    Args:
        plan: The column's plan.
        host_value: The value the host variable holds.

    Returns:
        The bound parameter. For a numeric column, the ABSOLUTE value, because the
            bridge's own text carries no sign.
    """
    if not plan.is_numeric:
        text = host_value if isinstance(host_value, str) else str(host_value)
        return text.rstrip(" ")
    if isinstance(host_value, str):
        return host_value
    return abs(host_value)


def _move_into(current: Any, value: Any, *, signed: bool | None) -> Any:
    """Reproduce one ``move HV-<column> to <record field>``.

    The receiving field's shape is read from the value already in it, which is exact
    here because every bridge issues ``INITIALIZE ...

    Args:
        current: The value in the receiving field, carrying its shape.
        value: The sending value.
        signed: Whether the RECEIVING copybook field is signed, or ``None`` when no
            copybook declares it. An unsigned receiver takes the absolute value,
            measured.

    Returns:
        The value as the receiving field would hold it.
    """
    if isinstance(current, str):
        text = value if isinstance(value, str) else str(value)
        width = len(current)
        return text[:width].ljust(width) if width else text
    if isinstance(current, Decimal):
        number = _as_decimal(value)
        if signed is False:
            number = number.copy_abs()
        return number.quantize(current, rounding=ROUND_DOWN)
    if isinstance(current, int) and not isinstance(current, bool):
        number = _truncate_toward_zero(_as_decimal(value), 0)
        if signed is False:
            number = number.copy_abs()
        return int(number)
    return value


def _pack_maps_ser(group: Any) -> str:
    """Pack ``Maps-Ser`` into the six characters ``HV-MAPS-SER`` carries.

    The work group is ``ws-maps-xx pic xx`` followed by ``ws-maps-nn pic 9(4)``
    [common/systemMT.cbl:L252-L254], so the numeric half is rendered zero-padded to four
    digits and an oversized value loses its high-order digits.

    Args:
        group: The record's ``Maps-Ser`` group.

    Returns:
        Exactly six characters.
    """
    prefix = str(group.maps_ser_xx)[:2].ljust(2)
    number = _high_order_truncate(
        _as_decimal(group.maps_ser_nn).copy_abs(), MAPS_SER_NN_DIGITS
    )
    return prefix + str(int(number)).rjust(MAPS_SER_NN_DIGITS, "0")


def _unpack_maps_ser(text: str, group: Any) -> None:
    """Unpack ``HV-MAPS-SER``'s six characters back into ``Maps-Ser``.

    Args:
        text: The host variable's six characters.
        group: The record's ``Maps-Ser`` group, mutated in place.
    """
    padded = str(text)[:6].ljust(6)
    group.maps_ser_xx = padded[:2]
    group.maps_ser_nn = _zoned_display_digits(padded[2:6])


def _fa_rdbms_flat_statuses_text(file_access: FileAccess) -> str:
    """Read ``FA-RDBMS-Flat-Statuses`` as the two characters the handler tests.

    and ``aa010-main`` compares the GROUP against the two-character literal ``"66"``
    [common/acas000.cbl:L352], which is a group comparison and so alphanumeric. So the
    selector is set by putting 6 in BOTH digits.

    Args:
        file_access: The caller's block.

    Returns:
        The two characters, in the group's declared order.
    """
    group = file_access.fa_rdbms_flat_statuses
    return (
        f"{int(group.fa_file_system_used) % 10}"
        f"{int(group.fa_file_duplicates_in_use) % 10}"
    )


def _ws_file_key_move(text: str) -> str:
    """Reproduce ``move <value> to WS-File-Key``.

    Args:
        text: The sending value, already rendered.

    Returns:
        Exactly ``WS_FILE_KEY_WIDTH`` characters.
    """
    return text[:WS_FILE_KEY_WIDTH].ljust(WS_FILE_KEY_WIDTH)


def _string_into_ws_file_key(existing: str, *parts: str) -> str:
    """Reproduce ``string <parts> into WS-File-Key``.

    MEASURED, and it is not the same as a MOVE: ``STRING`` overlays from the pointer and
    leaves whatever the field already held beyond the last character it wrote.

    Args:
        existing: The field's current sixty-four characters.
        *parts: The sending items, each contributing its full size, which is what
            ``STRING`` does when no ``DELIMITED BY`` is written.

    Returns:
        Exactly ``WS_FILE_KEY_WIDTH`` characters.
    """
    overlay = "".join(parts)
    base = existing[:WS_FILE_KEY_WIDTH].ljust(WS_FILE_KEY_WIDTH)
    joined = overlay + base[len(overlay):]
    return joined[:WS_FILE_KEY_WIDTH]


# All four bridges have the same nine-paragraph skeleton, so the skeleton is written
# once and every place they differ is read out of the bridge's own BridgeProfile.

WS_LOG_WHERE_WIDTH: Final[int] = 231

WE_ERROR_BRIDGE_BAD_FUNCTION: Final[int] = WeError.UNKNOWN_UNEXPECTED

#: The three ``WS-File-Key`` tags a read loop leaves on its three distinct end
#: conditions. Each is a plain ``move``, so the field is fully replaced.
READ_END_TAGS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "end_of_table": "EOF",
        "key_out_of_bound": "EOF3",
        "driver_failure": "EOF2",
        "no_rows": "No Data",
    }
)


def ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs`` - hand the shared blocks to the logger.

    [common/acas000.cbl:L608-L613], and the identically named paragraph at the
    foot of each of the four bridges [common/systemMT.cbl:L1062 region,
    common/dfltMT.cbl:L889, common/finalMT.cbl:L823, common/sys4MT.cbl:L1583],
    all of which are one statement::

        call     "fhlogger" using File-Access
                                  ACAS-DAL-Common-data.

    ``common/fhlogger.cbl`` is out of scope - Agent Action Plan section 0.2.2
    lists it under "Non-posting utilities" - and it writes to a log FILE, not
    to a table, so it has no database effect. Agent Action Plan section 0.3.4
    therefore governs: "Diagnostic displays with no database effect become log
    records at a severity matching the original's intent. They must not alter
    control flow and must not appear in any table dump." This function does
    exactly that and nothing else.

    ONE ADAPTER FOR ALL SEVENTEEN HANDLER MODULES. The record is composed by
    :func:`acas_posting.dal.status.log_file_handler_record`, not here, so the
    field set, the level and the counter arithmetic are the same in every handler
    instead of being twenty independent readings of the same one-line paragraph.
    That function's docstring records which three of ``Logging-Data``'s eleven
    fields are deliberately withheld - ``WS-File-Key``, ``WS-Log-Where`` and
    ``SQL-Msg`` - and why: the first is the record key of a business entity, and
    the other two are free text this layer cannot reason about.

    ``Log-File-Rec-Written`` [copybooks/Test-Data-Flags.cob:L18] IS NOW ADVANCED,
    and its omission here was a defect rather than a decision. ``fhlogger`` owns
    the counter and is out of scope, but the counter itself lives in
    ``ACAS-DAL-Common-data``, which this function is handed and which the caller
    keeps - so leaving it untouched made the shared block diverge from what the
    frozen run would hold. The adapter advances it by one modulo
    :data:`~acas_posting.dal.status.FH_LOG_REC_MODULUS`, which is the wrap its
    ``pic 9(6)`` imposes.

    Args:
        file_access: The shared ``File-Access`` block, read only.
        dal_common: The shared flags block. ``SW-Testing`` decides whether the
            caller performs this paragraph at all, which is why this function
            does not test it again - the COBOL tests it at each call site. Its
            ``Log-File-Rec-Written`` field is advanced by the adapter.
    """
    logging_data = file_access.logging_data
    log_file_handler_record(
        _LOG,
        program="acas000",
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=file_access.file_function,
        access_type=file_access.access_type,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=dal_common,
    )


def _testing_1(dal_common: AcasDalCommonData) -> bool:
    """Evaluate the ``Testing-1`` condition name.

    ``SW-Testing`` is ``pic 9 value 1`` [copybooks/Test-Data-Flags.cob:L10] and
    ``Testing-1`` is its ``88`` for the value 1. The frozen source ships it ON, which is
    preserved by the record module's default rather than quietly turned off.

    Args:
        dal_common: The shared flags block.

    Returns:
        Whether file-handler logging is on.
    """
    return dal_common.sw_testing == 1


def _ba010_initialise(
    bridge: BridgeProfile, file_access: FileAccess
) -> None:
    """``ba010-Initialise`` - clear the diagnostics, then dispatch.

    ANOMALY, RECORDED NOT REPRODUCED because it is already dead in the frozen source:
    each bridge carries its OWN key-range guard here, commented out. ``systemMT``'s
    covers read-indexed, start and delete [common/systemMT.cbl:L549-L566]; ``sys4MT``'s
    covers read-indexed only [common/sys4MT.cbl:L382-L390].

    Args:
        bridge: The bridge's profile, consulted for divergence 14.
        file_access: The shared block, mutated in place.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_where = " " * WS_LOG_WHERE_WIDTH
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    if bridge.captures_sqlstate:
        logging_data.sql_state = " " * SQL_STATE_WIDTH


def _ba020_process_open(
    bridge: BridgeProfile,
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba020-Process-Open`` - marshal the six parameters, then open.

    DIVERGENCE 13, measured: ``sys4MT`` sets its tag BEFORE the open
    [common/sys4MT.cbl:L456-L459], so a FAILED open leaves ``OPEN SYS4`` in ``WS-File-
    Key``; the other three set it after [common/systemMT.cbl:L623-L634], so a failed
    open leaves the spaces ``ba010-Initialise`` put there.

    Args:
        bridge: The bridge's profile.
        system: The system record, which is where
            :func:`~acas_posting.dal.connection.load_rdb_data_once` takes the connection
            parameters from - once per run, anomaly A-1.
        file_access: The shared block, mutated in place.
        dal_common: The shared flags block.
    """
    state = handler_state()
    rdb_data = file_access.rdb_data
    marshalled = (
        cobol_string_delimited_by_space(rdb_data.db_schema),
        cobol_string_delimited_by_space(rdb_data.db_host),
        cobol_string_delimited_by_space(rdb_data.db_uname),
        cobol_string_delimited_by_space(rdb_data.db_upass),
        cobol_string_delimited_by_space(rdb_data.db_port),
        cobol_string_delimited_by_space(rdb_data.db_socket),
    )
    #  THE ENDPOINT IS NOT NAMED, ONLY CLASSIFIED. The four fields this record
    #  used to interpolate - `DB-Schema`, `DB-Host`, `DB-Port` and `DB-Socket`
    #  [copybooks/wsfnctn.cob:L57-L62] - are the deployment's identity, and an
    #  operator needs none of it to act on a log line: it is written down in the
    #  deployment contract they configured. Printing it hands an attacker the
    #  reconnaissance half of the work for free (CWE-532) and makes the same event
    #  read differently on every deployment. `transport_category` answers the only
    #  question the record has to answer - can the credentials and the posted
    #  figures be read off the wire - with one of five fixed tokens.
    _LOG.debug(
        "%s open: transport=%s",
        bridge.program,
        transport_category({"host": marshalled[1], "unix_socket": marshalled[5]}
                           if marshalled[5] else {"host": marshalled[1]}),
    )
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_OPEN
    if bridge.open_tag_set_before_open:
        logging_data.ws_file_key = _ws_file_key_move(bridge.open_tag)
    outcome: OpenOutcome = mysql_1000_open(
        system,
        ws_no_paragraph=BRIDGE_PARAGRAPH_NO_OPEN,
        we_error=file_access.we_error,
        transport=state.transport,
        allow_frozen_placeholder_credentials=(
            state.allow_frozen_placeholder_credentials
        ),
    )
    mysql_1090_exit(outcome)
    outcome.apply_to_logging_data(logging_data)
    file_access.fs_reply = outcome.fs_reply
    file_access.we_error = outcome.we_error
    if outcome.fs_reply != FsReply.SUCCESS:
        return
    state.connection = outcome.connection
    if not bridge.open_tag_set_before_open:
        logging_data.ws_file_key = _ws_file_key_move(bridge.open_tag)
    state.cursors.reset(bridge.table)
    _LOG.info("%s opened %s", bridge.program, bridge.table)
    del dal_common


def _ba030_process_close(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba030-Process-Close`` - free any cursor, then close.

    Args:
        bridge: The bridge's profile.
        file_access: The shared block, mutated in place.
        dal_common: The shared flags block.
    """
    state = handler_state()
    if state.cursors.state_for(bridge.table).cursor_active():
        _ba998_free(bridge, file_access)
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_CLOSE
    logging_data.ws_file_key = _ws_file_key_move(bridge.close_tag)
    mysql_1980_close(state.connection)
    mysql_1999_exit()
    state.connection = None
    _LOG.info("%s closed %s", bridge.program, bridge.table)
    del dal_common


def _ba100_bad_function(file_access: FileAccess) -> None:
    """``ba100-Bad-Function`` - the bridge's own catch-all.

    Unreachable from this handler in practice, because ``aa010-main``'s own ``evaluate``
    [common/acas000.cbl:L372-L385] has already sent every function the bridges do not
    implement to ``aa100-Bad-Function`` and its ``999``. Reproduced anyway.

    Args:
        file_access: The shared block, mutated in place.
    """
    file_access.we_error = WE_ERROR_BRIDGE_BAD_FUNCTION
    file_access.fs_reply = FsReply.ERROR


def _ba998_free(bridge: BridgeProfile, file_access: FileAccess) -> None:
    """``ba998-Free`` - release the result set and forget the cursor.

    DIVERGENCE 5: ``systemMT`` numbers this paragraph 18 [common/systemMT.cbl:L1037];
    the other three number it 20 [common/dfltMT.cbl:L738, common/finalMT.cbl:L724,
    common/sys4MT.cbl:L755]. The number reaches the log record, so it is carried in the
    profile rather than hard-coded.

    Args:
        bridge: The bridge's profile, consulted for divergence 5.
        file_access: The shared block, mutated in place.
    """
    file_access.logging_data.ws_no_paragraph = bridge.free_paragraph_no
    handler_state().cursors.reset(bridge.table)


def _ba999_end(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba999-End`` - log, and for one bridge log a second time.

    Note that the second block is NOT guarded by ``Testing-1``, so a close through
    ``systemMT`` logs even with logging switched off, and it leaves ``File-Function``
    and ``Access-Type`` at zero in the caller's shared block - a side effect on data the
    caller owns, not merely a log line.

    Args:
        bridge: The bridge's profile, consulted for divergence 6.
        file_access: The shared block, mutated in place.
        dal_common: The shared flags block.
    """
    if _testing_1(dal_common):
        ca_process_logs(file_access, dal_common)
    if bridge.closes_log_on_close and (
        file_access.file_function == FileFunction.CLOSE
    ):
        file_access.file_function = 0
        file_access.access_type = 0
        ca_process_logs(file_access, dal_common)


ERRNO_NO_ERROR: Final[str] = "0  "


@dataclass(frozen=True, slots=True)
class _CommandOutcome:
    """What one ``MYSQL-1210-COMMAND`` left for its caller to test.

    The bridges never look at a return value; they test ``WS-MYSQL-COUNT-ROWS`` and
    then, only if it is not 1, ask the driver for an error number.

    Attributes:
        count_rows: ``WS-MYSQL-Count-Rows`` after the command.
        errno: What ``call "MySQL_errno"`` would return - ``"0 "`` when the driver
            reported nothing.
        message: What ``call "MySQL_error"`` would return, already safe to log.
        sql_state: What ``call "MySQL_sqlstate"`` would return. Only ``systemMT`` asks
            for it.
        statement: The statement text, for the log record.
    """

    count_rows: int
    errno: str
    message: str
    sql_state: str
    statement: str


def _initial_host_variable(plan: ColumnPlan) -> Decimal | int | str:
    """The value ``initialize TD-<TABLE>`` leaves in one host variable.

    ``bb000-HV-Load`` opens with ``initialize TD-SYSTEM-REC.``
    [common/systemMT.cbl:L1069] and ``initialize TD-SYSTOT-REC.``
    [common/sys4MT.cbl:L768]. Agent Action Plan section 0.6.2 states the consequence,
    verbatim: "an unset field becomes zero or space, never SQL ``NULL`` ...

    Args:
        plan: The column's plan.

    Returns:
        Spaces of the declared width, ``0``, or a zero at the declared scale.
    """
    if not plan.is_numeric:
        return " " * plan.character_length
    if plan.scale == 0:
        return 0
    return Decimal(0).quantize(Decimal(1).scaleb(-plan.scale))


def _bb000_hv_load(
    bridge: BridgeProfile,
    record: Any,
    *,
    subscript: int | None = None,
) -> dict[str, Decimal | int | str]:
    """``bb000-HV-Load`` - move the record into the host variables.

    [common/systemMT.cbl:L1061-L1243] and [common/sys4MT.cbl:L760-L789] for the two
    bridges that have the section; for ``dfltMT`` and ``finalMT`` this reproduces the
    inline moves their write and rewrite paragraphs make instead
    [common/dfltMT.cbl:L606-L614], [common/finalMT.cbl:L613-L614].

    Args:
        bridge: The bridge's profile.
        record: The record for the two single-row tables, or one ``OCCURS`` element for
            the two table-shaped ones.
        subscript: The one-based ``OCCURS`` subscript, for the two table-shaped tables.
            ``None`` for the other two.

    Returns:
        The host variables keyed by column name, in the frozen definition's ordinal
            order - which is also the order both statement builders and the fetch
            argument list use.

    Raises:
        ValueError: If a subscript is required and absent, or supplied and not required.
    """
    plans = column_plans_for(bridge.table)
    needs_subscript = bridge.table in OCCURS_SUBSCRIPT_PRIMARY_KEYS
    if needs_subscript and subscript is None:
        raise ValueError(
            f"{bridge.program} writes one row per OCCURS entry, so the "
            "subscript that becomes the primary key is required "
            f"{OCCURS_SUBSCRIPT_PRIMARY_KEYS[bridge.table]}"
        )
    if not needs_subscript and subscript is not None:
        raise ValueError(
            f"{bridge.program} addresses a single row and derives its key "
            "from a literal, so no subscript applies "
            f"[{LITERAL_ONE_PRIMARY_KEYS[bridge.table]}]"
        )
    # `initialize TD-<TABLE>.` - every host variable first, so an unloaded one is zero
    # or spaces rather than absent.
    host_variables: dict[str, Decimal | int | str] = {
        plan.column: _initial_host_variable(plan) for plan in plans
    }
    for plan in plans:
        short_name = plan.column
        if not plan.loads_from_record:
            # ANOMALY N-hvload [common/systemMT.cbl:L346, :L373, :L418, :L419, :L490].
            # The INITIALIZE value stands.
            continue
        if bridge.table in LITERAL_ONE_PRIMARY_KEYS and plan.route is None:
            if short_name == "SYSTEM-REC-KEY" or (
                short_name == "LEDGER-TOTALS-REC-KEY"
            ):
                host_variables[short_name] = 1
                continue
        if needs_subscript and plan.route is None:
            host_variables[short_name] = _host_variable_value(
                plan, subscript
            )
            continue
        if short_name == "SUSER":
            host_variables[short_name] = _host_variable_value(
                plan, _route_value(record, SUSER_ROUTE)
            )
            continue
        if short_name == "MAPS-SER":
            host_variables[short_name] = _host_variable_value(
                plan, _pack_maps_ser(_route_value(record, MAPS_SER_ROUTE))
            )
            continue
        route = plan.route
        if route is None:
            raise ValueError(
                f"{plan.key}: no route and no derivation this module knows "
                f"about. {plan.citation}"
            )
        value = _route_value(record, route)
        if plan.derivation_guard is not None and not isinstance(
            value, (int, Decimal)
        ):
            # The one guarded move in these four bridges: `if Def-Acs (A) numeric`
            # [common/dfltMT.cbl:L606-L607].
            continue
        host_variables[short_name] = _host_variable_value(plan, value)
    return host_variables


def _bb100_unload_hvs(
    bridge: BridgeProfile,
    record: Any,
    row: Mapping[str, Any],
    *,
    subscript: int | None = None,
) -> None:
    """``bb100-UnloadHVs`` - move the host variables back into the record.

    [common/systemMT.cbl:L1245-L1428] and [common/sys4MT.cbl:L794-L822]. Its opening
    comment states the reason every column can be ``NOT NULL``, verbatim: "NULL fields
    must not be returned in the buffer. SQL filters each column to ensure it has a
    proper value.

    Args:
        bridge: The bridge's profile.
        record: The record to store into, mutated in place.
        row: The fetched row keyed by column name.
        subscript: For the two table-shaped tables, the ``OCCURS`` position to store at
            - which the bridge takes from the KEY COLUMN's own value, not from its loop
            counter.
    """
    for plan in column_plans_for(bridge.table):
        if not plan.unloads_to_record:
            #  ANOMALY N-key1 / N-hvload.
            continue
        route = plan.route
        if plan.column == "SUSER":
            current = _route_value(record, SUSER_ROUTE)
            _assign_route(
                record,
                SUSER_ROUTE,
                _move_into(
                    current,
                    row[plan.column],
                    signed=plan.copybook_signed,
                ),
            )
            continue
        if plan.column == "MAPS-SER":
            _unpack_maps_ser(
                str(row[plan.column]), _route_value(record, MAPS_SER_ROUTE)
            )
            continue
        if route is None:
            continue
        if subscript is not None:
            # The two table-shaped layouts store through the subscript, so the tuple is
            # rebuilt rather than assigned through.
            _store_occurs_entry(bridge, record, row, subscript, plan)
            continue
        current = _route_value(record, route)
        _assign_route(
            record,
            route,
            _move_into(
                current, row[plan.column], signed=plan.copybook_signed
            ),
        )


def _store_occurs_entry(
    bridge: BridgeProfile,
    record: Any,
    row: Mapping[str, Any],
    subscript: int,
    plan: ColumnPlan,
) -> None:
    """Store one fetched column into one ``OCCURS`` entry.

    The subscript is the KEY COLUMN's value, so a row whose key does not match its
    arrival order lands where the key says, not where the loop is.

    Args:
        bridge: The bridge's profile.
        record: The record holding the table, mutated in place.
        row: The fetched row keyed by column name.
        subscript: The one-based position taken from the key column.
        plan: The column being stored.
    """
    table_attribute = (
        "ar1" if bridge.table == "SYSFINAL-REC" else "def_group"
    )
    entries = list(getattr(record, table_attribute))
    index = subscript - 1
    if not 0 <= index < len(entries):
        # Unreachable from the two bridges, which test the key against their own bound
        # first [common/finalMT.cbl:L564-L566, common/dfltMT.cbl:L551-L556].
        raise IndexError(
            f"{plan.key}: key {subscript} is outside the "
            f"{len(entries)}-entry OCCURS table"
        )
    if plan.route == ():
        entries[index] = _move_into(
            entries[index], row[plan.column], signed=plan.copybook_signed
        )
        setattr(record, table_attribute, tuple(entries))
        return
    entry = entries[index]
    current = _route_value(entry, plan.route or ())
    _assign_route(
        entry,
        plan.route or (),
        _move_into(current, row[plan.column], signed=plan.copybook_signed),
    )


#: ``A`` is ``pic 99 comp`` in the two table-shaped bridges [common/dfltMT.cbl:L301,
#: common/finalMT.cbl:L299], so ``move A to WS-File-Key`` renders TWO digits, and ``WS-
#: Key`` is ``pic 999`` [common/dfltMT.cbl:L302, common/finalMT.cbl:L300], so the
#: rewrite predicate carries three.
OCCURS_COUNTER_DIGITS: Final[int] = 2

REWRITE_KEY_DIGITS: Final[int] = 3


def _zero_filled(width: int) -> str:
    """Reproduce ``move zero to <alphanumeric item>``.

    The figurative constant ``ZERO`` moved to an alphanumeric item fills it with the
    CHARACTER zero, not with spaces.

    Args:
        width: The item's declared width.

    Returns:
        ``width`` character zeroes.
    """
    return "0" * width


def _numeric_move_text(value: int, digits: int) -> str:
    """Render a numeric sending item for a ``move`` into an alphanumeric item.

    Args:
        value: The sending value.
        digits: The sending item's declared digit count.

    Returns:
        Exactly ``digits`` characters.
    """
    return str(abs(int(value))).rjust(digits, "0")[-digits:]


def _errno_indicates_failure(bridge: BridgeProfile, errno: str) -> bool:
    """Evaluate the bridge's own test of ``WS-MYSQL-Error-Number``.

    Args:
        bridge: The bridge's profile.
        errno: The error number as the driver reported it.

    Returns:
        Whether the bridge would treat this as a failure worth recording.
    """
    if bridge.errno_test_width == 1:
        return errno[:1] != "0"
    return errno != ERRNO_NO_ERROR


def _insert_statement(bridge: BridgeProfile) -> str:
    """Build ``bb200-Insert``'s statement for one bridge.

    Two differences from the frozen text, both deliberate and neither observable in
    table state.

    Args:
        bridge: The bridge's profile.

    Returns:
        The statement, with one ``%s`` per column in ordinal order.
    """
    plans = column_plans_for(bridge.table)
    assignments = ", ".join(f"{plan.quoted}=%s" for plan in plans)
    return (
        f"INSERT INTO {quote_identifier(bridge.table)} SET "
        f"{assignments};"
    )


def _update_statement(bridge: BridgeProfile, where_clause: str) -> str:
    """Build ``bb300-Update``'s statement for one bridge.

    Note that the primary key is assigned in the ``SET`` list as well as tested in the
    ``WHERE`` - the generated builder emits every column without exception, and that
    includes the key. Preserved.

    Args:
        bridge: The bridge's profile.
        where_clause: The predicate ``ba090-Process-Rewrite`` built, already carrying
            its own ``%s``.

    Returns:
        The statement, with one ``%s`` per column in ordinal order followed by the
            predicate's own placeholder.
    """
    plans = column_plans_for(bridge.table)
    assignments = ", ".join(f"{plan.quoted}=%s" for plan in plans)
    return (
        f"UPDATE {quote_identifier(bridge.table)} SET {assignments}"
        f" WHERE {where_clause};"
    )


def _execute_command(
    bridge: BridgeProfile, statement: str, parameters: Sequence[Any]
) -> _CommandOutcome:
    """``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``.

    The frozen paragraph hands the assembled text to the client library and leaves the
    row count in ``WS-MYSQL-Count-Rows``.

    Args:
        bridge: The bridge's profile, for the log line.
        statement: The statement text.
        parameters: The values to bind, in the statement's own order.

    Returns:
        The outcome, for the caller to test.

    Raises:
        RuntimeError: If no connection is open. NO COBOL COUNTERPART: the frozen bridge
            would hand a null connection handle to the client library, whose behaviour
            is undefined.
    """
    connection = handler_state().connection
    if connection is None:
        raise RuntimeError(
            f"{bridge.program}: no connection is open. The caller must issue "
            "the System-Open verb before any other, exactly as the compiled "
            "chain does [common/systemMT.cbl:L592-L594]."
        )
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            count_rows = int(cursor.rowcount or 0)
    except Exception as error:
        status: DbErrorStatus = mysql_1100_db_error(
            errno=str(getattr(error, "errno", "") or ""),
            message=str(getattr(error, "msg", None) or error),
            sql_state=str(getattr(error, "sqlstate", "") or ""),
            command=statement,
        )
        #  NO RECORD HERE. `mysql_1100_db_error` has just emitted THE operator
        #  record for this failure - it stands in for the frozen
        #  `Mysql-1110-Report-Problem` [copybooks/mysql-procedures.cpy:L130-L137]
        #  and carries the status pair, the SQLSTATE, the error number and the
        #  stable category. A second record here reported the same three fields
        #  again, one layer up, and an operator had to correlate two lines for one
        #  fault. One failure, one record - see the safe-event schema in
        #  `dal/status.py`.
        state = handler_state()
        state.mysql_count_rows[bridge.program] = 0
        return _CommandOutcome(
            count_rows=0,
            errno=status.sql_err.strip() or ERRNO_NO_ERROR,
            message=status.sql_msg,
            sql_state=status.sql_state,
            statement=statement,
        )
    handler_state().mysql_count_rows[bridge.program] = count_rows
    return _CommandOutcome(
        count_rows=count_rows,
        errno=ERRNO_NO_ERROR,
        message=" " * SQL_MSG_WIDTH,
        sql_state=" " * SQL_STATE_WIDTH,
        statement=statement,
    )


def _bb200_insert(
    bridge: BridgeProfile, host_variables: Mapping[str, Any]
) -> _CommandOutcome:
    """``bb200-Insert`` - one row, every column, values bound.

    Args:
        bridge: The bridge's profile.
        host_variables: The host variables keyed by column name.

    Returns:
        The command outcome.
    """
    plans = column_plans_for(bridge.table)
    parameters = [
        _bound_parameter(plan, host_variables[plan.column]) for plan in plans
    ]
    return _execute_command(bridge, _insert_statement(bridge), parameters)


def _bb300_update(
    bridge: BridgeProfile,
    host_variables: Mapping[str, Any],
    where_clause: str,
    where_parameter: str,
) -> _CommandOutcome:
    """``bb300-Update`` - one row, every column, plus the predicate.

    Args:
        bridge: The bridge's profile.
        host_variables: The host variables keyed by column name.
        where_clause: The predicate text, carrying its own ``%s``.
        where_parameter: The predicate's bound value - the quoted digit string the
            frozen builder put into the text.

    Returns:
        The command outcome.
    """
    plans = column_plans_for(bridge.table)
    parameters = [
        _bound_parameter(plan, host_variables[plan.column]) for plan in plans
    ]
    parameters.append(where_parameter)
    return _execute_command(
        bridge, _update_statement(bridge, where_clause), parameters
    )


def _rewrite_predicate(
    bridge: BridgeProfile, subscript: int | None
) -> tuple[str, str]:
    """Build ``ba090-Process-Rewrite``'s ``WHERE``, and its logged text.

    ``K`` and ``L`` are loaded from the key table and then NEVER USED on this path,
    because the only surviving alternative is the literal or the subscript - the record-
    substring line that would have used them is commented out.

    Args:
        bridge: The bridge's profile.
        subscript: The ``OCCURS`` subscript for the two table-shaped bridges.

    Returns:
        The predicate carrying its ``%s``, and the value to bind.

    Raises:
        ValueError: If a subscript is needed and absent.
    """
    key = key_of_reference(bridge.table, 1)
    column = quote_identifier(key.column_name)
    if bridge.rewrite_key_is_literal_one:
        return (f"{column}=%s", "1")
    if subscript is None:
        raise ValueError(
            f"{bridge.program} rewrites by the OCCURS subscript "
            f"{OCCURS_SUBSCRIPT_PRIMARY_KEYS[bridge.table]}, so it is required"
        )
    return (
        f"{column}=%s",
        _numeric_move_text(subscript, REWRITE_KEY_DIGITS),
    )


BA999_END: Final[str] = "ba999-End"

BA999_EXIT: Final[str] = "ba999-Exit"


def _report_write_failure(
    bridge: BridgeProfile,
    file_access: FileAccess,
    outcome: _CommandOutcome,
) -> None:
    """The ``if WS-MYSQL-COUNT-ROWS not = 1`` block of ``ba070``.

    * ``WE-Error`` is NEVER set on this path, in ANY of the four bridges. A failed write
    reports through ``FS-Reply`` alone, so a caller that tests only ``WE-Error`` sees a
    clean write.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        outcome: What the command reported.
    """
    if not bridge.duplicate_check_is_live:
        return
    if outcome.count_rows == 1:
        return
    logging_data = file_access.logging_data
    if bridge.captures_sqlstate:
        # `call "MySQL_sqlstate" ...
        logging_data.sql_state = _move_into(
            logging_data.sql_state, outcome.sql_state, signed=None
        )
    if not _errno_indicates_failure(bridge, outcome.errno):
        # The mismatch is swallowed. Deliberate silence, preserved.
        return
    logging_data.sql_err = _move_into(
        logging_data.sql_err, outcome.errno, signed=None
    )
    logging_data.sql_msg = _move_into(
        logging_data.sql_msg, outcome.message, signed=None
    )
    sql_state = (
        logging_data.sql_state
        if bridge.duplicate_test_includes_sqlstate
        else ""
    )
    if is_duplicate_key_bridge_level(logging_data.sql_err, sql_state):
        file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
    else:
        file_access.fs_reply = int(FsReply.ERROR)


def _report_rewrite_failure(
    bridge: BridgeProfile,
    file_access: FileAccess,
    outcome: _CommandOutcome,
) -> bool:
    """The ``if WS-MYSQL-COUNT-ROWS not = 1`` block of ``ba090``.

    994 is ``WeError.REWRITE_SQLSTATE_NOT_00000``, whose name records what the
    maintainer's own error table says it means. The errno guard applies here too, with
    the same swallowing consequence.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        outcome: What the command reported.

    Returns:
        Whether the COUNT block was ENTERED - which is ``count_rows`` not 1, NOT whether
            a failure was reported.
    """
    if outcome.count_rows == 1:
        return False
    logging_data = file_access.logging_data
    if bridge.captures_sqlstate:
        logging_data.sql_state = _move_into(
            logging_data.sql_state, outcome.sql_state, signed=None
        )
    if not _errno_indicates_failure(bridge, outcome.errno):
        # ANOMALY NEW-19: the mismatch is swallowed, and the caller still takes the
        # count block's transfer.
        return True
    logging_data.sql_err = _move_into(
        logging_data.sql_err, outcome.errno, signed=None
    )
    logging_data.sql_msg = _move_into(
        logging_data.sql_msg, outcome.message, signed=None
    )
    file_access.fs_reply = int(FsReply.ERROR)
    file_access.we_error = int(WeError.REWRITE_SQLSTATE_NOT_00000)
    return True


def _occurs_entry_is_empty(bridge: BridgeProfile, entry: Any) -> bool:
    """The two bridges' "do not write out blank data" guards.

    Note what the guard means for table state: an occurrence the operator has genuinely
    cleared is not written, so a row that was present before a write of a cleared entry
    SURVIVES. Neither bridge issues a delete. Preserved.

    Args:
        bridge: The bridge's profile.
        entry: One ``OCCURS`` occurrence - a group for ``dfltMT``, a bare character item
            for ``finalMT``.

    Returns:
        Whether the frozen guard would skip this occurrence.
    """
    for plan in column_plans_for(bridge.table):
        if not plan.loads_from_record or plan.route is None:
            continue
        value = _route_value(entry, plan.route)
        if plan.is_numeric:
            try:
                if _as_decimal(value) != 0:
                    return False
            except ArithmeticError:
                return False
        elif str(value).strip(" ") != "":
            return False
    return True


def _log_where(clause: str, parameter: str) -> str:
    """Reproduce ``move WS-Where (1:J) to WS-Log-Where``.

    ``ba090-Process-Rewrite`` builds its predicate into ``WS-Where`` and then copies the
    used prefix into the log block [common/systemMT.cbl:L996, common/dfltMT.cbl:L668,
    common/finalMT.cbl:L668, common/sys4MT.cbl:L716].

    Args:
        clause: The predicate carrying its ``%s``.
        parameter: The value that will be bound.

    Returns:
        Exactly ``WS_LOG_WHERE_WIDTH`` characters.
    """
    rendered = clause.replace("%s", f'"{parameter}"') + " "
    return rendered[:WS_LOG_WHERE_WIDTH].ljust(WS_LOG_WHERE_WIDTH)


def _ba070_process_write(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
) -> str:
    """``ba070-Process-Write`` - insert, in each bridge's own shape.

    The two single-row bridges write ONE row and stamp ``WS-File-Key`` with the literal
    1 [common/systemMT.cbl:L942, common/sys4MT.cbl:L635], because both tables only ever
    hold row 1.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to write.

    Returns:
        The exit label reached, which decides whether ``ba999-End`` logs.
    """
    logging_data = file_access.logging_data
    if bridge.occurs_bound is None:
        host_variables = _bb000_hv_load(bridge, record)
        logging_data.ws_file_key = _ws_file_key_move("1")
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        if bridge.captures_sqlstate:
            logging_data.sql_state = _zero_filled(SQL_STATE_WIDTH)
        logging_data.sql_msg = " " * SQL_MSG_WIDTH
        logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_WRITE
        outcome = _bb200_insert(bridge, host_variables)
        if bridge.guards_on_incoming_status and (
            file_access.fs_reply != int(FsReply.SUCCESS)
            or file_access.we_error != int(WeError.SUCCESS)
        ):
            # sys4MT's 28/09/16 guard, placed AFTER the insert
            # [common/sys4MT.cbl:L640-L643]. GO TO class 3 - section exit.
            return BA999_EXIT
        _report_write_failure(bridge, file_access, outcome)
        if not bridge.write_exits_via_ba999_end:
            if _testing_1(dal_common):
                ca_process_logs(file_access, dal_common)
            return BA999_EXIT
        return BA999_END

    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_WRITE
    table = _route_value(record, OCCURS_TABLE_ROUTES[bridge.table])
    for index in range(1, bridge.occurs_bound + 1):
        entry = table[index - 1]
        if _occurs_entry_is_empty(bridge, entry):
            continue
        logging_data.ws_file_key = _ws_file_key_move(
            _numeric_move_text(index, OCCURS_COUNTER_DIGITS)
        )
        host_variables = _bb000_hv_load(bridge, entry, subscript=index)
        outcome = _bb200_insert(bridge, host_variables)
        _report_write_failure(bridge, file_access, outcome)
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)
            if bridge.clears_error_after_logging:
                file_access.fs_reply = int(FsReply.SUCCESS)
                logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
                logging_data.sql_msg = " " * SQL_MSG_WIDTH
    return BA999_EXIT


def _ba090_process_rewrite(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
) -> str:
    """``ba090-Process-Rewrite`` - update, in each bridge's own shape.

    DIVERGENCE 10: ``dfltMT`` sets the paragraph number INSIDE its loop
    [common/dfltMT.cbl:L660] while ``finalMT`` sets it once before
    [common/finalMT.cbl:L639]; the number reaches every log record, so the difference is
    observable.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to rewrite.

    Returns:
        The exit label reached.
    """
    logging_data = file_access.logging_data
    if bridge.occurs_bound is None:
        host_variables = _bb000_hv_load(bridge, record)
        logging_data.ws_file_key = _ws_file_key_move("1")
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_REWRITE
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        logging_data.sql_msg = " " * SQL_MSG_WIDTH
        logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
        if bridge.captures_sqlstate:
            logging_data.sql_state = _zero_filled(SQL_STATE_WIDTH)
        clause, parameter = _rewrite_predicate(bridge, None)
        logging_data.ws_log_where = _log_where(clause, parameter)
        outcome = _bb300_update(bridge, host_variables, clause, parameter)
        if bridge.guards_on_incoming_status and (
            file_access.fs_reply != int(FsReply.SUCCESS)
            or file_access.we_error != int(WeError.SUCCESS)
        ):
            # sys4MT's guard, again AFTER the command [common/sys4MT.cbl:L718-L721]. GO
            # TO class 3.
            return BA999_EXIT
        if _report_rewrite_failure(bridge, file_access, outcome):
            # The transfer belongs to the COUNT block, NOT to the errno test nested
            # inside it [common/systemMT.cbl:L1017, common/sys4MT.cbl:L722], so it is
            # taken whether or not a status was set - which is how ANOMALY NEW-19's
            # silent no-op rewrite ALSO skips the clear-to-zero that follows.
            if not bridge.write_exits_via_ba999_end:
                # sys4MT logs before its transfer, unconditionally inside the count
                # block [common/sys4MT.cbl:L718-L720]. DIVERGENCE 16: systemMT has no
                # log here at all, because its `ba999-End` does it
                # [common/systemMT.cbl:L1017].
                if _testing_1(dal_common):
                    ca_process_logs(file_access, dal_common)
                return BA999_EXIT
            return BA999_END
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
        logging_data.sql_msg = " " * SQL_MSG_WIDTH
        if bridge.captures_sqlstate:
            logging_data.sql_state = _zero_filled(SQL_STATE_WIDTH)
        if bridge.write_exits_via_ba999_end:
            return BA999_END
        return BA999_EXIT

    # dfltMT and finalMT. NO entry clear - ANOMALY NEW-12.
    if not bridge.rewrite_paragraph_no_inside_loop:
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_REWRITE
    table = _route_value(record, OCCURS_TABLE_ROUTES[bridge.table])
    for index in range(1, bridge.occurs_bound + 1):
        entry = table[index - 1]
        if _occurs_entry_is_empty(bridge, entry):
            continue
        logging_data.ws_file_key = _ws_file_key_move(
            _numeric_move_text(index, OCCURS_COUNTER_DIGITS)
        )
        host_variables = _bb000_hv_load(bridge, entry, subscript=index)
        if bridge.rewrite_paragraph_no_inside_loop:
            logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_REWRITE
        clause, parameter = _rewrite_predicate(bridge, index)
        logging_data.ws_log_where = _log_where(clause, parameter)
        outcome = _bb300_update(bridge, host_variables, clause, parameter)
        failed = _report_rewrite_failure(bridge, file_access, outcome)
        if failed and bridge.rewrite_loop_exits_on_mismatch:
            if _testing_1(dal_common):
                ca_process_logs(file_access, dal_common)
            # GO TO class 2 - forward terminator. The post-loop work below STILL RUNS,
            # which is exactly why NEW-8 wipes the status [common/dfltMT.cbl:L702-L708].
            break
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)
            if bridge.clears_error_after_logging:
                # ANOMALY NEW-10 again, on the rewrite path
                # [common/finalMT.cbl:L688-L690].
                file_access.fs_reply = int(FsReply.SUCCESS)
                logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
                logging_data.sql_msg = " " * SQL_MSG_WIDTH
    # ANOMALY NEW-8 / NEW-9 - the unconditional clear.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    return BA999_EXIT


def _positioning_where_text(bridge: BridgeProfile) -> str:
    """Reproduce the text ``ba040``'s positioning stage puts in ``WS-Where``.

    DIVERGENCE 2: ``systemMT`` emits the low key UNQUOTED [common/systemMT.cbl:L670]
    while the other three emit ``'"000"'``, quoted [common/dfltMT.cbl:L476,
    common/finalMT.cbl:L477, common/sys4MT.cbl:L503].

    Args:
        bridge: The bridge's profile.

    Returns:
        The predicate text, as the frozen builder would have left it.
    """
    key = key_of_reference(bridge.table, 1)
    start = SEQUENTIAL_READ_START[bridge.table]
    # `KeyName (KOR-x1) delimited by space` sends up to the first space, so a key name
    # padded in the key table contributes only its own characters
    # [common/systemMT.cbl:L667].
    name = key.key_name.split(" ")[0]
    low = f'"{start.low_key}"' if bridge.low_key_is_quoted else start.low_key
    return (
        f"`{name}` {start.relation.token} {low}"
        f" ORDER BY `{name}` ASC"
    )


def _read_one_row(bridge: BridgeProfile) -> CursorOutcome:
    """Issue one ``ba040`` fetch, positioning first if there is no position.

    Delegates the mechanics to :func:`acas_posting.dal.cursor_state.read_next`, which
    reproduces the identical two-stage shape from a sibling bridge and carries its
    anomalies A1, A9, A11 and A12 with it. ``file_access`` is NOT passed, deliberately.

    Args:
        bridge: The bridge's profile.

    Returns:
        The outcome, with the row keyed by column name or ``None``.

    Raises:
        RuntimeError: If no connection is open, for the reason :func:`_execute_command`
            documents.
    """
    state = handler_state()
    connection = state.connection
    if connection is None:
        raise RuntimeError(
            f"{bridge.program}: no connection is open. The caller must issue "
            "the System-Open verb first [common/systemMT.cbl:L592-L594]."
        )
    # A dead session - which anomaly A-8 makes reachable, since any bridge's close takes
    # the one process handle down - must arrive as a status pair and not as a raise,
    # because the frozen bridge has no cursor-acquisition step to fail at.
    cursor = acquire_cursor(connection)
    try:
        outcome = read_next(
            cursor,
            bridge.table,
            # `set KOR-x1 to 1 *> 1 = Primary, ...` - all four bridges hard-code the
            # primary key of reference and none of the four tables has a second one
            # [common/systemMT.cbl:L664, common/dfltMT.cbl:L470,
            # common/finalMT.cbl:L471, common/sys4MT.cbl:L497].
            slot=CursorSlot.PRIMARY,
            states=state.cursors,
        )
    finally:
        cursor.close()
    if outcome.row is None and outcome.file_key == READ_END_TAGS["no_rows"]:
        state.mysql_count_rows[bridge.program] = 0
    elif outcome.row is not None:
        state.mysql_count_rows[bridge.program] = max(
            state.mysql_count_rows.get(bridge.program, 0), 1
        )
    return outcome


def _ba040_process_read_next(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
) -> str:
    """``ba040-Process-Read-Next`` - the verb function codes 3 AND 4 reach.

    THE HANDLER PUBLISHES ``System-Read-Indexed`` AND NOTHING ELSE
    [copybooks/Proc-ACAS-FH-Calls.cob:L190-L230], yet every one of the four bridges routes BOTH
    function code 3 and function code 4 into this sequential paragraph
    [common/systemMT.cbl:L578-L581, and the same two ``when`` clauses in the other
    three].

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to unload into.

    Returns:
        The exit label reached.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    cursor_state = state.cursors.state_for(bridge.table)
    pending: CursorOutcome | None = None

    if cursor_state.cursor_not_active():
        logging_data.ws_log_where = _log_where_text(
            _positioning_where_text(bridge)
        )
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_POSITION
        pending = _read_one_row(bridge)
        logging_data.ws_file_key = _ws_file_key_move(bridge.positioned_tag)
        if bridge.guards_on_incoming_status and _status_is_dirty(file_access):
            # sys4MT's 28/09/16 guard, before the count test
            # [common/sys4MT.cbl:L538-L541]. GO TO class 4 - it calls ba998-Free, which
            # falls into ba999-End.
            _ba998_free(bridge, file_access)
            return BA999_END
        if state.mysql_count_rows.get(bridge.program, 0) == 0:
            if bridge.captures_sqlstate:
                logging_data.sql_state = _move_into(
                    logging_data.sql_state, pending.sql_state, signed=None
                )
            if _errno_indicates_failure(bridge, _outcome_errno(pending)):
                logging_data.sql_err = _move_into(
                    logging_data.sql_err, _outcome_errno(pending), signed=None
                )
                logging_data.sql_msg = _move_into(
                    logging_data.sql_msg,
                    pending.file_key or "",
                    signed=None,
                )
            (file_access.fs_reply, file_access.we_error) = (
                int(end_of_file_status()[0]),
                end_of_file_status()[1],
            )
            logging_data.ws_file_key = _ws_file_key_move(
                READ_END_TAGS["no_rows"]
            )
            _ba998_free(bridge, file_access)
            return BA999_END

    logging_data.ws_log_where = " " * WS_LOG_WHERE_WIDTH
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_FETCH

    if bridge.occurs_bound is None:
        return _ba040_single_row(
            bridge, file_access, dal_common, record, pending
        )
    return _ba040_occurs_table(
        bridge, file_access, dal_common, record, pending
    )


def _status_is_dirty(file_access: FileAccess) -> bool:
    """``if FS-Reply not = zero or WE-Error not = zero`` - ``sys4MT``'s guard.

    Added 28/09/16 and present at FOUR sites, all in ``sys4MT`` and nowhere else
    [common/sys4MT.cbl:L538-L541, :L593-L596, :L640-L643, :L718-L721]. DIVERGENCE 8.

    Args:
        file_access: The caller's status block.

    Returns:
        Whether either field is non-zero.
    """
    return (
        file_access.fs_reply != int(FsReply.SUCCESS)
        or file_access.we_error != int(WeError.SUCCESS)
    )


def _outcome_errno(outcome: CursorOutcome) -> str:
    """What ``call "MySQL_errno"`` would report after a positioning stage.

    RECORDED OMISSION, precisely bounded. ``dal/cursor_state.py`` reproduces anomaly A11
    - a failed statement is reported as end of file - and in doing so it collapses two
    distinguishable situations into one outcome.

    Args:
        outcome: What the positioning stage returned.

    Returns:
        The three-character error number, ``"0 "``.
    """
    del outcome
    return ERRNO_NO_ERROR


def _ba040_single_row(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
    pending: CursorOutcome | None,
) -> str:
    """``ba040``'s fetch for the two bridges that hold ONE row.

    [common/systemMT.cbl:L727-L937] and [common/sys4MT.cbl:L559-L627].

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to unload into.
        pending: The row the positioning stage already delivered, if this call
            positioned; ``None`` when the cursor was already set.

    Returns:
        The exit label reached, always ``ba999-End`` for these two.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    cursor_state = state.cursors.state_for(bridge.table)
    outcome = pending if pending is not None else _read_one_row(bridge)

    if bridge.guards_on_incoming_status and _status_is_dirty(file_access):
        # sys4MT's second 28/09/16 guard, AFTER the fetch [common/sys4MT.cbl:L593-L596].
        # GO TO class 4.
        _ba998_free(bridge, file_access)
        return BA999_END

    if outcome.row is None:
        (file_access.fs_reply, file_access.we_error) = (
            int(end_of_file_status()[0]),
            end_of_file_status()[1],
        )
        logging_data.ws_file_key = _ws_file_key_move(
            READ_END_TAGS["end_of_table"]
        )
        cursor_state.set_cursor_not_active()
        if bridge.clears_record_on_end_of_data:
            _initialize_with_filler(record)
        return BA999_END

    if state.mysql_count_rows.get(bridge.program, 0) == 0:
        # `if WS-MYSQL-Count-Rows = zero` AFTER the fetch - the EOF2 branch
        # [common/systemMT.cbl:L911-L923], [common/sys4MT.cbl:L605-L616]. ANOMALY
        # NEW-18.
        if bridge.captures_sqlstate:
            logging_data.sql_state = _move_into(
                logging_data.sql_state, outcome.sql_state, signed=None
            )
        if _errno_indicates_failure(bridge, _outcome_errno(outcome)):
            (file_access.fs_reply, file_access.we_error) = (
                int(end_of_file_status()[0]),
                end_of_file_status()[1],
            )
            _initialize_with_filler(record)
            logging_data.ws_file_key = _ws_file_key_move(
                READ_END_TAGS["driver_failure"]
            )
        cursor_state.set_cursor_not_active()
        return BA999_END

    if file_access.fs_reply == int(FsReply.END_OF_FILE):
        # ANOMALY A10 spelled inline - `if fs-reply = 10 *> belts and braces`
        # [common/systemMT.cbl:L925-L929], [common/sys4MT.cbl:L619-L623].
        cursor_state.set_cursor_not_active()
        logging_data.ws_file_key = _ws_file_key_move(
            READ_END_TAGS["key_out_of_bound"]
        )
        return BA999_END

    _bb100_unload_hvs(bridge, record, outcome.row)
    key_plan = _primary_key_plan(bridge)
    logging_data.ws_file_key = _ws_file_key_move(
        _numeric_move_text(
            int(_as_decimal(outcome.row[key_plan.column])),
            key_plan.integer_digits or REWRITE_KEY_DIGITS,
        )
    )
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    del dal_common
    return BA999_END


def _primary_key_plan(bridge: BridgeProfile) -> ColumnPlan:
    """The column plan for the table's single-column primary key.

    Args:
        bridge: The bridge's profile.

    Returns:
        The plan for the key column.

    Raises:
        KeyError: If the dictionary marks no column as the primary key, which would mean
            the frozen table definition had changed.
    """
    for plan in column_plans_for(bridge.table):
        if plan.ordinal == 1:
            return plan
    raise KeyError(f"{bridge.table} has no column at ordinal 1")


def _ba040_occurs_table(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
    pending: CursorOutcome | None,
) -> str:
    """``ba040``'s fetch for the two bridges that hold an ``OCCURS`` table.

    [common/dfltMT.cbl:L528-L590] and [common/finalMT.cbl:L529-L598]. One call delivers
    the WHOLE table.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to fill.
        pending: The row the positioning stage already delivered, if this call
            positioned; ``None`` when the cursor was already set.

    Returns:
        The exit label reached, always ``ba999-Exit`` for these two.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    cursor_state = state.cursors.state_for(bridge.table)
    # `occurs_bound` is set for exactly the two table-shaped bridges and the caller
    # reaches here only for those, so the bound is read from the public map whose
    # element type is not optional.
    bound = OCCURS_LOOP_BOUNDS[bridge.table]
    key_plan = _primary_key_plan(bridge)
    key_digits = key_plan.integer_digits or REWRITE_KEY_DIGITS

    _initialize_with_filler(record)
    hv_key = 0
    carried = pending
    for counter in range(1, bound + 1):
        # ANOMALY NEW-17.
        outcome = carried if carried is not None else _read_one_row(bridge)
        carried = None
        if outcome.row is None:
            (file_access.fs_reply, file_access.we_error) = (
                int(end_of_file_status()[0]),
                end_of_file_status()[1],
            )
            logging_data.ws_file_key = _ws_file_key_move(
                READ_END_TAGS["end_of_table"]
            )
            cursor_state.set_cursor_not_active()
            # GO TO class 2 - the post-loop work below STILL RUNS, which is precisely
            # how anomaly NEW-4 erases this status.
            break
        hv_key = int(_as_decimal(outcome.row[key_plan.column]))
        if hv_key == 0 or hv_key > bound:
            # `if return-code = zero and HV-DEF-REC-KEY = zero or > 32`
            # [common/dfltMT.cbl:L560-L565], [common/finalMT.cbl:L548-L553]. ANOMALY
            # NEW-16: `WE-Error` receives the OFFENDING KEY and `FS-Reply` is not
            # touched.
            logging_data.ws_file_key = _ws_file_key_move(
                READ_END_TAGS["key_out_of_bound"]
            )
            file_access.we_error = hv_key
            cursor_state.set_cursor_not_active()
            break
        if state.mysql_count_rows.get(bridge.program, 0) == 0:
            # The EOF2 branch [common/dfltMT.cbl:L567-L578],
            # [common/finalMT.cbl:L555-L566]. ANOMALY NEW-18 again.
            if _errno_indicates_failure(bridge, _outcome_errno(outcome)):
                (file_access.fs_reply, file_access.we_error) = (
                    int(end_of_file_status()[0]),
                    end_of_file_status()[1],
                )
                logging_data.ws_file_key = _ws_file_key_move(
                    READ_END_TAGS["driver_failure"]
                )
            cursor_state.set_cursor_not_active()
            break
        # The three store-backs [common/dfltMT.cbl:L579-L581] / the one
        # [common/finalMT.cbl:L587].
        _bb100_unload_hvs(bridge, record, outcome.row, subscript=hv_key)
        logging_data.ws_file_key = _ws_file_key_move(
            _numeric_move_text(hv_key, key_digits)
        )
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)

    # The post-loop block, UNCONDITIONAL - ANOMALY NEW-4 [common/dfltMT.cbl:L587-L590],
    # [common/finalMT.cbl:L595-L598].
    logging_data.ws_file_key = _ws_file_key_move(
        _numeric_move_text(hv_key, key_digits)
    )
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    return BA999_EXIT


def _log_where_text(text: str) -> str:
    """``move ws-Where (1:J) to WS-Log-Where`` for the positioning branch.

    Args:
        text: The predicate text.

    Returns:
        Exactly ``WS_LOG_WHERE_WIDTH`` characters.
    """
    return (text + " ")[:WS_LOG_WHERE_WIDTH].ljust(WS_LOG_WHERE_WIDTH)


# Each of the four is `CALL`ed with THREE parameters and `File-Access` FIRST
# [common/acas000.cbl:L576-L579], a different arity and order from the handler's own
# four-parameter linkage [common/acas000.cbl:L309-L315]; both are published as written
# rather than harmonised, so a reader can diff the argument lists (rule R-5).


def _run_bridge(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
) -> None:
    """One bridge's whole ``PROCEDURE DIVISION``, for one call.

    Function code 3 and function code 4 share one arm, and the arm is the SEQUENTIAL
    read.

    Args:
        bridge: The bridge's profile.
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The record to read into or write from.

    Raises:
        RuntimeError: From the paragraphs that need a connection and find none.
    """
    state = handler_state()
    _ba010_initialise(bridge, file_access)
    function = int(file_access.file_function)

    if function == int(FileFunction.OPEN):
        system = state.system_record
        if system is None and isinstance(record, SystemRecord):
            system = record
        if system is None:
            raise RuntimeError(
                f"{bridge.program}: the six connection parameters are loaded "
                "from the FILE SECTION system record "
                "[common/acas000.cbl:L557-L562], whose relative file is out "
                "of scope; open with File-Key-No 1 or 5 first so the "
                "SystemRecord that carries them reaches this handler. See "
                "anomaly N-fdcreds."
            )
        state.system_record = system
        _ba020_process_open(bridge, system, file_access, dal_common)
        label = BA999_END
    elif function == int(FileFunction.CLOSE):
        _ba030_process_close(bridge, file_access, dal_common)
        label = BA999_END
    elif function in {
        int(FileFunction.READ_NEXT),
        int(FileFunction.READ_INDEXED),
    }:
        label = _ba040_process_read_next(
            bridge, file_access, dal_common, record
        )
    elif function == int(FileFunction.WRITE):
        label = _ba070_process_write(bridge, file_access, dal_common, record)
    elif function == int(FileFunction.RE_WRITE):
        label = _ba090_process_rewrite(bridge, file_access, dal_common, record)
    else:
        # `when other` - 6 is spare, and 8 delete and 9 start never arrive because the
        # facade publishes no verb for them.
        _ba100_bad_function(file_access)
        label = BA999_END

    if label == BA999_END:
        _ba999_end(bridge, file_access, dal_common)


def system_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SystemRecord,
) -> None:
    """``call "systemMT" using File-Access ACAS-DAL-Common-data ...``.

    Its row is ALWAYS row 1: ``bb000-HV-Load`` opens with ``move 1 to HV-SYSTEM-REC-
    KEY`` [common/systemMT.cbl:L1070] and the rewrite predicate names the literal
    ``"1"`` [common/systemMT.cbl:L992]. That is the deeper reason dispatch arm 5 cannot
    reach a different row from arm 1.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The system record, read into or written from.
    """
    _run_bridge(SYSTEM_MT, file_access, dal_common, record)


def dflt_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SysDefaultRecord,
) -> None:
    """``call "dfltMT" using File-Access ACAS-DAL-Common-data ...``.

    [common/acas000.cbl:L581-L584], whose third argument is ``WS-System-Record`` with a
    trailing ``*> Default-Record`` comment - the comment is the ONLY thing that says a
    different layout is intended. Anomaly N9.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The defaults record, whose 33-entry table this fills or writes.
    """
    _run_bridge(DFLT_MT, file_access, dal_common, record)


def final_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SysFinalRecord,
) -> None:
    """``call "finalMT" using File-Access ACAS-DAL-Common-data ...``.

    [common/acas000.cbl:L586-L589], third argument ``WS-System-Record`` with a trailing
    ``*> Final-Record`` comment. Anomaly N9 again.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The final-accounts record, whose 26-entry table this fills.
    """
    _run_bridge(FINAL_MT, file_access, dal_common, record)


def sys4_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SystemRecord4,
) -> None:
    """``call "sys4MT" using File-Access ACAS-DAL-Common-data ...``.

    [common/acas000.cbl:L591-L594], third argument ``WS-System-Record`` with a trailing
    ``*> System-Record-4`` comment. Anomaly N9 once more.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The period-totals record.
    """
    _run_bridge(SYS4_MT, file_access, dal_common, record)


# One function per paragraph of `common/acas000.cbl`, in source order, each carrying its
# locator and each `GO TO` site annotated with its class from the Agent Action Plan
# section 0.4.2 taxonomy.


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa999-main-exit`` - log if testing, then fall through.

    It has no ``go to``, so it FALLS THROUGH into ``aa-main-exit`` and thence into ``aa-
    Exit`` [common/acas000.cbl:L497-L504].

    Args:
        file_access: The shared status block.
        dal_common: The shared flags block.
    """
    if _testing_1(dal_common):
        ca_process_logs(file_access, dal_common)


def aa_main_exit() -> None:
    """``aa-main-exit`` - an empty label.

    [common/acas000.cbl:L497-L500]. It carries only the comment "Now have processed
    cobol flat file ." and falls into ``aa-Exit``.
    """


def aa_exit() -> None:
    """``aa-Exit`` - ``exit program``."""


def aa100_bad_function(file_access: FileAccess) -> None:
    """``aa100-Bad-Function`` - 999 and 99, then fall through.

    The handler reports 999 where all four bridges report 990 for the same condition
    [common/systemMT.cbl:L1027-L1029].

    Args:
        file_access: The shared status block, mutated in place.
    """
    file_access.we_error = int(WeError.NOT_USED)
    file_access.fs_reply = int(FsReply.ERROR)


def aa020_process_open(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa020-Process-Open`` - open the RELATIVE FILE. Out of scope.

    [common/acas000.cbl:L389-L433]. Sets everything its COBOL sets, in the frozen order,
    and then raises, because the store it opens is not part of this migration.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: For the three access types that would
            actually open the file.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    logging_data.ws_file_key = _ws_file_key_move("OPEN SYSTEM File")
    logging_data.ws_no_paragraph = PARAGRAPH_NO_OPEN
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)

    if state.cobol_file_status == 1:
        logging_data.ws_file_key = _ws_file_key_move(
            "Already OPENed SYSTEM File"
        )
        file_access.we_error = WE_ERROR_FILE_ALREADY_OPEN
        file_access.fs_reply = FS_REPLY_FILE_ALREADY_OPEN
        aa999_main_exit(file_access, dal_common)
        return

    access = int(file_access.access_type)
    if access == int(AccessType.EXTEND):
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        file_access.fs_reply = int(FsReply.ERROR)
        aa999_main_exit(file_access, dal_common)
        return

    raise RelativeFileStoreNotMigratedError(
        "aa020-Process-Open would issue "
        f"`open {AccessType(access).name.lower()} System-File` on the "
        "relative file [common/acas000.cbl:L402-L421]. Put \"66\" in "
        "FA-RDBMS-Flat-Statuses to reach the migrated RDBMS path "
        "[common/acas000.cbl:L346-L354]. The relative organisation "
        "is declared at [copybooks/selsys.cob] over the file named "
        "at [copybooks/file00.cob]."
    )


def aa030_process_close(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa030-Process-Close`` - close the relative file, and log TWICE.

    So a close writes one log record with the real function code (if ``Testing-1``) and
    then a SECOND, UNCONDITIONAL record with ``File-Function`` and ``Access-Type``
    ZEROED in the caller's own block.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = PARAGRAPH_NO_CLOSE
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    if state.cobol_file_status == 1:
        logging_data.ws_file_key = _ws_file_key_move("CLOSE SYSTEM File")
    else:
        logging_data.ws_file_key = _ws_file_key_move(
            "Already CLOSED: SYSTEM File"
        )
    state.cobol_file_status = 0
    aa999_main_exit(file_access, dal_common)
    # `move zero to File-Function Access-Type. *> close log file`
    # [common/acas000.cbl:L449-L450].
    file_access.file_function = 0
    file_access.access_type = 0
    ca_process_logs(file_access, dal_common)
    aa_main_exit()


def aa050_process_read_indexed(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa050-Process-Read-Indexed`` - read relative record ``File-Key-No``.

    [common/acas000.cbl:L453-L467]. Its own comment states the contract the handler
    relies on and never checks.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: Always - the read itself needs the store.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = PARAGRAPH_NO_READ_INDEXED
    # `move File-Key-No to rrn.` [common/acas000.cbl:L461] - `Rrn` is `pic 9(5) comp` at
    # [copybooks/wsfnctn.cob:L26] and lives in the CALLER's block, so the relative
    # record number is observable.
    file_access.rrn = int(file_access.logging_data.file_key_no)
    rrn = file_access.rrn
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    logging_data.ws_file_key = _string_into_ws_file_key(
        logging_data.ws_file_key,
        "Read Indexed ",
        _numeric_move_text(rrn, FILE_KEY_NO_DIGITS),
    )
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    aa999_main_exit(file_access, dal_common)
    raise RelativeFileStoreNotMigratedError(
        f"aa050-Process-Read-Indexed would issue `read System-File record "
        f"into WS-System-Record` at rrn {rrn} [common/acas000.cbl:L465]. Put "
        '"66" in FA-RDBMS-Flat-Statuses to reach the migrated RDBMS path '
        "[common/acas000.cbl:L346-L354]. The relative organisation "
        "is declared at [copybooks/selsys.cob] over the file named "
        "at [copybooks/file00.cob]."
    )


def aa070_process_write(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa070-Process-Write`` - write relative record ``File-Key-No``.

    ``write System-Record from WS-System-Record`` writes the FILE SECTION record FROM
    the linkage buffer.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: Always.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = PARAGRAPH_NO_WRITE
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    logging_data.ws_file_key = _string_into_ws_file_key(
        logging_data.ws_file_key,
        "Write ",
        _numeric_move_text(
            int(file_access.logging_data.file_key_no), FILE_KEY_NO_DIGITS
        ),
    )
    file_access.rrn = int(file_access.logging_data.file_key_no)
    rrn = file_access.rrn
    aa999_main_exit(file_access, dal_common)
    raise RelativeFileStoreNotMigratedError(
        f"aa070-Process-Write would issue `write System-Record from "
        f"WS-System-Record` at rrn {rrn} [common/acas000.cbl:L474]. Put "
        '"66" in FA-RDBMS-Flat-Statuses to reach the migrated RDBMS path '
        "[common/acas000.cbl:L346-L354]. The relative organisation "
        "is declared at [copybooks/selsys.cob] over the file named "
        "at [copybooks/file00.cob]."
    )


def aa090_process_rewrite(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa090-Process-Rewrite`` - rewrite relative record ``File-Key-No``.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: Always.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = PARAGRAPH_NO_REWRITE
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    file_access.rrn = int(file_access.logging_data.file_key_no)
    rrn = file_access.rrn
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    logging_data.ws_file_key = _string_into_ws_file_key(
        logging_data.ws_file_key,
        "Rewrite ",
        _numeric_move_text(rrn, FILE_KEY_NO_DIGITS),
    )
    aa999_main_exit(file_access, dal_common)
    raise RelativeFileStoreNotMigratedError(
        f"aa090-Process-Rewrite would issue `rewrite System-Record from "
        f"WS-System-Record` at rrn {rrn} [common/acas000.cbl:L483]. Put "
        '"66" in FA-RDBMS-Flat-Statuses to reach the migrated RDBMS path '
        "[common/acas000.cbl:L346-L354]. The relative organisation "
        "is declared at [copybooks/selsys.cob] over the file named "
        "at [copybooks/file00.cob]."
    )


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit`` - an empty label ending the RDBMS section.

    [common/acas000.cbl:L604-L606]. It is the target of the one early transfer inside
    the section, the 901 record-length path [common/acas000.cbl:L549], and otherwise
    falls off the end of the section. Reproduced as an empty function for the same
    traceability reason as :func:`aa_main_exit`.
    """


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size`` - ONE statement, and it is anomaly N-log.

    ANOMALY N-log. ``aa010-main`` has already put 10 in that field
    [common/acas000.cbl:L328], and the two paths then diverge.

    Args:
        file_access: The shared status block, mutated in place.
    """
    file_access.logging_data.ws_log_file_no = LOG_FILE_NO_RDB_PATH


def ba012_test_ws_rec_size_2(
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2`` - the first-call-only credential load.

    [common/acas000.cbl:L523-L563]. Two things happen, both inside one ``if A = zero``
    guard whose ``end-if`` closes after the sixth move [common/acas000.cbl:L563].

    Args:
        system: The record the six parameters are taken from.
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Returns:
        Whether control transferred to ``ba-rdbms-exit``, which happens only on the dead
            901 path.
    """
    state = handler_state()
    if state.a != 0:
        # `if A = zero` is false from the second call onward, so the entire block -
        # check and load together - is skipped [common/acas000.cbl:L525, :L563].
        return False
    state.a = SYSTEM_RECORD_DECLARED_LENGTH
    state.b = SYSTEM_RECORD_DECLARED_LENGTH
    if state.a < state.b:
        file_access.we_error = int(WeError.RECORD_SIZE_MISMATCH)
        file_access.fs_reply = int(FsReply.ERROR)
    if file_access.we_error == int(WeError.RECORD_SIZE_MISMATCH):
        _LOG.error(
            "AC902 Program Error: Temp rec = %s < System-Rec = %s - the caller "
            "must stop [common/acas000.cbl:L536-L546]",
            state.a,
            state.b,
        )
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)
        return True
    rdb_data = load_rdb_data_once(system)
    file_access.rdb_data.db_schema = _move_into(
        file_access.rdb_data.db_schema, rdb_data.db_schema, signed=None
    )
    file_access.rdb_data.db_uname = _move_into(
        file_access.rdb_data.db_uname, rdb_data.db_uname, signed=None
    )
    file_access.rdb_data.db_upass = _move_into(
        file_access.rdb_data.db_upass, rdb_data.db_upass, signed=None
    )
    file_access.rdb_data.db_port = _move_into(
        file_access.rdb_data.db_port, rdb_data.db_port, signed=None
    )
    file_access.rdb_data.db_host = _move_into(
        file_access.rdb_data.db_host, rdb_data.db_host, signed=None
    )
    file_access.rdb_data.db_socket = _move_into(
        file_access.rdb_data.db_socket, rdb_data.db_socket, signed=None
    )
    return False


def ba015_test_ends(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SystemFileRecord,
) -> None:
    """``ba015-Test-Ends`` - THE DISPATCH. FIVE branches, one buffer.

    and the linkage comment states the arrangement outright [common/acas000.cbl:L311]:
    "with images for the other three record types as same size". So in the compiled
    handler the four layouts occupy ONE storage area and each bridge REINTERPRETS THOSE
    BYTES.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The one buffer, in whichever of its four readings the caller selected
            with ``File-Key-No``.
    """
    file_key_no = int(file_access.logging_data.file_key_no)
    bridge = BRIDGES_BY_FILE_KEY_NO.get(file_key_no)
    if bridge is None:
        #  GO TO class 3 - the `evaluate` simply ends and control reaches
        #  `ba-rdbms-exit` [common/acas000.cbl:L600, :L604]. No bridge call, no
        #  status write, no counter, no trace - anomaly N8's third face.
        #
        #  AND NO LOG RECORD EITHER, WHICH IS THE ANOMALY. "No trace" is the whole
        #  content of N8's third face: the `evaluate` has no `when other`
        #  [common/acas000.cbl:L574-L600], so an out-of-range `File-Key-No` is
        #  swallowed entirely and the caller's stale status pair is what it reads
        #  back. A record here would be a diagnostic the compiled program cannot
        #  produce and would make the defect look handled (rule R-4). It is
        #  recorded, with its locators, in `docs/migration/anomaly-log.md`, and the
        #  guard at [common/acas000.cbl:L333-L341] - which covers only
        #  File-Function 4, 5 and 7 - is why nothing upstream catches it.
        return
    if bridge is SYSTEM_MT:
        system_mt(file_access, dal_common, cast(SystemRecord, record))
    elif bridge is DFLT_MT:
        dflt_mt(file_access, dal_common, cast(SysDefaultRecord, record))
    elif bridge is FINAL_MT:
        final_mt(file_access, dal_common, cast(SysFinalRecord, record))
    else:
        sys4_mt(file_access, dal_common, cast(SystemRecord4, record))


def _credential_record(buffer: SystemFileRecord) -> SystemRecord:
    """The ``SystemRecord`` ``ba012``'s six credential moves read from.

    ANOMALY N-fdcreds, restated as a modelling decision. ``ba012`` names ``System-
    Record`` [common/acas000.cbl:L557-L562], the FILE SECTION record from
    [copybooks/fdsys.cob], whose relative file this migration does not open.

    Args:
        buffer: The one buffer, in the caller's chosen reading.

    Returns:
        The record to take the six parameters from.

    Raises:
        RuntimeError: If neither source is available, naming the omission rather than
            connecting with fabricated credentials.
    """
    state = handler_state()
    if isinstance(buffer, SystemRecord):
        state.system_record = buffer
        return buffer
    if state.system_record is not None:
        return state.system_record
    raise RuntimeError(
        "ba012-Test-WS-Rec-Size-2 takes the six connection parameters from "
        "the FILE SECTION system record [common/acas000.cbl:L557-L562], whose "
        "relative file is out of scope. Call this handler with File-Key-No 1 "
        "or 5 at least once so the SystemRecord that carries them arrives. "
        "See anomaly N-fdcreds."
    )


def ba_process_rdbms(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SystemFileRecord,
) -> None:
    """``ba-Process-RDBMS section`` - the whole migrated path, in order.

    [common/acas000.cbl:L508-L606]. A ``PERFORM`` of a SECTION runs every paragraph in
    it until the section ends, so the three paragraphs fall through one into the next
    with no transfer between them.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The one buffer, in the caller's chosen reading. Its credentials are
            recovered by :func:`_credential_record`.
    """
    # Each handler CALL starts with a fresh reply pair. The frozen menu normally
    # selects the relative-file path, whose operation paragraphs clear these
    # fields themselves; the migrated CLI must select the RDBMS path instead.
    # Without this boundary reset, systemMT's `if fs-reply = 10` guard
    # [common/systemMT.cbl:L925-L929] mistakes an earlier key's EOF for this
    # call's result and suppresses a valid later SYSTEM-REC read.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)

    ba010_test_ws_rec_size(file_access)
    if ba012_test_ws_rec_size_2(
        _credential_record(record), file_access, dal_common
    ):
        ba_rdbms_exit()
        return
    ba015_test_ends(file_access, dal_common, record)
    ba_rdbms_exit()


def key_range_guard_applies(file_function: int) -> bool:
    """Whether ``aa010-main``'s key-range guard fires for this function code.

    The ``evaluate`` has NO ``when other``, so an out-of-range ``File-Key-No`` on an
    open, a close, a read-next, a start or a delete is NOT DIAGNOSED - it passes
    silently and reaches :func:`ba015_test_ends`, whose own ``evaluate`` also has no
    ``when other`` and therefore calls no bridge and reports no status at all.

    Args:
        file_function: The requested function code.

    Returns:
        Whether the guard applies. >>> key_range_guard_applies(4),
            key_range_guard_applies(1) (True, False).
    """
    return file_function in KEY_RANGE_GUARDED_FUNCTIONS


def aa010_main(
    system: SystemFileRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa010-main`` - the handler's entry paragraph, in the frozen order.

    [common/acas000.cbl:L320-L387]. Six things happen, and the order matters because a
    caller can observe every one of them.

    Args:
        system: THE ONE BUFFER of anomaly N9 [common/acas000.cbl:L311], in whichever of
            its four readings ``File-Key-No`` selects. Named ``system`` because that is
            what the frozen linkage calls it.
        file_access: The shared status block, mutated in place.
        file_defs: The file-name definitions.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: From the relative-file paragraphs. An
            unmatched ``File-Key-No`` raises NOTHING - see :func:`ba015_test_ends` for
            anomaly N8's third face.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_system = int(LOG_SYSTEM)
    logging_data.ws_log_file_no = LOG_FILE_NO_FLAT_FILE_PATH

    function = int(file_access.file_function)
    if key_range_guard_applies(function):
        low, high = FILE_KEY_NO_GUARD_RANGE
        if not low <= int(file_access.logging_data.file_key_no) <= high:
            file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            aa999_main_exit(file_access, dal_common)
            return

    if _fa_rdbms_flat_statuses_text(file_access) == RDBMS_STORE_SELECTOR:
        ba_process_rdbms(file_access, dal_common, system)
        aa_main_exit()
        return

    ba012_test_ws_rec_size_2(
        _credential_record(system), file_access, dal_common
    )
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH

    if function == int(FileFunction.OPEN):
        aa020_process_open(file_access, dal_common)
    elif function == int(FileFunction.CLOSE):
        aa030_process_close(file_access, dal_common)
    elif function == int(FileFunction.READ_INDEXED):
        aa050_process_read_indexed(file_access, dal_common)
    elif function == int(FileFunction.WRITE):
        aa070_process_write(file_access, dal_common)
    elif function == int(FileFunction.RE_WRITE):
        aa090_process_rewrite(file_access, dal_common)
    else:
        # `when other *> 6 is spare / unused, no delete (8) or start (9)`
        # [common/acas000.cbl:L383-L384], and the unreachable `go to` below it
        # [common/acas000.cbl:L387] would land in the same place.
        aa100_bad_function(file_access)
        aa999_main_exit(file_access, dal_common)


def dispatch(
    system: SystemFileRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``call "acas000" using ...`` - FOUR parameters, in the frozen order.

    AND THE CALLER OWNS THE KEY. ``acas000.`` is the ONLY dispatch paragraph in the
    1,449-line facade with no ``move 1 to File-Key-No``.

    Args:
        system: THE ONE BUFFER of anomaly N9 [common/acas000.cbl:L311]. In the compiled
            handler this is a single ``01``-level item that four bridges each
            REINTERPRET.
        file_access: The shared status and function block
            [copybooks/wsfnctn.cob:L23-L64], mutated in place.
        file_defs: The file-name definitions [copybooks/wsnames.cob]. Accepted because
            the linkage names it [common/acas000.cbl:L314] and unused on the migrated
            path; see :func:`aa010_main` for the full record of that omission.
        dal_common: The shared testing and logging flags
            [copybooks/Test-Data-Flags.cob].

    Raises:
        RelativeFileStoreNotMigratedError: If the caller leaves
            ``fa_rdbms_flat_statuses`` at anything other than ``"66"`` and asks for a
            verb that would touch the relative file [common/acas000.cbl:L346-L354].
        RuntimeError: If a database verb is issued with no connection open, or if the
            credentials cannot be recovered - see :func:`_credential_record`. An
            unmatched ``File-Key-No`` raises nothing.
    """
    aa010_main(system, file_access, file_defs, dal_common)
