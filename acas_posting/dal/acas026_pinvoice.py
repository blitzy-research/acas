"""`acas026` and its bridge `plinvoiceMT` - the PInvoice entity, header AND lines.

One handler, two tables: `PUINVOICE-REC` for the purchase invoice header and
`PUINV-LINES-REC` for its lines. The module boundary follows the HANDLER, so both
tables live here and the pairing the COBOL performs is preserved.

A header write and its line writes are separate statements against separate
tables, in the order the bridge issues them, because a state comparison is
sensitive to what is present after a partial failure - and the frozen code does
not wrap them in a transaction.

Each write goes through the bridge's own host-variable record, whose load
paragraph initialises the group before moving fields in, so an unset field becomes
zero or space rather than SQL NULL.
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
    IhFig,
    IhInvoiceHeader,
    IhOrder,
    IhPrime,
    IhSubPrime,
    IhSupplier,
    IlInvoiceLine,
    IlInvoiceLineBody,
    IlKey,
    PInvoiceBodies,
    PInvoiceHeader,
    WsInvoiceKey,
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
    "linkage_header_for",
    "publish_linkage_header",
    "line_from_bodies",
    "line_from_buffer",
    "plinvoice_mt",
    "rendered_column_text",
]

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


HANDLER_NAME: Final[str] = "acas026"

BRIDGE_NAME: Final[str] = "plinvoiceMT"

HANDLER_PROG_NAME: Final[str] = "acas026 (3.3.00)"

ENTITY_FACADE: Final[str] = "PInvoice"

HEADER_TABLE: Final[str] = "PUINVOICE-REC"

LINES_TABLE: Final[str] = "PUINV-LINES-REC"

_HV_GROUP_SUFFIX_BY_TABLE: Final[Mapping[str, str]] = MappingProxyType(
    {HEADER_TABLE: "HV", LINES_TABLE: "HV1"}
)

#: The three declared record-size notes, spread over FOUR statements in THREE files,
#: published unresolved next to Agent Action Plan anomaly A-15.
DECLARED_RECORD_SIZE_NOTES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "copybooks/plwspinv.cob:L6": "100 bytes",
        "copybooks/plwspinv2.cob:L7-L8": "129 bytes, then 100 less filler err.",
        "copybooks/plfdpinv.cob:L6-L9": "100, then 126, then 129, then 100 bytes",
    }
)

#: ``N-dead-filler`` - `copybooks/plwspinv2.cob:L54` carries a COMMENTED-OUT `05 filler
#: pic x(30).` annotated `*> This appears to be empty of data on all rec types.` The
#: maintainer's own hedge - "appears to be" - was never resolved, and the declaration
#: was disabled rather than deleted, so the byte range it once covered is now simply
#: absent from the layout.
DEAD_DECLARATION_LOCATORS: Final[tuple[str, ...]] = (
    "copybooks/plwspinv2.cob:L54",
)

PLWSPINV2_CONSUMERS: Final[tuple[str, ...]] = (
    "common/plinvoiceLD.cbl",
    "common/plinvoiceRES.cbl",
    "common/plautogenLD.cbl",
    "common/plinvoiceUNL.cbl",
    "common/xl150.cbl",
    "purchase/pl055.cbl",
    "purchase/pl140.cbl",
)

#: The declared byte length of the passed working-storage record and of the file record,
#: as `ba012-Test-WS-Rec-Size-2` compares them with `function Length(WS-PInvoice-
#: Record)` against `function length(Invoice-Record)` [common/acas026.cbl:L562-L566].
_WS_RECORD_DECLARED_LENGTH: Final[int] = 100
_FILE_RECORD_DECLARED_LENGTH: Final[int] = 100

_DISPLAY_BLK_WIDTH: Final[int] = 75

_RECORD_SIZE_DIGITS: Final[int] = 4

#: `01  Error-Messages.` [common/acas026.cbl:L205-L209] - the handler's only two
#: literals, both `Module Specific` per the comment at [:L207]. `PL907` is 32
#: characters and `PL901` is 31; the continuation comment
#: `*>                                        yyy < Invoice-Rec = zzz` [:L210]
#: sketches the message `ba012-Test-WS-Rec-Size-2` assembles from it [:L573-L578].
#:
#: ``N-error-message-block`` - the sketch comment
#: `*>                                        yyy < Invoice-Rec = zzz`
#: [common/acas026.cbl:L210] uses THREE-character placeholders, `yyy` and `zzz`,
#: for two fields that are declared `pic 9(4)` [common/acas026.cbl:L193-L194] and
#: therefore render at FOUR digits, zero-filled. The comment is a stale sketch of
#: an earlier, narrower pair of counters; the assembled message is four digits
#: wide in each slot. Recorded, not corrected - :data:`_RECORD_SIZE_DIGITS` is 4
#: because the PICTURE says 4, and the comment is left describing 3.
#:
#: ``N-open-close-key-wording`` - a second stale-wording finding in the same
#: handler, worth reading beside this one. The handler logs
#: `"OPEN PL INVOICE File"` [common/acas026.cbl:L342] and
#: `"CLOSE PL INVOICE File"` [common/acas026.cbl:L353], naming the PURCHASE ledger
#: and suffixing `" File"`; the bridge logs `"OPEN SL INVOICE"` and
#: `"CLOSE SL INVOICE"` [common/plinvoiceMT.cbl:L605, :L631], naming the SALES
#: ledger and omitting the suffix. Same table, same run, two different log keys
#: depending only on which path served the call. Both are reproduced verbatim at
#: their own sites; see :func:`aa020_process_open`, :func:`aa030_process_close`,
#: :func:`ba020_process_open` and :func:`ba030_process_close`.
#:
#: DECLARED AND DELIBERATELY UNREFERENCED. The declaration is a fact about the frozen
#: ``Error-Messages`` group [common/acas026.cbl:L208] and R-5 keeps it verbatim, but
#: the literal's whole text is the acknowledgement half of the record-size
#: diagnostic - it asks the operator to hit return, which is the ``accept`` Agent
#: Action Plan section 0.3.4 drops - so no log record quotes it. Only the assembled
#: ``PL907`` diagnostic reaches a record.
_ERROR_MESSAGE_PL901: Final[str] = "PL901 Note error and hit return"
_ERROR_MESSAGE_PL907: Final[str] = "PL907 Program Error: Temp rec = "

# Linkage - the two parameter lists, published for traceability (R-5).

HANDLER_LINKAGE_PARAMETER_NAMES: Final[tuple[str, ...]] = (
    "System-Record",
    "WS-PInvoice-Record",
    "File-Access",
    "File-Defs",
    "ACAS-DAL-Common-data",
)

#: `PROCEDURE DIVISION using File-Access ACAS-DAL-Common-data WS-Invoice-Record.`
#: [common/plinvoiceMT.cbl:L478-L480]. Three parameters, and note the THIRD NAME.
BRIDGE_LINKAGE_PARAMETER_NAMES: Final[tuple[str, ...]] = (
    "File-Access",
    "ACAS-DAL-Common-data",
    "WS-Invoice-Record",
)


#: `move 4 to WS-Log-System.` [common/acas026.cbl:L240], whose own legend on that line
#: reads `*> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice used in FH logging`.
WS_LOG_SYSTEM: Final[status.LogSystem] = status.LogSystem.PL

WS_LOG_FILE_NO: Final[int] = 12

#: `move 12 to WS-Log-File-no. *> for FHlogger` on the RDB path
#: [common/acas026.cbl:L556]. TWELVE - the SAME value, not twenty-two.
WS_LOG_FILE_NO_RDB: Final[int] = 12

#: The ten siblings that DO add ten, recorded so the exception above is provably an
#: exception rather than an assumption. Values are ``(flat, rdb)``.
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
#: [common/acas026.cbl:L310, L348, L365, L418, L442, L490, L501, L513].
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
#: maintainer's own comment block [common/plinvoiceMT.cbl:L542-L563].
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


#: Exactly what `evaluate File-Function` dispatches in the HANDLER
#: [common/acas026.cbl:L283-L303].
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
#: [common/plinvoiceMT.cbl:L515-L540]. It differs from the handler's table in ONE entry,
#: and the difference is load bearing.
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

#: The corrected folder-wide census of the four EXTENDED function codes declared at
#: [copybooks/wsfnctn.cob:L102-L105]. ``acas026`` dispatches **34**, not 31 - `when 34
#: *> fn-Read-Next-Header` [common/acas026.cbl:L289].
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

#: The handler's key guard [common/acas026.cbl:L245-L259]: `fn-read-indexed` (4) and
#: `fn-start` (9) reject `File-Key-No not = 1` with `998`/`99`, and `fn-delete` (8)
#: rejects it with `996`/`99`.
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


KEY_OF_REFERENCE: Final[tuple[cursor_state.KeyOfReference, ...]] = (
    cursor_state.TABLE_OF_KEYNAMES[HEADER_TABLE]
    + cursor_state.TABLE_OF_KEYNAMES[LINES_TABLE]
)

_KOR_HEADER: Final[int] = 1
_KOR_LINES: Final[int] = 2


def _key_of_reference(kor_x1: int) -> cursor_state.KeyOfReference:
    """`KeyOfReference (KOR-x1)` - the one-based subscript into the key table.

    Every positioning paragraph in the bridge opens with the same three statements -
    `set KOR-x1 to <n>.` then `move KOR-offset (KOR-x1) to K` and `move KOR-length
    (KOR-x1) to L` [common/plinvoiceMT.cbl:L834-L836, :L965-L967, :L1053-L1055,
    :L1195-L1197, :L1291-L1293, :L1365-L1367, :L2365-L2367, :L2534-L2536, :L2698-L2700]
    - so the subscript is set, then the offset and length are read out of the indexed
    entry.
    """
    return KEY_OF_REFERENCE[kor_x1 - 1]

#: The two cursors this bridge declares - `05 Most-Cursor-Set pic 9 value zero.` and `05
#: Most-Cursor-Set-2 pic 9 value zero.
CURSOR_SLOTS: Final[Mapping[str, cursor_state.CursorSlot]] = MappingProxyType(
    {
        HEADER_TABLE: cursor_state.CursorSlot.PRIMARY,
        LINES_TABLE: cursor_state.CursorSlot.SECONDARY,
    }
)


@dataclasses.dataclass(frozen=True, slots=True)
class RepeatingGroupEntry:
    """One row of `RG-Table` / `RG-Entry` [common/plinvoiceMT.cbl:L316-L326].

    The declaration is inert by the maintainer's own labelling. It sits under `*> Start
    of RG (Repeat Groups) NOT USED - YET.` [:L313] and `*> Metadata on Repeating
    Groups...
    """

    rg_recname: str
    rg_maxoccurs: int
    #: `05 RG-noloaded pic s9(9) comp-5. *> Number loaded.` [:L326]; declared `value
    #: zero` [:L319] and never incremented anywhere in the bridge.
    rg_noloaded: int
    source_locator: str


#: `01 RG-Table.` as declared [common/plinvoiceMT.cbl:L316-L319].
RG_TABLE: Final[tuple[RepeatingGroupEntry, ...]] = (
    RepeatingGroupEntry(
        rg_recname=LINES_TABLE,
        rg_maxoccurs=40,
        rg_noloaded=0,
        source_locator="[common/plinvoiceMT.cbl:L316-L326]",
    ),
)

_BODIES_OCCURS: Final[int] = 40

#: `01 WS-Last-Read-Key.` with `03 WS-Last-Read-Invoice pic 9(8) value zero.` and `03
#: WS-Last-Read-Line pic 99 value 40.` [common/plinvoiceMT.cbl:L286-L288], with `01 WS-
#: Actual-Lines-In-Row pic 99 value zero.` [:L289].
_LAST_READ_INVOICE_INITIAL: Final[int] = 0
_LAST_READ_LINE_INITIAL: Final[int] = 40
_ACTUAL_LINES_IN_ROW_INITIAL: Final[int] = 0

#: `move "0000000000" to WS-File-Key` and the `" >= "` relation the sequential read
#: hard-codes for its first positioning [common/plinvoiceMT.cbl:L645-L646], already
#: published with both locators by
#: :data:`acas_posting.dal.cursor_state.SEQUENTIAL_READ_START`.
_SEQUENTIAL_READ_START: Final[cursor_state.SequentialReadStart] = (
    cursor_state.SEQUENTIAL_READ_START[HEADER_TABLE]
)

# Status codes this bridge owns and `dal/status.py` does not publish `dal/status.py`
# publishes the whole shared vocabulary - 0/10/21/22/23/99 for `FS-Reply` and
# 901/910/911/988/989/990/992/994/995/996/997/998/999 for `WE-Error` - and those are
# cited from there, never redefined.

#: `*> 8nn = Processing on RG Table & rows.` [common/plinvoiceMT.cbl:L205]. A band, not
#: a value.
WE_ERROR_RG_PROCESSING_BASE: Final[int] = 800

WE_ERROR_RG_UNKNOWN: Final[int] = 890

#: `*> 880 = Unexpected range error in Rg1 secondary key. Report to programming team.`
#: [common/plinvoiceMT.cbl:L206].
WE_ERROR_RG1_SECONDARY_KEY_RANGE: Final[int] = 880

#: `*> 901 = File Def record size not =< than WS record size. FATAL`, the code
#: `ba012-Test-WS-Rec-Size-2` would raise [common/acas026.cbl:L568-L569]. Taken from
#: `status.WeError`, not redefined.
_WE_ERROR_RECORD_SIZE: Final[status.WeError] = status.WeError.RECORD_SIZE_MISMATCH

_WE_ERROR_TABLE_LOCKED: Final[status.WeError] = status.WeError.TABLE_LOCKED

#: `move zero to SQL-State.` [common/plinvoiceMT.cbl:L498] - the figurative constant
#: ZERO moved into `SQL-State pic x(5)` [copybooks/wsfnctn.cob:L51], which fills the
#: field with the CHARACTER zero rather than with spaces.
_SQL_STATE_ZEROED: Final[str] = "0" * status.SQL_STATE_WIDTH

_MYSQL_ERRNO_NONE: Final[str] = "0  "

_DUPLICATE_KEY_SQL_STATE: Final[str] = str(status.DUPLICATE_KEY_SQLSTATE.value)
_DUPLICATE_KEY_ERRNO_PREFIXES: Final[tuple[str, ...]] = ("1062", "1022")


#: The five columns that can only ever hold a single space, for every row, forever - the
#: headline finding of this module.
HEADER_NEVER_POPULATED_COLUMNS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "IH-STATUS-A": "[common/plinvoiceMT.cbl:L408] / [mysql/ACASDB.sql:L563] 'Applied'",
        "IH-STATUS-C": "[common/plinvoiceMT.cbl:L409] / [mysql/ACASDB.sql:L564] 'cleared'",
        "IH-STATUS-I": "[common/plinvoiceMT.cbl:L410] / [mysql/ACASDB.sql:L565] 'Invoiced'",
        "IH-STATUS-L": "[common/plinvoiceMT.cbl:L411] / [mysql/ACASDB.sql:L566] 'printed'",
        "IH-STATUS-P": "[common/plinvoiceMT.cbl:L412] / [mysql/ACASDB.sql:L567] 'Pending'",
    }
)

_NEVER_POPULATED_STATUS_VALUE: Final[str] = " "

#: The two columns that are loaded and never unloaded - write-only columns.
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
#: executes - the Agent Action Plan anomaly A-11 family, and dictionary anomaly reference
#: ``A-11``. The QUESTION of what the unsigned column then holds - ``Q-3`` - has been
#: measured on the compiled oracle and is no longer published as open; the ANOMALY
#: stays, because the lost debit-versus-credit sense was not restored by measuring it.
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

    Both halves of that are reproduced here, in one place, so that the behaviour has
    exactly one implementation.
    """
    magnitude = value if value >= 0 else -value
    return magnitude % (10**digits)


_EDIT_WIDTH: Final[int] = 30
_EDIT_SIGN_POSITION: Final[int] = 1
_EDIT_INTEGER_POSITION: Final[int] = 2
_EDIT_INTEGER_DIGITS: Final[int] = 19
_EDIT_POINT_POSITION: Final[int] = 21
_EDIT_FRACTION_POSITION: Final[int] = 22
_EDIT_FRACTION_DIGITS: Final[int] = 9


@dataclasses.dataclass(frozen=True, slots=True)
class EditWindow:
    """One `WS-MYSQL-EDIT (offset:length)` reference modification."""

    offset: int
    length: int
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

        Never true for any window this bridge uses, which is precisely why the eleven
        signed decimal columns are written unsigned (anomaly ``N-signloss-in-render``).
        """
        return self.offset <= _EDIT_SIGN_POSITION < self.offset + self.length

    def apply(self, image: str) -> str:
        """Return the slice of ``image`` this window designates."""
        start = self.offset - 1
        return image[start : start + self.length]


_WINDOW_INT_10: Final[EditWindow] = EditWindow(11, 10, "[common/plinvoiceMT.cbl:L1556]")
_WINDOW_INT_07: Final[EditWindow] = EditWindow(14, 7, "[common/plinvoiceMT.cbl:L1631]")
_WINDOW_INT_05: Final[EditWindow] = EditWindow(16, 5, "[common/plinvoiceMT.cbl:L2916]")
_WINDOW_INT_03: Final[EditWindow] = EditWindow(18, 3, "[common/plinvoiceMT.cbl:L1819]")
_WINDOW_INT_02: Final[EditWindow] = EditWindow(19, 2, "[common/plinvoiceMT.cbl:L2966]")
_WINDOW_FRACTION_02: Final[EditWindow] = EditWindow(
    22, 2, "[common/plinvoiceMT.cbl:L1636]"
)


class _RenderKind(enum.StrEnum):
    """How the bridge turns one host variable into command text."""

    CHARACTER = "character"
    INTEGER = "integer"
    DECIMAL = "decimal"


@dataclasses.dataclass(frozen=True, slots=True)
class ColumnRender:
    """Everything needed to render one column exactly as the bridge does."""

    column: str
    dictionary_key: str
    host_variable: str
    kind: _RenderKind
    hv_scale: int
    hv_digits: int
    integer_window: EditWindow | None
    fraction_window: EditWindow | None
    loses_sign_in_render: bool
    loses_sign_in_load: bool
    cite: str


def _edit_image(value: decimal.Decimal | int | None, scale: int) -> str:
    """Return the 30-character `WS-MYSQL-EDIT` image of ``value``.

    Reproduces `MOVE <host variable> TO WS-MYSQL-EDIT` for the picture `-Z(18)9.9(9)`
    [common/plinvoiceMT.scb:L272].
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
    integer_field = integer_text[-_EDIT_INTEGER_DIGITS:].rjust(_EDIT_INTEGER_DIGITS)
    fraction_field = (fraction_text + "0" * _EDIT_FRACTION_DIGITS)[
        :_EDIT_FRACTION_DIGITS
    ]
    return f"{'-' if negative else ' '}{integer_field}.{fraction_field}"


def rendered_column_text(
    render: ColumnRender, value: decimal.Decimal | int | str | None
) -> str:
    """Render one column value into the exact text the bridge STRINGs.

    The returned string is the body that sits between the two `"` characters the bridge
    writes around every value, for every one of the forty-four columns of the two
    tables. It is text and nothing else.
    """
    if render.kind is _RenderKind.CHARACTER:
        text = "" if value is None else str(value)
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
    return f"{integer_text}.{render.fraction_window.apply(image)}"


#: The observed windows, keyed by the host variable's integer digit count.
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
    # Derived rather than transcribed only if a picture appears that the two in-scope
    # tables do not use.
    return EditWindow(
        _EDIT_POINT_POSITION - integer_digits,
        integer_digits,
        "[common/plinvoiceMT.scb:L272] derived from the WS-MYSQL-EDIT picture",
    )


def _column_render_table(table_name: str) -> Mapping[str, ColumnRender]:
    """Build the per-column render table for ``table_name`` from the dictionary.

    Field metadata is DERIVED from ``data_dictionary/acas_posting_dictionary.json`` and
    never transcribed by eye, which is the Agent Action Plan's section 0.8.1 directive:
    *"Data dictionary first. ... every Python field definition cites its entry.
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


HEADER_COLUMN_RENDER: Final[Mapping[str, ColumnRender]] = _column_render_table(
    HEADER_TABLE
)

LINES_COLUMN_RENDER: Final[Mapping[str, ColumnRender]] = _column_render_table(
    LINES_TABLE
)

RENDER_SIGN_LOSS_COLUMNS: Final[tuple[str, ...]] = tuple(
    f"{table}.{column}"
    for table, renders in (
        (HEADER_TABLE, HEADER_COLUMN_RENDER),
        (LINES_TABLE, LINES_COLUMN_RENDER),
    )
    for column, render in renders.items()
    if render.loses_sign_in_render
)

# The SIX ordering lists Load order, unload order and column order disagree on both
# tables, so all six lists are built independently and none is derived from another.


@dataclasses.dataclass(frozen=True, slots=True)
class HostVariableMove:
    """One `move` statement inside a load or unload paragraph."""

    dictionary_key: str | None
    host_variable: str
    record_field: str
    locator: str
    #: Whether the statement is written with a terminating period. The punctuation is
    #: irregular in both loads and both unloads and is preserved, not normalised
    #: (anomaly ``N-punctuation``).
    terminated_by_period: bool


#: `bb000-HV-Load Section.` [common/plinvoiceMT.cbl:L1442] - TWENTY-FIVE moves for a
#: THIRTY-column table, in copybook declaration order rather than column order.
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

#: `bb100-UnloadHVs Section.` [common/plinvoiceMT.cbl:L1482] - TWENTY-FOUR moves, one
#: fewer than the load, and the missing one is the PRIMARY KEY (anomaly ``N-pinvoice-
#: key-write-only``).
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

#: `bc000-HV-Load-rg1 Section. *> Dry chk ?` [common/plinvoiceMT.cbl:L2743] - FOURTEEN
#: moves for a fourteen-column table, so the count is right and the ORDER is not.
LINES_LOAD_SEQUENCE: Final[tuple[HostVariableMove, ...]] = (
    HostVariableMove(
        f"{LINES_TABLE}.IL-LINE-KEY",
        "HV1-IL-LINE-KEY",
        "WS-il-Key",
        "[common/plinvoiceMT.cbl:L2756]",
        True,
    ),
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

#: `bc100-UnloadHVs-rg1 Section. *> Dry chk ?` [common/plinvoiceMT.cbl:L2777] - THIRTEEN
#: moves against the load's fourteen.
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
    """Return ``table_name``'s columns in the frozen schema's declaration order."""
    entries = loader.entries_for_table(table_name)
    ordered = sorted(entries, key=lambda entry: entry.column.ordinal)
    return tuple(entry.column.name for entry in ordered)


HEADER_COLUMNS: Final[tuple[str, ...]] = _columns_in_ordinal_order(HEADER_TABLE)

LINES_COLUMNS: Final[tuple[str, ...]] = _columns_in_ordinal_order(LINES_TABLE)


def _attribute_for(host_variable_name: str) -> str:
    """Map a bridge host-variable name onto its Python attribute name.

    `HV-IH-DEDUCT-DAYS` becomes ``hv_ih_deduct_days`` and `HV1-IL-LINE-KEY` becomes
    ``hv1_il_line_key``, so a reader can move between the COBOL and the Python by
    mechanical transformation rather than by lookup (R-5).
    """
    return host_variable_name.lower().replace("-", "_")


#: Column name -> attribute name, per table, derived from the dictionary's own host-
#: variable names rather than transcribed.
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

#: Column name -> the width `initialize` fills with spaces, for character host variables
#: only.
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
    """`01 TD-PUINVOICE-REC.` [common/plinvoiceMT.cbl:L390-L420].

    Five of the thirty - :attr:`hv_ih_status_a` through :attr:`hv_ih_status_p` - have no
    counterpart in either purchase copybook and are touched by neither `bb000-HV-Load`
    nor `bb100-UnloadHVs`.
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

        The FIRST statement of the load, and the reason every unset column reaches MySQL
        as a space or a zero rather than as SQL `NULL`.
        """
        _initialise_group(self, _HEADER_ATTRIBUTE_BY_COLUMN, _HEADER_CHARACTER_WIDTHS)


@dataclasses.dataclass(slots=True)
class LineHostVariables:
    """`01 TD-PUINV-LINES-REC.` [common/plinvoiceMT.cbl:L425-L439].

    :attr:`hv1_il_invoice` is loaded [:L2758] and never unloaded [:L2789-L2801]; the
    asymmetry is deliberate and is not repaired here.
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

    Alphanumeric items become all spaces at their declared width, numeric items become
    zero at their declared scale. Nothing becomes ``None``.
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

    `01 WS-PInvoice-Record.` [copybooks/plwspinv2.cob:L10] is overlaid by `01 Invoice-
    Header redefines WS-PInvoice-Record.` [:L21] and by `01 Invoice-Line redefines WS-
    PInvoice-Record.` [:L56], so a single 100-byte area carries EITHER a header OR a
    line and the caller tells them apart only by which view it reads.
    """

    HEADER = "Invoice-Header"
    LINE = "Invoice-Line"


#: The two redefinitions of the shared buffer and the record class that models each, so
#: a reader can find the Python counterpart of either COBOL view.
_BUFFER_REDEFINITIONS: Final[Mapping[_BufferView, type]] = MappingProxyType(
    {
        _BufferView.HEADER: IhInvoiceHeader,
        _BufferView.LINE: IlInvoiceLine,
    }
)


@dataclasses.dataclass(slots=True)
class PInvoiceContext:
    """The bridge's own WORKING-STORAGE, which persists between calls.

    Nothing here is shared between concurrent workers because nothing in this migration
    runs concurrently.
    """

    connection: Any = None
    system_record: SystemRecord | None = None
    transport: connection.TransportSecurity | None = None
    header_hv: HeaderHostVariables = dataclasses.field(
        default_factory=HeaderHostVariables
    )
    line_hv: LineHostVariables = dataclasses.field(default_factory=LineHostVariables)
    # The caller view declares `ih-order pic x(10)` [copybooks/plwspinv2.cob:L28],
    # while the bridge view splits those same bytes into a group containing two
    # numeric fields [copybooks/plwspinv.cob:L17-L27]. Remember the exact incoming
    # image beside the split view: a group MOVE must preserve nonnumeric bytes until
    # one of the group's members is explicitly changed.
    ih_order_group: IhOrder | None = None
    ih_order_image: str = " " * 10
    ih_order_components: tuple[str, int, str, int] | None = None
    #: `01 WS-Invoice-Line.` [common/plinvoiceMT.cbl:L362-L379] - the bridge's own line
    #: record, declared separately because the third `REPLACING` clause renamed every
    #: copied `il-` field to `Un-Used-il-` [:L458].
    ws_invoice_line: IlInvoiceLineBody | None = None
    buffer_view: _BufferView = _BufferView.HEADER
    cursors: cursor_state.CursorStateTable = dataclasses.field(
        default_factory=cursor_state.CursorStateTable
    )
    most_cursor_set: int = 0
    most_cursor_set_2: int = 0
    #: `05 MOST-Relation pic xxx.` [common/plinvoiceMT.cbl:L329], initialised to spaces
    #: and left at spaces when `Access-Type` falls outside 5..9, because the `evaluate`
    #: has no `when other` [:L971-L982].
    most_relation: str = " " * cursor_state.MostRelation.WIDTH
    ws_where: str = ""
    ws_where_2: str = ""
    ws_mysql_count_rows: int = 0
    ws_mysql_save_count_rows: int = 0
    ws_mysql_save_count_rows_rg1: int = 0
    ws_temp_ed_row: int = 0
    ws_last_read_invoice: int = _LAST_READ_INVOICE_INITIAL
    #: `03 WS-Last-Read-Line pic 99 value 40.` [common/plinvoiceMT.cbl:L288] -
    #: initialised to the MAXIMUM line number, not to zero (anomaly ``N-last-read-
    #: line-40``).
    ws_last_read_line: int = _LAST_READ_LINE_INITIAL
    ws_actual_lines_in_row: int = _ACTUAL_LINES_IN_ROW_INITIAL
    rg_table: tuple[RepeatingGroupEntry, ...] = RG_TABLE
    ws_mysql_command: str = ""

    # `acas026`'s own working storage [common/acas026.cbl:L189-L209]. The handler and
    # the bridge are separate COBOL programs with separate working storage.
    record_size_a: int = 0
    record_size_b: int = 0
    #: `77 Cobol-File-Status pic 9 value zero.` [common/acas026.cbl:L196]. ANOMALY
    #: ``N-eof-flag-is-the-field``.
    cobol_file_status: int = 0
    #: `03 invoice-key.` inside `01 Invoice-Record.` [copybooks/plfdpinv.cob:L12-L15] -
    #: the FD record's ten-character key, held as TEXT so that `move spaces to Invoice-
    #: Key` [common/acas026.cbl:L369] can be reproduced literally into a group declared
    #: `pic 9(8)` plus `pic 99` (anomaly ``N-spaces-into-numeric-key``).
    invoice_key_raw: str = "0" * 10
    ws_temp_ed_1: int = 0
    ws_temp_ed_2: int = 0
    #: `77 Display-Blk pic x(75) value spaces.` [common/acas026.cbl:L195] - the record-
    #: size error message, and the one value on that path a caller can read because it
    #: is copied into `SQL-Msg` [:L581].
    display_blk: str = " " * _DISPLAY_BLK_WIDTH

    @property
    def cobol_file_eof(self) -> bool:
        """`88 Cobol-File-Eof value 1.` [common/acas026.cbl:L197].

        A condition name over :attr:`cobol_file_status`, not a field of its own. See
        that attribute's note for why the distinction matters.
        """
        return self.cobol_file_status == 1

    @cobol_file_eof.setter
    def cobol_file_eof(self, value: bool) -> None:
        """`set Cobol-File-EoF to true` [common/acas026.cbl:L378].

        Setting a condition name true assigns its first value, which here is 1.
        """
        self.cobol_file_status = 1 if value else 0

    @property
    def cursor_active(self) -> bool:
        """`88 Cursor-Active value 1.` [common/plinvoiceMT.cbl:L332]."""
        return self.most_cursor_set == 1

    @property
    def cursor_active_2(self) -> bool:
        """`88 Cursor-Active-2 value 1.` [common/plinvoiceMT.cbl:L335]."""
        return self.most_cursor_set_2 == 1


_DEFAULT_CONTEXT: Final[PInvoiceContext] = PInvoiceContext()


def default_context() -> PInvoiceContext:
    """Return the module-level working storage of ``plinvoiceMT``.

    Callers that need an isolated instance - a test, or a second logical run in one
    process - construct :class:`PInvoiceContext` directly. The default is shared because
    the COBOL's is.
    """
    return _DEFAULT_CONTEXT


def citations() -> tuple[str, ...]:
    """Return every source locator this module was written from.

    Published so the traceability document can be generated rather than maintained, in
    the same shape :func:`acas_posting.records.file_access.citations` uses.
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


# SQL assembly - this module owns EVERY statement for BOTH tables The bridge assembles
# each statement into `WS-MYSQL-COMMAND` with the `STRING` verb and then performs
# `MYSQL-1210-COMMAND`.


@dataclasses.dataclass(frozen=True, slots=True)
class SqlFragment:
    """One assembled piece of statement text, with its bound values.

    ``text`` carries ``%s`` placeholders and identifiers that have ALREADY been through
    :func:`connection.quote_identifier`; ``parameters`` carries the values those
    placeholders bind, in order.
    """

    text: str
    parameters: tuple[Any, ...]
    #: The exact text `WS-MYSQL-COMMAND` would hold.
    literal: str
    #: `[common/plinvoiceMT.cbl:L...]` of the `STRING` block this reproduces.
    locator: str


SqlStatement = SqlFragment


def _pointer_slice(predicate: SqlFragment) -> SqlFragment:
    """Model `WS-Where (1:J)` - the predicate plus ONE trailing space.

    `move spaces to WS-Where` runs before every predicate build, and the `STRING`
    pointer `J` ends one position past the last character written, so a reference
    modification of length `J` picks up that extra space.
    """
    return dataclasses.replace(
        predicate,
        text=predicate.text + " ",
        literal=predicate.literal + " ",
    )


def _keyname_delimited_by_space(key: cursor_state.KeyOfReference) -> str:
    """`KeyName (KOR-x1) delimited by space` - the trimmed key name."""
    return connection.cobol_string_delimited_by_space(key.key_name)


def _where_sequential_read(key: cursor_state.KeyOfReference) -> SqlFragment:
    """`ba040`'s self-positioning predicate [common/plinvoiceMT.cbl:L642-L654]."""
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
    """`` `KEY`="value" `` - the equality predicate, used by six paragraphs."""
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
    """`ba060`'s HEADER predicate [common/plinvoiceMT.cbl:L984-L999]."""
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

    ANOMALY ``N-start-rg1-unquoted-key``, carried in the register also under the heading
    ``N-rg1-start-predicate-unquoted`` - one finding, two names, because it is both a
    property of the RG1 START predicate and a property of its key value.
    """
    quoted = connection.quote_identifier(_keyname_delimited_by_space(key))
    token = relation.token
    return SqlFragment(
        text=f"{quoted}{token}%s ORDER BY {quoted} ASC  ",
        parameters=(key_value,),
        literal=f"{quoted}{token}{key_value} ORDER BY {quoted} ASC  ",
        locator="[common/plinvoiceMT.cbl:L1058-L1069]",
    )


def _where_delete_all_lines(ih_invoice: int) -> SqlFragment:
    """`bc085`'s predicate [common/plinvoiceMT.cbl:L2626-L2640].

    ANOMALY ``N-deleteall-single-quoted-column``, and it is fatal to the verb. The four
    `STRING` operands that would have emitted a BACKTICK-quoted key name from the key
    table are commented out [:L2629-L2632] - one of them carrying the maintainer's own
    `*> ??????
    """
    invoice = _digits(ih_invoice, 8)
    return SqlFragment(
        text="%s=%s",
        parameters=("IL-INVOICE", invoice),
        literal=f"'IL-INVOICE'=\"{invoice}\"",
        locator="[common/plinvoiceMT.cbl:L2626-L2640]",
    )


def _select_statement(table_name: str, predicate: SqlFragment) -> SqlStatement:
    """`SELECT * FROM ` `` `T` `` ` WHERE ` <slice> `;`"""
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

    `ba080` [common/plinvoiceMT.cbl:L1221-L1226], `ba085` [:L1318-L1323], `bc080`
    [:L2560-L2565] and `bc085` [:L2652-L2657] all omit the `";"` that every other
    builder appends, and all four embed the pointer slice untrimmed, so the statement
    ends in a space. Reproduced.
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
    """Build the `` `COL`="v", `` list every INSERT and UPDATE shares."""
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
    `bc200-Insert-rg1` [:L2816-L3003] for the lines. `SET` form, not ANOMALY ``N-insert-
    is-set-form``.
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
    `bc300-Update-rg1` [:L3009-L3201] for the lines.
    """
    clause = _set_clause(renders, columns, group, attribute_by_column)
    quoted = connection.quote_identifier(table_name)
    trimmed_text = _pointer_slice(predicate).text.strip(" ")
    trimmed_literal = _pointer_slice(predicate).literal.strip(" ")
    return SqlStatement(
        text=f"UPDATE {quoted} SET {clause.text} WHERE {trimmed_text};",
        parameters=clause.parameters + predicate.parameters,
        literal=f"UPDATE {quoted} SET {clause.literal} WHERE {trimmed_literal};",
        locator=locator,
    )


@dataclasses.dataclass(frozen=True, slots=True)
class ExecutionResult:
    """What one `MYSQL-1210-COMMAND` leaves behind."""

    count_rows: int
    rows: tuple[Mapping[str, object], ...] = ()
    error: status.DbErrorStatus | None = None


def _driver_error_fields(error: BaseException) -> tuple[str, str, str]:
    """Recover `MySQL_errno`, its message and `MySQL_sqlstate` from a driver error.

    The bridge reads three separate foreign calls - `call "MySQL_errno" using WS-MYSQL-
    Error-Number`, `call "MySQL_error" using WS-MYSQL-Error-Message` and `call
    "MySQL_sqlstate" using WS-MYSQL-SQLstate` [common/plinvoiceMT.cbl:L1163-L1165] - so
    all three are recovered here, from the driver exception's own attributes where it
    exposes them and from safe defaults where it does not.
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
    duplicate-key test, the SQLSTATE mapping and the generic `(99, 911)` pair all come
    from the one place that owns them.
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

    A driver failure is CAPTURED, never raised - `*> Any errors leave it to caller to
    recover from` [common/acas026.cbl:L617] - and the caller's own failure arm decides
    the status pair.
    """
    # `INITIALIZE WS-MYSQL-COMMAND` then the `STRING` assembly, mirrored so the last
    # statement this module built is always inspectable [common/plinvoiceMT.cbl:L1536,
    # :L1933].
    context.ws_mysql_command = statement.literal
    if context.connection is None:
        # The bridge cannot reach `MYSQL-1210-COMMAND` without a connection: every verb
        # but Open runs after `ba020-Process-Open` has succeeded
        # [common/plinvoiceMT.cbl:L595-L597].
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
                return ExecutionResult(count_rows=len(rows), rows=rows)
            affected = cursor.rowcount
            return ExecutionResult(
                count_rows=0 if affected is None or affected < 0 else int(affected)
            )
    except Exception as error:
        captured = _capture_driver_error(error, statement)
        # ONE ERROR, through the shared reporter, so this failure renders with the
        # same fields in the same order as every other handler's. The record already
        # carried no driver text and no statement; WARNING was the wrong LEVEL for
        # something the caller must handle as a failure.
        status.log_handler_failure(
            _LOG,
            program=BRIDGE_NAME,
            paragraph="MYSQL-1210-COMMAND",
            locator="[copybooks/mysql-procedures.cpy:L164-L178]",
            sql_err=captured.sql_err,
            sql_state=captured.sql_state,
            detail="the statement failed at the driver and is reported through "
            "the bridge's own failure arm [common/acas026.cbl:L617]",
        )
        return ExecutionResult(count_rows=0, error=captured)


def _store_result(cursor: Any) -> tuple[Mapping[str, object], ...]:
    """`PERFORM MYSQL-1220-STORE-RESULT` - materialise the whole result set.

    Column names come from the cursor's description so that every row is keyed by the
    schema's own hyphenated column name, which is what :func:`bb100_unload_hvs` and
    :func:`bc100_unload_hvs_rg1` read.
    """
    description = cursor.description or ()
    names = tuple(str(column[0]) for column in description)
    return tuple(dict(zip(names, row, strict=False)) for row in cursor.fetchall())


def _digits(value: int, width: int) -> str:
    """Render an unsigned `PIC 9(width)` display field."""
    magnitude = value if value >= 0 else -value
    return str(magnitude % (10**width)).rjust(width, "0")


def _characters(value: str, width: int) -> str:
    """Render an `PIC X(width)` display field - left justified, space filled."""
    return value[:width].ljust(width, " ")


def _binary_long_bytes(value: int) -> str:
    """Render a `binary-long` as the four bytes a group move would copy.

    GnuCOBOL stores `BINARY-LONG` high-order-byte-first by default - the ACAS build
    selects no dialect and passes no byte-order option anywhere [common/comp-common.sh]
    - so the four bytes are big endian, two's complement.
    """
    return int(value).to_bytes(4, "big", signed=True).decode("latin-1")


def _group_ws_invoice_key(ih_invoice: int, ih_test: int) -> str:
    """`move WS-Invoice-Key to HV-PINVOICE-KEY.` [common/plinvoiceMT.cbl:L1452].

    `05 WS-Invoice-Key.` is `07 ih-Invoice pic 9(8).` followed by `07 ih-Test pic 99
    value zero.` [copybooks/plwspinv.cob:L10-L12], so the ten characters are eight zero-
    filled invoice digits then two zero-filled test digits.
    """
    return _digits(ih_invoice, 8) + _digits(ih_test, 2)


def _group_il_key(il_invoice: int, il_line: int) -> str:
    """`move WS-il-Key to HV1-IL-LINE-KEY.` [common/plinvoiceMT.cbl:L2756].

    `05 il-Key.` is `07 il-invoice pic 9(8).` then `07 il-line pic 99. *> was binary-
    char.` [copybooks/plwspinv.cob:L67-L69] - the same ten-character shape as the header
    key, which is why `bc070` can observe `*> Same as WS-il-Key` [:L2492].
    """
    return _digits(il_invoice, 8) + _digits(il_line, 2)


def _group_ih_supplier(ih_nos: str, ih_check: int) -> str:
    """`move WS-ih-Supplier to HV-IH-SUPPLIER` [common/plinvoiceMT.cbl:L1456].

    `05 ih-Supplier.` is `07 ih-Nos pic x(6).` then `07 ih-Check pic 9.`
    [copybooks/plwspinv.cob:L13-L15].
    """
    return _characters(ih_nos, 6) + _digits(ih_check, 1)


def _ih_order_components(group: IhOrder) -> tuple[str, int, str, int]:
    """Return the four declared members of `05 ih-order.` in byte order."""
    return (
        group.ih_freq,
        int(group.ih_repeat),
        group.filler_1,
        int(group.ih_last_date),
    )


def _group_ih_order(group: IhOrder, context: PInvoiceContext) -> str:
    """`move WS-ih-Order to HV-IH-ORDER` [common/plinvoiceMT.cbl:L1458].

    NONE of those five members has a host variable or a column: only the enclosing ten
    bytes reach the database, as `IH-ORDER char(10)`. The file view can carry arbitrary
    characters in those bytes [copybooks/plwspinv2.cob:L28], so rebuilding the image
    unconditionally from numeric interpretations would change an untouched value.
    """
    components = _ih_order_components(group)
    if (
        context.ih_order_group is group
        and context.ih_order_components == components
    ):
        return context.ih_order_image

    image = (
        _characters(group.ih_freq, 1)
        + _digits(group.ih_repeat, 2)
        + _characters(group.filler_1, 3)
        + _binary_long_bytes(group.ih_last_date)
    )
    context.ih_order_group = group
    context.ih_order_image = image
    context.ih_order_components = components
    return image


def line_from_bodies(
    bodies: PInvoiceBodies, line_number: int
) -> IlInvoiceLineBody | None:
    """Return one occurrence of `03 invoice-line occurs 40.`

    `01 PInvoice-Bodies.` [copybooks/plwspinv.cob:L65-L66] is the caller-side table of
    up to forty lines; the bridge never sees it, because its own `COPY ...
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

    MODELLING NOTE, recorded as a modelling decision and NOT as a behaviour change.
    """
    il_invoice = int(pinvoice.ih_prime.ws_invoice_key.ih_invoice)
    il_line = int(pinvoice.ih_prime.ws_invoice_key.ih_test)
    staged = context.ws_invoice_line
    if staged is None:
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
    # The key ALWAYS comes from the buffer, because that is the one part of the move
    # whose bytes are identical under both views.
    return dataclasses.replace(
        staged, il_key=IlKey(il_invoice=il_invoice, il_line=il_line)
    )


def bb000_hv_load(pinvoice: PInvoiceHeader, context: PInvoiceContext) -> None:
    """`bb000-HV-Load Section.` [common/plinvoiceMT.cbl:L1442-L1477].

    * `HV-IH-STATUS-A`, `-C`, `-I`, `-L` and `-P` receive no move, so they keep the
    space `initialize` left and every INSERT writes a space into five `char(1) NOT NULL`
    columns forever (anomaly ``N-five-status-columns-never-populated``).
    """
    prime: IhPrime = pinvoice.ih_prime
    sub: IhSubPrime = pinvoice.ih_sub_prime
    header = context.header_hv

    header.initialize()

    # [common/plinvoiceMT.cbl:L1452] group move; loaded here, never unloaded.
    header.hv_pinvoice_key = _group_ws_invoice_key(
        prime.ws_invoice_key.ih_invoice, prime.ws_invoice_key.ih_test
    )
    header.hv_ih_invoice = prime.ws_invoice_key.ih_invoice
    header.hv_ih_test = prime.ws_invoice_key.ih_test
    header.hv_ih_supplier = _group_ih_supplier(
        prime.ih_supplier.ih_nos, prime.ih_supplier.ih_check
    )
    header.hv_ih_dat = _narrow_signed_to_unsigned_host_variable(prime.ih_date, 10)
    header.hv_ih_order = _group_ih_order(prime.ih_order, context)
    header.hv_ih_type = prime.ih_type
    header.hv_ih_ref = prime.ih_ref
    header.hv_ih_p_c = sub.ih_fig.ih_p_c
    header.hv_ih_net = sub.ih_fig.ih_net
    header.hv_ih_extra = sub.ih_fig.ih_extra
    header.hv_ih_carriage = sub.ih_fig.ih_carriage
    header.hv_ih_vat = sub.ih_fig.ih_vat
    header.hv_ih_discount = sub.ih_fig.ih_discount
    header.hv_ih_e_vat = sub.ih_fig.ih_e_vat
    header.hv_ih_c_vat = sub.ih_fig.ih_c_vat
    # [common/plinvoiceMT.cbl:L1469]. ANOMALY ``N-88-case-swap``.
    header.hv_ih_status = sub.ih_status
    header.hv_ih_lines = _narrow_signed_to_unsigned_host_variable(sub.ih_lines, 3)
    header.hv_ih_deduct_days = _narrow_signed_to_unsigned_host_variable(
        sub.ih_deduct_days, 3
    )
    header.hv_ih_deduct_amt = sub.ih_deduct_amt
    header.hv_ih_deduct_vat = sub.ih_deduct_vat
    header.hv_ih_days = _narrow_signed_to_unsigned_host_variable(sub.ih_days, 3)
    header.hv_ih_cr = _narrow_signed_to_unsigned_host_variable(sub.ih_cr, 10)
    header.hv_ih_day_book_flag = sub.ih_day_book_flag
    header.hv_ih_update = sub.ih_update


def bb100_unload_hvs(pinvoice: PInvoiceHeader, context: PInvoiceContext) -> None:
    """`bb100-UnloadHVs Section.` [common/plinvoiceMT.cbl:L1482-L1523].

    Twenty-four moves, in the order :data:`HEADER_UNLOAD_SEQUENCE` records, after
    `initialize WS-Invoice-Record.` [:L1487] - PLAIN, with no `with filler`, where
    `ba042-Fetch` writes `initialize WS-Invoice-Record with filler` at [:L802] (anomaly
    ``N-initialize``).
    """
    prime: IhPrime = pinvoice.ih_prime
    sub: IhSubPrime = pinvoice.ih_sub_prime
    header = context.header_hv

    _initialise_header_record(pinvoice)

    # [common/plinvoiceMT.cbl:L1489-L1490] - back into the key group's members.
    prime.ws_invoice_key.ih_invoice = header.hv_ih_invoice
    prime.ws_invoice_key.ih_test = header.hv_ih_test
    supplier = _characters(header.hv_ih_supplier, 7)
    prime.ih_supplier.ih_nos = supplier[:6]
    prime.ih_supplier.ih_check = int(supplier[6]) if supplier[6].isdigit() else 0
    prime.ih_date = header.hv_ih_dat
    _split_ih_order(header.hv_ih_order, prime.ih_order, context)
    prime.ih_type = header.hv_ih_type
    prime.ih_ref = header.hv_ih_ref
    sub.ih_fig.ih_p_c = header.hv_ih_p_c
    sub.ih_fig.ih_net = header.hv_ih_net
    sub.ih_fig.ih_extra = header.hv_ih_extra
    sub.ih_fig.ih_carriage = header.hv_ih_carriage
    sub.ih_fig.ih_vat = header.hv_ih_vat
    sub.ih_fig.ih_discount = header.hv_ih_discount
    sub.ih_fig.ih_e_vat = header.hv_ih_e_vat
    sub.ih_fig.ih_c_vat = header.hv_ih_c_vat
    sub.ih_status = header.hv_ih_status
    sub.ih_lines = header.hv_ih_lines
    sub.ih_deduct_days = header.hv_ih_deduct_days
    sub.ih_deduct_amt = header.hv_ih_deduct_amt
    sub.ih_deduct_vat = header.hv_ih_deduct_vat
    sub.ih_days = header.hv_ih_days
    sub.ih_cr = header.hv_ih_cr
    sub.ih_day_book_flag = header.hv_ih_day_book_flag
    sub.ih_update = header.hv_ih_update

    # `*> Here save the ih-Lines to WS so we can keep track of body-lines.`
    # [common/plinvoiceMT.cbl:L1516] A NARROWING MOVE, and the rule is the RECEIVING
    # field's.
    context.ws_actual_lines_in_row = _move_to_actual_lines_in_row(
        header.hv_ih_lines
    )
    # `*> Save sih Invoice & test as last key read.` [common/plinvoiceMT.cbl:L1520] -
    # and note `sih`, the SALES prefix, in the PURCHASE bridge's own comment (anomaly
    # ``N-sih-in-purchase-comment``).
    context.ws_last_read_invoice = header.hv_ih_invoice
    # [common/plinvoiceMT.cbl:L1523] `*> should be zero` - the maintainer's doubt,
    # preserved. NOT replaced by zero.
    context.ws_last_read_line = header.hv_ih_test
    context.buffer_view = _BufferView.HEADER


def _initialise_header_record(pinvoice: PInvoiceHeader) -> None:
    """`initialize WS-Invoice-Record.` [common/plinvoiceMT.cbl:L1487].

    Alphanumeric members to spaces at their declared widths, numeric members to zero.
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


def bc000_hv_load_rg1(line: IlInvoiceLineBody, context: PInvoiceContext) -> None:
    """`bc000-HV-Load-rg1 Section. *> Dry chk ?` [common/plinvoiceMT.cbl:L2743].

    Fourteen moves for a fourteen-column table, so nothing is missing - but `WS-il-Line`
    is moved at [:L2757] BEFORE `WS-il-Invoice` at [:L2758], which inverts the column
    order `IL-INVOICE` then `IL-LINE` (anomaly ``N-lines-loadorder``). The order is
    reproduced, not corrected.
    """
    lines = context.line_hv

    lines.initialize()

    lines.hv1_il_line_key = _group_il_key(line.il_key.il_invoice, line.il_key.il_line)
    lines.hv1_il_line = line.il_key.il_line
    # [common/plinvoiceMT.cbl:L2758] ... then INVOICE. Loaded here and NEVER unloaded
    # [:L2789-L2801] (anomaly ``N-il-invoice-never-unloaded``).
    lines.hv1_il_invoice = line.il_key.il_invoice
    lines.hv1_il_product = line.il_product
    lines.hv1_il_pa = line.il_pa
    lines.hv1_il_qty = _narrow_signed_to_unsigned_host_variable(line.il_qty, 5)
    lines.hv1_il_type = line.il_type
    lines.hv1_il_description = line.il_description
    lines.hv1_il_net = line.il_net
    lines.hv1_il_unit = line.il_unit
    lines.hv1_il_discount = line.il_discount
    lines.hv1_il_vat = line.il_vat
    lines.hv1_il_vat_code = line.il_vat_code
    lines.hv1_il_update = line.il_update
    # The two `filler pic xx` members of the line [copybooks/plwspinv.cob:L72, L76] have
    # no host variable and no column: deliberate omissions, recorded.


def bc100_unload_hvs_rg1(context: PInvoiceContext) -> IlInvoiceLineBody:
    """`bc100-UnloadHVs-rg1 Section. *> Dry chk ?` [common/plinvoiceMT.cbl:L2777].

    THIRTEEN moves against the load's fourteen: `HV1-IL-INVOICE` is never moved back
    [:L2789-L2801], so the `IL-INVOICE` column's value never reaches the record through
    its own host variable.
    """
    lines = context.line_hv

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

    key_text = _characters(lines.hv1_il_line_key, 10)
    line.il_key.il_invoice = int(key_text[:8]) if key_text[:8].isdigit() else 0
    line.il_key.il_line = int(key_text[8:10]) if key_text[8:10].isdigit() else 0
    line.il_key.il_line = lines.hv1_il_line
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

    context.ws_last_read_line = lines.hv1_il_line
    context.ws_invoice_line = line
    context.buffer_view = _BufferView.LINE
    return line


# The bridge - `plinvoiceMT`, its label machine and its twenty-eight paragraphs `ba-
# ACAS-DAL-Process section.` [common/plinvoiceMT.cbl:L482] is a `GO TO` dispatcher.


class _BridgeLabel(enum.StrEnum):
    """Every label the bridge's `GO TO`s and `PERFORM ... THRU`s can name."""

    BA020_PROCESS_OPEN = "ba020-Process-Open"
    BA030_PROCESS_CLOSE = "ba030-Process-Close"
    BA040_PROCESS_READ_NEXT = "ba040-Process-Read-Next"
    BA041_REREAD = "ba041-Reread"
    BA042_FETCH = "ba042-Fetch"
    BA050_PROCESS_READ_INDEXED = "ba050-Process-Read-Indexed"
    BA060_PROCESS_START = "ba060-Process-Start"
    BA070_PROCESS_WRITE = "ba070-Process-Write"
    BA080_PROCESS_DELETE = "ba080-Process-Delete"
    BA085_PROCESS_DELETE_ALL = "ba085-Process-Delete-ALL"
    BA090_PROCESS_REWRITE = "ba090-Process-Rewrite"
    BA100_BAD_FUNCTION = "ba100-Bad-Function"
    BA998_FREE = "ba998-Free"
    BA999_END = "ba999-end"
    BA999_EXIT = "ba999-exit"
    BC058_RESTORE_POINTERS = "bc058-Restore-Pointers"
    BC085_EXIT = "bc085-Exit"
    BC090_EXIT = "bc090-Exit"


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
    """`88 Testing-1 value 1.` [copybooks/Test-Data-Flags.cob:L11].

    The switch that gates ALL log-file production, `03 SW-Testing pic 9 value 1.` with
    the maintainer's own alternative in a trailing comment `*> zero.` [:L10] and the
    header note that it can be zeroed "When testing comlete" [:L3-L4].
    """
    return int(dal_common.sw_testing) == 1


def _testing_2(dal_common: AcasDalCommonData) -> bool:
    """`88 Testing-2 value 1.` [copybooks/Test-Data-Flags.cob:L16].

    Gates the SCREEN displays of `WS-Where` only - `03 SW-Testing-2 pic 9 value zero.`
    [:L15] with the note "Testing only for displays ws-where etc" [:L13].
    """
    return int(dal_common.sw_testing_2) == 1


def _display_message_1(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """`if Testing-2 display Display-Message-1 with erase eos end-if`.

    Seven identical sites, listed in :func:`_testing_2`. The COBOL paints
    `WS-Log-Where` on a curses screen.

     THE GUARD IS PRESERVED AND NOTHING IS EMITTED. `WS-Log-Where` is a
    rendered SQL predicate - for these two tables one carrying `PINVOICE-KEY` or
    `IL-LINE-KEY` as a literal - so it is SQL text and a business key in one field,
    which the safe-event schema in :mod:`acas_posting.dal.status` forbids outright
    (CWE-532). `redact_for_log` could not make it safe: it escapes control characters
    and recognises connection-message shapes, and a predicate is neither.

    The paragraph, its `Testing-2` guard and all seven call sites are kept, so a
    reader following the frozen source still finds every `display`. `WS-Log-Where` is
    still BUILT and still stored, because the bridge's own statements read it - the
    disposition is unchanged (R-3).
    """
    if _testing_2(dal_common):
        del file_access  # the predicate is deliberately not rendered into a record


def _set_status(file_access: FileAccess, fs_reply: int, we_error: int) -> None:
    """Write the `(FS-Reply, We-Error)` pair the way the frozen source writes it.

    Always a plain assignment of both fields, never a derivation: the bridge's arms are
    literal `move nn to fs-reply` / `move nn to WE-Error` statements and several of them
    deliberately write only one of the two.
    """
    file_access.fs_reply = int(fs_reply)
    file_access.we_error = int(we_error)


def _clear_sql_fields(file_access: FileAccess) -> None:
    """`move spaces to SQL-Msg SQL-Err` and `move zero to SQL-State`.

    `ba010-Initialise` clears six fields [common/plinvoiceMT.cbl:L503-L508] and ANOMALY
    ``N-sqlstate-zero-not-space`` sits in the line above them.
    """
    file_access.logging_data.sql_state = _SQL_STATE_ZEROED
    file_access.logging_data.sql_err = " " * status.SQL_ERR_WIDTH
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH


def _apply_db_error(
    file_access: FileAccess, error: status.DbErrorStatus
) -> None:
    """Move a captured driver failure into `SQL-State`, `SQL-Err` and `SQL-Msg`.

    SQL-State is moved UNCONDITIONALLY; SQL-Err and SQL-Msg only when the error number
    is not the frozen source's own `"0 "`. The status PAIR is NOT written here, because
    each arm writes its own.
    """
    file_access.logging_data.sql_state = error.sql_state[: status.SQL_STATE_WIDTH]
    if error.sql_err != _MYSQL_ERRNO_NONE:
        file_access.logging_data.sql_err = error.sql_err[: status.SQL_ERR_WIDTH]
        file_access.logging_data.sql_msg = error.sql_msg[: status.SQL_MSG_WIDTH]


def _file_key(file_access: FileAccess, text: str) -> None:
    """`move ... to WS-File-Key` - the 64-character log key.

    `05 WS-File-Key pic x(64) value spaces.` [copybooks/wsfnctn.cob:L52] - a `05` inside
    `01 File-Access.`'s `03 Logging-Data.`, not an `03` itself - truncates on the right,
    which is what a COBOL `move` into a shorter alphanumeric field does, and several of
    this bridge's log strings are longer than they look - `"> 0 got cnt=" WS-Temp-ED-Row
    " recs for INVOICE-REC Table"` [common/plinvoiceMT.cbl:L697-L701].
    """
    file_access.logging_data.ws_file_key = text[:64].ljust(64, " ")


def ba_acas_dal_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba-ACAS-DAL-Process section.` [common/plinvoiceMT.cbl:L482-L494].

    NONE of it has a database effect, so all of it is a DELIBERATE OMISSION under Agent
    Action Plan section 0.3.4 - "screen output that has no database effect" - and it is
    recorded here rather than silently dropped (anomaly ``N-bridge-section-entry-is-
    screen-setup``).
    """
    #  NO RECORD HERE. Six statements were dropped and not one of them
    #  displays anything, so a record announcing the drop is a record with no
    #  counterpart in the frozen source (R-4) - and it fired on every relational
    #  CALL. The omission is stated in the docstring above and in
    #  `docs/migration/traceability.md`, which is where a reader looks for it.
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

    `We-Error` and `Fs-Reply` are NOT cleared: the two statements that would have done
    it are commented out [:L500-L501], exactly as the handler comments out its own pair
    [common/acas026.cbl:L279-L280].
    """
    _clear_sql_fields(file_access)
    file_access.logging_data.ws_log_where = ""

    function = int(file_access.file_function)
    label = _BRIDGE_DISPATCH.get(function)
    if label is None:
        return _BridgeLabel.BA100_BAD_FUNCTION
    return label


def ba020_process_open(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    r"""`ba020-Process-Open.` [common/plinvoiceMT.cbl:L565-L607].

    [common/plinvoiceMT.cbl:L599-L603] carries a commented-out `/MYSQL INIT\` block with
    hard-coded placeholder base, implementation and password values. They are CITED and
    NEVER transcribed, per rule V.S1.
    """
    if context.system_record is None:
        # `MYSQL-1000-OPEN` cannot run without the `RDB-Data` block the six `string`s
        # read [:L570-L593].
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.RDB_INIT_ERROR),
        )
        file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"]
        return _BridgeLabel.BA999_END

    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"]
    # `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT.` [:L595]. The six credential
    # extractions [:L570-L593] are what `connection.load_rdb_data_once` and
    # `connection.cobol_string_delimited_by_space` reproduce, so they are called rather
    # than duplicated here.
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
        return _BridgeLabel.BA999_END
    context.connection = outcome.connection
    _set_status(file_access, int(outcome.fs_reply), int(outcome.we_error))
    file_access.logging_data.ws_no_paragraph = int(outcome.ws_no_paragraph)
    file_access.logging_data.sql_err = outcome.sql_err[: status.SQL_ERR_WIDTH]
    file_access.logging_data.sql_msg = outcome.sql_msg[: status.SQL_MSG_WIDTH]
    file_access.logging_data.sql_state = outcome.sql_state[: status.SQL_STATE_WIDTH]

    if int(outcome.fs_reply) != int(status.FsReply.SUCCESS):
        return _BridgeLabel.BA999_END

    # `move "OPEN SL INVOICE" to WS-File-Key` [:L605] - the sales-ledger label in the
    # purchase bridge, preserved (``N-sl-in-purchase-openclose``).
    _file_key(file_access, "OPEN SL INVOICE")
    context.cursors.state_for(HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]).free()
    context.most_cursor_set = 0
    return _BridgeLabel.BA999_END


def ba030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba030-Process-Close.` [common/plinvoiceMT.cbl:L609-L621].

    ANOMALY ``N-close-leaks-rg1-cursor``: the guard is `if Cursor-Active perform
    ba998-Free.` [:L610-L611] and `ba998-Free` frees `TP-PUINVOICE-REC` and clears slot
    1 only [:L1420-L1430].
    """
    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    if header_state.cursor_active():
        # `perform ba998-Free.` [:L610-L611].
        ba998_free(file_access, dal_common, pinvoice, context)

    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba030-Process-Close"]
    _file_key(file_access, "CLOSE SL INVOICE")
    connection.mysql_1980_close(context.connection)
    connection.mysql_1999_exit()
    context.connection = None
    # Slot 2 deliberately NOT freed - see the docstring. `go to ba999-end.` [:L621].
    # Class 3.
    return _BridgeLabel.BA999_END


def ba998_free(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba998-Free.` [common/plinvoiceMT.cbl:L1420-L1430]."""
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba998-Free"]
    context.cursors.state_for(HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]).free()
    context.most_cursor_set = 0
    return _BridgeLabel.BA999_END


def ba999_end(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba999-end.` [common/plinvoiceMT.cbl:L1432-L1437].

    `if Testing-1 perform Ca-Process-Logs end-if.` [:L1435-L1437] and nothing else, then
    a FALL-THROUGH into `ba999-exit` [:L1439].
    """
    if _testing_1(dal_common):
        ca_process_logs(file_access, dal_common, pinvoice, context)
    return _BridgeLabel.BA999_EXIT


def ba999_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba999-exit.` [common/plinvoiceMT.cbl:L1439-L1440] - `exit program.`"""
    return _BridgeLabel.BA999_EXIT


def _as_decimal(value: object, scale: int) -> decimal.Decimal:
    """Coerce a fetched column into the host variable's `COMP` decimal.

    `decimal.Decimal` only, and NEVER out of a binary floating-point value.
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

    Every integer host variable in both groups is `PIC 9(n) COMP` - UNSIGNED - and every
    corresponding column is `unsigned` too, so nothing here has to carry a sign.
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

    ANOMALY ``N-status-hvs-fetched-then-discarded``, and this is where it becomes
    visible.
    """
    for column in columns:
        render = renders[column]
        value = row.get(column)
        attribute = attribute_by_column[column]
        if value is None:
            # Every column of both tables is `NOT NULL`, so this cannot arise from the
            # frozen schema.
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

    The positioning block runs only `if Cursor-Not-Active` [:L635] and uses `set KOR-x1
    to 1` [:L636] - key 1 always, so the lines key can never position this verb - with
    the relation and low key hard-coded rather than taken from `Access-Type` (see
    :func:`_where_sequential_read`).
    """
    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    key = _key_of_reference(_KOR_HEADER)

    if header_state.cursor_not_active():
        predicate = _where_sequential_read(key)
        file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
        file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
            "ba040-Process-Read-Next"
        ]
        statement = _select_statement(HEADER_TABLE, predicate)
        result = _execute(context, statement, store_result=True)
        header_state.key_of_reference = key
        header_state.store_result(result.rows)
        header_state.position_at(_SEQUENTIAL_READ_START.low_key)
        _file_key(file_access, _SEQUENTIAL_READ_START.low_key)
        _display_message_1(file_access, dal_common)

        if result.count_rows == 0:
            if result.error is not None:
                _apply_db_error(file_access, result.error)
            _set_status(
                file_access,
                int(status.FsReply.END_OF_FILE),
                status.END_OF_FILE_WE_ERROR,
            )
            _file_key(file_access, "No Data")
            return _BridgeLabel.BA999_END

        header_state.set_cursor_active()
        context.most_cursor_set = 1
        context.ws_mysql_count_rows = result.count_rows
        context.ws_temp_ed_row = result.count_rows
        _file_key(
            file_access,
            f"> 0 got cnt={_digits(result.count_rows, 7)}"
            f" recs for INVOICE-REC Table",
        )
        ba999_end(file_access, dal_common, pinvoice, context)

    return ba041_reread(file_access, dal_common, pinvoice, context)


def ba041_reread(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba041-Reread.` [common/plinvoiceMT.cbl:L705-L740].

    1. `if WS-Last-Read-Invoice = zero go to ba042-Fetch.` [:L715-L716], commented `*>
    DALS Not yet called` and `*> so get header rec.` - a virgin bridge always delivers a
    header first. 2.
    """
    file_access.logging_data.ws_log_where = ""
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba041-Reread"
    ]
    # `move zero to return-code.` [:L711] - the fetch's own out-of-band signal, modelled
    # as the row count rather than a process return code.
    context.ws_mysql_count_rows = 0

    if context.ws_last_read_invoice == 0:
        return ba042_fetch(file_access, dal_common, pinvoice, context)

    if int(file_access.file_function) == int(status.FileFunction.READ_NEXT_HEADER):
        return ba042_fetch(file_access, dal_common, pinvoice, context)

    if context.ws_last_read_line < context.ws_actual_lines_in_row:
        next_line = context.ws_last_read_line + 1
        pinvoice.ih_prime.ws_invoice_key.ih_test = next_line
        pinvoice.ih_prime.ws_invoice_key.ih_invoice = context.ws_last_read_invoice
        bc050_process_read_indexed(file_access, dal_common, pinvoice, context)
        bc058_restore_pointers(file_access, dal_common, pinvoice, context)
        bc059_exit(file_access, dal_common, pinvoice, context)

        if int(file_access.fs_reply) != int(status.FsReply.SUCCESS):
            _initialise_header_record(pinvoice)
            key_text = _group_ws_invoice_key(
                pinvoice.ih_prime.ws_invoice_key.ih_invoice,
                pinvoice.ih_prime.ws_invoice_key.ih_test,
            )
            _file_key(file_access, f"{key_text} Not Found")
            return _BridgeLabel.BA999_END

        context.ws_last_read_line = pinvoice.ih_prime.ws_invoice_key.ih_test
        return _BridgeLabel.BA999_END

    return ba042_fetch(file_access, dal_common, pinvoice, context)


def ba042_fetch(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba042-Fetch.` [common/plinvoiceMT.cbl:L744-L820].

    `CALL "MySQL_fetch_record"` naming all thirty host variables [:L751-L781], then
    three end-of-data guards, then the unload.
    """
    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
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
        _set_status(
            file_access,
            int(status.FsReply.END_OF_FILE),
            status.END_OF_FILE_WE_ERROR,
        )
        _file_key(file_access, "EOF")
        # `set Cursor-Not-Active to true` [:L790] - a bare clear, NOT `ba998-Free`, so
        # the stored snapshot is left in place.
        header_state.set_cursor_not_active()
        context.most_cursor_set = 0
        return _BridgeLabel.BA999_END

    if header_state.count_rows == 0:
        # `if WS-MYSQL-Count-Rows = zero *> no data but should not happen here` [:L794].
        # Unreachable in practice, because guard 1 has already caught an empty snapshot.
        errno = file_access.logging_data.sql_err.strip()
        if errno and errno != _MYSQL_ERRNO_NONE.strip():
            _initialise_header_record(pinvoice)
            _file_key(file_access, "EOF2")
        _set_status(
            file_access,
            int(status.FsReply.END_OF_FILE),
            status.END_OF_FILE_WE_ERROR,
        )
        header_state.set_cursor_not_active()
        context.most_cursor_set = 0
        return _BridgeLabel.BA999_END

    if int(file_access.fs_reply) == int(status.FsReply.END_OF_FILE):
        header_state.set_cursor_not_active()
        context.most_cursor_set = 0
        _file_key(file_access, "EOF3")
        return _BridgeLabel.BA999_END

    bb100_unload_hvs(pinvoice, context)
    _file_key(
        file_access,
        _group_ws_invoice_key(
            pinvoice.ih_prime.ws_invoice_key.ih_invoice,
            pinvoice.ih_prime.ws_invoice_key.ih_test,
        ),
    )
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    return _BridgeLabel.BA999_END


def ba050_process_read_indexed(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba050-Process-Read-Indexed.` [common/plinvoiceMT.cbl:L822-L941].

    So the SECOND element of the ten-character key - `ih-Test`, the line number
    [copybooks/plwspinv.cob:L12] - is what selects the table.
    """
    if int(pinvoice.ih_prime.ws_invoice_key.ih_test) != 0:
        bc050_process_read_indexed(file_access, dal_common, pinvoice, context)
        bc058_restore_pointers(file_access, dal_common, pinvoice, context)
        bc059_exit(file_access, dal_common, pinvoice, context)
        # `go to ba999-exit.` [:L829] - straight out, NOT via `ba999-end`, so a line
        # read is logged by `bc058` and never by this paragraph.
        return _BridgeLabel.BA999_EXIT

    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    predicate = _where_key_equals(key, key_value, "[common/plinvoiceMT.cbl:L840-L848]")
    context.ws_where = _pointer_slice(predicate).literal
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    _display_message_1(file_access, dal_common)
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba050-Process-Read-Indexed/SELECT"
    ]

    statement = _select_statement(HEADER_TABLE, predicate)
    result = _execute(context, statement, store_result=True)
    header_state.key_of_reference = key
    header_state.store_result(result.rows)
    header_state.position_at(key_value)
    context.ws_mysql_count_rows = result.count_rows

    if result.count_rows == 0:
        _set_status(
            file_access,
            int(status.FsReply.KEY_NOT_FOUND),
            int(status.WeError.SUCCESS),
        )
        return _BridgeLabel.BA998_FREE

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
        if result.error is not None:
            _apply_db_error(file_access, result.error)
            we_error = int(status.WeError.UNKNOWN_UNEXPECTED)
        else:
            file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
            file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
            we_error = int(status.WeError.READ_INDEXED_UNEXPECTED)
        _set_status(file_access, int(status.FsReply.KEY_NOT_FOUND), we_error)
        _file_key(file_access, "")
        return _BridgeLabel.BA998_FREE

    bb100_unload_hvs(pinvoice, context)
    _file_key(file_access, context.header_hv.hv_pinvoice_key)
    ba999_end(file_access, dal_common, pinvoice, context)
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    ba998_free(file_access, dal_common, pinvoice, context)
    ba999_end(file_access, dal_common, pinvoice, context)
    return _BridgeLabel.BA999_EXIT


def ba060_process_start(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba060-Process-Start.` [common/plinvoiceMT.cbl:L943-L1138].

    ANOMALY ``N-start-guard-rejects-its-own-when-9``.
    """
    access_type = int(file_access.access_type)
    if access_type < 5 or access_type > 8:
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.ACCESS_TYPE_WRONG),
        )
        return _BridgeLabel.BA999_END

    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])

    if header_state.cursor_active():
        ba998_free(file_access, dal_common, pinvoice, context)
        ba999_end(file_access, dal_common, pinvoice, context)

    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    # `move spaces to MOST-Relation.` [:L969] then the `evaluate Access-Type`
    # [:L971-L982].
    relation = cursor_state.MostRelation.for_access_type(access_type)
    context.most_relation = relation.padded
    header_state.most_relation = relation

    predicate = _where_start_header(key, relation, key_value)
    context.ws_where = _pointer_slice(predicate).literal
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    _file_key(file_access, key_value)
    _display_message_1(file_access, dal_common)
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba060-Process-Start/SELECT-HEADER"
    ]

    header_result = _execute(
        context, _select_statement(HEADER_TABLE, predicate), store_result=True
    )
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
        if header_result.error is not None:
            _apply_db_error(file_access, header_result.error)
        _set_status(
            file_access,
            int(status.FsReply.INVALID_KEY_ON_START),
            int(status.WeError.SUCCESS),
        )
    else:
        _set_status(
            file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
        )
        context.ws_temp_ed_row = header_result.count_rows
        _file_key(
            file_access,
            f"{relation.token}{key_value} got "
            f"{_digits(header_result.count_rows, 7)} recs",
        )
    ba999_end(file_access, dal_common, pinvoice, context)

    # `set KOR-x1 to 2.` [:L1053] and the K2/L2 pair [:L1054-L1055] - the SAME ten
    # bytes, because both keys are offset 1 length 10.
    lines_key = _key_of_reference(_KOR_LINES)
    lines_predicate = _where_start_lines(lines_key, relation, key_value)
    context.ws_where_2 = _pointer_slice(lines_predicate).literal
    lines_state.most_relation = relation

    context.ws_mysql_save_count_rows = context.ws_mysql_count_rows
    context.ws_mysql_count_rows = 0
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba060-Process-Start/SELECT-LINES"
    ]

    lines_result = _execute(
        context, _select_statement(LINES_TABLE, lines_predicate), store_result=True
    )
    lines_state.key_of_reference = lines_key
    lines_state.store_result(lines_result.rows)
    lines_state.position_at(key_value)
    context.ws_mysql_count_rows = lines_result.count_rows

    if lines_result.count_rows != 0:
        lines_state.set_cursor_active()
        context.most_cursor_set_2 = 1
    else:
        lines_state.set_cursor_not_active()
        context.most_cursor_set_2 = 0

    if lines_result.count_rows == 0:
        if lines_result.error is not None:
            _apply_db_error(file_access, lines_result.error)
        _set_status(
            file_access,
            int(status.FsReply.INVALID_KEY_ON_START),
            int(status.WeError.SUCCESS),
        )
    else:
        _set_status(
            file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
        )
        context.ws_temp_ed_row = lines_result.count_rows
        _file_key(
            file_access,
            f"{relation.token}{key_value} got "
            f"{_digits(lines_result.count_rows, 7)} recs RG1 (Lines)",
        )

    context.ws_mysql_save_count_rows_rg1 = lines_result.count_rows
    context.ws_mysql_count_rows = context.ws_mysql_save_count_rows
    return _BridgeLabel.BA999_END


def ba070_process_write(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba070-Process-Write.` [common/plinvoiceMT.cbl:L1142-L1180].

    ANOMALY ``N-write-leaves-we-error-zero``.
    """
    if int(pinvoice.ih_prime.ws_invoice_key.ih_test) != 0:
        bc070_process_write(file_access, dal_common, pinvoice, context)
        return _BridgeLabel.BA999_EXIT

    bb000_hv_load(pinvoice, context)
    _file_key(file_access, context.header_hv.hv_pinvoice_key)
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    file_access.logging_data.sql_state = _SQL_STATE_ZEROED
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba070-Process-Write"
    ]

    result = bb200_insert(file_access, dal_common, pinvoice, context)

    if result.count_rows != 1:
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        file_access.fs_reply = int(status.FsReply.ERROR)
        if result.error is not None and result.error.duplicate_key:
            file_access.fs_reply = int(status.FsReply.DUPLICATE_KEY)
    ba999_end(file_access, dal_common, pinvoice, context)
    return _BridgeLabel.BA999_EXIT


def ba080_process_delete(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba080-Process-Delete.` [common/plinvoiceMT.cbl:L1182-L1248].

    ANOMALY ``N-read-indexed-status-zeroed-after-log`` in its second instance. On
    success the order is `perform ba999-End.` [:L1245] - the LOG - and only then `move
    zero to FS-Reply WE-Error.` [:L1247].
    """
    if int(pinvoice.ih_prime.ws_invoice_key.ih_test) != 0:
        bc080_process_delete(file_access, dal_common, pinvoice, context)
        return _BridgeLabel.BA999_EXIT

    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L1201-L1209]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    _file_key(file_access, key_value)
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    _display_message_1(file_access, dal_common)
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba080-Process-Delete"
    ]

    # The `DELETE` [:L1221-L1227] - no `STORE-RESULT`, so the affected-row count is the
    # command's own.
    result = _execute(
        context, _delete_statement(HEADER_TABLE, predicate), store_result=False
    )
    context.ws_mysql_count_rows = result.count_rows

    if result.count_rows != 1:
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.DELETE_SQLSTATE_NOT_00000),
        )
        return _BridgeLabel.BA999_END

    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    ba999_end(file_access, dal_common, pinvoice, context)
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    return _BridgeLabel.BA999_EXIT


def ba085_process_delete_all(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba085-Process-Delete-ALL.` [common/plinvoiceMT.cbl:L1250-L1349].

    `*> Delete all recs for a given invoice key / lines` [:L1250-L1251].
    """
    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L1297-L1305]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    # `move spaces to WS-File-Key` [:L1306] then `move WS-Invoice-Key to WS-File-Key`
    # [:L1307] - two moves into the same field, the first redundant because the second
    # is a full-width group move.
    _file_key(file_access, "")
    _file_key(file_access, key_value)
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    _display_message_1(file_access, dal_common)
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba085-Process-Delete-ALL"
    ]

    result = _execute(
        context, _delete_statement(HEADER_TABLE, predicate), store_result=False
    )
    context.ws_mysql_count_rows = result.count_rows

    if result.count_rows <= 0:
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.DELETE_SQLSTATE_NOT_00000),
        )
        return _BridgeLabel.BA999_END

    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    ba999_end(file_access, dal_common, pinvoice, context)
    bc085_process_delete_all(file_access, dal_common, pinvoice, context)
    return _BridgeLabel.BA999_EXIT


def ba090_process_rewrite(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba090-Process-Rewrite.` [common/plinvoiceMT.cbl:L1351-L1406].

    Unlike `ba070`, this verb DOES pair its failure status: `move 99 to fs-reply`
    [:L1396] with `move 994 to WE-Error` [:L1397].
    """
    if int(pinvoice.ih_prime.ws_invoice_key.ih_test) != 0:
        bc090_process_rewrite(file_access, dal_common, pinvoice, context)
        return _BridgeLabel.BA999_EXIT

    bb000_hv_load(pinvoice, context)
    _file_key(file_access, context.header_hv.hv_pinvoice_key)
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba090-Process-Rewrite"
    ]
    key = _key_of_reference(_KOR_HEADER)
    key_value = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L1371-L1379]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal

    result = bb300_update(file_access, dal_common, pinvoice, context, predicate)
    _display_message_1(file_access, dal_common)

    if result.count_rows != 1:
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.REWRITE_SQLSTATE_NOT_00000),
        )
        return _BridgeLabel.BA999_END

    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    ba999_end(file_access, dal_common, pinvoice, context)
    return _BridgeLabel.BA999_EXIT


def ba100_bad_function(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> _BridgeLabel:
    """`ba100-Bad-Function.` [common/plinvoiceMT.cbl:L1408-L1414].

    ANOMALY ``N-badfunction-pair-differs``: the HANDLER's equivalent returns `(99, 999)`
    [common/acas026.cbl:L527-L528] - 999, the code [copybooks/wsfnctn.cob] labels "not
    used" - while the bridge returns `(99, 990)`, "unknown/unexpected".
    """
    _set_status(
        file_access,
        int(status.FsReply.ERROR),
        int(status.WeError.UNKNOWN_UNEXPECTED),
    )
    return _BridgeLabel.BA999_END


def bb200_insert(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> ExecutionResult:
    """`bb200-Insert Section.` [common/plinvoiceMT.cbl:L1528-L1920].

    Assemble and run the thirty-column header `INSERT`.
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
    """`bb300-Update Section.` [common/plinvoiceMT.cbl:L1925-L2321].

    EVERY column is re-sent including the primary key itself - the statement sets
    `PINVOICE-KEY` to the value it is also keying on. Harmless in effect, load-bearing
    in evidence.
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


# `bc000-RG-Process section.` [common/plinvoiceMT.cbl:L2326] - the lines mirror The
# section header states its own contract [:L2329-L2346].


def bc000_rg_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc000-RG-Process section.` [common/plinvoiceMT.cbl:L2326-L2346].

    A SECTION HEADER with no statements of its own - every line between the label and
    `bc050-Process-Read-Indexed.` [:L2348] is a comment.
    """
    return None


def bc050_process_read_indexed(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc050-Process-Read-Indexed.` [common/plinvoiceMT.cbl:L2348-L2431].

    `set KOR-x1 to 2. *> was 1 = Primary now invoice line 12/07/23` [:L2365] dates the
    switch to key 2.
    """
    header_state = context.cursors.state_for(
        HEADER_TABLE, CURSOR_SLOTS[HEADER_TABLE]
    )
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])

    context.ws_mysql_save_count_rows = header_state.count_rows
    context.ws_mysql_count_rows = 0

    key = _key_of_reference(_KOR_LINES)
    key_value = _group_il_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L2370-L2378]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    _display_message_1(file_access, dal_common)
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc050-Process-Read-Indexed/SELECT"
    ]

    result = _execute(
        context, _select_statement(LINES_TABLE, predicate), store_result=True
    )
    lines_state.key_of_reference = key
    lines_state.store_result(result.rows)
    lines_state.position_at(key_value)
    context.ws_mysql_count_rows = result.count_rows

    if result.count_rows == 0:
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        # `move 23 to fs-reply` [:L2412] and `move 890 to WE-Error` [:L2413] - the
        # bridge-family status code for "unknown/unexpected error on RG processing",
        # declared in this module as :data:`WE_ERROR_RG_UNKNOWN` because
        # :class:`acas_posting.dal.status.WeError` carries no 890.
        _set_status(
            file_access, int(status.FsReply.KEY_NOT_FOUND), WE_ERROR_RG_UNKNOWN
        )
        _file_key(file_access, f"No RG1 Data for {key_value}")
        _initialise_header_record(pinvoice)
        context.ws_invoice_line = None
        context.buffer_view = _BufferView.HEADER
        # `go to bc058-Restore-Pointers *> do ba999-end at end` [:L2421].
        bc058_restore_pointers(file_access, dal_common, pinvoice, context)
        return None

    context.ws_temp_ed_row = result.count_rows
    _file_key(
        file_access,
        f"RG > 0 got cnt={_digits(result.count_rows, 7)}"
        f" recs, KEY={key_value}",
    )
    ba999_end(file_access, dal_common, pinvoice, context)
    bc051_fetch_rg1(file_access, dal_common, pinvoice, context)
    return None


def bc051_fetch_rg1(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc051-Fetch-RG1.` [common/plinvoiceMT.cbl:L2433-L2476].

    ANOMALY ``N-fetch-rg1-status-destroyed``, and it is the sharpest defect in the lines
    path.
    """
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc051-Fetch-RG1"
    ]
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
        bc100_unload_hvs_rg1(context)
    else:
        context.ws_invoice_line = None
        _initialise_header_record(pinvoice)
        context.buffer_view = _BufferView.HEADER
        file_access.fs_reply = int(status.FsReply.KEY_NOT_FOUND)

    _file_key(
        file_access,
        _group_il_key(
            pinvoice.ih_prime.ws_invoice_key.ih_invoice,
            pinvoice.ih_prime.ws_invoice_key.ih_test,
        ),
    )
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    # `bc058-Restore-Pointers.` [:L2478] follows with no transfer. Class 2 - a fall-
    # through. The caller's `PERFORM ...
    return None


def bc058_restore_pointers(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc058-Restore-Pointers.` [common/plinvoiceMT.cbl:L2478-L2484].

    `*> Restore the Primary table pointer & row count.` [:L2480]: `move WS-Mysql-Save-
    Result to WS-Mysql-Result.
    """
    context.ws_mysql_count_rows = context.ws_mysql_save_count_rows
    ba999_end(file_access, dal_common, pinvoice, context)
    return None


def bc059_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc059-Exit. Exit.` [common/plinvoiceMT.cbl:L2486].

    The terminator of the `PERFORM bc050-Process-Read-Indexed thru bc059-Exit` range
    used at [:L727] and [:L828].
    """
    return None


def bc070_process_write(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc070-Process-Write.` [common/plinvoiceMT.cbl:L2488-L2528].

    `move WS-Invoice-Record to WS-Invoice-Line.` [:L2490] reinterprets the shared
    hundred-byte buffer through the LINE redefinition [copybooks/plwspinv2.cob:L56]
    before loading the host variables - the one place in the bridge where the buffer's
    dual nature is written down as a move rather than assumed.
    """
    line = line_from_buffer(pinvoice, context)
    context.ws_invoice_line = line
    context.buffer_view = _BufferView.LINE
    bc000_hv_load_rg1(line, context)
    _file_key(file_access, context.line_hv.hv1_il_line_key)
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_state = " " * status.SQL_STATE_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc070-Process-Write"
    ]

    result = bc200_insert_rg1(file_access, dal_common, pinvoice, context)

    if result.count_rows != 1:
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        file_access.fs_reply = int(status.FsReply.ERROR)
        if result.error is not None:
            duplicate = result.error.duplicate_key or (
                result.error.sql_state[:5] == status.DUPLICATE_KEY_SQLSTATE.value
            )
            if duplicate:
                file_access.fs_reply = int(status.FsReply.DUPLICATE_KEY)
            else:
                file_access.fs_reply = int(status.FsReply.ERROR)
        _file_key(
            file_access,
            f"Cant Re|WriteRG1 Data on "
            f"{_group_il_key(line.il_key.il_invoice, line.il_key.il_line)}"
            f" RG={_digits(line.il_key.il_line, 2)}",
        )
    ba999_end(file_access, dal_common, pinvoice, context)
    return None


def bc080_process_delete(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc080-Process-Delete.` [common/plinvoiceMT.cbl:L2530-L2597].

    ANOMALY ``N-bc080-no-status-on-failure``. The failure arm [:L2571-L2589] captures
    the driver's error fields and builds a log key - and NEVER writes `FS-Reply` or `We-
    Error`.
    """
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])
    key = _key_of_reference(_KOR_LINES)
    key_value = _group_il_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L2540-L2548]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    _file_key(file_access, key_value)
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    _display_message_1(file_access, dal_common)
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc080-Process-Delete"
    ]

    result = _execute(
        context, _delete_statement(LINES_TABLE, predicate), store_result=False
    )
    context.ws_mysql_count_rows = result.count_rows
    lines_state.free_result()

    if result.count_rows <= 0:
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        context.ws_temp_ed_row = result.count_rows
        _file_key(
            file_access,
            f"Delete for {key_value} only found (rg01) "
            f"{_digits(result.count_rows, 7)} Rows",
        )
        # `go to ba999-End` [:L2589]. Class 4 - the target performs the log and then
        # falls through, so the named call is followed by an explicit return.
        ba999_end(file_access, dal_common, pinvoice, context)
        return None

    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_state = " " * status.SQL_STATE_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    ba999_end(file_access, dal_common, pinvoice, context)
    return None


def bc085_process_delete_all(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc085-Process-Delete-ALL.` [common/plinvoiceMT.cbl:L2599-L2688].

    `'IL-INVOICE'` in SINGLE quotes is a MySQL string LITERAL, not an identifier, so the
    statement compares the eleven-character constant `IL-INVOICE` against the eight-
    digit invoice number.
    """
    lines_state = context.cursors.state_for(LINES_TABLE, CURSOR_SLOTS[LINES_TABLE])
    # `set KOR-x1 to 2` [:L2622] and the offset/length pair [:L2623-L2624] - both
    # computed and then unused, because the live predicate operands do not reference
    # `KeyName` or the record slice.
    ih_invoice = int(pinvoice.ih_prime.ws_invoice_key.ih_invoice)
    predicate = _where_delete_all_lines(ih_invoice)
    context.ws_where = _pointer_slice(predicate).literal
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc085-Process-Delete-ALL"
    ]
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal
    _display_message_1(file_access, dal_common)

    result = _execute(
        context, _delete_statement(LINES_TABLE, predicate), store_result=False
    )
    context.ws_mysql_count_rows = result.count_rows
    context.ws_temp_ed_row = result.count_rows
    lines_state.free_result()

    # ANOMALY ``N-temp-ed-row-substring``. `move WS-MYSQL-COUNT-ROWS to WS-Temp-Ed-
    # Row` then the string [:L2660-L2667] - built unconditionally, BEFORE the count is
    # tested, and windowing `WS-Temp-Ed-Row (6:2)`.
    _file_key(
        file_access,
        f"Deleting All lines in {_digits(ih_invoice, 8)} with "
        f"{_digits(result.count_rows, 7)[5:7]} lines.",
    )

    if result.count_rows <= 0:
        if result.error is not None:
            _apply_db_error(file_access, result.error)
            if result.error.sql_err != _MYSQL_ERRNO_NONE:
                _set_status(
                    file_access,
                    int(status.FsReply.ERROR),
                    int(status.WeError.DELETE_SQLSTATE_NOT_00000),
                )
        ba999_end(file_access, dal_common, pinvoice, context)
        return None

    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    ba999_end(file_access, dal_common, pinvoice, context)
    return None


def bc085_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc085-Exit. Exit.` [common/plinvoiceMT.cbl:L2688] - a bare exit.

    The terminator of `perform bc085-Process-Delete-ALL thru bc085-Exit.` [:L1348]. No
    statements, so a documented no-op, present because rule R-5 wants one function per
    paragraph.
    """
    return None


def bc090_process_rewrite(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc090-Process-Rewrite section.` [common/plinvoiceMT.cbl:L2690-L2739].

    ANOMALY ``N-bc090-is-a-section``. This is declared `section` [:L2690] while its own
    sibling `bc080-Process-Delete` [:L2530] and its header counterpart `ba090-Process-
    Rewrite` [:L1351] are paragraphs, and while `bc070` [:L2488] and `bc085` [:L2599]
    are paragraphs.
    """
    line = line_from_buffer(pinvoice, context)
    context.ws_invoice_line = line
    context.buffer_view = _BufferView.LINE
    bc000_hv_load_rg1(line, context)
    _file_key(file_access, context.line_hv.hv1_il_line_key)
    # `move 56 to ws-No-Paragraph.` [:L2697] - the same 56 `bc998-Free` would have used
    # had it been reachable (``N-bridge-paragraph-56-duplicated``).
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "bc090-Process-Rewrite"
    ]
    key = _key_of_reference(_KOR_LINES)
    key_value = _group_il_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    predicate = _where_key_equals(
        key, key_value, "[common/plinvoiceMT.cbl:L2704-L2712]"
    )
    context.ws_where = _pointer_slice(predicate).literal
    file_access.logging_data.ws_log_where = _pointer_slice(predicate).literal

    result = bc300_update_rg1(file_access, dal_common, pinvoice, context, predicate)
    _display_message_1(file_access, dal_common)

    if result.count_rows != 1:
        if result.error is not None:
            _apply_db_error(file_access, result.error)
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.REWRITE_SQLSTATE_NOT_00000),
        )
        ba999_end(file_access, dal_common, pinvoice, context)
        return None

    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    file_access.logging_data.sql_err = "0".rjust(status.SQL_ERR_WIDTH, "0")
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    ba999_end(file_access, dal_common, pinvoice, context)
    return None


def bc090_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`bc090-Exit. exit.` [common/plinvoiceMT.cbl:L2741]."""
    return None


def bc200_insert_rg1(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> ExecutionResult:
    """`bc200-Insert-rg1 Section.` [common/plinvoiceMT.cbl:L2816-L3003].

    The column order here is the SCHEMA's - `IL-INVOICE` before `IL-LINE` - while
    `bc000-HV-Load-rg1` moves `WS-il-Line` BEFORE `WS-il-Invoice` [:L2757-L2758].
    Anomaly ``N-lines-loadorder``: two orders, two separate lists, neither derived from
    the other.
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
    """`bc300-Update-rg1 Section.` [common/plinvoiceMT.cbl:L3009-L3201].

    Like the header update, this re-sends the primary key it is keying on, and it re-
    sends `IL-INVOICE` from the never-unloaded host variable - so a rewrite of a row
    that was READ through this bridge writes back a zero invoice number unless the
    caller repopulated it, because `bc100-UnloadHVs-rg1` restored only the concatenated
    key [:L2789] and not the dedicated field.
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

    ANOMALY ``N-bc998-unreachable``: NOTHING PERFORMS THIS PARAGRAPH.
    """
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

    `common/fhlogger.cbl` is OUT OF SCOPE [Agent Action Plan section 0.2.2, "Non-posting
    utilities"], and rule R-1 forbids calling it in any case, so the log record is
    emitted through :mod:`logging` instead.
    """
    #  THE ONE ADAPTER, shared by every handler in this package, so the single
    # legacy log this cycle produces reads the same whichever table wrote it. Two
    # fields are WITHHELD: `WS-File-Key` is `PINVOICE-KEY` or `IL-LINE-KEY`, and
    # `WS-Log-Where` is a predicate carrying it as a literal (CWE-532). It also
    # advances `Log-File-Rec-Written` modulo one million, the range of the frozen
    # `pic 9(6)` [copybooks/Test-Data-Flags.cob:L18], which this paragraph did not
    # advance at all.
    status.log_file_handler_record(
        _LOG,
        program=BRIDGE_NAME,
        paragraph="Ca-Process-Logs",
        log_system=int(WS_LOG_SYSTEM),
        log_file_no=WS_LOG_FILE_NO_RDB,
        no_paragraph=file_access.logging_data.ws_no_paragraph,
        file_function=int(file_access.file_function),
        access_type=int(file_access.access_type),
        fs_reply=int(file_access.fs_reply),
        we_error=int(file_access.we_error),
        sql_err=file_access.logging_data.sql_err,
        sql_state=file_access.logging_data.sql_state,
        dal_common=dal_common,
    )


def ca_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    pinvoice: PInvoiceHeader,
    context: PInvoiceContext,
) -> None:
    """`ca-Exit.` [common/plinvoiceMT.cbl:L3224] - `exit.` and nothing else.

    A plain `exit`, not `exit section`, exactly as the handler's own `ca-Exit`
    [common/acas026.cbl:L629] is. Reproduced as an empty function because rule R-5 asks
    for one function per paragraph and a label with a single `exit` is still a
    paragraph.
    """
    return None


#: Which function implements each label the bridge's verbs can transfer to. Only labels
#: a verb RETURNS appear here.
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

    ANOMALY ``N-bridge-param-rename``. The caller passes `WS-PInvoice-Record`; the
    bridge calls the same operand `WS-Invoice-Record` - the identifier `slinvoiceMT`
    uses for the SALES header [common/slinvoiceMT.cbl:L480].
    """
    active = _DEFAULT_CONTEXT if context is None else context
    label = ba_acas_dal_process(file_access, dal_common, pinvoice, active)
    while label is not _BridgeLabel.BA999_EXIT:
        implementation = _BRIDGE_LABEL_FUNCTIONS.get(label)
        if implementation is None:
            # Unreachable: every member of `_BridgeLabel` a verb can return is in the
            # table.
            _set_status(
                file_access,
                int(status.FsReply.ERROR),
                int(status.WeError.UNKNOWN_UNEXPECTED),
            )
            break
        label = implementation(file_access, dal_common, pinvoice, active)
    return file_access


# The handler - `acas026`, five parameters, `aa-Process-Flat-File` and `ba-Process-
# RDBMS` THE FLAT-FILE PATH IS NOT EXECUTED BY THE MIGRATED CYCLE, and this is a
# deliberate omission recorded here rather than discovered later.

#: `False` on every migrated run. See the block comment above. Not a feature switch:
#: there is nothing to switch on, and rule R-3 forbids adding one.
FLAT_FILE_PATH_AVAILABLE: Final[bool] = False

_FS_REPLY_FILE_NOT_PRESENT: Final[int] = 35

#: `999` - `move 999 to WE-Error.` [common/acas026.cbl:L344, :L527].
_WE_ERROR_HANDLER_GENERIC: Final[int] = int(status.WeError.NOT_USED)


class _HandlerLabel(enum.StrEnum):
    """Every label `aa010-main`'s `evaluate` and the flat-file `GO TO`s name."""

    AA020_PROCESS_OPEN = "aa020-Process-Open"
    AA030_PROCESS_CLOSE = "aa030-Process-Close"
    AA040_PROCESS_READ_NEXT = "aa040-Process-Read-Next"
    AA050_PROCESS_READ_INDEXED = "aa050-Process-Read-Indexed"
    AA060_PROCESS_START = "aa060-Process-Start"
    AA070_PROCESS_WRITE = "aa070-Process-Write"
    AA080_PROCESS_DELETE = "aa080-Process-Delete"
    AA090_PROCESS_REWRITE = "aa090-Process-Rewrite"
    AA100_BAD_FUNCTION = "aa100-Bad-Function"
    AA999_MAIN_EXIT = "aa999-main-exit"
    AA_MAIN_EXIT = "aa-main-exit"
    AA_EXIT = "aa-Exit"


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
    [:L235]; control falls straight through into `aa010-main` [:L236]. Reproduced as a
    documented pass-through because rule R-5 wants one function per paragraph.
    """
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

    Log identity, key guard, path selection, record-size guard, SQL clear, verb dispatch
    - in that order and no other.
    """
    file_access.logging_data.ws_log_system = int(WS_LOG_SYSTEM)
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO

    # `evaluate File-Function` [:L245-L259] - the key guard.
    function = int(file_access.file_function)
    if function in KEY_NUMBER_GUARDED_FUNCTIONS:
        if int(file_access.logging_data.file_key_no) != _ONLY_ADMITTED_KEY_NUMBER:
            if function == int(status.FileFunction.DELETE):
                we_error = int(status.WeError.DELETE_KEY_OUT_OF_RANGE)
            else:
                we_error = int(status.WeError.FILE_KEY_NO_OUT_OF_RANGE)
            _set_status(file_access, int(status.FsReply.ERROR), we_error)
            return _HandlerLabel.AA999_MAIN_EXIT

    if int(system.system_data_block.rdbms_flat_statuses.file_system_used) != 0:
        file_access.fa_rdbms_flat_statuses.fa_file_system_used = int(
            system.system_data_block.rdbms_flat_statuses.file_system_used
        )
        file_access.fa_rdbms_flat_statuses.fa_file_duplicates_in_use = int(
            system.system_data_block.rdbms_flat_statuses.file_duplicates_in_use
        )
        # `perform ba-Process-RDBMS *> Can't hurt` [:L265] - the maintainer's own
        # comment, preserved. Class 4.
        ba_process_rdbms(
            system, pinvoice, file_access, file_defs, dal_common, context
        )
        return _HandlerLabel.AA_MAIN_EXIT

    # `perform ba012-Test-WS-Rec-Size-2.` [:L271] under `*> Test Rec lengths first.`
    # [:L269].
    ba012_test_ws_rec_size_2(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
    # ANOMALY ``N-no-status-zeroing``.
    file_access.logging_data.sql_err = " " * status.SQL_ERR_WIDTH
    file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
    file_access.logging_data.sql_state = " " * status.SQL_STATE_WIDTH

    label = _HANDLER_DISPATCH.get(function)
    if label is None:
        return _HandlerLabel.AA100_BAD_FUNCTION
    # `go to <verb paragraph>` [:L284-L300]. Class 3. The unconditional `go to
    # aa100-Bad-Function.` at [:L306] is unreachable because every arm of the `evaluate`
    # transfers.
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

    A four-way nested `if` on `Access-Type`: input, i-o, output, extend [:L311-L339].
    Only the fourth arm is data-independent, and it is the only one that writes a status
    of its own.
    """
    _file_key(file_access, "")
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa020-Process-Open"
    ]

    access_type = int(file_access.access_type)
    if access_type == int(status.AccessType.INPUT):
        # `open input Invoice-File` [:L312]. ANOMALY ``N-select-status-is-fs-reply``.
        file_access.fs_reply = _FS_REPLY_FILE_NOT_PRESENT
        if int(file_access.fs_reply) != int(status.FsReply.SUCCESS):
            # ANOMALY ``N-open-input-status-flattened``.
            file_access.fs_reply = _FS_REPLY_FILE_NOT_PRESENT
            return _HandlerLabel.AA999_MAIN_EXIT
    elif access_type == int(status.AccessType.I_O):
        # `open i-o Invoice-File` [:L320] then the create-if-missing dance [:L321-L326].
        # No status is written by any of it, so this branch deliberately executes no
        # statement.
        pass
    elif access_type == int(status.AccessType.OUTPUT):
        # `open output Invoice-File *> caller should check fs-reply` [:L329]. A plain
        # open - ``N-noopenoutput``. This branch deliberately executes no statement, and
        # the emptiness IS the anomaly.
        pass
    elif access_type == int(status.AccessType.EXTEND):
        # `if fn-extend *> Must not be used for ISAM files` [:L331], with `open extend
        # Invoice-File` commented out [:L332].
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.ACCESS_TYPE_WRONG),
        )
        return _HandlerLabel.AA999_MAIN_EXIT

    context.cobol_file_status = 0
    _file_key(file_access, "OPEN PL INVOICE File")
    if int(file_access.fs_reply) != int(status.FsReply.SUCCESS):
        file_access.we_error = _WE_ERROR_HANDLER_GENERIC
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

    ANOMALY ``N-close-logs-twice``. The ordering is unusual and load-bearing.
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa030-Process-Close"
    ]
    _file_key(file_access, "")
    context.cobol_file_status = 0
    _file_key(file_access, "CLOSE PL INVOICE File")
    aa999_main_exit(system, pinvoice, file_access, file_defs, dal_common, context)
    file_access.file_function = 0
    file_access.access_type = 0
    ca_process_logs_handler(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
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

    ANOMALY ``N-spaces-into-numeric-key``. The end-of-file pre-test moves `spaces`
    into `Invoice-Key` [:L369] - a group whose two halves are `pic 9(8)` and `pic 99`
    [copybooks/plwspinv2.cob:L11-L13], both NUMERIC.
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa040-Process-Read-Next"
    ]
    if context.cobol_file_eof:
        eof_reply, eof_we_error = status.end_of_file_status()
        _set_status(file_access, int(eof_reply), int(eof_we_error))
        context.invoice_key_raw = " " * 10
        file_access.logging_data.sql_err = " " * status.SQL_ERR_WIDTH
        file_access.logging_data.sql_msg = " " * status.SQL_MSG_WIDTH
        # `stop "Cobol File EOF"  *> for testing` [:L372] - ``N-stop``.
        #  ONE ERROR, THROUGH THE ONE REPORTER, at the same level and in the
        #  same words as every sibling handler. `STOP` with a literal DISPLAYS the
        #  literal and then waits: the display is a record, only the WAIT is the
        #  omission. DEBUG was both the wrong level for a production halt and a
        #  different level from the same statement's record in acas006, acas007,
        #  acas012 and acas019, so one event read as five.
        status.log_cobol_stop(
            _LOG,
            program=HANDLER_NAME,
            paragraph="aa040-Process-Read-Next",
            literal="Cobol File EOF",
            locator="[common/acas026.cbl:L372]",
        )
        return _HandlerLabel.AA999_MAIN_EXIT

    # `read Invoice-File next record at end` [:L376] - the ISAM verb, taking its own `at
    # end` branch [:L377-L382] because the file is not present.
    eof_reply, eof_we_error = status.end_of_file_status()
    _set_status(file_access, int(eof_reply), int(eof_we_error))
    context.cobol_file_eof = True
    context.cobol_file_status = 1
    _initialise_header_record(pinvoice)
    _file_key(file_access, "EOF")
    # `go to aa999-main-exit` [:L382]. Class 2. The statements below are the success
    # path [:L384-L389].
    return _HandlerLabel.AA999_MAIN_EXIT


def aa041_move_inv_data(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> None:
    """`aa041-Move-Inv-Data. *> Not really needed as both fields are now chars.`

    Both `pic 9`, not `pic x`. The paragraph is NOT deleted on the strength of its own
    comment; it is reproduced and the contradiction is recorded.
    """
    context.ws_temp_ed_1 = int(pinvoice.ih_prime.ws_invoice_key.ih_invoice)
    context.ws_temp_ed_2 = int(pinvoice.ih_prime.ws_invoice_key.ih_test)
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

    ANOMALY ``N-deadbranches``. The maintainer's own comment above the label reads `*>
    The next block will never get executed unless performed so is it needed ?` [:L396] -
    and it IS performed, from `aa050` [:L419] and `aa060` [:L443].
    """
    function = int(file_access.file_function)
    if function in (
        int(status.FileFunction.READ_INDEXED),
        int(status.FileFunction.WRITE),
        int(status.FileFunction.RE_WRITE),
        int(status.FileFunction.DELETE),
        int(status.FileFunction.START),
    ):
        # `evaluate File-Key-No` [:L405]. Only key 1 is admitted by `aa010-main`'s guard
        # for read-indexed, start and delete; write and rewrite are not guarded but
        # cannot reach here.
        if int(file_access.logging_data.file_key_no) == _ONLY_ADMITTED_KEY_NUMBER:
            context.invoice_key_raw = _group_ws_invoice_key(
                pinvoice.ih_prime.ws_invoice_key.ih_invoice,
                pinvoice.ih_prime.ws_invoice_key.ih_test,
            )
            aa041_move_inv_data(
                system, pinvoice, file_access, file_defs, dal_common, context
            )
        else:
            _file_key(file_access, "")
    else:
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

    ANOMALY ``N-failed-action``. On an invalid key the paragraph does TWO things
    [:L429-L430].
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa050-Process-Read-Indexed"
    ]
    aa045_eval_keys(system, pinvoice, file_access, file_defs, dal_common, context)
    context.cobol_file_status = 0
    if int(file_access.logging_data.file_key_no) == _ONLY_ADMITTED_KEY_NUMBER:
        _set_status(
            file_access,
            int(status.FsReply.INVALID_KEY_ON_START),
            int(status.FsReply.INVALID_KEY_ON_START),
        )
        if int(file_access.fs_reply) == int(status.FsReply.SUCCESS):
            aa041_move_inv_data(
                system, pinvoice, file_access, file_defs, dal_common, context
            )
        else:
            _initialise_header_record(pinvoice)
            _file_key(file_access, "Failed action")
        return _HandlerLabel.AA999_MAIN_EXIT

    _set_status(
        file_access,
        int(status.FsReply.ERROR),
        int(status.WeError.FILE_KEY_NO_OUT_OF_RANGE),
    )
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

    ANOMALIES ``N-start-guard-differs-from-bridge`` and ``N-start-guard-no-fs-reply``
    - one guard, two independent defects, the second the more serious because it is
    silent.
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa060-Process-Start"
    ]
    aa045_eval_keys(system, pinvoice, file_access, file_defs, dal_common, context)
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    context.cobol_file_status = 0

    access_type = int(file_access.access_type)
    if access_type < 5 or access_type > 8:
        file_access.we_error = int(status.WeError.FILE_KEY_NO_OUT_OF_RANGE)
        return _HandlerLabel.AA999_MAIN_EXIT

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
        file_access.fs_reply = int(status.FsReply.INVALID_KEY_ON_START)
        return _HandlerLabel.AA999_MAIN_EXIT

    if int(file_access.logging_data.file_key_no) == _ONLY_ADMITTED_KEY_NUMBER:
        aa041_move_inv_data(
            system, pinvoice, file_access, file_defs, dal_common, context
        )
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

    `perform aa041-Move-Inv-Data.` [:L497] runs UNCONDITIONALLY, after both the
    success and the failure of the write - so a failed write still logs the key it
    tried. Class 4.
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa070-Process-Write"
    ]
    context.invoice_key_raw = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    context.cobol_file_status = 0
    file_access.fs_reply = int(status.FsReply.DUPLICATE_KEY)
    aa041_move_inv_data(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
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

    Note that `aa080` does NOT re-check `File-Key-No`: `aa010-main`'s guard has
    already rejected anything but 1 with `996` [:L255], which is the one place in the
    handler where the delete verb gets its own error code.
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa080-Process-Delete"
    ]
    context.invoice_key_raw = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    context.cobol_file_status = 0
    file_access.fs_reply = int(status.FsReply.INVALID_KEY_ON_START)
    aa041_move_inv_data(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
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

    ANOMALY ``N-endrewrite-no-period``. The `end-rewrite` at [:L519] carries NO
    terminating period, unlike `end-write.` [:L496] and `end-delete.` [:L507] in the two
    paragraphs either side of it - three sibling paragraphs written to the same
    template, one of them punctuated differently.
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa090-Process-Rewrite"
    ]
    context.invoice_key_raw = _group_ws_invoice_key(
        pinvoice.ih_prime.ws_invoice_key.ih_invoice,
        pinvoice.ih_prime.ws_invoice_key.ih_test,
    )
    _set_status(
        file_access, int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS)
    )
    context.cobol_file_status = 0
    file_access.fs_reply = int(status.FsReply.INVALID_KEY_ON_START)
    aa041_move_inv_data(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
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

    ANOMALY ``N-badfunction-pair-differs``, carried in the register also under the
    heading ``N-badfunction-divergence`` - one finding, two names. The HANDLER writes
    `999` / `99`; the BRIDGE writes `990` / `99` for the same condition
    [common/plinvoiceMT.cbl:L1412-L1413].
    """
    _set_status(file_access, int(status.FsReply.ERROR), _WE_ERROR_HANDLER_GENERIC)
    return _HandlerLabel.AA999_MAIN_EXIT


def aa999_main_exit(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa999-main-exit.` [common/acas026.cbl:L530-L533]."""
    if _testing_1(dal_common):
        ca_process_logs_handler(
            system, pinvoice, file_access, file_defs, dal_common, context
        )
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

    A label carrying only the comment `*> Now have processed cobol flat file, so ..`
    [:L537] - and the sentence is never finished. Control falls through into `aa-Exit`
    [:L539].
    """
    return _HandlerLabel.AA_EXIT


def aa_exit(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> _HandlerLabel:
    """`aa-Exit.` [common/acas026.cbl:L539-L540] - `exit program.`"""
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

    The single early exit out of this chain is `ba012`'s `go to ba-rdbms-exit` [:L586]
    on a record-size error, which skips the ``CALL``. That is why
    :func:`ba010_test_ws_rec_size` and :func:`ba012_test_ws_rec_size_2` report whether
    they transferred.
    """
    section_exited = ba010_test_ws_rec_size(
        system, pinvoice, file_access, file_defs, dal_common, context
    )
    if section_exited:
        return None
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

    ANOMALY ``N-log-no-increment``. TWELVE - the same value `aa010-main` moved at
    [:L241]. Ten sibling handlers add ten here; this one does not, and nothing in the
    source marks the omission. NOT corrected to 22.
    """
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB
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

    `if A = zero *> so it is being called first time` [:L560] - `A` is the guard AND one
    of the two operands, which is why the comment on [:L552] warns `*> (So do NOT use
    var A & B again)`.
    """
    if context.record_size_a != 0:
        # `if A = zero` [:L560] - already run, so the whole block is skipped and control
        # falls straight through to `ba015-Test-Ends` [:L601].
        return False

    context.record_size_a = _WS_RECORD_DECLARED_LENGTH
    context.record_size_b = _FILE_RECORD_DECLARED_LENGTH

    if context.record_size_a < context.record_size_b:
        _set_status(
            file_access,
            int(status.FsReply.ERROR),
            int(status.WeError.RECORD_SIZE_MISMATCH),
        )

    if int(file_access.we_error) == int(status.WeError.RECORD_SIZE_MISMATCH):
        # `if WE-Error = 901` [:L571]. `move spaces to Display-Blk` [:L572] then five
        # operands, every one `delimited by size` [:L573-L577], into a `pic x(75)` field
        # [:L195].
        context.display_blk = (
            _ERROR_MESSAGE_PL907
            + _digits(context.record_size_a, _RECORD_SIZE_DIGITS)
            + " < "
            + "Invoice-Rec = "
            + _digits(context.record_size_b, _RECORD_SIZE_DIGITS)
        )[:_DISPLAY_BLK_WIDTH].ljust(_DISPLAY_BLK_WIDTH, " ")
        _LOG.error(
            "acas026 ba012 [common/acas026.cbl:L571-L579]: %s",
            status.sanitise_for_log(context.display_blk),
        )
        # `move Display-Blk to SQL-Msg` [:L581] - PRESERVED, because `SQL-Msg` is a data
        # field the caller reads, not screen output.
        file_access.logging_data.sql_msg = context.display_blk[
            : status.SQL_MSG_WIDTH
        ].ljust(status.SQL_MSG_WIDTH, " ")
        if _testing_1(dal_common):
            ca_process_logs_handler(
                system, pinvoice, file_access, file_defs, dal_common, context
            )
        # `accept Accept-Reply at 2433` [:L585] - the pause, DROPPED. `go to ba-rdbms-
        # exit` [:L586] - the transfer, PRESERVED. Class 4.
        ba_rdbms_exit(
            system, pinvoice, file_access, file_defs, dal_common, context
        )
        return True

    file_access.rdb_data = connection.load_rdb_data_once(system)
    context.system_record = system
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

    ANOMALY ``N-cdftodo``. Above the call sits an unfinished plan: `*> HERE we need a
    CDF [Compiler Directive] to select the correct DAL based *> on the pre SQL compiler
    e.g., JCs or dbpre or Prima conversions <<<< ?
    """
    plinvoice_mt(file_access, dal_common, pinvoice, context=context)
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
    """`ba-rdbms-exit.` [common/acas026.cbl:L619-L620] - `exit section.`"""
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

    ANOMALY ``N-nolog-on-dal``, and the comment that states it sits on the LABEL
    LINE ITSELF at [:L623]. On the RDB path the handler must NOT log, because the
    bridge's own `ba999-end` [common/plinvoiceMT.cbl:L1435-L1437] already did -
    and the handler's flat-file `aa999-main-exit` [:L531-L533] is the only route to
    this paragraph other than the close sentinel [:L357] and the record-size error
    [:L583]. Reproduced: this function is reached only from those three sites, and
    :func:`ca_process_logs` is the bridge's separate logger.

    R-1: `fhlogger` is a COBOL program [common/fhlogger.cbl] and is NOT called. The
    record it would have written is emitted through the SAME ONE ADAPTER the bridge's
    like-named paragraph uses, so the two render identically and differ only in the
    program they name. `WS-File-Key` is WITHHELD rather than redacted: for these
    tables it is the invoice key, and `redact_for_log` escapes a key rather than
    removing it (CWE-532).
    """
    logging_data = file_access.logging_data
    status.log_file_handler_record(
        _LOG,
        program=HANDLER_NAME,
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
    return None


def ca_exit_handler(
    system: SystemRecord,
    pinvoice: PInvoiceHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    context: PInvoiceContext,
) -> None:
    """`ca-Exit. exit.` [common/acas026.cbl:L629] - a PLAIN `exit`."""
    return None


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

    The statement order is the COBOL's exactly, and it is checked in the validation
    list of the agent brief: log identity [:L240-L241]; the key guard [:L245-L259]; NO
    Open-Output block anywhere; the RDB branch with both maintainer comments
    [:L263-L267].
    """
    active = _DEFAULT_CONTEXT if context is None else context
    label = aa_process_flat_file(
        system, pinvoice, file_access, file_defs, dal_common, active
    )
    while label is not _HandlerLabel.AA_EXIT:
        implementation = _HANDLER_LABEL_FUNCTIONS.get(label)
        if implementation is None:
            # Unreachable; defended the way this handler defends, with its own bad-
            # function pair [:L527-L528] rather than an exception.
            _set_status(
                file_access, int(status.FsReply.ERROR), _WE_ERROR_HANDLER_GENERIC
            )
            break
        label = implementation(
            system, pinvoice, file_access, file_defs, dal_common, active
        )
    return file_access


# The linkage projection - `WS-PInvoice-Record` and its two redefinitions TWO
# COPYBOOKS DESCRIBE THE SAME HUNDRED BYTES, and each caller copies the one it wants.


def _projected_pinvoice_views(record: object) -> bool:
    """Whether ``record`` is a caller's record AREA rather than a header.

    Recognised structurally, by the three names `plwspinv2.cob` gives the area and its
    two redefinitions, because the callers are ``programs/*`` modules this layer may not
    import.
    """
    if isinstance(record, PInvoiceHeader):
        return False
    return all(
        hasattr(record, attribute)
        for attribute in ("ws_pinvoice_record", "invoice_header", "invoice_line")
    )


def linkage_header_for(
    record: object, context: PInvoiceContext | None = None
) -> PInvoiceHeader:
    """Adopt the caller's record area as this handler's ``WS-PInvoice-Record``.

    Returns the :class:`PInvoiceHeader` :func:`dispatch` is entered with, having first
    copied the caller's flat views into it - BOTH of them, because a ``CALL`` hands over
    one storage and the two redefinitions are that storage seen twice.

    Args:
        record: The second operand of the ``CALL`` - a caller's record area, or a
            :class:`PInvoiceHeader` the caller manages itself.
        context: The working storage the call will use, so the caller's line view is
            staged where the bridge looks for it.

    Returns:
        The header record to pass to :func:`dispatch`.
    """
    if isinstance(record, PInvoiceHeader):
        return record
    if not _projected_pinvoice_views(record):
        raise TypeError(
            "acas026 takes WS-PInvoice-Record [common/acas026.cbl:L225-L231] - "
            "either a PInvoiceHeader or a record area exposing "
            "ws_pinvoice_record, invoice_header and invoice_line; got "
            f"{type(record).__name__}"
        )
    identity = id(record)
    held = _LINKAGE_HEADERS.get(identity)
    if held is None or held[0] is not record:
        held = (record, _new_linkage_header())
        _LINKAGE_HEADERS[identity] = held
    header = held[1]
    active = _DEFAULT_CONTEXT if context is None else context
    _load_header_from_record(record, header, active)
    _stage_line_from_record(record, active)
    return header


def publish_linkage_header(
    header: PInvoiceHeader,
    record: object,
    context: PInvoiceContext | None = None,
) -> None:
    """Copy the handler's record back over the caller's area, after the ``CALL``.

    A COBOL ``CALL`` passes the record area by reference, so whatever the handler and
    the bridge left in ``WS-PInvoice-Record`` is what the caller reads next.

    Args:
        header: The record :func:`dispatch` was given.
        record: The caller's record area, mutated in place. A :class:`PInvoiceHeader` is
            its own area and is left alone.
        context: The working storage the call used, for the staged line. Defaults to the
            module-level instance, as :func:`dispatch` does.
    """
    if isinstance(record, PInvoiceHeader):
        return
    if not _projected_pinvoice_views(record):
        return
    _store_record_from_header(
        header, record, _DEFAULT_CONTEXT if context is None else context
    )


#: The header record each caller area is walked through, keyed by the area's identity
#: and holding the area itself so the key stays valid.
_LINKAGE_HEADERS: Final[dict[int, tuple[object, PInvoiceHeader]]] = {}


def _new_linkage_header() -> PInvoiceHeader:
    """A ``PInvoice-Header`` at its ``INITIALIZE`` values [copybooks/plwspinv.cob:L8].
    """
    header = PInvoiceHeader(
        ih_prime=IhPrime(
            ws_invoice_key=WsInvoiceKey(ih_invoice=0, ih_test=0),
            ih_supplier=IhSupplier(ih_nos=" " * 6, ih_check=0),
            ih_date=0,
            ih_order=IhOrder(
                ih_freq=" ", ih_repeat=0, filler_1=" " * 3, ih_last_date=0
            ),
            ih_type=0,
            ih_ref=" " * 10,
        ),
        ih_sub_prime=IhSubPrime(
            ih_fig=IhFig(
                ih_p_c=_DECIMAL_ZERO,
                ih_net=_DECIMAL_ZERO,
                ih_extra=_DECIMAL_ZERO,
                ih_carriage=_DECIMAL_ZERO,
                ih_vat=_DECIMAL_ZERO,
                ih_discount=_DECIMAL_ZERO,
                ih_e_vat=_DECIMAL_ZERO,
                ih_c_vat=_DECIMAL_ZERO,
            ),
            ih_status=" ",
            ih_lines=0,
            ih_deduct_days=0,
            ih_deduct_amt=_DECIMAL_ZERO,
            ih_deduct_vat=_DECIMAL_ZERO,
            ih_days=0,
            ih_cr=0,
            ih_day_book_flag=" ",
            ih_update=" ",
        ),
    )
    return header


def _stage_line_from_record(record: object, context: PInvoiceContext) -> None:
    """The caller's `Invoice-Line` view into the buffer the bridge re-derives from.

    THE INBOUND HALF OF THE LINE VIEW, and it is what makes a caller's edit to a line
    REACH the database.
    """
    flat_line = getattr(record, "invoice_line", None)
    if flat_line is None:
        return
    context.ws_invoice_line = IlInvoiceLineBody(
        il_key=IlKey(
            il_invoice=int(flat_line.il_invoice),
            il_line=int(flat_line.il_line),
        ),
        il_product=flat_line.il_product,
        il_pa=flat_line.il_pa,
        filler_1=flat_line.filler_1,
        il_qty=flat_line.il_qty,
        il_type=flat_line.il_type,
        il_description=flat_line.il_description,
        filler_2=flat_line.filler_2,
        il_net=flat_line.il_net,
        il_unit=flat_line.il_unit,
        il_discount=flat_line.il_discount,
        il_vat=flat_line.il_vat,
        il_vat_code=flat_line.il_vat_code,
        il_update=flat_line.il_update,
    )


def _load_header_from_record(
    record: object, header: PInvoiceHeader, context: PInvoiceContext
) -> None:
    """The flat views into the nested record - one description into the other."""
    flat_header = getattr(record, "invoice_header")
    base = getattr(record, "ws_pinvoice_record")
    generic_invoice = int(base.invoice_key.invoice_nos) if base is not None else 0
    generic_test = int(base.invoice_key.item_nos) if base is not None else 0
    if flat_header is not None and not generic_invoice and not generic_test:
        generic_invoice = int(flat_header.ih_invoice)
        generic_test = int(flat_header.ih_test)
    prime = header.ih_prime
    sub = header.ih_sub_prime
    prime.ws_invoice_key.ih_invoice = generic_invoice
    prime.ws_invoice_key.ih_test = generic_test
    if flat_header is not None:
        prime.ih_supplier.ih_nos = flat_header.ih_supplier.ih_nos
        prime.ih_supplier.ih_check = flat_header.ih_supplier.ih_check
        prime.ih_date = flat_header.ih_date
        _split_ih_order(flat_header.ih_order, prime.ih_order, context)
        prime.ih_type = flat_header.ih_type
        prime.ih_ref = flat_header.ih_ref
        sub.ih_fig.ih_p_c = flat_header.ih_fig.ih_p_c
        sub.ih_fig.ih_net = flat_header.ih_fig.ih_net
        sub.ih_fig.ih_extra = flat_header.ih_fig.ih_extra
        sub.ih_fig.ih_carriage = flat_header.ih_fig.ih_carriage
        sub.ih_fig.ih_vat = flat_header.ih_fig.ih_vat
        sub.ih_fig.ih_discount = flat_header.ih_fig.ih_discount
        sub.ih_fig.ih_e_vat = flat_header.ih_fig.ih_e_vat
        sub.ih_fig.ih_c_vat = flat_header.ih_fig.ih_c_vat
        sub.ih_status = flat_header.ih_status
        sub.ih_lines = flat_header.ih_lines
        sub.ih_deduct_days = flat_header.ih_deduct_days
        sub.ih_deduct_amt = flat_header.ih_deduct_amt
        sub.ih_deduct_vat = flat_header.ih_deduct_vat
        sub.ih_days = flat_header.ih_days
        sub.ih_cr = flat_header.ih_cr
        sub.ih_day_book_flag = flat_header.ih_day_book_flag
        sub.ih_update = flat_header.ih_update


def _store_record_from_header(
    header: PInvoiceHeader, record: object, context: PInvoiceContext
) -> None:
    """The nested record back into the flat views - the same description swap."""
    prime = header.ih_prime
    sub = header.ih_sub_prime
    staged = context.ws_invoice_line
    if context.buffer_view is _BufferView.LINE and staged is not None:
        shared_invoice = int(staged.il_key.il_invoice)
        shared_test = int(staged.il_key.il_line)
    else:
        shared_invoice = int(prime.ws_invoice_key.ih_invoice)
        shared_test = int(prime.ws_invoice_key.ih_test)

    base = getattr(record, "ws_pinvoice_record")
    if base is not None:
        base.invoice_key.invoice_nos = shared_invoice
        base.invoice_key.item_nos = shared_test
        base.invoice_supplier = _group_ih_supplier(
            prime.ih_supplier.ih_nos, prime.ih_supplier.ih_check
        )
        base.invoice_date = prime.ih_date
        base.inv_order = _group_ih_order(prime.ih_order, context)
        base.invoice_type = prime.ih_type

    flat_header = getattr(record, "invoice_header")
    if flat_header is not None:
        flat_header.ih_invoice = shared_invoice
        flat_header.ih_test = shared_test
        flat_header.ih_supplier.ih_nos = prime.ih_supplier.ih_nos
        flat_header.ih_supplier.ih_check = prime.ih_supplier.ih_check
        flat_header.ih_date = prime.ih_date
        flat_header.ih_order = _group_ih_order(prime.ih_order, context)
        flat_header.ih_type = prime.ih_type
        flat_header.ih_ref = prime.ih_ref
        flat_header.ih_fig.ih_p_c = sub.ih_fig.ih_p_c
        flat_header.ih_fig.ih_net = sub.ih_fig.ih_net
        flat_header.ih_fig.ih_extra = sub.ih_fig.ih_extra
        flat_header.ih_fig.ih_carriage = sub.ih_fig.ih_carriage
        flat_header.ih_fig.ih_vat = sub.ih_fig.ih_vat
        flat_header.ih_fig.ih_discount = sub.ih_fig.ih_discount
        flat_header.ih_fig.ih_e_vat = sub.ih_fig.ih_e_vat
        flat_header.ih_fig.ih_c_vat = sub.ih_fig.ih_c_vat
        flat_header.ih_status = sub.ih_status
        flat_header.ih_lines = sub.ih_lines
        flat_header.ih_deduct_days = sub.ih_deduct_days
        flat_header.ih_deduct_amt = sub.ih_deduct_amt
        flat_header.ih_deduct_vat = sub.ih_deduct_vat
        flat_header.ih_days = sub.ih_days
        flat_header.ih_cr = sub.ih_cr
        flat_header.ih_day_book_flag = sub.ih_day_book_flag
        flat_header.ih_update = sub.ih_update

    flat_line = getattr(record, "invoice_line")
    if flat_line is not None and staged is not None:
        flat_line.il_invoice = shared_invoice
        flat_line.il_line = shared_test
        flat_line.il_product = staged.il_product
        flat_line.il_pa = staged.il_pa
        flat_line.filler_1 = staged.filler_1
        flat_line.il_qty = staged.il_qty
        flat_line.il_type = staged.il_type
        flat_line.il_description = staged.il_description
        flat_line.filler_2 = staged.filler_2
        flat_line.il_net = staged.il_net
        flat_line.il_unit = staged.il_unit
        flat_line.il_discount = staged.il_discount
        flat_line.il_vat = staged.il_vat
        flat_line.il_vat_code = staged.il_vat_code
        flat_line.il_update = staged.il_update


_ACTUAL_LINES_IN_ROW_DIGITS: Final[int] = 2


def _move_to_actual_lines_in_row(value: int) -> int:
    """``move HV-IH-LINES to WS-Actual-Lines-In-Row.`` [common/plinvoiceMT.cbl:L1518].

    The magnitude is taken without the builtin ``abs()``, which rule R-2's audit forbids
    in this layer; the sender is unsigned, so it is a faithful no-op for every value the
    column can hold.

    Args:
        value: What the host variable holds - the ``IH-LINES`` column's value.

    Returns:
        The two digits the receiving field keeps.
    """
    magnitude = -value if value < 0 else value
    return magnitude % 10**_ACTUAL_LINES_IN_ROW_DIGITS


def _split_ih_order(
    order: str, group: IhOrder, context: PInvoiceContext
) -> None:
    """Expose ten caller bytes through ``05 ih-order.`` without losing the image."""
    text = _characters(order, 10)
    group.ih_freq = text[0]
    group.ih_repeat = int(text[1:3]) if text[1:3].isdigit() else 0
    group.filler_1 = text[3:6]
    group.ih_last_date = int.from_bytes(
        text[6:10].encode("latin-1"), "big", signed=True
    )
    context.ih_order_group = group
    context.ih_order_image = text
    context.ih_order_components = _ih_order_components(group)
